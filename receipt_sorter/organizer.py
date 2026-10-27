"""Move files into year/month/category folders and write a CSV summary."""

from __future__ import annotations

import csv
import shutil
from dataclasses import asdict
from pathlib import Path

from .classifier import classify_path
from .dates import date_from_filename, date_from_mtime
from .models import ReceiptRecord, SortResult, SortStatus
from .ocr import date_from_ocr

SUPPORTED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".txt", ".csv",
}


def _safe_dest_name(name: str) -> str:
    """Return a filesystem-safe filename, preserving extension."""
    stem = Path(name).stem
    ext = Path(name).suffix
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in stem).strip() or "receipt"
    return f"{safe}{ext}"


def _unique_path(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    ext = Path(name).suffix
    i = 2
    while True:
        candidate = dest_dir / f"{stem}_{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1


def _resolve_date(path: Path, ocr: bool) -> str:
    """Return an ISO date string, preferring filename then OCR then mtime."""
    found = date_from_filename(path)
    if found is not None:
        return found.isoformat()
    if ocr:
        _, date_iso, _, _ = date_from_ocr(path)
        if date_iso:
            return date_iso
    mtime = date_from_mtime(path)
    return mtime.isoformat() if mtime else ""


def process_file(
    path: Path,
    root: Path,
    rules,
    ocr: bool,
    dry_run: bool,
) -> ReceiptRecord:
    """Classify and optionally move one file. Returns a ReceiptRecord."""
    original_name = path.name
    rule, status = classify_path(path, rules)
    date_iso = _resolve_date(path, ocr)
    year = date_iso[:4] if date_iso else ""
    month = date_iso[5:7] if len(date_iso) >= 7 else ""
    category = rule.category if rule else ""
    ocr_text = ""
    amount = ""
    merchant = ""
    if ocr and rule is not None:
        ocr_text, _, amount, merchant = date_from_ocr(path)

    destination = ""
    moved_name = original_name
    if rule is not None and status == SortStatus.SORTED and year and month:
        dest_dir = root / year / month / category
        new_name = _safe_dest_name(original_name)
        dest = _unique_path(dest_dir, new_name) if not dry_run else dest_dir / new_name
        if dry_run:
            destination = str(dest.relative_to(root))
            moved_name = dest.name
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))
            destination = str(dest.relative_to(root))
            moved_name = dest.name

    return ReceiptRecord(
        original_name=original_name,
        moved_name=moved_name,
        year=year,
        month=month,
        category=category,
        date_iso=date_iso,
        amount=amount,
        merchant=merchant,
        source_text=ocr_text,
        notes=("dry-run" if dry_run else "") if rule else "no matching rule",
        status=SortStatus.SORTED if rule else SortStatus.UNCLASSIFIED,
        destination=destination,
    )


def scan_folder(
    root: Path, rules, ocr: bool, dry_run: bool, recursive: bool = False
) -> SortResult:
    """Process every supported file in `root` (recursive if requested)."""
    result = SortResult()
    if not root.exists():
        result.errors.append(f"Source folder does not exist: {root}")
        return result
    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.iterdir()
    files = sorted(
        p for p in iterator
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    for path in files:
        try:
            record = process_file(path, root, rules, ocr, dry_run)
        except Exception as exc:  # pragma: no cover - defensive
            result.errors.append(f"{path.name}: {exc}")
            result.records.append(
                ReceiptRecord(
                    original_name=path.name,
                    moved_name=path.name,
                    year="",
                    month="",
                    category="",
                    date_iso="",
                    amount="",
                    merchant="",
                    source_text="",
                    notes=str(exc),
                    status=SortStatus.FAILED,
                )
            )
            continue
        result.records.append(record)
    return result


def write_csv(result: SortResult, csv_path: Path) -> None:
    """Write the expense summary CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "original_name",
        "moved_name",
        "year",
        "month",
        "category",
        "date_iso",
        "amount",
        "merchant",
        "source_text",
        "notes",
        "status",
        "destination",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in result.records:
            writer.writerow(asdict(record))
    # Append a totals footer row for bookkeeping convenience.
    with csv_path.open("a", encoding="utf-8", newline="") as fh:
        fh.write(
            f"TOTAL,,,,,,{result.total_amount:.2f},,,,,\n"
        )


__all__ = ["process_file", "scan_folder", "write_csv", "SUPPORTED_EXTENSIONS"]
