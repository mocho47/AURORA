# 📊 ESTADO REAL DE AURORA
### Última actualización: 2026-08-07

---

## 🎯 DÓNDE QUEDAMOS — 2026-08-07 (leer esto primero)

**293 pruebas pasan.** Último commit `2a5c7e5`, todo en GitHub.

### Probado en material o en vivo — no se re-verifica
| Qué | Evidencia |
|---|---|
| **Adaptar diseños a otro material** | **Anuar cortó y armó la casa de Bob Esponja** (3mm → 50% en 2.5) |
| Cajas (4 reglas, DXF, vista previa) | 4/4 por `/chat` con sus frases |
| Descargar archivos por red (Rocío) | HTTP 200 por 192.168.1.38; `.env` rechazado |
| Print & Cut: marcas de su Cameo 4 | medidas de un archivo que él exportó de SU Silhouette |

### Escrito y con pruebas, PERO SIN PROBAR EN VIVO
- Candados nuevos en el chat: `adaptar_diseno`, `print_and_cut`,
  `metodo_campana`, `campana_escolar` — **el servidor no se ha reiniciado**
- `TALLER/acomodar_hoja.py` (nesting) y `EDITOR/contorno_de_corte.py`
- Instagram en la tarea de ATF — no ha corrido la de las 19:00
- `corel_core.cerrar_a_curvas_y_publicar()` — **nunca con Corel abierto**

### Roto o pendiente, con el diagnóstico ya hecho
1. **El 50% no se aplica.** `_adaptar_diseno_real` entiende la escala (el
   regex la saca bien) pero el archivo sale sin escalar. Bug real, acotado.
2. **Casa de Calamardo**: devuelve `NO_HAY_RANURAS_SUELTAS`. Anuar lo
   desmintió —*"todo es encastres"*, y él ya la armó una vez— así que **es
   falla de detección**. Sospecha sin confirmar: encastres dentro de BLOCKs
   que `msp` no ve.
3. **18 mensajes de campaña sin enviar.** No es un bug: **la cuota mensual de
   Green API se agotó** (plan gratis, 20 mensajes, y solo deja hablar con 3
   números). Están listos en `Downloads\PENDIENTES_campana_18.txt`.
   **Mientras la cuota esté agotada, AURORA tampoco puede contestar WhatsApp
   a nadie más que a esos 3.**
4. **Instagram apunta a `rauna_892`**, la cuenta personal de Anuar. Falta que
   él decida si esa u otra de ATF.
5. **Nesting mezclado** — sin hacer, y es donde está el dinero: hoy cada
   tamaño va en su hoja y se tira 30-40% de cada una.

### El hallazgo que cambia precios
**Con marcas de registro caben la mitad de las piezas.** Se costeó la campaña
a 30 etiquetas por hoja y caben **14**. La etiqueta pasó de $0.26 a **$0.56**
y el paquete de primaria de 85% a **49% de margen**. Los precios de Rocío
($100 / $155 / $150 / $205) siguen sanos salvo **Primaria a $150**, que
debería subir a ~$180.

### Presupuesto
Anuar iba en **86% del límite semanal** (repone el 9 de agosto). Prioridad
acordada: (1) probar en vivo lo ya escrito, (2) el bug del 50%,
(3) nesting mezclado. Calamardo y el demo agnóstico quedan para después.

---

### Estado anterior: 2026-08-06

---

## 🆕 2026-08-06 — Cajas con las reglas de taller de Anuar

| Qué | Evidencia |
|---|---|
| **271 pruebas** | `python -m pytest tests/ -q` → 271 passed en 196 s (venían 244) |
| **Cajas en vivo** | 4/4 por `/chat` con sus frases literales, **DXF real verificado en disco** |
| **Cofre** | "cofre"/"baúl" → `PirateChest`. Él armó uno a mano para comparar: **quedó igual** |
| **PDF de gran formato** | `gomitas.pdf` 12 MB → arreglado 27 MB (era 247 MB con PNG; ahora JPEG) |
| **Trailer a DXF** | 58 trazos, capas CORTE (1) y GRABADO (57) separadas |

**Las 4 reglas de taller ya están EN EL CÓDIGO** (él las hacía a mano en la web
de boxes.py desde hace 2 años): orden **X, Y, H** · **DXF siempre** implícito ·
material 2.7 se corta a **2.5** (kerf) · dedos **con el punto quitado** (×10 del
default del generador). Detalle en `MANUALES/COMANDOS_VERIFICADOS.md`.

**3 falsos positivos del validador de honestidad, cerrados de raíz.** El que
importaba: el nombre de las cajas lleva el grosor (`..._2.5mm.svg`) y el regexp
cortaba la ruta en ese punto → decía "este archivo no existe" de un archivo de
75 KB que sí estaba. Como TODAS las cajas llevan el grosor en el nombre,
fallaba **siempre**. Lo encontró Anuar usando AURORA normal, igual que los 4
bugs anteriores.

**Cerrar a curvas ya se hace, no se pide.** `corel_core.cerrar_a_curvas_y_
publicar()` convierte y publica sobre una COPIA (su .cdr queda editable).

**Nota de método:** los "procesos que salían vacíos" toda la sesión eran el
buffer de stdout de Python al redirigir. Correr con `-u` o escribir a archivo.

---

### Estado anterior: 2026-07-31

> **Regla de este archivo:** aquí solo entra lo **verificado**, con evidencia.
> Nada de "debería funcionar". Si algo no se probó, va en la sección de
> no-verificado. **No re-verifiques lo que aquí ya dice verificado** — ese es
> exactamente el gasto que esta carpeta existe para evitar.

---

## ✅ Verificado y funcionando

| Qué | Evidencia |
|---|---|
| **74 pruebas de regresión** | `python -m pytest tests/ -q` → 74 passed en 61 s. Una prueba por bug real que de verdad ocurrió |
| **Candado anti-invención** | `CEREBRO/validador_honestidad.py` — 4/4 en vivo contra los inventos reales |
| **Fase 3 completa** | Las 20 carpetas del enrutador (~517 herramientas) revisadas comando por comando |
| **Navegación web natural** | 4/4 frases naturales con resultados reales (Amazon, proveedores de Guadalajara) |
| **Respaldo en GitHub** | `mocho47/AURORA` privado, al día, nada suelto |
| **Corel** | 8 comandos reales probados con Corel abierto (importar, extraer texto, escalar, exportar PDF 376 KB real, guardar copia 12.8 KB real, reparar conexión) |
| **Agenda** | Citas de hoy/mañana/próximas y creación real. No inventa cuando le faltan datos |
| **Cotizador** | Detecta el negocio solo: Milens (73 servicios) vs ATF (98 productos) |
| **Contactos** | Distingue familia de clientes; la intención de compra gana al tono (14/14) |
| **WhatsApp** | Green API instancia 7107622171, autorizada, envío real |
| **Multi-usuario** | Anuar y Rocío, ambos rol dueño, cada quien su PIN |
| **Panel** | 30 pestañas en 6 grupos, 163 endpoints, 0 crashes |
| **Offline** | Ollama local (llama3.2:3b) + SQLite. Aguanta sin WiFi; solo degradan web y publicar |

**Los dos manuales están al día:**
- `MANUALES/manual_comandos_aurora.md` — 679 líneas, **generado del código**
  (17 candados + 517 herramientas). Regenerar: `python CEREBRO/generar_manual.py`
- `MANUALES/COMANDOS_VERIFICADOS.md` — 147 líneas, **solo lo probado en vivo**

---

## ❌ No funciona (confirmado, con causa conocida)

| Qué | Por qué | Salida |
|---|---|---|
| **Exportar PNG/JPG desde Corel** | Incompatibilidad de pywin32, no del Corel de Anuar (el ejemplo oficial VBA sí corre dentro de Corel). 4 caminos intentados, los 4 fallaron | Usar PDF (funciona 100 %) o exportar a mano |
| **Caché `gen_py` de win32com corrupta** | Problema de entorno | Borrar `%TEMP%\gen_py` para que se regenere |
| **TikTok y YouTube** | Sin tokens propios | Pendiente de darlos de alta |
| **Marketplace de Facebook** | No tiene API pública | Usar Tienda/Catálogo |
| **Meta de Milens** | Faltan 4 variables en `.env` | Requiere un clic de Rocío en su PC |
| **Tareas de fondo largas** | Se cuelgan en `asyncio.to_thread` | Sin diagnosticar |

---

## ⚠️ Sabido pero sin arreglar

1. `vectoriza` / `vectorizar` no ejecuta directo como el resto de frases de su
   candado: pasa por el enrutador y pide confirmación aparte.
2. El enrutador prefiere `leer_archivo` sobre `abrir_archivo` cuando el usuario
   dice "ábrelo". Ya no es inseguro, pero sigue siendo la herramienta equivocada.
3. `generar_manual.py` no detecta candados con lógica compuesta (dos categorías
   de disparador a la vez, como `negocio` o `corel`). Hoy se avisa con nota a mano.
4. **Ruta sola: no completa sola la petición anterior (mitad pendiente).**
   La falsa negación YA se arregló (candado `ruta_sola`, verificado): mandar solo
   una ruta ya no responde "no puedo abrir archivos en la PC" — ahora ofrece las
   acciones reales con la ruta puesta. **Lo que falta** es la otra mitad: que la
   ruta complete sola la petición previa ("abre esta imagen en corel" + ruta →
   ejecutar). El código está escrito (`self._ultima_peticion` +
   `_ruta_sola_real`) pero **no se activa**.
   *Dos hipótesis descartadas el 2026-07-31:* (a) que el bloque de guardado
   estuviera después de los candados — se movió al inicio de `_procesar_interno`
   y siguió sin activarse; (b) que fuera el `session_id` — se verificó igual en
   ambos mensajes.
   *Sospecha viva sin comprobar:* el estado de instancia no persiste entre
   peticiones HTTP como se asumió. Comprobarlo primero antes de tocar más código.
   No es urgente: la mitad que funciona ya resuelve el problema real.

5. **FALSA NEGACIÓN al mandar solo una ruta.** Encontrado en vivo 2026-07-31:
   tras pedir "abre esto en Corel", al mandar solo `C:\...alon.jpg` (sin verbo)
   ningún candado la agarró, cayó a `motor_analisis` y contestó *"no tengo acceso
   a la PC"* — **es mentira, AURORA sí abre archivos en Corel.**
   *Causa:* el candado de Corel exige corel + acción, y el mensaje no traía
   ninguna de las dos; se perdió el hilo del mensaje anterior.
   *Arreglo de raíz propuesto:* si el mensaje es **solo una ruta de archivo** y el
   anterior pedía una acción sobre un archivo, usar esa ruta para completar la
   acción pendiente (ya existe el mecanismo: `_confirmar_accion_pendiente`).
   Es el patrón inverso al que se cerró: `_verificar_capacidad_real` debía
   atraparlo y no lo hizo.

6. **5 módulos muertos en CORE** que el enrutador cree disponibles. Quitarlos es
   decisión de Anuar (regla: no restar funciones sin su visto bueno).
7. Fichas del vendedor: solo 4 de 29 están completas. La del LED H4 tiene una
   incoherencia real (el texto menciona H7).
8. Videoteca: 296 archivos = ~127 únicos (169 duplicados sin depurar).

---

## 🚫 Documentos que AURORA generó y son FALSOS

**No usarlos. Se conservan solo como evidencia de por qué existe el candado.**

- **"MANUAL MAESTRO DE COMANDOS"** — 6 de 8 comandos inventados
  (`AGENDA/agrega_usuario`, `CORE/evalua_expresion`… ninguno existe)
- **"Kit de configuración crítica"** — manda ejecutar `REINICIAR_NGROK.bat`,
  `OPTIMIZAR_PC.bat` y `NEXUS.bat`. Los tres inexistentes.

Los manuales buenos son los dos de `MANUALES/` listados arriba.

---

## 🧭 Decisiones tomadas (no volver a discutirlas)

| Decisión | Fecha |
|---|---|
| AURORA es una **consola agnóstica de dominio**. El producto vendible es la consola + un **paquete de dominio**, no verticales separados | 30 jul |
| La Fábrica **se copia, no se corta**. AURORA sigue intacta; Aurorita XP es una copia con otro nombre, solo para generar motores | 30 jul |
| El cuello de botella de la motorteca es la **verificación**, no el disco. Mil motores ≈ 50 MB | 30 jul |
| FORJA es un proyecto **independiente e inconcluso**. Fuera del alcance de AURORA | 29 jul |
| Evolución se separa a su propia carpeta junto con NEXUS Teens | pendiente de ejecutar |
| MercadoLibre **pausado a propósito**. No reactivar | — |

---

## 📌 Pendientes por orden de valor

1. **Demo de AURORA con comandos normalizados** — es lo único que puede traer dinero esta semana
2. **Contrato del motor** (`motor.json`) — sin él, separar la Fábrica es cosmético
3. Precios de los 7 servicios de mano de obra de ATF — **los dicta Anuar**
4. Asistente de configuración inicial por voz — la pieza que vuelve vendible a AURORA
5. Unificar Evolución v1 y v2, separarla a su carpeta
6. Decidir qué se hace con `Marketing_Digital_Pro` (nunca se lanzó; el código se
   puede recuperar del .exe empacado con PyInstaller)
7. Distribución: instalador local + actualización automática

---

## 🖥️ Datos técnicos que siempre se preguntan

```
Ruta       C:\AURORA.worktrees
Arranque   python run_aurora.py   (~90 s, 28 motores en bus)
Puerto     5000
Salud      http://127.0.0.1:5000/health   ← 127.0.0.1, NO localhost (IPv6 falla)
Rocío      http://192.168.1.38:5000       (firewall abierto)
Python     C:\Program Files\Python312\python.exe
Pruebas    python -m pytest tests/ -q
Manual     python CEREBRO/generar_manual.py
GitHub     mocho47/AURORA (privado)
Reinicio   scratchpad/reiniciar.ps1  (evita falsos positivos del sandbox)
```

**Teléfono oficial de ATF: 3326148674.** Los viejos (3329879109, 3323530146)
están erradicados de todo el sistema; si aparece alguno, es un error.

---

## 📅 SESIÓN 2026-08-04 — lo que cambió

### Bugs de raíz cerrados (todos los encontró Anuar usando AURORA normal)
1. **"extrae el mapa de bits"** → faltaba el VERBO. Ahora los verbos se derivan del
   registro real de 537 herramientas (`_verbos_del_registro`), no de una lista a mano.
   Y "mapa de bits" llega a Corel sin nombrarlo (`_COREL_SIN_NOMBRARLO`).
2. **"✅ Abierto real" de una CARPETA** — `Path.exists()` da True para carpetas.
   `corel_core.abrir_documento` ahora las rechaza y compara el documento abierto
   contra el pedido: si no coincide, NO cuenta como hecho.
3. **Alerta falsa de WhatsApp** — `starting` y `sleepMode` son transitorios, no
   desconexión. Solo alerta por `notAuthorized` y `blocked`.
4. **El cotizador cotizó $75,000** cuando se pidió papel de MercadoLibre.
   `_es_compra_afuera` separa VENDER de COMPRAR.
5. **El conocimiento cargado era inalcanzable** — `_buscar_semantico` miraba solo
   la columna `tema`. Ahora busca en tema, patrón Y conocimiento, palabra por palabra.

### Mejoras
- **Aprende A LA PRIMERA** (`aprender_a_la_primera`): si el enrutador resuelve algo
  que ningún candado agarró, la frase queda registrada sin que Anuar tenga que
  reformular. Antes cada frase nueva le costaba un fracaso.
- **40 conocimientos reales** en memoria semántica (`MEMORIA/cargar_conocimiento_real.py`):
  láser, precios escolares, costeo, insumos, venta, negocio, método de trabajo,
  arquitectura, decisiones, infraestructura. Se consultan hablando normal.
- **Motor de red** ahora escanea TODA la red (cruza ping con tabla ARP), no solo Cast.
- **112 pruebas** de regresión (eran 87 al empezar el día).

### Medido, y por eso NO se hizo
- **Invertir el orden candados/enrutador**: los candados aciertan **22/23 (95%)** con
  **CERO** respuestas equivocadas. El cambio arriesgaba lo único que funciona. No se tocó.
- **Ollama en otra máquina**: cerrado. Gateway y Chromebook tienen 2 GB, Gemini sin
  cuota, y **Groq NUNCA ha fallado** (cero registros en logs).
- **Mover AURORA de máquina**: no. Consume **26 MB**; lo que satura son los
  navegadores (2 GB). Y Corel solo se controla desde donde está instalado.

### Pendiente de la palabra de Anuar
- **Enviar la campaña escolar** a las 22 clientas (`MARKETING/campana_regreso_clases.py --enviar`)
- Comprar $610 (100 hojas adhesivas + 2 m de vinil)
- Probar el cuadro de 10×10 con la maquila (el corte Cameo no cuadra)

---

## 📅 SESIÓN 2026-08-05 — capacidades que estaban muertas

### Se conectaron al chat capacidades que existían y NADIE podía llamar
El barrido del 2026-08-04 las encontró: código funcionando, sin puerta.

1. **Capturar clientes** (`oracle_leads`) — la que más dinero mueve y era
   inalcanzable. Un cliente que llamaba se anotaba en papel o se perdía.
   `apunta a Juan Perez 3312345678 interesado en faros` → lo guarda con folio,
   saca el teléfono del texto y detecta que es ATF. Sin nombre NO guarda.
2. **Cerrar citas** (`agenda`) — `actualizar_estado` no tenía ruta, así que las
   citas quedaban abiertas para siempre y la agenda dejaba de servir.
   `marca la cita 3 como hecha` · `cancela la cita 5`. Sin número PREGUNTA cuál.
3. **Directorio de proveedores** (`proveedores`) — no existía. Va ANTES de la
   búsqueda web: si el dato está en casa, no se va a internet.
   `quien me vende vinil` → Lideart, $180 el metro, con la fecha del dato.

### Bugs de raíz
- **"qué recuerdas de cotizar" devolvía una cotización de faros.** El candado
  vio la palabra "cotizar" dentro de la pregunta. Pasaba igual con video, corel
  y proveedores. Arreglado como **guard global** en el pipeline (`_solo_memoria`),
  no parche por candado — eso habría dejado abiertos los que nadie probó.
- **Los scripts nuevos secuestraban `sys.stdout` al importarse**, rompiéndole la
  salida a AURORA. Los 9 corregidos con `_consola_utf8()`.

### Herramientas nuevas (fuera del chat)
- `TALLER/indexar_dxf.py` — mide METROS DE CORTE reales con ezdxf y calcula
  precio con $8/min y 25 mm/s. `--buscar casa`
- `TALLER/consolidar_dxf.py` — junta los 665 DXF del disco y las USB, sin
  duplicados (hash del contenido, no nombre)
- `SISTEMA/indexar_programas.py` — 172 instalados, 68 instaladores, 8 portables.
  Solo lee, no copia
- `SISTEMA/apartar_duplicados.py` — los aparta para revisar, con `--deshacer`
- `TALLER/proveedores.py` — el directorio

### La lección que costó $250
Se vendió una casa de muñecas en $280 costando ~$200, porque no había DXF a la
mano para medir los metros. **No se cotiza por tamaño, se cotiza por metros de
corte.** Regla de bolsillo: metros × $50, mínimo $450 para armables.

### Números
53 conocimientos en 13 temas · 24 candados · 558 herramientas · **163 pruebas**
