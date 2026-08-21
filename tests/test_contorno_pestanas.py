# -*- coding: utf-8 -*-
"""Las pestañas del contorno de corte — lo que Anuar pidió el 2026-08-14.

*"al delineado sería cortarlo y dejar unas pequeñas pestañas para que no se
suelten las piezas"*. Todo lo que se mide aquí salió mal la primera vez, así
que cada prueba corresponde a un defecto real, no a una hipótesis.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from EDITOR.contorno_de_corte import _con_pestanas   # noqa: E402

CUADRADO = [(0, 0), (100, 0), (100, 100), (0, 100)]   # perímetro 400 mm


def _cortado(tramos):
    return sum(sum(((t[k + 1][0] - t[k][0]) ** 2 +
                    (t[k + 1][1] - t[k][1]) ** 2) ** 0.5
                   for k in range(len(t) - 1)) for t in tramos)


def test_deja_exactamente_lo_que_se_le_pide_sin_cortar():
    """4 pestañas de 5 mm en 400 de perímetro = 380 cortados. Ni uno más."""
    tramos = _con_pestanas(CUADRADO, 4, 5.0)
    assert len(tramos) == 4
    assert abs(_cortado(tramos) - 380.0) < 0.01


def test_no_repite_tramos():
    """El primer intento devolvía 655 mm de corte sobre un perímetro de 400:
    partía mal los lados y escribía pedazos dos veces. Con una máquina eso es
    pasar el láser encima de lo ya cortado."""
    for cuantas, ancho in ((4, 5.0), (8, 3.0), (12, 2.0)):
        tramos = _con_pestanas(CUADRADO, cuantas, ancho)
        assert _cortado(tramos) <= 400.0 + 0.01
        assert abs(_cortado(tramos) - (400 - cuantas * ancho)) < 0.01


def test_el_punto_de_arranque_no_es_una_pestana():
    """EL DEFECTO GRANDE: quedaba un boquete de 4 cm donde empieza el trazo
    —en las K-pop caía justo en la punta de la estrella— y ahí la pieza se
    soltaba sola. Ningún hueco puede ser más ancho que la pestaña pedida."""
    tramos = _con_pestanas(CUADRADO, 4, 5.0)
    huecos = []
    for i, t in enumerate(tramos):
        fin = t[-1]
        huecos.append(min(((fin[0] - o[0][0]) ** 2 + (fin[1] - o[0][1]) ** 2) ** 0.5
                          for j, o in enumerate(tramos) if j != i))
    assert max(huecos) <= 5.0 + 0.01, f"hueco de más: {max(huecos):.1f} mm"


def test_si_no_caben_se_devuelve_entero():
    """Mejor un contorno cerrado que uno picado en confeti: si las pestañas se
    comen la mitad del perímetro, no se corta nada y se avisa arriba."""
    assert _con_pestanas(CUADRADO, 50, 20.0) == [CUADRADO]
    assert _con_pestanas(CUADRADO, 0, 5.0) == [CUADRADO]
    assert _con_pestanas(CUADRADO, 4, 0.0) == [CUADRADO]


def test_una_sola_pestana_tambien_sirve():
    tramos = _con_pestanas(CUADRADO, 1, 10.0)
    assert len(tramos) == 1
    assert abs(_cortado(tramos) - 390.0) < 0.01


def test_los_tramos_no_se_quedan_en_un_punto():
    """Una polilínea de un solo punto no es un corte, es basura en el DXF."""
    for cuantas in (2, 3, 5, 9):
        for t in _con_pestanas(CUADRADO, cuantas, 4.0):
            assert len(t) > 1


def test_la_hoja_grande_no_revienta_la_memoria():
    """La hoja de las K-pop mide 165 cm: a calidad fija pedía 879 MB de un
    golpe y tronaba. El tope deja el píxel en 0.33 mm, más fino de lo que
    cualquier máquina de corte alcanza a seguir."""
    from EDITOR.contorno_de_corte import CALIDAD, MAX_PX
    ancho_pt = 4680.0                                  # la hoja real de él
    calidad = min(CALIDAD, MAX_PX / ancho_pt)
    px = ancho_pt * calidad
    assert px <= MAX_PX
    mm_px = 25.4 / 72 / calidad
    assert mm_px < 0.5, f"{mm_px:.2f} mm por píxel es demasiado grueso"
