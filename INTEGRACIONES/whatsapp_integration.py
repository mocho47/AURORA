# -*- coding: utf-8 -*-
"""
AURORA — INTEGRACION WHATSAPP
HTTP real via httpx + Green API. Sin simulaciones. Sin returns fake.
Patron: https://{server}.api.greenapi.com/waInstance{id}/{action}/{token}
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger("aurora.whatsapp")


class WhatsAppIntegration:
    def __init__(self):
        self.instance_id = os.getenv("GREEN_API_INSTANCE", os.getenv("GREEN_INSTANCE_ID", ""))
        self.token = os.getenv("GREEN_API_TOKEN", os.getenv("GREEN_API_KEY", ""))
        srv = os.getenv("GREEN_API_SERVER", "")
        host = f"https://{srv}.api.greenapi.com" if srv else "https://api.green-api.com"
        self._base = f"{host}/waInstance{self.instance_id}"

    def _disponible(self) -> bool:
        return bool(self.instance_id and self.token
                    and not self.instance_id.startswith("your_")
                    and not self.token.startswith("your_"))

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> Dict[str, Any]:
        """Envia mensaje de texto via Green API (HTTP real)."""
        if not self._disponible():
            logger.warning("WhatsApp: credenciales no configuradas")
            return {"status": "NO_CREDENCIALES", "telefono": telefono}

        # Green API espera el numero con codigo pais sin +, sufijo @c.us
        chat_id = telefono.replace("+", "").replace(" ", "") + "@c.us"
        url = f"{self._base}/sendMessage/{self.token}"
        payload = {"chatId": chat_id, "message": mensaje}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                return {
                    "status": "ENVIADO",
                    "telefono": telefono,
                    "message_id": data.get("idMessage", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"WA HTTP error {e.response.status_code}: {e.response.text[:200]}")
            return {"status": "ERROR_HTTP", "codigo": e.response.status_code}
        except Exception as e:
            logger.error(f"WA error: {e}")
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def enviar_cotizacion(self, telefono: str, cotizacion: Dict) -> Dict[str, Any]:
        """Formatea y envia una cotizacion por WhatsApp."""
        folio = cotizacion.get("folio", "")
        negocio = cotizacion.get("negocio", "").upper()
        texto_cot = cotizacion.get("cotizacion", cotizacion.get("respuesta", ""))
        partes = [
            f"*COTIZACION {folio}*",
            f"Negocio: {negocio}",
            "",
            texto_cot,
            "",
            "Responde SI para confirmar o haz tus preguntas.",
        ]
        mensaje = "\n".join(partes)
        return await self.enviar_mensaje(telefono, mensaje)

    async def enviar_confirmacion_pedido(self, telefono: str, pedido: Dict) -> Dict[str, Any]:
        """Envia confirmacion de pedido al cliente."""
        partes = [
            "*PEDIDO CONFIRMADO*",
            f"ID: {pedido.get('pedido_id', '')}",
            f"Cliente: {pedido.get('cliente', '')}",
            f"Producto: {pedido.get('producto', '')}",
            f"Total: ${pedido.get('precio', 0):,.0f} MXN",
            f"Estado: {pedido.get('estado', 'pendiente')}",
            "",
            "Nos pondremos en contacto para coordinar.",
        ]
        mensaje = "\n".join(partes)
        return await self.enviar_mensaje(telefono, mensaje)

    async def recibir_mensajes(self) -> Dict[str, Any]:
        """Polling de mensajes nuevos desde Green API."""
        if not self._disponible():
            return {"status": "NO_CREDENCIALES", "mensajes": []}
        url = f"{self._base}/receiveNotification/{self.token}"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                if r.status_code == 200 and r.text.strip() not in ("", "null"):
                    data = r.json()
                    receipt_id = data.get("receiptId") if data else None
                    if receipt_id:
                        await self._confirmar_recepcion(receipt_id)
                    return {"status": "OK", "mensajes": [data] if data else []}
            return {"status": "OK", "mensajes": []}
        except Exception as e:
            logger.error(f"WA recibir error: {e}")
            return {"status": "ERROR", "mensajes": [], "detalle": str(e)[:200]}

    async def _confirmar_recepcion(self, receipt_id: int) -> None:
        url = f"{self._base}/deleteNotification/{self.token}/{receipt_id}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.delete(url)
        except Exception:
            pass

    async def escuchar(self, callback) -> None:
        """Bucle de escucha continua. callback(data) se llama con cada mensaje."""
        logger.info("[WA] Iniciando escucha de mensajes...")
        while True:
            try:
                result = await self.recibir_mensajes()
                for msg in result.get("mensajes", []):
                    if msg:
                        await callback(msg)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"[WA] Error en ciclo: {e}")
                await asyncio.sleep(5)

    def get_status(self) -> Dict:
        return {
            "disponible": self._disponible(),
            "instance_id": self.instance_id[:6] + "***" if self.instance_id else "no configurado",
        }


whatsapp = WhatsAppIntegration()
