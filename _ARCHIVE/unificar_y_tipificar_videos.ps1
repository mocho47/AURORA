# Script de Unificación y Tipificación de Videos ATF
# Centraliza TODOS los videos y los organiza por tipo

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    UNIFICADOR Y TIPIFICADOR DE VIDEOS - ATF           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CREAR ESTRUCTURA CENTRALIZADA
# ════════════════════════════════════════════════════════════════════════════

$CARPETA_MAESTRO = "C:\VIDEOS_MAESTROS"
$CARPETA_ORIGINAL = "C:\Users\Administrador\Videos"

Write-Host "📁 PASO 1: Crear estructura centralizada..." -ForegroundColor Yellow
Write-Host ""

# Crear carpeta raíz
if (-not (Test-Path $CARPETA_MAESTRO)) {
    New-Item -ItemType Directory -Path $CARPETA_MAESTRO -Force | Out-Null
    Write-Host "✅ Creada: $CARPETA_MAESTRO"
} else {
    Write-Host "ℹ️  Existe: $CARPETA_MAESTRO"
}

# Crear subcarpetas por tipo
$SUBCARPETAS = @(
    "PROCESOS",
    "TERMINADOS",
    "ATF_PROCESADOS",
    "ORIGINALES",
    "STOCK",
    "OTROS"
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
# PASO 2: MAPEAR Y MOVER VIDEOS CON TIPIFICACIÓN
# ════════════════════════════════════════════════════════════════════════════

Write-Host "🎬 PASO 2: Unificar videos de todas las carpetas..." -ForegroundColor Yellow
Write-Host ""

$MAPEO = @{
    "procesos"              = "PROCESOS"
    "terminados"            = "TERMINADOS"
    "atf procesados"        = "ATF_PROCESADOS"
    "r10_ext"               = "ORIGINALES"
    "r11_ext"               = "ORIGINALES"
    "r5_ext"                = "ORIGINALES"
    "videosplan1retrofit"   = "STOCK"
    "Almacenamiento de Google One_files" = "OTROS"
}

$TOTAL_MOVIDOS = 0
$TOTAL_EXISTENTES = 0

foreach ($carpetaOrigen in $MAPEO.Keys) {
    $rutaOrigen = Join-Path $CARPETA_ORIGINAL $carpetaOrigen
    $carpetaDestino = $MAPEO[$carpetaOrigen]
    $rutaDestino = Join-Path $CARPETA_MAESTRO $carpetaDestino

    if (Test-Path $rutaOrigen) {
        Write-Host "   📂 Procesando: $carpetaOrigen → $carpetaDestino"

        $videos = Get-ChildItem -Path $rutaOrigen -File -Include "*.mp4","*.mov","*.avi","*.mkv" -ErrorAction SilentlyContinue

        foreach ($video in $videos) {
            $destino = Join-Path $rutaDestino $video.Name

            if (Test-Path $destino) {
                Write-Host "      ⏭️  Ya existe: $($video.Name)"
                $TOTAL_EXISTENTES++
            } else {
                try {
                    Copy-Item -Path $video.FullName -Destination $destino -Force
                    Write-Host "      ✅ Copiado: $($video.Name) ($([math]::Round($video.Length/1MB,2)) MB)"
                    $TOTAL_MOVIDOS++
                } catch {
                    Write-Host "      ❌ Error: $($video.Name) - $_"
                }
            }
        }

        Write-Host "      ├─ Total en $carpetaOrigen: $($videos.Count)"
        Write-Host ""
    }
}

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: CREAR ARCHIVO DE TIPIFICACIÓN
# ════════════════════════════════════════════════════════════════════════════

Write-Host "📊 PASO 3: Crear metadatos de tipificación..." -ForegroundColor Yellow
Write-Host ""

$TIPIFICACION = @{
    "PROCESOS" = @{
        "descripcion" = "Videos en proceso de edición/publicación"
        "estado" = "EN_PROGRESO"
        "prioridad" = "MEDIA"
    }
    "TERMINADOS" = @{
        "descripcion" = "Videos completamente editados y listos"
        "estado" = "LISTO"
        "prioridad" = "ALTA"
    }
    "ATF_PROCESADOS" = @{
        "descripcion" = "Videos ATF ya procesados/publicados"
        "estado" = "PUBLICADO"
        "prioridad" = "BAJA"
    }
    "ORIGINALES" = @{
        "descripcion" = "Videos originales sin editar"
        "estado" = "NUEVO"
        "prioridad" = "ALTA"
    }
    "STOCK" = @{
        "descripcion" = "Stock de videos de plan 1"
        "estado" = "ARCHIVO"
        "prioridad" = "BAJA"
    }
    "OTROS" = @{
        "descripcion" = "Videos diversos"
        "estado" = "REVISAR"
        "prioridad" = "BAJA"
    }
}

# Crear archivo JSON de tipificación
$tipoJson = @{}
foreach ($carpeta in $SUBCARPETAS) {
    $info = $TIPIFICACION[$carpeta]
    $rutaCarpeta = Join-Path $CARPETA_MAESTRO $carpeta

    if (Test-Path $rutaCarpeta) {
        $videos = Get-ChildItem -Path $rutaCarpeta -File | Measure-Object
        $infoCompleta = $info.Clone()
        $infoCompleta["cantidad_videos"] = $videos.Count
        $infoCompleta["ubicacion"] = $rutaCarpeta

        $tipoJson[$carpeta] = $infoCompleta
    }
}

$jsonRuta = Join-Path $CARPETA_MAESTRO "tipificacion.json"
$tipoJson | ConvertTo-Json | Set-Content -Path $jsonRuta -Encoding UTF8

Write-Host "✅ Archivo creado: tipificacion.json"
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: GENERAR REPORTE
# ════════════════════════════════════════════════════════════════════════════

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  📊 REPORTE FINAL DE UNIFICACIÓN" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$TOTAL_EN_MAESTRO = 0
foreach ($carpeta in $SUBCARPETAS) {
    $ruta = Join-Path $CARPETA_MAESTRO $carpeta
    if (Test-Path $ruta) {
        $cantidad = (Get-ChildItem -Path $ruta -File | Measure-Object).Count
        $tamaño = (Get-ChildItem -Path $ruta -File | Measure-Object -Sum Length).Sum
        $TOTAL_EN_MAESTRO += $cantidad

        Write-Host "📂 $carpeta"
        Write-Host "   ├─ Cantidad: $cantidad videos"
        Write-Host "   ├─ Tamaño: $([math]::Round($tamaño/1MB,2)) MB"
        Write-Host "   └─ Estado: $($TIPIFICACION[$carpeta]['estado'])"
        Write-Host ""
    }
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "✅ VIDEOS COPIADOS:       $TOTAL_MOVIDOS"
Write-Host "⏭️  YA EXISTÍAN:           $TOTAL_EXISTENTES"
Write-Host "📊 TOTAL UNIFICADOS:      $TOTAL_EN_MAESTRO"
Write-Host ""
Write-Host "📁 UBICACIÓN CENTRALIZADA: $CARPETA_MAESTRO"
Write-Host "🔧 TIPIFICACIÓN:          $jsonRuta"
Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: ACTUALIZAR ATF
# ════════════════════════════════════════════════════════════════════════════

Write-Host "⚙️  PASO 5: Actualizar configuración de ATF..." -ForegroundColor Yellow
Write-Host ""

$ARCHIVOS_ACTUALIZAR = @(
    "C:\AURORA\publicador_inteligente_atf.py",
    "C:\AURORA\app_atf_excelencia.py"
)

foreach ($archivo in $ARCHIVOS_ACTUALIZAR) {
    if (Test-Path $archivo) {
        $contenido = Get-Content $archivo -Raw -Encoding UTF8

        # Reemplazar paths antiguos
        $contenido = $contenido -replace 'C:\\Users\\Administrador\\Videos', $CARPETA_MAESTRO
        $contenido = $contenido -replace '"C:\\Users\\Administrador\\Videos"', "`"$CARPETA_MAESTRO`""

        Set-Content -Path $archivo -Value $contenido -Encoding UTF8
        Write-Host "✅ Actualizado: $archivo"
    }
}

Write-Host ""

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: CREAR ARCHIVO ÍNDICE
# ════════════════════════════════════════════════════════════════════════════

$indiceRuta = Join-Path $CARPETA_MAESTRO "INDICE.txt"

$contenidoIndice = @"
╔════════════════════════════════════════════════════════════╗
║          ÍNDICE DE VIDEOS MAESTRO CENTRALIZADO            ║
║                  Generado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')                  ║
╚════════════════════════════════════════════════════════════╝

📁 UBICACIÓN CENTRAL: $CARPETA_MAESTRO

CARPETAS Y TIPIFICACIÓN:
───────────────────────────────────────────────────────────────

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
   ├─ Cantidad: $cantidad videos
   └─ Tamaño: $([math]::Round($tamaño/1MB,2)) MB

"@
    }
}

$contenidoIndice += @"

───────────────────────────────────────────────────────────────

📊 RESUMEN:
   Total de videos centralizados: $TOTAL_EN_MAESTRO
   Tamaño total: $([math]::Round((Get-ChildItem -Path $CARPETA_MAESTRO -File -Recurse | Measure-Object -Sum Length).Sum/1GB,2)) GB
   Última actualización: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

🔄 PRÓXIMOS PASOS:
   1. Abrir: C:\Users\Administrador\Documents\ATF_Excelencia.exe
   2. Click: "Escanear Videos"
   3. Sistema detectará automáticamente: $TOTAL_EN_MAESTRO videos

✅ LISTA PARA USAR CON ATF EXCELENCIA

"@

Set-Content -Path $indiceRuta -Value $contenidoIndice -Encoding UTF8
Write-Host "✅ Archivo índice creado: INDICE.txt"

# ════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        ✅ UNIFICACIÓN COMPLETADA CON ÉXITO ✅         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 RESULTADOS:"
Write-Host "   ✅ $TOTAL_MOVIDOS videos nuevos unificados"
Write-Host "   ✅ $TOTAL_EN_MAESTRO videos totales disponibles"
Write-Host "   ✅ 6 carpetas tipificadas por estado"
Write-Host "   ✅ ATF configurado para carpeta centralizada"
Write-Host ""

Write-Host "📁 ACCESO:"
Write-Host "   Abre: $CARPETA_MAESTRO"
Write-Host "   Ver: INDICE.txt (descripción completa)"
Write-Host ""

Write-Host "🚀 PRÓXIMO PASO:"
Write-Host "   1. Abre: C:\Users\Administrador\Documents\ATF_Excelencia.exe"
Write-Host "   2. Click: 'Escanear Videos'"
Write-Host "   3. Sistema cargará $TOTAL_EN_MAESTRO videos automáticamente"
Write-Host ""

# Abrir carpeta
Read-Host "Presiona ENTER para abrir C:\VIDEOS_MAESTROS"
Invoke-Item $CARPETA_MAESTRO
