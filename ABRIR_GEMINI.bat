@echo off
REM Abre Gemini CLI ya parado en AURORA, con el GEMINI.md cargado.
REM Doble clic y listo, sin escribir cd ni acordarse de nada.
cd /d "C:\AURORA.worktrees"
echo.
echo  ==================================================
echo   AURORA - PRODUCCION
echo  ==================================================
echo.
echo   Carpeta: %CD%
if defined GEMINI_API_KEY (echo   Llave:   cargada) else (echo   Llave:   NO ESTA - cierra y abre esta ventana)
echo.
echo   Gemini lee GEMINI.md solo: ya trae las reglas.
echo   Escribe lo que necesitas, en espanol normal.
echo.
gemini
pause
