# receipt-sorter

A friendly, local-first command-line tool that sorts a folder of receipt files
(PDF, JPG, PNG, and a few other image formats) into `year/month/category`
folders and writes a CSV expense summary for bookkeeping.

Everything runs on your own machine. OCR is optional and only runs if you
install `pytesseract` and the `tesseract` binary. No cloud, no API keys, no
network calls, and nothing ever leaves your computer.

Built by **Asdale Dynamics, LLC** — beginner-friendly AI education, books,
guides, and practical small-business tools.

## What it does

Point `receipt-sorter` at a folder of receipts and it will:

1. **Read each filename** and guess the date, category, and amount.
2. **Move each receipt** into a `year/month/category` folder, such as
   `2024/07/Supplies/OfficeDepot_Receipt_2024-07-15.pdf`.
3. **Write `expenses.csv`** — one row per receipt with date, amount, merchant,
   and category, plus a `TOTAL` row at the bottom for bookkeeping.

If a file doesn't match any rule, it's reported as `unclassified` and left
exactly where it is — nothing is ever moved without a good reason.

## Features

- **Filename-based classification** — rules match on regex or plain text, so
  `OfficeDepot_Receipt_2024-07-15.pdf` lands in `2024/07/Supplies/`.
- **Optional local OCR** — with `pytesseract` + `tesseract` installed, image
  receipts get their text read for date/amount/merchant guessing.
- **Smart date resolution** — filename date first, then OCR text, then the
  file's modification date as a fallback.
- **CSV summary** — one row per receipt plus a `TOTAL` footer row.
- **Dry-run mode** (`--dry-run`) — preview every move without touching a file
  (no files moved, no CSV written).
- **Custom rules** (`--rules`) — load your own classification rules from a
  YAML or JSON file.
- **Recursive scanning** (`--recursive`) — look inside subfolders too.
- **JSON report** (`--json`) — a machine-readable summary next to the CSV.

## Installation

```bash
pip install -e .
# optional extras:
pip install -e ".[ocr,pdf,dev]"
```

To enable OCR you also need the `tesseract` binary, e.g.:

```bash
# Debian/Ubuntu
sudo apt install tesseract-ocr
# macOS
brew install tesseract
```

## Usage

**Step 1: Preview first (recommended).** Dry-run shows what would happen
without moving anything or writing any files:

```bash
receipt-sorter ./receipts --dry-run
```

**Step 2: Sort for real.**

```bash
receipt-sorter ./receipts --out ./expenses.csv
```

**With OCR** (reads text from images):

```bash
receipt-sorter ./receipts --ocr
```

**Include subfolders:**

```bash
receipt-sorter ./receipts --recursive
```

**Use your own rules** (`rules.yaml`):

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

### What the output looks like

```
receipts/
├── 2024/
│   └── 07/
│       └── Supplies/
│           └── OfficeDepot_Receipt_2024-07-15.pdf
expenses.csv
```

`expenses.csv` columns:
`original_name, moved_name, year, month, category, date_iso, amount,
merchant, source_text, notes, status, destination` — plus a `TOTAL` row at
the bottom.

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