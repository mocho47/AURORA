# -*- coding: utf-8 -*-
"""SUPER EDITOR de AURORA: edicion real de imagenes (quitar fondo, linea B&N para laser,
preparar grabado, recolorear, redimensionar). Trabaja sobre archivos del disco."""
import os
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageFilter, ImageOps, ImageChops

OUT = Path(r"C:\AURORA\EDITOR_OUT")
OUT.mkdir(parents=True, exist_ok=True)

def _stamp(ruta, sufijo, ext="png"):
    base = Path(ruta).stem
    return OUT / f"{base}_{sufijo}.{ext}"

def _clean(ruta: str) -> str:
    """Acepta rutas con o sin comillas (ej. 'Copiar como ruta de acceso' de Windows)."""
    return (ruta or "").strip().strip('"').strip("'").strip()

def info() -> dict:
    return {"salida": str(OUT), "funciones": ["quitar_fondo", "linea", "grabado", "recolor", "redimensionar"]}

def quitar_fondo(ruta: str) -> dict:
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        from rembg import remove
        im = Image.open(ruta).convert("RGBA")
        cut = remove(im)
        cut = cut.crop(cut.getbbox()) if cut.getbbox() else cut
        dst = _stamp(ruta, "sinfondo")
        cut.save(dst)
        return {"status": "OK", "salida": str(dst), "archivo": dst.name}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}

def linea(ruta: str) -> dict:
    """Dibujo lineal limpio B&N (para vectorizar / grabar)."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        im = Image.open(ruta).convert("L")
        w, h = im.size
        if max(w, h) < 1400:
            f = 1400 / max(w, h); im = im.resize((int(w*f), int(h*f)), Image.LANCZOS)
        g = im.filter(ImageFilter.GaussianBlur(0.7))
        edges = ImageOps.autocontrast(g.filter(ImageFilter.FIND_EDGES))
        edges = edges.filter(ImageFilter.MaxFilter(3))
        bw = ImageOps.invert(edges).point(lambda p: 0 if p < 150 else 255).convert("L")
        dst = _stamp(ruta, "linea")
        bw.save(dst)
        return {"status": "OK", "salida": str(dst), "archivo": dst.name}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}

def grabado(ruta: str, umbral: int = 128) -> dict:
    """B&N puro (1-bit) para grabado laser por trama/umbral."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        im = ImageOps.autocontrast(Image.open(ruta).convert("L"))
        bw = im.point(lambda p: 0 if p < umbral else 255).convert("L")
        dst = _stamp(ruta, "grabado")
        bw.save(dst)
        return {"status": "OK", "salida": str(dst), "archivo": dst.name}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}

def redimensionar(ruta: str, ancho_cm: float = 0, alto_cm: float = 0, dpi: int = 300) -> dict:
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        im = Image.open(ruta)
        w = int(ancho_cm/2.54*dpi) if ancho_cm else im.width
        h = int(alto_cm/2.54*dpi) if alto_cm else im.height
        im = im.resize((w, h), Image.LANCZOS)
        dst = _stamp(ruta, f"{int(ancho_cm)}x{int(alto_cm)}cm")
        im.save(dst, dpi=(dpi, dpi))
        return {"status": "OK", "salida": str(dst), "archivo": dst.name, "px": f"{w}x{h}"}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def pdf_gran_formato(ruta: str, ancho_cm: float = 60, alto_cm: float = 40) -> dict:
    """Convierte una imagen a PDF a TAMAÑO REAL (gran formato) para impresión/lona."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        dst = _stamp(ruta, f"granformato_{int(ancho_cm)}x{int(alto_cm)}cm", "pdf")
        c = canvas.Canvas(str(dst), pagesize=(ancho_cm * cm, alto_cm * cm))
        c.drawImage(ruta, 0, 0, width=ancho_cm * cm, height=alto_cm * cm,
                    preserveAspectRatio=True, anchor="c", mask="auto")
        c.save()
        return {"status": "OK", "salida": str(dst), "archivo": dst.name, "cm": f"{ancho_cm}x{alto_cm}"}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def low_poly(ruta: str, puntos: int = 1500) -> dict:
    """Convierte una imagen a estilo LOW-POLY (triangulación Delaunay)."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        import numpy as np
        from scipy.spatial import Delaunay
        from PIL import ImageDraw
        im = Image.open(ruta).convert("RGB")
        w, h = im.size
        if max(w, h) > 1200:
            f = 1200 / max(w, h); im = im.resize((int(w * f), int(h * f)), Image.LANCZOS); w, h = im.size
        arr = np.asarray(im)
        ed = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES)).astype(float)
        prob = (ed / (ed.max() or 1)).flatten() + 0.02
        prob /= prob.sum()
        idx = np.random.choice(len(prob), size=min(puntos, len(prob)), replace=True, p=prob)
        ys, xs = np.unravel_index(idx, (h, w))
        pts = np.column_stack([xs, ys]).astype(float)
        pts = np.vstack([pts, [[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]]])
        tri = Delaunay(pts)
        out = Image.new("RGB", (w, h)); dr = ImageDraw.Draw(out)
        for t in tri.simplices:
            p = pts[t]
            cx = min(max(int(p[:, 0].mean()), 0), w - 1); cy = min(max(int(p[:, 1].mean()), 0), h - 1)
            dr.polygon([tuple(v) for v in p], fill=tuple(int(c) for c in arr[cy, cx]))
        dst = _stamp(ruta, "lowpoly"); out.save(dst)
        return {"status": "OK", "salida": str(dst), "archivo": dst.name}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def cartoon(ruta: str) -> dict:
    """Convierte una FOTO PROPIA a estilo cartoon (bordes + color suavizado)."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        import cv2
        img = cv2.imread(ruta)
        if img is None:
            return {"status": "ERROR", "detalle": "No pude leer la imagen"}
        h, w = img.shape[:2]
        if max(w, h) > 1400:
            f = 1400 / max(w, h); img = cv2.resize(img, (int(w * f), int(h * f)))
        gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img, 9, 250, 250)
        out = cv2.bitwise_and(color, color, mask=edges)
        dst = _stamp(ruta, "cartoon")
        cv2.imwrite(str(dst), out)
        return {"status": "OK", "salida": str(dst), "archivo": dst.name}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}
