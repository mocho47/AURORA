"""
ORACLE - Panel operativo (captacion + orden de taller).
100% real: persistencia SQLite. Sin simulaciones, sin datos inventados.
Operado por AURORA. Reconstruccion del ORACLE original (2026-06-12).
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

DB = Path(__file__).parent.parent / "oracle.db"

# Etapas UNIFICADAS con VENDEDOR/seguimiento_ventas.py (antes Oracle no tenía
# 'negociando' y un lead en esa etapa no se podía representar aquí).
ESTADOS_LEAD = ["nuevo", "contactado", "cotizado", "negociando", "ganado", "perdido"]
ESTADOS_ABIERTOS = ["nuevo", "contactado", "cotizado", "negociando"]
ESTADOS_ORDEN = ["en_proceso", "terminado", "entregado"]


def _conn() -> sqlite3.Connection:
    # timeout + WAL + busy_timeout, igual que el taller. Antes abría pelado, que
    # es exactamente la configuración que provocó los "database is locked" en
    # taller.db el 27-jul. oracle.db guarda los LEADS: perder uno es perder un
    # cliente que ya había levantado la mano. Encontrado en la auditoría del
    # 2026-08-02, cuando esta base todavía estaba en journal de rollback.
    #
    # OJO con `with _conn() as c:` — el context manager de sqlite3 hace commit
    # o rollback, pero NO cierra la conexión. En este archivo hay 14 usos así y
    # ninguna llamada a close(). Por eso el timeout importa todavía más aquí:
    # sostiene la espera mientras el recolector de basura libera las anteriores.
    c = sqlite3.connect(str(DB), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=10000")
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            fuente TEXT,
            negocio TEXT DEFAULT 'atf',
            vehiculo TEXT,
            interes TEXT,
            estado TEXT DEFAULT 'nuevo',
            notas TEXT,
            creado TEXT,
            actualizado TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            cliente TEXT NOT NULL,
            telefono TEXT,
            negocio TEXT DEFAULT 'atf',
            vehiculo TEXT,
            servicio TEXT,
            kit TEXT,
            precio REAL DEFAULT 0,
            anticipo REAL DEFAULT 0,
            estado TEXT DEFAULT 'recibido',
            fecha_cita TEXT,
            instalador TEXT,
            notas TEXT,
            creado TEXT,
            actualizado TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )""")
        # Migracion: agregar 'negocio' a BD existentes
        cols = [r[1] for r in c.execute("PRAGMA table_info(ordenes)")]
        if "negocio" not in cols:
            c.execute("ALTER TABLE ordenes ADD COLUMN negocio TEXT DEFAULT 'atf'")
        # Migracion: valor estimado del lead -> permite PRONOSTICAR ventas del embudo
        cols_l = [r[1] for r in c.execute("PRAGMA table_info(leads)")]
        if "valor_estimado" not in cols_l:
            c.execute("ALTER TABLE leads ADD COLUMN valor_estimado REAL DEFAULT 0")


# ==================== LEADS (captacion) ====================

def crear_lead(nombre: str, telefono: str = "", fuente: str = "", negocio: str = "atf",
               vehiculo: str = "", interes: str = "", notas: str = "",
               valor_estimado: float = 0) -> Dict:
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del lead es obligatorio")
    ahora = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            # Fase 3 (2026-07-28), bug real encontrado: la columna valor_estimado
            # existe desde una migracion especificamente "para PRONOSTICAR ventas
            # del embudo", pero crear_lead() nunca la recibia ni la insertaba —
            # pronostico_embudo() siempre daba $0 sin importar cuantos leads reales
            # hubiera. Ahora se puede capturar desde la creacion del lead.
            """INSERT INTO leads (nombre, telefono, fuente, negocio, vehiculo, interes,
                                  estado, notas, valor_estimado, creado, actualizado)
               VALUES (?, ?, ?, ?, ?, ?, 'nuevo', ?, ?, ?, ?)""",
            (nombre.strip(), telefono, fuente, negocio, vehiculo, interes, notas,
             float(valor_estimado or 0), ahora, ahora))
        new_id = cur.lastrowid
    return obtener_lead(new_id)


def actualizar_lead_valor(lead_id: int, valor_estimado: float) -> Dict:
    """Actualiza el valor estimado de un lead ya creado (para cotizaciones que
    llegan despues del contacto inicial, o correcciones)."""
    if obtener_lead(lead_id) is None:
        raise ValueError(f"Lead {lead_id} no existe")
    with _conn() as c:
        c.execute("UPDATE leads SET valor_estimado = ?, actualizado = ? WHERE id = ?",
                  (float(valor_estimado or 0), datetime.now().isoformat(timespec="seconds"), lead_id))
    return obtener_lead(lead_id)


def obtener_lead(lead_id: int) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None


def listar_leads(estado: Optional[str] = None, negocio: Optional[str] = None) -> List[Dict]:
    q = "SELECT * FROM leads"
    cond, args = [], []
    if estado: cond.append("estado = ?"); args.append(estado)
    if negocio: cond.append("negocio = ?"); args.append(negocio.lower())
    if cond: q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY id DESC"
    with _conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def actualizar_lead_estado(lead_id: int, estado: str) -> Dict:
    if estado not in ESTADOS_LEAD:
        raise ValueError(f"Estado invalido. Validos: {ESTADOS_LEAD}")
    if obtener_lead(lead_id) is None:
        raise ValueError(f"Lead {lead_id} no existe")
    with _conn() as c:
        c.execute("UPDATE leads SET estado = ?, actualizado = ? WHERE id = ?",
                  (estado, datetime.now().isoformat(timespec="seconds"), lead_id))
    return obtener_lead(lead_id)


# ==================== ORDENES DE TALLER ====================

def crear_orden(cliente: str, telefono: str = "", negocio: str = "atf", vehiculo: str = "", servicio: str = "",
                kit: str = "", precio: float = 0, anticipo: float = 0,
                fecha_cita: str = "", instalador: str = "", notas: str = "",
                lead_id: Optional[int] = None) -> Dict:
    if not cliente or not cliente.strip():
        raise ValueError("El cliente de la orden es obligatorio")
    if lead_id is not None and obtener_lead(lead_id) is None:
        raise ValueError(f"lead_id {lead_id} no existe")
    ahora = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO ordenes (lead_id, cliente, telefono, negocio, vehiculo, servicio, kit,
                                    precio, anticipo, estado, fecha_cita, instalador, notas,
                                    creado, actualizado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'en_proceso', ?, ?, ?, ?, ?)""",
            (lead_id, cliente.strip(), telefono, (negocio or "atf").lower(), vehiculo, servicio, kit,
             float(precio or 0), float(anticipo or 0), fecha_cita, instalador, notas, ahora, ahora))
        new_id = cur.lastrowid
    return obtener_orden(new_id)


def obtener_orden(orden_id: int) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM ordenes WHERE id = ?", (orden_id,)).fetchone()
        return dict(row) if row else None


def listar_ordenes(estado: Optional[str] = None, negocio: Optional[str] = None) -> List[Dict]:
    q = "SELECT * FROM ordenes"
    cond, args = [], []
    if estado: cond.append("estado = ?"); args.append(estado)
    if negocio: cond.append("negocio = ?"); args.append(negocio.lower())
    if cond: q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY id DESC"
    with _conn() as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def actualizar_orden_estado(orden_id: int, estado: str) -> Dict:
    if estado not in ESTADOS_ORDEN:
        raise ValueError(f"Estado invalido. Validos: {ESTADOS_ORDEN}")
    if obtener_orden(orden_id) is None:
        raise ValueError(f"Orden {orden_id} no existe")
    with _conn() as c:
        c.execute("UPDATE ordenes SET estado = ?, actualizado = ? WHERE id = ?",
                  (estado, datetime.now().isoformat(timespec="seconds"), orden_id))
    return obtener_orden(orden_id)


# ==================== RELACIÓN LEAD ↔ ORDEN (lo que faltaba usar) ==========

def convertir_lead_a_orden(lead_id: int, servicio: str = "", precio: float = 0,
                           anticipo: float = 0, kit: str = "", fecha_cita: str = "",
                           instalador: str = "", notas: str = "") -> Dict:
    """Convierte un lead GANADO en orden, dejando la RELACIÓN registrada (lead_id).
    Así se puede rastrear qué fuente de leads trae ventas reales."""
    lead = obtener_lead(lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} no existe")
    orden = crear_orden(
        cliente=lead["nombre"], telefono=lead.get("telefono", ""),
        negocio=lead.get("negocio", "atf"), vehiculo=lead.get("vehiculo", ""),
        servicio=servicio or lead.get("interes", ""), kit=kit,
        precio=precio or float(lead.get("valor_estimado") or 0), anticipo=anticipo,
        fecha_cita=fecha_cita, instalador=instalador, notas=notas, lead_id=lead_id)
    # Al convertir, el lead pasa a 'ganado' (queda coherente el embudo)
    if lead.get("estado") != "ganado":
        actualizar_lead_estado(lead_id, "ganado")
    return {"status": "ok", "lead_id": lead_id, "orden": orden,
            "mensaje": f"Lead '{lead['nombre']}' convertido en orden #{orden['id']}."}


def ficha_cliente(lead_id: int) -> Dict:
    """Vista 360: el lead con TODAS sus órdenes relacionadas y lo facturado."""
    lead = obtener_lead(lead_id)
    if lead is None:
        return {"status": "no_encontrado"}
    with _conn() as c:
        ordenes = [dict(r) for r in c.execute(
            "SELECT * FROM ordenes WHERE lead_id = ? ORDER BY id DESC", (lead_id,)).fetchall()]
    total = round(sum(float(o.get("precio") or 0) for o in ordenes), 2)
    cobrado = round(sum(float(o.get("anticipo") or 0) for o in ordenes), 2)
    return {"status": "ok", "lead": lead, "ordenes": ordenes, "total_ordenes": len(ordenes),
            "valor_facturado": total, "cobrado": cobrado, "por_cobrar": round(total - cobrado, 2)}


def pronostico_embudo(negocio: Optional[str] = None) -> Dict:
    """PRONÓSTICO: cuánto dinero traes en el embudo por etapa (leads abiertos)."""
    wl = " AND negocio = ?" if negocio else ""
    al = [negocio.lower()] if negocio else []
    detalle, total_abierto = {}, 0.0
    with _conn() as c:
        for e in ESTADOS_LEAD:
            row = c.execute(
                f"SELECT COUNT(*) n, COALESCE(SUM(valor_estimado),0) v FROM leads WHERE estado = ?{wl}",
                [e] + al).fetchone()
            detalle[e] = {"leads": row[0], "valor": round(float(row[1] or 0), 2)}
            if e in ESTADOS_ABIERTOS:
                total_abierto += float(row[1] or 0)
        ganado = c.execute(
            f"SELECT COALESCE(SUM(valor_estimado),0) FROM leads WHERE estado='ganado'{wl}", al).fetchone()[0]
    return {"status": "ok", "por_etapa": detalle,
            "valor_en_embudo": round(total_abierto, 2),
            "valor_ganado": round(float(ganado or 0), 2),
            "nota": "valor_en_embudo = dinero potencial de leads aún abiertos"}


def fuentes_efectivas(negocio: Optional[str] = None) -> Dict:
    """¿QUÉ FUENTE TRAE CLIENTES QUE SÍ COMPRAN? (la pregunta que más vale)."""
    wl = " WHERE negocio = ?" if negocio else ""
    al = [negocio.lower()] if negocio else []
    with _conn() as c:
        rows = c.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(fuente),''),'(sin fuente)') AS fuente,
                   COUNT(*) AS leads,
                   SUM(CASE WHEN estado='ganado' THEN 1 ELSE 0 END) AS ganados,
                   COALESCE(SUM(CASE WHEN estado='ganado' THEN valor_estimado ELSE 0 END),0) AS valor
            FROM leads{wl} GROUP BY fuente ORDER BY ganados DESC, leads DESC""", al).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["conversion_pct"] = round((d["ganados"] / d["leads"]) * 100, 1) if d["leads"] else 0.0
        d["valor"] = round(float(d["valor"] or 0), 2)
        out.append(d)
    return {"status": "ok", "fuentes": out}


# ==================== RESUMEN (conteos REALES de la BD) ====================

def resumen(negocio: Optional[str] = None) -> Dict:
    wl = " WHERE negocio = ?" if negocio else ""
    al = [negocio.lower()] if negocio else []
    with _conn() as c:
        total_leads = c.execute("SELECT COUNT(*) FROM leads" + wl, al).fetchone()[0]
        total_ordenes = c.execute("SELECT COUNT(*) FROM ordenes" + wl, al).fetchone()[0]
        leads_por_estado = {e: c.execute("SELECT COUNT(*) FROM leads WHERE estado = ?" + (" AND negocio = ?" if negocio else ""), [e]+al).fetchone()[0]
                            for e in ESTADOS_LEAD}
        ordenes_por_estado = {e: c.execute("SELECT COUNT(*) FROM ordenes WHERE estado = ?" + (" AND negocio = ?" if negocio else ""), [e]+al).fetchone()[0]
                              for e in ESTADOS_ORDEN}
        valor = c.execute("SELECT COALESCE(SUM(precio),0), COALESCE(SUM(anticipo),0) FROM ordenes" + wl, al).fetchone()
        por_negocio = {n: {"leads": c.execute("SELECT COUNT(*) FROM leads WHERE negocio=?", [n]).fetchone()[0],
                           "ordenes": c.execute("SELECT COUNT(*) FROM ordenes WHERE negocio=?", [n]).fetchone()[0]}
                       for n in ("atf", "milens")}
    return {
        "negocio": negocio or "todos",
        "total_leads": total_leads,
        "total_ordenes": total_ordenes,
        "leads_por_estado": leads_por_estado,
        "ordenes_por_estado": ordenes_por_estado,
        "valor_total_ordenes": round(valor[0], 2),
        "anticipos_cobrados": round(valor[1], 2),
        "saldo_pendiente": round(valor[0] - valor[1], 2),
        "por_negocio": por_negocio,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

def obtener_conexion() -> sqlite3.Connection:
    """Enlace publico inyectado por el fix."""
    return _conn()
