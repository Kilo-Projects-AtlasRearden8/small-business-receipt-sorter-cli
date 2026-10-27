"""Optional local OCR.

OCR is entirely optional and local-only: it runs pytesseract against the
file if pytesseract and the tesseract binary are installed, and falls back
to extracting embedded text from PDFs with pdfplumber when available. If
nothing is available the file is still processed using filename rules only.
No data ever leaves the machine.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

_AMOUNT_RE = re.compile(
    r"(?:\$|€|£|USD|EUR|GBP)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})|\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})|\d+\.\d{2}"
)

_MERCHANT_STOP = {
    "total", "subtotal", "tax", "change", "cash", "card", "amount", "due",
    "paid", "balance", "grand", "tip", "receipt", "invoice", "order",
}


def _clean(text: str) -> str:
    return " ".join(text.split())


def ocr_text(path: Path) -> str:
    """Return extracted text for a file, or '' if OCR is unavailable."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf_text(path)
    if suffix in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"):
        return _image_text(path)
    return ""


def _pdf_text(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return ""
    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
            return _clean("\n".join(pages))
    except Exception:
        return ""


def _image_text(path: Path) -> str:
    if shutil.which("tesseract") is None:
        return ""
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        return ""
    try:
        text = pytesseract.image_to_string(Image.open(path))
        return _clean(text)
    except Exception:
        return ""


def extract_amount(text: str) -> str:
    """Pull the first currency-like amount out of OCR text, or ''."""
    if not text:
        return ""
    matches = _AMOUNT_RE.findall(text)
    if not matches:
        return ""
    # Prefer the largest-looking value (often the total) when several exist.
    def _norm(token: str) -> float:
        cleaned = token.replace("$", "").replace("€", "").replace("£", "")
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    best = max(matches, key=_norm)
    return f"{_norm(best):.2f}"


def extract_merchant(text: str) -> str:
    """Return the first non-trivial line of OCR text as a merchant guess."""
    if not text:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower().rstrip(":")
        if low in _MERCHANT_STOP:
            continue
        if len(line) < 2:
            continue
        return line[:80]
    return ""


def date_from_ocr(path: Path) -> tuple[str, str, str, str]:
    """Return (text, date_iso, amount, merchant) from OCR of a file."""
    text = ocr_text(path)
    date_iso = ""
    if text:
        from .dates import extract_date_from_text

        found = extract_date_from_text(text)
        if found is not None:
            date_iso = found.isoformat()
    return text, date_iso, extract_amount(text), extract_merchant(text)


__all__ = ["ocr_text", "extract_amount", "extract_merchant", "date_from_ocr"]
