# -*- coding: utf-8 -*-
"""AURORA · Plantillas de prenda para sublimar — a 300 DPI de verdad

Anuar lo pidió el 2026-08-16 con un jersey de béisbol: *"¿puedes fusilar ese
diseño a 300 DPI?"*, y de una foto de producto de 890 × 1200 px eso no
existe. Un panel de jersey adulto a 300 DPI son casi 6500 × 8900 píxeles:
ampliar la foto da pixelón, no diseño.

Lo que sí resuelve el trabajo es esto: el LIENZO del panel al tamaño real,
con sus guías y su sangrado, y el diseño acomodado encima al tamaño correcto.
Lo que se imprime no es la foto — es este archivo.

**Las medidas son de PRENDA TERMINADA**, medida a lo plano sobre la mesa (el
ancho es la mitad del contorno, que es como se mide una prenda extendida). El
sangrado va POR FUERA: si el color no pasa de la línea de corte, queda el
filo blanco de tela sin sublimar — el error más caro del oficio, porque no se
ve hasta que la prenda ya está armada.

El mismo día pidió el catálogo completo: *"intégrale playeras polo y cuello
redondo y cuello redondo manga larga, gorras, mandiles, pañaleros"*.

Programas del ramo, para cuando haga falta más que esto: **CLO 3D** y
**Marvelous Designer** (armar la prenda en 3D y ver cómo cae la tela — el más
fácil de los profesionales), **Valentina/Seamly2D** (patronaje, gratis y de
código abierto, pero es el más difícil), **Optitex/Audaces/Gerber**
(industrial, caro).

Correr:
    python EDITOR/plantilla_prenda.py --prenda playera --talla M --panel frente
    python EDITOR/plantilla_prenda.py --prenda panalero --talla 6-12m
    python EDITOR/plantilla_prenda.py --lista
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DPI = 300
SANGRADO_CM = 2.0

# ── LAS MEDIDAS ─────────────────────────────────────────────────────────
# (ancho a lo plano, largo total) en centímetros de prenda terminada.
_ADULTO = {
    "CH": (46.0, 68.0), "S": (46.0, 68.0),
    "M": (49.0, 71.0),
    "G": (52.0, 74.0), "L": (52.0, 74.0),
    "XG": (55.0, 76.0), "XL": (55.0, 76.0),
    "2XL": (58.0, 78.0), "3XL": (61.0, 80.0),
}
# El jersey deportivo va más holgado que la playera de diario.
_JERSEY = {
    "CH": (48.0, 68.0), "S": (48.0, 68.0),
    "M": (51.0, 71.0),
    "G": (54.0, 74.0), "L": (54.0, 74.0),
    "XG": (57.0, 76.0), "XL": (57.0, 76.0),
    "2XL": (60.0, 78.0), "3XL": (63.0, 80.0),
}
_NINO = {
    "2": (32.0, 40.0), "4": (35.0, 44.0), "6": (38.0, 48.0),
    "8": (41.0, 52.0), "10": (44.0, 56.0), "12": (47.0, 60.0),
    "14": (50.0, 64.0), "16": (53.0, 66.0),
}
# La sudadera va más ancha y más corta que la playera: la tela es gruesa y la
# prenda se usa encima de otra.
_SUDADERA = {
    "CH": (52.0, 66.0), "S": (52.0, 66.0),
    "M": (55.0, 69.0),
    "G": (58.0, 72.0), "L": (58.0, 72.0),
    "XG": (61.0, 74.0), "XL": (61.0, 74.0),
    "2XL": (64.0, 76.0), "3XL": (67.0, 78.0),
}
_SUDADERA_NINO = {
    "2": (36.0, 40.0), "4": (39.0, 44.0), "6": (42.0, 48.0),
    "8": (45.0, 52.0), "10": (48.0, 56.0), "12": (51.0, 59.0),
    "14": (54.0, 62.0), "16": (57.0, 64.0),
}
# El pañalero se pide por meses, nunca por talla de letra.
_BEBE = {
    "0-3M": (24.0, 38.0), "3-6M": (26.0, 41.0), "6-12M": (28.0, 44.0),
    "12-18M": (30.0, 47.0), "18-24M": (32.0, 50.0),
}


def _cuerpo(pecho: float, largo: float, manga_largo: float) -> dict:
    """Los paneles de una prenda de cuerpo, sacados del pecho y el largo.

    La manga se imprime como el rectángulo que la contiene: es un trapecio,
    pero al panel de sublimación lo que le importa es que el color le sobre
    por todos lados.
    """
    return {
        "frente": (pecho, largo),
        "espalda": (pecho, largo),
        "manga": (round(pecho * 0.80, 1), manga_largo),
    }


def _tallas(base: dict, manga: float, extra=None) -> dict:
    d = {t: _cuerpo(p, l, manga) for t, (p, l) in base.items()}
    if extra:
        for t in d:
            d[t].update(extra)
    return d


PRENDAS = {
    "jersey": {
        "nombre": "Jersey deportivo (béisbol)",
        "paneles": _tallas(_JERSEY, 22.0),
    },
    "playera": {
        "nombre": "Playera cuello redondo",
        "paneles": _tallas(_ADULTO, 22.0),
    },
    "playera_ml": {
        "nombre": "Playera cuello redondo manga larga",
        "paneles": _tallas(_ADULTO, 58.0),
    },
    "polo": {
        "nombre": "Playera polo",
        # La polo lleva tapeta y cuello tejido: se imprimen aparte y casi
        # siempre van lisos, pero se dan por si el diseño los cruza.
        "paneles": _tallas(_ADULTO, 22.0,
                           extra={"tapeta": (10.0, 16.0), "cuello": (42.0, 9.0)}),
    },
    "playera_nino": {
        "nombre": "Playera cuello redondo infantil",
        "paneles": _tallas(_NINO, 16.0),
    },
    "panalero": {
        "nombre": "Pañalero (body de bebé)",
        # El largo ya incluye la entrepierna con los broches.
        "paneles": _tallas(_BEBE, 12.0),
    },
    "sudadera": {
        "nombre": "Sudadera cuello redondo",
        "paneles": _tallas(_SUDADERA, 60.0,
                           extra={"puno": (22.0, 8.0), "pretina": (48.0, 8.0)}),
    },
    "sudadera_capucha": {
        "nombre": "Sudadera con capucha (hoodie)",
        # La capucha son DOS piezas iguales y se imprimen por separado; la
        # bolsa canguro va aparte porque queda encimada al frente.
        "paneles": _tallas(_SUDADERA, 60.0,
                           extra={"capucha": (30.0, 36.0),
                                  "bolsa": (35.0, 22.0),
                                  "puno": (22.0, 8.0),
                                  "pretina": (48.0, 8.0)}),
    },
    "sudadera_nino": {
        "nombre": "Sudadera infantil",
        "paneles": _tallas(_SUDADERA_NINO, 44.0,
                           extra={"puno": (18.0, 7.0), "pretina": (40.0, 7.0)}),
    },
    "gorra": {
        "nombre": "Gorra",
        # La gorra no tiene tallas de pecho: es una sola, y lo que cambia es
        # el panel. Las medidas son de área de estampado, no de la tela.
        "paneles": {"UNI": {
            "frente": (14.0, 7.0),      # los dos paneles del frente juntos
            "panel": (13.0, 15.0),      # un panel suelto, gorra de 5 o 6
            "visera": (22.0, 8.0),
            "trasera": (14.0, 7.0),
        }},
    },
    "mandil": {
        "nombre": "Mandil (delantal)",
        "paneles": {
            "ADULTO": {"frente": (70.0, 90.0), "bolsa": (30.0, 20.0),
                       "pechera": (30.0, 30.0)},
            "NINO": {"frente": (45.0, 60.0), "bolsa": (22.0, 15.0),
                     "pechera": (22.0, 22.0)},
        },
    },
}
# ── EL ÁREA DE TRABAJO ──────────────────────────────────────────────────
# Anuar lo corrigió el 2026-08-16: el lienzo útil no es el panel de tela
# entero, es **el área donde de verdad se estampa**. Son dos trabajos
# distintos y conviene poder pedir cualquiera de los dos:
#   - panel completo → sublimación all-over, el color llega hasta la costura.
#   - área de trabajo → estampado localizado (plancha, vinil, DTF): un
#     recuadro al centro del pecho, que es lo que se hace la mayoría de las
#     veces y donde el diseño de verdad se ve.
# (ancho, alto, desde el cuello hacia abajo) en centímetros.
AREAS = {
    "jersey":      {"frente": (30.0, 40.0, 7.0), "espalda": (30.0, 40.0, 8.0),
                    "manga": (8.0, 20.0, 3.0)},
    "playera":     {"frente": (30.0, 40.0, 7.0), "espalda": (30.0, 40.0, 8.0),
                    "manga": (8.0, 20.0, 3.0)},
    "playera_ml":  {"frente": (30.0, 40.0, 7.0), "espalda": (30.0, 40.0, 8.0),
                    "manga": (9.0, 30.0, 5.0)},
    "polo":        {"frente": (25.0, 30.0, 9.0), "espalda": (30.0, 40.0, 8.0),
                    "manga": (8.0, 20.0, 3.0)},
    "playera_nino": {"frente": (22.0, 28.0, 5.0), "espalda": (22.0, 28.0, 6.0),
                     "manga": (7.0, 15.0, 3.0)},
    "panalero":    {"frente": (15.0, 18.0, 4.0), "espalda": (15.0, 18.0, 5.0),
                    "manga": (6.0, 10.0, 2.0)},
    # En la sudadera con capucha el área baja menos: la bolsa canguro
    # empieza como a 38 cm del cuello y lo que caiga ahí se arruga.
    "sudadera":         {"frente": (30.0, 35.0, 8.0), "espalda": (30.0, 40.0, 9.0),
                         "manga": (9.0, 30.0, 5.0)},
    "sudadera_capucha": {"frente": (30.0, 28.0, 8.0), "espalda": (30.0, 40.0, 9.0),
                         "manga": (9.0, 30.0, 5.0), "capucha": (20.0, 14.0, 2.0),
                         "bolsa": (30.0, 16.0, 2.0)},
    "sudadera_nino":    {"frente": (22.0, 26.0, 6.0), "espalda": (22.0, 30.0, 7.0),
                         "manga": (8.0, 22.0, 4.0)},
    "gorra":  {"frente": (12.0, 6.0, 1.0), "panel": (10.0, 12.0, 1.0),
               "visera": (18.0, 5.0, 1.5), "trasera": (12.0, 6.0, 1.0)},
    "mandil": {"frente": (25.0, 30.0, 12.0), "pechera": (20.0, 20.0, 3.0),
               "bolsa": (22.0, 12.0, 2.0)},
}


def area_trabajo(prenda: str = "playera", panel: str = "frente"):
    """(ancho, alto, desde_el_cuello) del área estampable, en cm. None si no hay."""
    return AREAS.get(_cual_prenda(prenda), {}).get(
        (panel or "frente").lower().strip())


# ── LA SILUETA DE LA PRENDA ─────────────────────────────────────────────
# Anuar lo reclamó dos veces el 2026-08-16: *"el área de trabajo sigue siendo
# un rectángulo con el diseñador de prendas"*. Tenía razón. Ver el diseño
# dentro de una hoja blanca no te dice nada; verlo sobre la playera te dice
# de un vistazo si va muy alto, muy chico o encima de una costura.
#
# Las siluetas se DIBUJAN, no son fotos: geometría que sale limpia a
# cualquier tamaño y sin líos de derechos. Las coordenadas van en unidades
# del **ancho del cuerpo** (0 a 1 de izquierda a derecha del torso) y del
# **largo del cuerpo** (0 arriba, 1 abajo), para que cada talla se dibuje a
# su proporción real y no todas iguales.
#
# `caja` es dónde cae el torso dentro del dibujo completo (las mangas
# extendidas se salen del torso, por eso el lienzo es más ancho que 1).
_SILUETAS = {
    # (ancho total del lienzo en anchos de cuerpo, x donde empieza el torso)
    "playera": {
        "lienzo": (1.90, 0.45), "cuello": 0.13,
        "cuerpo": [(0.45, .02), (0.78, .03), (0.95, .13), (1.12, .03),
                   (1.45, .02), (1.85, .30), (1.62, .40), (1.45, .30),
                   (1.42, 1.0), (0.48, 1.0), (0.45, .30), (0.28, .40),
                   (0.05, .30)],
    },
    "playera_ml": {
        "lienzo": (1.90, 0.45), "cuello": 0.13,
        "cuerpo": [(0.45, .02), (0.78, .03), (0.95, .13), (1.12, .03),
                   (1.45, .02), (1.88, .30), (1.80, .78), (1.58, .80),
                   (1.45, .32), (1.42, 1.0), (0.48, 1.0), (0.45, .32),
                   (0.32, .80), (0.10, .78), (0.02, .30)],
    },
    "polo": {
        "lienzo": (1.90, 0.45), "cuello": 0.11, "tapeta": True,
        "cuerpo": [(0.45, .03), (0.80, .01), (0.95, .12), (1.10, .01),
                   (1.45, .03), (1.85, .30), (1.62, .40), (1.45, .30),
                   (1.42, 1.0), (0.48, 1.0), (0.45, .30), (0.28, .40),
                   (0.05, .30)],
    },
    "sudadera": {
        "lienzo": (1.96, 0.46), "cuello": 0.12, "pretina": 0.07, "punos": True,
        "cuerpo": [(0.46, .03), (0.78, .04), (0.95, .13), (1.14, .04),
                   (1.48, .03), (1.94, .30), (1.86, .76), (1.60, .78),
                   (1.48, .32), (1.46, 1.0), (0.46, 1.0), (0.44, .32),
                   (0.32, .78), (0.06, .76), (0.02, .30)],
    },
    "sudadera_capucha": {
        "lienzo": (1.96, 0.46), "cuello": 0.12, "pretina": 0.07,
        "punos": True, "capucha": True, "bolsa": True,
        "cuerpo": [(0.46, .07), (0.78, .08), (0.95, .17), (1.14, .08),
                   (1.48, .07), (1.94, .33), (1.86, .78), (1.60, .80),
                   (1.48, .35), (1.46, 1.0), (0.46, 1.0), (0.44, .35),
                   (0.32, .80), (0.06, .78), (0.02, .33)],
    },
    "panalero": {
        "lienzo": (1.86, 0.44), "cuello": 0.15,
        "cuerpo": [(0.44, .03), (0.76, .04), (0.93, .16), (1.10, .04),
                   (1.42, .03), (1.82, .32), (1.60, .43), (1.44, .33),
                   (1.40, .76), (1.16, .96), (1.05, 1.0), (0.81, 1.0),
                   (0.70, .96), (0.46, .76), (0.42, .33), (0.26, .43),
                   (0.04, .32)],
    },
    "gorra": {
        "lienzo": (1.30, 0.15), "cuello": 0.0, "es_gorra": True,
        "cuerpo": [(0.15, .72), (0.16, .42), (0.30, .16), (0.58, .04),
                   (0.87, .04), (1.10, .16), (1.18, .40), (1.15, .72)],
    },
    "mandil": {
        "lienzo": (1.20, 0.10), "cuello": 0.0, "es_mandil": True,
        "cuerpo": [(0.38, .00), (0.82, .00), (0.82, .10), (0.98, .18),
                   (1.10, .34), (1.12, 1.0), (0.08, 1.0), (0.10, .34),
                   (0.22, .18), (0.38, .10)],
    },
}
_SILUETAS["jersey"] = dict(_SILUETAS["playera"], tapeta=True)
_SILUETAS["playera_nino"] = _SILUETAS["playera"]
_SILUETAS["sudadera_nino"] = _SILUETAS["sudadera"]


def silueta(prenda: str = "playera", panel: str = "frente", talla: str = "M",
            ancho_px: int = 520, color_tela: str = "#FFFFFF",
            medida_cm=None, manga_largo=None, vista="frente"):
    """Dibuja la prenda y dice dónde cae el área de trabajo dentro del dibujo.

    Devuelve (imagen RGBA, caja) donde `caja` es (x, y, ancho, alto) en
    píxeles: exactamente el hueco donde va el diseño. La app pega ahí lo que
    el usuario armó, y así se ve el estampado sobre la prenda, no flotando en
    una hoja.

    El trazo lo hace `flat_prenda`: dibujo técnico con curvas y simetría, no
    el polígono tosco de la primera versión. Aquí solo se resuelven las
    medidas — cuánto mide de verdad esa talla, o la que tomaste con la cinta.
    """
    clave = _cual_prenda(prenda)
    med = medidas(clave, talla, "frente", medida_cm)
    area = area_trabajo(clave, panel)
    if not med:
        return None, None
    import importlib.util as _ilu
    _f = Path(__file__).with_name("flat_prenda.py")
    _s = _ilu.spec_from_file_location("flat_prenda", _f)
    _m = _ilu.module_from_spec(_s)
    _s.loader.exec_module(_m)
    return _m.dibujar(clave, med[0], med[1], ancho_px, color_tela, area,
                      manga_largo, vista=vista)


def _silueta_vieja(prenda, panel, talla, ancho_px, color_tela, medida_cm):
    """La primera versión, a base de polígonos. Se conserva solo de respaldo."""
    from PIL import Image, ImageDraw

    clave = _cual_prenda(prenda)
    forma = _SILUETAS.get(clave)
    med = medidas(clave, talla, "frente", medida_cm)
    area = area_trabajo(clave, panel)
    if not forma or not med:
        return None, None

    an_cm, al_cm = med[0], med[1]
    ancho_lienzo, x0 = forma["lienzo"]
    # Los dibujos de gorra y mandil no se rigen por el pecho: traen su propia
    # proporción, porque una gorra no es más ancha que alta como una playera.
    if forma.get("es_gorra"):
        an_cm, al_cm = 26.0, 16.0
    elif forma.get("es_mandil"):
        an_cm, al_cm = med[0], med[1]

    px_cm = ancho_px / (ancho_lienzo * an_cm)
    W = int(ancho_px)
    H = max(40, int(al_cm * px_cm) + 6)

    def _p(pt):
        return (int(pt[0] * an_cm * px_cm), int(pt[1] * al_cm * px_cm) + 3)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    borde = "#7d8794"
    cuerpo = [_p(q) for q in forma["cuerpo"]]
    d.polygon(cuerpo, fill=color_tela, outline=borde, width=2)

    # La capucha va DETRÁS del cuerpo, asomando por arriba de los hombros.
    if forma.get("capucha"):
        atras = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        da = ImageDraw.Draw(atras)
        da.polygon([_p((0.66, .10)), _p((0.74, -.01)), _p((0.95, -.04)),
                    _p((1.16, -.01)), _p((1.24, .10)), _p((1.14, .13)),
                    _p((0.95, .07)), _p((0.76, .13))],
                   fill=color_tela, outline=borde, width=2)
        img = Image.alpha_composite(atras, img)
        d = ImageDraw.Draw(img)
        # Los cordones, que es lo que hace que se lea "hoodie" de un vistazo.
        for x in (0.88, 1.02):
            d.line([_p((x, .14)), _p((x + .01, .30))], fill=borde, width=2)

    if forma.get("bolsa"):
        d.polygon([_p((0.62, .62)), _p((1.28, .62)), _p((1.24, .86)),
                   _p((0.66, .86))], outline=borde, width=2)
    if forma.get("pretina"):
        h = forma["pretina"]
        d.rectangle([_p((0.46, 1 - h))[0], _p((0.46, 1 - h))[1],
                     _p((1.46, 1.0))[0], _p((1.46, 1.0))[1]],
                    outline=borde, width=2)
    if forma.get("punos"):
        for a, b in (((0.02, .76), (0.10, .86)), ((1.86, .76), (1.94, .86))):
            d.line([_p(a), _p(b)], fill=borde, width=2)
    if forma.get("tapeta"):
        d.line([_p((0.95, .13)), _p((0.95, .30))], fill=borde, width=2)
        for y in (0.17, 0.24):
            cx, cy = _p((0.95, y))
            d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline=borde, width=1)
    if forma.get("es_gorra"):
        # La visera, que es medio óvalo saliendo por abajo del casco.
        d.chord([_p((0.10, .60))[0], _p((0.10, .60))[1],
                 _p((1.24, 1.0))[0], _p((1.24, 1.0))[1]],
                0, 180, fill=color_tela, outline=borde, width=2)
        d.line([_p((0.15, .70)), _p((1.15, .70))], fill=borde, width=2)
    if forma.get("es_mandil"):
        for a, b in (((0.38, .00), (0.20, -.06)), ((0.82, .00), (1.00, -.06))):
            d.line([_p(a), _p(b)], fill=borde, width=3)
    if forma.get("cuello"):
        d.arc([_p((0.76, -.03))[0], _p((0.76, -.03))[1],
               _p((1.14, forma["cuello"]))[0], _p((1.14, forma["cuello"]))[1]],
              0, 180, fill=borde, width=2)

    if not area:
        return img, None
    # DÓNDE CAE EL ÁREA. Centrada a lo ancho del torso y colgada del cuello,
    # que es como se mide en la mesa: con la regla desde la costura del cuello
    # hacia abajo.
    a_an, a_al, desde = area
    cx = (x0 + 0.5) * an_cm * px_cm
    if forma.get("es_gorra"):
        cx, arriba = 0.65 * an_cm * px_cm, 0.26 * al_cm * px_cm
    elif forma.get("es_mandil"):
        cx = 0.60 * an_cm * px_cm
        arriba = (desde / al_cm) * al_cm * px_cm
    else:
        arriba = (forma["cuello"] * al_cm + desde) * px_cm
    caja = (int(cx - a_an * px_cm / 2), int(arriba + 3),
            max(8, int(a_an * px_cm)), max(8, int(a_al * px_cm)))
    return img, caja


def sobre_la_prenda(prenda="playera", talla="M", panel="frente", diseno=None,
                    color_tela="#FFFFFF", ancho_px=520, medida_cm=None,
                    marcar=True, manga_largo=None, vista="frente"):
    """La prenda dibujada con el diseño ya puesto en su lugar. Para VER.

    El archivo que se manda a imprimir sigue siendo el área o el panel — esto
    es la vista, la que evita mandar a plancha un logo que iba tres dedos más
    arriba.
    """
    from PIL import Image, ImageDraw

    img, caja = silueta(prenda, panel, talla, ancho_px, color_tela, medida_cm,
                        manga_largo, vista)
    if img is None:
        return None
    # El área ya viene marcada por el dibujo técnico; aquí solo se pega el
    # diseño adentro.
    marcar = False
    if caja and diseno is not None:
        x, y, w, h = caja
        d = diseno.convert("RGBA")
        # Se ajusta al área respetando su forma: nunca se deforma un diseño
        # para que quepa, se acomoda del lado que tope.
        esc = min(w / d.width, h / d.height)
        d = d.resize((max(1, int(d.width * esc)), max(1, int(d.height * esc))),
                     Image.LANCZOS)
        img.alpha_composite(d, (x + (w - d.width) // 2, y + (h - d.height) // 2))
    if caja and marcar:
        dr = ImageDraw.Draw(img)
        x, y, w, h = caja
        for i in range(0, w, 12):          # rayita cortada, para que se lea
            dr.line([(x + i, y), (x + min(i + 6, w), y)], fill="#2d6cdf", width=2)
            dr.line([(x + i, y + h), (x + min(i + 6, w), y + h)],
                    fill="#2d6cdf", width=2)
        for j in range(0, h, 12):
            dr.line([(x, y + j), (x, y + min(j + 6, h))], fill="#2d6cdf", width=2)
            dr.line([(x + w, y + j), (x + w, y + min(j + 6, h))],
                    fill="#2d6cdf", width=2)
    return img


_ALIAS = {
    "cuello redondo": "playera", "redondo": "playera", "camiseta": "playera",
    "manga larga": "playera_ml", "playera manga larga": "playera_ml",
    "ml": "playera_ml", "baseball": "jersey", "beisbol": "jersey",
    "body": "panalero", "pañalero": "panalero", "panialero": "panalero",
    "delantal": "mandil", "infantil": "playera_nino", "nino": "playera_nino",
    "niño": "playera_nino",
}


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _carpeta(ext: str) -> Path:
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location(
            "carpetas_por_tipo", RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de(ext)
    except Exception:
        d = Path.home() / "Downloads" / ext
        d.mkdir(parents=True, exist_ok=True)
        return d


def _cm_px(cm: float) -> int:
    return int(round(cm / 2.54 * DPI))


def _cual_prenda(nombre: str) -> str:
    n = (nombre or "playera").lower().strip().replace("_", " ")
    if n.replace(" ", "_") in PRENDAS:
        return n.replace(" ", "_")
    return _ALIAS.get(n, n.replace(" ", "_"))


def a_la_medida(ancho_cm: float, largo_cm: float, manga_cm=None) -> dict:
    """Los paneles sacados de la prenda REAL, medida con cinta.

    Anuar lo pidió el 2026-08-16 y tiene toda la razón: *"ajustar la prenda a
    medida real, así con la cinta de medir acá no hay falla"*. Una talla M de
    un proveedor no es la M de otro — a veces hay 4 cm de diferencia, que es
    justo lo que hace que el estampado quede corrido. La talla es una
    suposición; la cinta es un dato.

    Se mide la prenda EXTENDIDA sobre la mesa:
      `ancho_cm` — de costura a costura por debajo de la manga (la mitad del
                   contorno, no la vuelta completa).
      `largo_cm` — del hombro, junto al cuello, hasta la bastilla.
      `manga_cm` — (ancho, largo) de la manga, si se quiere afinar; si no, se
                   saca del ancho de pecho como en las tallas de tabla.
    """
    a, l = float(ancho_cm), float(largo_cm)
    if a <= 0 or l <= 0:
        return {}
    d = _cuerpo(a, l, round(l * 0.30, 1))
    if manga_cm:
        d["manga"] = (float(manga_cm[0]), float(manga_cm[1]))
    return d


def medidas(prenda: str = "playera", talla: str = "M", panel: str = "frente",
            medida_cm=None, manga_cm=None):
    """(ancho_cm, alto_cm) de un panel, o None si no existe esa combinación.

    Si se pasa `medida_cm`, la cinta manda sobre la tabla de tallas.
    """
    p = (panel or "frente").lower().strip()
    if medida_cm:
        m = a_la_medida(medida_cm[0], medida_cm[1], manga_cm)
        if p in m:
            return m[p]
    pr = PRENDAS.get(_cual_prenda(prenda))
    if not pr:
        return None
    t = (talla or "M").upper().strip()
    if t not in pr["paneles"]:
        t = next(iter(pr["paneles"]))
    return pr["paneles"][t].get(p)


def catalogo() -> str:
    """Todo lo que sabe hacer, con sus tallas y paneles."""
    lineas = []
    for clave, pr in PRENDAS.items():
        tallas = ", ".join(pr["paneles"])
        paneles = ", ".join(next(iter(pr["paneles"].values())))
        lineas.append(f"• **{pr['nombre']}** (`{clave}`)\n"
                      f"   tallas: {tallas}\n   paneles: {paneles}")
    return "👕 **Prendas que puedo plantillar a 300 DPI**\n\n" + "\n".join(lineas)


def generar(prenda: str = "playera", talla: str = "M", panel: str = "frente",
            diseno: str = "", sangrado_cm: float = SANGRADO_CM,
            guias: bool = True, medida_cm=None, manga_cm=None) -> dict:
    """Arma el lienzo del panel a 300 DPI, con el diseño encima si lo hay.

    `medida_cm=(ancho, largo)` de la prenda medida con cinta manda sobre la
    tabla de tallas: es un dato en vez de una suposición.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    clave = _cual_prenda(prenda)
    pr = PRENDAS.get(clave)
    if not pr:
        return {"status": "PRENDA_RARA",
                "detalle": f"No conozco «{prenda}». Tengo: "
                           + ", ".join(PRENDAS)}
    t = (talla or "M").upper().strip()
    p = (panel or "frente").lower().strip()
    a_mano = bool(medida_cm)
    med = medidas(clave, t, p, medida_cm, manga_cm)
    if not med:
        if t not in pr["paneles"]:
            return {"status": "TALLA_RARA",
                    "detalle": f"En {pr['nombre']} las tallas son: "
                               + ", ".join(pr["paneles"])}
        return {"status": "PANEL_RARO",
                "detalle": f"En {pr['nombre']} los paneles son: "
                           + ", ".join(pr["paneles"][t])}

    an_cm, al_cm = med
    total_an = an_cm + sangrado_cm * 2
    total_al = al_cm + sangrado_cm * 2
    W, H = _cm_px(total_an), _cm_px(total_al)
    sang = _cm_px(sangrado_cm)

    lienzo = Image.new("RGB", (W, H), (255, 255, 255))

    puesto, dpi_real = "", DPI
    if diseno:
        d = Path(diseno)
        if not d.exists():
            return {"status": "DISENO_NO_EXISTE",
                    "detalle": f"No encontré el diseño: {diseno}"}
        img = Image.open(d).convert("RGBA")
        # SE CUBRE TODO EL LIENZO, sangrado incluido, recortando lo que sobre.
        # Ajustarlo "a que quepa" dejaría franjas blancas justo en la orilla,
        # que es donde el filo sin sublimar se nota.
        esc = max(W / img.width, H / img.height)
        img = img.resize((max(1, int(img.width * esc)),
                          max(1, int(img.height * esc))), Image.LANCZOS)
        lienzo.paste(img, ((W - img.width) // 2, (H - img.height) // 2), img)
        dpi_real = round(min(img.width / (total_an / 2.54),
                             img.height / (total_al / 2.54)))
        puesto = str(d)

    capa_p = None
    if guias:
        # Las guías van en capa aparte para poder quitarlas: se imprimen solo
        # en la prueba, nunca en la tela buena.
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g = ImageDraw.Draw(capa)
        g.rectangle([sang, sang, W - sang - 1, H - sang - 1],
                    outline=(0, 160, 255, 220), width=max(2, _cm_px(0.05)))
        g.line([(W // 2, 0), (W // 2, H)], fill=(255, 0, 0, 150),
               width=max(1, _cm_px(0.03)))
        capa_p = _carpeta("png") / f"GUIAS_{clave}_{p}_{t}.png"
        capa.save(capa_p, dpi=(DPI, DPI))

    etiqueta = (f"{clave.upper()}_{p}_{'CINTA' if a_mano else t}"
                f"_{total_an:g}x{total_al:g}cm_300dpi")
    destino = _carpeta("png") / f"{etiqueta}.png"
    k = 2
    while destino.exists():
        destino = destino.parent / f"{etiqueta}__{k}.png"
        k += 1
    lienzo.save(destino, dpi=(DPI, DPI))

    r = {"status": "OK", "archivo": str(destino), "prenda": pr["nombre"],
         "clave": clave, "talla": ("a la medida" if a_mano else t), "panel": p,
         "prenda_cm": f"{an_cm:g} × {al_cm:g}",
         "con_sangrado_cm": f"{total_an:g} × {total_al:g}",
         "sangrado_cm": sangrado_cm, "px": f"{W} × {H}",
         "dpi": DPI, "dpi_real_diseno": dpi_real,
         "kb": round(destino.stat().st_size / 1024, 1)}
    if capa_p:
        r["guias"] = str(capa_p)
    if puesto:
        r["diseno"] = puesto
        if dpi_real < 200:
            r["aviso"] = (f"El diseño da {dpi_real} DPI a este tamaño, no 300. "
                          f"Se va a ver el pixel en la tela. Para un panel de "
                          f"{total_an:g} × {total_al:g} cm hace falta una "
                          f"imagen de {_cm_px(total_an)} × {_cm_px(total_al)} "
                          f"píxeles.")
    else:
        r["aviso"] = "Lienzo vacío: pásame el diseño y lo acomodo encima."
    return r


def _fuente(px: int, negrita: bool = True):
    from PIL import ImageFont
    for nom in (("impact.ttf", "arialbd.ttf", "seguibl.ttf", "arial.ttf")
                if negrita else ("arial.ttf", "segoeui.ttf")):
        try:
            return ImageFont.truetype(nom, max(6, px))
        except Exception:
            continue
    return ImageFont.load_default()


def componer(prenda: str = "playera", talla: str = "M", panel: str = "frente",
             fondo=None, capas=None, medida_cm=None, manga_cm=None,
             sangrado_cm: float = SANGRADO_CM, alto_previa: int = 0,
             lienzo: str = "panel"):
    """Arma el panel con su fondo y sus capas encima. Devuelve (imagen, datos).

    Anuar la pidió abierta el 2026-08-16: *"compatible para pegar imágenes,
    colores… créala como tú creas conveniente y simple de uso, así como
    completa"*. Esto es el motor; la ventana solo lo llama.

    `fondo` — {"color": "#RRGGBB"} o {"imagen": ruta, "modo": "cubrir"|
               "centrada"|"mosaico"}.
    `capas` — lista, de abajo hacia arriba:
        {"tipo": "imagen", "ruta": …, "x_cm": …, "y_cm": …, "ancho_cm": …}
        {"tipo": "texto", "texto": …, "x_cm": …, "y_cm": …, "alto_cm": …,
         "color": "#RRGGBB"}
      Las posiciones son en CENTÍMETROS desde la esquina de arriba a la
      izquierda del panel CON sangrado — en centímetros y no en píxeles
      porque en el taller se mide con regla, no con Photoshop.

    `alto_previa` — si viene, se trabaja a esa altura en píxeles para ver
      rápido. La vista previa NUNCA se imprime: la buena va a 300 DPI.
    """
    from PIL import Image, ImageDraw

    clave = _cual_prenda(prenda)
    pr = PRENDAS.get(clave)
    if not pr:
        return None, {"status": "PRENDA_RARA",
                      "detalle": f"No conozco «{prenda}». Tengo: "
                                 + ", ".join(PRENDAS)}
    t = (talla or "M").upper().strip()
    p = (panel or "frente").lower().strip()
    med = medidas(clave, t, p, medida_cm, manga_cm)
    if not med:
        return None, {"status": "NO_HAY_ESA_MEDIDA",
                      "detalle": f"No tengo «{prenda}» talla «{talla}» "
                                 f"panel «{panel}»."}

    # PANEL COMPLETO o SOLO EL ÁREA DE ESTAMPADO. En el área no va sangrado:
    # ahí no se corta nada, el diseño va suelto sobre la tela.
    area = area_trabajo(clave, p) if lienzo == "area" else None
    if lienzo == "area" and not area:
        return None, {"status": "SIN_AREA",
                      "detalle": f"En «{pr['nombre']}» panel «{p}» no tengo "
                                 f"área de estampado; usa el panel completo."}
    if area:
        an_cm, al_cm = area[0], area[1]
        sangrado_cm = 0.0
    else:
        an_cm = med[0] + sangrado_cm * 2
        al_cm = med[1] + sangrado_cm * 2
    W, H = _cm_px(an_cm), _cm_px(al_cm)
    if alto_previa and alto_previa < H:
        W = max(20, int(W * alto_previa / H))
        H = alto_previa
    px_cm = W / an_cm

    fondo = fondo or {"color": "#FFFFFF"}
    if fondo.get("imagen"):
        f = Path(fondo["imagen"])
        if not f.exists():
            return None, {"status": "FONDO_NO_EXISTE",
                          "detalle": f"No encontré el fondo: {f}"}
        im = Image.open(f).convert("RGBA")
        modo = fondo.get("modo", "cubrir")
        lona = Image.new("RGB", (W, H), fondo.get("color", "#FFFFFF"))
        if modo == "mosaico":
            paso = max(1, int(px_cm * float(fondo.get("cm", 10))))
            tile = im.resize((paso, max(1, int(paso * im.height / im.width))),
                             Image.LANCZOS)
            for yy in range(0, H, tile.height):
                for xx in range(0, W, tile.width):
                    lona.paste(tile, (xx, yy), tile)
        else:
            # "cubrir" tapa todo el lienzo recortando lo que sobre — el
            # sangrado incluido, que es donde se nota el filo sin estampar.
            esc = (max(W / im.width, H / im.height) if modo == "cubrir"
                   else min(W / im.width, H / im.height))
            im = im.resize((max(1, int(im.width * esc)),
                            max(1, int(im.height * esc))), Image.LANCZOS)
            lona.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)
        dpi_fondo = round(min(im.width / (an_cm / 2.54),
                              im.height / (al_cm / 2.54)))
    else:
        lona = Image.new("RGB", (W, H), fondo.get("color", "#FFFFFF"))
        dpi_fondo = DPI

    flojas = []
    if dpi_fondo < 200 and fondo.get("imagen"):
        flojas.append(f"el fondo da {dpi_fondo} DPI")

    lona = lona.convert("RGBA")
    for c in (capas or []):
        try:
            x = int(float(c.get("x_cm", 0)) * px_cm)
            y = int(float(c.get("y_cm", 0)) * px_cm)
            if c.get("tipo") == "texto":
                txt = str(c.get("texto", ""))
                if not txt:
                    continue
                alto = max(1, int(float(c.get("alto_cm", 5)) * px_cm))
                fnt = _fuente(alto)
                d = ImageDraw.Draw(lona)
                caja = d.textbbox((0, 0), txt, font=fnt)
                if c.get("centrado"):
                    x -= (caja[2] - caja[0]) // 2
                d.text((x, y), txt, font=fnt,
                       fill=c.get("color", "#000000"))
            else:
                f = Path(c.get("ruta", ""))
                if not f.exists():
                    flojas.append(f"no encontré {f.name}")
                    continue
                im = Image.open(f).convert("RGBA")
                ancho = max(1, int(float(c.get("ancho_cm", 10)) * px_cm))
                im = im.resize((ancho, max(1, int(ancho * im.height / im.width))),
                               Image.LANCZOS)
                dpi_c = round(im.width / (float(c.get("ancho_cm", 10)) / 2.54))
                if dpi_c < 200 and not alto_previa:
                    flojas.append(f"{f.name} da {dpi_c} DPI")
                if c.get("centrado"):
                    x -= im.width // 2
                lona.alpha_composite(im, (x, y))
        except Exception as e:
            flojas.append(f"una capa falló: {e}")

    datos = {"status": "OK", "prenda": pr["nombre"], "clave": clave,
             "talla": ("a la medida" if medida_cm else t), "panel": p,
             "lienzo": ("área de estampado" if area else "panel completo"),
             "prenda_cm": f"{med[0]:g} × {med[1]:g}",
             "con_sangrado_cm": f"{an_cm:g} × {al_cm:g}",
             "px": f"{W} × {H}", "dpi": round(px_cm * 2.54),
             "previa": bool(alto_previa), "flojas": flojas}
    if area:
        datos["desde_el_cuello_cm"] = area[2]
    return lona.convert("RGB"), datos


def guardar_compuesto(prenda="playera", talla="M", panel="frente", fondo=None,
                      capas=None, medida_cm=None, manga_cm=None,
                      sangrado_cm: float = SANGRADO_CM, pdf: bool = True,
                      lienzo: str = "panel") -> dict:
    """Compone y guarda a 300 DPI. Con PDF, para que la impresora no reescale."""
    img, datos = componer(prenda, talla, panel, fondo, capas, medida_cm,
                          manga_cm, sangrado_cm, lienzo=lienzo)
    if img is None:
        return datos
    an, al = datos["con_sangrado_cm"].split(" × ")
    etiqueta = (f"{datos['clave'].upper()}_{panel}_"
                f"{'CINTA' if medida_cm else talla}_{an}x{al}cm"
                f"{'_AREA' if lienzo == 'area' else ''}_300dpi")
    destino = _carpeta("png") / f"{etiqueta}.png"
    k = 2
    while destino.exists():
        destino = destino.parent / f"{etiqueta}__{k}.png"
        k += 1
    img.save(destino, dpi=(DPI, DPI))
    datos["archivo"] = str(destino)
    if pdf:
        # El PDF lleva el tamaño escrito adentro: es lo que evita que el
        # driver de la impresora lo "ajuste a la página" y salga chico.
        try:
            pdf_p = destino.with_suffix(".pdf")
            img.save(pdf_p, "PDF", resolution=float(DPI))
            datos["pdf"] = str(pdf_p)
        except Exception:
            pass
    datos["kb"] = round(destino.stat().st_size / 1024, 1)
    return datos


def para_ploter(diseno: str, ancho_cm: float, colores: int = 3,
                minimo_mm2: float = 4.0, salida: str = "") -> dict:
    """El diseño separado por color y vectorizado, para cortar en vinil.

    Anuar lo pidió el 2026-08-16: *"no necesariamente para sublimar… si es
    compatible con el plóter y la impresora, queda una herramienta
    completa"*. Y es otro oficio: en sublimación se imprime todo junto, en
    vinil textil **cada color es un vinil distinto que se corta aparte y se
    plancha encimado**. Por eso aquí no sale una imagen: salen los contornos.

    Sale un DXF con **una capa por color**, con el nombre del color en la
    capa, para que en el plóter se corte de uno en uno sabiendo cuál va.

    Los pedacitos más chicos que `minimo_mm2` se tiran: en vinil no se pueden
    despicar y solo estorban.
    """
    try:
        import cv2
        import ezdxf
        import numpy as np
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    d = Path(diseno)
    if not d.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {diseno}"}
    img = cv2.imread(str(d), cv2.IMREAD_COLOR)
    if img is None:
        return {"status": "NO_ES_IMAGEN", "detalle": f"No pude leer: {diseno}"}

    n = max(1, min(12, int(colores)))
    px_mm = img.shape[1] / (float(ancho_cm) * 10)
    # k-means sobre el color: deja manchas planas, que es justo lo que se
    # puede cortar. Un degradado no se corta en vinil, se imprime.
    datos = img.reshape(-1, 3).astype("float32")
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _c, etiquetas, centros = cv2.kmeans(datos, n, None, crit, 3,
                                        cv2.KMEANS_PP_CENTERS)
    etiquetas = etiquetas.reshape(img.shape[:2])
    centros = centros.astype("uint8")

    dxf = ezdxf.new("R2010")
    msp = dxf.modelspace()
    alto_mm = img.shape[0] / px_mm
    mm = 1.0 / px_mm
    capas, total_mm = [], 0.0
    for i in range(n):
        b, g, r_ = (int(v) for v in centros[i])
        nombre = f"VINIL_{i + 1}_RGB_{r_}_{g}_{b}"
        try:
            dxf.layers.add(nombre)
        except Exception:
            pass
        masc = (etiquetas == i).astype("uint8") * 255
        masc = cv2.morphologyEx(masc, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        cont, _j = cv2.findContours(masc, cv2.RETR_CCOMP,
                                    cv2.CHAIN_APPROX_SIMPLE)
        minimo_px = minimo_mm2 * px_mm * px_mm
        puestos, largo = 0, 0.0
        for c in cont:
            if cv2.contourArea(c) < minimo_px:
                continue
            suave = cv2.approxPolyDP(c, max(1.0, 0.15 * px_mm), True)
            pts = [(float(q[0][0]) * mm, alto_mm - float(q[0][1]) * mm)
                   for q in suave]
            if len(pts) < 3:
                continue
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": nombre})
            puestos += 1
            cerrado = pts + [pts[0]]
            largo += sum(((y[0] - x[0]) ** 2 + (y[1] - x[1]) ** 2) ** 0.5
                         for x, y in zip(cerrado, cerrado[1:]))
        total_mm += largo
        capas.append({"capa": nombre, "rgb": (r_, g, b), "piezas": puestos,
                      "metros": round(largo / 1000, 2)})

    destino = Path(salida) if salida else (
        _carpeta("dxf") / f"{d.stem}_VINIL_{n}colores_{ancho_cm:g}cm.dxf")
    k = 2
    while destino.exists() and not salida:
        destino = destino.parent / f"{d.stem}_VINIL_{n}colores_{ancho_cm:g}cm__{k}.dxf"
        k += 1
    dxf.saveas(str(destino))

    return {"status": "OK", "archivo": str(destino), "colores": n,
            "mide_cm": f"{ancho_cm:g} × {alto_mm / 10:.1f}",
            "capas": capas, "metros_totales": round(total_mm / 1000, 2),
            "kb": round(destino.stat().st_size / 1024, 1)}


def _texto_ploter(r: dict) -> str:
    if r.get("status") != "OK":
        return f"No pude prepararlo: {r.get('detalle', r.get('status'))}"
    t = (f"✂️ **Para plóter — {r['colores']} colores de vinil**\n"
         f"   {r['mide_cm']} cm · {r['metros_totales']} m de corte en total\n"
         f"   **una capa por color**, se corta de uno en uno y se planchan "
         f"encimados:")
    for c in r["capas"]:
        t += (f"\n   • `{c['capa']}` — RGB {c['rgb'][0]},{c['rgb'][1]},"
              f"{c['rgb'][2]} · {c['piezas']} piezas · {c['metros']} m")
    return t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)"


def generar_juego(prenda: str = "playera", talla: str = "M", diseno: str = "",
                  reparto: str = "misma", sangrado_cm: float = SANGRADO_CM,
                  paneles=None, medida_cm=None, manga_cm=None) -> dict:
    """Todos los paneles de la prenda de un jalón, desde una sola imagen.

    Anuar lo pidió el 2026-08-16: *"que desde una imagen pueda crear el diseño
    frontal y trasero"*. Dos formas de repartirla, y la diferencia importa:

    - `reparto="misma"`   → la imagen completa en cada panel. Es lo normal.
    - `reparto="partida"` → la mitad izquierda al frente y la derecha a la
      espalda. Para los diseños que le dan la vuelta a la prenda y tienen que
      empatar en la costura del costado.
    """
    from PIL import Image
    clave = _cual_prenda(prenda)
    pr = PRENDAS.get(clave)
    if not pr:
        return {"status": "PRENDA_RARA",
                "detalle": f"No conozco «{prenda}». Tengo: " + ", ".join(PRENDAS)}
    t = (talla or "M").upper().strip()
    if not medida_cm and t not in pr["paneles"]:
        return {"status": "TALLA_RARA",
                "detalle": f"En {pr['nombre']} las tallas son: "
                           + ", ".join(pr["paneles"])}

    if paneles:
        quiero = list(paneles)
    elif medida_cm:
        quiero = ["frente", "espalda", "manga"]
    else:
        quiero = [p for p in ("frente", "espalda", "manga")
                  if p in pr["paneles"][t]]

    temporales, usar = [], {p: diseno for p in quiero}
    if diseno and reparto == "partida":
        d = Path(diseno)
        if not d.exists():
            return {"status": "DISENO_NO_EXISTE", "detalle": f"No encontré: {diseno}"}
        img = Image.open(d).convert("RGBA")
        mitad = img.width // 2
        for p, caja in (("frente", (0, 0, mitad, img.height)),
                        ("espalda", (mitad, 0, img.width, img.height))):
            if p not in quiero:
                continue
            tmp = _carpeta("png") / f"_parte_{p}_{d.stem}.png"
            img.crop(caja).save(tmp)
            temporales.append(tmp)
            usar[p] = str(tmp)

    hechos, fallos = [], []
    for p in quiero:
        r = generar(clave, t, p, usar.get(p, ""), sangrado_cm,
                    medida_cm=medida_cm, manga_cm=manga_cm)
        (hechos if r.get("status") == "OK" else fallos).append(r)
    for tmp in temporales:
        try:
            tmp.unlink()
        except Exception:
            pass

    if not hechos:
        return {"status": "NADA", "detalle": "No salió ningún panel.",
                "fallos": fallos}
    return {"status": "OK", "prenda": pr["nombre"], "clave": clave,
            "talla": ("a la medida" if medida_cm else t),
            "reparto": reparto, "paneles": hechos, "fallos": fallos,
            "archivos": [h["archivo"] for h in hechos]}


def _texto_juego(r: dict) -> str:
    if r.get("status") != "OK":
        return f"No pude armarlo: {r.get('detalle', r.get('status'))}"
    t = (f"👕 **{r['prenda']} talla {r['talla']}** — {len(r['paneles'])} "
         f"paneles a 300 DPI"
         + (" · imagen partida frente/espalda" if r["reparto"] == "partida" else ""))
    for h in r["paneles"]:
        t += (f"\n   • **{h['panel']}** {h['con_sangrado_cm']} cm · "
              f"{h['px']} px")
        if h.get("diseno") and h["dpi_real_diseno"] < 200:
            t += f"  ⚠️ el diseño da {h['dpi_real_diseno']} DPI"
    t += "\n\n" + "\n".join(f"📁 `{a}`" for a in r["archivos"])
    for f in r.get("fallos", []):
        t += f"\n⚠️ {f.get('detalle', f.get('status'))}"
    return t


def _texto(r: dict) -> str:
    if "paneles" in r or r.get("status") == "NADA":
        return _texto_juego(r)
    if r.get("status") != "OK":
        return f"No pude armarla: {r.get('detalle', r.get('status'))}"
    t = (f"👕 **{r['prenda']} — {r['panel']} talla {r['talla']}**\n"
         f"   prenda {r['prenda_cm']} cm · con sangrado "
         f"{r['con_sangrado_cm']} cm ({r['sangrado_cm']:g} cm por lado)\n"
         f"   {r['px']} px a {r['dpi']} DPI")
    if r.get("diseno"):
        t += f"\n   diseño colocado a {r['dpi_real_diseno']} DPI reales"
    if r.get("guias"):
        t += f"\n   guías aparte: `{r['guias']}` — no las imprimas en la buena"
    if r.get("aviso"):
        t += f"\n\n⚠️ {r['aviso']}"
    return t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)"


def main() -> int:
    _consola_utf8()
    crudos = sys.argv[1:]
    if "--lista" in crudos or not crudos:
        print(catalogo())
        return 0

    def _op(nombre, por_defecto):
        if f"--{nombre}" in crudos:
            i = crudos.index(f"--{nombre}")
            if i + 1 < len(crudos):
                return type(por_defecto)(crudos[i + 1])
        return por_defecto

    print(_texto(generar(prenda=_op("prenda", "playera"),
                         talla=_op("talla", "M"),
                         panel=_op("panel", "frente"),
                         diseno=_op("diseno", ""),
                         sangrado_cm=_op("sangrado_cm", SANGRADO_CM))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
