"""
AURORA SERVER - FastAPI Backend
Expone endpoints REST y WebSocket para operaciones
"""

import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Importar componentes AURORA
from aurora_cerebro import cerebro
from aurora_sync import sync

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurora.server")

# Crear aplicación FastAPI
app = FastAPI(
    title="AURORA v2",
    description="Sistema inteligente de operaciones sin censura",
    version="2.0.0"
)

# Modelos Pydantic
class MensajeRequest(BaseModel):
    """Solicitud de razonamiento al cerebro"""
    mensaje: str
    contexto: Optional[Dict[str, Any]] = None
    negocio: Optional[str] = None


class MensajeResponse(BaseModel):
    """Respuesta del cerebro"""
    respuesta: str
    confianza: float
    tipo: str
    timestamp: str


class CotizacionRequest(BaseModel):
    """Solicitud de cotización"""
    negocio: str  # "ATF" o "MILENS"
    producto: str
    cantidad: Optional[int] = 1
    cliente_id: Optional[str] = None


class PedidoRequest(BaseModel):
    """Solicitud de crear pedido"""
    cliente_id: str
    cliente_nombre: str
    producto: str
    cantidad: int
    precio: float
    negocio: str


# ==================== ENDPOINTS DE CEREBRO ====================

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz - redirige a panel"""
    return {
        "sistema": "AURORA v2",
        "status": "operativo",
        "cerebro": "activo",
        "sincronizacion": "conectado" if sync.conectado else "desconectado"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cerebro": "ready",
        "memoria": "loaded",
        "sync": "connected" if sync.conectado else "disconnected"
    }


@app.post("/razonar", response_model=MensajeResponse, tags=["Cerebro"])
async def razonar(request: MensajeRequest):
    """
    Endpoint principal del cerebro AURORA

    Ejecuta razonamiento profundo sin censura
    """
    try:
        logger.info(f"Razonamiento: {request.mensaje[:50]}...")

        # Preparar contexto
        contexto = request.contexto or {}
        contexto["negocio"] = request.negocio or "general"

        # Razonar con cerebro
        resultado = await cerebro.razonar(request.mensaje, contexto)

        logger.info(f"Respuesta generada (confianza: {resultado['confianza']:.2f})")

        return MensajeResponse(
            respuesta=resultado["respuesta"],
            confianza=resultado["confianza"],
            tipo=resultado["tipo"],
            timestamp=resultado["timestamp"]
        )

    except Exception as e:
        logger.error(f"Error en razonamiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/decidir", tags=["Cerebro"])
async def decidir_autonomamente(escenario: str):
    """
    Solicita decisión autónoma del cerebro

    Ejemplos:
    - "Cliente no pagó hace 7 días"
    - "Tengo 5 clientes esperando respuesta"
    """

    try:
        logger.info(f"Decisión autónoma: {escenario[:50]}...")

        resultado = await cerebro.decidir_autonomamente(escenario)

        logger.info(f"Decisión: {resultado['accion']}")

        return resultado

    except Exception as e:
        logger.error(f"Error en decisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE OPERACIONES ====================

@app.post("/cotizar", tags=["Operaciones"])
async def cotizar(request: CotizacionRequest):
    """
    Genera cotización automática

    Negocios soportados: ATF, MILENS
    """

    try:
        logger.info(f"Cotización: {request.negocio} - {request.producto} x {request.cantidad}")

        # Usar cerebro para razonar la cotización
        mensaje = f"""
        Cotiza para el cliente:
        Negocio: {request.negocio}
        Producto: {request.producto}
        Cantidad: {request.cantidad}
        Cliente ID: {request.cliente_id}
        """

        resultado = await cerebro.razonar(mensaje, {
            "negocio": request.negocio,
            "tipo": "cotizacion"
        })

        return {
            "cotizacion": resultado["respuesta"],
            "confianza": resultado["confianza"],
            "generada_en": resultado["timestamp"]
        }

    except Exception as e:
        logger.error(f"Error en cotización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pedido", tags=["Operaciones"])
async def crear_pedido(request: PedidoRequest):
    """
    Crea un nuevo pedido en el sistema

    Automáticamente:
    - Genera ID único (PED-YYYYMMDD-XXXXX)
    - Notifica via WhatsApp
    - Guarda en historial cliente
    """

    try:
        # Generar ID único
        fecha = datetime.now().strftime("%Y%m%d")
        contador = _obtener_contador_pedidos(fecha)
        pedido_id = f"PED-{fecha}-{contador:05d}"

        logger.info(f"Pedido creado: {pedido_id}")

        # Guardar en BD
        pedido = {
            "id": pedido_id,
            "cliente_id": request.cliente_id,
            "cliente_nombre": request.cliente_nombre,
            "producto": request.producto,
            "cantidad": request.cantidad,
            "precio": request.precio,
            "total": request.cantidad * request.precio,
            "negocio": request.negocio,
            "estado": "creado",
            "timestamp": datetime.now().isoformat()
        }

        _guardar_pedido(pedido)

        # Notificar via WhatsApp (sería integración real)
        logger.info(f"Notificación WA sería enviada a {request.cliente_nombre}")

        return {
            "pedido_id": pedido_id,
            "estado": "creado",
            "monto_total": pedido["total"],
            "timestamp": pedido["timestamp"]
        }

    except Exception as e:
        logger.error(f"Error creando pedido: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pedidos/{negocio}", tags=["Operaciones"])
async def listar_pedidos(negocio: str, estado: Optional[str] = None):
    """
    Lista pedidos de un negocio

    Filtros opcionales:
    - estado: "creado", "pagado", "enviado", "entregado"
    """

    try:
        pedidos = _cargar_pedidos_negocio(negocio)

        if estado:
            pedidos = [p for p in pedidos if p["estado"] == estado]

        return {
            "negocio": negocio,
            "total": len(pedidos),
            "pedidos": pedidos
        }

    except Exception as e:
        logger.error(f"Error listando pedidos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE SINCRONIZACIÓN ====================

@app.get("/sync/status", tags=["Sync"])
async def sync_status():
    """Status de sincronización entre PCs"""

    return {
        "conectado": sync.conectado,
        "ultimo_sync": sync.ultimo_sync.isoformat(),
        "tu_pc": sync.tu_pc["nombre"],
        "pc_esposa": sync.pc_esposa["nombre"],
        "cambios_pendientes": len(sync.cambios_locales),
        "conflictos": len(sync.conflictos)
    }


@app.post("/sync/manual", tags=["Sync"])
async def sincronizar_manual():
    """Ejecuta sincronización manual"""

    try:
        logger.info("Sincronización manual solicitada")

        await sync.sincronizar()

        return {
            "status": "completado",
            "timestamp": datetime.now().isoformat(),
            "cambios_locales": len(sync.cambios_locales),
            "cambios_remotos": len(sync.cambios_remotos),
            "conflictos_resueltos": len(sync.conflictos)
        }

    except Exception as e:
        logger.error(f"Error en sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE MEMORIA ====================

@app.get("/memoria/episodios", tags=["Memoria"])
async def obtener_episodios(fecha: Optional[str] = None, limit: int = 10):
    """Obtiene episodios de memoria"""

    try:
        if not fecha:
            fecha = datetime.now().date()

        episodios = cerebro._cargar_episodios_fecha(fecha)

        return {
            "fecha": str(fecha),
            "total": len(episodios),
            "episodios": episodios[-limit:]
        }

    except Exception as e:
        logger.error(f"Error obteniendo episodios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memoria/patrones", tags=["Memoria"])
async def obtener_patrones(limit: int = 20):
    """Obtiene patrones aprendidos"""

    return {
        "total": len(cerebro.patrones_aprendidos),
        "patrones": cerebro.patrones_aprendidos[:limit]
    }


# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para chat en tiempo real

    Flujo:
    1. Cliente se conecta
    2. Envía mensaje JSON
    3. AURORA procesa y responde
    4. Cliente recibe respuesta
    """

    await websocket.accept()
    logger.info("Cliente WebSocket conectado")

    try:
        while True:
            # Recibir mensaje
            datos = await websocket.receive_json()
            mensaje = datos.get("mensaje", "")
            contexto = datos.get("contexto", {})

            if not mensaje:
                await websocket.send_json({"error": "mensaje requerido"})
                continue

            logger.info(f"WS: {mensaje[:50]}...")

            # Procesar con cerebro
            resultado = await cerebro.razonar(mensaje, contexto)

            # Enviar respuesta
            await websocket.send_json({
                "respuesta": resultado["respuesta"],
                "confianza": resultado["confianza"],
                "tipo": resultado["tipo"],
                "timestamp": resultado["timestamp"]
            })

    except Exception as e:
        logger.error(f"Error WebSocket: {e}")
    finally:
        logger.info("Cliente WebSocket desconectado")


# ==================== FUNCIONES AUXILIARES ====================

def _obtener_contador_pedidos(fecha: str) -> int:
    """Obtiene contador de pedidos para hoy"""

    ruta = Path("C:/AURORA/DATA/pedidos_contador.json")
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if ruta.exists():
        with open(ruta) as f:
            contadores = json.load(f)
            contador = contadores.get(fecha, 0) + 1
    else:
        contadores = {}
        contador = 1

    contadores[fecha] = contador

    with open(ruta, "w") as f:
        json.dump(contadores, f)

    return contador


def _guardar_pedido(pedido: Dict):
    """Guarda pedido en BD"""

    ruta = Path("C:/AURORA/DATA/pedidos.jsonl")
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "a") as f:
        f.write(json.dumps(pedido) + "\n")


def _cargar_pedidos_negocio(negocio: str) -> List[Dict]:
    """Carga pedidos de un negocio"""

    ruta = Path("C:/AURORA/DATA/pedidos.jsonl")

    if not ruta.exists():
        return []

    pedidos = []

    with open(ruta) as f:
        for linea in f:
            if linea.strip():
                pedido = json.loads(linea)
                if pedido.get("negocio") == negocio:
                    pedidos.append(pedido)

    return pedidos


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""

    logger.info("=" * 60)
    logger.info("AURORA v2 INICIANDO")
    logger.info("=" * 60)
    logger.info(f"Cerebro: {type(cerebro).__name__} cargado")
    logger.info(f"Memoria episódica: {len(cerebro.memoria_episodica)} entradas")
    logger.info(f"Patrones aprendidos: {len(cerebro.patrones_aprendidos)}")
    logger.info(f"Sincronización: Tu PC ({sync.tu_pc['nombre']}) ↔ PC Esposa ({sync.pc_esposa['nombre']})")
    logger.info("=" * 60)

    # Iniciar sincronización en background
    asyncio.create_task(sync.sincronizar())


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de apagado"""

    logger.info("AURORA v2 APAGÁNDOSE...")
    logger.info(f"Episodios procesados: {sum(len(cerebro._cargar_episodios_fecha(datetime.now().date()))
 for _ in range(1))}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
