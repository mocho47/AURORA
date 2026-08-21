# -*- coding: utf-8 -*-
"""AURORA · ETIQUETAS Y TRAZABILIDAD

Anuar pidió el 2026-08-19, de un paquete de prompts, una etiqueta de producto
de 35×70 mm con logo, QR, lote y fecha, más stickers y variantes de color.

**Por qué esta y no las otras 29.** El lote se repite cada mes. Una vez que un
negocio te compra sus etiquetas, vuelve solo — no se vuelve a vender. Y él
imprime *y* suaja: es de los pocos que entrega la etiqueta impresa **con su
suaje**, no nada más el papel.

Lo que sale de aquí:

  · **PDF vectorial** — con el tamaño metido en el archivo, para que ninguna
    impresora lo «ajuste a página». Regla vieja de Anuar, aprendida a golpes.
  · **PNG a 300 DPI** — para ver y para quien pida imagen.
  · **DXF de suaje** — el contorno de corte para el láser o el plotter.
    Esto es lo que casi nadie entrega.
  · **Pliego armado** — las etiquetas ya acomodadas en la hoja, aprovechada,
    con marcas de registro para que el corte caiga donde debe.
  · **Bitácora de lotes** — qué se imprimió, para quién, cuándo y cuántas.

El QR se dibuja como **rectángulos vectoriales**, no como imagen pegada: en
imprenta una imagen de QR se ve mordida en los bordes y a veces deja de leerse.

Correr:
    python TALLER/etiquetas.py --etiqueta --nombre "Salsa La Güera" --lote L-2601 --qr "https://..."
    python TALLER/etiquetas.py --pliego --nombre "Salsa La Güera" --lote L-2601 --cuantas 40
    python TALLER/etiquetas.py --lotes
"""
from __future__ import annotations
import io
import json
import sqlite3
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONF = RAIZ / "CONFIG" / "etiquetas.json"
BD = RAIZ / "DATOS" / "etiquetas.db"
SALIDA = Path.home() / "Downloads" / "ETIQUETAS"

MM = 72.0 / 25.4          # milímetros a puntos (la unidad del PDF)
SANGRADO_MM = 2.0         # el color se pasa 2 mm de la línea de corte
MARGEN_MM = 3.0           # nada de texto a menos de 3 mm del filo

# Hojas donde se arman los pliegos, en milímetros.
HOJAS = {"carta": (215.9, 279.4), "oficio": (215.9, 355.6),
         "tabloide": (279.4, 431.8), "a4": (210.0, 297.0),
         "a3": (297.0, 420.0)}

# Los colores de variante sirven para que en el anaquel se distinga un lote de
# otro de un vistazo, sin leer. Es el truco que pide el pack de prompts y es
# de las cosas que más agradecen los que venden en tienda.
VARIANTES_BASE = {
    "original": {"color": "#C0392B", "texto": "#FFFFFF"},
    "verde":    {"color": "#1E8449", "texto": "#FFFFFF"},
    "azul":     {"color": "#1F4E79", "texto": "#FFFFFF"},
    "naranja":  {"color": "#D35400", "texto": "#FFFFFF"},
    "morado":   {"color": "#6C3483", "texto": "#FFFFFF"},
    "negro":    {"color": "#1C1C1C", "texto": "#FFFFFF"},
    "crema":    {"color": "#F4E3C1", "texto": "#3A2E1F"},
    "blanco":   {"color": "#FFFFFF", "texto": "#222222"},
}


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _sin_acentos(t) -> str:
    t = unicodedata.normalize("NFD", str(t or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _rgb(hexa: str):
    h = str(hexa or "#FFFFFF").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return (1.0, 1.0, 1.0)


def variantes() -> dict:
    """Los colores de lote. El archivo manda; si no existe, la tabla de aquí."""
    try:
        if CONF.exists():
            d = json.loads(CONF.read_text(encoding="utf-8"))
            if d.get("variantes"):
                return d["variantes"]
    except Exception:
        pass
    return VARIANTES_BASE


def guardar_config(vars_=None, medidas=None) -> Path:
    CONF.parent.mkdir(parents=True, exist_ok=True)
    prev = {}
    if CONF.exists():
        try:
            prev = json.loads(CONF.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    prev["variantes"] = vars_ or prev.get("variantes") or VARIANTES_BASE
    prev["medidas_comunes"] = medidas or prev.get("medidas_comunes") or {
        "etiqueta_frasco": [35, 70], "etiqueta_bote": [50, 80],
        "sticker_chico": [25, 25], "sticker_redondo": [40, 40],
        "etiqueta_ancha": [70, 35], "colgante": [40, 90]}
    prev["sangrado_mm"] = prev.get("sangrado_mm", SANGRADO_MM)
    prev["margen_mm"] = prev.get("margen_mm", MARGEN_MM)
    CONF.write_text(json.dumps(prev, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return CONF


# ── BITÁCORA DE LOTES ───────────────────────────────────────────────────
def _bd() -> sqlite3.Connection:
    BD.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(BD)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS lotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuando TEXT, cliente TEXT, producto TEXT, lote TEXT,
        caducidad TEXT, variante TEXT, piezas INTEGER,
        ancho_mm REAL, alto_mm REAL, archivo TEXT, nota TEXT)""")
    c.commit()
    return c


def registrar_lote(cliente="", producto="", lote="", caducidad="",
                   variante="original", piezas=0, ancho_mm=35.0,
                   alto_mm=70.0, archivo="", nota="") -> dict:
    """Deja constancia de lo impreso. Es la mitad del valor del servicio:
    cuando el cliente pregunta «¿qué le pusimos al lote de marzo?», hay
    respuesta."""
    c = _bd()
    c.execute("INSERT INTO lotes (cuando,cliente,producto,lote,caducidad,"
              "variante,piezas,ancho_mm,alto_mm,archivo,nota) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
              (datetime.now().isoformat(timespec="seconds"), cliente, producto,
               lote, caducidad, variante, int(piezas), float(ancho_mm),
               float(alto_mm), str(archivo), nota))
    c.commit()
    i = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return {"status": "OK", "id": i}


def lotes(cliente="", limite=40) -> dict:
    c = _bd()
    if cliente:
        f = c.execute("SELECT cuando,cliente,producto,lote,variante,piezas,"
                      "archivo FROM lotes WHERE cliente LIKE ? "
                      "ORDER BY id DESC LIMIT ?",
                      (f"%{cliente}%", limite)).fetchall()
    else:
        f = c.execute("SELECT cuando,cliente,producto,lote,variante,piezas,"
                      "archivo FROM lotes ORDER BY id DESC LIMIT ?",
                      (limite,)).fetchall()
    c.close()
    return {"status": "OK", "cuantos": len(f), "lotes": [
        {"cuando": x[0], "cliente": x[1], "producto": x[2], "lote": x[3],
         "variante": x[4], "piezas": x[5], "archivo": x[6]} for x in f]}


# ── EL QR, VECTORIAL ────────────────────────────────────────────────────
def _qr_modulos(dato: str):
    """Devuelve la matriz del QR. Sin librería, devuelve None y se omite."""
    try:
        import qrcode
        q = qrcode.QRCode(border=0,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(str(dato))
        q.make(fit=True)
        return q.get_matrix()
    except Exception:
        return None


def _pinta_qr(c, dato, x_mm, y_mm, lado_mm, color=(0, 0, 0)):
    """Dibuja el QR cuadrito por cuadrito, en vectores.

    Se dibuja así y no como imagen porque en imprenta un QR rasterizado se
    muerde en los bordes y hay lectores que dejan de leerlo. En vectores sale
    perfecto a cualquier tamaño.
    """
    m = _qr_modulos(dato)
    if not m:
        return False
    n = len(m)
    paso = lado_mm / n
    c.setFillColorRGB(*color)
    for fila in range(n):
        for col in range(n):
            if m[fila][col]:
                c.rect((x_mm + col * paso) * MM,
                       (y_mm + (n - 1 - fila) * paso) * MM,
                       paso * MM + 0.2, paso * MM + 0.2, stroke=0, fill=1)
    return True


# ── LA ETIQUETA ─────────────────────────────────────────────────────────
def _dibuja_una(c, x_mm, y_mm, ancho, alto, datos, v, con_sangrado=True):
    """Pinta una etiqueta con la esquina inferior izquierda en (x_mm, y_mm)."""
    from reportlab.lib.utils import ImageReader

    fondo = _rgb(v.get("color", "#FFFFFF"))
    tinta = _rgb(v.get("texto", "#222222"))
    sang = SANGRADO_MM if con_sangrado else 0.0

    # El fondo se pasa del corte. Así, si el suaje se recorre medio milímetro
    # —y siempre se recorre—, no aparece la orilla blanca del papel.
    c.setFillColorRGB(*fondo)
    c.rect((x_mm - sang) * MM, (y_mm - sang) * MM,
           (ancho + sang * 2) * MM, (alto + sang * 2) * MM, stroke=0, fill=1)

    m = MARGEN_MM
    cx = x_mm + ancho / 2

    # ── Logo, arriba y centrado ──
    y = y_mm + alto - m
    logo = datos.get("logo")
    if logo and Path(str(logo)).exists():
        try:
            img = ImageReader(str(logo))
            iw, ih = img.getSize()
            ancho_logo = min(ancho - m * 2, (ancho - m * 2))
            alto_logo = ancho_logo * ih / iw
            tope = alto * 0.30
            if alto_logo > tope:                 # que no se coma la etiqueta
                alto_logo = tope
                ancho_logo = alto_logo * iw / ih
            c.drawImage(img, (cx - ancho_logo / 2) * MM,
                        (y - alto_logo) * MM, ancho_logo * MM, alto_logo * MM,
                        mask="auto")
            y -= alto_logo + 2.0
        except Exception:
            pass

    # ── Nombre del producto ──
    nombre = _sin_acentos(datos.get("nombre", ""))
    if nombre:
        # El tamaño se ajusta solo para que quepa: un nombre largo no debe
        # desbordarse ni obligar a rehacer el diseño.
        pt = min(alto * 0.085 * MM / MM * 2.2, 16)
        while pt > 5:
            c.setFont("Helvetica-Bold", pt)
            if c.stringWidth(nombre, "Helvetica-Bold", pt) <= (ancho - m * 2) * MM:
                break
            pt -= 0.5
        c.setFillColorRGB(*tinta)
        c.setFont("Helvetica-Bold", pt)
        y -= pt / MM + 1.0
        c.drawCentredString(cx * MM, y * MM, nombre)

    sub = _sin_acentos(datos.get("descripcion", ""))
    if sub:
        c.setFont("Helvetica", 6.5)
        y -= 4.0
        c.drawCentredString(cx * MM, y * MM, sub[:44])

    # ── El pie primero: se le aparta su lugar ──
    # Si se dibuja al último sin reservarle espacio, los datos de trazabilidad
    # se le encaraman. Pasó en la primera prueba: el «CAD» se salió del corte.
    pie = _sin_acentos(datos.get("pie", ""))
    alto_pie = 3.5 if pie else 0.0
    if pie:
        c.setFillColorRGB(*tinta)
        c.setFont("Helvetica", 4.8)
        c.drawCentredString(cx * MM, (y_mm + 1.4) * MM, pie[:60])

    # ── QR abajo a la izquierda, trazabilidad a su derecha ──
    qr_dato = datos.get("qr", "")
    campos = [(e, v) for e, v in (("LOTE", datos.get("lote", "")),
                                  ("FECHA", datos.get("fecha", "")),
                                  ("CAD", datos.get("caducidad", "")))
              if v]
    # Cada dato en UNA sola línea («LOTE  L-2608»), no en dos. Ocupa la mitad
    # y se lee igual de bien; es lo que hace que quepan los tres.
    paso = 4.6
    alto_datos = max(0.0, len(campos) * paso)
    base = y_mm + m + alto_pie

    # El QR se lleva un tercio del ancho, no la mitad. En una etiqueta de 35 mm
    # un QR grande no deja lugar para la fecha: en la segunda prueba el
    # «19/08/2026» se salió por la derecha. Un tercio se sigue leyendo bien con
    # cualquier teléfono.
    lado = min(ancho * 0.34, alto * 0.26, 20.0)
    lado = min(max(lado, 11.0), ancho - m * 2)   # abajo de 11 mm ya no lee

    hay_qr = False
    if qr_dato:
        hay_qr = _pinta_qr(c, qr_dato, x_mm + m, base, lado, tinta)

    tx = (x_mm + m + lado + 2.0) if hay_qr else (x_mm + m)
    derecha = x_mm + ancho - m
    # Se apilan de arriba hacia abajo desde el tope del bloque, para que el
    # último campo caiga sobre la base y no debajo de ella.
    ty = base + max(lado, alto_datos) - 3.2
    c.setFillColorRGB(*tinta)
    for etq, val in campos:
        pt_e = 4.8
        c.setFont("Helvetica", pt_e)
        c.drawString(tx * MM, ty * MM, etq)
        # El valor arranca donde de verdad termina la palabra, medida en el
        # tipo real — no a 9 mm fijos, que es lo que reventaba el acomodo.
        sangria = c.stringWidth(etq, "Helvetica", pt_e) / MM + 1.2
        libre = derecha - (tx + sangria)
        vt = _sin_acentos(val)
        pt = 7.0
        while pt > 4.2 and c.stringWidth(vt, "Helvetica-Bold", pt) > libre * MM:
            pt -= 0.25
        c.setFont("Helvetica-Bold", pt)
        c.drawString((tx + sangria) * MM, ty * MM, vt[:20])
        ty -= paso


def etiqueta(nombre="Producto", lote="", fecha="", caducidad="", qr="",
             logo="", variante="original", descripcion="", pie="",
             ancho_mm=35.0, alto_mm=70.0, cliente="", salida="",
             piezas=0, png=True) -> dict:
    """Una etiqueta suelta: PDF vectorial + PNG de 300 DPI + DXF de suaje."""
    try:
        from reportlab.pdfgen import canvas as rl
    except ImportError:
        return {"status": "ERROR",
                "mensaje": "Falta reportlab: pip install reportlab"}

    v = variantes().get(variante, VARIANTES_BASE["original"])
    datos = {"nombre": nombre, "lote": lote,
             "fecha": fecha or date.today().strftime("%d/%m/%Y"),
             "caducidad": caducidad, "qr": qr, "logo": logo,
             "descripcion": descripcion, "pie": pie}

    carpeta = Path(salida) if salida else SALIDA
    carpeta.mkdir(parents=True, exist_ok=True)
    base = f"{_sin_acentos(nombre).replace(' ', '_')[:28]}_{variante}"
    if lote:
        base += f"_{_sin_acentos(lote).replace(' ', '')[:14]}"
    pdf = carpeta / f"{base}_{ancho_mm:g}x{alto_mm:g}mm.pdf"

    # La página mide la etiqueta MÁS el sangrado. Así el PDF ya trae adentro
    # la medida real y el driver no tiene nada que «ajustar».
    an = (ancho_mm + SANGRADO_MM * 2) * MM
    al = (alto_mm + SANGRADO_MM * 2) * MM
    c = rl.Canvas(str(pdf), pagesize=(an, al))
    c.setTitle(f"{nombre} · lote {lote}")
    _dibuja_una(c, SANGRADO_MM, SANGRADO_MM, ancho_mm, alto_mm, datos, v)
    # La línea de corte, punteada y del color de la tinta: sirve de guía si se
    # corta a mano y se borra sola si se manda a suaje.
    c.setStrokeColorRGB(*_rgb(v.get("texto", "#222222")))
    c.setLineWidth(0.25)
    c.setDash(2, 2)
    c.rect(SANGRADO_MM * MM, SANGRADO_MM * MM, ancho_mm * MM, alto_mm * MM,
           stroke=1, fill=0)
    c.showPage()
    c.save()

    r = {"status": "OK", "pdf": str(pdf), "ancho_mm": ancho_mm,
         "alto_mm": alto_mm, "variante": variante, "lote": lote,
         "sangrado_mm": SANGRADO_MM}

    if png:
        p = _png_de_pdf(pdf)
        if p:
            r["png"] = str(p)
    d = suaje_dxf(ancho_mm, alto_mm, 1, 1, carpeta, base)
    if d.get("dxf"):
        r["dxf"] = d["dxf"]

    registrar_lote(cliente, nombre, lote, caducidad, variante, piezas,
                   ancho_mm, alto_mm, str(pdf))
    return r


def _png_de_pdf(pdf: Path, dpi: int = 300):
    """Saca el PNG del mismo PDF, para que la vista sea lo que se imprime."""
    try:
        import fitz            # PyMuPDF
        d = fitz.open(str(pdf))
        pg = d.load_page(0)
        pix = pg.get_pixmap(dpi=dpi)
        out = pdf.with_suffix(".png")
        pix.save(str(out))
        d.close()
        return out
    except Exception:
        return None


# ── EL PLIEGO ───────────────────────────────────────────────────────────
def pliego(nombre="Producto", lote="", fecha="", caducidad="", qr="",
           logo="", variante="original", descripcion="", pie="",
           ancho_mm=35.0, alto_mm=70.0, cuantas=0, hoja="carta",
           separacion_mm=2.0, cliente="", salida="",
           lotes_variados=None) -> dict:
    """Acomoda las etiquetas en la hoja, aprovechada, con marcas de registro.

    Aquí está el ahorro de verdad: una etiqueta suelta por hoja es tirar
    papel. En carta caben 18 de 35×70 mm; imprimir 40 son 3 hojas, no 40.

    `lotes_variados` — una lista de lotes para que salgan en el mismo pliego
    (útil cuando el cliente pide varios lotes chicos de una vez).
    """
    try:
        from reportlab.pdfgen import canvas as rl
    except ImportError:
        return {"status": "ERROR",
                "mensaje": "Falta reportlab: pip install reportlab"}

    hj = HOJAS.get(str(hoja).lower(), HOJAS["carta"])
    hw, hh = hj
    orilla = 6.0                      # lo que no imprime casi ninguna impresora
    paso_x = ancho_mm + separacion_mm
    paso_y = alto_mm + separacion_mm
    cols = int((hw - orilla * 2 + separacion_mm) // paso_x)
    filas = int((hh - orilla * 2 + separacion_mm) // paso_y)

    # Si no cabe de pie, se prueba acostada. Muchas veces cambia el
    # rendimiento por completo y nadie lo revisa a mano.
    girada = False
    c2 = int((hw - orilla * 2 + separacion_mm) // (alto_mm + separacion_mm))
    f2 = int((hh - orilla * 2 + separacion_mm) // (ancho_mm + separacion_mm))
    if c2 * f2 > cols * filas:
        cols, filas, girada = c2, f2, True
        paso_x, paso_y = alto_mm + separacion_mm, ancho_mm + separacion_mm

    por_hoja = cols * filas
    if por_hoja < 1:
        return {"status": "ERROR",
                "mensaje": f"Una etiqueta de {ancho_mm:g}×{alto_mm:g} mm no "
                           f"cabe en hoja {hoja}. Usa una hoja más grande."}

    total = int(cuantas) if cuantas else por_hoja
    hojas = -(-total // por_hoja)          # redondeo para arriba

    v = variantes().get(variante, VARIANTES_BASE["original"])
    carpeta = Path(salida) if salida else SALIDA
    carpeta.mkdir(parents=True, exist_ok=True)
    base = f"PLIEGO_{_sin_acentos(nombre).replace(' ', '_')[:24]}_{variante}"
    pdf = carpeta / f"{base}_{total}pzs_{hoja}.pdf"

    c = rl.Canvas(str(pdf), pagesize=(hw * MM, hh * MM))
    c.setTitle(f"Pliego {nombre} · {total} piezas")
    # Centrado en la hoja: sobra igual de cada lado y el corte queda parejo.
    x0 = (hw - (cols * paso_x - separacion_mm)) / 2
    y0 = (hh - (filas * paso_y - separacion_mm)) / 2

    puestas = 0
    for h in range(hojas):
        for f in range(filas):
            for co in range(cols):
                if puestas >= total:
                    break
                lot = lote
                if lotes_variados:
                    lot = lotes_variados[puestas % len(lotes_variados)]
                datos = {"nombre": nombre, "lote": lot,
                         "fecha": fecha or date.today().strftime("%d/%m/%Y"),
                         "caducidad": caducidad, "qr": qr, "logo": logo,
                         "descripcion": descripcion, "pie": pie}
                x = x0 + co * paso_x
                y = hh - y0 - (f + 1) * paso_y + separacion_mm
                if girada:
                    c.saveState()
                    c.translate((x + alto_mm) * MM, y * MM)
                    c.rotate(90)
                    _dibuja_una(c, 0, 0, ancho_mm, alto_mm, datos, v,
                                con_sangrado=False)
                    c.restoreState()
                else:
                    _dibuja_una(c, x, y, ancho_mm, alto_mm, datos, v,
                                con_sangrado=False)
                puestas += 1
        _marcas_registro(c, hw, hh)
        c.showPage()

    c.save()
    r = {"status": "OK", "pdf": str(pdf), "hoja": hoja,
         "por_hoja": por_hoja, "columnas": cols, "filas": filas,
         "girada": girada, "piezas": total, "hojas": hojas,
         "aprovechamiento": round(
             por_hoja * ancho_mm * alto_mm / (hw * hh) * 100, 1)}
    d = suaje_dxf(ancho_mm, alto_mm, cols, filas, carpeta, base,
                  separacion_mm, girada, hw, hh, x0, y0)
    if d.get("dxf"):
        r["dxf_suaje"] = d["dxf"]
    p = _png_de_pdf(pdf)
    if p:
        r["png"] = str(p)
    registrar_lote(cliente, nombre, lote, caducidad, variante, total,
                   ancho_mm, alto_mm, str(pdf),
                   f"pliego {cols}x{filas} en {hoja}")
    return r


def _marcas_registro(c, hw, hh, largo=5.0, orilla=3.0):
    """Cruces en las esquinas. Sin ellas no hay forma de alinear el suaje con
    lo impreso, y el corte sale corrido en toda la tirada."""
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.3)
    c.setDash()
    for x, y in ((orilla, orilla), (hw - orilla, orilla),
                 (orilla, hh - orilla), (hw - orilla, hh - orilla)):
        c.line((x - largo / 2) * MM, y * MM, (x + largo / 2) * MM, y * MM)
        c.line(x * MM, (y - largo / 2) * MM, x * MM, (y + largo / 2) * MM)


def suaje_dxf(ancho_mm, alto_mm, cols=1, filas=1, carpeta=None, base="suaje",
              separacion_mm=2.0, girada=False, hoja_w=0, hoja_h=0,
              x0=None, y0=None) -> dict:
    """El contorno de corte para el láser o el plotter, en milímetros reales.

    Va en su propia capa `CORTE` para que la máquina la reconozca de una vez y
    no haya que separar nada a mano.
    """
    try:
        import ezdxf
    except ImportError:
        return {"status": "ERROR", "mensaje": "Falta ezdxf"}

    carpeta = Path(carpeta) if carpeta else SALIDA
    carpeta.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2010", setup=True)
    doc.units = 4                      # 4 = milímetros
    doc.layers.add("CORTE", color=1)
    doc.layers.add("REGISTRO", color=5)
    msp = doc.modelspace()

    an, al = (alto_mm, ancho_mm) if girada else (ancho_mm, alto_mm)
    px, py = an + separacion_mm, al + separacion_mm
    bx = x0 if x0 is not None else 0.0
    by = y0 if y0 is not None else 0.0

    for f in range(filas):
        for co in range(cols):
            x = bx + co * px
            y = by + f * py
            msp.add_lwpolyline(
                [(x, y), (x + an, y), (x + an, y + al), (x, y + al)],
                close=True, dxfattribs={"layer": "CORTE"})

    if hoja_w and hoja_h:
        orilla = 3.0
        for x, y in ((orilla, orilla), (hoja_w - orilla, orilla),
                     (orilla, hoja_h - orilla),
                     (hoja_w - orilla, hoja_h - orilla)):
            msp.add_line((x - 2.5, y), (x + 2.5, y),
                         dxfattribs={"layer": "REGISTRO"})
            msp.add_line((x, y - 2.5), (x, y + 2.5),
                         dxfattribs={"layer": "REGISTRO"})

    out = carpeta / f"{base}_SUAJE.dxf"
    doc.saveas(str(out))
    return {"status": "OK", "dxf": str(out), "piezas": cols * filas}


def sticker(nombre="", qr="", logo="", variante="original", diametro_mm=40.0,
            lote="", cliente="", salida="", cuantas=0, hoja="carta") -> dict:
    """Sticker redondo. Mismo motor, contorno circular en el suaje."""
    r = pliego(nombre=nombre, lote=lote, qr=qr, logo=logo, variante=variante,
               ancho_mm=diametro_mm, alto_mm=diametro_mm, cuantas=cuantas,
               hoja=hoja, cliente=cliente, salida=salida)
    if r.get("status") != "OK":
        return r
    # El suaje cuadrado no sirve para un redondo: se rehace con círculos.
    try:
        import ezdxf
        doc = ezdxf.new("R2010", setup=True)
        doc.units = 4
        doc.layers.add("CORTE", color=1)
        msp = doc.modelspace()
        rad = diametro_mm / 2
        paso = diametro_mm + 2.0
        for f in range(r["filas"]):
            for co in range(r["columnas"]):
                msp.add_circle((co * paso + rad, f * paso + rad), rad,
                               dxfattribs={"layer": "CORTE"})
        out = Path(r["pdf"]).with_name(Path(r["pdf"]).stem + "_SUAJE_REDONDO.dxf")
        doc.saveas(str(out))
        r["dxf_suaje"] = str(out)
        r["forma"] = "redondo"
    except Exception:
        pass
    return r


def cuanto_cobrar(piezas=100, ancho_mm=35.0, alto_mm=70.0, hoja="carta",
                  costo_hoja=3.5, con_suaje=True, minutos_suaje=None,
                  diseno=15.0) -> dict:
    """El precio con la fórmula de Anuar, sin adivinar.

    `(materiales × 1.20) + corte $8/min + diseño`. Y el corte se calcula del
    perímetro real a 20 mm/s, que es la velocidad de su máquina.
    """
    hj = HOJAS.get(str(hoja).lower(), HOJAS["carta"])
    cols = int((hj[0] - 12 + 2) // (ancho_mm + 2))
    filas = int((hj[1] - 12 + 2) // (alto_mm + 2))
    por_hoja = max(1, cols * filas)
    hojas = -(-int(piezas) // por_hoja)
    materiales = hojas * float(costo_hoja)

    corte = 0.0
    mins = 0.0
    if con_suaje:
        if minutos_suaje is None:
            # Perímetro de todas las piezas a 20 mm/s.
            mm_total = (ancho_mm + alto_mm) * 2 * int(piezas)
            mins = mm_total / 20.0 / 60.0
        else:
            mins = float(minutos_suaje)
        corte = mins * 8.0

    total = materiales * 1.20 + corte + float(diseno)
    return {"status": "OK", "piezas": int(piezas), "por_hoja": por_hoja,
            "hojas": hojas, "materiales": round(materiales, 2),
            "materiales_con_margen": round(materiales * 1.20, 2),
            "minutos_corte": round(mins, 1), "corte": round(corte, 2),
            "diseno": float(diseno), "total": round(total, 2),
            "por_pieza": round(total / max(1, int(piezas)), 2)}


def main() -> int:
    _consola_utf8()
    a = sys.argv[1:]

    def _op(n, d=None):
        if f"--{n}" in a:
            i = a.index(f"--{n}")
            if i + 1 < len(a):
                return a[i + 1]
        return d

    def _f(n, d=0.0):
        try:
            return float(str(_op(n, d)).replace(",", ""))
        except (TypeError, ValueError):
            return d

    comun = dict(nombre=_op("nombre", "Producto"), lote=_op("lote", ""),
                 fecha=_op("fecha", ""), caducidad=_op("cad", ""),
                 qr=_op("qr", ""), logo=_op("logo", ""),
                 variante=_op("variante", "original"),
                 descripcion=_op("desc", ""), pie=_op("pie", ""),
                 ancho_mm=_f("ancho", 35), alto_mm=_f("alto", 70),
                 cliente=_op("cliente", ""), salida=_op("salida", ""))

    if "--lotes" in a:
        r = lotes(_op("cliente", ""))
        print(f"📒 {r['cuantos']} lotes registrados\n")
        for x in r["lotes"]:
            print(f"  {x['cuando'][:16]}  {x['cliente'][:18]:<18} "
                  f"{x['producto'][:22]:<22} lote {x['lote'][:12]:<12} "
                  f"{x['variante'][:9]:<9} {x['piezas']:>5} pzs")
        return 0
    if "--variantes" in a:
        for k, v in variantes().items():
            print(f"  {k:<12} fondo {v['color']}  texto {v['texto']}")
        return 0
    if "--precio" in a:
        r = cuanto_cobrar(int(_f("piezas", 100)), _f("ancho", 35),
                          _f("alto", 70), _op("hoja", "carta"),
                          _f("costo_hoja", 3.5), "--sin-suaje" not in a,
                          None, _f("diseno", 15))
        print(f"💵 {r['piezas']} etiquetas de {_f('ancho', 35):g}×"
              f"{_f('alto', 70):g} mm\n"
              f"   {r['por_hoja']} por hoja → {r['hojas']} hojas\n"
              f"   Materiales +20%:  ${r['materiales_con_margen']:>8,.2f}\n"
              f"   Suaje ({r['minutos_corte']:g} min): ${r['corte']:>8,.2f}\n"
              f"   Diseño:           ${r['diseno']:>8,.2f}\n"
              f"   ──────────────────────────────\n"
              f"   TOTAL:            ${r['total']:>8,.2f}   "
              f"(${r['por_pieza']:.2f} c/u)")
        return 0
    if "--sticker" in a:
        r = sticker(comun["nombre"], comun["qr"], comun["logo"],
                    comun["variante"], _f("diametro", 40), comun["lote"],
                    comun["cliente"], comun["salida"],
                    int(_f("cuantas", 0)), _op("hoja", "carta"))
    elif "--pliego" in a:
        r = pliego(cuantas=int(_f("cuantas", 0)), hoja=_op("hoja", "carta"),
                   separacion_mm=_f("sep", 2), **comun)
    elif "--etiqueta" in a:
        r = etiqueta(piezas=int(_f("piezas", 0)), **comun)
    else:
        print(__doc__)
        return 0

    if r.get("status") != "OK":
        print(f"❌ {r.get('mensaje')}")
        return 1
    print("✅ Listo")
    for k in ("pdf", "png", "dxf", "dxf_suaje"):
        if r.get(k):
            print(f"   {k.upper():<10} {r[k]}")
    if r.get("por_hoja"):
        print(f"   {r['por_hoja']} por hoja ({r['columnas']}×{r['filas']}"
              + (", acostadas" if r.get("girada") else "")
              + f") · {r['hojas']} hojas · aprovecha "
                f"{r['aprovechamiento']}% del papel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
