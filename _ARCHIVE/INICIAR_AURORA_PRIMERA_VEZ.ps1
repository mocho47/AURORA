# AURORA v1 - First Time Setup Script
# Ejecuta este script UNA SOLA VEZ para instalar y configurar todo

param(
    [Switch]$SkipInstall,
    [Switch]$SkipShortcuts
)

$AURORA_DIR = "C:\AURORA"
$CORE_DIR = "$AURORA_DIR\CORE"

function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     AURORA v1 - Primer Arranque      ║" -ForegroundColor Cyan
    Write-Host "║  Intelligent Multi-Motor Orchestrator ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Verify-Python {
    Write-Host "[*] Verificando Python..." -ForegroundColor Yellow

    try {
        $version = python --version 2>&1
        Write-Host "[OK] Python detectado: $version" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[ERROR] Python no encontrado" -ForegroundColor Red
        Write-Host ""
        Write-Host "Solución: Instala Python 3.9+ desde https://www.python.org" -ForegroundColor Yellow
        Write-Host "Marca 'Add Python to PATH' durante instalación" -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
}

function Run-Installation {
    Write-Host ""
    Write-Host "[*] Instalando AURORA..." -ForegroundColor Yellow

    if (Test-Path "$AURORA_DIR\INSTALAR_AURORA.bat") {
        Write-Host ""
        Write-Host "Ejecutando instalador..."
        & "$AURORA_DIR\INSTALAR_AURORA.bat"

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] AURORA instalado correctamente!" -ForegroundColor Green
            return $true
        } else {
            Write-Host ""
            Write-Host "[ERROR] Fallo en instalación" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "[ERROR] No encontrado: INSTALAR_AURORA.bat" -ForegroundColor Red
        return $false
    }
}

function Create-Shortcuts {
    Write-Host ""
    Write-Host "[*] Creando shortcuts en escritorio..." -ForegroundColor Yellow

    if (Test-Path "$AURORA_DIR\CREAR_SHORTCUTS.ps1") {
        & "$AURORA_DIR\CREAR_SHORTCUTS.ps1"
        Write-Host "[OK] Shortcuts creados" -ForegroundColor Green
    } else {
        Write-Host "[WARN] No encontrado: CREAR_SHORTCUTS.ps1" -ForegroundColor Yellow
    }
}

function Show-Next-Steps {
    Write-Host ""
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "     [SUCCESS] AURORA ESTA LISTO" -ForegroundColor Green
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "PROXIMOS PASOS:" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "1. CONFIGURAR API KEY (Recomendado)" -ForegroundColor White
    Write-Host "   Opcion A: Variable de entorno Windows" -ForegroundColor Gray
    Write-Host "   - Win + X > Sistema" -ForegroundColor Gray
    Write-Host "   - Variables de entorno > Nueva" -ForegroundColor Gray
    Write-Host "   - GROQ_API_KEY = gsk_..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Opcion B: Archivo .env.local" -ForegroundColor Gray
    Write-Host "   - cd C:\AURORA\CORE" -ForegroundColor Gray
    Write-Host "   - notepad .env.local" -ForegroundColor Gray
    Write-Host "   - Agrega: GROQ_API_KEY=gsk_..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Obtener clave GROQ (gratis):" -ForegroundColor Cyan
    Write-Host "   https://console.groq.com/keys" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "2. ARRANCAR AURORA" -ForegroundColor White
    Write-Host "   Abre PowerShell en C:\AURORA y ejecuta:" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   .\LAUNCHER_AURORA.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Luego elige:" -ForegroundColor Gray
    Write-Host "   - Opcion 1: CLI interactivo" -ForegroundColor Gray
    Write-Host "   - Opcion 2: Servidor FastAPI (web)" -ForegroundColor Gray
    Write-Host "   - Opcion 3: Ejecutar tests" -ForegroundColor Gray
    Write-Host ""

    Write-Host "3. USAR AURORA" -ForegroundColor White
    Write-Host "   CLI:" -ForegroundColor Gray
    Write-Host "   > Analiza este codigo Python" -ForegroundColor Cyan
    Write-Host "   > ¿Como mejorar mi relacion familiar?" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Web:" -ForegroundColor Gray
    Write-Host "   http://localhost:8000/templates/dashboard.html" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "DOCUMENTACION:" -ForegroundColor Yellow
    Write-Host "- README.md: Inicio rapido y uso" -ForegroundColor Gray
    Write-Host "- PRIMER_ARRANQUE.md: Guia de primer arranque" -ForegroundColor Gray
    Write-Host "- DEPLOYMENT.md: Deploy en produccion" -ForegroundColor Gray
    Write-Host "- PROJECT_STATUS.md: Estado del proyecto" -ForegroundColor Gray
    Write-Host ""

    Write-Host "FEATURES PRINCIPALES:" -ForegroundColor Yellow
    Write-Host "- 6 motores especializados" -ForegroundColor Gray
    Write-Host "- 4 SDKs (Claude, Groq, Zai, Ollama)" -ForegroundColor Gray
    Write-Host "- Inteligencia 6-tier" -ForegroundColor Gray
    Write-Host "- Auto-discovery de motores" -ForegroundColor Gray
    Write-Host "- Fallback chain automatico" -ForegroundColor Gray
    Write-Host "- CLI + Servidor + Dashboard" -ForegroundColor Gray
    Write-Host ""

    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# Main
Show-Banner

# Check Python
if (-not (Verify-Python)) {
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Install
if (-not $SkipInstall) {
    if (-not (Run-Installation)) {
        Write-Host ""
        Write-Host "Por favor ejecuta manualmente:" -ForegroundColor Yellow
        Write-Host ".\INSTALAR_AURORA.bat" -ForegroundColor Cyan
        Read-Host "Presiona Enter"
        exit 1
    }
} else {
    Write-Host "[SKIP] Saltando instalacion (--SkipInstall)" -ForegroundColor Yellow
}

# Create Shortcuts
if (-not $SkipShortcuts) {
    Create-Shortcuts
} else {
    Write-Host "[SKIP] Saltando shortcuts (--SkipShortcuts)" -ForegroundColor Yellow
}

# Final message
Show-Next-Steps

Write-Host "Presiona Enter para terminar..." -ForegroundColor White
Read-Host
