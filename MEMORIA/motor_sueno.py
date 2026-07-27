# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║              😴 AURORA — MOTOR DE SUEÑO Y APRENDIZAJE                ║
║        Consolidación episódica → semántica via Groq LLM real         ║
║            Aprende patrones durante períodos de inactividad          ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/MEMORIA/motor_sueno.py
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from groq import AsyncGroq

sys.path.insert(0, str(Path(__file__).parent.parent))
from MEMORIA.sistema_memoria import memoria
from CEREBRO.bus_neuronal import bus, Mensaje, TipoMensaje

logger = logging.getLogger("aurora.motor_sueno")

# ─────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────

UMBRAL_INACTIVIDAD_SEG: int = 300      # 5 min sin actividad → iniciar sueño
MIN_EPISODIOS_PARA_SUENO: int = 5      # mínimo de episodios para consolidar
MAX_EPISODIOS_POR_CICLO: int = 40      # máximo que procesa en un ciclo
MODELO_LLM: str = "llama-3.1-8b-instant"
INTERVALO_VIGILANCIA_SEG: int = 60     # revisa inactividad cada 60 segundos

PROMPT_CONSOLIDACION = """Eres el sistema de consolidación de memoria de AURORA.
Se te entrega una lista de eventos/interacciones recientes del sistema.

Tu tarea es extraer PATRONES REALES y CONOCIMIENTO ÚTIL de estos episodios.
Devuelve EXCLUSIVAMENTE un JSON válido con este formato:

{
  "conocimientos": [
    {
      "tema": "categoria_corta",
      "patron": "descripcion_del_patron_aprendido",
      "conocimiento": "texto_explicativo_del_conocimiento_concreto",
      "confianza": 0.0_a_1.0
    }
  ],
  "resumen_ciclo": "resumen_breve_del_ciclo_de_sueno"
}

Reglas:
- Solo patrones REALES observados en los episodios, nunca inventados
- "tema" debe ser una de: ventas, coaching, marketing, usuario, sistema, negocio, producto
- "confianza" alta (>0.8) solo si el patrón aparece repetidamente
- Mínimo 1 conocimiento, máximo 10
- Si no hay patrones claros, devuelve 1 conocimiento con confianza 0.3"""


# ─────────────────────────────────────────────────────────────────────
# MOTOR DE SUEÑO
# ─────────────────────────────────────────────────────────────────────

class MotorSueno:
    """
    Motor de sueño y aprendizaje de AURORA.

    Monitorea la actividad del sistema.
    Cuando detecta inactividad suficiente, inicia una fase de sueño:
      1. Lee episodios no consolidados de la memoria episódica
      2. Envía a Groq LLM para extraer patrones y conocimientos
      3. Escribe los conocimientos en memoria semántica
      4. Marca los episodios como consolidados
      5. Notifica al bus neuronal sobre el nuevo aprendizaje
    """

    def __init__(self) -> None:
        self._api_key: str = os.getenv("GROQ_API_KEY", "")
        self._cliente: Optional[AsyncGroq] = (
            AsyncGroq(api_key=self._api_key) if self._api_key else None
        )
        self._ultimo_evento: datetime = datetime.utcnow()
        self._ciclos_completados: int = 0
        self._total_conocimientos: int = 0
        self._en_sueno: bool = False
        self._tarea_vigilancia: Optional[asyncio.Task] = None
        logger.info(
            f"😴 MotorSueno listo. LLM: {'✅' if self._cliente else '❌ sin GROQ_API_KEY'}"
        )

    # ── CICLO DE VIDA ─────────────────────────────────────────────

    async def iniciar(self) -> None:
        """Arranca el bucle de vigilancia en background."""
        await memoria.inicializar()
        if self._tarea_vigilancia is None or self._tarea_vigilancia.done():
            self._tarea_vigilancia = asyncio.create_task(
                self._bucle_vigilancia(), name="motor_sueno_vigilancia"
            )
            logger.info("▶️  MotorSueno activo — vigilancia iniciada.")

    async def detener(self) -> None:
        if self._tarea_vigilancia and not self._tarea_vigilancia.done():
            self._tarea_vigilancia.cancel()
            logger.info("⏹️  MotorSueno detenido.")

    def registrar_actividad(self) -> None:
        """Llamar cada vez que haya actividad en el sistema para resetear el temporizador."""
        self._ultimo_evento = datetime.utcnow()

    # ── VIGILANCIA ────────────────────────────────────────────────

    async def _bucle_vigilancia(self) -> None:
        """Revisa periódicamente si el sistema ha estado inactivo lo suficiente."""
        logger.info("🔍 Bucle de vigilancia de sueño activo.")
        while True:
            try:
                await asyncio.sleep(INTERVALO_VIGILANCIA_SEG)

                if self._en_sueno:
                    continue

                segundos_inactivo = (
                    datetime.utcnow() - self._ultimo_evento
                ).total_seconds()

                stats = await memoria.estadisticas()
                episodios_pendientes = stats.get("episodios_pendientes_sueno", 0)

                logger.debug(
                    f"💤 Inactividad: {segundos_inactivo:.0f}s | "
                    f"Episodios pendientes: {episodios_pendientes}"
                )

                if (
                    segundos_inactivo >= UMBRAL_INACTIVIDAD_SEG
                    and episodios_pendientes >= MIN_EPISODIOS_PARA_SUENO
                ):
                    logger.info(
                        f"😴 Iniciando fase de sueño. "
                        f"Inactividad: {segundos_inactivo:.0f}s, "
                        f"Episodios: {episodios_pendientes}"
                    )
                    await self._fase_sueno()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error en vigilancia de sueño: {exc}", exc_info=True)

    # ── FASE DE SUEÑO ─────────────────────────────────────────────

    async def _fase_sueno(self) -> None:
        """Ciclo completo de consolidación de memoria."""
        self._en_sueno = True
        inicio = datetime.utcnow()

        try:
            # 1. Leer episodios no consolidados
            episodios = await memoria.episodios_recientes(
                limite=MAX_EPISODIOS_POR_CICLO,
                solo_no_consolidados=True,
            )

            if not episodios:
                logger.info("💤 Sin episodios pendientes. Sueño cancelado.")
                return

            logger.info(f"🧠 Procesando {len(episodios)} episodios para consolidar...")

            # 2. Consolidar via LLM
            conocimientos = await self._consolidar(episodios)

            if not conocimientos:
                logger.warning("😶 LLM no devolvió conocimientos. Episodios marcados igual.")
            else:
                # 3. Escribir en memoria semántica
                for k in conocimientos:
                    await memoria.aprender(
                        tema=k.get("tema", "general"),
                        patron=k.get("patron", "desconocido"),
                        conocimiento=k.get("conocimiento", ""),
                        confianza=float(k.get("confianza", 0.5)),
                    )
                self._total_conocimientos += len(conocimientos)
                logger.info(
                    f"💡 {len(conocimientos)} conocimientos escritos en memoria semántica."
                )

            # 4. Marcar episodios como consolidados
            ids = [e["id"] for e in episodios]
            await memoria.marcar_consolidados(ids)

            # 4.5. Purgar episodios YA consolidados con más de 90 días — episodica no
            # tenía ningún límite de crecimiento y guarda TODO el trafico del bus, no
            # solo chat. Su resumen ya vive en semantica, así que no se pierde nada real.
            try:
                borrados = await memoria.purgar_episodios_viejos(90)
                if borrados:
                    logger.info(f"🧹 {borrados} episodios viejos (90+ días, ya consolidados) purgados.")
            except Exception as e:
                logger.debug(f"Purga de episodios no aplicó: {e}")

            # 5. Consolidar analítica de marketing (en paralelo)
            try:
                from MEMORIA.analitica_marketing import analitica_marketing
                await analitica_marketing.inicializar()
                res_mkt = await analitica_marketing.consolidar_en_semantica()
                if conocimientos is None:
                    conocimientos = []
                logger.info(f"📊 Marketing consolidado: {res_mkt.get('conocimientos_escritos', 0)} patrones")
            except Exception as _mkt_err:
                logger.debug(f"Marketing consolidación: {_mkt_err}")

            # 6. Notificar al bus neuronal
            duracion = (datetime.utcnow() - inicio).total_seconds()
            self._ciclos_completados += 1

            await bus.publicar(Mensaje(
                tipo=TipoMensaje.APRENDIZAJE,
                origen="motor_sueno",
                destino="broadcast",
                contenido={
                    "ciclo": self._ciclos_completados,
                    "episodios_procesados": len(episodios),
                    "conocimientos_nuevos": len(conocimientos) if conocimientos else 0,
                    "duracion_seg": round(duracion, 2),
                    "timestamp": inicio.isoformat(),
                },
                importancia=0.8,
            ))

            logger.info(
                f"✅ Ciclo de sueño #{self._ciclos_completados} completo. "
                f"Duración: {duracion:.1f}s"
            )

        except Exception as exc:
            logger.error(f"Error en fase de sueño: {exc}", exc_info=True)
        finally:
            self._en_sueno = False

    # ── CONSOLIDACIÓN VIA LLM ─────────────────────────────────────

    async def _consolidar(self, episodios: List[Dict]) -> List[Dict]:
        """Envía episodios al LLM y extrae conocimientos estructurados."""
        if not self._cliente:
            logger.error("❌ Sin cliente Groq — no se puede consolidar.")
            return []

        # Serializar episodios de forma legible para el LLM
        texto_episodios = json.dumps(
            [
                {
                    "ts": e["timestamp"],
                    "motor": e["motor_origen"],
                    "tipo": e["tipo_evento"],
                    "contenido": json.loads(e["contenido"])
                    if isinstance(e["contenido"], str)
                    else e["contenido"],
                }
                for e in episodios
            ],
            ensure_ascii=False,
            indent=2,
        )

        try:
            respuesta = await self._cliente.chat.completions.create(
                model=MODELO_LLM,
                messages=[
                    {"role": "system", "content": PROMPT_CONSOLIDACION},
                    {
                        "role": "user",
                        "content": f"Episodios a consolidar:\n{texto_episodios}",
                    },
                ],
                temperature=0.3,   # baja temperatura para extracción precisa
                max_tokens=1500,
            )

            raw = respuesta.choices[0].message.content.strip()

            # Parsear JSON de la respuesta
            # Groq puede envolver el JSON en markdown
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            datos = json.loads(raw)
            conocimientos = datos.get("conocimientos", [])
            resumen = datos.get("resumen_ciclo", "")

            if resumen:
                logger.info(f"📋 Resumen ciclo sueño: {resumen}")

            return conocimientos

        except json.JSONDecodeError as exc:
            logger.error(f"LLM devolvió JSON inválido: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Error al llamar a Groq en fase sueño: {exc}", exc_info=True)
            return []

    # ── DIAGNÓSTICO ───────────────────────────────────────────────

    def estado(self) -> Dict:
        segundos_inactivo = (
            datetime.utcnow() - self._ultimo_evento
        ).total_seconds()
        return {
            "sistema": "MotorSueno",
            "en_sueno_ahora": self._en_sueno,
            "ciclos_completados": self._ciclos_completados,
            "total_conocimientos_generados": self._total_conocimientos,
            "segundos_sin_actividad": round(segundos_inactivo, 0),
            "umbral_sueno_seg": UMBRAL_INACTIVIDAD_SEG,
            "llm_activo": self._cliente is not None,
            "vigilancia_activa": (
                self._tarea_vigilancia is not None
                and not self._tarea_vigilancia.done()
            ),
        }


# Instancia global
motor_sueno = MotorSueno()
