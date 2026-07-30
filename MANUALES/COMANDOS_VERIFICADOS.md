# Comandos VERIFICADOS de AURORA

**Esta lista es distinta al manual general.** Aquí solo van los comandos que se **probaron en vivo, contra el sistema real**, durante la auditoría de Fase 3 (2026-07-28/29) y que **respondieron correctamente**. Cada uno se ejecutó de verdad y se comprobó el resultado.

Si un comando no está en esta lista, no significa que no funcione — significa que **no se probó**, y ahí sí hay que verificarlo antes de confiar.

Actualizado: 2026-07-29 · 17 candados directos · 516 herramientas en el enrutador

---

## 🎨 Corel (probado con Corel abierto de verdad)

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `corel abre esta imagen C:\ruta\foto.jpg` | Importa la imagen al documento activo (crea uno si no hay) | ✅ con archivo de nombre largo y con espacios |
| `corel abre C:\ruta\archivo.pdf` | Abre PDF/CDR/AI dentro de Corel | ✅ |
| `corel extrae el texto del documento` | Lee todo el texto real del diseño abierto y cuenta los adornos | ✅ |
| `corel cierra el documento` | Cierra sin guardar | ✅ |
| `corel escala la pagina a 20x30 cm` | Cambia el tamaño de página (crea documento si no hay) | ✅ |
| `corel exporta a pdf` | Exporta a `Escritorio\PDFs a Impresion` | ✅ 376 KB real |
| `corel guarda una copia en C:\ruta\copia.cdr` | Copia sin tocar el original | ✅ 12.8 KB real |
| `arregla la conexión con corel` · `corel no responde` | Repara el caché corrupto y **confirma** reconectando | ✅ verificado contra Corel |

⚠️ **Exportar a PNG/JPG desde Corel no funciona** — limitación real conocida, documentada. Usa PDF, o exporta a mano desde Corel.

---

## 📅 Agenda

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `que tengo agendado hoy` | Citas de HOY (antes daba un resumen general, arreglado) | ✅ |
| `que tengo agendado manana` | Citas de mañana | ✅ |
| `proximas citas` | Lo que viene en 24 h | ✅ |
| `agenda una cita para Juan Perez el 2026-08-01 a las 14:00 tipo cita, tel 3312345678` | Agenda de verdad | ✅ creó la cita real |
| `agendame una cita` (sin datos) | Pide lo que falta, **no inventa** | ✅ |

Tipos válidos: `instalacion`, `entrega`, `cita`, `cotizacion`.

---

## 🧠 Sobre sí misma

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `autodescríbete a detalle` · `qué puedes hacer` · `cuántas herramientas tienes` | Da sus datos **reales** (candados, herramientas, módulos, integraciones y sus límites) | ✅ — antes inventaba capacidades falsas |

---

## 🔧 Taller y diseño

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `convierte a dxf C:\ruta\archivo.svg` | SVG/AI/EPS → DXF | ✅ ruta con espacios y paréntesis |
| `vectoriza C:\ruta\imagen.png` | Traza la imagen y genera SVG + DXF | ✅ (avisa si el DXF sale vacío) |

⚠️ **PDF que solo trae una imagen adentro:** AURORA ahora lo detecta y avisa que hay que vectorizarlo, en vez de entregar un DXF vacío diciendo "OK". Si el PDF tiene varias páginas, se puede vectorizar por página.

---

## 💰 Negocio y cotización

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `cuánto llevo vendido este mes` · `cómo va la contabilidad` | Cifras reales del taller | ✅ |
| `qué órdenes tengo pendientes` | Órdenes reales | ✅ |
| Cotizar tazas/termos/playeras | Usa el catálogo de **Milens** (73 servicios) | ✅ detecta el negocio solo |
| Cotizar faros/lupas/LED | Usa el catálogo de **ATF** (98 productos) | ✅ detecta el negocio solo |

---

## 🔩 Servicios de ATF (mano de obra)

AURORA **nunca niega** estos servicios. Si el precio no está capturado, dice que lo confirma — no lo inventa:

`recolocación de lupa` · `instalación de lupa / retrofit` · `instalación de kit LED` · `sellado de faro` · `calibración de luces` · `pulido de faro` · `diagnóstico`

Si además preguntas por espacio o cita, consulta la **agenda real**.

⏳ **Faltan los precios** — los dicta Anuar.

---

## 📱 WhatsApp

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `manda un whatsapp a 33XXXXXXXX diciendo ...` | Envía de verdad | ✅ |
| `manda el archivo C:\ruta\x.pdf por whatsapp a 33XXXXXXXX` | Envía el archivo real | ✅ |
| `repara whatsapp` | Limpia caché de WhatsApp Desktop | ✅ liberó 310 MB real |

**Quién escribe importa:** si el mensaje entrante es de familia o suena personal, AURORA **no vende ni registra lead** — responde con respeto y te avisa a ti. Verificado 14/14 casos reales.

---

## 💻 Sistema

| Escribe esto | Qué hace | Comprobado |
|---|---|---|
| `haz un diagnóstico de mi pc` | RAM, CPU, disco, procesos pesados — datos reales | ✅ |
| `optimiza mi pc` / `limpia temporales` | **Pide confirmación** antes de borrar | ✅ |
| `busca el archivo <nombre>` | Busca en Descargas, Escritorio, Documentos, Imágenes | ✅ 11 s (antes +2 min) |

---

## ⚠️ Lo que NO funciona todavía (honesto)

1. **Exportar PNG/JPG desde Corel** — incompatibilidad real de la librería. Usa PDF.
2. **Tareas automáticas en segundo plano nuevas** — se cuelgan. Por eso el pronóstico de ventas es bajo demanda (`/equipos/ventas/ultimo`), no automático cada 4 h.
3. **Publicar como Milens** — faltan sus 4 llaves de Meta en el `.env` (están en la PC de Rocío). Avisa honesto en vez de publicar en la página equivocada.
4. **Buscar en la web** — falta `GOOGLE_API_KEY`. Ahora lo dice en vez de devolver 0 resultados en silencio.
