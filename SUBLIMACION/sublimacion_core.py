# -*- coding: utf-8 -*-
"""SUBLIMACIÓN de AURORA — método de Anuar automatizado.
De un VIDEO (TikTok/url o local) o una IMAGEN, hasta el lienzo LISTO PARA IMPRIMIR
a 300 DPI (PDF + PNG + vista previa), en la medida real (taza/A4, etc.).

- Reutiliza herramientas libres: yt-dlp (descarga), ffmpeg (fotogramas), Pillow/reportlab (lienzo).
- Todo a 300 DPI, par PDF+PNG, dimensiones en cm — como trabaja Anuar.
"""
from __future__ import annotations
import os, subprocess, shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw

# Salida RELATIVA a la raíz de AURORA (antes quemada a C:\AURORA\SUBLIMACION_OUT,
# carpeta del proyecto viejo: los archivos se generaban fuera de AURORA).
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "SUBLIMACION_OUT"
OUT.mkdir(parents=True, exist_ok=True)
PY = r"C:\Program Files\Python312\python.exe"


def _ffmpeg() -> str:
    for c in (r"C:\Users\Administrador\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
              "ffmpeg"):
        try:
            subprocess.run([c, "-version"], capture_output=True, timeout=10)
            return c
        except Exception:
            continue
    return "ffmpeg"


def _cm(v, dpi=300):
    return int(round(v / 2.54 * dpi))


def de_video(origen: str, fps: int = 1) -> dict:
    """Descarga el video (si es url) y extrae fotogramas. Devuelve la carpeta de frames."""
    origen = (origen or "").strip().strip('"')
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = OUT / f"frames_{stamp}"; carpeta.mkdir(parents=True, exist_ok=True)
    if origen.startswith("http"):
        video = carpeta / "fuente.mp4"
        r = subprocess.run([PY, "-m", "yt_dlp", "-o", str(video), origen],
                           capture_output=True, text=True, timeout=300)
        if not video.exists():
            return {"status": "ERROR", "detalle": "No pude descargar: " + (r.stderr or "")[-200:]}
    else:
        if not os.path.isfile(origen):
            return {"status": "ERROR", "detalle": f"No existe: {origen}"}
        video = Path(origen)
    code = subprocess.run([_ffmpeg(), "-i", str(video), "-vf", f"fps={fps}", "-q:v", "2",
                           str(carpeta / "frame_%03d.jpg"), "-y"], capture_output=True, timeout=180)
    frames = sorted(carpeta.glob("frame_*.jpg"))
    if not frames:
        return {"status": "ERROR", "detalle": "No se extrajeron fotogramas"}
    return {"status": "OK", "carpeta": str(carpeta), "frames": len(frames),
            "ejemplos": [f.name for f in frames[:5]]}


def lienzo_blanco(ancho_cm: float = 21, alto_cm: float = 9, dpi: int = 300, hoja: str = "A4") -> dict:
    """Genera el LIENZO en blanco con guías (para armar a mano), 300 DPI: PNG + PDF + preview."""
    bw, bh = _cm(ancho_cm, dpi), _cm(alto_cm, dpi)
    W, H = (_cm(21.0, dpi), _cm(29.7, dpi)) if hoja.upper() == "A4" else (bw, bh)
    img = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(img)
    bx, by = (W - bw) // 2, (_cm(1.0, dpi) if hoja.upper() == "A4" else 0)
    d.rectangle([bx, by, bx + bw - 1, by + bh], outline=(170, 170, 170), width=3)
    m = _cm(0.5, dpi); d.rectangle([bx + m, by + m, bx + bw - 1 - m, by + bh - m], outline=(255, 120, 120), width=2)
    d.line([(bx + bw // 2, by), (bx + bw // 2, by + bh)], fill=(120, 170, 255), width=1)
    png = OUT / f"LIENZO_{int(ancho_cm)}x{int(alto_cm)}cm_{dpi}dpi.png"; img.save(png, dpi=(dpi, dpi))
    prev = OUT / f"LIENZO_{int(ancho_cm)}x{int(alto_cm)}_PREVIEW.jpg"; img.resize((W // 3, H // 3)).save(prev, quality=85)
    pdf = OUT / f"LIENZO_{int(ancho_cm)}x{int(alto_cm)}cm.pdf"
    try:
        from reportlab.pdfgen import canvas as rc
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm as CM
        if hoja.upper() == "A4":
            c = rc.Canvas(str(pdf), pagesize=A4); pw, ph = A4; px = (pw - ancho_cm * CM) / 2; py = ph - 1 * CM - alto_cm * CM
        else:
            c = rc.Canvas(str(pdf), pagesize=(ancho_cm * CM, alto_cm * CM)); px, py = 0, 0
        c.setStrokeColorRGB(.67, .67, .67); c.rect(px, py, ancho_cm * CM, alto_cm * CM)
        c.setStrokeColorRGB(1, .47, .47); c.rect(px + .5 * CM, py + .5 * CM, (ancho_cm - 1) * CM, (alto_cm - 1) * CM)
        c.save()
    except Exception:
        pdf = None
    return {"status": "OK", "png": str(png), "pdf": (str(pdf) if pdf else None), "preview": str(prev),
            "medida": f"{ancho_cm}x{alto_cm}cm @ {dpi}DPI ({hoja})"}


def montar(imagen: str, ancho_cm: float = 21, alto_cm: float = 9, dpi: int = 300,
           hoja: str = "A4") -> dict:
    """Monta una imagen de diseño en el lienzo a medida y exporta LISTO PARA IMPRIMIR
    (PNG 300 DPI + PDF a escala real + vista previa). hoja: 'A4' o 'exacto'."""
    imagen = (imagen or "").strip().strip('"')
    if not os.path.isfile(imagen):
        return {"status": "ERROR", "detalle": f"No existe la imagen: {imagen}"}
    try:
        dis = Image.open(imagen).convert("RGBA")
        bw, bh = _cm(ancho_cm, dpi), _cm(alto_cm, dpi)
        # ajustar diseño DENTRO de la banda (contener, sin deformar)
        dis.thumbnail((bw, bh), Image.LANCZOS)
        if hoja.upper() == "A4":
            W, H = _cm(21.0, dpi), _cm(29.7, dpi)
        else:
            W, H = bw, bh
        lienzo = Image.new("RGB", (W, H), (255, 255, 255))
        bx, by = (W - bw) // 2, _cm(1.0, dpi) if hoja.upper() == "A4" else 0
        # pegar diseño centrado en la banda
        ox = bx + (bw - dis.width) // 2; oy = by + (bh - dis.height) // 2
        lienzo.paste(dis, (ox, oy), dis)
        d = ImageDraw.Draw(lienzo)
        d.rectangle([bx, by, bx + bw, by + bh], outline=(200, 200, 200), width=2)
        d.line([(bx + bw // 2, by), (bx + bw // 2, by + bh)], fill=(180, 200, 255), width=1)
        base = Path(imagen).stem
        png = OUT / f"{base}_LISTO_{int(ancho_cm)}x{int(alto_cm)}cm_{dpi}dpi.png"
        lienzo.save(png, dpi=(dpi, dpi))
        prev = OUT / f"{base}_PREVIEW.jpg"
        lienzo.resize((W // 3, H // 3)).save(prev, quality=85)
        # PDF a escala real
        pdf = OUT / f"{base}_LISTO.pdf"
        try:
            from reportlab.pdfgen import canvas as rc
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm as CM
            if hoja.upper() == "A4":
                c = rc.Canvas(str(pdf), pagesize=A4); pw, ph = A4
                px = (pw - ancho_cm * CM) / 2; py = ph - 1 * CM - alto_cm * CM
            else:
                c = rc.Canvas(str(pdf), pagesize=(ancho_cm * CM, alto_cm * CM)); px, py = 0, 0
            c.drawImage(imagen, px, py, width=ancho_cm * CM, height=alto_cm * CM,
                        preserveAspectRatio=True, anchor="c", mask="auto")
            c.save()
        except Exception as e:
            pdf = None
        return {"status": "OK", "png": str(png), "pdf": (str(pdf) if pdf else None),
                "preview": str(prev), "medida": f"{ancho_cm}x{alto_cm}cm @ {dpi}DPI ({hoja})"}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}
