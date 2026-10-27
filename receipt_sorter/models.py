"""Data models for the receipt sorter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class SortStatus(str, Enum):
    """Outcome of processing a single file."""

    SORTED = "sorted"
    SKIPPED = "skipped"
    FAILED = "failed"
    UNCLASSIFIED = "unclassified"


@dataclass
class ReceiptRecord:
    """One row of the expense summary CSV."""

    original_name: str
    moved_name: str
    year: str
    month: str
    category: str
    date_iso: str
    amount: str
    merchant: str
    source_text: str
    notes: str
    status: SortStatus
    destination: str = ""


@dataclass
class SortResult:
    """Aggregate result of a sort run."""

    records: list[ReceiptRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def sorted_count(self) -> int:
        return sum(1 for r in self.records if r.status == SortStatus.SORTED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.records if r.status == SortStatus.SKIPPED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.records if r.status == SortStatus.FAILED)

    @property
    def unclassified_count(self) -> int:
        return sum(1 for r in self.records if r.status == SortStatus.UNCLASSIFIED)

    @property
    def total_amount(self) -> float:
        total = 0.0
        for r in self.records:
            if r.amount:
                try:
                    total += float(r.amount)
                except ValueError:
                    pass
        return round(total, 2)


def month_name(number: int) -> str:
    """Return zero-padded month number as string, e.g. '07'."""
    return f"{number:02d}"


def month_label(number: int) -> str:
    """Return human-readable month label, e.g. 'July'."""
    return date(2000, number, 1).strftime("%B")
