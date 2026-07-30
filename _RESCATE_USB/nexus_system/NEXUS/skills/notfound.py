import pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    print("Comando no reconocido.")
    speak("Comando no reconocido, intenta de nuevo.")