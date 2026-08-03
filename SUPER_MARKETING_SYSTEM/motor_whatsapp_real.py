# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import httpx
from datetime import datetime

logger = logging.getLogger("WhatsAppMotor")

class WhatsAppMotorReal:
    def __init__(self):
        # Leer credenciales reales del entorno .env
        self.instance_id = os.getenv("GREEN_API_INSTANCE", "7107622171")
        self.token = os.getenv("GREEN_API_TOKEN")
        # URL UNIVERSAL Y OFICIAL DE GREEN-API (Evita errores DNS)
        self.host = "https://greenapi.com"
        
    async def escuchar_mensajes(self):
        if not self.token:
            logger.error("❌ WhatsApp fuera de línea: GREEN_API_TOKEN no configurado.")
            return
            
        url = f"{self.host}/waInstance{self.instance_id}/receiveNotification/{self.token}"
        logger.info(f"🎧 Escuchando mensajes de WhatsApp en host seguro...")
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(url, timeout=20)
                    if response.status_code == 200 and response.json():
                        data = response.json()
                        # Aquí procesas la notificación con tu lógica unificada
                        receipt_id = data.get("receiptId")
                        if receipt_id:
                            # Confirmar recepción para limpiar la cola de Green-API
                            delete_url = f"{self.host}/waInstance{self.instance_id}/deleteNotification/{self.token}/{receipt_id}"
                            await client.delete(delete_url)
                    await asyncio.sleep(2)
                except httpx.RequestError as e:
                    logger.warning(f"⚠️ Alerta de red en WhatsApp (Reconectando de forma segura...): {e}")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"❌ Error en ciclo de WhatsApp: {e}")
                    await asyncio.sleep(5)

motor_whatsapp = WhatsAppMotorReal()
