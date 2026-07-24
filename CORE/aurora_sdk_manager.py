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

    async def _call_ollama(self, prompt: str, history: List[dict]) -> str:
        """Llama a Ollama (local)"""

        try:
            import httpx

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": "mistral",
                "messages": messages,
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json=data,
                    timeout=30
                )

            result = response.json()
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
