# -*- coding: utf-8 -*-
"""
AURORA · RESPALDO LOCAL CUANDO GROQ DICE QUE NO
===============================================

POR QUÉ EXISTE
--------------
Medido el 2026-07-31 en el log del servidor:

    HTTP/1.1 429 Too Many Requests
    groq._base_client: Retrying request in 3.000000 seconds   ← ×3

Ahí estaban los 16-22 segundos que hacían sentir a AURORA lenta. **No era la
arquitectura**: todo lo que no toca Groq responde en menos de un segundo. Era la
cuota del plan, y AURORA esperaba tres veces por lo mismo.

Ollama ya está instalado y corriendo en esta máquina. Cuando Groq no puede,
usarlo es mejor que esperar — y mucho mejor que fallar.

CÓMO SE CONECTA SIN TOCAR NADA
------------------------------
`consciencia.py` llama a Groq en ~10 lugares distintos. Cambiarlos todos sería
arriesgado en un archivo de 148,000 caracteres que sostiene el sistema.

En vez de eso, este módulo envuelve al cliente: se comporta exactamente igual
(`cliente.chat.completions.create(...)`), así que el resto del código no se
entera. Por dentro intenta Groq y, si falla, usa Ollama.

HONESTIDAD
----------
Cuando responde el modelo local, la respuesta **lo dice**. Regla del proyecto:
nunca ocultar de dónde salió una respuesta. El modelo local es más chico y se
equivoca más — el usuario tiene derecho a saberlo.
"""
from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any, List, Optional

logger = logging.getLogger("aurora.respaldo_local")

OLLAMA_URL = "http://127.0.0.1:11434"

# Ordenados por lo que de verdad cabe en esta PC (7.2 GB en total, y AURORA ya
# ocupa buena parte). El primero que esté instalado y quepa, se usa.
MODELOS_PREFERIDOS = ("llama3.2:3b", "qwen2.5-coder:1.5b", "qwen2.5:7b",
                      "dolphin-mistral:7b")

AVISO_LOCAL = "\n\n_(Groq no respondió; esto lo contestó el modelo local, que es más limitado.)_"


def _ollama_vivo(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def modelos_disponibles() -> List[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as r:
            datos = json.loads(r.read().decode())
        return [m.get("name", "") for m in datos.get("models", [])]
    except Exception:
        return []


def elegir_modelo() -> Optional[str]:
    """El primero de la lista de preferidos que esté instalado."""
    instalados = modelos_disponibles()
    for pref in MODELOS_PREFERIDOS:
        for m in instalados:
            if m == pref or m.startswith(pref.split(":")[0] + ":"):
                return m
    return instalados[0] if instalados else None


# Cuánto se espera al modelo local antes de rendirse.
# Medido en esta PC el 2026-08-03, con 0.8 GB de RAM libre de 7.2 GB: el modelo
# MÁS CHICO (qwen2.5-coder:1.5b, 0.9 GB) tardó 111.6 s en decir "hola", y
# `size_vram: 0` confirma que corre en CPU, sin tarjeta gráfica.
#
# Con esa RAM el respaldo es PEOR que el problema: hacer esperar dos minutos es
# peor que decir "no pude". Por eso se corta a los 25 s y se responde honesto.
# El día que la PC tenga 16 GB, este número se sube y el respaldo sirve de verdad
# — el código ya está listo, lo que falta es memoria.
SEGUNDOS_MAX_LOCAL = 25.0


def _pedir_a_ollama(modelo: str, messages: list, max_tokens: int, temperature: float,
                    timeout: float = SEGUNDOS_MAX_LOCAL) -> str:
    cuerpo = json.dumps({
        "model": modelo,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=cuerpo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        datos = json.loads(r.read().decode())
    return (datos.get("message") or {}).get("content", "") or ""


# ── Objetos que imitan la respuesta de Groq ──────────────────────────────────
# El código de consciencia lee r.choices[0].message.content y .finish_reason.
class _Mensaje:
    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


class _Opcion:
    def __init__(self, content: str):
        self.message = _Mensaje(content)
        self.finish_reason = "stop"


class _Respuesta:
    def __init__(self, content: str, modelo: str):
        self.choices = [_Opcion(content)]
        self.model = modelo
        self.desde_ollama = True      # para que quien quiera pueda distinguirlo


class _Completions:
    def __init__(self, dueno: "ClienteConRespaldo"):
        self._d = dueno

    async def create(self, *, model: str, messages: list, max_tokens: int = 800,
                     temperature: float = 0.7, **extra) -> Any:
        # 1) Groq, como siempre.
        if self._d._groq is not None:
            try:
                return await self._d._groq.chat.completions.create(
                    model=model, messages=messages, max_tokens=max_tokens,
                    temperature=temperature, **extra)
            except Exception as e:
                texto = str(e)
                # 429 = sin cuota. Los demás fallos (red, timeout) también se
                # respaldan: el usuario no tiene por qué quedarse sin respuesta
                # porque el proveedor tuvo un mal momento.
                logger.warning(f"Groq falló ({texto[:90]}) → intento con el modelo local")

        # 2) Ollama local.
        modelo_local = self._d.modelo_local
        if not modelo_local:
            raise RuntimeError("Groq no respondió y no hay modelo local disponible. "
                               "No se inventó una respuesta.")
        try:
            contenido = await asyncio.to_thread(
                _pedir_a_ollama, modelo_local, messages, max_tokens, temperature)
        except Exception as e:
            # Se dice la verdad en vez de dejar al usuario esperando o inventarle
            # algo. Con poca RAM el modelo local no alcanza a responder, y eso es
            # un dato honesto, no un fallo que haya que disimular.
            logger.warning(f"El modelo local tampoco pudo ({str(e)[:70]})")
            raise RuntimeError(
                "El proveedor de IA no tiene cuota ahora y el modelo local de esta "
                "PC no alcanzó a responder (le falta memoria). No te invento nada: "
                "vuelve a intentar en un momento, o pídeme algo que no necesite el "
                "modelo — la contabilidad, la agenda, las órdenes y los archivos "
                "funcionan sin él.") from e
        if not contenido.strip():
            raise RuntimeError("Ni Groq ni el modelo local devolvieron nada. "
                               "No se inventó una respuesta.")
        logger.info(f"[RESPALDO LOCAL] Respondió {modelo_local}")
        return _Respuesta(contenido.rstrip() + AVISO_LOCAL, modelo_local)


class _Chat:
    def __init__(self, dueno: "ClienteConRespaldo"):
        self.completions = _Completions(dueno)


class ClienteConRespaldo:
    """Se usa igual que el cliente de Groq, pero cae al modelo local si hace falta.

        cliente = ClienteConRespaldo(AsyncGroq(api_key=...))
        r = await cliente.chat.completions.create(model=..., messages=[...])

    El resto del código no cambia ni una línea.
    """

    def __init__(self, groq_client):
        self._groq = groq_client
        self.chat = _Chat(self)
        self._modelo_local: Optional[str] = None
        self._local_revisado = False

    @property
    def modelo_local(self) -> Optional[str]:
        # Se busca una sola vez: preguntar por cada mensaje sería tonto.
        if not self._local_revisado:
            self._local_revisado = True
            self._modelo_local = elegir_modelo() if _ollama_vivo() else None
            if self._modelo_local:
                logger.info(f"Respaldo local listo: {self._modelo_local}")
            else:
                logger.warning("Sin respaldo local: Ollama no responde en 11434")
        return self._modelo_local

    def __getattr__(self, nombre):
        # Cualquier otra cosa que el código le pida al cliente, se la pasa a Groq.
        return getattr(self._groq, nombre)
