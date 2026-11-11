@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if not exist output mkdir output
python -u run_experiments.py 6 > output\run_all.log 2>&1
echo Done. Results are in the output folder.
pause
