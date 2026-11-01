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


def extract_document_text(file_bytes, filename=None):
    """
    Extracts text from either a PDF or an image file (PNG, JPG, JPEG, WEBP, TIFF, BMP).
    Returns (extracted_text, extraction_method, pdf_bytes).
    The returned pdf_bytes is guaranteed to be a valid PDF suitable for downstream preview and archival.
    """
    filename_lower = (filename or "").lower()
    is_pdf = file_bytes.startswith(b"%PDF-") or filename_lower.endswith(".pdf")

    if is_pdf:
        try:
            extracted_text, method = extract_pdf_text(file_bytes)
            return extracted_text, method, file_bytes
        except OcrError as err:
            # If it's a scanned PDF and Tesseract is missing, don't crash — allow manual entry
            if "Tesseract OCR engine is unavailable" in str(err) or "No readable text" in str(err):
                return "", "scanned PDF (manual transcription)", file_bytes
            raise

    # ── Handle Image File (PNG, JPG, JPEG, WEBP, TIFF, BMP) ───────────
    import pymupdf
    from PIL import Image

    # 1. Convert image to single-page PDF for preview & archival
    ext = Path(filename).suffix.lstrip(".").lower() if filename else "png"
    if ext == "jpg":
        ext = "jpeg"
    pdf_bytes = None
    try:
        with pymupdf.open(stream=file_bytes, filetype=ext) as img_doc:
            pdf_bytes = img_doc.convert_to_pdf()
    except Exception:
        pass

    if not pdf_bytes:
        try:
            pil_img = Image.open(BytesIO(file_bytes)).convert("RGB")
            buf = BytesIO()
            pil_img.save(buf, format="PDF")
            pdf_bytes = buf.getvalue()
        except Exception as error:
            raise OcrError(f"Could not convert uploaded image to readable document: {error}") from error

    # 2. Extract text from image using local Tesseract OCR if available
    if ocr_engine_available():
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = _tesseract_executable()
        try:
            pil_img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(pil_img, timeout=25).strip()
            if text:
                return text[:MAX_EXTRACTED_CHARACTERS], "local Tesseract image OCR", pdf_bytes
            return "", "image scan (no text detected, manual entry)", pdf_bytes
        except Exception as error:
            raise OcrError(f"Image OCR processing failed: {error}") from error

    # If local Tesseract is not available on this server
    return "", "image scan (Tesseract not installed on server — manual entry)", pdf_bytes
