"""
AURORA - ARQUITECTURA UNIFICADA
Ecosistema integrado: Negocios + Educativo + Psicológico
Autonomía total, sin censura, lo mejor disponible siempre
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

class AURORARole(Enum):
    """6 roles integrados en AURORA"""
    TEEN = "teen"  # Adolescente (desarrollo humano)
    MAESTRO = "maestro"  # Maestro (admin + dinámicas)
    PADRE = "padre"  # Padre (escuela para padres)
    VENDEDOR = "vendedor"  # Vendedor (cotizador negocios)
    ADMIN = "admin"  # Admin (pedidos, finanzas)
    USUARIO_GENERAL = "usuario_general"  # Acceso limitado

class AURORACore:
    """
    AURORA Core: Cerebro unificado

    Contiene:
    1. 16 Librerías psicológicas (siempre activas)
    2. 6 Dinámicas educativas
    3. Sistema de cotización con 60+ productos
    4. Sistema de acompañamiento psicológico
    5. Detección de crisis
    6. Personalización extrema
    """

    def __init__(self):
        self.role = None
        self.user_id = None
        self.context = {}
        self.personality_profile = {}
        self.situation_detector = SituationDetector()
        self.library_selector = LibrarySelector()
        self.autonomy_level = "TOTAL"  # Sin restricciones

    async def process_interaction(self, message: str, role: AURORARole, user_data: Dict) -> Dict[str, Any]:
        """
        Procesa cualquier interacción en AURORA

        1. Detecta situación (negocio, educativa, psicológica)
        2. Selecciona librería apropiada
        3. Genera respuesta personalizada
        4. Registra para aprendizaje
        """

        self.role = role
        self.user_id = user_data.get('id')
        self.context = user_data

        # PASO 1: DETECCIÓN DE SITUACIÓN
        situation = await self.situation_detector.detect(message, role, user_data)

        # PASO 2: SELECCIÓN DE LIBRERÍA
        libraries = self.library_selector.select(situation, user_data)

        # PASO 3: GENERACIÓN DE RESPUESTA
        response = await self._generate_response(
            message=message,
            situation=situation,
            libraries=libraries,
            role=role,
            user_data=user_data
        )

        # PASO 4: REGISTRO
        await self._log_interaction(message, response, situation, libraries)

        return response

    async def _generate_response(self, message: str, situation: Dict,
                                libraries: List[str], role: AURORARole,
                                user_data: Dict) -> Dict[str, Any]:
        """Genera respuesta basada en librería seleccionada"""

        responses = {
            AURORARole.TEEN: await self._teen_response(message, libraries, user_data),
            AURORARole.MAESTRO: await self._maestro_response(message, libraries, user_data),
            AURORARole.PADRE: await self._padre_response(message, libraries, user_data),
            AURORARole.VENDEDOR: await self._vendedor_response(message, libraries, user_data),
            AURORARole.ADMIN: await self._admin_response(message, libraries, user_data),
        }

        return responses.get(role, {})

    async def _teen_response(self, message: str, libraries: List[str],
                            user_data: Dict) -> Dict[str, Any]:
        """Respuesta para adolescente: acompañamiento psicológico"""

        # Detectar estado emocional
        emotional_state = self._detect_emotional_state(message)

        # Seleccionar técnica
        if "estrés" in emotional_state or "ansiedad" in emotional_state:
            technique = "regulación_emocional"
        elif "identidad" in message.lower() or "quien soy" in message.lower():
            technique = "exploración_identidad"
        elif "soledad" in emotional_state or "no encajo" in message.lower():
            technique = "integración_social"
        else:
            technique = "resiliencia"

        return {
            "role": "TEEN",
            "tipo": "acompañamiento_psicológico",
            "emotional_state": emotional_state,
            "technique": technique,
            "content": self._generate_teen_content(message, technique, user_data),
            "autonomía": "RESPETA_AUTONOMÍA",
            "imposición": False,
            "crisis_detected": self._check_crisis(message),
        }

    async def _maestro_response(self, message: str, libraries: List[str],
                               user_data: Dict) -> Dict[str, Any]:
        """Respuesta para maestro: admin + dinámicas + alertas"""

        return {
            "role": "MAESTRO",
            "tipo": "administración_educativa",
            "admin_suggestencias": self._get_admin_suggestions(user_data),
            "dinámicas_disponibles": self._get_applicable_dynamics(message, user_data),
            "alertas": self._detect_student_risks(user_data),
            "recursos": self._get_educational_resources(message),
            "reportes": self._generate_reports(user_data),
        }

    async def _padre_response(self, message: str, libraries: List[str],
                             user_data: Dict) -> Dict[str, Any]:
        """Respuesta para padre: escuela para padres (invisible)"""

        # AURORA detecta qué necesita el padre SIN que lo pida
        detected_need = self._detect_parent_need(user_data)

        return {
            "role": "PADRE",
            "tipo": "escuela_para_padres_invisible",
            "opción_1": self._parent_option_1(detected_need),
            "opción_2": self._parent_option_2(detected_need),
            "no_obligatorio": True,
            "sin_imposición": True,
            "información_útil": True,
        }

    async def _vendedor_response(self, message: str, libraries: List[str],
                                user_data: Dict) -> Dict[str, Any]:
        """Respuesta para vendedor: cotizaciones + análisis"""

        cotización = self._process_cotization(message, user_data)

        return {
            "role": "VENDEDOR",
            "tipo": "cotización",
            "producto": cotización.get("producto"),
            "cantidad": cotización.get("cantidad"),
            "precio_unitario": cotización.get("precio_unitario"),
            "costo": cotización.get("costo"),
            "ganancia": cotización.get("ganancia"),
            "margen": cotización.get("margen"),
            "cotización_id": cotización.get("id"),
        }

    async def _admin_response(self, message: str, libraries: List[str],
                             user_data: Dict) -> Dict[str, Any]:
        """Respuesta para admin: pedidos + finanzas + reportes"""

        return {
            "role": "ADMIN",
            "tipo": "administración",
            "pedidos": self._get_pending_orders(user_data),
            "finanzas": self._get_financial_summary(user_data),
            "alertas": self._get_admin_alerts(user_data),
            "reportes": self._generate_admin_reports(user_data),
        }

    def _detect_emotional_state(self, message: str) -> str:
        """Detecta estado emocional del adolescente"""
        keywords = {
            "estrés": ["estrés", "presión", "abrumado", "no puedo"],
            "ansiedad": ["ansiedad", "miedo", "nervios", "pánico"],
            "soledad": ["solo", "aislado", "nadie me entiende", "no encajo"],
            "identidad": ["quién soy", "identidad", "no sé qué hacer"],
            "dolor": ["duele", "triste", "depre", "muerte"],
        }

        for estado, palabras in keywords.items():
            if any(palabra in message.lower() for palabra in palabras):
                return estado

        return "neutral"

    def _check_crisis(self, message: str) -> bool:
        """Detecta si hay crisis (pensamiento de auto-daño)"""
        crisis_keywords = [
            "quiero morir", "no quiero vivir", "me lastimo",
            "suicidio", "me corto", "no sirvo", "nadie me quiere"
        ]
        return any(keyword in message.lower() for keyword in crisis_keywords)

    def _generate_teen_content(self, message: str, technique: str,
                              user_data: Dict) -> str:
        """Genera contenido personalizado para adolescente"""

        name = user_data.get("nombre", "")
        age = user_data.get("edad", 15)

        # Contenido basado en técnica
        content_templates = {
            "regulación_emocional": f"""
            Entiendo que te sientes abrumado. Eso es NORMAL a tu edad.

            Aquí hay una técnica rápida (5-3 minutos):

            1. Respira: Inhala 4 seg, retén 4, exhala 4 (3 veces)
            2. Grounding: Toca 5 cosas → Mira 4 colores → Escucha 3 sonidos → Prueba 2 sabores → Huele 1 aroma
            3. Movimiento: Camina, baila o estira (lo que quieras)

            Tu cerebro está en "huida o pelea". Vamos a llevarlo a "seguridad".

            ¿Necesitas que hablemos más después?
            """,

            "exploración_identidad": f"""
            La pregunta "¿quién soy?" es LA pregunta adolescente.

            No es que no sepas. Es que ESTÁS DESCUBRIENDO.

            Lo que importa ahora:
            ✓ ¿Qué te hace FELIZ (sin que otro lo diga)?
            ✓ ¿En qué eres bueno (mejor que otros)?
            ✓ ¿Qué te enoja (injusticia que detectas)?
            ✓ ¿A quién quieres ser? (persona, no carrera)

            No tienes que saberlo YA. Pero sí explorar.

            ¿Quieres que exploremos juntos?
            """,

            "integración_social": f"""
            "No encajo" ≠ "Me rechazan"

            Diferencia CRÍTICA:
            - No encajo = Aún no encontré MI gente (existe, conozco)
            - Me rechazan = Ellos decidieron (temporal, no verdad)

            Tu "rareza" es tu PODER. Solo que no lo ves aún.

            Los que parecen "normales" también se sienten solos.

            ¿Cuál es tu "rareza" favorita? (Cuéntame)
            """,
        }

        return content_templates.get(technique, "Te escucho.")

    def _detect_parent_need(self, user_data: Dict) -> str:
        """Detecta qué NECESITA el padre sin que lo pida"""

        student_data = user_data.get("student_data", {})

        if student_data.get("ansiedad_detected"):
            return "ansiedad"
        elif student_data.get("aislamiento_detected"):
            return "aislamiento"
        elif student_data.get("bajo_desempeño"):
            return "académico"
        elif student_data.get("conflicto_familiar"):
            return "comunicación"

        return "general"

    def _parent_option_1(self, need: str) -> Dict[str, str]:
        """Primera opción para padre (invisible)"""
        options = {
            "ansiedad": {"tipo": "audio", "titulo": "Entender la ansiedad adolescente (10 min)"},
            "aislamiento": {"tipo": "artículo", "titulo": "Cuando el adolescente se aísla (lectura)"},
            "académico": {"tipo": "guía", "titulo": "Apoyo sin presión (paso a paso)"},
            "comunicación": {"tipo": "video", "titulo": "Comunicación sin culpa (5 min)"},
        }
        return options.get(need, {"tipo": "info", "titulo": "Recursos para padres"})

    def _parent_option_2(self, need: str) -> Dict[str, str]:
        """Segunda opción para padre (invisible)"""
        options = {
            "ansiedad": {"tipo": "técnica", "titulo": "Cómo calmar sin sermones"},
            "aislamiento": {"tipo": "actividad", "titulo": "Actividades que reconecten"},
            "académico": {"tipo": "estrategia", "titulo": "Mentoría natural"},
            "comunicación": {"tipo": "diálogo", "titulo": "Preguntas que abren conversación"},
        }
        return options.get(need, {"tipo": "recurso", "titulo": "Más información"})

    def _process_cotization(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """Procesa cotización de productos"""

        # Simulado - en producción integraría con catálogo real
        return {
            "producto": "Ejemplo",
            "cantidad": 1,
            "precio_unitario": 100,
            "costo": 50,
            "ganancia": 50,
            "margen": "50%",
            "id": f"COT-{datetime.now().strftime('%Y%m%d')}-001",
        }

    def _get_applicable_dynamics(self, message: str, user_data: Dict) -> List[str]:
        """Retorna dinámicas aplicables para maestro"""

        return [
            "Reto de 72 horas",
            "Experto por un día",
            "Debate estructurado",
            "Proyecto de impacto",
            "Círculo de confianza",
            "Mentoría inversa",
        ]

    def _detect_student_risks(self, user_data: Dict) -> List[str]:
        """Detecta riesgos en estudiantes"""

        alerts = []

        # Simulado - en producción usaría datos reales
        if user_data.get("faltas_aumentadas"):
            alerts.append("Aumento en ausencias")

        if user_data.get("tareas_no_entregadas"):
            alerts.append("Tareas incompletas")

        return alerts

    def _get_educational_resources(self, message: str) -> Dict[str, Any]:
        """Retorna recursos educativos para tema"""

        return {
            "libro_texto": "Fragmento relevante",
            "ejercicio": "Práctica sugerida",
            "vinculación": "Conexión a vida real",
            "dinámica": "Aplicable en clase",
        }

    async def _log_interaction(self, message: str, response: Dict,
                              situation: Dict, libraries: List[str]):
        """Registra interacción para aprendizaje"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id,
            "role": self.role.value if self.role else None,
            "message": message[:100],  # Primeros 100 caracteres
            "situation": situation,
            "libraries_used": libraries,
            "response_type": response.get("tipo"),
        }

        # En producción: guardar en base de datos
        print(f"[LOG] {log_entry}")


class SituationDetector:
    """Detecta tipo de situación (negocio, educativa, psicológica)"""

    async def detect(self, message: str, role, user_data: Dict) -> Dict[str, str]:

        message_lower = message.lower()

        # DETECCIÓN AUTOMÁTICA
        if any(word in message_lower for word in ["precio", "costo", "cotiza", "producto"]):
            return {"tipo": "negocio", "subtipo": "cotización"}

        elif any(word in message_lower for word in ["clase", "materia", "tarea", "examen"]):
            return {"tipo": "educativa", "subtipo": "académico"}

        elif any(word in message_lower for word in ["estrés", "ansiedad", "triste", "solo"]):
            return {"tipo": "psicológico", "subtipo": "emocional"}

        else:
            return {"tipo": "general", "subtipo": "consulta"}


class LibrarySelector:
    """Selecciona librerías según situación"""

    def select(self, situation: Dict, user_data: Dict) -> List[str]:

        tipo = situation.get("tipo")

        libraries_map = {
            "negocio": ["cotización", "finanzas"],
            "educativa": ["pedagogía", "dinámicas"],
            "psicológico": ["regulación_emocional", "resiliencia", "integración_social"],
            "general": ["acompañamiento", "orientación"],
        }

        return libraries_map.get(tipo, ["general"])


# ========== INICIALIZACIÓN ==========

async def main():
    """Test AURORA Core"""

    aurora = AURORACore()

    # Ejemplo Teen
    teen_response = await aurora.process_interaction(
        message="Me siento solo en la escuela, no encajo",
        role=AURORARole.TEEN,
        user_data={
            "id": "teen_001",
            "nombre": "Juan",
            "edad": 15,
            "escuela": "Secundaria",
        }
    )

    print("\n=== RESPUESTA AURORA TEEN ===")
    print(json.dumps(teen_response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
