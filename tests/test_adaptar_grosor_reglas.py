# -*- coding: utf-8 -*-
"""Las reglas de Anuar para adaptar un diseño a otro material (2026-08-06).

Salieron de una prueba real: las casas de Bob Esponja, Calamardo y el
Crustáceo Cascarudo, hechas para 3 mm, al 50% y en material de 2.5 mm.

Cada una de estas pruebas corresponde a algo que de verdad falló y que costó
material o lo habría costado.
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import importlib.util as _ilu                                      # noqa: E402

_s = _ilu.spec_from_file_location("adaptar_grosor",
                                  RAIZ / "TALLER" / "adaptar_grosor.py")
ag = _ilu.module_from_spec(_s)
_s.loader.exec_module(ag)


def _rect(cx, cy, ancho, largo, grados):
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    loc = [(-ancho / 2, -largo / 2), (ancho / 2, -largo / 2),
           (ancho / 2, largo / 2), (-ancho / 2, largo / 2)]
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in loc]


def _cruz(ancho, largo):
    h, L = ancho / 2, largo / 2
    return [(-h, -L), (h, -L), (h, -h), (L, -h), (L, h), (h, h),
            (h, L), (-h, L), (-h, h), (-L, h), (-L, -h), (-h, -h)]


# ── Las ranuras diagonales ya no se escapan ─────────────────────────────
# Anuar lo encontró a mano: "algunas vienen en posición diagonal y eso habría
# que rotarlas para poder ajustar de manera correcta". Rotar no hace falta.
def test_la_ranura_se_detecta_en_cualquier_angulo():
    for grados in (0, 15, 30, 45, 60, 90, 127, 180):
        es, direccion = ag._es_ranura(_rect(0, 0, 1.5, 20, grados), 1.5)
        assert es, f"se perdió la ranura a {grados}°"
        assert direccion is not None


def test_no_confunde_una_pieza_con_una_ranura():
    assert ag._es_ranura(_rect(0, 0, 60, 40, 33), 1.5)[0] is False


def test_no_confunde_un_cuadrito_con_una_ranura():
    """Una ranura es larga. Un cuadrado de 1.5×1.5 es otra cosa."""
    assert ag._es_ranura(_rect(0, 0, 1.5, 1.5, 20), 1.5)[0] is False


def test_no_toma_un_rombo_por_ranura():
    rombo = [(0, 0), (1.5, 0.6), (1.4, 20), (-0.1, 19.4)]
    assert ag._es_ranura(rombo, 1.5)[0] is False


# ── Los huecos en cruz se abren por brazo, sin alargarse ────────────────
def test_la_cruz_se_abre_a_lo_ancho_y_no_se_alarga():
    c = _cruz(1.5, 20)
    nuevos, lados = ag._ensanchar_hembra(c, 1.5, 0.5)
    assert lados == 8, "de los 12 lados solo se mueven los 8 largos"
    xs = [p[0] for p in nuevos]
    assert abs((max(xs) - min(xs)) - 20.0) < 1e-6, "el brazo no debe alargarse"
    # El brazo pasa de 1.5 a 2.5: cada lado largo se corrió 0.5.
    interiores = sorted({round(abs(p[0]), 3) for p in nuevos})
    assert abs(interiores[0] - 1.25) < 1e-6


def test_un_hueco_rectangular_solo_ensancha():
    r = [(-0.75, -10), (0.75, -10), (0.75, 10), (-0.75, 10)]
    nuevos, _ = ag._ensanchar_hembra(r, 1.5, 0.5)
    xs = [p[0] for p in nuevos]
    ys = [p[1] for p in nuevos]
    assert abs((max(xs) - min(xs)) - 2.5) < 1e-6
    assert abs((max(ys) - min(ys)) - 20.0) < 1e-6


def test_una_pieza_grande_no_se_toca():
    assert ag._ensanchar_hembra([(0, 0), (60, 0), (60, 40), (0, 40)],
                                1.5, 0.5)[1] == 0


# ── El grabado NUNCA se deforma ─────────────────────────────────────────
# Se activaron los dientes y el buscador entró a los contornos del "60" y el
# "10" de la casa de Bob, dejándolos hechos garabatos. Sin las etiquetas no se
# sabe qué pieza es cuál al armar.
def test_un_numero_grabado_se_reconoce_como_grabado():
    """Un dígito: chico, muchos vértices, segmentos cortísimos."""
    import math as m
    digito = [(m.cos(i / 24 * 2 * m.pi) * 2 + (i % 3) * 0.2,
               m.sin(i / 24 * 2 * m.pi) * 3) for i in range(24)]
    assert ag._es_grabado(digito, 1.5) is True


def test_el_contorno_de_una_pieza_no_es_grabado():
    """Grande y con tramos largos: es un corte, no una letra."""
    pieza = [(0, 0), (200, 0), (200, 150), (120, 150), (120, 100), (0, 100)]
    assert ag._es_grabado(pieza, 1.5) is False


def test_una_ranura_no_es_grabado():
    assert ag._es_grabado(_rect(0, 0, 1.5, 20, 0), 1.5) is False
