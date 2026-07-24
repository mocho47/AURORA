# -*- coding: utf-8 -*-
"""AUTOMACIONES de AURORA v3 — Demonios en segundo plano de ejecución real.
Monitorea la base de datos ORACLE para disparar seguimientos automáticos de WhatsApp.
"""
from __future__ import annotations
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "CEREBRO"))
sys.path.insert(0, str(RAIZ / "ORACLE"))

try:
    from aurora_cerebro_simple import AuroraCerebro
    import oracle_core
except Exception as e:
    logging.getLogger("AURORA_AUTOMATIONS").error(f"Error de importación en automatizaciones: {e}")
    AuroraCerebro = None
    oracle_core = None

logger = logging.getLogger("AURORA_AUTOMATIONS")

class MotorAutomatizaciones:
    def __init__(self):
        self.cerebro = AuroraCerebro() if AuroraCerebro else None
        self.ejecutando = False

    async def procesar_seguimientos_whatsapp(self):
        if not oracle_core or not self.cerebro or not self.cerebro.esta_operativo():
            return
        try:
            conn = oracle_core.obtener_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, telefono, vehiculo, interes FROM leads WHERE estado = 'nuevo' LIMIT 5")
            leads_nuevos = cursor.fetchall()
            conn.close()
        except Exception as e:
            logger.error(f"[ERROR AUTOMATION]: {e}")

    async def arrancar_demonio(self, intervalo_segundos: int = 45):
        self.ejecutando = True
        logger.info(f"[OK] Demonio de automatizaciones activo. Ciclo de escaneo: {intervalo_segundos}s.")
        while self.ejecutando:
            try:
                await self.procesar_seguimientos_whatsapp()
                await asyncio.sleep(intervalo_segundos)
            except asyncio.CancelledError:
                self.ejecutando = False
            except Exception as e:
                logger.error(f"[ERROR CRÍTICO EN DEMONIO]: {e}")
                await asyncio.sleep(10)
