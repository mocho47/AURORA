import os
import sys
import threading
import pyttsx3
import webbrowser
import tkinter as tk
from tkinter import ttk

def voz(texto):
    threading.Thread(target=lambda: pyttsx3.init().say(texto).runAndWait(), daemon=True).start()

def ejecutar_comando_trae(cmd):
    cmd = cmd.lower().strip()
    if "facebook" in cmd:
        webbrowser.open("https://facebook.com")
    elif "instagram" in cmd:
        webbrowser.open("https://instagram.com")
    elif "youtube" in cmd:
        webbrowser.open("https://youtube.com")
    elif "tiktok" in cmd:
        webbrowser.open("https://tiktok.com")
    elif "whatsapp" in cmd:
        webbrowser.open("https://web.whatsapp.com")

root = tk.Tk()
root.title("NEXUS")
root.geometry("900x600")
root.configure(bg="#0f1222")
root.resizable(False, False)

tk.Label(root, text="NEXUS", font=("Segoe UI", 60, "bold"), fg="#ffd700", bg="#0f1222").pack(pady=60)
tk.Label(root, text="Versión limpia y funcional", font=("Segoe UI", 24), fg="white", bg="#0f1222").pack(pady=20)

def probar():
    voz("Nexus funcionando al cien por cien")
    webbrowser.open("https://facebook.com")

ttk.Button(root, text="PROBAR AHORA - ABRIR FACEBOOK", command=probar, style="TButton").pack(pady=40)

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 18, "bold"), padding=20)

voz("Bienvenido a Nexus")
root.mainloop()
