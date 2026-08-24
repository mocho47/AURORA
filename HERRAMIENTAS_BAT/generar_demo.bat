@echo off
REM Genera la version demo (virgen + licencia) en C:\AURORA_DEMO
cd /d "C:\AURORA.worktrees"
"C:\Program Files\Python312\python.exe" EMPAQUETADO\generar_version_demo.py
pause
