"""
AURORA SDK Wrapper - Zai (GLM-4-Flash)
Based on TEENS evolucion_server.py L881-896
"""
import logging
from openai import OpenAI

logger = logging.getLogger("aurora.sdk.zai")

async def call_zai(prompt: str, mensaje: str, historial: list = None, api_key: str = "") -> str:
    """
    Call Zai (GLM-4-Flash via OpenAI SDK)

    Args:
        prompt: System prompt
        mensaje: User message
        historial: Last 6 messages (role/content pairs)
        api_key: ZAI_API_KEY

    Returns:
        Response text or None if error
    """
    if not api_key:
        logger.warning("Zai: No API key provided")
        return None

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            timeout=8.0,
        )

        # Build messages
        messages = [{"role": "user", "content": mensaje}]
        if historial:
            # Keep last 6 messages for Zai
            messages = historial[-6:] + messages

        completion = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "system", "content": prompt}] + messages,
            max_tokens=400,
            temperature=0.7,
        )

        response_text = completion.choices[0].message.content
        logger.info(f"Zai: Success ({len(response_text)} chars)")
        return response_text

    except Exception as e:
        logger.warning(f"Zai: {str(e)[:60]}")
        return None
