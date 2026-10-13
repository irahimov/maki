from text_slug import slugify
def test_basic(): assert slugify("Hello, World!") == "hello-world"
def test_spaces(): assert slugify(" " * 2 + "a" + " " * 3 + "b" + " " * 2) == "a-b"
def test_empty(): assert slugify("") == ""
def test_edges(): assert slugify("---x---") == "x"
def test_underscore_digits(): assert slugify("A_B 42") == "a-b-42"
