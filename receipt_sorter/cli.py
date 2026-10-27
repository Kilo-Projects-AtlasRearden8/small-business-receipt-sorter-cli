"""Command-line interface for the receipt sorter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .classifier import load_rules
from .models import SortStatus
from .organizer import scan_folder, write_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="receipt-sorter",
        description=(
            "Sort a folder of receipt files (PDF/JPG/PNG) into "
            "year/month/category folders and write a CSV expense summary."
        ),
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="Folder containing receipt files (default: current directory).",
    )
    parser.add_argument(
        "--out",
        default="expenses.csv",
        help="Path for the CSV summary (default: expenses.csv in the source folder).",
    )
    parser.add_argument(
        "--rules",
        default=None,
        help="Optional YAML/JSON file of custom classification rules.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Run local OCR (pytesseract) to extract dates/amounts from images.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview moves without changing any files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also write a machine-readable JSON summary next to the CSV.",
    )
    return parser


def _print_summary(result, dry_run: bool) -> int:
    label = "DRY RUN" if dry_run else "RUN"
    print(f"[{label}] sorted={result.sorted_count} "
          f"unclassified={result.unclassified_count} "
          f"failed={result.failed_count} skipped={result.skipped_count} "
          f"total=${result.total_amount:.2f}")
    for err in result.errors:
        print(f"error: {err}", file=sys.stderr)
    for record in result.records:
        if record.status != SortStatus.SORTED:
            print(f"  {record.status.value:13} {record.original_name} -> {record.notes}")
    return 0 if not result.errors else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.source).resolve()
    rules = load_rules(Path(args.rules) if args.rules else None)
    csv_path = Path(args.out)
    if not csv_path.is_absolute():
        csv_path = root / csv_path

    result = scan_folder(root, rules, ocr=args.ocr, dry_run=args.dry_run)
    if not args.dry_run:
        write_csv(result, csv_path)
        print(f"wrote {csv_path}")
    else:
        write_csv(result, csv_path)
        print(f"would write {csv_path}")

    if args.json:
        import json

        json_path = csv_path.with_suffix(".json")
        payload = {
            "summary": {
                "sorted": result.sorted_count,
                "unclassified": result.unclassified_count,
                "failed": result.failed_count,
                "skipped": result.skipped_count,
                "total_amount": result.total_amount,
                "errors": result.errors,
            },
            "records": [
                {
                    "original_name": r.original_name,
                    "moved_name": r.moved_name,
                    "year": r.year,
                    "month": r.month,
                    "category": r.category,
                    "date_iso": r.date_iso,
                    "amount": r.amount,
                    "merchant": r.merchant,
                    "status": r.status.value,
                    "destination": r.destination,
                }
                for r in result.records
            ],
        }
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"wrote {json_path}")

    return _print_summary(result, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
