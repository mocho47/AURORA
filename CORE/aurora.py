"""
AURORA v1 - Intelligent Orchestrator
Point of entry for multi-motor, multi-SDK NEXUS replacement
Integrates selector + sdk_manager + registry for autonomous operation
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("aurora")

# Import AURORA components
from aurora_selector import get_selector
from aurora_sdk_manager import call_with_fallback
from aurora_registry import MotorRegistry
from config import DEFAULT_MOTOR, SCORE_THRESHOLD


class AURORA:
    """Main orchestrator class"""

    def __init__(self):
        """Initialize AURORA with all subsystems"""
        self.selector = get_selector()
        self.registry = MotorRegistry()
        self.historial_dir = Path(r"C:\AURORA\SHARED\historial")
        self.historial_dir.mkdir(parents=True, exist_ok=True)
        logger.info("AURORA initialized")

    async def procesar_mensaje(self, mensaje: str, contexto: dict = None) -> dict:
        """
        Process user message and route to optimal motor + SDK

        Args:
            mensaje: User message
            contexto: Optional context dict

        Returns:
            Response dict with motor_id, respuesta, tokens_usados, etc.
        """
        contexto = contexto or {}
        start_time = datetime.now()

        logger.info(f"Processing: {mensaje[:50]}...")

        try:
            # TIER 1-6: Select motor + SDK
            motor_config, sdk_name = await self.selector.select(mensaje, contexto)
            logger.info(f"Routed to {motor_config.motor_id} via {sdk_name}")

            # Build prompt for motor
            prompt = self._build_prompt(motor_config, contexto)

            # Call SDK with fallback chain
            respuesta = await call_with_fallback(
                sdk_preference=sdk_name,
                prompt=prompt,
                mensaje=mensaje,
                historial=contexto.get("historial", []),
                fallback_chain=["groq", "zai", "ollama"],
            )

            if not respuesta:
                respuesta = "Disculpa, no pude procesar tu consulta. Intenta más tarde."

            # Record response in history
            await self._guardar_historial(motor_config.motor_id, mensaje, respuesta)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed in {elapsed:.2f}s")

            return {
                "motor_id": motor_config.motor_id,
                "respuesta": respuesta,
                "sdk_usado": sdk_name,
                "tiempo_ms": int(elapsed * 1000),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "motor_id": "error",
                "error": str(e),
                "status": "error",
            }

    def _build_prompt(self, motor_config, contexto: dict) -> str:
        """
        Build system prompt for motor

        Args:
            motor_config: MotorConfig object
            contexto: Context dict

        Returns:
            System prompt string
        """
        # Base prompt from motor description
        prompt = f"""Eres {motor_config.nombre}.
{motor_config.descripcion}

Tu objetivo es: responder consultas del usuario de manera útil y precisa.
Responde en español, sé directo y conciso.
"""

        # Add context if available
        if contexto.get("sensible"):
            prompt += (
                f"\n⚠️ Tema sensible detectado: {contexto.get('tema', 'general')}. "
                "Responde con cuidado y empatía."
            )

        if contexto.get("perfil"):
            prompt += f"\nUsuario: {contexto.get('perfil')}"

        return prompt

    async def _guardar_historial(self, motor_id: str, mensaje: str, respuesta: str):
        """Save message/response to history file"""
        try:
            timestamp = datetime.now().isoformat()
            entry = {
                "timestamp": timestamp,
                "motor_id": motor_id,
                "mensaje": mensaje[:200],
                "respuesta": respuesta[:200],
            }

            historial_file = self.historial_dir / f"{motor_id}_{datetime.now().date()}.json"

            # Append to file
            entries = []
            if historial_file.exists():
                with open(historial_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)

            entries.append(entry)

            with open(historial_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Failed to save history: {e}")

    async def main_loop(self):
        """Main interactive loop (for testing)"""
        logger.info("AURORA ready. Type messages (or 'exit' to quit):")
        while True:
            try:
                mensaje = input("\n> ").strip()
                if mensaje.lower() == "exit":
                    break

                result = await self.procesar_mensaje(mensaje)
                print(f"\n{result.get('respuesta', 'Error')}")
                print(f"[{result.get('motor_id')} / {result.get('sdk_usado')}]")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")


# Singleton instance
_aurora = None


def get_aurora() -> AURORA:
    """Get or create AURORA instance"""
    global _aurora
    if _aurora is None:
        _aurora = AURORA()
    return _aurora


async def main():
    """Entry point"""
    aurora = get_aurora()
    await aurora.main_loop()


if __name__ == "__main__":
    asyncio.run(main())
