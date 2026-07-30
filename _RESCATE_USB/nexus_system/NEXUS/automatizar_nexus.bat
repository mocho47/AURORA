@echo off
REM ============================================
REM Automatización modular de NEXUS
REM ============================================

set ROOT=D:\nexus_system\NEXUS

echo Creando estructura de carpetas...
if not exist "%ROOT%\skills" mkdir "%ROOT%\skills"
if not exist "%ROOT%\ears" mkdir "%ROOT%\ears"

echo Copiando módulos de acciones...
(
echo import os, platform, datetime, pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    print("=== NEXUS STATUS ===")
echo ^    print(f"Ruta actual      : {os.getcwd()}")
echo ^    print(f"Archivo ejecutado: {__file__}")
echo ^    print(f"Python versión   : {platform.python_version()}")
echo ^    print(f"Fecha y hora     : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
echo ^    print("====================")
echo ^    speak("Nexus está en línea.")
) > "%ROOT%\skills\status.py"

(
echo import sys, pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    print("Nexus se apaga...")
echo ^    speak("Nexus se apaga. Hasta luego.")
echo ^    sys.exit(0)
) > "%ROOT%\skills\exit.py"

(
echo import pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    cmds=["nexus status","nexus salir","nexus ayuda","nexus memoria","nexus log","nexus hora"]
echo ^    print("=== NEXUS HELP ===")
echo ^    [print(f"- {c}") for c in cmds]
echo ^    print("==================")
echo ^    speak("Comandos disponibles: status, salir, ayuda, memoria, log y hora.")
) > "%ROOT%\skills\help.py"

(
echo import json, os, pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    f="estado.json"
echo ^    if os.path.exists(f):
echo ^        d=json.load(open(f,"r",encoding="utf-8"))
echo ^        ultimo=d.get("ultimo_evento","No hay eventos.")
echo ^    else: ultimo="No se encontró archivo de estado."
echo ^    print("=== NEXUS MEMORY ===")
echo ^    print(f"Último evento: {ultimo}")
echo ^    print("====================")
echo ^    speak(f"Último evento: {ultimo}")
) > "%ROOT%\skills\memory.py"

(
echo import pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    try:
echo ^        lines=open("nexus.log","r",encoding="utf-8").readlines()[-5:]
echo ^        print("=== NEXUS LOG ===")
echo ^        [print(l.strip()) for l in lines]
echo ^        print("=================")
echo ^        speak("Mostrando últimos eventos del log.")
echo ^    except: 
echo ^        print("No se encontró nexus.log.")
echo ^        speak("No se encontró el archivo de log.")
) > "%ROOT%\skills\log.py"

(
echo import datetime, pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    h=datetime.datetime.now().strftime("%H:%M:%S")
echo ^    print("=== NEXUS TIME ===")
echo ^    print(f"Hora actual: {h}")
echo ^    print("==================")
echo ^    speak(f"La hora actual es {h}")
) > "%ROOT%\skills\time.py"

(
echo import pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    print("Comando no reconocido.")
echo ^    speak("Comando no reconocido, intenta de nuevo.")
) > "%ROOT%\skills\notfound.py"

(
echo import os, sys, winshell
echo from win32com.client import Dispatch
echo import pyttsx3
echo def speak(t): e=pyttsx3.init()^&e.say(t)^&e.runAndWait()
echo def main():
echo ^    desk=winshell.desktop()
echo ^    link=os.path.join(desk,"NEXUS.lnk")
echo ^    shell=Dispatch("WScript.Shell")
echo ^    sc=shell.CreateShortCut(link)
echo ^    sc.Targetpath=sys.executable
echo ^    sc.Arguments=f'"{os.path.abspath("%ROOT%\\ears\\voice_response.py")}"'
echo ^    sc.WorkingDirectory="%ROOT%"
echo ^    sc.IconLocation=os.path.abspath("%ROOT%\\nexus.ico")
echo ^    sc.save()
echo ^    print("Acceso directo creado en escritorio.")
echo ^    speak("Acceso directo creado en escritorio.")
) > "%ROOT%\skills\shortcut.py"

echo Creando archivos iniciales...
echo { "ultimo_evento": "Sistema inicializado correctamente" } > "%ROOT%\estado.json"
(
echo [2026-01-16 07:15:00] Sistema inicializado
echo [2026-01-16 07:15:10] Comando recibido: nexus status
echo [2026-01-16 07:15:15] Estado mostrado correctamente
) > "%ROOT%\nexus.log"

echo ============================================
echo NEXUS modular actualizado correctamente.
echo Usa el comando de voz "nexus acceso" para crear el acceso directo.
echo ============================================

pause