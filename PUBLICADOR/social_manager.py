# -*- coding: utf-8 -*-
"""
AURORA · ADMINISTRADOR DE REDES SOCIALES (gestor + agenda)  —  cartucho self-contained.

Qué hace (y qué NO):
- GESTIONA y AGENDA publicaciones para Facebook, Instagram, TikTok y YouTube.
- Reporta el estado REAL de conexión de cada red (token presente / falta configurar),
  reutilizando PUBLICADOR/publicador_core.py y las env vars oficiales.
- NO auto-postea. Publicar es una acción real; Anuar la aprueba y ejecuta desde el
  publicador. Este módulo llega hasta "listo para publicar", nunca postea solo.

Persistencia: SQLite en ROOT/social.db (WAL, row_factory=Row), mismo estilo que
MARKETING/plan_monetizacion.py. Todas las funciones devuelven dict con "status".
"""
from __future__ import annotations
import os
import importlib.util
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

# ROOT = C:\AURORA.worktrees  (mismo criterio que plan_monetizacion.py: parent.parent)
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "social.db"

# Redes soportadas y su env var de token de API oficial (fuente de verdad del estado).
REDES = {
    "facebook":  "FB_PAGE_TOKEN",
    "instagram": "INSTAGRAM_ACCESS_TOKEN",
    "tiktok":    "TIKTOK_ACCESS_TOKEN",
    "youtube":   "YOUTUBE_ACCESS_TOKEN",
}


# --------------------------------------------------------------------------- #
# Infra: .env + conexión + esquema
# --------------------------------------------------------------------------- #
def _cargar_env() -> None:
    """Carga ROOT/.env a os.environ si aún no está (para estado real standalone)."""
    envp = ROOT / ".env"
    if not envp.exists():
        return
    try:
        for linea in envp.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            red TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            texto TEXT DEFAULT '',
            media_url TEXT DEFAULT '',
            estado TEXT DEFAULT 'pendiente',
            creado_en TEXT,
            publicado_en TEXT
        )""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_agenda_fecha ON agenda(fecha)")
    con.commit()
    con.close()


def _norm_red(red: str) -> str:
    return (red or "").strip().lower()


# --------------------------------------------------------------------------- #
# Estado REAL de conexiones
# --------------------------------------------------------------------------- #
def _cargar_publicador():
    """Carga PUBLICADOR/publicador_core.py por ruta (importlib), cacheado en el módulo."""
    global _PUB_CACHE
    try:
        return _PUB_CACHE
    except NameError:
        pass
    ruta = Path(__file__).resolve().parent / "publicador_core.py"
    try:
        spec = importlib.util.spec_from_file_location("publicador_core", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        mod = None
    globals()["_PUB_CACHE"] = mod
    return mod


def estado_conexiones() -> dict:
    """
    Estado REAL de cada red. Honesto: si no hay token de API, dice 'falta configurar'.
    Se apoya en publicador_core.estado_redes() cuando está disponible (incluye el vault),
    y en las env vars oficiales como respaldo. Reporta también WhatsApp si hay datos.
    """
    _cargar_env()
    pub = _cargar_publicador()

    # Estado del vault/login vía publicador_core (si carga).
    detalle_pub = {}
    if pub is not None and hasattr(pub, "estado_redes"):
        try:
            for r in pub.estado_redes().get("redes", []):
                detalle_pub[_norm_red(r.get("plataforma"))] = r
        except Exception:
            detalle_pub = {}

    redes = []
    conectadas = 0
    for red, env_var in REDES.items():
        token = bool(os.getenv(env_var))
        info = detalle_pub.get(red, {})
        if token:
            estado, msg = "conectada", "Token de API presente."
            conectadas += 1
        elif info.get("login_vault"):
            estado, msg = "falta configurar", "Hay login en el vault pero falta token de API."
        else:
            estado, msg = "falta configurar", f"Sin token: define {env_var} en .env."
        redes.append({
            "red": red,
            "estado": estado,
            "token_api": token,
            "login_vault": bool(info.get("login_vault", False)),
            "env_var": env_var,
            "detalle": msg,
        })

    # WhatsApp (canal de contacto, no de publicación): estado real si hay credenciales.
    whatsapp = None
    if pub is not None and hasattr(pub, "estado_whatsapp"):
        try:
            whatsapp = pub.estado_whatsapp()
        except Exception:
            whatsapp = None

    return {
        "status": "ok",
        "conectadas": conectadas,
        "total": len(REDES),
        "redes": redes,
        "whatsapp": whatsapp,
        "publicador_core": bool(pub is not None),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


# --------------------------------------------------------------------------- #
# Agenda (CRUD)
# --------------------------------------------------------------------------- #
def agendar(red: str, fecha: str, hora: str, texto: str, media_url: str = "") -> dict:
    """
    Agenda una publicación (estado 'pendiente'). NO publica: sólo la deja lista.
    fecha 'YYYY-MM-DD', hora 'HH:MM'. Valida red y formato de fecha/hora.
    """
    init_db()
    r = _norm_red(red)
    if r not in REDES:
        return {"status": "error", "detalle": f"Red '{red}' no soportada. Usa: {', '.join(REDES)}"}
    try:
        datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"status": "error", "detalle": "fecha debe ser YYYY-MM-DD y hora HH:MM."}
    if not (texto or "").strip() and not (media_url or "").strip():
        return {"status": "error", "detalle": "La publicación necesita texto o media_url."}

    con = _conn()
    cur = con.execute(
        """INSERT INTO agenda (red, fecha, hora, texto, media_url, estado, creado_en)
           VALUES (?, ?, ?, ?, ?, 'pendiente', ?)""",
        (r, fecha, hora, texto or "", media_url or "",
         datetime.now().isoformat(timespec="seconds")))
    con.commit()
    pid = cur.lastrowid
    con.close()
    return {"status": "ok", "id": pid, "red": r, "fecha": fecha, "hora": hora,
            "estado": "pendiente", "nota": "Agendada. Anuar aprueba y publica; no se postea solo."}


def calendario(dias: int = 14) -> dict:
    """Publicaciones de HOY en adelante hasta hoy+dias, ordenadas por fecha y hora."""
    init_db()
    hoy = date.today().isoformat()
    fin = (date.today() + timedelta(days=max(1, int(dias)))).isoformat()
    con = _conn()
    rows = con.execute(
        """SELECT * FROM agenda WHERE fecha >= ? AND fecha <= ?
           ORDER BY fecha, hora, id""", (hoy, fin)).fetchall()
    con.close()
    return {"status": "ok", "desde": hoy, "hasta": fin,
            "total": len(rows), "items": [dict(x) for x in rows]}


def marcar_publicado(id: int) -> dict:
    """Marca una publicación agendada como 'publicado' (registro manual tras aprobar)."""
    init_db()
    con = _conn()
    con.execute("UPDATE agenda SET estado='publicado', publicado_en=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), int(id)))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    return ({"status": "ok", "id": int(id), "estado": "publicado"} if n
            else {"status": "no_encontrado", "id": int(id)})


def eliminar(id: int) -> dict:
    """Elimina una publicación de la agenda."""
    init_db()
    con = _conn()
    con.execute("DELETE FROM agenda WHERE id=?", (int(id),))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    return ({"status": "ok", "id": int(id), "eliminada": True} if n
            else {"status": "no_encontrado", "id": int(id)})


def resumen() -> dict:
    """Conteo de agendadas por red/estado + próximas publicaciones pendientes."""
    init_db()
    hoy = date.today().isoformat()
    con = _conn()
    pendientes = con.execute(
        "SELECT COUNT(*) FROM agenda WHERE estado='pendiente'").fetchone()[0]
    publicadas = con.execute(
        "SELECT COUNT(*) FROM agenda WHERE estado='publicado'").fetchone()[0]
    por_red = {row["red"]: row["n"] for row in con.execute(
        """SELECT red, COUNT(*) AS n FROM agenda WHERE estado='pendiente'
           GROUP BY red""").fetchall()}
    proximas = con.execute(
        """SELECT id, red, fecha, hora, substr(texto,1,60) AS resumen_texto
           FROM agenda WHERE estado='pendiente' AND fecha >= ?
           ORDER BY fecha, hora LIMIT 5""", (hoy,)).fetchall()
    con.close()
    return {"status": "ok", "pendientes": pendientes, "publicadas": publicadas,
            "por_red": por_red, "proximas": [dict(x) for x in proximas]}


# --------------------------------------------------------------------------- #
# Autoprueba standalone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import json

    def show(titulo, data):
        print(f"\n=== {titulo} ===")
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    show("estado_conexiones", estado_conexiones())

    a = agendar("instagram", "2026-07-20", "12:00",
                "Reel: antes/después de faros ATF. CTA a WhatsApp.",
                media_url="https://example.com/reel.mp4")
    show("agendar", a)
    pid = a.get("id")

    show("calendario(14)", calendario(14))
    show("resumen (con la de prueba)", resumen())
    show("marcar_publicado", marcar_publicado(pid))
    show("eliminar", eliminar(pid))
    show("resumen (limpio)", resumen())
    print("\nDB:", DB)
