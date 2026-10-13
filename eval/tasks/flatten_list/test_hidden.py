from flatten_list import flatten
def test_nested(): assert flatten([1, [2, [3, [4]]], 5]) == [1, 2, 3, 4, 5]
def test_empty(): assert flatten([]) == []
def test_strings(): assert flatten(["ab", ["cd"]]) == ["ab", "cd"]
def test_empty_nested(): assert flatten([[], [[]]]) == []
