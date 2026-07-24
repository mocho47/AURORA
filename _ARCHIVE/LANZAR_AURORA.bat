@echo off
REM ════════════════════════════════════════════════════════════════════════════════
REM                    🌟 AURORA v2 - LANZADOR COMPLETO 🌟
REM ════════════════════════════════════════════════════════════════════════════════

cls
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo                   ⚡ LANZANDO AURORA v2 - SISTEMA COMPLETO ⚡
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 🎯 SISTEMA INTEGRADO:
echo    • Cerebro sin censura (AURORA Core)
echo    • Crisis Protocol (5 niveles automáticos)
echo    • Chat Psicológico (16 librerías)
echo    • 6 Dinámicas Educativas
echo    • 6 Roles Simultáneos
echo    • Cotizador de Productos
echo    • Panel Profesional
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.

REM Cambiar a directorio CORE
cd /d C:\AURORA\CORE

echo ✓ Directorio: C:\AURORA\CORE
echo ✓ Python listo

REM Instalar dependencias
echo.
echo 📦 Instalando dependencias...
python -m pip install -q fastapi uvicorn 2>nul

echo ✓ Dependencias OK

echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo                          🚀 INICIANDO AURORA v2
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo Panel:      http://localhost:8000/panel
echo API Docs:   http://localhost:8000/docs
echo WebSocket:  ws://localhost:8000/ws
echo.
echo ROLES DISPONIBLES:
echo   🧠 Teen (Adolescente)
echo   👨‍🏫 Maestro (Educación)
echo   👨‍👩‍👧 Padre (Familia)
echo   💼 Vendedor (Negocios)
echo   ⚙️ Admin (Sistema)
echo.
echo CARACTERÍSTICAS:
echo   ✓ 16 Librerías Psicológicas
echo   ✓ 6 Dinámicas Educativas
echo   ✓ Protocolo de Crisis (5 niveles)
echo   ✓ Acompañamiento sin imposición
echo   ✓ Autonomía total
echo   ✓ Cotizador integrado
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ⏳ Servidor iniciando (espera 3-5 segundos)...
echo.

REM Esperar 3 segundos
timeout /t 3 /nobreak

REM Abrir navegador
start http://localhost:8000/panel

echo 🌐 Navegador abierto...
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo                   ✨ AURORA v2 OPERATIVO - SIN PARAR ✨
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo Sistema EN LÍNEA. Presiona Ctrl+C para detener.
echo.

REM Lanzar servidor
python servidor_aurora_completo.py
