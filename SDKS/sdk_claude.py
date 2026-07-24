"""
AURORA SDK Wrapper - Claude (Anthropic)
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger("aurora.sdk.claude")

async def call_claude(prompt: str, mensaje: str, historial: list = None, api_key: str = "") -> str:
    """
    Call Claude via Anthropic SDK

    Args:
        prompt: System prompt
        mensaje: User message
        historial: Last 8 messages (role/content pairs)
        api_key: CLAUDE_API_KEY

    Returns:
        Response text or None if error
    """
    if not api_key:
        logger.warning("Claude: No API key provided")
        return None

    try:
        client = Anthropic(api_key=api_key)

        # Build messages
        messages = [{"role": "user", "content": mensaje}]
        if historial:
            # Keep last 8 messages for Claude
            messages = historial[-8:] + messages

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=prompt,
            messages=messages,
        )

        response_text = response.content[0].text
        logger.info(f"Claude: Success ({len(response_text)} chars)")
        return response_text

    except Exception as e:
        logger.warning(f"Claude: {str(e)[:60]}")
        return None
