@echo off
title NEXUS - Inicializador Definitivo
chcp 65001 >nul

set ROOT=%~dp0NEXUS
set PY=python

echo ==============================
echo INICIANDO NEXUS
echo ==============================

echo.
echo [1/5] Verificando estructura...

mkdir "%ROOT%" 2>nul

for %%D in (core brain ears mouth memory skills logs config) do (
    if not exist "%ROOT%\%%D" (
        mkdir "%ROOT%\%%D"
        echo [+] Carpeta %%D creada.
    ) else (
        echo [OK] Carpeta %%D existe.
    )
)

echo.
echo [2/5] Verificando archivos base...

if not exist "%ROOT%\memory\state.json" (
    echo {} > "%ROOT%\memory\state.json"
    echo [+] state.json creado.
) else (
    echo [OK] state.json existe.
)

if not exist "%ROOT%\config\settings.json" (
    echo {} > "%ROOT%\config\settings.json"
    echo [+] settings.json creado.
) else (
    echo [OK] settings.json existe.
)

if not exist "%ROOT%\core\nexus.py" (
    echo print^("NEXUS ARRANCADO CORRECTAMENTE"^) > "%ROOT%\core\nexus.py"
    echo input^("Presiona ENTER para salir..."^) >> "%ROOT%\core\nexus.py"
    echo [+] nexus.py creado.
) else (
    echo [OK] nexus.py existe.
)

echo.
echo [3/5] Verificando Python...
%PY% --version >nul 2>&1 || (
    echo ERROR: Python no encontrado en PATH
    pause
    exit /b
)
echo [OK] Python detectado.

echo.
echo [4/5] Arrancando Nexus...
%PY% "%ROOT%\core\nexus.py"

echo.
echo Nexus cerrado correctamente.
pause

