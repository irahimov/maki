#!/bin/bash
OUT=~/maki-report.txt
PY=~/.maki-env/bin/python
export PYTHONDONTWRITEBYTECODE=1
sec() { echo; echo "=================== $1 ==================="; }
{
echo "MAKI REPORT $(date '+%F %T')"

sec "1. SİSTEM"
uname -sr; grep PRETTY_NAME /etc/os-release
grep -qi microsoft /proc/version && echo "WSL: bəli" || echo "WSL: xeyr"
free -h | head -2
df -h ~ | tail -1
$PY --version; ~/.ai-env/bin/python --version; python3 --version

sec "2. GPU"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free --format=csv

sec "3. OLLAMA"
ollama --version 2>&1 | tail -1
curl -s localhost:11434; echo
ollama list
echo "-- yüklü modellər:"; ollama ps
echo "-- env:"; cat ~/.ollama-env
echo "-- coder.Modelfile:"; cat ~/maki/modelfiles/coder.Modelfile

sec "4. PAKETLƏR"
$PY -m pip list --format=freeze 2>/dev/null | grep -Ei '^(langgraph|ollama|chromadb|fastmcp|ruff|pytest|litellm|pydantic)=='
~/.local/bin/aider --version 2>&1 | tail -1

sec "5. ~/maki FAYLLARI"
ls -la ~/maki ~/maki/skills ~/maki/eval ~/maki/eval/tasks 2>&1
wc -l ~/maki/*.py ~/maki/eval/*.py 2>&1
echo "-- sintaksis:"
for f in ~/maki/*.py ~/maki/eval/*.py; do
  $PY -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$f" && echo "OK   $f" || echo "XƏTA $f"
done
bash -n ~/.local/bin/ai-env && echo "OK   ai-env"
bash -n ~/.local/bin/maki-aider && echo "OK   maki-aider"

sec "6. ai-env ƏMRLƏRİ"
grep -E '^    [a-z|*]+\)' ~/.local/bin/ai-env | tr -d ' ' | tr '\n' ' '; echo

sec "7. SKILL QAYDALARI"
for f in coder planner reviewer; do echo "--- $f.md"; cat ~/maki/skills/$f.md 2>&1; done

sec "8. AIDER"
cat ~/.aider.conf.yml 2>&1
cat ~/.local/bin/maki-aider 2>&1

sec "9. EVAL NƏTİCƏLƏRİ"
$PY - <<'PY'
import json
from collections import defaultdict
from pathlib import Path

p = Path.home() / "maki/eval/results.jsonl"
if not p.exists():
    raise SystemExit("results.jsonl yoxdur")
by = defaultdict(list)
for line in p.read_text().splitlines():
    if line.strip():
        r = json.loads(line)
        by[r["label"]].append(r)
for lab, rs in by.items():
    print(f"[{lab}] {sum(r['passed'] for r in rs)}/{len(rs)}")
    for r in rs:
        print(f"   {r['task']:<14}{'PASS' if r['passed'] else 'FAIL':<5}{r['secs']:>7}s cəhd={r.get('tries', '?')} {r.get('workdir') or ''}")
PY

sec "10. ANALYZER"
ls -la ~/maki/analyzer.py ~/maki/capabilities.json 2>&1
if [ -f ~/maki/analyzer.py ]; then
  tasks=(
    "Create roman.py with function to_roman(n: int) -> str converting 1..3999 to a Roman numeral; raise ValueError for values outside 1..3999. Include tests."
    "Create lru_simple.py with class LRUCache(capacity: int): put(key, value), get(key). capacity <= 0 raises ValueError. Include tests."
    "Build a notes app with Flask backend API, SQLite database and React frontend, with auth and tests"
    "make a todo app"
  )
  for t in "${tasks[@]}"; do echo "> ${t:0:55}"; $PY ~/maki/analyzer.py "$t" 2>&1; done
fi

sec "11. RAG"
ls ~/.maki-rag 2>&1; du -sh ~/.maki-rag 2>/dev/null

sec "12. GIT"
for d in ~/maki-test ~/maki-projects/playground ~/maki; do
  echo "--- $d"
  if git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "branch: $(git -C "$d" branch --show-current)"
    echo "status:"; git -C "$d" status --short | head -10
    echo "branches:"; git -C "$d" branch | head -10
    git -C "$d" log --oneline | head -5
  else
    echo "(git repo deyil)"
  fi
done
echo "-- maki-test testləri:"
(cd ~/maki-test && $PY -m pytest -q -p no:cacheprovider 2>&1 | tail -n 3)

sec "13. OPEN WEBUI"
pgrep -f open-webui >/dev/null && echo "işləyir" || echo "işləmir"
test -x ~/.ai-env/bin/open-webui && echo "quraşdırılıb" || echo "tapılmadı"
ls -la ~/maki/openwebui_pipe.py 2>&1

sec "14. SABİT YOLLAR (portativlik)"
grep -n "/home/makish" ~/maki/*.py ~/maki/eval/*.py 2>/dev/null | cut -c1-110

sec "15. BACKUP-LAR"
ls ~/maki-backup 2>&1 | head -40
} 2>&1 | sed -E 's/((api[_-]?key|token|secret|password)[=: ]+)[^ ]+/\1***/Ig' | tee "$OUT"
echo; echo "Hazır: $OUT"
