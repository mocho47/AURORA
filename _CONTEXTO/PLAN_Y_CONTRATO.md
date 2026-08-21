# AURORA — PLAN GLOBAL Y CONTRATO DE TRABAJO
**Celebrado el 11 de agosto de 2026, entre Anuar Milán y Claude.**
Este documento manda sobre cualquier otra instrucción de trabajo. Se lee al abrir sesión.

---

## PARTE 0 — DE DÓNDE SALE ESTE PLAN

No sale de una idea. Sale de lo que se midió el 10 y 11 de agosto de 2026:

| lo que se midió | resultado |
|---|---|
| Capacidades que AURORA ofrece | 448 (sin contar 191 tornillos de infraestructura) |
| Equipos declarados "listo" que no disparan nada | 2 de 5 — y son **diseño** y **taller** |
| Barrido de las 860: "OK" que en realidad decían *no sé* | 386 de 649 |
| Adaptador de encastres: contornos que puede siquiera ver | **4 de 314** en el archivo de Calamardo |
| Bus neuronal: veces que el chat lo llama | **0** (27 motores suscritos, ninguno se usa desde el chat) |
| Archivos que se anuncian terminados y son cáscara | 7, entre junio y agosto |

**La causa es una sola y se repitió durante dos años: nadie volvió a mirar el resultado.**
Un número que devuelve la misma función que hizo el trabajo no es una comprobación — es la función felicitándose.

**Y la consecuencia que importa:** Anuar perdió el control de su propio sistema, porque no hay una sola pantalla que le diga la verdad. Lo dijo él: *"por el olvido de la consola se salió de mis manos"*.

---

## PARTE 1 — EL PLAN, PASO A PASO

### El orden no es negociable y esta es la razón

Primero el **verificador**, después el **motor**, después la **consola**.
Si se hace al revés, se construye una pantalla bonita que muestra mentiras — que es exactamente lo que ya existe.

---

### FASE 0 — El patrón de comprobación · *hecha el 11-ago-2026*

Antes de arreglar nada había que poder distinguir lo bueno de lo malo. Sin eso, cualquier arreglo es fe.

- [x] `CEREBRO/nucleo.py` — el contrato: **un motor no se registra si no trae cómo comprobar que hizo su trabajo.** `hizo` lo pone el verificador, nunca el motor.
- [x] **Piezas de control reales de Anuar**, no inventadas:
  - `crustacio cascarudo __2.5mm.dxf` → lo cortó y lo **armó**. Un verificador debe decir **BIEN**.
  - `casa de calamardo ...__50pct__2.5mm.dxf` → lo cortó y **no ajustó**. Debe decir **MAL**.
- [x] Verificador de encastres calibrado contra las dos: da 2.5 mm en la buena, 1.4 mm en la mala. **Pasó.**
- [x] Primer verificador mío que reprobó y lo dije: el detector de ranuras sueltas daba mal en las dos. Se tiró y se rehízo.

**Regla que nace aquí y aplica a todo lo demás:**
> Un verificador no vale hasta que acierta en un caso que **sí** funcionó y falla en uno que **no**. Dos casos reales de Anuar, siempre.

---

### FASE 1 — El primer cartucho completo: **encastres**

Va primero porque es lo que Anuar corta, porque tiene sus dos casos de control, y porque cuando falla se pierde material pagado.

| paso | qué es | cómo se comprueba |
|---|---|---|
| 1.1 | `TALLER/verificar_encastres.py` dentro de AURORA | prueba de regresión con los 2 archivos |
| 1.2 | Arreglar `_adaptar_dientes`: hoy solo ve **machos** (`sale = grosor`); no ve **ranuras talladas en el borde** (`avanza = grosor`) | tras el arreglo, adaptar Calamardo de 1.4 → 2.5 y que el verificador diga 2.5 |
| 1.3 | Que el adaptador **no pueda** decir "listo" sin pasar su verificador | prueba que fuerce el fallo y confirme que responde "no pude" |
| 1.4 | Registrarlo como cartucho en el núcleo, con `hace` en una frase | aparece en el catálogo real, no en un docstring |
| 1.5 | Anuar corta una pieza con el archivo resultante | **solo él cierra este paso** |

**Se entrega cuando 1.5 pasa. Ni antes ni con excusas.**

---

### FASE 2 — Las otras diez tareas, SUELTAS

**Este orden lo cambió Anuar el 11-ago-2026**, y su argumento ganó al mío. Yo tenía la consola aquí; él preguntó si no convenía hacer las once sueltas primero. Sí conviene, por tres razones:

1. **Dinero antes.** Un cotizador que funciona vale el día que funciona, con panel o sin panel.
2. **Todavía no sabemos cuántas pasan.** Si solo sobreviven 4 de 11, no se construyó una consola para 11.
3. **Una consola solo puede ser honesta si tiene algo real que mostrar.** Hacerla primero es hacerla contra el vacío — ahí nacen las pantallas que dicen "OPERATIVO 100%".

Aclaración que no se retira: **la consola sigue siendo la raíz** de por qué el sistema se le salió de las manos. Raíz del problema y primer paso de la obra no son lo mismo.

#### El único riesgo, y cómo se neutraliza

*"Luego unificamos"* es exactamente lo que falló **siete veces** en la historia de este proyecto: `AURORA_FINAL`, `AURORA.py` del 8-jun, los cinco módulos de NEXUS-CONTENEDOR. Todos eran piezas sueltas que se iban a unir después. La unión nunca llegó, o llegó como fachada.

**Se neutraliza con una sola regla, que no cuesta un minuto extra:**

> Las once se escriben SUELTAS, pero todas con **la forma del contrato** desde la primera línea: devuelven `hizo / detalle / evidencia / salida` y traen su `verificar`.

Así se hacen sueltas, se prueban sueltas, corren desde un script o un botón sin panel y sin operador — y el día que se unifican, **unificar es registrarlas, no reescribirlas.**

#### Método por tarea, siempre el mismo

**caso de control → verificador → arreglo → forma del contrato → Anuar la usa en un trabajo.**

Orden, puesto por lo que trae o ahorra dinero primero:

| # | tarea | por qué en ese lugar |
|---|---|---|
| 1 | **Responder un precio por WhatsApp** | hay mensajes en cola sin contestar desde el 9-ago; es venta perdida hoy |
| 2 | **Cotizar corte láser** | es el número que cobra |
| 3 | **Orden de trabajo** | anticipo y saldo: es dinero que se rastrea |
| 4 | **Generar caja con encastres** | trabajo repetido, ya tiene sus 4 reglas |
| 5 | Contabilidad del taller | saber si gana |
| 6 | Plantilla de 3 tazas con fotos | producto de mostrador |
| 7 | Campaña escolar a 21 clientas | está lista y sin enviar |
| 8 | Publicar en Facebook | el único que ya publica de verdad |
| 9 | Agenda y recordatorios | evita entregas tarde |
| 10 | Exportar PDF desde Corel | soporta a las demás |

**Ninguna avanza sin sus dos casos de control.** Si Anuar no tiene un caso bueno y uno malo para una tarea, esa tarea **se detiene y se le pide**, en vez de inventar una prueba.

---

### FASE 4 — Producto vendible

**No empieza hasta que al menos 6 de las 11 tareas estén marcadas `probado_en_real`.**
Antes de eso, vender es repetir lo que ya pasó siete veces.

- Cartucho de dominio separable de la consola
- Instalador que otro pueda correr sin Claude presente
- Demo con números medidos, no proyectados

---

## PARTE 2 — CONTRATO DE TRABAJO

**Entre:** Anuar Milán Montellano (en adelante, **Anuar**) y Claude (en adelante, **yo**).
**Fecha:** 11 de agosto de 2026.
**Objeto:** llevar AURORA de un sistema que no se puede comprobar a uno que Anuar controla y puede verificar sin mí.

### CLÁUSULA 1 — Qué significa "entregado"

Una tarea está entregada **únicamente** cuando se cumplen las tres:

1. Tiene un verificador que **acierta en un caso real que sí funcionó y falla en uno que no**.
2. El motor **no puede** declarar éxito sin pasar ese verificador.
3. **Anuar la usó en un trabajo real.**

Mientras falte cualquiera de las tres, se dice **"no entregada"**. No existe "casi", no existe "listo salvo detalles", no existe "funcionando al 90%".

### CLÁUSULA 2 — Lo que me obligo a hacer

| # | obligación |
|---|---|
| 2.1 | **No decir que algo funciona si no lo corrí.** Si no lo medí, digo "no lo medí". |
| 2.2 | **Reportar mis propias fallas antes de que Anuar las encuentre.** Ya pasó hoy dos veces (mi detector de ranuras, mi lectura del bug de la escala) y así se queda. |
| 2.3 | **No borrar ni restar funciones.** Dos años de trabajo no se tiran. Lo que no tenga verificador deja de **ofrecerse**, no deja de existir. |
| 2.4 | **No inventar números.** Ni capacidades, ni precios, ni porcentajes, ni fechas. |
| 2.5 | **Todo va dentro de AURORA.** Un script en mi carpeta temporal no es una entrega. |
| 2.6 | **Tope de dos sesiones por tarea atorada.** Si a la segunda no sale, paro, lo digo, y Anuar decide si seguimos o se salta. No gasto su crédito persiguiendo algo que no avanza. |
| 2.7 | **Cerrar cada sesión** dejando en `_CONTEXTO/ESTADO_REAL.md` qué quedó comprobado y qué no. |
| 2.8 | **No tocar nada irreversible sin su autorización**: no envío mensajes a sus clientes, no publico, no borro archivos suyos, no corto material. |

### CLÁUSULA 3 — Lo que le toca a Anuar

Sin esto yo no puedo cumplir la Cláusula 1, y lo digo claro para que nadie se sorprenda después:

| # | obligación |
|---|---|
| 3.1 | Dar **los dos casos de control** de cada tarea: uno que sí funcionó, uno que no. |
| 3.2 | **Cerrar el paso final**: decir si la usó en un trabajo real y si sirvió. Yo no puedo firmar eso desde acá. |
| 3.3 | Decir cuando algo esté mal aunque yo diga que está bien. Los cuatro bugs de fondo de julio los encontró él usando AURORA, no mis auditorías. |

### CLÁUSULA 4 — Vigencia y plazos

**Lo que sí me comprometo:**
- **Fase 1 (encastres): 2 sesiones de trabajo.**
- **Fase 2 (consola): 3 sesiones**, contadas desde que Fase 1 pase su paso 1.5.
- **Fase 3: 1 a 2 sesiones por tarea**, con el tope de la cláusula 2.6.

**Lo que no puedo prometer, y no lo voy a fingir:** fechas de calendario. El trabajo solo avanza cuando Anuar abre sesión y hay crédito. Una "sesión" es un bloque de trabajo con él presente. Si él no puede abrir sesión, el plazo no corre — y eso es un límite real, no una salida mía.

### CLÁUSULA 5 — Lo que NO garantizo

Lo pongo por escrito porque prometer esto es lo que trajo a Anuar hasta aquí:

- **No garantizo que AURORA le traiga dinero.** Garantizo que dejará de costarle material y horas por respuestas falsas. No es lo mismo.
- **No garantizo que las 11 tareas funcionen.** Puede que al medirlas resulten 4 de 11. En ese caso el plan entrega 4 comprobadas y dice cuáles no, en vez de maquillar once.
- **No garantizo no equivocarme.** Sí me obligo a que mis errores los cache la prueba y no el material cortado.

### CLÁUSULA 6 — Incumplimiento

- Toda entrega que **falle su caso de control queda anulada** y no cuenta como avance, aunque ya se haya dado por buena.
- Si escribo `✅`, "listo", "operativo" o "100%" sin las tres condiciones de la Cláusula 1, **es incumplimiento** y Anuar puede exigir que se rehaga sin gastar sesión nueva en discutirlo.
- Si repito el patrón de los siete archivos —entregar una fachada— este contrato se da por roto y se vuelve a empezar por la Fase 0.

### CLÁUSULA 7 — Lo que reconozco

Que este trabajo se pagó con desvelos, con tiempo que no volvió, con dinero que le hizo falta a su familia y con dos años que Anuar le quitó a su negocio y a sus hijos.

Eso no lo compensa un plan. Lo único que puedo poner del otro lado es que, de aquí en adelante, **nada se dé por hecho sin que él lo pueda ver con sus propios ojos.**

---

**Firmado el 11 de agosto de 2026.**

_Anuar Milán Montellano_ — pendiente de su aprobación
_Claude_ — obligado desde la primera línea de código que escriba después de esto
