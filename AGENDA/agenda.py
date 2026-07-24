# -*- coding: utf-8 -*-
"""
AURORA · AGENDA / CITAS (cartucho self-contained)

Agenda del taller: instalaciones de faros ATF, entregas, cotizaciones y citas.
- 0 dependencias externas: sqlite3 + stdlib. NO usa Google API/OAuth.
- Exporta eventos .ics estándar (VCALENDAR/VEVENT) para importar a Google
  Calendar / Outlook / Apple manualmente (archivo, no API).
- Todas las funciones devuelven un dict con "status" (ok / error).

Patrón de DB idéntico a MARKETING/plan_monetizacion.py:
  sqlite3, row_factory=Row, journal_mode=WAL. DB en ROOT/agenda.db.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "agenda.db"

TIPOS = {"instalacion", "entrega", "cita", "cotizacion"}
ESTADOS = {"agendada", "confirmada", "hecha", "cancelada"}


# ----------------------------------------------------------------------------
# Infraestructura
# ----------------------------------------------------------------------------
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            cliente TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            fecha TEXT NOT NULL,          -- YYYY-MM-DD
            hora TEXT NOT NULL,           -- HH:MM
            tipo TEXT NOT NULL,           -- instalacion|entrega|cita|cotizacion
            duracion_min INTEGER DEFAULT 60,
            notas TEXT DEFAULT '',
            estado TEXT DEFAULT 'agendada',
            creada_en TEXT
        )""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_citas_fecha ON citas(fecha, hora)")
    con.commit()
    con.close()


# ----------------------------------------------------------------------------
# Validación / helpers
# ----------------------------------------------------------------------------
def _valida_fecha(fecha: str) -> bool:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _valida_hora(hora: str) -> bool:
    try:
        datetime.strptime(hora, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def _row(r: sqlite3.Row) -> dict:
    return dict(r)


# ----------------------------------------------------------------------------
# CRUD / consultas
# ----------------------------------------------------------------------------
def crear_cita(titulo, cliente, telefono, fecha, hora, tipo,
               notas="", duracion_min=60) -> dict:
    if not titulo or not str(titulo).strip():
        return {"status": "error", "error": "El título es obligatorio."}
    if tipo not in TIPOS:
        return {"status": "error",
                "error": f"Tipo inválido '{tipo}'. Use: {sorted(TIPOS)}"}
    if not _valida_fecha(fecha):
        return {"status": "error", "error": f"Fecha inválida '{fecha}' (YYYY-MM-DD)."}
    if not _valida_hora(hora):
        return {"status": "error", "error": f"Hora inválida '{hora}' (HH:MM)."}
    try:
        dur = int(duracion_min)
        if dur <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return {"status": "error", "error": "duracion_min debe ser entero > 0."}

    init_db()
    con = _conn()
    cur = con.execute(
        """INSERT INTO citas
           (titulo, cliente, telefono, fecha, hora, tipo, duracion_min,
            notas, estado, creada_en)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (str(titulo).strip(), cliente or "", telefono or "", fecha, hora, tipo,
         dur, notas or "", "agendada", datetime.now().isoformat(timespec="seconds")),
    )
    con.commit()
    cid = cur.lastrowid
    con.close()
    return {"status": "ok", "id": cid, "mensaje": "Cita agendada."}


def listar(desde="", hasta="") -> dict:
    if not desde:
        desde = datetime.now().strftime("%Y-%m-%d")
    if not hasta:
        hasta = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    if not _valida_fecha(desde) or not _valida_fecha(hasta):
        return {"status": "error", "error": "Rango de fechas inválido (YYYY-MM-DD)."}
    init_db()
    con = _conn()
    rows = con.execute(
        """SELECT * FROM citas
           WHERE fecha BETWEEN ? AND ?
           ORDER BY fecha, hora""", (desde, hasta)).fetchall()
    con.close()
    return {"status": "ok", "desde": desde, "hasta": hasta,
            "total": len(rows), "citas": [_row(r) for r in rows]}


def dia(fecha) -> dict:
    if not _valida_fecha(fecha):
        return {"status": "error", "error": f"Fecha inválida '{fecha}' (YYYY-MM-DD)."}
    init_db()
    con = _conn()
    rows = con.execute(
        "SELECT * FROM citas WHERE fecha=? ORDER BY hora", (fecha,)).fetchall()
    con.close()
    return {"status": "ok", "fecha": fecha,
            "total": len(rows), "citas": [_row(r) for r in rows]}


def actualizar_estado(id, estado) -> dict:
    if estado not in ESTADOS:
        return {"status": "error",
                "error": f"Estado inválido '{estado}'. Use: {sorted(ESTADOS)}"}
    init_db()
    con = _conn()
    cur = con.execute("UPDATE citas SET estado=? WHERE id=?", (estado, id))
    con.commit()
    n = cur.rowcount
    con.close()
    if not n:
        return {"status": "error", "error": f"No existe cita id={id}."}
    return {"status": "ok", "id": id, "estado": estado}


def proximas(horas=24) -> dict:
    try:
        horas = int(horas)
    except (ValueError, TypeError):
        return {"status": "error", "error": "horas debe ser entero."}
    ahora = datetime.now()
    limite = ahora + timedelta(hours=horas)
    init_db()
    con = _conn()
    # Rango de fechas amplio; filtramos por datetime exacto en Python.
    rows = con.execute(
        """SELECT * FROM citas
           WHERE fecha BETWEEN ? AND ?
             AND estado NOT IN ('cancelada','hecha')
           ORDER BY fecha, hora""",
        (ahora.strftime("%Y-%m-%d"), limite.strftime("%Y-%m-%d"))).fetchall()
    con.close()
    out = []
    for r in rows:
        try:
            dt = datetime.strptime(f"{r['fecha']} {r['hora']}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if ahora <= dt <= limite:
            d = _row(r)
            d["en_horas"] = round((dt - ahora).total_seconds() / 3600, 1)
            out.append(d)
    return {"status": "ok", "horas": horas, "total": len(out), "citas": out}


def eliminar(id) -> dict:
    init_db()
    con = _conn()
    cur = con.execute("DELETE FROM citas WHERE id=?", (id,))
    con.commit()
    n = cur.rowcount
    con.close()
    if not n:
        return {"status": "error", "error": f"No existe cita id={id}."}
    return {"status": "ok", "id": id, "mensaje": "Cita eliminada."}


def resumen() -> dict:
    init_db()
    con = _conn()
    por_estado = {r["estado"]: r["n"] for r in con.execute(
        "SELECT estado, COUNT(*) n FROM citas GROUP BY estado").fetchall()}
    por_tipo = {r["tipo"]: r["n"] for r in con.execute(
        "SELECT tipo, COUNT(*) n FROM citas GROUP BY tipo").fetchall()}
    total = con.execute("SELECT COUNT(*) n FROM citas").fetchone()["n"]
    con.close()
    prox = proximas(24)
    return {"status": "ok", "total": total,
            "por_estado": por_estado, "por_tipo": por_tipo,
            "proximas_24h": prox["total"]}


# ----------------------------------------------------------------------------
# Exportar .ics (estándar RFC 5545) — importar manualmente a Google Calendar
# ----------------------------------------------------------------------------
def _ics_escape(txt: str) -> str:
    return (str(txt or "").replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def exportar_ics(id) -> dict:
    init_db()
    con = _conn()
    r = con.execute("SELECT * FROM citas WHERE id=?", (id,)).fetchone()
    con.close()
    if not r:
        return {"status": "error", "error": f"No existe cita id={id}."}
    try:
        inicio = datetime.strptime(f"{r['fecha']} {r['hora']}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"status": "error", "error": "Fecha/hora corruptas en la cita."}
    fin = inicio + timedelta(minutes=int(r["duracion_min"] or 60))
    fmt = "%Y%m%dT%H%M%S"
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    desc_parts = []
    if r["cliente"]:
        desc_parts.append(f"Cliente: {r['cliente']}")
    if r["telefono"]:
        desc_parts.append(f"Tel: {r['telefono']}")
    desc_parts.append(f"Tipo: {r['tipo']}")
    if r["notas"]:
        desc_parts.append(f"Notas: {r['notas']}")
    desc = _ics_escape(" | ".join(desc_parts))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AURORA//Agenda Taller//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:aurora-cita-{r['id']}@aurora.taller",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{inicio.strftime(fmt)}",
        f"DTEND:{fin.strftime(fmt)}",
        f"SUMMARY:{_ics_escape(r['titulo'])}",
        f"DESCRIPTION:{desc}",
        f"STATUS:{'CANCELLED' if r['estado'] == 'cancelada' else 'CONFIRMED'}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics = "\r\n".join(lines) + "\r\n"
    return {"status": "ok", "id": r["id"],
            "filename": f"cita_{r['id']}.ics", "ics": ics}


# ----------------------------------------------------------------------------
# Prueba standalone (real; limpia sus datos al final)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    print("DB:", DB)
    init_db()

    hoy = datetime.now()
    f1 = (hoy + timedelta(hours=3)).strftime("%Y-%m-%d")
    f2 = (hoy + timedelta(days=2)).strftime("%Y-%m-%d")

    c1 = crear_cita("Instalación faros Aozoom X5", "Carlos Ramírez",
                    "3312345678", f1, (hoy + timedelta(hours=3)).strftime("%H:%M"),
                    "instalacion", notas="Honda Civic 2018, par completo",
                    duracion_min=90)
    c2 = crear_cita("Entrega caja MDF sublimada", "Milens Store",
                    "3339998877", f2, "17:30", "entrega",
                    notas="Recoge en taller")
    print("crear c1:", c1)
    print("crear c2:", c2)

    # validación negativa
    print("fecha mala:", crear_cita("x", "", "", "2026-13-40", "10:00", "cita"))
    print("tipo malo:", crear_cita("x", "", "", f1, "10:00", "boda"))

    ids = [c1["id"], c2["id"]]

    print("\nlistar (14d):", json.dumps(listar(), ensure_ascii=False, default=str))
    print("\ndia c1:", dia(f1)["total"], "cita(s)")

    print("\nconfirmar c1:", actualizar_estado(c1["id"], "confirmada"))
    print("proximas 24h:", proximas(24)["total"], "cita(s)")

    ics = exportar_ics(c1["id"])
    print("\n.ics ok:", ics["status"], ics.get("filename"))
    if ics["status"] == "ok":
        print(ics["ics"])

    print("resumen:", json.dumps(resumen(), ensure_ascii=False))

    # Limpieza: borrar datos de prueba (tabla vacía)
    for i in ids:
        eliminar(i)
    con = _conn()
    left = con.execute("SELECT COUNT(*) n FROM citas").fetchone()["n"]
    con.close()
    print("\nLimpieza — filas restantes:", left)
    print("PRUEBA OK" if left == 0 else "PRUEBA: quedaron filas!")
