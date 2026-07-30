@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python ears\voice_response.py
pause