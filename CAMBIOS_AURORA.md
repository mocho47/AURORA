# Registro de cambios de AURORA

Registro en español simple, para que Anuar pueda saber qué cambió y por qué sin tener que leer código. Cada entrada tiene fecha, qué se hizo, y por qué — el código real queda en los commits de git (mensajes claros, uno por pieza).

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

## Planes futuros (próximas sesiones, en orden)

La corrección de esta noche arregló la ESTRUCTURA del enrutador (cómo decide qué hacer con cualquier mensaje, en los 14 dominios). Lo que falta es auditar el CONTENIDO interno de cada dominio con el mismo rigor que se le dio a Corel hoy (código real leído + probado en vivo, no solo teoría). Se agrupó por riesgo real, no por orden alfabético — cada grupo es una sesión completa:

1. **Negocio**: órdenes + inventario + CRM + contabilidad. Toca datos reales del taller, necesita probarse contra datos reales.
2. **Vendedor**: fichas técnicas y pitches. Ya se le quitó el bug de esta noche (mostraba texto interno crudo); falta auditar la calidad real de las fichas mismas.
3. **Publicador + WhatsApp**: la más delicada — manda posts y mensajes REALES a gente real. Sesión aparte, con más cuidado, sin compartir con nada más.

**Ya cerrado** (ver arriba, 2026-07-27): Grupo de Fábrica + editar código + consultar código + memoria real.

Es un estimado, no una promesa cerrada — Corel tomó una sesión completa por sorpresas que no se esperaban (COM, event loops). Alguno de estos 5 puede ser más rápido, otro puede encontrar lo suyo.

**Explícitamente diferido, no urgente**: fusionar los 10 candados de dominio dentro del enrutador de IA — hoy son más confiables por separado (determinístico vs. probabilístico); solo tiene sentido si en el futuro se decide que vale la pena el cambio de riesgo.
