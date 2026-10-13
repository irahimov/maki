from word_count import word_count
def test_basic(): assert word_count("The the cat.") == {"the": 2, "cat": 1}
def test_empty(): assert word_count("") == {}
def test_digits(): assert word_count("a1 B2 a1") == {"a1": 2, "b2": 1}
