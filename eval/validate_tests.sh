#!/bin/bash
PY=~/.maki-env/bin/python
for t in "$HOME"/maki/eval/tasks/*/; do
  [ -d "$t/ref" ] || continue
  d=$(mktemp -d)
  cp "$t"/ref/*.py "$d"/
  cp "$t/test_hidden.py" "$d"/
  echo "== $(basename "$t")"
  (cd "$d" && $PY -m pytest -q --tb=line -p no:cacheprovider test_hidden.py 2>&1 | tail -n 4)
  rm -rf "$d"
done
