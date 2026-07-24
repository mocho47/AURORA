# AURORA v2 - INTEGRACIÓN FINAL
# Lee API Keys + Repositorio GitHub + Inicia Sistema

Write-Host @"
════════════════════════════════════════════════════════════════════════════════
                    AURORA v2 - INTEGRACIÓN COMPLETA
                  (API Keys + GitHub + Sincronización)
════════════════════════════════════════════════════════════════════════════════
"@ -ForegroundColor Cyan

$coreDir = "$PSScriptRoot\CORE"
Set-Location $coreDir

# ============== PASO 1: VALIDAR API KEYS ==============
Write-Host "`n[1/5] Validando API Keys configuradas..." -ForegroundColor Yellow

python -c @"
from config_integrado import APIKeys

print()
disponibles = APIKeys.validar()

for api, activo in disponibles.items():
    estado = '✓' if activo else '✗'
    print(f'  {estado} {api.upper()}')

total = sum(disponibles.values())
print(f'\nAPIs disponibles: {total}/5')
print()
"@

# ============== PASO 2: LEER REPOSITORIO GITHUB ==============
Write-Host "[2/5] Verificando repositorio GitHub..." -ForegroundColor Yellow

python -c @"
from config_integrado import RepositorioGitHub

config = RepositorioGitHub.obtener_config()
print()
print(f'  Repositorio: {RepositorioGitHub.get_repo_nombre()}')
print(f'  URL: {RepositorioGitHub.get_repo_url()}')
print(f'  Rama: {config.get(\"rama\", \"main\")}')
print()
"@

# ============== PASO 3: LEER CONFIGURACIÓN SYNC ==============
Write-Host "[3/5] Configuración de sincronización..." -ForegroundColor Yellow

python -c @"
from config_integrado import ConfigSync

sync = ConfigSync.cargar()
print()
print(f'  Tu PC: {sync[\"tu_pc\"][\"nombre\"]} ({sync[\"tu_pc\"][\"ip\"]}:8000)')
print(f'  PC Esposa: {sync[\"pc_esposa\"][\"nombre\"]} ({sync[\"pc_esposa\"][\"ip\"]}:8000)')
print(f'  Modo: {sync[\"modo\"]}')
print()
"@

# ============== PASO 4: VALIDAR MOTORES ==============
Write-Host "[4/5] Validando 17 motores..." -ForegroundColor Yellow

python -c @"
from config_integrado import MotoresConfig, NegociosConfig

motores = MotoresConfig.obtener_motores_activos()
negocios = NegociosConfig.obtener_negocios_principales()

print()
print(f'  Motores activos: {len(motores)}/17')
print(f'  Negocios principales: {len(negocios)}')
print()
print('  Negocios:')
for negocio in negocios:
    print(f'    ✓ {negocio}')
print()
"@

# ============== PASO 5: INICIAR AURORA ==============
Write-Host "[5/5] Iniciando AURORA v2 con configuración integrada..." -ForegroundColor Yellow

python -c @"
from config_integrado import inicializar_config

config = inicializar_config()
"@

Write-Host "`nInstalando dependencias finales..." -ForegroundColor Green

$dependencias = @(
    "websockets==12.0",
    "python-dotenv==1.0.0"
)

foreach ($dep in $dependencias) {
    python -m pip install -q $dep 2>$null
}

Write-Host "✓ Dependencias listas" -ForegroundColor Green

# ============== LANZAR AURORA ==============
Write-Host @"
`n════════════════════════════════════════════════════════════════════════════════
                         🚀 INICIANDO AURORA v2
════════════════════════════════════════════════════════════════════════════════

COMPONENTES ACTIVOS:
  ✓ Cerebro inteligente (sin censura)
  ✓ Sincronización 2 PCs
  ✓ API Keys configuradas
  ✓ Repositorio GitHub conectado
  ✓ 17 Motores listos

ACCESO:
  • Panel: http://localhost:8000
  • API Docs: http://localhost:8000/docs

PRÓXIMOS PASOS:
  1. El servidor se abre en el navegador
  2. Comienza a usar AURORA
  3. Verás sincronización en PC esposa

════════════════════════════════════════════════════════════════════════════════
"@ -ForegroundColor Green

Write-Host "`n⏳ Iniciando servidor Aurora..." -ForegroundColor Cyan

# Abrir navegador
Start-Sleep -Seconds 2
Start-Process "http://localhost:8000" 2>$null

# Iniciar servidor
python aurora_server.py
