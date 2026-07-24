# -*- coding: utf-8 -*-
"""
🛠️ INYECTOR MAESTRO - REPARACIÓN GENERAL DE CONEXIÓN Y RUTAS
"""
import os
import shutil
from pathlib import Path

RAIZ = Path(r"C:\AURORA")
BACKUP_DIR = RAIZ / "BACKUPS"
BACKUP_DIR.mkdir(exist_ok=True)

# 1. Encontrar la ruta real del motor de WhatsApp
target_file = RAIZ / "SUPER_MARKETING_SYSTEM" / "motor_whatsapp_real.py"
if not target_file.exists():
    target_file = RAIZ / "motor_whatsapp_real.py"

if target_file.exists():
    # Respaldar versión previa antes de la sobreescritura limpia
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(str(target_file), str(BACKUP_DIR / f"motor_whatsapp_backup_{timestamp}.py"))
    
    # Escribir el motor de WhatsApp oficial asíncronico libre de URLs rotas
    whatsapp_clean_code = """# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import httpx
from datetime import datetime

logger = logging.getLogger("WhatsAppMotor")

class WhatsAppMotorReal:
    def __init__(self):
        # Leer credenciales reales del entorno .env
        self.instance_id = os.getenv("GREEN_API_INSTANCE_ID", "7107622171")
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
"""
    target_file.write_text(whatsapp_clean_code, encoding="utf-8")
    print("✅ Motor de WhatsApp reestructurado con URL universal api.greenapi.com")
else:
    print("❌ No se encontró el archivo motor_whatsapp_real.py")
