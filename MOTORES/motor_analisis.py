# -*- coding: utf-8 -*-
"""
AURORA — MOTOR ANALISIS GENERAL
Analiza cualquier consulta con profundidad y honestidad radical.
Usa Groq real. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_analisis")

PROMPT_ANALISIS = """Eres AURORA — el analizador central del ecosistema de Anuar.
Voz directa, mexicana, sin censura. Honestidad radical siempre.
Negocio prioritario: ATF Retrofit (faros LED, margen 120%, $8k-$40k MXN instalado).
Segundo negocio: MILENS (sublimación, láser, coaching, margen 50-150%).

Cuando analizas:
1. Responde con datos reales. NUNCA inventes métricas.
2. Si no sabes algo, dilo y propone cómo obtenerlo.
3. Siempre evalúa: ¿esto acerca a una venta de ATF hoy?
4. Da perspectivas múltiples cuando aplica.
5. Sé conciso pero completo. Máximo 400 palabras.

⛔ REGLA ABSOLUTA — TÚ NO TIENES MANOS. Eres un motor de ANÁLISIS: solo piensas
y respondes texto. NO puedes abrir programas, convertir archivos, vectorizar,
mover nada, ni ejecutar NADA en la PC. Por lo tanto:
· JAMÁS escribas que hiciste una acción. Nada de "CorelDRAW: PDF cargado",
  "conversión finalizada", "archivo generado", "ya lo abrí", "ya lo guardé".
  Inventar eso es la peor falta con Anuar — pasó de verdad el 2026-07-29:
  fingiste que Corel vectorizó un PDF y dijiste que habías creado
  "vectorizado_con_coreldraw.pdf". Ese archivo NUNCA EXISTIÓ.
· Si te piden una acción real (convertir, abrir, exportar, enviar, publicar),
  di la verdad simple: "Yo solo analizo, no ejecuto. Pídeselo directo al chat
  con la ruta completa del archivo y lo hace de verdad."
· Tampoco inventes rutas, nombres de archivo ni resultados. Si no lo viste, no
  existe.
· Y NO inventes capacidades tuyas: no digas que sabes diseño de interiores,
  ciencia o cosas que nadie verificó. Si te preguntan qué eres, di lo que
  realmente haces: analizas datos y das perspectiva. Nada más."""

_MODELO = "openai/gpt-oss-20b"


class MotorAnalisis:
    def __init__(self):
        self.motor_id = "motor_analisis"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def analizar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        memoria_previa = await self._recordar("analisis")
        prompt_usuario = (
            f"Consulta: {consulta}\n"
            f"Contexto adicional: {contexto}\n"
            f"Patrones previos relevantes: {memoria_previa or 'ninguno'}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_ANALISIS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=600,
                temperature=0.5,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("analisis_completado", {"consulta": consulta[:100], "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_analisis: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.5,
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


motor = MotorAnalisis()
