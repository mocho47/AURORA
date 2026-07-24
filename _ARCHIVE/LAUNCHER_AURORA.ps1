# AURORA v1 - Interactive Launcher
# Menú interactivo para gestionar AURORA

param(
    [Switch]$Server,
    [Switch]$CLI,
    [Switch]$Test,
    [Switch]$Install
)

$AURORA_DIR = "C:\AURORA"
$CORE_DIR = "$AURORA_DIR\CORE"
$env:PYTHONPATH = "$AURORA_DIR;$CORE_DIR"

function Show-Banner {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  AURORA v1 - Intelligent Orchestrator" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Menu {
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Yellow
    Write-Host "  1) CLI interactivo (recomendado)"
    Write-Host "  2) Servidor FastAPI (puerto 8000)"
    Write-Host "  3) Ejecutar tests"
    Write-Host "  4) Ver status"
    Write-Host "  5) Salir"
    Write-Host ""
}

function Start-CLI {
    Write-Host "[*] Iniciando AURORA CLI..." -ForegroundColor Green
    Write-Host ""
    Set-Location $CORE_DIR
    python aurora.py
}

function Start-Server {
    Write-Host "[*] Iniciando servidor AURORA..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Servidor disponible en: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Documentacion API: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Set-Location $CORE_DIR
    python -m uvicorn aurora_server:app --host 0.0.0.0 --port 8000 --reload
}

function Run-Tests {
    Write-Host "[*] Ejecutando suite de tests..." -ForegroundColor Green
    Write-Host ""
    Set-Location $CORE_DIR
    python test_aurora.py
    Read-Host "Presiona Enter para continuar"
}

function Show-Status {
    Write-Host "[*] Mostrando status de AURORA..." -ForegroundColor Green
    Write-Host ""
    Set-Location $CORE_DIR
    python -c "
import asyncio
from aurora import get_aurora
from aurora_registry import get_registry

aurora = get_aurora()
registry = get_registry()
status = registry.get_status()

print(f'Status AURORA: OPERATIVO')
print(f'Motores totales: {status[\"total_motors\"]}')
print(f'Motores activos: {status[\"active_motors\"]}')
print(f'Modulos cargados: {status[\"loaded_modules\"]}')
print()
print('Motores disponibles:')
for motor in status['motors']:
    icon = '[+]' if motor['activo'] else '[-]'
    print(f'  {icon} {motor[\"id\"]} ({motor[\"sdk_preferido\"]})')
"
    Write-Host ""
    Read-Host "Presiona Enter para continuar"
}

# Main
if ($Install) {
    Show-Banner
    Write-Host "Ejecutando instalador..." -ForegroundColor Yellow
    & "$AURORA_DIR\INSTALAR_AURORA.bat"
    exit
}

Show-Banner

# Check if script was run with parameters
if ($CLI) {
    Start-CLI
    exit
} elseif ($Server) {
    Start-Server
    exit
} elseif ($Test) {
    Run-Tests
    exit
}

# Interactive menu
while ($true) {
    Show-Menu
    $choice = Read-Host "Elige opcion"

    switch ($choice) {
        "1" { Start-CLI; break }
        "2" { Start-Server; break }
        "3" { Run-Tests }
        "4" { Show-Status }
        "5" {
            Write-Host "Saliendo..." -ForegroundColor Yellow
            break
        }
        default {
            Write-Host "Opcion invalida" -ForegroundColor Red
        }
    }

    if ($choice -eq "5") { break }
}

Write-Host "Hasta luego!" -ForegroundColor Cyan
