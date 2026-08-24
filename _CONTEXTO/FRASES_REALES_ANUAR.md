# Frases reales tuyas — registro completo, nada inventado

Escrito el 2026-08-23. Esto NO es la lista de "cómo pedir las cosas" que armé
antes (esa media-lista quedó interrumpida). Esto es lo que pediste ahora:
**todas las frases tuyas reales de las que tengo registro** — las que se
usaron para probar AURORA (174 frases, dos rondas, sacadas literal de los
archivos de prueba) y **todas las que de verdad dispararon un bug** de
razonamiento o comprensión, con fecha, con qué pasó, y si ya está corregido
o sigue abierto.

Fuentes reales (ninguna frase de aquí abajo se inventó):
- `PRUEBAS_VIVAS/frases_anuar.py` (ronda 1, 2026-08-10)
- `PRUEBAS_VIVAS/frases_anuar_ronda2.py` (ronda 2, 2026-08-10, frases nuevas)
- `tests/test_regresion_bugs_reales.py` (~30 bugs reales documentados con fecha)
- Esta sesión de hoy, 2026-08-23 (bugs vividos en vivo, contigo)

---

## PARTE 1 — Bugs reales que SÍ pasaron (lo que pediste primero)

### De hoy, 2026-08-23

| Frase real | Qué pasó | Estado |
|---|---|---|
| `cotiza "...\mibautizo.dxf" en material 2.5 + vinil dorado + instalacion` | Cobró $1,369.60 usando la escalera de catálogo de vinil (para piezas de 20-30cm) en vez de medir el .dxf real de 109×85cm | **Corregido y verificado por ti en vivo** |
| `vinil de recorte dorado` (búsqueda en catálogo) | No encontraba el color porque el nombre real es "Vinil de recorte metálico dorado" y buscaba la frase completa como substring exacto | **Corregido** |
| `9325.7 cm²` (como se mostraba el área) | Se leía a simple vista como si fueran 9 m², cuando son 0.93 m² | **Corregido**: ahora muestra cm² y m² juntos |
| Los 3 LLM caídos a la vez (Groq/Gemini/local) | Groq daba 404 en TODAS las llamadas — no era falta de cuota, el modelo `llama-3.1-8b-instant` ya no existe en el catálogo de Groq, y estaba escrito a mano en **29 archivos** | **Corregido de raíz**: se reemplazó en los 29, no con una tabla-parche |
| `"vonolmetalico"` (typo fuerte de "vinil metálico") | No se reconoció como vinil | **Sigue abierto** — falta tolerancia a errores de dedo por palabra clave, no por lista de erratas |
| `pasar a blanco y negro` | Cayó al LLM genérico en vez de la herramienta real de B&N | **Sigue abierto**, no se investigó a fondo hoy |
| `quita el fondo a [ruta]` / `quita el fondo de la imagen [ruta]` | "No tengo esa herramienta", aunque la función real existe y AURORA la acababa de ofrecer | **Sigue abierto** en el chat — pero **ya existe mecánico**: botón "✂️ Quitar fondo (IA)" en el panel, Editor y Diseño, sin escribir nada |
| Ruta pegada con comillas (`"C:\Users\...\archivo.dxf"`) en el formulario de Cotizar del panel | "No se pudo medir el archivo" — el chat sí quitaba las comillas que Windows agrega al copiar una ruta, el formulario del panel no | **Corregido de raíz**: se quitan las comillas donde se abre el archivo, sirve para cualquiera que llame a esa función |
| Dos sistemas de lenguaje (`consciencia.py` + `lengua_anuar.py`) | El mismo bug había que corregirlo dos veces, una por archivo | **Corregido de raíz**: se fusionaron en un solo archivo, verificado con 40 casos reales antes de conectarlo |

### Históricos (de `tests/test_regresion_bugs_reales.py`, todos ya corregidos y con prueba de regresión)

| Fecha | Frase o caso real | Qué pasó |
|---|---|---|
| — | (mandar un archivo para reparación de código) | `auto_reparacion` podía borrar el 96% de `consciencia.py`: mandaba 6,000 caracteres al modelo pero reemplazaba el archivo completo |
| — | `cotizar 50 tazas` | Usaba el catálogo de precios de ATF (faros) en vez de Milens |
| — | `papá ya sali` (de su hija) | Se registraba como LEAD de ventas en vez de reconocerse como familia |
| — | (cualquier ruta con espacios, ej. `Animal - Perro - Pitbull (Cabeza).pdf`) | No se reconocía la ruta por el patrón de regex |
| — | (crear un lead nuevo) | El pronóstico de ventas siempre daba $0 — nunca se guardaba el valor estimado |
| — | (generar una caja) | Decía medidas engañosas ("80x50x40cm... mm") y reportaba OK aunque el DXF no se generara |
| — | (sin internet) | La capacidad offline pedía un modelo que no estaba instalado |
| — | (buscar un archivo que no existe) | El chat se trababa más de 2 minutos |
| — | `describete` / `que puedes hacer` | AURORA inventaba capacidades que no tenía |
| — | (pedir vectorizar en Corel) | `motor_analisis` decía "CorelDRAW: PDF cargado... Vectorización finalizada" sin haber hecho nada |
| 29-30 jul | 7 casos reales | Cuando la frase no calzaba con ningún candado, caía a un modelo sin acceso al sistema que igual respondía como si hubiera actuado |
| — | (pedir una búsqueda web) | No se activaba con lenguaje natural |
| — | `usa coreldraw para vectorizar el archivo que tengo abierto` | El enrutador inventó la intención "preparar_para_lona" — nadie mencionó lonas |
| — | (mensajes con formatos de archivo mencionados) | El validador marcaba "PDF/CDR" como comando inventado — avisos falsos |
| — | `abre esta imagen en corel` + (mensaje siguiente solo con la ruta) | Caía a `motor_analisis`, que decía "no puedo abrir archivos en la PC" — negación falsa |
| — | (candado `ruta_sola`) | Recibía `session_id` vacío, nunca completaba la petición anterior |
| 27 jul | Anuar y Rocío usando el panel a la vez | `UNIQUE constraint failed` y `database is locked` |
| 2026-08-02 | (idea de Anuar) *"también podría ser que aprendiera del usuario cómo es que se expresa"* | Nació de aquí el trabajo de "cómo pide", que hoy se fusionó en un solo archivo |
| 2026-08-03 | `extrae el mapa de bits` (después de importar a Corel) | Faltaba el verbo "extrae" en la lista — mintió que lo había hecho |
| 2026-08-03 | `abre "...\Bart_simpson\Bart_simpson" y convierte a DXF` | Dijo "✅ Abierto real" de un archivo que nunca se abrió |
| 2026-08-04 | `busca en mercado libre el mejor precio de 100 hojas de papel adhesivo para impresora laser` | El cotizador cotizó 100 PLAYERAS — confundió "buscar precio afuera" con "vender" |
| 2026-08-04 | *"no sé cómo pedirle a AURORA sin que lance algo diferente"* | Dicho tuyo directo, origen del trabajo de lenguaje natural |
| 2026-08-04 | (preguntas normales sobre conocimiento cargado) | 40 conocimientos entraban bien pero no se alcanzaban con las preguntas reales |
| 2026-08-04 | 6 búsquedas seguidas reformulando el precio de papel adhesivo | Ninguna dio un enlace útil, por 3 causas juntas |
| 2026-08-04 | (llamada de un cliente nuevo) | `oracle_core:crear_lead` existía pero no tenía ninguna puerta desde el chat — leads se perdían |
| 2026-08-05 | `qué recuerdas de cotizar` | Devolvió una cotización de faros — el candado vio la palabra "cotizar" dentro de la pregunta |
| 2026-08-05 | (actualizar el estado de una cita) | `agenda:actualizar_estado` existía pero sin forma de llamarla — citas quedaban abiertas para siempre |
| 2026-08-05 | `abre pinterest y busca luna de mdf` | No abrió Pinterest — hizo una búsqueda web genérica (Wikipedia, MercadoLibre, una página turca) |
| 2026-08-05 | *"que TÚ la enseñes a usar boxes.py, no que ella aprenda con el uso"* | Dicho tuyo directo sobre cómo debía aprenderse el generador de cajas |
| 2026-08-05 | `busca diseños en pinterest` | Devolvió una lista de texto en vez de imágenes — el sitio solo se abría si el verbo "abre" iba primero |
| 2026-08-05 | *"¿y funciona para cualquier sitio?"* / `en ameede busca la torre eiffel en dxf` | No — solo con los sitios de una lista fija; ese caso se lo llevó el conversor de DXF |
| 2026-08-05 | (revisar historial de navegación) | Salieron 8 sitios reales de diseño/láser con sus visitas (3axis.co, dxfdownloads.com, etc.) |
| 2026-08-05 | `quita el fondo a esta imagen "C:\...\a1e3.jpg"` (dos mensajes seguidos) | Perdía el archivo entre mensajes, no encadenaba la petición |
| 2026-08-21 | `corel vectoriza C:\...\pieza.png` / `vectoriza C:\...\pieza.jpg` | `lengua_anuar` se lo llevaba a `foto_a_dxf` solo porque la extensión ".png"/".jpg" calzaba con la palabra suelta del patrón |
| 2026-08-21 | `abre esta imagen en corel` (y variantes) | `lengua_anuar` secuestraba CUALQUIER mensaje que empezara con "abre" hacia abrir el navegador |
| 2026-08-21 | `ábrelo` / `ábreme` + ruta | "abrir_archivo" perdía contra "leer_archivo" porque solo reconocía el infinitivo exacto "abrir" |

---

## PARTE 2 — Las 174 frases reales usadas para probar AURORA

Sacadas literal de `PRUEBAS_VIVAS/frases_anuar.py` (ronda 1) y
`frases_anuar_ronda2.py` (ronda 2, ángulos distintos a propósito — pregunta en
vez de orden, sin medida, con tu forma de escribir de prisa). 3 frases por
función, dos veces, sin repetirse entre rondas.

### Cotizar vinil (plotter/recorte/textil)
- "cuanto sale un vinil de recorte de 20x30"
- "cotisa unas letras en vinil"
- "unas letras de 10x28 y unos numeros de 15x10 en vinil de corte cuanto"
- "a como me sale el metro de vinil textil ya puesto"
- "oye y si son 5 calcas de 12x12 cuanto queda cada una"
- "en cuanto sale rotular una puerta de 90 x 45 en recorte"

### Generar letras/texto para corte (sin cotizar)
- "hazme la palabra bienvenidos en vinil para cortar"
- "necesito unas letras para el ploter"
- "ponme MILENS en letra gruesa y pasalo a corte para el ploter"
- "sacame el nombre SOFIA en tipo script para recortar"
- "hazme los numeros del 1 al 10 para el plotter"
- "quiero la frase gracias por su compra lista para el ploter"

### Print and cut
- "hazme un print and cut de este logo"
- "necesito imprimir y recortar unos stikers"
- "un stiker impreso con su linea de corte y marcas de registro"
- "esas calcomanias van impresas y luego recortadas verdad"
- "arma las marcas de registro para recortar lo impreso"
- "necesito calcas full color con su contorno de corte"

### Método/crítica de campaña (no precios)
- "revisa esta campaña a ver si esta bien"
- "como ves la campaña"
- "checa la campaña de regreso a clases y dime que le falta"
- "que le falta a la campaña para que jale"
- "que opinas de la campaña asi como esta"
- "revisame la campaña antes de mandarla"

### Precio de la campaña escolar viva
- "cuanto sale el paquete de primaria"
- "cuanto el de la campaña"
- "oiga cuanto me deja el paquete escolar de mi niño de primaria"
- "cuanto el paquete escolar"
- "el de secundaria en cuanto queda"
- "una clienta pregunta cuanto el de preescolar"

### Adaptar diseño existente a otro material
- "ajusta la casa de bob esponja al 50% para material de 2.5"
- "tengo un archivo de 3mm y mi material es de 2.5 que hago"
- "adaptame calamardo a 2.5 son puros encastres"
- "el diseño viene para 3mm y mi material es de 2.5"
- "reescala calamardo son puros encastres"
- "adapta la plantilla a mi mdf que es mas delgado"

### Quitar fondo + vectorizar + preparar para láser
- "quitale el fondo a esta foto y damela en dxf"
- "pasa esta imagen a dxf"
- "de esta foto quitame el fondo vectorizala y dejamela lista para cortar"
- "quitale el fondo a este logo y vectorizalo para cortar"
- "esta imagen la quiero limpia y en vector para el laser"
- "borra el fondo de la foto y dejala lista para corte"

### Generar caja
- "hazme una caja de 12x9x6 en mdf de 2.7"
- "necesito una caja"
- "un cofre de 20x15x10 con dedos y que me des el dxf"
- "armame un estuche de 15x10x8"
- "necesito un organizador de 30x20x12 en mdf"
- "una cajita de 8x8x5 para una taza"

### Cotizar corte de un archivo DXF real
- "cuanto cuesta cortar este archivo"
- "cuantos metros de corte trae"
- "checa este dxf y dime cuanto cobro por cortarlo en mdf de 3"
- "cuantos metros de corte trae este archivo"
- "mide el dxf y dime en cuanto lo dejo"
- "que me cobrarias por cortar este diseño en mdf"

### Cotizar del catálogo (tazas, termos, playeras...)
- "cuanto cuesta un termo yeti sublimado"
- "cuanto sale"
- "dame precio de 3 tazas y 2 termos personalizados"
- "en cuanto dejo una gorra bordada digo sublimada"
- "precio de una agenda de vinipiel grabada"
- "cuanto por 10 vasos cafeteros personalizados"

### Videos
- "que videos tengo listos para publicar"
- "cuantos videos hay"
- "sacame los videos de la carpeta de procesos que sirvan para tiktok"
- "que material de video tengo guardado"
- "hay clips que sirvan para un reel"
- "de los videos cuales estan sin publicar"

### Voz
- "como suenas"
- "prueba la voz"
- "puedes hablarme en lugar de escribir"
- "puedes contestarme hablando"
- "activa que me escuches"
- "quiero platicar contigo sin teclear"

### Qué ha aprendido de ti
- "que has aprendido de mi"
- "que sabes hacer"
- "dime que aprendiste esta semana y en que soy repetitivo"
- "que has ido aprendiendo de como trabajo"
- "en que soy repetitivo segun tu"
- "que patrones me has visto"

### Ruta sola (completar la petición anterior)
- `C:\Users\Administrador\Desktop\prueba.dxf`
- `C:\Users\Administrador\Videos`
- `D:\algo_que_no_existe.cdr`
- `C:\Users\Administrador\Downloads\logo.png`
- `C:\AURORA.worktrees\TALLER_OUT`
- `E:\usb\diseno.svg`

### Abrir un sitio y buscar
- "abre pinterest y busca luna de mdf"
- "abreme youtube"
- "metete a mercadolibre y buscame faros aozoom"
- "metete a facebook"
- "entra a 3axis y busca cajas"
- "abre google y busca precios de acrilico"

### Qué es AURORA / para qué sirve
- "quien eres"
- "que eres tu"
- "tu que puedes hacer por mi negocio explicamelo facil"
- "explicame que eres en pocas palabras"
- "para que me sirves tu"
- "que ganamos con que estes aqui"

### Proveedores
- "donde compro mdf en guadalajara"
- "quien vende acrilico"
- "necesito proveedor de vinil textil metalizado en gdl"
- "con quien surto acrilico"
- "quien me vende mdf barato"
- "mis proveedores de sublimacion cuales son"

### Búsqueda web
- "buscame en internet precios de faros led"
- "que se esta vendiendo en corte laser"
- "investiga que tendencias hay en sublimacion para regreso a clases"
- "investiga que se esta usando en corte laser este año"
- "googlea cuanto cobran por retrofit en guadalajara"
- "busca en internet ideas de regalos personalizados"

### Corel
- "corel esta abierto"
- "que tengo abierto en corel"
- "exportame a pdf lo que traigo abierto en corel"
- "que archivo traigo en corel"
- "corel lo tengo prendido"
- "pasa a pdf el documento de corel"

### Convertir a DXF
- "convierte esto a dxf"
- "pasalo a dxf"
- "vectoriza esta imagen y damela en dxf para el laser"
- "convierteme este svg a dxf"
- "necesito el archivo en dxf"
- "pasa el diseño a formato de corte"

### Cómo va el negocio
- "cuanto vendi este mes"
- "como voy"
- "dime cuanto llevo vendido y cuanto me deben los clientes"
- "como vamos este mes"
- "cuanto llevo vendido"
- "que tal va la venta"

### Publicar (siempre con preview primero)
- "que publico hoy"
- "de verdad que publico hoy"
- "arma el post de hoy para facebook de atf pero no lo subas"
- "que subo hoy a las redes"
- "arma el post pero no lo mandes"
- "que toca publicar de milens"

### Agenda
- "que tengo agendado"
- "que sigue"
- "que citas tengo esta semana y cuales son de atf"
- "que me toca hoy"
- "con quien quede esta semana"
- "para cuando quedo la entrega"

### Servicios ATF (faros)
- "cuanto cuesta un retrofit de faros"
- "hacen instalacion de leds"
- "traigo una jetta quiero ponerle aozoom cuanto me sale todo"
- "cuanto por ponerle biled a una hilux"
- "traigo un civic quiero mejorar los faros"
- "hacen proyectores de faro"

### Dar de alta un lead/cliente
- "apunta a juan perez 3312345678 interesado en faros"
- "guarda este cliente"
- "registra a maria del taller de enfrente quiere 50 playeras su tel es 3339998877"
- "apunta a roberto 3311223344 quiere unas playeras"
- "da de alta a la señora del kinder"
- "metelo al crm es cliente nuevo"

### Ficha de vendedor / argumentos de venta
- "dame la ficha del aozoom x1"
- "que le digo al cliente del x5"
- "como le vendo un retrofit a alguien que dice que esta caro"
- "que le contesto al cliente que dice que esta caro"
- "como cierro una venta de tiras secuenciales"
- "dame los argumentos de venta del led h4"

### Intuición / consejo de negocio
- "que me sugieres"
- "en que deberia enfocarme"
- "dime en que estoy perdiendo dinero sin darme cuenta"
- "que me conviene hacer ahorita"
- "donde estoy dejando dinero en la mesa"
- "que harias tu en mi lugar"

### Memoria (recordar/guardar algo)
- "que recuerdas de mi"
- "acuerdate que el telefono de atf es el 3326148674"
- "que te dije de los precios del acrilico"
- "apuntate que el acrilico de 2mm quedo en 1000"
- "que te dije del kerf del mdf"
- "no se te olvide que rocio usa la pc del local"

### Equipos de trabajo
- "pon a trabajar al equipo de marketing"
- "que equipos tienes"
- "activa el equipo de ventas y dime que encontro"
- "echame a andar el equipo de diseño"
- "cuales equipos tengo disponibles"
- "que puede hacer el equipo de publicacion"

### Preguntar cómo funciona el código por dentro
- "que hace el cotizador de vinil"
- "explicame como funciona el candado de honestidad"
- "en que archivo esta la escalera de precios del vinil"
- "como funciona la escalera de precios por dentro"
- "en que archivo guardas los precios del taller"
- "que hace el validador de honestidad"

---

## Lo que NO se prueba solo (por diseño, no por descuido)

Estos actúan de verdad desde el primer mensaje sin pedir permiso, así que
nunca se disparan en una prueba automática — se prueban contigo presente,
uno por uno:
- **crear_capacidad** — crea un motor real en disco
- **editar_codigo** — escribe archivos del núcleo y corre comandos
- **accion_fisica** — repara WhatsApp de verdad, manda peticiones reales

Estos sí se disparan solos pero dejan rastro real (se limpia después de
probar): alta_lead, generar_caja, texto_a_corte, print_and_cut, foto_a_dxf,
dxf, adaptar_diseno, abrir_navegador, voz, corel.
