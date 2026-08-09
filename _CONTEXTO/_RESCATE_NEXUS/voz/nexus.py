import os
import sys
import json
import vosk
import sounddevice as sd
import queue
import pyttsx3
import platform
import datetime

MODEL_PATH = "ears/model_es"
samplerate = 16000
device = None

model = vosk.Model(MODEL_PATH)
rec = vosk.KaldiRecognizer(model, samplerate)
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Estado de audio: {status}", flush=True)
    q.put(bytes(indata))

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()

def log_event(evento):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Actualizar estado.json
    with open("estado.json", "w", encoding="utf-8") as f:
        json.dump({"ultimo_evento": evento}, f, ensure_ascii=False, indent=2)
    # Añadir a nexus.log
    with open("nexus.log", "a", encoding="utf-8") as f:
        f.write(f"[{fecha}] {evento}\n")

def cmd_status():
    ruta = os.getcwd()
    archivo = __file__
    version = platform.python_version()
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=== NEXUS STATUS ===")
    print(f"Ruta actual      : {ruta}")
    print(f"Archivo ejecutado: {archivo}")
    print(f"Python versión   : {version}")
    print(f"Fecha y hora     : {fecha}")
    print("====================")
    speak(f"Nexus está en línea. Python versión {version}. Fecha y hora {fecha}.")
    log_event("Comando ejecutado: STATUS")

def cmd_exit():
    print("Nexus se apaga...")
    speak("Nexus se apaga. Hasta luego.")
    log_event("Comando ejecutado: EXIT")
    sys.exit(0)

def cmd_help():
    comandos = [
        "nexus status",
        "nexus salir",
        "nexus ayuda",
        "nexus memoria",
        "nexus log",
        "nexus hora"
    ]
    print("=== NEXUS HELP ===")
    for cmd in comandos:
        print(f"- {cmd}")
    print("==================")
    speak("Los comandos disponibles son: nexus status, salir, ayuda, memoria, log y hora.")
    log_event("Comando ejecutado: HELP")

def cmd_memory():
    try:
        with open("estado.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        ultimo = data.get("ultimo_evento", "No hay eventos registrados.")
    except FileNotFoundError:
        ultimo = "No se encontró archivo de estado."
    print("=== NEXUS MEMORY ===")
    print(f"Último evento: {ultimo}")
    print("====================")
    speak(f"Último evento registrado: {ultimo}")
    log_event("Comando ejecutado: MEMORY")

def cmd_log():
    try:
        with open("nexus.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-5:]
        print("=== NEXUS LOG ===")
        for line in lines:
            print(line.strip())
        print("=================")
        speak("Mostrando últimos eventos del log.")
    except FileNotFoundError:
        print("No se encontró el archivo nexus.log.")
        speak("No se encontró el archivo de log.")
    log_event("Comando ejecutado: LOG")

def cmd_time():
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    print("=== NEXUS TIME ===")
    print(f"Hora actual: {hora}")
    print("==================")
    speak(f"La hora actual es {hora}")
    log_event("Comando ejecutado: TIME")

def cmd_notfound():
    print("Comando no reconocido.")
    speak("Comando no reconocido, intenta de nuevo.")
    log_event("Comando ejecutado: NOTFOUND")

COMMANDS = {
    "nexus status": cmd_status,
    "nexus estatus": cmd_status,
    "nexus salir": cmd_exit,
    "nexus exit": cmd_exit,
    "nexus ayuda": cmd_help,
    "nexus help": cmd_help,
    "nexus memoria": cmd_memory,
    "nexus memory": cmd_memory,
    "nexus log": cmd_log,
    "nexus hora": cmd_time,
    "nexus time": cmd_time
}

def ejecutar_comando(texto):
    accion = COMMANDS.get(texto, cmd_notfound)
    accion()

def main():
    print("Habla...")
    log_event("Sistema inicializado")
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=device,
                           dtype="int16", channels=1, callback=audio_callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                texto = json.loads(result).get("text", "").strip()
                if texto:
                    print(f"Dijiste: {texto}")
                    ejecutar_comando(texto)

if __name__ == "__main__":
    main()