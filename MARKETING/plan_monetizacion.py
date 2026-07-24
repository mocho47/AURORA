# -*- coding: utf-8 -*-
"""
AURORA · PLAN DE MONETIZACIÓN (constancia medible, datos reales)

Filosofía honesta (regla de Anuar: 0 simulaciones):
- NO auto-postea. Publicar es acción real; Anuar aprueba y sube (regla del publicador).
- Lo que garantiza el resultado es la CONSTANCIA. Este motor la vuelve medible:
  arma el calendario con los VIDEOS REALES de Anuar y le sirve "el post de HOY".
- El gancho/caption es un BORRADOR (LLM real, Groq) que Anuar ajusta al video concreto;
  no se inventa contenido específico del video (los archivos no describen su contenido).

Horarios = best-practice general de cada red (NO son analytics de Anuar; para eso hay
que conectar Meta). Rotan los videos para no repetir hasta agotarlos.
"""
from __future__ import annotations
import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "monetizacion.db"
VIDEOS_DIR = Path(r"C:\Users\Administrador\Videos")

# DIRECTIVA (Anuar): 1 video al día, publicado en TODAS las redes el mismo día.
# El video avanza uno por día (no se toma otro hasta que el actual salió en todas).
PLATAFORMAS = [
    ("TikTok",    "19:00"),
    ("Instagram", "12:00"),
    ("Facebook",  "19:00"),
    ("YouTube",   "10:00"),
]
ANCHOR = date(2026, 7, 1)  # ancla fija (día 0 del calendario)
DIAS_ROTACION = 3          # el bloque de videos rota N días entre las redes, luego se toma otro bloque
BLOQUE = len(PLATAFORMAS)  # tamaño del bloque = nº de redes (1 video distinto por red)


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS plan_redes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            plataforma TEXT,
            hora TEXT,
            video TEXT,
            bloque INTEGER DEFAULT 0,
            aprobado INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'pendiente',
            publicado_en TEXT,
            UNIQUE(fecha, plataforma)
        )""")
    for ddl in ("bloque INTEGER DEFAULT 0", "aprobado INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE plan_redes ADD COLUMN {ddl}")
        except Exception:
            pass
    con.commit()
    con.close()


VIDEO_EXT = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm")


def listar_videos() -> list:
    """
    TODOS los videos REALES de Anuar, RECURSIVO (incluye subcarpetas: r11, terminados,
    VIRALIZADOS, etc.). Devuelve rutas relativas a VIDEOS_DIR para no repetir y variar.
    """
    if not VIDEOS_DIR.exists():
        return []
    # Excluye lo YA publicado y los duplicados apartados: el pool son solo únicos vivos.
    _EXCLUIR = {"PUBLICADOS", "DUPLICADOS_REVISAR"}
    vids = sorted(str(p.relative_to(VIDEOS_DIR)) for p in VIDEOS_DIR.rglob("*")
                  if p.is_file() and p.suffix.lower() in VIDEO_EXT
                  and not (_EXCLUIR & set(p.parts)))
    return vids


def catalogo() -> dict:
    """
    UNIFICA y AGRUPA los videos en un índice por carpeta (sin mover ni borrar nada).
    Este catálogo es la 'organización' segura + alimenta el plan.
    """
    if not VIDEOS_DIR.exists():
        return {"status": "sin_carpeta", "ruta": str(VIDEOS_DIR)}
    grupos: dict = {}
    total = 0
    tam = 0
    for p in VIDEOS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in VIDEO_EXT:
            carpeta = str(p.parent.relative_to(VIDEOS_DIR)) or "(raíz)"
            g = grupos.setdefault(carpeta, {"videos": 0, "mb": 0})
            g["videos"] += 1
            g["mb"] += round(p.stat().st_size / 1048576, 1)
            total += 1
            tam += p.stat().st_size
    grupos_ord = dict(sorted(grupos.items(), key=lambda kv: kv[1]["videos"], reverse=True))
    return {"status": "ok", "total_videos": total, "gb_total": round(tam / 1073741824, 2),
            "grupos": grupos_ord, "ruta": str(VIDEOS_DIR)}


def generar_plan(dias: int = 14, reiniciar: bool = False) -> dict:
    """
    Crea/extiende el calendario desde HOY por 'dias'. Idempotente: una fila por fecha.
    reiniciar=True borra las publicaciones PENDIENTES (respeta las ya publicadas).
    """
    init_db()
    videos = listar_videos()
    if not videos:
        return {"status": "sin_videos",
                "detalle": f"No hay videos en {VIDEOS_DIR}. Coloca .mp4 ahí y regenera."}
    con = _conn()
    if reiniciar:
        con.execute("DELETE FROM plan_redes WHERE estado='pendiente'")
        con.commit()
    creadas = 0
    hoy = date.today()
    nv = len(videos)
    for i in range(max(1, min(int(dias), 366))):
        fd = hoy + timedelta(days=i)
        f = fd.isoformat()
        dayidx = (fd - ANCHOR).days
        bloque = dayidx // DIAS_ROTACION           # qué bloque de videos toca
        rot = dayidx % DIAS_ROTACION               # cuántas posiciones rotó el bloque
        for j, (plat, hora) in enumerate(PLATAFORMAS):
            existe = con.execute("SELECT 1 FROM plan_redes WHERE fecha=? AND plataforma=?",
                                 (f, plat)).fetchone()
            if existe:
                continue
            # cada red toma un video DISTINTO del bloque; el bloque rota entre redes por día
            vidx = (bloque * BLOQUE + (j + rot) % BLOQUE) % nv
            con.execute("""INSERT INTO plan_redes (fecha, plataforma, hora, video, bloque, estado)
                           VALUES (?, ?, ?, ?, ?, 'pendiente')""", (f, plat, hora, videos[vidx], bloque))
            creadas += 1
    con.commit()
    con.close()
    return {"status": "ok", "creadas": creadas, "videos_disponibles": nv, "dias": dias,
            "dias_rotacion": DIAS_ROTACION, "redes": [p for p, _ in PLATAFORMAS]}


def post_de_hoy() -> dict:
    """Los posts de HOY: 1 video DISTINTO por red (TikTok/IG/FB/YouTube)."""
    init_db()
    con = _conn()
    hoy = date.today().isoformat()
    rows = con.execute("SELECT * FROM plan_redes WHERE fecha=? ORDER BY id", (hoy,)).fetchall()
    if not rows:
        con.close()
        g = generar_plan()
        if g["status"] != "ok":
            return g
        con = _conn()
        rows = con.execute("SELECT * FROM plan_redes WHERE fecha=? ORDER BY id", (hoy,)).fetchall()
    posts = [dict(r) for r in rows]
    con.close()
    pendientes = sum(1 for p in posts if p["estado"] == "pendiente")
    return {"status": "ok", "fecha": hoy, "posts": posts, "pendientes": pendientes,
            "ruta_videos": str(VIDEOS_DIR), **racha()}


def marcar_publicado(pid: int) -> dict:
    """Marca UNA red como publicada (avanza la racha si el día queda completo)."""
    init_db()
    con = _conn()
    con.execute("UPDATE plan_redes SET estado='publicado', publicado_en=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), pid))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    if not n:
        return {"status": "no_encontrado", "id": pid}
    return {"status": "ok", "id": pid, **racha()}


def marcar_dia(fecha: str = "") -> dict:
    """Marca TODAS las redes de un día como publicadas (por defecto HOY)."""
    init_db()
    fecha = fecha or date.today().isoformat()
    con = _conn()
    con.execute("UPDATE plan_redes SET estado='publicado', publicado_en=? "
                "WHERE fecha=? AND estado='pendiente'",
                (datetime.now().isoformat(timespec="seconds"), fecha))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    return {"status": "ok", "fecha": fecha, "marcadas": n, **racha()}


def racha() -> dict:
    """Racha: días CONSECUTIVOS donde TODAS las redes del día quedaron publicadas."""
    con = _conn()
    rows = con.execute(
        "SELECT fecha, SUM(CASE WHEN estado='publicado' THEN 1 ELSE 0 END) pub, COUNT(*) tot "
        "FROM plan_redes GROUP BY fecha").fetchall()
    total = con.execute("SELECT COUNT(*) FROM plan_redes WHERE estado='publicado'").fetchone()[0]
    con.close()
    completos = {r["fecha"] for r in rows if r["tot"] > 0 and r["pub"] == r["tot"]}
    d = date.today()
    if d.isoformat() not in completos:
        d = d - timedelta(days=1)
    r = 0
    while d.isoformat() in completos:
        r += 1
        d = d - timedelta(days=1)
    return {"racha_dias": r, "publicados_total": total}


def bloque_pendiente() -> dict:
    """El próximo bloque (de hoy en adelante) que NO ha sido aprobado. Para el aviso en pantalla."""
    init_db()
    con = _conn()
    hoy = date.today().isoformat()
    row = con.execute(
        "SELECT bloque, MIN(fecha) fi FROM plan_redes "
        "WHERE aprobado=0 AND fecha>=? GROUP BY bloque ORDER BY fi LIMIT 1", (hoy,)).fetchone()
    if not row:
        con.close()
        return {"status": "ok", "pendiente": False}
    bl = row["bloque"]
    posts = [dict(r) for r in con.execute(
        "SELECT * FROM plan_redes WHERE bloque=? ORDER BY fecha, id", (bl,)).fetchall()]
    con.close()
    fechas = sorted({p["fecha"] for p in posts})
    vids = []
    for p in posts:
        b = os.path.basename(p["video"])
        if b not in vids:
            vids.append(b)
    return {"status": "ok", "pendiente": True, "bloque": bl,
            "desde": fechas[0], "hasta": fechas[-1], "posts": posts,
            "videos": vids, "total": len(posts)}


def revisar_bloque(bloque: int) -> dict:
    """Todos los posts de un bloque (para revisarlo antes de aprobar)."""
    init_db()
    con = _conn()
    posts = [dict(r) for r in con.execute(
        "SELECT * FROM plan_redes WHERE bloque=? ORDER BY fecha, id", (int(bloque),)).fetchall()]
    con.close()
    return {"status": "ok", "bloque": bloque, "posts": posts}


def aprobar_post(pid: int) -> dict:
    """Aprueba UNA publicación del bloque."""
    init_db()
    con = _conn()
    con.execute("UPDATE plan_redes SET aprobado=1 WHERE id=?", (int(pid),))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    return {"status": "ok" if n else "no_encontrado", "id": pid}


def aprobar_bloque(bloque: int) -> dict:
    """Aprueba TODO un bloque de un golpe."""
    init_db()
    con = _conn()
    con.execute("UPDATE plan_redes SET aprobado=1 WHERE bloque=?", (int(bloque),))
    con.commit()
    n = con.execute("SELECT changes()").fetchone()[0]
    con.close()
    return {"status": "ok", "bloque": bloque, "aprobadas": n}


def plan(dias: int = 14) -> dict:
    """Calendario de HOY en adelante, agrupado por día (cada día trae sus redes)."""
    init_db()
    con = _conn()
    hoy = date.today().isoformat()
    fin = (date.today() + timedelta(days=max(1, dias))).isoformat()
    rows = con.execute(
        "SELECT * FROM plan_redes WHERE fecha>=? AND fecha<=? ORDER BY fecha, id",
        (hoy, fin)).fetchall()
    con.close()
    dias_map = {}
    for r in rows:
        dias_map.setdefault(r["fecha"], []).append(dict(r))
    items = [{"fecha": f, "posts": ps} for f, ps in sorted(dias_map.items())]
    return {"status": "ok", "items": items, **racha()}


def copy_borrador(plataforma: str = "TikTok", tipo: str = "Antes/Después",
                  producto: str = "retrofit de faros (ATF)") -> dict:
    """
    Borrador REAL de gancho+caption con Groq, para ATF. Anuar lo ajusta al video.
    Honesto: es plantilla de arranque, no descripción del video concreto.
    """
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return {"status": "sin_llm", "detalle": "Falta GROQ_API_KEY en .env."}
    prompt = (
        f"Eres experto en contenido corto para {plataforma}. Negocio: {producto} en Guadalajara. "
        f"Tipo de video: {tipo}. Genera en español mexicano natural, en JSON con: "
        "gancho (primeros 3 seg, para el video), caption (con CTA a WhatsApp), hashtags (6). "
        "Enfoca en el RESULTADO visual (ver mejor de noche, faros como nuevos) y en agendar. "
        "NO inventes precios ni specs. Solo el JSON."
    )
    try:
        import requests
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}"},
                          json={"model": "llama-3.1-8b-instant",
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.85}, timeout=30)
        return {"status": "ok", "plataforma": plataforma, "tipo": tipo,
                "borrador": r.json()["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}
