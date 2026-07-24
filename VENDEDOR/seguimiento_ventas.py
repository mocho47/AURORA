# -*- coding: utf-8 -*-
"""
AURORA · SEGUIMIENTO DE LEADS → VENTAS  (cartucho autónomo)

Embudo de ventas real sobre los leads del ORACLE CRM, con seguimiento por WhatsApp.

HONESTO:
- Sincroniza leads REALES del Oracle CRM (oracle.db) hacia un embudo propio (seguimiento.db).
- Preparar un mensaje NO lo envía. `mensaje_sugerido` solo redacta (Groq).
- `enviar_seguimiento` es la ÚNICA función que ejecuta la acción real (WhatsApp vía
  PUBLICADOR/publicador_core). Nada de spam masivo: se envía un lead a la vez, explícito.
- Groq: si falta GROQ_API_KEY, lo dice (status "sin_llm"); no inventa.

Autónomo: carga publicador_core con importlib (patrón `_mod()`), no importa nada del bus.
Un cartucho ausente/roto NO tumba el server.
"""
from __future__ import annotations

import os
import sqlite3
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "seguimiento.db"
ORACLE_DB = ROOT / "oracle.db"

# Etapas del embudo (superset honesto del Oracle: nuevo/contactado/cotizado/ganado/perdido
# + 'negociando' que aquí sí modelamos).
ETAPAS = ["nuevo", "contactado", "cotizado", "negociando", "ganado", "perdido"]
ETAPAS_ABIERTAS = ["nuevo", "contactado", "cotizado", "negociando"]
ETAPAS_CERRADAS = ["ganado", "perdido"]

# Regla de seguimiento: reactivar un lead abierto tras N horas sin interacción.
HORAS_SEGUIMIENTO = 48


# ----------------------------------------------------------------------------- infra
def _mod(nombre: str, ruta: Path):
    """Carga un módulo por ruta con importlib (patrón de MANUALES/aprendizaje.py)."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _publicador():
    return _mod("publicador_core", ROOT / "PUBLICADOR" / "publicador_core.py")


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS embudo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_lead_id INTEGER,
            nombre TEXT NOT NULL,
            telefono TEXT,
            negocio TEXT DEFAULT 'atf',
            interes TEXT,
            vehiculo TEXT,
            etapa TEXT DEFAULT 'nuevo',
            ultima_interaccion TEXT,
            creado TEXT,
            actualizado TEXT,
            UNIQUE(telefono)
        )""")
    con.execute("""
        CREATE TABLE IF NOT EXISTS interacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            tipo TEXT,
            canal TEXT,
            mensaje TEXT,
            resultado TEXT,
            fecha TEXT,
            FOREIGN KEY(lead_id) REFERENCES embudo(id)
        )""")
    con.commit()
    con.close()


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _lead(con: sqlite3.Connection, lead_id: int) -> Optional[Dict]:
    row = con.execute("SELECT * FROM embudo WHERE id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


# ----------------------------------------------------------------------------- API
def etapas() -> Dict:
    """Devuelve las etapas del embudo."""
    return {"status": "ok", "etapas": ETAPAS,
            "abiertas": ETAPAS_ABIERTAS, "cerradas": ETAPAS_CERRADAS,
            "horas_seguimiento": HORAS_SEGUIMIENTO}


def sincronizar_leads() -> Dict:
    """
    Trae leads REALES del Oracle CRM (oracle.db → tabla leads) al embudo.
    Evita duplicados por teléfono (UNIQUE) y por oracle_lead_id.
    Leads sin teléfono se guardan igual pero no se podrán seguir por WhatsApp.
    """
    init_db()
    if not ORACLE_DB.exists():
        return {"status": "error", "detalle": f"No existe el CRM Oracle: {ORACLE_DB}"}
    # Leer del Oracle directo (solo lectura, no tocamos su BD).
    try:
        oc = sqlite3.connect(str(ORACLE_DB))
        oc.row_factory = sqlite3.Row
        oleads = [dict(r) for r in oc.execute(
            "SELECT id, nombre, telefono, negocio, interes, vehiculo, estado FROM leads").fetchall()]
        oc.close()
    except Exception as e:
        return {"status": "error", "detalle": f"No se pudo leer oracle.db: {str(e)[:200]}"}

    nuevos, saltados = 0, 0
    con = _conn()
    try:
        for l in oleads:
            oid = l.get("id")
            tel = (l.get("telefono") or "").strip()
            # ¿ya existe por oracle_id o por teléfono?
            existe = con.execute(
                "SELECT id FROM embudo WHERE oracle_lead_id = ? OR (telefono != '' AND telefono = ?)",
                (oid, tel)).fetchone()
            if existe:
                saltados += 1
                continue
            # etapa inicial: respeta el estado del Oracle si es válido, si no 'nuevo'
            est = (l.get("estado") or "nuevo").lower()
            etapa = est if est in ETAPAS else "nuevo"
            ahora = _ahora()
            try:
                con.execute(
                    """INSERT INTO embudo (oracle_lead_id, nombre, telefono, negocio, interes,
                                           vehiculo, etapa, ultima_interaccion, creado, actualizado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                    (oid, l.get("nombre") or "(sin nombre)", tel, (l.get("negocio") or "atf"),
                     l.get("interes") or "", l.get("vehiculo") or "", etapa, ahora, ahora))
                nuevos += 1
            except sqlite3.IntegrityError:
                saltados += 1
        con.commit()
    finally:
        con.close()
    return {"status": "ok", "sincronizados": nuevos, "saltados_duplicados": saltados,
            "total_oracle": len(oleads)}


def pendientes() -> Dict:
    """
    Leads a seguir HOY: etapa abierta y (sin interacción nunca) o
    (última interacción hace ≥ HORAS_SEGUIMIENTO). Ordena por más rezagado primero.
    """
    init_db()
    limite = datetime.now() - timedelta(hours=HORAS_SEGUIMIENTO)
    con = _conn()
    try:
        rows = con.execute(
            "SELECT * FROM embudo WHERE etapa IN ({}) ORDER BY id".format(
                ",".join("?" * len(ETAPAS_ABIERTAS))), ETAPAS_ABIERTAS).fetchall()
    finally:
        con.close()
    out = []
    for r in rows:
        d = dict(r)
        ui = d.get("ultima_interaccion")
        vencido = True
        horas = None
        if ui:
            try:
                t = datetime.fromisoformat(ui)
                horas = round((datetime.now() - t).total_seconds() / 3600, 1)
                vencido = t <= limite
            except ValueError:
                vencido = True
        if vencido:
            d["horas_sin_contacto"] = horas
            d["motivo"] = "nunca contactado" if not ui else f"{horas}h sin contacto"
            out.append(d)
    out.sort(key=lambda x: (x["horas_sin_contacto"] is not None, -(x["horas_sin_contacto"] or 1e9)))
    return {"status": "ok", "total": len(out), "regla_horas": HORAS_SEGUIMIENTO, "pendientes": out}


def mensaje_sugerido(lead_id: int) -> Dict:
    """
    Redacta (NO envía) un mensaje de seguimiento con Groq: español mexicano, cálido,
    breve, con CTA a agendar. Honesto: si falta GROQ_API_KEY, usa una plantilla base.
    """
    init_db()
    con = _conn()
    try:
        lead = _lead(con, lead_id)
    finally:
        con.close()
    if not lead:
        return {"status": "error", "detalle": f"Lead {lead_id} no existe en el embudo"}

    nombre = lead["nombre"]
    interes = lead.get("interes") or lead.get("vehiculo") or ""
    negocio = "ATF (retrofit de faros)" if (lead.get("negocio") == "atf") else "Milens (corte láser/sublimación)"
    etapa = lead.get("etapa", "nuevo")

    key = os.getenv("GROQ_API_KEY")
    if not key:
        # Fallback honesto: plantilla base editable, no simula Groq.
        base = (f"¡Hola {nombre}! Le saluda el equipo de {negocio.split('(')[0].strip()}. "
                f"Quería dar seguimiento a su interés"
                f"{(' en ' + interes) if interes else ''}. "
                f"¿Le parece si agendamos para resolver sus dudas? Quedo atento. 🙌")
        return {"status": "sin_llm", "lead_id": lead_id, "etapa": etapa,
                "mensaje": base, "detalle": "Falta GROQ_API_KEY; plantilla base editable."}

    prompt = (
        f"Eres asesor de ventas de {negocio} en Guadalajara. Escribe UN mensaje de WhatsApp "
        f"de SEGUIMIENTO para el cliente '{nombre}'. Etapa actual del embudo: {etapa}. "
        f"Interés/vehículo: {interes or 'no especificado'}. "
        "Requisitos: español mexicano natural y cálido, tuteo respetuoso, 2-4 líneas máximo, "
        "un solo emoji opcional, SIN inventar precios ni promociones, con un CTA claro a "
        "agendar (visita/llamada). Devuelve SOLO el texto del mensaje, sin comillas ni encabezados."
    )
    try:
        import requests
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}"},
                          json={"model": "llama-3.1-8b-instant",
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.8}, timeout=30)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]["content"].strip().strip('"')
        return {"status": "ok", "lead_id": lead_id, "etapa": etapa, "mensaje": msg}
    except Exception as e:
        return {"status": "error", "lead_id": lead_id, "detalle": str(e)[:200]}


def enviar_seguimiento(lead_id: int, mensaje: str) -> Dict:
    """
    ACCIÓN REAL: envía `mensaje` por WhatsApp al lead vía publicador_core.enviar_whatsapp
    y registra la interacción. Marca 'contactado' si el lead seguía en 'nuevo'.
    """
    init_db()
    if not mensaje or not mensaje.strip():
        return {"status": "error", "detalle": "El mensaje está vacío. Nada que enviar."}
    con = _conn()
    try:
        lead = _lead(con, lead_id)
    finally:
        con.close()
    if not lead:
        return {"status": "error", "detalle": f"Lead {lead_id} no existe en el embudo"}
    tel = (lead.get("telefono") or "").strip()
    if not tel:
        return {"status": "error", "detalle": f"Lead {lead_id} sin teléfono; no se puede enviar WhatsApp"}

    # Envío real
    try:
        res = _publicador().enviar_whatsapp(tel, mensaje)
    except Exception as e:
        return {"status": "error", "detalle": f"publicador_core no disponible: {str(e)[:200]}"}

    ok = res.get("status") == "ENVIADO"
    ahora = _ahora()
    con = _conn()
    try:
        con.execute(
            """INSERT INTO interacciones (lead_id, tipo, canal, mensaje, resultado, fecha)
               VALUES (?, 'seguimiento', 'whatsapp', ?, ?, ?)""",
            (lead_id, mensaje, res.get("status"), ahora))
        # Actualiza última interacción SIEMPRE que hubo intento; avanza a contactado si iba en nuevo.
        nueva_etapa = "contactado" if (ok and lead.get("etapa") == "nuevo") else lead.get("etapa")
        con.execute(
            "UPDATE embudo SET ultima_interaccion = ?, etapa = ?, actualizado = ? WHERE id = ?",
            (ahora, nueva_etapa, ahora, lead_id))
        con.commit()
    finally:
        con.close()
    return {"status": ("ok" if ok else "fallo_envio"), "lead_id": lead_id,
            "whatsapp": res, "etapa": nueva_etapa}


def avanzar_etapa(lead_id: int, etapa: str) -> Dict:
    """Mueve el lead a otra etapa del embudo (validada) y registra la interacción."""
    init_db()
    etapa = (etapa or "").lower()
    if etapa not in ETAPAS:
        return {"status": "error", "detalle": f"Etapa inválida. Válidas: {ETAPAS}"}
    con = _conn()
    try:
        lead = _lead(con, lead_id)
        if not lead:
            return {"status": "error", "detalle": f"Lead {lead_id} no existe en el embudo"}
        ahora = _ahora()
        con.execute("UPDATE embudo SET etapa = ?, actualizado = ? WHERE id = ?",
                    (etapa, ahora, lead_id))
        con.execute(
            """INSERT INTO interacciones (lead_id, tipo, canal, mensaje, resultado, fecha)
               VALUES (?, 'cambio_etapa', 'panel', ?, ?, ?)""",
            (lead_id, f"{lead.get('etapa')} -> {etapa}", etapa, ahora))
        con.commit()
        lead = _lead(con, lead_id)
    finally:
        con.close()
    return {"status": "ok", "lead": lead}


def resumen() -> Dict:
    """Conteo por etapa + tasa de conversión (ganado / cerrados) sobre datos REALES."""
    init_db()
    con = _conn()
    try:
        total = con.execute("SELECT COUNT(*) FROM embudo").fetchone()[0]
        por_etapa = {e: con.execute("SELECT COUNT(*) FROM embudo WHERE etapa = ?", (e,)).fetchone()[0]
                     for e in ETAPAS}
        interacciones = con.execute("SELECT COUNT(*) FROM interacciones").fetchone()[0]
    finally:
        con.close()
    ganado = por_etapa.get("ganado", 0)
    perdido = por_etapa.get("perdido", 0)
    cerrados = ganado + perdido
    abiertos = sum(por_etapa.get(e, 0) for e in ETAPAS_ABIERTAS)
    tasa_cierre = round(100 * ganado / cerrados, 1) if cerrados else 0.0  # ganado / cerrados
    tasa_global = round(100 * ganado / total, 1) if total else 0.0        # ganado / total
    return {"status": "ok", "total": total, "por_etapa": por_etapa,
            "abiertos": abiertos, "cerrados": cerrados, "ganado": ganado, "perdido": perdido,
            "tasa_conversion_pct": tasa_cierre, "tasa_conversion_global_pct": tasa_global,
            "interacciones_registradas": interacciones,
            "timestamp": _ahora()}


# ----------------------------------------------------------------------------- CLI/prueba
if __name__ == "__main__":
    import json
    # Carga .env para que GROQ_API_KEY esté disponible en la prueba standalone.
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        pass

    print(">>> etapas()"); print(json.dumps(etapas(), ensure_ascii=False, indent=2))

    init_db()
    # Registrar 1 lead de prueba manual (teléfono no real; NO se envía WhatsApp).
    con = _conn()
    con.execute("DELETE FROM embudo WHERE nombre = '__PRUEBA_SEG__'")
    ahora = _ahora()
    cur = con.execute(
        """INSERT INTO embudo (oracle_lead_id, nombre, telefono, negocio, interes, vehiculo,
                               etapa, ultima_interaccion, creado, actualizado)
           VALUES (NULL, '__PRUEBA_SEG__', '0000000000', 'atf', 'faros LED demon',
                   'Mazda 3 2018', 'nuevo', NULL, ?, ?)""", (ahora, ahora))
    lead_id = cur.lastrowid
    con.commit(); con.close()
    print(f"\n>>> lead de prueba id={lead_id}")

    print("\n>>> mensaje_sugerido()")
    print(json.dumps(mensaje_sugerido(lead_id), ensure_ascii=False, indent=2))

    print("\n>>> avanzar_etapa(cotizado)")
    print(json.dumps(avanzar_etapa(lead_id, "cotizado"), ensure_ascii=False, indent=2))

    print("\n>>> pendientes()")
    p = pendientes(); print(f"total pendientes={p['total']}")

    print("\n>>> resumen()")
    print(json.dumps(resumen(), ensure_ascii=False, indent=2))

    # Limpieza de datos de prueba
    con = _conn()
    con.execute("DELETE FROM interacciones WHERE lead_id = ?", (lead_id,))
    con.execute("DELETE FROM embudo WHERE id = ?", (lead_id,))
    con.commit(); con.close()
    print(f"\n>>> limpieza OK (lead {lead_id} y sus interacciones borrados)")
