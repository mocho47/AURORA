@echo off
setlocal enabledelayedexpansion
title AUDITOR MAESTRO REFORZADO - AURORA
cls

:: Forzar rutas nativas sin importar desde dónde se ejecute
set "RAIZ_A=C:\AURORA"
set "ANIDADA_B=C:\AURORA\AURORA"
set "REPORTE=%USERPROFILE%\Desktop\REPORTE_AURORA_FINAL.txt"

echo ====================================================
echo   🔍 INICIANDO AUDITORÍA INTEGRAL REFORZADA
echo ====================================================
echo.

if not exist "%RAIZ_A%" (
    echo [❌ ERROR] No se encontro la carpeta principal en C:\AURORA
    echo Por favor, verifica que la ruta sea correcta.
    pause
    exit
)

echo [REPORTE DE AUDITORIA DE SISTEMA] > "%REPORTE%"
echo FECHA: %date% - HORA: %time% >> "%REPORTE%"
echo RUTA PRINCIPAL: %RAIZ_A% >> "%REPORTE%"
echo ---------------------------------------------------- >> "%REPORTE%"

echo [1/4] Analizando ejecutables de Python...
echo 1. ENTORNO PYTHON >> "%REPORTE%"
where python >> "%REPORTE%" 2>&1
python --version >> "%REPORTE%" 2>&1
echo LIBRERIAS GLOBALES: >> "%REPORTE%"
pip freeze >> "%REPORTE%" 2>&1
echo ---------------------------------------------------- >> "%REPORTE%"

echo [2/4] Analizando carpeta Aurora Principal (A)...
echo 2. ARCHIVOS EN RAÍZ A >> "%REPORTE%"
dir "%RAIZ_A%" /B /A:-D >> "%REPORTE%" 2>&1
echo. >> "%REPORTE%"
echo FUNCIONES EN RAÍZ A: >> "%REPORTE%"
for %%f in ("%RAIZ_A%\*.py") do (
    echo Archivo: %%~nxf >> "%REPORTE%"
    findstr /R /C:"^[ ]*def " /C:"^[ ]*class " /C:"import " /C:"from " "%%f" >> "%REPORTE%" 2>&1
)
echo ---------------------------------------------------- >> "%REPORTE%"

echo [3/4] Analizando carpeta Aurora Anidada (B)...
echo 3. ARCHIVOS EN CARPETA ANIDADA B >> "%REPORTE%"
if exist "%ANIDADA_B%" (
    dir "%ANIDADA_B%" /B /A:-D >> "%REPORTE%" 2>&1
    echo. >> "%REPORTE%"
    echo FUNCIONES EN CARPETA B: >> "%REPORTE%"
    for %%f in ("%ANIDADA_B%\*.py") do (
        echo Archivo: %%~nxf >> "%REPORTE%"
        findstr /R /C:"^[ ]*def " /C:"^[ ]*class " /C:"import " /C:"from " "%%f" >> "%REPORTE%" 2>&1
    )
) else (
    echo Subcarpeta B no encontrada >> "%REPORTE%"
)
echo ---------------------------------------------------- >> "%REPORTE%"

echo [4/4] Analizando variables de entorno...
echo 4. VARIABLES .ENV DETECTADAS >> "%REPORTE%"
if exist "%RAIZ_A%\.env" (
    echo Variables en A: >> "%REPORTE%"
    for /f "tokens=1 delims==" %%i in (%RAIZ_A%\.env) do (
        set "v=%%i"
        if not "!v:~0,1!"=="#" if not "!v!"=="" echo   - !v! >> "%REPORTE%"
    )
)
if exist "%ANIDADA_B%\.env" (
    echo Variables en B: >> "%REPORTE%"
    for /f "tokens=1 delims==" %%i in (%ANIDADA_B%\.env) do (
        set "v=%%i"
        if not "!v:~0,1!"=="#" if not "!v!"=="" echo   - !v! >> "%REPORTE%"
    )
)

echo.
echo ====================================================
echo   ✅ ¡PROCESO TERMINADO CON ÉXITO!
echo ====================================================
echo El archivo se ha creado directamente en tu Escritorio.
echo Nombre del archivo: REPORTE_AURORA_FINAL.txt
echo.
pause
