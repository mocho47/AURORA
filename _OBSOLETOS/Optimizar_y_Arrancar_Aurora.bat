@echo off
:: =====================================================================
::   AURORA v3.0 - FIJADOR DE ENTORNO (A PRUEBA DE FALLOS)
:: =====================================================================
CLS
color 0A

:: FORCE_ADMIN
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] ¡FALTAN PERMISOS DE ADMINISTRADOR!
    echo ---------------------------------------------------
    echo Por favor:
    echo 1. Cierra esta ventana.
    echo 2. Haz CLIC DERECHO sobre este archivo .bat
    echo 3. Selecciona "EJECUTAR COMO ADMINISTRADOR".
    echo ---------------------------------------------------
    pause
    exit
)

echo ===================================================
echo  1. Liberando puerto 5000...
echo ===================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo [OK] Puerto limpio.

echo ===================================================
echo  2. Abriendo Firewall de Windows...
echo ===================================================
netsh advfirewall firewall add rule name="Aurora_FastAPI_5000" dir=in action=allow protocol=TCP localport=5000 profile=any >nul 2>&1
echo [OK] Regla de red asegurada.

echo ===================================================
echo  3. Limpiando Proxies...
echo ===================================================
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f >nul 2>&1
echo [OK] Proxy desactivado.

echo ===================================================
echo  4. Iniciando AURORA v3.0...
echo ===================================================
echo.
echo [AVISO] Si la app no arranca, es porque el acceso directo 
echo no se llama "AURORA.lnk" en tu escritorio.
echo.

if exist "%USERPROFILE%\Desktop\AURORA.lnk" (
    start "" "%USERPROFILE%\Desktop\AURORA.lnk"
    echo [OK] Ejecutable lanzado desde el Escritorio.
) else (
    echo [ERROR] No encontre el acceso directo "AURORA.lnk" en el Escritorio.
    echo.
    echo Por favor, arrastra aqui el archivo ejecutable (.exe o acceso directo) 
    echo que usas normalmente para abrir AURORA y presiona ENTER:
    set /p RUTA_USER=""
    if defined RUTA_USER (
        start "" %RUTA_USER%
    )
)

echo.
echo Proceso terminado. Abriendo navegador...
timeout /t 3 > nul
start http://127.0.0.1:5000
exit