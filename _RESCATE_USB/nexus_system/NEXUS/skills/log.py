import pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    try:
        lines = open("nexus.log","r",encoding="utf-8").readlines()[-5:]
        print("=== NEXUS LOG ===")
        for l in lines:
            print(l.strip())
        print("=================")
        speak("Mostrando últimos eventos del log.")
    except:
        print("No se encontró nexus.log.")
        speak("No se encontró el archivo de log.")