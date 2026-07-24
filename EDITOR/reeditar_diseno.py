# -*- coding: utf-8 -*-
"""
AURORA · REEDITAR DISEÑO  (Función #2 del Editor/Conversor — modo Premium ligero)

Toma un PDF de cliente (como la lona) y permite:
  A. ANALIZAR   → inventario real: páginas, textos (fuente/tamaño/color/posición), imágenes, medidas.
  B. EXTRAER    → separa a una carpeta: fondo renderizado + cada imagen embebida + manifiesto de textos.
  C. REALZAR    → mejora una foto SIN IA pesada: LANCZOS + máscara de nitidez + contraste/color suave.
  D. REESCALAR  → lleva la página a una medida FÍSICA nueva (cm@DPI) con fidelidad total de fuentes
                  (PyMuPDF re-rasteriza el PDF original → respeta tipografía y layout) + realce opcional.

Sin simulación: todo con PyMuPDF (fitz) + Pillow, ambos ya instalados. Corre en la laptop sin GPU.
Real-ESRGAN (super-resolución IA) queda como upgrade OPCIONAL futuro; aquí no se usa.
"""
from __future__ import annotations
from pathlib import Path
import json
import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance

CM_POR_PULGADA = 2.54
MAX_MEGAPIXELES = 200  # guarda de memoria: >200MP se rechaza y se sugiere bajar DPI (regla lona de Anuar)


def _cm_a_px(cm: float, dpi: int) -> int:
    return round(cm / CM_POR_PULGADA * dpi)


def _px_a_cm(px: int, dpi: int) -> float:
    return round(px / dpi * CM_POR_PULGADA, 2)


def _hex_color(srgb_int: int) -> str:
    """fitz da el color como entero sRGB → '#rrggbb'."""
    try:
        return "#{:06x}".format(int(srgb_int) & 0xFFFFFF)
    except Exception:
        return "#000000"


def _dir_salida(pdf: str, sufijo: str) -> Path:
    p = Path(pdf)
    d = p.with_name(f"{p.stem}_{sufijo}")
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── A. ANALIZAR ──────────────────────────────────────────────────────────
def analizar_pdf(pdf: str, pagina: int = -1) -> dict:
    """Inventario real de un PDF: qué trae dentro para decidir cómo reeditarlo.
    pagina=-1 → resume TODAS; si das una, detalla textos e imágenes de esa página."""
    try:
        doc = fitz.open(pdf)
    except Exception as e:
        return {"status": "error", "mensaje": f"No pude abrir el PDF: {e}"}
    with doc:
        n = doc.page_count
        paginas = []
        for i in range(n):
            pg = doc[i]
            r = pg.rect
            paginas.append({
                "pagina": i,
                "ancho_cm": _px_a_cm(r.width, 72), "alto_cm": _px_a_cm(r.height, 72),
                "orientacion": "horizontal" if r.width >= r.height else "vertical",
                "textos": len([b for b in pg.get_text("dict")["blocks"] if b.get("type") == 0]),
                "imagenes": len(pg.get_images(full=True)),
            })
        detalle = None
        if 0 <= pagina < n:
            detalle = _detalle_pagina(doc[pagina])
        return {"status": "ok", "archivo": Path(pdf).name, "paginas_total": n,
                "paginas": paginas, "detalle_pagina": detalle}


def _detalle_pagina(pg) -> dict:
    textos, fuentes = [], {}
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b.get("lines", []):
            for sp in ln.get("spans", []):
                t = (sp.get("text") or "").strip()
                if not t:
                    continue
                f = sp.get("font", "?")
                fuentes[f] = fuentes.get(f, 0) + 1
                textos.append({
                    "texto": t[:80], "fuente": f,
                    "tamano_pt": round(sp.get("size", 0), 1),
                    "color": _hex_color(sp.get("color", 0)),
                    "pos": [round(v, 1) for v in sp.get("bbox", (0, 0, 0, 0))],
                })
    imgs = []
    for idx, im in enumerate(pg.get_images(full=True)):
        imgs.append({"n": idx, "ancho_px": im[2], "alto_px": im[3]})
    return {"fuentes_usadas": fuentes, "textos": textos[:60], "textos_total": len(textos),
            "imagenes": imgs}


# ── B. EXTRAER ───────────────────────────────────────────────────────────
def extraer_elementos(pdf: str, pagina: int = 0, dpi: int = 300, out_dir: str = "") -> dict:
    """Separa una página en piezas reales dentro de una carpeta:
       fondo_render.png + imagen_NN.ext (cada foto embebida) + textos.json (fuente/tam/color/pos)."""
    try:
        doc = fitz.open(pdf)
    except Exception as e:
        return {"status": "error", "mensaje": f"No pude abrir el PDF: {e}"}
    with doc:
        if not (0 <= pagina < doc.page_count):
            return {"status": "error", "mensaje": f"La página {pagina} no existe (0..{doc.page_count-1})."}
        pg = doc[pagina]
        carpeta = Path(out_dir) if out_dir else _dir_salida(pdf, f"partes_p{pagina}")
        carpeta.mkdir(parents=True, exist_ok=True)

        # fondo: render completo de la página a la resolución pedida
        pix = pg.get_pixmap(dpi=dpi)
        fondo = carpeta / "fondo_render.png"
        pix.save(str(fondo))

        # imágenes embebidas (las fotos reales, sin recomprimir)
        imgs_out = []
        vistos = set()
        for idx, im in enumerate(pg.get_images(full=True)):
            xref = im[0]
            if xref in vistos:
                continue
            vistos.add(xref)
            try:
                base = doc.extract_image(xref)
                ext = base.get("ext", "png")
                f = carpeta / f"imagen_{idx:02d}.{ext}"
                f.write_bytes(base["image"])
                imgs_out.append({"archivo": f.name, "px": f"{base.get('width')}x{base.get('height')}"})
            except Exception:
                continue

        # manifiesto de textos (para respetar tipografía al reacomodar a mano)
        det = _detalle_pagina(pg)
        (carpeta / "textos.json").write_text(
            json.dumps({"fuentes": det["fuentes_usadas"], "textos": det["textos"]},
                       ensure_ascii=False, indent=2), encoding="utf-8")

        return {"status": "ok", "carpeta": str(carpeta),
                "fondo": fondo.name, "imagenes": imgs_out,
                "textos_total": det["textos_total"], "fuentes": det["fuentes_usadas"],
                "nota": "fondo_render.png = la página completa; imagen_NN = fotos sueltas; "
                        "textos.json = qué fuente/tamaño/color usar para recomponer."}


# ── C. REALZAR FOTO (sin IA pesada) ──────────────────────────────────────
def realzar_foto(imagen: str, factor: float = 2.0, nitidez: bool = True,
                 contraste: float = 1.05, color: float = 1.05, salida: str = "") -> dict:
    """Mejora una foto para ampliarla: LANCZOS (factor×) + máscara de nitidez + realce suave.
    Honesto: NO inventa detalle como la IA; recupera nitidez percibida y evita el look 'lavado'
    del simple estirado. Ideal para logos/fotos que se van a ver a media/larga distancia."""
    try:
        img = Image.open(imagen)
    except Exception as e:
        return {"status": "error", "mensaje": f"No pude abrir la imagen: {e}"}
    modo_orig = img.mode
    img = img.convert("RGBA") if modo_orig in ("RGBA", "LA", "P") else img.convert("RGB")
    w0, h0 = img.size
    if factor and factor != 1.0:
        img = img.resize((max(1, round(w0 * factor)), max(1, round(h0 * factor))), Image.LANCZOS)
    if nitidez:
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    if contraste and contraste != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contraste)
    if color and color != 1.0 and img.mode in ("RGB", "RGBA"):
        img = ImageEnhance.Color(img).enhance(color)
    if not salida:
        p = Path(imagen)
        salida = str(p.with_name(f"{p.stem}_realzada.png"))
    img.save(salida)
    return {"status": "ok", "salida": salida,
            "px_original": f"{w0}x{h0}", "px_nuevo": f"{img.width}x{img.height}",
            "factor": factor,
            "nota": "Realce ligero (sin IA). Para máxima nitidez de cerca en ampliaciones grandes, "
                    "un futuro modo IA (Real-ESRGAN) daría más — no instalado por ahora."}


# ── D. REESCALAR PÁGINA A MEDIDA FÍSICA ──────────────────────────────────
def reescalar_a_medida(pdf: str, ancho_cm: float, alto_cm: float = 0, dpi: int = 150,
                       pagina: int = 0, realzar: bool = True, formato: str = "png",
                       ajuste: str = "proporcion", salida: str = "") -> dict:
    """Lleva una página del PDF a una medida física NUEVA (cm@DPI) re-rasterizando el PDF original
    con PyMuPDF → conserva tipografía y layout EXACTOS. Opcional: realce ligero de nitidez.
    - ajuste 'proporcion' (default): calcula el alto por el ancho (no deforma).
    - ajuste 'estirar': fuerza ancho_cm × alto_cm exactos (puede deformar; avisa).
    Si cambia la relación de aspecto (ej. vertical→horizontal), avisa: mejor extraer y reacomodar.
    """
    try:
        doc = fitz.open(pdf)
    except Exception as e:
        return {"status": "error", "mensaje": f"No pude abrir el PDF: {e}"}
    with doc:
        if not (0 <= pagina < doc.page_count):
            return {"status": "error", "mensaje": f"La página {pagina} no existe (0..{doc.page_count-1})."}
        pg = doc[pagina]
        r = pg.rect
        aspecto_src = r.width / r.height if r.height else 1.0

        dst_w = _cm_a_px(ancho_cm, dpi)
        if alto_cm and ajuste == "estirar":
            dst_h = _cm_a_px(alto_cm, dpi)
        else:
            dst_h = round(dst_w / aspecto_src)  # proporción del PDF

        # guarda de memoria (regla lona: 300dpi@gran formato = desperdicio y revienta RAM)
        mp = (dst_w * dst_h) / 1_000_000
        if mp > MAX_MEGAPIXELES:
            dpi_sug = int(dpi * (MAX_MEGAPIXELES / mp) ** 0.5)
            return {"status": "muy_pesado",
                    "motivo": f"{dst_w}x{dst_h}px = {mp:.0f} MP supera el límite de {MAX_MEGAPIXELES} MP.",
                    "sugerencia": f"Baja el DPI a ~{dpi_sug} (para gran formato/lona 150 DPI es lo correcto)."}

        # aviso de aspecto (vertical↔horizontal se pierde contenido si se estira)
        aviso = None
        if alto_cm and ajuste == "estirar":
            aspecto_dst = _cm_a_px(ancho_cm, dpi) / _cm_a_px(alto_cm, dpi)
            if abs(aspecto_dst - aspecto_src) / aspecto_src > 0.02:
                aviso = ("Cambiaste la relación de aspecto: el estirado deforma. "
                         "Para reencuadre real usa 'extraer' y reacomoda las piezas.")

        # render a un zoom que dé exactamente el ancho destino
        zoom = dst_w / r.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if (img.width, img.height) != (dst_w, dst_h):
            img = img.resize((dst_w, dst_h), Image.LANCZOS)
        if realzar:
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))

        p = Path(pdf)
        fmt = formato.lower()
        if not salida:
            salida = str(p.with_name(f"{p.stem}_p{pagina}_{round(ancho_cm)}x{_px_a_cm(dst_h, dpi):g}cm_{dpi}dpi.{fmt}"))
        if fmt in ("jpg", "jpeg"):
            img.save(salida, dpi=(dpi, dpi), quality=92)
        elif fmt == "pdf":
            img.save(salida, "PDF", resolution=float(dpi))
        else:
            img.save(salida, dpi=(dpi, dpi))

        return {"status": "ok", "salida": salida, "ajuste": ajuste,
                "px": f"{img.width}x{img.height}", "dpi": dpi,
                "tamano_cm": f"{_px_a_cm(img.width, dpi)} x {_px_a_cm(img.height, dpi)}",
                "megapixeles": round(mp, 1), "aviso": aviso,
                "nota": "Fidelidad total de tipografía/layout (re-render del PDF original)."}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(analizar_pdf(sys.argv[1], 0), ensure_ascii=False, indent=2))
