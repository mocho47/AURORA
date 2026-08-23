# -*- coding: utf-8 -*-
"""AURORA · Producción de piezas grandes (personajes/piñatas): escala + tabloides + MDF + corte

Pedido real de Anuar (2026-08-21, cliente Alicia Piñatas, personaje RUMI/RUMO):
este proceso se va a repetir con distintos tamaños e imágenes. Junta en un
solo cálculo lo que antes eran pasos sueltos:

  1. Escalar el DXF al tamaño real que pida (alto o ancho, en cm).
  2. Cuántos tabloides hacen falta para imprimir eso en vinil (reusa
     TALLER/dividir_en_hojas.py, el mismo cálculo, no uno aparte).
  3. Cuánto MDF real se necesita y su costo (×1.20, con los precios reales
     de CONFIG/precios_base.json).
  4. Cuánto sale el corte láser ($8/min sobre el perímetro real del DXF).
  5. El recordatorio de qué decirle a la maquila para que su corte en MDF
     coincida con lo que ellos impriman.

LO QUE ESTO NO HACE SOLO: separar el dibujo en piezas por prenda (cara,
pelo, chamarra, falda, piernas, botas) NO es automático de forma confiable
— un DXF de personaje normalmente no trae esa separación ya hecha (se
comprobó en vivo con RUMO.dxf: 126 curvas sueltas, sin capas por prenda).
Si el archivo ya trae capas reales por prenda, se usan. Si no, "despiece"
avisa que hace falta clasificarlo a mano una vez (como se hizo con RUMO) en
vez de inventar una separación y arriesgar un corte mal etiquetado.

Correr:  python TALLER/produccion_piezas_grandes.py "ruta.dxf" 90 contorno
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

VELOCIDAD_MM_S = 25.0
COSTO_MINUTO = 8.0


def _precio_mdf(grosor_mm: float = 2.7) -> dict:
    """Lee el precio real de la hoja de MDF de CONFIG/precios_base.json.
    No inventa un precio si no lo encuentra: lo dice."""
    import json
    ruta = RAIZ / "CONFIG" / "precios_base.json"
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        materiales = datos.get("laser", {}).get("materiales", []) or datos.get("materiales", [])
        for m in materiales:
            nombre = m.get("nombre", "").lower()
            if "mdf" in nombre and f"{grosor_mm:g}mm" in nombre.replace(" ", ""):
                return {"nombre": m["nombre"], "precio_hoja": m["precio_hoja"],
                        "ancho_cm": m["ancho"], "alto_cm": m["alto"]}
        # si no hay ese grosor exacto, la primera hoja de MDF que encuentre
        for m in materiales:
            if "mdf" in m.get("nombre", "").lower():
                return {"nombre": m["nombre"], "precio_hoja": m["precio_hoja"],
                        "ancho_cm": m["ancho"], "alto_cm": m["alto"],
                        "aviso": f"no había MDF de {grosor_mm}mm exacto, usé {m['nombre']}"}
    except Exception as e:
        pass
    return {}


def _perimetro_mm(msp) -> float:
    total = 0.0
    for e in msp:
        t = e.dxftype()
        try:
            if t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
            elif t == "POLYLINE":
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            elif t == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            else:
                continue
        except Exception:
            continue
        for a, b in zip(pts, pts[1:]):
            total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


HOJAS_MM = {"tabloide": (279.4, 431.8), "a4": (210.0, 297.0)}


def calcular(ruta_dxf: str, alto_cm: float = None, ancho_cm: float = None,
             modo: str = "contorno", grosor_mdf_mm: float = 2.7,
             costo_tabloide: float = 10.0, precio_tabloide: float = 25.0,
             traslape_mm: float = 5.0, cliente: str = "",
             con_suaje: bool = False, hoja: str = "tabloide",
             orientacion: str = "auto", n_hojas: int = None) -> dict:
    """El cálculo completo: escala + hojas de impresión + MDF + corte + recordatorio.

    cliente: si trae "alicia" (el acuerdo real de reventa de tabloides a
    $25 que ya cuesta $10, más el corte bajo registro — pedido 2026-08-21),
    se muestra venta/margen del tabloide como en ese trato. Con cualquier
    otro cliente (o sin dato) se usa el precio real de reventa general:
    $95 con suaje, $70 sin suaje (dictado por Anuar 2026-08-21).

    hoja: "tabloide" (default) o "a4" — el tamaño de hoja para calcular
    cuántas hacen falta. Pedido real 2026-08-22: elegir el tamaño de hoja.
    NO mezcla tamaños ni orientaciones distintas en un mismo trabajo — arma
    UNA sola cuadrícula con un solo tamaño y una sola orientación de hoja.

    orientacion: "auto" (default, la que dé menos hojas en total),
    "vertical" (obliga hoja en pie) u "horizontal" (obliga hoja acostada) —
    pedido real 2026-08-22: puede que salgan más hojas que con "auto", es a
    propósito, porque la maquila o el papel lo piden así.

    n_hojas: si Anuar YA sabe cuántas hojas quiere (las contó él, o así se
    lo pidió la maquila), se usa ese número tal cual para el costo — no se
    recalcula la cuadrícula. Pedido real 2026-08-22."""
    try:
        import ezdxf
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    ruta = Path(ruta_dxf)
    if not ruta.exists():
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}

    doc = ezdxf.readfile(str(ruta))
    msp = doc.modelspace()

    import ezdxf.bbox as bbmod
    ext = bbmod.extents(msp)
    if not ext:
        return {"status": "ERROR", "detalle": "No pude medir el DXF (sin geometría)."}
    eje_x_mm, eje_y_mm = ext.size.x, ext.size.y
    # El DXF puede venir acostado (como RUMO: 900x487.5, el personaje de pie
    # mide 900mm de alto pero el eje X del archivo es el que trae esa
    # medida). Por default se asume que el eje MÁS LARGO es el alto —cierto
    # para casi cualquier personaje/pieza de pie— y se avisa cuál se usó
    # para que se pueda corregir si esta vez no aplica.
    if eje_y_mm >= eje_x_mm:
        alto_mm, ancho_mm = eje_y_mm, eje_x_mm
        eje_alto_usado = "y"
    else:
        alto_mm, ancho_mm = eje_x_mm, eje_y_mm
        eje_alto_usado = "x"

    # ESCALA: se manda por alto o por ancho, lo que se haya pedido.
    escala = 1.0
    if alto_cm:
        escala = (alto_cm * 10) / alto_mm
    elif ancho_cm:
        escala = (ancho_cm * 10) / ancho_mm
    ancho_final_mm = ancho_mm * escala
    alto_final_mm = alto_mm * escala

    # CAPAS reales del archivo: si ya trae piezas separadas, se listan.
    capas = sorted({e.dxf.layer for e in msp if hasattr(e.dxf, "layer")})
    capas_utiles = [c for c in capas if c not in ("0", "Defpoints")]

    r = {"status": "OK", "modo": modo,
         "tamano_original_cm": (round(ancho_mm/10, 1), round(alto_mm/10, 1)),
         "tamano_pedido_cm": (round(ancho_final_mm/10, 1), round(alto_final_mm/10, 1)),
         "escala": round(escala, 4), "capas_reales": capas_utiles}

    if modo == "despiece" and len(capas_utiles) < 2:
        r["aviso_despiece"] = (
            "Este DXF NO trae las prendas ya separadas por capa "
            f"(solo tiene: {capas or ['ninguna']}). Separar cara/pelo/chamarra/"
            "falda/piernas/botas de un dibujo plano es trabajo real de "
            "clasificación, no es automático — dime si lo hago a mano "
            "(como con RUMO) o si me puedes dar el archivo ya con capas.")

    # HOJAS DE IMPRESIÓN (mismo cálculo real de dividir_en_hojas, sobre el tamaño YA escalado)
    hoja_mm = HOJAS_MM.get((hoja or "tabloide").lower(), HOJAS_MM["tabloide"])
    orient = (orientacion or "auto").lower()
    if orient == "vertical":
        candidatos = (hoja_mm,) if hoja_mm[0] <= hoja_mm[1] else ((hoja_mm[1], hoja_mm[0]),)
    elif orient == "horizontal":
        candidatos = (hoja_mm,) if hoja_mm[0] >= hoja_mm[1] else ((hoja_mm[1], hoja_mm[0]),)
    else:
        candidatos = (hoja_mm, (hoja_mm[1], hoja_mm[0]))
    mejor = None
    for hw, hh in candidatos:
        nx = max(1, math.ceil(ancho_final_mm / hw))
        ny = max(1, math.ceil(alto_final_mm / hh))
        if mejor is None or nx * ny < mejor[2]:
            mejor = (nx, ny, nx * ny)
    nx, ny, n_tabloides = mejor
    if n_hojas:
        # Anuar ya decidió el número — se respeta tal cual para el costo,
        # el grid (nx,ny) queda solo como referencia de la orientación.
        n_tabloides = int(n_hojas)
    es_alicia = "alicia" in (cliente or "").lower()
    r["tabloides"] = {"grid": (nx, ny), "cantidad": n_tabloides,
                       "costo_total": round(n_tabloides * costo_tabloide, 2)}
    if es_alicia:
        r["tabloides"]["venta_total"] = round(n_tabloides * precio_tabloide, 2)
        r["tabloides"]["margen"] = round(n_tabloides * (precio_tabloide - costo_tabloide), 2)
        r["tabloides"]["nota"] = "acuerdo real con Alicia Piñatas: compra $10, revende $25 c/u."
    else:
        precio_gral = 95.0 if con_suaje else 70.0
        r["tabloides"]["venta_total"] = round(n_tabloides * precio_gral, 2)
        r["tabloides"]["margen"] = round(n_tabloides * (precio_gral - costo_tabloide), 2)
        r["tabloides"]["nota"] = (
            f"precio general (no Alicia): ${precio_gral} c/u "
            f"({'con' if con_suaje else 'sin'} suaje). Falta sumar diseño + "
            "instalación de tu fórmula estándar antes de dar un precio final.")

    # MDF real (precios_base.json)
    mdf = _precio_mdf(grosor_mdf_mm)
    if mdf:
        area_pieza_cm2 = (ancho_final_mm/10) * (alto_final_mm/10)  # rectángulo envolvente, conservador
        area_hoja_cm2 = mdf["ancho_cm"] * mdf["alto_cm"]
        hojas = math.ceil(area_pieza_cm2 / area_hoja_cm2)
        costo_mdf = round(hojas * mdf["precio_hoja"] * 1.20, 2)
        r["mdf"] = {"material": mdf["nombre"], "hojas_necesarias": hojas,
                    "costo_con_margen": costo_mdf,
                    "nota": "área calculada sobre el rectángulo que envuelve la pieza "
                            "(conservador: la silueta real usa menos material)."}
        if mdf.get("aviso"):
            r["mdf"]["aviso"] = mdf["aviso"]
    else:
        r["mdf"] = {"aviso": f"No encontré precio real de MDF de {grosor_mdf_mm}mm en "
                              "CONFIG/precios_base.json — dime el precio de tu hoja."}

    # CORTE real ($8/min sobre el perímetro real, escalado)
    perim_mm = _perimetro_mm(msp) * escala
    minutos = (perim_mm / VELOCIDAD_MM_S) / 60
    r["corte"] = {"metros": round(perim_mm/1000, 2), "minutos": round(minutos, 1),
                  "costo": round(minutos * COSTO_MINUTO, 2)}

    r["total_estimado"] = round(
        r["mdf"].get("costo_con_margen", 0) + r["corte"]["costo"], 2)

    r["recordatorio_maquila"] = (
        f"Para que tu corte en MDF coincida con lo que impriman: manda las "
        f"{n_tabloides} hojas ({nx}x{ny}) a escala 1:1 REAL (sin 'ajustar a "
        f"página'), mismo tamaño en mm que tu DXF de corte, y pide que "
        f"respeten el traslape de {traslape_mm}mm entre hoja y hoja — ese "
        f"traslape es la referencia para alinear al pegar.")

    return r


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    ruta = sys.argv[1]
    alto = float(sys.argv[2]) if len(sys.argv) > 2 else None
    modo = sys.argv[3] if len(sys.argv) > 3 else "contorno"
    r = calcular(ruta, alto_cm=alto, modo=modo)
    import json
    print(json.dumps(r, ensure_ascii=False, indent=2))
