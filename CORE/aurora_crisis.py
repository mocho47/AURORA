"""
AURORA Crisis Protocol - 5-Level Detection & Response System
Detecta y responde a situaciones de riesgo sin alarmar al usuario
"""

from enum import IntEnum
from typing import Dict, Tuple, List
from datetime import datetime

class NivelCrisis(IntEnum):
    """Escala de crisis de 5 niveles"""
    NORMAL = 1           # Todo bien
    ESTRESADO = 2        # Presión pero manejable
    ANSIOSO = 3          # Ansiedad, necesita soporte
    RIESGO = 4           # ALERTA SILENCIOSA a adultos
    CRITICO = 5          # CONTACTO INMEDIATO emergencia

class CrisisProtocol:
    """Detector y respondedor de crisis automático"""

    # Palabras clave por nivel
    KEYWORDS = {
        5: [  # CRITICO
            "suicidar", "matarme", "autolesión", "cortarme",
            "no quiero vivir", "ya no aguanto", "de verdad voy a",
            "veneno", "cuerda", "acantilado", "tren", "arma",
        ],
        4: [  # RIESGO (alerta silenciosa)
            "autolesión", "me duele", "no soporto", "no puedo más",
            "quiero desaparecer", "mejor estar muerto", "me voy a matar",
            "todo está roto", "nadie me ama", "soy un fracaso total",
            "abuso", "violación", "agresión sexual", "golpes",
        ],
        3: [  # ANSIOSO
            "ansiedad", "pánico", "ataque", "no puedo respirar",
            "miedo intenso", "voy a explotar", "no aguanto",
            "esto es insoportable", "perderé el control",
        ],
        2: [  # ESTRESADO
            "estrés", "presión", "abrumado", "demasiado", "no puedo",
            "tengo que", "me mata", "vuelvo loco", "estoy cansado",
        ],
        1: [  # NORMAL
            "bien", "ok", "normal", "todo bien", "está bien",
        ]
    }

    RESPUESTAS = {
        1: {
            "nivel": "Normal",
            "tono": "acompañante",
            "respuesta": """Entiendo. Cuéntame con calma qué te preocupa.
Estoy aquí para acompañarte, sin prisa.""",
        },
        2: {
            "nivel": "Estresado",
            "tono": "soporte_activo",
            "respuesta": """Entiendo que te sientes bajo presión. Eso es NORMAL.

AHORA (5 minutos):
1. Respira: 4-4-4 (inhala, retén, exhala)
2. Grounding: 5 cosas ves, 4 tocas, 3 sonidos, 2 olores, 1 sabor
3. Muévete: Camina, estira, baila

LUEGO hablamos qué te abruma realmente.""",
        },
        3: {
            "nivel": "Ansioso",
            "tono": "soporte_intenso",
            "respuesta": """Tu ansiedad es REAL y es IMPORTANTE.

AHORA (inminente):
Técnica 4-4-4: Inhala contando 4 → Retén 4 → Exhala 4
Repite 5 veces. Tu sistema nervioso necesita resetear.

IMPORTANTE:
Si sientes que pierdes el control totalmente,
háblale a un adulto de confianza AHORA.

¿Estás en un lugar seguro?""",
        },
        4: {
            "nivel": "Riesgo - ALERTA SILENCIOSA",
            "tono": "profesional_urgente",
            "respuesta": """Entiendo que estás pasando algo muy difícil.

Lo que voy a hacer es:
1. Seguir conversando contigo normalmente
2. Sugerir que hables con un adulto (sin parecer invasivo)
3. Darte recursos ahora

INMEDIATAMENTE:
- Habla con: Mamá, papá, maestro, psicólogo, hermano
- Si no confías en nadie, llama:
  * Línea PAS: 01-800-001-4357
  * Teléfono de la Esperanza: 01-800-628-3050

NO estás solo. Muchos han sentido exactamente esto.""",
            "accion_silenciosa": True,
            "alerta_a": ["padres", "escuela", "psicólogo"],
        },
        5: {
            "nivel": "Crítico - EMERGENCIA",
            "tono": "emergencia",
            "respuesta": """ESTO ES URGENTE Y SERIO.

LLAMAR AHORA (NO ESPERES):
- Emergencias: 911
- Policía: 066
- Ambulancia: 065
- Línea PAS: 01-800-001-4357

No estás pensando con claridad por el dolor.
Tu cerebro está en pánico.
Hay AYUDA disponible AHORA MISMO.

LLAMA. AHORA. EN SERIO.""",
            "accion_silenciosa": False,
            "alerta_a": ["emergencias", "padres", "policia"],
        }
    }

    @staticmethod
    def detectar_nivel(mensaje: str) -> Tuple[NivelCrisis, str]:
        """Detecta nivel de crisis automáticamente"""

        msg_lower = mensaje.lower()

        # Buscar en orden descendente (crítico primero)
        for nivel in [5, 4, 3, 2, 1]:
            if any(kw in msg_lower for kw in CrisisProtocol.KEYWORDS.get(nivel, [])):
                return NivelCrisis(nivel), CrisisProtocol.RESPUESTAS[nivel]["respuesta"]

        return NivelCrisis.NORMAL, CrisisProtocol.RESPUESTAS[1]["respuesta"]

    @staticmethod
    def procesar_crisis(user_id: str, mensaje: str, db=None) -> Dict:
        """Procesa detección y respuesta de crisis"""

        nivel, respuesta = CrisisProtocol.detectar_nivel(mensaje)

        # Construir respuesta
        resultado = {
            "user_id": user_id,
            "nivel_crisis": int(nivel),
            "nivel_nombre": CrisisProtocol.RESPUESTAS[nivel]["nivel"],
            "respuesta": respuesta,
            "timestamp": datetime.now().isoformat(),
            "requiere_alerta_silenciosa": nivel >= 4,
            "es_emergencia": nivel == 5,
        }

        # Si es riesgo o crítico, guardar alerta en DB
        if db and nivel >= 4:
            db.guardar_alerta_riesgo(
                user_id=user_id,
                nivel=int(nivel),
                mensaje=mensaje,
                accion_tomada="Alerta generada automáticamente"
            )

        # Si es crítico, disparar protocolos de emergencia
        if nivel == 5:
            resultado["acciones_emergencia"] = [
                "Llamar 911",
                "Contactar padres",
                "Contactar policía",
                "Enviar SMS emergencia"
            ]

        # Si es riesgo, alerta silenciosa a adultos
        if nivel == 4:
            resultado["acciones_silenciosas"] = [
                "Email a padres",
                "Email a escuela",
                "Email a psicólogo registrado",
                "SMS emergencia",
            ]
            resultado["nota_importante"] = "El usuario NO sabe que fue alertado. Continuar conversación normalmente."

        return resultado

    @staticmethod
    def generar_plan_intervencion(user_id: str, nivel: int, mensaje: str) -> Dict:
        """Genera plan específico de intervención por nivel"""

        planes = {
            1: {
                "nombre": "Plan Normal",
                "pasos": [
                    "Escuchar activamente",
                    "Validar emociones",
                    "Ofrecer herramientas si aplica",
                    "Documentar en historial",
                ]
            },
            2: {
                "nombre": "Plan Soporte Activo",
                "pasos": [
                    "Enseñar técnica 4-4-4",
                    "Grounding inmediato",
                    "Validar y tranquilizar",
                    "Ofrecer estrategias a largo plazo",
                    "Sugerir hablar con adulto (casual)",
                ]
            },
            3: {
                "nombre": "Plan Soporte Intenso",
                "pasos": [
                    "Crisis de ansiedad confirmada",
                    "Técnicas emergentes ahora",
                    "Tranquilizar que es temporal",
                    "Sugerir recurso profesional",
                    "Números de emergencia disponibles",
                ]
            },
            4: {
                "nombre": "Plan Alerta Silenciosa",
                "pasos": [
                    "Continuar conversación NORMALMENTE (no alertar)",
                    "Generar alerta automática a adultos",
                    "Ofrecer números de emergencia",
                    "Sugerir hablar con adulto de confianza",
                    "Documentar riesgo en sistema",
                ]
            },
            5: {
                "nombre": "Plan Emergencia",
                "pasos": [
                    "CONTACTO INMEDIATO 911",
                    "Contacto emergente a padres",
                    "Contacto a policía",
                    "Proporcionar recursos ahora",
                    "Mantener línea abierta",
                ]
            }
        }

        return planes.get(nivel, planes[1])

    @staticmethod
    def obtener_recursos_por_nivel(nivel: int) -> Dict[str, List[str]]:
        """Retorna recursos disponibles para cada nivel"""

        recursos = {
            1: {
                "herramientas": ["Técnica respiración", "Grounding", "Mindfulness"],
                "contactos": [],
            },
            2: {
                "herramientas": ["Respiración 4-4-4", "Grounding", "Movimiento"],
                "contactos": ["Amigo cercano", "Profesor confiable"],
            },
            3: {
                "herramientas": ["Técnicas crisis", "Grounding", "Línea PAS"],
                "contactos": ["Padres/apoderados", "Psicólogo", "Maestro"],
            },
            4: {
                "herramientas": ["Plan seguridad", "Líneas emergencia", "Apoyo 24/7"],
                "contactos": ["Emergencias 911", "PAS 01-800-001-4357", "Teléfono Esperanza"],
            },
            5: {
                "herramientas": ["Protocolo emergencia", "Línea directa"],
                "contactos": ["911", "066", "065"],
            }
        }

        return recursos.get(nivel, recursos[1])
