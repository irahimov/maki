#!/usr/bin/env python3
"""MAKI ardıcıl pipeline: planner -> coder -> yoxlama -> reviewer."""
import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import ollama
from langgraph.graph import END, StateGraph

PLANNER = "qwen3:4b"
CODER = "qwen-coder-8k"
WORK = Path.cwd().resolve()
SKDIR = Path.home() / "maki/skills"
PLANNER_RULES = (SKDIR / "planner.md").read_text()
REVIEWER_RULES = (SKDIR / "reviewer.md").read_text()
FENCE = "`" * 3
CODER_RULES = (
    (SKDIR / "coder.md").read_text()
    + "\nOutput EVERY file as a fenced code block whose FIRST line is "
    "'# file: filename.py'. Include tests as test_*.py. No other prose."
)
FORMAT_HINT = (
    "\n\nREQUIRED OUTPUT FORMAT (example, fully implemented):\n"
    + FENCE
    + "python\n# file: fibonacci.py\ndef fibonacci(n: int) -> int:\n"
    "    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n"
    "    return a\n" + FENCE + "\n"
    + FENCE
    + "python\n# file: test_fibonacci.py\nfrom fibonacci import fibonacci\n\n\n"
    "def test_basic():\n    assert fibonacci(5) == 5\n" + FENCE
)
BLOCK = re.compile(FENCE + r"([\w+-]*)[ \t]*\n(.*?)" + FENCE, re.S)
PATH_RE = re.compile(r"([\w][\w./-]*\.(?:py|js|ts|html|css|json|md|txt|toml|sh))", re.I)
STATS = {"in": 0, "out": 0, "calls": 0}


class S(TypedDict, total=False):
    task: str
    plan: str
    code: str
    errors: str
    tries: int
    reviewed: int
    good: str
    ctx: str


def ask(model: str, system: str, prompt: str, ctx: int = 8192,
        think: bool | None = None) -> str:
    extra = {} if think is None else {"think": think}
    r = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        options={"num_ctx": ctx, "temperature": 0.2, "num_gpu": 99},
        keep_alive=0,
        **extra,
    )
    STATS["in"] += getattr(r, "prompt_eval_count", 0) or 0
    STATS["out"] += getattr(r, "eval_count", 0) or 0
    STATS["calls"] += 1
    text = r["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def project_context(task: str) -> str:
    if os.environ.get("MAKI_RAG") == "0":
        return ""
    try:
        sys.path.insert(0, str(Path.home() / "maki"))
        import rag

        rag.index()
        hits = [(i, d) for i, d in rag.search(task, 8) if not i.startswith("test_")]
    except Exception as e:
        print(f"ℹ RAG işləmədi: {e}")
        return ""
    return "\n\n".join(f"{i}\n{d[:700]}" for i, d in hits[:3])


def plan(s: S) -> S:
    print("▶ planner işləyir...")
    existing = sorted(p.name for p in WORK.glob("*.py") if not p.name.startswith("test_"))
    prompt = s["task"]
    if existing:
        prompt += "\n\nExisting modules (reuse, do not duplicate): " + ", ".join(existing)
    mode = os.environ.get("MAKI_PLAN", "auto")
    if mode == "auto":
        try:
            sys.path.insert(0, str(Path.home() / "maki"))
            import analyzer

            res = analyzer.analyze(s["task"])
            mode = "skip" if res["level"] == "simple" else "qwen3"
            print(f"  analyzer: {res['level']} (bal {res['score']})")
        except Exception as e:
            print(f"  analyzer işləmədi ({e}), planner istifadə olunur")
            mode = "qwen3"
    print(f"  plan rejimi: {mode}")
    if mode == "skip":
        plan_text = "(no separate plan: follow the task description exactly)"
    elif mode == "coder":
        plan_text = ask(CODER, PLANNER_RULES, prompt, 6144)
    else:
        plan_text = ask(PLANNER, PLANNER_RULES, prompt, 6144, think=False)
    return {"plan": plan_text, "ctx": project_context(s["task"])}


def code(s: S) -> S:
    n = s.get("tries", 0) + 1
    print(f"▶ coder işləyir (cəhd {n})...")
    prompt = f"Task: {s['task']}\nPlan:\n{s['plan']}"
    if s.get("ctx"):
        prompt += (
            "\n\nRelated existing code (import and reuse it; "
            "do NOT rewrite these files):\n" + s["ctx"]
        )
    if s.get("errors"):
        prompt += f"\n\nPrevious code:\n{s['code']}\n\nFix these errors:\n{s['errors']}"
    out = ask(CODER, CODER_RULES, prompt + FORMAT_HINT)
    (WORK / ".maki-last.txt").write_text(out)
    with open(WORK / ".maki-errors.txt", "a") as fh:
        fh.write(f"--- cəhd {n}, əvvəlki xətalar ---\n{s.get('errors', '')}\n")
    return {"code": out, "tries": n}


def guess_path(pre: str, lang: str, body: str, idx: int) -> tuple[str, str]:
    first, _, rest = body.partition("\n")
    m = PATH_RE.search(first) if first.lstrip().startswith(("#", "//")) else None
    if m:
        return m.group(1), rest
    lines = [x for x in pre.strip().splitlines() if x.strip()]
    m = PATH_RE.search(lines[-1]) if lines else None
    if m:
        return m.group(1), body
    if lang in ("", "python", "py"):
        return (f"test_main_{idx}.py" if "def test_" in body else f"main_{idx}.py"), body
    return "", body


def write_files(text: str) -> list[Path]:
    files: list[Path] = []
    prev = 0
    for i, m in enumerate(BLOCK.finditer(text)):
        pre, lang, body = text[prev:m.start()], m.group(1).lower(), m.group(2)
        prev = m.end()
        rel, body = guess_path(pre, lang, body, i)
        if not rel:
            continue
        path = WORK / Path(rel).name  # düz quruluş: alt qovluq yoxdur
        path.write_text(body)
        files.append(path)
    return files


def find_stubs(files: list[Path]) -> str:
    bad: list[str] = []
    for f in files:
        if f.suffix != ".py" or f.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue  # ruff özü tutacaq
        for n in ast.walk(tree):
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [
                b for b in n.body
                if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))
            ]
            if not body or all(isinstance(b, ast.Pass) for b in body):
                bad.append(f"{f.name}: {n.name}() is a stub, implement it fully")
    return "\n".join(bad)


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=WORK)
    except subprocess.TimeoutExpired:
        return 1, "Timeout (180s)"
    return p.returncode, (p.stdout + p.stderr).strip()


def check(s: S) -> S:
    files = write_files(s["code"])
    if not files:
        return {"errors": "No files found. Start each code block with '# file: name.py'."}
    errs: list[str] = []
    stubs = find_stubs(files)
    if stubs:
        errs.append(stubs)
    py = [str(f) for f in files if f.suffix == ".py"]
    if py:
        run([sys.executable, "-m", "ruff", "format", *py])
        run([sys.executable, "-m", "ruff", "check", "--fix", "-q", *py])
        rc, out = run([sys.executable, "-m", "ruff", "check", *py])
        if rc:
            errs.append(out)
    tests = [str(f) for f in files if f.name.startswith("test_")]
    if not tests:
        errs.append("Missing test file: write test_*.py")
    elif not errs:
        full = os.environ.get("MAKI_FULLFAIL") == "1"
        flags = ["--tb=short"] if full else ["-x"]
        rc, out = run([sys.executable, "-m", "pytest", "-q", *flags, *tests])
        if rc:
            errs.append(out[-(3500 if full else 2000):])
    print("✅ yoxlama keçdi" if not errs else "⚠ xəta tapıldı, düzəldilir")
    if errs:
        return {"errors": "\n".join(errs)}
    return {"errors": "", "tries": 0, "good": s["code"]}


def review(s: S) -> S:
    if os.environ.get("MAKI_REVIEW") != "1":
        return {"reviewed": 1, "errors": ""}
    print("▶ reviewer işləyir...")
    out = ask(CODER, REVIEWER_RULES, f"Task: {s['task']}\n\nCode:\n{s['code']}")
    if out.strip().upper().startswith("LGTM"):
        print("✅ reviewer: LGTM")
        return {"reviewed": 1, "errors": ""}
    names = re.findall(r"def (\w+)", s["code"])
    if not any(n in out for n in names):
        print("ℹ reviewer ümumi cavab verdi (funksiya adı yoxdur), nəzərə alınmır")
        return {"reviewed": 1, "errors": ""}
    print("⚠ reviewer qeydləri:\n" + out[:800])
    msg = (
        "Code review issues. Fix them. Keep ALL function names and signatures "
        "unchanged and keep all tests passing:\n" + out
    )
    return {"reviewed": 1, "errors": msg}


def route(s: S) -> str:
    if s["errors"]:
        return END if s["tries"] >= 3 else "code"
    return END if s.get("reviewed") else "review"


def after_review(s: S) -> str:
    return "code" if s["errors"] else END


g = StateGraph(S)
g.add_node("plan", plan)
g.add_node("code", code)
g.add_node("check", check)
g.add_node("review", review)
g.set_entry_point("plan")
g.add_edge("plan", "code")
g.add_edge("code", "check")
g.add_conditional_edges("check", route)
g.add_conditional_edges("review", after_review)
app = g.compile()

if __name__ == "__main__":
    final = app.invoke({"task": " ".join(sys.argv[1:])})
    print(f"TOKENS in={STATS['in']} out={STATS['out']} calls={STATS['calls']}")
    if final["errors"]:
        if final.get("good"):
            write_files(final["good"])
            print("\n↩ Reviewer düzəlişi kodu pozdu, keçən işləyən versiya bərpa edildi.")
        else:
            print("\n❌ 3 cəhddən sonra xəta qaldı:\n" + final["errors"])
            sys.exit(1)
    print("\n🎉 Hazırdır. `git diff` / `git status` ilə bax.")
