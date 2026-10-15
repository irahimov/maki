#!/usr/bin/env python3
"""Etiketləri müqayisə edir. İstifadə: compare.py ref=baseline+tokens skip=plan-skip"""
import json
import sys
from pathlib import Path

rows = [
    json.loads(line)
    for line in (Path(__file__).parent / "results.jsonl").read_text().splitlines()
    if line.strip()
]
groups = {}
for arg in sys.argv[1:] or sorted({r["label"] for r in rows}):
    name, _, labs = arg.partition("=")
    groups[name] = (labs or name).split("+")


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


head = f"{'qrup':<10}{'qaçış':>6}{'keçdi':>7}{'orta s':>8}{'cəhd':>6}{'tok in':>9}{'tok out':>9}"
print(head)
for name, labs in groups.items():
    rs = [r for r in rows if r["label"] in labs]
    if not rs:
        print(f"{name:<10} (məlumat yoxdur)")
        continue
    toks = [tuple(map(int, r["tokens"])) for r in rs
            if r.get("tokens") and sum(map(int, r["tokens"])) > 0]
    tries = [r["tries"] for r in rs if isinstance(r.get("tries"), int)]
    tin = f"{mean([t[0] for t in toks]):.0f}" if toks else "-"
    tout = f"{mean([t[1] for t in toks]):.0f}" if toks else "-"
    ok = f"{sum(r['passed'] for r in rs)}/{len(rs)}"
    print(f"{name:<10}{len(rs):>6}{ok:>7}{mean([r['secs'] for r in rs]):>8.0f}"
          f"{mean(tries):>6.1f}{tin:>9}{tout:>9}")

print()
print(f"{'tapşırıq':<14}" + "".join(f"{g:>14}" for g in groups))
for t in sorted({r["task"] for r in rows}):
    line = f"{t:<14}"
    for labs in groups.values():
        rs = [r for r in rows if r["label"] in labs and r["task"] == t]
        cell = (f"{sum(r['passed'] for r in rs)}/{len(rs)} {mean([r['secs'] for r in rs]):.0f}s"
                if rs else "-")
        line += f"{cell:>14}"
    print(line)
