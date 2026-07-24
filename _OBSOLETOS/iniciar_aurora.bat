@echo off
title AURORA v3.0 - Sistema de Marketing IA
color 0A
cls

echo =======================================================
echo    AURORA v3.0 - INICIANDO SISTEMA...
echo =======================================================
echo.

:: Moverse a la carpeta del proyecto
cd /d C:\AURORA

:: Forzar UTF-8 para evitar errores con caracteres especiales en Windows
set PYTHONUTF8=1
chcp 65001 > nul

:: 1. Activar entorno virtual
echo [1/3] Activando entorno virtual...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: No se encontro la carpeta .venv en C:\AURORA\
    goto :error
)

:: 2. Validar sistema
echo [2/3] Validando configuracion...
python validar_aurora.py
if %errorlevel% neq 0 goto :error

:: 3. Arrancar
echo.
echo [3/3] Todo listo! Ejecutando sistema...
echo =======================================================
python run_aurora.py
goto :end

:error
echo.
echo El arranque se detuvo por un error. Revisa la pantalla.
pause

:end
