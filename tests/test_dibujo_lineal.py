# -*- coding: utf-8 -*-
"""El dibujo lineal cortable — lo pidió Anuar el 2026-08-14.

*"quiero el dibujo lineal puro y que las líneas se puedan engrosar pues lo
cortaré"* … *"con pequeñas uniones para que no se suelten las piezas pero
sirva para trazarlo"*.

Lo que se prueba aquí es lo único que puede arruinarle el material: que los
puentes de verdad sostengan las piezas, y que el grosor pedido en milímetros
sea milímetros de verdad.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

cv2 = pytest.importorskip("cv2")

from EDITOR.dibujo_lineal import (_piezas_sueltas, _poner_puentes,   # noqa: E402
                                  _puentes_dirigidos, MAX_AMPLIACION)


def _dona(lado=200, r_ext=70, r_int=40, grueso=6):
    """Un anillo: el disco de adentro queda suelto si nada lo sostiene.

    Es el caso real del blanco de un ojo o del hueco de una letra.
    """
    img = np.zeros((lado, lado), np.uint8)
    cv2.circle(img, (lado // 2, lado // 2), r_ext, 255, grueso)
    cv2.circle(img, (lado // 2, lado // 2), r_int, 255, grueso)
    return img


def test_sin_puentes_las_piezas_se_caen():
    """Si no se hace nada, el anillo deja 2 pedazos sueltos. Ese es el
    problema que hay que resolver, y conviene tenerlo medido."""
    sueltas, _ = _piezas_sueltas(_dona())
    assert sueltas == 2


def test_los_puentes_dejan_todo_sostenido():
    """Lo que importa de verdad: después de los puentes, cero piezas sueltas."""
    d = _dona()
    con = _poner_puentes(d, px_mm=4.0, puente_mm=1.5, cada_mm=6.0)
    sueltas, _ = _piezas_sueltas(con)
    assert sueltas == 0, f"quedaron {sueltas} pedazos que se caen"


def test_los_puentes_no_borran_el_dibujo():
    """Un puente es una interrupción chica, no una podadora: la línea tiene
    que seguir ahí. Si se borra de más, el estarcido ya no dibuja nada."""
    d = _dona()
    con = _poner_puentes(d, px_mm=4.0, puente_mm=1.5, cada_mm=6.0)
    queda = (con > 0).sum() / max(1, (d > 0).sum())
    assert queda > 0.5, f"se borró demasiada línea: queda {queda:.0%}"


def test_puentes_mas_juntos_sostienen_mas():
    """La perilla tiene que ir en el sentido que dice el aviso: si sobran
    piezas sueltas, juntar los puentes debe mejorar, nunca empeorar."""
    d = _dona(lado=300, r_ext=120, r_int=70, grueso=8)
    lejos, _ = _piezas_sueltas(_poner_puentes(d, 4.0, 1.5, 60.0))
    cerca, _ = _piezas_sueltas(_poner_puentes(d, 4.0, 1.5, 8.0))
    assert cerca <= lejos


def test_lo_que_toca_la_orilla_no_cuenta_como_suelto():
    """El material que llega al borde de la hoja está sujeto por la hoja
    misma. Contarlo como suelto haría que el módulo pidiera puentes de más."""
    img = np.zeros((100, 100), np.uint8)
    cv2.line(img, (0, 50), (99, 50), 255, 3)       # parte la hoja en dos
    sueltas, pedazos = _piezas_sueltas(img)
    assert pedazos == 2 and sueltas == 0


def test_los_puentes_dirigidos_no_dejan_nada_suelto():
    """LO QUE DE VERDAD RESUELVE EL TRABAJO. La rejilla ciega dejaba 348
    pedazos sueltos en las K-pop porque las islas eran más chicas que su
    paso. Yendo por cada pieza que se cae, quedaron 2 — y esas 2 son tan
    chicas que el puente no cabe, lo cual se avisa arriba."""
    d = _dona()
    con, puestos, sueltas = _puentes_dirigidos(d, grosor_px=6)
    assert sueltas == 0, f"quedaron {sueltas} sueltas con {puestos} puentes"
    assert puestos >= 1


def test_los_puentes_dirigidos_aguantan_varias_islas_anidadas():
    """Anillo dentro de anillo: al unir la isla de en medio con la de afuera,
    el par puede seguir suelto. Por eso el proceso se repite."""
    img = np.zeros((320, 320), np.uint8)
    for r in (140, 110, 75, 45):
        cv2.circle(img, (160, 160), r, 255, 6)
    antes, _ = _piezas_sueltas(img)
    assert antes >= 3
    _con, _p, sueltas = _puentes_dirigidos(img, grosor_px=6)
    assert sueltas == 0


def test_los_puentes_dirigidos_no_tocan_lo_que_ya_esta_bien():
    """Si nada se cae, no se abre ni un puente: cada puente es un pedacito de
    dibujo que se pierde."""
    img = np.zeros((120, 120), np.uint8)
    cv2.line(img, (0, 60), (119, 60), 255, 4)      # llega a las dos orillas
    _con, puestos, sueltas = _puentes_dirigidos(img, grosor_px=4)
    assert (puestos, sueltas) == (0, 0)


def test_la_resolucion_no_se_inventa():
    """Ampliar una imagen chica no crea detalle. El tope está para que no se
    entregue un archivo que promete un fino que el original no tiene."""
    assert MAX_AMPLIACION <= 4.0


def test_el_grosor_va_en_milimetros_no_en_pixeles():
    """A 4 px por mm, un puente de 1.5 mm son 6 px. Si esto se desfasa, en el
    taller se pide 1.5 y sale cualquier cosa."""
    d = np.ones((80, 80), np.uint8) * 255
    con = _poner_puentes(d, px_mm=4.0, puente_mm=1.5, cada_mm=20.0)
    # La columna 10 no cae encima de la franja vertical (esa va en la 40), así
    # que ahí solo se ven los puentes horizontales, que es lo que se mide.
    fila = con[:, 10]
    # Cada franja borrada debe medir 6 px de ancho.
    cortes, actual = [], 0
    for v in fila:
        if v == 0:
            actual += 1
        elif actual:
            cortes.append(actual)
            actual = 0
    if actual:
        cortes.append(actual)
    assert cortes and all(c == 6 for c in cortes), cortes
