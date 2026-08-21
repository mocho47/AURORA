# -*- coding: utf-8 -*-
"""
AURORA · LA FÓRMULA DE PRECIOS DE ANUAR — fuente única
=============================================================================
Dictada por él en vivo el 2026-08-13, revisando por qué el sistema cotizaba
$284 y $538 donde su cuenta real da $180:

    PRECIO = (materiales × 1.20) + corte + diseño + instalación

Sus palabras textuales, que son las que mandan aquí:

  · "todos mis precios son más el 20% de compraventa Y + el corte o grabado
     o colocación"          -> el 1.20 va SOLO al material. Es compraventa.
  · "los 8 pesos son del minuto de láser, ese no me cuesta eso a mí"
                            -> el corte YA es precio de venta. NO lleva margen.
  · "diseño con imagen 15, sin imagen 20 ... si trae PDF o DXF, 10 pesitos"
                            -> el diseño se decide por la EXTENSIÓN del archivo.
  · "20 pesos mínimo, si mide más de 1 m el doble"
  · "no cobro corte de vinil porque lo pego al MDF y corto todo a la vez"
                            -> MDF + vinil = UN SOLO CORTE. Nunca dos.

POR QUÉ ESTE ARCHIVO EXISTE
---------------------------------------------------------------------------
Antes había tres cuentas distintas —el cotizador de corte, el de vinil y el
panel— y cada una daba un número diferente para el mismo trabajo. El error de
fondo era uno solo: aplicar el margen al total (`(corte + material) × 1.30`),
o sea cobrar ganancia sobre la propia ganancia.

Aquí se calcula una vez. Quien necesite un precio, lo pide aquí. Si mañana
Anuar cambia el minuto de corte, se cambia en un lugar y el sistema entero
queda parejo.

Los números NO están escritos en este código: se leen de
`CONFIG/catalogo_servicios.json`, que es donde él los dictó.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICIOS = ROOT / "CONFIG" / "catalogo_servicios.json"

# Respaldos por si el JSON no se puede leer. Son sus números reales, no
# inventados: si algún día no coinciden con el catálogo, manda el catálogo.
_POR_DEFECTO = {
    "compraventa": 1.20,
    "minuto_corte": 8.0,
    "velocidad_mm_s": 20.0,
    "diseno_vector": 10.0,
    "diseno_imagen": 15.0,
    "diseno_cero": 20.0,
    "instalacion": 20.0,
    "instalacion_grande": 40.0,
    "instalacion_cm_grande": 100.0,
}

# Extensiones que llegan ya listas para cortar (el trabajo es mínimo) frente a
# las que hay que vectorizar a mano. Su regla: se mira la extensión, no se
# pregunta.
_VECTOR = {".dxf", ".pdf", ".ai", ".eps", ".svg", ".cdr", ".plt", ".dwg"}
_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff",
           ".heic", ".avif"}


def _reglas() -> dict:
    """Los números de Anuar, leídos del catálogo donde él los dictó."""
    r = dict(_POR_DEFECTO)
    try:
        d = json.loads(SERVICIOS.read_text(encoding="utf-8"))
    except Exception:
        return r
    dis = d.get("diseno_reglas", {})
    ins = d.get("instalacion_reglas", {})
    las = d.get("laser_reglas", {})
    if dis.get("trae_vector_pdf_o_dxf") is not None:
        r["diseno_vector"] = float(dis["trae_vector_pdf_o_dxf"])
    if dis.get("trae_imagen_hay_que_vectorizar") is not None:
        r["diseno_imagen"] = float(dis["trae_imagen_hay_que_vectorizar"])
    if dis.get("no_trae_nada_diseno_desde_cero") is not None:
        r["diseno_cero"] = float(dis["no_trae_nada_diseno_desde_cero"])
    if ins.get("minimo") is not None:
        r["instalacion"] = float(ins["minimo"])
    if ins.get("si_mide_mas_de_1_metro") is not None:
        r["instalacion_grande"] = float(ins["si_mide_mas_de_1_metro"])
    if las.get("precio_minuto_corte_VENTA") is not None:
        r["minuto_corte"] = float(las["precio_minuto_corte_VENTA"])
    if las.get("velocidad_corte_3mm_mm_s") is not None:
        r["velocidad_mm_s"] = float(las["velocidad_corte_3mm_mm_s"])
    return r


def clasificar_diseno(archivo) -> str:
    """¿Qué tipo de diseño trae el cliente? Se decide por la extensión.

    Devuelve 'vector', 'imagen', 'cero' o 'ninguno'.

    - `None` / `False` / "no" -> 'ninguno' (no se cobra diseño; ya está resuelto)
    - `True` / "" / "desde_cero" -> 'cero' (no trajo nada, hay que dibujarlo)
    - una ruta o nombre de archivo -> según su extensión
    """
    if archivo is None or archivo is False:
        return "ninguno"
    if archivo is True:
        return "cero"
    txt = str(archivo).strip()
    if not txt:
        return "cero"
    bajo = txt.lower()
    if bajo in ("no", "ninguno", "sin", "sin_diseno", "sin diseño", "ya_tengo"):
        return "ninguno"
    if bajo in ("desde_cero", "desde cero", "nada", "cero"):
        return "cero"
    ext = Path(txt).suffix.lower()
    if ext in _VECTOR:
        return "vector"
    if ext in _IMAGEN:
        return "imagen"
    # Trae algo pero no reconozco el formato: se cobra como si hubiera que
    # rehacerlo. Es la opción honesta — cobrar de menos sale de su bolsa.
    return "cero" if ext else "cero"


def cotizar(materiales=0.0, minutos_corte: float = 0.0, diseno=None,
            instalacion: bool = False, lado_mayor_cm: float = 0.0,
            cantidad: int = 1) -> dict:
    """El precio de un trabajo, con la fórmula de Anuar y su desglose completo.

    materiales     : lo que a él le CUESTAN los materiales (compra, sin margen).
                     Puede ser un número o una lista de {"nombre", "costo"}.
    minutos_corte  : minutos reales de láser. Si el trabajo lleva vinil pegado
                     al MDF, son los MISMOS minutos: es un solo corte.
    diseno         : archivo del cliente (decide el precio por su extensión),
                     None si no se cobra diseño, True si hay que hacerlo de cero.
    instalacion    : si él la va a instalar.
    lado_mayor_cm  : el lado más largo de la pieza; arriba de 1 m la
                     instalación se cobra doble.
    cantidad       : piezas iguales. Multiplica material y corte —el diseño se
                     hace una vez, y la instalación se cuenta como un viaje.
    """
    r = _reglas()
    cantidad = max(1, int(cantidad or 1))

    # ── materiales ──────────────────────────────────────────────────────
    detalle_mat = []
    if isinstance(materiales, (list, tuple)):
        costo_mat = 0.0
        for m in materiales:
            if isinstance(m, dict):
                c = float(m.get("costo", 0) or 0)
                detalle_mat.append({"nombre": m.get("nombre", "material"),
                                    "costo": round(c, 2)})
                costo_mat += c
            else:
                costo_mat += float(m or 0)
    else:
        costo_mat = float(materiales or 0)

    costo_mat *= cantidad
    for m in detalle_mat:
        m["costo"] = round(m["costo"] * cantidad, 2)

    # El 20% es de COMPRAVENTA y va solo aquí. Es su piso, no su ganancia total.
    materiales_con_margen = round(costo_mat * r["compraventa"], 2)
    ganancia_material = round(materiales_con_margen - costo_mat, 2)

    # ── corte ───────────────────────────────────────────────────────────
    # Los $8 del minuto YA son precio de venta. No se les aplica margen: eso
    # era cobrar ganancia sobre la ganancia, y es lo que inflaba los precios.
    minutos = float(minutos_corte or 0) * cantidad
    corte = round(minutos * r["minuto_corte"], 2)

    # ── diseño ──────────────────────────────────────────────────────────
    # Una vez por trabajo, no por pieza: diseñar 10 iguales es diseñar una.
    tipo_dis = clasificar_diseno(diseno)
    precio_dis = {"vector": r["diseno_vector"], "imagen": r["diseno_imagen"],
                  "cero": r["diseno_cero"], "ninguno": 0.0}[tipo_dis]
    explica_dis = {
        "vector": "trae archivo listo (PDF/DXF)",
        "imagen": "trae imagen, hay que vectorizarla",
        "cero": "no trae nada, se diseña desde cero",
        "ninguno": "no se cobra diseño",
    }[tipo_dis]

    # ── instalación ─────────────────────────────────────────────────────
    inst = 0.0
    explica_inst = "no lleva instalación"
    if instalacion:
        grande = float(lado_mayor_cm or 0) > r["instalacion_cm_grande"]
        inst = r["instalacion_grande"] if grande else r["instalacion"]
        explica_inst = ("pasa de 1 m, se cobra doble" if grande
                        else "instalación normal")

    total = round(materiales_con_margen + corte + precio_dis + inst, 2)

    return {
        "status": "ok",
        "total": total,
        "cantidad": cantidad,
        "materiales": {
            "costo": round(costo_mat, 2),
            "con_compraventa": materiales_con_margen,
            "ganancia": ganancia_material,
            "factor": r["compraventa"],
            "detalle": detalle_mat,
        },
        "corte": {
            "minutos": round(minutos, 2),
            "por_minuto": r["minuto_corte"],
            "importe": corte,
            "nota": "precio de venta directo, sin margen encima",
        },
        "diseno": {"tipo": tipo_dis, "importe": precio_dis,
                   "por_que": explica_dis},
        "instalacion": {"importe": inst, "por_que": explica_inst,
                        "lado_mayor_cm": round(float(lado_mayor_cm or 0), 1)},
        "formula": "(materiales × 1.20) + corte + diseño + instalación",
        "_fuente": "dictada por Anuar 2026-08-13 · CONFIG/catalogo_servicios.json",
    }


def texto(r: dict) -> str:
    """El desglose como se lo quiere ver Anuar: en renglones, sin adornos."""
    if r.get("status") != "ok":
        return r.get("mensaje", "No se pudo cotizar.")
    m, c, d, i = r["materiales"], r["corte"], r["diseno"], r["instalacion"]
    L = []
    if r["cantidad"] > 1:
        L.append(f"**{r['cantidad']} piezas**")
    L.append(f"materiales  ${m['costo']:>8.2f}  ×1.20  =  ${m['con_compraventa']:.2f}")
    for x in m["detalle"]:
        L.append(f"    · {x['nombre']}: ${x['costo']:.2f}")
    L.append(f"corte       {c['minutos']:>7.2f} min × ${c['por_minuto']:.0f}  =  ${c['importe']:.2f}")
    if d["importe"]:
        L.append(f"diseño                        ${d['importe']:>8.2f}   ({d['por_que']})")
    if i["importe"]:
        L.append(f"instalación                   ${i['importe']:>8.2f}   ({i['por_que']})")
    L.append("")
    L.append(f"**TOTAL  ${r['total']:.2f}**")
    return "\n".join(L)


if __name__ == "__main__":
    # El caso real con el que se cerró la fórmula: happybirth.dxf, 60×60 cm,
    # MDF 2.7 + vinil dorado, el cliente trajo una foto, con instalación.
    demo = cotizar(
        materiales=[{"nombre": "MDF 2.7 (60×60)", "costo": 13.30},
                    {"nombre": "Vinil dorado (60 cm)", "costo": 28.80}],
        minutos_corte=11.82, diseno="referencia.jpg",
        instalacion=True, lado_mayor_cm=60,
    )
    print(texto(demo))
