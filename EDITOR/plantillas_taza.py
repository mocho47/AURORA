# -*- coding: utf-8 -*-
"""
AURORA · PLANTILLAS DE TAZA  (catálogo de 50 fondos por tema + composición)

Catálogo de 50 fondos bonitos predeterminados, 5 por tema (10 temas), para taza 11oz.
Tú o Rocío buscan por ocasión ("cumpleaños", "amor", "navidad"...), eligen un fondo y
AURORA arma la plantilla a la MEDIDA REAL de impresión (20x8.5 cm @300 DPI) en 3 modos:
frase+foto, solo foto, o solo frase. Lista para sublimar.

Fondos DE DISEÑO procedurales (sin IA pesada). Pillow, PNG reales a 300 DPI.
"""
from __future__ import annotations
from pathlib import Path
from functools import partial
import os
import math
import random
import unicodedata as _ud
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CM_POR_PULGADA = 2.54


def _cm_a_px(cm, dpi=300):
    """cm -> pixeles. El dpi se blinda contra None a proposito.

    El enrutador universal pasa None explicito cuando no logra sacar el valor
    de la frase, y un None explicito ANULA el default de la firma. Anuar lo
    cacho el 2026-08-10 pidiendo una plantilla de tazas: reventaba con
    "unsupported operand type(s) for *: 'float' and 'NoneType'".
    """
    return round(cm / CM_POR_PULGADA * (dpi or 300))


def _es_imagen(ruta) -> bool:
    """¿Esto es una foto de verdad que existe en el disco?"""
    if not isinstance(ruta, str) or not ruta.strip():
        return False
    p = Path(ruta.strip().strip('"').strip("'"))
    return p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp",
                                ".tif", ".tiff") and p.is_file()


def _encajar(foto: "Image.Image", ancho: int, alto: int, recortar: bool = False,
             relleno=(255, 255, 255)) -> "Image.Image":
    """Mete la foto en la caja sin deformarla nunca.

    recortar=False (lo normal): la foto entra COMPLETA y sobra fondo a los
    lados. recortar=True: llena toda la caja y se pierde orilla.

    EL DEFAULT ES «COMPLETA» POR UNA RAZÓN CARA.
    El área de una taza es 21x9 cm — ratio 2.3:1, larguísima y bajita. Una
    foto de celular es casi cuadrada. Al rellenar esa caja se recorta arriba
    y abajo, y lo primero que desaparece son las CABEZAS. Anuar mandó dos
    fotos de familia el 2026-08-10 y la primera versión de esto le entregó
    tres tazas con las caras cortadas. Una taza así no se entrega: se vuelve
    a hacer, y el material ya se gastó.

    Estirar no es opción en ninguno de los dos casos: una cara aplastada se
    nota más que una orilla de menos.
    """
    fw, fh = foto.size
    if recortar:
        escala = max(ancho / fw, alto / fh)
        nueva = foto.resize((max(1, round(fw * escala)), max(1, round(fh * escala))),
                            Image.LANCZOS)
        izq = (nueva.width - ancho) // 2
        arr = (nueva.height - alto) // 2
        return nueva.crop((izq, arr, izq + ancho, arr + alto))

    escala = min(ancho / fw, alto / fh)
    nueva = foto.resize((max(1, round(fw * escala)), max(1, round(fh * escala))),
                        Image.LANCZOS)
    lienzo = Image.new("RGB", (ancho, alto), relleno)
    lienzo.paste(nueva, ((ancho - nueva.width) // 2, (alto - nueva.height) // 2))
    return lienzo
def _norm(s): return "".join(c for c in _ud.normalize("NFD", (s or "").lower()) if _ud.category(c) != "Mn")


def _asegurar_extension(salida: str, ext: str = ".png") -> str:
    """PIL.Image.save() truena sin extensión reconocible. Si 'salida' no trae, se agrega."""
    p = Path(salida)
    return str(p) if p.suffix else str(p.with_suffix(ext))


def _font(size, bold=True):
    cands = ([r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
              r"C:\Windows\Fonts\calibrib.ttf"] if bold else
             [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"])
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _grad(w, h, c1, c2, horizontal=False):
    n = w if horizontal else h
    px = [tuple(round(c1[k] + (c2[k] - c1[k]) * (i / max(1, n - 1))) for k in range(3)) for i in range(n)]
    band = Image.new("RGB", (w, 1) if horizontal else (1, h)); band.putdata(px)
    return band.resize((w, h))


def _corazon(d, x, y, s, color):
    r = s / 2
    d.ellipse([x, y, x + r, y + r], fill=color); d.ellipse([x + r, y, x + s, y + r], fill=color)
    d.polygon([(x, y + r * 0.5), (x + s, y + r * 0.5), (x + r, y + s)], fill=color)


def _star(d, cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
    d.polygon(pts, fill=color)


# ── PINCELES (renderers parametrizados) ───────────────────────────────
def _tc(c):
    """PIL exige tuplas en fill=; el JSON del chat manda listas. Normaliza."""
    return tuple(c) if isinstance(c, list) else c

def _tcs(cols):
    return [_tc(c) for c in cols] if cols else cols


def r_grad(w, h, c1, c2, horizontal=False):
    return _grad(w, h, _tc(c1), _tc(c2), horizontal)

def r_confeti(w, h, c1, c2, cols, dense=200):
    c1, c2, cols = _tc(c1), _tc(c2), _tcs(cols)
    img = _grad(w, h, c1, c2); d = ImageDraw.Draw(img); rnd = random.Random(7)
    for _ in range(dense):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(max(4, h // 90), max(8, h // 55))
        d.ellipse([x, y, x + r, y + r], fill=rnd.choice(cols))
    return img

def r_corazones(w, h, c1, c2, cols, dense=70):
    c1, c2, cols = _tc(c1), _tc(c2), _tcs(cols)
    img = _grad(w, h, c1, c2); d = ImageDraw.Draw(img); rnd = random.Random(3)
    for _ in range(dense):
        x, y, s = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(max(16, h // 30), max(30, h // 16))
        _corazon(d, x, y, s, rnd.choice(cols))
    return img

def r_estrellas(w, h, c1, c2, dotcol, starcol, dense=200, bigs=14):
    c1, c2, dotcol, starcol = _tc(c1), _tc(c2), _tc(dotcol), _tc(starcol)
    img = _grad(w, h, c1, c2); d = ImageDraw.Draw(img); rnd = random.Random(9)
    for _ in range(dense):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(2, 5)
        d.ellipse([x, y, x + r, y + r], fill=dotcol)
    for _ in range(bigs):
        _star(d, rnd.randint(0, w), rnd.randint(0, h), rnd.randint(h // 40, h // 22), starcol)
    return img

def r_lunares(w, h, base, cols):
    base, cols = _tc(base), _tcs(cols)
    img = Image.new("RGB", (w, h), base); d = ImageDraw.Draw(img)
    step = max(40, round(h * 0.22))
    for gy in range(0, h + step, step):
        for gx in range(0, w + step, step):
            off = (step // 2) if (gy // step) % 2 else 0
            r = round(step * 0.22); cx, cy = gx + off, gy
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=cols[(gx // step) % len(cols)])
    return img

def r_olas(w, h, cols):
    cols = _tcs(cols)
    img = Image.new("RGB", (w, h), cols[0]); d = ImageDraw.Draw(img)
    bh = h / len(cols)
    for i, c in enumerate(cols):
        pts = [(0, h)]
        for x in range(0, w + 20, 20):
            pts.append((x, i * bh + math.sin(x / 120.0 + i) * (bh * 0.35)))
        pts += [(w, h)]; d.polygon(pts, fill=c)
    return img

def r_geom(w, h, base, cols):
    base, cols = _tc(base), _tcs(cols)
    img = Image.new("RGB", (w, h), base); d = ImageDraw.Draw(img); rnd = random.Random(4)
    s = max(60, round(h * 0.5))
    for gx in range(-s, w + s, s):
        for gy in range(0, h + s, s):
            d.polygon([(gx, gy), (gx + s, gy), (gx + s // 2, gy + s)], fill=rnd.choice(cols))
    return img

def r_marmol(w, h, c1, c2, vein):
    c1, c2, vein = _tc(c1), _tc(c2), _tc(vein)
    img = _grad(w, h, c1, c2, horizontal=True); d = ImageDraw.Draw(img); rnd = random.Random(6)
    for _ in range(14):
        x = rnd.randint(0, w); pts = [(x, 0)]
        for y in range(0, h + 30, 30):
            x += rnd.randint(-40, 40); pts.append((x, y))
        d.line(pts, fill=vein, width=rnd.randint(1, 3))
    return img.filter(ImageFilter.GaussianBlur(1.2))

def r_nieve(w, h, c1, c2, starcol=None):
    img = _grad(w, h, c1, c2); d = ImageDraw.Draw(img); rnd = random.Random(5)
    for _ in range(150):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(3, max(6, h // 80))
        d.ellipse([x, y, x + r, y + r], fill=(255, 255, 255))
    if starcol:
        for _ in range(16):
            _star(d, rnd.randint(0, w), rnd.randint(0, h), rnd.randint(h // 40, h // 22), starcol)
    return img

def r_rayas(w, h, cols, vertical=False):
    cols = _tcs(cols)
    img = Image.new("RGB", (w, h), cols[0]); d = ImageDraw.Draw(img)
    n = len(cols);
    if vertical:
        bw = w / n
        for i, c in enumerate(cols):
            d.rectangle([i * bw, 0, (i + 1) * bw, h], fill=c)
    else:
        bh = h / n
        for i, c in enumerate(cols):
            d.rectangle([0, i * bh, w, (i + 1) * bh], fill=c)
    return img

def r_floral(w, h, c1, c2, cols):
    c1, c2, cols = _tc(c1), _tc(c2), _tcs(cols)
    img = _grad(w, h, c1, c2, horizontal=True); d = ImageDraw.Draw(img); rnd = random.Random(11)
    for _ in range(45):
        cx, cy, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(max(12, h // 34), max(22, h // 18))
        col = rnd.choice(cols)
        for a in range(6):
            ang = a * math.pi / 3; px, py = cx + r * math.cos(ang), cy + r * math.sin(ang)
            d.ellipse([px - r * 0.6, py - r * 0.6, px + r * 0.6, py + r * 0.6], fill=col)
        d.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=(255, 236, 150))
    return img

def r_nubes(w, h, c1, c2):
    img = _grad(w, h, c1, c2).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); rnd = random.Random(1)
    for _ in range(14):
        cx, cy = rnd.randint(0, w), rnd.randint(int(h * 0.15), int(h * 0.9))
        rw, rh = rnd.randint(w // 8, w // 4), rnd.randint(h // 8, h // 5)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(255, 255, 255, 120))
    layer = layer.filter(ImageFilter.GaussianBlur(max(6, h // 26)))
    return Image.alpha_composite(img, layer).convert("RGB")

def r_glow(w, h, base, glow):
    base, glow = _tc(base), _tc(glow)
    img = Image.new("RGBA", (w, h), base + (255,))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx, cy = w // 2, h // 2; rw, rh = int(w * 0.32), int(h * 0.62)
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=glow + (170,))
    layer = layer.filter(ImageFilter.GaussianBlur(max(10, h // 7)))
    return Image.alpha_composite(img, layer).convert("RGB")


# ── FONDOS = temas x 5 ────────────────────────────────────────────────
_TEMAS = [
    ("Amor y San Valentín", ["amor", "san valentin", "novios", "aniversario", "pareja", "corazon"], [
        ("amor_1", "Corazones rojos", partial(r_corazones, c1=(255, 228, 235), c2=(255, 200, 214), cols=[(216, 27, 96), (255, 255, 255)])),
        ("amor_2", "Corazones vino", partial(r_corazones, c1=(120, 20, 40), c2=(80, 12, 28), cols=[(255, 90, 120), (255, 255, 255)])),
        ("amor_3", "Atardecer romántico", partial(r_grad, c1=(255, 128, 148), c2=(255, 196, 140))),
        ("amor_4", "Floral rosa", partial(r_floral, c1=(255, 235, 242), c2=(255, 214, 226), cols=[(255, 105, 150), (255, 160, 190)])),
        ("amor_5", "Rojo pasión", partial(r_grad, c1=(200, 30, 60), c2=(120, 10, 30))),
    ]),
    ("Cumpleaños", ["cumpleaños", "fiesta", "celebracion", "party", "festejo"], [
        ("cumple_1", "Confeti clásico", partial(r_confeti, c1=(255, 255, 255), c2=(240, 244, 248), cols=[(216, 27, 96), (0, 134, 241), (34, 197, 94), (255, 189, 89), (124, 58, 237)])),
        ("cumple_2", "Confeti azul", partial(r_confeti, c1=(0, 134, 241), c2=(120, 200, 255), cols=[(255, 255, 255), (255, 189, 89), (216, 27, 96)])),
        ("cumple_3", "Lunares fiesta", partial(r_lunares, base=(255, 246, 225), cols=[(255, 189, 89), (0, 134, 241), (216, 27, 96)])),
        ("cumple_4", "Estrellas fiesta", partial(r_estrellas, c1=(124, 58, 237), c2=(196, 181, 253), dotcol=(255, 255, 255), starcol=(255, 215, 120))),
        ("cumple_5", "Lila fiesta", partial(r_grad, c1=(124, 58, 237), c2=(236, 180, 255))),
    ]),
    ("Graduación", ["graduacion", "graduado", "titulacion", "egresado", "universidad", "generacion", "logro", "escuela"], [
        ("grad_1", "Confeti dorado", partial(r_confeti, c1=(22, 32, 60), c2=(35, 48, 85), cols=[(212, 175, 55), (255, 215, 120), (255, 255, 255)])),
        ("grad_2", "Estrellas doradas", partial(r_estrellas, c1=(18, 26, 52), c2=(30, 42, 78), dotcol=(255, 255, 255), starcol=(212, 175, 55))),
        ("grad_3", "Azul rey", partial(r_grad, c1=(20, 34, 80), c2=(45, 70, 140))),
        ("grad_4", "Geométrico oro", partial(r_geom, base=(20, 28, 52), cols=[(212, 175, 55), (40, 55, 95), (30, 42, 72)])),
        ("grad_5", "Mármol azul-oro", partial(r_marmol, c1=(28, 40, 75), c2=(18, 26, 50), vein=(212, 175, 55))),
    ]),
    ("En memoria (aniversario luctuoso)", ["luctuoso", "memoria", "recuerdo", "cielo", "luto", "descanso", "en memoria", "siempre", "rip", "aniversario luctuoso"], [
        ("memoria_1", "Cielo y nubes", partial(r_nubes, c1=(150, 190, 235), c2=(225, 238, 250))),
        ("memoria_2", "Una estrella en el cielo", partial(r_estrellas, c1=(16, 24, 54), c2=(34, 46, 86), dotcol=(255, 255, 255), starcol=(230, 225, 200))),
        ("memoria_3", "Luz de vela", partial(r_glow, base=(28, 24, 20), glow=(255, 190, 110))),
        ("memoria_4", "Gris sereno", partial(r_grad, c1=(96, 102, 114), c2=(58, 63, 74))),
        ("memoria_5", "Blanco de paz", partial(r_nubes, c1=(238, 240, 245), c2=(255, 255, 255))),
    ]),
    ("Día de las Madres", ["dia de las madres", "mama", "mujer", "madre", "10 de mayo"], [
        ("mama_1", "Floral pastel", partial(r_floral, c1=(255, 241, 246), c2=(255, 224, 236), cols=[(255, 138, 174), (255, 189, 89), (200, 150, 255)])),
        ("mama_2", "Floral durazno", partial(r_floral, c1=(255, 240, 230), c2=(255, 220, 200), cols=[(255, 160, 120), (255, 200, 150)])),
        ("mama_3", "Menta suave", partial(r_grad, c1=(120, 220, 190), c2=(200, 245, 225), horizontal=True)),
        ("mama_4", "Corazones pastel", partial(r_corazones, c1=(255, 240, 245), c2=(250, 225, 240), cols=[(255, 150, 180), (255, 200, 170)])),
        ("mama_5", "Mármol rosa", partial(r_marmol, c1=(255, 240, 245), c2=(250, 220, 232), vein=(210, 150, 175))),
    ]),
    ("Día del Padre", ["dia del padre", "papa", "hombre", "padre", "papá"], [
        ("papa_1", "Geométrico azul", partial(r_geom, base=(26, 36, 49), cols=[(0, 134, 241), (60, 90, 130), (40, 60, 90)])),
        ("papa_2", "Rayas marino", partial(r_rayas, cols=[(20, 40, 70), (30, 55, 95), (20, 40, 70), (30, 55, 95)])),
        ("papa_3", "Azul acero", partial(r_grad, c1=(40, 55, 75), c2=(90, 115, 145))),
        ("papa_4", "Geométrico bosque", partial(r_geom, base=(20, 40, 30), cols=[(34, 120, 80), (20, 70, 50), (60, 140, 90)])),
        ("papa_5", "Mármol gris", partial(r_marmol, c1=(70, 78, 90), c2=(45, 52, 64), vein=(150, 160, 175))),
    ]),
    ("Navidad", ["navidad", "diciembre", "posada", "fin de año", "santa", "noel"], [
        ("navidad_1", "Nieve roja", partial(r_nieve, c1=(150, 25, 35), c2=(95, 12, 20), starcol=(255, 215, 120))),
        ("navidad_2", "Nieve verde", partial(r_nieve, c1=(20, 90, 50), c2=(12, 55, 32), starcol=(255, 215, 120))),
        ("navidad_3", "Rojo festivo", partial(r_grad, c1=(190, 30, 40), c2=(120, 15, 25))),
        ("navidad_4", "Copos noche", partial(r_nieve, c1=(18, 30, 70), c2=(40, 55, 110))),
        ("navidad_5", "Dorado verde", partial(r_estrellas, c1=(16, 70, 45), c2=(30, 100, 65), dotcol=(255, 255, 255), starcol=(255, 205, 90))),
    ]),
    ("Bebé y Baby Shower", ["bebe", "baby shower", "nacimiento", "recien nacido", "bautizo"], [
        ("bebe_1", "Estrellas celeste", partial(r_estrellas, c1=(180, 215, 250), c2=(220, 235, 255), dotcol=(255, 255, 255), starcol=(120, 170, 230))),
        ("bebe_2", "Estrellas rosa", partial(r_estrellas, c1=(255, 220, 232), c2=(255, 235, 244), dotcol=(255, 255, 255), starcol=(240, 150, 180))),
        ("bebe_3", "Lunares pastel", partial(r_lunares, base=(240, 248, 255), cols=[(180, 210, 245), (255, 200, 220), (200, 240, 210)])),
        ("bebe_4", "Celeste suave", partial(r_grad, c1=(190, 225, 250), c2=(235, 245, 255))),
        ("bebe_5", "Olas suaves", partial(r_olas, cols=[(200, 230, 250), (225, 240, 250), (240, 248, 255), (255, 255, 255)])),
    ]),
    ("Infantil", ["niño", "niña", "infantil", "kids", "divertido"], [
        ("kids_1", "Confeti brillante", partial(r_confeti, c1=(255, 255, 255), c2=(255, 246, 230), cols=[(255, 80, 80), (0, 170, 255), (255, 200, 0), (60, 200, 90)], dense=240)),
        ("kids_2", "Lunares primarios", partial(r_lunares, base=(255, 255, 255), cols=[(255, 80, 80), (0, 150, 255), (255, 200, 0)])),
        ("kids_3", "Olas arcoíris", partial(r_olas, cols=[(255, 90, 90), (255, 180, 60), (90, 200, 100), (60, 160, 255), (150, 100, 220)])),
        ("kids_4", "Geométrico color", partial(r_geom, base=(255, 255, 255), cols=[(255, 100, 120), (0, 160, 255), (255, 190, 60), (90, 200, 120)])),
        ("kids_5", "Estrellas color", partial(r_estrellas, c1=(60, 160, 255), c2=(150, 210, 255), dotcol=(255, 255, 255), starcol=(255, 210, 70))),
    ]),
    ("Boda y Aniversario", ["boda", "aniversario", "novios", "compromiso", "15 años", "quinceañera"], [
        ("boda_1", "Mármol blanco", partial(r_marmol, c1=(252, 250, 248), c2=(235, 232, 228), vein=(200, 195, 188))),
        ("boda_2", "Floral elegante", partial(r_floral, c1=(250, 248, 245), c2=(240, 236, 230), cols=[(210, 180, 140), (230, 210, 180)])),
        ("boda_3", "Dorado suave", partial(r_grad, c1=(245, 232, 200), c2=(255, 248, 228), horizontal=True)),
        ("boda_4", "Corazones dorados", partial(r_corazones, c1=(250, 246, 238), c2=(240, 232, 216), cols=[(200, 165, 100), (230, 205, 160)])),
        ("boda_5", "Rayas plata", partial(r_rayas, cols=[(235, 236, 240), (215, 218, 226), (235, 236, 240), (215, 218, 226)])),
    ]),
    ("Empresa y Profesional", ["empresa", "profesional", "negocio", "corporativo", "logo", "oficina"], [
        ("empresa_1", "Mármol gris", partial(r_marmol, c1=(245, 246, 250), c2=(225, 228, 236), vein=(150, 160, 180))),
        ("empresa_2", "Azul corporativo", partial(r_geom, base=(20, 35, 60), cols=[(0, 110, 200), (20, 60, 110), (40, 80, 140)])),
        ("empresa_3", "Azul oscuro", partial(r_grad, c1=(18, 30, 55), c2=(40, 60, 95))),
        ("empresa_4", "Rayas grises", partial(r_rayas, cols=[(60, 66, 76), (48, 54, 64), (60, 66, 76), (48, 54, 64)])),
        ("empresa_5", "Minimal claro", partial(r_grad, c1=(238, 240, 244), c2=(255, 255, 255), horizontal=True)),
    ]),
    ("Verano y Playa", ["verano", "playa", "mar", "vacaciones", "tropical"], [
        ("verano_1", "Olas turquesa", partial(r_olas, cols=[(0, 120, 200), (0, 170, 220), (100, 210, 220), (200, 240, 230)])),
        ("verano_2", "Atardecer playa", partial(r_grad, c1=(255, 140, 100), c2=(255, 210, 130))),
        ("verano_3", "Olas verde agua", partial(r_olas, cols=[(0, 150, 136), (77, 200, 180), (160, 230, 210), (220, 248, 240)])),
        ("verano_4", "Lunares tropicales", partial(r_lunares, base=(255, 250, 235), cols=[(255, 120, 80), (0, 180, 160), (255, 200, 60)])),
        ("verano_5", "Cielo y mar", partial(r_grad, c1=(120, 200, 255), c2=(0, 120, 200))),
    ]),
]

# Índice plano
FONDOS = {}
for _tema, _tags, _items in _TEMAS:
    for _fid, _nom, _render in _items:
        FONDOS[_fid] = {"nombre": _nom, "tema": _tema, "render": _render, "tags": _tags}


def buscar_fondos(tema: str = "") -> dict:
    """Búsqueda indexada por ocasión/tema. Vacío = todos."""
    q = _norm(tema).strip()
    res = []
    for fid, meta in FONDOS.items():
        idx = _norm(meta["nombre"] + " " + meta["tema"] + " " + " ".join(meta["tags"]))
        score = 1 if not q else sum(1 for p in q.split() if len(p) > 2 and p in idx)
        if score:
            res.append({"id": fid, "nombre": meta["nombre"], "tema": meta["tema"], "score": score})
    res.sort(key=lambda r: -r["score"])
    return {"status": "ok", "tema": tema, "resultados": res, "total": len(res)}


def temas() -> dict:
    """Lista de temas (para el panel)."""
    return {"status": "ok", "temas": [{"tema": t, "tags": tg, "fondos": [i[0] for i in it]}
                                       for t, tg, it in _TEMAS], "total_fondos": len(FONDOS)}


def _wrap(d, texto, font, max_w):
    lineas, cur = [], ""
    for p in texto.split():
        prueba = (cur + " " + p).strip()
        if not cur or d.textlength(prueba, font=font) <= max_w:
            cur = prueba
        else:
            lineas.append(cur); cur = p
    if cur:
        lineas.append(cur)
    return lineas or [""]


def componer_taza(fondo_id: str, frase: str = "", modo: str = "frase_foto",
                  con_foto=None, ancho_cm: float = 20.0, alto_cm: float = 8.5,
                  dpi: int = 300, salida: str = "", foto: str = "",
                  recortar: bool = False) -> dict:
    """Compone la taza: fondo elegido + (según modo) foto y/o frase.
    modo: 'frase_foto' | 'solo_foto' | 'solo_frase'.
    foto: ruta a una imagen REAL; si no se da, se dibuja el recuadro guía.

    El parámetro `foto` se agregó el 2026-08-10. Hasta entonces este módulo
    NO podía recibir imágenes: dibujaba un recuadro con una X y la palabra
    "FOTO", y nada más. Anuar pidió «una plantilla para 3 tazas con estas 2
    fotos» y se topó con que la herramienta que el enrutador le ofrecía era
    incapaz de hacer justo eso. El recuadro sigue existiendo para cuando no
    hay foto — sirve de guía de armado —, pero ya no es lo único posible.
    """
    # Se normaliza AQUÍ y no solo en _cm_a_px: el dpi también viaja hasta
    # img.save(dpi=(dpi, dpi)), y ahí un None revienta igual pero con otro
    # mensaje. Blindar la conversión y dejar suelto el guardado fue mi error
    # del 2026-08-10: el bug se movió de sitio en vez de cerrarse.
    dpi = int(dpi or 300)
    if fondo_id not in FONDOS:
        return {"status": "error", "mensaje": f"Fondo '{fondo_id}' no existe.", "disponibles": list(FONDOS)}
    frase = (frase or "").strip()
    if con_foto is True:
        modo = "frase_foto" if frase else "solo_foto"
    elif con_foto is False:
        modo = "solo_frase"
    if modo not in ("frase_foto", "solo_foto", "solo_frase"):
        modo = "frase_foto"

    w, h = _cm_a_px(ancho_cm, dpi), _cm_a_px(alto_cm, dpi)
    meta = FONDOS[fondo_id]
    img = meta["render"](w, h).convert("RGB")
    d = ImageDraw.Draw(img)
    quiere_foto = modo in ("frase_foto", "solo_foto")
    quiere_frase = modo in ("frase_foto", "solo_frase")

    foto_puesta = ""
    if quiere_foto:
        m = round(h * 0.12)
        caja = [m, m, (w - m) if modo == "solo_foto" else round(w * 0.40), h - m]
        cw, ch = caja[2] - caja[0], caja[3] - caja[1]
        if _es_imagen(foto):
            # LA FOTO DE VERDAD. Se recorta para llenar la caja sin deformar.
            ruta = str(Path(str(foto).strip().strip('"').strip("'")))
            with Image.open(ruta) as _f:
                puesta = _encajar(_f.convert("RGB"), cw, ch, recortar=recortar)
            img.paste(puesta, (caja[0], caja[1]))
            # El marco blanco se conserva: en la taza impresa separa la foto
            # del fondo de color y hace que no se vea "pegada".
            d.rounded_rectangle(caja, radius=24, outline=(255, 255, 255), width=6)
            foto_puesta = ruta
        else:
            # Sin foto: el recuadro guía de siempre, para armar la plantilla.
            d.rounded_rectangle(caja, radius=24, outline=(255, 255, 255), width=6)
            d.line([caja[0], caja[1], caja[2], caja[3]], fill=(255, 255, 255), width=2)
            d.line([caja[2], caja[1], caja[0], caja[3]], fill=(255, 255, 255), width=2)
            ff = _font(round(h * 0.06)); bb = d.textbbox((0, 0), "FOTO", font=ff)
            d.text(((caja[0] + caja[2]) / 2 - (bb[2] - bb[0]) / 2, (caja[1] + caja[3]) / 2 - (bb[3] - bb[1]) / 2),
                   "FOTO", font=ff, fill=(255, 255, 255))

    if quiere_frase:
        frase = frase or ("Tu frase" if modo == "solo_frase" else "Tu nombre")
        cx = round(w * 0.70) if modo == "frase_foto" else round(w * 0.5)
        zona_w = round(w * 0.50) if modo == "frase_foto" else round(w * 0.82)
        fs = round(h * 0.20) if modo == "solo_frase" else round(h * 0.16)
        f = _font(fs); lineas = _wrap(d, frase, f, zona_w)
        while len(lineas) > 3 and fs > round(h * 0.08):
            fs = int(fs * 0.88); f = _font(fs); lineas = _wrap(d, frase, f, zona_w)
        lh = int(fs * 1.22); bloque_h = lh * len(lineas)
        tw = max(d.textlength(l, font=f) for l in lineas); pad = round(h * 0.05)
        banda = Image.new("RGBA", (int(tw) + pad * 2, bloque_h + pad * 2), (255, 255, 255, 215))
        bx, by = int(cx - banda.width / 2), int(h * 0.5 - banda.height / 2)
        img.paste(banda, (bx, by), banda)
        for i, l in enumerate(lineas):
            lw = d.textlength(l, font=f)
            d.text((cx - lw / 2, by + pad + i * lh), l, font=f, fill=(30, 41, 59))

    if not salida:
        carpeta = Path.home() / "Desktop" / "Plantillas_Taza"
        carpeta.mkdir(parents=True, exist_ok=True)
        salida = str(carpeta / f"taza_{fondo_id}_{modo}.png")
    salida = _asegurar_extension(salida)
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    img.save(salida, dpi=(dpi, dpi))
    return {"status": "ok", "fondo": meta["nombre"], "tema": meta["tema"], "modo": modo,
            "salida": salida, "px": f"{w}x{h}", "dpi": dpi,
            "foto": foto_puesta or "(recuadro guía, sin foto)"}


def generar_hoja_a4(items=None, dpi: int = 300, salida: str = "") -> dict:
    """Imposición: hasta 3 tazas (21x9 cm) apiladas en una hoja A4 lista para imprimir.
    items = [{'fondo_id','frase','modo'}, ...]  (si viene vacío, arma 3 de muestra)."""
    import tempfile
    dpi = int(dpi or 300)
    A4W, A4H = _cm_a_px(21, dpi), _cm_a_px(29.7, dpi)
    mw, mh = _cm_a_px(21, dpi), _cm_a_px(9, dpi)

    # ── ENTENDER LO QUE DE VERDAD LLEGA ───────────────────────────────────
    # Anuar escribió: «genera una plantilla para 3 tazas con estas 2 fotos
    # "C:\...\taza arbol.jpg" "C:\...\taza arbol2.jpeg"». El enrutador hizo lo
    # correcto —le pasó las dos rutas— y esta función reventaba con
    # "'str' object has no attribute 'get'" porque solo sabía de diccionarios.
    # El error no estaba en cómo pidió las cosas: estaba aquí.
    if isinstance(items, str):
        items = [items]
    items = list(items or [])
    fotos = [str(x) for x in items if _es_imagen(x)]
    dicts = [x for x in items if isinstance(x, dict)]

    if fotos:
        # Con fotos manda la foto: se rellenan las 3 tazas rotando las que
        # haya. Con 2 fotos y 3 tazas salen foto1, foto2, foto1 — que es lo
        # que Anuar pidió y lo que se manda a imprimir en una hoja.
        base = [d for d in FONDOS] or [""]
        items = [{"fondo_id": dicts[i].get("fondo_id") if i < len(dicts) and dicts[i].get("fondo_id") in FONDOS
                                else base[i % len(base)],
                  "frase": dicts[i].get("frase", "") if i < len(dicts) else "",
                  "modo": "solo_foto",
                  "foto": fotos[i % len(fotos)]}
                 for i in range(3)]
    elif dicts:
        items = [it for it in dicts if it.get("fondo_id") in FONDOS][:3]
    else:
        items = [{"fondo_id": i, "frase": "", "modo": "frase_foto"} for i in list(FONDOS)[:3]]

    if not items:
        return {"status": "error",
                "mensaje": "No reconocí ni fotos existentes ni fondos válidos. "
                           "Pásame rutas de imágenes reales o nombres de fondo.",
                "fondos_disponibles": list(FONDOS)[:12]}
    hoja = Image.new("RGB", (A4W, A4H), (255, 255, 255))
    dh = ImageDraw.Draw(hoja)
    gap = max(10, (A4H - len(items) * mh) // (len(items) + 1))
    puestas = []
    for idx, it in enumerate(items):
        tmp = str(Path(tempfile.gettempdir()) / f"_taza_slot_{idx}.png")
        r = componer_taza(it["fondo_id"], frase=it.get("frase", ""),
                          modo=it.get("modo", "frase_foto"), ancho_cm=21, alto_cm=9,
                          dpi=dpi, salida=tmp, foto=it.get("foto", ""))
        if r.get("status") != "ok":
            continue
        img = Image.open(tmp).convert("RGB")
        if img.size != (mw, mh):
            img = img.resize((mw, mh))
        y = gap + idx * (mh + gap)
        hoja.paste(img, (0, y))
        dh.rectangle([0, y, mw - 1, y + mh - 1], outline=(205, 208, 214), width=1)
        puestas.append(it["fondo_id"])
        try:
            os.remove(tmp)
        except Exception:
            pass
    if not salida:
        carpeta = Path.home() / "Desktop" / "Plantillas_Taza"
        carpeta.mkdir(parents=True, exist_ok=True)
        salida = str(carpeta / "hoja_A4_3tazas.png")
    salida = _asegurar_extension(salida)
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    hoja.save(salida, dpi=(dpi, dpi))
    return {"status": "ok", "salida": salida, "tazas": puestas,
            "hoja_cm": "21 x 29.7 (A4)", "taza_cm": "21 x 9", "px": f"{A4W}x{A4H}", "dpi": dpi}


def catalogo_fondos(salida: str = "") -> dict:
    """Hoja de contactos con los 50 fondos agrupados por tema (miniaturas)."""
    tw, th = 300, 128
    pad, lab, head = 16, 30, 42
    cols = 5
    W = cols * tw + (cols + 1) * pad
    H = len(_TEMAS) * (head + th + lab + pad) + pad + 50
    hoja = Image.new("RGB", (W, H), (247, 248, 250)); d = ImageDraw.Draw(hoja)
    d.text((pad, 14), f"Catálogo de fondos para taza — {len(FONDOS)} fondos, 5 por tema",
           font=_font(24), fill=(30, 41, 59))
    y = 56
    for tema, tags, items in _TEMAS:
        d.text((pad, y), tema, font=_font(19), fill=(0, 134, 241)); y += head - 8
        for i, (fid, nom, render) in enumerate(items):
            x = pad + i * (tw + pad)
            hoja.paste(render(tw, th).convert("RGB"), (x, y))
            d.rectangle([x, y, x + tw, y + th], outline=(210, 215, 222), width=1)
            d.text((x + 3, y + th + 6), nom, font=_font(14), fill=(30, 41, 59))
        y += th + lab + pad
    if not salida:
        salida = str(Path.home() / "Desktop" / "Catalogo_Fondos_Taza.png")
    salida = _asegurar_extension(salida)
    hoja.save(salida)
    return {"status": "ok", "salida": salida, "total_fondos": len(FONDOS), "temas": len(_TEMAS)}


if __name__ == "__main__":
    import json
    print(json.dumps(catalogo_fondos(), ensure_ascii=False, indent=2))
