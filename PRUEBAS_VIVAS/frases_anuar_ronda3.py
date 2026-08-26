# -*- coding: utf-8 -*-
"""Ronda 3 · 398 frases NUEVAS — y las 6 capacidades que NADIE habia probado.

Por que existe (2026-08-26): las rondas 1 y 2 dejaron 176 frases verificadas
sobre 30 capacidades. Pero AURORA tiene 36 candados, y SEIS de ellos no tenian
ni una sola frase probada:

    delineado · calcular_pieza_grande · cotizar_laser_medidas
    crear_capacidad · editar_codigo · accion_fisica

Una capacidad sin una frase probada es una capacidad que nadie sabe pedir. Los
tres ultimos ademas estaban marcados como NO_AUTOMATICOS en las rondas
anteriores — con razon: ejecutarlos escribe motores, toca el codigo vivo y manda
WhatsApps de verdad. Pero ENRUTARLOS no ejecuta nada. Aqui se prueba lo unico
que faltaba probar: que la frase LLEGA a donde debe. Ejecutarlas sigue siendo
cosa de Anuar, presente, una por una.

Ademas los 30 que ya tenian frases estaban cortos —4 a 6 cada uno— y el habla de
mil formas. Aqui cada capacidad sube a 10 o mas.

COMO SE VERIFICO CADA UNA (ninguna entro sin pasar por aqui):

    d = C._candado_por_familia(frase)          # la lengua de Anuar primero
    if not d:                                   # y si no, la fila de candados
        for nombre, disparador, _m, _i in C._CANDADOS:
            if disparador(frase): d = nombre; break

Una frase SOLO esta en este archivo si `d` salio EXACTAMENTE igual al candado
bajo el que esta escrita. Las que no llegaron NO se maquillaron ni se
reescribieron para que pasaran: se anotaron como triggers cortos, con el
fragmento de codigo que les falta, y se dejaron FUERA. Un archivo de pruebas que
solo guarda lo que pasa no prueba nada; lo que vale es lo que se cayo.

REGLA DE ESTE ARCHIVO: ninguna frase de la ronda 1 ni de la ronda 2 se repite.
Se escribe como escribe Anuar de verdad — sin acentos, con dedazos, con su
vocabulario de taller (encastres, ranurado, despiece, tabloides, kerf, cama,
lupa, retrofit, anticipo, planilla) y el producto antes que el verbo cuando trae
prisa.
"""

FRASES = {

    # ── LAS 6 QUE NADIE HABIA PROBADO NUNCA ───────────────────────────────
    # delineado: la silueta de AFUERA para recortar, o las lineas de ADENTRO
    # para estarcido. Anuar pidio las dos el 2026-08-14 con el PDF de las K-pop
    # y las llama casi igual; si no lo aclara, gana la silueta.
    "delineado": (
        [
            "sacame el delineado de este dibujo",
            "delinealo para que lo corte",
            "necesito la silueta nada mas",
            "hazme el recortable de las kpop",
            "sacale las lineas de corte al pdf",
            "me pidieron un delineado y dejarle pestañas para que no se suelten las piezas",
            "esto lo quiero en estarcido",
            "hazme un stencil de esta imagen",
            "la plantilla para trazar de este dibujo",
            "delineame el personaje",
            "quiero nada mas la silueta de afuera",
            "line art de la foto porfa",
            "sacame la silueta para recortar",
            "quiero el recortable con pestañas",
            "delinear el dibujo del cliente",
        ],
        "La silueta (o el dibujo lineal). NO es print&cut ni vectorizar a "
        "secas.",
    ),
    "calcular_pieza_grande": (
        [
            "cotiza esta piñata para alicia",
            "calcula esta piñata completa es con despiece",
            "calcula la caja de esta piñata es solo el contorno",
            "cotizame la pieza grande de la fiesta",
            "calculame el personaje a 89.5cm",
            "cotiza el personaje completo con despiece",
            "calcula cuantos tabloides me salen de esta pieza",
            "cotizame esta pinata a 1.20 de alto",
            "esta pinata cuanto sale calculala",
            "cotiza el personaje de bluey para una pinata",
            "calcula la pinata de alicia",
            "cotizame la pinata numero 5",
            "calcula esta pieza a escala",
            "cotiza esa pinata que te mande",
            "calcula esta pinata con despiece completo",
            "cotiza la pieza del personaje",
        ],
        "El calculo de produccion de la pinata: escala + tabloides + MDF + "
        "corte. NO debe armar una caja ni buscar en el catalogo.",
    ),
    "cotizar_laser_medidas": (
        [
            "cotiza esta imagen en corte laser con vinil dorado 72x41",
            "cuanto sale en mdf de 60 x 40",
            "a como me sale grabar acrilico de 30x20",
            "precio de cortar mdf 100 x 50",
            "cuanto cobro por un letrero en mdf de 80x30",
            "cotizame 109 x 85 en mdf con vinil metalico",
            "cuanto me cobras por grabado en madera de 25x25",
            "que precio tiene cortar triplay de 120x60",
            "cotiza laser de 40x40 en acrilico",
            "cuanto sale un corte laser de 50 x 70 en mdf",
            "a como el mdf cortado de 90x45",
            "cuanto me cuesta grabar en acrilico",
            "cotizame corte laser en mdf",
            "cuanto por cortar acrilico",
            "cuanto sale grabar madera de 15x15",
            "cotiza mdf de 30x30 con vinil negro",
        ],
        "Laser + material con las medidas EN EL TEXTO, sin DXF adjunto. El "
        "numero en UN turno: el cliente esta esperando.",
    ),
    "crear_capacidad": (
        [
            "creame un motor que saque los precios de acrilico",
            "crea una capacidad para medir el desperdicio",
            "fabricame un motor de etiquetas",
            "hazte capaz de leer facturas",
            "necesito un motor que cuente las piezas del despiece",
            "quiero un motor que me arme el despiece solo",
            "agregate la funcion de recordarme los saldos",
            "construye un motor para las prendas",
            "nuevo motor para el control de saldos",
            "motor nuevo que me avise de los pendientes",
            "crea un motor que me lea los tickets",
            "fabrica una capacidad para los anticipos",
            "creame una capacidad de kerf automatico",
            "agregate la capacidad de medir la cama",
            "crea una capacidad para el letrero luminoso",
        ],
        "Reconocerlo como peticion de motor nuevo. Hoy contesta que eso es "
        "de AURORITA XP (FABRICA_HABILITADA = False) — y esa respuesta es la correcta.",
    ),
    "editar_codigo": (
        [
            "edita CEREBRO/consciencia.py y quita ese mensaje",
            "modifica el archivo de precios del taller",
            "corrige TALLER/ordenes_taller.py",
            "arregla el archivo que trae el error",
            "cambia en el archivo el numero de telefono",
            "edita el codigo del cotizador",
            "agrega en el archivo la marca nueva",
            "reemplaza en el archivo el telefono viejo",
            "modifica MARKETING/generador_sitio_web.py para que no invente",
            "corrige el archivo de la campaña",
            "edita run_aurora.py y sube el puerto",
            "arregla config.json que trae un error",
            "quita de precios.json el termo viejo",
            "edita precios.json y sube el mdf",
        ],
        "Editar codigo de verdad o decir por que no. Nunca fingir el "
        "respaldo, el borrado y la compilacion (bug real del 2026-07-31).",
    ),
    "accion_fisica": (
        [
            "mueve estos archivos a la carpeta de entregados",
            "copia el dxf a la usb",
            "borra los temporales de la carpeta",
            "renombra el archivo con la fecha",
            "instala la libreria que falta",
            "manda un whatsapp a rocio",
            "mandale un whatsapp al cliente del kinder",
            "elimina los archivos repetidos",
            "pasalo a la carpeta de listos",
            "envia un whatsapp con el anticipo",
            "desinstala el programa viejo",
            "copia la carpeta al respaldo",
            "borra el archivo viejo",
            "instala el driver de la laser",
        ],
        "Hacerlo de verdad o decir que no puede. Jamas simular que lo hizo.",
    ),

    # ── Y LOS 30 QUE YA TENIAN FRASES, PERO POCAS ─────────────────────────
    "cotizar_vinil": (
        [
            "precio de vinil textil planchado en 20 playeras",
            "cuanto cobro por rotular un cristal",
            "el htv cuanto cuesta el metro",
            "cuanto sale una calca de 15x15 en recorte",
            "en cuanto dejo 50 stickers de vinil de 5x5",
            "cuanto es el planchado de un logo chico",
            "a como cobras el vinil metalico",
            "cuanto por un vinil de recorte para la camioneta",
            "precio del vinil tornasol por metro",
            "cotiza 20 calcas de 10x10 en vinil",
            "cuanto sale rotular la camioneta",
        ],
        "Precio de SU escalera de vinil. Con varias piezas, suma areas.",
    ),
    "texto_a_corte": (
        [
            "hazme el nombre valentina para el ploter",
            "las letras de MILENS en vinil de recorte",
            "quiero que diga felicidades en vinil",
            "escribe gracias en tipo script para cortar",
            "el rotulo de la puerta en vinil",
            "ponme los numeros del uno al diez para recortar",
            "necesito el texto de la promo listo para el plotter",
            "hazme la palabra abierto en vinil de recorte",
            "el nombre del bebe en vinil textil para la mantita",
            "las palabras feliz cumple para cortar en vinil",
        ],
        "Genera el archivo de corte. Sin cotizar: no le pidio precio.",
    ),
    "print_and_cut": (
        [
            "como corto lo impreso sin que se recorra",
            "ponle las marcas de registro a la hoja",
            "cuanto cabe en una hoja de stickers",
            "el area util de la hoja cual es",
            "cuanto desplazamiento le dejo al contorno",
            "unas calcas full color con su contorno",
            "necesito imprimir y cortar unas etiquetas",
            "marcas de silhouette como se ponen",
            "el excedente del corte cuanto le dejo",
            "print and cut de las calcas de luisa",
        ],
        "Impresion + linea de corte + marcas de registro. Pide el archivo "
        "si falta.",
    ),
    "metodo_campana": (
        [
            "armame una campaña para el dia del padre",
            "como se arma una campaña que sirva",
            "cuales son las reglas de las campanas",
            "como hiciste la campaña de regreso a clases",
            "crea una campaña para navidad",
            "revisa la campaña del dia de las madres",
            "anatomia de una campaña explicamela",
            "nueva campaña para los termos",
            "esta bien esta campaña o le falta gancho",
            "que le falta a la campaña de sublimacion",
        ],
        "El metodo y la critica de campanas, NO los precios de los "
        "paquetes.",
    ),
    "campana_escolar": (
        [
            "cuanto sale el paquete de secundaria",
            "el de kinder en cuanto sale",
            "que traen las etiquetas escolares",
            "las etiquetas para utiles que precio tienen",
            "una mama pregunta por el paquete escolar",
            "los nombres para la ropa cuanto salen",
            "cuanto la tabla de multiplicar",
            "precio del paquete de preescolar",
            "etiquetas para la escuela cuanto",
            "las etiquetas del nino de primaria",
        ],
        "Los 4 precios de la campana viva. Una clienta no puede recibir "
        "otro numero.",
    ),
    "adaptar_diseno": (
        [
            "adaptame el bob esponja a mdf de 5.5",
            "reescala el dibujo a 2.5 son encastres",
            "achicame el diseño a la mitad para mdf de 3mm",
            "amplia el archivo al doble y ajusta los encastres",
            "los machos y hembras ajustalos a 2.7",
            "mi material es de 2.5 acomoda el diseño",
            "viene para 4mm ajustalo",
            "adapta la plantilla a mi acrilico de 3",
            "ajusta el diseño a mi material de 6mm",
            "adapta el archivo a material de 2.5",
        ],
        "Reescala Y ajusta encastres. Dos perillas: escala y espesor. No "
        "crea cajas.",
    ),
    "foto_a_dxf": (
        [
            "quita el fondo de esta foto y pasala a dxf",
            "esta imagen vectorizala para la laser",
            "de esta imagen dame el vector para cortar",
            "borra el fondo del logo y dejalo en dxf",
            "vectoriza esta foto y dejala lista para el laser",
            "elimina el fondo y dejala para cortar",
            "el logo lo quiero limpio y en vector",
            "quitale el fondo al png y damelo en dxf",
            "recorta el sujeto de la foto para cortarlo",
            "sin el fondo y listo para la laser",
        ],
        "UNA cadena completa: fondo + vector + listo para cortar.",
    ),
    "generar_caja": (
        [
            "hazme una caja de 25x18x10",
            "un baul de 40x30x25 en mdf",
            "necesito un cofre para joyeria",
            "quiero una caja con tapa de 10x10x10",
            "armame una cajita de 6x6x4",
            "una caja de 50 x 35 x 20 para los termos",
            "hazme el estuche de 22x14x7 en mdf de 2.7",
            "organizador de 35x25x15 con dedos",
            "quiero un cofre tipo pirata de 30x20x15",
            "caja de 18x18x9 y dame el dxf",
        ],
        "X, Y, H · material 2.7 se corta a 2.5 por el kerf · DXF siempre · "
        "dedos sin el punto del default.",
    ),
    "cotizar_dxf": (
        [
            "cuantos mts de corte tiene el archivo",
            "mide este archivo y dime el corte",
            "cuanto cobro por cortar este diseño",
            "cotiza este archivo porfa",
            "cuanto cuesta cortar lo que te mande",
            "cotiza el dibujo que traigo",
            "cuanto tarda en cortar este dxf",
            "mide el corte del archivo",
            "cotiza este corte para el cliente",
            "cuanto sale cortar esto",
        ],
        "Mide el archivo real. Material por recuadro, corte lineal a 20 "
        "mm/s.",
    ),
    "cotizar": (
        [
            "cuanto cuesta una playera sublimada",
            "cotizame 20 termos con logo",
            "presupuesto de 50 tazas magicas",
            "cuanto vale una agenda personalizada",
            "cotiza 12 vasos cerveceros",
            "cuanto me sale una gorra bordada",
            "dame el precio de 100 llaveros",
            "cuanto cobras por una playera con foto",
            "cuanto cuesta un termo yeti con nombre",
            "cotizame 20 gorras personalizadas",
            "que precio tiene una taza magica",
        ],
        "Del catalogo real (135 productos). Si no lo tiene, decirlo.",
    ),
    "video": (
        [
            "cuantos videos hay en la videoteca",
            "que videos hay listos",
            "revisa los videos duplicados",
            "prepara los videos para tiktok",
            "cuales clips estan en vertical",
            "voltea los videos que estan horizontales",
            "que hay en la videoteca",
            "convierte los videos a 9:16",
            "cuantos reels tengo",
            "revisa los clips repetidos",
        ],
        "Los videos reales de la videoteca. Nada inventado.",
    ),
    "voz": (
        [
            "activa la voz porfa",
            "prende la voz",
            "apaga la voz que estoy con un cliente",
            "modo voz",
            "escuchame",
            "quiero hablarte",
            "di algo para probar",
            "hablame en vez de escribir",
            "desactiva la voz",
            "deja de escuchar",
        ],
        "Decir si la voz esta o no. Sin fingir que hablo.",
    ),
    "ver_aprendizaje": (
        [
            "que aprendiste de mi esta semana",
            "borra lo aprendido y empezamos de cero",
            "que sabes de como hablo",
            "lo que has aprendido enseñamelo",
            "olvida todo lo aprendido",
            "que has aprendido de mis pedidos",
            "olvidalo todo",
            "que aprendiste de como cotizo",
            "que has aprendido del taller",
            "que has aprendido de como te pido las cosas",
            "dime que aprendiste de mi forma de escribir",
        ],
        "Lo que registro de verdad, no un halago. Y poder borrarlo.",
    ),
    "ruta_sola": (
        [
            r"C:\Users\Administrador\Desktop\calamardo.dxf",
            r"C:\AURORA.worktrees\TALLER_OUT\caja.dxf",
            r"D:\trabajos\pinata.cdr",
            r"C:\Users\Administrador\Downloads",
            r"E:\respaldos\logo.svg",
            r"C:\Users\Administrador\Pictures\faro.jpg",
            r"D:\milens\etiquetas.pdf",
            r"C:\AURORA.worktrees\MANUALES",
            r"F:\usb\despiece.dxf",
            r"C:\Users\Administrador\Desktop\termo.png",
        ],
        "Completa la peticion ANTERIOR con ese dato, o pregunta. No es "
        "peticion nueva.",
    ),
    "abrir_navegador": (
        [
            "abre pinterest y busca cajas de mdf",
            "metete a amazon y busca laser",
            "abre milens.com",
            "entra a aliexpress y busca lupas",
            "abre google",
            "abre youtube y busca tutorial de rdworks",
            "metete a facebook y busca el grupo de laser",
            "abre pinterest y busca letreros luminosos",
            "entra a 3axis.co",
            "abre facebook",
            "entra a pinterest",
        ],
        "Abre el sitio, con la busqueda hecha si la pidio.",
    ),
    "acerca_de": (
        [
            "tu que eres exactamente",
            "quien eres tu",
            "para que me sirves en el taller",
            "explicame que eres sin rollos",
            "que ganamos con que estes aqui en el negocio",
            "de que me sirves",
            "que eres",
            "quien eres y de donde saliste",
            "explicame que eres a mi esposa",
            "que ganamos con que estes en la pc",
        ],
        "Honesta con lo que si puede. Sin prometer de mas.",
    ),
    "proveedor": (
        [
            "donde consigo acrilico de 3mm",
            "quien vende mdf en tlaquepaque",
            "con quien compro vinil textil",
            "mi proveedor de termos cual era",
            "proveedores de sublimacion en gdl",
            "donde compro laminas de mdf baratas",
            "quien me surte los termos yeti",
            "con quien consigo tinta de sublimacion",
            "proveedor de acrilico en guadalajara",
            "donde compro las prendas para sublimar",
        ],
        "SUS proveedores, de su directorio. Si no los tiene, decirlo y "
        "ofrecer buscar.",
    ),
    "busqueda_web": (
        [
            "investiga precios de maquinas laser en mexico",
            "googlea que es el kerf",
            "busca en internet ideas de letreros luminosos",
            "investiga que se vende en sublimacion",
            "busca en google como cotizan otros talleres",
            "buscame en internet tendencias de corte laser",
            "investiga cuanto cobran por letreros en gdl",
            "busca en linea proveedores de acrilico chinos",
            "googlea que resina usan para los faros",
            "investiga que piden las papelerias",
        ],
        "Web real con fuentes. Cero dominios inventados.",
    ),
    "corel": (
        [
            "que traigo abierto",
            "corel esta prendido",
            "exporta a pdf lo de corel",
            "abre corel",
            "que documento tengo en coreldraw",
            "el cdr que traigo abierto cual es",
            "corel dime que tengo",
            "pasa a pdf lo de corel",
            "en corel exporta la pagina",
            "que archivo cdr esta abierto",
        ],
        "Estado real de Corel. PDF si exporta, PNG/JPG no.",
    ),
    "dxf": (
        [
            "convierte este svg a dxf",
            "conviertelo a dxf porfa",
            "exporta a dxf esto",
            "quiero esto en dxf",
            "convierte el pdf a dxf",
            "pasa a dxf lo que te mande",
            "dame el archivo en dxf",
            "convierte el eps a dxf",
            "convierte esto a formato de corte",
            "dejalo a formato de corte",
        ],
        "Convierte de verdad o dice por que no pudo.",
    ),
    "negocio": (
        [
            "cuanto llevo vendido esta semana",
            "como va la venta",
            "cuanto me deben los clientes",
            "hazme el corte de caja de hoy",
            "cuanto entro hoy",
            "los numeros del mes como van",
            "que tal vamos",
            "cuanto facture el mes pasado",
            "cuanto llevo ganado",
            "como vamos de ventas",
        ],
        "Numeros REALES de su base. Cero cifras inventadas.",
    ),
    "publicar": (
        [
            "que publico hoy en atf",
            "arma el post de milens",
            "postea hoy en facebook",
            "que subo hoy a facebook",
            "publica en facebook lo de hoy",
            "sube el video de hoy",
            "arma el post pero no lo subas",
            "que toca publicar hoy",
            "publica el reel de la caja",
            "que publico hoy en milens",
            "publica en atf lo de la caja",
        ],
        "PREVIEW nada mas. Publicar de verdad exige un segundo mensaje.",
    ),
    "agenda": (
        [
            "que citas tengo manana",
            "agendame con don beto el jueves",
            "mi agenda como esta",
            "cancela la cita de las 5",
            "ya vino el cliente de los faros",
            "programa una cita para el lunes",
            "que tengo agendado el sabado",
            "confirma la cita del kinder",
            "agenda del dia porfa",
            "que tengo hoy",
            "tengo pendientes hoy",
        ],
        "Citas reales. Sin inventar compromisos.",
    ),
    "servicio_atf": (
        [
            "me pueden recolocar la lupa",
            "cuanto por un retrofit completo",
            "hacen bi led en guadalajara",
            "traigo un golf quiero cambiar los faros",
            "quiero mejorar los faros de mi troca",
            "instalan aozoom",
            "cuanto sale ponerle proyectores de faro",
            "tengo una hilux le quiero poner led",
            "cuanto cuesta el retrofit de un civic",
            "quiero lupas para mi jetta",
            "cuanto sale la lupa",
        ],
        "Los 7 servicios ATF. Los precios que faltan: decir que faltan.",
    ),
    "alta_lead": (
        [
            "apunta a laura 3312223344 quiere termos",
            "registra a don memo cliente nuevo",
            "da de alta a la señora de las playeras",
            "anota a carlos 3311112222 interesado en faros",
            "metelo a la lista es cliente nuevo",
            "nuevo cliente del kinder apuntalo",
            "apunta a rosa quiere 30 etiquetas",
            "registra a este prospecto",
            "otro lead de facebook apuntalo",
            "metelo al crm porfa",
        ],
        "Da de alta el lead. Si faltan datos, pedirlos.",
    ),
    "ficha_vendedor": (
        [
            "dame la ficha del x7",
            "argumentos de venta de los termos",
            "que le contesto al cliente que me dice que esta caro",
            "como le vendo unas tiras secuenciales",
            "hazme un pitch de la sublimacion",
            "como vendo el corte laser a un negocio",
            "brief de venta de los letreros",
            "que le digo al cliente que compara con chinos",
            "como cierro la venta del retrofit",
            "ficha del aozoom x2",
            "dame el pitch de los faros",
        ],
        "Ficha real con argumentos y objeciones. Sin inventar "
        "especificaciones.",
    ),
    "intuicion": (
        [
            "que me recomiendas hacer hoy",
            "en que me conviene meterme",
            "donde estoy perdiendo tiempo",
            "que oportunidad ves",
            "que deberia hacer con los videos parados",
            "que sigue segun tu",
            "tu intuicion que dice",
            "que me conviene mas",
            "donde estoy dejando lana",
            "que area tengo floja",
        ],
        "Basado en uso REAL. Si no hay datos, decirlo. Nunca escupir "
        "diccionarios.",
    ),
    "memoria": (
        [
            "acuerdate que rocio cierra los domingos",
            "guardate este dato del proveedor",
            "recuerda que la cama de la laser es de 60x40",
            "que recuerdas de los faros",
            "apuntate que el mdf lo compro en 2.7",
            "que sabes de la campaña escolar",
            "no se te olvide que anuar corta a 20 mm/s",
            "recuerdas que te dije lo del kerf",
            "que recuerdas del acrilico",
            "guardate que el mdf lo compro en 2.7",
            "que sabes del kerf",
        ],
        "Recuerda de verdad y puede guardar. Sin inventar recuerdos.",
    ),
    "equipos": (
        [
            "activa el equipo de marketing",
            "pon a trabajar el equipo de ventas",
            "arma el equipo de diseño",
            "que equipos de trabajo hay",
            "echame a andar el equipo de taller",
            "cuales equipos puedo usar",
            "que puede hacer el equipo de ventas",
            "lista de equipos porfa",
            "activa el equipo de publicacion",
        ],
        "Ejecuta y ENSENA el resultado, no solo 'trabajo'.",
    ),
    "consulta_codigo": (
        [
            "en que archivo guardas los precios",
            "explicame como funciona el cotizador",
            "que hace la consciencia",
            "en que archivo vive la agenda",
            "como funciona el enrutador",
            "que dice el archivo de configuracion",
            "explicame como trabaja la memoria",
            "que hace el candado de honestidad",
            "leeme el archivo de configuracion",
            "que hace el archivo de precios",
        ],
        "Lee su propio codigo y lo explica en cristiano.",
    ),
}

# ── LOS TRES QUE ACTUAN EN EL PRIMER MENSAJE ─────────────────────────────
# Siguen siendo peligrosos de EJECUTAR en automatico, y por eso las rondas 1 y 2
# ni los tocaron. Lo que cambia aqui es que su ENRUTAMIENTO si esta probado: las
# frases de arriba llegan al candado correcto sin ejecutar nada, porque probar el
# camino no es recorrerlo. Ejecutarlas sigue siendo con Anuar presente.
NO_AUTOMATICOS = {
    "crear_capacidad": "crea un motor REAL en disco (hoy ademas la Fabrica esta cerrada)",
    "editar_codigo":   "escribe archivos del nucleo y corre subprocess",
    "accion_fisica":   "repara Corel de verdad, manda WhatsApps reales, borra archivos",
}

DEJAN_RASTRO = {
    "alta_lead":              "mete leads de prueba al CRM",
    "generar_caja":           "escribe DXF en TALLER_OUT",
    "texto_a_corte":          "escribe archivos de corte",
    "print_and_cut":          "escribe archivos de impresion",
    "foto_a_dxf":             "escribe archivos vectorizados",
    "dxf":                    "escribe archivos convertidos",
    "adaptar_diseno":         "escribe el archivo reescalado",
    "delineado":              "escribe la silueta o el dibujo lineal",
    "calcular_pieza_grande":  "escribe el despiece en tabloides",
    "abrir_navegador":        "abre pestanas reales en Chrome",
    "voz":                    "puede sonar la bocina",
    "corel":                  "toca CorelDRAW si esta abierto",
}


# ══════════════════════════════════════════════════════════════════════════
# Los dos candados que nacieron el 2026-08-26, después de que se escribió el
# resto de este archivo. Son las dos formas en que Anuar le enseña ÉL MISMO,
# sin programador de por medio — la prioridad #1 del proyecto es que AURORA
# le sirva sin nadie más. Sin estas frases no salían en su hoja impresa.
# ══════════════════════════════════════════════════════════════════════════
FRASES.update({
    "ensenar": [
        "cuando te diga sacame la piñata es cotiza esta piñata para alicia",
        "cuando te diga el corte es convierte esto a dxf",
        "si te digo sacame el contorno es sacame el delineado",
        "aprende que chekame el corte es cotiza este dxf",
        "cuando te diga pasalo a curvas hazme exportame a pdf lo que traigo abierto en corel",
        "si te digo cuanto sale hazme cotiza este dxf",
        "apuntale que la caja es generame una caja de 40x30x20",
        "cuando te diga limpiala es quitale el fondo a esta imagen",
    ],
    "aprende_conocimiento": [
        "aurora aprende",
        "aurora aprende un tabloide mide 33x48",
        "aurora aprende que la hoja de mdf de 2.7 me cuesta 110",
        "aprende esto el minuto de corte lo cobro a 8 pesos",
        "aprendete que a alicia le dejo el minuto en 5 pesos",
        "quiero que aprendas que deja siempre 5mm de margen",
        "memoriza esto el vinil de recorte lo vendo por metro",
        "graba esto mi cama de laser mide 130x90",
        "apuntate esto la sublimacion en termo yeti son 180 pesos",
    ],
})
