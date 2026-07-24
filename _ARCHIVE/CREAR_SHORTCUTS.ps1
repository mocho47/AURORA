# AURORA v1 - Crear Shortcuts en Escritorio

$Desktop = [Environment]::GetFolderPath("Desktop")
$AURORA_DIR = "C:\AURORA"
$CORE_DIR = "$AURORA_DIR\CORE"

# Crear shortcut para Launcher
$LauncherPath = Join-Path $Desktop "AURORA Launcher.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($LauncherPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$AURORA_DIR\LAUNCHER_AURORA.ps1`""
$Shortcut.WorkingDirectory = $AURORA_DIR
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "[+] Shortcut 'AURORA Launcher' creado en escritorio"

# Crear shortcut para CLI
$CLIPath = Join-Path $Desktop "AURORA CLI.lnk"
$Shortcut = $Shell.CreateShortcut($CLIPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$AURORA_DIR\LAUNCHER_AURORA.ps1`" -CLI"
$Shortcut.WorkingDirectory = $CORE_DIR
$Shortcut.Save()

Write-Host "[+] Shortcut 'AURORA CLI' creado en escritorio"

# Crear shortcut para Servidor
$ServerPath = Join-Path $Desktop "AURORA Server.lnk"
$Shortcut = $Shell.CreateShortcut($ServerPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$AURORA_DIR\LAUNCHER_AURORA.ps1`" -Server"
$Shortcut.WorkingDirectory = $CORE_DIR
$Shortcut.Save()

Write-Host "[+] Shortcut 'AURORA Server' creado en escritorio"

Write-Host ""
Write-Host "Shortcuts creados en: $Desktop" -ForegroundColor Green
Write-Host ""
