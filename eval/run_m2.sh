#!/bin/bash
exec 9>/tmp/maki-eval.lock
flock -n 9 || { echo "BASQA EVAL ISLEYIR"; exit 1; }
cd ~/maki/eval
PY=~/.maki-env/bin/python
T="--task m_inventory --task m_bank --task m_calc --task m_intervals --task m_csv"
MAKI_PLAN=skip $PY run_eval.py --label m2-skip --repeat 2 $T
MAKI_PLAN=coder $PY run_eval.py --label m2-coder --repeat 2 $T
