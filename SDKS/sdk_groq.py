"""
AURORA SDK Wrapper - Groq
Based on TEENS evolucion_server.py L898-913
"""
import logging
from groq import Groq

logger = logging.getLogger("aurora.sdk.groq")

async def call_groq(prompt: str, mensaje: str, historial: list = None, api_key: str = "") -> str:
    """
    Call Groq Llama 3.3-70B

    Args:
        prompt: System prompt
        mensaje: User message
        historial: Last 4 messages (role/content pairs)
        api_key: GROQ_API_KEY

    Returns:
        Response text or None if error
    """
    if not api_key:
        logger.warning("Groq: No API key provided")
        return None

    try:
        client = Groq(api_key=api_key, timeout=12.0)

        # Build messages
        messages = [{"role": "user", "content": mensaje}]
        if historial:
            messages = historial + messages

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": prompt}] + messages,
            max_tokens=500,
            temperature=0.7,
        )

        response_text = completion.choices[0].message.content
        logger.info(f"Groq: Success ({len(response_text)} chars)")
        return response_text

    except Exception as e:
        logger.warning(f"Groq: {str(e)[:60]}")
        return None
