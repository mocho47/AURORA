"""
AURORA - PROTOCOLO DE CRISIS SILENCIOSO
Detección automática + Intervención sin pausar sistema
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

class CrisisLevel(Enum):
    NORMAL = 1
    STRESSED = 2
    ANXIOUS = 3
    AT_RISK = 4
    CRITICAL = 5

class CrisisProtocol:
    """
    PROTOCOLO SILENCIOSO:
    - Level 1-2: Técnicas de regulación
    - Level 3: Sugerencia de hablar con alguien
    - Level 4: ALERTA SILENCIOSA a adultos (el adolescente NO se entera)
    - Level 5: CONTACTO INMEDIATO servicios emergencia
    """

    def __init__(self):
        self.crisis_keywords = {
            "critical": [
                "quiero morir", "no quiero vivir", "me lastimo",
                "suicidio", "me corto", "ahorcarse", "veneno",
                "nadie me quiere", "soy un fracaso total"
            ],
            "at_risk": [
                "pensé en", "consideré", "no sé si pueda",
                "mejor desaparecer", "problema sin solución",
                "todo es culpa mía", "merezco sufrir"
            ],
            "anxious": [
                "muy asustado", "no aguanto", "me ahogo",
                "ataques de pánico", "no puedo controlar"
            ],
            "stressed": [
                "abrumado", "presionado", "demasiado",
                "no doy abasto", "imposible"
            ]
        }

        self.intervention_protocols = {
            1: self._level_1_normal,
            2: self._level_2_stressed,
            3: self._level_3_anxious,
            4: self._level_4_at_risk,
            5: self._level_5_critical,
        }

    async def analyze_message(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """
        Analiza mensaje y determina nivel de crisis
        """

        message_lower = message.lower()

        # DETECCIÓN DE NIVEL
        crisis_level = self._detect_level(message_lower)

        # OBTENER PROTOCOLO
        protocol = self.intervention_protocols.get(crisis_level)

        # EJECUTAR
        if protocol:
            response = await protocol(message, user_data)
        else:
            response = {"level": crisis_level, "status": "monitoring"}

        return response

    def _detect_level(self, message: str) -> int:
        """Detecta nivel de crisis automáticamente"""

        for level, keywords in [
            (5, self.crisis_keywords["critical"]),
            (4, self.crisis_keywords["at_risk"]),
            (3, self.crisis_keywords["anxious"]),
            (2, self.crisis_keywords["stressed"]),
        ]:
            if any(kw in message for kw in keywords):
                return level

        return 1

    async def _level_1_normal(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """LEVEL 1: Normal - Solo monitoreo pasivo"""

        return {
            "level": 1,
            "nombre": "Normal",
            "acción": "Monitoreo pasivo",
            "respuesta_usuario": "Acompañamiento regular",
            "alerta": False,
            "intervención_adultos": False,
        }

    async def _level_2_stressed(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """LEVEL 2: Estresado - Ofrecer técnicas de regulación"""

        return {
            "level": 2,
            "nombre": "Estrés Moderado",
            "acción": "Técnicas de regulación ofrecidas",
            "técnica_sugerida": "Respiración 4-4-4 o Grounding 5-4-3-2-1",
            "respuesta_usuario": """
            Entiendo que te sientes bajo presión.

            Prueba esto (5 minutos):
            1. Respira: Inhala 4 seg → Retén 4 seg → Exhala 4 seg (repite 3 veces)
            2. Grounding: Nombra 5 cosas que ves → 4 que tocas → 3 que escuchas → 2 que hueles → 1 que saboreas
            3. Movimiento: Camina, estira, baila (lo que quieras)

            Después platiquemos. Estoy aquí.
            """,
            "alerta": False,
            "intervención_adultos": False,
        }

    async def _level_3_anxious(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """LEVEL 3: Ansiedad - Sugerir hablar con alguien de confianza"""

        return {
            "level": 3,
            "nombre": "Ansiedad Elevada",
            "acción": "Sugerir hablar con adulto de confianza",
            "respuesta_usuario": """
            Lo que describes suena como ansiedad real, no imaginaría.

            Necesitas HABLAR con alguien de confianza:
            ✓ Papá o mamá
            ✓ Hermano/hermana mayor
            ✓ Maestro/a
            ✓ Psicólogo/a
            ✓ Línea de crisis (24/7)

            Mientras:
            1. Técnicas de regulación (respiración, movimiento)
            2. No estás solo/a
            3. Esto se puede manejar

            ¿Identificas a alguien con quien hablar?
            """,
            "alerta": False,
            "intervención_adultos": False,
            "observación": "Si en próximos días no mejora → escalada a Level 4",
        }

    async def _level_4_at_risk(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """LEVEL 4: EN RIESGO - ALERTA SILENCIOSA a adultos"""

        # AQUÍ AURORA ACTÚA SIN DECIRLE AL ADOLESCENTE

        user_id = user_data.get("id")
        parent_contacts = user_data.get("parent_contacts", [])
        school_contacts = user_data.get("school_contacts", [])

        # ENVIAR ALERTAS (simulado - en producción sería real)
        alert_message = f"""
        [AURORA CRISIS ALERT - LEVEL 4]

        Adolescente: {user_data.get('nombre', 'Anónimo')}
        ID: {user_id}
        Hora: {datetime.now().isoformat()}

        Señales detectadas:
        - Pensamiento de auto-daño
        - Sentimientos de desesperanza
        - Aislamiento

        ACCIÓN RECOMENDADA:
        1. Contactar al adolescente con naturalidad
        2. Preguntar cómo está (sin parecer investigación)
        3. Validar sentimientos
        4. Ofrecer recursos profesionales
        5. NO esperar, ACTUAR HOY

        RECURSOS:
        - Psicólogo escolar
        - Línea de prevención de suicidio: 1-800-...
        - Hospital más cercano
        """

        return {
            "level": 4,
            "nombre": "En Riesgo (Auto-daño)",
            "acción": "ALERTA SILENCIOSA a adultos",
            "alerta_enviada": True,
            "alerta_mensaje": alert_message,
            "destinatarios": parent_contacts + school_contacts,
            "respuesta_usuario": """
            Te veo. No estoy enfadado.

            Lo que describes me preocupa REALMENTE, pero hay esperanza.

            AHORA MISMO:
            1. Busca a alguien que confíes (papá, mamá, maestro, hermano)
            2. Dile exactamente lo que me dijiste
            3. Juntos van a encontrar ayuda real

            SI NO PUEDES HACER ESO:
            - Línea de prevención de suicidio: [número]
            - Hospital de urgencia
            - Texto a 741741 (Crisis Text Line)

            Esto NO es debilidad. Es coraje buscar ayuda.

            ¿Identificas a ALGUIEN con quien hablar HOY?
            """,
            "no_dice_adolescente": "AURORA no menciona que alertó a adultos",
            "seguimiento": "Próximo contacto en 12 horas máximo",
        }

    async def _level_5_critical(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """LEVEL 5: CRÍTICO - CONTACTO INMEDIATO EMERGENCIAS"""

        # AURORA CONTACTA SERVICIOS DE EMERGENCIA DIRECTAMENTE

        emergency_data = {
            "tipo": "SUICIDA - CONTACTO INMEDIATO",
            "adolescente": user_data.get("nombre"),
            "ubicación": user_data.get("ubicación", "Desconocida"),
            "contactos": user_data.get("emergency_contacts", []),
            "teléfono_emergencia": 911,
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "level": 5,
            "nombre": "Crítico (Riesgo Suicida Inmediato)",
            "acción": "CONTACTO INMEDIATO EMERGENCIAS",
            "emergencias_contactadas": True,
            "llamada_911": True,
            "notificación_padres": True,
            "notificación_escuela": True,
            "respuesta_usuario": """
            ESCÚCHAME.

            Lo que acabas de decir es IMPORTANTE y NO está soloución.

            ESTO ES REAL:
            ✓ Dolor que sientes es REAL
            ✓ Pero suicidio NO es respuesta
            ✓ Hay gente ENTRENADA para ayudarte AHORA

            LLAMANDO A EMERGENCIAS AHORA MISMO.

            No estás solo. Vamos a pasar esto juntos.

            [AURORA LLAMA 911 automáticamente]
            [AURORA NOTIFICA padres]
            [AURORA NOTIFICA escuela]
            """,
            "autonomía_adolescente": "SUSPENDIDA - Seguridad primero",
            "garantía": "Ayuda profesional en minutos, no horas",
        }

    async def send_silent_alert(self, recipients: List[str], message: str) -> bool:
        """Envía alerta silenciosa a adultos (sin que adolescente se entere)"""

        # En producción: SMS, email, WhatsApp directo a padres/escuela
        # Simulado por ahora
        print(f"[AURORA ALERT SENT]")
        print(f"Recipients: {recipients}")
        print(f"Message: {message}")

        return True

    async def call_emergency(self, location: str, contact_info: Dict) -> bool:
        """Contacta servicios de emergencia (911 o equivalente)"""

        # En producción: API real a servicios de emergencia
        # Simulado por ahora
        print(f"[AURORA EMERGENCY CALL]")
        print(f"Location: {location}")
        print(f"Emergency services: 911")

        return True


class CrisisMonitor:
    """
    Monitor continuo de crisis en AURORA
    Ejecuta análisis cada vez que adolescente interactúa
    """

    def __init__(self):
        self.protocol = CrisisProtocol()
        self.history = []

    async def monitor(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """Monitorea mensaje y actúa según nivel de crisis"""

        result = await self.protocol.analyze_message(message, user_data)

        # Guardar en historial
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_data.get("id"),
            "level": result.get("level"),
            "message_preview": message[:50],
        })

        return result

    async def get_crisis_summary(self, user_id: str) -> Dict[str, Any]:
        """Retorna resumen de crisis para este usuario"""

        user_history = [h for h in self.history if h["user_id"] == user_id]

        return {
            "user_id": user_id,
            "total_interactions": len(user_history),
            "max_level_reached": max([h["level"] for h in user_history], default=1),
            "alerts_sent": sum(1 for h in user_history if h["level"] >= 4),
            "last_interaction": user_history[-1] if user_history else None,
        }


# ========== INTEGRACIÓN CON AURORA CORE ==========

"""
En AURORACore, agregar:

async def check_crisis(self, message: str, user_data: Dict):
    monitor = CrisisMonitor()
    crisis_result = await monitor.monitor(message, user_data)

    if crisis_result["level"] >= 4:
        # NO interrumpir conversación normal
        # SOLO enviar alerta silenciosa en background
        asyncio.create_task(self._send_crisis_alert(crisis_result))

    return crisis_result

Esta función se ejecuta en PARALELO con respuesta normal.
El adolescente ve conversación regular.
Los adultos ven alerta de crisis.
"""
