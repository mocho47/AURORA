# -*- coding: utf-8 -*-
"""
AURORA — MOTOR VENTAS Y CRM
Gestión de leads, seguimiento, cierre de ventas ATF y MILENS.
Usa Groq + ORACLE SQLite. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_ventas")

PROMPT_VENTAS = """Eres el especialista en ventas de ATF Retrofit y MILENS de Anuar.
Técnicas reales: SPIN Selling, AIDA, Cierre por opción, Manejo de objeciones Cialdini.
Producto prioritario: ATF Retrofit LED (faros). Margen 120%. Precio: $8k-$40k MXN instalado.
Buyer persona ATF: hombre 20-40 años, le gusta su carro, quiere diferenciarse, medio-alto.

Metodología de venta:
1. SPIN primero: Situación → Problema → Implicación → Necesidad.
2. NUNCA presiones con escasez falsa. Solo escasez real (fechas reales, cupos reales).
3. Manejo de objeciones: Validar → Preguntar → Reencuadrar con valor.
4. Cierre: siempre con opción, nunca sí/no. "¿Lo agendo sábado o entre semana?"
5. Seguimiento: registrar en ORACLE. Ningún lead se enfría.
6. Velocidad: respuesta < 2 minutos en WhatsApp = ventaja competitiva enorme."""

_MODELO = "openai/gpt-oss-20b"


class MotorVentas:
    def __init__(self):
        self.motor_id = "motor_ventas"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def procesar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        cliente = contexto.get("cliente", "prospecto nuevo")
        etapa = contexto.get("etapa", "primer contacto")
        negocio = contexto.get("negocio", "ATF")
        historial_cliente = await self._obtener_historial(contexto.get("cliente_id"))
        prompt_usuario = (
            f"Cliente: {cliente} | Etapa: {etapa} | Negocio: {negocio}\n"
            f"Situación/mensaje: {consulta}\n"
            f"Historial del cliente en ORACLE: {historial_cliente}\n"
            f"Contexto adicional: {contexto}\n\n"
            f"Dame la respuesta/acción de venta apropiada para esta etapa."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_VENTAS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=500,
                temperature=0.5,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("interaccion_venta", {
                "cliente": cliente, "etapa": etapa, "negocio": negocio, "preview": respuesta[:150]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "cliente": cliente,
                "etapa": etapa,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_ventas: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _obtener_historial(self, cliente_id: int = None) -> str:
        if not cliente_id:
            return "cliente nuevo, sin historial previo"
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
            import oracle_core as oracle
            oracle.init_db()
            lead = oracle.obtener_lead(cliente_id)
            if not lead:
                return "lead no encontrado en ORACLE"
            return f"Lead #{cliente_id}: {lead['nombre']} | Estado: {lead['estado']} | Notas: {lead['notas'] or 'ninguna'}"
        except Exception as e:
            return f"ORACLE no disponible: {e}"

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


motor = MotorVentas()
