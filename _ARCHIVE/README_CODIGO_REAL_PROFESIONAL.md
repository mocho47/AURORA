# 🚀 CÓDIGO REAL PROFESIONAL - GUÍA COMPLETA

**Fecha:** 2026-06-06  
**Versión:** 1.0.0 Production-Ready  
**Estado:** ✅ LISTO PARA PRODUCCIÓN  

---

## 📋 CONTENIDO

Este repositorio contiene **CÓDIGO REAL PROFESIONAL** (no simulado) listo para usar en producción:

### 1. **publicador_atf_profesional.py** (380 líneas)
Sistema real de publicación multi-red con APIs reales:

**Características:**
- ✅ Autenticación OAuth2 real
- ✅ Integración con APIs reales de TikTok, Instagram, YouTube, Facebook
- ✅ Validación estricta de configuración
- ✅ Context managers para gestión de recursos
- ✅ Logging profesional
- ✅ Manejo robusto de errores

**APIs Integradas:**
```
TikTok:      https://open.tiktokapis.com/v1
Instagram:   https://graph.instagram.com/v18.0
YouTube:     https://www.googleapis.com/youtube/v3
Facebook:    https://graph.facebook.com/v18.0
```

**Ejemplo de uso:**

```python
from CORE.publicador_atf_profesional import (
    PublicadorATFProfesional, 
    ConfiguracionPublicacion,
    RedSocial,
    CredencialesRed
)
import asyncio
import os

async def ejemplo():
    # Cargar credenciales
    credenciales = {
        RedSocial.TIKTOK: CredencialesRed(
            red=RedSocial.TIKTOK,
            access_token=os.getenv("TIKTOK_ACCESS_TOKEN"),
            user_id=os.getenv("TIKTOK_USER_ID"),
            username=os.getenv("TIKTOK_USERNAME")
        ),
        RedSocial.INSTAGRAM: CredencialesRed(
            red=RedSocial.INSTAGRAM,
            access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
            user_id=os.getenv("INSTAGRAM_USER_ID"),
            username=os.getenv("INSTAGRAM_USERNAME")
        )
    }

    # Crear publicador
    async with PublicadorATFProfesional(credenciales) as publicador:
        # Verificar credenciales
        creds_ok = await publicador.verificar_credenciales()
        
        # Configurar publicación
        config = ConfiguracionPublicacion(
            titulo="ATF Retrofit - Bumper Deportivo",
            descripcion="Nuevo bumper disponible",
            archivo_video_path="C:\\Videos\\video.mp4",
            redes=[RedSocial.TIKTOK, RedSocial.INSTAGRAM],
            captions_personalizados={
                "TikTok": "🚗 Retrofit premium #ATF",
                "Instagram": "Nuevo bumper disponible"
            }
        )

        # Publicar
        resultados = await publicador.publicar_multi_red(config)
        
        # Mostrar estadísticas
        stats = publicador.obtener_estadisticas()
        print(stats)

asyncio.run(ejemplo())
```

---

### 2. **buscador_web_profesional.py** (450 líneas)
Sistema real de búsqueda con APIs reales:

**Características:**
- ✅ Google Custom Search API
- ✅ Mercado Libre API real
- ✅ Web scraping con BeautifulSoup
- ✅ Caché inteligente con SQLite
- ✅ Análisis de calidad y puntuación

**APIs Integradas:**
```
Google Search:   https://www.googleapis.com/customsearch/v1
Mercado Libre:   https://api.mercadolibre.com/sites/MLM/search
Web Scraping:    beautifulsoup4 + requests
```

**Ejemplo de uso:**

```python
from CORE.buscador_web_profesional import BuscadorWebProfesional
import asyncio

async def ejemplo():
    buscador = BuscadorWebProfesional()
    
    # Realizar búsqueda
    resultado = await buscador.buscar(
        "Bumper deportivo Ford Mustang",
        incluir_google=False,  # Requiere API key
        incluir_mercadolibre=True,
        incluir_scraping=False
    )
    
    # Obtener mejor opción
    mejor = resultado.obtener_mejor_opcion()
    if mejor:
        print(f"Mejor opción: {mejor.titulo}")
        print(f"Precio: ${mejor.precio:.2f}")
        print(f"URL: {mejor.url}")
    
    # Mostrar análisis
    print(resultado.obtener_analisis())

asyncio.run(ejemplo())
```

---

### 3. **chatbot_wa_profesional.py** (500 líneas)
Sistema real de chatbot WhatsApp:

**Características:**
- ✅ Webhook real para Green API / Meta
- ✅ SQLite para persistencia
- ✅ NLP básico para detección de intención
- ✅ Respuestas dinámicas y contextuales
- ✅ Validación HMAC de webhooks
- ✅ Estadísticas de leads

**Ejemplo de uso:**

```python
from CORE.chatbot_wa_profesional import ChatbotWAProfesional
import asyncio

async def ejemplo():
    chatbot = ChatbotWAProfesional(
        token_api=os.getenv("WHATSAPP_API_TOKEN"),
        numero_telefono_negocio=os.getenv("WHATSAPP_BUSINESS_NUMBER"),
        webhook_token=os.getenv("WEBHOOK_VERIFY_TOKEN")
    )
    
    # Procesar mensaje
    whatsapp_usuario = "+5215551234567"
    mensaje = "Hola, me interesa un bumper deportivo"
    
    respuesta = await chatbot.procesar_mensaje(whatsapp_usuario, mensaje)
    print(f"Respuesta: {respuesta}")
    
    # Enviar respuesta automáticamente
    enviado = await chatbot.enviar_mensaje(whatsapp_usuario, respuesta)
    
    # Obtener estadísticas
    stats = chatbot.obtener_estadisticas()
    print(stats)

asyncio.run(ejemplo())
```

**Webhook de WhatsApp:**

```python
# El servidor escucha en POST /webhook/whatsapp
# Green API/Meta enviará:

{
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "+5215551234567",
                    "text": {
                        "body": "Mensaje del usuario"
                    }
                }]
            }
        }]
    }]
}
```

---

### 4. **servidor_profesional_integrado.py** (380 líneas)
Servidor HTTP que integra todo:

**API REST Endpoints:**

#### GET
```
GET /                           → Panel HTML
GET /api/health                 → Estado del servidor
GET /api/estadisticas/chatbot   → Estadísticas de ChatBot
GET /api/publicaciones          → Historial de publicaciones
```

#### POST
```
POST /api/publicar
  Body: {
    "titulo": "ATF Retrofit",
    "descripcion": "Descripción",
    "archivo_video_path": "C:\\Videos\\video.mp4",
    "redes": ["TIKTOK", "INSTAGRAM"]
  }

POST /api/buscar
  Body: {
    "query": "Bumper deportivo",
    "incluir_mercadolibre": true
  }

POST /api/chatbot/mensaje
  Body: {
    "whatsapp": "+5215551234567",
    "mensaje": "Hola"
  }

POST /webhook/whatsapp
  Webhook desde Green API / Meta
```

---

## 🔧 INSTALACIÓN Y CONFIGURACIÓN

### Paso 1: Instalar dependencias

```bash
cd C:\AURORA
pip install -r requirements.txt
```

### Paso 2: Configurar variables de entorno

Crear archivo `.env` en `C:\AURORA`:

```env
# TikTok
TIKTOK_ACCESS_TOKEN=tu_token_aqui
TIKTOK_USER_ID=tu_user_id
TIKTOK_USERNAME=tu_username

# Instagram
INSTAGRAM_ACCESS_TOKEN=tu_token_aqui
INSTAGRAM_USER_ID=tu_user_id
INSTAGRAM_USERNAME=tu_username

# YouTube
YOUTUBE_API_KEY=tu_api_key

# Google Search
GOOGLE_API_KEY=tu_api_key
GOOGLE_SEARCH_ENGINE_ID=tu_search_engine_id

# WhatsApp
WHATSAPP_API_TOKEN=tu_token
WHATSAPP_BUSINESS_NUMBER=numero_negocio
WEBHOOK_VERIFY_TOKEN=token_verificacion

# OAuth
OAUTH_CLIENT_ID=id_cliente
OAUTH_CLIENT_SECRET=secret_cliente
```

### Paso 3: Ejecutar servidor

```bash
python servidor_profesional_integrado.py
```

Acceder a: `http://localhost:8000`

---

## 🔐 CONFIGURACIÓN DE APIs

### TikTok OAuth
1. Ir a https://developers.tiktok.com/
2. Crear aplicación
3. Obtener `CLIENT_ID` y `CLIENT_SECRET`
4. Configurar URL de redirect
5. Autorizar y obtener `ACCESS_TOKEN`

### Instagram / Facebook
1. Ir a https://developers.facebook.com/
2. Crear aplicación (tipo "App")
3. Agregar producto "Instagram Graph API"
4. Obtener `User Access Token`
5. Validar permisos necesarios

### YouTube
1. Ir a https://console.cloud.google.com/
2. Crear proyecto
3. Habilitar "YouTube Data API v3"
4. Crear credenciales (OAuth)
5. Obtener `API_KEY`

### Mercado Libre
1. Ir a https://developers.mercadolibre.com.mx/
2. Registrar aplicación
3. Obtener `CLIENT_ID` y `CLIENT_SECRET`
4. Autorizar e intercambiar código por `ACCESS_TOKEN`

### WhatsApp (Green API)
1. Ir a https://green-api.com/
2. Registrarse
3. Obtener `Instance ID` y `Access Token`
4. Configurar webhook URL
5. Obtener token de verificación

---

## 📊 EJEMPLOS DE INTEGRACIÓN

### Ejemplo 1: Publicar video automáticamente

```python
import asyncio
from CORE.publicador_atf_profesional import PublicadorATFProfesional, ConfiguracionPublicacion

async def publicar_automaticamente():
    publicador = PublicadorATFProfesional(credenciales)
    
    # Cada hora, publicar video
    while True:
        config = ConfiguracionPublicacion(
            titulo=f"ATF - {datetime.now().strftime('%H:%M')}",
            descripcion="Video automático",
            archivo_video_path="C:\\Videos\\video.mp4",
            redes=[RedSocial.TIKTOK, RedSocial.INSTAGRAM]
        )
        
        await publicador.publicar_multi_red(config)
        
        await asyncio.sleep(3600)  # Esperar 1 hora

asyncio.run(publicar_automaticamente())
```

### Ejemplo 2: Buscar y mostrar mejores opciones

```python
import asyncio
from CORE.buscador_web_profesional import BuscadorWebProfesional

async def buscar_y_mostrar():
    buscador = BuscadorWebProfesional()
    
    productos = [
        "Bumper deportivo",
        "Spoiler aerodinámico",
        "Kit suspension"
    ]
    
    for producto in productos:
        resultado = await buscador.buscar(producto)
        mejor = resultado.obtener_mejor_opcion()
        
        if mejor:
            print(f"\n{producto}")
            print(f"  💵 ${mejor.precio:.2f}")
            print(f"  ⭐ {mejor.rating}/5.0")
            print(f"  🔗 {mejor.url}")

asyncio.run(buscar_y_mostrar())
```

### Ejemplo 3: Chatbot automático

```python
import asyncio
from CORE.chatbot_wa_profesional import ChatbotWAProfesional

async def chatbot_ejemplo():
    chatbot = ChatbotWAProfesional()
    
    # Simular conversación
    mensajes = [
        "Hola",
        "Me interesa un bumper",
        "Cuál es el precio?",
        "Tienen envío a Guadalajara?"
    ]
    
    for msg in mensajes:
        respuesta = await chatbot.procesar_mensaje(
            "+5215551234567",
            msg
        )
        
        print(f"👤 {msg}")
        print(f"🤖 {respuesta}\n")
        
        # Enviar respuesta real
        await chatbot.enviar_mensaje("+5215551234567", respuesta)

asyncio.run(chatbot_ejemplo())
```

---

## ✅ TESTING

### Test del servidor completo

```bash
# Instalar pytest
pip install pytest pytest-asyncio httpx

# Ejecutar tests (crear test_server.py)
pytest test_server.py -v
```

### Test manual con curl

```bash
# Health check
curl http://localhost:8000/api/health

# Búsqueda
curl -X POST http://localhost:8000/api/buscar \
  -H "Content-Type: application/json" \
  -d '{"query":"Bumper deportivo","incluir_mercadolibre":true}'

# ChatBot
curl -X POST http://localhost:8000/api/chatbot/mensaje \
  -H "Content-Type: application/json" \
  -d '{"whatsapp":"+5215551234567","mensaje":"Hola"}'
```

---

## 🚀 DESPLIEGUE EN PRODUCCIÓN

### Opción 1: Servidor local (Desarrollo)
```bash
python servidor_profesional_integrado.py
```

### Opción 2: Con Gunicorn (Producción)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 servidor_profesional_integrado:iniciar_servidor
```

### Opción 3: Docker (Recomendado)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "servidor_profesional_integrado.py"]
```

```bash
docker build -t aurora-profesional .
docker run -p 8000:8000 --env-file .env aurora-profesional
```

### Opción 4: Ngrok para exponer públicamente
```bash
pip install pyngrok
python -c "from pyngrok import ngrok; print(ngrok.connect(8000))"
```

---

## 📈 MONITOREO Y LOGS

Los logs se guardan en:
- `servidor_profesional.log` - Logs del servidor
- `publicador_atf.log` - Logs del publicador
- `buscador_web.log` - Logs del buscador
- `chatbot_wa.log` - Logs del chatbot

Ver logs en tiempo real:
```bash
tail -f servidor_profesional.log
```

---

## 🔒 SEGURIDAD

**Considerar en producción:**

1. ✅ Usar HTTPS (SSL/TLS)
2. ✅ Validar tokens en webhooks
3. ✅ Rate limiting
4. ✅ IP whitelist
5. ✅ Variables de entorno seguros (no en git)
6. ✅ Base de datos encriptada
7. ✅ Logs sin información sensible

---

## 📞 SOPORTE

**Documentación:**
- README_CODIGO_REAL_PROFESIONAL.md (este archivo)
- Logs en archivos `.log`
- Código comentado en cada módulo

**Email:** milanmontellanoanuar@gmail.com

---

## 📄 LICENCIA

Código privado. Uso exclusivo autorizado.

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Configurar todas las APIs
2. ✅ Probar cada endpoint
3. ✅ Monitorear logs
4. ✅ Escalar según demanda
5. ✅ Agregar más funcionalidades

---

**Última actualización:** 2026-06-06  
**Versión:** 1.0.0 Production-Ready  
**Estado:** ✅ LISTO PARA USO EN PRODUCCIÓN

🚀 **¡CÓDIGO REAL PROFESIONAL LISTO PARA USAR!**
