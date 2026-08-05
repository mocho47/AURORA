# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║        🧠 AURORA — SISTEMA DE MEMORIA COGNITIVA Y GENERATIVA         ║
║                     Episódica + Semántica Real                        ║
║              Sin simulaciones — SQLite persistente en disco           ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/MEMORIA/sistema_memoria.py
"""
import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aurora.memoria")

DB_PATH = Path(__file__).parent / "aurora_memoria.db"

# ─────────────────────────────────────────────────────────────────────
# HELPERS SÍNCRONOS (se ejecutan en thread pool para no bloquear el loop)
# ─────────────────────────────────────────────────────────────────────

def _init_db() -> None:
    """Crea las tablas si no existen. WAL mode para concurrencia segura."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS episodica (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            motor_origen TEXT   NOT NULL,
            motor_destino TEXT  DEFAULT 'sistema',
            tipo_evento TEXT    NOT NULL,
            contenido   TEXT    NOT NULL,
            importancia REAL    DEFAULT 0.5,
            consolidado INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS semantica (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tema            TEXT NOT NULL,
            patron          TEXT NOT NULL,
            conocimiento    TEXT NOT NULL,
            confianza       REAL DEFAULT 0.7,
            fuente_count    INTEGER DEFAULT 1,
            fecha_aprendizaje TEXT NOT NULL,
            fecha_actualizacion TEXT NOT NULL,
            UNIQUE(tema, patron)
        );

        CREATE INDEX IF NOT EXISTS idx_episodica_ts ON episodica(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_episodica_consolidado ON episodica(consolidado);
        CREATE INDEX IF NOT EXISTS idx_semantica_tema ON semantica(tema);
    """)
    conn.commit()
    conn.close()
    logger.info(f"DB memoria inicializada: {DB_PATH}")


def _insertar_episodio(
    motor_origen: str,
    tipo_evento: str,
    contenido: Dict,
    motor_destino: str = "sistema",
    importancia: float = 0.5,
) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.execute(
        """INSERT INTO episodica
           (timestamp, motor_origen, motor_destino, tipo_evento, contenido, importancia)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            datetime.utcnow().isoformat(),
            motor_origen,
            motor_destino,
            tipo_evento,
            json.dumps(contenido, ensure_ascii=False),
            importancia,
        ),
    )
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def _obtener_episodios_recientes(
    limite: int = 50, solo_no_consolidados: bool = False
) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    filtro = "WHERE consolidado=0" if solo_no_consolidados else ""
    rows = conn.execute(
        f"SELECT * FROM episodica {filtro} ORDER BY timestamp DESC LIMIT ?",
        (limite,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _marcar_consolidados(ids: List[int]) -> None:
    if not ids:
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    placeholders = ",".join("?" * len(ids))
    conn.execute(
        f"UPDATE episodica SET consolidado=1 WHERE id IN ({placeholders})", ids
    )
    conn.commit()
    conn.close()


def _purgar_episodios_viejos(dias: int = 90) -> int:
    """Borra episodios YA consolidados (su resumen ya vive en `semantica`) con más de
    `dias` de antigüedad. episodica no tenía ningún límite de crecimiento — guarda
    TODO el tráfico del bus neuronal, no solo interacciones de chat, así que crecía
    sin techo con meses de uso. Solo se borra lo consolidado — nunca lo pendiente."""
    from datetime import timedelta
    limite = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.execute(
        "DELETE FROM episodica WHERE consolidado=1 AND timestamp < ?", (limite,)
    )
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n


def _upsert_semantico(
    tema: str,
    patron: str,
    conocimiento: str,
    confianza: float = 0.7,
) -> None:
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """INSERT INTO semantica
               (tema, patron, conocimiento, confianza, fuente_count,
                fecha_aprendizaje, fecha_actualizacion)
           VALUES (?, ?, ?, ?, 1, ?, ?)
           ON CONFLICT(tema, patron) DO UPDATE SET
               conocimiento       = excluded.conocimiento,
               confianza          = MAX(semantica.confianza, excluded.confianza),
               fuente_count       = semantica.fuente_count + 1,
               fecha_actualizacion = excluded.fecha_actualizacion""",
        (tema, patron, conocimiento, confianza, now, now),
    )
    conn.commit()
    conn.close()


def _buscar_semantico(tema: str = "", limite: int = 20) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    if tema:
        # Se busca en tema, patrón Y conocimiento — no solo en tema. Encontrado el
        # 2026-08-04 al verificar la carga de conocimiento real: "a cuánto corto
        # MDF de 2.7" no hallaba nada, porque la receta vive bajo el tema "laser"
        # y la palabra "mdf" solo aparece en el texto. Buscando solo por tema, el
        # conocimiento cargado era inalcanzable con las preguntas que de verdad
        # hace Anuar, y se caía al respaldo de episodios (que traía un precio
        # viejo del MDF en vez de los parámetros de corte).
        #
        # Se busca por CADA palabra, no por la frase entera: "corto mdf 2.7" como
        # una sola cadena no calza con ningún texto, pero "mdf" sí.
        palabras = [p for p in tema.split() if len(p) >= 3][:4] or [tema]
        condiciones = " OR ".join(
            ["tema LIKE ? OR patron LIKE ? OR conocimiento LIKE ?"] * len(palabras))
        args = []
        for p in palabras:
            args.extend([f"%{p}%"] * 3)
        rows = conn.execute(
            f"SELECT * FROM semantica WHERE {condiciones} ORDER BY confianza DESC LIMIT ?",
            (*args, limite),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM semantica ORDER BY fecha_actualizacion DESC LIMIT ?",
            (limite,),
        ).fetchall()
    resultado = [dict(r) for r in rows]
    # semantica.tema SOLO puede valer una de 7 categorías fijas (ventas/coaching/...) —
    # una búsqueda por nombre propio o tema específico NUNCA puede coincidir ahí por
    # diseño del esquema, sin importar qué tan bien se extraiga el tema del mensaje.
    # Además lo que registrar() guarda no es visible aquí hasta que corre un ciclo de
    # sueño (motor_sueno.py, cada 60s solo con 5+min de inactividad y Groq disponible).
    # Si no hay nada en semantica, se busca también en episodica.contenido (texto crudo,
    # sin consolidar, pero real) para dar memoria de corto plazo aunque el sueño no
    # haya corrido todavía.
    if tema and not resultado:
        ep_rows = conn.execute(
            "SELECT timestamp, contenido FROM episodica WHERE contenido LIKE ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (f"%{tema}%", limite),
        ).fetchall()
        resultado = [{"tema": tema, "patron": "memoria_reciente_sin_consolidar",
                      "conocimiento": f"[{r['timestamp']}] {r['contenido'][:300]}",
                      "confianza": 0.5} for r in ep_rows]
    conn.close()
    return resultado


def _estadisticas() -> Dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    total_ep = conn.execute("SELECT COUNT(*) FROM episodica").fetchone()[0]
    no_consol = conn.execute(
        "SELECT COUNT(*) FROM episodica WHERE consolidado=0"
    ).fetchone()[0]
    total_sem = conn.execute("SELECT COUNT(*) FROM semantica").fetchone()[0]
    conn.close()
    return {
        "episodios_total": total_ep,
        "episodios_pendientes_sueno": no_consol,
        "conocimientos_semanticos": total_sem,
    }


# ─────────────────────────────────────────────────────────────────────
# CLASE PRINCIPAL — interfaz async pública
# ─────────────────────────────────────────────────────────────────────

class SistemaMemoria:
    """
    Memoria Cognitiva y Generativa de AURORA.

    · Episódica  → graba TODOS los eventos del sistema en tiempo real
    · Semántica  → almacena conocimiento destilado por el motor de sueño
    """

    _instancia: Optional["SistemaMemoria"] = None

    def __new__(cls) -> "SistemaMemoria":
        """Singleton — una sola instancia en todo el proceso."""
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    async def inicializar(self) -> None:
        if self._inicializado:
            return
        await asyncio.to_thread(_init_db)
        self._inicializado = True
        logger.info("✅ SistemaMemoria listo.")

    # ── EPISÓDICA ──────────────────────────────────────────────────

    async def registrar(
        self,
        motor_origen: str,
        tipo_evento: str,
        contenido: Dict[str, Any],
        motor_destino: str = "sistema",
        importancia: float = 0.5,
    ) -> int:
        """Graba un evento en memoria episódica. Retorna el ID del registro."""
        return await asyncio.to_thread(
            _insertar_episodio,
            motor_origen,
            tipo_evento,
            contenido,
            motor_destino,
            importancia,
        )

    async def episodios_recientes(
        self, limite: int = 50, solo_no_consolidados: bool = False
    ) -> List[Dict]:
        return await asyncio.to_thread(
            _obtener_episodios_recientes, limite, solo_no_consolidados
        )

    async def marcar_consolidados(self, ids: List[int]) -> None:
        await asyncio.to_thread(_marcar_consolidados, ids)

    async def purgar_episodios_viejos(self, dias: int = 90) -> int:
        """Borra episodios consolidados con más de `dias` — devuelve cuántos borró."""
        return await asyncio.to_thread(_purgar_episodios_viejos, dias)

    # ── SEMÁNTICA ──────────────────────────────────────────────────

    async def aprender(
        self,
        tema: str,
        patron: str,
        conocimiento: str,
        confianza: float = 0.7,
    ) -> None:
        """
        Escribe o actualiza un conocimiento en memoria semántica.
        Si el (tema, patron) ya existe, incrementa fuente_count y actualiza.
        """
        await asyncio.to_thread(
            _upsert_semantico, tema, patron, conocimiento, confianza
        )
        logger.debug(f"💡 Conocimiento aprendido [{tema}] → {patron}")

    async def recordar(
        self, tema: str = "", limite: int = 20
    ) -> List[Dict]:
        """Recupera conocimientos de la memoria semántica."""
        return await asyncio.to_thread(_buscar_semantico, tema, limite)

    # ── STATS ──────────────────────────────────────────────────────

    async def estadisticas(self) -> Dict:
        return await asyncio.to_thread(_estadisticas)

    async def estado(self) -> Dict:
        stats = await self.estadisticas()
        return {
            "sistema": "SistemaMemoria",
            "db_path": str(DB_PATH),
            "inicializado": self._inicializado,
            **stats,
        }


# Instancia global (singleton)
memoria = SistemaMemoria()
