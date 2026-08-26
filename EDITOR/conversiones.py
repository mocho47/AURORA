# -*- coding: utf-8 -*-
"""
AURA · CONVERSIONES (skills de diseñador/taller)
Cada función es un COMANDO real que AURORA sabe ejecutar.
Basado en cómo trabaja Anuar: láser (DXF/RDWorks/Aspire), sublimación (300dpi/B&N),
lonas, planillas, papercraft. Sin simulación: herramientas reales (PyMuPDF, PIL, OpenCV, vtracer, ezdxf, Inkscape).
"""
from __future__ import annotations
import os, subprocess, tempfile
from pathlib import Path

import fitz          # PyMuPDF
from PIL import Image
import ezdxf

INKSCAPE = r"C:\Program Files\Inkscape\bin\inkscape.exe"

# Sesión de segmentación de PERSONAS (u2net_human_seg): aísla al personaje
# sin arrastrar objetos del fondo (autos, muebles). Cacheada = se carga 1 sola vez.
_SES_HUMANO = None
_SES_GENERAL = None


def _sesion_humano():
    global _SES_HUMANO
    if _SES_HUMANO is None:
        from rembg import new_session
        _SES_HUMANO = new_session("u2net_human_seg")
    return _SES_HUMANO


# ── 1. ALIGERAR DXF (splines→polilíneas, formato viejo) ───────────────
def aligerar_dxf(entrada: str, salida: str = "", flatten_mm: float = 0.12) -> dict:
    """Convierte splines a polilíneas y guarda R2000: RDWorks lo lee y pesa menos."""
    if not salida:
        p = Path(entrada); salida = str(p.with_name(p.stem + " LIGERO.dxf"))
    src = ezdxf.readfile(entrada); msp_s = src.modelspace()
    new = ezdxf.new("R2000")
    for lay in src.layers:
        n = lay.dxf.name
        if n not in new.layers:
            try: new.layers.add(n, color=lay.dxf.get("color", 7))
            except Exception: pass
    msp = new.modelspace(); conv = 0
    for e in msp_s:
        if e.dxftype() == "SPLINE":
            pts = [(round(q[0], 3), round(q[1], 3)) for q in e.flattening(distance=flatten_mm)]
            limpio = [pts[0]] if pts else []
            for q in pts[1:]:
                if q != limpio[-1]: limpio.append(q)
            if len(limpio) >= 2:
                lw = msp.add_lwpolyline(limpio, dxfattribs={"layer": e.dxf.layer})
                if getattr(e, "closed", False): lw.close(True)
                conv += 1
        elif e.dxftype() in ("LINE", "LWPOLYLINE", "CIRCLE", "ARC"):
            try: msp.add_foreign_entity(e.copy())
            except Exception: pass
    new.saveas(salida)
    o = os.path.getsize(entrada); n2 = os.path.getsize(salida)
    return {"status": "ok", "salida": salida, "piezas": conv,
            "mb_antes": round(o/1048576, 2), "mb_despues": round(n2/1048576, 2),
            "reduccion_pct": round((1 - n2/o) * 100)}


# ── 2. PDF/imagen → B&N PURO a 300 DPI (prep para Aspire) ─────────────
def a_bw_puro(imagen_o_pdf: str, salida: str = "", dpi: int = 300, umbral: int = 128, pagina: int = 0) -> dict:
    ruta = Path(imagen_o_pdf)
    if ruta.suffix.lower() == ".pdf":
        d = fitz.open(imagen_o_pdf)
        try:
            pagina = max(0, min(int(pagina), d.page_count - 1))   # clamp a rango válido
            p = d[pagina]
            pix = p.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
        finally:
            d.close()   # evita bloqueo del archivo en Windows
    else:
        img = Image.open(imagen_o_pdf).convert("L")
    bw = img.point(lambda x: 0 if x < umbral else 255, "1")
    if not salida:
        salida = str(ruta.with_name(ruta.stem + "_BN.png"))
    bw.save(salida)
    return {"status": "ok", "salida": salida, "px": f"{bw.width}x{bw.height}", "dpi": dpi}


# ── 3. IMAGEN/FOTO → DIBUJO LINEAL (contorno) ────────────────────────
def a_linea(imagen: str, salida: str = "", grosor: int = 2) -> dict:
    import cv2, numpy as np
    img = cv2.imread(imagen, cv2.IMREAD_GRAYSCALE)
    if img is None: return {"status": "error", "mensaje": "No se pudo abrir la imagen"}
    img = cv2.bilateralFilter(img, 7, 60, 60)
    bordes = cv2.Canny(img, 60, 160)
    if grosor > 1:
        bordes = cv2.dilate(bordes, np.ones((grosor, grosor), np.uint8))
    linea = cv2.bitwise_not(bordes)  # líneas negras, fondo blanco
    if not salida:
        p = Path(imagen); salida = str(p.with_name(p.stem + "_LINEA.png"))
    cv2.imwrite(salida, linea)
    return {"status": "ok", "salida": salida}


# ── 4. PAPERCRAFT (raster) → DXF vía vectorizado ─────────────────────
def papercraft_a_dxf(pdf: str, pagina: int = 0, salida: str = "", dpi: int = 300) -> dict:
    """Renderiza → B&N → vtracer(SVG) → Inkscape(DXF). Honesto: raster vectorizado (imperfecto)."""
    import vtracer
    tmp = Path(tempfile.gettempdir())
    bn = tmp / f"pc_bn_{pagina}.png"; svg = tmp / f"pc_{pagina}.svg"
    r = a_bw_puro(pdf, str(bn), dpi=dpi, pagina=pagina)
    vtracer.convert_image_to_svg_py(str(bn), str(svg), colormode="binary")
    if not salida:
        p = Path(pdf); salida = str(p.with_name(f"{p.stem}_pag{pagina+1}.dxf"))
    if not os.path.exists(INKSCAPE):
        return {"status": "error", "mensaje": f"Inkscape no está en {INKSCAPE}. Instálalo o corrige la ruta.",
                "bn": r.get("salida")}
    try:
        proc = subprocess.run([INKSCAPE, str(svg), "--export-type=dxf",
                               f"--export-filename={salida}"], capture_output=True, timeout=120)
    except FileNotFoundError:
        return {"status": "error", "mensaje": f"No se pudo ejecutar Inkscape ({INKSCAPE}).", "bn": r.get("salida")}
    ok = os.path.exists(salida) and proc.returncode == 0
    return {"status": "ok" if ok else "error", "salida": salida if ok else None,
            "bn": r["salida"], "svg": str(svg),
            "nota": "Raster vectorizado: revisa/limpia en Aspire (agarra números y dobleces)."}


# ── 5. QUITAR FONDO (IA de segmentación, rembg/u2net) ────────────────
def _sesion(modelo: str):
    """La sesion de rembg del modelo pedido, creada una sola vez cada una.

    Hay dos y NO dan lo mismo (medido el 2026-08-26 con la piñata de Alicia):
      · u2net_human_seg -> entrenado en PERSONAS. 42 s. Es el que se usa para
        las fotos de gente que van a sublimacion, y ahi es el bueno.
      · u2net           -> objetos en general. 14 s, tres veces mas rapido, y
        es el correcto para una piñata, un trailer, un logo o una pieza.
    Usar el de personas para recortar un objeto costaba 28 s de mas por foto y
    fue lo que hacia que la cotizacion desde imagen se pasara del limite del
    chat y le contestara a Anuar "mandame el DXF" en vez del precio.
    """
    if modelo == "u2net_human_seg":
        return _sesion_humano()
    global _SES_GENERAL
    if _SES_GENERAL is None:
        from rembg import new_session
        _SES_GENERAL = new_session(modelo)
    return _SES_GENERAL


def quitar_fondo(entrada: str, salida: str = "", sobre_blanco: bool = False,
                 modelo: str = "u2net_human_seg") -> dict:
    """Recorta el sujeto y elimina el fondo. IA real (rembg). PNG con transparencia.

    modelo="u2net_human_seg" (default, sin cambios) para fotos de personas.
    modelo="u2net" para objetos — mas rapido y mas correcto (ver _sesion)."""
    from rembg import remove
    img = Image.open(entrada).convert("RGBA")
    cut = remove(img, session=_sesion(modelo))
    if sobre_blanco:
        bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
        cut = Image.alpha_composite(bg, cut).convert("RGB")
    if not salida:
        p = Path(entrada); salida = str(p.with_name(p.stem + "_sinfondo.png"))
    cut.save(salida)
    return {"status": "ok", "salida": salida, "px": f"{cut.width}x{cut.height}",
            "nota": "Fondo eliminado con IA (rembg). PNG con transparencia."}


# ── 6. FOTO → DIBUJO LINEAL REALISTA B&N (recorte IA + XDoG) ──────────
def foto_a_lineal(entrada: str, salida: str = "") -> dict:
    """Recorta la persona (rembg) y genera dibujo lineal limpio B&N (XDoG + realce local).
    Líneas negras sólidas sobre blanco — listo para sublimación/láser/vinil."""
    import cv2, numpy as np
    from rembg import remove
    cut = np.array(remove(Image.open(entrada).convert("RGBA"), session=_sesion_humano()))
    if cut.shape[2] < 4:
        return {"status": "error", "mensaje": "No se obtuvo canal alfa del recorte"}
    alpha = cut[:, :, 3]
    # componente mas grande (sin manchas fantasma del fondo)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats((alpha > 40).astype(np.uint8), 8)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = (lbl == big).astype(np.uint8) * 255
    else:
        mask = (alpha > 40).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    # componer sobre blanco + realce local (CLAHE) para sacar detalle de ropa/ cara
    a = (alpha.astype(np.float32) / 255.0)[:, :, None]
    comp = (cut[:, :, :3].astype(np.float32) * a + 255.0 * (1 - a)).astype(np.uint8)
    gray = cv2.cvtColor(comp, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=3.2, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.bilateralFilter(gray, 7, 60, 60)
    # XDoG -> lineas artisticas finas
    g = gray.astype(np.float32) / 255.0
    g1 = cv2.GaussianBlur(g, (0, 0), 0.9); g2 = cv2.GaussianBlur(g, (0, 0), 0.9 * 1.6)
    d = g1 - 0.99 * g2
    xd = np.ones_like(d); m = d < 0.0; xd[m] = 1.0 + np.tanh(14 * (d[m]))
    lines = (np.clip(xd, 0, 1) * 255).astype(np.uint8)
    bw = cv2.threshold(lines, 185, 255, cv2.THRESH_BINARY)[1]          # cuerpo: limpio
    bw_detalle = cv2.threshold(lines, 208, 255, cv2.THRESH_BINARY)[1]  # cara: más rasgos
    # Detección de cara → realza detalle SOLO en la cabeza (ojos/nariz/gorra)
    try:
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        for (fx, fy, fw, fh) in casc.detectMultiScale(gray, 1.1, 5, minSize=(55, 55)):
            x0 = max(0, fx - int(fw * 0.4)); y0 = max(0, fy - int(fh * 0.8))
            x1 = min(bw.shape[1], fx + fw + int(fw * 0.4)); y1 = min(bw.shape[0], fy + fh + int(fh * 0.3))
            bw[y0:y1, x0:x1] = bw_detalle[y0:y1, x0:x1]
    except Exception:
        pass
    # solo dentro de la persona + contorno limpio + limpieza de motas
    inner = cv2.erode(mask, np.ones((5, 5), np.uint8), 1)
    res = np.full_like(bw, 255); res[inner > 127] = bw[inner > 127]
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(res, [c for c in cnts if cv2.contourArea(c) > 5000], -1, 0, 3)
    inv = (res < 128).astype(np.uint8)
    nn, ll, ss, _ = cv2.connectedComponentsWithStats(inv, 8)
    for i in range(1, nn):
        if ss[i, cv2.CC_STAT_AREA] < 14:
            res[ll == i] = 255
    if not salida:
        p = Path(entrada); salida = str(p.with_name(p.stem + "_lineal.png"))
    cv2.imwrite(salida, res)
    return {"status": "ok", "salida": salida, "px": f"{res.shape[1]}x{res.shape[0]}",
            "nota": "Recorte IA + dibujo lineal B&N (XDoG). Listo para sublimar/cortar/vinil."}


if __name__ == "__main__":
    import sys, json
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    args = sys.argv[2:]
    fn = {"aligerar": aligerar_dxf, "bw": a_bw_puro, "linea": a_linea, "papercraft": papercraft_a_dxf,
          "fondo": quitar_fondo, "lineal": foto_a_lineal}.get(cmd)
    if not fn:
        print("Comandos: aligerar <dxf> | bw <archivo> | linea <img> | papercraft <pdf> [pagina]")
    else:
        if cmd == "papercraft" and len(args) > 1: args = [args[0], int(args[1])]
        print(json.dumps(fn(*args), ensure_ascii=False, indent=2))
