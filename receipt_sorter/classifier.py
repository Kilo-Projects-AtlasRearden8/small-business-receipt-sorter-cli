"""Classification of receipt files by filename rules.

Rules are evaluated in order; the first matching rule wins. A rule may
specify a regex (matched against the full filename), a `contains` substring,
a `category`, and optionally a date pattern. If no rule matches, the file is
left unclassified (dry-run reports it; real run skips it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import SortStatus


@dataclass
class Rule:
    name: str
    category: str
    regex: str | None = None
    contains: str | None = None
    date: str | None = None
    _compiled: re.Pattern[str] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.regex is not None:
            self._compiled = re.compile(self.regex, re.IGNORECASE)

    def matches(self, filename: str) -> bool:
        if self._compiled is not None:
            return self._compiled.search(filename) is not None
        if self.contains is not None:
            return self.contains.lower() in filename.lower()
        return False


DEFAULT_RULES: list[Rule] = [
    Rule(
        name="office-supplies",
        category="Supplies",
        regex=r"(office|suppl|staple|pen|paper|ink)",
    ),
    Rule(
        name="software-saas",
        category="Software",
        regex=r"(software|saas|subscription|adobe|microsoft|google\s*workspace|slack|notion|aws|cloud|hosting)",
    ),
    Rule(
        name="marketing-advertising",
        category="Marketing",
        regex=r"(marketing|advertis|ads|facebook|google\s*ads|campaign|flyer)",
    ),
    Rule(
        name="travel",
        category="Travel",
        regex=r"(travel|flight|airline|hotel|uber|lyft|taxi|train|mileage)",
    ),
    Rule(
        name="meals",
        category="Meals",
        regex=r"(meal|lunch|dinner|breakfast|cafe|coffee|restaurant|food|eat|starbucks|bucks|pizza|grill|brew|bakery|deli|diner)",
    ),
    Rule(
        name="medical",
        category="Medical",
        regex=r"(medical|clinic|pharmacy|drug|rx|insurance|health)",
    ),
    Rule(
        name="utilities",
        category="Utilities",
        regex=r"(utility|electric|gas|water|internet|phone|bill|power)",
    ),
    Rule(
        name="shipping",
        category="Shipping",
        regex=r"(shipping|freight|postage|ups|fedex|usps|dhl)",
    ),
    Rule(
        name="equipment",
        category="Equipment",
        regex=r"(equipment|hardware|tool|machine|laptop|computer|monitor)",
    ),
    Rule(
        name="professional-services",
        category="Professional Services",
        regex=r"(legal|account|bookkeep|consult|audit|cpa|lawyer)",
    ),
    Rule(
        name="income",
        category="Income",
        regex=r"(income|revenue|sale|refund|payment\s*received)",
    ),
    Rule(
        name="online-retail",
        category="Online Retail",
        regex=r"(amazon|ebay|walmart|target|costco|etsy|shopify)",
    ),
    Rule(
        name="generic-receipt",
        category="General",
        regex=r"(receipt|invoice|purchase|order|pos|sale)",
    ),
]


def load_rules(path: Path | None) -> list[Rule]:
    """Load rules from a YAML/JSON file if given, else defaults."""
    if path is None:
        return list(DEFAULT_RULES)
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _parse_yaml_rules(text)
    if suffix == ".json":
        return _parse_json_rules(text)
    raise ValueError(f"Unsupported rules file type: {path}")


def _parse_yaml_rules(text: str) -> list[Rule]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised only without pyyaml
        raise RuntimeError("PyYAML is required to load YAML rule files") from exc
    data = yaml.safe_load(text) or {}
    return _rules_from_dict(data)


def _parse_json_rules(text: str) -> list[Rule]:
    import json

    data = json.loads(text)
    return _rules_from_dict(data)


def _rules_from_dict(data: object) -> list[Rule]:
    if not isinstance(data, dict):
        raise ValueError("Rules file must contain a mapping at the top level")
    raw = data.get("rules", data)
    if not isinstance(raw, list):
        raise ValueError("Rules file must contain a list of rules")
    rules: list[Rule] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rules.append(
            Rule(
                name=str(item.get("name", "rule")),
                category=str(item.get("category", "General")),
                regex=item.get("regex"),
                contains=item.get("contains"),
                date=item.get("date"),
            )
        )
    return rules or list(DEFAULT_RULES)


def classify(filename: str, rules: list[Rule]) -> Rule | None:
    """Return the first rule matching `filename`, or None."""
    for rule in rules:
        if rule.matches(filename):
            return rule
    return None


def classify_path(path: Path, rules: list[Rule]) -> tuple[Rule | None, SortStatus]:
    rule = classify(path.name, rules)
    if rule is None:
        return None, SortStatus.UNCLASSIFIED
    return rule, SortStatus.SORTED


__all__ = ["Rule", "DEFAULT_RULES", "load_rules", "classify", "classify_path"]
