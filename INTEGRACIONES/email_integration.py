#!/usr/bin/env python3
"""INTEGRACION EMAIL - Envíos automáticos de cotizaciones, confirmaciones, reportes.
100% HONESTO: envía REAL por SMTP cuando hay credenciales. Si faltan, lo DICE
(status FALTA_CREDENCIALES). NUNCA regresa "enviado" sin haber mandado nada."""

import asyncio
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any, List
import os

class EmailIntegration:
    def __init__(self):
        self.nombre = "email"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")

    def _configurado(self) -> bool:
        return bool(self.email_from and self.email_password)

    def _enviar_smtp_sync(self, destinatarios: List[str], asunto: str, cuerpo_html: str) -> Dict[str, Any]:
        if not self._configurado():
            return {"status": "FALTA_CREDENCIALES",
                    "detalle": "Falta EMAIL_FROM o EMAIL_PASSWORD en .env. No se envía nada — no se simula."}
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = self.email_from
            msg["To"] = ", ".join(destinatarios)
            msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as s:
                s.starttls()
                s.login(self.email_from, self.email_password)
                s.sendmail(self.email_from, destinatarios, msg.as_string())
            return {"status": "enviado"}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:250]}

    async def enviar_cotizacion(self, email_to: str, cotizacion: Dict) -> Dict[str, Any]:
        """Envía cotización por email REAL vía SMTP."""
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
        r = await asyncio.to_thread(self._enviar_smtp_sync, [email_to], asunto, cuerpo)
        return {"integracion": "email", "accion": "enviar_cotizacion", "email_to": email_to,
                "asunto": asunto, "timestamp": datetime.now().isoformat(), **r}

    async def enviar_confirmacion_pedido(self, email_to: str, pedido: Dict) -> Dict[str, Any]:
        """Envía confirmación de pedido REAL vía SMTP."""
        asunto = f"Pedido Confirmado - {pedido.get('pedido_id')}"
        cuerpo = f"<h2>Pedido confirmado</h2><p>Pedido: {pedido.get('pedido_id')}</p>"
        r = await asyncio.to_thread(self._enviar_smtp_sync, [email_to], asunto, cuerpo)
        return {"integracion": "email", "accion": "enviar_confirmacion", "email_to": email_to,
                "asunto": asunto, "pedido_id": pedido.get('pedido_id'),
                "timestamp": datetime.now().isoformat(), **r}

    async def enviar_reporte_diario(self, emails: List[str], reporte: Dict) -> Dict[str, Any]:
        """Envía reporte diario a equipo REAL vía SMTP."""
        asunto = f"Reporte Diario {datetime.now().strftime('%Y-%m-%d')}"
        cuerpo = f"<h2>Reporte diario</h2><pre>{json.dumps(reporte, ensure_ascii=False, indent=2)}</pre>"
        r = await asyncio.to_thread(self._enviar_smtp_sync, emails, asunto, cuerpo)
        estado = ("enviado_a_todos" if r.get("status") == "enviado" else r.get("status"))
        return {"integracion": "email", "accion": "enviar_reporte", "destinatarios": len(emails),
                "asunto": asunto, "timestamp": datetime.now().isoformat(),
                **{**r, "status": estado}}

    async def enviar_alerta(self, email_to: str, tipo: str, contenido: str) -> Dict[str, Any]:
        """Envía alertas por email REAL vía SMTP."""
        asunto_prefijos = {
            "error": "[ALERTA] Error del Sistema",
            "exito": "[EXITO] Operación completada",
            "info": "[INFO] Notificación"
        }
        asunto = asunto_prefijos.get(tipo, "[INFO]")
        cuerpo = f"<p>{contenido}</p>"
        r = await asyncio.to_thread(self._enviar_smtp_sync, [email_to], asunto, cuerpo)
        return {"integracion": "email", "accion": "enviar_alerta", "email_to": email_to,
                "asunto": asunto, "tipo": tipo, "timestamp": datetime.now().isoformat(), **r}

if __name__ == "__main__":
    email = EmailIntegration()
    resultado = asyncio.run(email.enviar_alerta("admin@aurora.local", "info", "Sistema operativo"))
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
