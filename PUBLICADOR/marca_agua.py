# -*- coding: utf-8 -*-
"""
AURORA · MARCA DE AGUA PARA TODO LO QUE SE PUBLICA
=============================================================================
Pedido de Anuar el 2026-08-26, textual:

    "que publique con lo que tiene en env, ya sea que genere marcas de agua
     en todas para que no haya bronca"

El contexto: la cuenta de Instagram que hay en el .env (`rauna_892`) es su
cuenta personal. Poniéndole la marca del negocio a CADA imagen, lo que se sube
queda identificado como de ATF (o de Milens) aunque salga por una cuenta
personal. Eso es "que no haya bronca".

POR QUÉ ESTE ARCHIVO Y NO OTRO
---------------------------------------------------------------------------
Se buscó primero en todo el proyecto: NO existía ningún módulo de marcas de
agua. Lo único que había eran tres frases de consejo en `MARKETING/asesor_core.py`
("sin marca de agua de TikTok"), que son texto para el humano, no código.
Así que este módulo es nuevo de verdad, no un gemelo.

LOS DATOS DE LA MARCA NO SE ESCRIBEN AQUÍ
---------------------------------------------------------------------------
El nombre y el teléfono se leen de `CONFIG/negocios.json`, que es donde Anuar
ya los tiene en un solo lugar. Ese archivo existe precisamente porque el
teléfono estaba copiado en tres módulos y 175 reels salieron con un número
viejo. No se repite ese error aquí.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
NEGOCIOS = RAIZ / "CONFIG" / "negocios.json"

# Fuentes de Windows, de la más a la menos deseable. Si no hay ninguna se usa
# la de Pillow (se ve pobre pero NUNCA deja de poner la marca: una imagen sin
# marca es justo lo que Anuar no quiere que salga).
_FUENTES = ("arialbd.ttf", "seguibl.ttf", "segoeuib.ttf", "arial.ttf", "calibrib.ttf")


def _datos_negocio(negocio: str) -> dict:
    """Nombre y teléfono del negocio, leídos de donde Anuar los mantiene."""
    try:
        d = json.loads(NEGOCIOS.read_text(encoding="utf-8"))
        n = (d.get("negocios") or {}).get((negocio or "atf").lower()) or {}
        return {"nombre": n.get("nombre", ""), "telefono": n.get("telefono", "")}
    except Exception:
        return {"nombre": "", "telefono": ""}


def _fuente(px: int):
    for nombre in _FUENTES:
        try:
            return ImageFont.truetype(nombre, px)
        except Exception:
            continue
    return ImageFont.load_default()


def _texto_marca(negocio: str, texto: str | None) -> str:
    """La línea que va sobre la imagen. Si no se le da texto, se arma con los
    datos reales del negocio. Si el JSON no se pudo leer, se dice — no se
    inventa un teléfono, que es exactamente el error de los 175 reels."""
    if texto:
        return texto
    d = _datos_negocio(negocio)
    if d["nombre"] and d["telefono"]:
        return f"{d['nombre']}  ·  WhatsApp {d['telefono']}"
    return d["nombre"] or ""


def poner_marca(entrada: str, salida: str = "", negocio: str = "atf",
                texto: str = "", opacidad: int = 165) -> dict:
    """Le pone la marca del negocio a UNA imagen. Devuelve la ruta del archivo
    nuevo (nunca pisa el original de Anuar).

    La marca es una banda oscura translúcida abajo con el nombre y el teléfono.
    Se escala con la imagen, así que se ve igual en una foto de 800 px que en
    una de 4000.
    """
    ruta = Path(entrada)
    if not ruta.is_file():
        return {"status": "ERROR", "detalle": f"No existe la imagen: {entrada}"}

    marca = _texto_marca(negocio, texto)
    if not marca:
        return {"status": "ERROR",
                "detalle": "No pude leer el nombre ni el teléfono del negocio en "
                           "CONFIG/negocios.json. No le pongo una marca inventada."}

    try:
        img = Image.open(ruta)
        img = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude abrir la imagen: {str(e)[:150]}"}

    ancho, alto = img.size
    # Todo proporcional al ancho: la marca se ve igual en cualquier tamaño.
    px = max(14, int(ancho * 0.032))
    margen = max(8, int(ancho * 0.018))
    fuente = _fuente(px)

    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dib = ImageDraw.Draw(capa)
    x0, y0, x1, y1 = dib.textbbox((0, 0), marca, font=fuente)
    ancho_txt, alto_txt = x1 - x0, y1 - y0
    alto_banda = alto_txt + margen * 2

    # Banda de lado a lado, pegada abajo.
    dib.rectangle([(0, alto - alto_banda), (ancho, alto)],
                  fill=(0, 0, 0, max(0, min(255, opacidad))))
    tx = (ancho - ancho_txt) // 2
    ty = alto - alto_banda + margen - y0
    # Sombra + texto: legible sobre cualquier foto, clara u oscura.
    dib.text((tx + 2, ty + 2), marca, font=fuente, fill=(0, 0, 0, 200))
    dib.text((tx, ty), marca, font=fuente, fill=(255, 255, 255, 255))

    final = Image.alpha_composite(img, capa).convert("RGB")

    if salida:
        destino = Path(salida)
    else:
        destino = ruta.with_name(f"{ruta.stem}_marca.jpg")
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        # JPEG de calidad alta: Instagram recomprime igual, y así el archivo
        # que se sube pesa poco (la subida por celular de Anuar es lenta).
        final.save(destino, "JPEG", quality=92, optimize=True)
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude guardar: {str(e)[:150]}"}

    return {"status": "OK", "ruta": str(destino), "marca": marca,
            "medidas": f"{ancho}x{alto}", "bytes": destino.stat().st_size}


def poner_marca_a_todas(carpeta: str, negocio: str = "atf",
                        salida_dir: str = "") -> dict:
    """La misma marca a todas las imágenes de una carpeta. Es lo que pidió
    Anuar: 'marcas de agua en TODAS'."""
    origen = Path(carpeta)
    if not origen.is_dir():
        return {"status": "ERROR", "detalle": f"No existe la carpeta: {carpeta}"}
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    hechas, fallidas = [], []
    for f in sorted(origen.iterdir()):
        if f.suffix.lower() not in exts or f.stem.endswith("_marca"):
            continue
        destino = str(Path(salida_dir) / f"{f.stem}_marca.jpg") if salida_dir else ""
        r = poner_marca(str(f), destino, negocio)
        (hechas if r["status"] == "OK" else fallidas).append(
            r.get("ruta") or f"{f.name}: {r.get('detalle')}")
    return {"status": "OK", "total": len(hechas), "marcadas": hechas,
            "fallidas": fallidas}
