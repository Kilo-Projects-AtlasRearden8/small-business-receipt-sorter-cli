# STATUS — receipt-sorter

A local-first CLI that sorts a folder of receipt files (PDF/JPG/PNG and a few
other image formats) into `year/month/category` folders and writes a CSV
expense summary for bookkeeping. Built by **Asdale Dynamics, LLC**.

## What was built

```
receipt-sorter/
├── LICENSE                  # MIT, Copyright (c) 2026 Asdale Dynamics, LLC
├── README.md                # beginner-friendly usage, rules table, license
├── pyproject.toml           # build + entry point `receipt-sorter`
├── receipt_sorter/
│   ├── __init__.py
│   ├── cli.py               # argparse CLI, summary printer, JSON output
│   ├── models.py            # ReceiptRecord, SortResult, SortStatus enums
│   ├── classifier.py        # filename rules (regex/contains), YAML+JSON loader
│   ├── dates.py             # date extraction from text/filenames/mtime
│   ├── ocr.py               # optional pytesseract + pdfplumber wrapper
│   └── organizer.py         # scan_folder, process_file, write_csv
└── tests/
    ├── test_cli.py           # CLI, dry-run, real run, JSON, custom rules
    └── test_logic.py         # classifier and date extraction
```

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/receipt-sorter ./receipts --dry-run          # preview only, writes nothing
.venv/bin/receipt-sorter ./receipts --out expenses.csv # sort for real
.venv/bin/receipt-sorter ./receipts --ocr --json      # OCR + JSON report
.venv/bin/receipt-sorter ./receipts --recursive --out expenses.csv  # include subfolders
.venv/bin/receipt-sorter ./receipts --rules rules.yaml
```

OCR is optional and only activates when `pytesseract` and the `tesseract`
binary are installed. Nothing ever leaves the machine.

## Verification results

- `pytest -q` → **22 passed** (classifier, dates, organizer, CSV, CLI dry-run,
  real run, JSON, custom rules, unclassified handling, empty folder, recursive).
- `ruff check .` → **All checks passed** (E/F/W/I/UP, line length 100).
- End-to-end smoke test (real files, real run) → files moved into
  `2024/07/Supplies/`, `2024/08/Online Retail/`, `2024/09/Software/`,
  `2024/10/General/` (nested, via `--recursive`), `2026/10/Meals/`;
  unclassified file left in place; `expenses.csv` written with a `TOTAL`
  footer row.
- Dry-run smoke test → no files moved, no folders created, no CSV/JSON written.
- Secrets scan → no API keys, tokens, or personal data in tracked files.
- Git initialized and committed as the existing identity (`Dylan Asdale`),
  plain commit message, no Co-authored-by trailers, no push, no remote.

## Known gaps

- OCR requires the system `tesseract` binary and the `pytesseract` package;
  without them, image receipts are processed by filename rules and mtime only.
- PDF text extraction requires `pdfplumber`; scanned PDFs without embedded
  text cannot be OCR'd.
- Amount/merchant extraction from OCR is heuristic (prefers lines mentioning
  "total", falls back to largest amount) and not validated.
- Rules are matched against the full filename; multi-word category folder
  names (e.g. `Professional Services`) contain spaces by design.
- No deduplication across runs beyond unique-path renaming on collisions.
- `--json` writes a sibling `.json` report; the CSV `TOTAL` footer row is not
  valid for machine parsers that expect uniform rows.
- Sorting is move-based by default; use `--dry-run` to preview first.