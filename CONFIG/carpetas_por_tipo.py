# -*- coding: utf-8 -*-
"""AURORA · Dónde va cada archivo que se genera. UNA sola regla.

Anuar lo pidió el 2026-08-05: *"que todos los dxf siempre los deje en la carpeta
de descargas dxf, al igual que los pdf en la carpeta pdf y así sucesivamente,
siempre"*.

Antes cada motor decidía por su cuenta dónde guardar, así que un DXF podía
acabar en Descargas, otro en la carpeta del archivo original y otro en el
escritorio. Buscarlos después era el problema.

Ahora todos preguntan aquí. Si un motor nuevo la usa, respeta la regla sin
tener que acordarse de ella.
"""
from __future__ import annotations
from pathlib import Path

BASE = Path.home() / "Downloads"

# Extensión → carpeta. Todo lo que no esté aquí se agrupa por su extensión.
_CARPETA = {
    # Diseño y corte
    "dxf": "dxf", "svg": "svg", "cdr": "cdr", "ai": "ai", "eps": "eps",
    "plt": "plt", "nc": "cnc", "gcode": "cnc", "rd": "laser", "lbrn": "laser",
    # Documentos
    "pdf": "pdf", "docx": "docs", "doc": "docs", "txt": "txt",
    "xlsx": "excel", "xls": "excel", "csv": "excel",
    # Imagen
    "png": "imagenes", "jpg": "imagenes", "jpeg": "imagenes",
    "webp": "imagenes", "psd": "imagenes", "tif": "imagenes",
    # Video
    "mp4": "videos", "mov": "videos", "avi": "videos", "mkv": "videos",
    # Comprimidos
    "zip": "zip", "rar": "rar", "7z": "7z",
}


def carpeta_de(extension: str) -> Path:
    """A qué carpeta va este tipo de archivo."""
    ext = (extension or "").lower().lstrip(".")
    destino = BASE / _CARPETA.get(ext, ext or "otros")
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def donde_guardar(nombre: str, extension: str = "") -> Path:
    """Ruta completa donde debe quedar un archivo, sin pisar otro.

    Si ya existe uno con ese nombre, le agrega __2, __3... en vez de
    sobrescribirlo: perder un diseño por reusar el nombre es peor que tener
    dos archivos.
    """
    p = Path(nombre)
    ext = (extension or p.suffix).lower().lstrip(".")
    destino = carpeta_de(ext) / f"{p.stem}.{ext}"
    n = 2
    while destino.exists():
        destino = destino.parent / f"{p.stem}__{n}.{ext}"
        n += 1
    return destino


def todas() -> dict:
    """Las carpetas que existen y cuántos archivos tiene cada una."""
    salida = {}
    for carpeta in sorted(set(_CARPETA.values())):
        d = BASE / carpeta
        if d.exists():
            salida[carpeta] = len([x for x in d.iterdir() if x.is_file()])
    return salida
