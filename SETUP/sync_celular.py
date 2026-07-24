# -*- coding: utf-8 -*-
"""Sincroniza el celular (Android, USB) y organiza TODO por tipo.
Requiere: cel conectado a ESTA PC + 'Depuracion USB' activada + autorizar en el cel.
Copia (no borra del cel) y ordena: videos con videos, fotos con fotos, etc."""
import subprocess, sys, shutil
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ADB = r"C:\AURORA\TOOLS\platform-tools\adb.exe"
IMPORT = Path(r"C:\AURORA\CELULAR_IMPORT")

DEST = {
    "video": (r"C:\Users\Administrador\Videos\CELULAR", (".mp4", ".mov", ".avi", ".mkv", ".3gp")),
    "foto":  (r"C:\Users\Administrador\Pictures\FOTOS_CELULAR", (".jpg", ".jpeg", ".png", ".heic", ".webp")),
    "pdf":   (r"C:\Users\Administrador\Documents\PDF", (".pdf",)),
    "zip":   (r"C:\Users\Administrador\Documents\ZIP", (".zip", ".rar", ".7z")),
    "audio": (r"C:\Users\Administrador\Music\CELULAR", (".mp3", ".wav", ".m4a", ".opus", ".ogg")),
    "doc":   (r"C:\Users\Administrador\Documents\OFFICE", (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt")),
}
CARPETAS_CEL = ["/sdcard/DCIM", "/sdcard/Pictures", "/sdcard/Download", "/sdcard/Movies",
                "/sdcard/WhatsApp/Media", "/sdcard/Documents"]


def conectado():
    try:
        r = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=20)
        return [l.split("\t")[0] for l in r.stdout.splitlines() if "\tdevice" in l]
    except Exception as e:
        return []


def descargar():
    IMPORT.mkdir(parents=True, exist_ok=True)
    for c in CARPETAS_CEL:
        try:
            subprocess.run([ADB, "pull", c, str(IMPORT)], capture_output=True, text=True, timeout=3600)
        except Exception:
            pass
    return IMPORT


def organizar(origen):
    for d, _ in DEST.values():
        Path(d).mkdir(parents=True, exist_ok=True)
    movidos = {}
    for f in Path(origen).rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            for cat, (dest, exts) in DEST.items():
                if ext in exts:
                    try:
                        shutil.copy2(f, Path(dest) / f.name); movidos[cat] = movidos.get(cat, 0) + 1
                    except Exception:
                        pass
                    break
    return movidos


if __name__ == "__main__":
    dev = conectado()
    if not dev:
        print("NO hay celular conectado.")
        print("Pasos: 1) conecta el A15 por USB a ESTA PC  2) en el cel: Ajustes > Opciones de desarrollador > Depuracion USB ON  3) autoriza el aviso en el cel  4) corre de nuevo.")
    else:
        print("Celular conectado:", dev)
        org = descargar()
        print("Descargado a", org)
        m = organizar(org)
        print("Organizado por tipo:", m)
