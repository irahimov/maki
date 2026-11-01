#!/bin/bash
# Runs every hidden test file against the reference solution in tasks/<name>/ref.
# Exit code 0 only if every task's reference passes its hidden tests.
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
set -o pipefail
fail=0
for t in "$HERE"/tasks/*/; do
  [ -d "$t/ref" ] || continue
  d=$(mktemp -d)
  cp "$t"/ref/*.py "$d"/
  cp "$t/test_hidden.py" "$d"/
  echo "== $(basename "$t")"
  if ! (cd "$d" && "$PY" -m pytest -q --tb=line -p no:cacheprovider test_hidden.py 2>&1 | tail -n 4); then
    fail=1
  fi
  rm -rf "$d"
done
exit $fail
