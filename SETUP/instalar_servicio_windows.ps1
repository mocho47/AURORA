#!/usr/bin/env powershell
# AURORA NEXUS v3 - INSTALACIÓN COMO SERVICIO WINDOWS 24/7
# Ejecución: powershell -ExecutionPolicy Bypass -File "C:\AURORA\SETUP\instalar_servicio_windows.ps1"
# REQUIERE: Privilegios de Administrador

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "AURORA NEXUS v3 - INSTALACIÓN COMO SERVICIO WINDOWS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Validar permisos admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Este script requiere privilegios de Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "SOLUCIÓN:" -ForegroundColor Yellow
    Write-Host "1. Presiona Windows + X" -ForegroundColor Yellow
    Write-Host "2. Selecciona 'Terminal de Windows (Admin)'" -ForegroundColor Yellow
    Write-Host "3. Ejecuta: powershell -ExecutionPolicy Bypass -File 'C:\AURORA\SETUP\instalar_servicio_windows.ps1'" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "[✓] Ejecutando con permisos de Administrador" -ForegroundColor Green
Write-Host ""

# PASO 1: Crear wrapper Python que inicia el servicio
Write-Host "[PASO 1] Creando wrapper del servicio..." -ForegroundColor Yellow

$wrapperScript = @'
#!/usr/bin/env python3
"""
AURORA NEXUS v3 - Service Wrapper
Ejecuta aurora_unified_main.py como servicio Windows con auto-recuperación
"""

import subprocess
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
log_path = Path("C:\\AURORA\\LOGS\\servicio.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AuroraService")

def main():
    """Ejecuta AURORA con auto-recuperación"""
    logger.info("="*80)
    logger.info("AURORA NEXUS v3 - SERVICIO INICIADO")
    logger.info("="*80)

    intentos = 0
    max_intentos = 5

    while True:
        try:
            intentos += 1
            logger.info(f"[{intentos}] Iniciando AURORA...")

            # Ejecutar servidor AURORA
            proceso = subprocess.Popen(
                [sys.executable, "C:\\AURORA\\aurora_unified_main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="C:\\AURORA"
            )

            logger.info(f"[OK] AURORA iniciado (PID: {proceso.pid})")
            logger.info("[OK] Servidor disponible en http://127.0.0.1:8000/")

            # Esperar a que termine (si falla, reintentar)
            proceso.wait()

            logger.warning(f"[ALERTA] AURORA se detuvo (PID: {proceso.pid})")

            if intentos >= max_intentos:
                logger.error(f"[ERROR] Máximo de intentos alcanzado ({max_intentos})")
                logger.error("[ERROR] Servicio DETENIÉNDOSE")
                break

            # Esperar antes de reintentar
            espera = 10 * intentos
            logger.info(f"[REINTENTOS] Reintentando en {espera} segundos...")
            time.sleep(espera)

        except KeyboardInterrupt:
            logger.info("[OK] Servicio detenido por usuario")
            break
        except Exception as e:
            logger.error(f"[ERROR] Excepción: {e}")
            if intentos >= max_intentos:
                logger.error("[ERROR] Servicio DETENIÉNDOSE")
                break
            espera = 30 * intentos
            logger.info(f"[REINTENTOS] Reintentando en {espera} segundos...")
            time.sleep(espera)

    logger.info("="*80)
    logger.info("AURORA NEXUS v3 - SERVICIO FINALIZADO")
    logger.info("="*80)

if __name__ == "__main__":
    main()
'@

Set-Content -Path "C:\AURORA\SETUP\aurora_service_wrapper.py" -Value $wrapperScript -Force
Write-Host "[✓] Wrapper creado: C:\AURORA\SETUP\aurora_service_wrapper.py" -ForegroundColor Green

Write-Host ""
Write-Host "[PASO 2] Creando ejecutable para el servicio..." -ForegroundColor Yellow

# Crear ejecutable .bat que inicia el wrapper
$batchServicio = @"
@echo off
REM AURORA NEXUS v3 - Service Batch Wrapper
REM Ejecuta wrapper Python que maneja auto-recuperación

setlocal enabledelayedexpansion

REM Cambiar a directorio AURORA
cd /d C:\AURORA

REM Ejecutar wrapper Python
python.exe "C:\AURORA\SETUP\aurora_service_wrapper.py"

REM Si el script termina, registrar en log
echo [%date% %time%] AURORA Service Wrapper termino >> "C:\AURORA\LOGS\servicio_wrapper.log"

REM Pausar si hay error
if %errorlevel% neq 0 (
    echo [ERROR] AURORA Service Wrapper fallo con codigo %errorlevel% >> "C:\AURORA\LOGS\servicio_wrapper.log"
)

endlocal
"@

Set-Content -Path "C:\AURORA\SETUP\aurora_service.bat" -Value $batchServicio -Force
Write-Host "[✓] Batch creado: C:\AURORA\SETUP\aurora_service.bat" -ForegroundColor Green

Write-Host ""
Write-Host "[PASO 3] Registrando servicio Windows..." -ForegroundColor Yellow

# Eliminar servicio anterior si existe
try {
    Stop-Service -Name "AuroraNexus" -ErrorAction SilentlyContinue -Force
    Start-Sleep -Seconds 2
    Remove-Service -Name "AuroraNexus" -ErrorAction SilentlyContinue -Force
    Write-Host "[INFO] Servicio anterior removido" -ForegroundColor Yellow
} catch {}

# Crear nuevo servicio
try {
    $servicioParams = @{
        Name = "AuroraNexus"
        DisplayName = "AURORA NEXUS v3 - Sistema Inteligente de Operaciones"
        BinaryPathName = "C:\AURORA\SETUP\aurora_service.bat"
        StartupType = "Automatic"
        ErrorAction = "Stop"
    }

    New-Service @servicioParams | Out-Null
    Write-Host "[✓] Servicio registrado: AuroraNexus" -ForegroundColor Green

} catch {
    Write-Host "[ERROR] No se pudo crear el servicio: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[PASO 4] Iniciando servicio..." -ForegroundColor Yellow

try {
    Start-Service -Name "AuroraNexus" -ErrorAction Stop
    Start-Sleep -Seconds 3

    $estado = Get-Service -Name "AuroraNexus" | Select-Object Status

    if ($estado.Status -eq "Running") {
        Write-Host "[✓] Servicio iniciado EXITOSAMENTE" -ForegroundColor Green
    } else {
        Write-Host "[ALERTA] Servicio creado pero no inició automáticamente" -ForegroundColor Yellow
        Write-Host "[INFO] Iniciando manualmente..." -ForegroundColor Yellow
        Start-Service -Name "AuroraNexus"
    }

} catch {
    Write-Host "[ERROR] No se pudo iniciar: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[PASO 5] Verificando estado..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$servicio = Get-Service -Name "AuroraNexus"
$proceso = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -eq "python"}

Write-Host ""
Write-Host "Servicio: $($servicio.Name)" -ForegroundColor Green
Write-Host "Estado: $($servicio.Status)" -ForegroundColor Green
Write-Host "Tipo: $($servicio.StartType)" -ForegroundColor Green

if ($proceso) {
    Write-Host "Proceso Python: ACTIVO (PID: $($proceso.Id))" -ForegroundColor Green
} else {
    Write-Host "Proceso Python: Iniciándose..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[PASO 6] Configurando monitoreo automático..." -ForegroundColor Yellow

# Crear tarea Windows para verificar servicio cada 5 minutos
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command `"if ((Get-Service AuroraNexus).Status -ne 'Running') { Start-Service AuroraNexus }`""
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery

Register-ScheduledTask -TaskName "Aurora-Monitor-Servicio" -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null

Write-Host "[✓] Monitoreo automático configurado (cada 5 min)" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "INSTALACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "AURORA NEXUS v3 ahora se ejecuta como SERVICIO WINDOWS:" -ForegroundColor Green
Write-Host ""
Write-Host "  ✓ Se inicia automáticamente con Windows" -ForegroundColor Green
Write-Host "  ✓ Se ejecuta 24/7 en background" -ForegroundColor Green
Write-Host "  ✓ Auto-recuperación si falla" -ForegroundColor Green
Write-Host "  ✓ Monitoreo cada 5 minutos" -ForegroundColor Green
Write-Host "  ✓ Logs completos en C:\AURORA\LOGS\" -ForegroundColor Green
Write-Host ""
Write-Host "ACCESO:" -ForegroundColor Cyan
Write-Host "  Dashboard: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "  API: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Logs: C:\AURORA\LOGS\servicio.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "COMANDOS ÚTILES:" -ForegroundColor Yellow
Write-Host "  Ver estado: Get-Service AuroraNexus" -ForegroundColor Yellow
Write-Host "  Detener: Stop-Service AuroraNexus" -ForegroundColor Yellow
Write-Host "  Iniciar: Start-Service AuroraNexus" -ForegroundColor Yellow
Write-Host "  Ver logs: Get-Content 'C:\AURORA\LOGS\servicio.log' -Tail 50" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
