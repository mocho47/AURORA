@echo off
REM LAUNCHER PROFESIONAL AURORA NEXUS v3
REM Sistema de Operaciones IA 100% Completo

setlocal enabledelayedexpansion

cls
echo.
echo ================================================================================
echo          AURORA NEXUS v3 - SISTEMA MAESTRO DE OPERACIONES IA
echo ================================================================================
echo.
echo [VALIDACION] Iniciando validación del sistema...
echo.

REM Validar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instala Python 3.9+
    pause
    exit /b 1
)
echo [OK] Python instalado

REM Validar pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip no encontrado
    pause
    exit /b 1
)
echo [OK] pip disponible

REM Instalar dependencias
echo.
echo [SETUP] Instalando dependencias...
pip install -q fastapi uvicorn groq anthropic >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Algunos paquetes pueden requerir versiones específicas
)
echo [OK] Dependencias listas

REM Crear directorios
echo.
echo [SETUP] Creando directorios necesarios...
if not exist "C:\AURORA\MEMORIA\episodica" mkdir C:\AURORA\MEMORIA\episodica
if not exist "C:\AURORA\MEMORIA\semantica" mkdir C:\AURORA\MEMORIA\semantica
if not exist "C:\AURORA\LOGS" mkdir C:\AURORA\LOGS
if not exist "C:\AURORA\AUDITORIAS" mkdir C:\AURORA\AUDITORIAS
echo [OK] Directorios creados

REM Mostrar menu
echo.
echo ================================================================================
echo OPCIONES DE INICIO
echo ================================================================================
echo.
echo [1] Iniciar AURORA (Servidor Principal)
echo [2] Dashboard (Navegador)
echo [3] Sleep Cycle (Consolidación)
echo [4] Auditoría Diaria
echo [5] Ver Registros
echo [6] Configuración
echo [7] Salir
echo.
set /p opcion="Selecciona opción [1-7]: "

if "%opcion%"=="1" (
    cls
    echo.
    echo ================================================================================
    echo INICIANDO AURORA NEXUS v3
    echo ================================================================================
    echo.
    echo [INFO] Servidor iniciando en http://127.0.0.1:8000
    echo [INFO] Dashboard disponible en http://127.0.0.1:8000/dashboard
    echo [INFO] Documentación en http://127.0.0.1:8000/docs
    echo.
    echo [STARTUP] Cargando componentes...
    python C:\AURORA\aurora_unified_main.py
) else if "%opcion%"=="2" (
    echo [INFO] Abriendo dashboard...
    start http://127.0.0.1:8000/dashboard
) else if "%opcion%"=="3" (
    cls
    echo.
    echo ================================================================================
    echo EJECUTANDO SLEEP CYCLE
    echo ================================================================================
    echo.
    python C:\AURORA\AUTOMATIONS\sleep_cycle.py
    echo.
    pause
) else if "%opcion%"=="4" (
    cls
    echo.
    echo ================================================================================
    echo EJECUTANDO AUDITORIA DIARIA
    echo ================================================================================
    echo.
    python C:\AURORA\AUDITORIAS\auditoria_diaria.py
    echo.
    pause
) else if "%opcion%"=="5" (
    echo [INFO] Abriendo registros...
    notepad C:\AURORA\REGISTRO_MAESTRO.jsonl
) else if "%opcion%"=="6" (
    cls
    echo.
    echo ================================================================================
    echo CONFIGURACION
    echo ================================================================================
    echo.
    echo Variables de entorno necesarias:
    echo - GROQ_API_KEY
    echo - CLAUDE_API_KEY
    echo - GREEN_API_KEY (WhatsApp)
    echo - TELEGRAM_TOKEN
    echo - EMAIL_PASSWORD
    echo.
    notepad C:\AURORA\.env
) else if "%opcion%"=="7" (
    echo [INFO] Saliendo...
    exit /b 0
) else (
    echo [ERROR] Opción no válida
)

pause
endlocal
