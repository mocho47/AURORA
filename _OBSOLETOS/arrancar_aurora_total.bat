@echo off
title 🚀 ENLACE VISUAL Y ARRANQUE ABSOLUTO - AURORA v3.5
color 0A
cd /d C:\AURORA

echo =================================================================
echo   NIVELANDO PAQUETES E INYECTANDO ENLACE VISUAL EN LA API
echo =================================================================

powershell -Command ""^
    $targetDir = 'C:\AURORA\SUPER_MARKETING_SYSTEM';^
    Write-Host '1. Forzando instalación de dependencias en subcarpeta...' -ForegroundColor Cyan;^
    python -m pip install 'supabase==2.3.0' 'httpx>=0.24.0,<0.26.0' 'pydantic==2.7.4' 'pydantic-core==2.18.4' --target $targetDir --upgrade --quiet;^
    ^
    $apiFile = 'C:\AURORA\SUPER_MARKETING_SYSTEM\api_v3_new.py';^
    if (Test-Path $apiFile) {^
        $content = [System.IO.File]::ReadAllText($apiFile);^
        if ($content -notlike '*app.mount(\"/dashboard\"*') {^
            Write-Host '2. Inyectando montaje estricto del Dashboard en el Core...' -ForegroundColor Green;^
            $enlaceVisual = [string]::Format('{0}# --- ENLACE VISUAL FINISHED ---{0}try:{0}    from dashboard import dashboard as db_mod{0}    app.mount(\"/dashboard\", db_mod.app){0}except Exception as e:{0}    print(e){0}', [Environment]::NewLine);^
            [System.IO.File]::WriteAllText($apiFile, $content + $enlaceVisual);^
        } else {^
            Write-Host '2. El enlace visual ya se encuentra declarado en la API.' -ForegroundColor Yellow;^
        }^
    } else {^
        Write-Host '❌ No se encontró el archivo api_v3_new.py' -ForegroundColor Red;^
    }""

echo =================================================================
echo   ARRANCANDO NÚCLEO DE 16 MOTORES EN EL PUERTO 5000
echo =================================================================
python run_aurora.py
pause
