# -*- coding: utf-8 -*-
from pathlib import Path

target_file = Path(r"C:\AURORA\SUPER_MARKETING_SYSTEM\motor_whatsapp_real.py")
if not target_file.exists():
    target_file = Path(r"C:\AURORA\motor_whatsapp_real.py")

whatsapp_code = """# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import urllib.request
import json

logger = logging.getLogger("WhatsAppMotor")

class WhatsAppMotorReal:
    def __init__(self):
        # Leer variables directas del entorno
        self.instance_id = os.environ.get("GREEN_API_INSTANCE_ID", "7107622171").strip()
        self.token = os.environ.get("GREEN_API_TOKEN", "").strip()
        self.host = "https://greenapi.com"
        
    async def escuchar_mensajes(self):
        # Si está vacío o tiene el tag por defecto, no detener el Hub, correr en bypass seguro
        if not self.token or self.token.startswith("your_"):
            logger.warning("⚠️ WhatsApp en modo de espera: GREEN_API_TOKEN no configurado en .env")
            return
            
        url = f"{self.host}/waInstance{self.instance_id}/receiveNotification/{self.token}"
        logger.info("🎧 Escuchando notificaciones de Green-API de forma segura...")
        
        while True:
            try:
                # Usamos la librería nativa de Python (urllib) para evitar choques con httpx de Supabase
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        res_data = json.loads(response.read().decode("utf-8"))
                        if res_data and "receiptId" in res_data:
                            r_id = res_data["receiptId"]
                            del_url = f"{self.host}/waInstance{self.instance_id}/deleteNotification/{self.token}/{r_id}"
                            del_req = urllib.request.Request(del_url, method="DELETE")
                            with urllib.request.urlopen(del_req, timeout=10) as del_res:
                                pass
                await asyncio.sleep(3)
            except Exception as e:
                # Captura caídas de internet sin tirar la API del puerto 5000
                await asyncio.sleep(5)

motor_whatsapp = WhatsAppMotorReal()
"""
target_file.write_text(whatsapp_code, encoding="utf-8")
print("✅ Motor de WhatsApp blindado con conector nativo de Windows.")
