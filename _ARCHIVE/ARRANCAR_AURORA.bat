@echo off
REM AURORA v1 Startup Script
REM Requiere Python 3.9+, todas las deps en requirements.txt instaladas

setlocal enabledelayedexpansion

set AURORA_DIR=C:\AURORA
set CORE_DIR=%AURORA_DIR%\CORE
set PYTHONPATH=%AURORA_DIR%;%CORE_DIR%

echo.
echo ============================================
echo   AURORA v1 - Intelligent Orchestrator
echo ============================================
echo.
echo Directorio: %AURORA_DIR%
echo PYTHONPATH: %PYTHONPATH%
echo.

REM Verificar que Python existe
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python 3.9+ y agrega a PATH.
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Instalar dependencias si no existen
echo Verificando dependencias...
pip install -q -r "%CORE_DIR%\requirements.txt"
if errorlevel 1 (
    echo ERROR: Fallo al instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias listas
echo.

REM Arrancar AURORA
echo Iniciando AURORA...
cd /d "%CORE_DIR%"
python aurora.py

pause
