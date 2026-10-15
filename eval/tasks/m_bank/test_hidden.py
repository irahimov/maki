import pytest
from account import Account
from bank import transfer


def test_deposit_withdraw():
    a = Account("x", 10.0)
    a.deposit(5)
    a.withdraw(3)
    assert a.balance == 12
    assert a.history == [("deposit", 5), ("withdraw", 3)]


def test_default_balance():
    assert Account("x").balance == 0


def test_negative_initial():
    with pytest.raises(ValueError):
        Account("x", -1)


@pytest.mark.parametrize("amt", [0, -5])
def test_invalid_amount(amt):
    a = Account("x", 10)
    with pytest.raises(ValueError):
        a.deposit(amt)
    with pytest.raises(ValueError):
        a.withdraw(amt)
    assert a.balance == 10 and a.history == []


def test_overdraw():
    a = Account("x", 10)
    with pytest.raises(ValueError):
        a.withdraw(10.01)
    assert a.balance == 10 and a.history == []


def test_withdraw_all():
    a = Account("x", 10)
    a.withdraw(10)
    assert a.balance == 0


def test_transfer():
    a, b = Account("a", 10), Account("b", 1)
    transfer(a, b, 4)
    assert (a.balance, b.balance) == (6, 5)
    assert a.history == [("withdraw", 4)]
    assert b.history == [("deposit", 4)]


def test_transfer_insufficient():
    a, b = Account("a", 1), Account("b", 1)
    with pytest.raises(ValueError):
        transfer(a, b, 5)
    assert (a.balance, b.balance) == (1, 1)
    assert a.history == [] and b.history == []


def test_transfer_invalid_amount():
    a, b = Account("a", 5), Account("b", 1)
    with pytest.raises(ValueError):
        transfer(a, b, 0)
    assert a.history == [] and b.history == []


def test_transfer_same_account():
    a = Account("a", 5)
    with pytest.raises(ValueError):
        transfer(a, a, 1)
    assert a.balance == 5 and a.history == []
