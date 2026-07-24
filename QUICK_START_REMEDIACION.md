# 🚀 AURORA AUDIT - QUICK START GUIDE

**Generado**: 2026-06-25  
**Para**: Implementación inmediata de remediaciones  

---

## 🔴 ACCIONES CRÍTICAS (HOY - 10 HORAS)

### 1. CAMBIAR CREDENCIALES (2 horas)

#### Paso 1.1: Groq
```bash
# Ir a: https://console.groq.com/
# 1. Settings → API Keys
# 2. "Delete" la clave actual (gsk_sDFWQhitHp...)
# 3. "Create New Secret Key"
# 4. Copiar nueva clave
# 5. GUARDAR en lugar seguro (no en .env aún)
```

#### Paso 1.2: Green API (WhatsApp)
```bash
# Ir a: https://app.greenapi.com/
# 1. Account → API Tokens
# 2. Regenerar token (d9dc6f6f2f59...)
# 3. Cambiar instance_id si es necesario
# 4. Validar que WhatsApp siga funcionando
```

#### Paso 1.3: Facebook
```bash
# Ir a: https://developers.facebook.com/
# 1. Settings → API Access Tokens
# 2. Regenerar token de página (EAAe3T5...)
# 3. Validar acceso a página
```

#### Paso 1.4: Instagram
```bash
# Ir a: https://www.instagram.com/accounts/login/
# 1. Settings → Apps and Websites
# 2. Regenerar token de acceso (EAAe3T5...)
# 3. Validar que publicaciones funcionen
```

**Verificación**:
```bash
# Después de cambiar, probar que funciona:
curl -X GET "https://api.groq.com/openai/v1/models" \
  -H "Authorization: Bearer NEW_KEY"
  
# Si retorna 200 OK → ✅ Funcionando
```

---

### 2. CREAR .env.example (30 min)

```bash
# C:\AURORA\.env.example (CREAR NUEVO)
# NUNCA COMITEAR - Este es el TEMPLATE

GROQ_API_KEY=your_groq_api_key_here
GREEN_API_INSTANCE=7107622171
GREEN_API_TOKEN=your_green_api_token_here
GREEN_API_SERVER=7107
FB_PAGE_ID=110364004632197
FB_PAGE_TOKEN=your_fb_page_token_here
INSTAGRAM_USER_ID=17841477357180920
INSTAGRAM_ACCESS_TOKEN=your_instagram_token_here

# Ejemplo para desarrollo
# Copiar este archivo a .env y reemplazar valores
```

**Comando**:
```bash
# Desde C:\AURORA\
cp .env.example .env  # En desarrollo, usar .env.example como base
```

---

### 3. ACTUALIZAR .gitignore (15 min)

```bash
# C:\AURORA\.gitignore (AGREGAR)

# Credenciales - NUNCA COMITEAR
.env
.env.local
.env.*.local

# Bases de datos
*.db
*.sqlite
*.sqlite3

# Logs
LOGS/
logs/
*.log

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.Python
venv/
env/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**Verificar**:
```bash
git status  # NO debe mostrar .env
```

---

### 4. LIMPIAR BACKUPS (30 min)

```bash
# Eliminar .env de todos los backups
# Desde C:\AURORA\

PowerShell:
Get-ChildItem -Path "BACKUPS" -Filter ".env" -Recurse | Remove-Item
Get-ChildItem -Path "BACKUPS" -Filter "*.db" -Recurse | Remove-Item

# Verificar que se eliminó
Get-ChildItem -Path "BACKUPS" -Include ".env" -Recurse
# No debe retornar nada
```

---

### 5. REORGANIZAR IMPORTACIONES (3 horas)

**Archivo**: `C:\AURORA\aurora_unified_main.py`

**Cambio**:
```python
# ❌ ANTES (LÍNEA 1-50) - IMPORTACIONES DESPUÉS DE sys.path
import os
import sys
import asyncio

# Cargar .env
def _cargar_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for linea in env_path.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_cargar_env()

# ❌ PROBLEMA: sys.path agregado DESPUÉS, imports fallan
try:
    from aurora_cerebro_simple import AuroraCerebro  # ERROR aquí
except Exception as e:
    AuroraCerebro = None

sys.path.insert(0, str(Path(__file__).parent / "CEREBRO"))  # Demasiado tarde


# ✅ DESPUÉS (CORRECTO) - sys.path PRIMERO
import os
import sys
import asyncio
from pathlib import Path

# 1. CARGAR .env PRIMERO
def _cargar_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for linea in env_path.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_cargar_env()

# 2. AGREGAR sys.path ANTES de imports
sys.path.insert(0, str(Path(__file__).parent / "CEREBRO"))
sys.path.insert(0, str(Path(__file__).parent / "ORACLE"))
sys.path.insert(0, str(Path(__file__).parent / "PUBLICADOR"))
sys.path.insert(0, str(Path(__file__).parent / "ACCESOS"))
# ... y todas las demás carpetas

# 3. AHORA SÍ IMPORTAR
try:
    from aurora_cerebro_simple import AuroraCerebro
    logger.info("[OK] AuroraCerebro importado")
except Exception as e:
    logger.error(f"[ERROR] AuroraCerebro: {e}")
    AuroraCerebro = None

try:
    import oracle_core
    oracle_core.init_db()
    logger.info("[OK] ORACLE cargado")
except Exception as e:
    logger.error(f"[ERROR] ORACLE: {e}")
    oracle_core = None

# ... resto de imports
```

---

### 6. AGREGAR AUTENTICACIÓN JWT (2 horas)

**Nuevo archivo**: `C:\AURORA\CORE\auth_middleware.py`

```python
# auth_middleware.py - Middleware de autenticación

import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

SECRET_KEY = os.getenv("JWT_SECRET", "aurora-dev-secret-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_token(data: dict, expires_in_minutes: int = 60):
    """Crear JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verificar JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def require_owner(token: str = Depends(security)):
    """Verificar que sea dueño"""
    payload = verify_token(token.credentials)
    if payload.get("rol") != "dueño":
        raise HTTPException(status_code=403, detail="Solo el dueño")
    return payload

# En aurora_unified_main.py - Usar así:

from CORE.auth_middleware import require_owner, create_token

@app.post("/api/acceso/ejecutar-comando")
async def acceso_ejecutar_comando(d: DatoEjecucion, user = Depends(require_owner)):
    # ✅ Ahora verificamos rol
    if not _validar_comando_whitelisted(d.comando):
        raise HTTPException(status_code=400, detail="Comando no permitido")
    return accesos_core.ejecutar_comando(d.comando)
```

---

### 7. CREAR requirements.txt (1 hora)

**Archivo**: `C:\AURORA\requirements.txt`

```
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

# LLMs
groq==0.5.0
anthropic==0.25.0

# Database
sqlite3  # (built-in)

# Web
requests==2.31.0
aiohttp==3.9.0
httpx==0.25.0

# Security
cryptography==41.0.0
PyJWT==2.8.1

# Images
pillow==10.1.0
opencv-python==4.8.0

# Scientific
numpy==1.24.0
scipy==1.11.0

# Code generation
openai==1.3.0  # Opcional

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0

# Development
black==23.10.0
flake8==6.1.0
pylint==3.0.0
mypy==1.6.0

# Monitoring (Phase 2)
sentry-sdk==1.37.0
prometheus-client==0.18.0

# Utilities
pytz==2023.3
tzlocal==5.1
```

**Instalar**:
```bash
pip install -r requirements.txt
```

---

## 🟠 ACCIONES ALTAS (Semanas 2-3 - 30 HORAS)

### Semana 2: TESTS + DOCUMENTACIÓN

#### Tests Básicos (15h)
```bash
# Crear tests/test_oracle.py
mkdir -p tests
cat > tests/test_oracle.py << 'EOF'
import pytest
from ORACLE import oracle_core

def test_crear_lead():
    lead = oracle_core.crear_lead("Juan", "123456789", "web")
    assert lead["nombre"] == "Juan"
    assert lead["estado"] == "nuevo"

def test_listar_leads():
    leads = oracle_core.listar_leads()
    assert isinstance(leads, list)

def test_crear_orden():
    orden = oracle_core.crear_orden(
        cliente="Maria",
        telefono="987654321",
        servicio="instalacion",
        kit="X5"
    )
    assert orden["cliente"] == "Maria"
    assert orden["estado"] == "recibido"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Ejecutar
pytest tests/ -v --cov=. --cov-report=html
```

#### Documentación APIs (5h)
```python
# En aurora_unified_main.py - Agregar documentación

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AURORA API",
        version="1.0.0",
        description="Sistema integrado de marketing digital + coaching",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Swagger disponible en: http://localhost:8000/docs
```

### Semana 3: CI/CD + CLEANUP

#### CI/CD Básico (5h)
```bash
# .github/workflows/test.yml
mkdir -p .github/workflows
cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
EOF

# Push a github y CI/CD corre automáticamente
```

#### Limpiar Versiones (3h)
```bash
# Eliminar versiones antiguas
rm CEREBRO/aurora_cerebro.py        # v1 obsoleta
rm CORE/config_integrado.py         # Redundante
rm CORE/servidor_simple.py          # Antiguo
rm CORE/servidor_aurora_completo.py # Antiguo

# Documentar versión activa
echo "VERSIÓN ACTIVA: aurora_cerebro_simple.py (Groq v3.1)" > CEREBRO/VERSION.txt
echo "VERSIÓN ACTIVA: aurora_unified_main.py" > VERSION.txt
```

---

## ✅ VERIFICACIÓN FINAL (Post-Implementación)

### Checklist de Seguridad

```bash
# 1. Credenciales no expuestas
grep -r "gsk_" . --include="*.py" --include="*.md"  # NO debe retornar nada
grep -r "EAAe3T5" . --include="*.py" --include="*.md"  # NO debe retornar nada

# 2. .env en .gitignore
cat .gitignore | grep "\.env"  # Debe retornar ".env"

# 3. JWT implementado
grep -r "require_owner" aurora_unified_main.py  # Debe retornar matches

# 4. Imports funcionan
python -c "from aurora_cerebro_simple import AuroraCerebro; print('OK')"
python -c "import oracle_core; print('OK')"

# 5. Tests pasan
pytest tests/ -v  # Todos deben pasar

# 6. No hay credenciales en backups
find BACKUPS -name ".env" 2>/dev/null  # NO debe retornar nada
```

---

## 📊 TRACKING DE PROGRESO

```
SEMANA 1 (SEGURIDAD):
- Día 1-2: Cambiar credenciales  [████████░░] 80%
- Día 2: .env.example + .gitignore [██████████] 100%
- Día 2-3: Limpiar backups        [██████████] 100%
- Día 3-4: Reorganizar imports    [████░░░░░░] 40%
- Día 4-5: Autenticación JWT      [██░░░░░░░░] 20%
- Día 5: requirements.txt          [██████████] 100%
```

---

## 🚨 CONTACTO Y ESCALACIÓN

Si encuentras problemas durante implementación:

1. **Errores de imports**: Verificar que sys.path esté antes de imports
2. **JWT no funciona**: Validar SECRET_KEY en variables de entorno
3. **Tests fallan**: Ejecutar `pytest -v -s` para ver detalles
4. **Credenciales aún expuestas**: Auditar git history con `git log --all -S "gsk_"`

---

**Guía creada**: 2026-06-25  
**Tiempo estimado**: 10 horas (Semana 1)  
**Siguiente milestone**: Semana 2 - Tests + Documentación
