# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║          👤 AURORA — CONTEXTO PERSISTENTE DE USUARIO                 ║
║    Recuerda quién es cada persona, su historial y temperatura         ║
║          de lead. Personalización real en cada interacción.           ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/MEMORIA/contexto_usuario.py
"""
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from groq import AsyncGroq

# Comparte la misma DB que sistema_memoria
from MEMORIA.sistema_memoria import DB_PATH

logger = logging.getLogger("aurora.contexto_usuario")

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# ─────────────────────────────────────────────────────────────────────
# PALABRAS CLAVE PARA HEURÍSTICA DE TEMPERATURA
# ─────────────────────────────────────────────────────────────────────

_PALABRAS_CIERRE = [
    "cómo pido", "cómo compro", "a nombre de", "cuándo pueden",
    "qué necesito", "me lo llevas", "cuándo me lo", "acepta tarjeta",
    "transferencia", "precio final", "quiero uno", "quiero dos",
]
_PALABRAS_INTERES = [
    "precio", "cuánto", "costo", "cotiz", "instala", "cuándo",
    "disponible", "quiero", "necesito", "mándame", "envíame",
]
_PALABRAS_INTERES_PRODUCTO = {
    "atf": ["atf", "retrofit", "led", "iluminación", "faros", "luces"],
    "milens": ["milens", "coaching", "laser", "familia", "teen"],
    "marketing": ["marketing", "redes", "tiktok", "instagram", "contenido"],
}
_TEMPERATURAS = ["frio", "tibio", "caliente", "cliente"]


# ─────────────────────────────────────────────────────────────────────
# OPS SÍNCRONAS (para thread pool)
# ─────────────────────────────────────────────────────────────────────

def _init_tablas() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios_contexto (
            user_id               TEXT PRIMARY KEY,
            nombre                TEXT DEFAULT 'Desconocido',
            canal_principal       TEXT DEFAULT 'api',
            interacciones_count   INTEGER DEFAULT 0,
            ultima_interaccion    TEXT,
            historial_resumen     TEXT DEFAULT '',
            estado_emocional      TEXT DEFAULT 'neutro',
            temperatura_lead      TEXT DEFAULT 'frio',
            interes_principal     TEXT DEFAULT '',
            estilo_comunicacion   TEXT DEFAULT 'directo',
            perfil_extra_json     TEXT DEFAULT '{}',
            fecha_primer_contacto TEXT
        );

        CREATE TABLE IF NOT EXISTS interacciones_detalle (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            canal           TEXT DEFAULT 'api',
            mensaje         TEXT NOT NULL,
            respuesta       TEXT NOT NULL,
            motores_usados  TEXT DEFAULT '',
            temperatura     TEXT DEFAULT 'frio',
            FOREIGN KEY(user_id) REFERENCES usuarios_contexto(user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_inter_uid  ON interacciones_detalle(user_id);
        CREATE INDEX IF NOT EXISTS idx_inter_ts   ON interacciones_detalle(timestamp DESC);
    """)
    conn.commit()
    conn.close()


def _get_usuario(user_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM usuarios_contexto WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _crear_usuario(user_id: str, canal: str) -> Dict:
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """INSERT OR IGNORE INTO usuarios_contexto
           (user_id, canal_principal, fecha_primer_contacto, ultima_interaccion)
           VALUES (?, ?, ?, ?)""",
        (user_id, canal, now, now),
    )
    conn.commit()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM usuarios_contexto WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row)


def _actualizar_perfil(
    user_id: str,
    interacciones_count: int,
    temperatura: str,
    interes: str,
    resumen: str,
    estado_emocional: str,
) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """UPDATE usuarios_contexto SET
               interacciones_count=?,
               temperatura_lead=?,
               interes_principal=?,
               historial_resumen=?,
               estado_emocional=?,
               ultima_interaccion=?
           WHERE user_id=?""",
        (
            interacciones_count,
            temperatura,
            interes,
            resumen,
            estado_emocional,
            datetime.utcnow().isoformat(),
            user_id,
        ),
    )
    conn.commit()
    conn.close()


def _insertar_interaccion(
    user_id: str,
    mensaje: str,
    respuesta: str,
    motores: str,
    canal: str,
    temperatura: str,
) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """INSERT INTO interacciones_detalle
           (user_id, timestamp, canal, mensaje, respuesta, motores_usados, temperatura)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            datetime.utcnow().isoformat(),
            canal,
            mensaje[:1000],
            respuesta[:1000],
            motores,
            temperatura,
        ),
    )
    conn.commit()
    conn.close()


def _get_ultimas_interacciones(user_id: str, limite: int = 10) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT mensaje, respuesta, temperatura FROM interacciones_detalle
           WHERE user_id=? ORDER BY timestamp DESC LIMIT ?""",
        (user_id, limite),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_leads_calientes() -> List[Dict]:
    """Retorna usuarios con temperatura 'caliente' o 'tibio' sin interacción reciente."""
    hace_48h = (datetime.utcnow() - timedelta(hours=48)).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT user_id, nombre, temperatura_lead, ultima_interaccion,
                  interes_principal, interacciones_count
           FROM usuarios_contexto
           WHERE temperatura_lead IN ('caliente', 'tibio')
             AND ultima_interaccion < ?
           ORDER BY temperatura_lead DESC, ultima_interaccion ASC
           LIMIT 20""",
        (hace_48h,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────

class ContextoUsuario:
    """
    Memoria persistente por usuario.

    · Recuerda a cada persona entre sesiones
    · Rastrea temperatura de lead (frio → tibio → caliente → cliente)
    · Resume el historial cada 10 interacciones con LLM
    · Detecta interés principal y estado emocional
    """

    _instancia: Optional["ContextoUsuario"] = None

    def __new__(cls) -> "ContextoUsuario":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self) -> None:
        if self._inicializado:
            return
        self._groq = AsyncGroq(api_key=GROQ_KEY) if GROQ_KEY else None

    async def inicializar(self) -> None:
        if self._inicializado:
            return
        await asyncio.to_thread(_init_tablas)
        self._inicializado = True
        logger.info("✅ ContextoUsuario listo.")

    # ── OBTENER / CREAR ───────────────────────────────────────────

    async def obtener(self, user_id: str, canal: str = "api") -> Dict:
        """Retorna el perfil del usuario. Lo crea si es nuevo."""
        ctx = await asyncio.to_thread(_get_usuario, user_id)
        if ctx is None:
            ctx = await asyncio.to_thread(_crear_usuario, user_id, canal)
            logger.info(f"👤 Nuevo usuario registrado: {user_id}")
        return ctx

    # ── ACTUALIZAR POST-INTERACCIÓN ───────────────────────────────

    async def actualizar(
        self,
        user_id: str,
        mensaje: str,
        respuesta: str,
        motores_usados: List[str],
        canal: str = "api",
    ) -> str:
        """
        Actualiza el perfil del usuario tras cada interacción.
        Retorna la nueva temperatura_lead.
        """
        ctx = await self.obtener(user_id, canal)
        count = ctx.get("interacciones_count", 0) + 1

        # Temperatura lead
        temp_nueva = self._calcular_temperatura(
            mensaje, ctx.get("temperatura_lead", "frio")
        )

        # Interés principal (detectado de la pregunta)
        interes = self._detectar_interes(mensaje) or ctx.get("interes_principal", "")

        # Estado emocional (heurístico rápido)
        emocional = self._detectar_emocion(mensaje)

        # Resumen de historial (cada 10 interacciones con LLM)
        resumen = ctx.get("historial_resumen", "")
        if count % 10 == 0 and self._groq:
            resumen = await self._resumir_historial(
                user_id, resumen, mensaje, respuesta
            )

        # Guardar interacción detallada
        await asyncio.to_thread(
            _insertar_interaccion,
            user_id,
            mensaje,
            respuesta,
            ",".join(motores_usados),
            canal,
            temp_nueva,
        )

        # Actualizar perfil
        await asyncio.to_thread(
            _actualizar_perfil,
            user_id,
            count,
            temp_nueva,
            interes,
            resumen,
            emocional,
        )

        if temp_nueva != ctx.get("temperatura_lead"):
            logger.info(
                f"🌡️  Lead {user_id}: {ctx.get('temperatura_lead')} → {temp_nueva}"
            )

        return temp_nueva

    async def leads_calientes(self) -> List[Dict]:
        """Retorna leads tibios/calientes sin interacción en 48h (para follow-up)."""
        return await asyncio.to_thread(_get_leads_calientes)

    # ── HEURÍSTICAS RÁPIDAS ───────────────────────────────────────

    def _calcular_temperatura(self, mensaje: str, temp_actual: str) -> str:
        msg = mensaje.lower()
        idx = _TEMPERATURAS.index(temp_actual) if temp_actual in _TEMPERATURAS else 0

        # Señal de cierre → sube 2 niveles
        if any(p in msg for p in _PALABRAS_CIERRE) and idx < 3:
            return _TEMPERATURAS[min(idx + 2, 2)]  # máx caliente, cliente lo confirma vendedor

        # Señal de interés → sube 1 nivel
        if any(p in msg for p in _PALABRAS_INTERES) and idx < 2:
            return _TEMPERATURAS[idx + 1]

        return temp_actual

    def _detectar_interes(self, mensaje: str) -> str:
        msg = mensaje.lower()
        for producto, palabras in _PALABRAS_INTERES_PRODUCTO.items():
            if any(p in msg for p in palabras):
                return producto
        return ""

    def _detectar_emocion(self, mensaje: str) -> str:
        msg = mensaje.lower()
        positivas = ["genial", "excelente", "gracias", "perfecto", "me encanta", "quiero"]
        negativas = ["mal", "problema", "no funciona", "enojado", "molesto", "falla"]
        if any(p in msg for p in positivas):
            return "positivo"
        if any(p in msg for p in negativas):
            return "negativo"
        return "neutro"

    # ── RESUMEN CON LLM ───────────────────────────────────────────

    async def _resumir_historial(
        self, user_id: str, resumen_previo: str, ultimo_msg: str, ultima_resp: str
    ) -> str:
        interacciones = await asyncio.to_thread(
            _get_ultimas_interacciones, user_id, 10
        )
        if not interacciones:
            return resumen_previo

        fragmentos = "\n".join([
            f"- Usuario: {i['mensaje'][:120]}\n  Aurora: {i['respuesta'][:120]}"
            for i in interacciones
        ])

        try:
            r = await self._groq.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Resumen previo del cliente: {resumen_previo}\n\n"
                        f"Últimas 10 interacciones:\n{fragmentos}\n\n"
                        "Escribe un resumen actualizado del perfil de este cliente en máximo 150 palabras. "
                        "Incluye: intereses, objeciones, temperatura de compra, y siguiente acción recomendada. "
                        "Solo el resumen, sin comentarios."
                    )
                }],
                max_tokens=250,
                temperature=0.3,
            )
            nuevo = r.choices[0].message.content.strip()
            logger.debug(f"📝 Historial resumido para {user_id}")
            return nuevo
        except Exception as exc:
            logger.warning(f"No se pudo resumir historial de {user_id}: {exc}")
            return resumen_previo


# Instancia global (singleton)
ctx_usuario = ContextoUsuario()
