"""
AURORA Registry - Motor Auto-Discovery
Based on NEXUS v3 importlib pattern (lines 219-233)
Dynamic motor loading and execution
"""
import json
import logging
import importlib.util
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger("aurora.registry")


class MotorRegistry:
    """Auto-discovers and manages motor modules"""

    def __init__(self, motores_dir: str = None):
        """
        Initialize registry

        Args:
            motores_dir: Path to motors directory (defaults to <raiz_proyecto>/MOTORES)
        """
        if motores_dir is None:
            motores_dir = str(Path(__file__).resolve().parent.parent / "MOTORES")

        self.motores_dir = Path(motores_dir)
        self.motores: Dict[str, Any] = {}
        self.metadata: Dict[str, dict] = {}

        self._load_metadata()
        self._discover_motors()

    def _load_metadata(self) -> None:
        """Load motor metadata from metadata.json"""
        try:
            metadata_file = self.motores_dir / "metadata.json"
            with open(metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for motor_def in data:
                    motor_id = motor_def.get("id")
                    self.metadata[motor_id] = motor_def
                logger.info(f"Loaded metadata for {len(self.metadata)} motors")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    def _discover_motors(self) -> None:
        """
        Auto-discover motor modules using importlib
        Pattern from NEXUS v3 L219-233
        """
        motor_files = list(self.motores_dir.glob("motor_*.py"))
        logger.info(f"Discovering motors in {self.motores_dir}")

        for motor_file in motor_files:
            motor_name = motor_file.stem  # e.g., "motor_analisis"
            try:
                # Load module using importlib
                spec = importlib.util.spec_from_file_location(
                    f"aurora.motores.{motor_name}", motor_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Extract motor instance
                    if hasattr(module, "motor"):
                        self.motores[motor_name] = module.motor
                        logger.info(f"Loaded motor: {motor_name}")
                    else:
                        logger.warning(f"{motor_name}: no 'motor' instance found")

            except Exception as e:
                logger.error(f"Failed to load {motor_name}: {e}")

    def get_motor(self, motor_id: str) -> Optional[Any]:
        """
        Get motor instance by ID

        Args:
            motor_id: Motor identifier (e.g., "motor_analisis")

        Returns:
            Motor instance or None
        """
        return self.motores.get(motor_id)

    def get_metadata(self, motor_id: str) -> Optional[dict]:
        """
        Get motor metadata

        Args:
            motor_id: Motor identifier

        Returns:
            Metadata dict or None
        """
        return self.metadata.get(motor_id)

    def get_active_motors(self) -> list[str]:
        """Get list of active motor IDs"""
        return [
            motor_id
            for motor_id, meta in self.metadata.items()
            if meta.get("activo", True)
        ]

    async def execute_motor(
        self, motor_id: str, action: str, data: dict = None
    ) -> dict:
        """
        Execute action on motor

        Args:
            motor_id: Motor to execute
            action: Action method name (e.g., "analyze")
            data: Input data dict

        Returns:
            Result dict
        """
        data = data or {}
        motor = self.get_motor(motor_id)

        if not motor:
            return {"status": "error", "error": f"Motor {motor_id} not found"}

        try:
            # Get method from motor
            if not hasattr(motor, action):
                return {
                    "status": "error",
                    "error": f"Motor {motor_id} has no action '{action}'",
                }

            method = getattr(motor, action)

            # Call method (assuming it's async)
            if callable(method):
                result = await method(**data) if asyncio.iscoroutinefunction(method) else method(**data)
                return result

            return {"status": "error", "error": f"Action '{action}' is not callable"}

        except Exception as e:
            logger.error(f"Error executing {motor_id}.{action}: {e}")
            return {"status": "error", "error": str(e)}

    def list_motors(self) -> list[dict]:
        """List all motors with metadata"""
        result = []
        for motor_id, meta in self.metadata.items():
            result.append({
                "id": motor_id,
                "nombre": meta.get("nombre"),
                "activo": meta.get("activo", True),
                "sdk_preferido": meta.get("sdk_preferido"),
                "puerto": meta.get("puerto"),
            })
        return result

    def get_status(self) -> dict:
        """Get registry status"""
        return {
            "total_motors": len(self.metadata),
            "active_motors": len(self.get_active_motors()),
            "loaded_modules": len(self.motores),
            "motors": self.list_motors(),
        }


# Singleton instance
_registry = None


def get_registry() -> MotorRegistry:
    """Get or create registry instance"""
    global _registry
    if _registry is None:
        _registry = MotorRegistry()
    return _registry
