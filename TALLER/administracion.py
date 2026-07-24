# -*- coding: utf-8 -*-
"""AURORA · ADMINISTRACIÓN DEL TALLER (cartucho ERP-lite).

FASE 1: Precios y materiales/artículos editables (actualizar costos y utilidad).
Escribe sobre CONFIG/precios_base.json (el mismo que usa el cotizador → los cambios
aplican al instante). Cero simulación: datos reales, persistentes.

Preparado para crecer: Inventario (Fase 2) y Contabilidad/Balance (Fase 3).
"""
from __future__ import annotations
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRECIOS = ROOT / "CONFIG" / "precios_base.json"


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _load() -> dict:
    try:
        return json.loads(PRECIOS.read_text(encoding="utf-8"))
    except Exception:
        return {"laser": {"costo_minuto": 8.0, "materiales": []}}


def _save(d: dict) -> None:
    PRECIOS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ── PRECIOS / MATERIALES ─────────────────────────────────────────────
def listar_precios() -> dict:
    """Costo por minuto + lista de materiales/artículos con su precio de hoja."""
    laser = _load().get("laser", {})
    return {"status": "ok",
            "costo_minuto": float(laser.get("costo_minuto", 8.0)),
            "materiales": laser.get("materiales", [])}


def set_costo_minuto(valor: float) -> dict:
    """Actualiza el costo por minuto de máquina."""
    try:
        v = float(valor)
        if v < 0:
            return {"status": "error", "mensaje": "El costo por minuto no puede ser negativo."}
    except Exception:
        return {"status": "error", "mensaje": "Valor inválido."}
    d = _load()
    d.setdefault("laser", {})["costo_minuto"] = v
    _save(d)
    return {"status": "ok", "costo_minuto": v}


def guardar_material(nombre: str, precio_hoja: float, ancho: float = 122.0, alto: float = 244.0) -> dict:
    """Agrega un material/artículo nuevo, o actualiza el existente (por nombre)."""
    if not nombre or not nombre.strip():
        return {"status": "error", "mensaje": "El nombre es obligatorio."}
    try:
        precio = float(precio_hoja); a = float(ancho); h = float(alto)
        if precio < 0 or a <= 0 or h <= 0:
            return {"status": "error", "mensaje": "Precio ≥ 0 y medidas > 0."}
    except Exception:
        return {"status": "error", "mensaje": "Precio/medidas inválidos."}
    d = _load()
    mats = d.setdefault("laser", {}).setdefault("materiales", [])
    for m in mats:
        if _norm(m.get("nombre", "")) == _norm(nombre):
            m["precio_hoja"] = precio; m["ancho"] = a; m["alto"] = h
            _save(d)
            return {"status": "ok", "accion": "actualizado", "material": m}
    nuevo = {"nombre": nombre.strip(), "precio_hoja": precio, "ancho": a, "alto": h}
    mats.append(nuevo)
    _save(d)
    return {"status": "ok", "accion": "agregado", "material": nuevo}


def borrar_material(nombre: str) -> dict:
    """Elimina un material/artículo por nombre."""
    d = _load()
    mats = d.setdefault("laser", {}).get("materiales", [])
    antes = len(mats)
    d["laser"]["materiales"] = [m for m in mats if _norm(m.get("nombre", "")) != _norm(nombre)]
    _save(d)
    quitados = antes - len(d["laser"]["materiales"])
    return {"status": "ok" if quitados else "no_encontrado", "borrados": quitados}


if __name__ == "__main__":
    print(json.dumps(listar_precios(), ensure_ascii=False, indent=2))
