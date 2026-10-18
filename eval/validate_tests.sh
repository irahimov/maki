#!/bin/bash
# Runs every hidden test file against the reference solution in tasks/<name>/ref.
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
for t in "$HERE"/tasks/*/; do
  [ -d "$t/ref" ] || continue
  d=$(mktemp -d)
  cp "$t"/ref/*.py "$d"/
  cp "$t/test_hidden.py" "$d"/
  echo "== $(basename "$t")"
  (cd "$d" && "$PY" -m pytest -q --tb=line -p no:cacheprovider test_hidden.py 2>&1 | tail -n 4)
  rm -rf "$d"
done
