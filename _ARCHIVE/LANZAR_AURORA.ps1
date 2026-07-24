# ════════════════════════════════════════════════════════════════════════════════
#                       🌟 AURORA v2 - LANZADOR COMPLETO 🌟
# ════════════════════════════════════════════════════════════════════════════════

Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                    ⚡ LANZANDO AURORA v2 - SISTEMA COMPLETO ⚡
════════════════════════════════════════════════════════════════════════════════

🎯 SISTEMA INTEGRADO:
   • Cerebro sin censura (AURORA Core)
   • Crisis Protocol (5 niveles automáticos)
   • Chat Psicológico (16 librerías)
   • 6 Dinámicas Educativas
   • 6 Roles Simultáneos
   • Cotizador de Productos
   • Panel Profesional

════════════════════════════════════════════════════════════════════════════════

"@ -ForegroundColor Cyan

# Detectar ubicación actual
$AuroraDir = "C:\AURORA"

if (-not (Test-Path $AuroraDir)) {
    Write-Host "❌ AURORA no encontrado en $AuroraDir" -ForegroundColor Red
    exit 1
}

$CoreDir = Join-Path $AuroraDir "CORE"

Write-Host "✓ Directorio AURORA: $AuroraDir" -ForegroundColor Green
Write-Host "✓ Directorio CORE: $CoreDir" -ForegroundColor Green

# Cambiar a directorio CORE
Set-Location $CoreDir

# Instalar dependencias si es necesario
Write-Host "`n📦 Verificando dependencias..." -ForegroundColor Yellow
python -m pip install -q fastapi uvicorn 2>$null

# Esperar un momento
Start-Sleep -Seconds 1

# Mostrar información de lanzamiento
Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                          🚀 INICIANDO AURORA v2
════════════════════════════════════════════════════════════════════════════════

Panel:      http://localhost:8000/panel
API Docs:   http://localhost:8000/docs
WebSocket:  ws://localhost:8000/ws

ROLES DISPONIBLES:
  🧠 Teen (Adolescente)
  👨‍🏫 Maestro (Educación)
  👨‍👩‍👧 Padre (Familia)
  💼 Vendedor (Negocios)
  ⚙️ Admin (Sistema)

CARACTERÍSTICAS:
  ✓ 16 Librerías Psicológicas
  ✓ 6 Dinámicas Educativas
  ✓ Protocolo de Crisis (5 niveles)
  ✓ Acompañamiento sin imposición
  ✓ Autonomía total
  ✓ Cotizador integrado

════════════════════════════════════════════════════════════════════════════════

⏳ Servidor iniciando (espera 3-5 segundos)...

"@ -ForegroundColor Green

# Esperar a que se inicie
Start-Sleep -Seconds 3

# Abrir navegador
Write-Host "🌐 Abriendo navegador..." -ForegroundColor Cyan
Start-Process "http://localhost:8000/panel" 2>$null

Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                    ✨ AURORA v2 OPERATIVO - SIN PARAR ✨
════════════════════════════════════════════════════════════════════════════════

Sistema EN LÍNEA. Presiona Ctrl+C para detener.

"@ -ForegroundColor Green

# Lanzar servidor
python servidor_aurora_completo.py
