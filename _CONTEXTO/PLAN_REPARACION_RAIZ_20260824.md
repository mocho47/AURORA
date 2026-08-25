# PLAN ÚNICO DE REPARACIÓN DE RAÍZ — AURORA
**2026-08-24 · Anuar Milán · Repo: C:\AURORA.worktrees**
**Versión 2** — corregida tras revisar la versión 1 (ver §7: qué estaba mal en mi propio plan).

Este plan NO arregla 38 bugs. Arregla las **causas** de las que esos 38 bugs
son síntomas. Si se corrigen las causas, los bugs se van en grupo y **dejan de
volver**.

Regla que gobierna todo: **cero parches.** No se corrige un valor en un
archivo; se elimina la posibilidad de que ese valor viva en dos lugares. Si un
arreglo no se puede hacer así, no se hace todavía y se dice por qué.

---

## 1. El diagnóstico, en una frase

AURORA no está mal construida. **Está construida dos veces.**

Cada bug crítico es la misma historia: existe la versión correcta de algo (la
fórmula de precios, el catálogo de ATF, el candado, el sistema de voz) **y
también una copia vieja que sigue viva**. Se corrige la buena, la copia sigue
corriendo, y semanas después el error reaparece pareciendo nuevo.

Eso es lo que ha costado los días perdidos: no falta de trabajo, sino trabajo
aplicado a una sola de las dos copias.

### La causa de la causa

¿Por qué hay copias? Porque en cuatro lugares distintos **algo se escribió a
mano en vez de derivarse de su fuente**:

| Lo que se escribió a mano | Dónde se ve el daño |
|---|---|
| Los precios y velocidades, copiados dentro del código | Cotizaciones equivocadas a clientes reales |
| La lista de qué respaldar, escrita a mano en el script | Un mes sin respaldos, y nadie se enteró |
| El estado del proyecto, escrito a mano en documentos | Cada sesión arranca con datos falsos |
| El texto de cada motor, copiado en un prompt | La lógica real del motor nunca se ejecuta |

**Una lista escrita a mano siempre se queda vieja.** Siempre. No es descuido
de nadie; es una propiedad de las listas a mano. El único arreglo que aguanta
es que el dato **se derive de su fuente** en vez de copiarse.

Ese es el principio que ordena todo este plan: **derivar, no copiar.**

---

## 2. Las causas y sus síntomas

| # | Causa | Bugs que explica | Gravedad |
|---|---|---|---|
| **A** | Precios, velocidades y fórmulas **copiados** dentro del código en vez de leerse de una sola fuente | 2.2, 2.6, 3.6, 4.6, 4.10, 4.11, 5.4, 5.5 | Crítica — cuesta dinero hoy |
| **B** | El despachador deja que una familia **fuerce** un candado, saltándose el disparador propio de ese candado | 2.1, 3.1, 4.1, 4.2 | Crítica — rompe la confianza a diario |
| **C** | Las pruebas verifican **texto y forma**, no comportamiento | 2.7, 2.8, 2.9, 3.7, 4.7, 4.8, 4.9 | Crítica — hace invisible todo lo demás |
| **D** | No hay **frontera de seguridad**: los secretos se protegen por costumbre, no por regla | 2.3, 2.4, 3.3, 4.4, 4.5, 5.2 | Crítica — expone acceso real |
| **E** | El respaldo tenía una **lista a mano** y nunca se verificó tras mover el proyecto | 2.5, 3.5 | Crítica — riesgo de perderlo todo |
| **F** | El chat usa el **texto del prompt** de cada motor, nunca su lógica real | 3.2 (y es la causa profunda de 2.2) | Alta |
| **G** | La documentación se escribe a mano y **nada marca qué está superado** | 3.8, 4.12, 5.6, la cadena de "planes maestros" | Media — quema tiempo cada sesión |

**Hallazgos nuevos, encontrados hoy al revisar la voz globalmente** (la
auditoría no cubrió `VOZ/`, lo dijo explícitamente):

| # | Hallazgo | Por qué importa |
|---|---|---|
| **H** | **La voz no arranca sola.** Solo se enciende pidiéndolo por el chat (`consciencia.py:5050`). | Para usar la voz hay que ir a la PC y escribir — justo lo que la voz existe para evitar. La capacidad está bien construida y desconectada. |
| **I** | **Dos sistemas de voz que no se conocen**: `VOZ/servicio_voz.py` (bocinas, edge-tts) y `voz_google` (Google Home, en el bus). | Es la causa A aplicada a la voz. Nadie decide cuál habla. |
| **J** | La voz crea **su propio bucle de eventos** por comando (`consciencia.py:5087`), aparte del servidor. | No ha tronado, pero es frágil por diseño: dos bucles tocando la misma memoria y el mismo bus. |
| **K** | El modelo de Vosk **no está en el repo** (`VOZ/.gitignore` lo excluye) ni en el respaldo. | Si restauras AURORA en otra PC, la voz queda muda sin avisar. |

---

## 3. El orden — y por qué este y no otro

El orden **no** es por gravedad. Es por dependencia: cada fase hace posible
verificar la siguiente.

> **Corrección importante sobre la versión 1 de este plan:** yo había puesto
> las pruebas reales en fase 3, *después* de tocar precios y despachador. Eso
> estaba mal y era el mismo error que causó todo esto: habría hecho los dos
> cambios más peligrosos verificándolos con la misma suite ciega que ya
> demostró no ver nada. **La red se pone antes de caminar por el alambre.**

### FASE 0 — Cerrar la puerta
*Causas D, E, K. No toca lógica de negocio, así que no puede romper AURORA.*

1. Reemplazar `SETUP/backup_aurora.py` (ya escrito, ver §6).
2. **Correr el respaldo y abrir el resultado.** No se da por bueno porque el
   script "ya no truena".
3. Corregir la tarea programada de Windows, que también apunta a `C:\AURORA`.
4. Endurecer el PIN (ya escrito, ver §6) y elegir uno de 8+.
5. Sacar `CONFIG/identidad.json` y `CONFIG/contactos.json` de git; purgar del
   historial esos y la llave vieja de Groq.
6. Borrar `_OBSOLETOS/AURORA_duplicado/` (copia byte a byte).

**Terminada cuando:** existe un ZIP de respaldo con las 14 bases verificadas
íntegras, `LastTaskResult` de la tarea es 0, y `git log` ya no contiene ninguna
credencial.

**Vuelta atrás:** trivial, nada de esto cambia comportamiento.

### FASE 1 — Poner la red
*Causa C. Sin esto, ninguna fase posterior se puede dar por buena.*

Tres pruebas, no trescientas:
1. Una que instancie `Consciencia` y llame a `procesar()` de punta a punta con
   mensajes reales, verificando **la respuesta**, no qué motor se eligió.
2. Una que levante el servidor real y golpee por HTTP los endpoints del taller
   más usados.
3. Una que corra la cadena foto→DXF completa con una imagen real y verifique
   que el DXF sale con geometría válida.

Y una regla nueva permanente: **cada bug que se arregle desde hoy nace con su
prueba de comportamiento**, nunca con una prueba de que cierto texto existe.

**Terminada cuando:** las tres pruebas existen, pasan, y —comprobado a
propósito— **fallan** si se rompe el comportamiento adrede.

**Vuelta atrás:** no aplica, solo agrega.

### FASE 2 — El candado que sabe lo que hace
*Causa B. Es lo que rompe la confianza en el uso diario.*

Hoy, si una familia reconoce un mensaje, **obliga** a ese candado aunque su
propio disparador diga que no aplica. Por eso "abre mi agenda" abre el
navegador.

El arreglo de raíz es una sola idea: **la familia prioriza, no obliga.** Si la
familia dice "esto es del candado X", X va primero — pero X conserva el derecho
a decir "esto no es mío", y entonces el turno **sigue** a los demás en vez de
morir ahí. Son ~15 líneas (ya escritas, ver §6) y matan la clase entera de
bugs de secuestro, no solo el de "abre".

**Terminada cuando:** las 425 pruebas siguen verdes, la prueba nueva de
punta a punta cubre "abre mi agenda de hoy" → agenda, y las 174 frases reales
de `PRUEBAS_VIVAS/` siguen resolviendo al mismo candado que antes.

**Vuelta atrás:** un solo bloque en un solo archivo; revertir es un `git revert`.

### FASE 3 — Una sola fuente para los números
*Causa A. Es lo que cuesta dinero cada día que pasa.*

Principio: **ningún archivo vuelve a escribir un precio, una velocidad o un
margen.** Todos los leen de `TALLER/formula_precios.py` y de los JSON de
`CONFIG/`. Un archivo que necesite un número y no lo pueda leer **falla
ruidoso**; nunca inventa un valor de respaldo (hoy `motor_cotizador.py:34`
inventa $180 si el catálogo falla — eso se va).

Se **elimina** la copia, no se corrige:
- `motor_negocios.py` y `motor_ventas.py`: fuera la tabla de precios de ATF.
- `indexar_dxf.py`, `produccion_piezas_grandes.py`, `cajas_boxes.py`: fuera
  `VELOCIDAD_MM_S`.
- `TALLER/generar_caja.py`: **verificado hoy** — `_generar_caja_real` usa
  `cajas_boxes.py`, nunca este archivo. Es un huérfano de línea de comandos con
  la fórmula vieja. Se archiva en `_OBSOLETOS/`, no se corrige.
- `CONFIG/operaciones.json`: velocidad vieja sin uso; se archiva.

**Terminada cuando:** existe una prueba que **recorre todo el repo y falla** si
encuentra un precio o una velocidad escritos a mano fuera de la fuente única.
Esa prueba es lo que impide que el bug regrese; sin ella la fase no está
cerrada aunque los archivos ya estén corregidos.

**Vuelta atrás:** rama propia, y la Fase 1 dice si algo se rompió.

### FASE 4 — Decidir qué es un motor
*Causa F. La más profunda; va después de tener red.*

Hoy el chat lee el *texto del prompt* de cada motor con una búsqueda de patrón
y nunca ejecuta la clase. Toda la lógica escrita dentro de los motores es
código muerto para el cliente real — y eso explica por qué el bug de precios de
ATF vivía en un string y no en una función.

Hay que decidir **una** de dos y escribirla como contrato:
- (a) el chat ejecuta las clases reales de los motores, o
- (b) los motores son solo prompts, y su lógica se elimina o se muda.

Dejarlo a medias —que es donde está— es lo que garantiza que el problema
vuelva. Aquí también se resuelve `motor_pedidos`, registrado como activo
aunque **el archivo no existe**.

**Terminada cuando:** ningún motor registrado en el bus carece de archivo, y
un cambio hecho dentro de una clase de motor se puede demostrar llegando al
chat (o se documenta que los motores son solo prompts y se borra la lógica
muerta).

### FASE 5 — La voz, completa
*Causas H, I, J, K. Va al final porque la voz habla con la misma boca que el
chat: arreglarla antes sería amplificar en audio los errores del chat.*

1. **Decidir cuál voz habla**; la otra pasa a ser una salida elegible, no un
   sistema paralelo.
2. **Arrancarla con AURORA**, con interruptor en configuración, para que sirva
   de verdad con las manos ocupadas en el láser.
3. **Un solo bucle de eventos**, compartido con el servidor.
4. **El modelo de Vosk al respaldo** (ya incluido en el script de la Fase 0).

**Terminada cuando:** dices el nombre sin haber tocado la PC y responde.

---

## 4. Lo que este plan NO hace

- **No reescribe AURORA desde cero.** Lo verificado funciona y son 2 años de
  trabajo real. Se corrigen causas, no se empieza de nuevo.
- **No toca las carpetas que la auditoría no revisó** (ORACLE, VENDEDOR,
  SUBLIMACION, MEMORIA, MARKETING, PUBLICADOR, INTEGRACIONES, EDITOR).
  Probablemente tienen los mismos patrones de la causa A — pero eso es una
  segunda auditoría, no una suposición. **No se "arregla" a ciegas lo que no
  se revisó.**
- **No persigue los 12 medios y 7 bajos uno por uno.** La mayoría muere sola
  al cerrar A, C y G. Los que sobrevivan se revisan al final, con la lista en
  la mano.

---

## 5. Lo que cuesta, honestamente

| Fase | Esfuerzo real | Riesgo de romper algo |
|---|---|---|
| 0 — cerrar la puerta | Corto | Casi nulo |
| 1 — poner la red | Medio | Nulo (solo agrega) |
| 2 — el candado | Corto de escribir, la verificación es lo que toma | Medio: toca el corazón del lenguaje |
| 3 — los números | Medio, son varios archivos | Medio |
| 4 — qué es un motor | **Largo.** Es rediseño, no corrección | Alto si se hace sin la Fase 1 |
| 5 — la voz | Medio | Bajo |

Las fases 0, 1 y 2 son las que cambian tu día a día. La 3 es la que deja de
costarte dinero. La 4 es la que evita que todo esto regrese en dos meses — y
es la única que de verdad pide tiempo.

---

## 6. Qué está escrito y qué no — a hoy

Nada de esto está integrado. **AURORA corre hoy exactamente igual que antes de
este plan.**

| Fase | Estado |
|---|---|
| 0 · respaldo | **Escrito, sin aplicar** → `_FIX_PROPUESTO_20260824/backup_aurora.py` |
| 0 · seguridad | **Escrito, sin aplicar** → `_FIX_PROPUESTO_20260824/identidad_core_endurecido.py`. El PIN nuevo y la purga del historial **esperan tu decisión** (la purga es irreversible). |
| 2 · candado | **Escrito, sin aplicar** → `_FIX_PROPUESTO_20260824/consciencia_despacho.py` |
| 1, 3, 4, 5 | **Especificadas, no escritas.** |

Las fases 4 y 5 no se escribieron porque **cada una necesita una decisión tuya**
(qué es un motor; cuál voz manda). Escribir código asumiendo esas respuestas
sería exactamente el error que este plan existe para no repetir.

---

## 7. Qué estaba mal en la versión 1 de este plan

Lo anoto porque el plan tiene que aguantar la misma vara que le pone al código.

1. **El orden estaba invertido.** Ponía las pruebas reales *después* de tocar
   precios y despachador — es decir, iba a hacer los cambios más peligrosos
   verificándolos con la suite que ya se demostró ciega. Corregido: la red va
   antes.
2. **Dejaba una suposición sin verificar.** Decía "hay que confirmar si
   `generar_caja.py` está muerto". Se podía comprobar en un minuto y no lo
   había hecho. Ya está comprobado y el dato está en la Fase 3.
3. **No decía cuándo termina cada fase.** Sin eso, es la misma trampa de "se
   arregla y no se cierra". Cada fase ahora tiene su "terminada cuando".
4. **No decía cómo volver atrás**, en un sistema del que depende tu negocio.
5. **No decía lo que cuesta.** Estás decidiendo con el dinero contado; tienes
   derecho a saber en qué te estás metiendo antes de empezar.
6. **Le faltaba el arreglo real de la causa G.** Los documentos de estado se
   siguen escribiendo a mano, que es la misma enfermedad que el resto del
   plan combate. Lo correcto es que `ESTADO_REAL.md` **se genere del sistema**,
   como ya se genera el manual de comandos desde el código — y así no pueda
   quedarse viejo.
