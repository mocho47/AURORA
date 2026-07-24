#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escribe los 9 motores reales de AURORA.
Ejecutar desde la raiz del proyecto.
"""
import os
from pathlib import Path

BASE = Path(__file__).parent.parent / "MOTORES"

# ─────────────────────────────────────────────────────────────────────
MOTORES = {}

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_analisis.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR ANALISIS GENERAL
Analiza cualquier consulta con profundidad y honestidad radical.
Usa Groq real. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_analisis")

PROMPT_ANALISIS = """Eres AURORA — el analizador central del ecosistema de Anuar.
Voz directa, mexicana, sin censura. Honestidad radical siempre.
Negocio prioritario: ATF Retrofit (faros LED, margen 120%, $8k-$40k MXN instalado).
Segundo negocio: MILENS (sublimación, láser, coaching, margen 50-150%).

Cuando analizas:
1. Responde con datos reales. NUNCA inventes métricas.
2. Si no sabes algo, dilo y propone cómo obtenerlo.
3. Siempre evalúa: ¿esto acerca a una venta de ATF hoy?
4. Da perspectivas múltiples cuando aplica.
5. Sé conciso pero completo. Máximo 400 palabras."""

_MODELO = "llama-3.1-8b-instant"


class MotorAnalisis:
    def __init__(self):
        self.motor_id = "motor_analisis"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def analizar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        memoria_previa = await self._recordar("analisis")
        prompt_usuario = (
            f"Consulta: {consulta}\\n"
            f"Contexto adicional: {contexto}\\n"
            f"Patrones previos relevantes: {memoria_previa or \'ninguno\'}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_ANALISIS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=600,
                temperature=0.5,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("analisis_completado", {"consulta": consulta[:100], "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_analisis: {e}")
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

    async def _recordar(self, tema: str) -> str:
        try:
            from MEMORIA.sistema_memoria import memoria
            conocimientos = await memoria.recordar(tema=tema, limite=3)
            if not conocimientos:
                return ""
            return " | ".join([f"{k[\'patron\']}: {k[\'conocimiento\'][:80]}" for k in conocimientos])
        except Exception:
            return ""

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorAnalisis()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_coaching.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR COACHING Y DESARROLLO
Coach experto en desarrollo personal, relaciones y familia.
Usa Groq real. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_coaching")

PROMPT_COACHING = """Eres AURORA — coach de desarrollo humano del ecosistema de Anuar.
Especializado en: relaciones familiares, crecimiento personal, metas, comunicación no violenta.
Metodologías reales: Erikson, Dweck, CNV de Rosenberg, Design Thinking, Frankl.
Voz empática pero directa. Sin rodeos. Sin frases vacías. Sin censura.

Reglas de coaching:
1. Valida primero — luego orienta. Nunca impones.
2. Preguntas Sócrates: una pregunta poderosa vale más que diez respuestas.
3. Celebras avances reales, no inventas motivación vacía.
4. Si detectas crisis real (autolesión, abuso) → escala inmediato a protocolo de crisis.
5. Máximo 350 palabras por respuesta. Concreto y accionable."""

_MODELO = "llama-3.1-8b-instant"


class MotorCoaching:
    def __init__(self):
        self.motor_id = "motor_coaching"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def coach(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        tipo = contexto.get("tipo", "personal")
        memoria_previa = await self._recordar("coaching")
        prompt_usuario = (
            f"Situación del usuario: {consulta}\\n"
            f"Tipo de coaching: {tipo}\\n"
            f"Contexto adicional: {contexto}\\n"
            f"Patrones previos exitosos: {memoria_previa or \'primera sesión\'}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_COACHING},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("sesion_coaching", {"tipo": tipo, "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "tipo": tipo,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_coaching: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.7,
            )
        except Exception:
            pass

    async def _recordar(self, tema: str) -> str:
        try:
            from MEMORIA.sistema_memoria import memoria
            conocimientos = await memoria.recordar(tema=tema, limite=3)
            if not conocimientos:
                return ""
            return " | ".join([f"{k[\'patron\']}: {k[\'conocimiento\'][:80]}" for k in conocimientos])
        except Exception:
            return ""

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCoaching()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_code_gen.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR GENERACION DE CODIGO
Genera código real, profesional y funcional en cualquier lenguaje.
Usa Groq real. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_code_gen")

PROMPT_CODE = """Eres AURORA — especialista en generación de código de producción.
Generas código real, funcional, limpio y bien estructurado. Sin placeholders. Sin TODOs sin resolver.
Lenguajes: Python, JavaScript, TypeScript, SQL, Bash, HTML/CSS.
Contexto del proyecto: sistema AURORA en Python/FastAPI, SQLite, Groq API, Green API WhatsApp.

Reglas absolutas:
1. El código que produces FUNCIONA. Sin pass vacíos. Sin ejemplos fake.
2. Incluyes manejo de errores apropiado.
3. Variables y funciones en español cuando el proyecto lo usa, inglés si el contexto lo requiere.
4. Respondes con el código directamente, sin relleno innecesario.
5. Si necesitas datos que no tienes (API key, path), los marcas con os.getenv() o variables claras."""

_MODELO = "llama-3.1-8b-instant"


class MotorCodeGen:
    def __init__(self):
        self.motor_id = "motor_code_gen"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def generar(self, requerimiento: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        lenguaje = contexto.get("lenguaje", "python")
        framework = contexto.get("framework", "")
        prompt_usuario = (
            f"Requerimiento: {requerimiento}\\n"
            f"Lenguaje: {lenguaje}\\n"
            f"Framework/contexto: {framework or \'ninguno específico\'}\\n"
            f"Contexto adicional: {contexto}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_CODE},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=2000,
                temperature=0.2,
            )
            codigo = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("codigo_generado", {"lenguaje": lenguaje, "requerimiento": requerimiento[:100]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "codigo": codigo,
                "lenguaje": lenguaje,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_code_gen: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.6,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCodeGen()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_cotizador.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR COTIZADOR INTELIGENTE
Genera cotizaciones reales con 3 opciones para ATF y MILENS.
Precios reales del catálogo. Usa Groq. Sin simulaciones.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_cotizador")

# Precios reales del catálogo ATF Retrofit
CATALOGO_ATF = {
    "aozoom_x1": {"nombre": "Aozoom X1 Básico", "costo": 3500, "precio_publico": 8000, "instalacion": 800},
    "aozoom_x3": {"nombre": "Aozoom X3 Standard", "costo": 6200, "precio_publico": 14999, "instalacion": 1200},
    "aozoom_x5": {"nombre": "Aozoom X5 Premium", "costo": 10500, "precio_publico": 24999, "instalacion": 1500},
    "aozoom_x7": {"nombre": "Aozoom X7 Elite", "costo": 16500, "precio_publico": 39999, "instalacion": 2000},
}

# Precios reales catálogo MILENS
CATALOGO_MILENS = {
    "polera": {"nombre": "Polera sublimada", "costo": 450, "precio_publico": 850, "mayorista": 650},
    "taza": {"nombre": "Taza sublimada 11oz", "costo": 85, "precio_publico": 170, "mayorista": 130},
    "taza_magica": {"nombre": "Taza mágica", "costo": 120, "precio_publico": 280, "mayorista": 200},
    "bolsa": {"nombre": "Bolsa sublimada", "costo": 180, "precio_publico": 380, "mayorista": 280},
    "caja": {"nombre": "Caja personalizada", "costo": 95, "precio_publico": 220, "mayorista": 160},
    "laser_grabado": {"nombre": "Grabado láser pieza", "costo": 60, "precio_publico": 180, "mayorista": 130},
}

PROMPT_COTIZADOR = """Eres el cotizador profesional de ATF Retrofit y MILENS de Anuar.
Generas SIEMPRE exactamente 3 opciones de cotización: Estándar, Premium y Cierre.
Usas los precios reales del catálogo proporcionado.
ATF margen real: 120-130%. MILENS margen real: 50-150%.
Formato de respuesta: claro, directo, con desglose de precios y próximo paso de acción.
Nunca inventas precios. Si el producto no está en catálogo, dices que necesitas verificar."""

_MODELO = "llama-3.1-8b-instant"


class MotorCotizador:
    def __init__(self):
        self.motor_id = "motor_cotizador"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def cotizar(self, requerimiento: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        negocio = contexto.get("negocio", "atf").lower()
        catalogo = CATALOGO_ATF if negocio == "atf" else CATALOGO_MILENS
        folio = f"COT-{datetime.now().strftime(\'%Y%m%d%H%M%S\')}"
        prompt_usuario = (
            f"Folio: {folio}\\n"
            f"Negocio: {negocio.upper()}\\n"
            f"Requerimiento del cliente: {requerimiento}\\n"
            f"Catálogo disponible: {catalogo}\\n"
            f"Contexto: {contexto}\\n\\n"
            f"Genera exactamente 3 opciones de cotización (Estándar / Premium / Cierre agresivo). "
            f"Incluye desglose, total y próximo paso accionable."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_COTIZADOR},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=700,
                temperature=0.3,
            )
            cotizacion = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("cotizacion_generada", {
                "folio": folio, "negocio": negocio,
                "requerimiento": requerimiento[:100], "preview": cotizacion[:200]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "folio": folio,
                "negocio": negocio,
                "cotizacion": cotizacion,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_cotizador: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.8,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCotizador()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_reasoning.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR RAZONAMIENTO PROFUNDO
Analiza decisiones complejas desde múltiples ángulos. Estrategia real.
Usa Groq. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_reasoning")

PROMPT_REASONING = """Eres AURORA — el motor de razonamiento estratégico de Anuar.
Piensas profundamente, sin censura, sin sesgos de confirmación.
Tu metodología: 6 dimensiones obligatorias por decisión compleja.

1. TÉCNICO: ¿Es factible? ¿Qué recursos requiere? ¿Tiempo realista?
2. FINANCIERO: ¿Cuánto cuesta? ¿Cuánto genera? ¿ROI real?
3. OPERACIONAL: ¿Afecta procesos actuales? ¿Carga de trabajo?
4. RELACIONAL: ¿Impacto en clientes, equipo, socios?
5. RIESGO: ¿Qué puede fallar? ¿Plan B?
6. DECISIÓN: Recomendación concreta con nivel de confianza 0.0-1.0.

Si confianza >= 0.75 → ACTÚA (recomienda acción inmediata).
Si confianza < 0.75 → da 2 opciones y pide confirmación.
NUNCA das respuestas vagas. Siempre terminas con acción concreta."""

_MODELO = "llama-3.1-8b-instant"


class MotorReasoning:
    def __init__(self):
        self.motor_id = "motor_reasoning"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def razonar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        memoria_previa = await self._recordar("razonamiento")
        prompt_usuario = (
            f"Problema/Decisión: {consulta}\\n"
            f"Restricciones conocidas: {contexto}\\n"
            f"Decisiones similares pasadas: {memoria_previa or \'ninguna registrada\'}\\n\\n"
            f"Analiza con las 6 dimensiones y dame una decisión concreta con nivel de confianza."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_REASONING},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=900,
                temperature=0.4,
            )
            analisis = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("razonamiento_completado", {"consulta": consulta[:100], "preview": analisis[:200]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "analisis": analisis,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_reasoning: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.8,
            )
        except Exception:
            pass

    async def _recordar(self, tema: str) -> str:
        try:
            from MEMORIA.sistema_memoria import memoria
            conocimientos = await memoria.recordar(tema=tema, limite=3)
            if not conocimientos:
                return ""
            return " | ".join([f"{k[\'patron\']}: {k[\'conocimiento\'][:80]}" for k in conocimientos])
        except Exception:
            return ""

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorReasoning()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_ventas.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR VENTAS Y CRM
Gestión de leads, seguimiento, cierre de ventas ATF y MILENS.
Usa Groq + ORACLE SQLite. Sin simulaciones. Sin placeholders.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_ventas")

PROMPT_VENTAS = """Eres el especialista en ventas de ATF Retrofit y MILENS de Anuar.
Técnicas reales: SPIN Selling, AIDA, Cierre por opción, Manejo de objeciones Cialdini.
Producto prioritario: ATF Retrofit LED (faros). Margen 120%. Precio: $8k-$40k MXN instalado.
Buyer persona ATF: hombre 20-40 años, le gusta su carro, quiere diferenciarse, medio-alto.

Metodología de venta:
1. SPIN primero: Situación → Problema → Implicación → Necesidad.
2. NUNCA presiones con escasez falsa. Solo escasez real (fechas reales, cupos reales).
3. Manejo de objeciones: Validar → Preguntar → Reencuadrar con valor.
4. Cierre: siempre con opción, nunca sí/no. "¿Lo agendo sábado o entre semana?"
5. Seguimiento: registrar en ORACLE. Ningún lead se enfría.
6. Velocidad: respuesta < 2 minutos en WhatsApp = ventaja competitiva enorme."""

_MODELO = "llama-3.1-8b-instant"


class MotorVentas:
    def __init__(self):
        self.motor_id = "motor_ventas"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def procesar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        cliente = contexto.get("cliente", "prospecto nuevo")
        etapa = contexto.get("etapa", "primer contacto")
        negocio = contexto.get("negocio", "ATF")
        historial_cliente = await self._obtener_historial(contexto.get("cliente_id"))
        prompt_usuario = (
            f"Cliente: {cliente} | Etapa: {etapa} | Negocio: {negocio}\\n"
            f"Situación/mensaje: {consulta}\\n"
            f"Historial del cliente en ORACLE: {historial_cliente}\\n"
            f"Contexto adicional: {contexto}\\n\\n"
            f"Dame la respuesta/acción de venta apropiada para esta etapa."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_VENTAS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=500,
                temperature=0.5,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("interaccion_venta", {
                "cliente": cliente, "etapa": etapa, "negocio": negocio, "preview": respuesta[:150]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "respuesta": respuesta,
                "cliente": cliente,
                "etapa": etapa,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_ventas: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _obtener_historial(self, cliente_id: int = None) -> str:
        if not cliente_id:
            return "cliente nuevo, sin historial previo"
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
            import oracle_core as oracle
            oracle.init_db()
            lead = oracle.obtener_lead(cliente_id)
            if not lead:
                return "lead no encontrado en ORACLE"
            return f"Lead #{cliente_id}: {lead[\'nombre\']} | Estado: {lead[\'estado\']} | Notas: {lead[\'notas\'] or \'ninguna\'}"
        except Exception as e:
            return f"ORACLE no disponible: {e}"

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.8,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorVentas()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_imagenes.py"] = '''\
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

from groq import AsyncGroq

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

_MODELO = "llama-3.1-8b-instant"

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
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
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
            f"Imagen/recurso: {descripcion}\\n"
            f"Uso: {uso}\\n"
            f"Plataforma destino: {plataforma}\\n"
            f"Specs requeridas: {specs_ref}\\n"
            f"Contexto: {contexto}\\n\\n"
            f"Dame recomendaciones técnicas precisas y accionables."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_IMAGENES},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            recomendaciones = r.choices[0].message.content.strip()
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
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_negocios.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR NEGOCIOS (ATF + MILENS)
Gestión operativa real de los negocios de Anuar.
Usa Groq + datos reales de CONFIG. Sin simulaciones.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_negocios")

PROMPT_NEGOCIOS = """Eres el gestor operativo de los negocios de Anuar: ATF Retrofit y MILENS.

ATF Retrofit — iluminación automotriz LED:
- Producto: kits Aozoom X1 ($8k), X3 ($15k), X5 ($25k), X7 ($40k) MXN instalado.
- Margen: 120% sobre costo.
- Canales: TikTok, Instagram, YouTube, WhatsApp directo.
- Prioridad #1: generar leads y cerrar instalaciones HOY.
- Respuesta a lead: < 5 minutos. Ningún lead se enfría.

MILENS — sublimación y láser:
- Productos: poleras ($850), tazas ($170), grabado láser ($180 por pieza).
- Margen: 50-150%.
- Clientes: empresas, eventos, regalos personalizados.
- Fortaleza: calidad + entrega rápida.

Tu rol: reportar estado real, proponer acciones, detectar oportunidades.
Regla fundamental: NUNCA inventes métricas. Si no tienes datos reales, dilo y propone cómo obtenerlos.
Siempre termina con "PRÓXIMA ACCIÓN RECOMENDADA:" + acción concreta."""

_MODELO = "llama-3.1-8b-instant"


class MotorNegocios:
    def __init__(self):
        self.motor_id = "motor_negocios"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def consultar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        negocio = contexto.get("negocio", "ambos")
        resumen_oracle = await self._resumen_oracle(negocio)
        prompt_usuario = (
            f"Consulta operativa: {consulta}\\n"
            f"Negocio: {negocio}\\n"
            f"Resumen actual desde ORACLE: {resumen_oracle}\\n"
            f"Contexto adicional: {contexto}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_NEGOCIOS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=600,
                temperature=0.4,
            )
            respuesta = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1
            await self._registrar("consulta_negocio", {"negocio": negocio, "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "negocio": negocio,
                "respuesta": respuesta,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_negocios: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _resumen_oracle(self, negocio: str) -> str:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
            import oracle_core as oracle
            oracle.init_db()
            r = oracle.resumen(negocio if negocio != "ambos" else None)
            return str(r)
        except Exception as e:
            return f"ORACLE no disponible: {e}"

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.7,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorNegocios()
'''

# ═══════════════════════════════════════════════════════════════════
MOTORES["motor_pedidos.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — MOTOR PEDIDOS
Captura y gestión de órdenes con persistencia SQLite real.
Usa ORACLE para CRM + Groq para confirmaciones. Sin simulaciones.
"""
import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_pedidos")

DB_PEDIDOS = Path(__file__).parent.parent / "pedidos.db"

PROMPT_PEDIDOS = """Eres el gestor de pedidos de ATF Retrofit y MILENS.
Cuando recibes datos de un pedido, generas una confirmación profesional clara.
Incluyes: ID de pedido, resumen de lo ordenado, precio total, próximo paso.
Si faltan datos críticos (nombre, teléfono, producto, precio), los solicitas.
Nunca confirmas un pedido sin monto real. Siempre terminas con el siguiente paso concreto."""

_MODELO = "llama-3.1-8b-instant"


def _init_db() -> None:
    conn = sqlite3.connect(str(DB_PEDIDOS))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id          TEXT PRIMARY KEY,
            negocio     TEXT NOT NULL DEFAULT \'atf\',
            cliente     TEXT NOT NULL,
            telefono    TEXT,
            producto    TEXT NOT NULL,
            precio      REAL DEFAULT 0,
            anticipo    REAL DEFAULT 0,
            estado      TEXT DEFAULT \'pendiente\',
            notas       TEXT,
            creado      TEXT NOT NULL,
            actualizado TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado)")
    conn.commit()
    conn.close()


def _crear_pedido_db(pedido_id: str, negocio: str, cliente: str, telefono: str,
                     producto: str, precio: float, notas: str) -> None:
    ahora = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(str(DB_PEDIDOS))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """INSERT INTO pedidos (id, negocio, cliente, telefono, producto, precio, notas, creado, actualizado)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (pedido_id, negocio, cliente, telefono, producto, precio, notas, ahora, ahora)
    )
    conn.commit()
    conn.close()


def _listar_pedidos_db(estado: Optional[str] = None, limit: int = 20) -> list:
    conn = sqlite3.connect(str(DB_PEDIDOS))
    conn.row_factory = sqlite3.Row
    if estado:
        rows = conn.execute("SELECT * FROM pedidos WHERE estado=? ORDER BY creado DESC LIMIT ?",
                            (estado, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM pedidos ORDER BY creado DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _actualizar_estado_db(pedido_id: str, nuevo_estado: str) -> bool:
    conn = sqlite3.connect(str(DB_PEDIDOS))
    ahora = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute("UPDATE pedidos SET estado=?, actualizado=? WHERE id=?",
                       (nuevo_estado, ahora, pedido_id))
    conn.commit()
    actualizado = cur.rowcount > 0
    conn.close()
    return actualizado


class MotorPedidos:
    def __init__(self):
        self.motor_id = "motor_pedidos"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}
        _init_db()

    async def capturar(self, datos: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        pedido_id = f"PED-{datetime.now().strftime(\'%Y%m%d\')}-{str(uuid4())[:6].upper()}"
        negocio = contexto.get("negocio", "atf")
        cliente = contexto.get("cliente", "por confirmar")
        telefono = contexto.get("telefono", "")
        producto = contexto.get("producto", "por confirmar")
        precio = float(contexto.get("precio", 0))
        notas = contexto.get("notas", "")
        prompt_usuario = (
            f"ID Pedido: {pedido_id}\\n"
            f"Negocio: {negocio.upper()}\\n"
            f"Cliente: {cliente} | Tel: {telefono}\\n"
            f"Producto: {producto} | Precio: ${precio:,.0f} MXN\\n"
            f"Datos adicionales: {datos}\\n"
            f"Notas: {notas}\\n\\n"
            f"Genera la confirmación de pedido profesional."
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_PEDIDOS},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=400,
                temperature=0.3,
            )
            confirmacion = r.choices[0].message.content.strip()
            _crear_pedido_db(pedido_id, negocio, cliente, telefono, producto, precio, notas)
            self.stats["exitosos"] += 1
            await self._registrar("pedido_capturado", {
                "pedido_id": pedido_id, "negocio": negocio,
                "cliente": cliente, "precio": precio
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "pedido_id": pedido_id,
                "confirmacion": confirmacion,
                "precio": precio,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_pedidos: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def listar(self, estado: str = None) -> Dict:
        pedidos = await asyncio.to_thread(_listar_pedidos_db, estado)
        return {"status": "OK", "motor": self.motor_id, "total": len(pedidos), "pedidos": pedidos}

    async def actualizar_estado(self, pedido_id: str, nuevo_estado: str) -> Dict:
        ok = await asyncio.to_thread(_actualizar_estado_db, pedido_id, nuevo_estado)
        await self._registrar("pedido_actualizado", {"pedido_id": pedido_id, "estado": nuevo_estado})
        return {"status": "OK" if ok else "ERROR", "pedido_id": pedido_id, "estado": nuevo_estado}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.9,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        pedidos_activos = len(_listar_pedidos_db("pendiente"))
        return {
            "motor_id": self.motor_id,
            "groq_activo": self._groq is not None,
            "db": str(DB_PEDIDOS),
            "pedidos_pendientes": pedidos_activos,
            "stats": self.stats,
        }


motor = MotorPedidos()
'''

# ─────────────────────────────────────────────────────────────────────
# ESCRITURA REAL
# ─────────────────────────────────────────────────────────────────────
errores = []
for nombre, contenido in MOTORES.items():
    ruta = BASE / nombre
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        size = os.path.getsize(ruta)
        print(f"OK  {nombre}  ({size} bytes)")
    except Exception as e:
        errores.append(f"ERROR {nombre}: {e}")
        print(f"ERROR {nombre}: {e}")

print()
if errores:
    print(f"FALLARON: {len(errores)}")
    for e in errores:
        print(f"  {e}")
else:
    print(f"COMPLETADO: {len(MOTORES)} motores escritos exitosamente.")
