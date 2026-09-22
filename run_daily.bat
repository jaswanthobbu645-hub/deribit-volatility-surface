@echo off
cd /d C:\Users\jaswa\OneDrive\Desktop\deribit_project
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe src\data\fetch_live.py >> logs\daily_run.log 2>&1
echo ---- Run completed at %date% %time% ---- >> logs\daily_run.log
