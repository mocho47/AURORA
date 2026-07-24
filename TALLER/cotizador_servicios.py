# -*- coding: utf-8 -*-
"""AURORA · COTIZADOR POR REGLAS (Prendas & Servicios).

Para trabajos SIN archivo DXF (prendas, DTF, vinil, lona, plumas, adhesivos…):
se cotiza por REGLAS desde CONFIG/catalogo_servicios.json (editable).
Calcula precio, COSTO real y GANANCIA por línea y total — base de la contabilidad.
La imagen de referencia (IA/Pinterest) es solo guía visual, NO se computa.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGO = ROOT / "CONFIG" / "catalogo_servicios.json"


def _load() -> dict:
    try:
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    CATALOGO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


UNIDADES_OK = ("pieza", "m2", "metro")


def guardar_servicio(nombre: str, precio, unidad: str = "pieza", costo=None) -> dict:
    """Agrega o actualiza un trabajo/servicio en el catálogo (categoría 'productos').
    Si ya existe uno con el mismo nombre, lo sobrescribe. unidad: pieza | m2 | metro."""
    nombre = (nombre or "").strip()
    if not nombre:
        return {"status": "error", "msg": "Falta el nombre del trabajo."}
    unidad = (unidad or "pieza").strip().lower()
    if unidad not in UNIDADES_OK:
        unidad = "pieza"
    try:
        precio = round(float(precio), 2)
    except Exception:
        return {"status": "error", "msg": "Precio inválido."}
    if precio <= 0:
        return {"status": "error", "msg": "El precio debe ser mayor a 0."}
    try:
        costo = round(float(costo), 2) if costo not in (None, "", " ") else None
    except Exception:
        costo = None
    d = _load()
    prods = d.setdefault("productos", [])
    nl = nombre.lower()
    item = {"nombre": nombre, "precio": precio, "unidad": unidad}
    if costo is not None:
        item["costo"] = costo
    for i, p in enumerate(prods):
        if str(p.get("nombre", "")).strip().lower() == nl:
            prods[i] = item
            _save(d)
            return {"status": "ok", "accion": "actualizado", "servicio": item}
    prods.append(item)
    _save(d)
    return {"status": "ok", "accion": "agregado", "servicio": item}


def borrar_servicio(nombre: str) -> dict:
    """Borra un trabajo/servicio del catálogo por nombre (solo de 'productos')."""
    nombre = (nombre or "").strip().lower()
    d = _load()
    prods = d.get("productos", [])
    nuevos = [p for p in prods if str(p.get("nombre", "")).strip().lower() != nombre]
    if len(nuevos) == len(prods):
        return {"status": "error", "msg": "No se encontró ese trabajo."}
    d["productos"] = nuevos
    _save(d)
    return {"status": "ok", "accion": "borrado"}


def catalogo_plano() -> dict:
    """Aplana el catálogo en una lista de artículos cotizables (precio + costo + unidad)."""
    d = _load()
    items = []
    for p in d.get("prendas", []):
        items.append({"nombre": p["nombre"], "categoria": "Prenda", "precio": p.get("precio"),
                      "costo": p.get("costo"), "unidad": "pieza", "incluye": p.get("incluye", "")})
    for e in d.get("extras", []):
        items.append({"nombre": e["nombre"], "categoria": "Extra", "precio": e.get("precio"),
                      "costo": e.get("costo"), "unidad": "pieza"})
    for pr in d.get("productos", []):
        if "precio_m2" in pr:
            items.append({"nombre": pr["nombre"], "categoria": "Producto", "precio": pr.get("precio_m2"),
                          "costo": pr.get("costo_m2"), "unidad": "m2"})
        else:
            # Modelo GENERAL de escalas por cantidad (compat con campos viejos).
            esc = pr.get("escalas")
            if not esc and "precio_pieza" in pr:
                esc = [{"desde": 1, "precio": pr["precio_pieza"]}]
                if pr.get("precio_docena_pza"):
                    esc.append({"desde": 12, "precio": pr["precio_docena_pza"]})
                if pr.get("precio_mayoreo_pza"):
                    esc.append({"desde": pr.get("mayoreo_desde", 50), "precio": pr["precio_mayoreo_pza"]})
            if esc:
                esc = sorted(esc, key=lambda e: e.get("desde", 1))
                items.append({"nombre": pr["nombre"], "categoria": "Producto", "precio": esc[0]["precio"],
                              "escalas": esc, "costo": pr.get("costo"), "unidad": pr.get("unidad", "pieza")})
            else:
                items.append({"nombre": pr["nombre"], "categoria": "Producto", "precio": pr.get("precio"),
                              "costo": pr.get("costo"), "unidad": pr.get("unidad", "pieza")})
    dtf = d.get("dtf", {})
    if dtf.get("venta_metro"):
        items.append({"nombre": "DTF (metro)", "categoria": "DTF", "precio": dtf.get("venta_metro"),
                      "costo": dtf.get("costo_metro_max"), "unidad": "metro"})
    return {"status": "ok", "total": len(items), "items": items}


def cotizar(carrito: list, pago_tarjeta: bool = False) -> dict:
    """
    carrito = [{"nombre": str, "cantidad": num}]
    Resuelve precios/costos reales del catálogo (aplica la escala por cantidad).
    pago_tarjeta=True agrega 4% de recargo por pago con tarjeta.
    """
    plano = {i["nombre"]: i for i in catalogo_plano()["items"]}
    lineas = []
    total_precio = 0.0
    total_costo = 0.0
    faltan_costo = False
    for c in carrito or []:
        it = plano.get(c.get("nombre"))
        if not it:
            continue
        try:
            cant = float(c.get("cantidad", 1))
        except Exception:
            cant = 1.0
        if cant <= 0:
            continue
        pu = it.get("precio") or 0
        por_docena = False
        tier = ""
        esc = it.get("escalas")
        if esc:
            aplic = [e for e in esc if cant >= e.get("desde", 1)]
            if aplic:
                sel = max(aplic, key=lambda e: e.get("desde", 1))
                pu = sel.get("precio", pu)
                if sel.get("desde", 1) > 1:
                    tier = f"{int(sel['desde'])}+ pzas"
        precio_linea = round(pu * cant, 2)
        costo_unit = it.get("costo")
        costo_linea = round(costo_unit * cant, 2) if costo_unit is not None else None
        if costo_linea is None:
            faltan_costo = True
        total_precio += precio_linea
        total_costo += (costo_linea or 0)
        lineas.append({"nombre": it["nombre"], "categoria": it.get("categoria", ""),
                       "cantidad": cant, "unidad": it.get("unidad", "pieza"),
                       "precio_unit": pu, "por_docena": por_docena, "tier": tier,
                       "precio": precio_linea, "costo": costo_linea})
    total_precio = round(total_precio, 2)
    recargo_tarjeta = round(total_precio * 0.04, 2) if pago_tarjeta else 0.0
    total_final = round(total_precio + recargo_tarjeta, 2)
    ganancia = round(total_final - total_costo, 2)
    return {"status": "ok", "lineas": lineas,
            "total_precio": total_precio,
            "pago_tarjeta": pago_tarjeta,
            "recargo_tarjeta": recargo_tarjeta,
            "total_final": total_final,
            "total_costo": round(total_costo, 2),
            "ganancia": ganancia,
            "faltan_costos": faltan_costo,
            "nota": "Costo parcial: algunos artículos aún no tienen costo capturado (la ganancia mostrada es máxima)." if faltan_costo else ""}


if __name__ == "__main__":
    print(json.dumps(catalogo_plano(), ensure_ascii=False, indent=2))
