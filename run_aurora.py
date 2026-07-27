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
sys.path.insert(0, str(ROOT / "CORE"))           # aurora.py, aurora_selector, etc.
sys.path.insert(0, str(ROOT / "SUPER_MARKETING_SYSTEM"))

# Cargar credenciales del .env como fuente única de verdad.
# (override=False: si una variable ya existe en el SO, se respeta; las faltantes
#  se llenan desde .env. Evita depender de variables de entorno del sistema.)
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

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
        asyncio.create_task(motor_sueno.iniciar(), name="motor_sueno")
        logger.info("      Motor de Sueno activo (consolidacion cada 60s).")
    except Exception as e:
        logger.warning(f"      Motor de Sueno no disponible: {e}")

    # 6. WHATSAPP LISTENER ───────────────────────────────────────────
    logger.info("[6/6] Iniciando WhatsApp listener...")
    try:
        from collections import deque
        from INTEGRACIONES.whatsapp_integration import whatsapp

        # Dedup real por idMessage: con el reordenamiento de ack (procesar antes de
        # confirmar recepción, whatsapp_integration.py) un fallo de red al borrar la
        # notificación puede hacer que Green API reentregue el mismo mensaje — sin
        # esto, se respondería 2 veces al mismo cliente por el mismo mensaje.
        _wa_ids_vistos = deque(maxlen=200)
        _wa_ids_set = set()

        def _wa_ya_procesado(id_msg: str) -> bool:
            if not id_msg:
                return False
            if id_msg in _wa_ids_set:
                return True
            if len(_wa_ids_vistos) == _wa_ids_vistos.maxlen:
                _wa_ids_set.discard(_wa_ids_vistos[0])
            _wa_ids_vistos.append(id_msg)
            _wa_ids_set.add(id_msg)
            return False

        async def _procesar_wa(data: dict) -> None:
            body = data.get("body", {})
            tipo = body.get("typeWebhook", "")
            if tipo == "incomingMessageReceived":
                id_msg = body.get("idMessage", "")
                if _wa_ya_procesado(id_msg):
                    logger.info(f"      [WA] Mensaje {id_msg} ya procesado, ignoro duplicado.")
                    return
                msg_data = body.get("messageData", {})
                texto = msg_data.get("textMessageData", {}).get("textMessage", "")
                sender = body.get("senderData", {}).get("sender", "")
                if texto and sender:
                    telefono = sender.replace("@c.us", "")
                    # Captura de lead en el CRM (solo 1ra vez por telefono, sin duplicar).
                    # Best-effort: si falla, NUNCA bloquea la respuesta al cliente.
                    try:
                        from ORACLE import oracle_core
                        ya = any((l.get("telefono") or "").replace("@c.us", "") == telefono
                                 for l in oracle_core.listar_leads())
                        if not ya:
                            oracle_core.crear_lead(
                                nombre=f"WhatsApp {telefono}", telefono=telefono,
                                fuente="whatsapp", negocio="milens",
                                interes=texto[:200],
                                notas="Auto-capturado del chat de WhatsApp de AURORA")
                            logger.info(f"      [WA] Lead nuevo capturado: {telefono}")
                    except Exception as e:
                        logger.warning(f"      [WA] No se pudo registrar lead: {e}")
                    # Responder al cliente con el cerebro (cotiza con catalogo real)
                    resultado = await consciencia.procesar(
                        mensaje=texto,
                        user_id=sender,
                        canal="whatsapp",
                    )
                    respuesta = resultado.get("respuesta", "")
                    if respuesta:
                        r_envio = await whatsapp.enviar_mensaje(telefono, respuesta)
                        if r_envio.get("status") != "ENVIADO":
                            # Antes este resultado se descartaba -- el cliente real
                            # nunca recibía nada y no quedaba ningún rastro del fallo.
                            logger.error(f"      [WA] FALLO envío real a {telefono}: {r_envio}")

        asyncio.create_task(whatsapp.escuchar(_procesar_wa), name="wa_listener")
        logger.info("      WhatsApp listener activo.")
    except Exception as e:
        logger.warning(f"      WhatsApp no disponible: {e}")

    # RECORDATORIO DIARIO DE PUBLICACION — que AURORA AVISE, no que espere ─────
    async def _recordatorio_post():
        import os, datetime as _dt
        from pathlib import Path as _P
        marca = _P(__file__).resolve().parent / "MEMORIA" / ".ultimo_recordatorio_post"
        HORA = int(os.getenv("HORA_RECORDATORIO_POST", "9"))
        # Encontrado en vivo 2026-07-27: el default viejo (5213326148674) es el MISMO
        # número del negocio (la instancia de Green API), no el personal de Anuar --
        # WA_RECORDATORIO no está definido en .env, así que el aviso se lo mandaba el
        # negocio a sí mismo y nunca le llegaba a Anuar. Sin default: si no está
        # configurado, se salta honesto (con aviso una sola vez) en vez de adivinar mal.
        MI_WA = os.getenv("WA_RECORDATORIO", "")
        _avisado_falta_config = False
        while True:
            try:
                hoy = _dt.date.today().isoformat()
                if not MI_WA and not _avisado_falta_config:
                    logger.warning("      [Recordatorio] WA_RECORDATORIO no está configurado en "
                                    ".env (número personal de Anuar) — el recordatorio diario no se manda.")
                    _avisado_falta_config = True
                ya = marca.read_text(encoding="utf-8").strip() if marca.exists() else ""
                if _dt.datetime.now().hour >= HORA and ya != hoy and MI_WA:
                    from INTEGRACIONES.whatsapp_integration import whatsapp as _wa
                    from MARKETING import plan_monetizacion as _pm
                    posts = (_pm.post_de_hoy() or {}).get("posts", [])
                    if posts:
                        lineas = "\n".join(
                            f"- {p['plataforma']} ({p.get('hora','')}): {os.path.basename(p['video'])}"
                            for p in posts)
                        msg = (f"AURORA - Tu post de HOY ({hoy})\n\n"
                               f"Sube estos videos:\n{lineas}\n\n"
                               f"Abrelo en el panel (Monetizacion) para aprobar el bloque.")
                        await _wa.enviar_mensaje(MI_WA, msg)
                        logger.info("      [Recordatorio] Aviso de post enviado por WhatsApp.")
                    marca.parent.mkdir(parents=True, exist_ok=True)
                    marca.write_text(hoy, encoding="utf-8")
            except Exception as e:
                logger.warning(f"      [Recordatorio] {e}")
            await asyncio.sleep(1800)  # revisa cada 30 min
    try:
        asyncio.create_task(_recordatorio_post(), name="recordatorio_post")
        logger.info("      Recordatorio diario de publicacion activo.")
    except Exception as e:
        logger.warning(f"      Recordatorio no disponible: {e}")

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
