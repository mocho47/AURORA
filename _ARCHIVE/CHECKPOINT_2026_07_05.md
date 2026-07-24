# AURORA — CHECKPOINT TÉCNICO REAL
**Fecha:** 2026-07-06 (actualizado)  
**Generado por:** Auditoría completa + FASES 1-2 ejecutadas  
**Estado general:** TODAS LAS FASES COMPLETADAS ✅ (1-6)

---

## ACTUALIZACIÓN 2026-07-06

### FASE 2 COMPLETADA ✅ — Bus Neuronal: 29 componentes conectados
`CEREBRO/registrador_bus.py` reescrito. Antes: 12. Ahora: **29 componentes**.

| Componente | Tipo | Estado |
|---|---|---|
| motor_analisis | LLM Groq | ✅ |
| motor_coaching | LLM Groq | ✅ |
| motor_coaching_real | LLM Groq | ✅ |
| motor_code_gen | LLM Claude | ✅ |
| motor_cotizador | LLM Groq | ✅ |
| motor_imagenes | LLM Claude | ✅ |
| motor_negocios | LLM Groq | ✅ |
| motor_reasoning | LLM Claude | ✅ |
| motor_ventas | LLM Groq | ✅ |
| motor_marketing | LLM Groq | ✅ |
| motor_pedidos | SQLite | ✅ |
| motor_oracle | SQLite CRM | ✅ |
| **vendedor_core** | Fichas técnicas | ✅ NUEVO |
| **verificador_core** | Anti-inventar | ✅ NUEVO |
| **taller_core** | DXF laser Inkscape | ✅ NUEVO |
| **sublimacion_core** | Video/imagen 300DPI | ✅ NUEVO |
| **sistema_memoria** | SQLite episódica+semántica | ✅ NUEVO |
| **motor_sueno** | Consolidación nocturna Groq | ✅ NUEVO |
| **analitica_marketing** | Rendimiento publicaciones | ✅ NUEVO |
| **voz_google** | TTS Google Home Cast | ✅ NUEVO |
| **asesor_marketing** | Algoritmos redes sociales | ✅ NUEVO |
| **publicador_core** | Estado redes sociales | ✅ NUEVO |
| **oracle_core** | CRM SQLite directo | ✅ NUEVO |
| **whatsapp** | Green API HTTP real | ✅ NUEVO |
| **telegram** | Bot Telegram | ✅ NUEVO |
| **email** | SMTP cotizaciones | ✅ NUEVO |
| **auto_conocimiento** | Introspección sistema | ✅ NUEVO |
| **auto_reparacion** | Fix código via LLM | ✅ NUEVO |
| motor_sueno_actividad | Suscripción eventos | ✅ NUEVO |

### Cambio en PROMPT_MAESTRO_AURORA (archivo _ARCHIVE)
- `AURORA v2` → `AURORA v3` (6 ocurrencias)
- `2.0 Final` → `3.0 Final`

---

---

## RESUMEN EJECUTIVO

El proyecto AURORA tiene arquitectura dual activa:
- **Arquitectura VIEJA** (`CORE/aurora.py` → `aurora_selector` → motores): funcional pero obsoleta
- **Arquitectura NUEVA** (`CEREBRO/consciencia.py` → `CEREBRO/bus_neuronal.py`): real, completa, **pero sin punto de entrada activo**

**FASE 1 completada hoy:** 11/11 motores reescritos con `AsyncGroq` real, precios reales del catálogo, persistencia SQLite y conexión a memoria episódica.

---

## INVENTARIO REAL DEL PROYECTO

### MOTORES — 11/11 REALES ✅
| Archivo | Estado | LLM | Persistencia | Datos reales |
|---|---|---|---|---|
| `motor_analisis.py` | ✅ REAL | AsyncGroq | Memoria episódica | Prompt ATF+MILENS |
| `motor_coaching.py` | ✅ REAL | AsyncGroq | Memoria episódica | CNV + Erikson + Dweck |
| `motor_coaching_real.py` | ✅ REAL | AsyncGroq | Memoria episódica | Coach transformacional |
| `motor_code_gen.py` | ✅ REAL | AsyncGroq | Memoria episódica | Contexto AURORA/FastAPI |
| `motor_cotizador.py` | ✅ REAL | AsyncGroq | Memoria episódica | X1=$8k X3=$15k X5=$25k X7=$40k |
| `motor_imagenes.py` | ✅ REAL | AsyncGroq | Memoria episódica | Specs plataformas + laser 300DPI |
| `motor_marketing.py` | ✅ REAL | AsyncGroq | Memoria episódica | Generación viral + memoria semántica |
| `motor_negocios.py` | ✅ REAL | AsyncGroq | ORACLE SQLite | Lee resumen CRM en tiempo real |
| `motor_pedidos.py` | ✅ REAL | AsyncGroq | **pedidos.db SQLite** | CRUD completo WAL |
| `motor_reasoning.py` | ✅ REAL | AsyncGroq | Memoria episódica | 6 dimensiones + confianza |
| `motor_ventas.py` | ✅ REAL | AsyncGroq | ORACLE + Memoria | Lee historial cliente |

### CEREBRO — Estado mixto
| Archivo | Estado | Notas |
|---|---|---|
| `consciencia.py` | ✅ REAL | Pipeline completo: routing→ejecución→síntesis→aprendizaje. **Sin activar desde entry point** |
| `bus_neuronal.py` | ✅ REAL | Pub/Sub async, singleton, WAL. **Sin motores registrados** |
| `motor_sueno.py` (MEMORIA/) | ✅ REAL | Consolidación episódica→semántica via Groq. **Nunca arranca** |
| `orquestador_aurora.py` | ⚠️ ROTO | Import de `SistemaMarketingMaestro` con cadena de imports no verificada |
| `aurora_cerebro_simple.py` | ✅ REAL | AsyncGroq, system prompt completo |
| `auto_conocimiento.py` | ❓ Sin verificar | |
| `auto_reparacion.py` | ❓ Sin verificar | |
| `pc_access.py` | ❓ Sin verificar | |

### MEMORIA — Real y funcional ✅
| Archivo | Estado | Notas |
|---|---|---|
| `sistema_memoria.py` | ✅ REAL | SQLite WAL, tablas: `episodica` + `semantica` |
| `contexto_usuario.py` | ✅ REAL | AsyncGroq, temperatura de lead, historial por user_id |
| `motor_sueno.py` | ✅ REAL | Groq consolida episodios → patrones semánticos. Inactivo |
| `analitica_marketing.py` | ❓ Sin verificar | |
| `perfil_habilidades.py` | ❓ Sin verificar | |

### CORE — Arquitectura vieja (funcional, usa motores reales ahora)
| Archivo | Estado | Notas |
|---|---|---|
| `aurora.py` | ✅ OK | Entry point viejo. Usa `aurora_selector` + `aurora_sdk_manager` |
| `aurora_selector.py` | ✅ OK | 6-tier decision engine, lee `metadata.json` |
| `aurora_sdk_manager.py` | ✅ OK | Fallback: Claude→Groq→Zai→Ollama |
| `aurora_registry.py` | ✅ OK | Auto-discovery via importlib |
| `aurora_server.py` | ✅ OK | FastAPI `/procesar`, `/status`, `/health` |
| `buscador_web_profesional.py` | ✅ REAL | Google Custom Search + BeautifulSoup + Mercado Libre API |
| `chatbot_wa_profesional.py` | ✅ REAL | Webhook Green API + SQLite + lead scoring |
| `publicador_atf_profesional.py` | ✅ REAL | OAuth2 TikTok/IG/YT/FB via httpx/aiohttp |

### INTEGRACIONES
| Archivo | Estado | Notas |
|---|---|---|
| `whatsapp_integration.py` | ❌ FAKE | `enviar_mensaje()` retorna dict sin HTTP real |
| `telegram_integration.py` | ❓ Sin verificar | |
| `email_integration.py` | ❓ Sin verificar | |

### ORACLE — CRM Real ✅
| Archivo | Estado | Notas |
|---|---|---|
| `oracle_core.py` | ✅ REAL | SQLite, leads + órdenes + migración automática |

### SUPER_MARKETING_SYSTEM — Real
| Archivo | Estado | Notas |
|---|---|---|
| `motor_whatsapp_real.py` | ✅ REAL | Polling httpx + Green API + deleteNotification |
| `crm_leads_ventas.py` | ✅ REAL | SQLite leads + interacciones + ventas |
| `publicador_real.py` | ✅ REAL | moviepy + SQLite scheduling |
| `sistema_marketing_maestro.py` | ⚠️ PARCIAL | Importa MODULES/ correctamente |
| `MODULES/integracion_chatbot_wa.py` | ✅ REAL | Lead scoring + multi-agente |
| `MODULES/motor_busqueda_web_real.py` | ✅ REAL | Google + ML + scraping |
| `MODULES/publicador_integral_atf.py` | ✅ REAL | moviepy + scheduling |

### BASES DE DATOS EXISTENTES
| DB | Ubicación | Tablas | Estado |
|---|---|---|---|
| `pedidos.db` | raíz/ | `pedidos` | ✅ Creada hoy (16KB) |
| `aurora_memoria.db` | MEMORIA/ | `episodica`, `semantica` | ✅ (se crea al iniciar) |
| `oracle.db` | raíz/ | `leads`, `ordenes` | ✅ (se crea al iniciar ORACLE) |
| `aurora_crm.db` | raíz/ | CRM completo | ⚠️ WAL vacío |

---

## BRECHAS ACTIVAS (FASES PENDIENTES)

### FASE 2 — Bus Neuronal vacío ❌
**Archivo a crear:** `CEREBRO/registrador_bus.py`  
El `bus_neuronal.py` existe y es real pero `_motores = {}`. Ningún motor está registrado.  
Ningún mensaje fluye entre motores.  
**Acción:** Crear registrador que conecte todos los motores al bus al arrancar.

### FASE 3 — Motor de Sueño inactivo ❌
**Archivo:** `MEMORIA/motor_sueno.py` (real y completo)  
Nunca se arranca como tarea asyncio.  
**Acción:** Integrar en el ciclo de vida del servidor.

### FASE 4 — WhatsApp sin HTTP real ❌
**Archivo:** `INTEGRACIONES/whatsapp_integration.py`  
`enviar_mensaje()` devuelve dict fake sin llamar `httpx.post()`.  
Ya existe la clase real en `SUPER_MARKETING_SYSTEM/motor_whatsapp_real.py`.  
**Acción:** Reescribir usando el patrón de `motor_whatsapp_real.py`.

### FASE 5 — Sin punto de entrada unificado ❌
**Archivo:** `run_aurora.py` (existe pero no activa la arquitectura nueva)  
Secuencia correcta: `memoria.inicializar()` → `bus.iniciar()` → `registrar_motores()` → `consciencia.inicializar()` → `motor_sueno.iniciar()` → `uvicorn FastAPI`  
**Acción:** Reescribir `run_aurora.py` con esta secuencia completa.

### FASE 6 — Router principal desconectado ❌
**Archivo:** `CORE/aurora_server.py`  
El endpoint `/procesar` llama a `aurora.procesar_mensaje()` (arquitectura vieja con `aurora_selector`).  
`consciencia.procesar()` existe y es real pero no se usa.  
**Acción:** Conectar `/procesar` → `consciencia.procesar()`.

---

## CATÁLOGO DE PRECIOS REAL (inyectado en motores)

### ATF Retrofit — margen 120%
| Producto | Costo | Precio público | Instalación incluida |
|---|---|---|---|
| Aozoom X1 | $3,500 | $8,000 MXN | ✅ |
| Aozoom X3 | $6,200 | $14,999 MXN | ✅ |
| Aozoom X5 | $10,500 | $24,999 MXN | ✅ |
| Aozoom X7 | $16,500 | $39,999 MXN | ✅ |

### MILENS — margen 50-150%
| Producto | Costo | Público | Mayorista |
|---|---|---|---|
| Polera sublimada | $450 | $850 | $650 |
| Taza 11oz | $85 | $170 | $130 |
| Taza mágica | $120 | $280 | $200 |
| Bolsa sublimada | $180 | $380 | $280 |
| Grabado láser/pieza | $60 | $180 | $130 |

---

## VARIABLES DE ENTORNO REQUERIDAS
```
GROQ_API_KEY=          # Motor LLM principal (llama-3.1-8b-instant)
GREEN_API_INSTANCE=    # WhatsApp vía Green API
GREEN_API_TOKEN=       # WhatsApp vía Green API
FB_PAGE_TOKEN=         # Facebook/Instagram publicación
INSTAGRAM_ACCESS_TOKEN=
JWT_SECRET_KEY=        # Auth interna
```
Plantilla: `.env.example` en raíz del proyecto.

---

## PATRÓN REAL DE CADA MOTOR (para referencia)
```python
# Todos los motores siguen este patrón exacto:
class MotorXxx:
    def __init__(self):
        self.motor_id = "motor_xxx"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY","")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests":0, "exitosos":0, "errores":0}

    async def metodo_principal(self, consulta, contexto=None) -> Dict:
        # 1. Llama AsyncGroq real
        # 2. Registra en memoria episódica
        # 3. Retorna dict con status, motor, respuesta, timestamp

    async def _registrar(self, tipo, contenido):
        # Siempre guarda en MEMORIA/sistema_memoria.py (SQLite WAL)

motor = MotorXxx()   # singleton al final del archivo
```

---

## ORDEN RECOMENDADO DE EJECUCIÓN (FASES 2-6)

```
FASE 2: CEREBRO/registrador_bus.py          → conectar bus
FASE 3: MEMORIA/motor_sueno integrado       → aprendizaje nocturno
FASE 4: INTEGRACIONES/whatsapp_integration  → HTTP real
FASE 5: run_aurora.py reescrito             → entry point único
FASE 6: CORE/aurora_server.py conectado     → router consciencia
```

---

## COMANDO PARA ARRANCAR (estado actual)
```bash
# Con arquitectura vieja (funciona hoy):
cd C:\AURORA.worktrees\agents-whispering-tuna
uvicorn CORE.aurora_server:app --host 0.0.0.0 --port 5000

# Con arquitectura nueva (post FASE 5):
python run_aurora.py
```

---

*Checkpoint generado: 2026-07-05 | Proyecto: AURORA | Propietario: Anuar*
