# -*- coding: utf-8 -*-
"""Las reglas de taller que Anuar dictó para las cajas (2026-08-06).

No son preferencias: son cómo trabaja. Si alguna se rompe, el DXF sale mal y
se pierde material real. Por eso quedan aquí y no solo en un comentario.
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import importlib.util as _ilu                                      # noqa: E402

_s = _ilu.spec_from_file_location("cajas_boxes", RAIZ / "TALLER" / "cajas_boxes.py")
cb = _ilu.module_from_spec(_s)
_s.loader.exec_module(cb)


# ── REGLA 1: el orden de las medidas es X, luego Y, al final H ───────────
def test_el_orden_es_x_y_h():
    """"20x15x7" = 20 de ancho, 15 de fondo, 7 de alto. Nunca al revés."""
    m = cb.que_medidas("crea una caja tipo cofre de 20x15x7")
    assert m["x"] == 200      # cm → mm
    assert m["y"] == 150
    assert m["h"] == 70


def test_con_dos_medidas_son_ancho_y_alto():
    m = cb.que_medidas("caja corazon de 45x7")
    assert m["x"] == 450 and m["h"] == 70


def test_el_orden_aguanta_como_el_las_escribe():
    """Con "cm" de por medio y espacios, que es como las dicta de verdad."""
    m = cb.que_medidas("una caja de 20 cm x 15 cm x 7 cm")
    assert (m["x"], m["y"], m["h"]) == (200, 150, 70)


# ── REGLA 2: cofre es cofre, no una caja rectangular ────────────────────
def test_cofre_es_pirate_chest():
    gen, _ = cb.que_generador("caja tipo cofre de 20x15x7")
    assert gen == "PirateChest"


def test_baul_tambien_es_cofre():
    gen, _ = cb.que_generador("hazme un baul de 30x20x15")
    assert gen == "PirateChest"


# ── REGLA 3: el grosor lleva compensación de kerf ───────────────────────
def test_el_kerf_esta_puesto_en_lo_que_el_midio():
    """Su MDF es 2.7 y él mete 2.5: 0.2 de diferencia, medido en el taller."""
    assert cb.KERF_MM == 0.2
    assert round(2.7 - cb.KERF_MM, 2) == 2.5
