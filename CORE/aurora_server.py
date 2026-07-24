"""
AURORA v3 - FastAPI Server
API unificada que usa CEREBRO/consciencia.py como router real.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Asegurar que ROOT está en el path para todos los imports
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("aurora.server")

# Initialize FastAPI
app = FastAPI(
    title="AURORA v3",
    description="Sistema Maestro — router via Consciencia",
    version="3.0.0",
)

# Servir imágenes de referencia de las órdenes de taller
try:
    _img_dir = _ROOT / "UPLOADS" / "ordenes"
    _img_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads-ordenes", StaticFiles(directory=str(_img_dir)), name="uploads-ordenes")
except Exception as _e:
    logger.warning(f"No se montaron imágenes de órdenes: {_e}")

# Servir entradas/salidas del Editor (subir archivo → procesar → descargar)
try:
    _ed_in = _ROOT / "UPLOADS" / "editor_in"
    _ed_out = _ROOT / "UPLOADS" / "editor_out"
    _ed_in.mkdir(parents=True, exist_ok=True)
    _ed_out.mkdir(parents=True, exist_ok=True)
    app.mount("/editor-out", StaticFiles(directory=str(_ed_out)), name="editor-out")
except Exception as _e:
    logger.warning(f"No se montó editor-out: {_e}")

# Servir el álbum de catálogo (imágenes + album.html)
try:
    _cat_dir = _ROOT / "UPLOADS" / "catalogo"
    _cat_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/catalogo", StaticFiles(directory=str(_cat_dir)), name="catalogo")
except Exception as _e:
    logger.warning(f"No se montó catalogo: {_e}")


# Models
class MensajeRequest(BaseModel):
    mensaje: str
    contexto: Optional[dict] = None


class MensajeResponse(BaseModel):
    motor_id: str
    respuesta: str
    sdk_usado: str
    tiempo_ms: int
    status: str


class StatusResponse(BaseModel):
    status: str
    motores_activos: int
    motores_totales: int
    timestamp: str


# Routes
@app.get("/", tags=["Panel"])
async def root():
    """Panel Maestro AURORA"""
    from fastapi.responses import FileResponse
    import os
    p = os.path.join(os.path.dirname(__file__), "..", "TEMPLATES", "panel-completo.html")
    return FileResponse(os.path.abspath(p), media_type="text/html")


@app.get("/panel", tags=["Panel"])
async def panel():
    """Panel Maestro AURORA (alias)"""
    from fastapi.responses import FileResponse
    import os
    p = os.path.join(os.path.dirname(__file__), "..", "TEMPLATES", "panel-completo.html")
    return FileResponse(os.path.abspath(p), media_type="text/html")


# ── ENDPOINTS CRM / ORACLE ────────────────────────────────────────────

@app.get("/oracle/leads", tags=["CRM"])
async def oracle_leads(estado: str = None, negocio: str = None, limite: int = 50):
    """Lista leads reales desde ORACLE SQLite."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
        import oracle_core as oracle
        oracle.init_db()
        # BUG corregido: antes se pasaba 'limite'(int) donde va 'negocio'(str) → int.lower() tronaba 500.
        leads = oracle.listar_leads(estado, negocio)
        if limite and len(leads) > limite:
            leads = leads[:limite]
        return {"status": "ok", "total": len(leads), "leads": leads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oracle/resumen", tags=["CRM"])
async def oracle_resumen(negocio: str = None):
    """Resumen CRM: totales por estado."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
        import oracle_core as oracle
        oracle.init_db()
        return oracle.resumen(negocio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _oracle():
    """Carga ORACLE (motor CRM: leads + órdenes + relación)."""
    import sys
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).parent.parent / "ORACLE"))
    import oracle_core as _o
    _o.init_db()
    return _o


class LeadNuevoReq(BaseModel):
    nombre: str
    telefono: str = ""
    fuente: str = ""
    negocio: str = "atf"
    vehiculo: str = ""
    interes: str = ""
    notas: str = ""


class EstadoLeadReq(BaseModel):
    estado: str


class OrdenCrmReq(BaseModel):
    cliente: str
    telefono: str = ""
    negocio: str = "atf"
    vehiculo: str = ""
    servicio: str = ""
    kit: str = ""
    precio: float = 0
    anticipo: float = 0
    fecha_cita: str = ""
    instalador: str = ""
    notas: str = ""
    lead_id: Optional[int] = None


class ConvertirLeadReq(BaseModel):
    servicio: str = ""
    precio: float = 0
    anticipo: float = 0
    kit: str = ""
    fecha_cita: str = ""
    instalador: str = ""
    notas: str = ""


@app.post("/oracle/lead", tags=["CRM"])
async def oracle_crear_lead(req: LeadNuevoReq):
    """Alta de lead (antes solo existía en el código, sin endpoint)."""
    o = _oracle()
    return await asyncio.to_thread(o.crear_lead, req.nombre, req.telefono, req.fuente,
                                   req.negocio, req.vehiculo, req.interes, req.notas)


@app.get("/oracle/lead/{lead_id}", tags=["CRM"])
async def oracle_ficha_cliente(lead_id: int):
    """Vista 360 del cliente: el lead + TODAS sus órdenes + facturado/por cobrar."""
    return await asyncio.to_thread(_oracle().ficha_cliente, lead_id)


@app.post("/oracle/lead/{lead_id}/estado", tags=["CRM"])
async def oracle_estado_lead(lead_id: int, req: EstadoLeadReq):
    try:
        return await asyncio.to_thread(_oracle().actualizar_lead_estado, lead_id, req.estado)
    except ValueError as e:
        return {"status": "error", "mensaje": str(e)}


@app.post("/oracle/lead/{lead_id}/convertir", tags=["CRM"])
async def oracle_convertir(lead_id: int, req: ConvertirLeadReq):
    """Convierte un lead en ORDEN dejando la relación (así se rastrea qué fuente vende)."""
    o = _oracle()
    try:
        return await asyncio.to_thread(o.convertir_lead_a_orden, lead_id, req.servicio, req.precio,
                                       req.anticipo, req.kit, req.fecha_cita, req.instalador, req.notas)
    except ValueError as e:
        return {"status": "error", "mensaje": str(e)}


@app.get("/oracle/ordenes", tags=["CRM"])
async def oracle_listar_ordenes(estado: str = None, negocio: str = None):
    """Órdenes del CRM (estaba escrito en el motor pero era invisible)."""
    ords = await asyncio.to_thread(_oracle().listar_ordenes, estado, negocio)
    return {"status": "ok", "total": len(ords), "ordenes": ords}


@app.post("/oracle/orden", tags=["CRM"])
async def oracle_crear_orden(req: OrdenCrmReq):
    o = _oracle()
    try:
        return await asyncio.to_thread(o.crear_orden, req.cliente, req.telefono, req.negocio,
                                       req.vehiculo, req.servicio, req.kit, req.precio, req.anticipo,
                                       req.fecha_cita, req.instalador, req.notas, req.lead_id)
    except ValueError as e:
        return {"status": "error", "mensaje": str(e)}


@app.post("/oracle/orden/{orden_id}/estado", tags=["CRM"])
async def oracle_estado_orden(orden_id: int, req: EstadoLeadReq):
    try:
        return await asyncio.to_thread(_oracle().actualizar_orden_estado, orden_id, req.estado)
    except ValueError as e:
        return {"status": "error", "mensaje": str(e)}


@app.get("/oracle/pronostico", tags=["CRM"])
async def oracle_pronostico(negocio: str = None):
    """Cuánto dinero traes en el embudo por etapa."""
    return await asyncio.to_thread(_oracle().pronostico_embudo, negocio)


@app.get("/oracle/fuentes", tags=["CRM"])
async def oracle_fuentes(negocio: str = None):
    """Qué fuente de leads SÍ convierte en ventas (con % de conversión)."""
    return await asyncio.to_thread(_oracle().fuentes_efectivas, negocio)


def _taller_core():
    """Motor de vectores/DXF del taller."""
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("taller_core", _ROOT / "TALLER" / "taller_core.py")
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


class TextoDxfReq(BaseModel):
    texto: str
    alto_cm: float = 5.0
    fuente: str = "Arial"


class GrosorReq(BaseModel):
    x: float
    y: float
    h: float
    nuevo_grosor: float
    generador: str = "UniversalBox"
    dedos: float = 2.0


@app.post("/taller/texto-dxf", tags=["Taller"])
async def taller_texto_dxf(req: TextoDxfReq):
    """Convierte un nombre/texto en DXF vectorial para cortar o grabar."""
    return await asyncio.to_thread(_taller_core().texto_a_dxf, req.texto, req.alto_cm, req.fuente)


@app.post("/taller/reajustar-grosor", tags=["Taller"])
async def taller_reajustar_grosor(req: GrosorReq):
    """Regenera una caja al NUEVO grosor de material manteniendo el tamaño del artículo
    (los encastres/dedos se ajustan solos). Ideal al cambiar de MDF 2.7 a 5.5 mm."""
    tc = _taller_core()
    return await asyncio.to_thread(tc.reajustar_grosor, req.x, req.y, req.h,
                                   req.nuevo_grosor, req.generador, req.dedos)


def _equipos():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("equipos", _ROOT / "CEREBRO" / "equipos.py")
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


@app.get("/equipos/listar", tags=["Equipos"])
async def equipos_listar():
    """Librería de equipos de trabajo (marketing, ventas, diseño, taller, publicación)."""
    return await asyncio.to_thread(_equipos().listar_equipos)


class ActivarEquipoReq(BaseModel):
    equipo_id: str


@app.post("/equipos/activar", tags=["Equipos"])
async def equipos_activar(req: ActivarEquipoReq):
    """Pone a trabajar un equipo: ejecuta su acción real coordinando sus motores."""
    return await asyncio.to_thread(_equipos().activar_equipo, req.equipo_id)


@app.get("/intuicion/sugerencia", tags=["Intuición"])
async def intuicion_sugerencia():
    """Sugerencia PROACTIVA basada en lo que AURORA ha aprendido del uso de Anuar.
    Es la 'intuición': detecta áreas de oportunidad por frecuencia y propone. Sin
    datos suficientes → lo dice honesto (no inventa)."""
    try:
        from MEMORIA.perfil_habilidades import perfil_habilidades
        await perfil_habilidades.inicializar()
        sug = await perfil_habilidades.sugerencia_proactiva()
        perfil = await perfil_habilidades.obtener_perfil()
        areas = perfil.get("areas_oportunidad", [])
        if not sug:
            return {"status": "aprendiendo",
                    "detalle": "Aún no tengo suficiente patrón de uso para anticiparme. "
                               "Mientras más uses AURORA, mejor te va a intuir.",
                    "areas_detectadas": len(areas)}
        return {"status": "ok", "sugerencia": sug,
                "areas_oportunidad": areas[:5],
                "nota": "Basado en tu uso real, no en suposiciones."}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


@app.get("/intuicion/perfil", tags=["Intuición"])
async def intuicion_perfil():
    """Lo que AURORA ha aprendido de Anuar (habilidades + áreas de oportunidad)."""
    try:
        from MEMORIA.perfil_habilidades import perfil_habilidades
        await perfil_habilidades.inicializar()
        return await perfil_habilidades.obtener_perfil()
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


@app.get("/health", tags=["Health"])
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "aurora": "ready"}


@app.get("/status", tags=["Status"], response_model=StatusResponse)
async def status():
    """Estado del sistema via Bus Neuronal"""
    try:
        from CEREBRO.bus_neuronal import bus
        estado = bus.estado()
        n = len(estado.get("motores_registrados", []))
        return StatusResponse(
            status="operativo",
            motores_activos=n,
            motores_totales=29,
            timestamp=datetime.now().isoformat(),
        )
    except Exception:
        return StatusResponse(status="iniciando", motores_activos=0,
                              motores_totales=29, timestamp=datetime.now().isoformat())


@app.post("/procesar", tags=["Mensaje"], response_model=MensajeResponse)
async def procesar_mensaje(request: MensajeRequest):
    """Procesa mensaje via consciencia (router LLM real)"""
    try:
        from CEREBRO.consciencia import consciencia
        if not consciencia._listo:
            await consciencia.inicializar()
        result = await consciencia.procesar(
            mensaje=request.mensaje, user_id="anuar", canal="api"
        )
        return MensajeResponse(
            motor_id=",".join(result.get("motores_usados", ["consciencia"])),
            respuesta=result.get("respuesta", ""),
            sdk_usado="groq",
            tiempo_ms=result.get("duracion_ms", 0),
            status="success",
        )
    except Exception as e:
        logger.error(f"Error en /procesar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/motores", tags=["Motores"])
async def list_motores():
    """Lista motores registrados en el bus"""
    try:
        from CEREBRO.bus_neuronal import bus
        motores = bus.estado().get("motores_registrados", [])
        return {"motores": motores, "total": len(motores)}
    except Exception as e:
        return {"motores": [], "total": 0, "error": str(e)}


class MotorEjecutarRequest(BaseModel):
    consulta: str = ""
    accion: Optional[str] = None
    datos: Optional[dict] = None
    contexto: Optional[dict] = None


@app.post("/motor/{motor_id}/ejecutar", tags=["Motores"])
async def ejecutar_motor(motor_id: str, request: MotorEjecutarRequest):
    """Ejecuta UN motor específico vía el bus neuronal y devuelve su resultado REAL."""
    import time as _time
    try:
        from CEREBRO.bus_neuronal import bus
        registrados = bus.estado().get("motores_registrados", [])
        if motor_id not in registrados:
            raise HTTPException(status_code=404, detail=f"Motor '{motor_id}' no registrado")
        # Contenido genérico: cubre motores LLM (consulta/mensaje) y de acción (accion/datos)
        contenido = {
            "consulta": request.consulta,
            "mensaje": request.consulta,
            "datos": request.consulta,
            "contexto": request.contexto or {},
        }
        if request.accion:
            contenido["accion"] = request.accion
        if request.datos:
            contenido.update(request.datos)
        t0 = _time.time()
        resultado = await bus.solicitar("panel", motor_id, contenido, timeout=30.0)
        dur = int((_time.time() - t0) * 1000)
        if resultado is None:
            return {
                "motor": motor_id, "status": "sin_respuesta", "resultado": None,
                "mensaje": f"'{motor_id}' no respondió a esta petición. Puede requerir una 'accion' o parámetros específicos.",
                "duracion_ms": dur,
            }
        return {"motor": motor_id, "status": "ok", "resultado": resultado, "duracion_ms": dur}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutar_motor {motor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── ÓRDENES DE TRABAJO DEL TALLER ─────────────────────────────────────
_ORDENES = None
def _ordenes():
    global _ORDENES
    if _ORDENES is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ordenes_taller", _ROOT / "TALLER" / "ordenes_taller.py")
        _ORDENES = _ilu.module_from_spec(spec)
        spec.loader.exec_module(_ORDENES)
    return _ORDENES


class CotizarReq(BaseModel):
    producto: str
    cantidad: int = 1


class OrdenReq(BaseModel):
    solicitante: str
    cliente: str
    telefono: str = ""
    trabajo: str
    piezas: int = 1
    producto: str = ""
    precio_unitario: float = 0
    valor_total: float = 0
    costo_real: float = 0
    anticipo: float = 0
    fecha_inicio: str = ""
    fecha_entrega: str = ""
    notas: str = ""
    imagenes: list = []


class EstadoReq(BaseModel):
    estado: str


@app.post("/taller/cotizar", tags=["Taller"])
async def taller_cotizar(req: CotizarReq):
    """Cotización determinista con precios REALES del catálogo (no inventa)."""
    return await asyncio.to_thread(_ordenes().cotizar, req.producto, req.cantidad)


@app.post("/taller/orden", tags=["Taller"])
async def taller_crear(req: OrdenReq):
    """Crea una orden de trabajo del taller."""
    return await asyncio.to_thread(_ordenes().crear_orden, req.dict())


@app.get("/taller/ordenes", tags=["Taller"])
async def taller_listar(estado: str = None):
    """Lista órdenes de trabajo (opcional filtrar por estado)."""
    return await asyncio.to_thread(_ordenes().listar_ordenes, estado)


@app.post("/taller/orden/{orden_id}/editar", tags=["Taller"])
async def taller_editar(orden_id: int, req: OrdenReq):
    """Edita una orden EXISTENTE (mismo folio, sin duplicar). Recalcula saldo/utilidad."""
    return await asyncio.to_thread(_ordenes().editar_orden, orden_id, req.dict())


@app.post("/taller/orden/{orden_id}/estado", tags=["Taller"])
async def taller_estado(orden_id: int, req: EstadoReq):
    """Actualiza el estado de una orden (agendado/en_proceso/listo/entregado/cancelado)."""
    return await asyncio.to_thread(_ordenes().actualizar_estado, orden_id, req.estado)


@app.get("/taller/alertas", tags=["Taller"])
async def taller_alertas():
    """Alertas de entrega en vivo (atrasadas + entrega ≤12h + agendadas)."""
    return await asyncio.to_thread(_ordenes().alertas)


@app.get("/taller/catalogo", tags=["Taller"])
async def taller_catalogo():
    """Catálogo combinado (ATF + Milens) para el buscador de productos."""
    c = await asyncio.to_thread(_ordenes().catalogo)
    return {"total": len(c), "productos": c}


class ImagenUrlReq(BaseModel):
    url: str


@app.post("/taller/imagen", tags=["Taller"])
async def taller_imagen_upload(file: UploadFile = File(...)):
    """Sube una imagen de referencia (archivo/arrastrada). Devuelve URL servible."""
    datos = await file.read()
    return await asyncio.to_thread(_ordenes().guardar_imagen_bytes, file.filename, datos)


@app.post("/taller/imagen-url", tags=["Taller"])
async def taller_imagen_url(req: ImagenUrlReq):
    """Descarga una imagen desde URL (Pinterest, etc.) y la guarda local."""
    return await asyncio.to_thread(_ordenes().guardar_imagen_url, req.url)


@app.post("/chat/archivo", tags=["Chat"])
async def chat_archivo(file: UploadFile = File(...)):
    """Recibe un archivo arrastrado/pegado al chat, lo GUARDA de verdad y dice qué
    puede hacer AURORA con él (real, sin simular). Fase 2: el chat como operador."""
    from pathlib import Path as _P
    datos = await file.read()
    carpeta = _ROOT / "ENTRADAS_CHAT"
    carpeta.mkdir(exist_ok=True)
    destino = carpeta / (file.filename or "archivo")
    destino.write_bytes(datos)
    ext = destino.suffix.lower().lstrip(".")
    kb = round(len(datos) / 1024, 1)
    sugerencias = {
        "jpg": "cotizar corte láser, quitar fondo, foto→dibujo lineal, pasar a B&N para láser",
        "jpeg": "cotizar corte láser, quitar fondo, foto→dibujo lineal, pasar a B&N para láser",
        "png": "cotizar corte láser, quitar fondo, foto→dibujo lineal, pasar a B&N para láser",
        "pdf": "convertir a DXF/PNG a 300 DPI, o ingerir a la Biblioteca para que lo aprenda",
        "svg": "convertir a DXF para RDWorks/Aspire, o aligerar",
        "dxf": "aligerar, reescalar, o preparar planilla de corte",
        "mp4": "usar como contenido para publicar en redes",
        "mov": "usar como contenido para publicar en redes",
    }
    accion = sugerencias.get(ext, "guardarlo; dime qué quieres hacer con él")
    return {"status": "recibido", "archivo": str(destino), "nombre": file.filename,
            "kb": kb, "tipo": ext or "desconocido",
            "respuesta": (f"📎 Recibí **{file.filename}** ({kb} KB) y lo guardé de verdad en ENTRADAS_CHAT. "
                          f"Con esto puedo: {accion}. Dime cuál y lo hago.")}


class VerReq(BaseModel):
    imagen_b64: str          # imagen en base64 (sin el prefijo data:...)
    pregunta: str = "¿Qué ves en esta imagen? Descríbelo en español, claro y breve."


@app.post("/chat/ver", tags=["Chat"])
async def chat_ver(req: VerReq):
    """👁️ AURORA VE: analiza una imagen (de la cámara o subida) con un modelo de visión
    LOCAL (moondream en Ollama). Local y privado: la imagen NUNCA sale de la PC."""
    import requests as _rq
    b64 = req.imagen_b64.split(",", 1)[-1].strip()  # tolera prefijo data:image/...
    def _pedir():
        r = _rq.post("http://127.0.0.1:11434/api/generate",
                     json={"model": "moondream", "prompt": req.pregunta,
                           "images": [b64], "stream": False}, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    try:
        desc = await asyncio.to_thread(_pedir)
        if not desc:
            return {"status": "sin_respuesta", "respuesta": "No logré describir la imagen (no invento lo que no vi)."}
        return {"status": "ok", "respuesta": f"👁️ {desc}"}
    except Exception as e:
        det = str(e)[:200]
        if "11434" in det or "Max retries" in det or "refused" in det.lower():
            return {"status": "sin_modelo", "respuesta": "Aún no tengo el modelo de visión listo (moondream se está descargando o Ollama no está corriendo). No te invento lo que veo."}
        return {"status": "error", "respuesta": f"No pude ver la imagen: {det}"}


@app.post("/chat/oir", tags=["Chat"])
async def chat_oir(file: UploadFile = File(...)):
    """👂 AURORA OYE fino: transcribe audio con Whisper de Groq (aguanta acento y ruido
    de taller). Devuelve el texto para meterlo al chat."""
    import os as _os, requests as _rq
    key = _os.getenv("GROQ_API_KEY", "")
    if not key:
        return {"status": "sin_llave", "texto": "", "respuesta": "Falta GROQ_API_KEY para Whisper."}
    datos = await file.read()
    def _transcribir():
        r = _rq.post("https://api.groq.com/openai/v1/audio/transcriptions",
                     headers={"Authorization": f"Bearer {key}"},
                     files={"file": (file.filename or "audio.webm", datos, "audio/webm")},
                     data={"model": "whisper-large-v3", "language": "es"}, timeout=60)
        r.raise_for_status()
        return r.json().get("text", "").strip()
    try:
        texto = await asyncio.to_thread(_transcribir)
        return {"status": "ok", "texto": texto}
    except Exception as e:
        return {"status": "error", "texto": "", "respuesta": f"No pude transcribir (necesita internet): {str(e)[:200]}"}


# ── EDITOR · AURORA hace el trabajo de diseño (skills profesionales) ──
_CONV = None
def _conv():
    global _CONV
    if _CONV is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("conversiones", _ROOT / "EDITOR" / "conversiones.py")
        _CONV = _ilu.module_from_spec(spec); spec.loader.exec_module(_CONV)
    return _CONV


class ConvReq(BaseModel):
    archivo: str
    salida: str = ""
    pagina: int = 0


@app.post("/editor/aligerar-dxf", tags=["Editor"])
async def editor_aligerar(req: ConvReq):
    """DXF pesado con splines → polilíneas R2000, legible en RDWorks."""
    return await asyncio.to_thread(_conv().aligerar_dxf, req.archivo, req.salida)


@app.post("/editor/bw", tags=["Editor"])
async def editor_bw(req: ConvReq):
    """Imagen o PDF → B&N puro a 300 DPI (prep para Aspire)."""
    return await asyncio.to_thread(_conv().a_bw_puro, req.archivo, req.salida, 300, 128, req.pagina)


@app.post("/editor/linea", tags=["Editor"])
async def editor_linea(req: ConvReq):
    """Foto/imagen → dibujo lineal (contorno)."""
    return await asyncio.to_thread(_conv().a_linea, req.archivo, req.salida)


@app.post("/editor/papercraft-dxf", tags=["Editor"])
async def editor_papercraft(req: ConvReq):
    """Papercraft (imagen) → DXF vectorizado. Honesto: revisar en Aspire."""
    return await asyncio.to_thread(_conv().papercraft_a_dxf, req.archivo, req.pagina, req.salida)


# ── EDITOR · CONVERSOR DE FORMATOS (Función #1: SVG/DXF/PDF/PNG vía Inkscape) ──
_CONVF = None
def _convf():
    global _CONVF
    if _CONVF is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("conversor_formatos", _ROOT / "EDITOR" / "conversor_formatos.py")
        _CONVF = _ilu.module_from_spec(spec); spec.loader.exec_module(_CONVF)
    return _CONVF


class ConvFmtReq(BaseModel):
    archivo: str
    a: str                 # formato destino: svg/png/pdf/dxf/eps/ps
    salida: str = ""
    dpi: int = 300
    pagina: int | None = None


class ConvTodoReq(BaseModel):
    archivo: str           # PDF multipágina
    a: str = "svg"
    dpi: int = 300
    carpeta: str = ""


@app.get("/editor/formatos", tags=["Editor"])
async def editor_formatos():
    """Qué convierte el módulo y los límites honestos (CDR importa, studio3 no exporta)."""
    return _convf().formatos()


@app.post("/editor/convertir", tags=["Editor"])
async def editor_convertir(req: ConvFmtReq):
    """Convierte un archivo entre SVG/DXF/PDF/PNG/EPS/PS con Inkscape real (~20s en frío)."""
    return await asyncio.to_thread(_convf().convertir, req.archivo, req.a, req.salida, req.dpi, req.pagina)


@app.post("/editor/convertir-todo", tags=["Editor"])
async def editor_convertir_todo(req: ConvTodoReq):
    """PDF multipágina → un archivo por página (lote). Ideal para reeditar o imprimir."""
    return await asyncio.to_thread(_convf().convertir_todo, req.archivo, req.a, req.dpi, req.carpeta)


# ── EDITOR · ESCALAS / DPI / PLANILLAS (Función #5 + Modo Rápido) ──────
_ESC = None
def _esc():
    global _ESC
    if _ESC is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("escalas_planillas", _ROOT / "EDITOR" / "escalas_planillas.py")
        _ESC = _ilu.module_from_spec(spec); spec.loader.exec_module(_ESC)
    return _ESC


# ── EDITOR · REEDITAR DISEÑO (Función #2: analizar/extraer/realzar/reescalar) ──
_REED = None
def _reed():
    global _REED
    if _REED is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("reeditar_diseno", _ROOT / "EDITOR" / "reeditar_diseno.py")
        _REED = _ilu.module_from_spec(spec); spec.loader.exec_module(_REED)
    return _REED


class EscalarReq(BaseModel):
    archivo: str
    ancho_cm: float
    alto_cm: float = 0
    dpi: int = 300
    modo: str = "rapido"
    mantener_proporcion: bool = True
    salida: str = ""


class DpiReq(BaseModel):
    archivo: str
    dpi: int = 300
    salida: str = ""


class PlanillaReq(BaseModel):
    archivo: str
    item_ancho_cm: float
    item_alto_cm: float = 0
    formato: str = "A4"
    dpi: int = 300
    margen_cm: float = 1.0
    gap_cm: float = 0.5
    orientacion: str = "vertical"
    fondo: str = "white"
    salida: str = ""


@app.get("/editor/formatos-papel", tags=["Editor"])
async def editor_formatos_papel():
    """Formatos de papel (A4/A3/carta/tabloide/gran formato) y DPI recomendado."""
    return _esc().formatos_papel()


@app.post("/editor/info-dpi", tags=["Editor"])
async def editor_info_dpi(req: DpiReq):
    """Reporta px, DPI embebido y el tamaño físico real de impresión."""
    return await asyncio.to_thread(_esc().info_dpi, req.archivo, req.dpi)


@app.post("/editor/fijar-dpi", tags=["Editor"])
async def editor_fijar_dpi(req: DpiReq):
    """Cambia solo el DPI embebido (ajusta tamaño de impresión sin remuestrear)."""
    return await asyncio.to_thread(_esc().fijar_dpi, req.archivo, req.dpi, req.salida)


@app.post("/editor/escalar", tags=["Editor"])
async def editor_escalar(req: EscalarReq):
    """Modo Rápido: lleva una imagen a una medida física (cm) con interpolación LANCZOS."""
    return await asyncio.to_thread(_esc().escalar_a_medida, req.archivo, req.ancho_cm,
                                   req.alto_cm, req.dpi, req.modo, req.mantener_proporcion, req.salida)


@app.post("/editor/planilla", tags=["Editor"])
async def editor_planilla(req: PlanillaReq):
    """Imposición: llena una hoja con copias de un ítem a medida exacta (stickers/sublimación)."""
    return await asyncio.to_thread(_esc().generar_planilla, req.archivo, req.item_ancho_cm,
                                   req.item_alto_cm, req.formato, req.dpi, req.margen_cm,
                                   req.gap_cm, req.orientacion, (), req.fondo, req.salida)


# ── BIBLIOTECA · conocimiento de manuales (AURORA consulta) ───────────
_BIB = None
def _bib():
    global _BIB
    if _BIB is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("biblioteca", _ROOT / "BIBLIOTECA" / "biblioteca.py")
        _BIB = _ilu.module_from_spec(spec); spec.loader.exec_module(_BIB)
    return _BIB


class BuscarReq(BaseModel):
    consulta: str
    limite: int = 4


class IngerirReq(BaseModel):
    ruta: str
    nombre: str = ""


@app.post("/biblioteca/buscar", tags=["Biblioteca"])
async def biblioteca_buscar(req: BuscarReq):
    return await asyncio.to_thread(_bib().buscar, req.consulta, req.limite)


@app.post("/biblioteca/ingerir", tags=["Biblioteca"])
async def biblioteca_ingerir(req: IngerirReq):
    return await asyncio.to_thread(_bib().ingerir_pdf, req.ruta, req.nombre)


@app.get("/biblioteca/estado", tags=["Biblioteca"])
async def biblioteca_estado():
    return await asyncio.to_thread(_bib().estado)


# ── SISTEMA · optimizador de PC (AURORA cuida tu equipo) ─────────────
_OPT = None
def _opt():
    global _OPT
    if _OPT is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("optimizador", _ROOT / "SISTEMA" / "optimizador.py")
        _OPT = _ilu.module_from_spec(spec); spec.loader.exec_module(_OPT)
    return _OPT


@app.get("/sistema/diagnostico", tags=["Sistema"])
async def sistema_diagnostico():
    return await asyncio.to_thread(_opt().diagnostico)


@app.post("/sistema/optimizar", tags=["Sistema"])
async def sistema_optimizar():
    return await asyncio.to_thread(_opt().optimizar)


# ── CLUSTER DE INGRESOS · Marketing / Publicador / Vendedor ───────────
def _carga_mod(carpeta, archivo, nombre):
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location(nombre, _ROOT / carpeta / archivo)
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m

_ASESOR = None
def _asesor():
    global _ASESOR
    if _ASESOR is None: _ASESOR = _carga_mod("MARKETING", "asesor_core.py", "asesor_core")
    return _ASESOR

_PUB = None
def _pub():
    global _PUB
    if _PUB is None: _PUB = _carga_mod("PUBLICADOR", "publicador_core.py", "publicador_core")
    return _PUB

_VEND = None
def _vend():
    global _VEND
    if _VEND is None: _VEND = _carga_mod("VENDEDOR", "vendedor_core.py", "vendedor_core")
    return _VEND


@app.get("/marketing/conocimiento", tags=["Marketing"])
async def mk_conocimiento(red: str = None):
    """Algoritmos y señales que premia cada red (datos reales)."""
    return await asyncio.to_thread(_asesor().conocimiento, red)

@app.get("/marketing/playbook", tags=["Marketing"])
async def mk_playbook(flanco: str = None):
    """Playbook por flanco (viralización/ventas/monetización)."""
    return await asyncio.to_thread(_asesor().playbook, flanco)

@app.get("/marketing/horarios", tags=["Marketing"])
async def mk_horarios():
    """Mejores horarios (honesto: SIN_DATOS si no hay métricas)."""
    return await asyncio.to_thread(_asesor().mejores_horarios, None)

@app.get("/publicador/estado-redes", tags=["Publicador"])
async def pub_estado():
    """Estado real de conexión de redes (FB/IG)."""
    return await asyncio.to_thread(_pub().estado_redes)

@app.get("/publicador/estado-whatsapp", tags=["Publicador"])
async def pub_wa():
    return await asyncio.to_thread(_pub().estado_whatsapp)

@app.get("/publicador/comentarios", tags=["Publicador"])
async def pub_comentarios(limite: int = 10):
    return await asyncio.to_thread(_pub().comentarios_pagina, limite)

class PublicarReq(BaseModel):
    plataforma: str
    texto: str = ""
    media_url: str = ""

@app.post("/publicador/publicar", tags=["Publicador"])
async def pub_publicar(req: PublicarReq):
    """Publica en la plataforma. ⚠️ Acción real — Anuar aprueba antes."""
    return await asyncio.to_thread(_pub().publicar, req.plataforma, req.texto, req.media_url)

def _pub_inteligente():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("publicacion_inteligente", _ROOT / "MARKETING" / "publicacion_inteligente.py")
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


@app.get("/publicador/preparar-hoy", tags=["Publicador"])
async def pub_preparar_hoy(negocio: str = "atf"):
    """Arma el post de hoy con criterio de viralización (video + copy nativo + hora). NO publica."""
    return await asyncio.to_thread(_pub_inteligente().preparar_publicacion, negocio)


@app.get("/publicador/estrategia", tags=["Publicador"])
async def pub_estrategia(negocio: str = "atf", tema: str = ""):
    """EQUIPO INTERACTIVO: algoritmo + estudio de mercado + plan de contenido, en una llamada."""
    return await asyncio.to_thread(_pub_inteligente().estrategia_ingresos, negocio, tema)


class PublicarHoyReq(BaseModel):
    red: str = "facebook"
    descripcion: str = ""
    aprobar: bool = False


@app.post("/publicador/publicar-hoy", tags=["Publicador"])
async def pub_publicar_hoy(req: PublicarHoyReq):
    """Publica el video de HOY. aprobar=False = dry-run (no sube). aprobar=True = REAL."""
    return await asyncio.to_thread(_pub_inteligente().publicar_hoy, req.red, req.descripcion, req.aprobar)


class VideoFbReq(BaseModel):
    ruta: str
    descripcion: str = ""

@app.post("/publicador/video-facebook", tags=["Publicador"])
async def pub_video_fb(req: VideoFbReq):
    """Sube un VIDEO local a la página de Facebook. ⚠️ PUBLICACIÓN REAL Y PÚBLICA —
    solo se dispara cuando Anuar lo pide expresamente."""
    return await asyncio.to_thread(_pub().publicar_video_fb, req.ruta, req.descripcion)

class ResponderComentarioReq(BaseModel):
    comment_id: str
    texto: str

@app.post("/publicador/responder-comentario", tags=["Publicador"])
async def pub_responder_comentario(req: ResponderComentarioReq):
    """Responde un comentario REAL en Facebook. ⚠️ Acción pública — Anuar aprueba."""
    return await asyncio.to_thread(_pub().responder_comentario, req.comment_id, req.texto)

@app.get("/vendedor/fichas", tags=["Vendedor"])
async def vend_fichas():
    return await asyncio.to_thread(_vend().listar_fichas)

@app.get("/vendedor/ficha", tags=["Vendedor"])
async def vend_ficha(producto: str):
    return await asyncio.to_thread(_vend().ficha, producto)

@app.get("/vendedor/tecnicas", tags=["Vendedor"])
async def vend_tecnicas(nombre: str = None):
    return await asyncio.to_thread(_vend().tecnicas, nombre)


class FichaEditReq(BaseModel):
    id: str
    nombre: str | None = None
    precio: float | None = None
    que_es: str | None = None
    compatibilidad: list | None = None
    diferencias: str | None = None
    specs: dict | None = None
    recomendado_para: str | None = None
    argumentos_venta: list | None = None
    fuentes: list | None = None


@app.post("/vendedor/guardar-ficha", tags=["Vendedor"])
async def vend_guardar_ficha(req: FichaEditReq):
    """Editor del panel: corrige/completa una ficha por su id (permite arreglar datos malos)."""
    datos = req.dict(exclude_none=True, exclude={"id", "fuentes"})
    return await asyncio.to_thread(_vend().editar_ficha, req.id, datos, req.fuentes)


class PitchReq(BaseModel):
    producto: str
    modo: str = "cliente"          # "cliente" (vender) o "interno" (asesor técnico de Anuar)
    objetivo: str = ""

@app.post("/vendedor/pitch", tags=["Vendedor"])
async def vend_pitch(req: PitchReq):
    """Genera el pitch/asesoría REAL: brief con la ficha real (marca lo pendiente) + Groq LLM.
    HONESTO: si la ficha tiene datos pendientes, el brief lo indica y el pitch no inventa specs."""
    def _run():
        import os, requests as _rq
        try:
            system = _vend().construir_brief(req.modo, req.producto, req.objetivo)
        except Exception as e:
            return {"status": "error", "mensaje": f"No se pudo armar el brief: {e}"}
        objetivo = req.objetivo or ("asesorar técnicamente a Anuar" if req.modo == "interno" else "cerrar la venta")
        user = (f"Genera el pitch/asesoría para este caso. Producto: {req.producto}. "
                f"Objetivo: {objetivo}. Usa SOLO los datos reales de la ficha; lo que esté "
                "pendiente, dilo con honestidad y ofrece confirmarlo (no inventes specs).")
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return {"status": "error", "mensaje": "Falta GROQ_API_KEY en el entorno."}
        try:
            r = _rq.post("https://api.groq.com/openai/v1/chat/completions",
                         headers={"Authorization": f"Bearer {key}"},
                         json={"model": "llama-3.1-8b-instant",
                               "messages": [{"role": "system", "content": system},
                                            {"role": "user", "content": user}],
                               "temperature": 0.8, "max_tokens": 1200}, timeout=45)
            texto = r.json()["choices"][0]["message"]["content"]
            return {"status": "ok", "pitch": texto, "producto": req.producto, "modo": req.modo}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}
    return await asyncio.to_thread(_run)


# ── COTIZADOR DE CORTE por DXF (skill de taller) ─────────────────────
_COT = None
def _cot():
    global _COT
    if _COT is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("cotizador_corte", _ROOT / "EDITOR" / "cotizador_corte.py")
        _COT = _ilu.module_from_spec(spec); spec.loader.exec_module(_COT)
    return _COT

class CotizarCorteReq(BaseModel):
    archivo: str
    material: str = ""
    velocidad_mm_s: float = 15.0
    margen_pct: float = 30.0

@app.post("/taller/cotizar-dxf", tags=["Taller"])
async def taller_cotizar_dxf(req: CotizarCorteReq):
    """Cotiza corte láser desde un DXF: longitud real + tiempo + material (precios Milens)."""
    return await asyncio.to_thread(_cot().cotizar_corte, req.archivo, req.material, req.velocidad_mm_s, req.margen_pct)


# ── COTIZAR desde IMAGEN pegada en el chat (quita fondo -> vectoriza -> escala -> cotiza) ──
_COTIMG = None
def _cotimg():
    global _COTIMG
    if _COTIMG is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("cotizar_imagen", _ROOT / "CEREBRO" / "cotizar_imagen.py")
        _COTIMG = _ilu.module_from_spec(spec); spec.loader.exec_module(_COTIMG)
    return _COTIMG

class CotizarImagenReq(BaseModel):
    imagen_ruta: str
    material: str = "MDF 2.7mm (Hoja)"
    altura_cm: float = 30.0
    modo: str = "corte_contorno"
    velocidad_corte_mm_s: float = 20.0
    velocidad_grabado_mm_s: float = 200.0

@app.post("/chat/cotizar-imagen", tags=["Chat"])
async def chat_cotizar_imagen(req: CotizarImagenReq):
    """Cotiza corte/grabado láser REAL desde una imagen: quita fondo, vectoriza a DXF, escala a la altura y mide (nunca inventa el precio)."""
    return await asyncio.to_thread(
        _cotimg().cotizar_imagen_laser, req.imagen_ruta, req.material, req.altura_cm,
        req.modo, req.velocidad_corte_mm_s, req.velocidad_grabado_mm_s)


# ── MÁXIMA EXPRESIÓN · generador de contenido (encadena asesor + LLM) ─
class ContenidoReq(BaseModel):
    producto: str
    red: str = "tiktok"
    objetivo: str = "ventas"

@app.post("/marketing/generar-contenido", tags=["Marketing"])
async def mk_generar_contenido(req: ContenidoReq):
    """Encadena el algoritmo real de la red + LLM → contenido listo (gancho, guion, copy, hashtags)."""
    def _run():
        import os, requests as _rq
        conoc = _asesor().conocimiento(req.red)
        señales = conoc.get("algoritmo", {}).get("señales_premia", []) if isinstance(conoc, dict) else []
        prompt = (
            f"Eres experto en contenido para {req.red}. Producto: {req.producto}. Objetivo: {req.objetivo}. "
            f"El algoritmo de {req.red} premia: {', '.join(señales[:4]) or 'retención y engagement'}. "
            "Genera contenido REAL en español (mexicano, natural), en JSON con: gancho (primeros 3 seg), "
            "guion_corto (para reel/video), copy (descripción), hashtags (6). Solo el JSON."
        )
        key = os.getenv("GROQ_API_KEY")
        try:
            r = _rq.post("https://api.groq.com/openai/v1/chat/completions",
                         headers={"Authorization": f"Bearer {key}"},
                         json={"model": "llama-3.1-8b-instant",
                               "messages": [{"role": "user", "content": prompt}],
                               "temperature": 0.85}, timeout=30)
            texto = r.json()["choices"][0]["message"]["content"]
            return {"status": "ok", "red": req.red, "producto": req.producto,
                    "algoritmo_usado": señales[:4], "contenido": texto}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}
    return await asyncio.to_thread(_run)


# ── PLAN DE CONTENIDO para MONETIZACIÓN (Reels + consistencia) ────────
class PlanReq(BaseModel):
    negocio: str = "Milens (taller láser, sublimación, DTF, prendas) y ATF (retrofit de faros)"
    red: str = "facebook"
    dias: int = 7
    objetivo: str = "monetizar: maximizar alcance y watch time (Reels) para cumplir requisitos de Meta"

@app.post("/marketing/plan-contenido", tags=["Marketing"])
async def mk_plan_contenido(req: PlanReq):
    """Genera un plan de contenido de N días enfocado a monetización (Reels, watch time, constancia)."""
    def _run():
        import os, requests as _rq
        conoc = _asesor().conocimiento(req.red)
        señales = conoc.get("algoritmo", {}).get("señales_premia", []) if isinstance(conoc, dict) else []
        dias = max(1, min(int(req.dias or 7), 30))
        prompt = (
            f"Eres estratega de contenido para {req.red}, enfocado en MONETIZACIÓN. "
            f"Negocio: {req.negocio}. Objetivo: {req.objetivo}. "
            f"El algoritmo premia: {', '.join(señales[:4]) or 'retención, watch time, engagement'}. "
            f"Diseña un plan REAL de {dias} días para un taller mexicano. Prioriza REELS (dan watch time). "
            "Contenido variado: transformaciones antes/después, proceso de trabajo satisfactorio, tips, "
            "detrás de cámaras, testimonios, oferta. Español mexicano natural. "
            "Devuelve SOLO un JSON: array de objetos con claves: dia (num), formato (Reel/Foto/Carrusel), "
            "idea, gancho (primeros 3s), guion_corto, copy, hashtags (lista de 6), cta, mejor_horario. "
            f"Exactamente {dias} objetos."
        )
        key = os.getenv("GROQ_API_KEY")
        try:
            r = _rq.post("https://api.groq.com/openai/v1/chat/completions",
                         headers={"Authorization": f"Bearer {key}"},
                         json={"model": "llama-3.1-8b-instant",
                               "messages": [{"role": "user", "content": prompt}],
                               "temperature": 0.9, "max_tokens": 2200}, timeout=45)
            texto = r.json()["choices"][0]["message"]["content"]
            return {"status": "ok", "red": req.red, "dias": dias,
                    "algoritmo_usado": señales[:4], "plan": texto}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}
    return await asyncio.to_thread(_run)


# ── MONETIZACIÓN · plan de 1 año con videos REALES (constancia medible) ─
_MON = None
def _mon():
    global _MON
    if _MON is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("plan_monetizacion", _ROOT / "MARKETING" / "plan_monetizacion.py")
        _MON = _ilu.module_from_spec(spec); spec.loader.exec_module(_MON)
    return _MON


class GenPlanReq(BaseModel):
    dias: int = 365
    reiniciar: bool = False


class PubReq(BaseModel):
    id: int


class CopyReq(BaseModel):
    plataforma: str = "TikTok"
    tipo: str = "Antes/Después"


@app.get("/monetizacion/catalogo", tags=["Monetización"])
async def mon_catalogo():
    """Catálogo unificado de TODOS los videos reales (agrupado por carpeta, sin mover nada)."""
    return await asyncio.to_thread(_mon().catalogo)


@app.get("/monetizacion/hoy", tags=["Monetización"])
async def mon_hoy():
    """El post de HOY listo para aprobar y subir (video + plataforma + hora)."""
    return await asyncio.to_thread(_mon().post_de_hoy)


@app.get("/monetizacion/plan", tags=["Monetización"])
async def mon_plan(dias: int = 14):
    """Calendario de HOY en adelante + racha de constancia."""
    return await asyncio.to_thread(_mon().plan, dias)


@app.post("/monetizacion/generar", tags=["Monetización"])
async def mon_generar(req: GenPlanReq):
    """Genera/extiende el plan (por defecto 1 año)."""
    return await asyncio.to_thread(_mon().generar_plan, req.dias, req.reiniciar)


@app.post("/monetizacion/publicado", tags=["Monetización"])
async def mon_publicado(req: PubReq):
    """Marca el post como publicado (avanza la racha)."""
    return await asyncio.to_thread(_mon().marcar_publicado, req.id)


@app.post("/monetizacion/copy", tags=["Monetización"])
async def mon_copy(req: CopyReq):
    """Borrador REAL de gancho+caption (Groq) para el post; Anuar lo ajusta al video."""
    return await asyncio.to_thread(_mon().copy_borrador, req.plataforma, req.tipo)


class BloqueReq(BaseModel):
    bloque: int


@app.get("/monetizacion/bloque-pendiente", tags=["Monetización"])
async def mon_bloque_pendiente():
    """El próximo bloque SIN aprobar (para el aviso en pantalla)."""
    return await asyncio.to_thread(_mon().bloque_pendiente)


@app.get("/monetizacion/revisar-bloque", tags=["Monetización"])
async def mon_revisar_bloque(bloque: int):
    """Todos los posts de un bloque, para revisarlo."""
    return await asyncio.to_thread(_mon().revisar_bloque, bloque)


@app.post("/monetizacion/aprobar-post", tags=["Monetización"])
async def mon_aprobar_post(req: PubReq):
    """Aprueba UNA publicación del bloque."""
    return await asyncio.to_thread(_mon().aprobar_post, req.id)


@app.post("/monetizacion/aprobar-bloque", tags=["Monetización"])
async def mon_aprobar_bloque(req: BloqueReq):
    """Aprueba TODO el bloque de un golpe."""
    return await asyncio.to_thread(_mon().aprobar_bloque, req.bloque)


# ── CONSOLA DE MOTORES · activar/apagar/agrupar cartuchos + loadouts ───
_CONSOLA = None
def _consola():
    global _CONSOLA
    if _CONSOLA is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("consola_motores", _ROOT / "CORE" / "consola_motores.py")
        _CONSOLA = _ilu.module_from_spec(spec); spec.loader.exec_module(_CONSOLA)
    return _CONSOLA


class ToggleReq(BaseModel):
    id: str
    activo: bool


class LoadoutReq(BaseModel):
    nombre: str
    activos: list = []


@app.get("/consola/motores", tags=["Consola"])
async def consola_motores():
    """Lista los cartuchos con su estado (activo/apagado), agrupados + loadouts."""
    return await asyncio.to_thread(_consola().estado)


@app.post("/consola/toggle", tags=["Consola"])
async def consola_toggle(req: ToggleReq):
    """Prende/apaga un cartucho (los núcleo no se apagan)."""
    return await asyncio.to_thread(_consola().toggle, req.id, req.activo)


@app.get("/consola/loadouts", tags=["Consola"])
async def consola_loadouts():
    return await asyncio.to_thread(_consola().listar_loadouts)


@app.post("/consola/loadout/guardar", tags=["Consola"])
async def consola_loadout_guardar(req: LoadoutReq):
    """Guarda un perfil (loadout) con los cartuchos que deben quedar activos."""
    return await asyncio.to_thread(_consola().guardar_loadout, req.nombre, req.activos)


@app.post("/consola/loadout/aplicar", tags=["Consola"])
async def consola_loadout_aplicar(req: LoadoutReq):
    """Aplica un perfil: deja activos solo los del loadout (+ núcleo)."""
    return await asyncio.to_thread(_consola().aplicar_loadout, req.nombre)


@app.post("/consola/loadout/eliminar", tags=["Consola"])
async def consola_loadout_eliminar(req: LoadoutReq):
    return await asyncio.to_thread(_consola().eliminar_loadout, req.nombre)


# ── ORGANIZADOR DE ARCHIVOS · escanear PC + agrupar por tipo (seguro) ──
_ORG = None
def _org():
    global _ORG
    if _ORG is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("organizador_archivos", _ROOT / "SISTEMA" / "organizador_archivos.py")
        _ORG = _ilu.module_from_spec(spec); spec.loader.exec_module(_ORG)
    return _ORG


class AgruparReq(BaseModel):
    carpeta: str
    mover: bool = False


@app.get("/archivos/seguras", tags=["Sistema"])
async def archivos_seguras():
    """Carpetas donde SÍ se permite agrupar y las zonas blindadas (nunca se tocan)."""
    return await asyncio.to_thread(_org().carpetas_seguras)


@app.get("/archivos/escanear", tags=["Sistema"])
async def archivos_escanear(raiz: str = ""):
    """SOLO LECTURA: cataloga archivos por tipo (zip/rar/dxf/…). No mueve nada."""
    return await asyncio.to_thread(_org().escanear, raiz, None, 5)


@app.post("/archivos/agrupar", tags=["Sistema"])
async def archivos_agrupar(req: AgruparReq):
    """Agrupa archivos sueltos por tipo en una carpeta segura. mover=false = simulacro."""
    return await asyncio.to_thread(_org().agrupar, req.carpeta, req.mover)


# ── APRENDIZAJE · descargar manuales oficiales → Biblioteca ────────────
_APR = None
def _apr():
    global _APR
    if _APR is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("aprendizaje", _ROOT / "MANUALES" / "aprendizaje.py")
        _APR = _ilu.module_from_spec(spec); spec.loader.exec_module(_APR)
    return _APR


class AprenderReq(BaseModel):
    herramienta: str


class ManualUrlReq(BaseModel):
    herramienta: str
    url: str


@app.get("/manuales/catalogo", tags=["Biblioteca"])
async def manuales_catalogo():
    """Herramientas cuyo manual AURORA puede aprender."""
    return await asyncio.to_thread(_apr().catalogo)


@app.post("/manuales/aprender", tags=["Biblioteca"])
async def manuales_aprender(req: AprenderReq):
    """Busca el manual oficial, lo descarga (si es PDF) y lo ingiere a la Biblioteca."""
    return await asyncio.to_thread(_apr().aprender, req.herramienta)


@app.post("/manuales/ingerir-url", tags=["Biblioteca"])
async def manuales_ingerir_url(req: ManualUrlReq):
    """Ruta manual: Anuar pega la URL del PDF y AURORA lo descarga + ingiere."""
    return await asyncio.to_thread(_apr().ingerir_url, req.herramienta, req.url)


# ── EDITOR · PROCESAR ARCHIVO SUBIDO (el "hardware" usable) ───────────
@app.post("/editor/procesar", tags=["Editor"])
async def editor_procesar(
    accion: str = Form(...),
    file: UploadFile = File(...),
    material: str = Form(""),
    velocidad: float = Form(15.0),
    margen: float = Form(30.0),
    merma: float = Form(0.0),
    pagina: int = Form(0),
    umbral: int = Form(128),
    formato_destino: str = Form("png"),   # convertir: svg/png/pdf/dxf/eps/ps
    dpi: int = Form(300),                 # escalar/planilla/convertir(png)
    ancho_cm: float = Form(0),            # escalar: medida / planilla: tamaño del ítem
    alto_cm: float = Form(0),
    proporcion: bool = Form(True),        # escalar: mantener proporción (False = estirar)
    paper: str = Form("A4"),              # planilla: formato de hoja
    margen_cm: float = Form(1.0),         # planilla: margen de hoja
    gap_cm: float = Form(0.5),            # planilla: separación entre copias
    factor: float = Form(2.0),            # realzar: multiplicador de tamaño (2x)
    realzar: bool = Form(True),           # reescalar: aplicar realce de nitidez
):
    """Recibe un archivo SUBIDO (no ruta) + acción, lo procesa y devuelve link de descarga."""
    import uuid, time
    in_dir = _ROOT / "UPLOADS" / "editor_in"
    out_dir = _ROOT / "UPLOADS" / "editor_out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "archivo").suffix.lower() or ".bin"
    stem = f"ed_{time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    in_path = in_dir / f"{stem}{ext}"
    in_path.write_bytes(await file.read())

    def _run():
        conv = _conv()
        try:
            if accion == "aligerar":
                out = out_dir / f"{stem}_ligero.dxf"
                r = conv.aligerar_dxf(str(in_path), str(out))
            elif accion == "papercraft":
                out = out_dir / f"{stem}_pag{pagina+1}.dxf"
                r = conv.papercraft_a_dxf(str(in_path), pagina, str(out))
            elif accion == "bw":
                out = out_dir / f"{stem}_bn.png"
                r = conv.a_bw_puro(str(in_path), str(out), 300, umbral, pagina)
            elif accion == "linea":
                out = out_dir / f"{stem}_linea.png"
                r = conv.a_linea(str(in_path), str(out))
            elif accion == "fondo":
                out = out_dir / f"{stem}_sinfondo.png"
                r = conv.quitar_fondo(str(in_path), str(out))
            elif accion == "lineal":
                out = out_dir / f"{stem}_lineal.png"
                r = conv.foto_a_lineal(str(in_path), str(out))
            elif accion == "convertir":
                a = (formato_destino or "png").lower().lstrip(".")
                out = out_dir / f"{stem}.{a}"
                r = _convf().convertir(str(in_path), a, str(out), dpi)
            elif accion == "escalar":
                out = out_dir / f"{stem}_escala.png"
                r = _esc().escalar_a_medida(str(in_path), ancho_cm, alto_cm, dpi, "rapido", proporcion, str(out))
            elif accion == "planilla":
                out = out_dir / f"{stem}_planilla.png"
                r = _esc().generar_planilla(str(in_path), ancho_cm, alto_cm, paper, dpi,
                                            margen_cm, gap_cm, "vertical", (), "white", str(out))
            elif accion == "cotizar":
                return _cot().cotizar_corte(str(in_path), material, velocidad, margen, True, merma)
            elif accion == "analizar":
                return _reed().analizar_pdf(str(in_path), pagina)
            elif accion == "extraer":
                sub = out_dir / f"{stem}_partes"
                r = _reed().extraer_elementos(str(in_path), pagina, dpi or 300, str(sub))
                if r.get("status") == "ok":
                    base = f"/editor-out/{sub.name}"
                    r["archivos"] = ([{"nombre": r["fondo"], "url": f"{base}/{r['fondo']}"}]
                                     + [{"nombre": im["archivo"], "url": f"{base}/{im['archivo']}"}
                                        for im in r.get("imagenes", [])]
                                     + [{"nombre": "textos.json", "url": f"{base}/textos.json"}])
                return r
            elif accion == "realzar":
                out = out_dir / f"{stem}_realzada.png"
                r = _reed().realzar_foto(str(in_path), factor, True, 1.05, 1.05, str(out))
            elif accion == "reescalar":
                a = (formato_destino or "png").lower().lstrip(".")
                if a not in ("png", "jpg", "jpeg", "pdf"):
                    a = "png"
                out = out_dir / f"{stem}_reescala.{a}"
                ajuste = "estirar" if not proporcion else "proporcion"
                r = _reed().reescalar_a_medida(str(in_path), ancho_cm, alto_cm, dpi or 150,
                                               pagina, realzar, a, ajuste, str(out))
            else:
                return {"status": "error", "mensaje": f"Acción desconocida: {accion}"}
            if r.get("status") == "ok":
                r["salida_url"] = f"/editor-out/{out.name}"
                r["salida_nombre"] = out.name
            return r
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    return await asyncio.to_thread(_run)


# ── WHATSAPP · conexión y QR (vincular número, escanear en vivo) ──────
def _green_creds():
    inst = os.getenv("GREEN_API_INSTANCE"); tok = os.getenv("GREEN_API_TOKEN")
    srv = os.getenv("GREEN_API_SERVER", "")
    host = f"https://{srv}.api.greenapi.com" if srv else "https://api.green-api.com"
    return host, inst, tok


@app.get("/whatsapp/estado", tags=["WhatsApp"])
async def whatsapp_estado():
    """Estado real de la instancia + número conectado + si ya es el de negocio."""
    host, inst, tok = _green_creds()
    if not (inst and tok):
        return {"status": "FALTA_TOKEN"}
    objetivo = os.getenv("WA_NUMERO_NEGOCIO", "3332386943")
    def _run():
        import requests
        try:
            st = requests.get(f"{host}/waInstance{inst}/getStateInstance/{tok}", timeout=12).json()
            estado = st.get("stateInstance", "")
            phone = ""
            if estado == "authorized":
                try:
                    wa = requests.get(f"{host}/waInstance{inst}/getWaSettings/{tok}", timeout=12).json()
                    phone = str(wa.get("phone") or "")
                except Exception:
                    phone = ""
            obj10 = "".join(ch for ch in objetivo if ch.isdigit())[-10:]
            es_negocio = bool(phone) and phone.endswith(obj10)
            return {"status": "ok", "estado": estado, "telefono": phone,
                    "objetivo": objetivo, "es_negocio": es_negocio}
        except Exception as e:
            return {"status": "error", "detalle": str(e)[:200]}
    return await asyncio.to_thread(_run)


@app.get("/whatsapp/qr", tags=["WhatsApp"])
async def whatsapp_qr():
    """QR en vivo de Green API para vincular. type 'alreadyLogged' = ya conectado (logout antes)."""
    host, inst, tok = _green_creds()
    if not (inst and tok):
        return {"status": "FALTA_TOKEN"}
    def _run():
        import requests
        try:
            r = requests.get(f"{host}/waInstance{inst}/qr/{tok}", timeout=15).json()
            return {"status": "ok", "type": r.get("type"), "message": r.get("message", "")}
        except Exception as e:
            return {"status": "error", "detalle": str(e)[:200]}
    return await asyncio.to_thread(_run)


@app.post("/whatsapp/reconectar", tags=["WhatsApp"])
async def whatsapp_reconectar():
    """Cierra sesión (logout) para poder vincular OTRO número por QR. Acción deliberada del dueño."""
    host, inst, tok = _green_creds()
    if not (inst and tok):
        return {"status": "FALTA_TOKEN"}
    def _run():
        import requests
        try:
            r = requests.get(f"{host}/waInstance{inst}/logout/{tok}", timeout=15)
            try:
                data = r.json()
            except Exception:
                data = {"raw": r.text[:100]}
            return {"status": "ok", "logout": data}
        except Exception as e:
            return {"status": "error", "detalle": str(e)[:200]}
    return await asyncio.to_thread(_run)


# ── PLANTILLAS DE TAZA (catálogo de fondos temáticos + generar) ───────
_TAZA = None
def _taza():
    global _TAZA
    if _TAZA is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("plantillas_taza", _ROOT / "EDITOR" / "plantillas_taza.py")
        _TAZA = _ilu.module_from_spec(spec); spec.loader.exec_module(_TAZA)
    return _TAZA


@app.get("/taza/temas", tags=["Taza"])
async def taza_temas():
    """Temas y fondos disponibles (para la galería)."""
    return _taza().temas()


@app.get("/taza/buscar", tags=["Taza"])
async def taza_buscar(q: str = ""):
    """Búsqueda de fondos por ocasión/tema. Vacío = todos."""
    return _taza().buscar_fondos(q)


@app.get("/taza/preview/{fondo_id}", tags=["Taza"])
async def taza_preview(fondo_id: str):
    """Miniatura PNG de un fondo (para mostrar en la galería)."""
    from fastapi.responses import Response
    m = _taza()
    if fondo_id not in m.FONDOS:
        raise HTTPException(status_code=404, detail="fondo no existe")
    def _png():
        import io
        img = m.FONDOS[fondo_id]["render"](300, 128).convert("RGB")
        buf = io.BytesIO(); img.save(buf, "PNG"); return buf.getvalue()
    data = await asyncio.to_thread(_png)
    return Response(content=data, media_type="image/png")


@app.post("/taza/generar", tags=["Taza"])
async def taza_generar(fondo_id: str = Form(...), frase: str = Form(""),
                       modo: str = Form("frase_foto")):
    """Compone la plantilla final y devuelve link de descarga."""
    import time
    out = _ROOT / "UPLOADS" / "editor_out"
    out.mkdir(parents=True, exist_ok=True)
    salida = out / f"taza_{fondo_id}_{modo}_{time.strftime('%H%M%S')}.png"
    def _run():
        return _taza().componer_taza(fondo_id, frase=frase, modo=modo, salida=str(salida))
    r = await asyncio.to_thread(_run)
    if r.get("status") == "ok":
        r["salida_url"] = f"/editor-out/{salida.name}"
    return r


class HojaA4Req(BaseModel):
    items: list = []


@app.post("/taza/hoja-a4", tags=["Taza"])
async def taza_hoja_a4(req: HojaA4Req):
    """Hoja A4 con hasta 3 tazas (21x9 cm) lista para imprimir."""
    import time
    out = _ROOT / "UPLOADS" / "editor_out"
    out.mkdir(parents=True, exist_ok=True)
    salida = out / f"hoja_A4_{time.strftime('%H%M%S')}.png"
    def _run():
        return _taza().generar_hoja_a4(items=req.items or None, salida=str(salida))
    r = await asyncio.to_thread(_run)
    if r.get("status") == "ok":
        r["salida_url"] = f"/editor-out/{salida.name}"
    return r


# ── BIBLIOTECA · subir PDF e ingerir (drag-drop real) ────────────────
@app.post("/biblioteca/subir", tags=["Biblioteca"])
async def biblioteca_subir(file: UploadFile = File(...), nombre: str = Form("")):
    """Recibe un PDF SUBIDO, lo guarda e ingiere en la biblioteca (FTS5)."""
    import time
    dest_dir = _ROOT / "UPLOADS" / "biblioteca"
    dest_dir.mkdir(parents=True, exist_ok=True)
    fname = Path(file.filename or "doc.pdf").name
    dest = dest_dir / f"{time.strftime('%Y%m%d%H%M%S')}_{fname}"
    dest.write_bytes(await file.read())
    return await asyncio.to_thread(_bib().ingerir_pdf, str(dest), nombre or fname)


# ── RED · diagnóstico IoT/Cast (cartucho: escanea y diagnostica desconexiones) ──
_RED = None
def _red():
    global _RED
    if _RED is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("red_diagnostico", _ROOT / "REDES" / "red_diagnostico.py")
        _RED = _ilu.module_from_spec(spec); spec.loader.exec_module(_RED)
    return _RED

@app.get("/red/cast", tags=["Red"])
async def red_cast():
    """Escanea la LAN y lista dispositivos Google Cast/Nest/Home (nombre, IP, señal)."""
    return await asyncio.to_thread(_red().escanear_cast)

@app.get("/red/diagnostico", tags=["Red"])
async def red_diagnostico(ip: str):
    """Diagnóstico real de un dispositivo (RSSI, pérdida, causas y acciones)."""
    return await asyncio.to_thread(_red().diagnosticar, ip)

@app.get("/red/ping", tags=["Red"])
async def red_ping(ip: str, n: int = 12):
    """Pérdida de paquetes y latencia hacia un dispositivo."""
    return await asyncio.to_thread(_red().ping_perdida, ip, n)


# ── WEB REAL · navegación/búsqueda en vivo (cartucho) ────────────────
_WEB = None
def _web():
    global _WEB
    if _WEB is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("web_real", _ROOT / "WEB" / "web_real.py")
        _WEB = _ilu.module_from_spec(spec); spec.loader.exec_module(_WEB)
    return _WEB

@app.get("/web/buscar", tags=["Web"])
async def web_buscar(q: str, n: int = 6):
    """Busca en internet en vivo (real, no de memoria)."""
    return await asyncio.to_thread(_web().buscar, q, n)

@app.get("/web/noticias", tags=["Web"])
async def web_noticias(q: str, n: int = 6):
    return await asyncio.to_thread(_web().noticias, q, n)

@app.get("/web/leer", tags=["Web"])
async def web_leer(url: str):
    """Abre una URL y extrae su texto real."""
    return await asyncio.to_thread(_web().leer_pagina, url)


# ── AUTH · identidad de dueño (PIN + llaves) ─────────────────────────
_IDENT = None
def _ident():
    global _IDENT
    if _IDENT is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("identidad_core", _ROOT / "AUTH" / "identidad_core.py")
        _IDENT = _ilu.module_from_spec(spec); spec.loader.exec_module(_IDENT)
    return _IDENT

def _es_dueno(token: str) -> bool:
    try:
        return _ident().rol(token or "") == "dueño"
    except Exception:
        return False

class PinReq(BaseModel):
    pin: str
    pin_actual: str = ""

@app.get("/auth/estado", tags=["Auth"])
async def auth_estado():
    return await asyncio.to_thread(_ident().estado)

@app.post("/auth/configurar-pin", tags=["Auth"])
async def auth_config(req: PinReq):
    return await asyncio.to_thread(_ident().configurar_pin, req.pin, req.pin_actual)

@app.post("/auth/login", tags=["Auth"])
async def auth_login(req: PinReq):
    return await asyncio.to_thread(_ident().login, req.pin)

@app.post("/auth/revocar", tags=["Auth"])
async def auth_revocar():
    return await asyncio.to_thread(_ident().revocar_todos)


# ── MULTI-USUARIO · Anuar + Rocío (login por PIN + rol = cartuchos) ────
_USU = None
def _usu():
    global _USU
    if _USU is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("usuarios", _ROOT / "AUTH" / "usuarios.py")
        _USU = _ilu.module_from_spec(spec); spec.loader.exec_module(_USU)
    return _USU


class LoginUsuReq(BaseModel):
    id: str
    pin: str = ""


class PinUsuReq(BaseModel):
    id: str
    pin: str
    pin_actual: str = ""


class CrearUsuReq(BaseModel):
    nombre: str
    rol: str = "colaborador"


@app.get("/usuarios/lista", tags=["Usuarios"])
async def usuarios_lista():
    """Usuarios para la pantalla de login (sin secretos)."""
    return await asyncio.to_thread(_usu().listar_usuarios)


@app.post("/usuarios/login", tags=["Usuarios"])
async def usuarios_login(req: LoginUsuReq):
    """Verifica PIN y devuelve rol + cartuchos permitidos."""
    return await asyncio.to_thread(_usu().login, req.id, req.pin)


@app.post("/usuarios/configurar-pin", tags=["Usuarios"])
async def usuarios_pin(req: PinUsuReq):
    """Crea o cambia el PIN de un usuario."""
    return await asyncio.to_thread(_usu().configurar_pin, req.id, req.pin, req.pin_actual)


@app.post("/usuarios/crear", tags=["Usuarios"])
async def usuarios_crear(req: CrearUsuReq):
    return await asyncio.to_thread(_usu().crear_usuario, req.nombre, req.rol)


@app.post("/usuarios/eliminar", tags=["Usuarios"])
async def usuarios_eliminar(req: LoginUsuReq):
    return await asyncio.to_thread(_usu().eliminar_usuario, req.id)


# ── ANALIZADOR DE MERCADO multi-nicho (web real + IA) ─────────────────
_MERC = None
def _merc():
    global _MERC
    if _MERC is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("analizador_mercado", _ROOT / "MARKETING" / "analizador_mercado.py")
        _MERC = _ilu.module_from_spec(spec); spec.loader.exec_module(_MERC)
    return _MERC


@app.get("/mercado/nichos", tags=["Mercado"])
async def mercado_nichos():
    """Nichos que AURORA puede analizar (retrofit/láser/sublimación/DTF)."""
    return await asyncio.to_thread(_merc().nichos)


@app.get("/mercado/analizar", tags=["Mercado"])
async def mercado_analizar(nicho: str):
    """Analiza un nicho: tendencias, competencia, precios reales (web) + resumen IA."""
    return await asyncio.to_thread(_merc().analizar, nicho)


@app.get("/mercado/precios", tags=["Mercado"])
async def mercado_precios(producto: str):
    """Compara precios reales de un producto en la web (con fuentes)."""
    return await asyncio.to_thread(_merc().comparar_precios, producto)


# ── ADMIN REDES SOCIALES (agenda multi-cuenta) ────────────────────────
_SOC = None
def _soc():
    global _SOC
    if _SOC is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("social_manager", _ROOT / "PUBLICADOR" / "social_manager.py")
        _SOC = _ilu.module_from_spec(spec); spec.loader.exec_module(_SOC)
    return _SOC


class AgendarSocReq(BaseModel):
    red: str
    fecha: str
    hora: str
    texto: str = ""
    media_url: str = ""


class SocIdReq(BaseModel):
    id: int


@app.get("/social/estado", tags=["Social"])
async def social_estado():
    """Estado real de conexión de cada red (FB/IG/TikTok/YT/WhatsApp)."""
    return await asyncio.to_thread(_soc().estado_conexiones)


@app.get("/social/calendario", tags=["Social"])
async def social_calendario(dias: int = 14):
    """Publicaciones agendadas de hoy en adelante."""
    return await asyncio.to_thread(_soc().calendario, dias)


@app.get("/social/resumen", tags=["Social"])
async def social_resumen():
    return await asyncio.to_thread(_soc().resumen)


@app.post("/social/agendar", tags=["Social"])
async def social_agendar(req: AgendarSocReq):
    """Agenda una publicación (Anuar aprueba y publica; no auto-postea)."""
    return await asyncio.to_thread(_soc().agendar, req.red, req.fecha, req.hora, req.texto, req.media_url)


@app.post("/social/publicado", tags=["Social"])
async def social_publicado(req: SocIdReq):
    return await asyncio.to_thread(_soc().marcar_publicado, req.id)


@app.post("/social/eliminar", tags=["Social"])
async def social_eliminar(req: SocIdReq):
    return await asyncio.to_thread(_soc().eliminar, req.id)


# ── PANELES DEL CEREBRO (autoconocimiento/sueño/reparación/voz) ───────
_CBR = None
def _cbr():
    global _CBR
    if _CBR is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("paneles_cerebro", _ROOT / "CEREBRO" / "paneles_cerebro.py")
        _CBR = _ilu.module_from_spec(spec); spec.loader.exec_module(_CBR)
    return _CBR


@app.get("/cerebro/resumen", tags=["Cerebro"])
async def cerebro_resumen():
    """Estado real de los motores del cerebro (autoconocimiento, sueño, reparación, voz)."""
    return await asyncio.to_thread(_cbr().resumen)


@app.get("/cerebro/autoconocimiento", tags=["Cerebro"])
async def cerebro_autoconocimiento():
    return await asyncio.to_thread(_cbr().autoconocimiento)


@app.get("/cerebro/sueno", tags=["Cerebro"])
async def cerebro_sueno():
    return await asyncio.to_thread(_cbr().sueno_reparacion)


@app.get("/cerebro/voz", tags=["Cerebro"])
async def cerebro_voz():
    return await asyncio.to_thread(_cbr().voz)


# ── INVENTARIO del taller (existencias, movimientos, alertas) ─────────
_INV = None
def _inv():
    global _INV
    if _INV is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("inventario", _ROOT / "TALLER" / "inventario.py")
        _INV = _ilu.module_from_spec(spec); spec.loader.exec_module(_INV)
    return _INV


class InvItemReq(BaseModel):
    nombre: str
    categoria: str = ""
    unidad: str = "pz"
    cantidad: float = 0
    minimo: float = 0
    costo_unitario: float = 0
    talla: str = ""
    color: str = ""


class InvBorrarReq(BaseModel):
    item_id: int


class InvMovReq(BaseModel):
    item_id: int
    delta: float
    motivo: str = ""


@app.get("/inventario/listar", tags=["Inventario"])
async def inventario_listar(categoria: str = ""):
    return await asyncio.to_thread(_inv().listar, categoria)


@app.get("/inventario/resumen", tags=["Inventario"])
async def inventario_resumen():
    return await asyncio.to_thread(_inv().resumen)


@app.get("/inventario/bajo-minimo", tags=["Inventario"])
async def inventario_bajo():
    return await asyncio.to_thread(_inv().bajo_minimo)


@app.get("/inventario/historial", tags=["Inventario"])
async def inventario_historial(item_id: int):
    return await asyncio.to_thread(_inv().historial, item_id)


@app.post("/inventario/agregar", tags=["Inventario"])
async def inventario_agregar(req: InvItemReq):
    return await asyncio.to_thread(_inv().agregar_item, req.nombre, req.categoria,
                                   req.unidad, req.cantidad, req.minimo, req.costo_unitario,
                                   req.talla, req.color)


class InvEditReq(BaseModel):
    item_id: int
    nombre: str | None = None
    categoria: str | None = None
    talla: str | None = None
    color: str | None = None
    unidad: str | None = None
    minimo: float | None = None
    costo_unitario: float | None = None


@app.post("/inventario/editar", tags=["Inventario"])
async def inventario_editar(req: InvEditReq):
    """Edita datos de un artículo (color, talla, unidad, mínimo, costo). La cantidad va por movimientos."""
    return await asyncio.to_thread(_inv().editar_item, req.item_id, req.nombre, req.categoria,
                                   req.talla, req.color, req.unidad, req.minimo, req.costo_unitario)


@app.post("/inventario/borrar", tags=["Inventario"])
async def inventario_borrar(req: InvBorrarReq):
    """Borra UN artículo del inventario (y su historial)."""
    return await asyncio.to_thread(_inv().borrar_item, req.item_id)


@app.post("/inventario/limpiar", tags=["Inventario"])
async def inventario_limpiar():
    """Vacía TODO el inventario. Acción deliberada del dueño."""
    return await asyncio.to_thread(_inv().limpiar_todo)


@app.post("/inventario/sembrar", tags=["Inventario"])
async def inventario_sembrar():
    """Precarga el catálogo real de Milens + ATF con cantidad 0 (solo falta capturar)."""
    return await asyncio.to_thread(_inv().sembrar_catalogo)


@app.post("/inventario/movimiento", tags=["Inventario"])
async def inventario_movimiento(req: InvMovReq):
    return await asyncio.to_thread(_inv().movimiento, req.item_id, req.delta, req.motivo)


# ── AGENDA / CITAS (instalaciones, entregas, citas) ───────────────────
_AGD = None
def _agd():
    global _AGD
    if _AGD is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("agenda", _ROOT / "AGENDA" / "agenda.py")
        _AGD = _ilu.module_from_spec(spec); spec.loader.exec_module(_AGD)
    return _AGD


class CitaReq(BaseModel):
    titulo: str
    cliente: str = ""
    telefono: str = ""
    fecha: str
    hora: str
    tipo: str = "cita"
    notas: str = ""
    duracion_min: int = 60


class CitaEstadoReq(BaseModel):
    id: int
    estado: str = ""


@app.get("/agenda/listar", tags=["Agenda"])
async def agenda_listar(desde: str = "", hasta: str = ""):
    return await asyncio.to_thread(_agd().listar, desde, hasta)


@app.get("/agenda/dia", tags=["Agenda"])
async def agenda_dia(fecha: str):
    return await asyncio.to_thread(_agd().dia, fecha)


@app.get("/agenda/proximas", tags=["Agenda"])
async def agenda_proximas(horas: int = 24):
    return await asyncio.to_thread(_agd().proximas, horas)


@app.get("/agenda/resumen", tags=["Agenda"])
async def agenda_resumen():
    return await asyncio.to_thread(_agd().resumen)


@app.post("/agenda/crear", tags=["Agenda"])
async def agenda_crear(req: CitaReq):
    return await asyncio.to_thread(_agd().crear_cita, req.titulo, req.cliente, req.telefono,
                                   req.fecha, req.hora, req.tipo, req.notas, req.duracion_min)


@app.post("/agenda/estado", tags=["Agenda"])
async def agenda_estado(req: CitaEstadoReq):
    return await asyncio.to_thread(_agd().actualizar_estado, req.id, req.estado)


@app.post("/agenda/eliminar", tags=["Agenda"])
async def agenda_eliminar(req: CitaEstadoReq):
    return await asyncio.to_thread(_agd().eliminar, req.id)


# ── SEGUIMIENTO Leads → Ventas (embudo + WhatsApp) ────────────────────
_SEG = None
def _seg():
    global _SEG
    if _SEG is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("seguimiento_ventas", _ROOT / "VENDEDOR" / "seguimiento_ventas.py")
        _SEG = _ilu.module_from_spec(spec); spec.loader.exec_module(_SEG)
    return _SEG


class SegEnviarReq(BaseModel):
    lead_id: int
    mensaje: str


class SegAvanzarReq(BaseModel):
    lead_id: int
    etapa: str


@app.get("/seguimiento/etapas", tags=["Seguimiento"])
async def seg_etapas():
    return await asyncio.to_thread(_seg().etapas)


@app.post("/seguimiento/sincronizar", tags=["Seguimiento"])
async def seg_sinc():
    return await asyncio.to_thread(_seg().sincronizar_leads)


@app.get("/seguimiento/pendientes", tags=["Seguimiento"])
async def seg_pend():
    return await asyncio.to_thread(_seg().pendientes)


@app.get("/seguimiento/mensaje", tags=["Seguimiento"])
async def seg_msg(lead_id: int):
    return await asyncio.to_thread(_seg().mensaje_sugerido, lead_id)


@app.get("/seguimiento/resumen", tags=["Seguimiento"])
async def seg_resumen():
    return await asyncio.to_thread(_seg().resumen)


@app.post("/seguimiento/enviar", tags=["Seguimiento"])
async def seg_enviar(req: SegEnviarReq):
    """Envía WhatsApp de seguimiento (acción real; Anuar confirma)."""
    return await asyncio.to_thread(_seg().enviar_seguimiento, req.lead_id, req.mensaje)


@app.post("/seguimiento/avanzar", tags=["Seguimiento"])
async def seg_avanzar(req: SegAvanzarReq):
    return await asyncio.to_thread(_seg().avanzar_etapa, req.lead_id, req.etapa)


# ── REPORTES / BI del taller (sobre taller.db real) ───────────────────
_RBI = None
def _rbi():
    global _RBI
    if _RBI is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("reportes_bi", _ROOT / "TALLER" / "reportes_bi.py")
        _RBI = _ilu.module_from_spec(spec); spec.loader.exec_module(_RBI)
    return _RBI


@app.get("/reportes/completo", tags=["Reportes"])
async def reportes_completo():
    """Todo el panel BI en una llamada (KPIs, meses, productos, solicitantes, estados, oportunidades)."""
    return await asyncio.to_thread(_rbi().reporte_completo)


# ── PC · control real del equipo (BLINDADO: exige PIN de dueño) ──────
_PCA = None
def _pca():
    global _PCA
    if _PCA is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("pc_access", _ROOT / "CEREBRO" / "pc_access.py")
        _PCA = _ilu.module_from_spec(spec); spec.loader.exec_module(_PCA)
    return _PCA

class PcReq(BaseModel):
    token: str
    arg: str = ""
    contenido: str = ""

def _guard(token: str):
    if not _es_dueno(token):
        raise HTTPException(status_code=403, detail="Requiere PIN de dueño (inicia sesión en el panel PC).")

@app.post("/pc/estado", tags=["PC"])
async def pc_estado(req: PcReq):
    _guard(req.token)
    return await _pca().pc_access.estado_sistema()

@app.post("/pc/listar", tags=["PC"])
async def pc_listar(req: PcReq):
    _guard(req.token)
    return await _pca().pc_access.listar_directorio(req.arg or str(_ROOT))

@app.post("/pc/ejecutar", tags=["PC"])
async def pc_ejecutar(req: PcReq):
    _guard(req.token)
    return await _pca().pc_access.ejecutar(req.arg)

@app.post("/pc/abrir", tags=["PC"])
async def pc_abrir(req: PcReq):
    _guard(req.token)
    return await _pca().pc_access.abrir_archivo(req.arg)

@app.post("/pc/apps", tags=["PC"])
async def pc_apps(req: PcReq):
    _guard(req.token)
    return await _pca().pc_access.apps_instaladas()

@app.post("/pc/portapapeles", tags=["PC"])
async def pc_portapapeles(req: PcReq):
    _guard(req.token)
    return {"status": "OK", "portapapeles": await _pca().pc_access.leer_portapapeles()}


# ── TALLER · ADMINISTRACIÓN (precios/materiales editables) ───────────
_ADM = None
def _adm():
    global _ADM
    if _ADM is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("administracion", _ROOT / "TALLER" / "administracion.py")
        _ADM = _ilu.module_from_spec(spec); spec.loader.exec_module(_ADM)
    return _ADM

@app.get("/taller/precios", tags=["Taller"])
async def taller_precios():
    return await asyncio.to_thread(_adm().listar_precios)

class MaterialReq(BaseModel):
    nombre: str
    precio_hoja: float
    ancho: float = 122.0
    alto: float = 244.0

@app.post("/taller/material", tags=["Taller"])
async def taller_material(req: MaterialReq):
    return await asyncio.to_thread(_adm().guardar_material, req.nombre, req.precio_hoja, req.ancho, req.alto)

class NombreReq(BaseModel):
    nombre: str

@app.post("/taller/material-borrar", tags=["Taller"])
async def taller_material_borrar(req: NombreReq):
    return await asyncio.to_thread(_adm().borrar_material, req.nombre)

class CostoMinReq(BaseModel):
    valor: float

@app.post("/taller/costo-minuto", tags=["Taller"])
async def taller_costo_minuto(req: CostoMinReq):
    return await asyncio.to_thread(_adm().set_costo_minuto, req.valor)


# ── TALLER · COTIZADOR POR REGLAS (Prendas & Servicios) ──────────────
_CSER = None
def _cser():
    global _CSER
    if _CSER is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("cotizador_servicios", _ROOT / "TALLER" / "cotizador_servicios.py")
        _CSER = _ilu.module_from_spec(spec); spec.loader.exec_module(_CSER)
    return _CSER

@app.get("/taller/servicios", tags=["Taller"])
async def taller_servicios():
    return await asyncio.to_thread(_cser().catalogo_plano)

class CarritoReq(BaseModel):
    carrito: list = []
    pago_tarjeta: bool = False

@app.post("/taller/cotizar-servicios", tags=["Taller"])
async def taller_cotizar_servicios(req: CarritoReq):
    return await asyncio.to_thread(_cser().cotizar, req.carrito, req.pago_tarjeta)

class ServicioReq(BaseModel):
    nombre: str
    precio: float
    unidad: str = "pieza"
    costo: float | None = None

@app.post("/taller/servicio", tags=["Taller"])
async def taller_guardar_servicio(req: ServicioReq):
    """Agrega o actualiza un trabajo/servicio en el catálogo del cotizador."""
    return await asyncio.to_thread(_cser().guardar_servicio, req.nombre, req.precio, req.unidad, req.costo)

class ServicioBorrarReq(BaseModel):
    nombre: str

@app.post("/taller/servicio/borrar", tags=["Taller"])
async def taller_borrar_servicio(req: ServicioBorrarReq):
    return await asyncio.to_thread(_cser().borrar_servicio, req.nombre)

@app.get("/taller/contabilidad", tags=["Taller"])
async def taller_contabilidad(mes: str = None):
    """Balance mensual real: ingresos, costos, utilidad, cobrado y por cobrar."""
    return await asyncio.to_thread(_ordenes().contabilidad_mensual, mes)

@app.post("/taller/album", tags=["Taller"])
async def taller_album():
    """Genera el álbum de catálogo (imágenes de productos + 'TU LOGO AQUÍ')."""
    return await asyncio.to_thread(_alb().generar_album)


# ── IDE DEL SISTEMA (editor de código — exige PIN de dueño) ──────────
_IDE = None
def _ide():
    global _IDE
    if _IDE is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ide_core", _ROOT / "CODIGO" / "ide_core.py")
        _IDE = _ilu.module_from_spec(spec); spec.loader.exec_module(_IDE)
    return _IDE

class IdeArbolReq(BaseModel):
    token: str
    ruta: str | None = None

class IdeLeerReq(BaseModel):
    token: str
    ruta: str

class IdeGuardarReq(BaseModel):
    token: str
    ruta: str
    contenido: str

class IdeRestaurarReq(BaseModel):
    token: str
    respaldo: str
    destino: str

@app.post("/ide/arbol", tags=["IDE"])
async def ide_arbol(req: IdeArbolReq):
    _guard(req.token)
    return await asyncio.to_thread(_ide().arbol, req.ruta)

@app.post("/ide/leer", tags=["IDE"])
async def ide_leer(req: IdeLeerReq):
    _guard(req.token)
    return await asyncio.to_thread(_ide().leer, req.ruta)

@app.post("/ide/guardar", tags=["IDE"])
async def ide_guardar(req: IdeGuardarReq):
    _guard(req.token)
    return await asyncio.to_thread(_ide().guardar, req.ruta, req.contenido)

@app.post("/ide/respaldos", tags=["IDE"])
async def ide_respaldos(req: IdeLeerReq):
    _guard(req.token)
    return await asyncio.to_thread(_ide().respaldos, req.ruta)

@app.post("/ide/restaurar", tags=["IDE"])
async def ide_restaurar(req: IdeRestaurarReq):
    _guard(req.token)
    return await asyncio.to_thread(_ide().restaurar, req.respaldo, req.destino)


# ── ACCIONES REALES DEL SISTEMA (mover/copiar/reparar — exige PIN) ────
_ACC = None
def _acc():
    global _ACC
    if _ACC is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("acciones_sistema", _ROOT / "CEREBRO" / "acciones_sistema.py")
        _ACC = _ilu.module_from_spec(spec); spec.loader.exec_module(_ACC)
    return _ACC

class AccMoverReq(BaseModel):
    token: str
    origen: str
    destino: str

class AccBuscarReq(BaseModel):
    token: str
    nombre: str

class AccTokenReq(BaseModel):
    token: str

@app.post("/accion/buscar", tags=["Acciones"])
async def accion_buscar(req: AccBuscarReq):
    _guard(req.token)
    return {"status": "ok", "resultados": await asyncio.to_thread(_acc().buscar_archivo, req.nombre)}

@app.post("/accion/copiar", tags=["Acciones"])
async def accion_copiar(req: AccMoverReq):
    _guard(req.token)
    return await asyncio.to_thread(_acc().copiar, req.origen, req.destino)

@app.post("/accion/mover", tags=["Acciones"])
async def accion_mover(req: AccMoverReq):
    _guard(req.token)
    return await asyncio.to_thread(_acc().mover, req.origen, req.destino)

@app.post("/accion/reparar-whatsapp", tags=["Acciones"])
async def accion_reparar_whatsapp(req: AccTokenReq):
    _guard(req.token)
    return await asyncio.to_thread(_acc().reparar_whatsapp)


# ── FÁBRICA DE MOTORES (EXCLUSIVA DEL DUEÑO — exige PIN) ──────────────
_FAB = None
def _fab():
    global _FAB
    if _FAB is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("fabrica_motores", _ROOT / "CEREBRO" / "fabrica_motores.py")
        _FAB = _ilu.module_from_spec(spec); spec.loader.exec_module(_FAB)
    return _FAB

class FabricarReq(BaseModel):
    token: str
    nombre: str = ""
    descripcion: str = ""
    slug: str = ""
    accion: str = ""
    datos: dict = {}

@app.post("/motor/fabricar", tags=["Fabrica"])
async def motor_fabricar(req: FabricarReq):
    _guard(req.token)   # solo el dueño puede crear motores
    return await asyncio.to_thread(_fab().crear_motor, req.nombre, req.descripcion)

@app.post("/motor/custom/listar", tags=["Fabrica"])
async def motor_custom_listar(req: FabricarReq):
    _guard(req.token)
    return await asyncio.to_thread(_fab().listar_motores_custom)

@app.post("/motor/custom/probar", tags=["Fabrica"])
async def motor_custom_probar(req: FabricarReq):
    _guard(req.token)
    return await asyncio.to_thread(_fab().probar_motor, req.slug, req.accion, req.datos or {})


# ── RAZONADOR PROFUNDO (cerebro grande bajo demanda) ─────────────────
_RAZ = None
def _raz():
    global _RAZ
    if _RAZ is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("razonador", _ROOT / "CEREBRO" / "razonador.py")
        _RAZ = _ilu.module_from_spec(spec); spec.loader.exec_module(_RAZ)
    return _RAZ

class RazonarReq(BaseModel):
    pregunta: str
    contexto: str = ""

@app.post("/razonar", tags=["Cerebro"])
async def razonar_endpoint(req: RazonarReq):
    """Razonamiento profundo bajo demanda (modelo grande + autocrítica)."""
    return await asyncio.to_thread(_raz().razonar, req.pregunta, req.contexto)


# ── ÁLBUM DE CATÁLOGO (loader) ───────────────────────────────────────
_ALB = None
def _alb():
    global _ALB
    if _ALB is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("album_catalogo", _ROOT / "TALLER" / "album_catalogo.py")
        _ALB = _ilu.module_from_spec(spec); spec.loader.exec_module(_ALB)
    return _ALB


# ── ENDPOINT NUEVO — usa Consciencia como router real ─────────────────

class ChatRequest(BaseModel):
    mensaje: str
    user_id: str = "anuar"
    session_id: Optional[str] = None
    canal: str = "api"


@app.post("/chat", tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Endpoint principal — usa CEREBRO/consciencia.py como router real.
    Routing LLM, memoria episódica/semántica, bus neuronal, motor de sueño.
    """
    try:
        from CEREBRO.consciencia import consciencia
        if not consciencia._listo:
            await consciencia.inicializar()
        result = await consciencia.procesar(
            mensaje=request.mensaje,
            user_id=request.user_id,
            session_id=request.session_id or request.user_id,
            canal=request.canal,
        )
        return {
            "respuesta": result.get("respuesta", ""),
            "motores_usados": result.get("motores_usados", []),
            "temperatura_lead": result.get("temperatura_lead", "frio"),
            "duracion_ms": result.get("duracion_ms", 0),
            "timestamp": result.get("timestamp", ""),
            "status": "ok",
        }
    except Exception as e:
        logger.error(f"Error en /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bus/estado", tags=["Sistema"])
async def bus_estado():
    """Estado real del Bus Neuronal — motores registrados y cola."""
    try:
        from CEREBRO.bus_neuronal import bus
        return bus.estado()
    except Exception as e:
        return {"error": str(e)}


@app.get("/memoria/resumen", tags=["Sistema"])
async def memoria_resumen():
    """Resumen de la memoria episódica y semántica."""
    try:
        from MEMORIA.sistema_memoria import memoria
        episodios = await memoria.contar_episodios()
        semantica = await memoria.recordar(tema=None, limite=5)
        return {
            "episodios_total": episodios,
            "semantica_reciente": semantica,
            "status": "ok",
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────


@app.get("/historial/{motor_id}", tags=["Historial"])
async def get_historial(motor_id: str, limit: int = 10):
    """Get interaction history for motor"""
    import json
    from pathlib import Path

    historial_dir = aurora.historial_dir
    historial_files = sorted(historial_dir.glob(f"{motor_id}_*.json"), reverse=True)

    if not historial_files:
        return {"motor_id": motor_id, "historial": []}

    # Load latest file
    latest_file = historial_files[0]
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "motor_id": motor_id,
                "historial": data[-limit:],
                "total": len(data),
            }
    except Exception as e:
        logger.error(f"Error loading historial: {e}")
        return {"motor_id": motor_id, "historial": [], "error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming responses"""
    await websocket.accept()
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            mensaje = data.get("mensaje", "")

            if not mensaje:
                await websocket.send_json(
                    {"error": "mensaje requerido"}
                )
                continue

            # Process
            logger.info(f"WS: {mensaje[:50]}")
            result = await aurora.procesar_mensaje(mensaje)

            # Send result
            await websocket.send_json({
                "motor_id": result.get("motor_id"),
                "respuesta": result.get("respuesta"),
                "sdk_usado": result.get("sdk_usado"),
                "tiempo_ms": result.get("tiempo_ms"),
                "status": result.get("status"),
            })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
        finally:
            await websocket.close()


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("AURORA Server iniciando...")
    try:
        from CEREBRO.bus_neuronal import bus
        n = len(bus.estado().get("motores_registrados", []))
        logger.info(f"Motores en bus: {n}")
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("AURORA Server cerrado")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
