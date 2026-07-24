# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║          🔀 AURORA — BUS NEURONAL MULTIDIRECCIONAL                   ║
║       Interconexión cruzada real entre todos los motores             ║
║   Publish/Subscribe + Request/Response + Broadcast asíncrono         ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/CEREBRO/bus_neuronal.py
"""
import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

# Permite importar desde cualquier ubicación dentro del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))
from MEMORIA.sistema_memoria import memoria

logger = logging.getLogger("aurora.bus_neuronal")


# ─────────────────────────────────────────────────────────────────────
# TIPOS DE MENSAJE
# ─────────────────────────────────────────────────────────────────────

class TipoMensaje(str, Enum):
    EVENTO        = "evento"         # fire-and-forget a suscriptores
    PETICION      = "peticion"       # request-response entre motores
    RESPUESTA     = "respuesta"      # respuesta a una peticion
    BROADCAST     = "broadcast"      # a TODOS los motores registrados
    ALERTA        = "alerta"         # urgente, máxima prioridad
    APRENDIZAJE   = "aprendizaje"    # nuevo conocimiento generado
    DECISION      = "decision"       # motor tomó una decisión
    INTERACCION   = "interaccion"    # mensaje usuario ↔ motor


@dataclass
class Mensaje:
    tipo:          TipoMensaje
    origen:        str
    contenido:     Dict[str, Any]
    destino:       str               = "broadcast"
    id:            str               = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:     str               = field(default_factory=lambda: datetime.utcnow().isoformat())
    respuesta_id:  Optional[str]     = None   # ID del mensaje al que responde
    importancia:   float             = 0.5    # 0.0–1.0


# ─────────────────────────────────────────────────────────────────────
# BUS NEURONAL
# ─────────────────────────────────────────────────────────────────────

Callback = Callable[[Mensaje], Coroutine[Any, Any, Optional[Dict]]]


class BusNeuronal:
    """
    Bus de comunicación multidireccional entre motores de AURORA.

    Funcionalidades reales:
    · publicar()   → fire-and-forget a todos los suscriptores del tipo de evento
    · solicitar()  → request-response con timeout entre dos motores
    · broadcast()  → mensaje a TODOS los motores registrados
    · suscribir()  → un motor declara qué tipos de evento quiere recibir
    · registrar()  → registra un motor en el bus (necesario para broadcast)

    Todos los mensajes se guardan automáticamente en la memoria episódica.
    """

    _instancia: Optional["BusNeuronal"] = None

    def __new__(cls) -> "BusNeuronal":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._listo = False
        return cls._instancia

    def __init__(self) -> None:
        if self._listo:
            return
        # motor_id → lista de (tipo_evento, callback)
        self._suscriptores: Dict[str, List[tuple[TipoMensaje, Callback]]] = {}
        # Motores registrados para broadcast
        self._motores: Dict[str, Callback] = {}
        # Futuras respuestas pendientes: mensaje_id → asyncio.Future
        self._pendientes: Dict[str, asyncio.Future] = {}
        # Cola interna de mensajes (buffer)
        self._cola: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._tarea_despacho: Optional[asyncio.Task] = None
        self._listo = True
        logger.info("🔀 BusNeuronal instanciado.")

    # ── CICLO DE VIDA ─────────────────────────────────────────────

    async def iniciar(self) -> None:
        """Arranca el despachador de mensajes en background."""
        await memoria.inicializar()
        if self._tarea_despacho is None or self._tarea_despacho.done():
            self._tarea_despacho = asyncio.create_task(
                self._despachador(), name="bus_neuronal_despacho"
            )
            logger.info("▶️  Bus Neuronal activo — despachador iniciado.")

    async def detener(self) -> None:
        if self._tarea_despacho and not self._tarea_despacho.done():
            self._tarea_despacho.cancel()
            logger.info("⏹️  Bus Neuronal detenido.")

    # ── REGISTRO DE MOTORES ───────────────────────────────────────

    def registrar(self, motor_id: str, callback_broadcast: Callback) -> None:
        """
        Registra un motor en el bus para que reciba broadcasts.
        callback_broadcast: función async que acepta un Mensaje.
        """
        self._motores[motor_id] = callback_broadcast
        if motor_id not in self._suscriptores:
            self._suscriptores[motor_id] = []
        logger.info(f"✅ Motor registrado en bus: {motor_id}")

    def suscribir(
        self,
        motor_id: str,
        tipo: TipoMensaje,
        callback: Callback,
    ) -> None:
        """
        Suscribe un motor a un tipo de mensaje específico.
        Puede llamarse múltiples veces para suscribirse a varios tipos.
        """
        if motor_id not in self._suscriptores:
            self._suscriptores[motor_id] = []
        self._suscriptores[motor_id].append((tipo, callback))
        logger.debug(f"📡 {motor_id} suscrito a [{tipo.value}]")

    # ── PUBLICACIÓN ───────────────────────────────────────────────

    async def publicar(self, mensaje: Mensaje) -> None:
        """Fire-and-forget. El mensaje se encola y se despacha sin bloquear."""
        await self._cola.put(mensaje)

    async def broadcast(
        self,
        origen: str,
        contenido: Dict[str, Any],
        importancia: float = 0.5,
    ) -> None:
        """Envía un mensaje a TODOS los motores registrados."""
        msg = Mensaje(
            tipo=TipoMensaje.BROADCAST,
            origen=origen,
            destino="todos",
            contenido=contenido,
            importancia=importancia,
        )
        await self.publicar(msg)

    async def solicitar(
        self,
        origen: str,
        destino: str,
        contenido: Dict[str, Any],
        timeout: float = 10.0,
        importancia: float = 0.6,
    ) -> Optional[Dict[str, Any]]:
        """
        Request-response entre dos motores.
        Espera la respuesta hasta `timeout` segundos.
        Retorna el contenido de la respuesta o None si hay timeout.
        """
        msg = Mensaje(
            tipo=TipoMensaje.PETICION,
            origen=origen,
            destino=destino,
            contenido=contenido,
            importancia=importancia,
        )
        loop = asyncio.get_event_loop()
        futuro: asyncio.Future = loop.create_future()
        self._pendientes[msg.id] = futuro

        await self.publicar(msg)

        try:
            respuesta = await asyncio.wait_for(futuro, timeout=timeout)
            return respuesta
        except asyncio.TimeoutError:
            logger.warning(
                f"⏱️  Timeout en solicitud {origen}→{destino} [{msg.id}]"
            )
            return None
        finally:
            self._pendientes.pop(msg.id, None)

    async def responder(
        self,
        peticion: Mensaje,
        contenido: Dict[str, Any],
    ) -> None:
        """Un motor responde a una petición recibida."""
        respuesta = Mensaje(
            tipo=TipoMensaje.RESPUESTA,
            origen=peticion.destino,
            destino=peticion.origen,
            contenido=contenido,
            respuesta_id=peticion.id,
            importancia=peticion.importancia,
        )
        await self.publicar(respuesta)

    # ── DESPACHADOR INTERNO ───────────────────────────────────────

    async def _despachador(self) -> None:
        """Bucle interno que saca mensajes de la cola y los entrega."""
        logger.info("🔄 Despachador iniciado.")
        while True:
            try:
                msg: Mensaje = await self._cola.get()
                asyncio.create_task(self._entregar(msg))
                self._cola.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error en despachador: {exc}", exc_info=True)

    async def _entregar(self, msg: Mensaje) -> None:
        """Entrega un mensaje a sus destinatarios y lo guarda en memoria."""
        try:
            # 1. Guardar en memoria episódica (siempre)
            await memoria.registrar(
                motor_origen=msg.origen,
                tipo_evento=msg.tipo.value,
                contenido=msg.contenido,
                motor_destino=msg.destino,
                importancia=msg.importancia,
            )

            # 2. Si es RESPUESTA → resolver el futuro pendiente
            if msg.tipo == TipoMensaje.RESPUESTA and msg.respuesta_id:
                futuro = self._pendientes.get(msg.respuesta_id)
                if futuro and not futuro.done():
                    futuro.set_result(msg.contenido)
                return

            # 3. BROADCAST → entregar a todos los motores registrados
            if msg.tipo == TipoMensaje.BROADCAST:
                tareas = [
                    asyncio.create_task(cb(msg))
                    for motor_id, cb in self._motores.items()
                    if motor_id != msg.origen
                ]
                if tareas:
                    await asyncio.gather(*tareas, return_exceptions=True)
                return

            # 4. PETICIÓN / EVENTO → entregar al destino y a suscriptores del tipo
            destinatarios = set()

            # Destino directo (para peticiones)
            if msg.destino in self._motores:
                destinatarios.add(msg.destino)

            # Suscriptores del tipo de mensaje
            for motor_id, suscripciones in self._suscriptores.items():
                for tipo_sus, _ in suscripciones:
                    if tipo_sus == msg.tipo and motor_id != msg.origen:
                        destinatarios.add(motor_id)

            for motor_id in destinatarios:
                # Buscar callback específico por tipo
                cb = self._motores.get(motor_id)
                for tipo_sus, cb_sus in self._suscriptores.get(motor_id, []):
                    if tipo_sus == msg.tipo:
                        cb = cb_sus
                        break
                if cb:
                    try:
                        resultado = await cb(msg)
                        # Si el callback devolvió algo y era una petición → responder
                        if resultado and msg.tipo == TipoMensaje.PETICION:
                            await self.responder(msg, resultado)
                    except Exception as exc:
                        logger.error(
                            f"Error en {motor_id} al procesar [{msg.tipo.value}]: {exc}",
                            exc_info=True,
                        )

        except Exception as exc:
            logger.error(f"Error al entregar mensaje: {exc}", exc_info=True)

    # ── DIAGNÓSTICO ───────────────────────────────────────────────

    def estado(self) -> Dict:
        return {
            "sistema": "BusNeuronal",
            "motores_registrados": list(self._motores.keys()),
            "total_suscripciones": sum(
                len(v) for v in self._suscriptores.values()
            ),
            "mensajes_en_cola": self._cola.qsize(),
            "peticiones_pendientes": len(self._pendientes),
            "despachador_activo": (
                self._tarea_despacho is not None
                and not self._tarea_despacho.done()
            ),
        }


# Instancia global (singleton)
bus = BusNeuronal()
