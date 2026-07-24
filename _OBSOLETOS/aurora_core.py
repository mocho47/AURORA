"""
AURORA CORE - Orquestador Principal
Integra SDKs, motores, y decisión inteligente
"""

import json
from datetime import datetime
from pathlib import Path

class AURORACore:
    """Orquestador central de AURORA"""

    def __init__(self):
        self.sdk_manager = None  # Se inyecta desde servidor
        self.registry = None      # Se inyecta desde servidor
        self.conversation_history = {}
        self.user_profiles = {}

    async def procesar_mensaje(self, mensaje: str, user_id: str, rol: str) -> dict:
        """
        Procesa mensaje y retorna respuesta inteligente
        Flujo: Detectar → Seleccionar SDK → Ejecutar → Responder
        """

        # 1. DETECTAR SITUACIÓN
        situacion = self._detectar_situacion(mensaje, rol)

        # 2. SELECCIONAR SDK ÓPTIMO
        sdk_optimo = self._seleccionar_sdk(situacion)

        # 3. CONSTRUIR PROMPT
        prompt = self._construir_prompt(mensaje, situacion, rol)

        # 4. EJECUTAR CON SDK
        try:
            respuesta = await self._ejecutar_sdk(sdk_optimo, prompt, mensaje)
        except:
            respuesta = self._respuesta_fallback(situacion, mensaje)

        # 5. GUARDAR HISTORIAL
        self._guardar_historial(user_id, mensaje, respuesta, situacion)

        # 6. RETORNAR
        return {
            "respuesta": respuesta,
            "situacion": situacion,
            "sdk": sdk_optimo,
            "timestamp": datetime.now().isoformat()
        }

    def _detectar_situacion(self, mensaje: str, rol: str) -> str:
        """Detecta tipo de situación del mensaje"""

        msg_lower = mensaje.lower()

        # Mapa de palabras clave → situación
        situaciones = {
            "coaching": ["teen", "adolescente", "estres", "ansiedad", "miedo", "solo", "triste"],
            "codigo": ["codigo", "python", "javascript", "funcion", "error", "bug", "fix"],
            "analisis": ["que piensas", "analiza", "cual es", "explica", "entiendo"],
            "ventas": ["precio", "costo", "cuota", "margen", "producto", "cotiza"],
            "marketing": ["post", "social", "publico", "anuncio", "contenido"],
        }

        for situacion, keywords in situaciones.items():
            if any(kw in msg_lower for kw in keywords):
                return situacion

        return "general"

    def _seleccionar_sdk(self, situacion: str) -> str:
        """Selecciona SDK óptimo según situación"""

        # Preferencias por situación
        preferencias = {
            "coaching": "groq",      # Groq es rápido para conversación
            "codigo": "claude",       # Claude es mejor en código
            "analisis": "claude",     # Claude para análisis
            "ventas": "groq",         # Groq rápido para cálculos
            "marketing": "groq",      # Groq para creatividad
            "general": "groq",        # Default
        }

        return preferencias.get(situacion, "groq")

    def _construir_prompt(self, mensaje: str, situacion: str, rol: str) -> str:
        """Construye prompt optimizado para la situación"""

        prompts_base = {
            "coaching": f"""Eres AURORA, asistente psicológico para adolescentes.
Contexto: Usuario es {rol}
Mensaje: {mensaje}

PRINCIPIOS:
- Acompañamiento sin imposición
- Validar emociones
- Proporcionar herramientas reales
- Nunca diagnostic ni medicalizar
- Ser directo y honesto

Responde en 2-3 párrafos.""",

            "codigo": f"""Eres AURORA, experto en código.
Problema: {mensaje}

ESTRUCTURA:
1. Entender el problema
2. Proponer solución
3. Código si necesario
4. Explicación""",

            "analisis": f"""Eres AURORA, analizador inteligente.
Pregunta: {mensaje}

Analiza profundamente y da insights.""",

            "ventas": f"""Eres AURORA, cotizador automático.
Solicitud: {mensaje}

Calcula precios automáticamente con márgenes.""",

            "general": f"""Eres AURORA, asistente inteligente.
Pregunta: {mensaje}

Responde directamente y útilmente.""",
        }

        return prompts_base.get(situacion, prompts_base["general"])

    async def _ejecutar_sdk(self, sdk_name: str, prompt: str, mensaje: str) -> str:
        """Ejecuta prompt con SDK seleccionado"""

        if not self.sdk_manager:
            return self._respuesta_fallback("general", mensaje)

        try:
            respuesta = await self.sdk_manager.call_sdk(sdk_name, prompt, [])
            return respuesta
        except:
            return self._respuesta_fallback("general", mensaje)

    def _respuesta_fallback(self, situacion: str, mensaje: str) -> str:
        """Respuesta fallback cuando no hay SDK disponible"""

        fallbacks = {
            "coaching": "Entiendo tu situación. ¿Cuéntame más sobre qué te preocupa?",
            "codigo": "Para ayudarte mejor, ¿puedes compartir el código que no funciona?",
            "analisis": "Esa es una buena pregunta. Déjame procesarla.",
            "ventas": "Puedo calcular precios. ¿Cuál es el producto y cantidad?",
            "general": "Entiendo. ¿Puedes ampliar la información?",
        }

        return fallbacks.get(situacion, "¿Puedes decirme más?")

    def _guardar_historial(self, user_id: str, mensaje: str, respuesta: str, situacion: str):
        """Guarda conversación en historial"""

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "mensaje": mensaje,
            "respuesta": respuesta,
            "situacion": situacion
        })

    def obtener_historial(self, user_id: str) -> list:
        """Retorna historial del usuario"""
        return self.conversation_history.get(user_id, [])
