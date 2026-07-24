#!/usr/bin/env python3
"""FLUJO VENTA ATF - Automatización completa de venta end-to-end"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import sys
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

class FlujoVentaATF:
    def __init__(self):
        self.nombre = "flujo_venta_atf"
        self.estado_actual = "esperando_cliente"
        self.cliente_actual = {}

    async def capturar_cliente(self, nombre: str, telefono: str, email: str) -> Dict[str, Any]:
        """Paso 1: Captura datos del cliente"""
        self.cliente_actual = {
            "nombre": nombre,
            "telefono": telefono,
            "email": email,
            "timestamp_ingreso": datetime.now().isoformat()
        }
        self.estado_actual = "cliente_capturado"
        return {
            "paso": 1,
            "accion": "capturar_cliente",
            "estado": self.estado_actual,
            "cliente": self.cliente_actual
        }

    async def analizar_necesidad(self, necesidad: str) -> Dict[str, Any]:
        """Paso 2: Análisis de necesidad"""
        self.estado_actual = "analizando"
        analisis = {
            "tipo": "retrofit" if "instalacion" in necesidad.lower() else "consulta",
            "urgencia": "alta" if "urgente" in necesidad.lower() else "normal",
            "presupuesto": "flexible"
        }
        self.estado_actual = "necesidad_analizada"
        return {
            "paso": 2,
            "accion": "analizar_necesidad",
            "estado": self.estado_actual,
            "analisis": analisis
        }

    async def generar_cotizacion(self, cantidad: int = 1) -> Dict[str, Any]:
        """Paso 3: Genera cotización automática"""
        self.estado_actual = "generando_cotizacion"
        cotizacion = {
            "producto": "ATF Retrofit Kit",
            "cantidad": cantidad,
            "precio_unitario": 450,
            "total": 450 * cantidad,
            "impuestos": int(450 * cantidad * 0.16),
            "total_final": int(450 * cantidad * 1.16),
            "vigencia": "30 días",
            "id_cotizacion": f"COT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        self.estado_actual = "cotizacion_generada"
        return {
            "paso": 3,
            "accion": "generar_cotizacion",
            "estado": self.estado_actual,
            "cotizacion": cotizacion
        }

    async def enviar_cotizacion(self, metodo: str = "email") -> Dict[str, Any]:
        """Paso 4: Envía cotización por email/whatsapp"""
        self.estado_actual = "cotizacion_enviada"
        return {
            "paso": 4,
            "accion": "enviar_cotizacion",
            "estado": self.estado_actual,
            "metodo": metodo,
            "enviado_a": self.cliente_actual.get("email"),
            "timestamp": datetime.now().isoformat()
        }

    async def seguimiento_cliente(self) -> Dict[str, Any]:
        """Paso 5: Seguimiento automático"""
        self.estado_actual = "en_seguimiento"
        return {
            "paso": 5,
            "accion": "seguimiento_cliente",
            "estado": self.estado_actual,
            "proxima_accion": "Contacto en 24h",
            "timestamp": datetime.now().isoformat()
        }

    async def cierre_venta(self, confirmado: bool = True) -> Dict[str, Any]:
        """Paso 6: Cierre de venta y creación de pedido"""
        if confirmado:
            self.estado_actual = "venta_cerrada"
            pedido_id = f"PED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return {
                "paso": 6,
                "accion": "cierre_venta",
                "estado": self.estado_actual,
                "pedido_id": pedido_id,
                "cliente": self.cliente_actual.get("nombre"),
                "ingresos_generados": 522,  # 450 + 72 IVA
                "timestamp": datetime.now().isoformat()
            }
        return {
            "paso": 6,
            "accion": "venta_no_confirmada",
            "estado": "seguimiento_continuo"
        }

    async def ejecutar_flujo_completo(self, datos_cliente: Dict) -> Dict[str, Any]:
        """Ejecuta flujo completo sin parar"""
        results = []

        results.append(await self.capturar_cliente(
            datos_cliente.get("nombre"),
            datos_cliente.get("telefono"),
            datos_cliente.get("email")
        ))

        results.append(await self.analizar_necesidad(datos_cliente.get("necesidad", "")))
        results.append(await self.generar_cotizacion(datos_cliente.get("cantidad", 1)))
        results.append(await self.enviar_cotizacion("email"))
        results.append(await self.seguimiento_cliente())
        results.append(await self.cierre_venta(True))

        return {
            "flujo": "venta_atf",
            "estado_final": self.estado_actual,
            "pasos": results,
            "cliente": self.cliente_actual.get("nombre"),
            "duracion": f"{datetime.now().isoformat()}"
        }

if __name__ == "__main__":
    datos = {
        "nombre": "Juan Pérez",
        "telefono": "573001234567",
        "email": "juan@example.com",
        "necesidad": "Instalación urgente",
        "cantidad": 2
    }
    flujo = FlujoVentaATF()
    resultado = asyncio.run(flujo.ejecutar_flujo_completo(datos))
    print(json.dumps(resultado, indent=2))
