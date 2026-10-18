#!/usr/bin/env python3
"""Uğursuz qaçışları təhlil edir. İstifadə: analyze_fail.py [etiket ...]"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

rows = [
    json.loads(line)
    for line in (Path(__file__).resolve().parent / "results.jsonl").read_text().splitlines()
    if line.strip()
]
labels = sys.argv[1:] or ["m2-skip", "m2-coder"]
cats: Counter = Counter()
errs: Counter = Counter()
ERR = re.compile(r"(\w+Error|DID NOT RAISE)")

for r in rows:
    if r["label"] not in labels or r["passed"]:
        continue
    wd = Path(r["workdir"]) if r.get("workdir") else None
    head = f"{r['label']:<9}{r['task']:<13}{r['secs']:>6.0f}s"
    if r.get("agent_rc") == 124:
        cats["TIMEOUT"] += 1
        log = wd / ".maki-errors.txt" if wd else None
        n = log.read_text().count("--- cəhd") if log and log.exists() else 0
        print(f"{head} TIMEOUT, bitmiş coder çağırışı: {n}")
        continue
    believed = "Commit olundu" in r.get("agent_tail", "")
    key = "agent 'keçdi' dedi, gizli test düşdü" if believed else "agent 3 cəhddə həll edə bilmədi"
    cats[key] += 1
    if not wd or not wd.exists():
        print(f"{head} (qovluq yoxdur)")
        continue
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rf", "--tb=no", "-p", "no:cacheprovider",
         f"test_hidden_{r['task']}.py"],
        cwd=wd, capture_output=True, text=True, timeout=120,
    )
    out = p.stdout
    failed = re.findall(r"^FAILED \S+?::(\S+)(?: - (.*))?$", out, re.M)
    summ = out.strip().splitlines()[-1] if out.strip() else "?"
    if failed:
        for _, msg in failed:
            m = ERR.search(msg or "")
            errs[m.group(1) if m else "digər"] += 1
        names = ", ".join(sorted({n.split("[")[0] for n, _ in failed})[:3])
    else:
        for msg in re.findall(r"^ERROR \S+ - (.*)$", out, re.M):
            m = ERR.search(msg)
            errs[m.group(1) if m else "digər"] += 1
        names = "toplama/import xətası"
    print(f"{head} {'agent+' if believed else 'agent-'} {summ} | {names}")
    src = wd / "inventory.py"
    if r["task"] == "m_inventory" and src.exists() and re.search(r"self\.stock\s*=", src.read_text()):
        print("           ^ self.stock atributu stock() metodunu kölgələyir")

print("\n=== kateqoriyalar")
for k, v in cats.most_common():
    print(f"{v:>3}  {k}")
print("=== gizli testlərdə xəta növləri")
for k, v in errs.most_common(8):
    print(f"{v:>3}  {k}")
