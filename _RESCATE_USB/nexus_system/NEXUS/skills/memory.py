import json, os, pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    f = "estado.json"
    if os.path.exists(f):
        d = json.load(open(f,"r",encoding="utf-8"))
        ultimo = d.get("ultimo_evento","No hay eventos.")
    else:
        ultimo = "No se encontró archivo de estado."
    print("=== NEXUS MEMORY ===")
    print(f"Último evento: {ultimo}")
    print("====================")
    speak(f"Último evento: {ultimo}")