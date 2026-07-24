@echo off
title Extractor de Cerebro Aurora v3.0
chcp 65001 > nul

:: Definición de rutas seguras
set "ORIGEN=C:\AURORA\SUPER_MARKETING_SYSTEM"
set "DESTINO=%USERPROFILE%\Desktop\CEREBRO_AURORA_EXTRAIDO.txt"

echo ===================================================
echo   AURORA v3.0 - ARCHIVERO DE AUDITORÍA DE SISTEMAS
echo ===================================================
echo.
echo Generando reporte de código fuente en el Escritorio...
echo Guardando en: %DESTINO%
echo.

:: Limpiar o crear el archivo de destino
echo =================================================== > "%DESTINO%"
echo   REPORTE COMPLETO DEL NÚCLEO LOGÍSTICO DE AURORA  >> "%DESTINO%"
echo   Fecha de extracción: 2026-07-05                  >> "%DESTINO%"
echo =================================================== >> "%DESTINO%"
echo. >> "%DESTINO%"

:: 1. Extraer API Principal (FastAPI)
if exist "%ORIGEN%\api_v3_new.py" (
    echo [1/4] Extrayendo api_v3_new.py...
    echo. >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo /// ARCHIVO: api_v3_new.py                      /// >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo. >> "%DESTINO%"
    type "%ORIGEN%\api_v3_new.py" >> "%DESTINO%"
) else (
    echo [ALERTA] No se encontró api_v3_new.py
)

:: 2. Extraer Publicador de Redes
if exist "%ORIGEN%\publicador_real.py" (
    echo [2/4] Extrayendo publicador_real.py...
    echo. >> "%DESTINO%"
    echo. >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo /// ARCHIVO: publicador_real.py                 /// >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo. >> "%DESTINO%"
    type "%ORIGEN%\publicador_real.py" >> "%DESTINO%"
) else (
    echo [ALERTA] No se encontró publicador_real.py
)

:: 3. Extraer Motor de WhatsApp
if exist "%ORIGEN%\motor_whatsapp_real.py" (
    echo [3/4] Extrayendo motor_whatsapp_real.py...
    echo. >> "%DESTINO%"
    echo. >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo /// ARCHIVO: motor_whatsapp_real.py             /// >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo. >> "%DESTINO%"
    type "%ORIGEN%\motor_whatsapp_real.py" >> "%DESTINO%"
) else (
    echo [ALERTA] No se encontró motor_whatsapp_real.py
)

:: 4. Extraer CRM de Leads e Integración SQLite
if exist "%ORIGEN%\crm_leads_ventas.py" (
    echo [4/4] Extrayendo crm_leads_ventas.py...
    echo. >> "%DESTINO%"
    echo. >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo /// ARCHIVO: crm_leads_ventas.py                /// >> "%DESTINO%"
    echo /////////////////////////////////////////////////// >> "%DESTINO%"
    echo. >> "%DESTINO%"
    type "%ORIGEN%\crm_leads_ventas.py" >> "%DESTINO%"
) else (
    echo [ALERTA] No se encontró crm_leads_ventas.py
)

echo.
echo ===================================================
echo  ✅ PROCESO COMPLETADO EXITOSAMENTE
echo  El archivo 'CEREBRO_AURORA_EXTRAIDO.txt' está listo.
echo ===================================================
pause
