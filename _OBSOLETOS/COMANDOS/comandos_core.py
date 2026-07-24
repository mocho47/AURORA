# -*- coding: utf-8 -*-
"""Comandos NEXUS v3 recuperados en AURORA: abrir apps/redes, escanear red, etc.
Ejecutables por lenguaje natural desde el chat."""
import os, subprocess, webbrowser

# app -> (tipo, destino). tipo: url | app
COMANDOS = {
    "facebook":   ("url", "https://facebook.com"),
    "whatsapp":   ("url", "https://web.whatsapp.com"),
    "instagram":  ("url", "https://instagram.com"),
    "youtube":    ("url", "https://youtube.com"),
    "tiktok":     ("url", "https://tiktok.com"),
    "gmail":      ("url", "https://mail.google.com"),
    "corel":      ("app", ["coreldrw.exe", "CorelDRW.exe"]),
    "coreldraw":  ("app", ["coreldrw.exe", "CorelDRW.exe"]),
    "aspire":     ("app", ["Aspire.exe"]),
    "silhouette": ("app", ["Silhouette Studio.exe", "SilhouetteStudio.exe"]),
    "rdworks":    ("app", ["RDWorksV8.exe", "RDWorks.exe"]),
    "explorador": ("app", ["explorer.exe"]),
    "navegador":  ("url", "https://www.google.com"),
}

def listar():
    return {"comandos": sorted(COMANDOS.keys()),
            "extra": ["escanear la red", "abrir <app>"]}

def _abrir_app(destinos):
    for d in destinos:
        try:
            os.startfile(d)  # busca en PATH/registro de Windows
            return True, d
        except Exception:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", d])
                return True, d
            except Exception:
                continue
    return False, destinos[0]

def ejecutar(texto: str) -> dict:
    t = (texto or "").lower()
    # escanear red
    if "escanea" in t and "red" in t:
        try:
            r = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=20)
            return {"status": "OK", "accion": "escanear_red", "salida": (r.stdout or "")[:4000]}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}
    # abrir app/red
    if "abre" in t or "abrir" in t or "lanza" in t:
        for nombre, (tipo, dest) in COMANDOS.items():
            if nombre in t:
                if tipo == "url":
                    webbrowser.open(dest)
                    return {"status": "OK", "accion": "abrir", "app": nombre, "url": dest}
                ok, usado = _abrir_app(dest if isinstance(dest, list) else [dest])
                return ({"status": "OK", "accion": "abrir", "app": nombre} if ok
                        else {"status": "ERROR", "app": nombre, "detalle": f"No encontré {usado}. ¿Está instalada?"})
        return {"status": "NO_MATCH", "detalle": "No reconocí qué abrir. Apps: " + ", ".join(sorted(COMANDOS))}
    return {"status": "NO_MATCH"}
