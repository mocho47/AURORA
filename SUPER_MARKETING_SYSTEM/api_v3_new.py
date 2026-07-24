# -*- coding: utf-8 -*-
"""
🚀 AURORA API v3 - WHATSAPP ENGINE + PUBLICADOR + CORE UNIFICADO
API de producción libre de simulaciones. Conexión directa con submódulos reales.
Versión Unificada y Optimizada (2026).
"""
import sys
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

import jwt
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ─── CONFIGURACIÓN DE RUTAS Y ENTORNO ────────────────────────────────────────
RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ))

# Inyección de rutas de submódulos para empaquetado seguro
sys.path.insert(0, str(RAIZ.parent / "CEREBRO"))
sys.path.insert(0, str(RAIZ.parent / "ORACLE"))
sys.path.insert(0, str(RAIZ.parent / "VENDEDOR"))

try:
    from config import settings, validate_production_settings
    from aurora_cerebro_simple import AuroraCerebro
    import oracle_core
    import vendedor_core
except ModuleNotFoundError:
    # Fallback por si las rutas están un nivel arriba
    sys.path.insert(0, str(RAIZ.parent))
    from config import settings, validate_production_settings
    from aurora_cerebro_simple import AuroraCerebro
    import oracle_core
    import vendedor_core

# Validar configuraciones de producción e inicializar logs
validate_production_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("AURORA_API")

# ─── INICIALIZACIÓN DE FASTAPI ──────────────────────────────────────────────
app = FastAPI(
    title="🚀 AURORA + NEXUS v3 UNIFIED",
    version="3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Inicializar instancia única del cerebro real con el motor de IA
cerebro_ia = AuroraCerebro() if 'AuroraCerebro' in globals() else None

# Configuración de CORS basada en los ajustes del sistema
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ─── SCHEMAS Y MODELOS DE PETICIÓN (PYDANTIC) ───────────────────────────────
class LoginPayload(BaseModel):
    usuario_id: str
    password: str

class MensajePayload(BaseModel):
    texto: str
    usuario_id: str
    chat_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class CotizacionIn(BaseModel):
    modelo: str  # X1, X2, X3, X4, X5, X6, X7
    incluye_instalacion: bool = True
    incluye_iva: bool = True

# ─── SEGURIDAD Y CONTROL DE TOKENS JWT ──────────────────────────────────────
def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"usuario_id": usuario_id, "exp": payload.get("exp")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

def create_jwt_token(usuario_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    payload = {"sub": usuario_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

# ─── CRM - BASE DE DATOS LOCAL SQLITE ───────────────────────────────────────
_CRM_DB = Path(__file__).parent.parent / "aurora_crm.db"

def _db():
    conn = sqlite3.connect(str(_CRM_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _init_crm():
    with _db() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT DEFAULT '',
                email TEXT DEFAULT '',
                direccion TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                fecha_alta TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE,
                cliente_id INTEGER REFERENCES clientes(id),
                descripcion TEXT NOT NULL,
                costo_total REAL DEFAULT 0,
                anticipo REAL DEFAULT 0,
                estado TEXT DEFAULT 'PENDIENTE',
                semaforo TEXT DEFAULT 'ROJO',
                fecha_entrada TEXT DEFAULT (datetime('now','localtime')),
                fecha_entrega_est TEXT DEFAULT '',
                fecha_terminado TEXT DEFAULT '',
                notas TEXT DEFAULT ''
            );
        """)

@app.on_event("startup")
async def startup():
    _init_crm()
    if oracle_core:
        oracle_core.init_db()
    logger.info("=== API UNIFICADA OPERATIVA ===")

# ─── ENDPOINTS PRINCIPALES (SISTEMA REAL) ───────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: LoginPayload):
    if credentials.usuario_id == "admin" and credentials.password == "admin":  
        token = create_jwt_token(credentials.usuario_id)
        return TokenResponse(access_token=token, expires_in=settings.jwt_expiration_hours * 3600)
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@app.post("/api/mensaje")
async def procesar_mensaje(payload: MensajePayload, token_user: Dict = Depends(verify_jwt)):
    """CEREBRO REAL: Envía las peticiones al motor de IA configurado"""
    if not cerebro_ia:
        raise HTTPException(status_code=503, detail="Cerebro AURORA no inicializado")
    try:
        respuesta = cerebro_ia.procesar_mensaje_real(payload.texto)
        return {
            "status": "ok",
            "respuesta": respuesta,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error en motor IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en Cerebro IA: {str(e)}")

# ─── ENDPOINTS DEL PANEL (ORACLE + VENDEDOR) ───────────────────────────────

@app.get("/api/oracle/leads")
async def listar_leads(token_user: Dict = Depends(verify_jwt)):
    """ORACLE CAPTACIÓN: Extrae datos directos de clientes"""
    with _db() as c:
        rows = c.execute("SELECT * FROM clientes ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/operacion/cotizar")
async def cotizar_producto(payload: CotizacionIn, token_user: Dict = Depends(verify_jwt)):
    """COTIZADOR REAL: Precios exactos de fichas técnicas ILUME/ATF X1-X7"""
    try:
        resultado = vendedor_core.calcular_precio_detallado(
            modelo=payload.modelo,
            instalacion=payload.incluye_instalacion,
            iva=payload.incluye_iva
        )
        return {"status": "ok", "cotizacion": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en cotizador: {str(e)}")

@app.get("/api/oracle/ordenes")
async def listar_ordenes_taller(token_user: Dict = Depends(verify_jwt)):
    """ORACLE TALLER: Listado dinámico con estado de semáforos para el panel"""
    with _db() as c:
        rows = c.execute("""
            SELECT o.*, c.nombre as cliente_nombre 
            FROM ordenes_trabajo o 
            JOIN clientes c ON o.cliente_id = c.id 
            ORDER BY o.id DESC
        """).fetchall()
        return [dict(r) for r in rows]

# ─── MONTAJE DEL DASHBOARD (FRONT-END PANEL) UNIFICADO ──────────────────────
try:
    from dashboard import dashboard as db_mod
    
    # 1. Ruta base raíz del panel
    @app.get("/dashboard/")
    async def serve_dashboard_root():
        return HTMLResponse(content=db_mod.crear_dashboard_html())
    
    # 2. Montaje de archivos estáticos y sub-rutas del panel frontal
    app.mount("/dashboard", db_mod.app)
    logger.info("👉 Panel Dashboard montado en /dashboard")
except Exception as e:
    logger.warning(f"⚠️ No se pudo montar el Dashboard: {str(e)}")
