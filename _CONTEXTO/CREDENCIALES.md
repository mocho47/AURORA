# 🔑 Credenciales de AURORA — qué hay, qué falta y cómo se saca
### Auditado 2026-08-03 · **este archivo NUNCA lleva valores, solo nombres**

El código busca 68 variables de entorno, pero la mayoría es ruido del sistema
(`TEMP`, `SSL_CERT_FILE`, `LOCALAPPDATA`…) o configuración con valor por
defecto. **Las que de verdad son credenciales son estas.**

---

## ✅ Lo que ya tienes y funciona

| Llave | Para qué | Estado |
|---|---|---|
| `GROQ_API_KEY` | El cerebro de AURORA y Whisper para la voz | funcionando |
| `GREEN_API_INSTANCE` + `GREEN_API_TOKEN` + `GREEN_API_SERVER` | WhatsApp real, envío comprobado | funcionando |
| `FB_PAGE_ID` + `FB_PAGE_TOKEN` | Publica en la página de ATF. **El token no vence** | funcionando |
| `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_USER_ID` | Instagram de ATF | funcionando |
| `WA_NUMERO_NEGOCIO` | El teléfono oficial: 3326148674 | funcionando |
| `SUPABASE_URL` + `SUPABASE_KEY` | Base en la nube (Evolución) | funcionando |
| `JWT_SECRET_KEY` | Sesiones del panel | funcionando |
| `GEMINI_API_KEY` | Puesta el 2026-08-02; el código aún no la usa | pendiente de cablear |

---

## 🔴 Bug encontrado y corregido: dos nombres para la misma llave

El código buscaba nombres distintos según el archivo:

```
.env tiene:   GREEN_API_INSTANCE      GREEN_API_TOKEN
código pedía: GREEN_INSTANCE_ID       GREEN_API_KEY        ← no existían
              GREEN_API_INSTANCE_ID
```

**WhatsApp funcionaba de suerte**: el módulo con el nombre correcto ganaba, y los
otros fallaban **en silencio**. Un fallo silencioso en WhatsApp es un cliente sin
respuesta y nadie se entera.

Corregido en `INTEGRACIONES/whatsapp_integration.py` y
`SUPER_MARKETING_SYSTEM/motor_whatsapp_real.py`. Los de `_OBSOLETOS/` no se
tocaron: ya están archivados.

---

## 🟡 Lo que falta — por lo que te sirve

### 1. Búsqueda web con Google *(opcional: hoy ya funciona sin esto)*
```
GOOGLE_API_KEY
GOOGLE_SEARCH_ENGINE_ID
```
**La búsqueda web YA funciona** por otra vía. Con estas dos sería más precisa y
con más resultados por consulta.

**Cómo se sacan** — 10 minutos, gratis (100 búsquedas/día):
1. `console.cloud.google.com` → crear proyecto
2. Habilitar **Custom Search API**
3. Credenciales → Crear → Clave de API → esa es `GOOGLE_API_KEY`
4. `programmablesearchengine.google.com` → crear buscador → "buscar en toda la
   web" → el **ID del buscador** es `GOOGLE_SEARCH_ENGINE_ID`

---

### 2. Meta de Milens *(esto sí te falta y es venta)*
```
FB_PAGE_ID_MILENS
FB_PAGE_TOKEN_MILENS
IG_USER_ID_MILENS
```
Hoy AURORA publica en ATF pero **no en Milens**. La mitad de tu negocio no está
publicando solo.

**Cómo se sacan** — requiere un clic de Rocío, que es quien administra esa página:
1. `developers.facebook.com/tools/explorer`
2. Elegir la app **"nexus"** (la que ya usas para ATF)
3. Permisos: `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`,
   `instagram_content_publish`
4. Generar token → seleccionar la página de **Milens**
5. Convertirlo a **token de larga duración** (igual que se hizo con ATF, que no vence)

---

### 3. TikTok y YouTube *(los más caros de conseguir)*
```
TIKTOK_ACCESS_TOKEN · TIKTOK_USER_ID
YOUTUBE_API_KEY
```

**TikTok:** `developers.tiktok.com` → registrar app → pedir acceso a **Content
Posting API**. La aprobación tarda días o semanas y piden sitio web y política de
privacidad. **Es el más lento de todos.**

**YouTube:** `console.cloud.google.com` → habilitar **YouTube Data API v3** →
credenciales OAuth. Más rápido que TikTok, pero el flujo OAuth necesita
configuración de pantalla de consentimiento.

> **Mientras no estén, AURORA no los simula: dice que faltan.** Es la decisión
> correcta — mejor un hueco conocido que una publicación fantasma.

---

### 4. Telegram *(útil y de lo más fácil)*
```
TELEGRAM_TOKEN
TELEGRAM_CHAT_ID
```
Serviría para que AURORA te avise al celular (una orden nueva, un lead, la PC sin
memoria) **sin gastar WhatsApp**.

**Cómo se saca** — 3 minutos, gratis:
1. En Telegram, escríbele a **@BotFather** → `/newbot` → te da el `TELEGRAM_TOKEN`
2. Escríbele a tu bot cualquier cosa
3. Abre `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` → ahí sale tu
   `TELEGRAM_CHAT_ID`

---

### 5. Correo *(para mandar cotizaciones por mail)*
```
SMTP_SERVER · SMTP_PORT · EMAIL_FROM · EMAIL_PASSWORD
```
Con Gmail: `smtp.gmail.com`, puerto `587`, y una **contraseña de aplicación**
(no la de tu cuenta) desde `myaccount.google.com/apppasswords`.

---

## ⚪ Lo que aparece pero NO necesitas

`ANTHROPIC_API_KEY` / `CLAUDE_API_KEY` / `ZAI_API_KEY` — de intentos anteriores.
`METRICOOL_*` — servicio que no usas.
`WHATSAPP_API_TOKEN` / `WHATSAPP_BUSINESS_NUMBER` — de la API oficial de Meta;
tú usas Green API, que ya funciona.
`OAUTH_*`, `WEBHOOK_VERIFY_TOKEN`, `SUPABASE_TEST_*` — de módulos archivados.
Todo lo demás (`TEMP`, `SSL_*`, `*_NO_EXTENSIONS`, `AURORA_PORT`…) es del
sistema o tiene valor por defecto.

---

## 📋 En orden de lo que te conviene

| # | Qué | Cuánto tarda | Qué ganas |
|---|---|---|---|
| 1 | **Meta de Milens** | 15 min + clic de Rocío | Milens publica solo, como ATF |
| 2 | **Telegram** | 3 min | Avisos al celular sin gastar WhatsApp |
| 3 | Google Custom Search | 10 min | Búsquedas más precisas |
| 4 | Correo SMTP | 5 min | Cotizaciones por mail |
| 5 | YouTube | 30 min | Publicar en Shorts |
| 6 | TikTok | días/semanas | Publicar en TikTok |

> ⚠️ **Ninguna llave se pega en el chat.** Van directo al `.env`, y de ahí solo se
> leen por nombre. Si alguna se expone, se revoca y se genera otra — como pasó el
> 2026-08-02 con la de Gemini.
