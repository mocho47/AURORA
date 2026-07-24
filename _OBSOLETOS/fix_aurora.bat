@echo off
title Reparador de Emergencia - AURORA v3.0
color 0B
cls

echo =======================================================
echo    🔧 REPARANDO COMPLETO: VALIDAR_AURORA.PY
echo =======================================================
echo.

:: Este comando busca la linea defectuosa usando una coincidencia parcial y la repara
python -c "path=r'C:\AURORA\validar_aurora.py'; f=open(path,'r',encoding='utf-8'); lineas=f.readlines(); f.close(); [lineas.__setitem__(i, '    print(\"\n   Ejecuta:\")\n') for i, l in enumerate(lineas) if 'Ejecuta:' in l]; f=open(path,'w',encoding='utf-8'); f.writelines(lineas); f.close(); print('--- ARCHIVO CORREGIDO ---')"

echo.
echo =======================================================
echo ✅ ¡Reparacion exitosa! Presiona una tecla para cerrar.
echo =======================================================
echo.
pause
