# Script de Unificación COMPLETA - Incluye carpetas "r" y Google Fotos
# Centraliza TODOS los videos de todas las fuentes

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   UNIFICADOR COMPLETO - Todas las Fuentes de Videos  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CREAR ESTRUCTURA EXPANDIDA
# ════════════════════════════════════════════════════════════════════════════

$CARPETA_MAESTRO = "C:\VIDEOS_MAESTROS"
$CARPETA_ORIGINAL = "C:\Users\Administrador\Videos"

Write-Host "📁 PASO 1: Crear estructura completa..." -ForegroundColor Yellow
Write-Host ""

# Crear carpeta raíz
if (-not (Test-Path $CARPETA_MAESTRO)) {
    New-Item -ItemType Directory -Path $CARPETA_MAESTRO -Force | Out-Null
    Write-Host "✅ Creada: $CARPETA_MAESTRO"
}

# Crear subcarpetas expandidas
$SUBCARPETAS = @(
    "ATF_ORIGINALES",           # Carpetas r5, r10, r11, r6, etc
    "PROCESOS",                 # En edición
    "TERMINADOS",               # Listos para publicar
    "ATF_PROCESADOS",          # Ya publicados
    "GOOGLE_FOTOS",            # Desde Google Fotos
    "GOOGLE_DRIVE",            # Desde Google Drive
    "STOCK",                   # Stock/plan 1
    "OTROS"                    # Diversos
)

foreach ($subcarpeta in $SUBCARPETAS) {
    $ruta = Join-Path $CARPETA_MAESTRO $subcarpeta
    if (-not (Test-Path $ruta)) {
        New-Item -ItemType Directory -Path $ruta -Force | Out-Null
        Write-Host "✅ Subcarpeta: $subcarpeta"
    }
}

Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 2: MAPEO EXPANDIDO DE CARPETAS
# ════════════════════════════════════════════════════════════════════════════

Write-Host "🎬 PASO 2: Unificar videos de TODAS las carpetas..." -ForegroundColor Yellow
Write-Host ""

# Mapeo: carpeta origen → destino tipificado
$MAPEO = @{
    # Originales (carpetas "r")
    "r5"                        = "ATF_ORIGINALES"
    "r5_ext"                    = "ATF_ORIGINALES"
    "r10_ext"                   = "ATF_ORIGINALES"
    "r11_ext"                   = "ATF_ORIGINALES"
    "r6_ext"                    = "ATF_ORIGINALES"

    # En proceso
    "procesos"                  = "PROCESOS"

    # Terminados
    "terminados"                = "TERMINADOS"

    # ATF procesados
    "atf procesados"            = "ATF_PROCESADOS"

    # Stock
    "videosplan1retrofit"       = "STOCK"

    # Diversos
    "Almacenamiento de Google One_files" = "GOOGLE_DRIVE"
    "Captures"                  = "OTROS"
    "DRIVE_DOWNLOADS"           = "GOOGLE_DRIVE"
    "familiar"                  = "OTROS"
    "familliar"                 = "OTROS"
    "publicados"                = "OTROS"
}

$TOTAL_MOVIDOS = 0
$TOTAL_EXISTENTES = 0

foreach ($carpetaOrigen in $MAPEO.Keys) {
    $rutaOrigen = Join-Path $CARPETA_ORIGINAL $carpetaOrigen
    $carpetaDestino = $MAPEO[$carpetaOrigen]
    $rutaDestino = Join-Path $CARPETA_MAESTRO $carpetaDestino

    if (Test-Path $rutaOrigen) {
        Write-Host "   📂 $carpetaOrigen → $carpetaDestino"

        $videos = Get-ChildItem -Path $rutaOrigen -File -Include "*.mp4","*.mov","*.avi","*.mkv" -ErrorAction SilentlyContinue

        foreach ($video in $videos) {
            $destino = Join-Path $rutaDestino $video.Name

            if (Test-Path $destino) {
                $TOTAL_EXISTENTES++
            } else {
                try {
                    Copy-Item -Path $video.FullName -Destination $destino -Force
                    $TOTAL_MOVIDOS++
                    Write-Host "      ✅ $($video.Name)"
                } catch {
                    Write-Host "      ❌ Error: $($video.Name)"
                }
            }
        }

        Write-Host "      └─ Total: $($videos.Count) videos"
        Write-Host ""
    }
}

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: INFORMACIÓN GOOGLE FOTOS/DRIVE
# ════════════════════════════════════════════════════════════════════════════

Write-Host "🔗 PASO 3: Acceso a Google Fotos y Drive..." -ForegroundColor Yellow
Write-Host ""

$googlePhotosPath = "$env:USERPROFILE\AppData\Local\Google\Photos"
$googleDrivePath = "$env:USERPROFILE\Google Drive"

Write-Host "   📱 Buscar Google Fotos:"
if (Test-Path $googlePhotosPath) {
    Write-Host "      ✅ Ubicación encontrada: $googlePhotosPath"
    Write-Host "      📌 Para sincronizar: Instala Google Photos Desktop app"
    Write-Host "      📌 O accede a: https://photos.google.com"
} else {
    Write-Host "      ℹ️  Google Photos app no detectado localmente"
    Write-Host "      📌 Puedes acceder a: https://photos.google.com"
}

Write-Host ""
Write-Host "   ☁️  Buscar Google Drive:"
if (Test-Path $googleDrivePath) {
    Write-Host "      ✅ Google Drive sincronizado en: $googleDrivePath"
    $driveVideos = Get-ChildItem -Path $googleDrivePath -File -Include "*.mp4","*.mov","*.avi" -Recurse -ErrorAction SilentlyContinue
    if ($driveVideos) {
        Write-Host "      📊 Videos encontrados: $($driveVideos.Count)"
        foreach ($video in $driveVideos) {
            Write-Host "         └─ $($video.Name)"
        }
    }
} else {
    Write-Host "      ℹ️  Google Drive app no detectado"
    Write-Host "      📌 Instala Google Drive para sincronizar"
}

Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: CREAR METADATOS COMPLETOS
# ════════════════════════════════════════════════════════════════════════════

Write-Host "📊 PASO 4: Crear metadatos de tipificación..." -ForegroundColor Yellow
Write-Host ""

$TIPIFICACION = @{
    "ATF_ORIGINALES" = @{
        "descripcion" = "Videos originales sin editar (r5, r10, r11, etc)"
        "estado" = "NUEVO"
        "prioridad" = "ALTA"
        "procesamiento" = "Requiere edición"
    }
    "PROCESOS" = @{
        "descripcion" = "Videos en proceso de edición/publicación"
        "estado" = "EN_PROGRESO"
        "prioridad" = "MEDIA"
        "procesamiento" = "En curso"
    }
    "TERMINADOS" = @{
        "descripcion" = "Videos completamente editados y listos para publicar"
        "estado" = "LISTO"
        "prioridad" = "ALTA"
        "procesamiento" = "Completado - Listo para usar"
    }
    "ATF_PROCESADOS" = @{
        "descripcion" = "Videos ATF ya procesados/publicados"
        "estado" = "PUBLICADO"
        "prioridad" = "BAJA"
        "procesamiento" = "Archivado"
    }
    "GOOGLE_FOTOS" = @{
        "descripcion" = "Videos sincronizados de Google Fotos"
        "estado" = "PENDIENTE"
        "prioridad" = "MEDIA"
        "procesamiento" = "Requiere descarga y edición"
        "acceso" = "https://photos.google.com"
    }
    "GOOGLE_DRIVE" = @{
        "descripcion" = "Videos de Google Drive"
        "estado" = "DISPONIBLE"
        "prioridad" = "MEDIA"
        "procesamiento" = "Requiere revisión"
    }
    "STOCK" = @{
        "descripcion" = "Stock de videos plan 1 retrofit"
        "estado" = "ARCHIVO"
        "prioridad" = "BAJA"
        "procesamiento" = "Archivo - Usar si es necesario"
    }
    "OTROS" = @{
        "descripcion" = "Videos diversos/varios"
        "estado" = "REVISAR"
        "prioridad" = "BAJA"
        "procesamiento" = "Requiere clasificación"
    }
}

# Crear JSON de tipificación
$tipoJson = @{}
$totalVideos = 0

foreach ($carpeta in $SUBCARPETAS) {
    $info = $TIPIFICACION[$carpeta]
    $rutaCarpeta = Join-Path $CARPETA_MAESTRO $carpeta

    if (Test-Path $rutaCarpeta) {
        $videos = Get-ChildItem -Path $rutaCarpeta -File | Measure-Object
        $infoCompleta = $info.Clone()
        $infoCompleta["cantidad_videos"] = $videos.Count
        $infoCompleta["ubicacion"] = $rutaCarpeta
        $totalVideos += $videos.Count

        $tipoJson[$carpeta] = $infoCompleta
    }
}

$jsonRuta = Join-Path $CARPETA_MAESTRO "TIPIFICACION.json"
$tipoJson | ConvertTo-Json -Depth 3 | Set-Content -Path $jsonRuta -Encoding UTF8

Write-Host "✅ Archivo TIPIFICACION.json creado"
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: CREAR ARCHIVO ÍNDICE COMPLETO
# ════════════════════════════════════════════════════════════════════════════

$indiceRuta = Join-Path $CARPETA_MAESTRO "INDICE_MAESTRO.txt"

$contenidoIndice = @"
╔════════════════════════════════════════════════════════════╗
║      ÍNDICE MAESTRO CENTRALIZADO - TODOS LOS VIDEOS       ║
║                  Generado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')                  ║
╚════════════════════════════════════════════════════════════╝

📁 UBICACIÓN CENTRAL: $CARPETA_MAESTRO

═══════════════════════════════════════════════════════════════

CONTENIDO POR CARPETA:

"@

foreach ($carpeta in $SUBCARPETAS) {
    $ruta = Join-Path $CARPETA_MAESTRO $carpeta
    if (Test-Path $ruta) {
        $cantidad = (Get-ChildItem -Path $ruta -File | Measure-Object).Count
        $tamaño = (Get-ChildItem -Path $ruta -File | Measure-Object -Sum Length).Sum
        $tipo = $TIPIFICACION[$carpeta]

        $contenidoIndice += @"

📂 $carpeta/
   ├─ Descripción: $($tipo['descripcion'])
   ├─ Estado: $($tipo['estado'])
   ├─ Prioridad: $($tipo['prioridad'])
   ├─ Procesamiento: $($tipo['procesamiento'])
   ├─ Cantidad: $cantidad videos
   └─ Tamaño: $([math]::Round($tamaño/1MB,2)) MB

"@
    }
}

$contenidoIndice += @"

═══════════════════════════════════════════════════════════════

📊 RESUMEN TOTAL:
   Total de videos unificados: $totalVideos
   Tamaño total: $([math]::Round((Get-ChildItem -Path $CARPETA_MAESTRO -File -Recurse | Measure-Object -Sum Length).Sum/1GB,2)) GB
   Última actualización: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

═══════════════════════════════════════════════════════════════

🔗 FUENTES EXTERNAS DISPONIBLES:

📱 GOOGLE FOTOS:
   URL: https://photos.google.com
   Estado: Sin sincronizar localmente
   Opción 1: Instalar Google Photos app
   Opción 2: Acceder web y descargar manualmente
   Instrucciones: Ve a Google Fotos → Selecciona videos → Descargar

☁️  GOOGLE DRIVE:
   Ubicación: $googleDrivePath
   Estado: $(if (Test-Path $googleDrivePath) { "✅ Sincronizado" } else { "❌ No sincronizado" })
   Instrucciones: Instala Google Drive desktop app para sincronizar

═══════════════════════════════════════════════════════════════

🎯 PRÓXIMOS PASOS:

1️⃣  USAR VIDEOS ACTUALES:
   └─ Abre: C:\Users\Administrador\Documents\ATF_Excelencia.exe
   └─ Click: "Escanear Videos"
   └─ Sistema cargará todos los videos centralizados

2️⃣  AGREGAR DE GOOGLE FOTOS:
   └─ Ve a: https://photos.google.com
   └─ Selecciona videos interesantes
   └─ Descarga y copia a: $CARPETA_MAESTRO\GOOGLE_FOTOS\
   └─ Reinicia ATF para que rescannee

3️⃣  AGREGAR DE GOOGLE DRIVE:
   └─ Instala Google Drive app
   └─ Copia videos a: $CARPETA_MAESTRO\GOOGLE_DRIVE\
   └─ Reinicia ATF para que rescannee

═══════════════════════════════════════════════════════════════

✅ LISTO PARA USAR CON ATF EXCELENCIA

"@

Set-Content -Path $indiceRuta -Value $contenidoIndice -Encoding UTF8
Write-Host "✅ Archivo INDICE_MAESTRO.txt creado"
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      ✅ UNIFICACIÓN COMPLETA REALIZADA ✅            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 RESULTADOS:"
Write-Host "   ✅ Videos nuevos unificados: $TOTAL_MOVIDOS"
Write-Host "   ✅ Videos ya existentes: $TOTAL_EXISTENTES"
Write-Host "   ✅ Total disponibles: $totalVideos"
Write-Host "   ✅ 8 carpetas organizadas por tipo"
Write-Host "   ✅ Acceso a Google Fotos: documentado"
Write-Host "   ✅ Acceso a Google Drive: documentado"
Write-Host ""

Write-Host "📁 UBICACIÓN: $CARPETA_MAESTRO"
Write-Host ""

Write-Host "📖 ARCHIVOS CREADOS:"
Write-Host "   1. INDICE_MAESTRO.txt (guía completa)"
Write-Host "   2. TIPIFICACION.json (metadatos)"
Write-Host ""

Write-Host "🚀 PRÓXIMO PASO:"
Write-Host "   1. Abre: C:\Users\Administrador\Documents\ATF_Excelencia.exe"
Write-Host "   2. Click: 'Escanear Videos'"
Write-Host "   3. Sistema cargará $totalVideos videos automáticamente"
Write-Host ""

# Abrir carpeta
Read-Host "Presiona ENTER para abrir C:\VIDEOS_MAESTROS"
Invoke-Item $CARPETA_MAESTRO
