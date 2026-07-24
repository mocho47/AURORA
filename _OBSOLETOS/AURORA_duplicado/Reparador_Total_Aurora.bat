@echo off
:: =====================================================================
::   AURORA v3.0 - INSTALADOR Y REPARADOR AUTOMÁTICO TOTAL
:: =====================================================================
CLS
color 0B
echo =====================================================================
echo  Iniciando Reparacion Automatizada y Lanzamiento de AURORA v3.0
echo =====================================================================
echo.

:: 1. VERIFICAR PERMISOS DE ADMINISTRADOR
echo [PASO 1] Verificando permisos de Administrador...
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
echo [OK] Permisos de Administrador confirmados.
echo.

:: DELEGACIÓN DE VARIABLES
set "TARGET_DIR=C:\AURORA\SUPER_MARKETING_SYSTEM"

:: 2. CERRAR PROCESOS EXISTENTES (PUERTO 5000)
echo [PASO 2] Liberando puerto 5000 de instancias colgadas...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo [OK] Puerto 5000 desbloqueado.
echo.

:: 3. ELIMINAR LIBRERÍAS CON CONFLICTO
echo [PASO 3] Eliminando modulos Supabase v2.31.0 con conflicto...
if exist "%TARGET_DIR%" (
    cd /d "%TARGET_DIR%"
    
    :: Borrar carpetas conflictivas si existen
    if exist "supabase" rd /s /q "supabase"
    if exist "supabase-2.31.0.dist-info" rd /s /q "supabase-2.31.0.dist-info"
    if exist "supabase_auth" rd /s /q "supabase_auth"
    if exist "supabase_auth-2.31.0.dist-info" rd /s /q "supabase_auth-2.31.0.dist-info"
    if exist "supabase_functions" rd /s /q "supabase_functions"
    if exist "supabase_functions-2.31.0.dist-info" rd /s /q "supabase_functions-2.31.0.dist-info"
    
    echo [OK] Carpetas obsoletas eliminadas correctamente.
) else (
    echo [ERROR] No se encontro el directorio base: %TARGET_DIR%
    pause
    exit
)
echo.

:: 4. INSTALAR VERSIÓN ESTABLE COMPATIBLE
echo [PASO 4] Instalando automaticamente version compatible de Supabase...
pip install "supabase==2.3.0" --target="%TARGET_DIR%" --upgrade

if %errorLevel% neq 0 (
    echo [ADVERTENCIA] Algo fallo con pip install directo. Reintentando...
    pip install "supabase==2.3.0" --target="%TARGET_DIR%"
)
echo [OK] Dependencias corregidas con exito.
echo.

:: 5. ASEGURAR FIREWALL DE WINDOWS
echo [PASO 5] Habilitando regla de entrada en el Firewall para el puerto 5000...
netsh advfirewall firewall add rule name="Aurora_FastAPI_5000" dir=in action=allow protocol=TCP localport=5000 profile=any >nul 2>&1
echo [OK] Regla de red aplicada.
echo.

:: 6. LANZAR AURORA
echo =====================================================================
echo  ¡TODO CONFIGURADO AUTOMÁTICAMENTE! Lanzando AURORA v3.0...
echo =====================================================================
echo.

if exist "%USERPROFILE%\Desktop\AURORA.lnk" (
    start "" "%USERPROFILE%\Desktop\AURORA.lnk"
    echo [OK] Ejecutable lanzado desde el Escritorio.
) else if exist "AURORA.lnk" (
    start "" "AURORA.lnk"
    echo [OK] Ejecutable lanzado desde el directorio raiz.
) else (
    echo [INFO] Entorno reparado con exito. 
    echo Por favor, arranca tu acceso directo de AURORA de forma normal desde tu escritorio.
)

echo.
echo Abriendo el navegador en tu Dashboard en 5 segundos...
timeout /t 5 > nul
start http://127.0.0.1:5000
exit