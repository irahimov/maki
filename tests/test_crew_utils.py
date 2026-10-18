import crew

FENCE = "`" * 3


def test_find_stubs_detects_pass_and_docstring_only(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text('def a():\n    pass\n\ndef b():\n    """doc"""\n\ndef c():\n    return 1\n')
    out = crew.find_stubs([f])
    assert "a() is a stub" in out
    assert "b() is a stub" in out
    assert "c() is a stub" not in out


def test_find_stubs_skips_test_files(tmp_path):
    f = tmp_path / "test_x.py"
    f.write_text("def t():\n    pass\n")
    assert crew.find_stubs([f]) == ""


def test_write_files_parses_header_block(tmp_path, monkeypatch):
    monkeypatch.setattr(crew, "WORK", tmp_path)
    text = f"{FENCE}python\n# file: a.py\nx = 1\n{FENCE}\n"
    files = crew.write_files(text)
    assert files == [tmp_path / "a.py"]
    assert (tmp_path / "a.py").read_text() == "x = 1\n"


def test_write_files_stays_inside_workdir(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(crew, "WORK", work)
    text = f"{FENCE}python\n# file: ../evil.py\nx = 1\n{FENCE}\n"
    files = crew.write_files(text)
    assert [p.parent for p in files] == [work]
    assert not (tmp_path / "evil.py").exists()
