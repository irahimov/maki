import pytest
from intervals import merge_intervals
from schedule import free_slots


def test_merge_basic():
    assert merge_intervals([(1, 3), (2, 6), (8, 10)]) == [(1, 6), (8, 10)]


def test_merge_touching():
    assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]


def test_merge_unsorted():
    assert merge_intervals([(8, 10), (1, 3), (2, 4)]) == [(1, 4), (8, 10)]


def test_merge_contained():
    assert merge_intervals([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]


def test_merge_empty():
    assert merge_intervals([]) == []


def test_merge_no_mutation():
    data = [(5, 6), (1, 2)]
    merge_intervals(data)
    assert data == [(5, 6), (1, 2)]


def test_merge_invalid():
    with pytest.raises(ValueError):
        merge_intervals([(3, 1)])


def test_free_basic():
    assert free_slots([(9, 10), (12, 13)], 8, 17) == [(8, 9), (10, 12), (13, 17)]


def test_free_overlapping_busy():
    assert free_slots([(9, 12), (10, 11)], 8, 14) == [(8, 9), (12, 14)]


def test_free_outside_day():
    assert free_slots([(0, 9), (16, 30)], 8, 17) == [(9, 16)]


def test_free_all_busy():
    assert free_slots([(0, 20)], 8, 17) == []


def test_free_no_busy():
    assert free_slots([], 8, 17) == [(8, 17)]


def test_free_touching_edges():
    assert free_slots([(8, 10), (10, 17)], 8, 17) == []


def test_free_invalid_day():
    with pytest.raises(ValueError):
        free_slots([], 10, 10)
