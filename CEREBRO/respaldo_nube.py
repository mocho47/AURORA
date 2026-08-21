# -*- coding: utf-8 -*-
"""AURORA · SEGUNDO PROVEEDOR DE NUBE (GEMINI)

POR QUÉ EXISTE
--------------
El 2026-08-19 Anuar le pidió a AURORA un plan de estudio y esperó **780
segundos** para leer esto:

    El proveedor de IA no tiene cuota ahora y el modelo local de esta PC no
    alcanzó a responder (le falta memoria).

Las dos mitades eran ciertas y las dos estaban medidas:

  · Groq se quedó sin cuota del plan gratis.
  · La PC tiene **7.2 GB de RAM soldada** y quedaban **0.6 GB libres**.
    `llama3.2:3b` pesa 2 GB. No cabía. No es que fuera lento: no cabía.

Y en el `.env` llevaba tiempo una **`GEMINI_API_KEY` que nadie usaba**. Estaba
en los documentos del proyecto y en `SETUP/probar_credenciales.py`, pero el
cerebro de AURORA no la conocía.

Gemini Flash regala 1,500 peticiones al día. Con eso, el día que Groq se
acaba, AURORA sigue trabajando en vez de disculparse.

CÓMO SE CONECTA
---------------
No se toca `consciencia.py`. Ese archivo llama al cerebro en unos quince
lugares distintos y ya existe el envoltorio `ClienteConRespaldo` que los cubre
todos. Aquí solo se agrega un escalón a esa escalera, en su punto único:

    Groq  →  **Gemini**  →  modelo local  →  la verdad

Mismo principio de siempre: un candado en el punto de salida, no quince
parches regados.

HONESTIDAD
----------
Cuando contesta Gemini, la respuesta **lo dice**. Es la misma regla que ya
cumple el respaldo local: nunca esconder de dónde salió una respuesta.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import List, Optional

logger = logging.getLogger("aurora.respaldo_nube")

BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Del mejor al más disponible. Se prueban en orden porque Google renombra y
# retira modelos sin avisar, y quedarse con uno solo es quedarse sin respaldo
# el día que lo apaguen.
#
# ESTA LISTA NO SE ADIVINÓ. El 2026-08-19 se le preguntó a la API cuáles
# acepta de verdad la llave de Anuar (`GET /v1beta/models`) y respondió con 37.
# El primer intento usaba `gemini-2.0-flash` y `gemini-1.5-flash`: los dos
# dieron **404, ya no existen**. Si algún día vuelve a fallar con 404, se
# corre esa misma consulta y se actualiza aquí — no se inventan nombres.
#
# `gemini-flash-latest` va en medio a propósito: es un alias que Google
# mantiene apuntando al modelo vigente, así que es el que más aguanta cuando
# los nombres con número se retiran.
# Tres, no cinco: cada modelo de más es un corte de espera más el día que la
# red anda mal, y en la prueba del 2026-08-19 esa cola tumbó la petición.
MODELOS = ("gemini-3.6-flash", "gemini-flash-latest", "gemini-3.1-flash-lite")

# Cuánto se espera a UN modelo antes de pasar al siguiente.
#
# Historia de este número, medida el 2026-08-19 y anotada para no repetirla:
# empezó en 30 s (la cadena llegó a tardar 42 s), se bajó a 14 s creyendo que
# eso la haría rápida, y **fue peor**: con cinco modelos en fila, cinco cortes
# seguidos suman más de un minuto y la petición se cayó completa. Recortar el
# tiempo de cada intento no sirve si se hacen muchos intentos.
#
# Lo que de verdad lo arregla es no volver a explorar: abajo se recuerda cuál
# modelo contestó y se prueba ése primero. Con eso, lo normal son 4 a 6 s y
# este número solo importa el día que el modelo de siempre se caiga.
SEGUNDOS_MAX = 22.0

# El que funcionó la última vez. Se prueba primero. AURORA vive días enteros en
# el mismo proceso, así que con recordarlo en memoria alcanza.
_ULTIMO_BUENO: Optional[str] = None

AVISO = "\n\n_(Groq no tenía cuota; esto lo contestó Gemini.)_"


def hay_llave() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _a_formato_gemini(messages: list) -> tuple:
    """Traduce los mensajes al formato de Google.

    Gemini no entiende el rol `assistant` (usa `model`) ni acepta el mensaje
    de sistema dentro de la conversación: va aparte, en `systemInstruction`.
    """
    sistema: List[str] = []
    turnos = []
    for m in messages or []:
        rol = (m.get("role") or "user").lower()
        txt = m.get("content") or ""
        if not isinstance(txt, str):
            txt = str(txt)
        if not txt.strip():
            continue
        if rol == "system":
            sistema.append(txt)
            continue
        turnos.append({"role": "model" if rol == "assistant" else "user",
                       "parts": [{"text": txt}]})
    # Gemini exige que la conversación empiece con el usuario.
    while turnos and turnos[0]["role"] == "model":
        turnos.pop(0)
    if not turnos:
        turnos = [{"role": "user", "parts": [{"text": "Hola"}]}]
    return turnos, "\n\n".join(sistema)


def _pedir(modelo: str, turnos: list, sistema: str, max_tokens: int,
           temperature: float, llave: str, timeout: float = SEGUNDOS_MAX,
           sin_pensar: bool = True) -> str:
    # Los Gemini 3.x «piensan» antes de contestar, y ese pensamiento **se cobra
    # del mismo presupuesto de salida**. Medido el 2026-08-19: con 300 tokens
    # la respuesta llegó cortada a media frase («Es enfocarte en el 2»).
    #
    # Dos arreglos, los dos necesarios:
    #   · `thinkingBudget: 0` — no queremos que razone, queremos que conteste.
    #   · un piso de 900 tokens — por si el modelo ignora lo anterior.
    gen = {"maxOutputTokens": max(int(max_tokens), 900),
           "temperature": float(temperature)}
    if sin_pensar:
        gen["thinkingConfig"] = {"thinkingBudget": 0}
    cuerpo = {"contents": turnos, "generationConfig": gen}
    if sistema:
        cuerpo["systemInstruction"] = {"parts": [{"text": sistema}]}
    req = urllib.request.Request(
        f"{BASE}/{modelo}:generateContent?key={llave}",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        datos = json.loads(r.read().decode("utf-8"))

    cands = datos.get("candidates") or []
    if not cands:
        # Gemini bloquea contenido a veces. Se dice cuál fue la razón en vez de
        # devolver vacío y dejar creer que el modelo no supo qué contestar.
        razon = (datos.get("promptFeedback") or {}).get("blockReason", "")
        raise RuntimeError(f"Gemini no devolvió respuesta"
                           + (f" (bloqueó el contenido: {razon})" if razon else ""))
    partes = (cands[0].get("content") or {}).get("parts") or []
    texto = "".join(p.get("text", "") for p in partes)
    if not texto.strip():
        fin = cands[0].get("finishReason", "")
        raise RuntimeError(f"Gemini devolvió vacío (motivo: {fin or 'desconocido'})")
    return texto


def responder(messages: list, max_tokens: int = 800,
              temperature: float = 0.7) -> Optional[str]:
    """Le pregunta a Gemini. Devuelve el texto, o None si no se pudo.

    Devuelve None en vez de reventar a propósito: quien llama tiene todavía el
    modelo local por probar, y un error aquí no debe cortar la cadena.
    """
    llave = os.getenv("GEMINI_API_KEY", "").strip()
    if not llave:
        return None
    turnos, sistema = _a_formato_gemini(messages)

    global _ULTIMO_BUENO
    # El que ya funcionó va primero; los demás quedan de reserva por si ese día
    # se cae. Así el caso normal es un solo intento, no cinco.
    orden = list(MODELOS)
    if _ULTIMO_BUENO and _ULTIMO_BUENO in orden:
        orden.remove(_ULTIMO_BUENO)
        orden.insert(0, _ULTIMO_BUENO)

    ultimo = ""
    for modelo in orden:
        for sin_pensar in (True, False):
            try:
                texto = _pedir(modelo, turnos, sistema, max_tokens,
                               temperature, llave, sin_pensar=sin_pensar)
                _ULTIMO_BUENO = modelo
                logger.info(f"[GEMINI] Respondió {modelo}")
                return texto
            except urllib.error.HTTPError as e:
                cuerpo = ""
                try:
                    cuerpo = e.read().decode("utf-8", "replace")[:200]
                except Exception:
                    pass
                ultimo = f"HTTP {e.code} {cuerpo}"
                # 429 = se acabó la cuota de HOY. Todos los modelos comparten
                # la misma bolsa, así que seguir intentando es perder tiempo.
                if e.code == 429:
                    logger.warning("[GEMINI] Sin cuota por hoy (429)")
                    return None
                if e.code == 403:
                    logger.warning(f"[GEMINI] Llave rechazada: {ultimo}")
                    return None
                # 400 puede ser que ESTE modelo no acepte `thinkingConfig`.
                # Vale la pena reintentarlo sin esa opción antes de descartarlo.
                if e.code == 400 and sin_pensar:
                    continue
                break
            except Exception as e:
                ultimo = str(e)[:160]
                break
    logger.warning(f"[GEMINI] Ningún modelo respondió. Último error: {ultimo}")
    return None
