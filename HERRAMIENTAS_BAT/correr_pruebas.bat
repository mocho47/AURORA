@echo off
REM Corre todas las pruebas de regresion de AURORA
cd /d "C:\AURORA.worktrees"
"C:\Program Files\Python312\python.exe" -m pytest tests/ -q
pause
