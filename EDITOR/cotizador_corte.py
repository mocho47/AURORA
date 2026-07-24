# -*- coding: utf-8 -*-
"""
AURORA · COTIZADOR DE CORTE POR DXF (Milens)
Lee un DXF, calcula la LONGITUD REAL de corte, el tiempo, el costo por minuto
y el material — con los precios REALES de Anuar (precios_base.json). Cero invento.
Adaptado (lógica, no copia) del concepto de Dessina DXF calculator, para MDF/acrílico.
"""
from __future__ import annotations
import json
import math
import unicodedata
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bbox

ROOT = Path(__file__).resolve().parent.parent
PRECIOS = ROOT / "CONFIG" / "precios_base.json"


def _norm(s: str) -> str:
    s = (s or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _cargar_laser() -> dict:
    try:
        return json.loads(PRECIOS.read_text(encoding="utf-8")).get("laser", {})
    except Exception:
        return {"costo_minuto": 8.0, "materiales": []}


def _long_entidad(e) -> float:
    """Longitud de corte de una entidad, en unidades del DXF (mm)."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return math.dist((a.x, a.y), (b.x, b.y))
        if t == "CIRCLE":
            return 2 * math.pi * e.dxf.radius
        if t == "ARC":
            # barrido CCW real (DXF siempre es antihorario); % de Python normaliza negativos.
            # NO usar abs() antes del %: rompería arcos que cruzan 0° (p.ej. 350°→10° = 20°).
            ang = (e.dxf.end_angle - e.dxf.start_angle) % 360
            return math.radians(ang) * e.dxf.radius
        if t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            if getattr(e, "closed", False) and len(pts) > 2:
                pts.append(pts[0])
            return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        if t == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        if t == "SPLINE":
            pts = [(p[0], p[1]) for p in e.flattening(distance=0.2)]
            return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        if t == "ELLIPSE":
            pts = [(p.x, p.y) for p in e.flattening(distance=0.2)]
            return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    except Exception:
        return 0.0
    return 0.0


def cotizar_corte(ruta: str, material: str = "", velocidad_mm_s: float = 15.0,
                  margen_pct: float = 30.0, cortar_recuadro: bool = True,
                  merma_pct: float = 0.0) -> dict:
    """
    Cotiza corte láser desde un DXF con precios reales de Milens.
    - velocidad_mm_s: velocidad de corte (Anuar pone la suya).
    - cortar_recuadro: suma los mm del perímetro del recuadro X×Y al corte.
    - merma_pct: desperdicio EXTRA sobre el material (acomodo/sobrante entre trabajos).
    DESPERDICIO: el material se cobra por el RECUADRO X×Y completo (lo que de verdad
    consumes de la hoja), así el sobrante alrededor de las piezas YA queda cobrado.
    """
    p = Path(ruta)
    if not p.exists():
        return {"status": "error", "mensaje": f"No existe: {ruta}"}
    try:
        doc = ezdxf.readfile(ruta)
    except Exception as e:
        return {"status": "error", "mensaje": f"No se pudo leer el DXF: {e}"}
    msp = doc.modelspace()

    long_piezas_mm = 0.0
    piezas = 0
    for e in msp:
        long_piezas_mm += _long_entidad(e)
        if e.dxftype() in ("CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE", "ELLIPSE"):
            piezas += 1

    # Recuadro (bounding box) = X×Y que REALMENTE ocupas de la hoja (incluye desperdicio)
    try:
        ext = ezdxf.bbox.extents(msp)
        ancho_mm, alto_mm = ext.size.x, ext.size.y
    except Exception:
        ancho_mm = alto_mm = 0.0
    ancho_cm, alto_cm = ancho_mm / 10.0, alto_mm / 10.0
    area_recuadro_cm2 = ancho_cm * alto_cm

    # mm EXTRA por cortar el recuadro (perímetro del bounding box)
    perimetro_recuadro_mm = 2 * (ancho_mm + alto_mm) if cortar_recuadro else 0.0
    long_mm = long_piezas_mm + perimetro_recuadro_mm

    long_m = long_mm / 1000.0
    tiempo_min = long_mm / (velocidad_mm_s * 60.0) if velocidad_mm_s > 0 else 0.0
    laser = _cargar_laser()
    costo_min = float(laser.get("costo_minuto", 8.0))
    costo_corte = tiempo_min * costo_min

    # Material: cobra el RECUADRO X×Y (incluye desperdicio) + merma extra opcional
    costo_material = 0.0
    costo_desperdicio = 0.0
    material_info = None
    if material:
        q = _norm(material)
        for m in laser.get("materiales", []):
            if q in _norm(m.get("nombre", "")):
                hoja_cm2 = float(m.get("ancho", 122)) * float(m.get("alto", 244))
                precio_hoja = float(m.get("precio_hoja", 0))
                frac = min(1.0, area_recuadro_cm2 / hoja_cm2) if hoja_cm2 else 0
                base_mat = precio_hoja * frac
                costo_desperdicio = round(base_mat * (merma_pct / 100.0), 2)
                costo_material = round(base_mat + costo_desperdicio, 2)
                material_info = {"nombre": m.get("nombre", ""), "precio_hoja": precio_hoja,
                                 "fraccion_hoja_pct": round(frac * 100, 1), "merma_pct": merma_pct}
                break
        if material_info is None:
            material_info = {"aviso": f"Material '{material}' no está en tu lista; costo material = 0."}

    subtotal = costo_corte + costo_material
    total = round(subtotal * (1 + margen_pct / 100.0), 2)

    return {
        "status": "ok",
        "archivo": p.name,
        "medida_cm": f"{ancho_cm:.1f} x {alto_cm:.1f}",
        "area_recuadro_cm2": round(area_recuadro_cm2, 1),
        "piezas_aprox": piezas,
        "longitud_corte_m": round(long_m, 2),
        "longitud_piezas_m": round(long_piezas_mm / 1000.0, 2),
        "longitud_recuadro_m": round(perimetro_recuadro_mm / 1000.0, 2),
        "corto_recuadro": cortar_recuadro,
        "velocidad_mm_s": velocidad_mm_s,
        "tiempo_min": round(tiempo_min, 1),
        "costo_minuto": costo_min,
        "costo_corte": round(costo_corte, 2),
        "material": material_info,
        "costo_material": costo_material,
        "costo_desperdicio": costo_desperdicio,
        "merma_pct": merma_pct,
        "margen_pct": margen_pct,
        "total": total,
        "nota": "Material por recuadro X×Y (incluye desperdicio). +merma_pct opcional. Corte suma el perímetro del recuadro.",
    }


if __name__ == "__main__":
    import sys
    r = cotizar_corte(sys.argv[1] if len(sys.argv) > 1 else "",
                      sys.argv[2] if len(sys.argv) > 2 else "MDF 5.5")
    print(json.dumps(r, ensure_ascii=False, indent=2))
