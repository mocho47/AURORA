@echo off
REM ════════════════════════════════════════════════════════════════════════════════
REM    📤 ACTUALIZAR GITHUB - PUSH AUTOMÁTICO
REM    Sube todos los cambios del Asistente Final Profesional a GitHub
REM ════════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║                    📤 ACTUALIZAR GITHUB                                   ║
echo ║                                                                            ║
echo ║         Subiendo Asistente Final Profesional a repositorio                ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Cambiar al directorio del repositorio
cd /d C:\AURORA

REM Verificar que git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Git no está instalado
    echo Por favor instala Git desde https://git-scm.com
    pause
    exit /b 1
)

echo ✅ Git detectado
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM Verificar estado del repositorio
REM ────────────────────────────────────────────────────────────────────────────

echo 📋 Verificando estado del repositorio...
git status

echo.
echo ────────────────────────────────────────────────────────────────────────────
echo 📌 ARCHIVOS NUEVOS/MODIFICADOS:
echo ────────────────────────────────────────────────────────────────────────────

git status --porcelain

echo.
echo ────────────────────────────────────────────────────────────────────────────
echo 📦 PREPARANDO COMMIT...
echo ────────────────────────────────────────────────────────────────────────────
echo.

REM Agregar todos los archivos nuevos/modificados
git add -A

echo ✅ Archivos preparados
echo.

REM Crear mensaje de commit descriptivo
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%
set MESSAGE=⚡ ASISTENTE FINAL PROFESIONAL v1.0.0 - Integración Completa NEXUS+AURORA

echo 💬 Mensaje de commit:
echo    "%MESSAGE%"
echo.

REM Realizar commit
git commit -m "%MESSAGE%" -m "Features:" -m "- Asistente Final Profesional integrado" -m "- Publicador Multi-Red con sincronización paso a paso" -m "- Edición de Videos IA con hooks visuales" -m "- Búsqueda Web Real con cotizaciones inteligentes" -m "- ChatBot WhatsApp integrado" -m "- Dashboard Analytics en vivo" -m "- API REST con 20+ endpoints" -m "- Panel web HTML5 responsivo" -m "Co-Authored-By: Asistente NEXUS-AURORA <noreply@sistema.local>"

if errorlevel 1 (
    echo ❌ Error en el commit. Posible razón: no hay cambios o error de git
    pause
    exit /b 1
)

echo ✅ Commit realizado
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM PUSH A GITHUB
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo ────────────────────────────────────────────────────────────────────────────
echo 📤 ENVIANDO A GITHUB...
echo ────────────────────────────────────────────────────────────────────────────
echo.

git push origin main

if errorlevel 1 (
    echo.
    echo ⚠️  ERROR en push. Posibles razones:
    echo    • No hay conexión a GitHub
    echo    • Credenciales no configuradas
    echo    • La rama no existe en remoto
    echo.
    echo 💡 Solución: Ejecuta estos comandos manualmente:
    echo    git config user.email "milanmontellanoanuar@gmail.com"
    echo    git config user.name "Anuar Milan"
    echo    git push -u origin main --force
    pause
    exit /b 1
)

echo.
echo ✅ Push completado exitosamente
echo.

REM ────────────────────────────────────────────────────────────────────────────
REM VERIFICACIÓN FINAL
REM ────────────────────────────────────────────────────────────────────────────
echo.
echo ────────────────────────────────────────────────────────────────────────────
echo 📊 RESUMEN FINAL
echo ────────────────────────────────────────────────────────────────────────────
echo.

echo 📌 Último commit:
git log --oneline -1

echo.
echo 🌐 Repositorio:
git config --get remote.origin.url

echo.
echo ════════════════════════════════════════════════════════════════════════════
echo ✅ GITHUB ACTUALIZADO CORRECTAMENTE
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 📋 Resumen de cambios:
echo    • Asistente Final Profesional v1.0.0
echo    • 5 sistemas integrados
echo    • API REST completa
echo    • Panel web interactivo
echo    • Documentación profesional
echo.
echo 🔗 Ver en GitHub:
echo    https://github.com/mocho47/ASISTENTE-NEXUS-AURORA
echo.

pause
