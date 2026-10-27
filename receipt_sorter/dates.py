"""Date extraction from filenames and OCR text.

Filenames often embed a date like 2024-07-15, 07152024, or July 15 2024.
We try a handful of common patterns in priority order. If nothing matches we
fall back to the file's mtime, which is a reasonable, local-only heuristic.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
_ISO = re.compile(r"(20\d{2})[-/.\s](\d{1,2})[-/.\s](\d{1,2})")
# MM-DD-YYYY, MM/DD/YYYY, MM.DD.YYYY
_MDY = re.compile(r"(\d{1,2})[-/.\s](\d{1,2})[-/.\s](20\d{2})")
# DD-MM-YYYY (European) - only tried if MM/DD/YYYY fails
_DMY = re.compile(r"(\d{1,2})[-/.\s](\d{1,2})[-/.\s](20\d{2})")
# Compact 8 digits: 20240715, 07152024
_COMPACT_YMD = re.compile(r"(20\d{2})(\d{2})(\d{2})")
_COMPACT_MDY = re.compile(r"(\d{2})(\d{2})(20\d{2})")
# Named months
_NAMED = re.compile(
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(\d{1,2}),?\s+(20\d{2})",
    re.IGNORECASE,
)
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _valid(year: int, month: int, day: int) -> bool:
    if not (2000 <= year <= 2099):
        return False
    if not (1 <= month <= 12):
        return False
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _from_iso(m: re.Match[str]) -> date | None:
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d) if _valid(y, mo, d) else None


def _from_mdy(m: re.Match[str]) -> date | None:
    mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d) if _valid(y, mo, d) else None


def _from_dmy(m: re.Match[str]) -> date | None:
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d) if _valid(y, mo, d) else None


def _from_named(m: re.Match[str]) -> date | None:
    month = _MONTHS.get(m.group(1)[:3].lower())
    if month is None:
        return None
    d, y = int(m.group(2)), int(m.group(3))
    return date(y, month, d) if _valid(y, month, d) else None


def extract_date_from_text(text: str) -> date | None:
    """Search `text` for a date and return the first valid one found."""
    if not text:
        return None
    for pattern, extractor in (
        (_ISO, _from_iso),
        (_NAMED, _from_named),
        (_COMPACT_YMD, lambda m: date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if _valid(int(m.group(1)), int(m.group(2)), int(m.group(3))) else None),
        (_MDY, _from_mdy),
        (_COMPACT_MDY, lambda m: date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        if _valid(int(m.group(3)), int(m.group(1)), int(m.group(2))) else None),
    ):
        m = pattern.search(text)
        if m:
            result = extractor(m)
            if result is not None:
                return result
    # DMY only after the others fail, to disambiguate 01-05-2024 style strings
    m = _DMY.search(text)
    if m:
        result = _from_dmy(m)
        if result is not None:
            return result
    return None


def date_from_filename(path: Path) -> date | None:
    """Best-effort date from the filename alone."""
    return extract_date_from_text(path.stem)


def date_from_mtime(path: Path) -> date | None:
    """Fall back to the file's last-modified date (local-only heuristic)."""
    try:
        return date.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


__all__ = ["extract_date_from_text", "date_from_filename", "date_from_mtime"]
