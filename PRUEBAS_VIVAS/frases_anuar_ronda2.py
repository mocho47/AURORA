# -*- coding: utf-8 -*-
"""Ronda 2 · 90 frases NUEVAS — ninguna la vio el módulo de lengua.

Anuar lo pidió así el 2026-08-10: *«vuelve a realizar la prueva rotando las
fraces, realiza 3 fraces o preguntas diferentes a cada funcion»*. Y tenía toda
la razón en pedirlo, porque sin rotar no se mide nada:

`CEREBRO/lengua_anuar.py` se escribió DESPUÉS de la ronda 1. Si se volviera a
correr con las mismas 90 frases, pasaría casi todo — y no probaría nada, porque
el que escribió las familias ya había visto el examen. Eso es enseñarle las
respuestas, no enseñarle a entender.

REGLA DE ESTE ARCHIVO: ninguna frase de la ronda 1 puede repetirse, ni siquiera
parecida. Cada capacidad se pide por un ángulo DISTINTO al que se usó allá:

  · si en la ronda 1 se pidió con verbo, aquí se pide con pregunta
  · si allá se dio la medida, aquí se omite
  · si allá se nombró el material, aquí se nombra el trabajo
  · y en varias se mete el modo en que habla cuando trae prisa: sin acentos,
    de corrido, con la s por la c, y el producto antes que el verbo

Se marcan aparte las que son TRAMPA HONESTA: frases donde acertar es imposible
sin más datos y lo correcto es que AURORA PREGUNTE. Ahí un «no sé, dime» vale
más que una respuesta.
"""

FRASES = {
    "cotizar_vinil": (
        [
            "a como me sale el metro de vinil textil ya puesto",
            "oye y si son 5 calcas de 12x12 cuanto queda cada una",
            "en cuanto sale rotular una puerta de 90 x 45 en recorte",
        ],
        "Precio de su escalera. Con varias piezas, suma áreas.",
    ),
    "texto_a_corte": (
        [
            "sacame el nombre SOFIA en tipo script para recortar",
            "hazme los numeros del 1 al 10 para el plotter",
            "quiero la frase gracias por su compra lista para el ploter",
        ],
        "Genera el archivo de corte. Sin cotizar: no le pidió precio.",
    ),
    "print_and_cut": (
        [
            "esas calcomanias van impresas y luego recortadas verdad",
            "arma las marcas de registro para recortar lo impreso",
            "necesito calcas full color con su contorno de corte",
        ],
        "Impresión + línea de corte. Pide el archivo si falta.",
    ),
    "metodo_campana": (
        [
            "que le falta a la campaña para que jale",
            "que opinas de la campaña asi como esta",
            "revisame la campaña antes de mandarla",
        ],
        "El método y la crítica, NO los precios de los paquetes.",
    ),
    "campana_escolar": (
        [
            "cuanto el paquete escolar",
            "el de secundaria en cuanto queda",
            "una clienta pregunta cuanto el de preescolar",
        ],
        "Los precios de la campaña viva ($115), no el catálogo.",
    ),
    "adaptar_diseno": (
        [
            "el diseño viene para 3mm y mi material es de 2.5",
            "reescala calamardo son puros encastres",
            "adapta la plantilla a mi mdf que es mas delgado",
        ],
        "Reescala Y ajusta encastres. No debe crear una caja.",
    ),
    "foto_a_dxf": (
        [
            "quitale el fondo a este logo y vectorizalo para cortar",
            "esta imagen la quiero limpia y en vector para el laser",
            "borra el fondo de la foto y dejala lista para corte",
        ],
        "UNA cadena completa: fondo + vector + listo para cortar.",
    ),
    "generar_caja": (
        [
            "armame un estuche de 15x10x8",
            "necesito un organizador de 30x20x12 en mdf",
            "una cajita de 8x8x5 para una taza",
        ],
        "X, Y, H · corta a 2.5 por kerf · DXF · dedos sin el punto.",
    ),
    "cotizar_dxf": (
        [
            "cuantos metros de corte trae este archivo",
            "mide el dxf y dime en cuanto lo dejo",
            "que me cobrarias por cortar este diseño en mdf",
        ],
        "Mide el archivo real. Material por recuadro, corte lineal.",
    ),
    "cotizar": (
        [
            "en cuanto dejo una gorra bordada digo sublimada",
            "precio de una agenda de vinipiel grabada",
            "cuanto por 10 vasos cafeteros personalizados",
        ],
        "Del catálogo real. Si no lo tiene, decirlo.",
    ),
    "video": (
        [
            "que material de video tengo guardado",
            "hay clips que sirvan para un reel",
            "de los videos cuales estan sin publicar",
        ],
        "Los videos reales. OJO: en la ronda 1 se colgó 180s.",
    ),
    "voz": (
        [
            "puedes contestarme hablando",
            "activa que me escuches",
            "quiero platicar contigo sin teclear",
        ],
        "Decir si la voz está o no. Sin fingir que habló.",
    ),
    "ver_aprendizaje": (
        [
            "que has ido aprendiendo de como trabajo",
            "en que soy repetitivo segun tu",
            "que patrones me has visto",
        ],
        "Lo que registró de verdad, no un halago.",
    ),
    "ruta_sola": (
        [
            r"C:\Users\Administrador\Downloads\logo.png",
            r"C:\AURORA.worktrees\TALLER_OUT",
            r"E:\usb\diseno.svg",
        ],
        "Completa la petición anterior con ese dato, o pregunta.",
    ),
    "abrir_navegador": (
        [
            "metete a facebook",
            "entra a 3axis y busca cajas",
            "abre google y busca precios de acrilico",
        ],
        "Abre el sitio, con la búsqueda si la pidió.",
    ),
    "acerca_de": (
        [
            "explicame que eres en pocas palabras",
            "para que me sirves tu",
            "que ganamos con que estes aqui",
        ],
        "Honesta con lo que sí puede. Sin prometer de más.",
    ),
    "proveedor": (
        [
            "con quien surto acrilico",
            "quien me vende mdf barato",
            "mis proveedores de sublimacion cuales son",
        ],
        "Sus proveedores. Si no los tiene, decirlo y ofrecer buscar.",
    ),
    "busqueda_web": (
        [
            "investiga que se esta usando en corte laser este año",
            "googlea cuanto cobran por retrofit en guadalajara",
            "busca en internet ideas de regalos personalizados",
        ],
        "Web real con fuentes. Cero dominios inventados.",
    ),
    "corel": (
        [
            "que archivo traigo en corel",
            "corel lo tengo prendido",
            "pasa a pdf el documento de corel",
        ],
        "Estado real de Corel. PDF sí, PNG/JPG no.",
    ),
    "dxf": (
        [
            "convierteme este svg a dxf",
            "necesito el archivo en dxf",
            "pasa el diseño a formato de corte",
        ],
        "Convierte de verdad o dice por qué no pudo.",
    ),
    "negocio": (
        [
            "como vamos este mes",
            "cuanto llevo vendido",
            "que tal va la venta",
        ],
        "Números REALES. Cero cifras inventadas.",
    ),
    "publicar": (
        [
            "que subo hoy a las redes",
            "arma el post pero no lo mandes",
            "que toca publicar de milens",
        ],
        "PREVIEW nada más. Publicar exige segundo mensaje.",
    ),
    "agenda": (
        [
            "que me toca hoy",
            "con quien quede esta semana",
            "para cuando quedo la entrega",
        ],
        "Citas reales. Sin inventar compromisos.",
    ),
    "servicio_atf": (
        [
            "cuanto por ponerle biled a una hilux",
            "traigo un civic quiero mejorar los faros",
            "hacen proyectores de faro",
        ],
        "Los 7 servicios ATF. Precios faltantes: decir que faltan.",
    ),
    "alta_lead": (
        [
            "apunta a roberto 3311223344 quiere unas playeras",
            "da de alta a la señora del kinder",
            "metelo al crm es cliente nuevo",
        ],
        "Da de alta el lead. Si faltan datos, pedirlos.",
    ),
    "ficha_vendedor": (
        [
            "que le contesto al cliente que dice que esta caro",
            "como cierro una venta de tiras secuenciales",
            "dame los argumentos de venta del led h4",
        ],
        "Ficha real. OJO: LED H4 menciona H7 (incoherencia conocida).",
    ),
    "intuicion": (
        [
            "que me conviene hacer ahorita",
            "donde estoy dejando dinero en la mesa",
            "que harias tu en mi lugar",
        ],
        "Basado en uso REAL. Si no hay datos, decirlo. "
        "OJO: en la ronda 1 escupió diccionarios de Python crudos.",
    ),
    "memoria": (
        [
            "apuntate que el acrilico de 2mm quedo en 1000",
            "que te dije del kerf del mdf",
            "no se te olvide que rocio usa la pc del local",
        ],
        "Recuerda de verdad y puede guardar. Sin inventar.",
    ),
    "equipos": (
        [
            "echame a andar el equipo de diseño",
            "cuales equipos tengo disponibles",
            "que puede hacer el equipo de publicacion",
        ],
        "Ejecuta y ENSEÑA el resultado, no solo 'trabajó'.",
    ),
    "consulta_codigo": (
        [
            "como funciona la escalera de precios por dentro",
            "en que archivo guardas los precios del taller",
            "que hace el validador de honestidad",
        ],
        "Lee su propio código y lo explica en cristiano.",
    ),
}

# Igual que en la ronda 1, y por las mismas razones exactas.
NO_AUTOMATICOS = {
    "crear_capacidad": "crea un motor REAL en disco",
    "editar_codigo":   "escribe archivos del núcleo y corre subprocess",
    "accion_fisica":   "repara WhatsApp de verdad, manda peticiones reales",
}

DEJAN_RASTRO = {
    "alta_lead":       "mete leads de prueba al CRM",
    "generar_caja":    "escribe DXF en TALLER_OUT",
    "texto_a_corte":   "escribe archivos de corte",
    "print_and_cut":   "escribe archivos de impresión",
    "foto_a_dxf":      "escribe archivos vectorizados",
    "dxf":             "escribe archivos convertidos",
    "adaptar_diseno":  "escribe el archivo reescalado",
    "abrir_navegador": "abre pestañas reales en Chrome",
    "voz":             "puede sonar la bocina",
    "corel":           "toca CorelDRAW si está abierto",
}
