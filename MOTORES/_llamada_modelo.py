# -*- coding: utf-8 -*-
"""
AURORA · LA LLAMADA AL MODELO, EN UN SOLO LUGAR (para los motores)
=============================================================================
EL BUG QUE ARREGLA ESTE ARCHIVO — encontrado corriéndolos de verdad el 2026-08-26
---------------------------------------------------------------------------
Los 10 motores de MOTORES/ usan `openai/gpt-oss-20b`, que es un modelo de
RAZONAMIENTO: antes de contestar escribe su pensamiento en un canal aparte
(`reasoning`) y ese pensamiento GASTA del mismo `max_tokens`. Cuando el
pensamiento se alarga, el presupuesto se acaba antes de escribir la respuesta y
Groq devuelve `finish_reason="length"` con **`content` vacío**.

Los motores no miraban eso. Hacían `r.choices[0].message.content.strip()` y
devolvían **`status: "OK"` con la respuesta en blanco**. Medido en vivo:

  · `motor_cotizador` — cotización de 50 tazas para MILENS: status OK, campo
    `cotizacion` VACÍO. El pensamiento se comió los 700 tokens (1,545 caracteres
    de razonamiento, 0 de respuesta).
  · `motor_marketing.estrategia_semanal` — una corrida devolvió el plan vacío y
    la siguiente 951 caracteres. Intermitente, que es lo peor: parece que
    funciona hasta que un cliente está enfrente.

Es el peor tipo de fallo para Anuar: no truena, no avisa, y el chat le enseña
una respuesta en blanco como si todo hubiera salido bien.

LOS DOS ARREGLOS
---------------------------------------------------------------------------
1. `reasoning_effort="low"`. Comprobado contra Groq: con el mismo `max_tokens`
   de 700 el razonamiento baja de ~1,545 a ~96 caracteres y `finish_reason`
   pasa de `length` a `stop`. La respuesta cabe.
2. Si aun así vuelve vacía, se REINTENTA una vez con el doble de presupuesto, y
   si sigue vacía se LEVANTA el error. Nunca se devuelve un OK en blanco.

Y DE PASO: LOS MOTORES YA NO SE QUEDAN MUDOS
---------------------------------------------------------------------------
Se reusa `CEREBRO/respaldo_local.py` (`ClienteConRespaldo`), que ya existía y ya
tiene el escalón Groq → Gemini → modelo local. El chat lo usaba desde el
2026-08-19; los motores no, así que si Groq se quedaba sin cuota los motores se
morían aunque Gemini estuviera disponible. No se escribió un gemelo de esa
lógica: se usa la que ya está.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

logger = logging.getLogger("aurora.llamada_modelo")

# El modelo que ya usaban los 10 motores. No se cambia: solo se le pide que
# piense menos en voz alta.
MODELO = "openai/gpt-oss-20b"


def cliente():
    """El cliente con el que hablan los motores. `None` si no hay GROQ_API_KEY.

    Devuelve el envoltorio con respaldo (Groq → Gemini → local) en vez del
    cliente pelón de Groq, para que un bajón del proveedor no deje mudo al motor.
    """
    llave = os.getenv("GROQ_API_KEY", "")
    if not llave:
        return None
    from groq import AsyncGroq
    groq = AsyncGroq(api_key=llave)
    try:
        from CEREBRO.respaldo_local import ClienteConRespaldo
        return ClienteConRespaldo(groq)
    except Exception as e:
        # Si el respaldo no carga, mejor Groq solo que ningún motor.
        logger.warning(f"Sin respaldo (Gemini/local): {str(e)[:120]}. Sigo con Groq.")
        return groq


async def responder(cli, sistema: str, usuario: str, max_tokens: int = 600,
                    temperature: float = 0.5, modelo: str = MODELO) -> str:
    """Le pregunta al modelo y devuelve TEXTO NO VACÍO, o levanta el error.

    Que levante en vez de devolver "" es a propósito: cada motor ya tiene su
    `except` que responde `{"status": "ERROR", "detalle": ...}`. Así un fallo
    del modelo llega al chat como un fallo, y no como una respuesta en blanco
    con sello de OK.
    """
    if cli is None:
        raise RuntimeError("Sin GROQ_API_KEY")
    mensajes = [{"role": "system", "content": sistema},
                {"role": "user", "content": usuario}]

    intentos = ((max_tokens, "low"), (max_tokens * 2, "low"))
    ultimo_motivo = ""
    for presupuesto, esfuerzo in intentos:
        try:
            r = await cli.chat.completions.create(
                model=modelo, messages=mensajes, max_tokens=presupuesto,
                temperature=temperature, reasoning_effort=esfuerzo)
        except TypeError:
            # Un respaldo (Gemini/local) que no acepte `reasoning_effort`.
            r = await cli.chat.completions.create(
                model=modelo, messages=mensajes, max_tokens=presupuesto,
                temperature=temperature)
        opcion = r.choices[0]
        texto = (opcion.message.content or "").strip()
        if texto:
            return texto
        ultimo_motivo = getattr(opcion, "finish_reason", "?")
        logger.warning(
            f"El modelo devolvió vacío (finish_reason={ultimo_motivo}) con "
            f"{presupuesto} tokens. Reintento con más presupuesto.")

    raise RuntimeError(
        f"El modelo se quedó sin espacio para contestar (finish_reason="
        f"{ultimo_motivo}) y devolvió una respuesta vacía las dos veces. "
        f"No te entrego una respuesta en blanco como si fuera buena.")
