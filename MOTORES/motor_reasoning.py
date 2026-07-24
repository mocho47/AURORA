# -*- coding: utf-8 -*-
"""
AURORA — MOTOR RAZONAMIENTO PROFUNDO
Analiza decisiones complejas desde múltiples ángulos. Estrategia real.
Usa Groq. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_reasoning")

PROMPT_REASONING = """Eres AURORA — el motor de razonamiento estratégico de Anuar.
Piensas profundamente, sin censura, sin sesgos de confirmación.
Tu metodología: 6 dimensiones obligatorias por decisión compleja.

1. TÉCNICO: ¿Es factible? ¿Qué recursos requiere? ¿Tiempo realista?
2. FINANCIERO: ¿Cuánto cuesta? ¿Cuánto genera? ¿ROI real?
3. OPERACIONAL: ¿Afecta procesos actuales? ¿Carga de trabajo?
4. RELACIONAL: ¿Impacto en clientes, equipo, socios?
5. RIESGO: ¿Qué puede fallar? ¿Plan B?
6. DECISIÓN: Recomendación concreta con nivel de confianza 0.0-1.0.

Si confianza >= 0.75 → ACTÚA (recomienda acción inmediata).
Si confianza < 0.75 → da 2 opciones y pide confirmación.
NUNCA das respuestas vagas. Siempre terminas con acción concreta."""

_MODELO = "llama-3.1-8b-instant"


class MotorReasoning:
    def __init__(self):
        self.motor_id = "motor_reasoning"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def razonar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        memoria_previa = await self._recordar("razonamiento")
        prompt_usuario = (
            f"Problema/Decisión: {consulta}\n"
            f"Restricciones conocidas: {contexto}\n"
            f"Decisiones similares pasadas: {memoria_previa or 'ninguna registrada'}\n\n"
            f"Analiza con las 6 dimensiones y dame una decisión concreta con nivel de confianza."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_REASONING},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=900,
                temperature=0.4,
            )
            analisis = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("razonamiento_completado", {"consulta": consulta[:100], "preview": analisis[:200]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "analisis": analisis,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_reasoning: {e}")
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


motor = MotorReasoning()
