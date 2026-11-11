#!/bin/sh
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
mkdir -p output
python3 -u run_experiments.py 6 2>&1 | tee output/run_all.log
