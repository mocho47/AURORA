# -*- coding: utf-8 -*-
"""
📊 AURORA — ANALÍTICA DE MARKETING CON MEMORIA
Registra rendimiento de publicaciones. Extrae qué funcionó.
Alimenta la memoria semántica con conocimiento real de campañas.
Ruta: C:/AURORA/MEMORIA/analitica_marketing.py
"""
import asyncio, json, logging, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from MEMORIA.sistema_memoria import DB_PATH

logger = logging.getLogger("aurora.analitica_marketing")


# ── Tablas SQLite ────────────────────────────────────────────────────

def _init_tablas() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS publicaciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            plataforma      TEXT NOT NULL,
            tipo_contenido  TEXT NOT NULL,   -- hook|caption|reels|story|post
            hook_texto      TEXT DEFAULT '',
            caption_texto   TEXT DEFAULT '',
            hashtags        TEXT DEFAULT '',
            url_contenido   TEXT DEFAULT '',
            -- métricas (se actualizan después)
            vistas          INTEGER DEFAULT 0,
            likes           INTEGER DEFAULT 0,
            compartidos     INTEGER DEFAULT 0,
            comentarios     INTEGER DEFAULT 0,
            leads_generados INTEGER DEFAULT 0,
            engagement_rate REAL    DEFAULT 0.0,
            -- estado
            activa          INTEGER DEFAULT 1,
            consolidada     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS rendimiento_diario (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            plataforma  TEXT NOT NULL,
            total_vistas    INTEGER DEFAULT 0,
            total_leads     INTEGER DEFAULT 0,
            engagement_prom REAL    DEFAULT 0.0,
            mejor_contenido TEXT DEFAULT '',
            UNIQUE(fecha, plataforma)
        );

        CREATE INDEX IF NOT EXISTS idx_pub_plataforma ON publicaciones(plataforma);
        CREATE INDEX IF NOT EXISTS idx_pub_fecha      ON publicaciones(fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_pub_consolid   ON publicaciones(consolidada);
    """)
    conn.commit()
    conn.close()


def _insertar_publicacion(datos: Dict) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.execute(
        """INSERT INTO publicaciones
           (fecha,plataforma,tipo_contenido,hook_texto,caption_texto,hashtags,url_contenido)
           VALUES (?,?,?,?,?,?,?)""",
        (
            datos.get("fecha", datetime.utcnow().isoformat()),
            datos.get("plataforma", ""),
            datos.get("tipo_contenido", "post"),
            datos.get("hook", "")[:500],
            datos.get("caption", "")[:1000],
            datos.get("hashtags", "")[:300],
            datos.get("url", ""),
        ),
    )
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def _actualizar_metricas(pub_id: int, metricas: Dict) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    vistas = metricas.get("vistas", 0)
    likes  = metricas.get("likes", 0)
    eng    = round((likes / vistas * 100), 2) if vistas else 0.0
    conn.execute(
        """UPDATE publicaciones SET
               vistas=?, likes=?, compartidos=?, comentarios=?,
               leads_generados=?, engagement_rate=?
           WHERE id=?""",
        (vistas, likes, metricas.get("compartidos", 0),
         metricas.get("comentarios", 0), metricas.get("leads", 0), eng, pub_id),
    )
    conn.commit()
    conn.close()


def _get_top_performers(dias: int = 30, limite: int = 10) -> List[Dict]:
    desde = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT * FROM publicaciones
           WHERE fecha >= ? AND vistas > 0
           ORDER BY engagement_rate DESC, leads_generados DESC
           LIMIT ?""",
        (desde, limite),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_no_consolidadas() -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM publicaciones WHERE consolidada=0 AND vistas > 0 ORDER BY fecha DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _marcar_consolidadas(ids: List[int]) -> None:
    if not ids:
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"UPDATE publicaciones SET consolidada=1 WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()


def _resumen_por_plataforma(dias: int = 30) -> List[Dict]:
    desde = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT plataforma,
                  COUNT(*) as publicaciones,
                  SUM(vistas) as total_vistas,
                  SUM(leads_generados) as total_leads,
                  ROUND(AVG(engagement_rate),2) as eng_prom,
                  MAX(engagement_rate) as eng_max
           FROM publicaciones
           WHERE fecha >= ?
           GROUP BY plataforma
           ORDER BY total_leads DESC""",
        (desde,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Clase principal ───────────────────────────────────────────────────

class AnaliticaMarketing:
    """
    Registra rendimiento de publicaciones y alimenta la memoria semántica.
    El motor de sueño llama a consolidar_en_semantica() durante cada ciclo.
    """

    _instancia: Optional["AnaliticaMarketing"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    async def inicializar(self) -> None:
        if self._inicializado:
            return
        await asyncio.to_thread(_init_tablas)
        self._inicializado = True
        logger.info("✅ AnaliticaMarketing lista.")

    # ── REGISTRO ───────────────────────────────────────────────

    async def registrar_publicacion(self, datos: Dict) -> int:
        """Registra una nueva publicación. Retorna su ID."""
        pub_id = await asyncio.to_thread(_insertar_publicacion, datos)
        # También en episódica
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen="analitica_marketing",
                tipo_evento="publicacion_creada",
                contenido={"pub_id": pub_id, "plataforma": datos.get("plataforma"), "hook": datos.get("hook", "")[:100]},
                importancia=0.6,
            )
        except Exception:
            pass
        return pub_id

    async def actualizar_metricas(self, pub_id: int, metricas: Dict) -> None:
        """Actualiza vistas, likes, leads de una publicación después de publicarla."""
        await asyncio.to_thread(_actualizar_metricas, pub_id, metricas)
        # Si generó leads → importancia alta en episódica
        if metricas.get("leads", 0) > 0:
            try:
                from MEMORIA.sistema_memoria import memoria
                await memoria.registrar(
                    motor_origen="analitica_marketing",
                    tipo_evento="lead_generado",
                    contenido={"pub_id": pub_id, **metricas},
                    importancia=0.95,
                )
            except Exception:
                pass

    # ── ANÁLISIS ───────────────────────────────────────────────

    async def top_performers(self, dias: int = 30) -> List[Dict]:
        return await asyncio.to_thread(_get_top_performers, dias)

    async def resumen_plataformas(self, dias: int = 30) -> List[Dict]:
        return await asyncio.to_thread(_resumen_por_plataforma, dias)

    # ── CONSOLIDACIÓN A MEMORIA SEMÁNTICA ─────────────────────

    async def consolidar_en_semantica(self) -> Dict:
        """
        Extrae patrones de las publicaciones no consolidadas
        y los escribe en memoria semántica.
        Llamado por motor_sueno durante cada ciclo de sueño.
        """
        publicaciones = await asyncio.to_thread(_get_no_consolidadas)
        if not publicaciones:
            return {"consolidadas": 0}

        from MEMORIA.sistema_memoria import memoria

        conocimientos_escritos = 0
        ids_procesados = []

        # Patrón: mejores plataformas
        resumen = await self.resumen_plataformas(30)
        for item in resumen:
            if item["publicaciones"] >= 2:
                await memoria.aprender(
                    tema="marketing",
                    patron=f"rendimiento_{item['plataforma']}",
                    conocimiento=(
                        f"{item['plataforma']}: {item['publicaciones']} publicaciones, "
                        f"{item['total_vistas']} vistas totales, "
                        f"{item['total_leads']} leads, "
                        f"engagement promedio {item['eng_prom']}%"
                    ),
                    confianza=min(0.5 + item["publicaciones"] * 0.05, 0.95),
                )
                conocimientos_escritos += 1

        # Patrón: top performers → qué hooks funcionaron
        top = await self.top_performers(30)
        for pub in top[:5]:
            if pub.get("engagement_rate", 0) > 3.0 or pub.get("leads_generados", 0) > 0:
                await memoria.aprender(
                    tema="marketing",
                    patron=f"hook_exitoso_{pub['plataforma']}",
                    conocimiento=(
                        f"Hook exitoso en {pub['plataforma']} ({pub['engagement_rate']}% eng, "
                        f"{pub['leads_generados']} leads): \"{pub['hook_texto'][:150]}\""
                    ),
                    confianza=min(0.6 + pub["leads_generados"] * 0.1, 0.95),
                )
                conocimientos_escritos += 1
            ids_procesados.append(pub["id"])

        # Marcar todas las procesadas como consolidadas
        all_ids = [p["id"] for p in publicaciones]
        await asyncio.to_thread(_marcar_consolidadas, all_ids)

        logger.info(f"📊 Marketing consolidado: {conocimientos_escritos} patrones → memoria semántica")
        return {
            "publicaciones_procesadas": len(all_ids),
            "conocimientos_escritos": conocimientos_escritos,
        }

    async def estado(self) -> Dict:
        top = await self.top_performers(7)
        return {
            "sistema": "AnaliticaMarketing",
            "inicializado": self._inicializado,
            "top_7dias": len(top),
        }


# Instancia global
analitica_marketing = AnaliticaMarketing()
