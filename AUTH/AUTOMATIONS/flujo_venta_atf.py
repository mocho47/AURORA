# -*- coding: utf-8 -*-
"""FLUJO VENTA ATF - Automatización de venta end-to-end, CONECTADA A MOTORES REALES.

REGLA SAGRADA (Anuar): prohibido simular/inventar. Cada paso usa un motor REAL de AURORA:
  1. capturar_cliente   -> ORACLE/oracle_core.crear_lead        (lead REAL en oracle.db)
  2. generar_cotizacion -> TALLER/ordenes_taller.cotizar        (precio REAL del catálogo)
  3. enviar_cotizacion  -> PUBLICADOR/publicador_core.enviar_whatsapp (WhatsApp REAL)
  4. cierre_venta       -> ORACLE/oracle_core.convertir_lead_a_orden  (orden REAL en oracle.db)
  5. seguimiento_cliente-> VENDEDOR/seguimiento_ventas.mensaje_sugerido / enviar_seguimiento

DISEÑO: los pasos que ESCRIBEN o ENVÍAN (crear lead, crear orden, enviar whatsapp) reciben
`confirmar: bool = False`.
  - confirmar=False -> DRY-RUN REAL: calcula/prepara con datos verdaderos (precio de catálogo,
    texto real) pero NO ejecuta la acción irreversible, y lo declara ("simulado": True).
  - confirmar=True  -> ejecuta de verdad contra el motor.
Si un motor real falla o no está disponible, se propaga el error HONESTO; no se tapa con datos falsos.
"""
from __future__ import annotations

import asyncio
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# AUTH/AUTOMATIONS/flujo_venta_atf.py -> ROOT = C:\AURORA.worktrees
ROOT = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------------ carga de motores
def _mod(nombre: str, ruta: Path):
    """Carga un módulo por ruta con importlib (patrón estándar de AURORA)."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _oracle():
    return _mod("oracle_core", ROOT / "ORACLE" / "oracle_core.py")


def _ordenes_taller():
    return _mod("ordenes_taller", ROOT / "TALLER" / "ordenes_taller.py")


def _publicador():
    return _mod("publicador_core", ROOT / "PUBLICADOR" / "publicador_core.py")


def _seguimiento():
    return _mod("seguimiento_ventas", ROOT / "VENDEDOR" / "seguimiento_ventas.py")


class FlujoVentaATF:
    def __init__(self):
        self.nombre = "flujo_venta_atf"
        self.estado_actual = "esperando_cliente"
        self.cliente_actual: Dict[str, Any] = {}
        self.lead_id: Optional[int] = None
        self.cotizacion_actual: Dict[str, Any] = {}

    # ---------------------------------------------------------------- PASO 1: LEAD REAL
    async def capturar_cliente(self, nombre: str, telefono: str, email: str = "",
                               fuente: str = "flujo_venta", interes: str = "",
                               vehiculo: str = "", negocio: str = "atf",
                               confirmar: bool = False) -> Dict[str, Any]:
        """Paso 1: crea un lead REAL en el CRM Oracle (o dry-run si confirmar=False)."""
        self.cliente_actual = {
            "nombre": nombre, "telefono": telefono, "email": email,
            "interes": interes, "vehiculo": vehiculo, "negocio": negocio,
            "timestamp_ingreso": datetime.now().isoformat(timespec="seconds"),
        }
        base = {"paso": 1, "accion": "capturar_cliente", "cliente": self.cliente_actual}

        if not confirmar:
            self.estado_actual = "cliente_preparado"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje": "DRY-RUN: NO se creó lead. Con confirmar=True se registraría en oracle.db.",
                    "lead_id": None}
        try:
            lead = _oracle().crear_lead(
                nombre=nombre, telefono=telefono, fuente=fuente,
                negocio=negocio, vehiculo=vehiculo, interes=interes)
            self.lead_id = lead.get("id")
            self.estado_actual = "cliente_capturado"
            return {**base, "estado": self.estado_actual, "simulado": False,
                    "lead_id": self.lead_id, "lead": lead}
        except Exception as e:
            self.estado_actual = "error_capturar_cliente"
            return {**base, "estado": self.estado_actual, "error": str(e)}

    # ------------------------------------------------------------- PASO 2: análisis (RO)
    async def analizar_necesidad(self, necesidad: str) -> Dict[str, Any]:
        """Paso 2: análisis local, sin efectos (solo lectura)."""
        self.estado_actual = "necesidad_analizada"
        analisis = {
            "tipo": "retrofit" if "instalacion" in necesidad.lower() else "consulta",
            "urgencia": "alta" if "urgente" in necesidad.lower() else "normal",
            "texto": necesidad,
        }
        return {"paso": 2, "accion": "analizar_necesidad",
                "estado": self.estado_actual, "analisis": analisis}

    # -------------------------------------------------------- PASO 3: COTIZACIÓN REAL
    async def generar_cotizacion(self, producto: str, cantidad: int = 1) -> Dict[str, Any]:
        """Paso 3: cotización REAL contra el catálogo de TALLER (precio verdadero, NO inventa).
        Es de solo lectura, así que se ejecuta real siempre."""
        self.estado_actual = "generando_cotizacion"
        try:
            cot = _ordenes_taller().cotizar(producto, cantidad)
        except Exception as e:
            self.estado_actual = "error_cotizacion"
            return {"paso": 3, "accion": "generar_cotizacion",
                    "estado": self.estado_actual, "error": str(e)}

        self.cotizacion_actual = cot
        if cot.get("status") == "ok":
            self.estado_actual = "cotizacion_generada"
        else:
            # Honesto: no encontrado / varios / vacío -> se reporta tal cual, sin inventar precio.
            self.estado_actual = "cotizacion_sin_precio"
        return {"paso": 3, "accion": "generar_cotizacion",
                "estado": self.estado_actual, "cotizacion": cot}

    # ----------------------------------------------------- PASO 4: ENVÍO WHATSAPP REAL
    def _texto_cotizacion(self) -> str:
        c = self.cotizacion_actual
        nombre = self.cliente_actual.get("nombre", "")
        if c.get("status") == "ok":
            return (f"Hola {nombre}, gracias por tu interés. Cotización:\n"
                    f"{c['producto']} (x{c['cantidad']})\n"
                    f"Precio unitario: ${c['precio_unitario']}\n"
                    f"Subtotal: ${c['subtotal']}\n"
                    f"Quedamos atentos para agendar.")
        return (f"Hola {nombre}, sobre tu solicitud: aún no tengo el precio confirmado en catálogo, "
                f"te lo confirmo enseguida. No invento precios.")

    async def enviar_cotizacion(self, confirmar: bool = False) -> Dict[str, Any]:
        """Paso 4: prepara/envía la cotización por WhatsApp (REAL vía Green API)."""
        texto = self._texto_cotizacion()
        telefono = self.cliente_actual.get("telefono", "")
        base = {"paso": 4, "accion": "enviar_cotizacion", "metodo": "whatsapp",
                "destino": telefono, "texto": texto}

        if not confirmar:
            self.estado_actual = "cotizacion_preparada"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje": "DRY-RUN: NO se envió WhatsApp. Con confirmar=True se enviaría este texto."}
        if not telefono:
            self.estado_actual = "error_envio"
            return {**base, "estado": self.estado_actual,
                    "error": "Cliente sin teléfono; no se puede enviar WhatsApp."}
        try:
            res = _publicador().enviar_whatsapp(telefono, texto)
            self.estado_actual = "cotizacion_enviada" if res.get("status") == "ENVIADO" else "envio_fallido"
            return {**base, "estado": self.estado_actual, "simulado": False, "resultado": res}
        except Exception as e:
            self.estado_actual = "error_envio"
            return {**base, "estado": self.estado_actual, "error": str(e)}

    # --------------------------------------------------------- PASO 5: SEGUIMIENTO REAL
    async def seguimiento_cliente(self, confirmar: bool = False) -> Dict[str, Any]:
        """Paso 5: prepara (o envía) el mensaje de seguimiento del embudo real.
        Requiere lead_id real (existe solo tras capturar_cliente con confirmar=True)."""
        base = {"paso": 5, "accion": "seguimiento_cliente", "lead_id": self.lead_id}
        if self.lead_id is None:
            self.estado_actual = "seguimiento_sin_lead"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje": "No hay lead REAL (capturar_cliente fue dry-run). Sin lead no hay seguimiento real."}
        try:
            seg = _seguimiento()
            seg.sincronizar_leads()  # asegura que el lead del Oracle esté en el embudo
            sugerido = seg.mensaje_sugerido(self.lead_id)
        except Exception as e:
            self.estado_actual = "error_seguimiento"
            return {**base, "estado": self.estado_actual, "error": str(e)}

        mensaje = sugerido.get("mensaje", "")
        if not confirmar:
            self.estado_actual = "seguimiento_preparado"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje_sugerido": sugerido,
                    "nota": "DRY-RUN: NO se envió. Con confirmar=True se enviaría el mensaje sugerido."}
        try:
            res = seg.enviar_seguimiento(self.lead_id, mensaje)
            self.estado_actual = "en_seguimiento"
            return {**base, "estado": self.estado_actual, "simulado": False, "resultado": res}
        except Exception as e:
            self.estado_actual = "error_seguimiento"
            return {**base, "estado": self.estado_actual, "error": str(e)}

    # ------------------------------------------------------------ PASO 6: ORDEN REAL
    async def cierre_venta(self, servicio: str = "", precio: float = 0,
                           anticipo: float = 0, confirmar: bool = False) -> Dict[str, Any]:
        """Paso 6: convierte el lead REAL en orden REAL (oracle.db). Dry-run si confirmar=False."""
        # Si no pasan precio, usar el de la cotización real (nunca inventado).
        if not precio and self.cotizacion_actual.get("status") == "ok":
            precio = self.cotizacion_actual.get("subtotal", 0)
        if not servicio:
            servicio = self.cliente_actual.get("interes", "") or self.cotizacion_actual.get("producto", "")

        base = {"paso": 6, "accion": "cierre_venta", "lead_id": self.lead_id,
                "servicio": servicio, "precio": precio, "anticipo": anticipo}

        if self.lead_id is None:
            self.estado_actual = "cierre_sin_lead"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje": "No hay lead REAL (capturar_cliente fue dry-run). Sin lead no se crea orden."}
        if not confirmar:
            self.estado_actual = "cierre_preparado"
            return {**base, "estado": self.estado_actual, "simulado": True,
                    "mensaje": "DRY-RUN: NO se creó orden. Con confirmar=True se registraría en oracle.db."}
        try:
            res = _oracle().convertir_lead_a_orden(
                self.lead_id, servicio=servicio, precio=float(precio or 0),
                anticipo=float(anticipo or 0))
            self.estado_actual = "venta_cerrada"
            return {**base, "estado": self.estado_actual, "simulado": False, "resultado": res}
        except Exception as e:
            self.estado_actual = "error_cierre"
            return {**base, "estado": self.estado_actual, "error": str(e)}

    # ------------------------------------------------------------ ORQUESTACIÓN
    async def ejecutar_flujo_completo(self, datos_cliente: Dict,
                                      confirmar: bool = False) -> Dict[str, Any]:
        """Ejecuta el flujo completo. Con confirmar=False (default) TODO es dry-run REAL:
        trae datos verdaderos pero no crea lead/orden ni envía WhatsApp."""
        results = []
        results.append(await self.capturar_cliente(
            datos_cliente.get("nombre"), datos_cliente.get("telefono"),
            datos_cliente.get("email", ""), interes=datos_cliente.get("necesidad", ""),
            vehiculo=datos_cliente.get("vehiculo", ""),
            negocio=datos_cliente.get("negocio", "atf"), confirmar=confirmar))
        results.append(await self.analizar_necesidad(datos_cliente.get("necesidad", "")))
        results.append(await self.generar_cotizacion(
            datos_cliente.get("producto", ""), datos_cliente.get("cantidad", 1)))
        results.append(await self.enviar_cotizacion(confirmar=confirmar))
        results.append(await self.seguimiento_cliente(confirmar=confirmar))
        results.append(await self.cierre_venta(
            servicio=datos_cliente.get("necesidad", ""),
            precio=datos_cliente.get("precio", 0),
            anticipo=datos_cliente.get("anticipo", 0), confirmar=confirmar))
        return {
            "flujo": "venta_atf",
            "confirmar": confirmar,
            "estado_final": self.estado_actual,
            "lead_id": self.lead_id,
            "pasos": results,
            "cliente": self.cliente_actual.get("nombre"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


if __name__ == "__main__":
    datos = {
        "nombre": "Cliente Prueba",
        "telefono": "3320000000",
        "necesidad": "Instalación de faros",
        "producto": "termo",
        "cantidad": 2,
    }
    flujo = FlujoVentaATF()
    resultado = asyncio.run(flujo.ejecutar_flujo_completo(datos, confirmar=False))
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
