#!/usr/bin/env python3
"""Deterministik yoxlama: ruff + pyright + pytest/coverage. Çıxış: JSON."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, cwd, env=None, timeout=180):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def verify(project, min_cov=80):
    root = Path(project).resolve()
    srcs = sorted(p.name for p in root.glob("*.py") if not p.name.startswith("test_"))
    result = {"sources": srcs}

    rc, out = run([sys.executable, "-m", "ruff", "check", "."], root)
    result["ruff_ok"] = rc == 0
    result["ruff_out"] = out[-1500:]

    pyright_errors = []
    if srcs:
        rc, out = run([sys.executable, "-m", "pyright", "--outputjson", *srcs], root)
        try:
            diags = json.loads(out)["generalDiagnostics"]
            pyright_errors = [
                f'{Path(d["file"]).name}:{d["range"]["start"]["line"] + 1}: {d["message"]}'
                for d in diags if d["severity"] == "error"
            ]
        except (json.JSONDecodeError, KeyError):
            pyright_errors = [f"pyright çıxışı oxunmadı: {out[-300:]}"]
    result["pyright_errors"] = pyright_errors

    tmp = Path(tempfile.mkdtemp())
    env = {**os.environ, "COVERAGE_FILE": str(tmp / ".coverage")}
    covjson = tmp / "cov.json"
    rc, out = run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--cov=.", f"--cov-report=json:{covjson}"],
        root, env=env,
    )
    result["tests_ok"] = rc == 0
    result["tests_out"] = out[-1500:]

    coverage = {}
    if covjson.exists():
        files = json.loads(covjson.read_text())["files"]
        for name in srcs:
            info = files.get(name)
            coverage[name] = round(info["summary"]["percent_covered"], 1) if info else 0.0
    result["coverage"] = coverage
    result["low_coverage"] = [n for n, c in coverage.items() if c < min_cov]

    result["ok"] = (result["ruff_ok"] and not pyright_errors
                    and result["tests_ok"] and not result["low_coverage"])
    return result


if __name__ == "__main__":
    print(json.dumps(verify(sys.argv[1] if len(sys.argv) > 1 else "."),
                     indent=2, ensure_ascii=False))
