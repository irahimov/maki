from pathlib import Path

import analyzer

TASKS = Path(__file__).resolve().parent.parent / "eval" / "tasks"
SIMPLE = ["flatten_list", "lru_simple", "roman", "text_slug", "word_count"]
MEDIUM = ["m_bank", "m_calc", "m_csv", "m_intervals", "m_inventory"]


def prompt(name: str) -> str:
    return (TASKS / name / "prompt.txt").read_text().strip()


def test_simple_tasks_are_simple(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "TABLE", tmp_path / "cap.json")
    for name in SIMPLE:
        res = analyzer.analyze(prompt(name))
        assert res["level"] == "simple", name
        assert len(res["subtasks"]) == 1, name
        assert res["subtasks"][0]["tier"] == "local", name


def test_medium_tasks_are_complex(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "TABLE", tmp_path / "cap.json")
    for name in MEDIUM:
        res = analyzer.analyze(prompt(name))
        assert res["level"] == "complex", name
        assert res["needs_architect"] is True, name


def test_route_escalates_after_repeated_failures(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "TABLE", tmp_path / "cap.json")
    for _ in range(5):
        analyzer.record("local", "algorithm", "simple", False)
    assert analyzer.route("algorithm", "simple") == "cloud-mid"


def test_route_stays_local_when_local_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "TABLE", tmp_path / "cap.json")
    for _ in range(5):
        analyzer.record("local", "algorithm", "simple", True)
    assert analyzer.route("algorithm", "simple") == "local"
