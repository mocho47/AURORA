@echo off
echo.
echo ?? INSTALADOR AUTOM?TICO
echo.
echo Creando ejecutables...

cd /d C:\AURORA

python crear_exe_atf.py
python crear_exe_milens.py

echo.
echo ? COMPLETADO
echo.
echo ?? Ejecutables listos en:
echo    - C:\AURORA\dist_atf\ATF_Retrofit_App.exe
echo    - C:\AURORA\dist_milens\Milens_App.exe
echo.
pause
