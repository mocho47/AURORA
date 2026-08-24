# -*- coding: utf-8 -*-
"""
AURORA — MOTOR NEGOCIOS (ATF + MILENS)
Gestión operativa real de los negocios de Anuar.
Usa Groq + datos reales de CONFIG. Sin simulaciones.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_negocios")

PROMPT_NEGOCIOS = """Eres el gestor operativo de los negocios de Anuar: ATF Retrofit y MILENS.

ATF Retrofit — iluminación automotriz LED:
- Producto: kits Aozoom X1 ($8k), X3 ($15k), X5 ($25k), X7 ($40k) MXN instalado.
- Margen: 120% sobre costo.
- Canales: TikTok, Instagram, YouTube, WhatsApp directo.
- Prioridad #1: generar leads y cerrar instalaciones HOY.
- Respuesta a lead: < 5 minutos. Ningún lead se enfría.

MILENS — sublimación y láser:
- Productos: poleras ($850), tazas ($170), grabado láser ($180 por pieza).
- Margen: 50-150%.
- Clientes: empresas, eventos, regalos personalizados.
- Fortaleza: calidad + entrega rápida.

Tu rol: reportar estado real, proponer acciones, detectar oportunidades.
Regla fundamental: NUNCA inventes métricas. Si no tienes datos reales, dilo y propone cómo obtenerlos.
Siempre termina con "PRÓXIMA ACCIÓN RECOMENDADA:" + acción concreta."""

_MODELO = "openai/gpt-oss-20b"


class MotorNegocios:
    def __init__(self):
        self.motor_id = "motor_negocios"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def consultar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        negocio = contexto.get("negocio", "ambos")
        resumen_oracle = await self._resumen_oracle(negocio)
        prompt_usuario = (
            f"Consulta operativa: {consulta}\n"
            f"Negocio: {negocio}\n"
            f"Resumen actual desde ORACLE: {resumen_oracle}\n"
            f"Contexto adicional: {contexto}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_NEGOCIOS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=600,
                temperature=0.4,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("consulta_negocio", {"negocio": negocio, "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "negocio": negocio,
                "respuesta": respuesta,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_negocios: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _resumen_oracle(self, negocio: str) -> str:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
            import oracle_core as oracle
            oracle.init_db()
            r = oracle.resumen(negocio if negocio != "ambos" else None)
            return str(r)
        except Exception as e:
            return f"ORACLE no disponible: {e}"

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.7,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorNegocios()
