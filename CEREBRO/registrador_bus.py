# -*- coding: utf-8 -*-
"""
AURORA — REGISTRADOR DE BUS NEURONAL v3
Conecta TODOS los motores, integraciones y servicios al bus.
Pub/Sub: cualquier componente puede publicar y suscribirse a cualquier evento.

Componentes registrados (27 total):
  MOTORES/        : analisis, coaching, coaching_real, code_gen, cotizador,
                    imagenes, negocios, reasoning, ventas, marketing
  ORACLE/         : motor_oracle (CRM SQLite), oracle_core (operaciones directas)
  VENDEDOR/       : vendedor_core, verificador_core
  SUBLIMACION/    : sublimacion_core
  TALLER/         : taller_core (DXF laser)
  MEMORIA/        : sistema_memoria, motor_sueno, analitica_marketing
  VOZ/            : voz_google (Google Cast TTS)
  MARKETING/      : asesor_marketing
  PUBLICADOR/     : publicador_core (redes sociales)
  INTEGRACIONES/  : whatsapp, telegram, email
  CEREBRO/        : auto_conocimiento, auto_reparacion
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


def _callback_corel(motor_obj):
    """Callback especial para MotorCorel (metodos multiples)."""
    async def callback(msg: Mensaje) -> Optional[dict]:
        accion = msg.contenido.get("accion", "info")
        try:
            if accion == "exportar_pdf":
                return await motor_obj.exportar_pdf(msg.contenido.get("ruta_salida", ""))
            elif accion == "escalar_pagina":
                return await motor_obj.escalar_pagina(
                    msg.contenido.get("ancho_cm", 0),
                    msg.contenido.get("alto_cm", 0),
                    msg.contenido.get("en_documento_nuevo", False),
                )
            else:
                return await motor_obj.info_documento()
        except Exception as e:
            logger.error(f"Error callback corel: {e}")
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
    Carga y registra todos los motores en el bus neuronal en PARALELO.
    Configura suscripciones cruzadas para interconexion real.
    Retorna dict con resultado de cada motor.
    """
    resultado = {}

    # ── Motores LLM (MOTORES/) — carga en paralelo ─────────────────
    motores_llm = {
        "motor_analisis":      "analizar",
        "motor_coaching":      "coach",
        "motor_coaching_real": "sesion_coaching",
        "motor_code_gen":      "generar",
        "motor_cotizador":     "cotizar",
        "motor_imagenes":      "analizar",
        "motor_negocios":      "consultar",
        "motor_reasoning":     "razonar",
        "motor_ventas":        "procesar",
    }

    # Consola de Motores: respeta lo que Anuar apagó (seguro; los núcleo nunca se apagan).
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("consola_motores", ROOT / "CORE" / "consola_motores.py")
        _cm = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_cm)
        _off = _cm.motores_desactivados_bus()
        if _off:
            motores_llm = {k: v for k, v in motores_llm.items() if k not in _off}
            logger.info(f"[BUS] Consola de Motores: apagados por Anuar -> {sorted(_off)}")
    except Exception as _e:
        logger.warning(f"[BUS] No se pudo leer la consola de motores (sigo con todos): {_e}")

    def _registrar_uno(motor_id: str, metodo: str) -> str:
        motor_obj = _cargar_motor(motor_id)
        if motor_obj:
            cb = _callback_para(motor_obj, metodo)
            bus.registrar(motor_id, cb)
            logger.info(f"[BUS] Registrado: {motor_id}")
            return "registrado"
        logger.warning(f"[BUS] No se pudo cargar: {motor_id}")
        return "no_cargado"

    # Ejecutar en thread pool para no bloquear el loop con las importaciones
    import concurrent.futures
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        tareas = {
            motor_id: loop.run_in_executor(pool, _registrar_uno, motor_id, metodo)
            for motor_id, metodo in motores_llm.items()
        }
        resultados_raw = await asyncio.gather(*tareas.values(), return_exceptions=True)
    for motor_id, res in zip(tareas.keys(), resultados_raw):
        resultado[motor_id] = str(res) if isinstance(res, Exception) else res

    # ── motor_marketing (callback especial) ────────────────────────
    m_marketing = _cargar_motor("motor_marketing")
    if m_marketing:
        bus.registrar("motor_marketing", _callback_marketing(m_marketing))
        resultado["motor_marketing"] = "registrado"
        logger.info("[BUS] Registrado: motor_marketing")

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

    # ── MotorCorel (desde adaptadores) — control real de CorelDRAW ─
    try:
        sys.path.insert(0, str(ROOT / "MOTORES"))
        import adaptadores as _adap
        corel_obj = _adap.MotorCorel()
        bus.registrar("motor_corel", _callback_corel(corel_obj))
        resultado["motor_corel"] = "registrado"
        logger.info("[BUS] Registrado: motor_corel (CorelDRAW COM)")
    except Exception as e:
        resultado["motor_corel"] = f"error: {e}"
        logger.warning(f"[BUS] motor_corel: {e}")

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

    # ── VENDEDOR — ficha técnica y técnicas de venta ───────────────
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("vendedor_core", ROOT / "VENDEDOR" / "vendedor_core.py")
        mod_vend = _ilu.module_from_spec(spec); spec.loader.exec_module(mod_vend)

        async def _cb_vendedor(msg: Mensaje) -> Optional[dict]:
            accion = msg.contenido.get("accion", "ficha")
            try:
                loop = asyncio.get_event_loop()
                if accion == "listar":
                    return await loop.run_in_executor(None, mod_vend.listar_fichas)
                elif accion == "tecnicas":
                    return await loop.run_in_executor(None, mod_vend.tecnicas,
                                                      msg.contenido.get("nombre"))
                elif accion == "brief":
                    return {"brief": await loop.run_in_executor(
                        None, mod_vend.construir_brief,
                        msg.contenido.get("modo", "cliente"),
                        msg.contenido.get("producto", ""),
                        msg.contenido.get("objetivo", ""),
                        msg.contenido.get("negocio", "atf"),
                    )}
                else:
                    return await loop.run_in_executor(None, mod_vend.ficha,
                                                      msg.contenido.get("producto", ""))
            except Exception as e:
                logger.error(f"vendedor_core: {e}")
            return None

        bus.registrar("vendedor_core", _cb_vendedor)
        resultado["vendedor_core"] = "registrado"
        logger.info("[BUS] Registrado: vendedor_core")
    except Exception as e:
        resultado["vendedor_core"] = f"error: {e}"
        logger.warning(f"[BUS] vendedor_core: {e}")

    # ── VERIFICADOR — calidad anti-inventar ────────────────────────
    try:
        spec = importlib.util.spec_from_file_location("verificador_core", ROOT / "VENDEDOR" / "verificador_core.py")
        mod_ver = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_ver)

        async def _cb_verificador(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                if msg.contenido.get("ficha"):
                    return {"issues": await loop.run_in_executor(
                        None, mod_ver.verificar_ficha, msg.contenido["ficha"])}
                else:
                    return await loop.run_in_executor(
                        None, mod_ver.verificar_todas,
                        msg.contenido.get("degradar", True))
            except Exception as e:
                logger.error(f"verificador_core: {e}")
            return None

        bus.registrar("verificador_core", _cb_verificador)
        resultado["verificador_core"] = "registrado"
        logger.info("[BUS] Registrado: verificador_core")
    except Exception as e:
        resultado["verificador_core"] = f"error: {e}"
        logger.warning(f"[BUS] verificador_core: {e}")

    # ── TALLER — conversión DXF para láser (Inkscape) ─────────────
    try:
        spec = importlib.util.spec_from_file_location("taller_core", ROOT / "TALLER" / "taller_core.py")
        mod_taller = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_taller)

        async def _cb_taller(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "convertir")
                if accion == "catalogo":
                    return await loop.run_in_executor(None, mod_taller.catalogo)
                elif accion == "disponible":
                    return {"disponible": await loop.run_in_executor(None, mod_taller.disponible)}
                else:
                    return await loop.run_in_executor(
                        None, mod_taller.convertir_a_dxf,
                        msg.contenido.get("ruta", ""))
            except Exception as e:
                logger.error(f"taller_core: {e}")
            return None

        bus.registrar("taller_core", _cb_taller)
        resultado["taller_core"] = "registrado"
        logger.info("[BUS] Registrado: taller_core")
    except Exception as e:
        resultado["taller_core"] = f"error: {e}"
        logger.warning(f"[BUS] taller_core: {e}")

    # ── SUBLIMACION — procesamiento de video/imagen para sublimación
    try:
        spec = importlib.util.spec_from_file_location("sublimacion_core", ROOT / "SUBLIMACION" / "sublimacion_core.py")
        mod_sub = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_sub)

        async def _cb_sublimacion(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "video")
                if accion == "lienzo":
                    return await loop.run_in_executor(
                        None, mod_sub.crear_lienzo,
                        msg.contenido.get("imagen", ""),
                        msg.contenido.get("producto", "taza_11oz"),
                        msg.contenido.get("dpi", 300),
                    )
                else:
                    return await loop.run_in_executor(
                        None, mod_sub.de_video,
                        msg.contenido.get("origen", ""),
                        msg.contenido.get("fps", 1),
                    )
            except Exception as e:
                logger.error(f"sublimacion_core: {e}")
            return None

        bus.registrar("sublimacion_core", _cb_sublimacion)
        resultado["sublimacion_core"] = "registrado"
        logger.info("[BUS] Registrado: sublimacion_core")
    except Exception as e:
        resultado["sublimacion_core"] = f"error: {e}"
        logger.warning(f"[BUS] sublimacion_core: {e}")

    # ── SISTEMA DE MEMORIA — episódica + semántica SQLite ──────────
    try:
        sys.path.insert(0, str(ROOT / "MEMORIA"))
        from MEMORIA.sistema_memoria import memoria as _memoria

        async def _cb_memoria(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "buscar")
                if accion == "guardar_episodio":
                    await _memoria.guardar_episodio(
                        motor_origen=msg.contenido.get("motor_origen", "sistema"),
                        tipo_evento=msg.contenido.get("tipo_evento", "interaccion"),
                        contenido=msg.contenido.get("contenido", {}),
                        importancia=msg.contenido.get("importancia", 0.5),
                    )
                    return {"status": "guardado"}
                elif accion == "buscar_semantico":
                    return {"resultados": await _memoria.buscar_semantico(
                        msg.contenido.get("tema", ""),
                        msg.contenido.get("limite", 10),
                    )}
                elif accion == "estadisticas":
                    return await _memoria.estadisticas()
                else:
                    return {"resultados": await _memoria.obtener_episodios_recientes(
                        msg.contenido.get("limite", 20)
                    )}
            except Exception as e:
                logger.error(f"sistema_memoria: {e}")
            return None

        bus.registrar("sistema_memoria", _cb_memoria)
        resultado["sistema_memoria"] = "registrado"
        logger.info("[BUS] Registrado: sistema_memoria")
    except Exception as e:
        resultado["sistema_memoria"] = f"error: {e}"
        logger.warning(f"[BUS] sistema_memoria: {e}")

    # ── MOTOR SUEÑO — consolidación episódica nocturna ─────────────
    try:
        from MEMORIA.motor_sueno import motor_sueno as _motor_sueno

        async def _cb_sueno(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "estado")
                if accion == "iniciar":
                    await _motor_sueno.iniciar()
                    return {"status": "iniciado"}
                elif accion == "detener":
                    await _motor_sueno.detener()
                    return {"status": "detenido"}
                elif accion == "actividad":
                    _motor_sueno.registrar_actividad()
                    return {"status": "actividad_registrada"}
                else:
                    return {
                        "ciclos_completados": _motor_sueno._ciclos_completados,
                        "total_conocimientos": _motor_sueno._total_conocimientos,
                        "en_sueno": _motor_sueno._en_sueno,
                    }
            except Exception as e:
                logger.error(f"motor_sueno: {e}")
            return None

        bus.registrar("motor_sueno", _cb_sueno)
        resultado["motor_sueno"] = "registrado"
        logger.info("[BUS] Registrado: motor_sueno")
    except Exception as e:
        resultado["motor_sueno"] = f"error: {e}"
        logger.warning(f"[BUS] motor_sueno: {e}")

    # ── ANALÍTICA DE MARKETING — rendimiento de publicaciones ──────
    try:
        spec = importlib.util.spec_from_file_location("analitica_marketing", ROOT / "MEMORIA" / "analitica_marketing.py")
        mod_anal = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_anal)

        async def _cb_analitica(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "resumen")
                if accion == "registrar":
                    return await loop.run_in_executor(
                        None, mod_anal.registrar_publicacion,
                        msg.contenido.get("datos", {}))
                elif accion == "actualizar_metricas":
                    return await loop.run_in_executor(
                        None, mod_anal.actualizar_metricas,
                        msg.contenido.get("pub_id"),
                        msg.contenido.get("metricas", {}))
                else:
                    return await loop.run_in_executor(
                        None, mod_anal.resumen_rendimiento,
                        msg.contenido.get("dias", 7),
                        msg.contenido.get("plataforma"))
            except Exception as e:
                logger.error(f"analitica_marketing: {e}")
            return None

        bus.registrar("analitica_marketing", _cb_analitica)
        resultado["analitica_marketing"] = "registrado"
        logger.info("[BUS] Registrado: analitica_marketing")
    except Exception as e:
        resultado["analitica_marketing"] = f"error: {e}"
        logger.warning(f"[BUS] analitica_marketing: {e}")

    # ── VOZ GOOGLE — TTS via Google Home / Chromecast ──────────────
    try:
        spec = importlib.util.spec_from_file_location("voz_google", ROOT / "VOZ" / "voz_google.py")
        mod_voz = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_voz)

        async def _cb_voz(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "hablar")
                if accion == "dispositivos":
                    return {"dispositivos": await loop.run_in_executor(None, mod_voz.dispositivos)}
                else:
                    return await loop.run_in_executor(
                        None, mod_voz.hablar_google,
                        msg.contenido.get("texto", ""),
                        msg.contenido.get("device", "oficina"),
                        msg.contenido.get("lang", "es"),
                    )
            except Exception as e:
                logger.error(f"voz_google: {e}")
            return None

        bus.registrar("voz_google", _cb_voz)
        resultado["voz_google"] = "registrado"
        logger.info("[BUS] Registrado: voz_google")
    except Exception as e:
        resultado["voz_google"] = f"error: {e}"
        logger.warning(f"[BUS] voz_google: {e}")

    # ── ASESOR MARKETING — algoritmos y playbooks de redes ─────────
    try:
        spec = importlib.util.spec_from_file_location("asesor_marketing", ROOT / "MARKETING" / "asesor_core.py")
        mod_asesor = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_asesor)

        async def _cb_asesor_mkt(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "conocimiento")
                if accion == "playbook":
                    return await loop.run_in_executor(
                        None, mod_asesor.playbook, msg.contenido.get("flanco"))
                elif accion == "horarios":
                    return await loop.run_in_executor(
                        None, mod_asesor.mejores_horarios,
                        msg.contenido.get("actividad_por_hora"))
                elif accion == "diagnostico":
                    return await loop.run_in_executor(
                        None, mod_asesor.diagnostico,
                        msg.contenido.get("metricas"))
                elif accion == "brief":
                    return {"brief": await loop.run_in_executor(
                        None, mod_asesor.construir_brief_para_cerebro,
                        msg.contenido.get("negocio", "atf"),
                        msg.contenido.get("metricas"),
                        msg.contenido.get("objetivo", "leads"),
                    )}
                else:
                    return await loop.run_in_executor(
                        None, mod_asesor.conocimiento,
                        msg.contenido.get("red"))
            except Exception as e:
                logger.error(f"asesor_marketing: {e}")
            return None

        bus.registrar("asesor_marketing", _cb_asesor_mkt)
        resultado["asesor_marketing"] = "registrado"
        logger.info("[BUS] Registrado: asesor_marketing")
    except Exception as e:
        resultado["asesor_marketing"] = f"error: {e}"
        logger.warning(f"[BUS] asesor_marketing: {e}")

    # ── PUBLICADOR — estado redes sociales ─────────────────────────
    try:
        spec = importlib.util.spec_from_file_location("publicador_core", ROOT / "PUBLICADOR" / "publicador_core.py")
        mod_pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_pub)

        async def _cb_publicador(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "estado")
                if accion == "publicar" and hasattr(mod_pub, "publicar"):
                    return await loop.run_in_executor(
                        None, mod_pub.publicar,
                        msg.contenido.get("plataforma", "instagram"),
                        msg.contenido.get("contenido", {}),
                    )
                else:
                    return await loop.run_in_executor(None, mod_pub.estado_redes)
            except Exception as e:
                logger.error(f"publicador_core: {e}")
            return None

        bus.registrar("publicador_core", _cb_publicador)
        resultado["publicador_core"] = "registrado"
        logger.info("[BUS] Registrado: publicador_core")
    except Exception as e:
        resultado["publicador_core"] = f"error: {e}"
        logger.warning(f"[BUS] publicador_core: {e}")

    # ── ORACLE CORE — operaciones CRM SQLite directas ──────────────
    try:
        spec = importlib.util.spec_from_file_location("oracle_core", ROOT / "ORACLE" / "oracle_core.py")
        mod_oc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod_oc)
        mod_oc.init_db()  # asegurar tablas

        async def _cb_oracle_core(msg: Mensaje) -> Optional[dict]:
            try:
                loop = asyncio.get_event_loop()
                accion = msg.contenido.get("accion", "listar_leads")
                if accion == "crear_lead":
                    return await loop.run_in_executor(
                        None, mod_oc.crear_lead,
                        msg.contenido.get("nombre", ""),
                        msg.contenido.get("telefono", ""),
                        msg.contenido.get("negocio", "atf"),
                        msg.contenido.get("vehiculo"),
                        msg.contenido.get("interes"),
                    )
                elif accion == "actualizar_lead":
                    return await loop.run_in_executor(
                        None, mod_oc.actualizar_lead,
                        msg.contenido.get("lead_id"),
                        msg.contenido.get("estado", "contactado"),
                        msg.contenido.get("notas", ""),
                    )
                elif accion == "crear_orden":
                    return await loop.run_in_executor(
                        None, mod_oc.crear_orden,
                        msg.contenido.get("lead_id"),
                        msg.contenido.get("descripcion", ""),
                        msg.contenido.get("monto", 0),
                    )
                else:
                    return await loop.run_in_executor(
                        None, mod_oc.listar_leads,
                        msg.contenido.get("estado"),
                        msg.contenido.get("negocio"),
                        msg.contenido.get("limite", 50),
                    )
            except Exception as e:
                logger.error(f"oracle_core: {e}")
            return None

        bus.registrar("oracle_core", _cb_oracle_core)
        resultado["oracle_core"] = "registrado"
        logger.info("[BUS] Registrado: oracle_core")
    except Exception as e:
        resultado["oracle_core"] = f"error: {e}"
        logger.warning(f"[BUS] oracle_core: {e}")

    # ── WHATSAPP — mensajería Green API ────────────────────────────
    try:
        from INTEGRACIONES.whatsapp_integration import WhatsAppIntegration
        _wa = WhatsAppIntegration()

        async def _cb_whatsapp(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "enviar")
                if accion == "cotizacion":
                    return await _wa.enviar_cotizacion(
                        msg.contenido.get("telefono", ""),
                        msg.contenido.get("cotizacion", {}),
                    )
                else:
                    return await _wa.enviar_mensaje(
                        msg.contenido.get("telefono", ""),
                        msg.contenido.get("mensaje", ""),
                    )
            except Exception as e:
                logger.error(f"whatsapp: {e}")
            return None

        bus.registrar("whatsapp", _cb_whatsapp)
        resultado["whatsapp"] = "registrado"
        logger.info("[BUS] Registrado: whatsapp")
    except Exception as e:
        resultado["whatsapp"] = f"error: {e}"
        logger.warning(f"[BUS] whatsapp: {e}")

    # ── TELEGRAM ───────────────────────────────────────────────────
    try:
        from INTEGRACIONES.telegram_integration import TelegramIntegration
        _tg = TelegramIntegration()

        async def _cb_telegram(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "enviar")
                chat_id = msg.contenido.get("chat_id", _tg.chat_id)
                if accion == "dashboard":
                    return await _tg.enviar_dashboard(chat_id, msg.contenido.get("datos", {}))
                elif accion == "alerta":
                    return await _tg.enviar_alerta(
                        msg.contenido.get("tipo", "info"),
                        msg.contenido.get("contenido", ""),
                    )
                else:
                    return await _tg.enviar_mensaje(chat_id, msg.contenido.get("mensaje", ""))
            except Exception as e:
                logger.error(f"telegram: {e}")
            return None

        bus.registrar("telegram", _cb_telegram)
        resultado["telegram"] = "registrado"
        logger.info("[BUS] Registrado: telegram")
    except Exception as e:
        resultado["telegram"] = f"error: {e}"
        logger.warning(f"[BUS] telegram: {e}")

    # ── EMAIL ──────────────────────────────────────────────────────
    try:
        from INTEGRACIONES.email_integration import EmailIntegration
        _em = EmailIntegration()

        async def _cb_email(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "cotizacion")
                if accion == "confirmacion":
                    return await _em.enviar_confirmacion_pedido(
                        msg.contenido.get("email_to", ""),
                        msg.contenido.get("pedido", {}),
                    )
                elif accion == "reporte" and hasattr(_em, "enviar_reporte"):
                    return await _em.enviar_reporte(
                        msg.contenido.get("email_to", ""),
                        msg.contenido.get("reporte", {}),
                    )
                else:
                    return await _em.enviar_cotizacion(
                        msg.contenido.get("email_to", ""),
                        msg.contenido.get("cotizacion", {}),
                    )
            except Exception as e:
                logger.error(f"email: {e}")
            return None

        bus.registrar("email", _cb_email)
        resultado["email"] = "registrado"
        logger.info("[BUS] Registrado: email")
    except Exception as e:
        resultado["email"] = f"error: {e}"
        logger.warning(f"[BUS] email: {e}")

    # ── AUTO-CONOCIMIENTO — introspección del sistema ──────────────
    try:
        from CEREBRO.auto_conocimiento import auto_conocimiento as _ac

        async def _cb_auto_conocimiento(msg: Mensaje) -> Optional[dict]:
            try:
                accion = msg.contenido.get("accion", "mapa")
                if accion == "capacidades":
                    return await _ac.capacidades()
                elif accion == "estado_integraciones":
                    return await _ac.estado_integraciones()
                elif accion == "leer_archivo":
                    return await _ac.leer_archivo(msg.contenido.get("ruta_relativa", ""))
                else:
                    return await _ac.mapa_sistema()
            except Exception as e:
                logger.error(f"auto_conocimiento: {e}")
            return None

        bus.registrar("auto_conocimiento", _cb_auto_conocimiento)
        resultado["auto_conocimiento"] = "registrado"
        logger.info("[BUS] Registrado: auto_conocimiento")
    except Exception as e:
        resultado["auto_conocimiento"] = f"error: {e}"
        logger.warning(f"[BUS] auto_conocimiento: {e}")

    # ── AUTO-REPARACIÓN — fix de código via LLM ────────────────────
    try:
        from CEREBRO.auto_reparacion import auto_reparacion as _ar

        async def _cb_auto_reparacion(msg: Mensaje) -> Optional[dict]:
            try:
                return await _ar.reparar(
                    msg.contenido.get("descripcion_error", ""),
                    msg.contenido.get("archivo_relativo", ""),
                )
            except Exception as e:
                logger.error(f"auto_reparacion: {e}")
            return None

        bus.registrar("auto_reparacion", _cb_auto_reparacion)
        resultado["auto_reparacion"] = "registrado"
        logger.info("[BUS] Registrado: auto_reparacion")
    except Exception as e:
        resultado["auto_reparacion"] = f"error: {e}"
        logger.warning(f"[BUS] auto_reparacion: {e}")

    # (Las suscripciones cruzadas de ventas/marketing/reasoning YA se hicieron arriba.
    #  Aquí estaba un bloque DUPLICADO que las registraba 2 veces y re-importaba los
    #  motores de más — eliminado para quitar suscripciones dobles y acelerar el boot.)

    # motor_sueno registra actividad en cada evento del bus
    try:
        from MEMORIA.motor_sueno import motor_sueno as _ms_sub

        async def _registrar_actividad_sueno(msg: Mensaje) -> None:
            _ms_sub.registrar_actividad()

        bus.suscribir("motor_sueno_actividad", TipoMensaje.EVENTO,
                      _registrar_actividad_sueno)
        logger.info("[BUS] Suscripcion: motor_sueno <- EVENTO (actividad)")
    except Exception:
        pass

    registrados = sum(1 for v in resultado.values() if v == "registrado")
    total = len(resultado)
    logger.info(f"[BUS] ✅ Total registrados: {registrados}/{total}")
    return resultado
