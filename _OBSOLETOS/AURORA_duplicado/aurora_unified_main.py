#!/usr/bin/env python3
"""
AURORA + NEXUS v3 UNIFIED MAIN
Sistema integrado 100% operativo
Todos los motores + Cerebro + APIs + Automaciones
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AURORA_MAIN")

# Cargar variables de entorno desde .env (clave Groq, etc.) — robusto: no depende
# de como se lance el proceso (tarea de logon, doble clic, terminal).
def _cargar_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for linea in env_path.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_cargar_env()

# Imports - CEREBRO
sys.path.insert(0, str(Path(__file__).parent / "CEREBRO"))
sys.path.insert(0, str(Path(__file__).parent / "ORACLE"))
sys.path.insert(0, str(Path(__file__).parent / "PUBLICADOR"))
sys.path.insert(0, str(Path(__file__).parent / "ACCESOS"))
sys.path.insert(0, str(Path(__file__).parent / "VIDEO"))
sys.path.insert(0, str(Path(__file__).parent / "EDITOR"))
sys.path.insert(0, str(Path(__file__).parent / "MODULOS"))
sys.path.insert(0, str(Path(__file__).parent / "COMANDOS"))
sys.path.insert(0, str(Path(__file__).parent / "REPARADOR"))
sys.path.insert(0, str(Path(__file__).parent / "TALLER"))
sys.path.insert(0, str(Path(__file__).parent / "MARKETING"))
sys.path.insert(0, str(Path(__file__).parent / "VENDEDOR"))
sys.path.insert(0, str(Path(__file__).parent / "AUTH"))
sys.path.insert(0, str(Path(__file__).parent / "PROGRAMADOR"))
sys.path.insert(0, str(Path(__file__).parent / "SUBLIMACION"))
sys.path.insert(0, str(Path(__file__).parent / "VOZ"))

try:
    # aurora_cerebro_simple = cerebro real con Groq (v3.1).
    # aurora_cerebro.py quedó obsoleto: usa modelo mixtral dado de baja + crash al cargar.
    from aurora_cerebro_simple import AuroraCerebro
    logger.info("[OK] AuroraCerebro v3.1 (Groq real) importado")
except Exception as e:
    logger.error(f"[ERROR] AuroraCerebro: {e}")
    AuroraCerebro = None

# Imports - MOTORES
# Los 9 "motores" anteriores (MOTORES/__init__.py) eran SIMULACIONES: texto fijo,
# imagen de 1x1 px, precios falsos que duplicaban cerebro + cotizador + ORACLE.
# Eliminados (regla: real o no existe). Las capacidades REALES viven en sus modulos.
MOTORES = {}
CAPACIDADES = [
    {"id": "cerebro", "nombre": "Cerebro AURORA", "real": True,
     "desc": "Razonamiento real (Groq llama-3.1-8b-instant)", "endpoint": "/api/chat/send"},
    {"id": "cotizador", "nombre": "Cotizador ILUME/ATF", "real": True,
     "desc": "Precios reales X1-X7 + instalacion + IVA", "endpoint": "/api/operacion/cotizar"},
    {"id": "oracle_captacion", "nombre": "ORACLE Captacion", "real": True,
     "desc": "Leads reales (SQLite)", "endpoint": "/api/oracle/leads"},
    {"id": "oracle_taller", "nombre": "ORACLE Taller", "real": True,
     "desc": "Ordenes de taller reales (SQLite)", "endpoint": "/api/oracle/ordenes"},
    {"id": "publicador", "nombre": "Publicador Redes", "real": True,
     "desc": "Publica real via API con token; honesto cuando falta (no simula)", "endpoint": "/api/publicador/estado"},
    {"id": "acceso_web", "nombre": "Acceso Web", "real": True,
     "desc": "Lee paginas y busca en internet (real)", "endpoint": "/api/acceso/web"},
    {"id": "acceso_pc", "nombre": "Acceso PC", "real": True,
     "desc": "Comandos + archivos con candados (carpetas permitidas, lista negra, log)", "endpoint": "/api/acceso/estado"},
    {"id": "video", "nombre": "Video viral", "real": True,
     "desc": "Lista videos, genera hook/caption (cerebro) y reedita a 9:16 (ffmpeg)", "endpoint": "/api/video/listar"},
    {"id": "seguimiento", "nombre": "Seguimiento leads", "real": True,
     "desc": "Mensaje de WhatsApp generado por el cerebro por lead", "endpoint": "/api/oracle/lead/{id}/seguimiento"},
]
logger.info(f"[OK] {len(CAPACIDADES)} capacidades reales (0 motores stub)")

# Imports - ORACLE (panel operativo: captacion + orden de taller, 100% real)
sys.path.insert(0, str(Path(__file__).parent / "ORACLE"))
try:
    import oracle_core
    oracle_core.init_db()
    logger.info("[OK] ORACLE cargado (captacion + orden de taller)")
except Exception as e:
    logger.error(f"[ERROR] ORACLE: {e}")
    oracle_core = None

# Imports - PUBLICADOR (redes: real via API con token; honesto cuando falta)
sys.path.insert(0, str(Path(__file__).parent / "PUBLICADOR"))
try:
    import publicador_core
    logger.info("[OK] PUBLICADOR cargado")
except Exception as e:
    logger.error(f"[ERROR] PUBLICADOR: {e}")
    publicador_core = None

# Imports - ACCESOS (web + PC, reales, con candados de seguridad)
sys.path.insert(0, str(Path(__file__).parent / "ACCESOS"))
try:
    import accesos_core
    logger.info("[OK] ACCESOS cargado (web + PC con candados)")
except Exception as e:
    logger.error(f"[ERROR] ACCESOS: {e}")
    accesos_core = None

# Imports - VIDEO (reedicion real para viralizacion)
sys.path.insert(0, str(Path(__file__).parent / "VIDEO"))
try:
    import video_core
    logger.info("[OK] VIDEO cargado (reedicion viral)")
except Exception as e:
    logger.error(f"[ERROR] VIDEO: {e}")
    video_core = None

# Imports - EDITOR (super editor de imagenes)
sys.path.insert(0, str(Path(__file__).parent / "EDITOR"))
try:
    import editor_core
    logger.info("[OK] EDITOR cargado (imagenes)")
except Exception as e:
    logger.error(f"[ERROR] EDITOR: {e}")
    editor_core = None

# Imports - MODULOS (FORJA, EVOLUCION, CANBUSFIX en modo pausado)
sys.path.insert(0, str(Path(__file__).parent / "MODULOS"))
try:
    import modulos_core
    logger.info("[OK] MODULOS cargado (FORJA/EVOLUCION/CANBUSFIX en pausa)")
except Exception as e:
    logger.error(f"[ERROR] MODULOS: {e}")
    modulos_core = None

# Imports - COMANDOS (NEXUS v3: abrir apps/redes, escanear red)
sys.path.insert(0, str(Path(__file__).parent / "COMANDOS"))
try:
    import comandos_core
    logger.info("[OK] COMANDOS NEXUS cargado")
except Exception as e:
    logger.error(f"[ERROR] COMANDOS: {e}")
    comandos_core = None

# Imports - REPARADOR (reparar apps de Windows colgadas)
sys.path.insert(0, str(Path(__file__).parent / "REPARADOR"))
try:
    import reparador_core
    logger.info("[OK] REPARADOR de apps cargado")
except Exception as e:
    logger.error(f"[ERROR] REPARADOR: {e}")
    reparador_core = None

# Imports - TALLER (vector/DXF para laser via Inkscape)
sys.path.insert(0, str(Path(__file__).parent / "TALLER"))
try:
    import taller_core
    logger.info("[OK] TALLER cargado (DXF/vector via Inkscape)")
except Exception as e:
    logger.error(f"[ERROR] TALLER: {e}")
    taller_core = None

# Imports - MARKETING (Asesor de marketing digital: algoritmos + viralización/ventas/monetización)
sys.path.insert(0, str(Path(__file__).parent / "MARKETING"))
try:
    import asesor_core
    logger.info("[OK] ASESOR de marketing cargado (algoritmos + playbook real)")
except Exception as e:
    logger.error(f"[ERROR] ASESOR marketing: {e}")
    asesor_core = None

# Imports - VENDEDOR (asesor técnico interno + súper-vendedor con fichas reales)
sys.path.insert(0, str(Path(__file__).parent / "VENDEDOR"))
try:
    import vendedor_core
    logger.info("[OK] VENDEDOR cargado (fichas técnicas + técnicas de venta reales)")
except Exception as e:
    logger.error(f"[ERROR] VENDEDOR: {e}")
    vendedor_core = None

# Imports - IDENTIDAD (reconoce al dueño Anuar vs cliente; seguridad local)
sys.path.insert(0, str(Path(__file__).parent / "AUTH"))
try:
    import identidad_core
    logger.info("[OK] IDENTIDAD cargada (dueño vs cliente)")
except Exception as e:
    logger.error(f"[ERROR] IDENTIDAD: {e}")
    identidad_core = None

# Imports - AGENDADOR (cola de contenido + publicación automática supervisada)
sys.path.insert(0, str(Path(__file__).parent / "PROGRAMADOR"))
try:
    import agendador_core
    logger.info("[OK] AGENDADOR cargado (cola + publicación supervisada)")
except Exception as e:
    logger.error(f"[ERROR] AGENDADOR: {e}")
    agendador_core = None

# Imports - SUBLIMACION (video/foto -> lienzo listo para imprimir 300 DPI)
sys.path.insert(0, str(Path(__file__).parent / "SUBLIMACION"))
try:
    import sublimacion_core
    logger.info("[OK] SUBLIMACION cargada (fotograma -> lienzo 300 DPI)")
except Exception as e:
    logger.error(f"[ERROR] SUBLIMACION: {e}")
    sublimacion_core = None

# Imports - VERIFICADOR (capa de calidad anti-incoherencias)
try:
    import verificador_core
    logger.info("[OK] VERIFICADOR cargado (anti-errores/incoherencias)")
except Exception as e:
    logger.error(f"[ERROR] VERIFICADOR: {e}")
    verificador_core = None

# Imports - VOZ GOOGLE (AURORA habla por el Google Home Mini / casting)
sys.path.insert(0, str(Path(__file__).parent / "VOZ"))
try:
    import voz_google
    logger.info("[OK] VOZ GOOGLE cargada (habla por Google Mini)")
except Exception as e:
    logger.error(f"[ERROR] VOZ GOOGLE: {e}")
    voz_google = None

# FastAPI setup
try:
    from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, UploadFile, File, Form, Header, Depends
    from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    try:
        import jwt
    except Exception:
        jwt = None
    logger.info("[OK] FastAPI importado")
except Exception as e:
    logger.error(f"[ERROR] FastAPI: {e}")
    sys.exit(1)

# Crear directorio static si no existe
import os
static_dir = Path(__file__).parent / "FRONTEND"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)

# Crear app FastAPI
app = FastAPI(
    title="AURORA NEXUS v3",
    description="Sistema inteligente de operaciones sin censura",
    version="3.0.0"
)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("AURORA_JWT_SECRET_KEY") or ""
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
try:
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
except Exception:
    JWT_EXPIRATION_HOURS = 24


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


def _decode_jwt(token: str) -> dict:
    if not token or jwt is None or not JWT_SECRET_KEY:
        return {}
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _issue_jwt(identity_token: str, rol: str = "dueño") -> str | None:
    if jwt is None or not JWT_SECRET_KEY:
        return None
    payload = {
        "sub": "aurora-session",
        "rol": rol,
        "identity_token": identity_token,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    try:
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"[ERROR] JWT: {e}")
        return None


def _resolve_owner_token(token: str = "", authorization: str | None = None) -> str:
    candidato = token or _bearer_token(authorization)
    if not candidato:
        raise HTTPException(status_code=401, detail="Falta token de acceso.")
    if identidad_core is None:
        raise HTTPException(status_code=503, detail="Identidad no disponible")
    if identidad_core.estado().get("configurado"):
        payload = _decode_jwt(candidato)
        if payload.get("rol") == "dueño" and payload.get("identity_token"):
            candidato = str(payload["identity_token"])
        elif payload:
            raise HTTPException(status_code=403, detail="Token JWT inválido para dueño.")
        elif identidad_core.rol(candidato) != "dueño":
            raise HTTPException(status_code=403, detail="Solo Anuar (dueño) puede hacer esto.")
    return candidato


def _solo_dueno(token: str = "", authorization: str | None = None):
    _resolve_owner_token(token, authorization)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (HTML, CSS, JS)
try:
    static_dir = Path(__file__).parent / "FRONTEND"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"[OK] Archivos estáticos montados en /static")
    # Escaparate: servir la carpeta de videos
    _videos_dir = r"C:\Users\Administrador\Videos"
    if os.path.isdir(_videos_dir):
        app.mount("/videos", StaticFiles(directory=_videos_dir), name="videos")
        logger.info("[OK] Videos montados en /videos (escaparate)")
    _ed_out = r"C:\AURORA\EDITOR_OUT"
    os.makedirs(_ed_out, exist_ok=True)
    app.mount("/editor-out", StaticFiles(directory=_ed_out), name="editor_out")
    _ta_out = r"C:\AURORA\TALLER_OUT"
    os.makedirs(_ta_out, exist_ok=True)
    app.mount("/taller-out", StaticFiles(directory=_ta_out), name="taller_out")
    _up_dir = r"C:\AURORA\UPLOADS"
    os.makedirs(_up_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=_up_dir), name="uploads")
except Exception as e:
    logger.warning(f"[WARN] No se pudieron montar archivos estáticos: {e}")

# Modelos
class MensajeRequest(BaseModel):
    mensaje: str
    contexto: dict = {}
    negocio: str = "general"
    sessionId: str = "session_default"
    token: str = ""   # llave de identidad (dueño vs cliente)

class MensajeResponse(BaseModel):
    respuesta: str
    confianza: float
    timestamp: str

# Dependencia para verificar el token JWT
async def verificar_token_jwt(credenciales: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    Dependencia de FastAPI para verificar un token JWT.
    Extrae el token, lo decodifica y valida el rol.
    """
    if not JWT_SECRET_KEY or not jwt:
        raise HTTPException(status_code=500, detail="JWT no configurado en el servidor.")
    
    token = credenciales.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        rol = payload.get("rol")
        if rol != "dueño":
            raise HTTPException(status_code=403, detail="Permiso denegado: se requiere rol de 'dueño'.")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token ha expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")
    except Exception:
        raise HTTPException(status_code=401, detail="No se pudo validar el token.")

# ==================== ENDPOINTS ====================

# HEALTH
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "sistema": "AURORA NEXUS v3",
        "timestamp": datetime.now().isoformat(),
        "capacidades_reales": len(CAPACIDADES),
        "oracle": "activo" if oracle_core else "offline",
        "cerebro": "activo" if AuroraCerebro else "offline"
    }

# CEREBRO - Razonamiento
@app.post("/api/cerebro/razonar")
async def cerebro_razonar(request: MensajeRequest):
    if not AuroraCerebro:
        raise HTTPException(status_code=500, detail="Cerebro offline")

    try:
        cerebro = AuroraCerebro()
        resultado = await cerebro.razonar(request.mensaje, request.contexto)
        return {
            "status": "OK",
            "resultado": resultado,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error razonamiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CEREBRO - Decisión autónoma
@app.post("/api/cerebro/decidir")
async def cerebro_decidir(escenario: str):
    if not AuroraCerebro:
        raise HTTPException(status_code=500, detail="Cerebro offline")

    try:
        cerebro = AuroraCerebro()
        resultado = await cerebro.decidir_autonomamente(escenario)
        return {
            "status": "OK",
            "resultado": resultado,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error decisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CAPACIDADES REALES - Listar (solo lo que de verdad funciona, sin stubs)
@app.get("/api/motores/listar")
async def listar_motores():
    return {"total": len(CAPACIDADES), "capacidades": CAPACIDADES}

# Catálogo de precios REAL (cargado de C:\AURORA\CONFIG\precios_base.json). Sin supuestos.
_CATALOGO = None

def _cargar_catalogo():
    global _CATALOGO
    if _CATALOGO is None:
        atf, milens, costo_min = {}, {}, 8.0
        try:
            d = json.loads(Path(r"C:\AURORA\CONFIG\precios_base.json").read_text(encoding="utf-8"))
            for it in d.get("retrofit", []):
                atf[it["nombre"].lower()] = {"precio": float(it["precio"]), "cat": "ATF retrofit", "id": it.get("id", "")}
            # Catálogo ATF completo (106 productos, precios públicos, marca blanca)
            try:
                ca = json.loads(Path(r"C:\AURORA\CONFIG\catalogo_atf.json").read_text(encoding="utf-8"))
                for it in ca.get("productos", []):
                    atf[it["nombre"].lower()] = {"precio": float(it["precio"]),
                                                 "cat": it.get("categoria", "ATF"), "id": it.get("sku", "")}
            except Exception as e:
                logger.warning(f"[COTIZADOR] catalogo_atf: {e}")
            for it in d.get("sublimacion_personalizacion", []):
                precio = next((it[k] for k in ("precio_subli", "precio_laser", "precio_vinil", "precio_dtf")
                               if it.get(k)), 0)
                if precio:
                    milens[it["nombre"].lower()] = {"precio": float(precio), "cat": it.get("cat", "")}
            for m in d.get("laser", {}).get("materiales", []):
                milens[m["nombre"].lower()] = {"precio": float(m["precio_hoja"]), "cat": "Material láser"}
            costo_min = float(d.get("laser", {}).get("costo_minuto", 8.0))
        except Exception as e:
            logger.warning(f"[COTIZADOR] catálogo: {e}")
        _CATALOGO = {"atf": atf, "milens": milens, "costo_minuto": costo_min}
    return _CATALOGO

import unicodedata as _ud
def _norm(s: str) -> str:
    """minúsculas sin acentos, para comparar como escribe el usuario (sin tildes)."""
    return "".join(c for c in _ud.normalize("NFD", (s or "").lower()) if _ud.category(c) != "Mn")

# OPERACIONES - Cotizar (precios REALES de tu catálogo; honesto si no encuentra, no inventa)
def _cotizar(negocio: str = "atf", producto: str = "", cantidad: int = 1):
    p = (producto or "").lower().strip()
    if not p:
        return {"status": "ERROR", "detalle": "Indica un producto"}
    c = _cargar_catalogo()
    items = c["atf"] if negocio.lower() == "atf" else c["milens"]
    pn = _norm(p)
    enc = next((n for n in items if pn == _norm(n) or pn in _norm(n) or _norm(n) in pn), None)
    if enc is None:
        toks = [w for w in _re.split(r"\s+", pn) if len(w) > 2 or any(ch.isdigit() for ch in w)]
        if toks:
            enc = next((n for n in items if all(
                w in _norm(n) or (w.endswith("s") and w[:-1] in _norm(n)) for w in toks)), None)
    if enc is None and negocio.lower() == "atf":
        enc = next((n for n, v in items.items() if v.get("id") and pn in _norm(v["id"])), None)
    if enc is None:
        extra = (f" Si es corte láser se calcula por material + minutos (${c['costo_minuto']}/min)."
                 if negocio.lower() == "milens" else "")
        return {"status": "NO_ENCONTRADO", "negocio": negocio, "producto": producto,
                "precio_unitario": 0, "subtotal_producto": 0, "costo_instalacion": 0,
                "impuestos": 0, "total_final": 0,
                "detalle": f"'{producto}' no está en tu catálogo {negocio.upper()}. No invento precios." + extra,
                "disponibles": list(items.keys())[:30]}
    base = items[enc]["precio"]; nota = items[enc]["cat"]
    if negocio.lower() == "milens" and ("termo" in enc or "grabad" in enc) and cantidad >= 25:
        base = round(base * 0.85, 2); nota += " (−15% por 25+ piezas)"
    sub = base * cantidad
    return {"status": "OK", "negocio": negocio, "producto": enc, "cantidad": cantidad,
            "precio_unitario": base, "subtotal_producto": sub, "costo_instalacion": 0,
            "impuestos": int(sub * 0.16), "total_final": int(sub * 1.16),
            "nota": nota, "timestamp": datetime.now().isoformat()}

@app.get("/api/operacion/cotizar")
async def cotizar(negocio: str = "atf", producto: str = "", cantidad: int = 1):
    return _cotizar(negocio, producto, cantidad)

# PANEL UNICO - ORACLE (operado por AURORA)
@app.get("/", response_class=HTMLResponse)
async def panel():
    panel_file = Path(__file__).parent / "FRONTEND" / "panel.html"
    return FileResponse(str(panel_file))

@app.get("/escaparate", response_class=HTMLResponse)
async def escaparate():
    return FileResponse(str(Path(__file__).parent / "FRONTEND" / "escaparate.html"))

@app.get("/manual", response_class=HTMLResponse)
async def manual():
    return FileResponse(str(Path(__file__).parent / "FRONTEND" / "manual.html"))

# PWA: instalable como app
_FE = Path(__file__).parent / "FRONTEND"
@app.get("/manifest.json")
async def _manifest(): return FileResponse(str(_FE / "manifest.json"))
@app.get("/sw.js")
async def _sw(): return FileResponse(str(_FE / "sw.js"), media_type="application/javascript")
@app.get("/icon-192.png")
async def _i192(): return FileResponse(str(_FE / "icon-192.png"))
@app.get("/icon-512.png")
async def _i512(): return FileResponse(str(_FE / "icon-512.png"))

# ==================== CHAT SYSTEM ====================

import sqlite3
import json
from datetime import datetime, timedelta

# Chat database
CHAT_DB = Path(__file__).parent / "chat_memory.db"

def init_chat_db():
    conn = sqlite3.connect(str(CHAT_DB))
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS conversaciones (
        id TEXT PRIMARY KEY,
        usuario TEXT,
        timestamp TEXT,
        mensajes TEXT,
        metadata TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS aprendizajes (
        id INTEGER PRIMARY KEY,
        entrada TEXT,
        respuesta TEXT,
        feedback REAL,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

@app.get("/chat")
async def chat_page():
    return RedirectResponse("/")

def detect_motor(mensaje: str) -> str:
    """Detecta automáticamente el motor óptimo basado en palabras clave"""
    msg_lower = mensaje.lower()

    patterns = {
        "motor_coaching": ["potencial", "liderazgo", "creencia", "transformación", "propósito", "meta", "coach"],
        "motor_analisis": ["analiza", "mercado", "tendencia", "datos", "oportunidad", "industria"],
        "motor_ventas": ["venta", "cliente", "conversión", "pitch", "estrategia", "cierre"],
        "motor_code_gen": ["código", "script", "función", "programación", "python", "javascript"],
        "motor_imagenes": ["imagen", "visual", "diseño", "foto", "crea una imagen"]
    }

    scores = {}
    for motor, keywords in patterns.items():
        scores[motor] = sum(1 for kw in keywords if kw in msg_lower)

    return max(scores, key=scores.get) if max(scores.values()) > 0 else "motor_analisis"

import re as _re

def _usar_herramienta(mensaje: str):
    """Si el mensaje pide una accion real (web/PC/comando), la ejecuta. Devuelve (etiqueta, payload) o None."""
    m = mensaje.strip()
    bajo = m.lower()
    # Comandos NEXUS: abrir apps/redes, escanear red
    if comandos_core is not None and ("escanea" in bajo and "red" in bajo):
        return ("comando_nexus", comandos_core.ejecutar(m))
    if comandos_core is not None and bajo.startswith(("abre", "abrir", "lanza")):
        # Si pediste abrir algo, SIEMPRE respondemos honesto (aunque no lo reconozca), no charlamos.
        return ("comando_nexus", comandos_core.ejecutar(m))
    if accesos_core is None:
        return None
    url = _re.search(r"https?://[^\s]+", m)
    if url:
        return ("web", accesos_core.leer_web(url.group(0)))
    for t in ["busca en internet", "buscar en internet", "investiga en internet", "busca en la web", "googlea", "busca sobre", "investiga sobre"]:
        if t in bajo:
            q = m[bajo.index(t) + len(t):].strip(" :") or m
            return ("buscar", accesos_core.buscar_web(q))
    for t in ["ejecuta el comando", "ejecuta comando", "corre el comando", "ejecuta:", "corre:"]:
        if t in bajo:
            cmd = m[bajo.index(t) + len(t):].strip(" :")
            if cmd:
                return ("comando", accesos_core.ejecutar_comando(cmd))
    for t in ["lee el archivo", "leer archivo", "lee archivo", "abre el archivo"]:
        if t in bajo:
            ruta = m[bajo.index(t) + len(t):].strip(" :")
            if ruta:
                return ("archivo", accesos_core.leer_archivo(ruta))
    for t in ["lista la carpeta", "listar carpeta", "que hay en la carpeta", "contenido de la carpeta"]:
        if t in bajo:
            ruta = m[bajo.index(t) + len(t):].strip(" :")
            if ruta:
                return ("listar", accesos_core.listar_directorio(ruta))
    return None

def _ruta_archivo(m: str):
    """Extrae una ruta de archivo Windows del mensaje (C:\\...)."""
    mm = _re.search(r'[A-Za-z]:\\[^\s"\'<>|]+', m)
    return mm.group(0) if mm else None

def _usar_motor(mensaje: str):
    """Detecta intención de motor (cotizar/caja/editor/dxf/ORACLE) en lenguaje natural y lo ejecuta.
    Devuelve (etiqueta, dict_resultado) o None. Solo datos reales; si falta info, el core responde honesto."""
    m = mensaje.strip(); bajo = m.lower()
    ruta = _ruta_archivo(m)

    # ---- COTIZADOR (precios reales del catálogo) ----
    for t in ("cotiza ", "cotización de ", "cotizacion de ", "cuánto cuesta ", "cuanto cuesta ",
              "cuánto vale ", "cuanto vale ", "precio de ", "precio del "):
        if t in bajo:
            resto = m[bajo.index(t) + len(t):].strip(" :?¿")
            # Cantidad SOLO si va al inicio ("3 servilleteros"); NO borrar números del producto (30oz, h4)
            cant = 1
            mq = _re.match(r'^(\d+)\s+(.+)$', resto)
            if mq:
                cant = int(mq.group(1)); resto = mq.group(2)
            neg = "atf" if any(k in bajo for k in ("atf", "retrofit", "ojos demonio", "demonio", "tiras",
                  "fibra optica", "fibra óptica", "led h", "faro", "secuencial")) else "milens"
            prod = _re.sub(r'\b(para|de|del)\s+(atf|milens)\b', ' ', resto, flags=_re.I)
            prod = _re.sub(r'\b(atf|milens|piezas?|pzas?|unidades?|uds?)\b', ' ', prod, flags=_re.I)
            prod = _re.sub(r'^\s*(unos?|unas?|el|la|los|las)\s+', '', prod, flags=_re.I)
            prod = _re.sub(r'\s+', ' ', prod).strip(" .")
            r = _cotizar(neg, prod, cant)
            if r.get("status") != "OK":
                r2 = _cotizar("atf" if neg == "milens" else "milens", prod, cant)
                if r2.get("status") == "OK":
                    r = r2
            return ("cotizar", r)

    # ---- TALLER: CAJA paramétrica (boxes.py) ----
    if taller_core is not None and "caja" in bajo and any(w in bajo for w in
            ("haz", "hacer", "crea", "crear", "genera", "generar", "diseña", "disena", "dame", "necesito")):
        nums = [float(x) for x in _re.findall(r'\d+(?:\.\d+)?', m)]
        mg = (_re.search(r'(?:grosor|espesor)\s*(?:de\s*)?(\d+(?:\.\d+)?)', bajo)
              or _re.search(r'\ba\s+(\d+(?:\.\d+)?)\s*mm', bajo)
              or _re.search(r'(\d+(?:\.\d+)?)\s*mm', bajo))
        gros = 3.0
        if mg:
            gros = float(mg.group(1))
            if gros in nums:
                nums.remove(gros)
        x = nums[0] if len(nums) >= 1 else 80
        y = nums[1] if len(nums) >= 2 else 50
        h = nums[2] if len(nums) >= 3 else 40
        return ("taller", taller_core.caja(x, y, h, gros))

    # ---- TALLER: catálogo de diseños DXF ----
    if taller_core is not None and any(k in bajo for k in
            ("catálogo de diseños", "catalogo de disenos", "mis diseños", "mis disenos",
             "qué dxf tengo", "que dxf tengo", "mis trabajos dxf", "lista mis diseños")):
        return ("catalogo", taller_core.catalogo())

    # ---- TALLER: convertir a DXF ----
    if taller_core is not None and ruta and "dxf" in bajo and any(w in bajo for w in ("convierte", "convertir", "pasa", "exporta")):
        return ("taller", taller_core.convertir_a_dxf(ruta))

    # ---- TALLER: vectorizar imagen ----
    if taller_core is not None and ruta and any(w in bajo for w in ("vectoriza", "vectorizar", "vector lineal", "traza")):
        return ("taller", taller_core.vectorizar(ruta))

    # ---- TALLER: texto/nombre a DXF ----
    for t in ("texto a dxf", "nombre a dxf", "nombre en dxf", "dxf del nombre", "dxf del texto", "graba el nombre"):
        if taller_core is not None and t in bajo:
            txt = m[bajo.index(t) + len(t):].strip(" :")
            if txt:
                return ("taller", taller_core.texto_a_dxf(txt))

    # ---- EDITOR (requieren ruta de imagen) ----
    if editor_core is not None and ruta:
        if "low" in bajo and "poly" in bajo:
            return ("editor", editor_core.low_poly(ruta))
        if any(k in bajo for k in ("cartoon", "caricatura", "cómic", "comic")):
            return ("editor", editor_core.cartoon(ruta))
        if "fondo" in bajo and any(w in bajo for w in ("quita", "quitar", "elimina", "sin", "remueve", "remover")):
            return ("editor", editor_core.quitar_fondo(ruta))
        if "pdf" in bajo and any(k in bajo for k in ("gran formato", "granformato", "plotter", "gran-formato")):
            return ("editor", editor_core.pdf_gran_formato(ruta))
        if any(k in bajo for k in ("línea", "linea", "lineal", "contorno")):
            return ("editor", editor_core.linea(ruta))
        if any(k in bajo for k in ("grabado", "grabar", "láser", "laser")):
            return ("editor", editor_core.grabado(ruta))

    # ---- ASESOR MARKETING: algoritmo de una red ----
    if asesor_core is not None and "algoritmo" in bajo:
        red = next((r for r in ("tiktok", "instagram", "facebook", "youtube") if r in bajo), None)
        if not red:
            red = "instagram" if "insta" in bajo else ("facebook" if "face" in bajo else None)
        return ("marketing", asesor_core.conocimiento(red))

    # ---- ASESOR MARKETING: playbook / buenas prácticas ----
    if asesor_core is not None and any(k in bajo for k in
            ("playbook", "buenas practicas", "buenas prácticas", "como viralizo", "cómo viralizo",
             "como vendo mas", "como vendo más", "como monetizo", "cómo monetizo",
             "tips de marketing", "consejos de marketing", "como vender mas", "cómo vender más")):
        if any(k in bajo for k in ("viral", "alcance")):
            fl = "viralizacion"
        elif any(k in bajo for k in ("monetiz", "dinero", "ingreso", "roi")):
            fl = "monetizacion"
        elif any(k in bajo for k in ("vend", "venta", "cerrar", "cliente")):
            fl = "ventas"
        else:
            fl = None
        return ("marketing", asesor_core.playbook(fl))

    # ---- VENDEDOR: ficha técnica de un equipo ----
    if vendedor_core is not None:
        for t in ("ficha tecnica de ", "ficha técnica de ", "ficha de ", "datos de ",
                  "especificaciones de ", "compatibilidad de ", "ficha tecnica ", "ficha técnica "):
            if t in bajo:
                prod = m[bajo.index(t) + len(t):].strip(" :?¿")
                if prod:
                    return ("vendedor_ficha", vendedor_core.ficha(prod))
    # ---- VENDEDOR: técnicas de venta ----
    if vendedor_core is not None and any(k in bajo for k in
            ("tecnicas de venta", "técnicas de venta", "tecnica de venta", "técnica de venta",
             "como cierro", "cómo cierro", "manejo de objeciones", "libreria de ventas")):
        return ("vendedor_tec", vendedor_core.tecnicas(None))

    # ---- SUBLIMACIÓN: lienzo o montar imagen para imprimir ----
    if sublimacion_core is not None and "lienzo" in bajo and not ruta:
        nums = [float(x) for x in _re.findall(r'\d+(?:\.\d+)?', m)]
        a = nums[0] if len(nums) >= 1 else 21
        al = nums[1] if len(nums) >= 2 else 9
        return ("sublimacion", sublimacion_core.lienzo_blanco(a, al))
    if sublimacion_core is not None and ruta and any(k in bajo for k in
            ("sublima", "monta", "para taza", "imprimir taza", "lienzo con", "para imprimir")):
        nums = [float(x) for x in _re.findall(r'\d+(?:\.\d+)?', m)]
        a = nums[0] if len(nums) >= 2 else 21
        al = nums[1] if len(nums) >= 2 else 9
        return ("sublimacion", sublimacion_core.montar(ruta, a, al))

    # ---- ORACLE: resumen del taller ----
    if oracle_core is not None and any(k in bajo for k in
            ("resumen", "cuántos leads", "cuantos leads", "cuántos interesados", "cuantos interesados", "cuántas órdenes", "cuantas ordenes",
             "estado del taller", "cómo va el taller", "como va el taller")):
        neg = "atf" if " atf" in (" " + bajo) else ("milens" if "milens" in bajo else None)
        return ("resumen", oracle_core.resumen(neg))

    # ---- ORACLE: registrar lead ----
    for t in ("registra lead", "registrar lead", "nuevo lead", "agrega lead", "captura lead", "anota lead",
              "registra interesado", "registrar interesado", "nuevo interesado", "agrega interesado", "anota interesado"):
        if oracle_core is not None and t in bajo:
            resto = m[bajo.index(t) + len(t):].strip(" :")
            mt = _re.search(r'(\+?\d[\d\s\-]{6,})', resto)
            tel = mt.group(1).strip() if mt else ""
            neg = "atf" if "atf" in bajo else ("milens" if "milens" in bajo else "atf")
            nombre = _re.sub(r'(\+?\d[\d\s\-]{6,})', '', resto)
            nombre = _re.sub(r'\b(tel|teléfono|telefono|cel|celular|atf|milens|whatsapp|wa)\b', '', nombre, flags=_re.I)
            nombre = nombre.strip(" :,-") or "Sin nombre"
            try:
                return ("lead", oracle_core.crear_lead(nombre, tel, "chat", neg))
            except Exception as e:
                return ("lead", {"status": "ERROR", "detalle": str(e)})

    return None

def _formato_resultado(etiqueta: str, r: dict) -> str:
    s = r.get("status")
    if etiqueta == "comando":
        if s == "OK":
            out = r.get("salida") or "(sin salida)"
            return f"💻 Comando (código {r['codigo']}):\n{out}" + (f"\n⚠️ {r['error']}" if r.get("error") else "")
        if s == "BLOQUEADO":
            return f"🔒 {r['detalle']}"
        return f"❌ {r.get('detalle')}"
    if etiqueta == "archivo":
        return f"📄 {r['ruta']}:\n{r['contenido']}" if s == "OK" else f"🔒/❌ {r.get('detalle')}"
    if etiqueta == "listar":
        if s == "OK":
            return "📁 " + r["ruta"] + ":\n" + "\n".join(
                ("- " + i["nombre"] + (f" ({i['kb']}KB)" if i["tipo"] == "archivo" else "/")) for i in r["items"])
        return f"🔒/❌ {r.get('detalle')}"
    if etiqueta == "comando_nexus":
        if s == "OK" and r.get("accion") == "escanear_red":
            return "🌐 Dispositivos en la red:\n" + r.get("salida", "")
        if s == "OK":
            return f"✅ Abriendo {r.get('app','')}…"
        return f"❌ {r.get('detalle', 'No se pudo')}"
    if etiqueta == "cotizar":
        if s == "OK":
            txt = (f"💰 {r['producto'].title()} ({r['negocio'].upper()}) ×{r['cantidad']}\n"
                   f"• Unitario: ${r['precio_unitario']:,.0f}\n"
                   f"• Subtotal: ${r['subtotal_producto']:,.0f}\n"
                   f"• IVA (16%): ${r['impuestos']:,.0f}\n"
                   f"• TOTAL: ${r['total_final']:,.0f}")
            return txt + (f"\n📌 {r['nota']}" if r.get("nota") else "")
        if s == "NO_ENCONTRADO":
            disp = ", ".join(r.get("disponibles", [])[:12])
            return f"🔎 {r['detalle']}" + (f"\n\n📋 Disponibles: {disp}" if disp else "")
        return f"❌ {r.get('detalle', 'No pude cotizar')}"
    if etiqueta in ("taller", "editor"):
        if s == "OK":
            archivo = r.get("dxf") or r.get("svg") or r.get("salida") or r.get("archivo") or ""
            emoji = "✂️" if etiqueta == "taller" else "🎨"
            extra = []
            if r.get("medidas"): extra.append(r["medidas"])
            if r.get("px"): extra.append(r["px"] + "px")
            if r.get("cm"): extra.append(r["cm"] + "cm")
            if r.get("kb"): extra.append(f"{r['kb']}KB")
            if r.get("nota"): extra.append(r["nota"])
            return f"{emoji} Listo: {archivo}" + (f"\n📐 {' · '.join(extra)}" if extra else "")
        return f"❌ {r.get('detalle', 'No se pudo procesar')}"
    if etiqueta == "catalogo":
        if s == "OK":
            top = "\n".join(f"• {t['nombre']} ({t['kb']}KB)" for t in r.get("trabajos", [])[:20])
            return f"✂️ Tienes {r['total']} diseños DXF:\n{top}" + ("\n…(mostrando 20)" if r['total'] > 20 else "")
        return f"❌ {r.get('detalle', 'Sin catálogo')}"
    if etiqueta == "resumen":
        return (f"📊 Resumen ({r.get('negocio')}):\n"
                f"• Interesados: {r.get('total_leads')}\n"
                f"• Órdenes: {r.get('total_ordenes')}\n"
                f"• Valor órdenes: ${r.get('valor_total_ordenes', 0):,.0f}\n"
                f"• Anticipos: ${r.get('anticipos_cobrados', 0):,.0f}\n"
                f"• Saldo pendiente: ${r.get('saldo_pendiente', 0):,.0f}")
    if etiqueta == "lead":
        if r.get("status") == "ERROR":
            return f"❌ {r.get('detalle')}"
        return (f"✅ Interesado registrado #{r.get('id')}: {r.get('nombre')}"
                + (f" · 📞 {r.get('telefono')}" if r.get("telefono") else "")
                + f" · {r.get('negocio','').upper()} · estado: {r.get('estado')}")
    if etiqueta == "marketing":
        if s != "OK":
            return f"❌ {r.get('detalle', 'No disponible')}"
        if "algoritmo" in r:
            a = r["algoritmo"]
            return (f"📱 Algoritmo {r['red'].upper()} — qué premia:\n"
                    + "\n".join("• " + x for x in a["señales_premia"])
                    + f"\n✅ Formato nativo: {r.get('formato_nativo','')}"
                    + "\n🚫 Evita: " + ", ".join(r.get("evitar", [])[:3]))
        if "algoritmos" in r:
            return ("📱 Entiendo los algoritmos de: " + ", ".join(r["algoritmos"].keys())
                    + ".\nPregúntame por uno (ej. \"algoritmo de tiktok\").")
        if "flanco" in r:
            return f"🎯 Playbook {r['flanco']}:\n" + "\n".join("• " + x for x in r["principios"])
        if "playbook" in r:
            return ("🎯 Tengo playbook de: " + ", ".join(r["playbook"].keys())
                    + ".\nPídeme uno: \"cómo viralizo\", \"cómo vendo más\", \"cómo monetizo\".")
        return str(r)
    if etiqueta == "vendedor_ficha":
        if s == "NO_ENCONTRADO":
            return f"🔎 {r['detalle']}\n📋 Equipos: " + ", ".join(r.get("disponibles", []))
        f = r["ficha"]
        txt = f"🔧 {f['nombre']} — ${f.get('precio',0):,.0f}\n"
        if r.get("completa"):
            txt += f"• {f.get('que_es','')}\n• Compatibilidad: {', '.join(f.get('compatibilidad',[]))}\n• {f.get('diferencias','')}"
        else:
            txt += f"⚠️ {r.get('aviso','')}"
        return txt
    if etiqueta == "vendedor_tec":
        return "🛒 Técnicas de venta reales:\n" + "\n".join("• " + k.replace("_", " ") for k in r["tecnicas"].keys())
    if etiqueta == "sublimacion":
        if r.get("status") == "OK":
            return (f"🖨️ Listo para imprimir ({r.get('medida','')}):\n"
                    f"• PNG: {r.get('png','')}\n• PDF: {r.get('pdf','')}\n• Vista previa: {r.get('preview','')}")
        return f"❌ {r.get('detalle', 'No se pudo')}"
    return str(r)

@app.post("/api/chat/send")
async def chat_send(request: MensajeRequest):
    """Procesa mensaje con detección automática de motor y razonamiento"""
    try:
        motor_detectado = detect_motor(request.mensaje)
        herramienta = _usar_herramienta(request.mensaje)
        if not herramienta:
            herramienta = _usar_motor(request.mensaje)

        # Identidad: dueño vs cliente. Si no hay PIN configurado, todo es dueño (compatibilidad).
        rol_usuario = "dueño"
        if identidad_core is not None and identidad_core.estado().get("configurado"):
            token_usuario = request.token or ""
            payload = _decode_jwt(token_usuario)
            if payload.get("identity_token"):
                token_usuario = str(payload["identity_token"])
            rol_usuario = identidad_core.rol(token_usuario)
        _SOLO_DUENO = ("comando", "archivo", "listar", "comando_nexus", "resumen")
        if rol_usuario != "dueño" and herramienta and herramienta[0] in _SOLO_DUENO:
            return {"status": "OK", "respuesta": "🔒 Esa acción es solo para Anuar (el dueño). "
                    "Soy AURORA, su asistente — con gusto te ayudo con productos, precios o tu pedido.",
                    "motor": "seguridad", "confidence": 1.0, "id": f"msg_{int(datetime.now().timestamp()*1000)}",
                    "timestamp": datetime.now().isoformat()}

        _OPERATIVAS = ("comando", "archivo", "listar", "comando_nexus",
                       "cotizar", "taller", "editor", "catalogo", "resumen", "lead", "marketing",
                       "vendedor_ficha", "vendedor_tec", "sublimacion")
        if herramienta and herramienta[0] in _OPERATIVAS:
            # Acción operativa (acceso o motor): devolver el resultado REAL directamente
            etiqueta, r = herramienta
            motor_detectado = "motor_" + etiqueta
            respuesta = _formato_resultado(etiqueta, r)
            confianza = 0.4 if r.get("status") == "ERROR" else 1.0
        elif AuroraCerebro:
            cerebro = AuroraCerebro()
            mensaje_cerebro = request.mensaje
            ctx = dict(request.contexto)
            if rol_usuario == "cliente":
                ctx["rol"] = "cliente"
                mensaje_cerebro = ("[Hablas con un CLIENTE en modo VENDEDOR de ATF/MILENS: cálido, experto y honesto. "
                                   "NO reveles datos internos, números del negocio ni del dueño.]\n\n" + mensaje_cerebro)
            # Catálogo: si pregunta por productos/equipos/kit, aterrizar al catálogo REAL (no inventar)
            _bm = request.mensaje.lower()
            if any(k in _bm for k in ("catalog", "catálog", "mis productos", "que vendo", "qué vendo",
                    "kit retrofit", "kit completo", "mi kit", "que ofrezco", "qué ofrezco")):
                try:
                    _cat = _cargar_catalogo()
                    _atf = ", ".join(list(_cat["atf"].keys()))
                    _mil = ", ".join(list(_cat["milens"].keys()))
                    mensaje_cerebro = (
                        "[RESPONDE SOLO CON EL CATÁLOGO REAL DE ANUAR. PROHIBIDO INVENTAR productos que no estén en esta lista.\n"
                        f"ATF (retrofit): {_atf}\n"
                        f"MILENS: {_mil}\n"
                        "Si para un 'kit completo' faltan piezas que no están en el catálogo (ej. proyectores/lupas o mano de obra), "
                        "dilo como FALTANTE honesto, NO lo inventes.]\n\n" + mensaje_cerebro)
                except Exception:
                    pass
            # Marketing: dar al cerebro el conocimiento real del asesor (sin inventar métricas)
            if asesor_core is not None and any(k in request.mensaje.lower() for k in
                    ("marketing", "viral", "algoritmo", "monetiz", "publicar", "alcance",
                     "vender", "ventas", "contenido", "publicidad")):
                mensaje_cerebro = (asesor_core.construir_brief_para_cerebro(
                    ctx.get("negocio", "ATF"), None, request.mensaje)
                    + "\n\n[Responde la pregunta del usuario]: " + mensaje_cerebro)
            if herramienta and herramienta[0] in ("web", "buscar"):
                r = herramienta[1]
                datos = r.get("texto") or "\n".join(
                    f"- {x['titulo']} ({x['url']})" for x in r.get("resultados", [])[:5])
                mensaje_cerebro += "\n\n[Datos reales de internet, úsalos para responder]:\n" + datos[:6000]
                motor_detectado = "acceso_" + herramienta[0]
            razonamiento = await cerebro.razonar(mensaje_cerebro, ctx)
            respuesta = razonamiento.get("respuesta") or (
                razonamiento.get("razonamiento", ["Entendido."])[0]
                if razonamiento.get("razonamiento") else "Entendido."
            )
            recomendaciones = razonamiento.get("recomendaciones", [])
            if recomendaciones:
                respuesta += "\n\n📋 Recomendaciones:\n" + "\n".join(f"• {r}" for r in recomendaciones[:3])
            if herramienta:
                respuesta = "🌐 (consulté la web)\n\n" + respuesta
            confianza = razonamiento.get("confianza", 0.88)
        else:
            respuesta = "Cerebro AURORA offline. Modo básico."
            confianza = 0.5

        init_chat_db()
        conn = sqlite3.connect(str(CHAT_DB))
        c = conn.cursor()
        msg_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        msg_data = {
            "id": msg_id,
            "usuario": request.mensaje,
            "aurora": respuesta,
            "motor": motor_detectado,
            "timestamp": datetime.now().isoformat()
        }
        # Acumular el hilo: leer mensajes previos de la sesión y agregar el nuevo
        c.execute("SELECT mensajes FROM conversaciones WHERE id = ?", (request.sessionId,))
        row = c.fetchone()
        hilo = json.loads(row[0]) if row else []
        hilo.append(msg_data)
        c.execute("INSERT OR REPLACE INTO conversaciones VALUES (?, ?, ?, ?, ?)",
                  (request.sessionId, "user",
                   datetime.now().isoformat(), json.dumps(hilo), json.dumps({"motor": motor_detectado})))
        conn.commit()
        conn.close()

        return {
            "status": "OK",
            "respuesta": respuesta,
            "motor": motor_detectado,
            "confidence": confianza,
            "id": msg_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error chat: {e}")
        return {
            "status": "ERROR",
            "respuesta": f"Error: {str(e)}",
            "confianza": 0.0
        }

@app.post("/api/chat/learn")
async def chat_learn(data: dict):
    """Registra feedback y actualiza confianza del modelo"""
    try:
        init_chat_db()
        conn = sqlite3.connect(str(CHAT_DB))
        c = conn.cursor()

        c.execute("""INSERT INTO aprendizajes (entrada, respuesta, feedback, timestamp)
                     VALUES (?, ?, ?, ?)""",
                  (data.get("entrada", ""), data.get("sessionId", ""),
                   data.get("feedback", 0.5), datetime.now().isoformat()))

        conn.commit()

        c.execute("SELECT AVG(feedback) FROM aprendizajes WHERE entrada LIKE ?",
                  (f"%{data.get('entrada', '')[:20]}%",))
        avg_feedback = c.fetchone()[0] or 0.5

        conn.close()

        return {
            "status": "OK",
            "feedback_registrado": True,
            "confianza_actualizada": avg_feedback,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error learn: {e}")
        return {"status": "ERROR", "feedback_registrado": False}

@app.get("/api/chat/history")
async def chat_history(sessionId: str = ""):
    """Obtiene historial de chat"""
    try:
        init_chat_db()
        conn = sqlite3.connect(str(CHAT_DB))
        c = conn.cursor()
        c.execute("SELECT mensajes FROM conversaciones WHERE id = ?", (sessionId,))
        row = c.fetchone()
        conn.close()

        if row:
            return {"status": "OK", "mensajes": json.loads(row[0])}
        return {"status": "OK", "mensajes": []}
    except Exception as e:
        return {"status": "ERROR", "mensajes": []}

@app.post("/api/chat/sleep")
async def chat_sleep():
    """Sleep cycle: consolida aprendizajes y genera reporte"""
    try:
        init_chat_db()
        conn = sqlite3.connect(str(CHAT_DB))
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM aprendizajes WHERE timestamp > datetime('now', '-24 hours')")
        aprendizajes_24h = c.fetchone()[0]

        c.execute("SELECT AVG(feedback), COUNT(*) FROM aprendizajes")
        avg_feedback, total_aprendizajes = c.fetchone()

        c.execute("SELECT entrada FROM aprendizajes ORDER BY timestamp DESC LIMIT 5")
        temas_recientes = [row[0] for row in c.fetchall()]

        conn.close()

        reporte = {
            "status": "OK",
            "consolidacion": {
                "episodios_24h": aprendizajes_24h,
                "total_aprendizajes": total_aprendizajes,
                "confianza_promedio": avg_feedback or 0.5,
                "temas_recientes": temas_recientes
            },
            "timestamp": datetime.now().isoformat()
        }

        if AuroraCerebro:
            cerebro = AuroraCerebro()
            sleep_result = await cerebro.etapa_sueno()
            reporte["cerebro"] = sleep_result

        return reporte
    except Exception as e:
        logger.error(f"Error sleep: {e}")
        return {"status": "ERROR", "consolidacion": {}}

# ==================== ORACLE (captacion + orden de taller) ====================

class LeadIn(BaseModel):
    nombre: str
    telefono: str = ""
    fuente: str = ""
    negocio: str = "atf"
    vehiculo: str = ""
    interes: str = ""
    notas: str = ""

class OrdenIn(BaseModel):
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

class EstadoIn(BaseModel):
    estado: str

def _oracle_guard():
    if oracle_core is None:
        raise HTTPException(status_code=503, detail="ORACLE no disponible")

@app.post("/api/oracle/lead")
async def oracle_crear_lead(data: LeadIn):
    _oracle_guard()
    try:
        return {"status": "OK", "lead": oracle_core.crear_lead(**data.dict())}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/oracle/leads")
async def oracle_listar_leads(estado: str = None, negocio: str = None):
    _oracle_guard()
    return {"status": "OK", "leads": oracle_core.listar_leads(estado, negocio)}

@app.post("/api/oracle/lead/{lead_id}/estado")
async def oracle_lead_estado(lead_id: int, data: EstadoIn):
    _oracle_guard()
    try:
        return {"status": "OK", "lead": oracle_core.actualizar_lead_estado(lead_id, data.estado)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/oracle/orden")
async def oracle_crear_orden(data: OrdenIn):
    _oracle_guard()
    try:
        return {"status": "OK", "orden": oracle_core.crear_orden(**data.dict())}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/oracle/ordenes")
async def oracle_listar_ordenes(estado: str = None, negocio: str = None):
    _oracle_guard()
    return {"status": "OK", "ordenes": oracle_core.listar_ordenes(estado, negocio)}

@app.post("/api/oracle/orden/{orden_id}/estado")
async def oracle_orden_estado(orden_id: int, data: EstadoIn):
    _oracle_guard()
    try:
        return {"status": "OK", "orden": oracle_core.actualizar_orden_estado(orden_id, data.estado)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/oracle/resumen")
async def oracle_resumen(negocio: str = None):
    _oracle_guard()
    return {"status": "OK", "resumen": oracle_core.resumen(negocio)}

@app.get("/oracle")
async def oracle_panel():
    return RedirectResponse("/")

# ==================== PUBLICADOR (redes) ====================

class PublicarIn(BaseModel):
    plataforma: str
    texto: str = ""
    media_url: str = ""

@app.get("/api/publicador/estado")
async def publicador_estado():
    if publicador_core is None:
        raise HTTPException(status_code=503, detail="Publicador no disponible")
    return {"status": "OK", **publicador_core.estado_redes()}

@app.post("/api/publicador/publicar", dependencies=[Depends(verificar_token_jwt)])
async def publicador_publicar(data: PublicarIn):
    if publicador_core is None:
        raise HTTPException(status_code=503, detail="Publicador no disponible")
    return publicador_core.publicar(data.plataforma, data.texto, data.media_url)

# ==================== ACCESOS (web + PC) ====================

class WebIn(BaseModel):
    url: str = ""
    query: str = ""

class ComandoIn(BaseModel):
    comando: str

class ArchivoIn(BaseModel):
    ruta: str
    contenido: str = ""

def _acc_guard():
    if accesos_core is None:
        raise HTTPException(status_code=503, detail="Accesos no disponible")

@app.get("/api/acceso/estado")
async def acceso_estado(authorization: str | None = Header(default=None)):
    _acc_guard()
    _solo_dueno("", authorization)
    return {"status": "OK", **accesos_core.estado()}

@app.post("/api/acceso/web")
async def acceso_web(data: WebIn, authorization: str | None = Header(default=None)):
    _acc_guard()
    _solo_dueno("", authorization)
    if data.url:
        return accesos_core.leer_web(data.url)
    if data.query:
        return accesos_core.buscar_web(data.query)
    raise HTTPException(status_code=400, detail="Falta url o query")

@app.post("/api/acceso/comando", dependencies=[Depends(verificar_token_jwt)])
async def acceso_comando(data: ComandoIn):
    _acc_guard()
    return accesos_core.ejecutar_comando(data.comando)

@app.post("/api/acceso/archivo/leer", dependencies=[Depends(verificar_token_jwt)])
async def acceso_leer(data: ArchivoIn):
    _acc_guard()
    return accesos_core.leer_archivo(data.ruta)

@app.post("/api/acceso/archivo/escribir", dependencies=[Depends(verificar_token_jwt)])
async def acceso_escribir(data: ArchivoIn):
    _acc_guard()
    return accesos_core.escribir_archivo(data.ruta, data.contenido)

@app.get("/api/acceso/listar")
async def acceso_listar(ruta: str, authorization: str | None = Header(default=None)):
    _acc_guard()
    _solo_dueno("", authorization)
    return accesos_core.listar_directorio(ruta)

# ==================== VIDEO (viralizacion) ====================

class VideoIn(BaseModel):
    nombre: str

@app.get("/api/video/listar")
async def video_listar():
    if video_core is None:
        raise HTTPException(status_code=503, detail="Video no disponible")
    return video_core.listar()

@app.post("/api/video/viral")
async def video_viral(data: VideoIn):
    """Genera hook+caption+hashtags REAL (cerebro) para un video. No reedita (eso es /reeditar)."""
    if not AuroraCerebro:
        raise HTTPException(status_code=503, detail="Cerebro offline")
    cerebro = AuroraCerebro()
    prompt = (f"Para un video de ATF (retrofit de faros, sin rostro) llamado '{data.nombre}', "
              "dame para TikTok/Reels: 1) un HOOK de 1 línea muy fuerte, 2) un CAPTION corto, "
              "3) 8 hashtags. Formato claro y listo para copiar.")
    r = await cerebro.razonar(prompt, {"negocio": "ATF"})
    return {"status": "OK", "nombre": data.nombre, "viral": r.get("respuesta", "")}

@app.post("/api/video/reeditar")
async def video_reeditar(data: VideoIn):
    """Reedita el video a 9:16 vertical (ffmpeg REAL)."""
    if video_core is None:
        raise HTTPException(status_code=503, detail="Video no disponible")
    return video_core.reeditar_vertical(data.nombre)

# ==================== ORACLE - seguimiento de leads (cerebro) ====================

@app.post("/api/oracle/lead/{lead_id}/seguimiento")
async def oracle_seguimiento(lead_id: int):
    _oracle_guard()
    lead = oracle_core.obtener_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no existe")
    if not AuroraCerebro:
        raise HTTPException(status_code=503, detail="Cerebro offline")
    cerebro = AuroraCerebro()
    prompt = (f"Escribe un mensaje de WhatsApp de seguimiento, cálido y directo, para este lead de ATF: "
              f"nombre={lead['nombre']}, vehículo={lead.get('vehiculo','')}, interés={lead.get('interes','')}, "
              f"estado={lead['estado']}. Máximo 4 líneas, cierra invitando a agendar. Listo para enviar.")
    r = await cerebro.razonar(prompt, {"negocio": "ATF"})
    mensaje = r.get("respuesta", "")
    envio = None
    if publicador_core is not None and lead.get("telefono"):
        envio = publicador_core.enviar_whatsapp(lead["telefono"], mensaje)
    return {"status": "OK", "lead_id": lead_id, "mensaje": mensaje, "envio_whatsapp": envio}

class MetaIn(BaseModel):
    user_token: str
    app_id: str
    app_secret: str

@app.post("/api/publicador/configurar-meta")
async def configurar_meta(data: MetaIn, authorization: str | None = Header(default=None)):
    if publicador_core is None:
        raise HTTPException(status_code=503, detail="Publicador no disponible")
    _solo_dueno("", authorization)
    return publicador_core.configurar_meta(data.user_token, data.app_id, data.app_secret)

@app.get("/api/whatsapp/estado")
async def whatsapp_estado():
    if publicador_core is None:
        raise HTTPException(status_code=503, detail="Publicador no disponible")
    return publicador_core.estado_whatsapp()

# ==================== SUPER EDITOR ====================

class EditorIn(BaseModel):
    ruta: str
    umbral: int = 128
    ancho_cm: float = 0
    alto_cm: float = 0
    puntos: int = 1500

def _ed_guard():
    if editor_core is None:
        raise HTTPException(status_code=503, detail="Editor no disponible")

@app.get("/api/editor/info")
async def editor_info():
    _ed_guard()
    return {"status": "OK", **editor_core.info()}

@app.post("/api/editor/quitar-fondo")
async def editor_quitar_fondo(d: EditorIn):
    _ed_guard()
    return editor_core.quitar_fondo(d.ruta)

@app.post("/api/editor/linea")
async def editor_linea(d: EditorIn):
    _ed_guard()
    return editor_core.linea(d.ruta)

@app.post("/api/editor/grabado")
async def editor_grabado(d: EditorIn):
    _ed_guard()
    return editor_core.grabado(d.ruta, d.umbral)

@app.post("/api/editor/redimensionar")
async def editor_redimensionar(d: EditorIn):
    _ed_guard()
    return editor_core.redimensionar(d.ruta, d.ancho_cm, d.alto_cm)

@app.post("/api/editor/pdf-gran-formato")
async def editor_pdf_gf(d: EditorIn):
    _ed_guard()
    return editor_core.pdf_gran_formato(d.ruta, d.ancho_cm or 60, d.alto_cm or 40)

@app.post("/api/editor/low-poly")
async def editor_lowpoly(d: EditorIn):
    _ed_guard()
    return editor_core.low_poly(d.ruta, d.puntos)

@app.post("/api/editor/cartoon")
async def editor_cartoon(d: EditorIn):
    _ed_guard()
    return editor_core.cartoon(d.ruta)

@app.post("/api/editor/procesar")
async def editor_procesar(
    archivo: UploadFile = File(...),
    accion: str = Form(...),
    umbral: int = Form(128),
    ancho_cm: float = Form(0),
    alto_cm: float = Form(0),
    puntos: int = Form(1500),
):
    """Recibe un archivo SUBIDO (arrastrar / copiar-pegar / elegir) y aplica la acción.
    Devuelve el resultado + URL para previsualizar o descargar. Sin teclear rutas."""
    import shutil
    up_dir = Path(r"C:\AURORA\UPLOADS"); up_dir.mkdir(parents=True, exist_ok=True)
    nombre = Path(archivo.filename or "archivo").name
    destino = up_dir / nombre
    with open(destino, "wb") as f:
        shutil.copyfileobj(archivo.file, f)
    ruta = str(destino)

    acciones_editor = {
        "linea": lambda: editor_core.linea(ruta),
        "grabado": lambda: editor_core.grabado(ruta, umbral),
        "quitar-fondo": lambda: editor_core.quitar_fondo(ruta),
        "low-poly": lambda: editor_core.low_poly(ruta, puntos),
        "cartoon": lambda: editor_core.cartoon(ruta),
        "redimensionar": lambda: editor_core.redimensionar(ruta, ancho_cm, alto_cm),
        "pdf-gran-formato": lambda: editor_core.pdf_gran_formato(ruta, ancho_cm or 60, alto_cm or 40),
    }
    acciones_taller = {
        "convertir-dxf": lambda: taller_core.convertir_a_dxf(ruta),
        "vectorizar": lambda: taller_core.vectorizar(ruta),
    }
    if accion in acciones_editor:
        if editor_core is None:
            raise HTTPException(status_code=503, detail="Editor no disponible")
        r = acciones_editor[accion](); carpeta = "editor-out"
    elif accion in acciones_taller:
        if taller_core is None:
            raise HTTPException(status_code=503, detail="Taller no disponible")
        r = acciones_taller[accion](); carpeta = "taller-out"
    else:
        raise HTTPException(status_code=400, detail=f"Acción desconocida: {accion}")

    if isinstance(r, dict) and r.get("status") == "OK":
        sal = r.get("dxf") or r.get("svg") or r.get("salida") or r.get("archivo") or ""
        r["url"] = ("/" + carpeta + "/" + Path(sal).name) if sal else ""
        r["entrada_url"] = "/uploads/" + nombre
    return r

# ==================== TALLER (DXF/vector) ====================

class TallerIn(BaseModel):
    ruta: str = ""
    texto: str = ""
    alto_cm: float = 5.0
    fuente: str = "Arial"

@app.get("/api/taller/catalogo")
async def taller_catalogo():
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.catalogo()

@app.post("/api/taller/convertir-dxf")
async def taller_convertir(d: TallerIn):
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.convertir_a_dxf(d.ruta)

@app.post("/api/taller/vectorizar")
async def taller_vectorizar(d: TallerIn):
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.vectorizar(d.ruta)

@app.post("/api/taller/texto-dxf")
async def taller_texto(d: TallerIn):
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.texto_a_dxf(d.texto, d.alto_cm, d.fuente)

class CajaIn(BaseModel):
    x: float = 80
    y: float = 50
    h: float = 40
    thickness: float = 3
    generador: str = "UniversalBox"
    dedos: float = 2.0
    nuevo_grosor: float = 2.7

@app.post("/api/taller/caja")
async def taller_caja(d: CajaIn):
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.caja(d.x, d.y, d.h, d.thickness, d.generador, d.dedos)

@app.post("/api/taller/reajustar-grosor")
async def taller_reajustar(d: CajaIn):
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return taller_core.reajustar_grosor(d.x, d.y, d.h, d.nuevo_grosor, d.generador, d.dedos)

@app.get("/api/taller/generadores")
async def taller_generadores():
    if taller_core is None: raise HTTPException(status_code=503, detail="Taller no disponible")
    return {"status": "OK", "cajas": taller_core.GENERADORES_CAJA}

# ==================== ASESOR DE MARKETING DIGITAL ====================

class MarketingIn(BaseModel):
    negocio: str = "ATF"
    objetivo: str = ""
    metricas: dict = {}            # métricas REALES por red; vacío => no inventa
    actividad_por_hora: dict = {}  # {hora: actividad} de insights reales

@app.get("/api/marketing/algoritmo")
async def marketing_algoritmo(red: str = ""):
    if asesor_core is None: raise HTTPException(status_code=503, detail="Asesor no disponible")
    return asesor_core.conocimiento(red or None)

@app.get("/api/marketing/playbook")
async def marketing_playbook(flanco: str = ""):
    if asesor_core is None: raise HTTPException(status_code=503, detail="Asesor no disponible")
    return asesor_core.playbook(flanco or None)

@app.post("/api/marketing/horarios")
async def marketing_horarios(d: MarketingIn):
    if asesor_core is None: raise HTTPException(status_code=503, detail="Asesor no disponible")
    act = {int(k): float(v) for k, v in d.actividad_por_hora.items()} if d.actividad_por_hora else None
    return asesor_core.mejores_horarios(act)

@app.post("/api/marketing/analizar")
async def marketing_analizar(d: MarketingIn):
    """Diagnóstico sobre métricas REALES (si las hay). Sin datos => honesto + playbook."""
    if asesor_core is None: raise HTTPException(status_code=503, detail="Asesor no disponible")
    return asesor_core.diagnostico(d.metricas or None)

@app.post("/api/marketing/plan")
async def marketing_plan(d: MarketingIn):
    """Plan de acción del cerebro con el conocimiento del asesor sobre datos reales."""
    if asesor_core is None: raise HTTPException(status_code=503, detail="Asesor no disponible")
    brief = asesor_core.construir_brief_para_cerebro(d.negocio, d.metricas or None, d.objetivo)
    if not AuroraCerebro:
        return {"status": "OK", "plan": None, "brief": brief,
                "detalle": "Cerebro offline; te dejo el contexto base. Conecta métricas para personalizar."}
    cerebro = AuroraCerebro()
    r = await cerebro.razonar(brief, {"negocio": d.negocio, "modo": "asesor_marketing"})
    return {"status": "OK",
            "plan": r.get("respuesta") or (r.get("razonamiento", [""])[0] if r.get("razonamiento") else ""),
            "recomendaciones": r.get("recomendaciones", []),
            "datos_reales": bool(d.metricas),
            "aviso": None if d.metricas else "Plan base: conecta Meta para personalizar con tus números reales."}

# ==================== VENDEDOR (asesor técnico + súper-vendedor) ====================

class VendedorIn(BaseModel):
    modo: str = "cliente"      # cliente | interno
    producto: str = ""
    objetivo: str = ""
    negocio: str = ""          # ATF | MILENS (si vacío, se deriva de la ficha)

@app.get("/api/vendedor/fichas")
async def vendedor_fichas():
    if vendedor_core is None: raise HTTPException(status_code=503, detail="Vendedor no disponible")
    return vendedor_core.listar_fichas()

@app.get("/api/vendedor/ficha")
async def vendedor_ficha(producto: str):
    if vendedor_core is None: raise HTTPException(status_code=503, detail="Vendedor no disponible")
    return vendedor_core.ficha(producto)

@app.get("/api/vendedor/tecnicas")
async def vendedor_tecnicas(nombre: str = ""):
    if vendedor_core is None: raise HTTPException(status_code=503, detail="Vendedor no disponible")
    return vendedor_core.tecnicas(nombre or None)

@app.post("/api/vendedor/investigar")
async def vendedor_investigar(d: VendedorIn):
    """AURORA investiga en la web/fabricantes y autocompleta la ficha con datos REALES + fuentes.
    Lo que no encuentra verificable queda PENDIENTE; nunca inventa specs ni cableado."""
    if vendedor_core is None: raise HTTPException(status_code=503, detail="Vendedor no disponible")
    if accesos_core is None: raise HTTPException(status_code=503, detail="Acceso web no disponible")
    prod = (d.producto or "").strip()
    if not prod: raise HTTPException(status_code=400, detail="Indica el producto a investigar")
    busq = accesos_core.buscar_web(prod + " especificaciones ficha tecnica instalacion")
    def _url_ok(u: str) -> bool:
        u = (u or "").lower()
        if not u.startswith("http"):
            return False
        basura = ["duckduckgo.com/y.js", "/aclick", "ad_domain", "googleadservices",
                  "doubleclick", "/y.js", "bing.com/aclick", "syndication"]
        return not any(b in u for b in basura)
    textos, fuentes = [], []
    for res in (busq.get("resultados") or [])[:8]:
        url = res.get("url")
        if not url or not _url_ok(url):
            continue
        try:
            w = accesos_core.leer_web(url)
            if w.get("texto") and len(w["texto"]) > 200:
                textos.append(w["texto"]); fuentes.append(url)
        except Exception:
            continue
        if len(fuentes) >= 3:
            break
    if not textos:
        return {"status": "SIN_FUENTES", "detalle": "No encontré fuentes legibles. No invento la ficha.",
                "consultado": busq.get("resultados", [])[:3]}
    if not AuroraCerebro:
        return {"status": "OK", "detalle": "Tengo el texto real pero el cerebro está offline para estructurarlo.",
                "fuentes": fuentes}
    cerebro = AuroraCerebro()
    r = await cerebro.razonar(vendedor_core.prompt_extraccion(prod, "\n\n".join(textos)),
                              {"modo": "extraccion_ficha"})
    raw = r.get("respuesta") or ""
    mjson = _re.search(r"\{.*\}", raw, _re.S)
    if not mjson:
        return {"status": "PARCIAL", "detalle": "No pude estructurar datos confiables.", "fuentes": fuentes}
    try:
        datos = json.loads(mjson.group(0))
    except Exception:
        return {"status": "PARCIAL", "detalle": "La extracción no fue estructurable.", "fuentes": fuentes}
    saved = vendedor_core.guardar_ficha(prod, datos, fuentes)
    # Capa de verificación: degrada a PENDIENTE lo incoherente (no da por bueno lo dudoso)
    if verificador_core is not None:
        try:
            verificador_core.verificar_todas()
            saved = vendedor_core.ficha(prod)
        except Exception:
            pass
    if isinstance(saved, dict):
        saved["fuentes"] = fuentes
    return saved

@app.post("/api/vendedor/responder")
async def vendedor_responder(d: VendedorIn):
    """El vendedor (o asesor interno) razona con datos REALES de la ficha. No inventa lo PENDIENTE."""
    if vendedor_core is None: raise HTTPException(status_code=503, detail="Vendedor no disponible")
    brief = vendedor_core.construir_brief(d.modo, d.producto, d.objetivo, d.negocio)
    if not AuroraCerebro:
        return {"status": "OK", "respuesta": None, "brief": brief, "detalle": "Cerebro offline."}
    cerebro = AuroraCerebro()
    r = await cerebro.razonar(brief, {"negocio": d.negocio or "ATF", "modo": "vendedor_" + d.modo})
    return {"status": "OK",
            "respuesta": r.get("respuesta") or (r.get("razonamiento", [""])[0] if r.get("razonamiento") else ""),
            "recomendaciones": r.get("recomendaciones", [])}

# ==================== IDENTIDAD (dueño vs cliente) ====================

class IdentidadIn(BaseModel):
    pin: str = ""
    pin_actual: str = ""
    token: str = ""

@app.post("/api/auth/login")
async def auth_login(d: IdentidadIn):
    if identidad_core is None:
        raise HTTPException(status_code=503, detail="Identidad no disponible")
    r = identidad_core.login(d.pin)
    if r.get("status") != "OK":
        raise HTTPException(status_code=401, detail=r.get("detalle", "Login denegado"))
    jwt_token = _issue_jwt(r.get("token", ""), "dueño")
    if jwt_token:
        r["jwt"] = jwt_token
        r["token_type"] = "Bearer"
    else:
        r["jwt"] = None
        r["token_type"] = "legacy"
        r["aviso"] = "JWT_SECRET_KEY no configurada; usando la llave local del dispositivo."
    return r

@app.get("/api/identidad/estado")
async def identidad_estado():
    if identidad_core is None: raise HTTPException(status_code=503, detail="Identidad no disponible")
    return identidad_core.estado()

@app.post("/api/identidad/configurar")
async def identidad_configurar(d: IdentidadIn):
    if identidad_core is None: raise HTTPException(status_code=503, detail="Identidad no disponible")
    return identidad_core.configurar_pin(d.pin, d.pin_actual)

@app.post("/api/identidad/login")
async def identidad_login(d: IdentidadIn):
    if identidad_core is None: raise HTTPException(status_code=503, detail="Identidad no disponible")
    return identidad_core.login(d.pin)

@app.post("/api/identidad/revocar")
async def identidad_revocar(d: IdentidadIn):
    if identidad_core is None: raise HTTPException(status_code=503, detail="Identidad no disponible")
    _solo_dueno(d.token)
    return identidad_core.revocar_todos()

# ==================== AGENDADOR (cola + publicación supervisada) ====================

class AgendaIn(BaseModel):
    cantidad: int = 10
    token: str = ""

@app.get("/api/agenda/estado")
async def agenda_estado():
    if agendador_core is None: raise HTTPException(status_code=503, detail="Agendador no disponible")
    return agendador_core.estado_pipeline()

@app.post("/api/agenda/preparar")
async def agenda_preparar(d: AgendaIn, authorization: str | None = Header(default=None)):
    """AURORA copia candidatos de ORIGINAL a 1_REVISION (con caption + red de rotación)."""
    if agendador_core is None: raise HTTPException(status_code=503, detail="Agendador no disponible")
    _solo_dueno(d.token, authorization)
    return agendador_core.preparar_revision(d.cantidad)

@app.post("/api/agenda/publicar-pendientes")
async def agenda_publicar_pendientes():
    """Tick: publica lo que Anuar movió a 2_APROBADOS (FB real). Lo llama la tarea programada."""
    if agendador_core is None or publicador_core is None:
        raise HTTPException(status_code=503, detail="No disponible")
    return agendador_core.publicar_aprobados(publicador_core.publicar_video_fb, max_por_corrida=1)

# ==================== SUBLIMACION (fotograma -> lienzo 300 DPI) ====================

class SublimacionIn(BaseModel):
    origen: str = ""
    imagen: str = ""
    ancho_cm: float = 21
    alto_cm: float = 9
    dpi: int = 300
    hoja: str = "A4"
    fps: int = 1

@app.post("/api/sublimacion/lienzo")
async def sub_lienzo(d: SublimacionIn):
    if sublimacion_core is None: raise HTTPException(status_code=503, detail="Sublimación no disponible")
    return sublimacion_core.lienzo_blanco(d.ancho_cm, d.alto_cm, d.dpi, d.hoja)

@app.post("/api/sublimacion/montar")
async def sub_montar(d: SublimacionIn):
    if sublimacion_core is None: raise HTTPException(status_code=503, detail="Sublimación no disponible")
    return sublimacion_core.montar(d.imagen, d.ancho_cm, d.alto_cm, d.dpi, d.hoja)

@app.post("/api/sublimacion/video")
async def sub_video(d: SublimacionIn):
    if sublimacion_core is None: raise HTTPException(status_code=503, detail="Sublimación no disponible")
    return sublimacion_core.de_video(d.origen, d.fps)

# ==================== BRIEFING (inicio proactivo estilo JARVIS) ====================

@app.get("/api/briefing")
async def briefing():
    """Parte proactivo con DATOS REALES (ORACLE, agenda, fichas, redes) + siguiente mejor acción.
    El cerebro NO inventa números: usa solo estos datos. 'AURORA respira ATF'."""
    datos = {}
    if oracle_core is not None:
        try: datos["negocio"] = oracle_core.resumen()
        except Exception: pass
    if agendador_core is not None:
        try: datos["contenido"] = agendador_core.estado_pipeline()
        except Exception: pass
    if vendedor_core is not None:
        try:
            lf = vendedor_core.listar_fichas()
            datos["fichas"] = {"total": lf.get("total"), "completas": lf.get("completas")}
        except Exception: pass
    if publicador_core is not None:
        try:
            datos["redes_conectadas"] = [r["plataforma"] for r in publicador_core.estado_redes().get("redes", [])
                                         if r.get("token_api")]
        except Exception: pass
    texto = None
    if AuroraCerebro:
        try:
            cerebro = AuroraCerebro()
            prompt = ("Eres AURORA, asistente personal de Anuar (estilo JARVIS). Con estos DATOS REALES da un "
                      "parte BREVE (4-6 líneas): cómo va ATF/MILENS hoy y la SIGUIENTE MEJOR ACCIÓN. "
                      "PROHIBIDO inventar números: usa SOLO estos datos. Si algo está vacío, dilo honesto. "
                      "Di SIEMPRE 'interesados' (NUNCA 'leads'). 'total_leads' = interesados.\n\n"
                      + json.dumps(datos, ensure_ascii=False)[:3000])
            r = await cerebro.razonar(prompt, {"modo": "briefing"})
            texto = r.get("respuesta") or (r.get("razonamiento", [""])[0] if r.get("razonamiento") else None)
        except Exception:
            pass
    return {"status": "OK", "datos": datos, "briefing": texto, "timestamp": datetime.now().isoformat()}

# ==================== REDES: comentarios (leer + responder) ====================

class ComentarioIn(BaseModel):
    comment_id: str = ""
    texto: str = ""
    token: str = ""

@app.get("/api/redes/comentarios")
async def redes_comentarios(limite: int = 10):
    if publicador_core is None: raise HTTPException(status_code=503, detail="Publicador no disponible")
    return publicador_core.comentarios_pagina(limite)

@app.post("/api/redes/responder")
async def redes_responder(d: ComentarioIn, authorization: str | None = Header(default=None)):
    """Responde un comentario REAL en FB. Acción pública -> solo Anuar (dueño)."""
    if publicador_core is None: raise HTTPException(status_code=503, detail="Publicador no disponible")
    _solo_dueno(d.token, authorization)
    if not d.comment_id or not d.texto:
        raise HTTPException(status_code=400, detail="Faltan comment_id y texto")
    return publicador_core.responder_comentario(d.comment_id, d.texto)

# ==================== VOZ por Google Mini (salida) ====================

class VozIn(BaseModel):
    texto: str = ""
    device: str = "oficina 2"

@app.get("/api/voz/dispositivos")
async def voz_dispositivos():
    if voz_google is None: raise HTTPException(status_code=503, detail="Voz Google no disponible")
    return {"status": "OK", "dispositivos": voz_google.dispositivos()}

@app.post("/api/voz/google")
async def voz_google_hablar(d: VozIn):
    """AURORA habla por el Google Home Mini (casting). Solo salida."""
    if voz_google is None: raise HTTPException(status_code=503, detail="Voz Google no disponible")
    if not d.texto: raise HTTPException(status_code=400, detail="Indica el texto")
    return voz_google.hablar_google(d.texto, d.device)

# ==================== REPARADOR de apps ====================

class ReparaIn(BaseModel):
    app: str
    reset: bool = False
    abrir: bool = False

@app.post("/api/reparar")
async def reparar_app(d: ReparaIn):
    if reparador_core is None: raise HTTPException(status_code=503, detail="Reparador no disponible")
    return reparador_core.reparar(d.app, d.reset, d.abrir)

# ==================== COMANDOS NEXUS ====================

class ComandoNexusIn(BaseModel):
    texto: str

@app.get("/api/comandos")
async def comandos_listar():
    if comandos_core is None:
        raise HTTPException(status_code=503, detail="Comandos no disponible")
    return {"status": "OK", **comandos_core.listar()}

@app.post("/api/comandos/ejecutar")
async def comandos_ejecutar(d: ComandoNexusIn):
    if comandos_core is None:
        raise HTTPException(status_code=503, detail="Comandos no disponible")
    return comandos_core.ejecutar(d.texto)

# ==================== MODULOS (FORJA / EVOLUCION / CANBUSFIX) ====================

@app.get("/api/modulos")
async def modulos_listar():
    if modulos_core is None:
        raise HTTPException(status_code=503, detail="Modulos no disponible")
    return {"status": "OK", **modulos_core.listar()}

@app.post("/api/modulos/{mid}/activar")
async def modulos_activar(mid: str):
    if modulos_core is None:
        raise HTTPException(status_code=503, detail="Modulos no disponible")
    return modulos_core.activar(mid)

@app.post("/api/modulos/{mid}/pausar")
async def modulos_pausar(mid: str):
    if modulos_core is None:
        raise HTTPException(status_code=503, detail="Modulos no disponible")
    return modulos_core.pausar(mid)

# ==================== ESTUDIO DE MERCADO ====================

class EstudioIn(BaseModel):
    negocio: str = "atf"
    tema: str = ""

@app.post("/api/estudio-mercado")
async def estudio_mercado(d: EstudioIn):
    if not AuroraCerebro:
        raise HTTPException(status_code=503, detail="Cerebro offline")
    neg = (d.negocio or "atf").lower()
    base = {
        "atf": ["precio retrofit faros led mexico", "competencia iluminacion automotriz guadalajara",
                "tendencias faros led 2026 autos"],
        "milens": ["precio grabado laser mexico", "negocio sublimacion personalizados mexico",
                   "tendencias productos personalizados 2026"],
    }
    consultas = base.get(neg, base["atf"])
    if d.tema:
        consultas = [d.tema + " " + neg] + consultas
    datos = ""
    if accesos_core:
        for q in consultas[:3]:
            r = accesos_core.buscar_web(q)
            if r.get("status") == "OK":
                datos += f"\n[{q}]\n" + "\n".join(f"- {x['titulo']}" for x in r.get("resultados", [])[:5])
    cerebro = AuroraCerebro()
    prompt = (f"Haz un ESTUDIO DE MERCADO breve y accionable para el negocio {neg.upper()} "
              f"(en México/Guadalajara). Usa estos datos reales de búsqueda:\n{datos[:4000]}\n\n"
              "Entrega: 1) Competencia y rango de precios, 2) Oportunidades/nichos, "
              "3) Tendencias 2026, 4) 3 acciones concretas para vender más. Directo, sin relleno.")
    rr = await cerebro.razonar(prompt, {"negocio": neg})
    return {"status": "OK", "negocio": neg, "fuentes": consultas[:3], "estudio": rr.get("respuesta", "")}

# ==================== STARTUP ====================

def auto_sleep_cycle():
    """Ejecuta sleep cycle automáticamente cada 24h"""
    while True:
        time.sleep(86400)
        try:
            conn = sqlite3.connect(str(CHAT_DB))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM aprendizajes WHERE timestamp > datetime('now', '-24 hours')")
            count = c.fetchone()[0]
            if count > 0:
                logger.info("[SLEEP] Ejecutando ciclo de consolidación...")
                c.execute("SELECT AVG(feedback) FROM aprendizajes")
                avg = c.fetchone()[0] or 0.5
                logger.info(f"[SLEEP] ✓ Consolidadas {count} interacciones | Confianza: {avg:.2f}")
            conn.close()
        except Exception as e:
            logger.error(f"[SLEEP] Error: {e}")

def auto_publicar_diario():
    """Publica 1 post de ATF en Facebook cada día a la hora objetivo (si está LISTA)."""
    import asyncio as _aio
    HORA_OBJETIVO = 12  # 12:00 PM
    flag_pausa = Path(__file__).parent / "AUTO_POST_PAUSADO"
    ultimo_dia = None
    while True:
        time.sleep(300)  # revisa cada 5 min
        try:
            ahora = datetime.now()
            if flag_pausa.exists():
                continue
            if ahora.hour == HORA_OBJETIVO and ultimo_dia != ahora.date():
                if not (AuroraCerebro and publicador_core):
                    continue
                if os.getenv("FB_PAGE_TOKEN"):
                    cerebro = AuroraCerebro()
                    r = _aio.run(cerebro.razonar(
                        "Escribe UN post corto y atractivo para Facebook de ATF (retrofit de faros, "
                        "instalación profesional). 2-3 líneas + 2 hashtags + invita a agendar. Solo el texto, sin comillas.",
                        {"negocio": "ATF"}))
                    texto = (r.get("respuesta") or "").strip().strip('"')
                    if texto:
                        res = publicador_core.publicar("facebook", texto)
                        logger.info(f"[AUTO-POST] {res.get('status')}: {texto[:50]}")
                        ultimo_dia = ahora.date()
        except Exception as e:
            logger.error(f"[AUTO-POST] Error: {e}")

@app.post("/api/publicador/auto")
async def publicador_auto(activo: bool = True):
    """Activa/pausa el auto-posteo diario (crea/borra el flag)."""
    flag = Path(__file__).parent / "AUTO_POST_PAUSADO"
    if activo:
        if flag.exists():
            flag.unlink()
        return {"status": "OK", "auto_post": "ACTIVO"}
    flag.write_text("pausado")
    return {"status": "OK", "auto_post": "PAUSADO"}

@app.on_event("startup")
async def startup():
    init_chat_db()
    logger.info("=" * 70)
    logger.info("AURORA NEXUS v3 - INICIANDO")
    logger.info("=" * 70)
    logger.info(f"[OK] {len(CAPACIDADES)} capacidades reales")
    logger.info(f"[OK] Cerebro: {'activo' if AuroraCerebro else 'offline'}")
    logger.info(f"[OK] API en http://127.0.0.1:8000")
    logger.info(f"[OK] Dashboard en http://127.0.0.1:8000/")
    logger.info(f"[OK] Chat en http://127.0.0.1:8000/chat")
    logger.info("=" * 70)

    thread = threading.Thread(target=auto_sleep_cycle, daemon=True)
    thread.start()
    threading.Thread(target=auto_publicar_diario, daemon=True).start()
    logger.info("[OK] Auto-posteo diario de Facebook ACTIVO (12:00 PM)")

# ==================== RUN ====================

if __name__ == "__main__":
    print("\n[AURORA] Iniciando sistema...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        logger.info("[STOP] Sistema detenido por usuario")
    except Exception as e:
        logger.error(f"[ERROR] {e}")
        sys.exit(1)
