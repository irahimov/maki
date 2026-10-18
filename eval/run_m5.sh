#!/bin/bash
exec 9>/tmp/maki-eval.lock
flock -n 9 || { echo "BASQA EVAL ISLEYIR"; exit 1; }
cd ~/maki/eval
T="--task m_inventory --task m_bank --task m_calc --task m_intervals --task m_csv"
MAKI_PLAN=skip MAKI_FULLFAIL=1 ~/.maki-env/bin/python run_eval.py --label m5-fullcap --repeat 2 $T
