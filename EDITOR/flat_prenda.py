# -*- coding: utf-8 -*-
"""AURORA · EL DIBUJO TÉCNICO DE LA PRENDA (flat)

Anuar rechazó la primera versión el 2026-08-16, y con razón: *"parece que mi
hija Romina fue la que dibujó esas áreas… son muy pero muy básicas"*. Lo eran:
polígonos de líneas rectas. Preguntó si bajaba siluetas de Pinterest.

**Se generan aquí, y no se bajan, por dos razones que sí importan:**

1. Una imagen bajada tiene dueño. Esta no.
2. Y la de peso: una imagen **no se estira a tu medida**. Cuando escribes
   56 × 72 cm con la cinta, o mueves el largo de manga, este dibujo se
   **vuelve a trazar** con esa proporción. Una foto solo se deforma.

Es un **flat técnico**: el dibujo plano que se usa en la industria textil para
especificar una prenda. Por definición no lleva sombras ni volumen — lleva
contorno limpio, costuras finas y pespuntes punteados. Se construye con:

  · **Curvas de Bézier**, no líneas rectas. Un hombro es una curva.
  · **Simetría por espejo**: se traza la mitad derecha y se refleja. Una
    prenda simétrica de verdad se nota al instante.
  · **Supersampling ×4**: se dibuja al cuádruple y se reduce. Eso da la orilla
    suave; dibujar al tamaño final deja el borde con escalones.
  · **Manga configurable**: el largo de manga es una perilla, no un dibujo
    distinto. La manga sale del hombro en un ángulo y crece hacia afuera.

Todas las medidas van en proporción a la prenda real, así que una talla 3XL se
dibuja ancha y un pañalero 0-3M se dibuja chiquito.
"""
from __future__ import annotations
import math

SUPER = 4                      # cuánto se agranda antes de reducir
CONTORNO = "#5b6472"
COSTURA = "#98a1ad"
MARCA = "#2d6cdf"              # el azul del área de trabajo


# ─────────────────────────────── geometría ───────────────────────────────
def _bezier(p0, p1, p2, p3, n=26):
    """Los puntos de una curva cúbica. Es lo que vuelve redondo un hombro."""
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0]
                    + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1]
                    + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def _trazo(nodos):
    """Convierte la receta en puntos. ('L', p) recta · ('C', c1, c2, p) curva."""
    pts = [nodos[0][1]]
    for n in nodos[1:]:
        if n[0] == "L":
            pts.append(n[1])
        else:
            pts += _bezier(pts[-1], n[1], n[2], n[3])
    return pts


def _espejo(pts):
    """La otra mitad. La simetría exacta es la mitad de la calidad del dibujo."""
    return [(-x, y) for x, y in reversed(pts)]


def _manga(hombro, largo, ancho_puno, grados, axila):
    """La manga como perilla: sale del hombro en un ángulo y crece.

    `largo` va en la misma unidad que el resto (1.0 = medio ancho de cuerpo),
    así que una manga corta y una larga son el MISMO dibujo con otro número —
    que es justo lo que Anuar pidió poder configurar.
    """
    a = math.radians(grados)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx                      # perpendicular, hacia el puño
    sup = (hombro[0] + dx * largo, hombro[1] + dy * largo)
    inf = (sup[0] + px * ancho_puno, sup[1] + py * ancho_puno)
    return [("C", (hombro[0] + dx * largo * .45, hombro[1] + dy * largo * .38),
             (sup[0] - dx * .05, sup[1] - dy * .10), sup),
            ("C", (sup[0] + px * ancho_puno * .5 + dx * .03,
                   sup[1] + py * ancho_puno * .5),
             (inf[0] + dx * .02, inf[1] - dy * .02), inf),
            ("C", ((inf[0] + axila[0]) / 2 + .02,
                   (inf[1] + axila[1]) / 2 + .03),
             (axila[0] + .06, axila[1] + .04), axila)]


# ───────────────────────────── las prendas ───────────────────────────────
def _torso(escote_h, escote_w, hombro, caida, axila, cintura, largo,
           manga_largo, manga_puno, manga_ang=34.0, dobladillo=0.0):
    """La mitad derecha de un torso, de escote a centro del dobladillo.

    Todos los cuerpos salen de aquí: playera, sudadera, jersey y polo son la
    misma construcción con otros números. Cambiar la forma en un solo lugar
    es lo que evita que una prenda quede bien y las otras chuecas.
    """
    hom = (hombro, caida)
    n = [("M", (0.0, escote_h)),
         ("C", (escote_w * .55, escote_h), (escote_w * .80, caida * .55),
          (escote_w, caida * .30)),
         ("C", (escote_w + (hombro - escote_w) * .45, caida * .05),
          (hombro - .06, caida * .55), hom)]
    n += _manga(hom, manga_largo, manga_puno, manga_ang, (axila, cintura[1]))
    n += [("C", (axila - .015, cintura[1] + (largo - cintura[1]) * .35),
           (cintura[0], cintura[1] + (largo - cintura[1]) * .55),
           (cintura[0], largo - dobladillo * .4)),
          ("C", (cintura[0] * .92, largo), (cintura[0] * .55, largo),
           (0.0, largo))]
    return n


def _receta(clave, manga_largo=None):
    """La receta de cada prenda. `manga_largo` la sobreescribe si viene."""
    m = manga_largo
    if clave in ("playera", "playera_nino", "camiseta"):
        return {"cuerpo": _torso(.105, .30, .50, .075, .48, (.50, .30), 1.0,
                                 m if m is not None else .40, .17),
                "escote": .105, "ancho": 1.05, "cuello_doble": True}
    if clave == "jersey":
        # El jersey abre al frente: escote más chico y una tapeta al centro.
        return {"cuerpo": _torso(.09, .26, .50, .075, .48, (.50, .30), 1.0,
                                 m if m is not None else .38, .17),
                "escote": .09, "ancho": 1.05, "tapeta": True,
                "cuello_doble": True}
    if clave == "polo":
        return {"cuerpo": _torso(.085, .24, .50, .075, .48, (.49, .30), 1.0,
                                 m if m is not None else .36, .155),
                "escote": .085, "ancho": 1.05, "polo": True}
    if clave == "playera_ml":
        return {"cuerpo": _torso(.105, .30, .50, .075, .48, (.50, .30), 1.0,
                                 m if m is not None else .92, .105),
                "escote": .105, "ancho": 1.05, "cuello_doble": True}
    if clave in ("sudadera", "sudadera_nino"):
        return {"cuerpo": _torso(.10, .28, .53, .085, .51, (.54, .32), 1.0,
                                 m if m is not None else .95, .115, 32.0, .09),
                "escote": .10, "ancho": 1.12, "cuello_doble": True,
                "pretina": .085, "punos": True}
    if clave == "sudadera_capucha":
        return {"cuerpo": _torso(.145, .27, .53, .13, .51, (.54, .36), 1.0,
                                 m if m is not None else .95, .115, 32.0, .09),
                "escote": .145, "ancho": 1.12, "capucha": True,
                "pretina": .085, "punos": True, "bolsa": True}
    if clave == "panalero":
        n = [("M", (0.0, .115)),
             ("C", (.17, .115), (.25, .05), (.30, .035)),
             ("C", (.38, .01), (.44, .03), (.47, .075))]
        n += _manga((.47, .075), .30, .155, 36.0, (.45, .32))
        n += [("C", (.455, .48), (.45, .60), (.44, .66)),
              ("C", (.42, .80), (.33, .84), (.26, .87)),
              ("C", (.20, .90), (.14, .93), (.11, .985)),
              ("L", (0.0, .995))]
        return {"cuerpo": n, "escote": .115, "ancho": 1.0,
                "cuello_doble": True, "broches": True}
    if clave == "gorra":
        # De perfil, mirando a la derecha. **No se espeja**: una gorra vista
        # de lado no es simétrica — la nuca cae recta y el frente sale con la
        # visera. Espejarla la convertía en un platillo volador.
        #
        # Y va con `cuadrada`: alto y ancho a la misma escala. Sin eso se
        # aplastaba, porque sus medidas de catálogo (14 × 7 cm) son las del
        # ÁREA de estampado, no las de la gorra.
        n = [("M", (-.70, .93)),
             ("C", (-.75, .55), (-.55, .12), (-.05, .07)),
             ("C", (.42, .10), (.68, .50), (.70, .93)),
             ("L", (-.70, .93))]
        return {"cuerpo": n, "escote": 0, "ancho": 1.12, "gorra": True,
                "sin_espejo": True, "cuadrada": True, "alto_u": 1.28}
    if clave == "mandil":
        # Anuar: *"el mandil está desproporcionado"*. Lo estaba. Un mandil es
        # angosto de pechera y ancho de falda — casi el doble abajo que arriba.
        n = [("M", (0.0, .015)),
             ("L", (.245, .015)),
             ("C", (.255, .10), (.27, .17), (.30, .225)),
             ("C", (.40, .27), (.455, .33), (.465, .40)),
             ("C", (.475, .60), (.475, .82), (.465, .985)),
             ("L", (0.0, .995))]
        return {"cuerpo": n, "escote": 0, "ancho": 1.0, "mandil": True}
    return None


# ────────────────────────────── vista lateral ────────────────────────────
def _receta_lado(clave, manga_largo=None):
    """La misma prenda vista de lado. Anuar la pidió el 2026-08-16 para todas.

    Sirve para lo que la vista de frente no puede: ver el estampado de la
    **manga** y del **costado**, que es donde va el logo chico y donde más se
    equivoca uno de altura.

    De lado la prenda no es simétrica, así que se traza completa (no hay
    espejo) y el ancho es el del **costado**, no el del pecho: una playera se
    ve angosta de lado. Se dibuja en escala cuadrada, porque el ancho de lado
    no tiene nada que ver con el ancho de frente.
    """
    m = manga_largo
    largos = {"playera": .40, "playera_nino": .40, "jersey": .38,
              "polo": .36, "playera_ml": .92, "sudadera": .95,
              "sudadera_nino": .95, "sudadera_capucha": .95}
    if clave in largos:
        lm = m if m is not None else largos[clave]
        gorda = clave.startswith("sudadera")
        an = .30 if gorda else .25          # el grosor del torso, de lado
        # De lado la manga **cuelga**, no se extiende: se ve el tubo cayendo
        # por el frente. Por eso aquí no se usa `_manga()` — esa es la de
        # frente, con la prenda acostada en la mesa. El largo solo dice hasta
        # dónde baja.
        pu = .10 + lm * .72
        gr = .13 if gorda else .155         # el grosor del tubo de la manga
        n = [("M", (-an, .075)),
             ("C", (-an * .55, .015), (an * .40, .012), (an, .075)),
             ("C", (an + .16, .10), (an + .20, .15), (an + .185, .23)),
             ("C", (an + .19, pu * .62), (an + .175, pu * .88), (an + .165, pu)),
             ("C", (an + .12, pu + .045), (an + .05, pu + .05), (an + .015, pu)),
             ("C", (an + .02, pu * .72), (an + .03, .45), (an * .97, .34)),
             ("C", (an * .99, .58), (an, .80), (an, .965)),
             ("C", (an * .5, 1.005), (-an * .5, 1.005), (-an, .965)),
             ("C", (-an * 1.03, .70), (-an * 1.03, .35), (-an, .075))]
        _ = gr
        return {"cuerpo": n, "escote": .075, "ancho": an + .24,
                "sin_espejo": True, "cuadrada": True,
                "alto_u": 1.06, "lado": True,
                "pretina": .085 if gorda else 0,
                "capucha_lado": clave == "sudadera_capucha"}
    if clave == "panalero":
        n = [("M", (-.24, .10)),
             ("C", (-.13, .03), (.10, .02), (.235, .075))]
        n += _manga((.235, .075), .28, .15, 64.0, (.22, .33))
        n += [("C", (.235, .50), (.22, .64), (.20, .72)),
              ("C", (.17, .85), (.08, .93), (-.02, .965)),
              ("C", (-.14, .98), (-.24, .90), (-.245, .74)),
              ("C", (-.25, .45), (-.25, .25), (-.24, .10))]
        return {"cuerpo": n, "escote": .10, "ancho": .52, "sin_espejo": True,
                "cuadrada": True, "alto_u": 1.02, "lado": True}
    if clave == "mandil":
        n = [("M", (-.10, .015)), ("L", (.09, .015)),
             ("C", (.11, .22), (.13, .55), (.125, .985)),
             ("L", (-.085, .995)),
             ("C", (-.10, .55), (-.11, .22), (-.10, .015))]
        return {"cuerpo": n, "escote": 0, "ancho": .32, "sin_espejo": True,
                "cuadrada": True, "alto_u": 1.02, "lado": True,
                "mandil_lado": True}
    if clave == "gorra":
        return _receta(clave)          # la gorra YA se dibuja de perfil
    return None


# ────────────────────────────── el dibujo ────────────────────────────────
def dibujar(clave, ancho_cm, largo_cm, ancho_px=520, color="#FFFFFF",
            area=None, manga_largo=None, marcar=True, vista="frente"):
    """La prenda dibujada. Devuelve (imagen RGBA, caja del área en píxeles).

    `area` = (ancho_cm, alto_cm, desde_el_cuello_cm) — la caja que sale es
    exactamente ese recuadro, colgado del cuello como se mide en la mesa.
    `vista` = "frente" o "lado".
    """
    from PIL import Image, ImageDraw

    r = (_receta_lado(clave, manga_largo) if vista == "lado"
         else _receta(clave, manga_largo))
    if not r:
        return None, None

    der = _trazo(r["cuerpo"])
    contorno = der if r.get("sin_espejo") else _espejo(der) + der

    # La prenda se dibuja a su proporción REAL: el alto sale del largo contra
    # el ancho de la prenda de verdad, no de un número inventado.
    prop = (largo_cm / ancho_cm) if ancho_cm else 1.3
    if r.get("cuadrada"):
        prop = 1.0                    # alto y ancho a la misma escala
    ancho_u = r["ancho"] * 2          # de punta de manga a punta de manga
    S = SUPER
    W = int(ancho_px) * S
    esc = W / ancho_u                 # píxeles por unidad
    H = int((r.get("alto_u", 1.0) * prop + .10) * esc)
    cx, top = W / 2, int(.045 * esc)

    def P(p):
        return (cx + p[0] * esc, top + p[1] * prop * esc)

    img = Image.new("RGBA", (W, H + top * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if r.get("capucha_lado"):
        # De lado la capucha se ve caída sobre la espalda: es lo que más
        # distingue una sudadera con capucha de una lisa.
        cap = _trazo([("M", (-.30, .085)),
                      ("C", (-.52, .06), (-.62, .20), (-.60, .34)),
                      ("C", (-.58, .46), (-.44, .46), (-.34, .40)),
                      ("C", (-.28, .32), (-.28, .18), (-.30, .085))])
        d.polygon([P(p) for p in cap], fill=color, outline=CONTORNO,
                  width=int(2.2 * S))
    if r.get("capucha"):
        # La capucha va detrás: se dibuja primero para que el cuerpo la tape.
        cap = [(0.0, -.10), (.30, -.085), (.40, .03), (.42, .145),
               (.26, .13), (.13, .105), (0.0, .10)]
        d.polygon([P(p) for p in _espejo(cap) + cap], fill=color,
                  outline=CONTORNO, width=int(2.2 * S))

    d.polygon([P(p) for p in contorno], fill=color, outline=CONTORNO,
              width=int(2.4 * S))

    fino = max(1, int(1.3 * S))

    def _linea(pts, ancho=None, color_l=COSTURA):
        d.line([P(p) for p in pts], fill=color_l, width=ancho or fino,
               joint="curve")

    # EL CUELLO. La segunda línea por dentro es el tejido del cuello: es el
    # detalle chico que hace que se lea como prenda y no como recorte.
    if r.get("cuello_doble"):
        e = r["escote"]
        adentro = _trazo([("M", (0.0, e + .035)),
                          ("C", (.20, e + .035), (.28, .085), (.335, .052))])
        _linea(_espejo(adentro) + adentro)
    if r.get("polo"):
        e = r["escote"]
        cuello = [(0.0, e + .085), (.13, e + .045), (.235, .028), (.25, .06),
                  (.15, .10), (.06, .135)]
        d.polygon([P(p) for p in _espejo(cuello) + cuello], fill=color,
                  outline=CONTORNO, width=fino)
        _linea([(-.045, e + .085), (-.045, e + .30)], fino, CONTORNO)
        _linea([(.045, e + .085), (.045, e + .30)], fino, CONTORNO)
        for y in (e + .13, e + .23):
            a, b = P((0.0, y)), None
            rr = .012 * esc
            d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr],
                      outline=CONTORNO, width=fino)
    if r.get("tapeta"):
        _linea([(0.0, r["escote"] + .02), (0.0, .34)], fino, CONTORNO)
        for y in (.10, .18, .26):
            a = P((0.0, y))
            rr = .011 * esc
            d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr],
                      outline=CONTORNO, width=fino)
    if r.get("capucha"):
        # Los cordones: dos líneas y sus ojales. Es lo que dice "hoodie".
        for s in (-1, 1):
            _linea([(s * .075, .145), (s * .085, .40)], fino, CONTORNO)
            a = P((s * .075, .155))
            rr = .010 * esc
            d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr],
                      outline=CONTORNO, width=fino)
    if r.get("bolsa"):
        bolsa = [(0.0, .60), (.34, .60), (.40, .68), (.40, .855), (0.0, .855)]
        d.line([P(p) for p in _espejo(bolsa) + bolsa], fill=COSTURA,
               width=fino, joint="curve")
    if r.get("mandil_lado"):
        _linea([(-.095, .015), (-.16, -.10), (-.26, -.155)], int(2.0 * S),
               CONTORNO)
        _linea([(.115, .43), (.26, .40), (.36, .46)], int(2.0 * S), CONTORNO)
    if r.get("pretina"):
        y = 1.0 - r["pretina"]
        ancho_p = .34 if r.get("lado") else .54
        _linea([(-ancho_p, y), (ancho_p, y)], fino, CONTORNO)
    if r.get("punos") and not r.get("lado"):
        for s in (-1, 1):
            _linea([(s * 1.02, .625), (s * 1.11, .705)], int(1.8 * S), CONTORNO)
    if r.get("broches"):
        for x in (-.16, -.055, .055, .16):
            a = P((x, .945))
            rr = .011 * esc
            d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr],
                      outline=CONTORNO, width=fino)
    if r.get("gorra"):
        # La visera sale del frente y baja curveando, como la de verdad.
        vis = _trazo([("M", (.60, .86)),
                      ("C", (1.00, .88), (1.26, .94), (1.34, 1.05)),
                      ("C", (1.18, 1.15), (.88, 1.16), (.58, 1.09)),
                      ("C", (.48, 1.04), (.48, .92), (.60, .86))])
        d.polygon([P(p) for p in vis], fill=color, outline=CONTORNO,
                  width=int(2.2 * S))
        _linea(_trazo([("M", (.66, .93)),
                       ("C", (.95, .96), (1.15, 1.00), (1.24, 1.06))]), fino)
        # Los gajos y la banda de abajo: sin eso parece un casco liso.
        for a_, b_ in ((-.40, -.55), (-.05, -.12), (.34, .42)):
            _linea(_trazo([("M", (a_ * .35, .085)),
                           ("C", (b_ * .9, .38), (b_, .65), (b_, .90))]), fino)
        _linea([(-.69, .855), (.69, .855)], fino)
        a = P((-.05, .07))
        rr = .030 * esc              # el botón de arriba
        d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr],
                  fill=color, outline=CONTORNO, width=fino)
    if r.get("mandil"):
        # Los tirantes al cuello y los lazos de la cintura.
        for s in (-1, 1):
            _linea([(s * .245, .02), (s * .20, -.10), (s * .085, -.16)],
                   int(2.0 * S), CONTORNO)
            _linea([(s * .465, .43), (s * .60, .40), (s * .70, .45)],
                   int(2.0 * S), CONTORNO)
        bolsa = [(0.0, .55), (.30, .55), (.30, .70), (0.0, .70)]
        d.line([P(p) for p in _espejo(bolsa) + bolsa], fill=COSTURA,
               width=fino, joint="curve")
        _linea([(0.0, .55), (0.0, .70)], fino)
        _linea([(-.245, .225), (.245, .225)], fino)   # unión pechera/falda

    # EL ÁREA DE TRABAJO. Se marca punteada para que se distinga del dibujo:
    # es una guía, no una costura.
    caja = None
    # De lado no se marca el área del pecho: sería mentira, el pecho no se ve.
    # De lado se ve el COSTADO y la MANGA, que es justo para lo que sirve —
    # ubicar el logo chico de manga sin equivocarse de altura.
    if area and r.get("lado"):
        area = None
    if area:
        a_an, a_al, desde = area
        pu = esc / ancho_cm                    # píxeles por centímetro real
        centro = cx
        if r.get("gorra"):
            # El frente de la gorra está a la derecha del dibujo, no al
            # centro: de perfil, el estampado cae sobre el panel delantero,
            # arriba de la banda y sin montarse en la visera.
            pu = esc / 27.0            # una gorra mide ~27 cm de perfil
            arriba = .34 * esc
            centro = cx + .17 * esc
        elif r.get("mandil"):
            arriba = (desde / largo_cm) * prop * esc
        else:
            arriba = (r["escote"] * prop * esc) + desde * pu
        x0, y0 = centro - a_an * pu / 2, top + arriba
        w, h = a_an * pu, a_al * pu
        caja = (int(x0 / S), int(y0 / S), int(w / S), int(h / S))
        if marcar:
            paso, raya = int(.028 * esc), int(.016 * esc)
            gr = max(1, int(1.6 * S))
            for i in range(0, int(w), paso):
                d.line([(x0 + i, y0), (x0 + min(i + raya, w), y0)],
                       fill=MARCA, width=gr)
                d.line([(x0 + i, y0 + h), (x0 + min(i + raya, w), y0 + h)],
                       fill=MARCA, width=gr)
            for j in range(0, int(h), paso):
                d.line([(x0, y0 + j), (x0, y0 + min(j + raya, h))],
                       fill=MARCA, width=gr)
                d.line([(x0 + w, y0 + j), (x0 + w, y0 + min(j + raya, h))],
                       fill=MARCA, width=gr)

    from PIL import Image as _I
    return img.resize((W // S, img.height // S), _I.LANCZOS), caja
