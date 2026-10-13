#!/usr/bin/env python3
"""MAKI task analyzer v0. İstifadə:
  analyzer.py "tapşırıq mətni"
  analyzer.py record <tier> <domain> <level> pass|fail
"""
import json
import re
import sys
from pathlib import Path

TIERS = ["local", "cloud-mid", "cloud-strong"]
TABLE = Path.home() / "maki/capabilities.json"
MIN_RUNS, MIN_RATE = 3, 0.8

# asılılıq sırası ilə (əvvəlkilər əvvəl icra olunur)
DOMAINS = {
    "database": r"\b(sql\w*|postgres\w*|database|schema|migration|orm)\b|verilənlər bazası",
    "backend": r"\b(api|endpoint|server|backend|flask|fastapi|django|rest|crud|auth\w*)\b",
    "algorithm": r"\b(algorithm|alqoritm|sort\w*|search|tree|graph|recursi\w*|cache|evict\w*|parse|convert\w*)\b",
    "cli": r"\b(cli|command|argv|terminal)\b",
    "frontend": r"\b(ui|frontend|react|html|css|page|component|button|form|dashboard|səhifə|düymə)\b",
}
SCOPE = r"\b(app|application|system|platform|project|website|site|service|tətbiq|sistem|sayt)\b"


def features(task: str) -> dict:
    files = set(re.findall(r"\b[\w-]+\.(?:py|js|ts|tsx|html|css|sql)\b", task))
    sigs = re.findall(r"\w+\([^)]*\)\s*->", task)
    return {
        "deliverables": len(files) + len(sigs),
        "constraints": len(re.findall(r"raise|must|never|only|should|error", task, re.I)),
        "domains": [d for d, rx in DOMAINS.items() if re.search(rx, task, re.I)],
        "scope": bool(re.search(SCOPE, task, re.I)),
        "ambiguous": not files and not sigs,
        "words": len(task.split()),
    }


def score(f: dict) -> float:
    s = min(f["deliverables"], 5)
    s += 2.5 * max(len(f["domains"]) - 1, 0)
    s += 0.5 * min(f["constraints"], 6)
    s += 2 * f["ambiguous"] + 3 * f["scope"]
    s += 0.03 * min(f["words"], 100)
    return round(s, 1)


def level(f: dict, s: float) -> str:
    if len(f["domains"]) >= 3 or (f["ambiguous"] and len(f["domains"]) >= 2):
        return "complex"
    return "simple" if s < 5 else "medium" if s < 8 else "complex"


def load() -> dict:
    return json.loads(TABLE.read_text()) if TABLE.exists() else {}


def route(domain: str, lv: str) -> str:
    table = load()
    for tier in TIERS:
        passes, runs = table.get(tier, {}).get(f"{domain}/{lv}", [0, 0])
        rate = (passes + 1) / (runs + 2)  # Laplace hamarlaması
        if runs < MIN_RUNS or rate >= MIN_RATE:
            return tier
    return TIERS[-1]


def record(tier: str, domain: str, lv: str, passed: bool) -> None:
    table = load()
    cell = table.setdefault(tier, {}).setdefault(f"{domain}/{lv}", [0, 0])
    cell[0] += int(passed)
    cell[1] += 1
    TABLE.write_text(json.dumps(table, indent=2))


def analyze(task: str) -> dict:
    f = features(task)
    s = score(f)
    lv = level(f, s)
    doms = f["domains"] or ["general"]
    if lv == "simple":
        doms = doms[:1]
    subtasks = [
        {"id": i, "domain": d, "tier": route(d, lv), "deps": [i - 1] if i else []}
        for i, d in enumerate(doms)
    ]
    return {
        "level": lv,
        "score": s,
        "needs_architect": lv == "complex" or f["scope"],
        "subtasks": subtasks,
    }


if __name__ == "__main__":
    if sys.argv[1:2] == ["record"] and len(sys.argv) == 6:
        _, _, tier, domain, lv, res = sys.argv
        record(tier, domain, lv, res == "pass")
        print("yazıldı:", TABLE)
    else:
        print(json.dumps(analyze(" ".join(sys.argv[1:])), ensure_ascii=False))
