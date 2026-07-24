# AURORA v1 Startup Script (PowerShell)
# Uso: .\ARRANCAR_AURORA.ps1

param(
    [Switch]$NoInstall,
    [Switch]$Verbose
)

$ErrorActionPreference = "Stop"

$AURORA_DIR = "C:\AURORA"
$CORE_DIR = "$AURORA_DIR\CORE"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AURORA v1 - Intelligent Orchestrator" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Directorio: $AURORA_DIR"
Write-Host "PYTHONPATH: $AURORA_DIR;$CORE_DIR"
Write-Host ""

# Verificar Python
try {
    $PythonVersion = python --version 2>&1
    Write-Host "[OK] Python detectado: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no encontrado. Instala Python 3.9+" -ForegroundColor Red
    exit 1
}

# Instalar dependencias
if (-not $NoInstall) {
    Write-Host "Verificando dependencias..."
    $ReqFile = "$CORE_DIR\requirements.txt"
    if (Test-Path $ReqFile) {
        pip install -q -r $ReqFile
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Dependencias listas" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Fallo al instalar dependencias" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""
Write-Host "Iniciando AURORA..." -ForegroundColor Cyan
Write-Host ""

# Configurar PYTHONPATH y arrancar
$env:PYTHONPATH = "$AURORA_DIR;$CORE_DIR"
Set-Location $CORE_DIR

if ($Verbose) {
    python -u aurora.py
} else {
    python aurora.py
}
