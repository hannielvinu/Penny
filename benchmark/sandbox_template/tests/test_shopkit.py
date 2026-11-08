"""Synthetic shopkit acceptance tests, committed before measurements."""
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

MODULES = ['catalog.products', 'catalog.inventory', 'catalog.categories', 'catalog.search', 'catalog.variants', 'pricing.discounts', 'pricing.currency', 'pricing.totals', 'pricing.promotions', 'pricing.quotes', 'tax.calculator', 'tax.rates', 'tax.regions', 'tax.exemptions', 'tax.invoices', 'shipping.rates', 'shipping.parcels', 'shipping.zones', 'shipping.tracking', 'shipping.labels', 'orders.checkout', 'orders.fulfillment', 'orders.returns', 'orders.payments', 'orders.cart', 'users.profiles', 'users.addresses', 'users.preferences', 'users.accounts', 'users.sessions', 'reports.sales', 'reports.inventory', 'reports.customers', 'reports.daily', 'reports.export', 'utils.pagination', 'utils.validation', 'utils.collections', 'utils.dates', 'utils.cli']

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
