# AURORA v2 - LAUNCHER COMPLETO
# Inicia todo en paralelo: Cerebro + Sync + Servidor

Write-Host @"
════════════════════════════════════════════════════════════════════════════════
                         AURORA v2 - LANZAMIENTO
                          Sistema inteligente operativo
════════════════════════════════════════════════════════════════════════════════
"@ -ForegroundColor Cyan

$coreDir = "$PSScriptRoot\CEREBRO"
$scriptDir = "$PSScriptRoot"

# Cambiar directorio
Set-Location $coreDir
Write-Host "📍 Directorio: $coreDir" -ForegroundColor Yellow

# Instalar dependencias si no existen
Write-Host "`n📦 Instalando dependencias..." -ForegroundColor Yellow

$dependencias = @(
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    "pydantic==1.10.12",
    "anthropic==0.25.1",
    "groq==0.4.2",
    "aiohttp==3.9.1",
    "websockets==12.0",
    "python-dotenv==1.0.0"
)

foreach ($dep in $dependencias) {
    python -m pip install -q $dep 2>$null
}

Write-Host "✓ Dependencias instaladas" -ForegroundColor Green

# Crear directorio de memorias si no existen
Write-Host "`n📁 Creando directorios necesarios..." -ForegroundColor Yellow

$directorios = @(
    "C:\AURORA\MEMORIA\episodica",
    "C:\AURORA\MEMORIA\semantica",
    "C:\AURORA\MEMORIA\consolidacion",
    "C:\AURORA\DATA",
    "C:\AURORA\SYNC",
    "C:\AURORA\MOTORES\output"
)

foreach ($dir in $directorios) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ $dir"
    }
}

# Crear archivo de configuración .env
Write-Host "`n⚙️  Configurando variables de entorno..." -ForegroundColor Yellow

$envContent = @"
# AURORA v2 - Variables de entorno

# APIs
CLAUDE_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
ZAI_API_KEY=your_key_here

# Sincronización
SYNC_TU_PC_IP=192.168.1.100
SYNC_PC_ESPOSA_IP=192.168.1.101
SYNC_PUERTO=9000

# Rutas
AURORA_ROOT=C:\AURORA
MEMORIA_DIR=C:\AURORA\MEMORIA
DATA_DIR=C:\AURORA\DATA
"@

if (!(Test-Path "$coreDir\.env")) {
    Set-Content -Path "$coreDir\.env" -Value $envContent
    Write-Host "✓ Archivo .env creado" -ForegroundColor Green
} else {
    Write-Host "✓ Archivo .env ya existe" -ForegroundColor Green
}

# Iniciar componentes en paralelo
Write-Host @"
`n🚀 Iniciando componentes AURORA en paralelo:
  • Aurora Cerebro (razonamiento inteligente)
  • Aurora Sync (sincronización PC)
  • Aurora Server (API FastAPI)
"@ -ForegroundColor Green

# Terminal 1: Sync
Write-Host "`n[1/3] Iniciando Aurora Sync..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$coreDir'; python aurora_sync.py"

Start-Sleep -Seconds 2

# Terminal 2: Cerebro (opcional, corre en background del servidor)
Write-Host "[2/3] Aurora Cerebro integrado en servidor..." -ForegroundColor Cyan

# Terminal 3: Servidor FastAPI
Write-Host "[3/3] Iniciando Aurora Server (FastAPI)..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$coreDir'
Write-Host '════════════════════════════════════════════════════════════════' -ForegroundColor Yellow
Write-Host 'AURORA SERVER - FastAPI' -ForegroundColor Cyan
Write-Host '════════════════════════════════════════════════════════════════' -ForegroundColor Yellow
Write-Host 'Iniciando en puerto 8000...' -ForegroundColor Green
Write-Host ''
python aurora_server.py
"@

Start-Sleep -Seconds 3

# Esperar a que servidor inicie
Write-Host "`n⏳ Esperando que servidor inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar que servidor está vivo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue

    if ($response.StatusCode -eq 200) {
        Write-Host "`n✓ Servidor respondiendo en http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "`n⚠️  Servidor puede estar inicializando, intenta en unos segundos..." -ForegroundColor Yellow
}

# Abrir navegador
Write-Host "`n🌐 Abriendo navegador..." -ForegroundColor Green

Start-Sleep -Seconds 2

try {
    Start-Process "http://localhost:8000"
} catch {
    Write-Host "⚠️  No se pudo abrir navegador automáticamente" -ForegroundColor Yellow
    Write-Host "Accede manualmente a: http://localhost:8000" -ForegroundColor Yellow
}

# Información de acceso
Write-Host @"

════════════════════════════════════════════════════════════════════════════════
                      ✓ AURORA v2 COMPLETAMENTE OPERATIVO
════════════════════════════════════════════════════════════════════════════════

ACCESO:
  • Panel principal:    http://localhost:8000
  • API REST:           http://localhost:8000/docs
  • WebSocket:          ws://localhost:8000/ws

COMPONENTES EJECUTÁNDOSE:
  • ✓ Aurora Cerebro    (razonamiento sin censura)
  • ✓ Aurora Sync       (sincronización PC ↔ PC)
  • ✓ Aurora Server     (FastAPI + endpoints)

SINCRONIZACIÓN:
  • Tu PC:    192.168.1.100:8000
  • PC Esposa: 192.168.1.101:8000
  • Estado:    Bidireccional (sincronización cada 5 segundos)

CARACTERÍSTICAS:
  ✓ Razonamiento profundo sin censura
  ✓ Memoria generativa (episódica + semántica)
  ✓ Aprendizaje automático
  ✓ Toma de decisiones autónoma
  ✓ Sincronización multi-PC en tiempo real
  ✓ Cotizador, pedidos, imágenes (en construcción)

PRÓXIMOS PASOS:
  1. Configura API Keys en .env
  2. Accede a http://localhost:8000
  3. Comienza a usar AURORA

════════════════════════════════════════════════════════════════════════════════
                    Presiona Ctrl+C para detener AURORA
════════════════════════════════════════════════════════════════════════════════
"@ -ForegroundColor Green

# Mantener ventana activa
Write-Host ""
Read-Host "Presiona Enter para ver logs del servidor en tiempo real"
