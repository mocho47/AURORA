# Pendientes al cierre de la sesión — 2026-08-21 (actualizado 2026-08-22)

## ACTUALIZACIÓN 2026-08-22 — leer esto primero

**Arreglado y verificado en vivo hoy:**
- El candado de piñatas/piezas grandes ahora vectoriza imágenes con
  `EDITOR/imagen_a_dxf.py` (rembg+vtracer, separa capas CORTE/GRABADO), NO
  con `taller_core.vectorizar` (Inkscape, probado que se pasa de 180s y
  mezcla todo en una sola capa — así salió el `piñata.dxf` de 380
  entidades/4.4MB que Anuar generó con el candado viejo antes del fix).
- Se agregó: salto automático de rembg cuando el PNG ya trae transparencia
  real (ahorra minutos reales, medido); filtro de "basuritas" (brillos/
  sparkles) antes de vectorizar; filtro bilateral en vez de Gaussian para
  que los degradados de sombreado no generen bandas falsas; tope duro de
  400 trazos máximo pase lo que pase.
- Con todo eso, el pipeline aislado corre en ~15s. **PERO en el servidor
  real, bajo carga, ha llegado a tardar varios minutos con la imagen del
  sticker de Alicia (degradados en pelo/piel) — no se aisló la causa exacta
  a tiempo.** Por eso se agregó un tope duro de tiempo en el chat: 45s en el
  candado de piñatas (si se pasa, avisa y sugiere mandar el DXF directo),
  90s en el candado genérico "convierte a dxf" (sin calculo de precio
  encima, corre con calma). Esto es una red de seguridad, NO la solución de
  fondo — la causa raíz de por qué tarda tanto en el servidor real sigue sin
  encontrarse del todo.
- El candado genérico "convierte a dxf" (`_convertir_formato_real` en
  `consciencia.py`, ~línea 5490) ya apunta a `imagen_a_dxf.py` para
  imágenes; `taller_core.convertir_a_dxf` se queda SOLO para archivos ya
  vectoriales (svg/pdf/ai/eps/cdr), eso no se tocó.
- **Bug real encontrado y arreglado, afecta TODO el chat, no solo esto**:
  el modelo de Groq `llama-3.1-8b-instant` da 403/404 (cuenta sin acceso o
  modelo dado de baja) y el SDK no traía timeout propio — cada mensaje del
  chat tardaba ~60-90s en fallar a Groq ANTES de caer a Gemini. Se agregó
  timeout de 10s en `CEREBRO/respaldo_local.py`. Sigue pendiente investigar
  por qué Groq da 403 en la cuenta (posible tema de cuota/facturación,
  fuera de lo que se puede arreglar por código).
- Falso positivo descartado: los acentos rotos ("estÃ¡") que parecían un
  bug del servidor eran PowerShell decodificando mal la respuesta en mis
  propias pruebas — los bytes reales del servidor vienen en UTF-8 correcto,
  no hay nada que arreglar ahí.
- Nuevo: `EDITOR/escalas_planillas.py::dividir_imagen_en_hojas()` — escala
  una imagen a su medida física real (cm+dpi) y la parte en tabloides para
  mandar a IMPRIMIR (no confundir con el despiece del DXF, que es para
  CORTAR — Anuar lo aclaró explícito: la impresión nunca se despieza, solo
  se pagina). Aún no conectado a un candado de chat — falta ese paso.
- Idea nueva capturada, NO construida (pausada a propósito por Anuar):
  servicio de generación de sitios web + redes vía cuestionario genérico —
  ver memoria `idea_servicio_sitios_web_cuestionario.md`. 2 clientes reales
  ya en fila (restaurante de mariscos abre viernes, salón de belleza).

## Listo y verificado esta sesión (real, probado) — 2026-08-21

## Listo y verificado esta sesión (real, probado)
- Enrutador: bugs de "abrir_archivo" y "vectoriza" arreglados, 268 pruebas nuevas en verde.
- Fichas técnicas de vendedor: 4→12 completas.
- Lámpara de media luna: capacidad completa en AURORA, DXF real entregado.
- Producción de piezas grandes (Alicia/RUMI): módulo + candado en el chat, probado en vivo por HTTP real. Distingue precio Alicia ($10/$25) de precio general ($70 sin suaje / $95 con suaje).
- `dividir_en_hojas.py`: parte un DXF grande en hojas tamaño tabloide.
- Commit real `7b19e4e` con todo lo de arriba — **falta el `git push` al remoto** (no se ha hecho, pendiente de que Anuar diga cuándo).
- Versión DEMO generada en `C:\AURORA_DEMO`: sin ningún dato real de Anuar (17 CONFIG reemplazados por ejemplo), con candado de licencia funcional (probado con clave real: status OK). Bat de prueba: `C:\AURORA_DEMO\PROBAR_DEMO.bat` (puerto 5001).
- `.bat` para uso directo sin gastar tokens: `HERRAMIENTAS_BAT\reiniciar_aurora.bat`, `generar_demo.bat`, `correr_pruebas.bat`.

## Pendiente real, sin tocar todavía
0. **Integrar el ranurado de la silueta al proceso de Alicia** (pedido 2026-08-22): hoy calculo la silueta ranurada + despiece + MDF compartido + tabloides A MANO en el chat cada vez. Falta una función real en `TALLER/produccion_piezas_grandes.py` que lo haga de una sola llamada (mismo patrón que ya existe, pero cubriendo las 2 piezas del trabajo de Alicia juntas: 1 hoja de MDF compartida si caben, tabloides SOLO para el despiece, silueta como corte ranurado aparte). Ojo real: hoy el perímetro que mide es el DXF completo para ambos modos — no distingue "solo contorno exterior" de "todas las líneas de despiece", así que el corte de la silueta se está aproximando con el mismo número (probablemente por arriba de lo real). No inventar una velocidad distinta para "ranurado" sin que Anuar la dicte.
1. **RUMO.dxf — despiece real de las 6 piezas** (cara, pelo, chamarra, falda, piernas, botas) para el trabajo de Alicia Piñatas. El cálculo de tabloides/MDF/corte ya funciona, pero el archivo NO trae las prendas separadas por capa — hay que clasificarlo a mano con la imagen de referencia a color que mandó Anuar, o pedirle a la clienta el archivo ya en capas.
2. **La segunda figura para la caja de la piñata** (silueta completa, sin despiece) — no se ha generado su DXF todavía.
3. **Bug 3 (ruta_sola)**: no se investigó. La sospecha original era que el estado de "última ruta mencionada" no persiste entre peticiones HTTP — falta confirmarlo y arreglarlo.
4. **`git push`** del commit `7b19e4e` al repo privado — decisión de Anuar, no se hizo aún.
5. **Android**: NO se intentó y NO es viable en el tiempo/tokens de esta sesión como app nativa. La alternativa real que ya existe: el panel web de AURORA se abre desde el navegador de cualquier celular en la misma red (`http://<ip-de-la-pc>:5000`, como ya hace Rocío). Para acceso real desde fuera de la casa (no solo la red local) hace falta hospedar AURORA en un servidor real — es un proyecto aparte, no construido.
6. **Demo pública para pilotos**: quedó anotada como idea (no como pendiente activo) — usar el `AURORA_DEMO` con licencia para dejar que 1-2 personas de confianza la prueben vía túnel (ngrok), no vía GitHub. No se construyó.
7. **motor.json**: solo hay una propuesta escrita (`_CONTEXTO/PROPUESTA_MOTOR_JSON.md`), no implementada.

## Decisiones que Anuar tomó y quedan firmes
- El acuerdo real con Alicia Piñatas: compra tabloide a $10, revende a $25.
- Precio general (cualquier otro cliente): $70 sin suaje, $95 con suaje.
- No se construye el demo público con pilotos "por ahora" — confirmado explícitamente.
- No se toca MercadoLibre (pausado a propósito).
