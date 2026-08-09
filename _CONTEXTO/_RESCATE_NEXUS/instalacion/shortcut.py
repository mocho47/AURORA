import os, sys, winshell
from win32com.client import Dispatch
import pyttsx3

def speak(t):
    e = pyttsx3.init()
    e.say(t)
    e.runAndWait()

def main():
    desk = winshell.desktop()
    link = os.path.join(desk,"NEXUS.lnk")
    shell = Dispatch("WScript.Shell")
    sc = shell.CreateShortCut(link)
    sc.Targetpath = sys.executable
    sc.Arguments = f'"{os.path.abspath("ears/voice_response.py")}"'
    sc.WorkingDirectory = os.path.abspath(".")
    sc.IconLocation = os.path.abspath("nexus.ico")
    sc.save()
    print("Acceso directo creado en escritorio.")
    speak("Acceso directo creado en escritorio.")