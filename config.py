# -*- coding: utf-8 -*-
"""
⚙️  CONFIGURACIÓN CENTRALIZADA DE AURORA - PRODUCCIÓN
Lee variables del archivo .env
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
from pydantic import model_validator
import os
from pathlib import Path

class Settings(BaseSettings):
    """Configuración validada de AURORA v3"""
    
    # =========== GROQ API ===========
    groq_api_key: str
    groq_model: str = "mixtral-8x7b-32768"
    
    # =========== WHATSAPP (GREEN-API) ===========
    green_api_instance_id: str = "7107622171"
    green_api_token: str
    
    # =========== FACEBOOK/INSTAGRAM ===========
    fb_page_id: Optional[str] = None
    fb_page_token: Optional[str] = None
    facebook_access_token: Optional[str] = None
    facebook_page_id: Optional[str] = None
    instagram_user_id: Optional[str] = None
    instagram_business_account_id: Optional[str] = None
    instagram_access_token: Optional[str] = None
    
    # =========== META ADS ===========
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_business_account_id: Optional[str] = None
    
    # =========== TIKTOK ===========
    tiktok_access_token: Optional[str] = None
    tiktok_business_account_id: Optional[str] = None
    
    # =========== DATABASE ===========
    db_path: str = r"C:\AURORA\SUPER_MARKETING_SYSTEM\analytics\marketing.db"
    db_backup_path: str = r"C:\AURORA\BACKUPS"
    
    # =========== JWT SECURITY ===========
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # =========== SERVER ===========
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 5000
    fastapi_env: str = "production"
    
    # =========== LOGGING ===========
    log_level: str = "INFO"
    log_file: str = r"C:\AURORA\LOGS\aurora.log"
    
    # =========== RATE LIMITING ===========
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    cors_origins: List[str] = ["http://localhost:5000", "http://localhost:3000"]

    @model_validator(mode='after')
    def unificar_tokens_facebook(self):
        """
        Si facebook_access_token no está definido, usa fb_page_token como fallback.
        Esto resuelve la inconsistencia entre los nombres de variables en el .env.
        """
        if not self.facebook_access_token and self.fb_page_token:
            self.facebook_access_token = self.fb_page_token
        if not self.facebook_page_id and self.fb_page_id:
            self.facebook_page_id = self.fb_page_id
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Obtener configuración (cached)"""
    return Settings()

def validate_production_settings():
    """Valida que estemos en producción"""
    settings = get_settings()
    
    # Credenciales críticas
    critical = [
        ("groq_api_key", settings.groq_api_key),
        ("green_api_token", settings.green_api_token),
        ("jwt_secret_key", settings.jwt_secret_key),
    ]
    
    # Aceptar Facebook O Instagram
    has_facebook = settings.facebook_access_token or settings.fb_page_token
    has_instagram = settings.instagram_access_token
    
    if not (has_facebook or has_instagram):
        raise ValueError("❌ CRÍTICO: Se requiere token de Facebook O Instagram")
    
    for field_name, field_val in critical:
        if not field_val or field_val.startswith("your_"):
            raise ValueError(f"❌ CRÍTICO: {field_name} no configurado en .env")
    
    print("✅ Configuración de producción validada")
    return settings

# Instancia global
settings = get_settings()
