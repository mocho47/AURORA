# AURORA — Operador de negocio con IA (Milens / ATF)

**Estado real, verificado 2026-08-23:** servidor arriba, 425/425 pruebas en verde, health check en vivo.
Este README describe lo que HOY corre de verdad — no una foto vieja. La versión anterior de este
archivo (fechada 2026-06-25, firmada "Ejecutado por: GitHub Copilot") describía un sistema distinto
que nunca fue el real; queda archivada, sin editar, en `_OBSOLETOS/AURORA_duplicado/README.md` y
`_ARCHIVE/README.md` solo como referencia histórica — **ninguna de las dos** es la arquitectura actual.

## Arranque

```powershell
cd C:\AURORA.worktrees
python run_aurora.py
```

- Puerto: **5000**
- Health: `GET http://127.0.0.1:5000/health`
- Docs (Swagger): `http://127.0.0.1:5000/docs`
- Acceso directo: `Desktop\AURORA.lnk`
- Arranque completo: ~90s

⚠️ El health check hay que pegarlo por **127.0.0.1**, no `localhost` — con `localhost` a veces
responde antes de que el servidor esté listo de verdad.

## Qué es, de verdad

Un **operador de negocio** para Milens (corte láser/sublimación) y ATF (retrofit de faros), no un
"sistema de marketing" genérico. Un solo cerebro de lenguaje decide qué hacer con lo que Anuar escribe
o dice, y ~35 motores reales ejecutan la acción sobre el negocio.

## Arquitectura real

```
run_aurora.py            → arranca todo, registra ~35 motores en el bus
CORE/aurora_server.py    → FastAPI, expone los endpoints reales (/taller, /oracle, /alertas, /procesar, /motores...)
CEREBRO/consciencia.py   → el ÚNICO despachador de lenguaje: reconoce lo que Anuar pide y decide
                            qué candado/motor dispara (candados directos + familias de frases reales)
MOTORES/                 → ~35 motores (cotizador, imágenes, ventas, negocios, coaching, code_gen...)
TALLER/                  → órdenes de trabajo, cotizador real, catálogo, alertas
EDITOR/                  → cotizador de corte láser, DXF, escalas
MEMORIA/                 → SQLite WAL (episódica + semántica), perfil de habilidades, sueño/consolidación
CEREBRO/respaldo_local.py→ escalón de respaldo si Groq falla (Gemini → local)
```

No hay JWT, no hay CRM separado, no hay Mercado Pago ni Zapier ni app móvil — eso era la versión
de junio que nunca se construyó así. Lo que sí existe y corre: WhatsApp Web (`MARKETING/campana_por_whatsapp_web.py`),
publicación real a Facebook (`PUBLICADOR/auto_publicar_atf.py`), el panel web (`TEMPLATES/panel-completo.html`)
con formularios mecánicos para cotizar/editar imagen sin depender del lenguaje libre.

## Cómo entiende AURORA lo que se le pide

Un solo punto de decisión, `CEREBRO/consciencia.py`:
1. `_candado_por_familia(mensaje)` — reconoce por patrones reales (las frases con las que Anuar
   habla de verdad, no comandos formales) y decide qué candado gana el turno.
2. Si no hay familia que reconozca el mensaje, cae a los 36 candados directos (`_CANDADOS`), en
   orden fijo, cada uno con su propio trigger.
3. Si Groq no puede resolver, escalón de respaldo: Gemini → modelo local.

Esto vivía partido en dos archivos (`consciencia.py` + `lengua_anuar.py`) — se fusionó en uno solo
el 2026-08-23 porque la duplicación causaba el mismo bug corregido en un lado y vivo en el otro.

## Pruebas

```powershell
python -m pytest tests/ -q
```

425 casos reales, 0 simulados. Última corrida completa: 425 passed, 445s.

## Documentación viva

- `_CONTEXTO/LEEME_PRIMERO.md` — reglas + mapa, leer primero cada sesión
- `_CONTEXTO/ESTADO_REAL.md` — qué funciona VERIFICADO (no lo que se supone que funciona)
- `_CONTEXTO/PROMPT_MAESTRO_AURORA.md` — arquitectura correcta completa, cada regla atada a un bug real
- `_CONTEXTO/PROMPT_HONESTIDAD_IA.md` — reglas de honestidad/rigor para cualquier IA que trabaje aquí
- `_CONTEXTO/FRASES_REALES_ANUAR.md` — frases reales de Anuar + historial de bugs de lenguaje

## Seguridad

Credenciales solo en `.env` (nunca en código, nunca en este README, nunca impresas en el chat).
`.env` fuera de git.
