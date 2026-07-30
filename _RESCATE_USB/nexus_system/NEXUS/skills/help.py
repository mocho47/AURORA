import pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    cmds = [
        "nexus status",
        "nexus salir",
        "nexus ayuda",
        "nexus memoria",
        "nexus log",
        "nexus hora",
        "nexus acceso"
    ]
    print("=== NEXUS HELP ===")
    for c in cmds:
        print(f"- {c}")
    print("==================")
    speak("Comandos disponibles: status, salir, ayuda, memoria, log, hora y acceso.")