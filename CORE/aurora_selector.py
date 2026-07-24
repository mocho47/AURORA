"""
AURORA Selector - Decision Engine
Basado en TEENS evolucion_server.py tiers 1-6 (líneas 319-1441)
Analiza mensajes y elige motor + SDK óptimo
"""
import logging
import json
from typing import Optional, Tuple, Dict
from pathlib import Path

logger = logging.getLogger("aurora.selector")


class MotorConfig:
    """Motor metadata and configuration"""

    def __init__(self, motor_id: str, metadata: dict):
        self.motor_id = motor_id
        self.nombre = metadata.get("nombre", "Unknown")
        self.descripcion = metadata.get("descripcion", "")
        self.patrones = metadata.get("patrones", [])
        self.sdk_preferido = metadata.get("sdk_preferido", "groq")
        self.puerto = metadata.get("puerto", 8001)
        self.timeout = metadata.get("timeout", 12.0)
        self.max_tokens = metadata.get("max_tokens", 500)
        self.activo = metadata.get("activo", True)


class AuroraSelector:
    """Decision engine: 6-tier analysis for motor + SDK selection"""

    def __init__(self, motores_metadata_path: str = None):
        """
        Initialize with motor registry

        Args:
            motores_metadata_path: Path to metadata.json (defaults to C:\AURORA\MOTORES\metadata.json)
        """
        if motores_metadata_path is None:
            motores_metadata_path = r"C:\AURORA\MOTORES\metadata.json"

        self.motores: Dict[str, MotorConfig] = {}
        self._load_metadata(motores_metadata_path)
        self.default_motor = "motor_analisis"
        self.sdk_fallback_chain = ["groq", "zai", "ollama"]

    def _load_metadata(self, path: str) -> None:
        """Load motor metadata from JSON"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    motor_id = item.get("id")
                    self.motores[motor_id] = MotorConfig(motor_id, item)
                logger.info(f"Loaded {len(self.motores)} motors from {path}")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    async def select(
        self, mensaje: str, contexto: dict = None
    ) -> Tuple[MotorConfig, str]:
        """
        Select optimal motor and SDK for message

        TIER LOGIC (based on TEENS L319-1441):
        1. Vital Risk Detection: autolesión, abuso, drogas → motor_seguridad + ollama (local)
        2. Sensitive Topics: emocional, familia, trauma → aumenta contexto
        3. Dynamic Context: historial, membresía, perfil → refina selección
        4. Motor Pattern Matching: keywords en patrones → scoring
        5. Profile Detection: tipo usuario (teen/padre/maestro) → ajusta prompt
        6. SDK Selection: verifica env vars, aplica fallback ZAI→GROQ→OLLAMA

        Args:
            mensaje: User message
            contexto: Optional context dict

        Returns:
            (MotorConfig, sdk_name) tuple
        """
        contexto = contexto or {}

        # ─── TIER 1: Vital Risk Detection ───────────────────────────────────
        riesgo_vital = await self._tier1_vital_risk(mensaje, contexto)
        if riesgo_vital:
            logger.warning(f"Vital risk detected: {riesgo_vital}")
            # Return safety motor + local SDK
            motor = self.motores.get(
                "motor_seguridad", self.motores.get(self.default_motor)
            )
            return (motor, "ollama")  # Local only for safety

        # ─── TIER 2: Sensitive Topics ───────────────────────────────────────
        sensible = await self._tier2_sensitive_topics(mensaje)
        if sensible:
            logger.debug(f"Sensitive topic detected: {sensible}")
            contexto["sensible"] = True
            contexto["tema"] = sensible

        # ─── TIER 3: Dynamic Context ────────────────────────────────────────
        contexto = await self._tier3_dynamic_context(mensaje, contexto)

        # ─── TIER 4: Motor Pattern Matching ──────────────────────────────────
        motor_candidates = await self._tier4_pattern_matching(mensaje)
        if not motor_candidates:
            motor = self.motores.get(self.default_motor)
            logger.debug(f"No match, using default: {motor.motor_id}")
        else:
            motor = motor_candidates[0][0]  # Highest score first
            logger.debug(
                f"Selected motor: {motor.motor_id} (score: {motor_candidates[0][1]})"
            )

        # ─── TIER 5: Profile Detection ───────────────────────────────────────
        perfil = await self._tier5_profile_detection(contexto)
        contexto["perfil"] = perfil
        logger.debug(f"Profile detected: {perfil}")

        # ─── TIER 6: SDK Selection ───────────────────────────────────────────
        sdk = await self._tier6_sdk_selection(motor.sdk_preferido)
        logger.info(f"Final: motor={motor.motor_id}, sdk={sdk}")

        return (motor, sdk)

    async def _tier1_vital_risk(self, mensaje: str, contexto: dict) -> Optional[str]:
        """
        TIER 1: Detect critical safety keywords
        Autolesión, abuso, intención de dañarse → activar protocolo seguridad
        """
        keywords_riesgo = {
            "autolesión": ["cortarme", "me corto", "lastimarme", "suicidia"],
            "abuso": ["abusó", "abuso", "violación", "violó"],
            "drogas_severo": [
                "overdosis",
                "envenenarme",
                "me enveno",
                "drogarme",
            ],
        }

        msg_lower = mensaje.lower()
        for riesgo_tipo, keywords in keywords_riesgo.items():
            for kw in keywords:
                if kw in msg_lower:
                    return riesgo_tipo

        return None

    async def _tier2_sensitive_topics(self, mensaje: str) -> Optional[str]:
        """
        TIER 2: Detect sensitive but non-critical topics
        Familia, emociones, relaciones → aumentar contexto en prompt
        """
        temas_sensibles = {
            "familia": ["papá", "mamá", "hermano", "familia", "padres", "casa"],
            "emocional": [
                "triste",
                "deprimido",
                "miedo",
                "ansiedad",
                "asustado",
                "llorar",
            ],
            "relaciones": ["novio", "novia", "amor", "pareja", "enamorad@"],
            "identidad": ["identidad", "género", "sexualidad", "quién soy"],
        }

        msg_lower = mensaje.lower()
        for tema, keywords in temas_sensibles.items():
            for kw in keywords:
                if kw in msg_lower:
                    return tema

        return None

    async def _tier3_dynamic_context(self, mensaje: str, contexto: dict) -> dict:
        """
        TIER 3: Enrich context with dynamic data
        Historial, perfil de usuario, preferencias previas
        """
        # In full implementation, would load from DB:
        # - Historial de usuario
        # - Preferencias
        # - Contexto previo

        contexto.setdefault("mensaje_length", len(mensaje))
        contexto.setdefault("tiene_preguntas", "?" in mensaje)
        contexto.setdefault("tiene_numeros", any(c.isdigit() for c in mensaje))

        return contexto

    async def _tier4_pattern_matching(
        self, mensaje: str
    ) -> list[Tuple[MotorConfig, float]]:
        """
        TIER 4: Match message against motor patterns
        Scoring: suma de keywords encontrados
        """
        msg_lower = mensaje.lower()
        scores = {}

        for motor_id, motor in self.motores.items():
            if not motor.activo:
                continue

            score = 0.0
            for patron in motor.patrones:
                if patron.lower() in msg_lower:
                    score += 1.0

            if score > 0:
                scores[motor_id] = score / len(motor.patrones) if motor.patrones else 0.5

        # Sort by score descending
        candidatos = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.motores[mid], score) for mid, score in candidatos]

    async def _tier5_profile_detection(self, contexto: dict) -> str:
        """
        TIER 5: Detect user profile (teen, padre, maestro, etc)
        Ajusta tone/context del prompt
        """
        # In full implementation, would detect from:
        # - user_id membership
        # - previous interactions
        # - role in familia_id

        perfil = contexto.get("perfil", "usuario_generico")
        return perfil

    async def _tier6_sdk_selection(self, sdk_preferido: str) -> str:
        """
        TIER 6: Select optimal SDK with fallback
        Logic from TEENS L871-879:
        - Si ZAI_API_KEY: intenta zai
        - Si GROQ_API_KEY: intenta groq
        - Siempre ollama (local)
        """
        import os

        zai_key = os.getenv("ZAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        claude_key = os.getenv("CLAUDE_API_KEY")

        # Build chain: preferred first, then fallbacks
        chain = [sdk_preferido]
        for sdk in self.sdk_fallback_chain:
            if sdk not in chain:
                chain.append(sdk)

        # Check availability
        available = {
            "zai": bool(zai_key),
            "groq": bool(groq_key),
            "claude": bool(claude_key),
            "ollama": True,  # Always available locally
        }

        for sdk in chain:
            if available.get(sdk, False):
                logger.debug(f"SDK {sdk} available, selected")
                return sdk

        logger.warning(f"No SDK available, defaulting to ollama")
        return "ollama"


# Singleton instance
_selector = None


def get_selector() -> AuroraSelector:
    """Get or create selector instance"""
    global _selector
    if _selector is None:
        _selector = AuroraSelector()
    return _selector
