"""Tests for classification and date extraction logic."""

from pathlib import Path

from receipt_sorter.classifier import DEFAULT_RULES, classify, classify_path, load_rules
from receipt_sorter.dates import date_from_filename, extract_date_from_text


def test_classify_office_supplies():
    rule = classify("OfficeDepot_Receipt_2024-07-15.pdf", DEFAULT_RULES)
    assert rule is not None
    assert rule.category == "Supplies"


def test_classify_meals():
    rule = classify("Starbucks_July_2024.jpg", DEFAULT_RULES)
    assert rule is not None
    assert rule.category == "Meals"


def test_classify_software():
    rule = classify("AWS_Invoice_2024-09-01.pdf", DEFAULT_RULES)
    assert rule is not None
    assert rule.category == "Software"


def test_classify_unknown_returns_none():
    assert classify("totally_unknown_file.bin", DEFAULT_RULES) is None


def test_classify_path_unclassified_status():
    path = Path("random_file.bin")
    rule, status = classify_path(path, DEFAULT_RULES)
    assert rule is None
    assert status.value == "unclassified"


def test_extract_date_iso():
    assert extract_date_from_text("Receipt 2024-07-15 total").isoformat() == "2024-07-15"


def test_extract_date_mdy():
    assert extract_date_from_text("paid on 07/15/2024").isoformat() == "2024-07-15"


def test_extract_date_named_month():
    assert extract_date_from_text("July 15, 2024").isoformat() == "2024-07-15"


def test_extract_date_compact():
    assert extract_date_from_text("20240715").isoformat() == "2024-07-15"


def test_extract_date_none():
    assert extract_date_from_text("no date here") is None


def test_date_from_filename():
    assert date_from_filename(Path("Store_2024-08-02.png")).isoformat() == "2024-08-02"


def test_load_rules_yaml(tmp_path):
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        "rules:\n"
        "  - name: coffee\n"
        "    category: Meals\n"
        "    contains: starbucks\n",
        encoding="utf-8",
    )
    rules = load_rules(rules_path)
    assert len(rules) == 1
    assert rules[0].category == "Meals"
    assert rules[0].contains == "starbucks"


def test_load_rules_json(tmp_path):
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        '{"rules": [{"name": "x", "category": "Travel", "regex": "uber"}]}',
        encoding="utf-8",
    )
    rules = load_rules(rules_path)
    assert rules[0].category == "Travel"
    assert rules[0].matches("uber receipt")


def test_load_rules_none_returns_defaults():
    rules = load_rules(None)
    assert rules is not DEFAULT_RULES
    assert len(rules) == len(DEFAULT_RULES)
