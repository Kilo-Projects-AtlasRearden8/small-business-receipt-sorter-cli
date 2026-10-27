"""Tests for the receipt-sorter CLI."""

import csv
import json
from pathlib import Path

from receipt_sorter import cli
from receipt_sorter.organizer import scan_folder


def _make_receipts(root: Path) -> list[Path]:
    files = [
        "OfficeDepot_Receipt_2024-07-15.pdf",
        "Starbucks_July_2024.jpg",
        "Amazon_Business_2024-08-02.png",
        "AWS_Invoice_2024-09-01.pdf",
        "random_unknown_file.txt",
    ]
    paths = []
    for name in files:
        p = root / name
        p.write_text(name, encoding="utf-8")
        paths.append(p)
    return paths


def test_dry_run_moves_nothing(tmp_path):
    receipts = _make_receipts(tmp_path)
    rc = cli.main([str(tmp_path), "--dry-run", "--out", "expenses.csv"])
    assert rc == 0
    assert all(p.exists() for p in receipts)
    remaining = {p.name for p in tmp_path.iterdir()}
    # Dry-run writes nothing: only the original receipts remain.
    assert remaining == {p.name for p in receipts}
    assert not (tmp_path / "expenses.csv").exists()


def test_real_run_organizes_files(tmp_path):
    _make_receipts(tmp_path)
    rc = cli.main([str(tmp_path), "--out", "expenses.csv"])
    assert rc == 0
    moved = [p for p in tmp_path.rglob("*") if p.is_file() and p.name != "expenses.csv"]
    assert moved
    assert not (tmp_path / "OfficeDepot_Receipt_2024-07-15.pdf").exists()
    assert (tmp_path / "2024" / "07" / "Supplies" / "OfficeDepot_Receipt_2024-07-15.pdf").exists()
    csv_path = tmp_path / "expenses.csv"
    rows = [r for r in csv.DictReader(csv_path.open()) if r["original_name"] != "TOTAL"]
    assert any(r["category"] == "Supplies" for r in rows)
    last = list(csv_path.open())[-1].strip()
    assert last.startswith("TOTAL")


def test_json_summary(tmp_path):
    _make_receipts(tmp_path)
    rc = cli.main([str(tmp_path), "--json", "--out", "expenses.csv"])
    assert rc == 0
    payload = json.loads((tmp_path / "expenses.json").read_text())
    assert "summary" in payload
    assert "records" in payload
    assert payload["summary"]["sorted"] >= 1


def test_custom_rules_yaml(tmp_path):
    _make_receipts(tmp_path)
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        "rules:\n"
        "  - name: coffee\n"
        "    category: Meals\n"
        "    contains: starbucks\n",
        encoding="utf-8",
    )
    rc = cli.main([str(tmp_path), "--rules", str(rules), "--out", "expenses.csv"])
    assert rc == 0
    rows = [
        r
        for r in csv.DictReader((tmp_path / "expenses.csv").open())
        if r["original_name"] != "TOTAL"
    ]
    starbucks = [r for r in rows if r["original_name"] == "Starbucks_July_2024.jpg"]
    assert starbucks and starbucks[0]["category"] == "Meals"


def test_unclassified_files_left_in_place(tmp_path):
    _make_receipts(tmp_path)
    rc = cli.main([str(tmp_path), "--out", "expenses.csv"])
    assert rc == 0
    rows = [
        r
        for r in csv.DictReader((tmp_path / "expenses.csv").open())
        if r["original_name"] != "TOTAL"
    ]
    unclassified = [r for r in rows if r["status"] == "unclassified"]
    assert any(r["original_name"] == "random_unknown_file.txt" for r in unclassified)
    assert (tmp_path / "random_unknown_file.txt").exists()


def test_source_dir_default_is_cwd(tmp_path, monkeypatch):
    receipts = _make_receipts(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["--dry-run", "--out", "expenses.csv"])
    assert rc == 0
    remaining = {p.name for p in tmp_path.iterdir()}
    assert remaining == {p.name for p in receipts}
    assert not (tmp_path / "expenses.csv").exists()


def test_recursive_scan(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "OfficeDepot_Receipt_2024-07-15.pdf").write_text("x", encoding="utf-8")
    (sub / "Starbucks_July_2024.jpg").write_text("x", encoding="utf-8")
    rc = cli.main([str(tmp_path), "--dry-run", "--recursive", "--out", "expenses.csv"])
    assert rc == 0
    # Dry-run writes nothing; receipts still in place.
    assert (tmp_path / "OfficeDepot_Receipt_2024-07-15.pdf").exists()
    assert (sub / "Starbucks_July_2024.jpg").exists()
    assert not (tmp_path / "expenses.csv").exists()


def test_scan_folder_handles_empty_dir(tmp_path):
    result = scan_folder(tmp_path, [], ocr=False, dry_run=True)
    assert result.records == []
    assert result.total_amount == 0.0
