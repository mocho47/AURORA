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

                    # ── QUIEN ESCRIBE (agregado 2026-07-29) ───────────────────
                    # Riesgo real que señalo Anuar: WhatsApp es el 90% de su
                    # dialogo con TODOS. Antes, su hija escribiendo "papa ya
                    # sali" quedaba registrada como LEAD (con eso como "interes")
                    # y recibia respuesta de ventas. AURORA nunca debe hacerse
                    # pasar por Anuar con su familia: avisa y da un trato digno.
                    try:
                        from CONFIG import contactos as _cont
                        quien = _cont.clasificar(telefono, texto)
                    except Exception as e:
                        logger.warning(f"      [WA] No pude clasificar el contacto, trato como cliente: {e}")
                        quien = {"relacion": "desconocido", "vender": True, "responder": True,
                                 "avisar_a_anuar": False, "registrar_lead": True}

                    # Aprende que este numero ya hablo con Anuar (pedido suyo:
                    # "que aprenda que numeros ya han tenido interaccion conmigo").
                    try:
                        _cont.recordar_interaccion(telefono)
                    except Exception:
                        pass

                    if not quien.get("registrar_lead", True) or not quien.get("vender", True):
                        etiqueta = quien.get("titulo") or quien.get("nombre") or quien.get("relacion")
                        logger.info(f"      [WA] {telefono} = {etiqueta} ({quien['relacion']}) "
                                    f"-> no se vende ni se registra como lead.")
                        # Trato configurable (CONFIG/contactos.json), con su NOMBRE
                        # si se conoce ("Hola Luis! En un momento te responde Anuar").
                        _resp_personal = (quien.get("respuesta") or "").strip()
                        if _resp_personal:
                            _resp_personal = _cont.saludo_personal(telefono, _resp_personal)
                        if quien.get("responder") and _resp_personal:
                            r_p = await whatsapp.enviar_mensaje(telefono, _resp_personal)
                            if r_p.get("status") != "ENVIADO":
                                logger.error(f"      [WA] FALLO envío a {etiqueta} ({telefono}): {r_p}")
                        # AVISAR A ANUAR POR TODOS LOS MEDIOS REALES DISPONIBLES
                        # (pedido suyo). Se deja constancia en disco SIEMPRE — asi
                        # el aviso no depende de que WhatsApp funcione, y el panel
                        # lo muestra como alerta pendiente hasta que el lo vea.
                        if quien.get("avisar_a_anuar"):
                            import os as _os, json as _js, datetime as _d
                            from pathlib import Path as _Pt
                            _nom = ""
                            try:
                                _nom = _cont.nombre_conocido(telefono)
                            except Exception:
                                pass
                            _quien_txt = _nom or etiqueta
                            # 1) Constancia en disco (el medio que nunca falla).
                            try:
                                _bandeja = _Pt(__file__).resolve().parent / "MEMORIA" / "mensajes_personales.json"
                                _prev = []
                                if _bandeja.exists():
                                    try:
                                        _prev = _js.loads(_bandeja.read_text(encoding="utf-8"))
                                        if not isinstance(_prev, list):
                                            _prev = []
                                    except Exception:
                                        _prev = []
                                _prev.append({"cuando": _d.datetime.now().isoformat(timespec="seconds"),
                                              "telefono": telefono, "quien": _quien_txt,
                                              "relacion": quien.get("relacion", ""),
                                              "mensaje": texto[:500], "visto": False})
                                _bandeja.parent.mkdir(parents=True, exist_ok=True)
                                _bandeja.write_text(_js.dumps(_prev[-200:], ensure_ascii=False, indent=2),
                                                    encoding="utf-8")
                            except Exception as e:
                                logger.warning(f"      [WA] No pude guardar el aviso personal: {e}")
                            # 2) WhatsApp a su numero personal real, si esta configurado.
                            _mi_wa = _os.getenv("WA_RECORDATORIO", "")
                            if _mi_wa:
                                r_av = await whatsapp.enviar_mensaje(
                                    _mi_wa,
                                    f"📩 Te escribió {_quien_txt} ({telefono}):\n\n\"{texto[:300]}\"\n\n"
                                    f"No le contesté por ti — solo le dije que le avisaba.")
                                if r_av.get("status") != "ENVIADO":
                                    logger.error(f"      [WA] FALLO el aviso a Anuar: {r_av} "
                                                 f"(pero quedó guardado en MEMORIA/mensajes_personales.json)")
                            else:
                                logger.warning("      [WA] WA_RECORDATORIO no configurado: el aviso "
                                               "quedó guardado en MEMORIA/mensajes_personales.json y "
                                               "aparecerá en el panel.")
                        return

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

    # REPORTE MENSUAL DE CONTABILIDAD — real, con datos reales del taller ──────
    # Pedido de Anuar 2026-07-27: reusa contabilidad_mensual() (ya corregida esta
    # noche: no cuenta canceladas, no falsea cobros) + el envio real de WhatsApp
    # ya probado. El dia 1 de cada mes manda por WhatsApp el resumen real del mes
    # que acaba de cerrar. Usa el mismo WA_RECORDATORIO (numero personal real de
    # Anuar en .env) que ya usa el recordatorio de publicaciones -- mismo candado
    # de "sin numero configurado no se manda, nunca se adivina".
    async def _reporte_mensual_contabilidad():
        import os, datetime as _dt
        from pathlib import Path as _P
        marca = _P(__file__).resolve().parent / "MEMORIA" / ".ultimo_reporte_mensual"
        MI_WA = os.getenv("WA_RECORDATORIO", "")
        while True:
            try:
                hoy = _dt.date.today()
                mes_actual = hoy.isoformat()[:7]
                ya = marca.read_text(encoding="utf-8").strip() if marca.exists() else ""
                if hoy.day == 1 and ya != mes_actual and MI_WA:
                    mes_anterior = (hoy.replace(day=1) - _dt.timedelta(days=1)).isoformat()[:7]
                    from TALLER import ordenes_taller as _ot
                    cont = await asyncio.to_thread(_ot.contabilidad_mensual, mes_anterior)
                    datos = next((x for x in cont.get("meses", []) if x["mes"] == mes_anterior), None)
                    if datos:
                        msg = (f"📊 AURORA - Reporte de Contabilidad ({mes_anterior})\n\n"
                               f"💰 Ingresos: ${datos['ingresos']:,.2f}\n"
                               f"💸 Costos: ${datos['costos']:,.2f}\n"
                               f"✅ Utilidad: ${datos['utilidad']:,.2f} ({datos['margen_pct']}%)\n"
                               f"💵 Cobrado: ${datos['cobrado']:,.2f}\n"
                               f"⏳ Por cobrar: ${datos['por_cobrar']:,.2f}\n"
                               f"📦 Órdenes del mes: {datos['ordenes']}\n\n"
                               f"Generado automático con datos reales del taller.")
                    else:
                        msg = (f"📊 AURORA - Reporte de Contabilidad ({mes_anterior})\n\n"
                               f"No hubo movimientos registrados ese mes (dato real, no error).")
                    from INTEGRACIONES.whatsapp_integration import whatsapp as _wa
                    r = await _wa.enviar_mensaje(MI_WA, msg)
                    if r.get("status") == "ENVIADO":
                        logger.info("      [Reporte mensual] Contabilidad real enviada por WhatsApp.")
                        marca.parent.mkdir(parents=True, exist_ok=True)
                        marca.write_text(mes_actual, encoding="utf-8")
                    else:
                        logger.error(f"      [Reporte mensual] FALLO envío, no se marca enviado (reintentará): {r}")
            except Exception as e:
                logger.warning(f"      [Reporte mensual] {e}")
            await asyncio.sleep(3600)  # revisa cada hora (solo actua el dia 1)
    try:
        asyncio.create_task(_reporte_mensual_contabilidad(), name="reporte_mensual")
        logger.info("      Reporte mensual de contabilidad activo.")
    except Exception as e:
        logger.warning(f"      Reporte mensual no disponible: {e}")

    # Pedido de Anuar 2026-07-29: Equipo de Ventas "corriendo solo".
    # INTENTO REAL de tarea de fondo periodica (cada 4h) — encontrado en vivo:
    # se cuelga sin excepcion ni timeout dentro de asyncio.to_thread() cuando se
    # llama desde una tarea creada en el arranque (aunque el MISMO codigo
    # (oracle_core.pronostico_embudo via to_thread) responde instantaneo desde
    # un endpoint HTTP normal, GET /oracle/pronostico). No se encontro la causa
    # raiz exacta a tiempo esta noche — probablemente relacionado a como esta
    # tarea especifica interactua con el loop/executor al crearse en el arranque,
    # a diferencia de reporte_mensual/motor_sueno que si funcionan. Documentado
    # honesto, no se deja una tarea colgada corriendo para siempre: se retira el
    # bucle automatico y se deja SOLO el endpoint bajo demanda (GET
    # /equipos/ventas/ultimo), que usa el mismo patron ya probado del endpoint
    # /oracle/pronostico que si funciona 100%. Pendiente real: encontrar la
    # causa raiz del cuelgue en tareas de fondo nuevas creadas en el arranque.

    logger.info("")
    logger.info("=" * 60)
    logger.info("  AURORA completamente inicializada")
    logger.info("  Motor LLM : openai/gpt-oss-20b (Groq)")
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
