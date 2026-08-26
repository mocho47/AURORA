# -*- coding: utf-8 -*-
"""
AURORA — MOTOR IMAGENES Y CONTENIDO VISUAL
Guía de optimización de imágenes para ATF, MILENS y redes sociales.
Usa Groq para análisis y recomendaciones reales. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from MOTORES import _llamada_modelo as _lm
except ImportError:
    import _llamada_modelo as _lm

logger = logging.getLogger("aurora.motor_imagenes")

PROMPT_IMAGENES = """Eres el especialista en contenido visual de AURORA para ATF Retrofit y MILENS.
Das recomendaciones reales y accionables para optimizar imágenes y videos.

Especificaciones reales por plataforma:
- TikTok: 9:16 vertical, 1080x1920, <500MB, .mp4
- Instagram Reels: 9:16, 1080x1920, <650MB
- Instagram Feed: 1:1 cuadrado 1080x1080 o 4:5 vertical
- YouTube: 16:9 horizontal 1920x1080, thumbnail 1280x720
- Facebook: 1:1 o 16:9, <4GB
- WhatsApp: <64MB, JPG/PNG para fotos, <16MB audio

Para grabado láser ATF:
- Formato: PNG o SVG vectorial
- Resolución: 300 DPI mínimo
- Modo: Escala de grises o bitmap puro
- Contraste máximo: negro puro sobre blanco puro

Para sublimación MILENS:
- Formato: PNG con transparencia
- Resolución: 150-300 DPI según producto
- Perfil color: RGB (no CMYK)
- Sangrado: 3mm mínimo

Siempre das especificaciones técnicas exactas y reales."""

_MODELO = "openai/gpt-oss-20b"

SPECS_LASER = {
    "formato": "PNG o SVG",
    "resolucion": "300 DPI mínimo",
    "modo_color": "escala de grises o bitmap",
    "contraste": "negro puro #000000 sobre blanco #FFFFFF",
    "nota": "Sin medios tonos. El láser quema o no quema.",
}

SPECS_PLATAFORMAS = {
    "tiktok": {"ratio": "9:16", "res": "1080x1920", "max_mb": 500, "formato": "mp4"},
    "instagram_reel": {"ratio": "9:16", "res": "1080x1920", "max_mb": 650, "formato": "mp4"},
    "instagram_feed": {"ratio": "1:1 o 4:5", "res": "1080x1080", "max_mb": 100, "formato": "jpg/png"},
    "youtube": {"ratio": "16:9", "res": "1920x1080", "max_mb": 128000, "formato": "mp4"},
    "facebook": {"ratio": "1:1 o 16:9", "res": "1080x1080", "max_mb": 4000, "formato": "mp4/jpg"},
    "whatsapp": {"ratio": "cualquiera", "max_mb": 64, "formato": "mp4/jpg/png"},
}


class MotorImagenes:
    def __init__(self):
        self.motor_id = "motor_imagenes"
        self._groq = _lm.cliente()
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def analizar(self, descripcion: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        uso = contexto.get("uso", "redes_sociales")
        plataforma = contexto.get("plataforma", "instagram")
        specs_ref = SPECS_PLATAFORMAS.get(plataforma, {})
        prompt_usuario = (
            f"Imagen/recurso: {descripcion}\n"
            f"Uso: {uso}\n"
            f"Plataforma destino: {plataforma}\n"
            f"Specs requeridas: {specs_ref}\n"
            f"Contexto: {contexto}\n\n"
            f"Dame recomendaciones técnicas precisas y accionables."
        )
        try:
            recomendaciones = await _lm.responder(
                self._groq, PROMPT_IMAGENES, prompt_usuario,
                max_tokens=500, temperature=0.3, modelo=_MODELO)
            self.stats["exitosos"] += 1
            await self._registrar("imagen_analizada", {"uso": uso, "plataforma": plataforma})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "recomendaciones": recomendaciones,
                "specs_plataforma": specs_ref,
                "specs_laser": SPECS_LASER if uso == "laser" else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_imagenes: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.5,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorImagenes()
