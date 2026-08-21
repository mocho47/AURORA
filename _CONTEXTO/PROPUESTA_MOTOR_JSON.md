# PROPUESTA — Contrato del motor (`motor.json`)

**Esto es investigación y propuesta, no implementación.** No se tocó código de
ningún motor. No existe todavía ningún `motor.json` real en disco. Es la tarea
que pide el pendiente #2 de `ESTADO_REAL.md`: *"Contrato del motor — sin él,
separar la Fábrica es cosmético"*.

**Hallazgo que cambia el punto de partida: esto ya se intentó TRES veces.**
Antes de proponer una forma nueva, hay que decirlo con nombre y línea, porque
si no se corre el riesgo de construir un cuarto intento abandonado.

---

## PARTE 0 — Lo que ya existe (los tres intentos previos)

### Intento 1 — `CEREBRO/registrador_bus.py` (el registro a mano, vivo, 35 motores)

Es el que funciona hoy. Cada motor es un bloque de 15-40 líneas escrito a
mano: carga el módulo por ruta (`spec_from_file_location`), arma un callback
`async def callback(msg) -> Optional[dict]` que lee `msg.contenido.get("accion", ...)`
y llama al método o función real, atrapa la excepción con un `try/except`
que solo escribe a un log que nadie ve en vivo, y termina con
`bus.registrar(motor_id, callback)`. 1,064 líneas, 35 motores, cero forma
declarada — "un motor" es literalmente lo que alguien escribió aquí.

### Intento 2 — `CEREBRO/plugins.py` + `PLUGINS/*.json` (parcial, con un bug real)

El propio docstring de `CEREBRO/plugins.py` (líneas 25-26) dice:

> *"Esto también cierra el pendiente viejo del `motor.json`: es el contrato
> del motor, pero escrito para lo que de verdad hacía falta."*

**Esto no está cerrado y hay que decirlo directo, no con reservas:**

- Cubre **3 de 35** motores: `PLUGINS/estratega_shorts.json`,
  `PLUGINS/etiquetas.json`, `PLUGINS/plantillas_prenda.json`.
- Es un catálogo de **ruteo de chat** (frase → app → acción), pensado para
  que AURORA reconozca qué le están pidiendo. No declara identidad del motor,
  ni requisitos (.env, dependencias), ni cómo se conecta al bus — nada de lo
  que pide el pendiente #2.
- **Tiene un bug reproducible, verificado, no inferido**, en la propia pieza
  que se anuncia como la solución. `ejecutar()` (`CEREBRO/plugins.py:152-192`)
  lee las acciones así:
  ```python
  a = next((x for x in p.get("acciones", []) if x.get("nombre") == accion), None)
  ```
  Esto asume que `acciones` es una **lista** de dicts con `nombre`/`funcion`/`params`.
  Pero se verificó con Python que **2 de las 3 fichas reales** (`etiquetas.json`,
  `estratega_shorts.json`) escriben `acciones` como **diccionario**, con claves
  `funcion`/`para_que`/`pide` — la forma que sí entiende `_pares_acciones()`
  (usada por `buscar()` y `catalogo()`, ahí sí con la normalización correcta,
  `plugins.py:71-85`). Si `acciones` es dict, iterarlo con `for x in ...` da
  **las claves** (texto), y `x.get("nombre")` truena con `AttributeError` —
  **antes** de llegar al único `try/except` que hay más abajo en la función.
  O sea: `ejecutar()` está roto hoy para `etiquetas` y `estratega_shorts`, y
  solo funciona para `plantillas_prenda.json`, que sí usa lista.

Este es exactamente el patrón que ya está anotado en la memoria del proyecto
(Calamardo, el .exe que nunca existió): algo se declaró "listo" y nadie lo
volvió a correr.

### Intento 3 — `MOTORES/adaptadores.py` (una capa de adaptadores, mitad huérfana)

Define **9 clases adaptadoras** (`MotorOracle`, `MotorFichas`, `MotorTaller`,
`MotorSublimacion`, `MotorPublicador`, `MotorVoz`, `MotorAsesor`, `MotorEditor`,
`MotorBuscador`, `MotorProgramador`, más `MotorCorel`), cada una envolviendo un
módulo de funciones (`taller_core`, `vendedor_core`, `asesor_core`, etc.) en
métodos async con nombre y `get_status()`.

`registrador_bus.py` **solo usa 2 de las 9`** (`MotorOracle`, `MotorCorel`, vía
`import adaptadores as _adap`). Las otras 7 —`MotorTaller`, `MotorSublimacion`,
`MotorPublicador`, `MotorVoz`, `MotorAsesor`, `MotorEditor`, `MotorBuscador`,
`MotorFichas`, `MotorProgramador`— existen y no las llama nadie: el bus
carga esos mismos módulos por su cuenta, con callbacks escritos a mano que ya
se separaron de lo que la clase adaptadora ofrece. Ejemplo verificado:
`MotorTaller.vectorizar()` existe en `adaptadores.py:101-103`, pero el
callback real del bus para `taller_core` (`registrador_bus.py:337-351`) no
tiene acción `vectorizar` — solo `catalogo`, `disponible` y el default
`convertir_a_dxf`. Los dos ya no dicen lo mismo.

### Intento 4 (el que nadie cuenta como intento porque nunca se usó) — `CEREBRO/nucleo.py`

Este es el hallazgo más importante de los cuatro. `CEREBRO/nucleo.py` (230
líneas) es un contrato **completo, firmado y nunca conectado**:

- Nace el 2026-08-10 y quedó **firmado por escrito** en
  `_CONTEXTO/PLAN_Y_CONTRATO.md` (11-ago-2026), Fase 0: *"Un motor no se puede
  ofrecer si no trae CÓMO COMPROBAR QUE HIZO SU TRABAJO."*
- Define `Resultado` (`hizo`, `detalle`, `evidencia`, `parcial`, `salida`,
  `segundos`, `motor`) y `Motor` (`clave`, `hace`, `ejecutar`, `verificar`,
  `necesita`, `peligrosa`, `probado_en_real`). `Motor.__post_init__` **exige**
  un `verificar` callable o levanta `ValueError` — el motor ni se registra.
  `atender()` ejecuta y **luego verifica contra la realidad**, nunca contra
  lo que el motor opina de sí mismo.
- Se verificó con `grep` en todo el repo: **ningún archivo de código importa
  `CEREBRO.nucleo` ni llama a `nucleo.registrar()`**. `_MOTORES` está vacío
  siempre. Ninguno de los 35 motores de `registrador_bus.py` — ni los
  registrados después del 11-ago (`etiquetas`, `estratega_shorts`,
  `analizador_mercado`, `buscador_clientes`, `licencias`, `plugins_catalogo`,
  `texto_a_corte`, todos con fecha 2026-08-20 en sus comentarios) — pasan por
  aquí. Es cimiento sin nada construido encima.

**Por qué importa para esta propuesta:** ya existe, ya está firmado, y ya
tiene exactamente el campo que el pendiente #2 necesita para no ser cosmético
(`verificar`). No hay que inventar esa pieza — hay que decidir si `motor.json`
alimenta a `nucleo.py` o si `nucleo.py` se da por superado. Proponer un
`motor.json` que ignore esto sería un **quinto** intento paralelo.

---

## PARTE 1 — El patrón real de los 35 motores

Se leyeron los 35 bloques de `registrador_bus.py` y se revisaron 8 archivos
fuente reales (`motor_cotizador.py`, `MOTORES/adaptadores.py`,
`TALLER/etiquetas.py`, `TALLER/taller_core.py` [por su bloque],
`MARKETING/estratega_shorts.py` [por su bloque], `MERCADO/analizador_mercado.py`
[por su bloque], `MEMORIA/sistema_memoria.py`, `CEREBRO/auto_conocimiento.py`).
Hay exactamente **dos formas**, no treinta y cinco:

### Forma A — clase + instancia única (`motor = Clase()`), un método principal

Ejemplo real, `MOTORES/motor_cotizador.py`:
```python
class MotorCotizador:
    def __init__(self):
        self.motor_id = "motor_cotizador"
        self._groq = AsyncGroq(...) if os.getenv("GROQ_API_KEY") else None
        self.stats = {...}
    async def cotizar(self, requerimiento: str, contexto: dict = None) -> Dict:
        ...
        return {"status": "OK"|"ERROR", "motor": ..., ...}
    def get_status(self) -> Dict: ...

motor = MotorCotizador()
```
El bus llama `metodo(consulta, contexto)` genéricamente vía `_callback_para()`
(`registrador_bus.py:60-82`). Devuelve siempre `{"status": "OK"|"ERROR", ...}`.
**12 motores** son de esta forma: los 9 de `motores_llm`, más
`motor_marketing`, `motor_oracle` y `motor_corel` (estos dos últimos vía las
clases adaptadoras de `adaptadores.py`, con 2-3 métodos en vez de uno).

### Forma B — módulo de funciones sueltas, sin clase, sin `motor_id`

Ejemplo real, `TALLER/etiquetas.py`: son puras `def` a nivel de módulo
(`etiqueta()`, `pliego()`, `sticker()`, `lotes()`, `variantes()`,
`cuanto_cobrar()`...), síncronas, sin estado, sin `self`. El bus las envuelve
en `loop.run_in_executor(None, ...)` y arma **a mano** el dispatch por
`accion` dentro de cada bloque (ver `registrador_bus.py:801-843` para
etiquetas). **23 motores** son de esta forma: `vendedor_core`,
`verificador_core`, `taller_core`, `sublimacion_core`, `sistema_memoria`,
`motor_sueno`, `analitica_marketing`, `voz_google`, `asesor_marketing`,
`publicador_core`, `oracle_core`, `whatsapp`, `telegram`, `email`,
`auto_conocimiento`, `auto_reparacion`, `etiquetas`, `estratega_shorts`,
`analizador_mercado`, `buscador_clientes`, `licencias`, `plugins_catalogo`,
`texto_a_corte`.

### Lo que NINGÚN motor declara hoy, de ninguna forma

- Qué acciones soporta y sus parámetros — vive solo en el `if/elif` de
  `registrador_bus.py`, a mano.
- Qué necesita para funcionar (.env, librería, app externa, base de datos) —
  vive disperso: `os.getenv("GROQ_API_KEY", ...)` en el motor, `import qrcode`
  / `from reportlab...` / `import fitz` dentro de las funciones de
  `etiquetas.py` (líneas 176, 211, 330, 385, 412 — imports perezosos, ni
  siquiera arriba del archivo), `pychromecast` dentro de `voz_google.py`.
  Un solo `requirements.txt` monolítico de 62 líneas junta todo, sin decir
  qué motor ocupa qué.
- Un verificador (`nucleo.py` sí lo exige, pero nada lo usa).

**Esta doble ausencia —ni el "qué acciones" ni el "qué necesita" están en
ningún lugar legible por máquina— es el hueco real que llena `motor.json`.**
Y ya se vio en vivo dos veces adónde lleva no tenerlo: el callback de
`sistema_memoria` (`registrador_bus.py:398-403`) llamaba a métodos que no
existían (`guardar_episodio`/`buscar_semantico`/`obtener_episodios_recientes`
en vez de los reales `registrar`/`recordar`/`episodios_recientes`), y el de
`auto_conocimiento` (`registrador_bus.py:751-757`) hacía lo mismo con
`capacidades()`/`mapa_sistema()`/`estado_integraciones()`. Los dos fallaban en
silencio —`AttributeError` atrapado, perdido en un log— y los encontró Anuar
usando AURORA, no una auditoría. Un `motor.json` cuyo `funcion` se valida
contra el módulo real al cargarlo habría atrapado los dos **antes** de que le
llegaran a él.

---

## PARTE 2 — Esquema propuesto de `motor.json`

Reutiliza el vocabulario que ya existe en `PLUGINS/*.json`
(`app`/`nombre`/`que_hace`/`motor`/`frases`/`palabras`/`acciones`/`funcion`/
`para_que`/`pide`) para no inventar un segundo idioma, y **arregla** la
ambigüedad dict-o-lista fijando `acciones` siempre como **lista** (es la forma
que `ejecutar()` ya sabe leer sin tronar). Le agrega los tres campos que hoy
no existen en ningún lado: `tipo`/`conexion` (cómo lo carga el bus),
`requisitos` (qué necesita para funcionar) y `verificar` (el campo que
`CEREBRO/nucleo.py` ya exige por contrato firmado, aquí opcional al inicio
para no bloquear la migración, pero con su lugar reservado desde el día uno).

```jsonc
{
  "motor_id": "etiquetas",                     // = motor_id / clave, único
  "nombre": "Etiquetas y Trazabilidad",
  "que_hace": "Etiquetas de producto con logo, QR, lote y fecha...",

  "archivo": "TALLER/etiquetas.py",             // ruta real desde ROOT
  "tipo": "modulo_funciones",                   // "clase_singleton" | "modulo_funciones"
  "objeto_bus": null,                           // si tipo=clase_singleton: nombre del atributo (ej. "motor")
  "sincrono": true,                             // true = se llama con run_in_executor

  "accion_default": "cuanto_cobrar",            // qué corre si el mensaje no trae "accion"
  "acciones": [
    {
      "accion": "etiqueta",
      "funcion": "etiqueta",
      "para_que": "Una etiqueta suelta. Saca PDF, PNG y DXF.",
      "pide": ["nombre", "lote", "qr", "logo", "variante", "ancho_mm", "alto_mm"],
      "verificar": null
    },
    {
      "accion": "cuanto_cobrar",
      "funcion": "cuanto_cobrar",
      "para_que": "Precio con la fórmula de Anuar: materiales +20%, corte $8/min a 20 mm/s, más diseño.",
      "pide": ["piezas", "ancho_mm", "alto_mm", "hoja", "costo_hoja", "diseno"],
      "verificar": null
    }
  ],

  "requisitos": {
    "env": [],
    "paquetes": ["qrcode", "reportlab", "PyMuPDF"],   // no cubiertos como top-level import; se ven al leer el archivo
    "apps_externas": [],
    "datos": ["taller.db (tabla de lotes)"]
  },

  "peligrosa": false,
  "probado_en_real": true,
  "fuente_registro": "CEREBRO/registrador_bus.py:801-843"
}
```

### Caso 2 — motor Forma A (clase+singleton), `motor_cotizador`

```jsonc
{
  "motor_id": "motor_cotizador",
  "nombre": "Cotizador ATF/MILENS",
  "que_hace": "Genera cotizaciones con 3 opciones (Estándar/Premium/Cierre) usando el catálogo real.",

  "archivo": "MOTORES/motor_cotizador.py",
  "tipo": "clase_singleton",
  "objeto_bus": "motor",                        // MOTORES/motor_cotizador.py define `motor = MotorCotizador()`
  "sincrono": false,

  "accion_default": "cotizar",
  "acciones": [
    {
      "accion": "cotizar",
      "funcion": "cotizar",
      "para_que": "Cotización real con 3 opciones, catálogo ATF (106 productos) o MILENS (73 servicios).",
      "pide": ["requerimiento", "contexto.negocio (opcional, se detecta solo)"],
      "verificar": null
    }
  ],

  "requisitos": {
    "env": ["GROQ_API_KEY"],
    "paquetes": ["groq"],
    "apps_externas": [],
    "datos": ["CONFIG/catalogo_atf.json", "TALLER/cotizador_servicios.py (catálogo MILENS)"]
  },

  "peligrosa": false,
  "probado_en_real": true,
  "fuente_registro": "CEREBRO/registrador_bus.py:161-206"
}
```

### Caso 3 — motor Forma A con varias acciones reales, `motor_oracle`

```jsonc
{
  "motor_id": "motor_oracle",
  "nombre": "ORACLE — CRM (vía adaptador)",
  "que_hace": "Leads y resúmenes del CRM SQLite de ATF/MILENS.",

  "archivo": "MOTORES/adaptadores.py",
  "clase": "MotorOracle",
  "tipo": "clase_singleton",
  "sincrono": false,

  "accion_default": "resumen",
  "acciones": [
    {"accion": "crear_lead", "funcion": "crear_lead",
     "pide": ["nombre", "telefono", "negocio"], "verificar": null},
    {"accion": "listar_leads", "funcion": "listar_leads",
     "pide": ["estado (opcional)"], "verificar": null},
    {"accion": "resumen", "funcion": "resumen",
     "pide": ["negocio (opcional)"], "verificar": null}
  ],

  "requisitos": {"env": [], "paquetes": [], "apps_externas": [], "datos": ["oracle.db"]},
  "peligrosa": false,
  "probado_en_real": true,
  "fuente_registro": "CEREBRO/registrador_bus.py:216-225 + MOTORES/adaptadores.py:20-45"
}
```

### Notas de diseño (por qué cada campo, no aspiracional)

- **`tipo`/`objeto_bus`/`sincrono`** — existen porque son la única diferencia
  real de cómo el bus tiene que invocar al motor (`await metodo(...)` directo
  vs `run_in_executor`). Sin esto un loader genérico no sabe cuál de los dos
  caminos tomar.
- **`acciones` siempre lista** — corrige el bug verificado de la Parte 0
  (dict vs lista). No se propone soportar ambas formas "por compatibilidad":
  eso es lo que ya causó el bug.
- **`requisitos`** — se ancla en lo que ya se ve en el código
  (`os.getenv(...)`, imports perezosos dentro de función, nombres de app
  externa en comentarios como "Google Cast", "CorelDRAW COM", "Inkscape").
  No se propone un gestor de dependencias por motor (`requirements.txt` sigue
  siendo uno solo) — el campo es **documental y de diagnóstico**: que al
  registrar un motor y fallar, el error diga "te falta GROQ_API_KEY" en vez
  de perderse en el log, tal como ya casi lo hace `motor_cotizador.cotizar()`
  con `"ERROR", "detalle": "Sin GROQ_API_KEY"`.
- **`verificar`** — se deja el campo **desde ya**, opcional (`null` es
  válido), justo para que quien migre un motor no tenga que resolver la
  Fase 1/2 completa de `PLAN_Y_CONTRATO.md` para poder escribir su
  `motor.json`. Pero el campo existe, con su nombre real
  (`Motor.verificar` en `CEREBRO/nucleo.py:99`), para que el día que se
  decida usar `nucleo.py` de verdad, `motor.json` ya tenga dónde apuntar y no
  haga falta un segundo formato.
- **`fuente_registro`** — no es cosmético: apunta a las líneas exactas de
  `registrador_bus.py` que hoy hacen lo mismo a mano, para que migrar un
  motor sea "leer esto, transcribirlo" y no "adivinar".

### Lo que este esquema deliberadamente NO resuelve hoy

No decide si `motor.json` alimenta a `CEREBRO/nucleo.py` (Intento 4) o si ese
archivo se da por superado y se retira. Esa es una decisión de Anuar, no
técnica — implica reabrir la Fase 1/2 de un contrato que él mismo pausó el
14-ago-2026 al decidir "apps chicas aisladas". El esquema deja el campo
`verificar` listo para cualquiera de las dos respuestas sin tener que
rediseñar el JSON después.

---

## PARTE 3 — Plan de migración honesto

| grupo | motores | qué hace falta |
|---|---|---|
| **Forma A, sin refactor** | 12: los 9 `motores_llm`, `motor_marketing`, `motor_oracle`, `motor_corel` | Solo escribir el `.json`. La acción y sus parámetros ya están en una sola llamada por método — es transcripción directa desde `_callback_para()`/`_callback_marketing()`/`_callback_oracle()`/`_callback_corel()`. Cero cambio de código. |
| **Forma B, transcripción manual por bloque** | 23: `vendedor_core`, `verificador_core`, `taller_core`, `sublimacion_core`, `sistema_memoria`, `motor_sueno`, `analitica_marketing`, `voz_google`, `asesor_marketing`, `publicador_core`, `oracle_core`, `whatsapp`, `telegram`, `email`, `auto_conocimiento`, `auto_reparacion`, `etiquetas`, `estratega_shorts`, `analizador_mercado`, `buscador_clientes`, `licencias`, `plugins_catalogo`, `texto_a_corte` | Cada `if accion == "..."` de `registrador_bus.py` hay que leerlo a mano y convertirlo en una entrada de `acciones[]` — no es mecánico, porque el nombre de la acción, el de la función real y los parámetros no siempre coinciden (ej. `etiquetas`: acción `"colores"` llama a la función `variantes`). De estos, 2-3 son casi triviales por tener una sola rama real (`auto_reparacion` no tiene dispatch de `accion`, es una sola llamada). |
| **No migran solos** | `motor_code_gen` | Ligado también al pendiente de la Fábrica/IDE (`PENDIENTES_POR_MOTOR.md:79`) — depende de la misma decisión de fondo, no es un caso más de transcripción. |

**Total: 12 sin tocar código, 23 con una transcripción manual pero mecánica
(15-30 min cada uno leyendo su bloque), 1 fuera de alcance de este plan.**

### Candidato #1 para probar el contrato en vivo: `etiquetas`

No se elige un motor de Forma A (serían "gratis" y no probarían nada: la
prueba real es si el esquema aguanta el caso difícil). Tampoco se elige uno
crítico (`oracle_core`, `whatsapp`, `email` tocan leads y clientes reales).

`etiquetas` es el candidato porque:

1. Es Forma B con 6 acciones reales — prueba el caso difícil, no el fácil.
2. Bajo riesgo real: no manda mensajes, no toca leads, no cobra nada solo —
   produce archivos (PDF/PNG/DXF) y escribe en su propia bitácora SQLite.
3. **Ya tiene su ficha en `PLUGINS/etiquetas.json` — y esa ficha ya está rota**
   en `ejecutar()` (Parte 0, Intento 2). Migrarla a `motor.json` da a Anuar
   un antes/después verificable con sus propias manos: hoy `ejecutar("etiquetas",
   "pliego", ...)` truena con `AttributeError`; con el `motor.json` nuevo, no.
   No es solo un ejercicio de formato — cierra un bug real de paso.

Alternativa aún más chica si se quiere probar sin ningún efecto secundario en
disco: `analizador_mercado` (puro cálculo, sin archivos, sin base de datos).

---

## PARTE 4 — Riesgos reales

- **El riesgo más grande no es técnico, es repetir el patrón.** Ya hay tres
  intentos de contrato de motor en este repo y uno de ellos —`nucleo.py`—
  está firmado en un contrato con Anuar y nunca se usó. Un cuarto esquema que
  tampoco se conecta a nada es peor que no proponer nada, porque le suma
  confusión a la próxima persona (o sesión) que abra el repo preguntando
  "¿cuál de los cuatro es el bueno?". **Antes de escribir el primer `motor.json`
  real, alguien tiene que decidir explícitamente qué pasa con `plugins.py`
  (¿se corrige su bug y sigue siendo el ruteo de chat?) y con `nucleo.py`
  (¿se retira o se conecta?).** Este documento no toma esa decisión — la
  señala para que no se tome por omisión.
- **No versionar el esquema desde el inicio rompe silenciosamente.** Si
  `motor.json` cambia de forma más adelante (por ejemplo si se decide meter
  `verificar` de verdad), cualquier loader que ya exista debe poder leer las
  fichas viejas o fallar con un mensaje claro — no con un `AttributeError`
  como el de `plugins.py`.
  Recomendación: un campo `"version_contrato": 1` desde la primera ficha.
- **Migrar los 23 de Forma B a mano es trabajo real, no cosmético — subestimarlo
  rompe la promesa de "todo completo/real".** 23 bloques × 15-30 min es
  6-12 horas de lectura cuidadosa, no un script. Si se apura, se repite el
  error ya documentado de `sistema_memoria`/`auto_conocimiento`: nombres de
  función que no existen, atrapados en silencio.
- **Qué NO vale la pena estandarizar todavía:**
  - Las **suscripciones cruzadas** (`bus.suscribir(..., TipoMensaje.EVENTO, ...)`
    de `motor_ventas`, `motor_marketing`, `motor_reasoning`, `motor_sueno`) —
    son 4 casos, cada uno con su propia razón de negocio, y forzarlos a un
    campo genérico de `motor.json` los volvería menos legibles, no más.
  - Un **gestor de dependencias por motor** — con un solo `requirements.txt`
    que ya funciona, partirlo por motor es trabajo sin beneficio inmediato;
    el campo `requisitos.paquetes` de este esquema es documental, no un
    instalador.
  - Los **7 motores que hoy solo existen en `Consola de Motores`** como
    apagables (`motores_desactivados_bus()`, `registrador_bus.py:174-184`) —
    ese mecanismo ya funciona y no lo toca este esquema.

---

## Resumen para decidir

1. Se investigaron los 35 motores de `CEREBRO/registrador_bus.py`: hay
   exactamente 2 formas reales (clase+singleton, 12 motores; módulo de
   funciones con dispatch a mano, 23 motores) y ninguna declara sus acciones
   ni sus requisitos en un lugar legible por máquina.
2. Ya hay **tres intentos previos** de resolver esto: `CEREBRO/plugins.py`
   (parcial, 3/35, con un bug real verificado en `ejecutar()`),
   `MOTORES/adaptadores.py` (7 de 9 clases huérfanas, ya con drift real
   contra el bus) y `CEREBRO/nucleo.py` (completo, firmado en
   `PLAN_Y_CONTRATO.md` el 11-ago-2026, y **nunca usado por ningún motor**).
3. Se propone un esquema de `motor.json` anclado en el vocabulario que ya usa
   `PLUGINS/*.json`, con tres campos nuevos que hoy no existen en ningún
   lado (`tipo`/`objeto_bus`/`sincrono` para saber cómo invocarlo,
   `requisitos` para lo que necesita, `verificar` reservado para conectar
   con `nucleo.py` si Anuar decide usarlo).
4. Migración: 12 motores sin tocar código (solo el `.json`), 23 con
   transcripción manual del bloque real (6-12 horas de trabajo cuidadoso, no
   un script), 1 fuera de alcance por depender de la Fábrica/IDE.
5. El riesgo real no es de código: es que este sea un cuarto intento que
   tampoco se conecta a nada. Antes de escribir el primer `motor.json` en
   serio hay que decidir el destino de `plugins.py` y de `nucleo.py`.

**Recomendación de primer paso concreto, si Anuar decide seguir:**
No escribir los 35 de golpe. Escribir **un solo `motor.json` real para
`etiquetas`**, siguiendo el esquema de la Parte 2, y usarlo para dos cosas a
la vez: probar el contrato contra el caso difícil (Forma B, 6 acciones) y
arreglar de paso el bug ya verificado de `PLUGINS/etiquetas.json` en
`ejecutar()`. Es una entrega chica, comprobable con las manos (Anuar pide una
etiqueta por el chat y ve que sale bien), y sirve de plantilla real para
transcribir los otros 22 de Forma B después — sin haber apostado 6-12 horas
a un esquema que nadie probó todavía.
