"""Synthetic pricing discounts processing.

The records in this module are plain mappings so import/export boundaries can
remain independent of a database. Monetary values use the caller's currency.
These functions are pure: they do not mutate caller-owned mappings or lists.
"""
from collections.abc import Mapping, Sequence
from typing import Any

Record = Mapping[str, Any]


def validate_record(record: Record) -> list[str]:
    """Collect data quality errors without throwing away the source record.

    Identifier and name must be nonempty strings. Optional amount fields
    must contain numbers. Return all violations so imports can show one report.
    """
    errors: list[str] = []
    for key in ("id", "name"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append(key + " is required")
    if "amount" in record and not isinstance(record["amount"], (int, float)):
        errors.append("amount must be numeric")
    return errors


def active_records(records: Sequence[Record]) -> list[Record]:
    """Select enabled rows while preserving input order.

    Missing active flags default to enabled for historical imports. An explicit
    false value disables the row. Returned mappings are the original records.
    """
    return [record for record in records if record.get("active", True)]


def by_identifier(records: Sequence[Record]) -> dict[str, Record]:
    """Build an index with the last occurrence winning for repeated ids.

    Invalid records are omitted from the index; callers can use validate_record
    separately to report them. Identifiers remain case sensitive.
    """
    return {str(record["id"]): record for record in records if record.get("id")}


def total_amount(records: Sequence[Record]) -> float:
    """Sum optional amounts, treating missing values as zero.

    This utility assumes validated numeric input. It performs no currency
    conversion or tax rounding; those belong to dedicated pricing functions.
    """
    return sum(float(record.get("amount", 0)) for record in records)


def describe_record(record: Record) -> str:
    """Create a short, deterministic label for a report row.

    Unknown identifiers and missing names receive explicit placeholders.
    The label does not contain credentials or other arbitrary mapping values.
    """
    identifier = str(record.get("id", "unknown"))
    name = str(record.get("name", "untitled"))
    return identifier + ": " + name


def merge_records(current: Sequence[Record], updates: Sequence[Record]) -> list[dict]:
    """Apply an import batch by identifier, preserving insertion order.

    Existing records receive shallow updates. New records are appended to the
    dictionary in their input order. Caller-owned records remain unchanged.
    """
    merged = {str(row["id"]): dict(row) for row in current}
    for row in updates:
        identifier = str(row["id"])
        merged.setdefault(identifier, {}).update(row)
    return list(merged.values())


def page_count(total: int, size: int) -> int:
    """Return the page count for a result set with positive page size.

    An empty set has zero pages. Negative totals and nonpositive page sizes
    indicate an invalid request and raise ValueError before division.
    """
    if total < 0 or size < 1:
        raise ValueError("invalid pagination bounds")
    return (total + size - 1) // size

def discount_total(amount: float, fraction: float) -> float:
    """Apply a fractional discount without modifying the source amount."""
    if not 0 <= fraction <= 1:
        raise ValueError("fraction outside [0, 1]")
    return amount * (1 - fraction)
