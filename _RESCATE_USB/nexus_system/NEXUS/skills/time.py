import datetime, pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    h = datetime.datetime.now().strftime("%H:%M:%S")
    print("=== NEXUS TIME ===")
    print(f"Hora actual: {h}")
    print("==================")
    speak(f"La hora actual es {h}")