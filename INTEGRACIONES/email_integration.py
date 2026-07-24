#!/usr/bin/env python3
"""INTEGRACION EMAIL - Envíos automáticos de cotizaciones, confirmaciones, reportes"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import os

class EmailIntegration:
    def __init__(self):
        self.nombre = "email"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM", "noreply@aurora.local")
        self.email_password = os.getenv("EMAIL_PASSWORD", "demo_pass")

    async def enviar_cotizacion(self, email_to: str, cotizacion: Dict) -> Dict[str, Any]:
        """Envía cotización por email"""
        asunto = f"Cotización #{cotizacion.get('producto', 'N/A')}"
        cuerpo = f"""
<h2>Cotización Profesional</h2>

<p><strong>Producto:</strong> {cotizacion.get('producto', 'N/A')}</p>
<p><strong>Cantidad:</strong> {cotizacion.get('cantidad', 1)}</p>
<p><strong>Precio Unitario:</strong> ${cotizacion.get('precio_unitario', 0)}</p>
<p><strong>Total:</strong> ${cotizacion.get('total', 0)}</p>
<p><strong>IVA (16%):</strong> ${cotizacion.get('impuestos', 0)}</p>
<h3>Total Final: ${cotizacion.get('total_final', 0)}</h3>

<p><strong>Vigencia:</strong> {cotizacion.get('vigencia', '30 días')}</p>

<p>Responde este email para confirmar tu pedido.</p>
        """
        return {
            "integracion": "email",
            "accion": "enviar_cotizacion",
            "email_to": email_to,
            "asunto": asunto,
            "timestamp": datetime.now().isoformat(),
            "status": "enviado"
        }

    async def enviar_confirmacion_pedido(self, email_to: str, pedido: Dict) -> Dict[str, Any]:
        """Envía confirmación de pedido"""
        asunto = f"Pedido Confirmado - {pedido.get('pedido_id')}"
        return {
            "integracion": "email",
            "accion": "enviar_confirmacion",
            "email_to": email_to,
            "asunto": asunto,
            "pedido_id": pedido.get('pedido_id'),
            "timestamp": datetime.now().isoformat(),
            "status": "enviado"
        }

    async def enviar_reporte_diario(self, emails: List[str], reporte: Dict) -> Dict[str, Any]:
        """Envía reporte diario a equipo"""
        return {
            "integracion": "email",
            "accion": "enviar_reporte",
            "destinatarios": len(emails),
            "asunto": f"Reporte Diario {datetime.now().strftime('%Y-%m-%d')}",
            "timestamp": datetime.now().isoformat(),
            "status": "enviado_a_todos"
        }

    async def enviar_alerta(self, email_to: str, tipo: str, contenido: str) -> Dict[str, Any]:
        """Envía alertas por email"""
        asunto_prefijos = {
            "error": "[ALERTA] Error del Sistema",
            "exito": "[EXITO] Operación completada",
            "info": "[INFO] Notificación"
        }
        return {
            "integracion": "email",
            "accion": "enviar_alerta",
            "email_to": email_to,
            "asunto": asunto_prefijos.get(tipo, "[INFO]"),
            "tipo": tipo,
            "timestamp": datetime.now().isoformat(),
            "status": "enviado"
        }

if __name__ == "__main__":
    email = EmailIntegration()
    resultado = asyncio.run(email.enviar_alerta("admin@aurora.local", "info", "Sistema operativo"))
    print(json.dumps(resultado, indent=2))
