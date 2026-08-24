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


def _formula():
    """La fórmula de precios de Anuar. Aquí no se calcula ningún total: se
    mide el DXF y se le pasan los números a `TALLER/formula_precios.py`, que
    es el único lugar donde vive su cuenta (2026-08-14)."""
    import importlib.util as _ilu
    ruta = ROOT / "TALLER" / "formula_precios.py"
    spec = _ilu.spec_from_file_location("formula_precios", ruta)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def _costo_de_rollo(nombre: str, ancho_cm: float, alto_cm: float) -> dict:
    """Lo que cuesta el vinil que cubre una pieza de ancho×alto.

    El vinil se vende por METRO LINEAL de un rollo de ancho fijo. Una pieza de
    60×60 salida de un rollo de 60 cm consume 60 cm lineales — no "0.36 m²".
    Cobrar por metro cuadrado da números que no existen en su factura.

    Se prueba en las dos orientaciones porque girar la pieza es gratis.
    """
    q = _norm(nombre)
    try:
        cat = json.loads((ROOT / "CONFIG" / "catalogo_maestro.json")
                         .read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "aviso": "No se pudo leer el catálogo de materiales."}

    # Se juntan TODOS los que coinciden antes de decidir. Buscar "dorado"
    # encuentra el textil (que está vacío a propósito) y el de recorte (que sí
    # tiene su precio): quedarse con el primero devolvía "no tiene precio"
    # teniendo el dato a dos renglones de distancia (2026-08-14).
    candidatos, sin_precio = [], []
    for r in cat.get("renglones", []):
        if not isinstance(r, dict) or r.get("tipo") != "material":
            continue
        if q not in _norm(r.get("nombre", "")):
            continue
        if r.get("compra") and r.get("medida"):
            candidatos.append(r)
        else:
            sin_precio.append(r.get("nombre", "?"))

    if not candidatos:
        if sin_precio:
            return {"ok": False,
                    "aviso": (f"Encontré {', '.join(sin_precio)} pero sin precio ni ancho "
                              f"de rollo capturado. Dime cuánto te cuesta el metro.")}
        return {"ok": False, "aviso": f"'{nombre}' no está en tu catálogo de materiales."}

    # Con varios candidatos válidos gana el de nombre más corto: es el que
    # menos palabras añade a lo que él pidió, o sea el más parecido.
    no_cupieron = []
    for r in sorted(candidatos, key=lambda x: len(x.get("nombre", ""))):
        precio_m = float(r["compra"])
        ar = float(r["medida"])
        # ¿De qué lado sale? El que quepa en el ancho del rollo.
        if ancho_cm <= ar:
            lineales_cm = alto_cm
        elif alto_cm <= ar:
            lineales_cm = ancho_cm
        else:
            # Este rollo es angosto para la pieza, pero puede haber otro más
            # ancho del mismo material: se sigue buscando antes de rendirse.
            no_cupieron.append(f"{r.get('nombre')} ({ar:.0f} cm)")
            continue
        costo = round(precio_m * (lineales_cm / 100.0), 2)
        return {"ok": True, "nombre": r.get("nombre"), "costo": costo,
                "precio_metro": precio_m, "ancho_rollo_cm": ar,
                "metros_lineales": round(lineales_cm / 100.0, 3)}

    return {"ok": False,
            "aviso": (f"La pieza mide {ancho_cm:.0f}×{alto_cm:.0f} cm y no la cubre "
                      f"ningún rollo que tienes de ese material: {', '.join(no_cupieron)}. "
                      f"Hay que unirlo o cambiar de material.")}


def _cabe_en_la_maquina(ancho_mm: float, alto_mm: float) -> dict:
    """¿Este diseño entra en su láser, o se va a enterar con el material puesto?

    Su máquina es una 1390: la cama mide 1300 × 900 mm. La hoja de MDF mide
    1220 × 2440, así que **la hoja completa no entra** —hay que partirla en
    tiras— y un diseño largo puede caber en la hoja y aun así no caber en la
    máquina. Ese error se descubre normalmente cuando ya se cargó el material
    y se cerró la tapa (2026-08-08).

    Se prueba en las dos orientaciones: girar la pieza es gratis.
    """
    try:
        cfg = json.loads((ROOT / "CONFIG" / "maquinas.json")
                         .read_text(encoding="utf-8"))
        cama = cfg.get("laser", {}).get("area_de_corte_mm")
        if not cama:
            return {"sabemos": False}
        cx, cy = float(cama[0]), float(cama[1])
    except Exception:
        return {"sabemos": False}

    a, b = float(ancho_mm), float(alto_mm)
    derecho = a <= cx and b <= cy
    girado = b <= cx and a <= cy
    r = {"sabemos": True, "cabe": derecho or girado,
         "cama_mm": [cx, cy], "girando": (not derecho) and girado}
    if not r["cabe"]:
        sobra_x = max(0.0, min(a, b) - cy)
        sobra_y = max(0.0, max(a, b) - cx)
        r["detalle"] = (
            f"NO CABE en tu 1390 ({cx:g}×{cy:g} mm). El diseño mide "
            f"{a:.0f}×{b:.0f} mm y se pasa por "
            + (f"{sobra_y:.0f} mm de largo" if sobra_y else "")
            + (" y " if sobra_x and sobra_y else "")
            + (f"{sobra_x:.0f} mm de ancho" if sobra_x else "")
            + ". Hay que partirlo en piezas o cortarlo en otro lado.")
    return r


def cotizar_corte(ruta: str, material: str = "", velocidad_mm_s: float = 20.0,
                  margen_pct: float = 0.0, cortar_recuadro: bool = True,
                  merma_pct: float = 0.0, diseno=None,
                  instalacion: bool = False, cantidad: int = 1,
                  materiales_extra=None) -> dict:
    """
    Cotiza corte láser desde un DXF con precios reales de Milens.
    - velocidad_mm_s: 20 mm/s, la que Anuar dictó el 2026-08-13.
    - cortar_recuadro: suma los mm del perímetro del recuadro X×Y al corte.
    - merma_pct: desperdicio EXTRA sobre el material (acomodo/sobrante entre trabajos).
    - diseno: archivo del cliente; su extensión decide el precio del diseño.
    - instalacion: si él la va a poner (el lado mayor decide si es doble).
    - materiales_extra: lo que va ADEMÁS de la hoja — típicamente el vinil de
      recorte. Lista de {"nombre", "costo"} o el nombre del vinil en texto (se
      busca su precio en el catálogo y se cobra la superficie del recuadro).
      Su regla: el vinil se pega al MDF y se corta TODO A LA VEZ, así que NO
      se suma corte de plotter aparte — son los mismos minutos de láser.

    DESPERDICIO: el material se cobra por el RECUADRO X×Y completo (lo que de verdad
    consumes de la hoja), así el sobrante alrededor de las piezas YA queda cobrado.

    `margen_pct` SIGUE EN LA FIRMA pero ya no se usa para el total. Los tres
    llamadores (el panel y el chat) lo mandan por posición y quitarlo los
    rompería. La cuenta real vive en `TALLER/formula_precios.py`: el 20% es de
    compraventa y va solo al material, porque los $8 del minuto de corte YA son
    precio de venta. Aplicarle margen encima era cobrar ganancia sobre la
    ganancia — eso daba $284 donde su cuenta da $180 (2026-08-14).
    """
    # Windows agrega comillas al copiar una ruta ("Copiar como ruta de acceso");
    # el chat ya las quitaba, este cotizador no — por eso el panel decía "no
    # se pudo medir" con una ruta real y bien escrita (2026-08-23).
    ruta = ruta.strip().strip('"').strip("'").strip()
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

    # ── el precio, con la fórmula de Anuar ───────────────────────────────
    # `costo_material` es lo que a él le CUESTA (fracción de hoja + merma).
    # La compraventa, el diseño y la instalación los pone la fórmula única.
    lado_mayor_cm = max(ancho_cm, alto_cm)

    lista_mat = []
    if costo_material:
        lista_mat.append({"nombre": (material_info or {}).get("nombre", material) or "material",
                          "costo": costo_material})

    # Lo que va pegado encima: vinil de recorte, normalmente. Mismo corte.
    avisos_extra = []
    for extra in (materiales_extra or []):
        if isinstance(extra, dict) and "costo" in extra:
            lista_mat.append({"nombre": extra.get("nombre", "extra"),
                              "costo": float(extra["costo"])})
            continue
        nombre_extra = extra.get("nombre", "") if isinstance(extra, dict) else str(extra)
        v = _costo_de_rollo(nombre_extra, ancho_cm, alto_cm)
        if v.get("ok"):
            lista_mat.append({"nombre": v["nombre"], "costo": v["costo"]})
        else:
            avisos_extra.append(v.get("aviso", f"No pude cotizar '{nombre_extra}'."))

    try:
        _f = _formula()
        precio = _f.cotizar(
            materiales=lista_mat if lista_mat else 0.0,
            minutos_corte=tiempo_min, diseno=diseno,
            instalacion=instalacion, lado_mayor_cm=lado_mayor_cm,
            cantidad=cantidad)
        total = precio["total"]
        desglose = _f.texto(precio)
    except Exception as e:
        # Si la fórmula no carga, se dice — no se inventa un número.
        precio = {"status": "error", "mensaje": f"No se pudo cargar la fórmula: {e}"}
        total = round(costo_material * 1.20 + costo_corte, 2)
        desglose = "(fórmula no disponible; total = material×1.20 + corte)"

    return {
        "status": "ok",
        "archivo": p.name,
        "precio": precio,
        "desglose": desglose,
        "avisos": avisos_extra,
        "medida_cm": f"{ancho_cm:.1f} x {alto_cm:.1f}",
        "cabe_en_la_maquina": _cabe_en_la_maquina(ancho_mm, alto_mm),
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
        "margen_pct_ignorado": margen_pct,
        "total": total,
        "nota": ("Material por recuadro X×Y (incluye desperdicio). +merma_pct opcional. "
                 "Corte suma el perímetro del recuadro. El precio lo calcula "
                 "TALLER/formula_precios.py — aquí no se hace ninguna cuenta."),
    }


if __name__ == "__main__":
    import sys
    r = cotizar_corte(sys.argv[1] if len(sys.argv) > 1 else "",
                      sys.argv[2] if len(sys.argv) > 2 else "MDF 5.5")
    print(json.dumps(r, ensure_ascii=False, indent=2))
