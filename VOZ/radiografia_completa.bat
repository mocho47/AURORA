@echo off
TITLE AURORA NEXUS v4 - RADIOGRAFÍA AUTOMÁTICA
CLS

:REVISAR_PERMISOS
net session >nul 2>&1
if %errorLevel% == 0 (
    goto INICIAR_ESCANEO
) else (
    goto SOLICITAR_PERMISOS
)

:SOLICITAR_PERMISOS
echo Set UAC = CreateObject("Shell.Application") > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
del "%temp%\getadmin.vbs"
exit /B

:INICIAR_ESCANEO
chcp 65001 > nul
set "REPORTE=%temp%\radiografia_aurora_temp.txt"

echo ============================================================
echo   ?? EJECUTANDO RADIOGRAFÍA COGNITIVA AUTOMÁTICA
echo   ?? ESCANEANDO SISTEMA Y COPIANDO AL PORTAPELES...
echo ============================================================
echo.

echo === RADIOGRAFÍA DE ARQUITECTURA COGNITIVA REAL === > "%REPORTE%"
echo Fecha y Hora: %date% %time% >> "%REPORTE%"
echo -------------------------------------------------- >> "%REPORTE%"

:: 1. MAPEO DE ARCHIVOS REALES
echo [??] Analizando estructura de carpetas de AURORA...
echo [1. ESTRUCTURA DE ARCHIVOS REALES] >> "%REPORTE%"
cd /d C:\AURORA 2>nul
if %errorLevel% neq 0 (
    echo ERROR CRÍTICO: La carpeta C:\AURORA no existe en el disco C. >> "%REPORTE%"
    goto FINALIZAR
)
tree /F >> "%REPORTE%"
echo. >> "%REPORTE%"

:: 2. DETECCIÓN DE ERRORES DE SINTAXIS
echo [??] Buscando errores de código en scripts de Python...
echo [2. ERRORES DE SINTAXIS ENCONTRADOS] >> "%REPORTE%"
for /R C:\AURORA %%I in (*.py) do (
    echo Archivo: %%~nxI >> "%REPORTE%"
    python -m py_compile "%%I" 2>> "%REPORTE%"
    if %errorLevel% == 0 (
        echo ESTADO: SINTAXIS OK >> "%REPORTE%"
    ) else (
        echo ESTADO: FALLA DE SINTAXIS DETECTADA >> "%REPORTE%"
    )
    echo -------------------------------------------------- >> "%REPORTE%"
)
echo. >> "%REPORTE%"

:: 3. REVISIÓN DE ENTRADAS DE RED Y PUERTOS
echo [??] Verificando estado de los sockets de red...
echo [3. OCUPACIÓN DE PUERTOS EN WINDOWS] >> "%REPORTE%"
echo --- Puerto 8000 --- >> "%REPORTE%"
netstat -ano | findstr :8000 >> "%REPORTE%"
echo --- Puerto 8080 --- >> "%REPORTE%"
netstat -ano | findstr :8080 >> "%REPORTE%"
echo. >> "%REPORTE%"

:: 4. IDENTIFICAR CANAL DE VOZ MASCULINO
echo [??] Extrayendo lista de voces disponibles...
echo [4. VOCES INSTALADAS EN EL SISTEMA] >> "%REPORTE%"
powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name + ' (GENDER: ' + $_.VoiceInfo.Gender + ' - LANG: ' + $_.VoiceInfo.Culture + ')' }" >> "%REPORTE%"

:FINALIZAR
echo. >> "%REPORTE%"
echo === FIN DEL REPORTE AUTOMÁTICO === >> "%REPORTE%"

:: Copiar el contenido completo directamente al portapapeles de Windows
type "%REPORTE%" | clip

echo ============================================================
echo   ? ¡PROCESO COMPLETADO CON ÉXITO!
echo   ?? Los datos ya se copiaron a tu portapapeles.
echo ============================================================
echo.
echo Solo regresa aquí, da clic derecho y selecciona "Pegar" (Ctrl + V).
echo.
del "%REPORTE%" 2>nul
pause
