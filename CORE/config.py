"""
AURORA Configuration Manager - Professional Setup
"""

import os
from pathlib import Path

class Config:
    """Gestor centralizado de configuración"""

    # ========== PATHS ==========
    PROJECT_DIR = Path(__file__).parent.parent
    CORE_DIR = Path(__file__).parent
    DB_PATH = PROJECT_DIR / "aurora.db"
    PANEL_PATH = PROJECT_DIR / "panel.html"
    LOG_DIR = PROJECT_DIR / "logs"

    # ========== SERVER ==========
    HOST = os.getenv("AURORA_HOST", "127.0.0.1")
    PORT = int(os.getenv("AURORA_PORT", "8000"))
    DEBUG = os.getenv("AURORA_DEBUG", "false").lower() == "true"

    # ========== APIs ==========
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # ========== DATABASE ==========
    DB_WAL = True
    DB_TIMEOUT = 30

    # ========== MODELOS ==========
    DEFAULT_MODEL_CLAUDE = "claude-3-5-sonnet-20241022"
    DEFAULT_MODEL_GROQ = "mixtral-8x7b-32768"
    DEFAULT_MODEL_OLLAMA = "mistral"
    MAX_TOKENS = 1024

    # ========== CRISIS PROTOCOL ==========
    CRISIS_ALERT_EMAIL = os.getenv("CRISIS_ALERT_EMAIL", "")
    CRISIS_AUTO_ESCALATE = os.getenv("CRISIS_AUTO_ESCALATE", "true").lower() == "true"

    @staticmethod
    def validate():
        """Valida configuración"""
        has_sdk = (
            Config.ANTHROPIC_API_KEY or
            Config.GROQ_API_KEY or
            Config.ZAI_API_KEY
        )

        if not has_sdk:
            return False, "Sin SDK configurado. Fallback: Ollama"

        return True, "OK"

    @staticmethod
    def print_status():
        """Imprime estado de config"""
        valid, msg = Config.validate()

        print("\n" + "="*70)
        print("AURORA CONFIGURATION")
        print("="*70)
        print(f"Server:    {Config.HOST}:{Config.PORT}")
        print(f"Database:  {Config.DB_PATH}")
        print(f"\nSDKs Available:")
        print(f"  Claude:  {'✅' if Config.ANTHROPIC_API_KEY else '❌'}")
        print(f"  Groq:    {'✅' if Config.GROQ_API_KEY else '❌'}")
        print(f"  Zai:     {'✅' if Config.ZAI_API_KEY else '❌'}")
        print(f"  Ollama:  ✅ {Config.OLLAMA_URL}")
        print(f"\nStatus: {msg}")
        print("="*70 + "\n")

    @staticmethod
    def get_available_sdks():
        """Retorna SDKs disponibles"""
        available = []

        if Config.ANTHROPIC_API_KEY:
            available.append("claude")
        if Config.GROQ_API_KEY:
            available.append("groq")
        if Config.ZAI_API_KEY:
            available.append("zai")

        available.append("ollama")
        return available
