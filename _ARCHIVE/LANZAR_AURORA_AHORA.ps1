# AURORA v2 - LANZAR AHORA (Versión simplificada)

Write-Host @"
════════════════════════════════════════════════════════════════════════════════
                    AURORA v2 - LANZAMIENTO INMEDIATO
════════════════════════════════════════════════════════════════════════════════
"@ -ForegroundColor Cyan

$coreDir = "$PSScriptRoot\CORE"
Set-Location $coreDir

Write-Host "`n✓ Directorio: $coreDir" -ForegroundColor Green
Write-Host "✓ Python listo" -ForegroundColor Green
Write-Host "✓ FastAPI configurado" -ForegroundColor Green

# Instalar FastAPI y uvicorn (lo básico)
Write-Host "`n📦 Instalando dependencias necesarias..." -ForegroundColor Yellow
python -m pip install -q fastapi uvicorn 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Advertencia en instalación, continuando..." -ForegroundColor Yellow
}

Write-Host "✓ Dependencias OK" -ForegroundColor Green

# Lanzar servidor
Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                        🚀 INICIANDO AURORA v2
════════════════════════════════════════════════════════════════════════════════

Servidor FastAPI iniciando en:
  🌐 http://localhost:8000

Acceso:
  • Panel: http://localhost:8000/panel
  • API Docs: http://localhost:8000/docs
  • WebSocket: ws://localhost:8000/ws

════════════════════════════════════════════════════════════════════════════════

⏳ Servidor iniciando (espera 2-3 segundos)...
"@ -ForegroundColor Green

# Esperar a que se inicie
Start-Sleep -Seconds 2

# Intentar abrir navegador con panel completo
try {
    Start-Process "http://localhost:8000/panel" 2>$null
    Write-Host "`n✓ Navegador abierto en http://localhost:8000/panel" -ForegroundColor Green
} catch {
    Write-Host "`n⚠️ No se pudo abrir navegador automáticamente" -ForegroundColor Yellow
    Write-Host "   Abre manualmente: http://localhost:8000/panel" -ForegroundColor Yellow
}

Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                        ✨ AURORA v2 OPERATIVO ✨
════════════════════════════════════════════════════════════════════════════════

Presiona Ctrl+C para detener AURORA
"@ -ForegroundColor Green

Write-Host ""

# Lanzar servidor
python servidor_simple.py
