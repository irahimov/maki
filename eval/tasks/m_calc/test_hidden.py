import pytest
from calc import evaluate
from tokenizer import tokenize


def test_tokenize():
    assert tokenize(" 12+3.5*(2 - 1)") == ["12", "+", "3.5", "*", "(", "2", "-", "1", ")"]


def test_tokenize_empty():
    assert tokenize("   ") == []


def test_tokenize_bad():
    with pytest.raises(ValueError):
        tokenize("2 $ 3")


@pytest.mark.parametrize(
    "expr,val",
    [
        ("1+2*3", 7),
        ("(1+2)*3", 9),
        ("10/4", 2.5),
        ("2-3-4", -5),
        ("8/4/2", 1),
        ("-3 + 2", -1),
        ("2 * -(1 + 1)", -4),
        ("((2))", 2),
        ("1.5+1.5", 3),
    ],
)
def test_values(expr, val):
    assert evaluate(expr) == pytest.approx(val)


def test_zero_div():
    with pytest.raises(ZeroDivisionError):
        evaluate("1/(2-2)")


@pytest.mark.parametrize("expr", ["", "(1+2", "1+2)", "1*/2", "1+", "*2", "2 3"])
def test_malformed(expr):
    with pytest.raises(ValueError):
        evaluate(expr)
