@echo off
title 🛠️ SOLUCIÓN ABSOLUTA DE UN SOLO CLIC - AURORA v3.5
color 0A
cd /d C:\AURORA

echo =================================================================
echo   1/2 NIVELANDO LIBRERÍAS HTTP Y CERRANDO CONFLICTOS DE ENTORNO
echo =================================================================
powershell -Command "python -m pip install 'supabase==2.4.3' 'httpx>=0.24.0,<0.26.0' 'pydantic==2.7.4' 'pydantic-core==2.18.4' --target C:\AURORA\SUPER_MARKETING_SYSTEM --upgrade --quiet"

echo =================================================================
echo   2/2 INYECTANDO BYPASS INDESTRUCTIBLE DIRECTO EN EL CORE
echo =================================================================
powershell -Command "$apiFile = 'C:\AURORA\SUPER_MARKETING_SYSTEM\api_v3_new.py'; if (Test-Path $apiFile) { $content = [System.IO.File]::ReadAllText($apiFile); if ($content -notlike '*# --- FIJADO ABSOLUTO ---*') { $bypass = [Environment]::NewLine + '# --- FIJADO ABSOLUTO ---' + [Environment]::NewLine + 'try:' + [Environment]::NewLine + '    from dashboard import dashboard as db_inst' + [Environment]::NewLine + '    @app.get(\"/dashboard/\")' + [Environment]::NewLine + '    async def serve_dashboard_root():' + [Environment]::NewLine + '        from fastapi.responses import HTMLResponse' + [Environment]::NewLine + '        return HTMLResponse(content=db_inst.crear_dashboard_html())' + [Environment]::NewLine + '    app.mount(\"/dashboard\", db_inst.app)' + [Environment]::NewLine + 'except Exception as e:' + [Environment]::NewLine + '    print(e)' + [Environment]::NewLine; [System.IO.File]::WriteAllText($apiFile, $content + $bypass); Write-Host '✅ Enlace visual blindado en el Core.' -ForegroundColor Green } else { Write-Host '🔹 Enlace ya registrado.' -ForegroundColor Yellow } }"

echo =================================================================
echo   🚀 TODO LISTO. ARRANCANDO CORE SUPREMO EN EL PUERTO 5000
echo =================================================================
python run_aurora.py
pause
