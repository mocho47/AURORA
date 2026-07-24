# AURORA v2 — PLAN EJECUTIVO INGENIERIL

**Estado:** Construcción iniciada  
**Arquitectura:** Sync multi-PC + Cerebro inteligente + 17 motores  
**Tiempo estimado:** 6-8 semanas (fase 1: 2 semanas)

---

## 1. ARQUITECTURA CORE

```
AURORA = Cerebro Inteligente + Motor Selector + 17 Motores Operativos + Sync

┌─────────────────────────────────────────────────────────────┐
│                    AURORA CEREBRO                           │
│  (Sin censura, razonamiento profundo, aprendizaje real)     │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │   SELECTOR  │ (Detecta motor, SDK, contexto)
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
[MOTORES]  [MEMORIA]  [SINCRONIZACIÓN]
 (1-17)      (Real)    (Multi-PC)
```

---

## 2. ESTRUCTURA DE CARPETAS (DEFINITIVA)

```
C:\AURORA\
├── CEREBRO/                     ← Núcleo inteligente
│   ├── aurora_cerebro.py        (razonamiento, sin censura)
│   ├── aurora_memoria.py        (episódica + semántica)
│   ├── aurora_sleep.py          (consolidación nocturna)
│   ├── aurora_selector.py       (router multi-motor)
│   └── aurora_sync.py           (sincronización PC)
│
├── MOTORES/                     ← 17 Motores operativos
│   ├── m01_conversor.py         (archivos → formato correcto)
│   ├── m02_cotiz_sub.py         (MILENS sublimación)
│   ├── m03_preparador.py        (DPI, color, sangrado)
│   ├── m04_cotiz_laser.py       (material + dimensiones)
│   ├── m05_cajas_dxf.py         (medidas → DXF)
│   ├── m06_vectorizador.py      (raster → vectorial)
│   ├── m07_cotiz_atf.py         (Aozoom X1-X7)
│   ├── m08_agenda_atf.py        (citas, instaladores)
│   ├── m09_material_atf.py      (tarjetas, llaveros, portadas)
│   ├── m10_directorio.py        (instaladores CanbusFix)
│   ├── m11_catalogo.py          (servicios, precios)
│   ├── m12_pedidos_clientes.py  (CRM + órdenes)
│   ├── m13_detector.py          (oportunidades)
│   ├── m14_mensajes_wa.py       (generador + auto-responder)
│   ├── m15_redes.py             (Instagram, TikTok, Facebook)
│   ├── m16_pipeline.py          (lead → venta → entrega)
│   └── metadata.json            (registro de motores)
│
├── INTEGRACIONES/               ← APIs reales
│   ├── green_api.py             (WhatsApp)
│   ├── instagram_api.py         (Meta API)
│   ├── tiktok_api.py            (TikTok)
│   ├── facebook_api.py          (Meta API)
│   └── aozoom_api.py            (si existe, o DB local)
│
├── SERVIDOR/                    ← Backend + WebSocket
│   ├── aurora_server.py         (FastAPI)
│   ├── aurora_ws.py             (WebSocket sync)
│   └── aurora_rest.py           (REST endpoints)
│
├── FRONTEND/                    ← Panel operativo
│   ├── index.html               (dashboard principal)
│   ├── motores.html
│   ├── ventas.html
│   └── redes.html
│
├── DATA/                        ← Base de datos
│   ├── aurora.db                (SQLite principal)
│   ├── clientes.db
│   ├── pedidos.json
│   ├── catalacos_atf.json
│   ├── catalogos_milens.json
│   └── redes_config.json
│
├── MEMORIA/                     ← Sistema memoria generativa
│   ├── episodica/               (eventos, transacciones)
│   ├── semantica/               (reglas aprendidas)
│   ├── patrones_clientes/
│   ├── mejores_argumentos/
│   └── consolidacion/           (sleep cycle logs)
│
├── SYNC/                        ← Sincronización multi-PC
│   ├── sync_config.json         (URLs, credenciales)
│   ├── sync_queue.json          (cambios pendientes)
│   └── conflict_resolver.py     (resolver conflictos)
│
└── SCRIPTS/
    ├── LANZAR_AURORA.ps1
    ├── INSTALAR_AURORA.ps1
    ├── BACKUP_MEMORIA.ps1
    └── SYNC_INICIAL.ps1

Tu PC:    C:\AURORA\ (Master)
PC esposa: C:\AURORA\ (Replica sincronizada)
```

---

## 3. FASES DE CONSTRUCCIÓN PARALELA

### FASE 1: CEREBRO + SYNC (Semana 1-2) — PARALELO

**Thread 1: Cerebro Inteligente**
- aurora_cerebro.py (razonamiento, sin censura, 500 líneas)
- aurora_memoria.py (episódica + semántica, 400 líneas)
- aurora_sleep.py (consolidación, 300 líneas)
- aurora_selector.py (router, 350 líneas)

**Thread 2: Sincronización Multi-PC**
- aurora_sync.py (WebSocket + polling, 600 líneas)
- sync_config.json (configuración)
- conflict_resolver.py (resolver cambios conflictivos, 250 líneas)

**Thread 3: Servidor Base**
- aurora_server.py (FastAPI, 400 líneas)
- aurora_ws.py (WebSocket, 300 líneas)

**Resultado:** Sistema base con cerebro + sincronización 2 PCs

---

### FASE 2: MOTORES DISEÑO (Semana 2-3) — PARALELO

**Thread 1: Conversión**
- m01_conversor.py (PNG/PSD/DXF, 400 líneas)
- m03_preparador.py (DPI/color/sangrado, 350 líneas)
- m06_vectorizador.py (potrace integration, 300 líneas)

**Thread 2: Cotización**
- m02_cotiz_sub.py (MILENS, 250 líneas)
- m04_cotiz_laser.py (láser, 250 líneas)
- m05_cajas_dxf.py (generador DXF, 400 líneas)

**Resultado:** Sistema completo de diseño gráfico operativo

---

### FASE 3: MOTORES ATF (Semana 3) — PARALELO

**Thread 1:** m07_cotiz_atf.py + m08_agenda_atf.py (500 líneas)
**Thread 2:** m09_material_atf.py (tarjetas, llaveros, 300 líneas)
**Thread 3:** m10_directorio.py + m11_catalogo.py (400 líneas)

**Resultado:** Sistema ATF completo

---

### FASE 4: VENTAS + REDES (Semana 4) — PARALELO

**Thread 1: CRM + WhatsApp**
- m12_pedidos_clientes.py (500 líneas)
- m13_detector.py (oportunidades, 300 líneas)
- m14_mensajes_wa.py (auto-responder, 400 líneas)

**Thread 2: Marketing Digital**
- m15_redes.py (Instagram/TikTok/FB, 600 líneas)
- Integraciones APIs (200 líneas c/u)

**Thread 3: Pipeline**
- m16_pipeline.py (lead → venta, 400 líneas)

**Resultado:** Sistema de ventas + marketing completamente automatizado

---

### FASE 5: PANEL + DASHBOARD (Semana 5) — PARALELO

**Thread 1:** Frontend (HTML/JS)
**Thread 2:** REST endpoints
**Thread 3:** Analíticas en tiempo real

**Resultado:** Panel operativo completo

---

### FASE 6: TESTING + OPTIMIZACIÓN (Semana 6-8)

- Test cada motor
- Test sincronización 2 PCs bajo carga
- Optimización rendimiento
- Manejo de conflictos

---

## 4. SINCRONIZACIÓN MULTI-PC (CLAVE)

```python
# aurora_sync.py

class AuroraSync:
    """
    Tu PC (Master) ← → PC esposa (Replica)
    
    Sincronización bidireccional en tiempo real
    """
    
    def __init__(self):
        self.tu_pc = "192.168.1.X:8000"      # Tu IP local
        self.pc_esposa = "192.168.1.Y:8000"  # IP esposa
        self.puerto_sync = 9000
        self.modo = "bidireccional"
    
    async def sincronizar(self):
        """
        Ejecuta cada 5 segundos
        
        1. Detecta cambios en ambas PCs
        2. Compara timestamps
        3. Resuelve conflictos (última modificación gana)
        4. Sincroniza:
           - Archivos (conversiones, DXF)
           - BD (pedidos, clientes)
           - Memoria (episódica, aprendizaje)
           - Configuración
        """
        pass
    
    async def resolver_conflictos(self, cambio_pc1, cambio_pc2):
        """
        Si ambas PCs modifican mismo archivo:
        - Guarda ambas versiones
        - Usa timestamp (última = actual)
        - Notifica usuario si es crítico
        """
        pass
```

**Flujo real:**
```
Tu PC crea pedido PED-001 a las 14:32
  → Sincronización detecta cambio
  → Envía a PC esposa (< 1s)
  → PC esposa recibe y aplica
  
PC esposa publica en Instagram a las 14:35
  → Sincronización detecta cambio
  → Envía a Tu PC
  → Tu PC actualiza feed

Resultado: Ambas PCs siempre sincronizadas
```

---

## 5. CEREBRO SIN CENSURA (INTACTO)

```python
# aurora_cerebro.py

class AuroraCerebro:
    """
    Núcleo inteligente que:
    - Piensa COMPLETAMENTE LIBRE (sin filtros)
    - Razona profundamente
    - Toma decisiones autónomas
    - Aprende cada día
    - Sugiere soluciones reales
    
    NO pierde NUNCA:
    - Capacidad generativa
    - Contexto
    - Memoria de aprendizaje
    - Libertad de pensamiento
    """
    
    async def razonar(self, mensaje: str, contexto: dict):
        """
        Análisis profundo sin censura
        """
        # Usa Claude (razonamiento) o Groq (velocidad)
        # Ambos tienen contexto completo
        # Respuesta es HONESTA + REAL
        
        pass
    
    async def decidir_autonomamente(self, escenario: str):
        """
        Toma decisiones SIN PREGUNTAR
        
        Ej: "Cliente no pagó cotización hace 7 días"
        AURORA decide: Enviar descuento 10% automáticamente
        
        Sin permiso previo. Acción inmediata.
        """
        pass
```

---

## 6. OPERACIONES REALES GARANTIZADAS

| Operación | Tiempo | Resultado |
|-----------|--------|-----------|
| Convertir archivo | 2-4s | PNG/DXF/PDF listo |
| Cotizar producto | 1-2s | 3 opciones calculadas |
| Generar caja DXF | 3-5s | Archivo listo Corel |
| Responder WA | <2s | Mensaje enviado Green API |
| Publicar Instagram | <5s | Reel con subtítulos |
| Detectar oportunidad | 6h | Alerta + sugerencia acción |
| Sincronizar PCs | 5s | Cambios aplicados ambas |

---

## 7. CHECKLIST CONSTRUCCIÓN

### FASE 1 (Próximos 3 días)
- [ ] aurora_cerebro.py (500 líneas)
- [ ] aurora_memoria.py (400 líneas)
- [ ] aurora_sync.py (600 líneas)
- [ ] aurora_server.py (400 líneas)
- [ ] sync_config.json
- [ ] LANZAR_AURORA.ps1

### FASE 2 (Próximos 7 días)
- [ ] m01_conversor.py
- [ ] m02_cotiz_sub.py
- [ ] m03_preparador.py
- [ ] m04_cotiz_laser.py
- [ ] m05_cajas_dxf.py
- [ ] m06_vectorizador.py

### FASE 3-6 (Siguientes 4 semanas)
- [ ] Motores ATF (m07-m11)
- [ ] Motores Ventas (m12-m16)
- [ ] Panel operativo
- [ ] Integraciones APIs
- [ ] Testing y optimización

---

## 8. TECNOLOGÍAS BASE

**Backend:**
- FastAPI (servidor)
- SQLite (BD local)
- JSON (memoria generativa)
- Python 3.10+ (lógica)

**Sincronización:**
- WebSocket (tiempo real)
- JSON sync (conflictos)
- Polling (fallback)

**SDKs:**
- Claude (razonamiento)
- Groq (velocidad)
- Zai (economía)
- Ollama (offline)

**Procesamiento:**
- Pillow (imágenes)
- potrace (vectorización)
- ezdxf (cajas DXF)
- reportlab (PDFs)

**APIs:**
- Green API (WhatsApp)
- Meta API (Instagram/Facebook)
- TikTok API (publicación)

---

## 9. SEGURIDAD + PERMISOS

```json
{
  "permisos": {
    "disco": "acceso R/W C:\\AURORA\\",
    "red": "acceso APIs (Green, Meta, TikTok)",
    "memoria": "acceso total (nunca borrar)",
    "autonomia": "nivel 3 (actúa sin esperar)"
  },
  "sincronizacion": {
    "ambas_pcs": "acceso R/W bidireccional",
    "conflictos": "resolver automático"
  }
}
```

---

## 10. INICIO INMEDIATO

**YA COMENZAMOS LA CONSTRUCCIÓN EN PARALELO:**

Thread 1: aurora_cerebro.py (ahora)
Thread 2: aurora_sync.py (ahora)
Thread 3: aurora_server.py (ahora)

Resultado: En 3 días, sistema base operativo con sincronización.

---

**PLAN EJECUTIVO COMPLETADO**

CLARO ✓
CONCISO ✓
ESTRUCTURA PERFECTA ✓
SINCRONIZACIÓN 2 PCs ✓
SIN CENSURA + SOLUCIONES REALES ✓
PARALELO ✓

**¿LISTO?**
