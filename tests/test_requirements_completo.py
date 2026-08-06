# -*- coding: utf-8 -*-
"""requirements.txt tiene que traer TODO lo que AURORA usa de verdad.

Estaba incompleto y nadie se enteraba: quien instalara desde ahí se quedaba
con una AURORA a medias —sin cajas, sin quitar fondos, sin DXF, sin Corel—
y sin un error que dijera por qué. Se descubrió el 2026-08-06 al medir qué
tan complejo sería instalarla en la PC de Rocío.

Esta prueba existe para que no vuelva a pasar cuando se agregue una librería
nueva y se olvide anotarla.
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Las que sin ellas AURORA deja de hacer algo que Anuar usa todos los días.
IMPRESCINDIBLES = {
    "boxes": "los 189 generadores de cajas",
    "ezdxf": "leer y medir DXF para cotizar el corte",
    "svgpathtools": "pasar las cajas de SVG a DXF",
    "rembg": "quitar el fondo de las fotos",
    "onnxruntime": "el motor que corre rembg",
    "vtracer": "vectorizar",
    "PyMuPDF": "revisar y arreglar los PDF de gran formato",
    "opencv-python": "medir y limpiar imágenes",
    "numpy": "base de todo el procesamiento de imagen",
    "pywin32": "hablarle a CorelDRAW",
    "ddgs": "buscar en internet",
}


def _listadas() -> set:
    """Los nombres de paquete que sí aparecen en requirements.txt."""
    txt = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    nombres = set()
    for linea in txt.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        # Se corta en lo que separa el nombre de la versión o del marcador:
        # "pywin32>=306; sys_platform == 'win32'" → "pywin32"
        nombre = linea.split(";")[0]
        for corte in (">=", "==", "<=", ">", "<", "["):
            nombre = nombre.split(corte)[0]
        nombres.add(nombre.strip().lower())
    return nombres


def test_no_falta_nada_de_lo_imprescindible():
    faltan = {p: para_que for p, para_que in IMPRESCINDIBLES.items()
              if p.lower() not in _listadas()}
    assert not faltan, (
        "requirements.txt no trae: "
        + ", ".join(f"{p} ({q})" for p, q in faltan.items()))


def test_corel_solo_se_instala_en_windows():
    """pywin32 en Linux revienta la instalación completa. Va con marcador."""
    txt = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    linea = next(l for l in txt.splitlines()
                 if l.strip().lower().startswith("pywin32"))
    assert "sys_platform" in linea, "pywin32 necesita el marcador de Windows"
