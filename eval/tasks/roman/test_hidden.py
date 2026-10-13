import pytest
from roman import to_roman
@pytest.mark.parametrize("n,s", [(1, "I"), (4, "IV"), (9, "IX"), (58, "LVIII"), (1994, "MCMXCIV"), (3999, "MMMCMXCIX")])
def test_values(n, s): assert to_roman(n) == s
@pytest.mark.parametrize("n", [0, -1, 4000])
def test_invalid(n): pytest.raises(ValueError, to_roman, n)
