#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escribe FASES 2-6 de AURORA: bus, whatsapp, run_aurora, server.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

archivos = {}

# ═══════════════════════════════════════════════════════════
# FASE 2 — CEREBRO/registrador_bus.py
# Conecta todos los motores al bus neuronal multidireccional
# ═══════════════════════════════════════════════════════════
archivos["CEREBRO/registrador_bus.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — REGISTRADOR DE BUS NEURONAL
Conecta todos los motores al bus para interconexion multidireccional real.
Pub/Sub: cualquier motor puede publicar y suscribirse a cualquier evento.
"""
import asyncio
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from CEREBRO.bus_neuronal import bus, Mensaje, TipoMensaje

logger = logging.getLogger("aurora.registrador_bus")


# ─────────────────────────────────────────────────────────────────────
# UTILIDAD: carga un motor por nombre
# ─────────────────────────────────────────────────────────────────────

def _cargar_motor(nombre: str):
    ruta = ROOT / "MOTORES" / f"{nombre}.py"
    if not ruta.exists():
        return None
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return getattr(mod, "motor", None)
    except Exception as e:
        logger.error(f"Error cargando {nombre}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# FABRICA DE CALLBACKS
# Cada motor expone un metodo principal distinto.
# El callback traduce Mensaje → llamada real al metodo.
# ─────────────────────────────────────────────────────────────────────

def _callback_para(motor_obj, metodo_principal: str):
    """
    Devuelve un callback async que:
    1. Extrae consulta/contexto del mensaje
    2. Llama al metodo real del motor
    3. Retorna el resultado (para request-response)
    """
    async def callback(msg: Mensaje) -> Optional[dict]:
        consulta = (
            msg.contenido.get("consulta")
            or msg.contenido.get("mensaje")
            or msg.contenido.get("datos")
            or str(msg.contenido)
        )
        contexto = msg.contenido.get("contexto", {})
        try:
            metodo = getattr(motor_obj, metodo_principal, None)
            if metodo:
                return await metodo(consulta, contexto)
        except Exception as e:
            logger.error(f"Error en callback {motor_obj.motor_id}.{metodo_principal}: {e}")
        return None
    return callback


def _callback_oracle(motor_obj):
    """Callback especial para MotorOracle (metodos multiples)."""
    async def callback(msg: Mensaje) -> Optional[dict]:
        accion = msg.contenido.get("accion", "resumen")
        try:
            if accion == "crear_lead":
                return await motor_obj.crear_lead(
                    msg.contenido.get("nombre", ""),
                    msg.contenido.get("telefono", ""),
                    msg.contenido.get("negocio", "atf"),
                )
            elif accion == "listar_leads":
                return await motor_obj.listar_leads(msg.contenido.get("estado"))
            else:
                return await motor_obj.resumen(msg.contenido.get("negocio"))
        except Exception as e:
            logger.error(f"Error callback oracle: {e}")
        return None
    return callback


def _callback_pedidos(motor_obj):
    """Callback especial para MotorPedidos."""
    async def callback(msg: Mensaje) -> Optional[dict]:
        accion = msg.contenido.get("accion", "capturar")
        try:
            if accion == "listar":
                return await motor_obj.listar(msg.contenido.get("estado"))
            elif accion == "actualizar":
                return await motor_obj.actualizar_estado(
                    msg.contenido.get("pedido_id", ""),
                    msg.contenido.get("nuevo_estado", "pendiente"),
                )
            else:
                return await motor_obj.capturar(
                    msg.contenido.get("datos", ""),
                    msg.contenido.get("contexto", {}),
                )
        except Exception as e:
            logger.error(f"Error callback pedidos: {e}")
        return None
    return callback


def _callback_marketing(motor_obj):
    """Callback especial para MotorMarketing."""
    async def callback(msg: Mensaje) -> Optional[dict]:
        accion = msg.contenido.get("accion", "generar_contenido")
        try:
            if accion == "estrategia":
                return await motor_obj.estrategia_semanal(
                    msg.contenido.get("objetivo", "leads ATF")
                )
            else:
                return await motor_obj.generar_contenido(
                    tipo=msg.contenido.get("tipo", "hook"),
                    plataforma=msg.contenido.get("plataforma", "tiktok"),
                    producto=msg.contenido.get("producto", "ATF Retrofit LED"),
                    contexto_extra=msg.contenido.get("contexto_extra", ""),
                )
        except Exception as e:
            logger.error(f"Error callback marketing: {e}")
        return None
    return callback


# ─────────────────────────────────────────────────────────────────────
# REGISTRO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────

async def registrar_todos_los_motores() -> dict:
    """
    Carga y registra todos los motores en el bus neuronal.
    Configura suscripciones cruzadas para interconexion real.
    Retorna dict con resultado de cada motor.
    """
    resultado = {}

    # ── Motores LLM (MOTORES/) ──────────────────────────────────────
    motores_llm = {
        "motor_analisis":      ("analizar",  None),
        "motor_coaching":      ("coach",     None),
        "motor_coaching_real": ("sesion_coaching", None),
        "motor_code_gen":      ("generar",   None),
        "motor_cotizador":     ("cotizar",   None),
        "motor_imagenes":      ("analizar",  None),
        "motor_negocios":      ("consultar", None),
        "motor_reasoning":     ("razonar",   None),
        "motor_ventas":        ("procesar",  None),
    }

    for motor_id, (metodo, _) in motores_llm.items():
        motor_obj = _cargar_motor(motor_id)
        if motor_obj:
            cb = _callback_para(motor_obj, metodo)
            bus.registrar(motor_id, cb)
            resultado[motor_id] = "registrado"
            logger.info(f"[BUS] Registrado: {motor_id}")
        else:
            resultado[motor_id] = "no_cargado"
            logger.warning(f"[BUS] No se pudo cargar: {motor_id}")

    # ── motor_marketing (callback especial) ────────────────────────
    m_marketing = _cargar_motor("motor_marketing")
    if m_marketing:
        bus.registrar("motor_marketing", _callback_marketing(m_marketing))
        resultado["motor_marketing"] = "registrado"
        logger.info("[BUS] Registrado: motor_marketing")

    # ── motor_pedidos (callback especial) ──────────────────────────
    m_pedidos = _cargar_motor("motor_pedidos")
    if m_pedidos:
        bus.registrar("motor_pedidos", _callback_pedidos(m_pedidos))
        resultado["motor_pedidos"] = "registrado"
        logger.info("[BUS] Registrado: motor_pedidos")

    # ── MotorOracle (desde adaptadores) ────────────────────────────
    try:
        sys.path.insert(0, str(ROOT / "MOTORES"))
        import adaptadores as _adap
        oracle_obj = _adap.MotorOracle()
        bus.registrar("motor_oracle", _callback_oracle(oracle_obj))
        resultado["motor_oracle"] = "registrado"
        logger.info("[BUS] Registrado: motor_oracle (ORACLE SQLite)")
    except Exception as e:
        resultado["motor_oracle"] = f"error: {e}"
        logger.warning(f"[BUS] motor_oracle: {e}")

    # ── SUSCRIPCIONES CRUZADAS ──────────────────────────────────────
    # Cuando llega un nuevo lead → motor_ventas lo recibe
    m_ventas = _cargar_motor("motor_ventas")
    if m_ventas:
        bus.suscribir(
            "motor_ventas",
            TipoMensaje.EVENTO,
            _callback_para(m_ventas, "procesar"),
        )
        logger.info("[BUS] Suscripcion: motor_ventas <- EVENTO")

    # Cuando se genera contenido → motor_marketing lo puede recibir para aprender
    if m_marketing:
        bus.suscribir(
            "motor_marketing",
            TipoMensaje.APRENDIZAJE,
            _callback_marketing(m_marketing),
        )
        logger.info("[BUS] Suscripcion: motor_marketing <- APRENDIZAJE")

    # motor_reasoning escucha decisiones para mejorar su modelo
    m_reasoning = _cargar_motor("motor_reasoning")
    if m_reasoning:
        bus.suscribir(
            "motor_reasoning",
            TipoMensaje.DECISION,
            _callback_para(m_reasoning, "razonar"),
        )
        logger.info("[BUS] Suscripcion: motor_reasoning <- DECISION")

    registrados = sum(1 for v in resultado.values() if v == "registrado")
    logger.info(f"[BUS] Total registrados: {registrados}/{len(resultado)}")
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# FASE 4 — INTEGRACIONES/whatsapp_integration.py
# HTTP real via httpx + Green API
# ═══════════════════════════════════════════════════════════
archivos["INTEGRACIONES/whatsapp_integration.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — INTEGRACION WHATSAPP
HTTP real via httpx + Green API. Sin simulaciones. Sin returns fake.
Patron: https://greenapi.com/waInstance{id}/{action}/{token}
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger("aurora.whatsapp")

GREEN_HOST = "https://greenapi.com"


class WhatsAppIntegration:
    def __init__(self):
        self.instance_id = os.getenv("GREEN_API_INSTANCE", os.getenv("GREEN_INSTANCE_ID", ""))
        self.token = os.getenv("GREEN_API_TOKEN", os.getenv("GREEN_API_KEY", ""))
        self._base = f"{GREEN_HOST}/waInstance{self.instance_id}"

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
        mensaje = (
            f"*COTIZACION {folio}*\n"
            f"Negocio: {negocio}\n\n"
            f"{texto_cot}\n\n"
            f"Responde SI para confirmar o haz tus preguntas."
        )
        return await self.enviar_mensaje(telefono, mensaje)

    async def enviar_confirmacion_pedido(self, telefono: str, pedido: Dict) -> Dict[str, Any]:
        """Envia confirmacion de pedido al cliente."""
        mensaje = (
            f"*PEDIDO CONFIRMADO*\n"
            f"ID: {pedido.get('pedido_id', '')}\n"
            f"Cliente: {pedido.get('cliente', '')}\n"
            f"Producto: {pedido.get('producto', '')}\n"
            f"Total: ${pedido.get('precio', 0):,.0f} MXN\n"
            f"Estado: {pedido.get('estado', 'pendiente')}\n\n"
            f"Nos pondremos en contacto para coordinar."
        )
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
'''

# ═══════════════════════════════════════════════════════════
# FASE 5 — run_aurora.py (entry point unificado real)
# ═══════════════════════════════════════════════════════════
archivos["run_aurora.py"] = '''\
# -*- coding: utf-8 -*-
"""
AURORA — PUNTO DE ENTRADA UNIFICADO
Secuencia real de arranque:
  1. Memoria (SQLite WAL)
  2. Bus Neuronal (pub/sub async)
  3. Registro de todos los motores en el bus
  4. Consciencia (router LLM)
  5. Motor de Sueno (aprendizaje en background)
  6. WhatsApp listener (background)
  7. FastAPI + uvicorn

Sin simulaciones. Sin shortcuts.
"""
import asyncio
import io
import logging
import os
import sys
from pathlib import Path

# UTF-8 en consola Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SUPER_MARKETING_SYSTEM"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("AURORA")


def _verificar_puerto(host: str, port: int) -> None:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((host, port)) == 0:
            logger.warning(f"Puerto {port} en uso. Puede que AURORA ya este corriendo.")


async def _arrancar() -> None:
    # 1. MEMORIA ──────────────────────────────────────────────────────
    logger.info("[1/6] Inicializando memoria SQLite...")
    from MEMORIA.sistema_memoria import memoria
    await memoria.inicializar()
    logger.info("      Memoria lista.")

    # 2. BUS NEURONAL ─────────────────────────────────────────────────
    logger.info("[2/6] Iniciando Bus Neuronal...")
    from CEREBRO.bus_neuronal import bus
    await bus.iniciar()
    logger.info("      Bus activo.")

    # 3. REGISTRO DE MOTORES ─────────────────────────────────────────
    logger.info("[3/6] Registrando motores en bus...")
    from CEREBRO.registrador_bus import registrar_todos_los_motores
    resultado = await registrar_todos_los_motores()
    registrados = sum(1 for v in resultado.values() if v == "registrado")
    logger.info(f"      {registrados}/{len(resultado)} motores registrados.")

    # 4. CONSCIENCIA ─────────────────────────────────────────────────
    logger.info("[4/6] Inicializando Consciencia...")
    from CEREBRO.consciencia import consciencia
    await consciencia.inicializar()
    logger.info("      Consciencia lista.")

    # 5. MOTOR DE SUENO ──────────────────────────────────────────────
    logger.info("[5/6] Activando Motor de Sueno...")
    try:
        from MEMORIA.motor_sueno import motor_sueno
        asyncio.create_task(motor_sueno.iniciar_vigilancia(), name="motor_sueno")
        logger.info("      Motor de Sueno activo (consolidacion cada 60s).")
    except Exception as e:
        logger.warning(f"      Motor de Sueno no disponible: {e}")

    # 6. WHATSAPP LISTENER ───────────────────────────────────────────
    logger.info("[6/6] Iniciando WhatsApp listener...")
    try:
        from INTEGRACIONES.whatsapp_integration import whatsapp

        async def _procesar_wa(data: dict) -> None:
            body = data.get("body", {})
            tipo = body.get("typeWebhook", "")
            if tipo == "incomingMessageReceived":
                msg_data = body.get("messageData", {})
                texto = msg_data.get("textMessageData", {}).get("textMessage", "")
                sender = body.get("senderData", {}).get("sender", "")
                if texto and sender:
                    resultado = await consciencia.procesar(
                        mensaje=texto,
                        user_id=sender,
                        canal="whatsapp",
                    )
                    respuesta = resultado.get("respuesta", "")
                    if respuesta:
                        telefono = sender.replace("@c.us", "")
                        await whatsapp.enviar_mensaje(telefono, respuesta)

        asyncio.create_task(whatsapp.escuchar(_procesar_wa), name="wa_listener")
        logger.info("      WhatsApp listener activo.")
    except Exception as e:
        logger.warning(f"      WhatsApp no disponible: {e}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("  AURORA completamente inicializada")
    logger.info("  Motor LLM : llama-3.1-8b-instant (Groq)")
    logger.info(f"  Motores   : {registrados} activos en el bus")
    logger.info("  Memoria   : SQLite WAL (episodica + semantica)")
    logger.info("  Sueno     : consolidacion automatica activa")
    logger.info("  API       : http://0.0.0.0:5000")
    logger.info("  Docs      : http://0.0.0.0:5000/docs")
    logger.info("=" * 60)
    logger.info("")


def main() -> None:
    import uvicorn

    # Importar la app FastAPI (que ahora usa consciencia como router)
    from CORE.aurora_server import app

    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "5000"))
    _verificar_puerto(host, port)

    # Arrancar subsistemas antes de que uvicorn empiece a servir
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_arrancar())

    # Servir con uvicorn usando el loop ya configurado
    uvicorn.run(
        app,
        host=host,
        port=port,
        loop="none",  # usamos el loop ya creado
        log_level="warning",  # logs de uvicorn minimizados
    )


if __name__ == "__main__":
    main()
'''

# ═══════════════════════════════════════════════════════════
# FASE 6 — CORE/aurora_server.py (conectar /procesar a consciencia)
# Solo se agrega el nuevo endpoint /chat que usa consciencia.
# /procesar se mantiene compatible con la arquitectura vieja.
# ═══════════════════════════════════════════════════════════
# (No se reescribe completo — se agrega el endpoint en la fase de edicion)

# ─────────────────────────────────────────────────────────────────────
# ESCRITURA REAL
# ─────────────────────────────────────────────────────────────────────
ok = 0
errores = []
for ruta_rel, contenido in archivos.items():
    ruta = ROOT / ruta_rel
    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        size = os.path.getsize(ruta)
        print(f"OK   {ruta_rel}  ({size:,} bytes)")
        ok += 1
    except Exception as e:
        msg = f"ERROR  {ruta_rel}  {e}"
        print(msg)
        errores.append(msg)

print()
print(f"Escritos: {ok}/{len(archivos)}  |  Errores: {len(errores)}")
