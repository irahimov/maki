#!/bin/bash
echo "== proseslər =="
pgrep -af "run_eval|crew.py" || echo "(işləyən yoxdur)"
echo "== GPU model =="
ollama ps | tail -n +2
echo "== nəticələr =="
~/.maki-env/bin/python - <<'PY'
import json
from pathlib import Path
rows = [json.loads(l) for l in (Path.home()/"maki/eval/results.jsonl").read_text().splitlines()]
rows = [r for r in rows if r["label"] == "baseline"]
for r in rows:
    print(f"{r['task']:<14} {'PASS' if r['passed'] else 'FAIL':<5} {r['secs']:>6}s cəhd={r.get('tries','?')}")
print(f"{sum(r['passed'] for r in rows)}/{len(rows)} keçdi")
PY
