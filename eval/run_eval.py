#!/usr/bin/env python3
"""Hər tapşırıq üçün təmiz git repo yaradır, agent işlədir, gizli testi keçirir."""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EVAL = Path(__file__).resolve().parent
TASKS = EVAL / "tasks"
RESULTS = EVAL / "results.jsonl"
AGENT_CMD = os.environ.get("MAKI_EVAL_CMD", "ai-env agent")


def sh(cmd, cwd, env=None, timeout=900):
    t = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                           text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout + p.stderr, time.time() - t
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT", time.time() - t


def run_task(name, label):
    tdir = TASKS / name
    prompt = (tdir / "prompt.txt").read_text().strip()
    work = Path(tempfile.mkdtemp(prefix=f"eval-{name}-"))
    sh(["git", "init", "-q", "-b", "main"], work)
    (work / ".gitignore").write_text("__pycache__\n.pytest_cache\n.ruff_cache\n.maki-*\n")
    sh(["git", "add", "-A"], work)
    sh(["git", "-c", "user.name=eval", "-c", "user.email=eval@local",
        "commit", "-qm", "init"], work)

    env = {**os.environ, "MAKI_RAG": "0"}
    a_rc, a_out, secs = sh([*shlex.split(AGENT_CMD), prompt], work, env=env)

    shutil.copy(tdir / "test_hidden.py", work / f"test_hidden_{name}.py")
    t_rc, t_out, _ = sh([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         f"test_hidden_{name}.py"], work)
    passed = t_rc == 0
    rec = {"label": label, "task": name, "passed": passed, "agent_rc": a_rc,
           "secs": round(secs, 1), "tries": a_out.count("coder işləyir"),
           "tokens": (re.findall(r"TOKENS in=(\d+) out=(\d+)", a_out) or [("0", "0")])[-1],
           "workdir": str(work),
           "agent_tail": a_out[-400:], "test_tail": t_out[-400:]}
    if passed:
        shutil.rmtree(work, ignore_errors=True)
        rec["workdir"] = None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--task", action="append")
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()

    names = args.task or sorted(p.name for p in TASKS.iterdir() if p.is_dir())
    recs = []
    for n in names * args.repeat:
        print(f"[{args.label}] {n} ...", flush=True)
        rec = run_task(n, args.label)
        recs.append(rec)
        with RESULTS.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"   -> {'PASS' if rec['passed'] else 'FAIL'} ({rec['secs']}s)", flush=True)

    ok = sum(r["passed"] for r in recs)
    avg = sum(r["secs"] for r in recs) / len(recs)
    print(f"\n[{args.label}] {ok}/{len(recs)} keçdi, orta {avg:.0f}s")


if __name__ == "__main__":
    main()
