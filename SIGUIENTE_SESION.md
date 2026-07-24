# 🟢 AURORA — REGISTRO DE ARRANQUE (próxima sesión)
_Última sesión: 2026-07-10 · Cierre en excelencia, todo probado end-to-end._

---

## ▶️ CÓMO ARRANCAR
- Doble clic al acceso **AURORA** del escritorio (INICIAR_AURORA.bat) → arranca + abre el panel solo.
- O manual: `C:\Program Files\Python312\python.exe run_aurora.py` en `C:\AURORA.worktrees`.
- Arranque ~60–90 s (28 motores en el bus). Panel: **http://127.0.0.1:5000/panel**
- Salud: `http://127.0.0.1:5000/health` (usar 127.0.0.1, NO localhost).

---

## ✅ HARDWARE TERMINADO Y PROBADO (11 endpoints en verde)
Paneles usables (menú izquierdo del panel), cada uno arrastra-y-usa, real, sin simular:

| Panel | Qué hace | Endpoint clave |
|---|---|---|
| **Editor · Herramientas** | Cotizar DXF, aligerar, PDF→DXF, B&N, línea, **quitar fondo (IA)**, **foto→dibujo lineal (IA)** | `/editor/procesar` (subida) |
| **Vendedor · Fichas** | 29 fichas técnicas reales | `/vendedor/fichas` |
| **Marketing IA** | Contenido (algoritmo real + LLM) + inteligencia de redes | `/marketing/*` |
| **Redes · Publicador** | Estado FB/IG/WhatsApp + publicar | `/publicador/*` |
| **Biblioteca** | Buscar + subir PDF (FTS5) | `/biblioteca/{buscar,subir,estado}` |
| **Sistema · PC** | Diagnóstico + optimizar | `/sistema/*` |
| **Red · Dispositivos** | Escanea LAN, diagnostica desconexiones (Cast/Nest) | `/red/{cast,diagnostico,ping}` |
| **Web en vivo** | Búsqueda/noticias/leer página REALES (ddgs) | `/web/{buscar,noticias,leer}` |
| **PC · Control** | Ejecutar, listar, abrir, apps, portapapeles — **BLINDADO con PIN** | `/pc/*` (403 sin token) |
| — Auth dueño | PIN + llave por dispositivo (local) | `/auth/{estado,configurar-pin,login,revocar}` |

**Módulos nuevos:** `EDITOR/conversiones.py` (rembg u2net_human_seg + XDoG + detección de cara), `EDITOR/cotizador_corte.py`, `REDES/red_diagnostico.py`, `WEB/web_real.py` (ddgs). Expuestos: `AUTH/identidad_core.py`, `CEREBRO/pc_access.py`.
**Libs instaladas:** `ddgs`, `rembg`. **Arquitectura = cartuchos** (carga bajo demanda; quitar/poner sin romper).

---

## ⚠️ PENDIENTES DE ANUAR (fuera del código)
1. **PIN de dueño = VIRGEN.** Ponerlo la 1ª vez en el panel **PC · Control** (mín. 4 caracteres). Si se olvida: borrar `CONFIG/identidad.json` y reponer `{"pin_salt":"","pin_hash":"","tokens":[]}`.
2. **Google Home Mini "Oficina 2"** se desconecta. En el router **ZTE F689** (`192.168.1.1`, login `user`/`user`) → *Red local → LAN → IPv4 → Enlace DHCP*: crear `Nombre=OficinaMini · MAC=00:F6:20:64:03:47 · IP=192.168.1.10 · Crear nuevo elemento`. Opcional DNS (Servidor DHCP): principal `8.8.8.8`, secundario `1.1.1.1`. Luego desenchufar el Mini 10 s.

---

## 🚀 PRÓXIMO SALTO (por valor, lo elijo yo salvo que digas otra cosa)
1. **RAG: Biblioteca → chat** — que AURORA responda usando TUS manuales (RDWorks/K10). *El mayor valor pendiente.*
2. **Wire Web real al chat** — hoy `_buscar_web` (CEREBRO/consciencia.py) cae al LLM; conectarlo a `WEB/web_real.py`.
3. **Vendedor completo** — exponer `construir_brief` (pitch), `tecnicas`, `prompt_extraccion`+`guardar_ficha` (auto-fichado desde web), `registrar_venta_db`.
4. Afinar/pulir lo que pidas del Editor (modo "retrato detallado" opcional para póster).

---

## 📋 NOTAS DE CONTEXTO
- Directivas vigentes: nada simulado/parcial, siempre a máxima expresión y profesional; arquitectura de cartuchos; "es tu proyecto, manéjalo".
- Credenciales AURORA: GROQ/FB/IG/WhatsApp OK. Supabase caído. GREEN_API_SERVER roto en .env.
- Extensión "Claude para Chrome" NO conectó esta sesión (por eso el router se guió a mano).
- Todo esto también está en la memoria persistente (MEMORY.md) — se carga solo al iniciar.
