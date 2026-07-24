# AURORA v1 - Crear Shortcuts Completos en Escritorio
# Ejecuta este script para crear accesos directos

$Desktop = [Environment]::GetFolderPath("Desktop")
$AURORA_DIR = "C:\AURORA"

Write-Host ""
Write-Host "Creando shortcuts en: $Desktop" -ForegroundColor Cyan
Write-Host ""

$Shell = New-Object -ComObject WScript.Shell

# ============================================================================
# SHORTCUT 1: AURORA CLI (CLI Interactivo Directo)
# ============================================================================

$CLIPath = Join-Path $Desktop "AURORA CLI.lnk"
$Shortcut = $Shell.CreateShortcut($CLIPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"cd $AURORA_DIR; .\LAUNCHER_AURORA.ps1 -CLI`""
$Shortcut.WorkingDirectory = $AURORA_DIR
$Shortcut.Description = "AURORA v1 - CLI Interactivo"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA CLI.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = CLI interactivo directo" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# SHORTCUT 2: AURORA SERVER (Servidor Web + Dashboard)
# ============================================================================

$ServerPath = Join-Path $Desktop "AURORA SERVER.lnk"
$Shortcut = $Shell.CreateShortcut($ServerPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"cd $AURORA_DIR; .\LAUNCHER_AURORA.ps1 -Server`""
$Shortcut.WorkingDirectory = $AURORA_DIR
$Shortcut.Description = "AURORA v1 - Servidor FastAPI"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA SERVER.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = Servidor (http://localhost:8000)" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# SHORTCUT 3: AURORA LAUNCHER (Menu Interactivo)
# ============================================================================

$LauncherPath = Join-Path $Desktop "AURORA Launcher.lnk"
$Shortcut = $Shell.CreateShortcut($LauncherPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$AURORA_DIR\LAUNCHER_AURORA.ps1`""
$Shortcut.WorkingDirectory = $AURORA_DIR
$Shortcut.Description = "AURORA v1 - Menu Interactivo"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA Launcher.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = Menu con 5 opciones" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# SHORTCUT 4: AURORA TESTS (Validacion)
# ============================================================================

$TestPath = Join-Path $Desktop "AURORA Tests.lnk"
$Shortcut = $Shell.CreateShortcut($TestPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"cd $AURORA_DIR; .\LAUNCHER_AURORA.ps1 -Test`""
$Shortcut.WorkingDirectory = $AURORA_DIR
$Shortcut.Description = "AURORA v1 - Suite de Tests"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA Tests.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = Ejecuta 6/6 tests" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# SHORTCUT 5: AURORA Dashboard (Directo a web)
# ============================================================================

$DashboardPath = Join-Path $Desktop "AURORA Dashboard.lnk"
$Shortcut = $Shell.CreateShortcut($DashboardPath)
$Shortcut.TargetPath = "http://localhost:8000/templates/dashboard.html"
$Shortcut.Description = "AURORA v1 - Dashboard Web"
$Shortcut.IconLocation = "iexplore.exe,0"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA Dashboard.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = Abre dashboard (requiere servidor corriendo)" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# SHORTCUT 6: Abrir Carpeta AURORA
# ============================================================================

$FolderPath = Join-Path $Desktop "AURORA Folder.lnk"
$Shortcut = $Shell.CreateShortcut($FolderPath)
$Shortcut.TargetPath = $AURORA_DIR
$Shortcut.Description = "AURORA v1 - Carpeta del Proyecto"
$Shortcut.IconLocation = "shell32.dll,3"
$Shortcut.Save()

Write-Host "[OK] Shortcut creado: AURORA Folder.lnk" -ForegroundColor Green
Write-Host "     - Doble clic = Abre carpeta C:\AURORA" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# RESUMEN
# ============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SHORTCUTS CREADOS EXITOSAMENTE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "5 Shortcuts en tu escritorio:" -ForegroundColor Yellow
Write-Host "  1. AURORA CLI          -> Interactivo directo" -ForegroundColor Green
Write-Host "  2. AURORA SERVER       -> Web + Dashboard" -ForegroundColor Green
Write-Host "  3. AURORA Launcher     -> Menu (5 opciones)" -ForegroundColor Green
Write-Host "  4. AURORA Tests        -> Validacion (6/6)" -ForegroundColor Green
Write-Host "  5. AURORA Folder       -> Carpeta del proyecto" -ForegroundColor Green
Write-Host ""

Write-Host "RECOMENDADO:" -ForegroundColor Yellow
Write-Host "  - Uso diario: AURORA CLI (doble clic = listo)" -ForegroundColor Gray
Write-Host "  - Ver dashboard: AURORA SERVER -> abre web" -ForegroundColor Gray
Write-Host "  - Ver opciones: AURORA Launcher -> menu" -ForegroundColor Gray
Write-Host ""

Write-Host "Todos los shortcuts estan en: $Desktop" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presiona Enter para cerrar"
