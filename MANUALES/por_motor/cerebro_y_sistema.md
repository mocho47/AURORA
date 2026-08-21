# Cerebro y Sistema — comandos reales de AURORA

**cotizar_vinil** (cotizador_vinil)
- Qué hace: el precio sale de SU lista, no de una adivinanza.
- Frases que reconoce: «acrilico», «caja», «cajas», «cameo», «cobrar», «cobro», «coste», «costo», «cotiza», «cotizacion», «cotizame», «cuesta»

**texto_a_corte** (texto_a_corte)
- Qué hace: convierte las palabras en archivo de corte real.
- Frases que reconoce: «Oswaldo», «cameo», «cortado», «cortar», «corte», «el letrero», «el nombre», «el rotulo», «el texto», «la palabra», «las letras», «las palabras»

**delineado** (contorno_de_corte)
- Qué hace: El delineado de un dibujo: la silueta de afuera o las líneas de adentro.
- Frases que reconoce: «contorno de corte», «contorno para cortar», «delineado», «delineala», «delinealo», «delineame», «delinear», «dibujo lineal», «estarcido», «estencil», «line art», «linea de corte»

**print_and_cut** (print_and_cut)
- Qué hace: El proceso completo de imprimir y cortar, con sus advertencias.
- Frases que reconoce: «area util de la hoja», «como corto lo impreso», «como pongo las marcas», «contorno extra», «cortar lo impreso», «cuanto cabe en una hoja», «desplazamiento», «excedente del corte», «imprimir y cortar», «marcas de registro», «marcas de silhouette», «marcas de silouette»

**metodo_campana** (metodo_campanas)
- Qué hace: Enseña cómo se arma una campaña, o revisa la que le pasen.
- Frases que reconoce: «anatomia de una campana», «arma una campana», «armame una campana», «checa esta campana», «como armo una campana», «como hiciste la campana», «como se arma una campana», «como se hace una campana», «crea una campana», «creame una campana», «esta bien esta campana», «nueva campana»

**campana_escolar** (campana_escolar)
- Qué hace: Contesta con los paquetes escolares EXACTOS que se le mandaron.
- Frases que reconoce: «el de preescolar», «el de primaria», «etiquetas del nino», «etiquetas del niño», «etiquetas escolares», «etiquetas para la escuela», «etiquetas para utiles», «etiquetas para útiles», «nombres para la ropa», «paquete de preescolar», «paquete de primaria», «paquete escolar»

**adaptar_diseno** (adaptar_grosor)
- Qué hace: Deja un DXF listo para OTRO material y, si se pide, de otro tamaño.
- Frases que reconoce: «achica», «achicame», «achicar», «achicarla», «achicarlo», «adapta», «adaptame», «adaptar», «adaptarla», «adaptarlo», «agranda», «agrandar»

**foto_a_dxf** (foto_a_dxf)
- Qué hace: la cadena completa: foto → sin fondo → vectorizada → DXF.
- Frases que reconoce: «cortarlo», «elimina el fondo», «para cortar», «para corte», «para el laser», «para la laser», «quita el fondo», «quita el fondo y», «quitale el fondo», «quitale el fondo y», «recorta el sujeto», «recorta la imagen»

**generar_caja** (generador_cajas)
- Qué hace: boxes.py: genera la caja que se pidió EN ESPAÑOL, y la cotiza.
- Frases que reconoce: «arma una caja», «caja con divisiones», «caja corazon», «crea una caja», «creame una caja», «genera una bandeja», «genera una caja», «generame el dxf de una caja», «generame una caja», «haz una caja», «hazme un cajon», «hazme una bandeja»

**cotizar_dxf** (cotizador_laser)
- Qué hace: mide los METROS DE CORTE reales de un DXF y lo cotiza.
- Frases que reconoce: «cortar», «corte», «cotiza», «cotiza el archivo», «cotiza el corte», «cotiza el dibujo», «cotiza el diseno», «cotiza el dxf», «cotiza este archivo», «cotiza este corte», «cotiza este diseno», «cotiza este dxf»

**cotizar** (cotizador)
- Qué hace: Cotiza con los precios reales de tu catálogo (98 productos de ATF, 73 servicios de Milens). Si no encuentra el producto lo dice: no inventa precios.
- Frases que reconoce: «cotiza», «cotizacion», «cotizame», «cotizar», «cual es el precio», «cuanto cobras», «cuanto cuesta», «cuanto cuesta el faro aozoom x5», «cuanto me sale», «cuanto sale», «cuanto vale», «cuánto cuesta / sale / vale»

**video** (motor_video)
- Qué hace: Trabaja con tus 296 videos: te dice cuáles ya sirven para Reels, voltea los horizontales a 9:16 con su portada, y encuentra los repetidos por su contenido (no por el nombre). Solo reporta los duplicados: borrar lo decides tú.
- Frases que reconoce: «clip», «clips», «convertir», «convierte», «duplicado», «duplicados», «listos», «miniatura», «portada», «prepara», «preparar», «publicar»

**voz** (voz)
- Qué hace: Prende o apaga la voz: te escucha por el micrófono y te contesta hablando, con voz mexicana. También te avisa si la PC se queda sin memoria.
- Frases que reconoce: «activa la voz», «apaga la voz», «callate», «como suenas», «deja de escuchar», «desactiva la voz», «di algo», «enciende la voz», «escuchame», «hablame», «modo voz», «prende la voz»

**ver_aprendizaje** (aprendizaje)
- Qué hace: Te muestra las formas de hablar que te ha aprendido y te deja borrar las que estén mal, con «olvida <la frase>» (listar, olvidar, olvidar_todo).
- Frases que reconoce: «borra lo aprendido», «lo que has aprendido», «muestrame lo aprendido», «olvida todo lo aprendido», «olvidalo todo», «que aprendiste», «que has aprendido», «que sabes de como hablo»

**ruta_sola** (contexto_archivo)
- Qué hace: Si le mandas solo la ruta de un archivo, lo encuentra —aunque le falte la extensión— y te dice qué puede hacer con él. Si venías pidiendo algo, completa esa petición con ese archivo.
- Frases que reconoce: «abre esta imagen en corel»

**abrir_navegador** (pc_access)
- Qué hace: Abre páginas en tu navegador de verdad. Entiende «abre youtube» sin que tengas que decir el punto-com; reconoce 24 sitios por su nombre (abrir_url).
- Frases que reconoce: «3axis», «abre la pagina», «abre pinterest y busca X», «abre youtube», «abrela», «abrelo», «abreme», «abrir la pagina», «ameede», «behance», «biblioteca de corte», «bibliotecadecorte»

**acerca_de** (auto_conocimiento)
- Qué hace: Te dice qué puede hacer de verdad, con los números reales del sistema y sus límites — nunca inventa capacidades (obtener_capacidades + descubrir).
- Frases que reconoce: «auto describete», «autodescribete», «autodescribirte», «como funcionas», «cuales son tus funciones», «cuantas herramientas», «cuentame de ti», «de que eres capaz», «de que estas hecha», «describete», «descripcion de ti», «descríbete»

**proveedor** (proveedores)
- Qué hace: quién vende qué, y a cuánto.
- Frases que reconoce: «a cuanto me lo dan», «a quien le compro», «con quien compro», «donde le compro», «mi proveedor», «mis proveedores», «proveedor de», «proveedores de», «que proveedores tengo», «quien me lo surte», «quien me surte», «quien me vende»

**servicio_atf** (servicios_atf)
- Qué hace: Atiende a un cliente que pide un servicio de mano de obra de ATF —recolocar una lupa, instalar un retrofit— y **nunca niega uno que sí haces**. Existe porque una vez le negó el servicio a un cliente real.
- Frases que reconoce: «palabras_cliente»

**alta_lead** (oracle_leads)
- Qué hace: da de alta un cliente nuevo con lo que se dictó.
- Frases que reconoce: «anota a», «anota este cliente», «anota un cliente», «apunta a», «apunta este cliente», «apunta un cliente», «crea un lead», «crear lead», «dar de alta al cliente», «guarda el cliente», «guarda este contacto», «me escribio un cliente»

**intuicion** (intuicion)
- Qué hace: Te propone el siguiente paso a partir de tu perfil real de trabajo: qué sueles hacer, qué está pendiente y qué conviene ahora. No adivina, lee tus datos (obtener_perfil + sugerencia_proactiva).
- Frases que reconoce: «prediccion», «predice», «que deberia hacer», «que me recomiendas», «que me sugieres», «que sigue», «sugerencia proactiva», «tu intuicion»

**memoria** (memoria)
- Qué hace: Busca en lo que ya se habló y se aprendió antes, para no repetir ni perder contexto entre sesiones.
- Frases que reconoce: «a cuanto corto», «a cuanto grabo», «a que distancia», «a que potencia», «a que velocidad», «como corto», «como esta el laser», «como esta el tubo», «como esta la impresora», «como esta la lente», «como esta la maquina», «como grabo»

**equipos** (equipos)
- Qué hace: Coordina varios motores a la vez cuando un trabajo necesita más de uno (por ejemplo cotizar + agendar + avisar al cliente).
- Frases que reconoce: «activa el equipo», «activar equipo», «arma el equipo», «equipo de marketing», «equipo de ventas», «lista de equipos», «pon a trabajar el equipo», «que equipos tienes»

**crear_capacidad** (fabrica)
- Qué hace: Crear motores nuevos ya no lo hace AURORA: es trabajo de AURORITA XP, la fábrica que vive aparte. Aquí solo se cargan motores ya probados.
- Frases que reconoce: «agregate la capacidad», «agregate la funcion», «construye un motor», «crea un motor», «crea una capacidad», «creame un motor», «creame una capacidad», «fabrica un motor», «fabrica una capacidad», «fabricame un motor», «hazte capaz de», «motor nuevo que»

**consulta_codigo** (ide)
- Qué hace: Te lee y te explica el código de la propia AURORA, sin modificar nada.
- Frases que reconoce: «.bmp», «.cdr», «.dwg», «.dxf», «.eps», «.jpeg», «.jpg», «.pdf», «.plt», «.png», «.psd», «.svg»

**editar_codigo** (ide_editor)
- Qué hace: Edita archivos de código de verdad: hace respaldo antes, verifica que compile después y revierte solo si algo sale mal. El corazón del sistema está blindado y te pide confirmación explícita.
- Frases que reconoce: «agrega en», «agrega en el archivo», «agregar en», «arregla», «arregla el archivo», «arreglar», «borra la linea», «cambia en», «cambia en el archivo», «cambiar en», «comenta», «corregir»

**accion_fisica** (accion_sistema)
- Qué hace: Abre programas y archivos de tu PC de verdad (Corel, Silhouette, carpetas, documentos).
- Frases que reconoce: «arregla corel», «arregla corell», «arregla la conexion con corel», «borra», «borra cache», «borrar», «contactalo por whatsapp», «copia», «copialo», «copiar», «corel no conecta», «corel no responde»
