import pytest
from inventory import Inventory
from report import format_report


def make():
    inv = Inventory()
    inv.add("b", 5)
    inv.add("a", 2)
    return inv


def test_stock_unknown():
    assert Inventory().stock("x") == 0


def test_add_accumulates():
    inv = make()
    inv.add("a", 3)
    assert inv.stock("a") == 5


def test_add_invalid():
    with pytest.raises(ValueError):
        Inventory().add("a", 0)


def test_remove_ok():
    inv = make()
    inv.remove("b", 2)
    assert inv.stock("b") == 3


@pytest.mark.parametrize("sku,qty", [("a", 3), ("zzz", 1), ("a", 0), ("a", -1)])
def test_remove_invalid_keeps_state(sku, qty):
    inv = make()
    with pytest.raises(ValueError):
        inv.remove(sku, qty)
    assert inv.stock("a") == 2 and inv.stock("b") == 5


def test_low_stock():
    inv = make()
    assert inv.low_stock(5) == ["a"]
    assert inv.low_stock(6) == ["a", "b"]
    assert inv.low_stock(2) == []


def test_low_stock_includes_zero():
    inv = make()
    inv.remove("a", 2)
    assert inv.low_stock(1) == ["a"]


def test_report():
    assert format_report(make()) == "a: 2\nb: 5"


def test_report_empty():
    assert format_report(Inventory()) == "(empty)"


def test_report_skips_zero():
    inv = make()
    inv.remove("a", 2)
    assert format_report(inv) == "b: 5"


def test_report_all_zero():
    inv = Inventory()
    inv.add("a", 1)
    inv.remove("a", 1)
    assert format_report(inv) == "(empty)"
