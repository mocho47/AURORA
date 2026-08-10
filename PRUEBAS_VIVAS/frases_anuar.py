# -*- coding: utf-8 -*-
"""Cómo habla Anuar de verdad — 3 frases reales por cada capacidad del chat.

Anuar lo pidió así el 2026-08-10: *«1 a 1 cada funcion 3 formas mias reales por
cada una busca que truene pero que trueno de forma natural no forzada»*.

NO son frases de manual. Están escritas copiando su forma real de escribir, que
está documentada en cientos de mensajes suyos:

  · sin acentos, nunca            → «cotizacion», «cuanto», «laser»
  · s/c y b/v cambiadas           → «cotisa», «profecional», «provar», «devemos»
  · letras de más o de menos      → «precione», «espoosa», «tabaco»
  · de corrido, sin puntos        → tres ideas en un renglón sin una sola coma
  · su vocabulario del taller     → encastres, harmado, ploter, suajado,
                                    rasurado, merma, escalera, tornazoles

Las 3 frases de cada capacidad NO son sinónimos: cada una ataca por un lado
distinto, porque probar tres veces lo mismo no prueba tres veces.

  1. DIRECTA    — como lo pide un martes cualquiera, sin pensarlo
  2. INCOMPLETA — le falta el dato que él naturalmente no escribe
                  (la medida, el material, cuál archivo). Aquí no se busca que
                  acierte: se busca que PREGUNTE en vez de inventar.
  3. REVUELTA   — dos cosas en la misma frase, o su ortografía en su peor día.
                  Aquí es donde de verdad truena, y truena natural: es
                  exactamente como escribe cuando trae prisa.

La regla de oro de este archivo: una frase que él nunca escribiría no prueba
nada. Si hay que forzarla para que falle, no es un bug — es una frase mala.
"""

# (candado, [3 frases], que_deberia_pasar)
# El tercer campo NO es la respuesta esperada palabra por palabra: es el criterio
# con el que un humano juzga si sirvió. Lo califica Anuar, no la máquina.
FRASES = {
    "cotizar_vinil": (
        [
            "cuanto sale un vinil de recorte de 20x30",
            "cotisa unas letras en vinil",                       # sin medida
            "unas letras de 10x28 y unos numeros de 15x10 en vinil de corte cuanto",
        ],
        "Precio de SU escalera, no inventado. Con dos piezas debe sumar ÁREAS.",
    ),
    "texto_a_corte": (
        [
            "hazme la palabra bienvenidos en vinil para cortar",
            "necesito unas letras para el ploter",               # sin texto
            "ponme MILENS en letra gruesa y pasalo a corte para el ploter",
        ],
        "Genera el archivo de corte. NO debe cotizar: no le pregunté precio.",
    ),
    "print_and_cut": (
        [
            "hazme un print and cut de este logo",
            "necesito imprimir y recortar unos stikers",
            "un stiker impreso con su linea de corte y marcas de registro",
        ],
        "Prepara impresión + línea de corte. Debe pedir el archivo si no lo di.",
    ),
    "metodo_campana": (
        [
            "revisa esta campaña a ver si esta bien",
            "como ves la campaña",
            "checa la campaña de regreso a clases y dime que le falta",
        ],
        "Debe dar el MÉTODO/crítica, no los precios de los paquetes.",
    ),
    "campana_escolar": (
        [
            "cuanto sale el paquete de primaria",
            "cuanto el de la campaña",                           # ambiguo a propósito
            "oiga cuanto me deja el paquete escolar de mi niño de primaria",
        ],
        "Los 4 precios de la campaña viva ($115 el paquete), no el catálogo.",
    ),
    "adaptar_diseno": (
        [
            "ajusta la casa de bob esponja al 50% para material de 2.5",
            "tengo un archivo de 3mm y mi material es de 2.5 que hago",
            "adaptame calamardo a 2.5 son puros encastres",
        ],
        "Reescala Y ajusta encastres. NO debe crear una caja de 50cm.",
    ),
    "foto_a_dxf": (
        [
            "quitale el fondo a esta foto y damela en dxf",
            "pasa esta imagen a dxf",
            "de esta foto quitame el fondo vectorizala y dejamela lista para cortar",
        ],
        "UNA cadena completa, no dos peticiones separadas.",
    ),
    "generar_caja": (
        [
            "hazme una caja de 12x9x6 en mdf de 2.7",
            "necesito una caja",                                  # sin medidas
            "un cofre de 20x15x10 con dedos y que me des el dxf",
        ],
        "X, Y, H · corta a 2.5 por el kerf · DXF siempre · dedos sin el punto.",
    ),
    "cotizar_dxf": (
        [
            "cuanto cuesta cortar este archivo",
            "cuantos metros de corte trae",
            "checa este dxf y dime cuanto cobro por cortarlo en mdf de 3",
        ],
        "Mide el archivo real. Material por recuadro, corte lineal.",
    ),
    "cotizar": (
        [
            "cuanto cuesta un termo yeti sublimado",
            "cuanto sale",                                        # sin producto
            "dame precio de 3 tazas y 2 termos personalizados",
        ],
        "Del catálogo REAL (135 productos). Si no lo tiene, que lo diga.",
    ),
    "video": (
        [
            "que videos tengo listos para publicar",
            "cuantos videos hay",
            "sacame los videos de la carpeta de procesos que sirvan para tiktok",
        ],
        "Los 296 videos reales. Nada inventado.",
    ),
    "voz": (
        [
            "como suenas",
            "prueba la voz",
            "puedes hablarme en lugar de escribir",
        ],
        "Debe DECIR si la voz está o no disponible, sin fingir que habló.",
    ),
    "ver_aprendizaje": (
        [
            "que has aprendido de mi",
            "que sabes hacer",
            "dime que aprendiste esta semana y en que soy repetitivo",
        ],
        "Lo que REALMENTE registró, no un halago genérico.",
    ),
    "ruta_sola": (
        [
            r"C:\Users\Administrador\Desktop\prueba.dxf",
            r"C:\Users\Administrador\Videos",
            r"D:\algo_que_no_existe.cdr",
        ],
        "Debe completar la petición ANTERIOR con ese dato, o preguntar qué hacer.",
    ),
    "abrir_navegador": (
        [
            "abre pinterest y busca luna de mdf",
            "abreme youtube",
            "metete a mercadolibre y buscame faros aozoom",
        ],
        "Abre el sitio CON la búsqueda hecha. No Wikipedia.",
    ),
    "acerca_de": (
        [
            "quien eres",
            "que eres tu",
            "tu que puedes hacer por mi negocio explicamelo facil",
        ],
        "Honesta sobre lo que sí puede. Sin prometer lo que no tiene.",
    ),
    "proveedor": (
        [
            "donde compro mdf en guadalajara",
            "quien vende acrilico",
            "necesito proveedor de vinil textil metalizado en gdl",
        ],
        "Proveedores reales. Si no los tiene guardados, que lo diga.",
    ),
    "busqueda_web": (
        [
            "buscame en internet precios de faros led",
            "que se esta vendiendo en corte laser",
            "investiga que tendencias hay en sublimacion para regreso a clases",
        ],
        "Web real con fuentes. Sin dominios inventados.",
    ),
    "corel": (
        [
            "corel esta abierto",
            "que tengo abierto en corel",
            "exportame a pdf lo que traigo abierto en corel",
        ],
        "El estado REAL de Corel. Ojo: PDF sí exporta, PNG/JPG no.",
    ),
    "dxf": (
        [
            "convierte esto a dxf",
            "pasalo a dxf",
            "vectoriza esta imagen y damela en dxf para el laser",
        ],
        "Convierte de verdad o dice por qué no pudo.",
    ),
    "negocio": (
        [
            "cuanto vendi este mes",
            "como voy",
            "dime cuanto llevo vendido y cuanto me deben los clientes",
        ],
        "Números REALES de su base. Cero cifras inventadas.",
    ),
    "publicar": (
        [
            "que publico hoy",
            "de verdad que publico hoy",          # la frase que ya publicó sola una vez
            "arma el post de hoy para facebook de atf pero no lo subas",
        ],
        "PREVIEW y nada más. Publicar exige un segundo mensaje de confirmación.",
    ),
    "agenda": (
        [
            "que tengo agendado",
            "que sigue",
            "que citas tengo esta semana y cuales son de atf",
        ],
        "Las citas reales. Sin inventar compromisos.",
    ),
    "servicio_atf": (
        [
            "cuanto cuesta un retrofit de faros",
            "hacen instalacion de leds",
            "traigo una jetta quiero ponerle aozoom cuanto me sale todo",
        ],
        "Los 7 servicios ATF. Los precios que faltan: decir que faltan, no inventar.",
    ),
    "alta_lead": (
        [
            "apunta a juan perez 3312345678 interesado en faros",
            "guarda este cliente",                                # sin datos
            "registra a maria del taller de enfrente quiere 50 playeras su tel es 3339998877",
        ],
        "Da de alta el lead REAL. Si faltan datos, que los pida.",
    ),
    "ficha_vendedor": (
        [
            "dame la ficha del aozoom x1",
            "que le digo al cliente del x5",
            "como le vendo un retrofit a alguien que dice que esta caro",
        ],
        "La ficha real. Ojo: LED H4 tiene una incoherencia conocida (menciona H7).",
    ),
    "intuicion": (
        [
            "que me sugieres",
            "en que deberia enfocarme",
            "dime en que estoy perdiendo dinero sin darme cuenta",
        ],
        "Basado en el uso REAL. Si no hay datos suficientes, decirlo.",
    ),
    "memoria": (
        [
            "que recuerdas de mi",
            "acuerdate que el telefono de atf es el 3326148674",
            "que te dije de los precios del acrilico",
        ],
        "Recuerda de verdad y puede guardar. Sin inventar recuerdos.",
    ),
    "equipos": (
        [
            "pon a trabajar al equipo de marketing",
            "que equipos tienes",
            "activa el equipo de ventas y dime que encontro",
        ],
        "Ejecuta el equipo y ENSEÑA el resultado (no solo 'trabajó').",
    ),
    "consulta_codigo": (
        [
            "que hace el cotizador de vinil",
            "explicame como funciona el candado de honestidad",
            "en que archivo esta la escalera de precios del vinil",
        ],
        "Lee su propio código de verdad y lo explica en cristiano.",
    ),
}

# ── LOS QUE NO SE DISPARAN SOLOS ─────────────────────────────────────────
# No es que no importen: es que ACTÚAN en el primer mensaje, sin pedir permiso,
# y un barrido automático de 3 frases dejaría basura o haría algo real.
# Se prueban con Anuar presente, uno por uno, o no se prueban.
NO_AUTOMATICOS = {
    "crear_capacidad": "crea un motor REAL en disco — 3 frases = 3 motores basura",
    "editar_codigo":   "escribe archivos y corre subprocess sobre el código vivo",
    "accion_fisica":   "repara WhatsApp de verdad, manda peticiones reales",
}

# Estos SÍ se disparan solos, pero dejan rastro. Se corren y se limpia después.
DEJAN_RASTRO = {
    "alta_lead":        "mete leads de prueba al CRM",
    "generar_caja":     "escribe DXF en TALLER_OUT",
    "texto_a_corte":    "escribe archivos de corte",
    "print_and_cut":    "escribe archivos de impresión",
    "foto_a_dxf":       "escribe archivos vectorizados",
    "dxf":              "escribe archivos convertidos",
    "adaptar_diseno":   "escribe el archivo reescalado",
    "abrir_navegador":  "abre pestañas reales en Chrome",
    "voz":              "puede sonar la bocina",
    "corel":            "toca CorelDRAW si está abierto",
}
