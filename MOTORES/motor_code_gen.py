# -*- coding: utf-8 -*-
"""
AURORA — MOTOR GENERACION DE CODIGO
Genera código real, profesional y funcional en cualquier lenguaje.
Usa Groq real. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_code_gen")

PROMPT_CODE = """Eres AURORA — especialista en generación de código de producción.
Generas código real, funcional, limpio y bien estructurado. Sin placeholders. Sin TODOs sin resolver.
Lenguajes: Python, JavaScript, TypeScript, SQL, Bash, HTML/CSS.
Contexto del proyecto: sistema AURORA en Python/FastAPI, SQLite, Groq API, Green API WhatsApp.

Reglas absolutas:
1. El código que produces FUNCIONA. Sin pass vacíos. Sin ejemplos fake.
2. Incluyes manejo de errores apropiado.
3. Variables y funciones en español cuando el proyecto lo usa, inglés si el contexto lo requiere.
4. Respondes con el código directamente, sin relleno innecesario.
5. Si necesitas datos que no tienes (API key, path), los marcas con os.getenv() o variables claras."""

_MODELO = "llama-3.1-8b-instant"


class MotorCodeGen:
    def __init__(self):
        self.motor_id = "motor_code_gen"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def generar(self, requerimiento: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        lenguaje = contexto.get("lenguaje", "python")
        framework = contexto.get("framework", "")
        prompt_usuario = (
            f"Requerimiento: {requerimiento}\n"
            f"Lenguaje: {lenguaje}\n"
            f"Framework/contexto: {framework or 'ninguno específico'}\n"
            f"Contexto adicional: {contexto}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_CODE},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=2000,
                temperature=0.2,
            )
            codigo = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("codigo_generado", {"lenguaje": lenguaje, "requerimiento": requerimiento[:100]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "codigo": codigo,
                "lenguaje": lenguaje,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_code_gen: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.6,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCodeGen()
