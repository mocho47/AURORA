# -*- coding: utf-8 -*-
"""
AURORA · ESCALAS / DPI / PLANILLAS  (Función #5 del Editor/Conversor + Modo Rápido)
Medidas físicas REALES: convierte entre cm ↔ px según DPI y arma planillas listas
para imprimir/sublimar/cortar. Sin simulación: usa Pillow y verifica el resultado.

Modo Rápido (lo que Anuar hace en LibreOffice cuando el cliente no paga diseño):
estirar suave a la medida con interpolación LANCZOS → queda soft pero SIN pixeleo;
en gran formato, visto a distancia, se ve bien. Es válido y correcto.

DPI de referencia (regla de Anuar):
- Sublimación / corte fino: 300 DPI.
- Lona / gran formato: 150 DPI (300 es desperdicio, se ve a distancia).
"""
from __future__ import annotations
import os
from pathlib import Path
from PIL import Image

CM_POR_PULGADA = 2.54

# Formatos de papel estándar en cm (ancho, alto) en vertical
FORMATOS = {
    "A4":        (21.0, 29.7),
    "A3":        (29.7, 42.0),
    "carta":     (21.59, 27.94),
    "oficio":    (21.59, 33.02),
    "tabloide":  (27.94, 43.18),   # Ledger 11x17"
    "gran_formato": (200.0, 100.0),  # rollo típico taller (editable con formato_cm)
}


def cm_a_px(cm: float, dpi: int) -> int:
    return round(cm / CM_POR_PULGADA * dpi)


def px_a_cm(px: int, dpi: int) -> float:
    return round(px / dpi * CM_POR_PULGADA, 2)


def formatos_papel() -> dict:
    """Lista de formatos disponibles (para el panel)."""
    return {"status": "ok",
            "formatos": {k: {"ancho_cm": v[0], "alto_cm": v[1]} for k, v in FORMATOS.items()},
            "dpi_recomendado": {"sublimacion_corte": 300, "lona_gran_formato": 150}}


def info_dpi(imagen: str, dpi_asumido: int = 0) -> dict:
    """Reporta tamaño en px, DPI embebido y el tamaño físico real al que imprimiría."""
    img = Image.open(imagen)
    dpi_emb = img.info.get("dpi", (0, 0))
    dpi = dpi_asumido or (int(dpi_emb[0]) if dpi_emb and dpi_emb[0] else 0)
    r = {"status": "ok", "px": f"{img.width}x{img.height}",
         "dpi_embebido": int(dpi_emb[0]) if dpi_emb and dpi_emb[0] else None}
    if dpi:
        r["tamano_fisico_cm"] = f"{px_a_cm(img.width, dpi)} x {px_a_cm(img.height, dpi)}"
        r["dpi_usado"] = dpi
    else:
        r["aviso"] = "La imagen no trae DPI. Pásame dpi_asumido para calcular el tamaño físico."
    return r


def fijar_dpi(imagen: str, dpi: int, salida: str = "") -> dict:
    """Cambia SOLO el DPI embebido (no remuestrea): ajusta el tamaño de impresión sin tocar píxeles."""
    img = Image.open(imagen)
    if not salida:
        p = Path(imagen); salida = str(p.with_name(f"{p.stem}_{dpi}dpi{p.suffix}"))
    img.save(salida, dpi=(dpi, dpi))
    return {"status": "ok", "salida": salida, "dpi": dpi,
            "tamano_fisico_cm": f"{px_a_cm(img.width, dpi)} x {px_a_cm(img.height, dpi)}",
            "nota": "Mismos píxeles, distinto tamaño impreso. No mejora resolución."}


def escalar_a_medida(imagen: str, ancho_cm: float, alto_cm: float = 0, dpi: int = 300,
                     modo: str = "rapido", mantener_proporcion: bool = True,
                     salida: str = "") -> dict:
    """
    Lleva una imagen a una medida FÍSICA real (cm) a un DPI dado.
    - modo 'rapido': interpolación LANCZOS (suave, sin pixeleo) = escalado de producción.
    - mantener_proporcion: si alto_cm=0 lo calcula del aspecto; si das ambos y esto es
      True, encaja dentro sin deformar; si es False, ESTIRA a la medida exacta (Anuar-LibreOffice).
    """
    img = Image.open(imagen).convert("RGBA") if imagen.lower().endswith(".png") \
        else Image.open(imagen).convert("RGB")
    dst_w = cm_a_px(ancho_cm, dpi)
    if alto_cm and not mantener_proporcion:
        dst_h = cm_a_px(alto_cm, dpi)                       # estirar exacto
    elif alto_cm and mantener_proporcion:
        # encajar dentro del rectángulo destino sin deformar
        dst_h = cm_a_px(alto_cm, dpi)
        escala = min(dst_w / img.width, dst_h / img.height)
        dst_w, dst_h = round(img.width * escala), round(img.height * escala)
    else:
        dst_h = round(img.height * (dst_w / img.width))    # proporción por ancho

    remuestreo = Image.LANCZOS   # suave, calidad de producción
    nueva = img.resize((max(1, dst_w), max(1, dst_h)), remuestreo)
    if not salida:
        p = Path(imagen)
        salida = str(p.with_name(f"{p.stem}_{round(ancho_cm)}x{px_a_cm(dst_h, dpi):g}cm.png"))
    nueva.save(salida, dpi=(dpi, dpi))
    ampliando = dst_w > img.width
    return {"status": "ok", "salida": salida, "modo": modo,
            "px": f"{nueva.width}x{nueva.height}", "dpi": dpi,
            "tamano_cm": f"{px_a_cm(nueva.width, dpi)} x {px_a_cm(nueva.height, dpi)}",
            "aviso": ("Ampliación: en modo Rápido queda suave pero sin pixeleo (ok a distancia). "
                      "Para calidad de cerca usa modo Premium con IA." if ampliando else None)}


def generar_planilla(imagen: str, item_ancho_cm: float, item_alto_cm: float = 0,
                     formato: str = "A4", dpi: int = 300, margen_cm: float = 1.0,
                     gap_cm: float = 0.5, orientacion: str = "vertical",
                     formato_cm: tuple = (), fondo: str = "white", salida: str = "") -> dict:
    """
    Imposición: llena una hoja con copias de un ítem a medida física exacta.
    Ideal para stickers/sublimación/etiquetas. Devuelve cuántas copias caben y el archivo.
    - formato: A4/A3/carta/oficio/tabloide/gran_formato, o pasa formato_cm=(ancho,alto).
    """
    if formato_cm:
        hoja_w_cm, hoja_h_cm = formato_cm
    elif formato in FORMATOS:
        hoja_w_cm, hoja_h_cm = FORMATOS[formato]
    else:
        return {"status": "error", "mensaje": f"Formato '{formato}' desconocido. {list(FORMATOS)}"}
    if orientacion == "horizontal":
        hoja_w_cm, hoja_h_cm = hoja_h_cm, hoja_w_cm

    src = Image.open(imagen).convert("RGBA")
    # ítem a medida física
    item_w = cm_a_px(item_ancho_cm, dpi)
    if item_alto_cm:
        item_h = cm_a_px(item_alto_cm, dpi)
    else:
        item_h = round(src.height * (item_w / src.width))
    item = src.resize((max(1, item_w), max(1, item_h)), Image.LANCZOS)

    hoja_w, hoja_h = cm_a_px(hoja_w_cm, dpi), cm_a_px(hoja_h_cm, dpi)
    margen, gap = cm_a_px(margen_cm, dpi), cm_a_px(gap_cm, dpi)

    util_w, util_h = hoja_w - 2 * margen, hoja_h - 2 * margen
    cols = max(0, (util_w + gap) // (item_w + gap))
    filas = max(0, (util_h + gap) // (item_h + gap))
    total = int(cols * filas)
    if total == 0:
        return {"status": "no_cabe",
                "motivo": f"El ítem ({item_ancho_cm}cm) no cabe en {formato} con margen {margen_cm}cm.",
                "hoja_cm": f"{hoja_w_cm}x{hoja_h_cm}"}

    hoja = Image.new("RGBA", (hoja_w, hoja_h), fondo)
    for r in range(int(filas)):
        for c in range(int(cols)):
            x = margen + c * (item_w + gap)
            y = margen + r * (item_h + gap)
            hoja.paste(item, (x, y), item if item.mode == "RGBA" else None)

    if not salida:
        p = Path(imagen)
        salida = str(p.with_name(f"{p.stem}_planilla_{formato}_{int(cols)}x{int(filas)}.png"))
    hoja.convert("RGB").save(salida, dpi=(dpi, dpi))
    return {"status": "ok", "salida": salida, "copias": total,
            "grid": f"{int(cols)} x {int(filas)}", "formato": formato,
            "hoja_cm": f"{hoja_w_cm} x {hoja_h_cm}", "item_cm": f"{item_ancho_cm} x {px_a_cm(item_h, dpi)}",
            "dpi": dpi, "px": f"{hoja_w}x{hoja_h}"}
