# 📋 PENDIENTES, MOTOR POR MOTOR
### Levantado el 2026-08-19 leyendo el código, no la memoria
### ACTUALIZADO 2026-08-20 — ver aviso abajo, dos puntos ya no aplican

Los 28 que dice el panel salen de `CEREBRO/registrador_bus.py`. Esta lista los
recorre uno por uno y dice qué le falta a cada quien.

**Cómo se midió:** los nombres salen del registro real del bus; la columna
«panel» se buscó en `TEMPLATES/panel-completo.html` por texto, así que es una
señal, no una prueba — hay que confirmar mirando la pestaña.

---

## ✅ ACTUALIZACIÓN 2026-08-20 — dos puntos de este documento ya se cerraron

1. **El bloque de abajo ("10 módulos nuevos que NO están en el bus") ya no
   aplica a 7 de los 9 reales** (`plantilla_prenda`/`flat_prenda` combo y
   `cotizador_vinil` seguían aparte del resto). Se conectaron y se probaron
   EN VIVO por el bus real (`bus.solicitar`, no solo `--lista` de consola):
   `etiquetas`, `estratega_shorts`, `analizador_mercado`, `buscador_clientes`,
   `licencias`, `plugins_catalogo`, `texto_a_corte`. El bus pasó de 27 a 35
   registrados. De paso se encontró y arregló un bug real: `plugins.catalogo()`
   tenía el mismo error que ya se había corregido en `buscar()` («'str' object
   has no attribute 'get'» por fichas con `acciones` como diccionario) — nunca
   se le aplicó el mismo arreglo. Ya está corregido de raíz con una función
   compartida (`_pares_acciones`), probado por el bus.
2. **`motor_cotizador` (el «lo más grave» de la lista de abajo) ya no cobra
   de más.** Confirmado en código real: `EDITOR/cotizador_corte.py` y
   `TALLER/cotizador_vinil.py` SÍ leen `TALLER/formula_precios.py` — una sola
   fórmula, un solo lugar. Ver [[formula_precios_anuar]] para el detalle.

El resto de este documento (fichas de vendedor, RAM, RDWorks, etc.) no se
volvió a medir hoy — puede seguir igual.

---

## 🚨 LO PRIMERO (ESTADO VIEJO, 2026-08-19): hay 10 módulos nuevos que NO están en el bus

Se construyeron en las últimas dos semanas, **funcionan y están probados**,
pero `registrador_bus.py` no los conoce. Se comprobó buscando sus nombres en
ese archivo: **cero coincidencias.**

Eso significa que AURORA **no los puede usar desde el chat** aunque el código
esté ahí. Es el pendiente más grande y el más barato de cerrar.

| Módulo | Qué hace | Cómo se abre hoy |
|---|---|---|
| `TALLER/etiquetas.py` | Etiquetas con QR, lote y suaje | app suelta / terminal |
| `MARKETING/estratega_shorts.py` | Si un canal deja dinero o no | terminal |
| `MERCADO/analizador_mercado.py` | Rentabilidad por canal de venta | app suelta |
| `MERCADO/buscador_clientes.py` | 401,813 negocios del INEGI | app suelta |
| `LICENCIA/licencias.py` | Licencias de 3 meses | solo por código |
| `CEREBRO/plugins.py` | El catálogo de apps | solo por código |
| `EDITOR/plantilla_prenda.py` + `flat_prenda.py` | Siluetas de prenda | app suelta |
| `TALLER/cotizador_vinil.py` | Precio de vinil (ya tiene candado) | chat ✅ |
| `EDITOR/texto_a_corte.py` | Palabras a corte con soldado | sin probar en vivo |

**Lo que falta:** o meterlos al registrador, o —mejor— que el registrador lea
las fichas de `PLUGINS/*.json` y los cargue solo. Con lo segundo, cada app
nueva se conecta sola y esto no vuelve a pasar.

---

## Los 28 del bus, uno por uno

### MOTORES/ — los diez de lenguaje

| Motor | Panel | Qué le falta |
|---|---|---|
| `motor_cotizador` | sí | **El más grave.** No usa la fórmula real de Anuar. Medido: daba **$284 y $538** donde la cuenta correcta era **$180**. Toca cablearlo a `(materiales × 1.20) + corte $8/min + diseño`. |
| `motor_imagenes` | sí | **Ya se puede cerrar.** La llave de Gemini tiene `nano-banana-pro-preview` y `gemini-3-pro-image`. Falta escribir el módulo que las llame. Cierra el pendiente viejo de «generar imágenes con IA». |
| `motor_ventas` | sí | Se encima con `ORACLE` y `VENDEDOR/seguimiento_ventas`. **Son tres sistemas de venta**; hay que quedarse con uno. |
| `motor_analisis` | sí | No conoce `MERCADO/analizador_mercado.py`, que es el que sí tiene los números de comisiones y punto de equilibrio. |
| `motor_marketing` | sí | No conoce `estratega_shorts` ni las campañas nuevas. |
| `motor_coaching` | **NO** | Sin panel y sin uso conocido. Viene de la época de Evolución/Teens. **Decisión pendiente de Anuar:** ¿se queda o se archiva? Yo no lo quito. |
| `motor_coaching_real` | **NO** | Igual que el anterior. |
| `motor_negocios` | **NO** | Sin panel. Se encima con el asesor de negocio. |
| `motor_reasoning` | **NO** | Sin panel. Es el que razona; vale confirmar si de verdad se usa o el chat lo esquiva. |
| `motor_code_gen` | **NO** | Sin panel. Es la pieza de la Fábrica/IDE. Ligado al pendiente del **contrato del motor (`motor.json`)** — sin eso, separar la Fábrica es cosmético. |

### ORACLE/ y VENDEDOR/

| Motor | Panel | Qué le falta |
|---|---|---|
| `oracle_core` | sí | Parte del solape de tres sistemas de venta. |
| `motor_oracle` | sí | Idem. |
| `vendedor_core` | sí | **Fichas de vendedor: 4 de 29 completas.** Y la de LED H4 tiene una incoherencia real (el texto menciona H7). |
| `verificador_core` | **NO** | Mide **un solo espesor**; falta que mida varios. Falta detectar muescas al borde. Y en Calamardo quedaron **~20 encastres sin reconocer** de ~50. |

### TALLER/ y SUBLIMACION/

| Motor | Panel | Qué le falta |
|---|---|---|
| `taller_core` | sí | El cotizador láser ya tiene desperdicio. Falta **Inventario Fase 2** y capturar más productos. |
| `sublimacion_core` | **NO** | Sin panel. Y los parámetros de MDF (190–200 °C / 50–70 s) no están adentro; hoy viven en el recetario. |

### MEMORIA/

| Motor | Panel | Qué le falta |
|---|---|---|
| `sistema_memoria` | **NO** | Sin panel. |
| `motor_sueno` | señal débil | Es el auto-reparador nocturno. Confirmar que la pestaña existe de verdad. |
| `analitica_marketing` | **NO** | Sin panel. |

### VOZ/

| Motor | Panel | Qué le falta |
|---|---|---|
| `voz_google` | **NO** | Solo saca voz (TTS de Google Cast). **La voz completa de NEXUS ya existe y está rescatada** en la USB (`voice_service.py`: escucha es-MX, VOSK local, Whisper de Groq, gTTS mexicano). **No hay que construirla, hay que portarla.** Y al portarla, que la voz pase por el validador de honestidad y confirme por voz lo irreversible. Ligado al **asistente de configuración inicial por voz**, que es la pieza que vuelve vendible a AURORA. |

### MARKETING/ y PUBLICADOR/

| Motor | Panel | Qué le falta |
|---|---|---|
| `asesor_marketing` | **NO** | Sin panel. |
| `publicador_core` | sí | Tres pendientes concretos: **mover el video ya publicado a PUBLICADOS**, **depurar 169 duplicados**, y **definir cuál es el Instagram de ATF**. TikTok y YouTube siguen **sin llave**. |

### INTEGRACIONES/

| Motor | Panel | Qué le falta |
|---|---|---|
| `whatsapp` | sí | **Green API gratis solo manda a 3 números.** La salida ya escrita es `MARKETING/campana_por_whatsapp_web.py`. Falta `WA_RECORDATORIO` en el `.env`. |
| `telegram` | **NO** | Sin panel. Confirmar si tiene llave o está muerto. |
| `email` | **NO** | Sin panel. Igual: confirmar si funciona. |

### CEREBRO/

| Motor | Panel | Qué le falta |
|---|---|---|
| `auto_conocimiento` | **NO** | Sin panel. |
| `auto_reparacion` | **NO** | Sin panel. Cuidado: es el que **podía borrar el 96% de `consciencia.py`** — ya arreglado, pero no se toca sin pruebas. |

---

## Fuera de los motores, pero pendiente

1. **RDWorks se sigue trabando.** Sin resolver. No es AURORA.
2. **Faltan 6.5 GB de RAM por explicar.** Cerrar AURORA solo liberó 0.1 GB, así
   que no es ella. Hay que encontrar quién se los come.
3. **Precios de los 7 servicios ATF** — los dicta Anuar, nadie más.
4. **Distribución:** instalador local + auto-actualización. Hoy cada cliente es
   una instalación a mano.
5. **Demo de AURORA con comandos normalizados** — lo único que puede traer
   dinero pronto.
6. **La campaña escolar está lista y NO se ha enviado**: 21 clientas reales con
   teléfono, 4 paquetes de Rocío. Falta el OK de Anuar.
7. **Corel no exporta PNG/JPG** por pywin32 (PDF sí, al 100%).
8. **`vectoriza` no corre directo** — pasa por el enrutador. Y el enrutador
   prefiere `leer_archivo` sobre `abrir_archivo`.
9. **Una ruta sola no completa la petición previa** (2 hipótesis ya descartadas).
10. **Motor Print&Cut** y **nesting** (Deepnest es GPL, ojo con la licencia).
11. **Alertas de pendientes (Trabajo 12)** — el plan ya está escrito en
    `.claude/plans/mellow-frolicking-canyon.md`; se generaliza el modal de
    Taller, no se construye de cero.

---

## Si hay que escoger tres

1. **Cablear los 10 módulos nuevos al bus** — es trabajo hecho que hoy no se
   puede usar desde el chat. El mejor rendimiento por hora.
2. **Arreglar `motor_cotizador`** — está cobrando de más. Eso cuesta ventas
   hoy, no en abstracto.
3. **Cerrar `motor_imagenes` con nano-banana** — la llave ya está pagada y
   destraba el mousepad y las artes del taller.
