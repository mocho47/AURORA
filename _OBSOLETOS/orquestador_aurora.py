#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║         🧠 ORQUESTADOR INTELIGENTE AURORA - CEREBRO v5 🧠                 ║
║                                                                             ║
║     Toma de decisiones centralizada y consciente del estado del sistema.    ║
║                   Fase 1: Despertar al "Cerebro"                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

# Añadir el path raíz del proyecto para poder importar módulos de otras carpetas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SUPER_MARKETING_SYSTEM.sistema_marketing_maestro import SistemaMarketingMaestro, ConfiguracionATF

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [🧠 CEREBRO] %(message)s'
)
logger = logging.getLogger("ORQUESTADOR_AURORA")


class ContextEngine:
    """
    El Motor de Conciencia de Aurora.
    Recopila y centraliza el estado de todo el ecosistema.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.estado_actual = {}
        logger.info("👁️ Motor de Conciencia (ContextEngine) inicializado.")

    async def actualizar_estado_completo(self):
        """
        Recopila métricas clave de la base de datos y otros sistemas
        para tener una visión 360° en tiempo real.
        """
        logger.info("Actualizando estado completo del sistema...")
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Ejemplo: Obtener métricas de publicaciones recientes
            c.execute("SELECT COUNT(*), AVG(engagement_rate) FROM publicaciones WHERE fecha_publicacion >= date('now', '-1 day')")
            publicaciones_24h, engagement_avg_24h = c.fetchone()

            # Ejemplo: Obtener estado de leads
            c.execute("SELECT estado_lead, COUNT(*) FROM leads_conversiones GROUP BY estado_lead")
            estado_leads = dict(c.fetchall())

            conn.close()

            self.estado_actual = {
                "timestamp": datetime.now(),
                "publicaciones_ultimas_24h": publicaciones_24h or 0,
                "engagement_promedio_24h": engagement_avg_24h or 0.0,
                "distribucion_leads": estado_leads,
                "salud_sistema": "🟢 OPERATIVO"
            }
            logger.info(f"Estado actualizado: {self.estado_actual}")

        except Exception as e:
            logger.error(f"Error al actualizar el estado del sistema: {e}", exc_info=True)
            self.estado_actual["salud_sistema"] = "🔴 ERROR"


class OrquestadorAurora:
    """
    El Cerebro central. Utiliza el ContextEngine para tomar decisiones
    y coordina los diferentes motores del sistema.
    """
    def __init__(self):
        self.config = ConfiguracionATF()
        self.context_engine = ContextEngine(self.config.db_path)
        self.sistema_marketing = SistemaMarketingMaestro(self.config)
        self.sesion_activa = True
        logger.info("🚀 Orquestador Aurora (Cerebro v5) inicializado y listo.")

    async def tomar_proxima_accion_inteligente(self) -> str:
        """
        El corazón de la toma de decisiones.
        Analiza el contexto y decide la acción más estratégica.
        """
        await self.context_engine.actualizar_estado_completo()
        contexto = self.context_engine.estado_actual

        # --- LÓGICA DE DECISIÓN (Fase 1 Inicial) ---
        # Por ahora, la lógica es simple, pero aquí es donde crecerá la inteligencia.

        if contexto.get("salud_sistema") == "🔴 ERROR":
            logger.error("El sistema está en estado de error. No se ejecutarán ciclos.")
            return "CICLO_REPARACION" # Futura acción

        if contexto.get("engagement_promedio_24h", 0.0) < self.config.meta_engagement_rate / 2:
            logger.warning("Engagement bajo detectado. Priorizando ciclo de contenido viral.")
            return "CICLO_CONTENIDO_VIRAL"

        logger.info("El sistema está estable. Ejecutando ciclo de marketing estándar.")
        return "CICLO_COMPLETO_DIARIO"

    async def ejecutar_bucle_principal(self):
        """
        El bucle de vida de Aurora. Se ejecuta continuamente, tomando
        decisiones y orquestando acciones.
        """
        ciclo = 0
        while self.sesion_activa:
            ciclo += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"🧠 CICLO DE ORQUESTACIÓN #{ciclo} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*80}\n")

            accion_decision = await self.tomar_proxima_accion_inteligente()

            try:
                if accion_decision == "CICLO_COMPLETO_DIARIO":
                    await self.sistema_marketing.ejecutar_ciclo_completo_diario()
                elif accion_decision == "CICLO_CONTENIDO_VIRAL":
                    # En el futuro, podríamos tener ciclos especializados
                    logger.info("Ejecutando un ciclo especializado en contenido viral...")
                    await self.sistema_marketing.ejecutar_ciclo_completo_diario() # Por ahora, usa el mismo
                else:
                    logger.error(f"Decisión desconocida: {accion_decision}. Pausando.")
                    await asyncio.sleep(60)
                    continue

                # Esperar para el próximo ciclo de decisión
                espera_horas = 6
                logger.info(f"Ciclo de acción finalizado. Esperando {espera_horas} horas para la siguiente decisión.")
                await asyncio.sleep(espera_horas * 3600)

            except KeyboardInterrupt:
                logger.info("🛑 Orquestador detenido por el usuario.")
                self.sesion_activa = False
            except Exception as e:
                logger.critical(f"❌ Error crítico en el bucle principal del orquestador: {e}", exc_info=True)
                self.sesion_activa = False


async def main():
    """Punto de entrada para iniciar el Cerebro de Aurora."""
    orquestador = OrquestadorAurora()
    await orquestador.ejecutar_bucle_principal()


if __name__ == "__main__":
    asyncio.run(main())
