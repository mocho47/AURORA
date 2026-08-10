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
    """[(id, texto)] de cada renglón, en orden."""
    nav = html[html.index("<nav>"):html.index("</nav>")]
    out = []
    for a in re.finditer(r"<a[^>]*?onclick=\"go\('([a-z]+)'[^>]*>", nav):
        crudo = nav[a.end():nav.find("</a>", a.end())]
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

    El Dashboard es la única excepción: es la portada, va antes del primer
    grupo a propósito.
    """
    nav = html[html.index("<nav>"):html.index("</nav>")]
    primer_grupo = nav.index('<div class="nav-group">')
    antes = re.findall(r"onclick=\"go\('([a-z]+)'", nav[:primer_grupo])
    assert antes == ["dash"], f"renglones sueltos antes del primer grupo: {antes}"
