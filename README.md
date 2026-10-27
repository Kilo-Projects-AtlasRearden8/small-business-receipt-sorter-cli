# receipt-sorter

A small, local-first command-line tool that sorts a folder of receipt files
(PDF, JPG, PNG, and a few other image formats) into `year/month/category`
folders and writes a CSV expense summary for bookkeeping.

Everything runs on your machine. OCR is optional and only runs if
[pytesseract](https://github.com/madmaze/pytesseract) and the
`tesseract` binary are installed. No cloud, no API keys, no network calls.

Built by **Asdale Dynamics, LLC** — beginner-friendly AI education, books,
guides, and practical small-business tools.

## Features

- **Filename-based classification** — rules match on regex or substring, so
  `OfficeDepot_Receipt_2024-07-15.pdf` lands in `2024/07/Supplies/`.
- **Optional local OCR** — with pytesseract + tesseract installed, image
  receipts get their text extracted for date/amount/merchant guessing.
- **Date resolution** — filename date first, then OCR text, then the file's
  modification time as a fallback.
- **CSV summary** — one row per receipt plus a `TOTAL` footer row for
  bookkeeping.
- **Dry-run mode** — preview every move without touching a file.
- **Custom rules** — load classification rules from a YAML or JSON file.
- **JSON summary** — `--json` also writes a machine-readable report.

## Installation

```bash
pip install -e .
# optional extras:
pip install -e ".[ocr,pdf,dev]"
```

To enable OCR you also need the tesseract binary, e.g.:

```bash
# Debian/Ubuntu
sudo apt install tesseract-ocr
# macOS
brew install tesseract
```

## Usage

Dry run (no files moved):

```bash
receipt-sorter ./receipts --dry-run
```

Sort for real, writing `expenses.csv` next to the source folder:

```bash
receipt-sorter ./receipts --out ./expenses.csv
```

With local OCR:

```bash
receipt-sorter ./receipts --ocr
```

Custom rules file (`rules.yaml`):

```yaml
rules:
  - name: software
    category: Software
    regex: "(software|saas|subscription)"
  - name: coffee
    category: Meals
    contains: "starbucks"
```

```bash
receipt-sorter ./receipts --rules rules.yaml --ocr --json
```

### Output

Files are organized as:

```
receipts/
├── 2024/
│   └── 07/
│       └── Supplies/
│           └── OfficeDepot_Receipt_2024-07-15.pdf
expenses.csv
```

`expenses.csv` columns: `original_name, moved_name, year, month, category,
date_iso, amount, merchant, source_text, notes, status, destination`, with a
`TOTAL` row appended.

## Default rules

| Category             | Matches                                            |
| -------------------- | -------------------------------------------------- |
| Supplies             | office, suppl, staple, pen, paper, ink             |
| Software             | software, saas, subscription, adobe, slack, aws    |
| Marketing            | marketing, ads, campaign, flyer                    |
| Travel               | travel, flight, hotel, uber, taxi, mileage        |
| Meals                | meal, cafe, coffee, restaurant, food, starbucks    |
| Medical              | medical, clinic, pharmacy, insurance               |
| Utilities            | utility, electric, internet, phone, bill           |
| Shipping             | shipping, freight, ups, fedex, usps                |
| Equipment            | equipment, hardware, tool, laptop, monitor         |
| Professional Services | legal, account, bookkeep, consult, cpa             |
| Online Retail        | amazon, ebay, walmart, target, costco              |
| Income               | income, revenue, sale, refund                      |
| General              | receipt, invoice, purchase, order, pos             |

Rules are tried in order; the first match wins. Anything that matches nothing
is reported as `unclassified` and left in place.

## Testing

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2026 Asdale Dynamics, LLC.