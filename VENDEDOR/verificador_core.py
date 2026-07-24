# -*- coding: utf-8 -*-
"""VERIFICADOR de AURORA — capa de calidad anti-errores (anti 'inventar/incongruente').
Revisa lo que el motor autocompleta y DEGRADA a PENDIENTE lo incoherente, en vez de
darlo por bueno. Ej: ficha 'LED H4' que en su texto habla de 'H7' -> incoherente -> PENDIENTE.
Regla de oro: si no es coherente y verificable, NO se marca COMPLETA.
"""
from __future__ import annotations
import json, unicodedata as _ud
from pathlib import Path

FICHAS = Path(__file__).resolve().parent.parent / "CONFIG" / "fichas_tecnicas.json"
MODELOS_FARO = ["h1", "h3", "h4", "h7", "h8", "h11", "h13", "9005", "9006", "880", "d2s", "d4s"]


def _norm(s) -> str:
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    return "".join(c for c in _ud.normalize("NFD", s.lower()) if _ud.category(c) != "Mn")


def verificar_ficha(f: dict) -> list:
    """Devuelve lista de incoherencias detectadas (vacía = ok)."""
    issues = []
    nombre = _norm(f.get("nombre", ""))
    texto = _norm(f.get("que_es", "")) + " " + _norm(f.get("diferencias", "")) + " " + _norm(f.get("specs", {}))
    # 1) Modelo de faro: el del texto no debe contradecir el del nombre
    mod_nom = [m for m in MODELOS_FARO if m in nombre]
    if mod_nom:
        mod_txt = [m for m in MODELOS_FARO if m in texto]
        conflicto = [m for m in mod_txt if m not in mod_nom]
        if conflicto:
            issues.append(f"texto menciona modelo {conflicto} pero el producto es {mod_nom}")
    # 2) Tamaño en oz (termos/tazas): no debe contradecir
    import re
    oz_nom = re.findall(r"(\d+)\s*oz", nombre)
    if oz_nom:
        oz_txt = re.findall(r"(\d+)\s*oz", texto)
        if oz_txt and not set(oz_nom) & set(oz_txt):
            issues.append(f"oz del texto {oz_txt} no coincide con el producto {oz_nom}")
    # 3) que_es demasiado corto para ser COMPLETA
    if f.get("estado_ficha") == "COMPLETA" and len(f.get("que_es", "").strip()) < 25:
        issues.append("que_es muy corto para COMPLETA")
    return issues


def verificar_todas(degradar: bool = True) -> dict:
    """Revisa todo el catálogo. Si degradar=True, baja a PENDIENTE lo incoherente y limpia
    los campos auto-llenados malos (para que se vuelva a investigar bien)."""
    try:
        d = json.loads(FICHAS.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}
    reporte = []
    for f in d.get("fichas", []):
        issues = verificar_ficha(f)
        if issues:
            reporte.append({"ficha": f.get("nombre"), "estado_previo": f.get("estado_ficha"), "problemas": issues})
            if degradar:
                f["estado_ficha"] = "PENDIENTE"
                f["que_es"] = ""; f["diferencias"] = ""; f["specs"] = {}
                f["instalacion"] = {"dificultad": "", "tiempo_aprox": "", "requiere": [], "pasos": []}
                f["recomendado_para"] = ""; f["argumentos_venta"] = []; f["fuentes"] = []
                f["nota_verificacion"] = "Degradada por incoherencia: " + "; ".join(issues)
    if degradar and reporte:
        FICHAS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "OK", "incoherentes": len(reporte), "detalle": reporte,
            "nota": "Lo incoherente se mandó a PENDIENTE; no se da por bueno lo dudoso."}


if __name__ == "__main__":
    import sys
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    r = verificar_todas(degradar=True)
    print(json.dumps(r, ensure_ascii=False, indent=2))
