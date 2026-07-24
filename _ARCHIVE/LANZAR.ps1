# AURORA v1 - Launcher
# ==================

Write-Host "
════════════════════════════════════════════════════════════════════
                    AURORA v1 - SISTEMA OPERATIVO
════════════════════════════════════════════════════════════════════
" -ForegroundColor Cyan

# Cambiar a directorio CORE
$coreDir = "$PSScriptRoot\CORE"
Set-Location $coreDir

Write-Host "⚡ Iniciando servidor AURORA..." -ForegroundColor Yellow

# Instalar dependencias si no existen
Write-Host "📦 Verificando dependencias..." -ForegroundColor Yellow
python -m pip install -q -r requirements.txt 2>$null

# Iniciar servidor
Write-Host "🚀 Arrancando servidor en http://localhost:8000" -ForegroundColor Green
Write-Host "⏳ Espera 3 segundos..." -ForegroundColor Gray

$proc = Start-Process python -ArgumentList "aurora_server.py" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Abrir navegador
Write-Host "🌐 Abriendo navegador..." -ForegroundColor Green
Start-Process "http://localhost:8000"

Write-Host "
════════════════════════════════════════════════════════════════════
            ✓ AURORA está OPERATIVO
            ✓ Panel en http://localhost:8000
            ✓ Listo para usar
════════════════════════════════════════════════════════════════════
" -ForegroundColor Green

# Mantener script activo
Write-Host "Presiona Ctrl+C para detener AURORA" -ForegroundColor Yellow

try {
    while ($proc.HasExited -eq $false) {
        Start-Sleep -Seconds 1
    }
} catch {
    # User pressed Ctrl+C
    Write-Host "`nDeteniend servidor..." -ForegroundColor Yellow
    Stop-Process -Id $proc.Id -Force 2>$null
    Write-Host "✓ AURORA apagado" -ForegroundColor Green
}
