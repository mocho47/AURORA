# -*- coding: utf-8 -*-
"""
AURORA · INVENTARIO del taller (EXISTENCIAS reales)

Filosofía honesta (regla de Anuar: 0 simulaciones):
- Este módulo es EL SISTEMA de existencias: altas de materiales, movimientos
  (entradas/salidas), historial y alertas de stock bajo.
- Las EXISTENCIAS las captura Anuar en el taller físico (conteo real). Aquí solo
  se registran y se llevan al día. Nada se inventa.
- Inventario = EXISTENCIAS (cuánto hay). NO es precios/costos de cotización:
  eso ya vive en TALLER/administracion.py y NO se duplica aquí. El costo_unitario
  que se guarda es solo para valorizar el inventario (Σ cantidad×costo).

Materiales típicos del taller: MDF, acrílico, termos, playeras, tintas, vinil, etc.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "inventario.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT DEFAULT '',
            talla TEXT DEFAULT '',
            color TEXT DEFAULT '',
            unidad TEXT DEFAULT 'pz',
            cantidad REAL DEFAULT 0,
            minimo REAL DEFAULT 0,
            costo_unitario REAL DEFAULT 0,
            creado TEXT,
            actualizado TEXT,
            UNIQUE(nombre, categoria, talla, color)
        )""")
    # Migración de esquema viejo (UNIQUE sin talla/color impedía el mismo
    # artículo en varias tallas/colores). Se recrea la tabla con el esquema nuevo.
    cols = [r[1] for r in con.execute("PRAGMA table_info(items)").fetchall()]
    if "talla" not in cols or "color" not in cols:
        # Respaldo real antes de una migración destructiva (nunca DROP sin respaldo).
        import json as _json
        backup_dir = ROOT / ".ide_backups"
        backup_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        viejos_items = [dict(r) for r in con.execute("SELECT * FROM items").fetchall()]
        try:
            viejos_mov = [dict(r) for r in con.execute("SELECT * FROM movimientos").fetchall()]
        except sqlite3.OperationalError:
            viejos_mov = []
        if viejos_items or viejos_mov:
            (backup_dir / f"inventario_pre_migracion.{ts}.bak.json").write_text(
                _json.dumps({"items": viejos_items, "movimientos": viejos_mov}, ensure_ascii=False, indent=2),
                encoding="utf-8")
        con.execute("DROP TABLE IF EXISTS items")
        con.execute("DROP TABLE IF EXISTS movimientos")
        con.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT DEFAULT '',
                talla TEXT DEFAULT '',
                color TEXT DEFAULT '',
                unidad TEXT DEFAULT 'pz',
                cantidad REAL DEFAULT 0,
                minimo REAL DEFAULT 0,
                costo_unitario REAL DEFAULT 0,
                creado TEXT,
                actualizado TEXT,
                UNIQUE(nombre, categoria, talla, color)
            )""")
    con.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            delta REAL NOT NULL,
            saldo REAL NOT NULL,
            motivo TEXT DEFAULT '',
            fecha TEXT,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )""")
    con.commit()
    con.close()


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def agregar_item(nombre, categoria="", unidad="pz", cantidad=0,
                 minimo=0, costo_unitario=0, talla="", color="") -> dict:
    """
    Alta de un material. Identidad = nombre + categoría + TALLA/MEDIDA + COLOR,
    para que el mismo artículo en distinta talla o color sea una línea aparte
    (ej. Playera blanca CH / M / G, o MDF 2.7mm / 3mm / 6mm).
    Si ya existe esa combinación, SUMA la cantidad y la registra en el historial.
    """
    nombre = (nombre or "").strip()
    categoria = (categoria or "").strip()
    talla = (talla or "").strip()
    color = (color or "").strip()
    if not nombre:
        return {"status": "error", "mensaje": "El nombre es obligatorio."}
    try:
        cantidad = float(cantidad)
        minimo = float(minimo)
        costo_unitario = float(costo_unitario)
    except (TypeError, ValueError):
        return {"status": "error", "mensaje": "cantidad/mínimo/costo deben ser numéricos."}

    init_db()
    con = _conn()
    row = con.execute(
        "SELECT * FROM items WHERE nombre=? AND categoria=? AND talla=? AND color=?",
        (nombre, categoria, talla, color)
    ).fetchone()

    if row:
        nueva = float(row["cantidad"]) + cantidad
        if nueva < 0:
            con.close()
            return {"status": "sin_stock",
                    "mensaje": f"Existencia insuficiente: hay {row['cantidad']} {row['unidad']}, "
                               f"no se puede aplicar {cantidad} (quedaría negativo).",
                    "existencia": float(row["cantidad"])}
        con.execute(
            "UPDATE items SET unidad=?, minimo=?, costo_unitario=?, cantidad=?, actualizado=? WHERE id=?",
            (unidad or row["unidad"], minimo, costo_unitario, nueva, _ahora(), row["id"]))
        if cantidad:
            con.execute(
                "INSERT INTO movimientos (item_id, delta, saldo, motivo, fecha) VALUES (?,?,?,?,?)",
                (row["id"], cantidad, nueva, "alta/reabasto", _ahora()))
        con.commit()
        iid = row["id"]
        con.close()
        return {"status": "actualizado", "item_id": iid, "nombre": nombre,
                "categoria": categoria, "cantidad": nueva}

    now = _ahora()
    cur = con.execute(
        "INSERT INTO items (nombre, categoria, talla, color, unidad, cantidad, minimo, costo_unitario, creado, actualizado) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nombre, categoria, talla, color, unidad, cantidad, minimo, costo_unitario, now, now))
    iid = cur.lastrowid
    if cantidad:
        con.execute(
            "INSERT INTO movimientos (item_id, delta, saldo, motivo, fecha) VALUES (?,?,?,?,?)",
            (iid, cantidad, cantidad, "alta inicial", now))
    con.commit()
    con.close()
    return {"status": "creado", "item_id": iid, "nombre": nombre,
            "categoria": categoria, "cantidad": cantidad}


def editar_item(item_id, nombre=None, categoria=None, talla=None, color=None,
                unidad=None, minimo=None, costo_unitario=None) -> dict:
    """Edita los datos de un artículo EXISTENTE (color, talla, unidad, mínimo, costo).
    La CANTIDAD no se toca aquí — esa se mueve con entradas/salidas para que quede historial."""
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return {"status": "error", "mensaje": "item_id inválido."}
    init_db()
    con = _conn()
    row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        con.close()
        return {"status": "no_encontrado", "mensaje": f"No existe item id={item_id}."}

    n = (nombre if nombre is not None else row["nombre"]).strip()
    c = (categoria if categoria is not None else row["categoria"] or "").strip()
    t = (talla if talla is not None else row["talla"] or "").strip()
    col = (color if color is not None else row["color"] or "").strip()
    u = (unidad if unidad is not None else row["unidad"] or "pz").strip()
    if not n:
        con.close()
        return {"status": "error", "mensaje": "El nombre es obligatorio."}
    try:
        mi = float(minimo) if minimo is not None else float(row["minimo"])
        co = float(costo_unitario) if costo_unitario is not None else float(row["costo_unitario"])
    except (TypeError, ValueError):
        con.close()
        return {"status": "error", "mensaje": "mínimo/costo deben ser numéricos."}

    # Evitar chocar con otro artículo que ya tenga esa misma combinación
    dup = con.execute(
        "SELECT id FROM items WHERE nombre=? AND categoria=? AND talla=? AND color=? AND id<>?",
        (n, c, t, col, item_id)).fetchone()
    if dup:
        con.close()
        return {"status": "duplicado",
                "mensaje": f"Ya existe otro artículo con esa combinación (nombre/categoría/talla/color)."}

    con.execute("UPDATE items SET nombre=?, categoria=?, talla=?, color=?, unidad=?, "
                "minimo=?, costo_unitario=?, actualizado=? WHERE id=?",
                (n, c, t, col, u, mi, co, _ahora(), item_id))
    con.commit()
    con.close()
    return {"status": "ok", "item_id": item_id,
            "mensaje": f"Actualizado: {n}" + (f" · {t}" if t else "") + (f" · {col}" if col else "")}


def borrar_item(item_id) -> dict:
    """Borra UN artículo del inventario y su historial de movimientos."""
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return {"status": "error", "mensaje": "item_id inválido."}
    init_db()
    con = _conn()
    row = con.execute("SELECT nombre FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        con.close()
        return {"status": "no_encontrado", "mensaje": f"No existe item id={item_id}."}
    nombre = row["nombre"]
    con.execute("DELETE FROM movimientos WHERE item_id=?", (item_id,))
    con.execute("DELETE FROM items WHERE id=?", (item_id,))
    con.commit()
    con.close()
    return {"status": "ok", "mensaje": f"Borrado: {nombre}"}


def limpiar_todo() -> dict:
    """Vacía TODO el inventario (artículos + movimientos). Acción deliberada."""
    init_db()
    con = _conn()
    n = con.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    con.execute("DELETE FROM movimientos")
    con.execute("DELETE FROM items")
    con.commit()
    con.close()
    return {"status": "ok", "borrados": n, "mensaje": f"Inventario vaciado ({n} artículos)."}


# ── Catálogo base de Milens + ATF (se siembra con cantidad 0 para capturar) ──
TALLAS_ROPA = ["CH", "M", "G", "XG", "XXL"]


def _catalogo_base() -> list:
    """Artículos REALES de Milens y ATF, listos para que Anuar solo ponga cantidades.
    talla = talla de ropa O medida del material. color = libre (termos, vinil, etc.)."""
    items = []
    # ── MILENS · Prendas (por talla) ──
    for pren, costo in (("Playera blanca poliéster (sublimar)", 60),
                        ("Playera polo manga corta", 90),
                        ("Playera cuello redondo", 80)):
        for t in TALLAS_ROPA:
            items.append({"nombre": pren, "categoria": "Prendas", "talla": t,
                          "unidad": "pz", "minimo": 3, "costo_unitario": costo})
    items.append({"nombre": "Boxer blanco poliéster", "categoria": "Prendas",
                  "talla": "Unitalla", "unidad": "pz", "minimo": 3, "costo_unitario": 70})
    # ── MILENS · Gorras ──
    for g in ("Gorra para sublimar", "Gorra para bordado/DTF"):
        items.append({"nombre": g, "categoria": "Gorras", "talla": "Unitalla",
                      "unidad": "pz", "minimo": 5, "costo_unitario": 25})
    # ── MILENS · Termos (color lo escribe Anuar) ──
    for oz in ("18oz", "20oz", "30oz"):
        items.append({"nombre": "Termo acero", "categoria": "Termos", "talla": oz,
                      "unidad": "pz", "minimo": 3, "costo_unitario": 0})
    items.append({"nombre": "Taza cerámica", "categoria": "Termos y tazas", "talla": "11oz",
                  "unidad": "pz", "minimo": 5, "costo_unitario": 0})
    items.append({"nombre": "Taza cerámica", "categoria": "Termos y tazas", "talla": "15oz",
                  "unidad": "pz", "minimo": 3, "costo_unitario": 0})
    # ── MATERIALES en HOJAS (costos REALES de precios_base.json) ──
    for nom, esp, costo in (("MDF", "2.7mm", 110), ("MDF", "5.5mm", 280),
                            ("Multiplay", "4mm", 350)):
        items.append({"nombre": nom, "categoria": "Materiales", "talla": esp,
                      "unidad": "hoja", "minimo": 2, "costo_unitario": costo})
    # ── MATERIALES · Acrílico en M² (hoja 120x180 = 2.16 m² → costo por m²) ──
    for esp, costo_hoja in (("3mm Color", 900), ("3mm Transparente", 800), ("6mm", 1800)):
        items.append({"nombre": "Acrílico", "categoria": "Materiales", "talla": esp,
                      "unidad": "m2", "minimo": 1,
                      "costo_unitario": round(costo_hoja / 2.16, 2)})
    # ── INSUMOS textiles (por metro, precios reales de precios_base) ──
    for nom, costo in (("DTF", 300), ("DTF UV", 550), ("Vinil textil", 180), ("Bifaz", 80)):
        items.append({"nombre": nom, "categoria": "Insumos textiles", "talla": "",
                      "unidad": "metro", "minimo": 1, "costo_unitario": costo})
    # ── ATF · Proyectores Bi-LED y accesorios (lo que se stockea) ──
    for x in ("X1 3\"", "X2 3\"", "X3 3\"", "X4 3\"", "X5 2.5\"", "X6 3\"", "X7 3\" (nieblas)"):
        items.append({"nombre": f"Proyector Bi-LED {x}", "categoria": "ATF · Proyectores",
                      "talla": "", "unidad": "pz", "minimo": 1, "costo_unitario": 0})
    for a, costo in (("Tiras Secuenciales Premium", 2300), ("Tiras Secuenciales Std", 1600),
                     ("Ojos Demonio (1 Color)", 500), ("Ojos Demonio RGB BT", 1500),
                     ("Fibra Óptica Interior", 2000), ("LED H4 Premium", 1850),
                     ("LED H7 Premium", 1850), ("LED Intermedio (General)", 950)):
        items.append({"nombre": a, "categoria": "ATF · Accesorios", "talla": "",
                      "unidad": "pz", "minimo": 1, "costo_unitario": costo})
    return items


def sembrar_catalogo() -> dict:
    """Precarga los artículos de Milens y ATF con cantidad 0 (solo faltan cantidades).
    No duplica: si el artículo ya existe (nombre+categoría+talla+color), lo respeta."""
    init_db()
    creados, existentes = 0, 0
    for it in _catalogo_base():
        con = _conn()
        row = con.execute(
            "SELECT id FROM items WHERE nombre=? AND categoria=? AND talla=? AND color=?",
            (it["nombre"], it["categoria"], it.get("talla", ""), "")).fetchone()
        con.close()
        if row:
            existentes += 1
            continue
        agregar_item(it["nombre"], it["categoria"], it.get("unidad", "pz"), 0,
                     it.get("minimo", 0), it.get("costo_unitario", 0),
                     it.get("talla", ""), "")
        creados += 1
    return {"status": "ok", "creados": creados, "ya_existian": existentes,
            "mensaje": f"Catálogo sembrado: {creados} artículos nuevos listos para capturar cantidades."}


def movimiento(item_id, delta, motivo="") -> dict:
    """
    Entrada(+) / salida(-) de existencias. Registra el movimiento en el historial.
    NO permite que la existencia quede negativa (avisa y no aplica el movimiento).
    """
    try:
        item_id = int(item_id)
        delta = float(delta)
    except (TypeError, ValueError):
        return {"status": "error", "mensaje": "item_id/delta inválidos."}
    if delta == 0:
        return {"status": "error", "mensaje": "El movimiento no puede ser 0."}

    init_db()
    con = _conn()
    row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        con.close()
        return {"status": "no_encontrado", "mensaje": f"No existe item id={item_id}."}

    saldo = float(row["cantidad"]) + delta
    if saldo < 0:
        con.close()
        return {"status": "sin_stock",
                "mensaje": f"Existencia insuficiente: hay {row['cantidad']} {row['unidad']}, "
                           f"pide salida de {abs(delta)}.",
                "existencia": float(row["cantidad"])}

    now = _ahora()
    con.execute("UPDATE items SET cantidad=?, actualizado=? WHERE id=?", (saldo, now, item_id))
    con.execute(
        "INSERT INTO movimientos (item_id, delta, saldo, motivo, fecha) VALUES (?,?,?,?,?)",
        (item_id, delta, saldo, (motivo or "").strip(), now))
    con.commit()
    con.close()
    return {"status": "ok", "item_id": item_id, "delta": delta,
            "existencia": saldo, "tipo": "entrada" if delta > 0 else "salida"}


def listar(categoria="") -> dict:
    init_db()
    con = _conn()
    if categoria:
        rows = con.execute(
            "SELECT * FROM items WHERE categoria=? ORDER BY nombre", (categoria.strip(),)
        ).fetchall()
    else:
        rows = con.execute("SELECT * FROM items ORDER BY categoria, nombre").fetchall()
    con.close()
    items = []
    for r in rows:
        items.append({
            "id": r["id"], "nombre": r["nombre"], "categoria": r["categoria"],
            "talla": r["talla"] or "", "color": r["color"] or "",
            "unidad": r["unidad"], "cantidad": float(r["cantidad"]),
            "minimo": float(r["minimo"]), "costo_unitario": float(r["costo_unitario"]),
            "valor": round(float(r["cantidad"]) * float(r["costo_unitario"]), 2),
            "bajo_minimo": float(r["cantidad"]) <= float(r["minimo"]),
            "actualizado": r["actualizado"],
        })
    return {"status": "ok", "total": len(items), "items": items}


def bajo_minimo() -> dict:
    init_db()
    con = _conn()
    rows = con.execute(
        "SELECT * FROM items WHERE cantidad <= minimo ORDER BY categoria, nombre"
    ).fetchall()
    con.close()
    items = [{
        "id": r["id"], "nombre": r["nombre"], "categoria": r["categoria"],
        "unidad": r["unidad"], "cantidad": float(r["cantidad"]),
        "minimo": float(r["minimo"]),
        "faltante": round(float(r["minimo"]) - float(r["cantidad"]), 3),
    } for r in rows]
    return {"status": "ok", "total": len(items), "items": items}


def historial(item_id) -> dict:
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return {"status": "error", "mensaje": "item_id inválido."}
    init_db()
    con = _conn()
    item = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not item:
        con.close()
        return {"status": "no_encontrado", "mensaje": f"No existe item id={item_id}."}
    rows = con.execute(
        "SELECT * FROM movimientos WHERE item_id=? ORDER BY id DESC", (item_id,)
    ).fetchall()
    con.close()
    movs = [{
        "id": r["id"], "delta": float(r["delta"]), "saldo": float(r["saldo"]),
        "motivo": r["motivo"], "fecha": r["fecha"],
        "tipo": "entrada" if float(r["delta"]) > 0 else "salida",
    } for r in rows]
    return {"status": "ok", "item_id": item_id, "nombre": item["nombre"],
            "total": len(movs), "movimientos": movs}


def resumen() -> dict:
    init_db()
    con = _conn()
    rows = con.execute("SELECT cantidad, costo_unitario, minimo FROM items").fetchall()
    con.close()
    n = len(rows)
    valor = round(sum(float(r["cantidad"]) * float(r["costo_unitario"]) for r in rows), 2)
    bajos = sum(1 for r in rows if float(r["cantidad"]) <= float(r["minimo"]))
    return {"status": "ok", "n_items": n, "valor_total": valor, "bajo_minimo": bajos}


# ---------------------------------------------------------------------------
# Prueba standalone (datos reales de ejemplo; se limpian al final)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    def _p(t, d):
        print(f"\n=== {t} ===")
        print(json.dumps(d, ensure_ascii=False, indent=2))

    # DB de prueba aislada para no tocar producción
    DB = ROOT / "inventario_test.db"
    if DB.exists():
        DB.unlink()
    for ext in ("-wal", "-shm"):
        p = Path(str(DB) + ext)
        if p.exists():
            p.unlink()

    init_db()

    a = agregar_item("MDF 3mm 60x40", "Madera", "hoja", cantidad=20, minimo=5, costo_unitario=45)
    b = agregar_item("Termo acero 18oz Bala", "Termos", "pz", cantidad=8, minimo=10, costo_unitario=110)
    c = agregar_item("Playera algodón blanca M", "Textil", "pz", cantidad=50, minimo=15, costo_unitario=38)
    _p("agregar_item x3", [a, b, c])

    # reabasto de un existente (suma + historial)
    _p("agregar_item existente (reabasto)",
       agregar_item("MDF 3mm 60x40", "Madera", "hoja", cantidad=10, minimo=5, costo_unitario=45))

    _p("salida MDF (usa 12 hojas)", movimiento(a["item_id"], -12, "Orden #1042 cajas"))
    _p("salida Termos (usa 3)", movimiento(b["item_id"], -3, "Sublimación pedido Rocío"))
    _p("salida imposible (stock negativo)", movimiento(b["item_id"], -50, "prueba tope"))
    _p("entrada Termos (llega compra)", movimiento(b["item_id"], 20, "Compra proveedor"))

    _p("listar TODO", listar())
    _p("listar categoría Termos", listar("Termos"))
    _p("bajo_minimo", bajo_minimo())
    _p("historial MDF", historial(a["item_id"]))
    _p("resumen", resumen())

    # limpieza: borra la DB de prueba
    con = _conn()
    con.close()
    for ext in ("", "-wal", "-shm"):
        p = Path(str(DB) + ext)
        if p.exists():
            p.unlink()
    print("\n[OK] Prueba completa. DB de prueba eliminada. La DB real (inventario.db) NO se tocó.")
