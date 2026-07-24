# 🔐 PROMPT MAESTRO 01: SEGURIDAD QUIRÚRGICA
## Para AI IDE (Claude, Copilot Code, etc.)

### CONTEXTO
- Proyecto: AURORA - Sistema de Marketing IA
- Estado actual: 6.5/10, credenciales expuestas
- Objetivo: Implementar seguridad de producción en 45 minutos
- Alcance: TODO el folder C:\AURORA

---

## 📋 TAREA PRINCIPAL

Implementa seguridad de PRODUCCIÓN en AURORA ejecutando estos pasos EN PARALELO:

### PASO 1: ARCHIVO .ENV (10 min)

**Crear archivo**: `C:\AURORA\.env.example`

```
# GROQ API
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=mixtral-8x7b-32768

# GREEN-API (WhatsApp)
GREEN_API_INSTANCE_ID=7107622171
GREEN_API_TOKEN=your_green_api_token_here

# FACEBOOK/INSTAGRAM
FACEBOOK_ACCESS_TOKEN=your_facebook_token_here
FACEBOOK_PAGE_ID=your_page_id_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id_here

# META BUSINESS (Ads)
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_BUSINESS_ACCOUNT_ID=your_business_id_here

# TIKTOK
TIKTOK_ACCESS_TOKEN=your_tiktok_token_here
TIKTOK_BUSINESS_ACCOUNT_ID=your_account_id_here

# DATABASE
DB_PATH=C:\\AURORA\\SUPER_MARKETING_SYSTEM\\analytics\\marketing.db
DB_BACKUP_PATH=C:\\AURORA\\BACKUPS\\

# JWT SECURITY
JWT_SECRET_KEY=your_super_secure_random_key_here_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# SERVER
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=5000
FASTAPI_LOG_LEVEL=info
FASTAPI_ENV=production

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=C:\\AURORA\\LOGS\\aurora.log
LOG_MAX_SIZE=50MB
LOG_BACKUP_COUNT=5

# SEGURIDAD
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:5000"]
```

**Crear archivo**: `C:\AURORA\.env` (para desarrollo local)
- Copiar .env.example
- Reemplazar valores con credenciales REALES

**Crear archivo**: `C:\AURORA\.gitignore` (agregar)
```
.env
.env.local
*.pyc
__pycache__/
.pytest_cache/
.coverage
*.db
*.log
/venv/
/dist/
/build/
```

---

### PASO 2: CARGAR .ENV EN CÓDIGO (15 min)

**Crear archivo**: `C:\AURORA\config.py`

```python
# -*- coding: utf-8 -*-
"""
Configuración centralizada de AURORA
Carga variables de .env y las valida
"""
from pydantic import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Configuración con validación"""
    
    # GROQ
    groq_api_key: str
    groq_model: str = "mixtral-8x7b-32768"
    
    # GREEN-API
    green_api_instance_id: str
    green_api_token: str
    
    # FACEBOOK
    facebook_access_token: str
    facebook_page_id: str
    instagram_business_account_id: str
    
    # META
    meta_app_id: str
    meta_app_secret: str
    meta_business_account_id: str
    
    # TIKTOK
    tiktok_access_token: str
    tiktok_business_account_id: str
    
    # DATABASE
    db_path: str = r"C:\AURORA\SUPER_MARKETING_SYSTEM\analytics\marketing.db"
    db_backup_path: str = r"C:\AURORA\BACKUPS"
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # SERVER
    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 5000
    fastapi_log_level: str = "info"
    fastapi_env: str = "development"
    
    # LOGGING
    log_level: str = "INFO"
    log_file: str = r"C:\AURORA\LOGS\aurora.log"
    log_max_size: str = "50MB"
    
    # RATE LIMITING
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_cors: bool = True
    cors_origins: List[str] = ["http://localhost:5000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instancia global
settings = Settings()

# Validar que las credenciales estén configuradas
def validate_settings():
    """Valida que todas las credenciales estén configuradas"""
    required_fields = [
        "groq_api_key",
        "green_api_instance_id",
        "green_api_token",
        "jwt_secret_key"
    ]
    
    for field in required_fields:
        value = getattr(settings, field, None)
        if not value or value.startswith("your_"):
            raise ValueError(f"❌ Configuración incompleta: {field} no está definido en .env")
    
    print("✅ Configuración validada correctamente")

if __name__ == "__main__":
    validate_settings()
```

---

### PASO 3: SEGURIDAD EN API (15 min)

**REEMPLAZAR** en `C:\AURORA\SUPER_MARKETING_SYSTEM\api_v3.py`:

```python
# -*- coding: utf-8 -*-
"""API v3 de AURORA — Servidor FastAPI con Green-API y Seguridad."""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import sys
import os
from pathlib import Path
import logging

# Config
RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "CEREBRO"))
sys.path.insert(0, str(RAIZ))

from config import settings
from config import validate_settings

# Validar config al startup
validate_settings()

# Logger
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("AURORA_API")

# FastAPI app
app = FastAPI(
    title="AURORA v3 WHATSAPP ENGINE",
    version="4.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security = HTTPBearer()

class MensajePayload(BaseModel):
    texto: str
    usuario_id: str

class TokenPayload(BaseModel):
    token: str

def verify_jwt_token(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """Verifica JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        usuario_id = payload.get("sub")
        if usuario_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"usuario_id": usuario_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def create_jwt_token(usuario_id: str, expires_delta: timedelta = None) -> str:
    """Crea JWT token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": usuario_id, "exp": expire}
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

@app.post("/api/auth/login")
async def login(usuario_id: str):
    """Obtener JWT token"""
    token = create_jwt_token(usuario_id)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/mensaje")
async def procesar_mensaje(
    payload: MensajePayload,
    token_user: dict = Depends(verify_jwt_token)
):
    """Procesar mensaje (requiere autenticación)"""
    try:
        logger.info(f"📨 Mensaje recibido: {payload.texto}")
        # Aquí va la lógica de procesamiento
        return {"status": "ok", "respuesta": "Mensaje procesado"}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status(token_user: dict = Depends(verify_jwt_token)):
    """Estado del sistema (requiere autenticación)"""
    return {
        "status": "🟢 ONLINE",
        "version": "4.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "status": "🟢 ONLINE",
        "mensaje": "Aurora v4 operando",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando Aurora API...")
    uvicorn.run(
        app,
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        log_level=settings.fastapi_log_level
    )
```

---

### PASO 4: REEMPLAZAR TOKENS EN CÓDIGO (10 min)

**EN TODOS LOS ARCHIVOS .py:**

Buscar y reemplazar:

```python
# ANTES (INSEGURO):
inst = "7107622171"
tok = "d9dc6f6f2f5944888d313b3148a93a2d85b48b59b18e4c15ba"
GROQ_API_KEY = "gsk_xxxxxxxxxxxxx"
FACEBOOK_TOKEN = "EAAB..."

# DESPUÉS (SEGURO):
from config import settings

inst = settings.green_api_instance_id
tok = settings.green_api_token
GROQ_API_KEY = settings.groq_api_key
FACEBOOK_TOKEN = settings.facebook_access_token
```

---

### PASO 5: REQUIREMENTS.txt (5 min)

**Crear/Actualizar**: `C:\AURORA\requirements.txt`

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose==3.3.0
PyJWT==2.8.1
requests==2.31.0
aiohttp==3.9.1
sqlalchemy==2.0.23
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

---

## ✅ VALIDACIÓN

Al terminar, ejecuta:

```bash
python -c "from config import settings; settings.validate_settings(); print('✅ Todas las credenciales OK')"
```

---

## 🎯 TIEMPO ESTIMADO
- PASO 1: 10 min
- PASO 2: 15 min
- PASO 3: 15 min
- PASO 4: 10 min
- PASO 5: 5 min
- **TOTAL: 45 minutos**

---

## 📊 RESULTADO
✅ .env creado y configurado
✅ Todas las credenciales externalizado
✅ JWT implementado en api_v3.py
✅ Rate limiting listo
✅ .gitignore protege secrets
✅ Config centralizada en config.py
✅ 0 credenciales en código
