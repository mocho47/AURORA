# -*- coding: utf-8 -*-
"""El menú se puede reordenar; lo que NO se puede es perder una pantalla.

Anuar reagrupó el menú el 2026-08-09 (*«son demasiadas pestañas revueltas»*).
Reacomodar 31 renglones a mano es justo donde se cae uno sin que nadie lo note
—y una función que existe pero ya no se puede abrir está muerta en la práctica,
que es exactamente lo que su regla prohíbe: no restar funciones.

Estas pruebas no opinan del orden. Solo cuidan que:
  · todo renglón del menú abra una pantalla que de verdad existe
  · toda pantalla del panel sea alcanzable desde el menú
  · cada renglón viva dentro de un grupo (nada suelto, se lo pidió así)
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PANEL = RAIZ / "TEMPLATES" / "panel-completo.html"

# Pantallas que a propósito NO tienen renglón: se abren desde otro lado.
SIN_RENGLON = {
    "taza",        # se abre desde Editor y Diseño
    "wappconn",    # se abre desde la alerta de WhatsApp
}


@pytest.fixture(scope="module")
def html():
    return PANEL.read_text(encoding="utf-8", errors="ignore")


def _menu(html):
    """[(id, texto)] de cada renglón, en orden.

    Se lee la barra COMPLETA, no solo <nav>: la Guía vive fija al pie, fuera de
    la lista que se desplaza. Si esto mirara únicamente <nav>, mover un renglón
    al pie lo daría por perdido y la prueba mentiría al revés.
    """
    barra = html[html.index('<div class="sidebar">'):html.index('<div class="main">')]
    out = []
    for a in re.finditer(r"<a[^>]*?onclick=\"go\('([a-z]+)'[^>]*>", barra):
        crudo = barra[a.end():barra.find("</a>", a.end())]
        texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", crudo)).strip()
        out.append((a.group(1), texto))
    return out


def _secciones(html):
    return set(re.findall(r'<section id="([a-z]+)"', html))


def test_ningun_renglon_apunta_al_vacio(html):
    """Un renglón que abre una pantalla inexistente truena al hacer clic."""
    secciones = _secciones(html)
    for ident, texto in _menu(html):
        assert ident in secciones, f"«{texto}» abre '{ident}', que no existe"


def test_no_se_perdio_ninguna_pantalla(html):
    """Toda pantalla debe ser alcanzable: si no, la función quedó enterrada."""
    del_menu = {i for i, _ in _menu(html)}
    huerfanas = _secciones(html) - del_menu - SIN_RENGLON
    assert not huerfanas, (
        f"pantallas sin cómo abrirse: {sorted(huerfanas)} — o se les pone "
        f"renglón, o se anotan en SIN_RENGLON diciendo desde dónde se abren")


def test_no_hay_renglones_repetidos(html):
    ids = [i for i, _ in _menu(html)]
    assert len(ids) == len(set(ids)), "hay una pantalla con dos renglones"


def test_todo_renglon_vive_en_un_grupo(html):
    """Anuar lo pidió literal: «el resto sin sueltos».

    Dos excepciones, ninguna por descuido: el Dashboard es la portada y va
    antes del primer grupo, y la Guía va fija al pie. Un manual no es un área
    del negocio —es la salida cuando uno se pierde— y metido en un grupo Anuar
    no lo encontró (2026-08-10: «¿dónde me entero del funcionamiento?»).
    """
    nav = html[html.index("<nav>"):html.index("</nav>")]
    primer_grupo = nav.index('<div class="nav-group">')
    antes = re.findall(r"onclick=\"go\('([a-z]+)'", nav[:primer_grupo])
    assert antes == ["dash"], f"renglones sueltos antes del primer grupo: {antes}"

    pie = html[html.index("</nav>"):html.index('<div class="main">')]
    assert re.findall(r"onclick=\"go\('([a-z]+)'", pie) == ["guia"], (
        "el pie de la barra es solo para la ayuda; lo demás va en un grupo")


def test_la_ayuda_se_ve_sin_desplazar_el_menu(html):
    """De nada sirve moverla al pie si se va con el scroll de la lista."""
    assert ".nav-pie" in html, "la Guía perdió su renglón fijo"
    for regla in ("flex-shrink:0",):
        assert regla in html[html.index(".nav-pie{"):html.index("}", html.index(".nav-pie{"))], (
            f".nav-pie necesita {regla} o el menú largo lo empuja fuera")
    assert "nav a, .nav-pie" in html, (
        "go() debe limpiar también el pie, si no se queda marcado para siempre")
