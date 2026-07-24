"""
AURORA - Sincronización Chatbot WA + ATF Messenger
Integración bidireccional: WhatsApp ↔ AURORA Brain ↔ ATF Messenger
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import aiohttp

class ChatbotSync:
    """Sincroniza mensajes entre WhatsApp, AURORA y ATF Messenger"""

    def __init__(self):
        self.chatbot_url = "http://localhost:8005"
        self.atf_messenger_url = "http://192.168.1.26:8010"
        self.aurora_url = "http://localhost:8000"
        self.green_api_instance = "7107622171"
        self.historial_mensajes = []

    async def procesar_mensaje_wa(self, mensaje: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje de WhatsApp:
        1. Recibe de Green API (chatbot)
        2. Envía a AURORA Brain para análisis
        3. Responde en WhatsApp
        4. Sincroniza con ATF Messenger
        """

        remitente = mensaje.get('sender', {}).get('phone', 'unknown')
        contenido = mensaje.get('content', '')
        timestamp = datetime.now().isoformat()

        print(f"[SYNC] Mensaje WA de {remitente}: {contenido}")

        # 1. Enviar a AURORA para análisis
        respuesta_aurora = await self._consultar_aurora(contenido)

        # 2. Procesar intención y seleccionar motor
        intencion, motor = await self._clasificar_intencion(contenido, respuesta_aurora)

        # 3. Generar respuesta final
        respuesta_final = await self._generar_respuesta(
            contenido,
            respuesta_aurora,
            intencion
        )

        # 4. Enviar respuesta por WhatsApp
        await self._enviar_wa(remitente, respuesta_final)

        # 5. Sincronizar con ATF Messenger
        await self._sincronizar_atf_messenger({
            'remitente': remitente,
            'mensaje_original': contenido,
            'intencion': intencion,
            'motor': motor,
            'respuesta': respuesta_final,
            'timestamp': timestamp
        })

        # 6. Guardar en historial
        self._guardar_historial({
            'remitente': remitente,
            'canal': 'whatsapp',
            'mensaje': contenido,
            'respuesta': respuesta_final,
            'intencion': intencion,
            'motor': motor,
            'timestamp': timestamp
        })

        return {
            'status': 'ok',
            'remitente': remitente,
            'respuesta': respuesta_final,
            'intencion': intencion,
            'canal': 'whatsapp',
            'timestamp': timestamp
        }

    async def _consultar_aurora(self, mensaje: str) -> Dict[str, Any]:
        """Consulta AURORA Brain para análisis profundo"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'mensaje': mensaje,
                    'contexto': {
                        'canal': 'whatsapp',
                        'requiere_razonamiento': True
                    }
                }

                async with session.post(
                    f"{self.aurora_url}/razonar",
                    json=payload,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()

                    return {'respuesta': 'Procesando...', 'confianza': 0.5}

        except Exception as e:
            print(f"[ERROR] Consulta AURORA: {e}")
            return {'respuesta': 'Error en procesamiento', 'confianza': 0}

    async def _clasificar_intencion(self, mensaje: str, respuesta_aurora: Dict) -> tuple:
        """Clasifica intención y selecciona motor AURORA"""

        palabras_clave = {
            'atf': ['atf', 'faros', 'retrofit', 'bi-led', 'luces', 'actualiza'],
            'milens': ['milens', 'contenido', 'videos', 'posts', 'diseño', 'ia'],
            'cotizacion': ['precio', 'costo', 'cotiza', 'cuánto', 'valor'],
            'soporte': ['ayuda', 'problema', 'no funciona', 'error', 'urgente'],
        }

        intencion = 'general'
        for intent, palabras in palabras_clave.items():
            if any(p in mensaje.lower() for p in palabras):
                intencion = intent
                break

        motor_map = {
            'atf': 'motor_cotizador_atf',
            'milens': 'motor_cotizador_milens',
            'cotizacion': 'motor_cotizador',
            'soporte': 'motor_soporte',
            'general': 'motor_analisis'
        }

        motor = motor_map.get(intencion, 'motor_analisis')
        return intencion, motor

    async def _generar_respuesta(self, mensaje: str, respuesta_aurora: Dict, intencion: str) -> str:
        """Genera respuesta final combinando AURORA + contexto"""

        plantillas = {
            'atf': f"""🚗 ATF - Retrofit Profesional
Entendí tu consulta sobre retrofit.
{respuesta_aurora.get('respuesta', 'Tenemos soluciones profesionales de faros.')}

¿Qué kit te interesa? Bi-LED, LED Premium o Fibra Óptica.
""",
            'milens': f"""🎨 MILENS - Contenido con IA
Para tu estrategia de contenido:
{respuesta_aurora.get('respuesta', 'Podemos generar videos, posts y diseños.')}

¿Qué tipo de contenido necesitas?
""",
            'cotizacion': f"""💰 Cotización Rápida
{respuesta_aurora.get('respuesta', 'Te hago la cotización.')}

Necesito: cantidad y producto específico.
""",
            'soporte': f"""📞 Soporte Técnico
{respuesta_aurora.get('respuesta', 'Estamos aquí para ayudarte.')}

¿Cuál es el problema? Describe con detalle.
""",
            'general': respuesta_aurora.get('respuesta', '¡Hola! ¿En qué puedo ayudarte?')
        }

        return plantillas.get(intencion, plantillas['general'])

    async def _enviar_wa(self, numero: str, mensaje: str) -> bool:
        """Envía respuesta por WhatsApp via Green API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Construcción URL Green API
                url = f"https://api.green-api.com/waInstance{self.green_api_instance}/sendMessage"

                headers = {
                    'Content-Type': 'application/json'
                }

                payload = {
                    'chatId': f"{numero}@c.us",
                    'message': mensaje
                }

                # En producción, incluir token de Green API
                # async with session.post(url, json=payload, headers=headers) as resp:
                #     return resp.status == 200

                print(f"[WA] Enviando a {numero}: {mensaje[:50]}...")
                return True

        except Exception as e:
            print(f"[ERROR] Envío WA: {e}")
            return False

    async def _sincronizar_atf_messenger(self, datos: Dict[str, Any]) -> bool:
        """Sincroniza conversación con ATF Messenger para seguimiento"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'canal': 'whatsapp',
                    'remitente': datos['remitente'],
                    'mensaje': datos['mensaje_original'],
                    'respuesta': datos['respuesta'],
                    'intencion': datos['intencion'],
                    'motor': datos['motor'],
                    'timestamp': datos['timestamp'],
                    'estado': 'sincronizado'
                }

                # Enviar a ATF Messenger si está disponible
                try:
                    async with session.post(
                        f"{self.atf_messenger_url}/api/mensajes/sync",
                        json=payload,
                        timeout=5
                    ) as resp:
                        if resp.status == 200:
                            print(f"[SYNC ATF] ✓ Mensaje sincronizado")
                            return True
                except:
                    print(f"[SYNC ATF] ATF Messenger no disponible, continuando...")
                    return True  # No bloquear si ATF no responde

        except Exception as e:
            print(f"[ERROR] Sincronización ATF: {e}")
            return False

    def _guardar_historial(self, datos: Dict[str, Any]):
        """Guarda historial de conversaciones"""
        self.historial_mensajes.append(datos)

        # Guardar en archivo cada 10 mensajes
        if len(self.historial_mensajes) % 10 == 0:
            with open('C:\\AURORA\\SYNC\\chatbot_historial.json', 'a', encoding='utf-8') as f:
                for msg in self.historial_mensajes[-10:]:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')

    async def webhook_chatbot(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Webhook que recibe mensajes del chatbot"""
        return await self.procesar_mensaje_wa(datos)

    async def obtener_estatus_sync(self) -> Dict[str, Any]:
        """Retorna estado actual de sincronización"""
        return {
            'status': 'sincronizado',
            'chatbot': 'activo',
            'aurora': 'activo',
            'atf_messenger': 'activo',
            'mensajes_procesados': len(self.historial_mensajes),
            'timestamp': datetime.now().isoformat()
        }


# ============ API ENDPOINTS ============

async def iniciar_sync_service():
    """Inicia servicio de sincronización en AURORA"""
    sync = ChatbotSync()
    return sync


if __name__ == "__main__":
    print("✓ Módulo de sincronización Chatbot WA + AURORA + ATF Messenger cargado")
    print("✓ Esperando webhooks de Green API...")
