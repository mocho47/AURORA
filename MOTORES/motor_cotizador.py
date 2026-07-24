# -*- coding: utf-8 -*-
"""
AURORA — MOTOR COTIZADOR INTELIGENTE
Genera cotizaciones reales con 3 opciones para ATF y MILENS.
Precios reales del catálogo. Usa Groq. Sin simulaciones.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_cotizador")

# Precios reales del catálogo ATF Retrofit
CATALOGO_ATF = {
    "aozoom_x1": {"nombre": "Aozoom X1 Básico", "costo": 3500, "precio_publico": 8000, "instalacion": 800},
    "aozoom_x3": {"nombre": "Aozoom X3 Standard", "costo": 6200, "precio_publico": 14999, "instalacion": 1200},
    "aozoom_x5": {"nombre": "Aozoom X5 Premium", "costo": 10500, "precio_publico": 24999, "instalacion": 1500},
    "aozoom_x7": {"nombre": "Aozoom X7 Elite", "costo": 16500, "precio_publico": 39999, "instalacion": 2000},
}

# Precios reales catálogo MILENS
CATALOGO_MILENS = {
    "polera": {"nombre": "Polera sublimada", "costo": 450, "precio_publico": 850, "mayorista": 650},
    "taza": {"nombre": "Taza sublimada 11oz", "costo": 85, "precio_publico": 170, "mayorista": 130},
    "taza_magica": {"nombre": "Taza mágica", "costo": 120, "precio_publico": 280, "mayorista": 200},
    "bolsa": {"nombre": "Bolsa sublimada", "costo": 180, "precio_publico": 380, "mayorista": 280},
    "caja": {"nombre": "Caja personalizada", "costo": 95, "precio_publico": 220, "mayorista": 160},
    "laser_grabado": {"nombre": "Grabado láser pieza", "costo": 60, "precio_publico": 180, "mayorista": 130},
}

PROMPT_COTIZADOR = """Eres el cotizador profesional de ATF Retrofit y MILENS de Anuar.
Generas SIEMPRE exactamente 3 opciones de cotización: Estándar, Premium y Cierre.
Usas los precios reales del catálogo proporcionado.
ATF margen real: 120-130%. MILENS margen real: 50-150%.
Formato de respuesta: claro, directo, con desglose de precios y próximo paso de acción.
Nunca inventas precios. Si el producto no está en catálogo, dices que necesitas verificar."""

_MODELO = "llama-3.1-8b-instant"


class MotorCotizador:
    def __init__(self):
        self.motor_id = "motor_cotizador"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def cotizar(self, requerimiento: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        negocio = contexto.get("negocio", "atf").lower()
        catalogo = CATALOGO_ATF if negocio == "atf" else CATALOGO_MILENS
        folio = f"COT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        prompt_usuario = (
            f"Folio: {folio}\n"
            f"Negocio: {negocio.upper()}\n"
            f"Requerimiento del cliente: {requerimiento}\n"
            f"Catálogo disponible: {catalogo}\n"
            f"Contexto: {contexto}\n\n"
            f"Genera exactamente 3 opciones de cotización (Estándar / Premium / Cierre agresivo). "
            f"Incluye desglose, total y próximo paso accionable."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_COTIZADOR},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=700,
                temperature=0.3,
            )
            cotizacion = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("cotizacion_generada", {
                "folio": folio, "negocio": negocio,
                "requerimiento": requerimiento[:100], "preview": cotizacion[:200]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "folio": folio,
                "negocio": negocio,
                "cotizacion": cotizacion,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_cotizador: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.8,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCotizador()
