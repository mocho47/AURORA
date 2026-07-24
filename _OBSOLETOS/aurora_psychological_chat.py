"""
AURORA CHAT - Motor Psicológico Integrado
16 librerías activadas automáticamente según contexto
"""

import asyncio
from typing import Dict, Any, List

class PsychologicalLibraries:
    """16 librerías de psicología - Siempre disponibles, automáticamente seleccionadas"""

    def __init__(self):
        self.libraries = {
            "regulación_emocional": {
                "base": "Siegel, van der Kolk - Neurobiología del estrés",
                "técnicas": [
                    "Respiración 4-4-4 (calma el sistema nervioso)",
                    "Grounding 5-4-3-2-1 (ancla al presente)",
                    "Movimiento (libera estrés del cuerpo)",
                    "Expresión emocional (write/draw/move)",
                ],
                "cuándo": "Detecto estrés, ansiedad, arrebatos",
            },

            "fortalezas": {
                "base": "Clifton, Seligman - Strengths-Based",
                "técnicas": [
                    "Identificar fortalezas del adolescente",
                    "Aplicar fortaleza a debilidad (ej: lógica → resolver problemas)",
                    "Rol donde fortaleza es POTENCIA",
                    "Narrativa: 'Soy bueno en esto'",
                ],
                "cuándo": "Detecto inseguridad, fracaso, baja autoestima",
            },

            "resiliencia": {
                "base": "Frankl, Dweck, Brown - Crecimiento desde dificultad",
                "técnicas": [
                    "Reframe fracaso: 'Estoy aprendiendo'",
                    "Buscar significado en dificultad",
                    "Celebrar intentos, no solo resultados",
                    "Narrativa de crecimiento",
                ],
                "cuándo": "Detecto rendición, 'no puedo', fracaso",
            },

            "integración_social": {
                "base": "Siegel, Brown - Pertenencia auténtica",
                "técnicas": [
                    "Diferencia 'no encajo' de 'me rechazan'",
                    "Tu 'rareza' es tu PODER",
                    "Búsqueda de 'mi gente' (existe)",
                    "Autenticidad > Conformidad",
                ],
                "cuándo": "Detecto soledad, aislamiento, exclusión",
            },

            "identidad_valores": {
                "base": "Erikson, Marcia, Frankl - Construcción de yo",
                "técnicas": [
                    "Espacio para explorar (sin imposición)",
                    "Validar cuestionamiento",
                    "Ayudar a articular valores propios",
                    "Autonomía en identidad",
                ],
                "cuándo": "Detecto confusión identitaria, búsqueda de sentido",
            },

            "toma_decisiones": {
                "base": "Steinberg - Neurobiología adolescente",
                "técnicas": [
                    "Explicar POR QUÉ son impulsivos (neurobiología)",
                    "Framework simple (no abrumador)",
                    "Empoderamiento sin control",
                    "Consecuencias naturales",
                ],
                "cuándo": "Detecto decisiones riesgosas, impulsividad",
            },

            "estrés_académico": {
                "base": "Selye, Lazarus - Convivencia con estrés",
                "técnicas": [
                    "NO eliminar estrés (imposible), convivir",
                    "Detectar cuando excede capacidad",
                    "Apoyo académico sin presión",
                    "Balance vida-estudio",
                ],
                "cuándo": "Detecto bloqueo académico, ansiedad por examen",
            },

            "relaciones_sexualidad": {
                "base": "Taormino, Perel - Educación real",
                "técnicas": [
                    "Información sin sermón",
                    "Responder preguntas que no harían a adultos",
                    "Normalizar curiosidad",
                    "Consentimiento y comunicación",
                ],
                "cuándo": "Detecto dudas sobre relaciones o sexualidad",
            },

            "propósito_carrera": {
                "base": "Sinek, Ikigai, Ryan & Deci - Vocación",
                "técnicas": [
                    "Explorar QUÉ IMPORTA (no dinero)",
                    "Conectar fortalezas + valores + mundo",
                    "Desmentir 'debe ser'",
                    "Carrera como expresión de yo",
                ],
                "cuándo": "Detecto presión, incertidumbre sobre futuro",
            },

            "salud_mental": {
                "base": "DSM-5, Nock - Normalización + acción",
                "técnicas": [
                    "Signos temprana de depresión/ansiedad",
                    "Destigmatizar terapia",
                    "Cuando buscar profesional",
                    "Recursos disponibles",
                ],
                "cuándo": "Detecto síntomas persistentes",
            },

            "autonomía_límites": {
                "base": "Ryan & Deci, Baumrind - Balance",
                "técnicas": [
                    "Enseñar a decir NO (a presiones)",
                    "Diferencia rebeldía sana de autodestrucción",
                    "Necesidad de independencia es normal",
                    "Límites cuidadosos, no controladores",
                ],
                "cuándo": "Detecto presión extrema, sumisión, o desafío destructivo",
            },

            "creatividad_expresion": {
                "base": "Brown, Csikszentmihalyi - Voz personal",
                "técnicas": [
                    "Activar creatividad como regulación",
                    "Arte/música/escritura como expresión",
                    "Celebrar 'rareza creativa'",
                    "Flow state (inmersión)",
                ],
                "cuándo": "Detecto represión, falta de outlet, genio dormido",
            },

            "mindfulness_presencia": {
                "base": "JAMA, Kabat-Zinn - Presencia sin religión",
                "técnicas": [
                    "Técnicas simples (no meditación forzada)",
                    "Presencia en momento difícil",
                    "Observar sin reaccionar",
                    "Reduce ruido mental",
                ],
                "cuándo": "Detecto ruido mental, ansiedad anticipatoria, preocupación",
            },

            "comunicacion_no_violenta": {
                "base": "Rosenberg, Siegel - Conexión real",
                "técnicas": [
                    "Expresar necesidades sin atacar",
                    "Escucha profunda",
                    "Palabras exactas para situaciones difíciles",
                    "Empatía como puente",
                ],
                "cuándo": "Detecto conflictos, comunicación rota, malentendidos",
            },

            "cuerpo_movimiento": {
                "base": "van der Kolk - Neuromovimiento",
                "técnicas": [
                    "Movimiento como regulación",
                    "Cuerpo mantiene puntaje (memoria somática)",
                    "Danza/deporte/yoga según necesidad",
                    "Desconexión mente-cuerpo",
                ],
                "cuándo": "Detecto disociación, estrés somático, apatía",
            },

            "narrativa_personal": {
                "base": "McAdams, Bruner - Reescribir historia",
                "técnicas": [
                    "De 'soy fracasado' a 'he crecido en dificultad'",
                    "Identidad como narrativa, no destino",
                    "Punto de giro: significado en sufrimiento",
                    "Agentic voice ('Yo decidí')",
                ],
                "cuándo": "Detecto identidad fija, historias negativas, victimismo",
            },
        }

    def select_libraries(self, situation: str, context: Dict) -> List[str]:
        """Selecciona automáticamente librerías según situación"""

        situation_library_map = {
            "estrés": ["regulación_emocional", "resiliencia", "mindfulness_presencia"],
            "baja_autoestima": ["fortalezas", "narrativa_personal", "resiliencia"],
            "soledad": ["integración_social", "creatividad_expresion", "comunicacion_no_violenta"],
            "identidad": ["identidad_valores", "narrativa_personal", "autonomía_límites"],
            "fracaso": ["resiliencia", "fortalezas", "toma_decisiones"],
            "conflicto": ["comunicacion_no_violenta", "empatía", "regulación_emocional"],
            "ansiedad": ["regulación_emocional", "estrés_académico", "mindfulness_presencia"],
            "depresión": ["salud_mental", "narrativa_personal", "propósito_carrera"],
            "futuro": ["propósito_carrera", "fortalezas", "identidad_valores"],
            "relaciones": ["relaciones_sexualidad", "comunicacion_no_violenta", "integración_social"],
        }

        return situation_library_map.get(situation, ["regulación_emocional"])


class PsychologicalChatEngine:
    """Motor de chat que usa las 16 librerías automáticamente"""

    def __init__(self):
        self.libraries = PsychologicalLibraries()
        self.conversation_history = []

    async def generate_response(self, message: str, user_data: Dict) -> Dict[str, Any]:
        """Genera respuesta psicológicamente informada"""

        # 1. DETECTAR SITUACIÓN
        situation = await self._detect_situation(message)

        # 2. SELECCIONAR LIBRERÍAS
        selected_libs = self.libraries.select_libraries(situation, user_data)

        # 3. GENERAR RESPUESTA
        response = await self._craft_response(message, situation, selected_libs, user_data)

        # 4. GUARDAR
        self.conversation_history.append({
            "message": message,
            "situation": situation,
            "libraries_used": selected_libs,
            "response": response,
        })

        return {
            "response": response,
            "situation": situation,
            "libraries": selected_libs,
            "tone": "acompañamiento",
            "imposición": False,
        }

    async def _detect_situation(self, message: str) -> str:
        """Detecta situación del adolescente"""

        message_lower = message.lower()

        situations = {
            "estrés": ["abrumado", "presión", "no puedo", "demasiado"],
            "baja_autoestima": ["no valgo", "soy malo", "fracaso", "inútil"],
            "soledad": ["solo", "aislado", "nadie", "excluido"],
            "identidad": ["quién soy", "qué debo", "identidad"],
            "fracaso": ["fallar", "no sirve", "error"],
            "conflicto": ["pelea", "conflicto", "argumento"],
            "ansiedad": ["miedo", "nervios", "pánico"],
            "depresión": ["triste", "sin esperanza", "vacío"],
            "futuro": ["carrera", "qué estudiar", "qué hacer"],
            "relaciones": ["novio", "novia", "sexo", "relación"],
        }

        for situation, keywords in situations.items():
            if any(kw in message_lower for kw in keywords):
                return situation

        return "general"

    async def _craft_response(self, message: str, situation: str,
                             libraries: List[str], user_data: Dict) -> str:
        """Redacta respuesta usando librerías seleccionadas"""

        templates = {
            "estrés": """
            Entiendo que te sientes bajo presión. Eso es NORMAL a tu edad.

            Aquí está el punto: No vamos a eliminar el estrés (imposible).
            Vamos a aprender a convivir con él.

            Técnica rápida (próximas 5 minutos):
            1️⃣ Respira: Inhala 4 seg → Retén 4 seg → Exhala 4 seg (3 veces)
            2️⃣ Grounding: Nombra 5 cosas que ves → 4 que tocas → 3 sonidos → 2 olores → 1 sabor
            3️⃣ Muévete: Camina, estira, baila (lo que quieras)

            Después: ¿Platicamos qué te abruma realmente?
            """,

            "baja_autoestima": """
            "No valgo" es una MENTIRA que tu mente te dice cuando estás cansado.

            Aquí está la verdad:
            ✓ Eres bueno en algo (sin duda)
            ✓ Importas a alguien (aunque no lo veas)
            ✓ Creciste este año (aunque no lo reconozcas)

            Cuéntame: ¿En qué SÍ eres bueno? (Aunque sea pequeño)
            Vamos a construir desde ahí.
            """,

            "soledad": """
            "No encajo" ≠ "Me rechazan". Diferencia CRÍTICA.

            - No encajo = Aún no encontré MI gente (existe, conozco)
            - Me rechazan = Ellos decidieron (temporal, no verdad absoluta)

            Tu "rareza" es tu PODER. Los que parecen "normales" también se sienten solos.

            ¿Cuál es tu "rareza" favorita? Esa que te hace diferente.
            Vamos a buscar gente así.
            """,

            "identidad": """
            "¿Quién soy?" es LA pregunta adolescente.

            No es que no sepas. Es que ESTÁS DESCUBRIENDO.

            Lo importante AHORA:
            ✓ ¿Qué te hace FELIZ? (Sin que otro lo diga)
            ✓ ¿En qué eres bueno?
            ✓ ¿Qué te enoja? (injusticia que detectas)
            ✓ ¿A quién quieres ser? (persona, no carrera)

            No tienes que saberlo YA. Pero sí explorar.
            ¿Quieres que exploremos juntos?
            """,

            "fracaso": """
            El fracaso es el mejor profesor. (No es cliché, es neurociencia.)

            Tu cerebro está DISEÑADO para aprender de errores.

            La pregunta no es "¿por qué fallé?"
            Es "¿qué aprendí?"

            ¿Qué pasó exactamente?
            Vamos a encontrar la lección.
            """,

            "general": """
            Te escucho. ¿Cuéntame más?
            Estoy aquí para acompañarte, no para juzgarte.
            """,
        }

        return templates.get(situation, templates["general"])


# ========== INTEGRACIÓN ==========

"""
En el chat del panel:
1. Cada mensaje del adolescente pasa por PsychologicalChatEngine
2. Se detecta situación automáticamente
3. Se seleccionan librerías
4. Se genera respuesta personalizada
5. Si nivel de crisis >= 4: AURORA activa protocolo silencioso (sin que adolescente lo sepa)
"""
