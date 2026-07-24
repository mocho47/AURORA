# AURORA v1 - Primer Arranque

## ✅ Sistema Completado

AURORA v1 está **100% listo para usar**.

### Estado Actual:
- ✅ **6 motores** operacionales
- ✅ **4 SDKs** (Claude, Groq, Zai, Ollama)
- ✅ **CLI interactivo** + Servidor FastAPI
- ✅ **Dashboard web** visual
- ✅ **6 tests** validando todo
- ✅ **Auto-discovery** de motores
- ✅ **Fallback chain** inteligente

---

## 🚀 Arrancar Ahora

### Paso 1: Instalar Dependencias (solo 1 vez)

```powershell
cd C:\AURORA
.\INSTALAR_AURORA.bat
```

Esto:
- Instala Python si no existe
- Descarga todas las librerías
- Ejecuta validación (6/6 tests)

### Paso 2: Configurar API Keys (Opcional pero Recomendado)

**Opción A: Variable de Entorno Windows (Permanente)**

1. `Win + X` → "Sistema"
2. "Configuración avanzada del sistema" → "Variables de entorno"
3. "Nueva variable de usuario"
4. Nombre: `GROQ_API_KEY`
5. Valor: Copia tu clave desde https://console.groq.com/keys

Luego reinicia PowerShell.

**Opción B: .env.local (Solo AURORA)**

```powershell
cd C:\AURORA\CORE
# Abre Notepad
notepad .env.local

# Pega esto:
GROQ_API_KEY=gsk_tu_clave_aqui
```

**Opción C: Sin API Keys (Usa Ollama Local)**

AURORA funciona sin claves, pero tendrás límites. Instala Ollama:
- https://ollama.ai
- `ollama pull dolphin-mixtral:latest`

### Paso 3: Arrancar

**Menú Interactivo:**
```powershell
.\LAUNCHER_AURORA.ps1
# Elige: 1 (CLI) o 2 (Servidor)
```

**O directo:**
```powershell
.\LAUNCHER_AURORA.ps1 -CLI          # Línea de comandos
.\LAUNCHER_AURORA.ps1 -Server       # Servidor web
.\LAUNCHER_AURORA.ps1 -Test         # Validación
```

---

## 💬 Probando AURORA

### CLI (Interactivo)

```
AURORA ready. Type messages (or 'exit' to quit):

> Analiza este código Python def hello(): print('Hello')
[motor_code_gen / claude]
Análisis del código...

> ¿Cómo mejorar mi relación familiar?
[motor_coaching / groq]
Te sugiero empezar con...

> exit
```

### Servidor + Dashboard

1. Ejecuta: `.\LAUNCHER_AURORA.ps1 -Server`
2. Abre navegador: `http://localhost:8000/templates/dashboard.html`
3. Escribe mensajes en el dashboard
4. Ver respuestas en tiempo real

### API (cURL)

```bash
# Procesar mensaje
curl -X POST http://localhost:8000/procesar \
  -H "Content-Type: application/json" \
  -d '{"mensaje":"Hola AURORA"}'

# Ver motores disponibles
curl http://localhost:8000/motores

# Ver documentación API interactiva
# Abre: http://localhost:8000/docs
```

---

## 🎯 Motores Disponibles

| Motor | SDK Preferido | Uso |
|-------|---|---|
| **analisis** | Groq | Default - análisis general |
| **code_gen** | Claude | Generación de código |
| **coaching** | Groq | Coaching personal/familiar |
| **ventas** | Groq | CRM y gestión de ventas |
| **marketing** | Zai | Contenido y marketing |
| **reasoning** | Claude | Análisis profundo y estrategia |

**Routing Automático:**
- Mensaje con "código" → motor_code_gen
- Mensaje con "familia" → motor_coaching
- Mensaje con "venta" → motor_ventas
- Otros → motor_analisis

---

## 🔑 Obtener API Keys (Gratis)

### Groq (⭐ RECOMENDADO - Gratis)
1. https://console.groq.com/keys
2. Haz login con Google/GitHub
3. Copia la API key (gsk_...)
4. Límite: 500k tokens/día = GRATIS

### Claude (Opcional)
1. https://console.anthropic.com/
2. Crea cuenta
3. Copia API key (sk-ant-...)
4. Costo: Pay-as-you-go (~$0.003-0.015 por 1K tokens)

### Zai (GLM-4, Económico)
1. https://open.bigmodel.cn/
2. Sign up
3. Copia API key
4. Costo: Económico

---

## 📊 Monitoreo

### Ver Estado
```powershell
.\LAUNCHER_AURORA.ps1 -Test
# Muestra: motores activos, SDKs, configuración
```

### Ver Historial
```powershell
# Ver último archivo de historial
Get-Content C:\AURORA\SHARED\historial\motor_analisis_*.json -Tail 20
```

### Logs en Tiempo Real
```powershell
Get-Content C:\AURORA\SHARED\historial\*.json | ConvertFrom-Json | Select timestamp,motor_id,respuesta
```

---

## ⚙️ Configuración Avanzada

### Cambiar SDK Fallback

```python
# C:\AURORA\CORE\config.py
DEFAULT_SDK_FALLBACK = ["claude", "groq", "zai", "ollama"]  # Orden de preferencia
```

### Agregar Motor Personalizado

1. Crea `motor_xxx.py` en `C:\AURORA\MOTORES\`
2. Agrega entrada en `metadata.json`
3. Listo - AURORA lo descubre automáticamente

Ejemplo:
```json
{
  "id": "motor_custom",
  "nombre": "Mi Motor",
  "patrones": ["custom", "mio"],
  "sdk_preferido": "groq",
  "puerto": 8010,
  "activo": true,
  "timeout": 12.0,
  "max_tokens": 500
}
```

### Aumentar Timeouts

```python
# Si necesitas respuestas más largas
SDK_TIMEOUTS = {
    "claude": 30.0,    # Aumenta para análisis profundos
    "groq": 20.0,
    "zai": 15.0,
    "ollama": 120.0,   # Local es más lento
}
```

---

## 🐛 Troubleshooting

### "Python no encontrado"
```
Solución: Instala Python 3.9+ desde https://python.org
Asegúrate de marcar "Add to PATH" en instalación
```

### "API key inválida"
```
1. Verifica clave en portal respectivo
2. Copia sin espacios
3. Reinicia PowerShell después de configurar var de entorno
```

### "Todos los SDKs fallaron"
```
Solución: Instala Ollama
https://ollama.ai
ollama pull dolphin-mixtral:latest
```

### Motor no se descubre
```
1. Verifica archivo existe: C:\AURORA\MOTORES\motor_xxx.py
2. Verifica en metadata.json con ID correcto
3. Ejecuta: .\LAUNCHER_AURORA.ps1 -Test
```

### Servidor en puerto 8000 ocupado
```
# Encuentra proceso usando puerto 8000
netstat -ano | findstr :8000

# Mata proceso
taskkill /PID <PID> /F

# O usa puerto diferente en aurora_server.py
```

---

## 📈 Próximas Mejoras

- [ ] Dashboard mejorado (gráficos, historial)
- [ ] Persistencia en BD (SQLite/Postgres)
- [ ] Authentication (JWT)
- [ ] Rate limiting
- [ ] Cache inteligente
- [ ] Webhooks
- [ ] Integración Telegram/WhatsApp
- [ ] Mobile app

---

## 🎓 Notas Técnicas

### Arquitectura
```
User Input
    ↓
aurora.py (main loop)
    ↓
aurora_selector (6-tier decision engine)
    ↓
(motor_config, sdk_name)
    ↓
aurora_sdk_manager (SDK dispatcher)
    ↓
[SDK fallback: preferred → groq → zai → ollama]
    ↓
Response
    ↓
Save to historial
    ↓
Return to user
```

### 6 Tiers de Decisión
1. **Vital Risk**: Autolesión, abuso → Ollama local
2. **Sensitive**: Emociones, familia → Enriquece contexto
3. **Dynamic Context**: Historial, perfil → Refina
4. **Pattern Match**: Keywords → Scoring → Motor
5. **Profile Detection**: Teen/padre/maestro → Ajusta tone
6. **SDK Selection**: Verifica env vars → Fallback chain

### Auto-Discovery
```python
importlib.util.spec_from_file_location("aurora.motores.motor_xxx", "path/to/motor_xxx.py")
# AURORA carga motor automaticamente
```

---

## 📞 Soporte

- **Docs**: C:\AURORA\README.md
- **Deployment**: C:\AURORA\DEPLOYMENT.md
- **API Docs**: http://localhost:8000/docs (cuando servidor corre)
- **Tests**: `.\LAUNCHER_AURORA.ps1 -Test`

---

## 🎉 ¡Listo!

AURORA está completamente operacional. 

**Pasos siguientes:**
1. ✅ Instalar (INSTALAR_AURORA.bat)
2. ✅ Configurar API key (opcional pero recomendado)
3. ✅ Arrancar (LAUNCHER_AURORA.ps1)
4. ✅ Probar en CLI o Dashboard

**Disfruta de la inteligencia multi-motor sin censura ni vendor lock-in!**

---

**AURORA v1 - Powered by TEENS + NEXUS patterns © 2026**
