# -*- coding: utf-8 -*-
"""
REPORTES / INTELIGENCIA DE NEGOCIO — AURORA v3  (cartucho self-contained)
Datos 100% REALES de taller.db (tabla `ordenes`). NO inventa nada:
- Detecta columnas existentes con PRAGMA table_info y se adapta.
- Si una columna no existe o no hay datos, devuelve un reporte vacío honesto.

Funciones públicas (todas devuelven dict con clave "status":
    "ok" | "vacio" | "error"):
    resumen_general()
    por_mes()
    top_productos(n=10)
    por_solicitante()
    estados()
    oportunidades()
    reporte_completo()   # conveniencia: junta todo

Patrón AURORA (bus neuronal): también expone process_query() / requiere_contexto().
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "taller.db"


# ── utilidades internas ───────────────────────────────────────────────
def _cols():
    """Columnas REALES de la tabla ordenes (vacío si no existe)."""
    if not DB.exists():
        return set()
    con = sqlite3.connect(str(DB))
    try:
        existe = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ordenes'"
        ).fetchone()
        if not existe:
            return set()
        return {r[1] for r in con.execute("PRAGMA table_info(ordenes)").fetchall()}
    finally:
        con.close()


def _rows():
    """Todas las filas como lista de dicts (solo columnas reales)."""
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("SELECT * FROM ordenes").fetchall()]
    finally:
        con.close()


def _num(v):
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _pct(parte, total):
    return round(parte / total * 100, 1) if total else 0.0


def _dinero(v):
    return f"${v:,.0f}"


def _mes_de(row, cols):
    """AAAA-MM a partir de 'creado' o, en su defecto, 'fecha_entrega'."""
    for campo in ("creado", "fecha_entrega", "fecha_inicio"):
        if campo in cols and row.get(campo):
            s = str(row[campo])
            if len(s) >= 7 and s[4] == "-":
                return s[:7]
    return "sin_fecha"


def _sin_datos(cols):
    """True si no hay tabla o no hay filas."""
    if not cols:
        return True
    con = sqlite3.connect(str(DB))
    try:
        return con.execute("SELECT COUNT(*) FROM ordenes").fetchone()[0] == 0
    finally:
        con.close()


# ── 1. RESUMEN GENERAL ────────────────────────────────────────────────
def resumen_general():
    cols = _cols()
    if _sin_datos(cols):
        return {"status": "vacio", "mensaje": "No hay órdenes registradas todavía.",
                "n_ordenes": 0}
    rows = _rows()
    n = len(rows)
    ingresos = sum(_num(r.get("valor_total")) for r in rows) if "valor_total" in cols else 0.0
    costos = sum(_num(r.get("costo_real")) for r in rows) if "costo_real" in cols else 0.0
    # utilidad: usa columna si existe y aporta datos; si no, deriva ingresos-costos
    util_col = sum(_num(r.get("utilidad")) for r in rows) if "utilidad" in cols else 0.0
    utilidad = util_col if util_col else (ingresos - costos)
    cobrado = sum(_num(r.get("anticipo")) for r in rows) if "anticipo" in cols else 0.0
    por_cobrar = sum(_num(r.get("saldo")) for r in rows) if "saldo" in cols else 0.0
    return {
        "status": "ok",
        "n_ordenes": n,
        "ingresos": round(ingresos, 2),
        "costos": round(costos, 2),
        "utilidad": round(utilidad, 2),
        "margen_pct": _pct(utilidad, ingresos),
        "cobrado": round(cobrado, 2),
        "por_cobrar": round(por_cobrar, 2),
        "ticket_promedio": round(ingresos / n, 2) if n else 0.0,
        "nota_costos": ("Costos capturados en 0 — la utilidad mostrada asume "
                        "ingresos completos." if not costos else ""),
    }


# ── 2. POR MES ────────────────────────────────────────────────────────
def por_mes():
    cols = _cols()
    if _sin_datos(cols):
        return {"status": "vacio", "meses": []}
    rows = _rows()
    agg = {}
    for r in rows:
        m = _mes_de(r, cols)
        a = agg.setdefault(m, {"mes": m, "n_ordenes": 0, "ingresos": 0.0,
                               "costos": 0.0, "utilidad": 0.0})
        a["n_ordenes"] += 1
        a["ingresos"] += _num(r.get("valor_total")) if "valor_total" in cols else 0.0
        a["costos"] += _num(r.get("costo_real")) if "costo_real" in cols else 0.0
        a["utilidad"] += _num(r.get("utilidad")) if "utilidad" in cols else 0.0
    meses = []
    for m in sorted(agg):
        a = agg[m]
        util = a["utilidad"] if a["utilidad"] else (a["ingresos"] - a["costos"])
        meses.append({
            "mes": a["mes"],
            "n_ordenes": a["n_ordenes"],
            "ingresos": round(a["ingresos"], 2),
            "costos": round(a["costos"], 2),
            "utilidad": round(util, 2),
            "margen_pct": _pct(util, a["ingresos"]),
        })
    return {"status": "ok", "meses": meses}


# ── 3. TOP PRODUCTOS ──────────────────────────────────────────────────
def top_productos(n=10):
    cols = _cols()
    if "producto" not in cols:
        return {"status": "vacio",
                "mensaje": "La tabla no tiene columna 'producto'.", "productos": []}
    if _sin_datos(cols):
        return {"status": "vacio", "productos": []}
    rows = _rows()
    agg = {}
    for r in rows:
        p = (r.get("producto") or "").strip() or "(sin producto)"
        a = agg.setdefault(p, {"producto": p, "n_ordenes": 0, "piezas": 0,
                               "ingresos": 0.0, "utilidad": 0.0})
        a["n_ordenes"] += 1
        a["piezas"] += int(_num(r.get("piezas"))) if "piezas" in cols else 0
        a["ingresos"] += _num(r.get("valor_total")) if "valor_total" in cols else 0.0
        a["utilidad"] += _num(r.get("utilidad")) if "utilidad" in cols else 0.0
    lst = list(agg.values())
    por_frecuencia = sorted(lst, key=lambda x: (-x["n_ordenes"], -x["ingresos"]))[:n]
    por_utilidad = sorted(lst, key=lambda x: -x["utilidad"])[:n]
    return {
        "status": "ok",
        "por_frecuencia": [
            {**p, "ingresos": round(p["ingresos"], 2),
             "utilidad": round(p["utilidad"], 2)} for p in por_frecuencia],
        "por_utilidad": [
            {**p, "ingresos": round(p["ingresos"], 2),
             "utilidad": round(p["utilidad"], 2)} for p in por_utilidad],
    }


# ── 4. POR SOLICITANTE ────────────────────────────────────────────────
def por_solicitante():
    cols = _cols()
    if "solicitante" not in cols:
        return {"status": "vacio",
                "mensaje": "La tabla no tiene columna 'solicitante'.", "solicitantes": []}
    if _sin_datos(cols):
        return {"status": "vacio", "solicitantes": []}
    rows = _rows()
    agg = {}
    for r in rows:
        s = (r.get("solicitante") or "").strip() or "(sin solicitante)"
        a = agg.setdefault(s, {"solicitante": s, "n_ordenes": 0, "ingresos": 0.0,
                               "utilidad": 0.0, "por_cobrar": 0.0})
        a["n_ordenes"] += 1
        a["ingresos"] += _num(r.get("valor_total")) if "valor_total" in cols else 0.0
        a["utilidad"] += _num(r.get("utilidad")) if "utilidad" in cols else 0.0
        a["por_cobrar"] += _num(r.get("saldo")) if "saldo" in cols else 0.0
    lst = []
    for a in agg.values():
        util = a["utilidad"]
        lst.append({
            "solicitante": a["solicitante"],
            "n_ordenes": a["n_ordenes"],
            "ingresos": round(a["ingresos"], 2),
            "utilidad": round(util, 2),
            "margen_pct": _pct(util, a["ingresos"]),
            "por_cobrar": round(a["por_cobrar"], 2),
        })
    lst.sort(key=lambda x: -x["ingresos"])
    return {"status": "ok", "solicitantes": lst}


# ── 5. ESTADOS ────────────────────────────────────────────────────────
def estados():
    cols = _cols()
    if "estado" not in cols:
        return {"status": "vacio",
                "mensaje": "La tabla no tiene columna 'estado'.", "estados": []}
    if _sin_datos(cols):
        return {"status": "vacio", "estados": []}
    rows = _rows()
    total = len(rows)
    agg = {}
    for r in rows:
        e = (r.get("estado") or "").strip() or "(sin estado)"
        a = agg.setdefault(e, {"estado": e, "n_ordenes": 0, "por_cobrar": 0.0})
        a["n_ordenes"] += 1
        a["por_cobrar"] += _num(r.get("saldo")) if "saldo" in cols else 0.0
    lst = [{
        "estado": a["estado"],
        "n_ordenes": a["n_ordenes"],
        "pct": _pct(a["n_ordenes"], total),
        "por_cobrar": round(a["por_cobrar"], 2),
    } for a in agg.values()]
    lst.sort(key=lambda x: -x["n_ordenes"])
    return {"status": "ok", "total": total, "estados": lst}


# ── 6. OPORTUNIDADES (insights derivados SOLO de los números) ──────────
def oportunidades():
    cols = _cols()
    if _sin_datos(cols):
        return {"status": "vacio", "insights": [],
                "mensaje": "Sin datos: registra órdenes para generar insights."}
    rg = resumen_general()
    ins = []

    # 1) Dinero por cobrar (cuenta órdenes con saldo>0 real)
    if rg.get("por_cobrar", 0) > 0:
        n_pend = (sum(1 for r in _rows() if _num(r.get("saldo")) > 0)
                  if "saldo" in cols else 0)
        ins.append({
            "tipo": "cobranza",
            "prioridad": "alta",
            "mensaje": f"{_dinero(rg['por_cobrar'])} por cobrar"
                       + (f" en {n_pend} orden(es) con saldo." if n_pend else "."),
        })

    # 2) Costos sin capturar → utilidad no confiable
    if rg.get("ingresos", 0) > 0 and rg.get("costos", 0) == 0:
        ins.append({
            "tipo": "datos",
            "prioridad": "media",
            "mensaje": "No hay costos capturados (costo_real = 0). El margen real "
                       "es desconocido; captura costos para medir utilidad verdadera.",
        })

    # 3) Margen global bajo (solo si hay costos reales)
    if rg.get("costos", 0) > 0 and rg.get("margen_pct", 0) < 30:
        ins.append({
            "tipo": "margen",
            "prioridad": "alta",
            "mensaje": f"Margen global bajo: {rg['margen_pct']}%. Revisa precios o costos.",
        })

    # 4) Producto de menor margen (con costos reales)
    tp = top_productos(50)
    con_util = [p for p in tp.get("por_utilidad", []) if p["ingresos"] > 0]
    if rg.get("costos", 0) > 0 and con_util:
        peor = min(con_util, key=lambda p: _pct(p["utilidad"], p["ingresos"]))
        m = _pct(peor["utilidad"], peor["ingresos"])
        if m < 30:
            ins.append({
                "tipo": "margen",
                "prioridad": "media",
                "mensaje": f"Margen bajo en '{peor['producto']}': {m}% "
                           f"({_dinero(peor['utilidad'])} de {_dinero(peor['ingresos'])}).",
            })

    # 5) Producto estrella por frecuencia
    if tp.get("por_frecuencia"):
        top = tp["por_frecuencia"][0]
        if top["n_ordenes"] >= 2:
            ins.append({
                "tipo": "oportunidad",
                "prioridad": "info",
                "mensaje": f"Producto más pedido: '{top['producto']}' "
                           f"({top['n_ordenes']} órdenes, {_dinero(top['ingresos'])}). "
                           "Considera promoverlo o hacer paquetes.",
            })

    # 6) Órdenes canceladas
    est = estados()
    canc = next((e for e in est.get("estados", [])
                 if e["estado"].lower().startswith("cancel")), None)
    if canc and canc["n_ordenes"] > 0:
        ins.append({
            "tipo": "alerta",
            "prioridad": "media",
            "mensaje": f"{canc['n_ordenes']} orden(es) cancelada(s) "
                       f"({canc['pct']}% del total).",
        })

    if not ins:
        ins.append({
            "tipo": "info",
            "prioridad": "info",
            "mensaje": "Sin focos rojos con los datos actuales. "
                       f"{rg['n_ordenes']} orden(es), {_dinero(rg['ingresos'])} en ingresos.",
        })
    return {"status": "ok", "insights": ins}


# ── conveniencia ──────────────────────────────────────────────────────
def reporte_completo():
    return {
        "status": "ok",
        "resumen": resumen_general(),
        "por_mes": por_mes(),
        "top_productos": top_productos(),
        "por_solicitante": por_solicitante(),
        "estados": estados(),
        "oportunidades": oportunidades(),
    }


# ── patrón AURORA (bus neuronal) ──────────────────────────────────────
def requiere_contexto():
    return False


def process_query(query="", contexto=None):
    q = (query or "").lower()
    if "mes" in q:
        return por_mes()
    if "producto" in q:
        return top_productos()
    if "solicit" in q or "quien" in q or "vend" in q:
        return por_solicitante()
    if "estado" in q:
        return estados()
    if "oportun" in q or "insight" in q or "consejo" in q:
        return oportunidades()
    return resumen_general()


def execute(accion="resumen", **kw):
    return {
        "resumen": resumen_general,
        "mes": por_mes,
        "productos": lambda: top_productos(kw.get("n", 10)),
        "solicitante": por_solicitante,
        "estados": estados,
        "oportunidades": oportunidades,
        "completo": reporte_completo,
    }.get(accion, resumen_general)()


# ── prueba standalone ─────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    print("DB:", DB, "existe:", DB.exists())
    print("Columnas reales:", sorted(_cols()))
    print("\n=== resumen_general ===")
    print(json.dumps(resumen_general(), indent=2, ensure_ascii=False))
    print("\n=== por_mes ===")
    print(json.dumps(por_mes(), indent=2, ensure_ascii=False))
    print("\n=== top_productos ===")
    print(json.dumps(top_productos(), indent=2, ensure_ascii=False))
    print("\n=== por_solicitante ===")
    print(json.dumps(por_solicitante(), indent=2, ensure_ascii=False))
    print("\n=== estados ===")
    print(json.dumps(estados(), indent=2, ensure_ascii=False))
    print("\n=== oportunidades ===")
    print(json.dumps(oportunidades(), indent=2, ensure_ascii=False))
