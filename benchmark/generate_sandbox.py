"""Deterministic synthetic shopkit repository. No downloaded code or measurements."""

import argparse
from pathlib import Path

DOMAINS = {
    "catalog": ["products", "inventory", "categories", "search", "variants"],
    "pricing": ["discounts", "currency", "totals", "promotions", "quotes"],
    "tax": ["calculator", "rates", "regions", "exemptions", "invoices"],
    "shipping": ["rates", "parcels", "zones", "tracking", "labels"],
    "orders": ["checkout", "fulfillment", "returns", "payments", "cart"],
    "users": ["profiles", "addresses", "preferences", "accounts", "sessions"],
    "reports": ["sales", "inventory", "customers", "daily", "export"],
    "utils": ["pagination", "validation", "collections", "dates", "cli"],
}

CORE = {
    "utils/pagination": '''
def paginate(items: list, page: int, page_size: int) -> list:
    """Return a one-based page of items."""
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    start = (page - 1) * page_size
    return items[start:start + page_size]
''',
    "tax/calculator": '''
from decimal import ROUND_HALF_UP, Decimal

def calculate_tax(amount: str, rate: str) -> Decimal:
    """Round currency half up, including at half-cent boundaries."""
    return (Decimal(amount) * Decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
''',
    "pricing/discounts": '''
def discount_total(amount: float, fraction: float) -> float:
    """Apply a fractional discount without modifying the source amount."""
    if not 0 <= fraction <= 1:
        raise ValueError("fraction outside [0, 1]")
    return amount * (1 - fraction)
''',
    "pricing/quotes": '''
from shopkit.pricing.discounts import discount_total

def quote_amount(amount: float) -> float:
    """Apply the standard quote discount."""
    return discount_total(amount, 0.1)
''',
    "orders/checkout": '''
from shopkit.pricing.discounts import discount_total

def checkout_amount(amount: float) -> float:
    """Apply the standard checkout discount."""
    return discount_total(amount, 0.1)
''',
    "orders/cart": '''
from shopkit.pricing.discounts import discount_total

def cart_amount(amount: float) -> float:
    """Apply the standard cart discount."""
    return discount_total(amount, 0.1)
''',
    "reports/sales": '''
def average_sale(values: list[float]) -> float:
    """Empty sales periods have an average of zero."""
    return sum(values) / len(values) if values else 0.0
''',
    "utils/collections": '''
def unique_ordered(values: list) -> list:
    """Return unique hashable values in first-occurrence order."""
    return list(dict.fromkeys(values))
''',
    "shipping/rates": '''
def shipping_fee(weight: float) -> float:
    """Charge two currency units per kilogram."""
    return weight * 2.0
''',
    "orders/fulfillment": '''
from shopkit.shipping.rates import shipping_fee

def fulfillment_total(subtotal: float, weight: float) -> float:
    """Combine the subtotal with the separate shipping calculation."""
    return subtotal + shipping_fee(weight)
''',
    "users/addresses": '''
def normalize_address(value: str) -> str:
    """Trim, collapse spaces and lowercase a postal address."""
    return " ".join(value.strip().lower().split())

def billing_address(value: str) -> str:
    """Normalize billing input using the shared address helper."""
    return normalize_address(value)

def delivery_address(value: str) -> str:
    """Normalize delivery input using the shared address helper."""
    return normalize_address(value)
''',
    "utils/cli": '''
import argparse

def main(argv: list[str] | None = None) -> str:
    """Format a shop identifier with an optional uppercase flag."""
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--uppercase", action="store_true")
    args = parser.parse_args(argv)
    return args.name.upper() if args.uppercase else args.name

if __name__ == "__main__":
    print(main())
''',
}

TESTS = '''"""Synthetic shopkit acceptance tests, committed before measurements."""
from decimal import Decimal
import inspect
import importlib
import pytest
from shopkit.utils.pagination import paginate
from shopkit.tax.calculator import calculate_tax
from shopkit.pricing.discounts import discount_total
from shopkit.pricing.quotes import quote_amount
from shopkit.orders.checkout import checkout_amount
from shopkit.orders.cart import cart_amount
from shopkit.reports.sales import average_sale
from shopkit.utils.collections import unique_ordered
from shopkit.orders.fulfillment import fulfillment_total
from shopkit.users.addresses import billing_address, delivery_address
from shopkit.utils.cli import main

def test_pagination():
    assert paginate(list(range(10)), 1, 3) == [0, 1, 2]
    assert paginate(list(range(10)), 2, 3) == [3, 4, 5]
    assert paginate([], 1, 10) == []
    with pytest.raises(ValueError):
        paginate([], 0, 1)

def test_tax_rounding():
    assert calculate_tax("1.00", "0.005") == Decimal("0.01")
    assert calculate_tax("20", "0.1") == Decimal("2.00")

def test_discount_rename():
    assert discount_total(100, 0.1) == 90
    assert quote_amount(100) == checkout_amount(100) == cart_amount(100) == 90

def test_empty_sales():
    assert average_sale([]) == 0
    assert average_sale([10, 20]) == 15

def test_unique_ordered():
    assert unique_ordered([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert unique_ordered([]) == []

def test_fulfillment():
    assert fulfillment_total(10, 3) == 16

def test_address_refactor():
    assert billing_address("  A   ROAD ") == delivery_address("A ROAD") == "a road"
    for func in (billing_address, delivery_address):
        assert "normalize_address(value)" in inspect.getsource(func)

def test_uppercase_cli():
    assert main(["shop"]) == "shop"
    assert main(["shop", "--uppercase"]) == "SHOP"

MODULES = __MODULES__

@pytest.mark.parametrize("module", MODULES)
def test_domain_records(module):
    m = importlib.import_module("shopkit." + module)
    rows = [{"id": "one", "name": "First", "amount": 2, "active": True}, {"id": "two", "name": "Second", "amount": 4, "active": False}]
    assert m.total_amount(rows) == 6
    assert len(m.active_records(rows)) == 1
    assert m.by_identifier(rows)["one"]["name"] == "First"
    assert m.validate_record(rows[0]) == []
    assert m.describe_record(rows[0]).startswith("one:")
    assert m.merge_records(rows, [{"id": "one", "name": "New"}])[0]["name"] == "New"
    assert m.page_count(11, 5) == 3
'''


def support_module(domain: str, module: str) -> str:
    return f'''"""Synthetic {domain} {module} processing.

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
    return {{str(record["id"]): record for record in records if record.get("id")}}


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
    merged = {{str(row["id"]): dict(row) for row in current}}
    for row in updates:
        identifier = str(row["id"])
        merged.setdefault(identifier, {{}}).update(row)
    return list(merged.values())


def page_count(total: int, size: int) -> int:
    """Return the page count for a result set with positive page size.

    An empty set has zero pages. Negative totals and nonpositive page sizes
    indicate an invalid request and raise ValueError before division.
    """
    if total < 0 or size < 1:
        raise ValueError("invalid pagination bounds")
    return (total + size - 1) // size
'''


def generate(target: Path):
    target.mkdir(parents=True, exist_ok=True)
    (target / "shopkit").mkdir(exist_ok=True)
    (target / "shopkit/__init__.py").write_text(
        '"""Synthetic benchmark project; not production commerce software."""\n', encoding="utf-8"
    )
    modules = []
    for domain, names in DOMAINS.items():
        folder = target / "shopkit" / domain
        folder.mkdir(exist_ok=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        for name in names:
            key = domain + "/" + name
            text = support_module(domain, name) + CORE.get(key, "")
            (folder / (name + ".py")).write_text(text, encoding="utf-8")
            modules.append(domain + "." + name)
    (target / "tests").mkdir(exist_ok=True)
    (target / "tests/test_shopkit.py").write_text(
        TESTS.replace("__MODULES__", repr(modules)), encoding="utf-8"
    )
    (target / "pytest.ini").write_text(
        "[pytest]\npythonpath = .\ntestpaths = tests\n", encoding="utf-8"
    )
    (target / ".gitignore").write_text(
        ".penny/\n.penny-benchmark-sandbox\n__pycache__/\n.pytest_cache/\n", encoding="utf-8"
    )
    (target / "README.md").write_text(
        "# shopkit\n\nDeterministic synthetic Python project for Penny's pre-registered benchmark.\nNot a real commerce package. Run `python -m pytest -q`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target", type=Path, nargs="?", default=Path(__file__).parent / "sandbox_template"
    )
    generate(parser.parse_args().target)
