# =================================================================================================
# INSTALADOR Y CONFIGURADOR PROFESIONAL DE AURORA V3
#
# Propósito:
# 1. Crea una estructura de carpetas de producción limpia en C:\AURORA_PRODUCCION.
# 2. Copia todos los componentes necesarios (ejecutables, carpetas de trabajo) a la nueva ubicación.
# 3. Crea un conjunto completo de accesos directos en el escritorio del usuario para un acceso rápido.
# 4. Proporciona un desinstalador para limpiar el entorno.
# =================================================================================================

# --- CONFIGURACIÓN ---
$SourceDir = $PSScriptRoot
$InstallDir = "C:\AURORA_PRODUCCION"
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$WScriptShell = New-Object -ComObject WScript.Shell

# --- FUNCIÓN PARA CREAR ACCESOS DIRECTOS ---
function Create-Shortcut {
    param (
        [string]$ShortcutName,
        [string]$TargetPath,
        [string]$WorkingDirectory,
        [string]$IconLocation,
        [string]$Description
    )
    
    $Shortcut = $WScriptShell.CreateShortcut("$DesktopPath\$ShortcutName.lnk")
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.WorkingDirectory = $WorkingDirectory
    if ($IconLocation) {
        $Shortcut.IconLocation = $IconLocation
    }
    $Shortcut.Description = $Description
    $Shortcut.Save()
}

# --- FASE 1: LIMPIEZA Y CREACIÓN DE DIRECTORIOS ---
Write-Host "--- Iniciando Instalación de AURORA v3 Producción ---" -ForegroundColor Green

if (Test-Path $InstallDir) {
    Write-Host "Directorio de instalación existente encontrado. Limpiando..." -ForegroundColor Yellow
    Remove-Item -Path $InstallDir -Recurse -Force
}

Write-Host "Creando estructura de directorios en $InstallDir..."
New-Item -Path $InstallDir -ItemType Directory | Out-Null

# Crear subdirectorios de producción
$SubDirs = @(
    "dist", "dist_atf", "dist_milens", "dist_venta",
    "TALLER", "TALLER_OUT", "VIDEO", "VIDEO_OUT", "UPLOADS", "LOGS", "MEMORIA", "REPORTES"
)
foreach ($sub in $SubDirs) {
    New-Item -Path (Join-Path $InstallDir $sub) -ItemType Directory | Out-Null
}

# --- FASE 2: COPIA DE ARCHIVOS DE PRODUCCIÓN ---
Write-Host "Copiando archivos de producción..."

# Copiar ejecutables principales
Copy-Item -Path (Join-Path $SourceDir "dist\aurora_unified_main.exe") -Destination (Join-Path $InstallDir "dist")
Copy-Item -Path (Join-Path $SourceDir "dist_atf\*") -Destination (Join-Path $InstallDir "dist_atf") -Recurse
Copy-Item -Path (Join-Path $SourceDir "dist_milens\*") -Destination (Join-Path $InstallDir "dist_milens") -Recurse
Copy-Item -Path (Join-Path $SourceDir "dist_venta\*") -Destination (Join-Path $InstallDir "dist_venta") -Recurse
Copy-Item -Path (Join-Path $SourceDir "production_hub_launcher.py") -Destination $InstallDir

# Copiar dependencias y herramientas (ffmpeg)
if (Test-Path (Join-Path $SourceDir "TOOLS\ffmpeg.exe")) {
    New-Item -Path (Join-Path $InstallDir "TOOLS") -ItemType Directory | Out-Null
    Copy-Item -Path (Join-Path $SourceDir "TOOLS\ffmpeg.exe") -Destination (Join-Path $InstallDir "TOOLS")
}

# --- FASE 3: CREACIÓN DE ACCESOS DIRECTOS ---
Write-Host "Creando accesos directos en el escritorio..."

# Lanzador Principal
Create-Shortcut -ShortcutName "AURORA HUB" `
                -TargetPath "C:\Windows\System32\cmd.exe" `
                -Arguments "/c start pythonw `"$InstallDir\production_hub_launcher.py`"" `
                -WorkingDirectory $InstallDir `
                -IconLocation "$SourceDir\CORE\aurora_icon.ico,0" `
                -Description "Lanzador central de AURORA."

# Sistema Completo (Directo)
Create-Shortcut -ShortcutName "Iniciar AURORA (Consola)" `
                -TargetPath (Join-Path $InstallDir "dist\aurora_unified_main.exe") `
                -WorkingDirectory $InstallDir `
                -IconLocation "$SourceDir\CORE\aurora_icon.ico,1" `
                -Description "Inicia el servidor principal de AURORA."

# Carpetas de Trabajo
Create-Shortcut -ShortcutName "TALLER (Corte)" -TargetPath (Join-Path $InstallDir "TALLER") -IconLocation "imageres.dll,3"
Create-Shortcut -ShortcutName "DISEÑOS TERMINADOS" -TargetPath (Join-Path $InstallDir "TALLER_OUT") -IconLocation "imageres.dll,112"
Create-Shortcut -ShortcutName "VIDEOS (Entrada)" -TargetPath (Join-Path $InstallDir "VIDEO") -IconLocation "imageres.dll,12"
Create-Shortcut -ShortcutName "VIDEOS (Salida)" -TargetPath (Join-Path $InstallDir "VIDEO_OUT") -IconLocation "imageres.dll,18"
Create-Shortcut -ShortcutName "UPLOADS" -TargetPath (Join-Path $InstallDir "UPLOADS") -IconLocation "imageres.dll,13"

# --- FASE 4: CREACIÓN DEL DESINSTALADOR ---
Write-Host "Creando desinstalador..."
$UninstallScriptContent = @"
`$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
Write-Host "Eliminando accesos directos..."
Remove-Item -Path "`$DesktopPath\AURORA HUB.lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\Iniciar AURORA (Consola).lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\TALLER (Corte).lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\DISEÑOS TERMINADOS.lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\VIDEOS (Entrada).lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\VIDEOS (Salida).lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$DesktopPath\UPLOADS.lnk" -ErrorAction SilentlyContinue

Write-Host "Eliminando directorio de instalación C:\AURORA_PRODUCCION..."
Remove-Item -Path "C:\AURORA_PRODUCCION" -Recurse -Force

Write-Host "Desinstalación completada." -ForegroundColor Green
Read-Host "Presione Enter para salir"
"@
$UninstallScriptContent | Out-File -FilePath (Join-Path $InstallDir "uninstall.ps1") -Encoding utf8

Create-Shortcut -ShortcutName "Desinstalar AURORA" `
                -TargetPath "powershell.exe" `
                -Arguments "-ExecutionPolicy Bypass -File `"$InstallDir\uninstall.ps1`"" `
                -WorkingDirectory $InstallDir `
                -IconLocation "imageres.dll,48" `
                -Description "Elimina AURORA y todos sus componentes."


# --- FINALIZACIÓN ---
Write-Host "¡Instalación de AURORA v3 completada con éxito!" -ForegroundColor Green
Write-Host "Puede encontrar todos los accesos directos en su escritorio."
Write-Host "Para desinstalar, use el acceso directo 'Desinstalar AURORA'."

# Pausa para que el usuario vea el mensaje
Read-Host "Presione Enter para finalizar la instalación"
