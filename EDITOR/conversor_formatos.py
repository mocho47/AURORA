# -*- coding: utf-8 -*-
"""
AURORA · CONVERSOR DE FORMATOS (Función #1 del Editor/Conversor)
Convierte entre SVG / DXF / PDF / PNG / EPS / PS usando Inkscape 1.4.3 como brazo.
Sin simulación: llama a Inkscape real y verifica que el archivo salga.

HONESTO sobre los límites reales del formato (no del programa):
- CDR (CorelDRAW): solo se IMPORTA. No hay exportador libre → se entrega en SVG/PDF/EPS.
- .studio3 (Silhouette): formato cerrado, NO se exporta. Silhouette importa DXF/SVG.
- Raster → vector (PNG/JPG → SVG/DXF): requiere VECTORIZADO, no una simple conversión.
  Aquí NO se hace a ciegas: se redirige a papercraft_a_dxf (vtracer) para no dar basura.
"""
from __future__ import annotations
import os, subprocess
from pathlib import Path

INKSCAPE = r"C:\Program Files\Inkscape\bin\inkscape.exe"

RASTER = {"png", "jpg", "jpeg", "bmp", "tif", "tiff", "webp", "gif"}
# Entradas que Inkscape sabe abrir (vector + import-only como cdr)
IMPORTABLES = {"svg", "svgz", "pdf", "eps", "ps", "ai", "cdr", "dxf", "emf", "wmf"} | RASTER
# Salidas que Inkscape sabe exportar
EXPORTABLES = {"svg", "png", "pdf", "eps", "ps", "dxf", "emf", "wmf"}
# Destinos imposibles con explicación honesta (por qué + qué entregar)
NO_EXPORTA = {
    "cdr": "CorelDRAW no tiene exportador libre. Inkscape solo IMPORTA .cdr. "
           "Entrega en SVG/PDF/EPS (Corel los abre y edita).",
    "studio3": "Silhouette Studio (.studio3) es formato cerrado: NO se exporta. "
               "Silhouette IMPORTA DXF/SVG → entrega en DXF o SVG.",
    "ai": "Illustrator .ai no tiene exportador libre fiable. "
          "Entrega en PDF/EPS/SVG (Illustrator los abre).",
}


def _ext(ruta: str) -> str:
    return Path(ruta).suffix.lower().lstrip(".")


def paginas_pdf(pdf: str) -> int:
    """Número de páginas de un PDF (para conversión por lote)."""
    import fitz
    d = fitz.open(pdf)
    try:
        return d.page_count
    finally:
        d.close()


def formatos() -> dict:
    """Qué puede convertir el módulo (para el panel). Transparente con los límites."""
    return {
        "status": "ok",
        "entradas": sorted(IMPORTABLES),
        "salidas": sorted(EXPORTABLES),
        "limites": {k: v for k, v in NO_EXPORTA.items()},
        "nota_raster_a_vector": "PNG/JPG → SVG/DXF requiere vectorizar (usa papercraft_a_dxf).",
    }


def convertir(entrada: str, a: str, salida: str = "", dpi: int = 300,
              pagina: int | None = None) -> dict:
    """
    Convierte 'entrada' al formato 'a' (svg/png/pdf/dxf/eps/ps).
    - dpi: resolución al rasterizar a PNG (300 sublimación, 150 lona gran formato).
    - pagina: para PDF multipágina, índice 0-based de la página a convertir.
              None = página 1. Para convertir TODAS usa convertir_todo().
    Devuelve rutas reales verificadas en disco, sin inventar éxito.
    """
    src = Path(entrada)
    if not src.exists():
        return {"status": "error", "mensaje": f"No existe el archivo: {entrada}"}

    ext = _ext(entrada)
    dst = a.lower().lstrip(".")

    # 1) Rechazos honestos por el formato destino
    if dst in NO_EXPORTA:
        return {"status": "no_soportado", "destino": dst, "motivo": NO_EXPORTA[dst]}
    if dst not in EXPORTABLES:
        return {"status": "error",
                "mensaje": f"Destino '{dst}' no soportado. Válidos: {sorted(EXPORTABLES)}"}
    if ext not in IMPORTABLES:
        return {"status": "error",
                "mensaje": f"Entrada '{ext}' no reconocida. Válidas: {sorted(IMPORTABLES)}"}

    # 2) Raster → vector: no se hace a ciegas, se redirige al vectorizador
    if ext in RASTER and dst in {"svg", "dxf"}:
        return {"status": "requiere_vectorizado",
                "motivo": f"{ext.upper()} → {dst.upper()} no es una conversión directa: "
                          "una imagen no tiene vectores. Hay que VECTORIZAR.",
                "usar": "papercraft_a_dxf (vtracer) o el flujo B&N→Aspire para calidad de corte."}

    # 3) Salida por defecto
    if not salida:
        sufijo = f"_p{pagina+1}" if (ext == "pdf" and pagina is not None) else ""
        salida = str(src.with_name(f"{src.stem}{sufijo}.{dst}"))

    # 4) Comando Inkscape real
    cmd = [INKSCAPE, str(src), "--export-type=" + dst, f"--export-filename={salida}"]
    if ext == "pdf" and pagina is not None:
        cmd.insert(2, f"--pages={pagina+1}")   # Inkscape 1.4.3: --pages, no --pdf-page (1-based)
    if dst == "png":
        cmd.append(f"--export-dpi={dpi}")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"status": "error", "mensaje": "Inkscape tardó demasiado (>180s)."}

    if not os.path.exists(salida) or os.path.getsize(salida) == 0:
        err = (r.stderr or r.stdout or "sin detalle").strip()[:300]
        return {"status": "error", "mensaje": f"Inkscape no generó el archivo. {err}"}

    out = {"status": "ok", "salida": salida, "de": ext, "a": dst,
           "mb": round(os.path.getsize(salida) / 1048576, 3)}
    if dst == "png":
        out["dpi"] = dpi
    if dst == "dxf":
        out["nota"] = "DXF de vectores reales (limpio). Si venía de raster, no aplica: vectoriza aparte."
    return out


def convertir_todo(pdf: str, a: str, dpi: int = 300, carpeta: str = "") -> dict:
    """PDF multipágina → un archivo por página (lote). Ideal SVG/PNG para reeditar/imprimir."""
    if _ext(pdf) != "pdf":
        return {"status": "error", "mensaje": "convertir_todo es solo para PDF multipágina."}
    n = paginas_pdf(pdf)
    base = Path(carpeta) if carpeta else Path(pdf).parent
    base.mkdir(parents=True, exist_ok=True)
    stem = Path(pdf).stem
    resultados = []
    for i in range(n):
        salida = str(base / f"{stem}_p{i+1}.{a.lower().lstrip('.')}")
        resultados.append(convertir(pdf, a, salida=salida, dpi=dpi, pagina=i))
    ok = sum(1 for r in resultados if r.get("status") == "ok")
    return {"status": "ok" if ok == n else "parcial", "paginas": n, "convertidas": ok,
            "archivos": [r.get("salida") for r in resultados if r.get("status") == "ok"],
            "detalle": resultados}
