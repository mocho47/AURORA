#!/usr/bin/env powershell
# AURORA - Crear Scheduled Tasks automáticas
# Ejecutar: powershell -ExecutionPolicy Bypass -File "C:\AURORA\SETUP\crear_scheduled_tasks.ps1"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "AURORA NEXUS v3 - CREAR SCHEDULED TASKS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Validar permisos admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] Este script requiere privilegios de administrador" -ForegroundColor Red
    Write-Host "[INFO] Ejecuta PowerShell como administrador" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Privilegios de administrador validados" -ForegroundColor Green
Write-Host ""

# Task 1: Sleep Cycle Diario (3:00 AM)
Write-Host "[SETUP] Creando Task: Sleep Cycle (Consolidación 24h)..." -ForegroundColor Yellow
$trigger1 = New-ScheduledTaskTrigger -At 03:00 -Daily
$action1 = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\AURORA\AUTOMATIONS\sleep_cycle.py"
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery
Register-ScheduledTask -TaskName "Aurora-SleepCycle-Diario" -Trigger $trigger1 -Action $action1 -Settings $settings1 -Force | Out-Null
Write-Host "[OK] Task creada: Aurora-SleepCycle-Diario (03:00 AM)" -ForegroundColor Green

# Task 2: Auditoria Cada 6 horas
Write-Host "[SETUP] Creando Task: Auditoría cada 6h..." -ForegroundColor Yellow
$trigger2 = New-ScheduledTaskTrigger -At 06:00 -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Hours 24)
$action2 = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\AURORA\AUDITORIAS\auditoria_diaria.py"
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery
Register-ScheduledTask -TaskName "Aurora-Auditoria-6h" -Trigger $trigger2 -Action $action2 -Settings $settings2 -Force | Out-Null
Write-Host "[OK] Task creada: Aurora-Auditoria-6h (06:00, 12:00, 18:00, 00:00)" -ForegroundColor Green

# Task 3: Flujo Venta ATF (Cada 2h, 8AM-8PM)
Write-Host "[SETUP] Creando Task: Flujo Venta ATF (cada 2h)..." -ForegroundColor Yellow
$trigger3 = New-ScheduledTaskTrigger -At 08:00 -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration (New-TimeSpan -Hours 12)
$action3 = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\AURORA\AUTOMATIONS\flujo_venta_atf.py"
$settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery
Register-ScheduledTask -TaskName "Aurora-VentaATF-2h" -Trigger $trigger3 -Action $action3 -Settings $settings3 -Force | Out-Null
Write-Host "[OK] Task creada: Aurora-VentaATF-2h (08:00 - 20:00)" -ForegroundColor Green

# Task 4: Marketing MILENS (Diario 12:00 PM)
Write-Host "[SETUP] Creando Task: Marketing MILENS (diario)..." -ForegroundColor Yellow
$trigger4 = New-ScheduledTaskTrigger -At 12:00 -Daily
$action4 = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\AURORA\AUTOMATIONS\flujo_marketing_milens.py"
$settings4 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery
Register-ScheduledTask -TaskName "Aurora-MarketingMilens-Diario" -Trigger $trigger4 -Action $action4 -Settings $settings4 -Force | Out-Null
Write-Host "[OK] Task creada: Aurora-MarketingMilens-Diario (12:00 PM)" -ForegroundColor Green

# Task 5: Reporte Diario (8:00 PM)
Write-Host "[SETUP] Creando Task: Reporte Diario..." -ForegroundColor Yellow
$trigger5 = New-ScheduledTaskTrigger -At 20:00 -Daily
$action5 = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\AURORA\INTEGRACIONES\email_integration.py"
$settings5 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBattery
Register-ScheduledTask -TaskName "Aurora-ReporteDiario" -Trigger $trigger5 -Action $action5 -Settings $settings5 -Force | Out-Null
Write-Host "[OK] Task creada: Aurora-ReporteDiario (20:00)" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE TAREAS CREADAS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Aurora-SleepCycle-Diario" -ForegroundColor Green
Write-Host "   ├─ Hora: 03:00 AM (Diariamente)" -ForegroundColor Cyan
Write-Host "   └─ Acción: Consolidación 24h, análisis patrones, optimización" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Aurora-Auditoria-6h" -ForegroundColor Green
Write-Host "   ├─ Horas: 06:00, 12:00, 18:00, 00:00" -ForegroundColor Cyan
Write-Host "   └─ Acción: Validación completa del sistema" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Aurora-VentaATF-2h" -ForegroundColor Green
Write-Host "   ├─ Horas: 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00" -ForegroundColor Cyan
Write-Host "   └─ Acción: Flujo de venta automático ATF" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Aurora-MarketingMilens-Diario" -ForegroundColor Green
Write-Host "   ├─ Hora: 12:00 PM (Diariamente)" -ForegroundColor Cyan
Write-Host "   └─ Acción: Generación y publicación de contenido MILENS" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Aurora-ReporteDiario" -ForegroundColor Green
Write-Host "   ├─ Hora: 20:00 (Diariamente)" -ForegroundColor Cyan
Write-Host "   └─ Acción: Envío de reporte diario por email" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VER TAREAS EN: Programador de tareas > Biblioteca de Programador > Aurora" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[✓] Todas las tareas creadas exitosamente" -ForegroundColor Green
Write-Host ""

# Listar tareas creadas
Write-Host "Verificando tareas creadas..." -ForegroundColor Yellow
Get-ScheduledTask -TaskName "Aurora-*" | Select-Object TaskName, State | Format-Table -AutoSize
