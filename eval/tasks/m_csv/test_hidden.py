import pytest
from csv_tools import parse_csv
from stats import column_stats


def test_parse_basic():
    assert parse_csv("a,b\n1,2\n3,4") == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_parse_quotes():
    assert parse_csv('name,note\nx,"hello, world"') == [{"name": "x", "note": "hello, world"}]


def test_parse_whitespace_blank():
    assert parse_csv("\n a , b \n\n 1 , 2 \n\n") == [{"a": "1", "b": "2"}]


def test_parse_header_only():
    assert parse_csv("a,b") == []


def test_parse_bad_row():
    with pytest.raises(ValueError):
        parse_csv("a,b\n1,2,3")


def test_stats_basic():
    rows = [{"v": "1"}, {"v": "2"}, {"v": "6"}]
    assert column_stats(rows, "v") == {"count": 3, "mean": 3.0, "min": 1.0, "max": 6.0}


def test_stats_ignores_bad():
    rows = [{"v": "1.5"}, {"v": ""}, {"v": "abc"}, {"v": "2.5"}]
    assert column_stats(rows, "v") == {"count": 2, "mean": 2.0, "min": 1.5, "max": 2.5}


def test_stats_missing_column():
    with pytest.raises(KeyError):
        column_stats([{"a": "1"}], "b")


def test_stats_no_numeric():
    with pytest.raises(ValueError):
        column_stats([{"v": "x"}, {"v": ""}], "v")


def test_stats_empty_rows():
    with pytest.raises(KeyError):
        column_stats([], "v")
