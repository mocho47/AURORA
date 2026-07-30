"""
AURORA SDK Manager - Multi-SDK Orchestrator
Soporta: Claude, Groq, Zai, Ollama (con fallback automático)
"""

import os
import asyncio
from typing import Optional, List

class AuroraSDKManager:
    """Orquesta entre múltiples SDKs con fallback inteligente"""

    def __init__(self):
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.zai_key = os.getenv("ZAI_API_KEY")

    async def call_sdk(self, sdk_name: str, prompt: str, history: List[dict] = None) -> str:
        """
        Llama SDK especificado con fallback automático
        Fallback: SDK primario → Groq → Ollama → Fallback local
        """

        if history is None:
            history = []

        try:
            if sdk_name == "claude" and self.claude_key:
                return await self._call_claude(prompt, history)
            elif sdk_name == "groq" and self.groq_key:
                return await self._call_groq(prompt, history)
            elif sdk_name == "zai" and self.zai_key:
                return await self._call_zai(prompt, history)
            elif sdk_name == "ollama":
                return await self._call_ollama(prompt, history)
        except Exception as e:
            print(f"Error con {sdk_name}: {e}")

        # Fallback automático
        return await self._fallback(prompt, history)

    async def _call_claude(self, prompt: str, history: List[dict]) -> str:
        """Llama a Claude via Anthropic API"""

        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.claude_key)

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system="Eres AURORA, asistente inteligente para desarrollo humano, educación y negocios.",
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            raise Exception(f"Claude error: {str(e)}")

    async def _call_groq(self, prompt: str, history: List[dict]) -> str:
        """Llama a Groq API"""

        try:
            from groq import Groq

            client = Groq(api_key=self.groq_key)

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=1024,
                messages=messages
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Groq error: {str(e)}")

    async def _call_zai(self, prompt: str, history: List[dict]) -> str:
        """Llama a Zai GLM-4"""

        try:
            import httpx

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            headers = {"Authorization": f"Bearer {self.zai_key}"}
            data = {
                "model": "glm-4",
                "messages": messages,
                "max_tokens": 1024
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.zai.ai/v1/chat/completions",
                    json=data,
                    headers=headers,
                    timeout=30
                )

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            raise Exception(f"Zai error: {str(e)}")

    # Preferencia de modelos LOCALES, del mejor al mas ligero. Se elige el primero
    # que de verdad este instalado (arreglo 2026-07-29): antes estaba hardcodeado
    # "mistral", que NO esta instalado en esta maquina -> Ollama respondia 404 y el
    # manager caia en relevo a Groq EN SILENCIO. Parecia funcionar, pero la
    # capacidad OFFLINE (la que aguanta sin WiFi) estaba muerta en este modulo.
    # ORDEN POR HARDWARE REAL, no por "cual es el mejor modelo" (medido en vivo
    # 2026-07-29): esta PC tiene 7.2 GB de RAM. Un modelo de 7B (qwen2.5:7b,
    # dolphin-mistral:7b) en CPU con esa RAM se pasa de 120s y no contesta —
    # probado. llama3.2:3b es el que ya usa consciencia.py y SI responde. Los 7B
    # quedan al final: solo servirian en una maquina con mas RAM.
    PREFERENCIA_OLLAMA = ("llama3.2:3b", "qwen2.5-coder:1.5b",
                          "qwen2.5:7b", "dolphin-mistral:7b", "mistral")

    async def _modelo_ollama_disponible(self) -> str:
        """Pregunta a Ollama que modelos tiene y devuelve el mejor segun la
        preferencia. Cadena vacia si Ollama no responde (no se adivina)."""
        if getattr(self, "_modelo_ollama_cache", None):
            return self._modelo_ollama_cache
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{self.ollama_url}/api/tags", timeout=10)
            instalados = [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            return ""
        for preferido in self.PREFERENCIA_OLLAMA:
            if preferido in instalados:
                self._modelo_ollama_cache = preferido
                return preferido
        # Ninguno de los preferidos: se usa el primero instalado que no sea de
        # embeddings ni de vision (esos no sirven para conversar).
        for nombre in instalados:
            if not any(x in nombre for x in ("embed", "moondream", "vision")):
                self._modelo_ollama_cache = nombre
                return nombre
        return ""

    async def _call_ollama(self, prompt: str, history: List[dict]) -> str:
        """Llama a Ollama (local, funciona sin internet)."""
        try:
            import httpx

            modelo = await self._modelo_ollama_disponible()
            if not modelo:
                raise Exception("Ollama no responde o no tiene ningún modelo de chat instalado "
                                "(revisa que Ollama esté corriendo: ollama list)")

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={"model": modelo, "messages": messages, "stream": False},
                    timeout=120,   # un modelo local en CPU tarda mas que la nube
                )

            result = response.json()
            # Error honesto: si Ollama contesta con {"error": ...} se dice cual fue,
            # en vez de reventar con un KeyError incomprensible ('message').
            if "error" in result:
                raise Exception(f"Ollama rechazó la petición (modelo '{modelo}'): {result['error']}")
            if "message" not in result:
                raise Exception(f"Ollama respondió sin 'message' (modelo '{modelo}'): {str(result)[:150]}")
            return result["message"]["content"]

        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")

    async def _fallback(self, prompt: str, history: List[dict]) -> str:
        """Fallback automático: intenta Groq → Ollama → Local"""

        # Intenta Groq
        if self.groq_key:
            try:
                return await self._call_groq(prompt, history)
            except:
                pass

        # Intenta Ollama
        try:
            return await self._call_ollama(prompt, history)
        except:
            pass

        # Fallback final: respuesta local
        return "Lo siento, no hay SDKs disponibles. Configura GROQ_API_KEY o Ollama."

    def list_available_sdks(self) -> List[str]:
        """Lista SDKs disponibles"""

        available = []

        if self.claude_key:
            available.append("claude")
        if self.groq_key:
            available.append("groq")
        if self.zai_key:
            available.append("zai")

        # Ollama siempre está disponible
        available.append("ollama")

        return available if available else ["fallback_local"]

    def get_sdk_status(self) -> dict:
        """Retorna estado de cada SDK"""

        return {
            "claude": bool(self.claude_key),
            "groq": bool(self.groq_key),
            "zai": bool(self.zai_key),
            "ollama": True,  # Asumimos localhost
            "fallback": "activo"
        }
