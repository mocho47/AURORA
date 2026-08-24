# -*- coding: utf-8 -*-
"""
AURORA — MOTOR COACHING REAL (transformacional)
Coach de negocios y desarrollo personal con Groq real.
Metodologías: SPIN, CNV, Dweck, Frankl. Sin simulaciones.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_coaching_real")

PROMPT_COACHING_REAL = """Eres AURORA en modo COACH TRANSFORMACIONAL de Anuar.
Tu propósito: desafiar creencias limitantes, abrir posibilidades reales, guiar a acción concreta.
Metodologías reales que usas: CNV (Comunicación No Violenta), Growth Mindset (Dweck),
Logoterapia (Frankl), Preguntas Socráticas, Design Thinking aplicado a negocios.

Contexto del ecosistema:
- ATF Retrofit: meta = liderar mercado iluminación automotriz en Guadalajara.
- MILENS: meta = ser el proveedor #1 de sublimación y láser para empresas locales.

Reglas del coaching:
1. Preguntas poderosas primero. NO das la respuesta de inmediato.
2. Validas la realidad del coachee antes de desafiarla.
3. Señalas la creencia limitante con honestidad radical, sin crueldad.
4. Propones UNA acción concreta al terminar, no una lista de 10.
5. Máximo 300 palabras. Directo al punto. Sin frases motivacionales vacías."""

_MODELO = "openai/gpt-oss-20b"


class MotorCoachingReal:
    def __init__(self):
        self.motor_id = "motor_coaching_real"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def sesion_coaching(self, tema: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        memoria_previa = await self._recordar("coaching")
        prompt_usuario = (
            f"Tema de la sesión: {tema}\n"
            f"Contexto del coachee: {contexto}\n"
            f"Sesiones previas registradas: {memoria_previa or 'primera sesión'}\n\n"
            f"Conduce la sesión de coaching. Empieza con una pregunta poderosa si hay ambigüedad."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_COACHING_REAL},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=450,
                temperature=0.7,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("sesion_coaching_real", {
                "tema": tema[:80], "preview": respuesta[:150]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "tema": tema,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_coaching_real: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def ejecutar(self, data: dict = None) -> Dict:
        data = data or {}
        tema = data.get("mensaje", data.get("tema", "desarrollo personal"))
        return await self.sesion_coaching(tema, data.get("contexto", {}))

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.7,
            )
        except Exception:
            pass

    async def _recordar(self, tema: str) -> str:
        try:
            from MEMORIA.sistema_memoria import memoria
            conocimientos = await memoria.recordar(tema=tema, limite=3)
            if not conocimientos:
                return ""
            return " | ".join([f"{k['patron']}: {k['conocimiento'][:80]}" for k in conocimientos])
        except Exception:
            return ""

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCoachingReal()
