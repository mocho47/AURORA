@echo off
title NEXUS SYSTEM LOADER
cls

echo ===============================
echo      NEXUS SYSTEM INIT
echo ===============================
echo.

REM --- Forzar ruta correcta ---
cd /d D:\NEXUS_SYSTEM\NEXUS

REM --- Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH
    echo Instala Python 3.11 y vuelve a ejecutar.
    pause
    exit /b
)

REM --- Verificar core ---
if not exist core\nexus.py (
    echo ERROR: core\nexus.py no encontrado
    pause
    exit /b
)

REM --- Lanzar Nexus ---
echo Iniciando NEXUS...
echo.
python core\nexus.py

echo.
echo NEXUS finalizado.
pause
