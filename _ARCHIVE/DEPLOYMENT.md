# AURORA v1 - Deployment Guide

## Quick Start (5 minutos)

### 1. Instalar

```powershell
cd C:\AURORA
.\INSTALAR_AURORA.bat
```

### 2. Configurar API Keys (Opcional)

```powershell
# Abre PowerShell como Administrador
$env:GROQ_API_KEY = "tu-clave-aqui"
```

O edita manualmente en Windows:
- `Win + X` → "Configuración del Sistema"
- "Variables de entorno" → "Nueva"
- Nombre: `GROQ_API_KEY`
- Valor: tu clave

### 3. Arrancar

```powershell
.\LAUNCHER_AURORA.ps1
# Elige opción 1 (CLI) o 2 (Servidor)
```

## Opciones de Inicio

### CLI Interactivo (Recomendado para testing)
```powershell
.\LAUNCHER_AURORA.ps1 -CLI

# Menú interactivo en terminal
> Analiza este código
[motor_code_gen / groq]
Respuesta...
```

### Servidor FastAPI (Producción)
```powershell
.\LAUNCHER_AURORA.ps1 -Server

# Acceso:
# - API:       http://localhost:8000
# - Docs:      http://localhost:8000/docs
# - WebSocket: ws://localhost:8000/ws
```

### Tests
```powershell
.\LAUNCHER_AURORA.ps1 -Test
# Valida que todos los componentes funcionan
```

## Configuración de API Keys

### Opción 1: Variables de Entorno Windows

1. `Win + X` → "Sistema"
2. "Configuración avanzada del sistema"
3. "Variables de entorno"
4. Nueva:
   - `GROQ_API_KEY` = gsk_...
   - `CLAUDE_API_KEY` = sk-ant-...
   - `ZAI_API_KEY` = ...

### Opción 2: .env File

```bash
cd C:\AURORA\CORE
cp .env.example .env
# Edita .env con tus claves
```

### Opción 3: .env.local (Git-ignored)

```
GROQ_API_KEY=tu-clave
CLAUDE_API_KEY=tu-clave
```

## Claves Recomendadas

### GROQ (⭐ RECOMENDADO)
- **URL**: https://console.groq.com/keys
- **Modelo**: llama-3.3-70b-versatile
- **Límite**: 500k tokens/día (gratis)
- **Velocidad**: Ultra rápido
- **Costo**: Gratis

### Claude (Opcional)
- **URL**: https://console.anthropic.com/
- **Modelo**: claude-3-5-sonnet-20241022
- **Costo**: Pay-as-you-go
- **Ventaja**: Mejor razonamiento

### Zai (GLM-4)
- **URL**: https://open.bigmodel.cn/
- **Modelo**: glm-4-flash
- **Costo**: Económico
- **Ventaja**: Rápido

### Ollama (Local, 100% Privado)
- **Instalación**: https://ollama.ai
- **Comando**: `ollama pull dolphin-mixtral:latest`
- **Costo**: Gratis, usa tu GPU
- **Privacidad**: Total

## API Endpoints

### REST

```bash
# Health check
GET http://localhost:8000/health

# Status
GET http://localhost:8000/status

# Procesar mensaje
POST http://localhost:8000/procesar
{
  "mensaje": "Analiza este código",
  "contexto": {"tipo": "codigo"}
}

# Listar motores
GET http://localhost:8000/motores

# Ver motor específico
GET http://localhost:8000/motores/motor_code_gen

# Historial
GET http://localhost:8000/historial/motor_code_gen?limit=10
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({
        mensaje: "Hola AURORA"
    }));
};

ws.onmessage = (event) => {
    console.log(JSON.parse(event.data));
};
```

## Estructura de Respuesta

```json
{
  "motor_id": "motor_code_gen",
  "respuesta": "def hello():\n    print('Hello')",
  "sdk_usado": "claude",
  "tiempo_ms": 1234,
  "status": "success"
}
```

## Monitoreo

### Ver Logs
```powershell
# En tiempo real
tail -f C:\AURORA\SHARED\historial\*.json

# PowerShell
Get-Content C:\AURORA\SHARED\historial\motor_analisis_2026-06-04.json | ConvertFrom-Json
```

### Metrics
```powershell
GET http://localhost:8000/status

# Respuesta:
{
  "status": "operativo",
  "motores_activos": 6,
  "motores_totales": 6,
  "timestamp": "2026-06-04T12:34:56"
}
```

## Performance Tuning

### Aumentar Timeouts
```python
# CORE/config.py
SDK_TIMEOUTS = {
    "claude": 30.0,   # Increase
    "groq": 20.0,
    "zai": 15.0,
    "ollama": 120.0,
}
```

### Aumentar Max Tokens
```python
SDK_MAX_TOKENS = {
    "claude": 8192,    # Increase
    "groq": 1000,
    "zai": 800,
    "ollama": 1024,
}
```

### Rate Limiting
```python
# Próxima versión - por ahora sin limit
```

## Troubleshooting

### Error: "Python no encontrado"
```
Solución: Instala Python 3.9+ desde python.org
Asegúrate de agregar a PATH durante instalación
```

### Error: "API key inválida"
```
1. Verifica tu API key en el portal respectivo
2. Cópiala correctamente (sin espacios)
3. Reinicia AURORA después de configurar
```

### Error: "Todos los SDKs fallaron"
```
Solución 1: Configura al menos una API key (GROQ recomendado)
Solución 2: Instala Ollama localmente
Solución 3: Ejecuta: pip install -r requirements.txt
```

### Motor no descubierto
```
1. Verifica que motor_xxx.py existe en C:\AURORA\MOTORES\
2. Verifica que está registrado en metadata.json
3. Ejecuta test: .\LAUNCHER_AURORA.ps1 -Test
```

## Production Deployment

### Gunicorn + Nginx

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 aurora_server:app
```

### Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "uvicorn", "aurora_server:app", "--host", "0.0.0.0"]
```

### Systemd Service

```ini
[Unit]
Description=AURORA v1 Orchestrator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/AURORA/CORE
ExecStart=/usr/bin/python3 -m uvicorn aurora_server:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Notes

1. **Never commit API keys** - Use environment variables
2. **Use HTTPS in production** - Configura certificados SSL
3. **Rate limit** - Implementar en próxima versión
4. **Authentication** - Agregar JWT en próxima versión
5. **Input validation** - Ya implementado en Pydantic models

## Next Steps

1. ✅ Instalación completada
2. ⏭️ Configura al menos una API key
3. ⏭️ Ejecuta tests
4. ⏭️ Prueba CLI o Servidor
5. ⏭️ Agrega motores personalizados

## Support

- **Issues**: github.com/mocho47/aurora/issues
- **Docs**: C:\AURORA\README.md
- **Tests**: .\LAUNCHER_AURORA.ps1 -Test

---

**AURORA v1 - Powered by TEENS + NEXUS patterns**
