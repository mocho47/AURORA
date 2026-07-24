"""
AURORA SDK Wrapper - Ollama (Local)
Based on TEENS evolucion_server.py L915-929
"""
import logging
import aiohttp
import json

logger = logging.getLogger("aurora.sdk.ollama")

async def call_ollama(prompt: str, mensaje: str, historial: list = None, base_url: str = "http://localhost:11434") -> str:
    """
    Call Ollama (local HTTP API)

    Args:
        prompt: System prompt
        mensaje: User message
        historial: Last 4 messages (role/content pairs)
        base_url: Ollama base URL

    Returns:
        Response text or None if error
    """
    try:
        # Build messages
        messages = [{"role": "user", "content": mensaje}]
        if historial:
            messages = historial[-4:] + messages

        url = f"{base_url}/api/chat"

        payload = {
            "model": "dolphin-mixtral:latest",
            "messages": [{"role": "system", "content": prompt}] + messages,
            "stream": False,
        }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.warning(f"Ollama: HTTP {resp.status}")
                    return None

                data = await resp.json()
                response_text = data.get("message", {}).get("content", "")

                if response_text:
                    logger.info(f"Ollama: Success ({len(response_text)} chars)")
                    return response_text
                else:
                    logger.warning("Ollama: Empty response")
                    return None

    except Exception as e:
        logger.warning(f"Ollama: {str(e)[:60]}")
        return None
