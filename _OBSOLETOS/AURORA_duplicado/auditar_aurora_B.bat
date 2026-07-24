@echo off
setlocal enabledelayedexpansion
title AUDITOR DE NUCLEO - AURORA VERSION B
chcp 65001 > nul

:: ==========================================
:: CONFIGURA AQUÍ LA RUTA DE LA SEGUNDA AURORA
set "RUTA_AURORA=C:\Ruta\A\Tu\Segunda\Aurora"
:: ==========================================

set "ID_AUDITORIA=AUD_B_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%"
set "ID_AUDITORIA=%ID_AUDITORIA: =0%"
set "REPORTE=%RUTA_AURORA%\REPORT_%ID_AUDITORIA%.md"

echo ====================================================
echo   🔍 INICIANDO AUDITORÍA INTEGRAL - AURORA VERSION B
echo ====================================================
echo ID ÚNICO: %ID_AUDITORIA%
echo Carpeta de análisis: %RUTA_AURORA%
echo.

if not exist "%RUTA_AURORA%" (
    echo [❌ ERROR] No se encontró la ruta %RUTA_AURORA%. Modifica el archivo .bat con la ruta correcta.
    pause
    exit
)

echo # REPORT DE AUDITORÍA ÚNICA: %ID_AUDITORIA% > "%REPORTE%"
echo ## 📅 FECHA Y HORA: %date% %time% >> "%REPORTE%"
echo ## 📁 RUTA ANALIZADA: `%RUTA_AURORA%` >> "%REPORTE%"
echo --- >> "%REPORTE%"

echo [1/4] Analizando entorno de ejecución...
echo ## 💻 1. ENTORNO DE EJECUCIÓN Y PATH >> "%REPORTE%"
echo ```text >> "%REPORTE%"
echo [PYTHON PATH]: >> "%REPORTE%"
where python >> "%REPORTE%" 2>&1
echo [VERSION]: >> "%REPORTE%"
python --version >> "%REPORTE%" 2>&1
echo [PIP FREEZE - LIBRERÍAS]: >> "%REPORTE%"
pip freeze >> "%REPORTE%" 2>&1
echo ``` >> "%REPORTE%"

echo [2/4] Mapeando estructura de archivos...
echo ## 🗂️ 2. ESTRUCTURA COMPLETA DEL DIRECTORIO >> "%REPORTE%"
echo ```text >> "%REPORTE%"
tree "%RUTA_AURORA%" /F /A >> "%REPORTE%"
echo ``` >> "%REPORTE%"

echo [3/4] Escaneando funciones y alcances en scripts Python...
echo ## ⚡ 3. MAPEO DE FUNCIONES, CLASES Y ALCANCES >> "%REPORTE%"
for /r "%RUTA_AURORA%" %%f in (*.py) do (
    set "archivo_rel=%%f"
    set "archivo_rel=!archivo_rel:%RUTA_AURORA%\=!"
    echo ### 📄 Archivo: `!archivo_rel!` >> "%REPORTE%"
    echo ```python >> "%REPORTE%"
    findstr /R /C:"^[ ]*def " /C:"^[ ]*class " /C:"import " /C:"from " "%%f" >> "%REPORTE%"
    echo ``` >> "%REPORTE%"
)

echo [4/4] Verificando configuraciones de entorno (.env)...
echo ## 🔑 4. VERIFICACIÓN DE VARIABLES (SIN REVELAR CLAVES) >> "%REPORTE%"
echo ```text >> "%REPORTE%"
if exist "%RUTA_AURORA%\.env" (
    echo [OK] Archivo .env presente. >> "%REPORTE%"
    echo Variables detectadas: >> "%REPORTE%"
    for /f "tokens=1 delims==" %%i in (%RUTA_AURORA%\.env) do (
        set "var=%%i"
        if not "!var:~0,1!"=="#" if not "!var!"=="" echo   - !var! >> "%REPORTE%"
    )
) else (
    echo [ADVERTENCIA] No se encontró archivo .env en esta raíz. >> "%REPORTE%"
)
echo ``` >> "%REPORTE%"

echo. >> "%REPORTE%"
echo --- >> "%REPORTE%"
echo **FIN DEL REPORTE AUTOMÁTICO - REPORTE VÁLIDO PARA ANÁLISIS DE IA** >> "%REPORTE%"

echo [✅ COMPLETADO] Auditoría finalizada con éxito.
echo Reporte generado en: %REPORTE%
echo.
pause
