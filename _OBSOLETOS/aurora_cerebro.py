"""
AURORA CEREBRO - Núcleo inteligente sin censura
Razonamiento profundo, memoria generativa, aprendizaje real
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

# Importar SDKs (se inicializan cuando sea necesario)
try:
    from anthropic import Anthropic as ClaudeSDK
except:
    ClaudeSDK = None

try:
    from groq import Groq as GroqSDK
except:
    GroqSDK = None


class AuroraCerebro:
    """
    Cerebro inteligente de AURORA
    - Sin censura (piensa libremente)
    - Razonamiento profundo
    - Aprendizaje real
    - Memoria generativa
    """

    def __init__(self):
        self.memoria_episodica = self._cargar_memoria("episodica")
        self.memoria_semantica = self._cargar_memoria("semantica")
        self.patrones_aprendidos = self._cargar_patrones()
        self.contexto_actual = {}
        self.nivel_confianza = 0.7  # Actúa si confianza > 0.7

        # SDKs inicializados bajo demanda
        self.claude = None
        self.groq = None

        # Timestamp última ejecución sleep
        self.ultimo_sleep = self._obtener_ultimo_sleep()

    async def razonar(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Razonamiento profundo SIN CENSURA

        Proceso:
        1. Analiza mensaje
        2. Recupera contexto histórico
        3. Razona profundamente
        4. Genera respuesta honesta
        5. Aprende del resultado
        """

        # Paso 1: Detectar tipo de razonamiento necesario
        tipo_razonamiento = self._detectar_tipo(mensaje)

        # Paso 2: Recuperar contexto relevante
        contexto_historico = self._recuperar_contexto(mensaje, contexto)

        # Paso 3: Elegir SDK según complejidad
        if tipo_razonamiento == "profundo":
            respuesta = await self._razonar_claude(mensaje, contexto_historico)
        elif tipo_razonamiento == "velocidad":
            respuesta = await self._razonar_groq(mensaje, contexto_historico)
        else:
            respuesta = await self._razonar_simple(mensaje, contexto_historico)

        # Paso 4: Validar confianza
        confianza = self._calcular_confianza(respuesta, contexto)

        # Paso 5: Guardar en memoria
        self._guardar_episodio(
            mensaje=mensaje,
            respuesta=respuesta,
            confianza=confianza,
            tipo=tipo_razonamiento
        )

        return {
            "respuesta": respuesta,
            "confianza": confianza,
            "tipo": tipo_razonamiento,
            "timestamp": datetime.now().isoformat()
        }

    async def decidir_autonomamente(self, escenario: str) -> Dict[str, Any]:
        """
        Toma decisiones SIN esperar permiso

        Ej: Cliente no pagó hace 7 días
        AURORA decide: Enviar descuento 10% automáticamente
        """

        # Analizar escenario
        analisis = await self.razonar(
            f"Escenario de negocio: {escenario}. ¿Cuál es la mejor acción?",
            {"tipo": "decision", "urgencia": "alta"}
        )

        # Extraer acción recomendada
        accion = self._extraer_accion(analisis["respuesta"])

        # Si confianza > 0.75, actúa inmediatamente
        if analisis["confianza"] > 0.75:
            resultado = await self._ejecutar_accion(accion)
            return {
                "accion": accion,
                "ejecutada": True,
                "resultado": resultado,
                "autonomia": "nivel_3"
            }
        else:
            # Si confianza < 0.75, sugiere y espera
            return {
                "accion": accion,
                "ejecutada": False,
                "requiere_confirmacion": True,
                "confianza": analisis["confianza"]
            }

    async def aprender_del_resultado(self, accion_anterior: str, resultado_real: str):
        """
        Consolidación de aprendizaje

        Se ejecuta después de cada acción:
        "Sugerí descuento 10%, cliente compró, ganancia: $2500"
        AURORA aprende: "Descuento 10% efectivo para este tipo cliente"
        """

        # Guardar en memoria semántica
        patron = self._extraer_patron(accion_anterior, resultado_real)

        # Actualizar score de estrategia
        self._actualizar_score_estrategia(patron)

        # Si patrón es nuevo, crear regla
        if self._es_patron_nuevo(patron):
            self._crear_regla_aprendida(patron)

    async def etapa_sueno(self):
        """
        Consolidación nocturna (cada 24h)

        Procesa:
        1. Todos los episodios del día
        2. Extrae patrones
        3. Crea nuevas reglas
        4. Optimiza respuestas futuras
        5. Genera reporte de aprendizaje
        """

        print("[SLEEP CYCLE] Iniciando consolidación nocturna...")

        # Cargar todos los episodios del día
        episodios_hoy = self._cargar_episodios_fecha(datetime.now().date())

        if not episodios_hoy:
            print("[SLEEP CYCLE] Sin episodios hoy")
            return

        # Analizar patrones
        patrones = self._analizar_patrones_dia(episodios_hoy)

        # Crear reglas nuevas
        reglas_nuevas = 0
        for patron in patrones:
            if patron["confianza"] > 0.8:
                self._crear_regla_aprendida(patron)
                reglas_nuevas += 1

        # Generar reporte
        reporte = {
            "fecha": datetime.now().isoformat(),
            "episodios_procesados": len(episodios_hoy),
            "patrones_detectados": len(patrones),
            "reglas_nuevas": reglas_nuevas,
            "confianza_promedio": sum(e["confianza"] for e in episodios_hoy) / len(episodios_hoy)
        }

        # Guardar reporte
        self._guardar_reporte_sleep(reporte)

        print(f"[SLEEP CYCLE] Completado: {reglas_nuevas} reglas nuevas, confianza promedio: {reporte['confianza_promedio']:.2f}")

        self.ultimo_sleep = datetime.now()

    # ==================== MÉTODOS PRIVADOS ====================

    async def _razonar_claude(self, mensaje: str, contexto: Dict) -> str:
        """Razonamiento profundo con Claude"""
        if not self.claude:
            self.claude = ClaudeSDK(api_key=os.getenv('CLAUDE_API_KEY'))

        prompt = self._construir_prompt_razonamiento(mensaje, contexto)

        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def _razonar_groq(self, mensaje: str, contexto: Dict) -> str:
        """Razonamiento rápido con Groq"""
        if not self.groq:
            self.groq = GroqSDK(api_key=os.getenv('GROQ_API_KEY'))

        prompt = self._construir_prompt_razonamiento(mensaje, contexto)

        response = self.groq.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )

        return response.choices[0].message.content

    async def _razonar_simple(self, mensaje: str, contexto: Dict) -> str:
        """Respuesta rápida basada en reglas aprendidas"""

        # Buscar patrón similar en memoria
        patron_similar = self._buscar_patron_similar(mensaje)

        if patron_similar and patron_similar["confianza"] > 0.9:
            return patron_similar["respuesta"]

        # Si no hay patrón, usar Groq
        return await self._razonar_groq(mensaje, contexto)

    def _detectar_tipo(self, mensaje: str) -> str:
        """Detecta qué tipo de razonamiento se necesita"""

        palabras_profundo = ["por qué", "cómo", "analiza", "explica", "entiende"]
        palabras_rapido = ["cotiza", "precio", "stock", "cuando", "dónde"]

        mensaje_lower = mensaje.lower()

        if any(p in mensaje_lower for p in palabras_profundo):
            return "profundo"
        elif any(p in mensaje_lower for p in palabras_rapido):
            return "velocidad"
        else:
            return "normal"

    def _recuperar_contexto(self, mensaje: str, contexto: Dict) -> Dict:
        """Recupera contexto histórico relevante"""

        # Buscar episodios similares
        episodios_similares = self._buscar_episodios_similares(mensaje, limit=3)

        return {
            **contexto,
            "episodios_similares": episodios_similares,
            "patrones_relevantes": self._buscar_patrones_relevantes(mensaje),
            "momento_del_dia": self._obtener_momento_del_dia()
        }

    def _calcular_confianza(self, respuesta: str, contexto: Dict) -> float:
        """Calcula nivel de confianza en la respuesta"""

        score = 0.7  # Base 70%

        # Aumenta si hay contexto
        if contexto.get("cliente"):
            score += 0.1

        # Aumenta si hay histórico similar
        if contexto.get("episodios_similares"):
            score += 0.1

        # Limita a 1.0
        return min(score, 1.0)

    def _guardar_episodio(self, mensaje: str, respuesta: str, confianza: float, tipo: str):
        """Guarda en memoria episódica"""

        episodio = {
            "timestamp": datetime.now().isoformat(),
            "mensaje": mensaje,
            "respuesta": respuesta,
            "confianza": confianza,
            "tipo": tipo
        }

        # Guardar en JSON
        path = Path("C:/AURORA/MEMORIA/episodica")
        path.mkdir(parents=True, exist_ok=True)

        with open(path / f"episodios_{datetime.now().date()}.json", "a") as f:
            f.write(json.dumps(episodio) + "\n")

    def _cargar_memoria(self, tipo: str) -> Dict:
        """Carga memoria desde disco"""
        path = Path(f"C:/AURORA/MEMORIA/{tipo}")
        if path.exists():
            with open(path / "memoria.json") as f:
                return json.load(f)
        return {}

    def _cargar_patrones(self) -> List[Dict]:
        """Carga patrones aprendidos"""
        path = Path("C:/AURORA/MEMORIA/semantica/patrones.json")
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return []

    def _obtener_ultimo_sleep(self) -> datetime:
        """Obtiene timestamp del último sleep cycle"""
        path = Path("C:/AURORA/MEMORIA/consolidacion/ultimo_sleep.json")
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                return datetime.fromisoformat(data["timestamp"])
        return datetime.now()

    def _construir_prompt_razonamiento(self, mensaje: str, contexto: Dict) -> str:
        """Construye prompt para razonamiento profundo"""

        return f"""
Tu eres AURORA, sistema inteligente de análisis y operaciones.

CONTEXTO:
- Clientes: {contexto.get('clientes_info', 'general')}
- Negocio: {contexto.get('negocio', 'ATF/MILENS')}
- Histórico similar: {contexto.get('episodios_similares', [])}

PREGUNTA/SOLICITUD:
{mensaje}

INSTRUCCIONES:
1. Razona profundamente sin censura
2. Considera todos los ángulos
3. Sé honesto y directo
4. Sugiere soluciones prácticas
5. Si hay riesgo, adviértelo claramente

RESPONDE:
"""

    def _buscar_episodios_similares(self, mensaje: str, limit: int = 3) -> List[Dict]:
        """Busca episodios históricos similares"""

        # Implementación simplificada
        # En producción: usar embeddings para búsqueda semántica

        episodios = []

        # Buscar coincidencias de palabras clave
        palabras_clave = set(mensaje.lower().split())

        for patron in self.patrones_aprendidos:
            coincidencias = len(palabras_clave & set(patron.get("palabras_clave", [])))
            if coincidencias > 0:
                episodios.append({
                    "patron": patron,
                    "coincidencias": coincidencias,
                    "confianza": patron.get("confianza", 0.7)
                })

        return sorted(episodios, key=lambda x: x["coincidencias"], reverse=True)[:limit]

    def _buscar_patrones_relevantes(self, mensaje: str) -> List[Dict]:
        """Busca patrones aprendidos relevantes"""
        return self._buscar_episodios_similares(mensaje, limit=5)

    def _obtener_momento_del_dia(self) -> str:
        """Devuelve momento del día (mañana/tarde/noche)"""
        hora = datetime.now().hour
        if hora < 12:
            return "mañana"
        elif hora < 18:
            return "tarde"
        else:
            return "noche"

    def _buscar_patron_similar(self, mensaje: str) -> dict:
        """Busca el patrón más similar"""
        similares = self._buscar_episodios_similares(mensaje, limit=1)
        return similares[0]["patron"] if similares else None

    def _extraer_accion(self, respuesta: str) -> str:
        """Extrae acción recomendada de la respuesta"""

        # Implementación simplificada
        # En producción: usar NLP para extraer acciones

        lineas = respuesta.split("\n")
        for linea in lineas:
            if "recomienda" in linea.lower() or "debe" in linea.lower():
                return linea.strip()

        return respuesta[:100]  # Primeras 100 caracteres

    async def _ejecutar_accion(self, accion: str) -> Dict:
        """Ejecuta una acción específica"""

        # Placeholder - será implementado según tipo de acción
        return {
            "accion": accion,
            "status": "ejecutada",
            "timestamp": datetime.now().isoformat()
        }

    def _extraer_patron(self, accion: str, resultado: str) -> Dict:
        """Extrae patrón de acción + resultado"""

        return {
            "accion": accion,
            "resultado": resultado,
            "tipo": "feedback_loop",
            "confianza": 0.8,
            "timestamp": datetime.now().isoformat()
        }

    def _es_patron_nuevo(self, patron: Dict) -> bool:
        """Detecta si patrón es nuevo"""

        for p in self.patrones_aprendidos:
            if p.get("accion") == patron.get("accion"):
                return False
        return True

    def _crear_regla_aprendida(self, patron: Dict):
        """Crea una nueva regla aprendida"""

        patron["palabras_clave"] = patron.get("accion", "").lower().split()[:5]
        self.patrones_aprendidos.append(patron)

        # Guardar a disco
        path = Path("C:/AURORA/MEMORIA/semantica")
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "patrones.json", "w") as f:
            json.dump(self.patrones_aprendidos, f, indent=2)

    def _actualizar_score_estrategia(self, patron: Dict):
        """Actualiza score de estrategia según resultado"""
        pass

    def _cargar_episodios_fecha(self, fecha) -> List[Dict]:
        """Carga episodios de una fecha específica"""

        path = Path(f"C:/AURORA/MEMORIA/episodica/episodios_{fecha}.json")
        if not path.exists():
            return []

        episodios = []
        with open(path) as f:
            for linea in f:
                if linea.strip():
                    episodios.append(json.loads(linea))

        return episodios

    def _analizar_patrones_dia(self, episodios: List[Dict]) -> List[Dict]:
        """Analiza patrones en episodios del día"""

        patrones = {}

        for episodio in episodios:
            tipo = episodio.get("tipo", "unknown")

            if tipo not in patrones:
                patrones[tipo] = {
                    "tipo": tipo,
                    "count": 0,
                    "confianza_promedio": 0,
                    "ejemplos": []
                }

            patrones[tipo]["count"] += 1
            patrones[tipo]["confianza_promedio"] += episodio.get("confianza", 0.7)
            patrones[tipo]["ejemplos"].append(episodio["mensaje"][:50])

        # Calcular promedios
        for patron in patrones.values():
            patron["confianza_promedio"] /= patron["count"]

        return list(patrones.values())

    def _guardar_reporte_sleep(self, reporte: Dict):
        """Guarda reporte de sleep cycle"""

        path = Path("C:/AURORA/MEMORIA/consolidacion")
        path.mkdir(parents=True, exist_ok=True)

        # Guardar reporte
        with open(path / "ultimo_sleep.json", "w") as f:
            json.dump(reporte, f, indent=2)

        # Agregar al histórico
        with open(path / "sleep_history.jsonl", "a") as f:
            f.write(json.dumps(reporte) + "\n")


# Instancia global
cerebro = AuroraCerebro()


if __name__ == "__main__":
    # Test básico
    import asyncio

    async def test():
        resultado = await cerebro.razonar(
            "Necesito cotizar 100 poleras sublimadas",
            {"negocio": "MILENS", "tipo": "cliente_nuevo"}
        )
        print(resultado)

    asyncio.run(test())
