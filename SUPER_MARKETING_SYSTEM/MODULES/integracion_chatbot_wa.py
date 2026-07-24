#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║          💬 INTEGRACIÓN CHATBOT WA CON SISTEMA DE MARKETING 💬             ║
║                                                                             ║
║ Conecta el Chatbot de WhatsApp con:                                        ║
║ • Leads desde publicaciones en redes (TikTok, Instagram, etc.)            ║
║ • Automatización de respuestas inteligentes                                ║
║ • Califical clasificación de leads                                         ║
║ • Integración con CRM                                                      ║
║ • Generación de reportes de conversión                                     ║
║ • Respuestas personalizadas por producto                                   ║
║ • Multi-agente: IA responsable, gestor de ventas, especialista técnico    ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger("INTEGRACION_CHATBOT_WA")


class EstadoLead(Enum):
    """Estados del ciclo de vida de un lead"""
    NUEVO = "nuevo"
    CALIFICADO = "calificado"
    CONTACTADO = "contactado"
    EN_NEGOCIACION = "en_negociacion"
    CERRADO_GANADO = "cerrado_ganado"
    CERRADO_PERDIDO = "cerrado_perdido"
    ABANDONADO = "abandonado"


class CalificacionLead(Enum):
    """Niveles de calificación de leads"""
    HOT = "hot"  # Cliente activo, listo para comprar
    WARM = "warm"  # Interesado, necesita nurturing
    COLD = "cold"  # Contacto nuevo, sin interés claro


class ProductoInteres(Enum):
    """Productos ATF que pueden interesar"""
    BUMPER = "bumper_deportivo"
    SPOILER = "spoiler_aerodinamico"
    KIT_SUSPENSION = "kit_suspension_deportiva"
    RINES = "rines_aleacion"
    ESCAPE = "escape_deportivo"
    TUNING_MOTOR = "tuning_motor"
    ILUMINACION_LED = "iluminacion_led"
    SISTEMA_AUDIO = "sistema_audio_premium"
    INTERIOR_DEPORTIVO = "interior_deportivo"
    CALCO_VINILO = "calco_vinilo_personalizado"


@dataclass
class PerfilLead:
    """Perfil completo de un lead"""
    id_lead: str
    nombre: str
    whatsapp: str
    email: Optional[str] = None
    origen_red: str = ""  # tiktok, instagram, youtube, etc.
    id_publicacion_origen: Optional[str] = None

    # Datos de interés
    producto_interes: Optional[ProductoInteres] = None
    marca_auto: Optional[str] = None
    modelo_auto: Optional[str] = None
    año_auto: Optional[int] = None
    presupuesto_estimado: Optional[float] = None

    # Calificación
    estado: EstadoLead = EstadoLead.NUEVO
    calificacion: CalificacionLead = CalificacionLead.COLD
    score_calificacion: float = 0.0  # 0.0 a 1.0

    # Histórico de conversación
    mensajes_recibidos: int = 0
    mensajes_enviados: int = 0
    ultima_interaccion: Optional[datetime] = None
    fecha_primer_contacto: datetime = None

    # Valor
    valor_potencial_pesos: float = 0.0
    tasa_conversion_estimada: float = 0.0
    dias_en_pipeline: int = 0

    fecha_creacion: datetime = None


@dataclass
class MensajeWA:
    """Un mensaje de WhatsApp"""
    id_mensaje: str
    id_lead: str
    quien_envia: str  # "usuario" o "bot"
    contenido: str
    timestamp: datetime
    tipo: str = "texto"  # texto, imagen, documento, audio, etc.
    adjuntos_path: Optional[List[str]] = None
    procesado_por_ia: bool = False


class ClasificadorLeads:
    """Clasifica y califica leads automáticamente"""

    @staticmethod
    def analizar_interes_producto(mensaje: str) -> Tuple[Optional[ProductoInteres], float]:
        """Detecta qué producto interesa al cliente"""
        keywords_productos = {
            ProductoInteres.BUMPER: ["bumper", "defensa", "parachoques"],
            ProductoInteres.SPOILER: ["spoiler", "alerón", "aleta"],
            ProductoInteres.KIT_SUSPENSION: ["suspension", "amortiguador", "altura"],
            ProductoInteres.RINES: ["rines", "llantas", "ruedas", "wheel"],
            ProductoInteres.ESCAPE: ["escape", "tubo", "sistem exhaust"],
            ProductoInteres.TUNING_MOTOR: ["motor", "turbo", "caballos", "performance"],
            ProductoInteres.ILUMINACION_LED: ["led", "luz", "iluminación"],
            ProductoInteres.SISTEMA_AUDIO: ["audio", "bocinas", "sonido"],
            ProductoInteres.INTERIOR_DEPORTIVO: ["interior", "asientos", "tapicería"],
            ProductoInteres.CALCO_VINILO: ["calco", "vinilo", "diseño", "custom"],
        }

        mensaje_lower = mensaje.lower()
        scores = {}

        for producto, keywords in keywords_productos.items():
            coincidencias = sum(1 for kw in keywords if kw in mensaje_lower)
            scores[producto] = coincidencias

        if not scores or max(scores.values()) == 0:
            return None, 0.0

        producto_detectado = max(scores, key=scores.get)
        score = min(scores[producto_detectado] * 0.5, 1.0)  # Máximo 1.0

        return producto_detectado, score

    @staticmethod
    def detectar_datos_auto(mensaje: str) -> Dict[str, Any]:
        """Extrae info del auto del cliente"""
        # Simplificado - en producción usar NER o regex avanzados
        marcas_comunes = ["toyota", "ford", "chevrolet", "nissan", "volkswagen", "hyundai"]
        datos = {
            "marca": None,
            "modelo": None,
            "año": None,
            "found": False,
        }

        mensaje_lower = mensaje.lower()
        for marca in marcas_comunes:
            if marca in mensaje_lower:
                datos["marca"] = marca
                datos["found"] = True

        return datos

    @staticmethod
    def calcular_score_calificacion(perfil: PerfilLead) -> Tuple[CalificacionLead, float]:
        """Calcula score de calificación HOT/WARM/COLD"""
        score = 0.0

        # Factores que aumentan score
        if perfil.producto_interes:
            score += 0.3
        if perfil.marca_auto:
            score += 0.2
        if perfil.presupuesto_estimado and perfil.presupuesto_estimado > 0:
            score += 0.2
        if perfil.mensajes_recibidos > 3:
            score += 0.15
        if perfil.estado in [EstadoLead.CONTACTADO, EstadoLead.EN_NEGOCIACION]:
            score += 0.15

        # Determinar calificación
        if score >= 0.75:
            calificacion = CalificacionLead.HOT
        elif score >= 0.40:
            calificacion = CalificacionLead.WARM
        else:
            calificacion = CalificacionLead.COLD

        return calificacion, min(score, 1.0)


class ResponderAutomaticoIA:
    """Genera respuestas automáticas inteligentes contextualizadas"""

    RESPUESTAS_SALUDAR = [
        "¡Hola! 👋 Bienvenido a ATF Retrofit. ¿En qué podemos ayudarte hoy?",
        "¡Hey! 🚗 Soy tu asistente ATF. Cuéntame qué tipo de retrofit buscas",
        "Hola 👋 ATF aquí. ¿Qué accesorios te interesan para tu auto?",
    ]

    RESPUESTAS_PRODUCTO = {
        ProductoInteres.BUMPER: "¡Perfecto! 💪 Tenemos bumpers deportivos de calidad premium. ¿Qué marca y modelo es tu auto?",
        ProductoInteres.SPOILER: "¡Excelente! 🏁 Nuestros spoilers aerodinámicos son de alta calidad. ¿Cuéntame de tu vehículo?",
        ProductoInteres.KIT_SUSPENSION: "¡Buena opción! ⚙️ Kit de suspension deportiva disponible. ¿Cuál es tu presupuesto?",
        ProductoInteres.RINES: "¡Sí! 🎨 Tenemos rines de aleación con diseños exclusivos. ¿Te envío catálogo?",
        ProductoInteres.ESCAPE: "🔊 Nuestros escapes deportivos mejoran sonido y performance. ¿Interesado?",
        ProductoInteres.TUNING_MOTOR: "⚡ Tuning motor es nuestra especialidad. ¿Cuántos caballos buscas?",
        ProductoInteres.ILUMINACION_LED: "💡 LED premium disponible. Moderniza tu auto. ¿Qué tipo de luz buscas?",
        ProductoInteres.SISTEMA_AUDIO: "🎵 Sistemas de audio de calidad profesional. ¿Presupuesto para audio?",
        ProductoInteres.INTERIOR_DEPORTIVO: "🏎️ Interior deportivo personalizado. ¿Qué estilo te atrae?",
        ProductoInteres.CALCO_VINILO: "🎨 Diseños custom y personalización. ¿Qué estilo buscas?",
    }

    RESPUESTAS_PRECIO = {
        "caro": "Entiendo. Te paso opciones más económicas que mantienen calidad. ¿Qué presupuesto es viable?",
        "descuento": "¡Claro! Tenemos promociones especiales. ¿Cuál es tu presupuesto total?",
        "precio": "Te paso el precio exacto. ¿Cuál es tu auto para cotización precisa?",
    }

    @staticmethod
    async def generar_respuesta_contextualizada(
        perfil: PerfilLead,
        mensaje_usuario: str
    ) -> str:
        """Genera respuesta IA personalizada según contexto"""

        # Detectar intención
        mensaje_lower = mensaje_usuario.lower()

        # Saludar
        if any(palabra in mensaje_lower for palabra in ["hola", "hi", "buenas", "ayuda"]):
            return ResponderAutomaticoIA.RESPUESTAS_SALUDAR[0]

        # Pregunta sobre producto específico
        producto, _ = ClasificadorLeads.analizar_interes_producto(mensaje_usuario)
        if producto and producto in ResponderAutomaticoIA.RESPUESTAS_PRODUCTO:
            return ResponderAutomaticoIA.RESPUESTAS_PRODUCTO[producto]

        # Pregunta sobre precio
        if any(kw in mensaje_lower for kw in ["precio", "costo", "caro", "descuento", "promo"]):
            return "Claro, te paso todos nuestros precios y promociones actuales. ¿Cuál es tu presupuesto?"

        # Respuesta genérica si no hay contexto
        return "Entiendo. 👍 Dime más sobre qué tipo de retrofit necesitas y tu presupuesto aproximado."


class GestorConversacionesWA:
    """Maneja las conversaciones en WhatsApp con el chatbot"""

    def __init__(self):
        self.leads_activos: Dict[str, PerfilLead] = {}
        self.historial_mensajes: Dict[str, List[MensajeWA]] = {}
        self.clasificador = ClasificadorLeads()
        self.responder_auto = ResponderAutomaticoIA()
        logger.info("💬 Gestor de Conversaciones WA inicializado")

    async def procesar_mensaje_entrante(
        self,
        whatsapp_numero: str,
        contenido: str,
        id_publicacion_origen: Optional[str] = None,
        origen_red: str = "directo"
    ) -> Tuple[PerfilLead, str]:
        """
        Procesa un mensaje entrante de WhatsApp.
        Retorna: (perfil_lead_actualizado, respuesta_automática)
        """
        # Crear o recuperar lead
        if whatsapp_numero not in self.leads_activos:
            id_lead = f"lead_{hashlib.md5(whatsapp_numero.encode()).hexdigest()[:8]}"
            perfil = PerfilLead(
                id_lead=id_lead,
                nombre=f"Cliente {whatsapp_numero[-4:]}",  # Nombre temporal
                whatsapp=whatsapp_numero,
                origen_red=origen_red,
                id_publicacion_origen=id_publicacion_origen,
                fecha_primer_contacto=datetime.now(),
                fecha_creacion=datetime.now(),
            )
            self.leads_activos[whatsapp_numero] = perfil
            self.historial_mensajes[whatsapp_numero] = []
            logger.info(f"✅ Nuevo lead creado: {id_lead}")
        else:
            perfil = self.leads_activos[whatsapp_numero]

        # Registrar mensaje entrante
        mensaje = MensajeWA(
            id_mensaje=str(uuid.uuid4()),
            id_lead=perfil.id_lead,
            quien_envia="usuario",
            contenido=contenido,
            timestamp=datetime.now(),
        )
        self.historial_mensajes[whatsapp_numero].append(mensaje)

        # Actualizar estadísticas
        perfil.mensajes_recibidos += 1
        perfil.ultima_interaccion = datetime.now()
        perfil.dias_en_pipeline = (datetime.now() - perfil.fecha_primer_contacto).days

        # Clasificar interés de producto
        producto, score_producto = self.clasificador.analizar_interes_producto(contenido)
        if producto:
            perfil.producto_interes = producto
            logger.info(f"📌 Producto detectado: {producto.value}")

        # Detectar datos del auto
        datos_auto = self.clasificador.detectar_datos_auto(contenido)
        if datos_auto["marca"]:
            perfil.marca_auto = datos_auto["marca"]
            logger.info(f"🚗 Marca detectada: {datos_auto['marca']}")

        # Recalcular calificación
        calificacion, score = self.clasificador.calcular_score_calificacion(perfil)
        perfil.calificacion = calificacion
        perfil.score_calificacion = score

        # Generar respuesta automática
        respuesta = await self.responder_auto.generar_respuesta_contextualizada(perfil, contenido)

        # Registrar respuesta enviada
        mensaje_bot = MensajeWA(
            id_mensaje=str(uuid.uuid4()),
            id_lead=perfil.id_lead,
            quien_envia="bot",
            contenido=respuesta,
            timestamp=datetime.now(),
            procesado_por_ia=True,
        )
        self.historial_mensajes[whatsapp_numero].append(mensaje_bot)
        perfil.mensajes_enviados += 1

        logger.info(f"💬 Respuesta enviada: {respuesta[:80]}...")
        logger.info(f"   Calificación: {calificacion.value} ({score:.0%})")

        return perfil, respuesta

    async def enviar_propuesta_personalizada(self, whatsapp_numero: str) -> str:
        """Envía propuesta personalizada según el perfil del cliente"""
        if whatsapp_numero not in self.leads_activos:
            return "❌ Cliente no encontrado"

        perfil = self.leads_activos[whatsapp_numero]

        if not perfil.producto_interes or not perfil.marca_auto:
            return "Necesito más info. ¿Cuál es tu presupuesto aproximado?"

        propuesta = f"""
        🎯 PROPUESTA PERSONALIZADA ATF

        Para tu {perfil.marca_auto.title()} {perfil.modelo_auto or ''}:
        • Producto: {perfil.producto_interes.value}
        • Presupuesto estimado: ${perfil.presupuesto_estimado or 'A consultar'} pesos

        ✨ BENEFICIOS:
        → Calidad premium garantizada
        → Instalación profesional disponible
        → Garantía de 12 meses
        → Envío gratis para compras > $2,000

        📅 Oferta válida por 48 horas
        💬 ¿Te interesa? Confirma para enviarte cotización exacta
        """

        perfil.estado = EstadoLead.EN_NEGOCIACION
        return propuesta

    def obtener_estadisticas_leads(self) -> Dict[str, Any]:
        """Retorna estadísticas de todos los leads"""
        if not self.leads_activos:
            return {"total_leads": 0}

        leads = list(self.leads_activos.values())
        hot_leads = [l for l in leads if l.calificacion == CalificacionLead.HOT]
        warm_leads = [l for l in leads if l.calificacion == CalificacionLead.WARM]

        valor_total = sum(l.valor_potencial_pesos for l in leads)
        conversion_estimada = sum(l.tasa_conversion_estimada for l in leads) / len(leads) if leads else 0.0

        return {
            "total_leads": len(leads),
            "hot_leads": len(hot_leads),
            "warm_leads": len(warm_leads),
            "cold_leads": len(leads) - len(hot_leads) - len(warm_leads),
            "valor_pipeline_pesos": valor_total,
            "tasa_conversion_promedio": f"{conversion_estimada:.1%}",
            "leads_con_producto_definido": len([l for l in leads if l.producto_interes]),
            "leads_con_auto_definido": len([l for l in leads if l.marca_auto]),
        }


class IntegracionChatbotWA:
    """Orquestador principal de integración ChatBot WA"""

    def __init__(self):
        self.gestor_conversaciones = GestorConversacionesWA()
        logger.info("🔗 Integración ChatBot WA con Marketing System iniciada")

    async def procesar_lead_desde_publicacion(
        self,
        whatsapp_numero: str,
        id_publicacion: str,
        plataforma_origen: str
    ) -> PerfilLead:
        """
        Procesa un lead que vino desde una publicación en redes.
        Inicia conversación automática.
        """
        logger.info(f"🔗 Lead desde {plataforma_origen}: {whatsapp_numero}")

        mensaje_inicial = f"¡Hola! Te contactamos desde nuestra publicación en {plataforma_origen.title()}. ¿Te interesa saber más sobre nuestros productos?"

        perfil, respuesta = await self.gestor_conversaciones.procesar_mensaje_entrante(
            whatsapp_numero,
            mensaje_inicial,
            id_publicacion_origen=id_publicacion,
            origen_red=plataforma_origen
        )

        return perfil

    async def webhook_mensaje_entrante(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja webhook de mensaje entrante del chatbot WA.
        (Simulado - en producción sería real)
        """
        logger.info(f"📨 Webhook de mensaje entrante procesado")

        whatsapp_numero = payload.get("from", "")
        contenido = payload.get("text", "")

        perfil, respuesta_auto = await self.gestor_conversaciones.procesar_mensaje_entrante(
            whatsapp_numero,
            contenido
        )

        return {
            "status": "success",
            "id_lead": perfil.id_lead,
            "respuesta_enviada": respuesta_auto,
            "calificacion": perfil.calificacion.value,
            "score": perfil.score_calificacion,
        }

    def obtener_dashboard_leads(self) -> Dict[str, Any]:
        """Obtiene dashboard de leads"""
        return {
            "timestamp": datetime.now().isoformat(),
            "estadisticas": self.gestor_conversaciones.obtener_estadisticas_leads(),
            "sistema": "✅ ChatBot WA - Integración Completa",
            "leads_activos": len(self.gestor_conversaciones.leads_activos),
        }


# Test
async def test_integracion_chatbot():
    """Test de la integración"""
    sistema = IntegracionChatbotWA()

    # Test 1: Lead desde publicación
    print("\n" + "="*80)
    print("TEST 1: Lead desde Publicación en TikTok")
    print("="*80)
    perfil = await sistema.procesar_lead_desde_publicacion(
        "+5215551234567",
        "pub_abc123_tiktok",
        "tiktok"
    )
    print(f"✅ Lead creado: {perfil.id_lead}")

    # Test 2: Conversación
    print("\n" + "="*80)
    print("TEST 2: Conversación sobre Productos")
    print("="*80)
    perfil, respuesta = await sistema.gestor_conversaciones.procesar_mensaje_entrante(
        "+5215551234567",
        "Hola, me interesa un bumper deportivo para mi Ford Mustang"
    )
    print(f"Respuesta: {respuesta}")
    print(f"Calificación: {perfil.calificacion.value}")

    # Test 3: Dashboard
    print("\n" + "="*80)
    print("TEST 3: Dashboard de Leads")
    print("="*80)
    dashboard = sistema.obtener_dashboard_leads()
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    asyncio.run(test_integracion_chatbot())
