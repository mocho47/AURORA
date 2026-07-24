# Script para centralizar TODOS los videos en una sola carpeta
# Uso: .\centralizar_videos.ps1

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CENTRALIZADOR DE VIDEOS - ATF EXCELENCIA" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Crear carpeta centralizada
$CARPETA_MAESTRO = "C:\VIDEOS_MAESTROS"

if (-not (Test-Path $CARPETA_MAESTRO)) {
    Write-Host "📁 Creando carpeta centralizada: $CARPETA_MAESTRO"
    New-Item -ItemType Directory -Path $CARPETA_MAESTRO -Force | Out-Null
    Write-Host "✅ Carpeta creada"
} else {
    Write-Host "📁 Carpeta ya existe: $CARPETA_MAESTRO"
}

Write-Host ""

# Ubicaciones de videos a buscar
$UBICACIONES = @(
    "C:\Users\Administrador\Videos",
    "C:\Users\Administrador\Videos\",
    "$env:USERPROFILE\Videos",
    "C:\AURORA\VIDEOS",
    "C:\NEXUS\VIDEOS",
    "C:\NEXUS-CONTENEDOR\VIDEOS"
)

$TOTAL_MOVIDOS = 0
$TOTAL_EXISTENTES = 0
$EXTENSIONES = @("*.mp4", "*.mov", "*.avi", "*.mkv", "*.webm")

# Buscar y mover videos
foreach ($ubicacion in $UBICACIONES) {
    if (Test-Path $ubicacion) {
        Write-Host "🔍 Buscando videos en: $ubicacion"

        foreach ($ext in $EXTENSIONES) {
            $videos = Get-ChildItem -Path $ubicacion -Filter $ext -File -ErrorAction SilentlyContinue

            foreach ($video in $videos) {
                $destino = Join-Path $CARPETA_MAESTRO $video.Name

                if (Test-Path $destino) {
                    Write-Host "   ⏭️  Ya existe: $($video.Name) (saltando)"
                    $TOTAL_EXISTENTES++
                } else {
                    try {
                        Write-Host "   ➡️  Moviendo: $($video.Name) ($([math]::Round($video.Length/1MB,2)) MB)"
                        Copy-Item -Path $video.FullName -Destination $destino -Force
                        $TOTAL_MOVIDOS++
                    } catch {
                        Write-Host "   ❌ Error al copiar: $($video.Name) - $_"
                    }
                }
            }
        }
    } else {
        # Silencioso si no existe
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ CENTRALIZACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Resumen:"
Write-Host "   Videos movidos:    $TOTAL_MOVIDOS"
Write-Host "   Ya existían:       $TOTAL_EXISTENTES"
Write-Host "   Carpeta maestro:   $CARPETA_MAESTRO"
Write-Host ""

# Contar total
$TOTAL_EN_MAESTRO = (Get-ChildItem -Path $CARPETA_MAESTRO -File | Measure-Object).Count
Write-Host "   TOTAL VIDEOS CENTRALIZADOS: $TOTAL_EN_MAESTRO"
Write-Host ""

# Actualizar ATF
Write-Host "🔧 Actualizando configuración de ATF..."

$ARCHIVO_PY = "C:\AURORA\publicador_inteligente_atf.py"
if (Test-Path $ARCHIVO_PY) {
    $contenido = Get-Content $ARCHIVO_PY -Raw

    # Reemplazar ruta de videos
    $contenido = $contenido -replace 'VIDEOS_DIR = "C:\\Users\\Administrador\\Videos"', `
                            "VIDEOS_DIR = `"$CARPETA_MAESTRO`""

    Set-Content -Path $ARCHIVO_PY -Value $contenido -Encoding UTF8
    Write-Host "✅ ATF actualizado para usar: $CARPETA_MAESTRO"
} else {
    Write-Host "⚠️  Archivo publicador_inteligente_atf.py no encontrado"
}

Write-Host ""
Write-Host "🎉 ¡LISTO! Ahora ejecuta: C:\Users\Administrador\Documents\ATF_Excelencia.exe"
Write-Host "   El dashboard escaneará automáticamente desde: $CARPETA_MAESTRO"
Write-Host ""

# Opcional: Abrir carpeta
Read-Host "Presiona ENTER para abrir la carpeta de videos centralizados"
Invoke-Item $CARPETA_MAESTRO
