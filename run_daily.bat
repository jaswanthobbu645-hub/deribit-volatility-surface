@echo off
cd /d C:\Users\jaswa\OneDrive\Desktop\deribit_project
if not exist logs mkdir logs

REM Check if today's row already exists
for /f "tokens=1-3 delims=/- " %%a in ("%date%") do set TODAY=%%c-%%b-%%a
findstr /C:"%TODAY%" metrics_history.csv >nul 2>&1
if %errorlevel%==0 (
    echo [SKIP] Today's row already exists. Skipping.
    exit /b 0
)

set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe src\data\fetch_live.py >> logs\daily_run.log 2>&1
echo ---- Run completed at %date% %time% ---- >> logs\daily_run.log
