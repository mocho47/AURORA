# PROMPT MAESTRO — cómo se debió pedir AURORA desde el principio

Escrito el 2026-08-23, después de un día completo corrigiendo los mismos tipos de
bug una y otra vez (modelo de IA dado de baja escrito a mano en 29 archivos,
dos sistemas de lenguaje que se estorban, rutas con comillas que un formulario
sí limpiaba y otro no, respuestas con nombres de campo distintos). No es una
lista de deseos: cada regla de aquí abajo nació de un bug real de HOY o de
sesiones anteriores. Este documento es el prompt — cópialo y pégalo completo
si algún día hay que reconstruir AURORA desde cero, o úsalo como checklist
para corregir lo que ya existe.

---

## EL PROMPT (copiar tal cual)

Quiero que construyas un sistema operador de negocio para un taller de corte
láser/sublimación y retrofit de faros, manejado por una sola persona sin
conocimientos de programación. El sistema se llama AURORA. No es un prototipo:
cada función que exista debe funcionar de verdad contra datos reales, nunca
simulados. Sigue estas reglas de arquitectura sin excepción:

### 1. Una sola fuente de verdad por cada dato o regla — nunca dos

Prohibido que la misma regla de negocio, el mismo precio, el mismo nombre de
modelo de IA, o la misma lista de frases reconocidas exista escrita a mano en
más de un archivo. Si dos módulos necesitan el mismo dato, uno de los dos debe
IMPORTAR la fuente real, nunca copiarla. Antes de escribir una constante,
buscar en todo el proyecto si ya existe una igual en otro lugar.

Ejemplo real de lo que pasa si se rompe esta regla: el nombre de un modelo de
IA quedó escrito literal en 29 archivos distintos. Cuando el proveedor lo dio
de baja, arreglar uno solo no arregló nada — cada módulo tenía su propia copia
del valor muerto, y el sistema fallaba de forma distinta según qué módulo
tocara el usuario en cada momento.

### 2. El cerebro de lenguaje es UN sistema, no dos

Solo puede existir UN mecanismo que decida qué quiso decir el usuario cuando
escribe en lenguaje natural. Nunca un sistema de reglas y, encima, un segundo
sistema de "familias" o intenciones que puede pisar las decisiones del
primero. Si el primero falla en reconocer una frase real, la corrección se
hace DENTRO del mismo sistema (agregando o afinando su propia regla), nunca
levantando un sistema paralelo por encima que decide antes que el original.

Ese único sistema debe:
- Vivir en una sola tabla/registro: nombre de la acción → función que detecta
  si el mensaje la pide → función que la ejecuta. Un solo lugar para leer
  "qué sabe hacer AURORA", no dos ni tres.
- Tolerar errores de dedo en las palabras clave de negocio (nombres de
  material, "vinil", "láser", "mdf") con una comparación de distancia de
  edición por palabra, no con una lista fija de erratas conocidas escritas a
  mano — esa lista siempre se queda corta el día que aparece una errata nueva.
- Generar automáticamente el texto que se le muestra al usuario cuando
  pregunta "qué puedes hacer" A PARTIR de esa misma tabla de acciones reales
  — nunca un texto escrito aparte a mano, porque ese texto se desincroniza en
  cuanto alguien cambia una función y se le olvida actualizar el texto.
- Cuando dos capacidades parecidas compiten por la misma frase (p.ej. "quita
  el fondo" podría ser parte de "conviértelo a DXF" o una acción aislada),
  cada capacidad real debe tener su propio disparador directo — nunca
  depender de que el usuario también diga una palabra extra ("dxf", "corel")
  para que la acción base funcione sola.

### 3. Toda acción de uso diario tiene también una forma mecánica, sin lenguaje

Las funciones que el usuario usa todos los días para cotizar y facturar (no
las raras, las del pan de cada día) deben tener SIEMPRE dos caminos:
1. Lenguaje natural en el chat (para cuando está ocupado o en el celular).
2. Un formulario o botón directo, con campos explícitos (dropdowns, casillas,
   números) que llama exactamente a la misma función real que usa el chat —
   nunca una copia de la lógica, la misma función. Aquí no se adivina nada de
   texto: el usuario elige de una lista, así que nunca puede fallar por un
   error de escritura o de reconocimiento de frase.

El resto de las funciones — las que se usan rara vez — se quedan solo en el
chat de lenguaje natural. No se construye un botón por cada función que
existe: si el sistema tiene mil capacidades, no se hacen mil botones. El
lenguaje natural existe precisamente para no tener que hacer eso. La regla es:
alto uso + alto costo de un error → mecánico. Bajo uso → lenguaje.

### 4. Nunca un parche encima de un valor incorrecto — se corrige en el origen

Cuando algo está mal, la corrección se hace en el lugar exacto donde nace el
dato incorrecto, no con una tabla de traducción o un "if" que intercepta el
valor malo antes de que llegue a donde importa. Una tabla de traducción que
arregla un valor al vuelo dura hasta el día en que alguien crea una ruta
nueva que no pasa por esa tabla — y ese día vuelve a fallar exactamente igual,
pero en un lugar distinto, y parece un bug nuevo cuando es el mismo de
siempre.

Toda limpieza de datos de entrada (quitar comillas de una ruta de archivo,
normalizar mayúsculas, quitar acentos) se hace UNA sola vez, en la función
real que consume ese dato — nunca en cada quien-la-llama por separado. Así
sea el chat, un formulario o una llamada futura que nadie ha escrito todavía,
todos quedan arreglados con un solo cambio.

### 5. Contrato de respuesta idéntico en todos los endpoints

Toda función que se expone como endpoint del servidor devuelve exactamente la
misma forma de respuesta: `{status: "ok" | "error", mensaje: "..."}` más los
datos específicos de esa acción. Nunca un endpoint usa `detalle`, otro
`error`, otro `mensaje` para decir lo mismo — eso hace que el frontend tenga
que adivinar qué campo leer, y cuando adivina mal, el usuario ve un mensaje
genérico e inútil en vez del error real que el servidor sí calculó bien.

### 6. Nunca inventar una respuesta — jamás

Si ningún proveedor de IA responde, el sistema lo dice tal cual, sin fingir
una respuesta y sin quedarse callado sin explicación. Si una respuesta viene
de un modelo de respaldo más limitado (no el principal), el sistema lo
declara en la misma respuesta — el usuario tiene derecho a saber de dónde
salió lo que está leyendo.

### 7. Nada se declara "listo" sin las tres pruebas, en este orden

1. El código se reinicia de verdad (matar el proceso viejo, lanzar el nuevo).
2. Se confirma, leyendo el log del proceso vivo (no el archivo en disco), que
   el cambio realmente está corriendo — un archivo editado no sirve de nada
   si el proceso que sigue vivo es el de antes del cambio.
3. Se prueba con un caso real, con datos reales que el usuario de verdad va a
   usar (no un caso de laboratorio inventado) — y se prueba desde donde el
   usuario realmente lo va a usar (el panel, el chat, WhatsApp), no solo
   leyendo el código y asumiendo que va a funcionar.

Sin las tres, no está "arreglado" — está "editado", que no es lo mismo.

### 8. Los precios y fórmulas de negocio viven en un solo módulo

Toda la aritmética de cuánto cobrar (materiales × margen, minutos de corte ×
tarifa, diseño, instalación) vive en una sola función que toda la aplicación
llama — el panel, el chat, cualquier reporte. Nunca se reescribe la misma
cuenta en dos lugares "porque es rápido copiarla" — el día que cambie un
precio, cambia en un lugar y automáticamente es correcto en todos los demás.

Cualquier número que se le muestre al usuario y que se pueda malinterpretar
por su unidad (área en cm² que parece m² a simple vista, por ejemplo) se
acompaña siempre de su equivalente en la unidad más natural de leer.

### 9. Arquitectura en capas, agnóstica del giro del negocio

- **Motores**: las capacidades reales, la despensa. Nunca se borra una
  función de aquí para "limpiar" — solo se agregan. Lo que no sirve se
  documenta como obsoleto y se archiva aparte, nunca se elimina en silencio.
- **Equipos**: recetas declarativas que combinan motores para un resultado de
  negocio (cotizar, generar una caja, publicar un post).
- **Cerebro**: la única capa de decisión — el sistema de lenguaje de la regla
  2 vive aquí, y solo aquí.
- **Consola**: la interfaz. No sabe de qué gira el negocio (láser, faros,
  lo que sea) — carga un "paquete de dominio" que sí lo sabe. Así el mismo
  motor de consola sirve para vender el sistema a otro negocio sin
  reescribir nada del núcleo.

### 10. El sistema debe poder operar sin la persona que lo programó

Todo reinicio, todo respaldo, toda recuperación debe poder hacerla el dueño
del negocio solo, sin depender de quien escribió el código — con scripts
simples, con contraseñas por default documentadas, con un manual generado
del código real (nunca escrito a mano aparte, porque se desactualiza). Si una
función requiere que el programador original esté presente para mantenerla
viva, esa función está mal diseñada, sin importar qué tan bien funcione hoy.

### 11. Honestidad radical en cada respuesta, sin excepción

El sistema nunca dice que hizo algo que no hizo, nunca oculta que una
herramienta no existe fingiendo que sí, nunca reporta éxito sin haber
verificado el resultado real. Si algo no se puede hacer, se dice
directamente y se explica qué sí se puede hacer en su lugar — sin inventar
una salida falsa para no decepcionar.

---

## Por qué este prompt y no otro

Cada regla de arriba tiene un bug real de hoy o de sesiones pasadas detrás:

| Regla | Bug real que la originó |
|---|---|
| 1. Una sola fuente de verdad | Modelo de Groq dado de baja, escrito a mano en 29 archivos — arreglar uno no arregló nada |
| 2. Un solo cerebro de lenguaje | `consciencia.py` y `lengua_anuar.py` compitiendo, el segundo pisando al primero, mismo bug arreglado dos veces por separado |
| 3. Mecánico para lo diario | "quita el fondo" fallaba en el chat por typo o frase rara — pero ya existía como botón directo, sin lenguaje, en el panel |
| 4. Corregir en el origen, no parchar | El primer arreglo del modelo de Groq fue una tabla-traductora — se quitó apenas se corrigió la causa real, porque dejarla ahí seguía siendo un parche |
| 5. Contrato de respuesta único | El panel de cotizar leía `r.detalle` pero el servidor mandaba `r.mensaje` — el error real existía pero el usuario nunca lo vio |
| 6. Nunca inventar respuesta | "Se cayeron los tres" — Groq, Gemini y el modelo local fallaron a la vez, y el sistema lo dijo en vez de inventar una respuesta |
| 7. Las tres pruebas antes de "listo" | El formulario de cotizar por ruta se dio por "ya existe, verificado" leyendo el código, sin probarlo con una ruta real con comillas — falló en vivo |
| 8. Fórmulas en un solo módulo | La regla de sumar áreas de vinil (no precios) vive en el motor para que el panel y el chat nunca se desalineen |
| 9. Capas agnósticas | Así el mismo AURORA puede venderse a otro negocio sin reescribir el núcleo |
| 10. Operable sin el programador | Es la prioridad #1 declarada: que AURORA funcione sin que el dueño dependa de quien la construyó |
| 11. Honestidad radical | AURORA fingía acciones y negaba poder abrir archivos — 4 bugs cerrados de raíz en julio por esto mismo |
