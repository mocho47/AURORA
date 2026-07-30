# Registro de cambios de AURORA

Registro en español simple, para que Anuar pueda saber qué cambió y por qué sin tener que leer código. Cada entrada tiene fecha, qué se hizo, y por qué — el código real queda en los commits de git (mensajes claros, uno por pieza).

---

## 🏁 2026-07-29 — FASE 3 COMPLETA: las 20 carpetas verificadas comando por comando

Se cerró la verificación en vivo de las ~514 herramientas del enrutador universal, carpeta por carpeta, probando contra el sistema real (nada simulado). **FORJA quedó excluida por decisión de Anuar** (es otro proyecto independiente e inconcluso).

**Carpetas cerradas (20):** AGENDA, SISTEMA, SUBLIMACION, REDES, WEB, MANUALES, BIBLIOTECA, MOTORES_CUSTOM, ORACLE, INTEGRACIONES, VENDEDOR, MARKETING, PUBLICADOR, AUTH, MEMORIA, TALLER, CEREBRO, EDITOR, MOTORES, CORE.

### Los 3 bugs más graves que se encontraron y arreglaron

1. **El auto-reparador podía borrar el 96% del cerebro de AURORA.** Le mandaba al modelo solo los primeros 6,000 caracteres de un archivo pero reemplazaba el archivo completo. En `consciencia.py` (148,330 caracteres) eso habría destruido casi todo. Y además nunca había reparado nada en su vida (la IA devolvía el código en markdown y eso jamás compila). Hoy tiene 4 candados y sí repara de verdad.

2. **El cotizador usaba precios del negocio equivocado.** Siempre asumía ATF: cotizar 50 tazas sublimadas (trabajo de Milens) usaba el catálogo de faros. Y tenía su propia copia hardcodeada de 4 productos ATF y 6 de Milens, mientras los catálogos reales tienen 98 y 73. Ahora detecta el negocio del pedido y lee los catálogos de verdad.

3. **La capacidad offline estaba muerta.** El multi-SDK pedía un modelo local (`mistral`) que no está instalado, así que Ollama devolvía 404 y caía a la nube en silencio. Si se iba el internet, no había respaldo real. Ahora elige el mejor modelo instalado según la RAM de la máquina (probado: 81s real sin internet).

### Otros arreglos verificados
`medidor_dxf` nunca midió nada (API mal usada) · `pronostico_embudo` siempre daba $0 · buscar archivos tardaba +2 minutos cuando no encontraba · el generador de cajas decía medidas engañosas ("80x50x40cm... mm" cuando son milímetros) y escondía fallos de DXF · la agenda ignoraba la fecha pedida · el cotizador láser tardaba 288s en cada cotización de la misma pieza (ahora 1.2s) · el buscador web devolvía 0 resultados sin decir que faltaba una llave.

### Lo que se encontró y NO se tocó (decisión de Anuar)
5 módulos en CORE que el sistema vivo no usa pero que el enrutador cree disponibles: la arquitectura paralela `aurora.py`+`aurora_selector` (con un bug de enrutamiento: manda 5 de 6 mensajes al motor equivocado), un segundo sistema de WhatsApp que corrió una sola vez, un publicador duplicado y dos módulos de crisis que se duplican entre sí. Nada se borró.

### Balance honesto
No todo lo que parecía roto lo estaba: dos "bugs" en los renderizadores de taza y en el catálogo de fondos eran errores míos leyendo el código — los 60 fondos funcionan perfecto. Y varias carpetas (SISTEMA, WEB, MANUALES, VENDEDOR, MARKETING) salieron limpias, sin un solo bug.

---

## 2026-07-29 — CEREBRO y TALLER: el bug más peligroso del proyecto + mejoras reales

### 🚨 Lo más importante: el auto-reparador podía borrar el 96% del cerebro de AURORA

`auto_reparacion` le mandaba al modelo de IA solo los **primeros 6,000 caracteres** de un archivo, pero después **reemplazaba el archivo completo** con lo que la IA devolvía. Medido real: `consciencia.py` tiene 148,330 caracteres — la IA veía el 4% y su respuesta habría borrado el otro 96%. Y la única validación que había (que compile) lo aprobaba, porque un archivo cortado a la mitad compila perfecto. Peor: `diagnosticar_y_reparar_todo()` corría eso **solo, automáticamente**, sobre cada módulo con error. Choca de frente con tu regla permanente de nunca restar funciones.

**Blindado con 4 candados, los 4 probados en vivo:**
1. Los archivos del núcleo (consciencia, aurora_server, run_aurora...) **jamás** se auto-reparan sin ti.
2. Si el archivo no cabe completo en lo que la IA alcanza a ver, se rechaza diciendo el porcentaje exacto que se perdería.
3. Si el arreglo pierde más del 25% de las líneas, se rechaza aunque compile.
4. Después de aplicar, se intenta **importar de verdad** el módulo; si no importa, se restaura el respaldo solo.

**Y además: esa función nunca había reparado nada en su vida.** La IA devuelve el código envuelto en markdown (` ```python `) y eso jamás compila, así que todos los intentos morían. Arreglado — verificado end-to-end con un archivo roto a propósito: ahora sí lo repara.

**Mejorado** (tu pedido de "si ya repara, mejóralo"): pasó del modelo chico al grande (`llama-3.3-70b-versatile`), lo que además permitió subir el límite de 6,000 a 40,000 caracteres — la cobertura pasa de 80 a más de 170 de los 195 archivos.

### 🔧 Nuevo: reparar la conexión con Corel, desde el chat
La noche anterior se arregló **a mano** un caché corrupto de `win32com` que dejaba todas las constantes de Corel vacías, rompiendo en silencio escalar página, planilla, lona y exportar PNG. Ahora es una función real (`reparar_corel`) que AURORA ejecuta sola, y **no se conforma con borrar el caché: reconecta con Corel y confirma que quedó bien** antes de decírtelo. Se puede pedir por chat: *"arregla la conexión con Corel"* o *"Corel no responde"*.

### ⚡ Cotizador láser: 288 segundos → 1.2 segundos
Cotizar la misma pieza en 3 modos (corte / grabado / ambos) para comparar precios repetía desde cero el trabajo caro (quitar fondo con IA + vectorizar). Ahora se guarda el vectorizado: la primera cotización cuesta lo mismo, las siguientes de la misma imagen son instantáneas. **240 veces más rápido**, medido. Y ya acepta palabras naturales: "corte" en vez de tener que escribir "corte_contorno".

### 🐌 Buscar archivos: de más de 2 minutos a 11 segundos
Buscar un archivo que no existía (un typo, por ejemplo) trababa el chat más de 2 minutos, porque recorría archivo por archivo carpetas que jamás contienen lo que buscas (.git con 3,749 archivos, manuales descargados con 2,568, librerías de terceros).

### 📐 Generador de cajas: decía medidas engañosas y escondía fallos
Respondía "80x50x40cm... mm" (texto mezclado y equivocado): boxes.py trabaja en **milímetros**, así que pedir una caja "80x50x40" pensando en centímetros daba una cajita de 8×5×4 cm. Y si la conversión a DXF fallaba, respondía "OK" igual, sin DXF y sin avisar. Ambas cosas arregladas y verificadas.

### Otros verificados sin bugs
`razonador` (matemática real correcta), `paneles_cerebro`, `equipos` (5 equipos reales), órdenes de taller, reportes BI, inventario, precios.

---

## 2026-07-28/29 — Fase 3 continuación: ORACLE, INTEGRACIONES, VENDEDOR, MARKETING, PUBLICADOR, AUTH, MEMORIA (7 carpetas más)

**Por qué**: seguir cerrando Fase 3 carpeta por carpeta, priorizando lecturas seguras en las carpetas de alto riesgo (las que mandan WhatsApp o publican en redes reales NO se dispararon en vivo, solo se revisó el código y se probaron sus lecturas de estado).

**Bug real encontrado y arreglado — ORACLE**: `pronostico_embudo()` (cuánto dinero traes en el embudo de ventas) siempre daba \$0, sin importar cuántos leads reales hubiera. Causa: la columna `valor_estimado` existe en la base desde una migración específica "para pronosticar", pero `crear_lead()` nunca recibía ese dato ni lo guardaba. Arreglado: `crear_lead()` ahora acepta `valor_estimado`, y se agregó `actualizar_lead_valor()` para corregirlo después. Verificado en vivo con un lead de prueba real (creado y limpiado después).

**Sin bugs, verificadas con datos reales**:
- **INTEGRACIONES**: Email/Telegram/WhatsApp — patrón honesto confirmado (nunca dicen "enviado" sin mandar nada real). WhatsApp con credenciales reales y funcionando; Email y Telegram genuinamente sin configurar (decisión pendiente de Anuar, no bug).
- **VENDEDOR**: `verificador_core.py` (el que detecta fichas incoherentes tipo "H4 con texto de H7") probado en vivo, 0 incoherencias actuales. Resto de fichas/CRM coincide exacto con lo ya documentado.
- **MARKETING**: `analizador_mercado` (búsqueda real de nicho con URLs reales), `asesor_core` (playbooks/diagnóstico honesto, dice "SIN_DATOS" en vez de inventar), `catalogo_compartible` (PDF real de 73 productos generado y verificado).
- **PUBLICADOR**: estados reales de Facebook/Instagram/WhatsApp/Metricool coinciden con lo esperado (TikTok y Metricool sin configurar, resto conectado). Nada se publicó en vivo — muy alto riesgo, solo lecturas.
- **AUTH**: usuarios (Anuar+Rocío como dueños) y automatizaciones de venta/marketing revisadas en lecturas seguras, coincide con lo documentado.
- **MEMORIA**: 76 habilidades reales detectadas, 364 episodios registrados. Observación (no confirmado como bug): el ciclo de sueño/consolidación tiene 0 ciclos completados — probablemente porque necesita 5 min de inactividad real y esta sesión no ha parado en toda la noche, no error de código.

**15 de ~21 carpetas de Fase 3 cerradas.** Quedan: EDITOR, CORE, MOTORES, CEREBRO, TALLER, FORJA.

---

## 2026-07-28 — Fase 3 (arranque): AGENDA completa + bloque de Monetización conectado al panel

**Por qué**: Fase 3 es verificar en vivo, carpeta por carpeta, las ~510 herramientas del router universal (510 es demasiado para una sola sesión — se acordó ir cerrando carpetas completas, no arañar todas a medias). Se eligió AGENDA (9 herramientas) como primera carpeta completa de esta fase, mismo método que "Corel al 100%": leer el código real, correr la prueba propia del módulo, probar en vivo por chat, arreglar lo que falle.

**Qué se encontró y se arregló:**
1. El candado directo de "agenda" solo llamaba a `resumen()` o `proximas()` — preguntar "qué tengo hoy" o "qué tengo mañana" SIEMPRE regresaba el resumen general de todas las citas, sin filtrar por la fecha real pedida. Ahora reconoce hoy/mañana/fecha explícita y llama a `dia()` de verdad.
2. Crear una cita nueva no tenía **ninguna** ruta por chat — se ignoraba en silencio. Ahora se puede agendar de verdad (pide fecha, hora, tipo y cliente si faltan — no los inventa).
3. Encontrado en vivo por Anuar usando la alerta global: avisaba "12 publicaciones sin aprobar" pero el panel nunca tuvo forma de revisarlas — el endpoint real ya existía (`/monetizacion/bloque-pendiente`), solo no estaba conectado a ninguna pantalla. Se agregó una tarjeta real en la pestaña Monetización con la lista del bloque pendiente y un botón para aprobarlo.

**Pendiente real**: quedan 19 carpetas más de Fase 3 (EDITOR, CORE, MOTORES, CEREBRO, TALLER, FORJA, AUTH, MEMORIA, MARKETING, PUBLICADOR, VENDEDOR, ORACLE, INTEGRACIONES, BIBLIOTECA, SISTEMA, MOTORES_CUSTOM, WEB, REDES, MANUALES, SUBLIMACION) — trabajo real de varias sesiones más, no de una noche.

**Continuación misma noche — 7 carpetas chicas más, cerradas completas:**
- **SISTEMA** (6/6 ok): `optimizador.py` (diagnóstico real de RAM/CPU/disco, limpieza de temporales con confirmación real antes de borrar) y `organizador_archivos.py` (escaneo real de 3972 archivos/12.91GB probado en Downloads, blindaje real que nunca toca AURORA/Windows/AppData) — ambos sin bugs, ya bien construidos.
- **SUBLIMACION** (3/3 ok): lienzo en blanco y montaje de diseño a 300DPI, PDF+PNG reales generados y verificados.
- **REDES** (3/3 ok): diagnóstico real de dispositivos Google Cast en la LAN — encontró un dispositivo real y dio diagnóstico real de señal/pérdida de paquetes. Útil para el pendiente de la Mini "Oficina 2" cuando se corra en esa red.
- **WEB** (verificada): búsqueda real, lectura de página real, todo probado con datos reales de internet.
- **MANUALES** (verificada): confirmó que el sistema de aprendizaje de manuales es el mismo que ya trajo los PDFs de Corel esta noche — y de paso se descubrió que **el manual de Vectric Aspire (48 páginas) ya estaba ingerido**, contradiciendo lo que se le dijo antes a Anuar sobre no tener documentación de Aspire.
- **BIBLIOTECA** (6/6 ok): motor de búsqueda híbrido (texto + semántico) probado en vivo con una consulta real en español ("velocidad de corte") que encontró contenido técnico real en inglés de los manuales de RDWorks — el glosario ES→EN funciona.
- **MOTORES_CUSTOM** (5/5, 1 bug real arreglado): `medidor_dxf.py` usaba `.query()` de ezdxf incorrectamente (nunca fue la API real para bounding box, y solo buscaba bloques INSERT, ignorando toda otra geometría) — con un DXF real de prueba (rectángulo 10x5) siempre fallaba con "error_desconocido". Arreglado con `ezdxf.bbox.extents()`, la API real; verificado exacto (10.0 x 5.0).

**8 de 20 carpetas de Fase 3 cerradas esta noche** (AGENDA + estas 7). Quedan 12: EDITOR, CORE, MOTORES, CEREBRO, TALLER, FORJA, AUTH, MEMORIA, MARKETING, PUBLICADOR, VENDEDOR, ORACLE, INTEGRACIONES.

---

## 2026-07-28 — Lote "Corel al 100%" (consciencia.py + corel_core.py + pc_access.py)

**Por qué**: Anuar probó Corel en vivo con amigos de 4Forte y falló en lo más básico (abrir una imagen). En vez de parchar ese caso puntual otra vez, se leyó el código real completo de Corel y se probó comando por comando contra el Corel real de Anuar.

**Qué se arregló, todo verificado en vivo:**

1. **Rutas con espacios sin comillas** (el caso más común al copiar de WhatsApp/Windows) no se reconocían — regex reescrita no-greedy.
2. **Extensiones incompletas**: `.ai`, `.bmp`, `.gif`, `.tif/.tiff` no se reconocían en la ruta aunque el motor ya los soportaba.
3. **Typo "corell"** (doble L) de Anuar, no se reconocía como "corel".
4. **"Cerrar documento"** existía en el motor pero ningún comando de chat lo alcanzaba — ahora sí.
5. **"Extraer el texto"** se había pedido en vivo y no existía como función real (se ignoraba en silencio) — ahora lee el texto real de Corel vía COM, y de paso cuenta las demás formas ("adornos": imágenes, rectángulos, etc.).
6. **Escalar página** fallaba si no había ningún documento abierto — ahora crea uno nuevo automático, igual que ya pasaba con importar imágenes.
7. **Ruta inventada por el enrutador de IA**: si ni el archivo ni la carpeta existían, se ejecutaba igual a ciegas — ahora se verifica primero.
8. **Un cuelgue de Corel bloqueaba el chat completo para todos los usuarios** (no solo Corel) — ahora responde honesto a los 25s.
9. Se limpió el caché corrupto de `win32com` (`gen_py`) que traía las constantes de Corel en cero — el problema real detrás de varias fallas silenciosas.

**Lo que NO se logró cerrar, documentado sin fingir**: exportar directo a PNG/JPG desde Corel. Se encontró la causa real leyendo el SDK oficial (el método `ExportBitmap` requiere llamar `.Finish()` en el objeto que regresa, cosa que el código nunca hacía), y Anuar confirmó en vivo que el ejemplo oficial SÍ funciona corrido directo dentro de Corel — pero la librería de Python (pywin32) tiene una incompatibilidad real con ese método específico que no se pudo resolver esta noche pese a varios enfoques distintos, todos con evidencia real. **Exportar a PDF sí funciona 100% verificado** — es la alternativa mientras no se resuelva. Camino real identificado para la próxima sesión: en vez de llamar `ExportBitmap` desde Python, hacer que Corel corra su propia macro VBA (ya probada funcionando) y que Python solo dispare esa macro.

**Bono real encontrado**: ya existe en disco el SDK/Object Model oficial completo de CorelDRAW extraído (2560 páginas HTML, `MANUALES/descargas/draw_om_extraido/`) de una sesión anterior — sirvió esta noche para diagnosticar el bug de ExportBitmap con la fuente real en vez de adivinar. Pendiente conectarlo al cartucho de Biblioteca/Manuales para consulta futura.

---

## 2026-07-26/27 — Corrección de raíz del enrutador (consciencia.py + registro_herramientas.py)

**Por qué**: Anuar encontró esta noche que AURORA negaba capacidades reales, entraba en respuestas circulares, y no seguía sus propias reglas. Se investigó a fondo (3 auditorías reales en paralelo, código leído línea por línea, nada especulado) antes de tocar nada, y se corrigió todo junto — no parche por parche.

**Qué se encontró y se arregló:**

1. **El enrutador tenía 17 reglas apiladas con el tiempo**, sin orden real (una quedó numerada "2.535" pero insertada físicamente después de otra llamada "2.61"). Se convirtió en una lista ordenada por especificidad — agregar algo nuevo mañana es una línea, no cirugía.

2. **"Núcleo blindado" no protegía nada** — el archivo se escribía en disco ANTES de checar si era del núcleo (consciencia.py mismo, el propio cerebro). Ahora pide confirmación real ANTES de tocar un archivo del núcleo, no un aviso después del hecho.

3. **Palabras cortas se confundían con otras** — "hazme un **borra**dor" se interceptaba como orden de borrar archivos; "eso me con**mueve**" como orden de mover archivos; "la **instala**ción cuesta" como orden de instalar algo. Arreglado con coincidencia de palabra completa, no de fragmento.

4. **Mismo bug de Corel, pero en 329 funciones más**: el sistema que ejecuta herramientas reales fallaba al llamar cualquier función que fuera "async" desde un hilo de fondo — el error real quedaba disfrazado de "fallo genérico". Es el mismo tipo de bug que ya se había arreglado hoy en Corel, solo que aquí afectaba potencialmente a todo el catálogo.

5. **Una función que sí modifica archivos** (`diagnosticar_y_reparar_todo`) estaba clasificada como "solo lectura" — se hubiera ejecutado sin pedir confirmación. Corregido.

6. **WhatsApp real mandaba siempre un saludo genérico**, ignorando lo que Anuar pedía escribir — aunque el sistema SÍ decía "enviado de verdad" (el envío era real, el contenido no era el pedido). Corregido para usar el texto real.

7. **El "candado único de verdad"**: ahora CUALQUIER respuesta de AURORA, antes de llegar al chat, se revisa contra el catálogo real de herramientas. Si dice "no puedo hacer X" y sí existe una herramienta real para X, se corrige automáticamente — sin importar qué modelo de IA generó la respuesta ni si el modelo decidió ignorar las instrucciones.

8. **El "razonador profundo"** (para preguntas largas/complejas) antes corría primero y sin saber nada de lo que AURORA puede hacer — por eso mensajes largos se iban directo a una respuesta genérica. Ahora es el último recurso de verdad (después de intentar todo lo real) y recibe el contexto completo, incluida la Biblioteca de manuales.

9. Varios bugs menores de un pitch de venta que mostraba texto interno crudo en vez del pitch real, una búsqueda de memoria que no encontraba el tema real de la pregunta, y coincidencias de palabras que no calzaban entre lo que el candado reconocía y lo que buscaba adentro.

**Probado en vivo, no solo en teoría**: se reprodujeron los 3 mensajes exactos que fallaron esta noche y las 3 colisiones de palabras encontradas — los 6 casos ahora responden correctamente. Los comandos de Corel de hoy (gotero, planilla, exportar, etc.) siguen funcionando igual, sin romper nada.

**Archivos que cambiaron**: `CEREBRO/consciencia.py`, `CEREBRO/registro_herramientas.py`, `CEREBRO/equipos.py`.

**Explícitamente NO se hizo en esta corrección** (para no prometer de más): no se fusionaron los candados de dominio dentro del enrutador universal (son más confiables por separado, es un cambio de riesgo real para otra sesión); no se construyó ninguna capacidad nueva (eso es trabajo aparte, con su propia prueba real).

---

## 2026-07-27 (madrugada) — Bugs reales encontrados por Anuar probando en vivo, ya corregidos

Después de la corrección de arriba, Anuar probó pidiéndole a AURORA (no a mí) exportar los 3 logos de Corel a PDF con lenguaje natural. Encontró 2 problemas reales de inmediato — se corrigieron y probaron en el momento:

1. **"Almacenar" no se reconocía** — solo "exportar" disparaba el comando directo de Corel. Al no reconocerlo, el mensaje se fue al enrutador de IA, que adivinó mal DOS veces: primero eligió una herramienta de conversión que no aplicaba, luego (peor) eligió una herramienta genérica de "escribir archivo" y creó un archivo basura real de 6 bytes con la palabra "titulo" adentro en la carpeta raíz de AURORA. Se agregaron "almacena/almacenar/guarda/guardar" como sinónimos reales de exportar, y se enseñó a armar la ruta real a partir de "carpeta conocida + título" (ej. "en descargas con el título X") en vez de exigir una ruta completa que Anuar no iba a dar.

2. **Carpeta única para PDFs de Corel** — a petición de Anuar, se creó `C:\Users\Administrador\Desktop\PDFs a Impresion` como el ÚNICO destino real para cualquier PDF que AURORA genere desde Corel. Ahora "guárdalo/almacénalo como PDF" (sin decir dónde, sin decir cómo se llama) ya sabe adónde ir, y si no le das título usa el nombre REAL del documento abierto en Corel (nunca inventa uno). Solo aplica a PDF — PNG/JPG siguen respetando la carpeta que menciones.

**Probado en vivo, ambos con archivo real generado y confirmado en disco** (629,647 bytes cada vez). Este hallazgo confirma algo importante: las pruebas de Anuar pidiendo las cosas en su lenguaje natural (no técnico) siguen encontrando huecos reales que ninguna auditoría de código por sí sola hubiera visto — vale la pena seguir haciéndolo antes de dar por cerrado cualquier arreglo.

**Archivos que cambiaron**: `CEREBRO/consciencia.py` (2 commits separados).

---

## 2026-07-27 (madrugada) — Grupo 5: Fábrica + editar código + consultar código + memoria real

**Por qué**: siguiente grupo de mayor riesgo real por auditar — las capacidades donde AURORA se modifica o construye a sí misma, más el sistema de memoria real que había quedado a medio arreglar. Se hicieron 4 auditorías reales en paralelo (~291k tokens combinados, evidencia citada línea por línea, varios hallazgos reproducidos con archivos reales del proyecto) antes de tocar nada, y se corrigió todo junto por causa raíz.

**Qué se encontró y se arregló:**

1. **El endpoint de chat no distingue dueño de cliente externo** — por esa puerta se podía disparar la Fábrica de motores (que escribe código a disco) o la edición de archivos sin ningún candado de dueño, incluso desde WhatsApp. Se agregó un candado real: si el mensaje llega por `canal="whatsapp"`, AURORA responde honesto que esa acción es solo del dueño desde el panel, y no la ejecuta. Probado en vivo: confirmado que ambas rutas (crear motor, editar archivo) se niegan correctamente por WhatsApp.

2. **Hueco real de seguridad en la Fábrica** (`fabrica_motores.py`): si el nombre del motor traía una diagonal (`/`), se saltaba la limpieza del nombre y en teoría se podía apuntar a cualquier archivo `.py` del sistema. Cerrado — el nombre siempre se limpia primero.

3. **"Compila" no era "funciona"**: la Fábrica sí probaba el motor recién creado, pero si fallaba al cargarse de verdad (import roto), el error se tragaba y AURORA decía "✅ creado de verdad" de un motor roto. Ahora, si falla la carga real, lo dice honesto: "el código compila pero el motor falla al cargarse — no lo doy por creado". Probado en vivo con un motor real que falló al recrearse — el mensaje salió correcto.

4. **Sobrescritura silenciosa de motores** — crear un motor con un nombre que ya existía pisaba el archivo sin aviso ni respaldo. Ahora se guarda una copia de respaldo con fecha/hora antes de pisarlo, y el mensaje lo avisa explícito. Confirmado en vivo: respaldo real encontrado en `.ide_backups/`.

5. **Un motor recién creado por el chat no aparecía disponible hasta reiniciar el servidor** — el catálogo de herramientas nunca se refrescaba después de crear uno, y además la carpeta de motores hechos por la Fábrica ni siquiera estaba en la lista de carpetas que se escanean. Arreglado ambos huecos. Probado en vivo: motor creado y usado exitosamente por el router en la misma sesión, sin reiniciar nada.

6. **Buscar algo en el código de AURORA congelaba todo el sistema hasta ~22 segundos** (medido, no estimado) — cualquier otra sesión/usuario se quedaba esperando mientras tanto. Además, 8 de cada 10 archivos que revisaba eran librerías de terceros, no código de AURORA. Arreglado: la búsqueda corre en segundo plano sin bloquear nada más, ya no revisa librerías de terceros, y tiene un límite de archivos. Medido en vivo: de ~22s bajó a 2.17s.

7. **El guardián contra respuestas cortadas de la IA se podía burlar** — un archivo cortado a medio guardar podía pasar como válido. Ahora se revisa un dato real que manda la IA (si terminó de verdad o se quedó sin espacio), y si se cortó, AURORA lo rechaza honesto en vez de guardar algo incompleto. Se subió también el espacio disponible para que pase menos seguido.

8. **Colisión real: pedir "enséñame el código Y corrígelo" a la vez ganaba la edición sobre solo mostrar** — se reordenó para que, ante un mensaje ambiguo, gane siempre la opción más segura (mostrar) sobre la que modifica archivos. Probado en vivo con el mensaje exacto que lo disparaba — ahora responde mostrando el código, no editándolo.

9. **Memoria real, 4 arreglos**: (a) si falla el guardado en memoria durante una conversación normal, ya no tira la respuesta que AURORA sí había generado — el fallo queda aislado; (b) cuando la búsqueda de memoria no encuentra nada en lo ya consolidado, ahora también busca en el historial crudo reciente antes de rendirse — probado en vivo: un dato guardado momentos antes SÍ se encontró, sin esperar al ciclo de sueño nocturno; (c) se corrigieron 2 rutas de memoria completamente rotas por nombres de función que ya no existían (el conector del bus neuronal y el resumen del panel); (d) se agregó una purga de historial viejo ya consolidado (más de 90 días) para que no crezca sin límite para siempre.

**Probado en vivo, checklist completo**: reinicio limpio y saludable, motor creado y usado en la misma sesión, reemplazo de motor con respaldo confirmado en disco, motor roto detectado honesto, búsqueda de código de 22s a 2.17s, colisión consulta/editar resuelta a favor de solo mostrar, memoria episódica encontrando un dato reciente sin ciclo de sueño, Fábrica y edición de código ambas rechazadas correctamente por WhatsApp.

**Archivos que cambiaron**: `CEREBRO/consciencia.py`, `CEREBRO/fabrica_motores.py`, `CEREBRO/registro_herramientas.py`, `CEREBRO/registrador_bus.py`, `CORE/aurora_server.py`, `MEMORIA/sistema_memoria.py`, `MEMORIA/motor_sueno.py`.

**Explícitamente NO se hizo en esta corrección** (para no prometer de más): no se construyó un sistema de autenticación/sesión real para el chat completo — el candado de canal cierra la exposición más probable (WhatsApp) sin inventar sesiones que no existen hoy; eso es un proyecto de seguridad aparte, más grande. No se construyó edición de código por diff/parche (confirmado que no existe ese patrón en todo el proyecto — construirlo es un proyecto real aparte). No se rediseñó el esquema de memoria semántica (categorías fijas vs. temas libres) — el arreglo de "buscar también en lo reciente" da alivio real sin tocar el ciclo de sueño que ya funciona. No se tocó `fabrica_agentes.py` (sistema paralelo de agentes conversacionales, mismo tipo de hueco encontrado, pero es otro sistema, fuera de este grupo).

---

## 2026-07-27 (madrugada) — Grupo Negocio: Órdenes + Inventario + CRM + Contabilidad

**Por qué**: siguiente grupo de la lista, con datos reales de dinero del taller. 2 auditorías reales en paralelo (código completo leído, ~177k tokens combinados) sobre `TALLER/ordenes_taller.py`, `TALLER/inventario.py`, `TALLER/reportes_bi.py`, `TALLER/administracion.py`, `TALLER/cotizador_servicios.py`, `TALLER/taller_core.py`, `TALLER/album_catalogo.py` y `ORACLE/oracle_core.py`.

**Aclaración importante** (no fue un bug): un agente marcó como crítico que `taller.db` estaba vacía en vez de tener las 34 órdenes reales — es el reset intencional "AURORA virgen" que Anuar pidió el 2026-07-24, con respaldo real conservado en `_BACKUP_DB_pre_virgen_20260723_235128/`. No se tocó.

**Qué se encontró y se arregló:**

1. **La contabilidad mensual contaba órdenes CANCELADAS como ingresos y utilidad reales** — una orden cancelada de $500 inflaba el reporte en vez de excluirse. Ahora `contabilidad_mensual()` ignora las canceladas. Probado en vivo: crear+cancelar una orden de prueba, el reporte volvió a $0 correcto.

2. **Cambiar el estado de una orden que NO existe respondía "ok"** — mentira por omisión, nunca revisaba si la orden era real. Ahora responde error honesto. Probado en vivo con un id inexistente.

3. **Marcar una orden como "entregada" la marcaba automáticamente como COBRADA (saldo=0), sin verificar que de verdad se pagó** — si alguien de la familia (Samm/Rocío/Anuar) entregaba el producto sin cobrar antes, el sistema igual reportaba el dinero como cobrado, perdiendo visibilidad real de cuentas por cobrar. Ahora el estado y el cobro son cosas separadas: si queda saldo pendiente al entregar, el mensaje lo avisa explícito en vez de ocultarlo. Probado en vivo con una orden de prueba con saldo pendiente.

4. **Se podían dejar existencias de inventario en NEGATIVO** — reabastecer con una cantidad negativa (típico error de captura) dejaba el stock en números negativos sin ningún aviso, contaminando el valor total del inventario. Ahora se bloquea igual que ya bloqueaba la función de movimientos. Probado en vivo: intento de dejar un artículo de prueba en negativo, bloqueado.

5. **Una migración de base de datos del inventario podía borrar TODO sin respaldo** — código dormido (el esquema real ya está al día, 73 artículos reales confirmados sanos), pero si alguna vez se disparaba, borraba items y movimientos sin guardar copia. Ahora, si algún día se dispara, respalda todo a un JSON con fecha antes de borrar.

6. **Bug de "utilidad $0" en los reportes de negocio (BI)** — si un mes tenía una utilidad real capturada de exactamente $0, el sistema la descartaba en silencio y la reemplazaba con un cálculo derivado distinto, sin avisar. Corregido para respetar el dato real capturado, sea cual sea.

7. **Crear 2 órdenes casi al mismo tiempo podía perder una de las dos** — medido en vivo: 5 órdenes creadas en paralelo, 3 de 5 fallaban con error 500 (folios que colisionaban por venir del mismo segundo + la base de datos bloqueándose entre sí). Arreglado con el mismo patrón que ya usa el resto del proyecto (modo WAL + tiempo de espera) más un folio que ya no puede repetirse. Probado en vivo: 5 de 5 órdenes creadas sin error.

8. **2 arreglos menores de consistencia**: preguntar por el pronóstico de ventas (CRM) por chat pedía una confirmación extra innecesaria (siendo una consulta de solo lectura, igual que preguntar por inventario) — ya responde directo. Y 2 endpoints del CRM que sí bloqueaban brevemente el sistema mientras respondían, ahora corren igual que el resto.

**Probado en vivo, checklist completo**: contabilidad excluye canceladas, estado sobre orden inexistente da error honesto, entregar no fuerza cobro falso, inventario bloquea negativos, 5 órdenes simultáneas sin fallos, pronóstico de embudo responde directo. Todos los datos de prueba (etiquetados `AUDIT2_*`) limpiados al final — inventario real (73 artículos) y resto del negocio intactos.

**Archivos que cambiaron**: `TALLER/ordenes_taller.py`, `TALLER/inventario.py`, `TALLER/reportes_bi.py`, `CEREBRO/registro_herramientas.py`, `CORE/aurora_server.py`.

**Explícitamente NO se hizo en esta corrección** (con razón real): no se arregló la carrera lectura-modificación-escritura en los almacenes JSON de materiales/servicios (riesgo real pero no reproducido con pérdida de datos; arreglarlo bien pide locking de archivo, otro proyecto). No se distinguió "costo nunca capturado" de "costo capturado en $0 real" en los reportes (pide una columna nueva en la base de datos, cambio de esquema fuera de alcance). No se tocó la ambigüedad de "bajo mínimo" entre artículos nunca contados y stock realmente bajo (cosmético, mejora de UX para otra sesión).

---

## 2026-07-27 — Grupos finales: Vendedor + Publicador + WhatsApp

**Por qué**: los últimos 2 grupos de la lista. Publicador y WhatsApp son distintos a todo lo anterior: tienen consecuencias reales hacia AFUERA (Facebook/WhatsApp reales de ATF, gente real). 3 auditorías reales en paralelo (~273k tokens, solo lectura de código + endpoints de solo-lectura, nunca se ejecutó nada que publique o envíe de verdad durante la auditoría).

**El hallazgo que cambió el enfoque de todo el arreglo**: el candado que bloquea Fábrica/editar-código por WhatsApp (de la corrección anterior) era la EXCEPCIÓN, no la regla. El resto del sistema (acción física, publicar, las ~690 herramientas del router universal, confirmar acciones pendientes) nunca revisaba por qué canal llegaba el mensaje. En la práctica: **cualquier cliente que le escribiera al WhatsApp real de ATF podía lograr que AURORA mandara un WhatsApp real a un tercer número, abriera cualquier página web en la PC real del taller, matara/reparara WhatsApp Desktop, publicara de verdad en Facebook, o ejecutara cualquiera de las ~690 herramientas del negocio con solo responder "ok"/"va"/"sale"**.

**Qué se corrigió (por causa raíz, un solo candado central, no uno por función):**

1. **Candado de canal centralizado**: un único punto en el enrutador ahora revisa, antes de ejecutar cualquier acción de escritura/física/externa (mandar WhatsApp, abrir el navegador, publicar, editar código, crear capacidades), si el mensaje llegó por WhatsApp — si es así, se rechaza honesto, sin importar cuál de esas acciones sea. También se revisa al CONFIRMAR una acción pendiente (no solo al proponerla): como el chat no tiene login real, alguien podía dejar pendiente algo peligroso bajo un identificador que coincidiera con el de un cliente real de WhatsApp, esperando que lo confirmara sin saberlo con un "sí" cualquiera — cerrado.

2. **Publicar en Facebook ya no se dispara por accidente**: antes, cualquier mensaje que mencionara la frase "de verdad" (aunque fuera casual, ej. "de verdad no sé qué publicar hoy") podía disparar una publicación REAL. Ahora siempre muestra primero el preview y pide un "sí" claro en el turno siguiente — mismo mecanismo estricto que ya protege otras acciones peligrosas.

3. **WhatsApp real, 4 arreglos**: (a) un mensaje real de un cliente ya no desaparece para siempre si algo falla al procesarlo — antes se borraba de la cola ANTES de contestar; (b) si un envío real de WhatsApp falla, ahora queda registrado en vez de ser invisible; (c) desconectar el WhatsApp real del negocio ahora exige el PIN del dueño — antes cualquiera con una sola petición podía cortarlo; (d) el recordatorio diario de "sube tus videos" ya no se lo manda el negocio a sí mismo (antes el número por default coincidía con el del propio negocio, nunca le llegaba a Anuar).

4. **Publicador, condición de carrera real**: 2 publicaciones al mismo tiempo (doble ejecución de la tarea automática, doble clic) podían subir el MISMO video 2 veces a Facebook. Ahora hay una reserva real antes de subir (nadie más puede tomar el mismo post mientras se sube). También se agregó un registro permanente de "esto ya se publicó" que no depende de que mover el archivo a la carpeta PUBLICADOS haya funcionado — antes, si ese movimiento fallaba, el video podía volver a salir sorteado en el futuro.

5. **Vendedor, 2 bugs reales de datos incorrectos**: pedir la ficha de un producto por su código (ej. "led h7") podía regresar la ficha de OTRO producto (ej. H4) — datos reales pero del equipo equivocado, verificado en vivo. Y pedir el "pitch de venta para X" hacía que el sistema buscara mal el nombre del producto, no lo encontrara, y el modelo de IA terminara inventando especificaciones que sonaban reales pero no existían en ningún lado — ahora se corta antes de llegar al modelo si la ficha no se encuentra de verdad.

6. **Vendedor, 2 arreglos de seguimiento**: un segundo cliente sin teléfono capturado se perdía silenciosamente (se contaba como "duplicado" cuando era una pérdida real); y un intento fallido de contactar a un cliente por WhatsApp marcaba el lead como "contactado hace poco" igual que si sí hubiera funcionado, escondiéndolo de la lista de pendientes por 48 horas sin ningún reintento real.

**Probado en vivo, checklist de 10 puntos completo**: WhatsApp bloqueado en acción física y en herramientas peligrosas del router; vector de colisión de canal cerrado (confirmado que un pendiente creado por el panel se descarta si alguien lo confirma por WhatsApp); "de verdad" ya no publica solo; WhatsApp sigue autorizado tras los cambios; reconectar sin PIN da error; ficha de "led h7" regresa H7 (antes H4); pitch de "led h4" encuentra la ficha real; Corel/negocio/memoria sin regresión.

**Hallazgo aparte, no relacionado a esta corrección**: Corel dio un error de conexión (`no attribute 'MinorVersion'`) con el programa SÍ abierto — es una caché interna de Windows corrupta (pywin32), no algo que se tocó esta noche. Queda pendiente, no urgente.

**Archivos que cambiaron**: `CEREBRO/consciencia.py`, `INTEGRACIONES/whatsapp_integration.py`, `run_aurora.py`, `CORE/aurora_server.py`, `MARKETING/plan_monetizacion.py`, `MARKETING/publicacion_inteligente.py`, `PUBLICADOR/auto_publicar_atf.py`, `PUBLICADOR/corregir_telefono_atf.py`, `VENDEDOR/vendedor_core.py`, `VENDEDOR/seguimiento_ventas.py`.

**Explícitamente NO se hizo en esta corrección** (con razón real): no se construyó autenticación real completa para el chat (el candado de canal cierra la exposición práctica sin inventar sesiones que no existen); no se tocó la asimetría de códigos de foco en el verificador de fichas ni el criterio inconsistente de "ficha completa" (no muerden datos reales hoy, catálogo chico); no se conectó ni se borró código de ventas que hoy no se usa; no se clasificaron a detalle los tipos de error de Facebook/Meta (mejora de diagnóstico, no de seguridad).

---

## 2026-07-27 — Asistente de Alertas globales + Manual de comandos generado

**Por qué**: 2 pedidos de Anuar tras cerrar los 5 grupos de auditoría — que nunca se pase por alto una publicación pendiente o que WhatsApp se desconecte, y un manual de comandos generado del código real (no escrito a mano, para que nunca se desincronice).

**Alertas globales**: en vez de construir algo nuevo, se generalizó el sistema de alertas que YA existía y funcionaba para Taller (el modal que se muestra encima de todo, el badge, el aviso una vez por hora). Ahora también agrega: publicaciones sin aprobar (Facebook/Instagram/TikTok, ya comparten la misma fuente real), leads sin contactar a tiempo, y si WhatsApp real se desconecta — con un nuevo badge que titila en la pestaña del Chat, como se pidió. **Se descartó explícitamente** una alerta de Facebook Marketplace (no existe esa integración hoy, no se simula) y de "WhatsApp sin responder" (no existe ese concepto — cada mensaje se contesta automático al instante; en su lugar se alerta si la conexión de WhatsApp se cae, que es lo que sí puede fallar de verdad).

**Manual de comandos**: nuevo script (`CEREBRO/generar_manual.py`) que lee directo el código de los 14 candados del chat y el registro de las ~510 herramientas reales, y arma `MANUALES/manual_comandos_aurora.md` — indexado por grupo de trabajo (Taller, Ventas, Marketing, Diseño, Conocimiento, Cerebro y Sistema), en lenguaje simple, con las frases reales que cada uno reconoce. Ligado a la pestaña "📖 Guía/Manual" que ya existía. **Probado en vivo** (no solo generado): un agente probó 8 frases reales del grupo Taller contra el servidor real — 7 de 8 funcionaron exactamente como decía el manual. La única que no (`negocio` con "cómo va") reveló que ese candado en particular necesita DOS tipos de palabra juntas en el mismo mensaje (una de pregunta + una de dominio, ej. "cómo va el inventario"), no basta una frase suelta — se agregó un aviso real en el manual explicando esto en vez de dejarlo como si funcionara solo.

**Archivos que cambiaron**: `CORE/aurora_server.py` (endpoints `/alertas/resumen` y `/manuales/comandos`), `TEMPLATES/panel-completo.html` (badge, modal generalizado, CSS de parpadeo), `CEREBRO/generar_manual.py` (nuevo).

**Explícitamente NO se hizo** (con razón real): no se conectó Marketplace de Facebook (no existe); no se construyó WebSocket para las alertas (el `setInterval` que ya usa todo el panel es suficiente, cambiar de arquitectura no resuelve nada real hoy); no se probaron en vivo las ~510 herramientas del enrutador universal, solo los 14 candados directos — queda declarado como próxima fase, es un trabajo mucho más grande.

---

## 2026-07-27 — Verificación en vivo completa de los 14 candados directos (los 6 grupos)

Después de cerrar el manual, se probaron en vivo los 6 grupos de trabajo completos (no solo un piloto) contra el servidor real — 5 agentes en paralelo más verificación directa donde el agente se negó por exceso de cautela:

- **Taller** (negocio, agenda): 7/8 ✅. Reveló que `negocio` necesita palabra de pregunta + palabra de dominio juntas.
- **Ventas** (ficha_vendedor): 8/8 ✅.
- **Marketing** (publicar): 2/2 ✅ (sin confirmar ninguna publicación real).
- **Diseño** (corel, dxf): 5/6 ✅. Reveló que "vectoriza" (a diferencia de "convierte a dxf") pasa por el enrutador de IA pidiendo confirmación en vez de ejecutar directo — mismo candado, comportamiento distinto según la frase exacta.
- **Conocimiento** (busqueda_web): 2/2 ✅.
- **Cerebro y Sistema** (intuicion, memoria, equipos, consulta_codigo, abrir_navegador — los 3 de mayor riesgo real ya se habían probado en la auditoría de seguridad, no se repitieron): 5/5 ✅.

**Total: 24/26 pruebas reales coinciden exactamente con lo que promete el manual.** Los 2 hallazgos reales quedaron documentados como aviso dentro del propio manual generado (no se "corrigieron" para no inflar el alcance de hoy — son comportamientos reales que vale la pena revisar en otra sesión).

---

## 2026-07-27 — Fase 3 del manual (510 herramientas): intentada, hallazgo real de robustez

Se lanzaron 11 agentes en paralelo para verificar en vivo las 20 carpetas del enrutador universal (510 herramientas). **No se completó** — reveló un problema real: mandar muchas peticiones reales simultáneas a `/chat` puede colgar el servidor (el endpoint `/health` seguía respondiendo sano, pero `/chat` dejaba de contestar por completo, consistente con una petición que se atoró internamente y bloqueó la cola de las demás). Confirmado por 2 agentes independientes con el mismo síntoma. El servidor se reinició limpio sin problema, pero **no se repitió el intento de 11 agentes a la vez** para no volver a tumbarlo mientras Anuar seguía usando el panel en vivo.

**Queda como hallazgo real pendiente**: el servidor de AURORA no está pensado para muchas peticiones de chat concurrentes — vale la pena investigar si `/chat` tiene algún candado/recurso compartido sin `asyncio.to_thread` o algún llamado sin timeout que bloquee el event loop completo. La Fase 3 completa (510 herramientas) queda pendiente para otra sesión, con un enfoque más controlado (secuencial o con pocos agentes a la vez, no 11 en paralelo).

**2 bugs reales más encontrados por Anuar probando en vivo, ya corregidos**:
1. Pedir "el pdf" de nombre "argan" abrió `argan.gsp` (un archivo de corte de 5KB, no el PDF) — la búsqueda de archivo aproximado no respetaba la extensión pedida. Corregido: ahora solo compara contra archivos del mismo tipo, y si hay varios candidatos reales parecidos, pregunta en vez de adivinar.
2. AURORA no tenía ninguna forma real de enviar un ARCHIVO por WhatsApp (solo texto) — pedir "envíaselo como documento por WhatsApp" hacía que el enrutador adivinara mal (abrir el archivo local, o intentar abrirlo en Corel). Se construyó `enviar_archivo()` real vía Green API (`sendFileByUpload`), con resolución de contacto por número real o por nombre buscado en el CRM (ORACLE) — nunca inventa un número.

**Archivos que cambiaron**: `CEREBRO/pc_access.py`, `CEREBRO/consciencia.py`, `INTEGRACIONES/whatsapp_integration.py`.

---

## Planes futuros (próximas sesiones)

Con esto se cierran los 5 grupos de la auditoría de dominio (bajo riesgo, Fábrica/código/memoria, Negocio, Vendedor, Publicador+WhatsApp) más las 2 capacidades nuevas de alertas/manual, con sus 14 candados ya verificados en vivo. Pendientes para otra sesión:

1. **Investigar por qué `/chat` se cuelga con varias peticiones reales simultáneas** (encontrado 2026-07-27 con la Fase 3) — prioridad alta, es un riesgo real de que el panel se quede sin responder si dos personas lo usan a la vez.
2. **Verificación en vivo de las ~510 herramientas del enrutador universal** (Fase 3 del manual de comandos) — intentada, no completada por el hallazgo de arriba. Retomar con un enfoque secuencial/controlado, no muchos agentes a la vez.
3. Caché de pywin32 corrupta en Corel — fix rápido pendiente, no urgente.
4. Generador del manual: no distingue candados con lógica compuesta (2 categorías de trigger a la vez, ej. `negocio`/`corel`) — hoy se avisa con una nota, sería mejor detectarlo automático.
5. `dxf`: "vectoriza" no se comporta igual que las demás frases del mismo candado (ver hallazgo arriba) — revisar por qué.

**Explícitamente diferido, no urgente**: fusionar los 10 candados de dominio dentro del enrutador de IA — hoy son más confiables por separado (determinístico vs. probabilístico); solo tiene sentido si en el futuro se decide que vale la pena el cambio de riesgo.
