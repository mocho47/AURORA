@echo off
REM Mata AURORA vieja (puerto 5000) y la levanta de nuevo, limpia.
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
)
cd /d "C:\AURORA.worktrees"
start "" /min "C:\Program Files\Python312\python.exe" run_aurora.py
echo AURORA reiniciada. Espera unos 90 segundos y abre http://127.0.0.1:5000
pause
