# -*- coding: utf-8 -*-
"""
ÓRDENES DE TRABAJO DEL TALLER — AURORA v3
BD real (SQLite) + cotización determinista con precios REALES del catálogo
(NO inventa: si no encuentra el producto, lo dice y sugiere).
Alertas de entrega calculadas en vivo (agendado + 12h antes, recordatorio por hora).
Solicitantes: Samm (hija), Rocío (esposa), Anuar.
"""
import json
import sqlite3
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "taller.db"
CONFIG = ROOT / "CONFIG"

SOLICITANTES = ["Anuar", "Samm", "Rocío"]
ESTADOS = ["agendado", "en_proceso", "listo", "entregado", "cancelado"]


# ── BASE DE DATOS ─────────────────────────────────────────────────────
IMG_DIR = ROOT / "UPLOADS" / "ordenes"


def init_db() -> None:
    # Con timeout y WAL, igual que _con(). Era el ÚNICO punto del camino del
    # dinero que quedó sin el arreglo del 27-jul (commit 77423a0), y se llama al
    # inicio de CADA operación del taller: crear orden, editar, cambiar estado,
    # listar, alertas, contabilidad. Sin timeout se rendía a los 5 s por defecto,
    # que es justo como aparece "database is locked" en el log.
    con = sqlite3.connect(str(DB), timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE,
            solicitante TEXT NOT NULL,
            cliente TEXT NOT NULL,
            telefono TEXT,
            trabajo TEXT NOT NULL,
            piezas INTEGER DEFAULT 1,
            producto TEXT,
            precio_unitario REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            anticipo REAL DEFAULT 0,
            saldo REAL DEFAULT 0,
            fecha_inicio TEXT,
            fecha_entrega TEXT,
            estado TEXT DEFAULT 'agendado',
            notas TEXT DEFAULT '',
            imagenes TEXT DEFAULT '[]',
            creado TEXT
        )
    """)
    # Migración segura: agregar 'imagenes' si la tabla es de una versión previa
    cols = [r[1] for r in con.execute("PRAGMA table_info(ordenes)").fetchall()]
    for _col, _ddl in (("imagenes", "TEXT DEFAULT '[]'"),
                       ("costo_real", "REAL DEFAULT 0"),
                       ("utilidad", "REAL DEFAULT 0")):
        if _col not in cols:
            con.execute(f"ALTER TABLE ordenes ADD COLUMN {_col} {_ddl}")
    con.commit()
    con.close()
    IMG_DIR.mkdir(parents=True, exist_ok=True)


# ── IMÁGENES DE REFERENCIA ────────────────────────────────────────────
def guardar_imagen_bytes(nombre_original: str, datos: bytes) -> dict:
    """Guarda bytes de imagen subida. Devuelve la ruta relativa servible."""
    import uuid
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(nombre_original or "img.jpg").suffix.lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"):
        ext = ".jpg"
    fname = f"ref_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    (IMG_DIR / fname).write_bytes(datos)
    return {"status": "ok", "archivo": fname, "url": f"/uploads-ordenes/{fname}"}


def guardar_imagen_url(url: str) -> dict:
    """Descarga una imagen desde URL (Pinterest, etc.) y la guarda local."""
    import requests
    if not url or not url.startswith("http"):
        return {"status": "error", "mensaje": "URL inválida (arrastra desde Pinterest o pega un enlace http)."}
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200 or not r.headers.get("Content-Type", "").startswith("image"):
            return {"status": "error", "mensaje": f"No es una imagen descargable (HTTP {r.status_code}). Guárdala y arrástrala del explorador."}
        ext = "." + (r.headers["Content-Type"].split("/")[-1].split(";")[0])
        return guardar_imagen_bytes("img" + ext, r.content)
    except Exception as e:
        return {"status": "error", "mensaje": f"No se pudo descargar: {e}"}


def _con():
    con = sqlite3.connect(str(DB), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    return con


# ── CATÁLOGO / COTIZACIÓN (determinista, precios reales) ──────────────
def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return s


_CATALOGO_CACHE = None


def catalogo() -> list:
    """Combina catalogo_atf.json + fichas_tecnicas.json en una lista buscable."""
    global _CATALOGO_CACHE
    if _CATALOGO_CACHE is not None:
        return _CATALOGO_CACHE
    productos = []
    # ATF (106)
    try:
        d = json.loads((CONFIG / "catalogo_atf.json").read_text(encoding="utf-8"))
        prods = d.get("productos", d) if isinstance(d, dict) else d
        for p in prods:
            if p.get("precio"):
                productos.append({
                    "nombre": p.get("nombre", ""),
                    "precio": float(p.get("precio", 0)),
                    "negocio": p.get("negocio", "ATF"),
                    "categoria": p.get("categoria", ""),
                    "sku": p.get("sku", ""),
                })
    except Exception:
        pass
    # Fichas técnicas (29: termos, grabados, X1-X7, etc.)
    try:
        d = json.loads((CONFIG / "fichas_tecnicas.json").read_text(encoding="utf-8"))
        for f in d.get("fichas", []):
            if f.get("precio"):
                productos.append({
                    "nombre": f.get("nombre", ""),
                    "precio": float(f.get("precio", 0)),
                    "negocio": f.get("negocio", ""),
                    "categoria": f.get("categoria", ""),
                    "sku": f.get("id", ""),
                })
    except Exception:
        pass
    _CATALOGO_CACHE = productos
    return productos


def cotizar(producto: str, cantidad: int = 1) -> dict:
    """Busca precio REAL en el catálogo. Determinista, sin LLM, sin inventar."""
    q = _norm(producto)
    cat = catalogo()
    if not q:
        return {"status": "vacio", "mensaje": "Escribe un producto para cotizar."}
    # 1) match exacto por sku
    for p in cat:
        if q == _norm(p["sku"]) and p["sku"]:
            return _resultado(p, cantidad)
    # 2) match por nombre exacto
    for p in cat:
        if q == _norm(p["nombre"]):
            return _resultado(p, cantidad)
    # 3) substring (todas las palabras del query en el nombre)
    palabras = q.split()
    candidatos = [p for p in cat if all(w in _norm(p["nombre"]) or w in _norm(p["sku"]) for w in palabras)]
    if len(candidatos) == 1:
        return _resultado(candidatos[0], cantidad)
    if len(candidatos) > 1:
        return {
            "status": "varios",
            "mensaje": f"{len(candidatos)} coincidencias, especifica:",
            "opciones": [{"nombre": p["nombre"], "precio": p["precio"], "sku": p["sku"]} for p in candidatos[:8]],
        }
    # 4) no encontrado → honesto + sugerencias (NO inventa precio)
    sugerencias = [p["nombre"] for p in cat if palabras and palabras[0] in _norm(p["nombre"])][:6]
    return {
        "status": "no_encontrado",
        "mensaje": f"No encontré '{producto}' en el catálogo. No invento precios.",
        "sugerencias": sugerencias,
    }


def _resultado(p: dict, cantidad: int) -> dict:
    cantidad = max(1, int(cantidad or 1))
    subtotal = round(p["precio"] * cantidad, 2)
    return {
        "status": "ok",
        "producto": p["nombre"],
        "sku": p["sku"],
        "negocio": p["negocio"],
        "precio_unitario": p["precio"],
        "cantidad": cantidad,
        "subtotal": subtotal,
    }


# ── ÓRDENES ───────────────────────────────────────────────────────────
def crear_orden(data: dict) -> dict:
    init_db()
    solicitante = data.get("solicitante", "").strip()
    if solicitante not in SOLICITANTES:
        return {"status": "error", "mensaje": f"Solicitante inválido. Debe ser: {', '.join(SOLICITANTES)}"}
    cliente = (data.get("cliente") or "").strip()
    trabajo = (data.get("trabajo") or "").strip()
    if not cliente or not trabajo:
        return {"status": "error", "mensaje": "Cliente y trabajo solicitado son obligatorios."}

    piezas = int(data.get("piezas") or 1)
    valor_total = float(data.get("valor_total") or 0)
    costo_real = float(data.get("costo_real") or 0)
    utilidad = round(valor_total - costo_real, 2)
    anticipo = float(data.get("anticipo") or 0)
    saldo = round(valor_total - anticipo, 2)
    import uuid
    ahora = datetime.now()
    folio = "OT-" + ahora.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4].upper()

    imagenes = data.get("imagenes") or []
    if not isinstance(imagenes, list):
        imagenes = []
    con = _con()
    con.execute("""
        INSERT INTO ordenes (folio, solicitante, cliente, telefono, trabajo, piezas,
            producto, precio_unitario, valor_total, anticipo, saldo,
            fecha_inicio, fecha_entrega, estado, notas, imagenes, costo_real, utilidad, creado)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (folio, solicitante, cliente, data.get("telefono", ""), trabajo, piezas,
          data.get("producto", ""), float(data.get("precio_unitario") or 0),
          valor_total, anticipo, saldo,
          data.get("fecha_inicio", ""), data.get("fecha_entrega", ""),
          "agendado", data.get("notas", ""), json.dumps(imagenes),
          costo_real, utilidad, ahora.isoformat()))
    con.commit()
    con.close()
    return {"status": "ok", "folio": folio, "saldo": saldo, "utilidad": utilidad,
            "mensaje": f"Orden {folio} agendada por {solicitante}."}


def agregar_imagen_orden(orden_id: int, archivo: str) -> dict:
    """Añade una imagen (ya guardada) a una orden existente."""
    init_db()
    con = _con()
    row = con.execute("SELECT imagenes FROM ordenes WHERE id=?", (orden_id,)).fetchone()
    if not row:
        con.close()
        return {"status": "error", "mensaje": "Orden no encontrada"}
    try:
        imgs = json.loads(row["imagenes"] or "[]")
    except Exception:
        imgs = []
    imgs.append(archivo)
    con.execute("UPDATE ordenes SET imagenes=? WHERE id=?", (json.dumps(imgs), orden_id))
    con.commit()
    con.close()
    return {"status": "ok", "imagenes": imgs}


def listar_ordenes(estado: str = None, limite: int = 100) -> dict:
    init_db()
    con = _con()
    if estado and estado != "todas":
        rows = con.execute("SELECT * FROM ordenes WHERE estado=? ORDER BY fecha_entrega ASC, id DESC LIMIT ?",
                           (estado, limite)).fetchall()
    else:
        rows = con.execute("SELECT * FROM ordenes ORDER BY fecha_entrega ASC, id DESC LIMIT ?",
                           (limite,)).fetchall()
    con.close()
    ordenes = []
    for r in rows:
        o = dict(r)
        try:
            o["imagenes"] = json.loads(o.get("imagenes") or "[]")
        except Exception:
            o["imagenes"] = []
        ordenes.append(o)
    return {"status": "ok", "ordenes": ordenes, "total": len(ordenes)}


def editar_orden(orden_id: int, data: dict) -> dict:
    """Edita una orden EXISTENTE (mismo folio). Recalcula saldo y utilidad.
    Evita duplicar: en vez de crear otra orden, actualiza la actual."""
    init_db()
    con = _con()
    # BEGIN IMMEDIATE: se lee y se escribe DENTRO de la misma transacción.
    # Sin esto, dos ediciones simultáneas de la misma orden (Anuar en la PC y
    # Rocío en 192.168.1.38, por ejemplo) provocaban un "lost update": la
    # segunda pisaba a la primera. Y lo peor no era el choque — era que NO
    # TRUENA y NO QUEDA EN EL LOG. Un anticipo cobrado podía desaparecer del
    # saldo sin dejar rastro. Encontrado en la auditoría del 2026-08-02.
    con.execute("BEGIN IMMEDIATE")
    row = con.execute("SELECT * FROM ordenes WHERE id=?", (orden_id,)).fetchone()
    if not row:
        con.rollback()
        con.rollback()   # cierra la transacción abierta arriba
        con.close()
        return {"status": "error", "mensaje": "Orden no encontrada."}
    actual = dict(row)

    solicitante = (data.get("solicitante") or actual["solicitante"]).strip()
    if solicitante not in SOLICITANTES:
        con.rollback()   # cierra la transacción abierta arriba
        con.close()
        return {"status": "error", "mensaje": f"Solicitante inválido. Debe ser: {', '.join(SOLICITANTES)}"}
    cliente = (data.get("cliente") if data.get("cliente") is not None else actual["cliente"]).strip()
    trabajo = (data.get("trabajo") if data.get("trabajo") is not None else actual["trabajo"]).strip()
    if not cliente or not trabajo:
        con.rollback()   # cierra la transacción abierta arriba
        con.close()
        return {"status": "error", "mensaje": "Cliente y trabajo solicitado son obligatorios."}

    def _num(clave, default):
        v = data.get(clave)
        return float(v) if v not in (None, "") else float(default or 0)

    piezas = int(data.get("piezas") or actual["piezas"] or 1)
    valor_total = _num("valor_total", actual["valor_total"])
    costo_real = _num("costo_real", actual["costo_real"])
    anticipo = _num("anticipo", actual["anticipo"])
    utilidad = round(valor_total - costo_real, 2)
    saldo = round(valor_total - anticipo, 2)

    con.execute("""
        UPDATE ordenes SET solicitante=?, cliente=?, telefono=?, trabajo=?, piezas=?,
            producto=?, precio_unitario=?, valor_total=?, anticipo=?, saldo=?,
            fecha_inicio=?, fecha_entrega=?, notas=?, costo_real=?, utilidad=?
        WHERE id=?
    """, (solicitante, cliente,
          data.get("telefono", actual["telefono"]) or "",
          trabajo, piezas,
          data.get("producto", actual["producto"]) or "",
          _num("precio_unitario", actual["precio_unitario"]),
          valor_total, anticipo, saldo,
          data.get("fecha_inicio", actual["fecha_inicio"]) or "",
          data.get("fecha_entrega", actual["fecha_entrega"]) or "",
          data.get("notas", actual["notas"]) or "",
          costo_real, utilidad, orden_id))
    con.commit()
    con.close()
    return {"status": "ok", "folio": actual["folio"], "saldo": saldo, "utilidad": utilidad,
            "mensaje": f"Orden {actual['folio']} actualizada (sin duplicar)."}


def actualizar_estado(orden_id: int, estado: str) -> dict:
    if estado not in ESTADOS:
        return {"status": "error", "mensaje": f"Estado inválido: {estado}"}
    init_db()
    con = _con()
    row = con.execute("SELECT saldo FROM ordenes WHERE id=?", (orden_id,)).fetchone()
    if not row:
        con.close()
        return {"status": "error", "mensaje": f"Orden {orden_id} no existe."}
    # El estado y el cobro son cosas distintas: entregar NO marca el saldo como
    # pagado solo. Si queda saldo pendiente, se avisa explícito en vez de ocultarlo
    # (antes se forzaba saldo=0/anticipo=valor_total sin verificar pago real).
    con.execute("UPDATE ordenes SET estado=? WHERE id=?", (estado, orden_id))
    con.commit()
    con.close()
    msg = f"Orden {orden_id} → {estado}"
    saldo = row["saldo"] or 0
    if estado == "entregado" and saldo > 0:
        msg += f" (⚠️ con saldo pendiente de ${saldo} — no se marcó como cobrado)"
    return {"status": "ok", "mensaje": msg}


# ── ALERTAS (calculadas en vivo, solo panel) ──────────────────────────
def alertas() -> dict:
    """
    Calcula alertas de entrega en vivo:
      - atrasadas: fecha_entrega ya pasó y no está entregada
      - por_entregar_12h: entrega dentro de las próximas 12h (recordatorio por hora)
      - agendadas: recién agendadas (aún no en proceso)
    """
    init_db()
    con = _con()
    rows = con.execute(
        "SELECT * FROM ordenes WHERE estado NOT IN ('entregado','cancelado')"
    ).fetchall()
    con.close()
    ahora = datetime.now()
    atrasadas, por_entregar, agendadas = [], [], []
    for r in rows:
        o = dict(r)
        fe = o.get("fecha_entrega")
        dt = None
        if fe:
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(fe, fmt); break
                except ValueError:
                    continue
        if dt:
            horas = (dt - ahora).total_seconds() / 3600.0
            o["horas_restantes"] = round(horas, 1)
            if horas < 0:
                atrasadas.append(o)
            elif horas <= 12:
                por_entregar.append(o)
            elif o.get("estado") == "agendado":
                agendadas.append(o)
        elif o.get("estado") == "agendado":
            agendadas.append(o)
    por_entregar.sort(key=lambda x: x.get("horas_restantes", 999))
    atrasadas.sort(key=lambda x: x.get("horas_restantes", 0))
    total = len(atrasadas) + len(por_entregar)
    return {
        "status": "ok",
        "total_alertas": total,
        "atrasadas": atrasadas,
        "por_entregar_12h": por_entregar,
        "agendadas": agendadas,
        "timestamp": ahora.isoformat(),
    }


# ── CONTABILIDAD MENSUAL (balance real: ingresos, costos, utilidad) ────
def contabilidad_mensual(mes: str = None) -> dict:
    """Balance por mes (por fecha de entrega; si falta, por fecha de creación).
    - ingresos = valor_total facturado | costos = costo_real | utilidad = ingresos−costos
    - cobrado = anticipos | por_cobrar = saldos pendientes
    Si 'mes' (YYYY-MM) se pasa, incluye el detalle de órdenes de ese mes.
    """
    init_db()
    con = _con()
    rows = con.execute("SELECT folio,cliente,valor_total,costo_real,utilidad,anticipo,saldo,"
                       "estado,creado,fecha_entrega FROM ordenes WHERE estado != 'cancelado'").fetchall()
    con.close()
    meses = {}
    detalle = []
    for r in rows:
        o = dict(r)
        mk = (o.get("fecha_entrega") or "")[:7] or (o.get("creado") or "")[:7]
        if not mk:
            continue
        m = meses.setdefault(mk, {"mes": mk, "ordenes": 0, "ingresos": 0.0, "costos": 0.0,
                                  "utilidad": 0.0, "cobrado": 0.0, "por_cobrar": 0.0})
        val = o.get("valor_total") or 0
        cos = o.get("costo_real") or 0
        uti = o.get("utilidad") if o.get("utilidad") is not None else (val - cos)
        m["ordenes"] += 1
        m["ingresos"] += val
        m["costos"] += cos
        m["utilidad"] += uti
        m["cobrado"] += o.get("anticipo") or 0
        m["por_cobrar"] += o.get("saldo") or 0
        if mes and mk == mes:
            detalle.append({"folio": o["folio"], "cliente": o["cliente"], "valor": val,
                            "costo": cos, "utilidad": uti, "saldo": o.get("saldo") or 0,
                            "estado": o.get("estado")})
    lista = sorted(meses.values(), key=lambda x: x["mes"], reverse=True)
    for m in lista:
        for k in ("ingresos", "costos", "utilidad", "cobrado", "por_cobrar"):
            m[k] = round(m[k], 2)
        m["margen_pct"] = round(m["utilidad"] / m["ingresos"] * 100, 1) if m["ingresos"] else 0.0
    out = {"status": "ok", "meses": lista}
    if mes:
        out["detalle"] = {"mes": mes, "ordenes": detalle}
    return out


if __name__ == "__main__":
    init_db()
    print("Catálogo:", len(catalogo()), "productos")
    print("Cotizar 'termo 30oz' x2:", cotizar("termo 30oz", 2))
    print("Cotizar 'x5':", cotizar("x5"))
    print("Cotizar 'faro led plus single':", cotizar("faro led plus single"))
