@echo off
title 🚀 REPARACIÓN FORZADA Y ARRANQUE - AURORA v3.5
color 0A
cd /d C:\AURORA

echo =================================================================
echo   1/3 MATANDO PROCESOS RETENIDOS EN LA MEMORIA RAM DE WINDOWS
echo =================================================================
:: Cierra de forma agresiva cualquier proceso de Python que bloquee los archivos .pyd
taskkill /f /im python.exe /im uvicorn.exe /im python3.exe 2>nul
timeout /t 2 /nobreak >nul

echo =================================================================
echo   2/3 ELIMINANDO RASTROS CORRUPTOS Y REINSTALANDO PYDANTIC CLEAN
echo =================================================================
:: Usamos PowerShell nativo para borrar las carpetas sin errores de acceso denegado
powershell -Command "$target = 'C:\AURORA\SUPER_MARKETING_SYSTEM'; foreach($f in @('pydantic','pydantic_core','annotated_types')){ $p = Join-Path $target $f; if(Test-Path $p){ Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue } }; python -m pip install 'pydantic==2.7.4' 'pydantic-core==2.18.4' 'annotated-types==0.7.0' --target $target --upgrade --force-reinstall --quiet"

echo =================================================================
echo   3/3 PROCESO COMPLETADO. ARRANCANDO CORE EN EL PUERTO 5000
echo =================================================================
python run_aurora.py
pause
