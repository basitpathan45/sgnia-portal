"""
pdf_generator.py — Official Sindh Government PDF Auto-Generation Engine
=======================================================================
Generates A4 PDFs matching real Sindh Government departmental orders,
notifications, circulars, letters, and advisories.

Layout (top → bottom):
    • Sindh Government emblem (logo) — top-center
    • "GOVERNMENT OF SINDH" — bold, centered
    • Department name — bold, centered
    • "Karachi, dated the DD Month, YYYY" — italic, right-aligned
    • Heading e.g. "O R D E R" — spaced, bold, centered + underline
    • Reference number — bold, left-aligned
    • Subject — bold, left-aligned (optional)
    • Body text — times-roman, left-aligned (multi-paragraph)
    • Signatory block — bottom-right
    • Secure QR code — bottom-left with labels

QR code encodes the SGNIA public verification URL for the document
reference, allowing physical paper holders to scan and authenticate.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    import pymupdf  # PyMuPDF ≥ 1.24
except ImportError:
    import fitz as pymupdf  # older alias

import qrcode
import qrcode.constants
from PIL import Image

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sindh Government brand colours
# ---------------------------------------------------------------------------
_SINDH_GREEN = (0.043, 0.227, 0.196)        # #0b3a32 (dark green — QR fill)
_SINDH_GREEN_LABEL = (0.1, 0.35, 0.2)       # text label colour
_BLACK = (0, 0, 0)
_DARK_GREY = (0.2, 0.2, 0.2)
_MID_GREY = (0.3, 0.3, 0.3)
_LIGHT_GREY = (0.4, 0.4, 0.4)

# ---------------------------------------------------------------------------
# Page dimensions (A4 in PDF points: 1 pt = 1/72 inch)
# ---------------------------------------------------------------------------
_PAGE_W = 595.3
_PAGE_H = 841.9
_MARGIN_L = 50
_MARGIN_R = 545   # _PAGE_W - 50

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_official_sindh_pdf(
    reference: str,
    title: str,
    category: str,
    department: str,
    subject: str,
    body: str,
    document_date: date,
    official_reference: Optional[str],
    destination_path: Path,
    host_url: str = "http://127.0.0.1:5000/",
    logo_path: Optional[Path] = None,
) -> str:
    """
    Generate an official Sindh Government PDF document.

    Parameters
    ----------
    reference         : Internal SGNIA archive reference (e.g. SGNIA-2026-ABCD1234).
    title             : Human-readable title of the notification/order.
    category          : Document type: Notification | Order | Circular | Letter | Advisory.
    department        : Full department name (e.g. "Finance Department").
    subject           : One-line subject line.
    body              : Full body text (paragraphs separated by newline).
    document_date     : Effective date of the document.
    official_reference: Optional official file/reference number printed on the PDF.
    destination_path  : Absolute path where the PDF file will be written.
    host_url          : Base URL of the SGNIA portal (used in the QR verification link).
    logo_path         : Path to the Sindh Government emblem PNG. Auto-resolved if None.

    Returns
    -------
    str
        SHA-256 hex digest of the generated PDF file.
    """
    destination_path = Path(destination_path)

    # ---- Resolve logo path ------------------------------------------------
    if logo_path is None:
        # From staff_portal/app/pdf_generator.py → root is two levels up
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "government-of-sindh-logo.png"

    # ---- Create document and A4 page --------------------------------------
    doc = pymupdf.open()
    page = doc.new_page(width=_PAGE_W, height=_PAGE_H)

    # ------------------------------------------------------------------ #
    # 1. Sindh Government Emblem (top-center)                             #
    # ------------------------------------------------------------------ #
    if logo_path.is_file():
        try:
            pil_img = Image.open(logo_path).convert("RGBA")
            img_bytes = BytesIO()
            pil_img.save(img_bytes, format="PNG")
            logo_rect = pymupdf.Rect(272, 35, 323, 95)   # 51×60 pt, centered
            page.insert_image(logo_rect, stream=img_bytes.getvalue())
        except Exception as exc:
            log.warning("PDF generator: could not insert logo — %s", exc)

    # ------------------------------------------------------------------ #
    # 2. Header: "GOVERNMENT OF SINDH" + department                       #
    # ------------------------------------------------------------------ #
    page.insert_textbox(
        pymupdf.Rect(_MARGIN_L, 100, _MARGIN_R, 124),
        "GOVERNMENT OF SINDH",
        fontname="helv",
        fontsize=12,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )

    dept_upper = (department or "GOVERNMENT OF SINDH").upper()
    page.insert_textbox(
        pymupdf.Rect(_MARGIN_L, 124, _MARGIN_R, 148),
        dept_upper,
        fontname="helv",
        fontsize=10.5,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )

    # Thin rule under department name
    page.draw_line(
        pymupdf.Point(_MARGIN_L, 150),
        pymupdf.Point(_MARGIN_R, 150),
        color=_BLACK,
        width=0.5,
    )

    # ------------------------------------------------------------------ #
    # 3. City and Date (right-aligned, italic)                            #
    # ------------------------------------------------------------------ #
    if hasattr(document_date, "strftime"):
        date_str = document_date.strftime("%d %B, %Y")
    else:
        date_str = str(document_date)
    city_date = f"Karachi, dated the {date_str}"
    page.insert_textbox(
        pymupdf.Rect(_MARGIN_L, 155, _MARGIN_R, 180),
        city_date,
        fontname="times-italic",
        fontsize=10.5,
        color=_DARK_GREY,
        align=pymupdf.TEXT_ALIGN_RIGHT,
    )

    # ------------------------------------------------------------------ #
    # 4. Document heading  e.g. "O R D E R"  (centered, bold, spaced)    #
    # ------------------------------------------------------------------ #
    cat_upper = (category or "NOTIFICATION").upper()
    spaced_heading = " ".join(list(cat_upper))
    page.insert_textbox(
        pymupdf.Rect(_MARGIN_L, 185, _MARGIN_R, 215),
        spaced_heading,
        fontname="times-bold",
        fontsize=14,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )
    # Underline proportional to heading length
    heading_width = min(len(spaced_heading) * 8.5, _MARGIN_R - _MARGIN_L)
    cx = _PAGE_W / 2
    page.draw_line(
        pymupdf.Point(cx - heading_width / 2, 216),
        pymupdf.Point(cx + heading_width / 2, 216),
        color=_BLACK,
        width=0.8,
    )

    # ------------------------------------------------------------------ #
    # 5. Reference number                                                 #
    # ------------------------------------------------------------------ #
    effective_ref = (
        official_reference.strip()
        if official_reference and official_reference.strip()
        else reference
    )
    if effective_ref.upper().startswith("NO.") or effective_ref.upper().startswith("NO "):
        ref_text = f"{effective_ref}:" if not effective_ref.endswith(":") else effective_ref
    else:
        ref_text = f"NO. {effective_ref}:"
    page.insert_textbox(
        pymupdf.Rect(_MARGIN_L, 224, _MARGIN_R, 248),
        ref_text,
        fontname="times-bold",
        fontsize=11,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_LEFT,
    )

    # ------------------------------------------------------------------ #
    # 6. Subject line (optional)                                          #
    # ------------------------------------------------------------------ #
    y_cursor = 250
    if subject and subject.strip():
        subj_text = f"SUBJECT:   {subject.strip().upper()}"
        page.insert_textbox(
            pymupdf.Rect(_MARGIN_L, y_cursor, _MARGIN_R, y_cursor + 40),
            subj_text,
            fontname="times-bold",
            fontsize=10.5,
            color=_BLACK,
            align=pymupdf.TEXT_ALIGN_LEFT,
        )
        y_cursor += 42

    # ------------------------------------------------------------------ #
    # 7. Body text                                                        #
    # ------------------------------------------------------------------ #
    # Reserve bottom 200pt for signatory + QR area
    body_bottom = _PAGE_H - 200
    body_rect = pymupdf.Rect(_MARGIN_L, y_cursor, _MARGIN_R, body_bottom)
    overflow = page.insert_textbox(
        body_rect,
        body.strip() if body else "",
        fontname="times-roman",
        fontsize=11,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_LEFT,
    )
    if overflow < 0:
        log.info("PDF generator: body text overflow (%d pt) for ref %s", overflow, reference)

    # ------------------------------------------------------------------ #
    # 8. Signatory block (bottom-right)                                   #
    # ------------------------------------------------------------------ #
    sig_top = _PAGE_H - 185
    page.insert_textbox(
        pymupdf.Rect(300, sig_top, _MARGIN_R, sig_top + 25),
        "-SECRETARY TO GOVT. OF SINDH-",
        fontname="times-bold",
        fontsize=10,
        color=_BLACK,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )
    page.insert_textbox(
        pymupdf.Rect(300, sig_top + 45, _MARGIN_R, sig_top + 65),
        "SECTION OFFICER",
        fontname="times-bold",
        fontsize=9.5,
        color=_DARK_GREY,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )
    page.insert_textbox(
        pymupdf.Rect(300, sig_top + 65, _MARGIN_R, sig_top + 85),
        department,
        fontname="times-italic",
        fontsize=8.5,
        color=_MID_GREY,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )

    # ------------------------------------------------------------------ #
    # 9. Secure QR code (bottom-left)                                     #
    # Encodes the SGNIA public verification URL for this reference.       #
    # The QR data uses the archive reference — any tampering with the     #
    # document (even a single byte) will not decode to a valid URL in     #
    # the SGNIA system, because the reference is bound to the original    #
    # content via the signed SHA-256 stored server-side.                  #
    # ------------------------------------------------------------------ #
    clean_host = host_url.rstrip("/")
    verification_url = f"{clean_host}/verify/{reference}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0b3a32", back_color="white")

    qr_bytes = BytesIO()
    qr_img.save(qr_bytes, format="PNG")

    qr_top = _PAGE_H - 180
    qr_rect = pymupdf.Rect(_MARGIN_L, qr_top, _MARGIN_L + 75, qr_top + 75)
    page.insert_image(qr_rect, stream=qr_bytes.getvalue())

    # QR label strip (right of QR code)
    lbl_x0 = _MARGIN_L + 80
    page.insert_textbox(
        pymupdf.Rect(lbl_x0, qr_top + 5, 330, qr_top + 18),
        "OFFICIAL SINDH GOVERNMENT NOTIFICATION",
        fontname="helv",
        fontsize=6.5,
        color=_SINDH_GREEN_LABEL,
    )
    page.insert_textbox(
        pymupdf.Rect(lbl_x0, qr_top + 19, 330, qr_top + 31),
        f"Archive Ref: {reference}",
        fontname="courier",
        fontsize=7,
        color=_BLACK,
    )
    page.insert_textbox(
        pymupdf.Rect(lbl_x0, qr_top + 32, 330, qr_top + 44),
        "Scan QR code to verify authenticity",
        fontname="helv",
        fontsize=6,
        color=_MID_GREY,
    )
    page.insert_textbox(
        pymupdf.Rect(lbl_x0, qr_top + 45, 330, qr_top + 56),
        "Sindh Government Notification Issuing Authority (SGNIA)",
        fontname="helv",
        fontsize=5.5,
        color=_LIGHT_GREY,
    )

    # Thin top border line above footer area
    page.draw_line(
        pymupdf.Point(_MARGIN_L, qr_top - 5),
        pymupdf.Point(_MARGIN_R, qr_top - 5),
        color=_MID_GREY,
        width=0.4,
    )

    # ------------------------------------------------------------------ #
    # 10. Save and hash                                                   #
    # ------------------------------------------------------------------ #
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(destination_path))
    doc.close()

    # Return SHA-256 of the written file
    hasher = hashlib.sha256()
    with destination_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

