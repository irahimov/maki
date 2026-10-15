#!/bin/bash
echo "== proseslər =="
pgrep -af "run_eval|crew.py" | cut -c1-90 || echo "(işləyən yoxdur)"
pgrep -f "run_eval|crew.py" >/dev/null || echo "(işləyən yoxdur)"
echo "== GPU model =="
ollama ps | tail -n +2
echo "== nəticələr (etiket: ${1:-ən sonuncu}) =="
~/.maki-env/bin/python - "$1" <<'PY'
import json, sys
from pathlib import Path
rows = [json.loads(l) for l in (Path.home()/"maki/eval/results.jsonl").read_text().splitlines() if l.strip()]
label = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else rows[-1]["label"]
rows = [r for r in rows if r["label"] == label]
ti = to = 0
for r in rows:
    i, o = map(int, r.get("tokens", (0, 0)))
    ti += i; to += o
    print(f"{r['task']:<14}{'PASS' if r['passed'] else 'FAIL':<5}{r['secs']:>7}s cəhd={r.get('tries','?')} in={i} out={o}")
print(f"[{label}] {sum(r['passed'] for r in rows)}/{len(rows)} keçdi | token in={ti} out={to}")
PY
