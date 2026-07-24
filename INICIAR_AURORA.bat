@echo off
title ENTORNO UNIFICADO - AURORA v3.0 + NEXUS
cd /d "C:\AURORA.worktrees"

echo [1/2] Limpiando residuos de memoria de Python...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo [2/2] Iniciando el Bus Neuronal de Aurora...

:: Cerebro OFFLINE (Ollama) — para que AURORA piense aunque se caiga el WiFi
start "" "C:\Users\Administrador\AppData\Local\Programs\Ollama\ollama.exe" serve

:: Abridor del panel: espera a que el servidor responda y abre el navegador (en segundo plano)
start "" powershell -NoProfile -WindowStyle Hidden -Command "$probe='http://127.0.0.1:5000/health'; $panel='http://127.0.0.1:5000/'; for($i=0;$i -lt 150;$i++){ try{ $null = Invoke-WebRequest $probe -UseBasicParsing -TimeoutSec 2; Start-Process $panel; break } catch { Start-Sleep -Seconds 2 } }"

:: Iniciamos Aurora de forma visible en la misma ventana
"C:\Program Files\Python312\python.exe" .\run_aurora.py

echo.
echo ============================================================
echo      ?? PROCESANDO CIERRE SEGURO DE AURORA V3.0
echo ============================================================
echo Sincronizando y guardando bases de datos SQLite...
"C:\Program Files\Python312\python.exe" -c "
import sqlite3
for db in ['MEMORIA/aurora_memoria.db', 'oracle.db']:
    try:
        conn = sqlite3.connect(f'C:/AURORA.worktrees/{db}')
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
        conn.close()
    except: pass
"
taskkill /f /im pythonw.exe >nul 2>&1

echo.
echo ============================================================
echo      ?? COPIA EL SIGUIENTE PROMPT PARA TU PR�XIMO CHAT
echo ============================================================
echo Hola IA. Retomamos desarrollo de AURORA v3.0. Mi entorno esta unificado en C:\AURORA.worktrees con la arquitectura de 28 motores en el Bus Neuronal nativo. El microfono local corre en C:\NEXUS\escuha_taller.py configurado a 2 canales estereo (device=5 Realtek HD Audio) e inyecta directamente al objeto global 'bus' de CEREBRO.bus_neuronal usando el metodo 'publicar' mediante el diccionario unico del Intento B. El sistema arranca limpio desde el acceso directo del escritorio. Ponme al tanto de donde nos quedamos.
echo ============================================================
echo.
echo Ya puedes cerrar esta ventana y apagar tu PC con confianza.
pause
