# 🔑 Conectar TikTok y YouTube GRATIS — paso a paso (para Anuar)

Meta ya lo tienes (Facebook ✅, Instagram con la misma app). Esto es para las 2 que faltan, **sin pagar Metricool**. Cuando termines cada una, pásale a AURORA/Claude el dato final y ella queda publicando.

---

## ▶️ YOUTUBE (gratis) — lo más fácil de los dos

**1.** Crea una cuenta Google para ATF (si no tienes): https://accounts.google.com/signup
**2.** Crea el canal de YouTube "Actualiza Tus Faros" (youtube.com → tu foto → Crear canal).
**3.** Entra a **https://console.cloud.google.com** con esa cuenta → arriba, **"Nuevo proyecto"** → nómbralo `ATF`.
**4.** Menú ☰ → **APIs y servicios → Biblioteca** → busca **"YouTube Data API v3"** → **Habilitar**.
**5.** Menú → **APIs y servicios → Pantalla de consentimiento OAuth** → tipo **Externo** → llena nombre de app y tu correo → Guardar (puedes dejarla "en pruebas").
**6.** Menú → **Credenciales → Crear credenciales → ID de cliente de OAuth** → tipo **App de escritorio** → Crear.
**7.** Descarga el archivo JSON (botón de descarga ⬇️). Se llama algo como `client_secret_XXXX.json`.
**8.** Pon ese archivo en `C:\AURORA.worktrees\` y avísale a AURORA: *"ya está el client_secret de YouTube"*.

💡 Gratis: la cuota diaria de la API te alcanza para ~6 subidas de video al día (tú subes 1). Cero costo.

---

## 🎵 TIKTOK (gratis, pero el más lento) — requiere que TikTok apruebe

**1.** Ten lista la cuenta de **TikTok de ATF**.
**2.** Entra a **https://developers.tiktok.com** → inicia sesión con esa cuenta.
**3.** **Manage apps → Connect an app** → llena los datos (nombre: ATF, descripción del taller).
**4.** En tu app, pide el producto **"Content Posting API"**.
**5.** ⚠️ AQUÍ ESTÁ EL HUESO: TikTok **revisa tu app** antes de dejar publicar automático a **público**.
   - Mientras no la aprueben, la API solo deja subir como **borrador privado** (tú lo publicas a mano desde la app).
   - La aprobación puede tardar días/semanas. Es gratis, solo lento.
**6.** Cuando aprueben (o para usar borradores): copia el **Client Key** y **Client Secret** de tu app y pásaselos a AURORA.

💡 Alternativa mientras TikTok aprueba: AURORA te deja el **video + texto listos** y tú los subes en 2 minutos. Cero espera.

---

## ✅ Resumen del plan gratis
- **Facebook** ✅ ya publica solo
- **Instagram** → misma app de Meta + ngrok gratis (para la liga de video) — avísale a AURORA cuando definas la cuenta IG de ATF
- **YouTube** → los 8 pasos de arriba (gratis, ~30 min)
- **TikTok** → developers + esperar aprobación (gratis, lento) o subir a mano con lo que AURORA prepara

**Nada de esto cuesta mensualidad.** Metricool solo valdría la pena si algún día quieres TikTok automático YA sin esperar la aprobación.
