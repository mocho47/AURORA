# -*- coding: utf-8 -*-
"""SDKS de AURORA v3 — Validador y puente de ejecutables nativos.
Verifica la presencia real de FFmpeg e Inkscape en el sistema local.
"""
from __future__ import annotations
from pathlib import Path

# Rutas físicas a los binarios necesarios en tu carpeta de SDKs
FFMPEG_PATH = Path(r"C:\AURORA\SDKS\ffmpeg\bin\ffmpeg.exe")
INKSCAPE_PATH = Path(r"C:\AURORA\SDKS\inkscape\bin\inkscape.com")

def verificar_entorno_sdks() -> dict:
    """Confirma que los ejecutables respondan en la PC del taller."""
    ffmpeg_ok = FFMPEG_PATH.exists()
    inkscape_ok = INKSCAPE_PATH.exists()
    
    return {
        "status": "OK" if (ffmpeg_ok and inkscape_ok) else "FALTAN_BINARIOS",
        "ffmpeg": ffmpeg_ok,
        "inkscape": inkscape_ok
    }
