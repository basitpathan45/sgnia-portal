import importlib.util
import os
import shutil
from io import BytesIO
from pathlib import Path

from flask import current_app, has_app_context
from pypdf import PdfReader

MAX_OCR_PAGES = 20
MAX_EXTRACTED_CHARACTERS = 200_000


class OcrError(Exception):
    pass


def _tesseract_executable():
    configured_path = current_app.config.get("TESSERACT_CMD") if has_app_context() else None
    executable = configured_path or shutil.which("tesseract")
    if executable and (Path(executable).is_file() or shutil.which(executable)):
        return executable
    if configured_path:
        return None
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        installed_path = Path(program_files) / "Tesseract-OCR" / "tesseract.exe"
        if installed_path.is_file():
            return str(installed_path)
    return None


def ocr_engine_available():
    return bool(
        _tesseract_executable()
        and importlib.util.find_spec("pytesseract")
        and importlib.util.find_spec("pymupdf")
    )


def extract_pdf_text(pdf_bytes):
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=True)
        if reader.is_encrypted:
            raise OcrError("Password-protected PDFs cannot be processed.")
        if not reader.pages:
            raise OcrError("The PDF has no pages.")
        if len(reader.pages) > MAX_OCR_PAGES:
            raise OcrError(f"Processing is limited to {MAX_OCR_PAGES} pages per document.")
        page_text = [page.extract_text() or "" for page in reader.pages]
    except OcrError:
        raise
    except Exception as error:
        raise OcrError("The PDF could not be read. Upload a valid, unencrypted PDF.") from error

    extracted_text = "\n\n".join(text.strip() for text in page_text if text.strip())
    if extracted_text:
        return extracted_text[:MAX_EXTRACTED_CHARACTERS], "embedded text"
    if not ocr_engine_available():
        raise OcrError(
            "This looks like a scanned PDF, but the local Tesseract OCR engine is unavailable. "
            "Install Tesseract on this server; documents are never sent to a cloud OCR service."
        )

    import pymupdf
    import pytesseract
    from PIL import Image

    pytesseract.pytesseract.tesseract_cmd = _tesseract_executable()
    results = []
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            for page in document:
                page_rect = page.rect
                if page_rect.width * 1.5 * page_rect.height * 1.5 > 20_000_000:
                    raise OcrError("A PDF page exceeds the local OCR image-size limit.")
                image = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
                page_image = Image.frombytes("RGB", (image.width, image.height), image.samples)
                results.append(pytesseract.image_to_string(page_image, timeout=15).strip())
                if sum(map(len, results)) >= MAX_EXTRACTED_CHARACTERS:
                    break
    except OcrError:
        raise
    except Exception as error:
        raise OcrError(f"Local OCR failed: {error}") from error

    extracted_text = "\n\n".join(text for text in results if text)
    if not extracted_text:
        raise OcrError("No readable text was detected. Review the scan or type the text manually.")
    return extracted_text[:MAX_EXTRACTED_CHARACTERS], "local Tesseract OCR"
