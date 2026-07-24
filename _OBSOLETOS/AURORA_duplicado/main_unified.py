# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║               🚀 AURORA — PUNTO DE ENTRADA UNIFICADO                 ║
║          Interconexión cruzada multidireccional entre motores         ║
║          Memoria cognitiva/generativa + Etapa de sueño real           ║
╚══════════════════════════════════════════════════════════════════════╝
Arranca en orden:
  1. SistemaMemoria (SQLite episódica + semántica)
  2. BusNeuronal (interconexión multidireccional)
  3. Conecta los 10 motores al bus
  4. MotorSueno (consolidación + aprendizaje en background)
  5. FastAPI + uvicorn (API + WhatsApp)
"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# ── Rutas del proyecto ─────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SUPER_MARKETING_SYSTEM"))
sys.path.insert(0, str(ROOT / "CEREBRO"))
sys.path.insert(0, str(ROOT / "MEMORIA"))
sys.path.insert(0, str(ROOT / "MOTORES"))

load_dotenv(ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aurora.main")

# ── Imports del núcleo ─────────────────────────────────────────────
from MEMORIA.sistema_memoria import memoria
from CEREBRO.bus_neuronal import bus, TipoMensaje, Mensaje
from MEMORIA.motor_sueno import motor_sueno
from CEREBRO.consciencia import consciencia
from CEREBRO.auto_conocimiento import auto_conocimiento
from CEREBRO.auto_reparacion import auto_reparacion


# ─────────────────────────────────────────────────────────────────────
# ADAPTADORES DE MOTORES AL BUS
# Cada motor recibe mensajes del bus a través de su callback.
# Los motores también pueden publicar al bus usando la instancia global.
# ─────────────────────────────────────────────────────────────────────

async def _hacer_callback_motor(motor_id: str, nombre_clase: str):
    """
    Carga dinámicamente un motor y retorna su callback para el bus.
    El callback registra actividad en el motor de sueño y delega al motor real.
    """
    try:
        modulo = __import__(f"MOTORES.{motor_id}", fromlist=[nombre_clase])
        clase = getattr(modulo, nombre_clase, None)
        if clase is None:
            return None
        instancia = clase()

        async def callback(msg: Mensaje) -> Dict[str, Any]:
            motor_sueno.registrar_actividad()
            # Todos los motores responden a broadcasts con su estado
            if msg.tipo == TipoMensaje.BROADCAST:
                if hasattr(instancia, "get_status"):
                    return instancia.get_status()
            # Las peticiones directas se enrutan al método apropiado del motor
            if msg.tipo == TipoMensaje.PETICION:
                accion = msg.contenido.get("accion", "")
                datos = msg.contenido.get("datos", {})
                if hasattr(instancia, accion) and callable(getattr(instancia, accion)):
                    metodo = getattr(instancia, accion)
                    if asyncio.iscoroutinefunction(metodo):
                        return await metodo(**datos)
                    return metodo(**datos)
            return None

        return callback

    except Exception as exc:
        logger.warning(f"Motor {motor_id} no cargado: {exc}")
        return None


MOTORES_CATALOGO = {
    "motor_analisis":      "MotorAnalisis",
    "motor_code_gen":      "MotorCodeGen",
    "motor_coaching":      "MotorCoaching",
    "motor_coaching_real": "MotorCoachingReal",
    "motor_cotizador":     "MotorCotizador",
    "motor_imagenes":      "MotorImagenes",
    "motor_negocios":      "MotorNegocios",
    "motor_pedidos":       "MotorPedidos",
    "motor_reasoning":     "MotorReasoning",
    "motor_ventas":        "MotorVentas",
    "motor_marketing":      "MotorMarketing",
}
# Adaptadores de módulos funcionales existentes
async def conectar_adaptadores() -> int:
    from MOTORES.adaptadores import ADAPTADORES_CATALOGO
    conectados = 0
    for motor_id, clase in ADAPTADORES_CATALOGO.items():
        try:
            instancia = clase()
            async def _cb(msg, inst=instancia):
                motor_sueno.registrar_actividad()
                if hasattr(inst, "get_status"):
                    return inst.get_status()
                return None
            bus.registrar(motor_id, _cb)
            bus.suscribir(motor_id, TipoMensaje.BROADCAST, _cb)
            conectados += 1
        except Exception as e:
            logger.warning(f"Adaptador {motor_id}: {e}")
    logger.info(f"🔌 {conectados} adaptadores adicionales conectados.")
    return conectados

async def conectar_motores() -> int:
    """Registra todos los motores en el bus neuronal. Retorna cuántos se conectaron."""
    conectados = 0
    for motor_id, nombre_clase in MOTORES_CATALOGO.items():
        cb = await _hacer_callback_motor(motor_id, nombre_clase)
        if cb:
            bus.registrar(motor_id, cb)
            # Suscribir a eventos relevantes
            bus.suscribir(motor_id, TipoMensaje.BROADCAST, cb)
            bus.suscribir(motor_id, TipoMensaje.ALERTA, cb)
            conectados += 1
    logger.info(f"🔌 {conectados}/{len(MOTORES_CATALOGO)} motores conectados al bus.")
    return conectados


# ─────────────────────────────────────────────────────────────────────
# LIFESPAN — arranque y cierre limpio del sistema
# ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    """Gestiona el ciclo de vida de AURORA al arrancar y apagar FastAPI."""
    logger.info("=" * 60)
    logger.info("🚀 AURORA — Arrancando sistema completo")
    logger.info("=" * 60)

    # 1. Memoria
    await memoria.inicializar()
    stats = await memoria.estadisticas()
    logger.info(f"🧠 Memoria: {stats}")

    # 2. Bus neuronal
    await bus.iniciar()

    # 3. Motores → bus
    await conectar_motores()
    await conectar_adaptadores()

    # 4. Consciencia central
    await consciencia.inicializar()

    # 5. Motor de sueño
    await motor_sueno.iniciar()

    # 6. Anunciar arranque completo en el bus
    await bus.broadcast(
        origen="sistema",
        contenido={
            "evento": "AURORA_ONLINE",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "motores": list(bus.estado()["motores_registrados"]),
        },
        importancia=0.9,
    )

    logger.info("✅ AURORA completamente operativo.")
    logger.info(f"   Bus: {bus.estado()}")
    logger.info(f"   Consciencia: {consciencia.estado()}")
    logger.info(f"   Sueño: {motor_sueno.estado()}")

    yield  # ← aquí corre la API

    # Apagado limpio
    logger.info("🛑 AURORA apagándose...")
    await bus.detener()
    await motor_sueno.detener()
    logger.info("✅ Apagado limpio completado.")


# ─────────────────────────────────────────────────────────────────────
# IMPORTAR app DE FastAPI e inyectar lifespan
# ─────────────────────────────────────────────────────────────────────

try:
    from SUPER_MARKETING_SYSTEM.api_v3 import app as _app_v3, verify_jwt
    _app_v3.router.lifespan_context = lifespan
    app = _app_v3
except Exception as exc:
    logger.warning(f"api_v3 no disponible ({exc}), usando aurora_unified_main")
    try:
        # aurora_unified_main.py tiene 94 endpoints ya construidos — usarlo como base
        sys.path.insert(0, str(ROOT))
        from aurora_unified_main import app as _app_legacy
        _app_legacy.router.lifespan_context = lifespan
        app = _app_legacy
        # stub verify_jwt para endpoints del nucleo
        from fastapi.security import HTTPBearer
        _sec = HTTPBearer(auto_error=False)
        async def verify_jwt(credentials=Depends(_sec)):
            return {"usuario_id": "sistema"}
    except Exception as exc2:
        logger.error(f"No se pudo importar ninguna app: {exc2}")
        from fastapi import FastAPI
        from fastapi.security import HTTPBearer
        app = FastAPI(title="AURORA", lifespan=lifespan)
        _sec = HTTPBearer(auto_error=False)
        async def verify_jwt(credentials=Depends(_sec)):
            return {"usuario_id": "sistema"}

router_nucleo = APIRouter(prefix="/nucleo", tags=["Núcleo AURORA"])


class ChatPayload(BaseModel):
    texto: str
    session_id: Optional[str] = None
    canal: Optional[str] = "api"


@router_nucleo.post("/chat")
async def chat_aurora(payload: ChatPayload, user_info: Dict = Depends(verify_jwt)):
    """Punto de entrada principal — pipeline cognitivo completo de AURORA."""
    return await consciencia.procesar(
        mensaje=payload.texto,
        user_id=user_info["usuario_id"],
        session_id=payload.session_id or user_info["usuario_id"],
        canal=payload.canal or "api",
    )

@router_nucleo.post("/chat/publico")
async def chat_publico(payload: ChatPayload):
    """Chat sin JWT — para WhatsApp y canales externos."""
    return await consciencia.procesar(
        mensaje=payload.texto,
        user_id=payload.session_id or "anonimo",
        session_id=payload.session_id or "anonimo",
        canal=payload.canal or "whatsapp",
    )

@router_nucleo.get("/estado")
async def estado_nucleo():
    return {
        "bus":         bus.estado(),
        "memoria":     await memoria.estado(),
        "consciencia": consciencia.estado(),
        "sueno":       motor_sueno.estado(),
    }

@router_nucleo.get("/memoria/episodica")
async def ver_episodica(limite: int = 20):
    return await memoria.episodios_recientes(limite=limite)

@router_nucleo.get("/memoria/semantica")
async def ver_semantica(tema: str = "", limite: int = 20):
    return await memoria.recordar(tema=tema, limite=limite)

@router_nucleo.post("/bus/broadcast")
async def emitir_broadcast(payload: dict):
    """Emite un broadcast a todos los motores desde la API."""
    await bus.broadcast(
        origen="api",
        contenido=payload,
        importancia=payload.get("importancia", 0.5),
    )
    return {"status": "emitido", "motores": bus.estado()["motores_registrados"]}

@router_nucleo.post("/marketing/contenido")
async def generar_contenido_marketing(payload: dict):
    """Genera hook/caption/estrategia con memoria semántica de campañas previas."""
    from MOTORES.motor_marketing import MotorMarketing
    motor = MotorMarketing()
    return await motor.generar_contenido(
        tipo=payload.get("tipo", "hook"),
        plataforma=payload.get("plataforma", "tiktok"),
        producto=payload.get("producto", "ATF Retrofit LED"),
        contexto_extra=payload.get("contexto", ""),
    )

@router_nucleo.post("/marketing/estrategia")
async def estrategia_semanal_marketing(payload: dict):
    from MOTORES.motor_marketing import MotorMarketing
    motor = MotorMarketing()
    return await motor.estrategia_semanal(objetivo=payload.get("objetivo", "leads ATF"))

@router_nucleo.post("/marketing/publicacion")
async def registrar_publicacion(payload: dict):
    from MEMORIA.analitica_marketing import analitica_marketing
    await analitica_marketing.inicializar()
    pub_id = await analitica_marketing.registrar_publicacion(payload)
    return {"status": "OK", "pub_id": pub_id}

@router_nucleo.put("/marketing/metricas/{pub_id}")
async def actualizar_metricas_publicacion(pub_id: int, payload: dict):
    from MEMORIA.analitica_marketing import analitica_marketing
    await analitica_marketing.inicializar()
    await analitica_marketing.actualizar_metricas(pub_id, payload)
    return {"status": "OK", "pub_id": pub_id}

@router_nucleo.get("/marketing/top")
async def top_publicaciones(dias: int = 30):
    from MEMORIA.analitica_marketing import analitica_marketing
    await analitica_marketing.inicializar()
    return {
        "top_performers":   await analitica_marketing.top_performers(dias),
        "por_plataforma":   await analitica_marketing.resumen_plataformas(dias),
    }

app.include_router(router_nucleo)


# ─────────────────────────────────────────────────────────────────────
# ARRANQUE
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main_unified:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level="info",
    )

