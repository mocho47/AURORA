@echo off
REM AURORA v1 - Installer
REM Instala y configura AURORA completo

setlocal enabledelayedexpansion

set AURORA_DIR=C:\AURORA
set CORE_DIR=%AURORA_DIR%\CORE
set PYTHONPATH=%AURORA_DIR%;%CORE_DIR%

echo.
echo ============================================
echo   AURORA v1 - Instalador
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado
    echo Por favor instala Python 3.9+ desde https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo [OK] %PYVER%

REM Crear directorios
echo [*] Creando estructura de directorios...
if not exist "%AURORA_DIR%\SHARED\historial" mkdir "%AURORA_DIR%\SHARED\historial"
if not exist "%AURORA_DIR%\SHARED\cache" mkdir "%AURORA_DIR%\SHARED\cache"
if not exist "%AURORA_DIR%\TEMPLATES" mkdir "%AURORA_DIR%\TEMPLATES"
echo [OK] Directorios listos

REM Instalar dependencias
echo.
echo [*] Instalando dependencias...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r "%CORE_DIR%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

REM Ejecutar tests
echo.
echo [*] Validando instalación...
cd /d "%CORE_DIR%"
python test_aurora.py
if errorlevel 1 (
    echo [ERROR] Tests fallaron
    pause
    exit /b 1
)

echo.
echo ============================================
echo   [SUCCESS] AURORA instalado correctamente
echo ============================================
echo.
echo Proximos pasos:
echo.
echo 1. Configurar variables de entorno:
echo    - GROQ_API_KEY (recomendado)
echo    - CLAUDE_API_KEY (opcional)
echo    - ZAI_API_KEY (opcional)
echo.
echo 2. Arrancar AURORA:
echo    .\ARRANCAR_AURORA.ps1
echo.
echo 3. Abrir en navegador:
echo    http://localhost:8000
echo.
echo Para mas info: cat README.md
echo.
pause
