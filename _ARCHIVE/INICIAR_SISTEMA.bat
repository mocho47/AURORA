@echo off
REM ════════════════════════════════════════════════════════════════════════════════
REM    🚀 ASISTENTE FINAL PROFESIONAL - SCRIPT DE ARRANQUE
REM    Inicia el sistema completo NEXUS + AURORA en paralelo
REM ════════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║          🚀 INICIANDO ASISTENTE FINAL PROFESIONAL                         ║
echo ║                                                                            ║
echo ║          Orquestador Unificado: NEXUS + AURORA                            ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Cambiar al directorio de AURORA
cd /d C:\AURORA

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en PATH
    echo Por favor instala Python 3.9+ desde https://www.python.org
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM Iniciar servicios en paralelo
REM ────────────────────────────────────────────────────────────────────────────

echo 📋 Iniciando servicios...
echo.

REM AURORA Marketing System (Puerto 8010)
echo 📍 Iniciando AURORA Marketing System (puerto 8010)...
start "AURORA_MARKETING" cmd /k "cd C:\AURORA\SUPER_MARKETING_SYSTEM && python servidor_super_marketing.py"

timeout /t 2 /nobreak

REM NEXUS Motores (Puerto 8001)
echo 📍 Iniciando NEXUS Motores (puerto 8001)...
start "NEXUS_MOTORES" cmd /k "cd C:\nexus_v2 && python server.py"

timeout /t 2 /nobreak

REM ChatBot SaaS (Puerto 8005)
echo 📍 Iniciando ChatBot SaaS (puerto 8005)...
start "CHATBOT_SAAS" cmd /k "cd C:\chatbot_saas && python app.py"

timeout /t 2 /nobreak

REM Asistente Principal
echo 📍 Iniciando Asistente Final Profesional...
cd C:\AURORA
python asistente_final_profesional.py

echo.
echo ════════════════════════════════════════════════════════════════════════════
echo 🟢 SISTEMA ACTIVO
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo Accede al panel web:
echo   🌐 http://localhost:8000       ← Panel Principal
echo   📱 http://localhost:8010       ← AURORA Marketing
echo   🎯 http://localhost:8001       ← NEXUS Motores
echo   💬 http://localhost:8005       ← ChatBot SaaS
echo   📚 http://localhost:8080       ← TEENS Coaching
echo   🏠 http://localhost:8007       ← HomePro SaaS
echo.
echo Presiona Ctrl+C para detener el sistema
echo ════════════════════════════════════════════════════════════════════════════
echo.

pause
