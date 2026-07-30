import sys, pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    print("Nexus se apaga...")
    speak("Nexus se apaga. Hasta luego.")
    sys.exit(0)