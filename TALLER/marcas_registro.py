# -*- coding: utf-8 -*-
"""AURORA · Las marcas de registro de la Cameo 4 de Anuar (Print & Cut)

MEDIDAS REALES, no de manual. Salieron de un archivo que él exportó de su
propio Silhouette Studio el 2026-08-07, después de una tarde entera en que
las marcas de Corel no registraron ni una vez.

Esa es la lección que hay detrás: **Corel pone marcas de imprenta —cuatro
cruces simétricas para alinear planchas de offset— y Silhouette busca otra
cosa: un cuadro relleno y dos escuadras en L, asimétricas a propósito para
saber cómo está orientada la hoja.** No hay medida de página que las haga
coincidir. La máquina lo confirmó: "no registraba".

Con esto AURORA arma hojas listas para imprimir y cortar: acomoda las piezas
dentro del área útil y pone las marcas donde su Cameo las busca.

Correr:  python TALLER/marcas_registro.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# ── LO MEDIDO EN SU MÁQUINA (A4, Cameo 4, Silhouette Business Edition) ──
MARGEN_MM = 15.6          # de cada orilla de la hoja hasta la marca
CUADRO_MM = 5.5           # el cuadro relleno de arriba-izquierda
ESCUADRA_MM = 20.2        # el largo del brazo de cada escuadra en L
TRAZO_MM = 0.47           # grosor de la línea de las escuadras

# Cuánto separar el dibujo de las marcas. Si una figura queda pegada, el
# sensor la confunde con la marca y no registra.
AIRE_MM = 2.0


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def marcas(ancho_mm: float = 210.0, alto_mm: float = 297.0) -> dict:
    """Dónde van las tres marcas en una hoja de este tamaño."""
    m = MARGEN_MM
    return {
        "cuadro": {"x": m, "y": m, "w": CUADRO_MM, "h": CUADRO_MM},
        "escuadra_arriba_derecha": {
            "x": ancho_mm - m - ESCUADRA_MM, "y": m,
            "w": ESCUADRA_MM, "h": ESCUADRA_MM},
        "escuadra_abajo_izquierda": {
            "x": m, "y": alto_mm - m - ESCUADRA_MM,
            "w": ESCUADRA_MM, "h": ESCUADRA_MM},
    }


def area_util(ancho_mm: float = 210.0, alto_mm: float = 297.0) -> dict:
    """El rectángulo donde SÍ se puede poner dibujo, esquivando las marcas.

    Se toma el borde de la marca más adentro en cada lado, más el aire.
    En A4 son 151 × 238 mm — lo demás lo ocupan las marcas y su respiro.
    """
    m = MARGEN_MM
    x0 = m + CUADRO_MM + AIRE_MM
    y0 = m + CUADRO_MM + AIRE_MM
    x1 = ancho_mm - m - ESCUADRA_MM - AIRE_MM
    y1 = alto_mm - m - ESCUADRA_MM - AIRE_MM
    return {"x": round(x0, 1), "y": round(y0, 1),
            "ancho": round(x1 - x0, 1), "alto": round(y1 - y0, 1),
            "hasta_x": round(x1, 1), "hasta_y": round(y1, 1)}


def cabe(pieza_ancho: float, pieza_alto: float, separacion: float = 3.0,
         ancho_mm: float = 210.0, alto_mm: float = 297.0) -> dict:
    """Cuántas piezas de ese tamaño caben en una hoja, con sus marcas."""
    u = area_util(ancho_mm, alto_mm)
    cols = int((u["ancho"] + separacion) // (pieza_ancho + separacion))
    filas = int((u["alto"] + separacion) // (pieza_alto + separacion))
    return {"columnas": max(0, cols), "filas": max(0, filas),
            "total": max(0, cols * filas), "area_util": u}


def _texto() -> str:
    u = area_util()
    m = marcas()
    s = [f"📐 **Marcas de registro de tu Cameo 4** — medidas de tu archivo\n",
         f"Hoja A4 · margen de **{MARGEN_MM} mm** en las cuatro orillas\n"]
    s.append(f"   • Cuadro relleno arriba-izquierda: {CUADRO_MM} × {CUADRO_MM} mm")
    s.append(f"   • Escuadra en L arriba-derecha: {ESCUADRA_MM} × {ESCUADRA_MM} mm")
    s.append(f"   • Escuadra en L abajo-izquierda: {ESCUADRA_MM} × {ESCUADRA_MM} mm")
    s.append(f"   • Grosor del trazo: {TRAZO_MM} mm\n")
    s.append(f"**Área útil: {u['ancho']} × {u['alto']} mm** "
             f"(de X {u['x']} a {u['hasta_x']}, de Y {u['y']} a {u['hasta_y']})\n")
    s.append("Cuántas piezas caben:")
    for w, h, nom in ((27, 60, "etiquetas 2.7 × 6"), (50, 50, "de 5 × 5"),
                      (40, 90, "de 4 × 9"), (30, 30, "calcomanías de 3 × 3")):
        c = cabe(w, h)
        s.append(f"   • {nom}: **{c['total']}** "
                 f"({c['columnas']} × {c['filas']})")
    s.append("\n_Corel pone marcas de imprenta, no de Silhouette. No hay "
             "medida de página que las haga coincidir — ya se comprobó en la "
             "máquina._")
    return "\n".join(s)


def main() -> int:
    _consola_utf8()
    print(_texto())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
