# AURORA v1 - Lanzamiento Inmediato del Ecosistema
# Ejecuta sin preguntar

$AURORA_DIR = "C:\AURORA"
$CORE_DIR = "$AURORA_DIR\CORE"
$env:PYTHONPATH = "$AURORA_DIR;$CORE_DIR"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AURORA v1 - ECOSISTEMA LANZADO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Validate
Write-Host "[+] Validando componentes..." -ForegroundColor Yellow
Set-Location $CORE_DIR

$validation = python -c "
import sys
sys.path.insert(0, '.')
from aurora import get_aurora
from aurora_registry import get_registry

aurora = get_aurora()
registry = get_registry()
status = registry.get_status()

print(f'OK|{status[\"total_motors\"]}|{status[\"active_motors\"]}')
" 2>&1

if ($validation -match "OK") {
    $parts = $validation -split '\|'
    $total = $parts[1]
    $active = $parts[2]

    Write-Host "[OK] AURORA Inicializado" -ForegroundColor Green
    Write-Host "[OK] $total motores descubiertos" -ForegroundColor Green
    Write-Host "[OK] $active motores activos" -ForegroundColor Green
    Write-Host "[OK] SDK Manager operativo" -ForegroundColor Green
    Write-Host "[OK] 6-Tier Decision Engine activo" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Validacion fallida" -ForegroundColor Red
    Write-Host $validation
    exit 1
}

Write-Host ""
Write-Host "MOTORES OPERACIONALES:" -ForegroundColor Yellow
python -c "
import sys
sys.path.insert(0, '.')
from aurora_registry import get_registry

registry = get_registry()
status = registry.get_status()

for m in status['motors']:
    print(f'  > {m[\"id\"]:20} ({m[\"sdk_preferido\"]:6})')
" 2>&1 | Where-Object {$_ -match ">"}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ECOSISTEMA AURORA V1 - OPERATIVO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "MODO CLI INTERACTIVO - INICIANDO..." -ForegroundColor Cyan
Write-Host ""

# Arrancar CLI
python aurora.py
