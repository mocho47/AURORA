# -*- coding: utf-8 -*-
"""
🧬 AURORA — PERFIL DE HABILIDADES DE ANUAR
Aprende las habilidades reales de Anuar, detecta áreas de oportunidad
y complementa de forma proactiva y coherente.
Ruta: C:/AURORA/MEMORIA/perfil_habilidades.py
"""
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from groq import AsyncGroq
from MEMORIA.sistema_memoria import DB_PATH

logger = logging.getLogger("aurora.perfil_habilidades")

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# ── Categorías de habilidades ─────────────────────────────────────
CATEGORIAS = [
    "ventas",        # cerrar tratos, negociación, seguimiento
    "marketing",     # contenido, estrategia, redes sociales
    "tecnico",       # programación, software, hardware
    "operaciones",   # logística, procesos, administración
    "creatividad",   # diseño, video, fotografía
    "finanzas",      # contabilidad, precios, márgenes
    "liderazgo",     # gestión de equipo, toma de decisiones
    "comunicacion",  # redacción, presentaciones, persuasión
]

NIVELES = {1: "básico", 2: "en desarrollo", 3: "competente", 4: "avanzado", 5: "experto"}


# ── Ops síncronas ─────────────────────────────────────────────────

def _init_tablas() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS habilidades_anuar (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria       TEXT NOT NULL,
            habilidad       TEXT NOT NULL,
            nivel           INTEGER DEFAULT 3,   -- 1-5
            evidencia       TEXT DEFAULT '',
            veces_detectada INTEGER DEFAULT 1,
            ultima_actualizacion TEXT NOT NULL,
            UNIQUE(categoria, habilidad)
        );

        CREATE TABLE IF NOT EXISTS areas_oportunidad (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria       TEXT NOT NULL,
            descripcion     TEXT NOT NULL,
            frecuencia      INTEGER DEFAULT 1,   -- cuántas veces AURORA ayudó aquí
            accion_sugerida TEXT DEFAULT '',
            resuelta        INTEGER DEFAULT 0,
            fecha           TEXT NOT NULL,
            UNIQUE(categoria, descripcion)
        );

        CREATE TABLE IF NOT EXISTS sesiones_aprendizaje (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            resumen     TEXT NOT NULL,
            habilidades_nuevas  TEXT DEFAULT '[]',
            areas_nuevas        TEXT DEFAULT '[]'
        );

        CREATE INDEX IF NOT EXISTS idx_hab_cat ON habilidades_anuar(categoria);
        CREATE INDEX IF NOT EXISTS idx_aop_cat ON areas_oportunidad(categoria);
    """)
    conn.commit()
    conn.close()


def _upsert_habilidad(categoria: str, habilidad: str, nivel: int, evidencia: str) -> None:
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        INSERT INTO habilidades_anuar (categoria, habilidad, nivel, evidencia, ultima_actualizacion)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(categoria, habilidad) DO UPDATE SET
            nivel = MAX(habilidades_anuar.nivel, excluded.nivel),
            veces_detectada = habilidades_anuar.veces_detectada + 1,
            evidencia = excluded.evidencia,
            ultima_actualizacion = excluded.ultima_actualizacion
    """, (categoria, habilidad, nivel, evidencia[:300], now))
    conn.commit()
    conn.close()


def _upsert_area_oportunidad(categoria: str, descripcion: str, accion: str) -> None:
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        INSERT INTO areas_oportunidad (categoria, descripcion, accion_sugerida, fecha)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(categoria, descripcion) DO UPDATE SET
            frecuencia = areas_oportunidad.frecuencia + 1,
            accion_sugerida = excluded.accion_sugerida,
            fecha = excluded.fecha
    """, (categoria, descripcion[:300], accion[:300], now))
    conn.commit()
    conn.close()


def _get_perfil_completo() -> Dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row

    habilidades = [dict(r) for r in conn.execute(
        "SELECT * FROM habilidades_anuar ORDER BY nivel DESC, veces_detectada DESC"
    ).fetchall()]

    areas = [dict(r) for r in conn.execute(
        "SELECT * FROM areas_oportunidad WHERE resuelta=0 ORDER BY frecuencia DESC LIMIT 10"
    ).fetchall()]

    conn.close()
    return {"habilidades": habilidades, "areas_oportunidad": areas}


# ── Clase principal ───────────────────────────────────────────────

class PerfilHabilidades:
    """
    Perfil cognitivo de Anuar.
    Aprende sus habilidades de cada interacción y detecta dónde AURORA debe complementar.
    """

    _instancia: Optional["PerfilHabilidades"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self):
        if self._inicializado:
            return
        self._groq = AsyncGroq(api_key=GROQ_KEY) if GROQ_KEY else None

    async def inicializar(self) -> None:
        if self._inicializado:
            return
        await asyncio.to_thread(_init_tablas)
        self._inicializado = True
        logger.info("✅ PerfilHabilidades listo.")

    # ── ANÁLISIS DE INTERACCIÓN ───────────────────────────────────

    async def analizar_interaccion(
        self,
        mensaje_usuario: str,
        respuesta_aurora: str,
        motores_usados: List[str],
    ) -> Dict:
        """
        Analiza una interacción y extrae:
        1. Habilidades que demuestra Anuar
        2. Áreas donde necesitó ayuda (oportunidades de mejora)
        Llamado por la Consciencia después de cada interacción.
        """
        if not self._groq or len(mensaje_usuario) < 20:
            return {}

        prompt = f"""Analiza esta interacción entre Anuar y AURORA.

Mensaje de Anuar: "{mensaje_usuario[:400]}"
Respuesta de AURORA: "{respuesta_aurora[:300]}"
Motores usados: {motores_usados}

Extrae en JSON:
{{
  "habilidades_demostradas": [
    {{"categoria": "ventas|marketing|tecnico|operaciones|creatividad|finanzas|liderazgo|comunicacion",
      "habilidad": "descripcion concreta", "nivel": 1_a_5, "evidencia": "por qué"}}
  ],
  "areas_oportunidad": [
    {{"categoria": "...", "descripcion": "en qué necesitó ayuda", "accion_sugerida": "cómo AURORA puede ayudar más"}}
  ]
}}
Máximo 2 habilidades y 2 áreas. Solo lo realmente observable en el mensaje. Si no hay evidencia clara, devuelve listas vacías."""

        try:
            r = await self._groq.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400, temperature=0.2,
            )
            raw = r.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip().split("```")[0]
            datos = json.loads(raw)

            # Persistir habilidades
            for h in datos.get("habilidades_demostradas", []):
                await asyncio.to_thread(
                    _upsert_habilidad,
                    h.get("categoria", ""), h.get("habilidad", ""),
                    int(h.get("nivel", 3)), h.get("evidencia", "")
                )

            # Persistir áreas de oportunidad
            for a in datos.get("areas_oportunidad", []):
                await asyncio.to_thread(
                    _upsert_area_oportunidad,
                    a.get("categoria", ""), a.get("descripcion", ""),
                    a.get("accion_sugerida", "")
                )

            return datos

        except Exception as e:
            logger.debug(f"Análisis habilidades: {e}")
            return {}

    # ── PERFIL Y RECOMENDACIONES ──────────────────────────────────

    async def obtener_perfil(self) -> Dict:
        """Perfil completo: habilidades + áreas de oportunidad."""
        perfil = await asyncio.to_thread(_get_perfil_completo)
        return perfil

    async def resumen_para_contexto(self) -> str:
        """
        Resumen compacto del perfil para inyectar en el contexto de cada motor.
        Permite que AURORA personalice sus respuestas según las habilidades de Anuar.
        """
        perfil = await self.obtener_perfil()
        habs = perfil.get("habilidades", [])
        areas = perfil.get("areas_oportunidad", [])

        if not habs and not areas:
            return "Perfil de Anuar: en construcción (pocas interacciones registradas aún)."

        top_habs = [f"{h['habilidad']} ({NIVELES.get(h['nivel'], '?')})" for h in habs[:5]]
        top_areas = [a["descripcion"] for a in areas[:3]]

        resumen = f"Habilidades fuertes de Anuar: {', '.join(top_habs)}."
        if top_areas:
            resumen += f" Áreas donde AURORA complementa: {', '.join(top_areas)}."
        return resumen

    async def sugerencia_proactiva(self) -> Optional[str]:
        """
        Genera una sugerencia proactiva basada en áreas de oportunidad.
        AURORA dice: 'Oye, noto que en X área podrías mejorar, ¿quieres que te ayude?'
        """
        perfil = await self.obtener_perfil()
        areas = perfil.get("areas_oportunidad", [])
        if not areas or not self._groq:
            return None

        area_principal = areas[0]
        try:
            r = await self._groq.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": (
                    f"AURORA detectó que Anuar necesita ayuda frecuente en: '{area_principal['descripcion']}' (categoría: {area_principal['categoria']}).\n"
                    f"Frecuencia: {area_principal['frecuencia']} veces.\n"
                    f"Acción sugerida previa: {area_principal['accion_sugerida']}\n\n"
                    "Genera un mensaje proactivo corto (2 frases máximo) que AURORA le diría a Anuar para complementar esta área. "
                    "Tono directo, mexicano, sin rodeos."
                )}],
                max_tokens=120, temperature=0.7,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return None

    async def estado(self) -> Dict:
        perfil = await self.obtener_perfil()
        return {
            "sistema": "PerfilHabilidades",
            "habilidades_registradas": len(perfil.get("habilidades", [])),
            "areas_oportunidad_activas": len(perfil.get("areas_oportunidad", [])),
        }


# Instancia global
perfil_habilidades = PerfilHabilidades()
