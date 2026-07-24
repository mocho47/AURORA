@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  AURORA NEXUS v3 - SISTEMA MAESTRO
echo ============================================================
echo.

REM Verificar Python
echo [1/4] Validando Python...
python --version > /dev/null 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)
echo [OK] Python disponible

REM Instalar dependencias
echo [2/4] Verificando dependencias...
python -m pip install fastapi uvicorn groq anthropic -q

REM Crear directorios
echo [3/4] Inicializando directorios...
if not exist "C:\AURORA\MEMORIA\episodica" mkdir "C:\AURORA\MEMORIA\episodica"
if not exist "C:\AURORA\MEMORIA\semantica" mkdir "C:\AURORA\MEMORIA\semantica"
if not exist "C:\AURORA\MEMORIA\consolidacion" mkdir "C:\AURORA\MEMORIA\consolidacion"
if not exist "C:\AURORA\LOGS" mkdir "C:\AURORA\LOGS"
if not exist "C:\AURORA\AUDITORIAS" mkdir "C:\AURORA\AUDITORIAS"

echo.
echo ============================================================
echo  AURORA NEXUS v3 - LANZANDO
echo ============================================================
echo.
echo  Dashboard:     http://127.0.0.1:8000
echo  API Health:    http://127.0.0.1:8000/health
echo  Motores:       9 activos
echo  Cerebro:       En vivo
echo.
echo  Presiona CTRL+C para detener
echo ============================================================
echo.

cd /d C:\AURORA
python aurora_unified_main.py

pause
