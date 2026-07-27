# Manual de comandos reales de AURORA

Generado automáticamente del código real (no escrito a mano) — si algo cambia en el código, este manual se regenera corriendo `python CEREBRO/generar_manual.py` y queda al día. Cada frase de ejemplo listada aquí es una que AURORA reconoce de verdad hoy.

**Aviso real** (encontrado probando en vivo, 2026-07-27): algunos candados combinan DOS categorías de frases a la vez (ej. `negocio` necesita una palabra de pregunta como "cuánto"/"cómo va" JUNTO CON una palabra de dominio como "inventario"/"contabilidad" en el MISMO mensaje; `corel` necesita "corel"/"cdr" JUNTO CON una acción como "exporta"). Una sola frase suelta de la lista puede no bastar por sí sola — este generador aún no distingue esa lógica compuesta, es una mejora pendiente.

**Aviso real 2** (mismo día): dentro de `dxf`, la frase "vectoriza"/"vectorizar" no ejecuta directo como las demás ("convierte a dxf", "pásalo a dxf") — pasa por el enrutador de IA y pide confirmación aparte antes de correr. Mismo candado, comportamiento distinto según la frase exacta usada — verificado en vivo, no corregido todavía.

## Índice por grupo de trabajo (comandos directos)

### Taller

**negocio** (negocio_real)
- Qué hace: CHAT ↔ MOTORES DE NEGOCIO. Lee datos REALES (órdenes, inventario, CRM,
- Frases que reconoce: «bajo minimo», «clientes nuevos», «cobrar», «como va», «contabilidad», «cuales», «cuantas», «cuanto», «cuanto llevo», «cuanto me queda», «cuanto tengo de», «cuanto vendi»

**agenda** (agenda)
- Qué hace: (sin descripción en el código)
- Frases que reconoce: «agenda de hoy», «citas de hoy», «mi agenda», «proxima cita», «proximas citas», «que citas tengo», «que tengo agendado», «que tengo hoy», «resumen de agenda», «tengo pendientes hoy»


### Ventas

**ficha_vendedor** (vendedor)
- Qué hace: (sin descripción en el código)
- Frases que reconoce: «argumentos de venta», «brief de venta», «como vender el», «como vendo el», «dame el pitch», «ficha de», «ficha tecnica de», «hazme un pitch»


### Marketing

**publicar** (publicador)
- Qué hace: CHAT ↔ PUBLICADOR: muestra el preview real de HOY y deja pendiente la
- Frases que reconoce: «estrategia de ingresos», «postea hoy», «prepara la publicacion», «preparar publicacion», «publica el reel», «publica en atf», «publica en facebook», «publica hoy», «publicalo de verdad», «publicalo ya», «publicar hoy», «que publico hoy»


### Diseño

**corel** (motor_corel)
- Qué hace: CHAT ↔ COREL: comandos directos y fijos sobre motor_corel (COM real).
- Frases que reconoce: «abre», «abrir», «almacena», «almacenar», «aplica el color», «cdr», «combina», «corel», «escala», «exporta», «exportar», «extrae el color»

**dxf** (taller_dxf)
- Qué hace: CHAT ↔ TALLER: convierte de verdad un archivo a DXF con taller_core
- Frases que reconoce: «a dxf», «convertir», «convierte», «conviertelo», «dxf», «en dxf», «exporta a dxf», «pasa a dxf», «pasalo a dxf», «vectoriza», «vectorizar»


### Conocimiento

**busqueda_web** (web_search)
- Qué hace: Envoltorio delgado para que _buscar_web calce con la firma uniforme
- Frases que reconoce: «busca en google», «busca en internet», «busca en la red», «busca en la web», «busca en linea», «buscar en internet», «buscar en la web», «consulta en internet», «en internet busca», «googlea», «investiga en la web», «navega»


### Cerebro y Sistema

**abrir_navegador** (pc_access)
- Qué hace: CHAT ↔ pc_access: abre un dominio/URL real directo en el navegador
- Frases que reconoce: «abre la pagina», «abrela», «abrelo», «abrir la pagina», «chrome», «dejala abierta», «dejalo abierto», «dejarla abierta», «dejarlo abierto», «navegador»

**intuicion** (intuicion)
- Qué hace: (sin descripción en el código)
- Frases que reconoce: «prediccion», «predice», «que deberia hacer», «que me recomiendas», «que me sugieres», «que sigue», «sugerencia proactiva», «tu intuicion»

**memoria** (memoria)
- Qué hace: (sin descripción en el código)
- Frases que reconoce: «que recuerdas de», «que recuerdas sobre», «que sabes de», «que tienes guardado sobre», «recuerdas cuando», «recuerdas que», «tu memoria»

**equipos** (equipos)
- Qué hace: (sin descripción en el código)
- Frases que reconoce: «activa el equipo», «activar equipo», «arma el equipo», «equipo de marketing», «equipo de ventas», «lista de equipos», «pon a trabajar el equipo», «que equipos tienes»

**crear_capacidad** (fabrica)
- Qué hace: CHAT ↔ FÁBRICA: crea un motor/capacidad nuevo DE VERDAD (aislado y validado).
- Frases que reconoce: «agregate la capacidad», «agregate la funcion», «construye un motor», «crea un motor», «crea una capacidad», «creame un motor», «creame una capacidad», «fabrica un motor», «fabrica una capacidad», «fabricame un motor», «hazte capaz de», «motor nuevo que»

**consulta_codigo** (ide)
- Qué hace: CHAT ↔ IDE (SOLO LECTURA): lee/busca/explica código real. NUNCA edita el núcleo.
- Frases que reconoce: «abre el archivo», «busca en el codigo», «busca en los archivos», «donde esta la funcion», «en que archivo esta», «ensename el codigo de», «lee el archivo», «leeme el archivo», «muestrame el archivo», «muestrame el codigo», «muestrame el codigo de», «que dice el archivo»

**editar_codigo** (ide_editor)
- Qué hace: CHAT ↔ IDE (EDITAR): modifica cualquier archivo con red anti-ruptura.
- Frases que reconoce: «agrega en el archivo», «arregla el archivo», «cambia en el archivo», «corrige el archivo», «edita el archivo», «edita el codigo», «modifica el archivo», «modifica el codigo», «reemplaza en el archivo»

**accion_fisica** (accion_sistema)
- Qué hace: Ejecuta DE VERDAD una acción física, o dice honestamente por qué no.
- Frases que reconoce: «borra», «borra cache», «borrar», «contactalo por whatsapp», «copia», «copialo», «copiar», «descarga e instala», «desinstala», «desinstalar», «elimina», «eliminar»


## Herramientas del enrutador universal (~510 funciones reales)

Estas no se activan por una frase fija — el enrutador de IA elige la que mejor responda a lo que pidas, verificando que existan los datos necesarios antes de ejecutarla de verdad (nunca la adivina a ciegas).

### AGENDA (9)

- `AGENDA/agenda:init_db` — init db (agenda)
- `AGENDA/agenda:crear_cita` — crear cita (agenda)
- `AGENDA/agenda:listar` — listar (agenda)
- `AGENDA/agenda:dia` — dia (agenda)
- `AGENDA/agenda:actualizar_estado` — actualizar estado (agenda)
- `AGENDA/agenda:proximas` — proximas (agenda)
- `AGENDA/agenda:eliminar` — eliminar (agenda)
- `AGENDA/agenda:resumen` — resumen (agenda)
- `AGENDA/agenda:exportar_ics` — exportar ics (agenda)

### AUTH (31)

- `AUTH/identidad_core:estado` — estado (identidad_core)
- `AUTH/identidad_core:configurar_pin` — Define o cambia el PIN del dueño. Si ya existe, exige el PIN actual.
- `AUTH/identidad_core:login` — Verifica el PIN y, si es correcto, emite una LLAVE única para este dispositivo.
- `AUTH/identidad_core:rol` — Devuelve 'dueño' si la llave es válida; si no, 'cliente'.
- `AUTH/identidad_core:revocar_todos` — Cierra sesión en TODOS los dispositivos (si pierdes uno o sospechas).
- `AUTH/usuarios:listar_usuarios` — Para la pantalla de login: nombres, rol y si ya tienen PIN. Sin secretos.
- `AUTH/usuarios:configurar_pin` — Define o cambia el PIN de un usuario. Si ya tiene, exige el actual.
- `AUTH/usuarios:login` — Verifica el PIN y devuelve rol + cartuchos permitidos + una llave de sesión.
- `AUTH/usuarios:crear_usuario` — Agrega un usuario nuevo (rol válido). El PIN lo pone él en su primer login.
- `AUTH/usuarios:eliminar_usuario` — eliminar usuario (usuarios)
- `AUTH/automation_core:MotorAutomatizaciones.procesar_seguimientos_whatsapp` — procesar seguimientos whatsapp (MotorAutomatizaciones)
- `AUTH/automation_core:MotorAutomatizaciones.arrancar_demonio` — arrancar demonio (MotorAutomatizaciones)
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.generar_idea` — Paso 1: idea REAL de contenido generada por Groq con el contexto del Asesor.
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.generar_script` — Paso 2: script REAL de video (Groq) a partir de la idea real.
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.generar_imagen` — Paso 3: HONESTO. No hay generador de imágenes conectado en AURORA.
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.generar_caption` — Paso 4: caption + hashtags REALES generados por Groq.
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.publicar_redes` — Paso 5: publicación REAL con salvaguarda.
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.monitorear_engagement` — Paso 6: métricas REALES (comentarios de la página FB). Sin tokens/datos,
- `AUTH/flujo_marketing_milens:FlujoMarketingMilens.ejecutar_flujo_completo` — Ciclo completo REAL. Por defecto confirmar=False → NO publica.
- `AUTH/flujo_venta_atf:FlujoVentaATF.capturar_cliente` — Paso 1: crea un lead REAL en el CRM Oracle (o dry-run si confirmar=False).
- `AUTH/flujo_venta_atf:FlujoVentaATF.analizar_necesidad` — Paso 2: análisis local, sin efectos (solo lectura).
- `AUTH/flujo_venta_atf:FlujoVentaATF.generar_cotizacion` — Paso 3: cotización REAL contra el catálogo de TALLER (precio verdadero, NO inventa).
- `AUTH/flujo_venta_atf:FlujoVentaATF.enviar_cotizacion` — Paso 4: prepara/envía la cotización por WhatsApp (REAL vía Green API).
- `AUTH/flujo_venta_atf:FlujoVentaATF.seguimiento_cliente` — Paso 5: prepara (o envía) el mensaje de seguimiento del embudo real.
- `AUTH/flujo_venta_atf:FlujoVentaATF.cierre_venta` — Paso 6: convierte el lead REAL en orden REAL (oracle.db). Dry-run si confirmar=False.
- `AUTH/flujo_venta_atf:FlujoVentaATF.ejecutar_flujo_completo` — Ejecuta el flujo completo. Con confirmar=False (default) TODO es dry-run REAL:
- `AUTH/sleep_cycle:SleepCycle.resumen_taller` — Ingresos/órdenes/estados REALES del taller (34 órdenes reales).
- `AUTH/sleep_cycle:SleepCycle.resumen_crm` — Leads y órdenes CRM REALES. Si oracle.db está vacía → 0 honesto.
- `AUTH/sleep_cycle:SleepCycle.horas_pico` — Calcula hora pico a partir de CUÁNDO se crearon las órdenes reales.
- `AUTH/sleep_cycle:SleepCycle.mantenimiento` — Revisa de verdad que los módulos compilen. No modifica nada.
- `AUTH/sleep_cycle:SleepCycle.ejecutar_ciclo_completo` — ejecutar ciclo completo (SleepCycle)

### BIBLIOTECA (6)

- `BIBLIOTECA/biblioteca:init_db` — init db (biblioteca)
- `BIBLIOTECA/biblioteca:reindexar_semantica` — Calcula embeddings para páginas de 'docs' que aún no lo tengan.
- `BIBLIOTECA/biblioteca:ingerir_pdf` — ingerir pdf (biblioteca)
- `BIBLIOTECA/biblioteca:buscar` — HÍBRIDO: combina FTS5 (palabras) + similitud semántica (significado, vía embeddings).
- `BIBLIOTECA/biblioteca:contexto_para_llm` — Devuelve un bloque de texto de los manuales, para inyectar al cerebro.
- `BIBLIOTECA/biblioteca:estado` — estado (biblioteca)

### CEREBRO (50)

- `CEREBRO/acciones_sistema:buscar_archivo` — Busca un archivo por nombre (o fragmento) en las carpetas comunes. Real.
- `CEREBRO/acciones_sistema:copiar` — Copia un archivo y VERIFICA que llegó. destino puede ser carpeta o archivo.
- `CEREBRO/acciones_sistema:mover` — Mueve un archivo y VERIFICA (existe en destino y ya no en origen).
- `CEREBRO/acciones_sistema:reparar_whatsapp` — Cierra WhatsApp y limpia su cache REAL. Devuelve exactamente qué hizo.
- `CEREBRO/aurora_cerebro_simple:AuroraCerebro.esta_operativo` — esta operativo (AuroraCerebro)
- `CEREBRO/aurora_cerebro_simple:AuroraCerebro.razonar` — razonar (AuroraCerebro)
- `CEREBRO/aurora_cerebro_v4:AuroraCerebro.esta_operativo` — esta operativo (AuroraCerebro)
- `CEREBRO/aurora_cerebro_v4:AuroraCerebro.razonar` — razonar (AuroraCerebro)
- `CEREBRO/auto_conocimiento:AutoConocimiento.escanear_estructura` — Escanea los archivos Python de AURORA y devuelve un mapa completo.
- `CEREBRO/auto_conocimiento:AutoConocimiento.leer_archivo` — Lee el contenido de un archivo propio de AURORA.
- `CEREBRO/auto_conocimiento:AutoConocimiento.diagnosticar_modulos` — Intenta importar cada módulo de MOTORES y CEREBRO.
- `CEREBRO/auto_conocimiento:AutoConocimiento.obtener_capacidades` — Retorna un mapa de todas las capacidades activas de AURORA.
- `CEREBRO/auto_conocimiento:AutoConocimiento.estado_sistema_completo` — Fotografía completa del sistema en este momento.
- `CEREBRO/auto_conocimiento:AutoConocimiento.buscar_en_codigo` — Busca un patrón de texto en todos los archivos Python de AURORA.
- `CEREBRO/auto_reparacion:AutoReparacion.reparar` — Repara un archivo. Backup → LLM fix → validar → aplicar o rollback.
- `CEREBRO/auto_reparacion:AutoReparacion.diagnosticar_y_reparar_todo` — Escanea todos los módulos, detecta errores de sintaxis y los repara.
- `CEREBRO/auto_reparacion:AutoReparacion.revertir` — Restaura el backup más reciente de un archivo.
- `CEREBRO/cotizar_imagen:cotizar_imagen_laser` — Cotiza corte/grabado láser REAL desde una imagen pegada: quita fondo, vectoriza a DXF, escala a altura_cm y mide la longitud real (nunca inventa el precio).
- `CEREBRO/equipos:listar_equipos` — Catálogo de equipos con sus motores, meta y si su acción está lista.
- `CEREBRO/equipos:activar_equipo` — Pone a trabajar un equipo: ejecuta su acción REAL. Si no tiene una acción
- `CEREBRO/fabrica_agentes:crear_agente` — Guarda un agente REAL en disco. Devuelve su ficha.
- `CEREBRO/fabrica_agentes:listar_agentes` — listar agentes (fabrica_agentes)
- `CEREBRO/fabrica_agentes:obtener_agente` — obtener agente (fabrica_agentes)
- `CEREBRO/fabrica_agentes:marcar_ejecucion` — marcar ejecucion (fabrica_agentes)
- `CEREBRO/fabrica_agentes:eliminar_agente` — eliminar agente (fabrica_agentes)
- `CEREBRO/fabrica_agentes:prompt_ejecucion` — Arma el prompt para que el cerebro EJECUTE el agente con su contexto real.
- `CEREBRO/fabrica_motores:crear_motor` — Genera con Groq un motor .py que cumple el contrato, lo valida con
- `CEREBRO/fabrica_motores:listar_motores_custom` — Lista los .py de MOTORES_CUSTOM con su META (carga aislada, tolerante).
- `CEREBRO/fabrica_motores:probar_motor` — Carga el motor <slug> con importlib y ejecuta ejecutar(accion, datos).
- `CEREBRO/generar_manual:generar` — generar (generar_manual)
- `CEREBRO/paneles_cerebro:autoconocimiento` — Inventario/estado REAL del sistema, leído por AURORA sobre sí misma.
- `CEREBRO/paneles_cerebro:sueno_reparacion` — Estado combinado del motor de sueño + memoria + auto-reparación.
- `CEREBRO/paneles_cerebro:voz` — Estado REAL del subsistema de voz (VOZ/voz_google.py).
- `CEREBRO/paneles_cerebro:resumen` — Junta los tres motores del cerebro en un solo dict para el panel.
- `CEREBRO/pc_access:PcAccess.ejecutar` — Ejecuta un comando PowerShell real. Bloqueados los destructivos.
- `CEREBRO/pc_access:PcAccess.ejecutar_python` — Ejecuta código Python en el contexto del proyecto.
- `CEREBRO/pc_access:PcAccess.leer_archivo` — Lee cualquier archivo de TEXTO del PC (código, .txt, .json, .csv...).
- `CEREBRO/pc_access:PcAccess.escribir_archivo` — Escribe un archivo. Solo en rutas permitidas.
- `CEREBRO/pc_access:PcAccess.listar_directorio` — Lista el contenido de un directorio.
- `CEREBRO/pc_access:PcAccess.buscar_archivos` — Busca archivos por patrón glob.
- `CEREBRO/pc_access:PcAccess.estado_sistema` — Estado en tiempo real: CPU, RAM, disco, procesos.
- `CEREBRO/pc_access:PcAccess.procesos_activos` — Lista los procesos con más uso de CPU/RAM.
- `CEREBRO/pc_access:PcAccess.espacio_disco` — espacio disco (PcAccess)
- `CEREBRO/pc_access:PcAccess.leer_portapapeles` — Lee el contenido actual del portapapeles.
- `CEREBRO/pc_access:PcAccess.escribir_portapapeles` — Escribe texto al portapapeles.
- `CEREBRO/pc_access:PcAccess.abrir_archivo` — Abre un archivo con su aplicación predeterminada. Resuelve carpetas
- `CEREBRO/pc_access:PcAccess.abrir_url` — Abre una URL real en el navegador default (Start-Process). NO es un
- `CEREBRO/pc_access:PcAccess.apps_instaladas` — apps instaladas (PcAccess)
- `CEREBRO/razonador:razonar` — Razona en profundidad: piensa paso a paso, se autocritica y da la respuesta final.
- `CEREBRO/razonador:ejecutar` — ejecutar (razonador)

### CORE (56)

- `CORE/aurora:AURORA.procesar_mensaje` — Process user message and route to optimal motor + SDK
- `CORE/aurora:AURORA.main_loop` — Main interactive loop (for testing)
- `CORE/aurora:get_aurora` — Get or create AURORA instance
- `CORE/aurora:main` — Entry point
- `CORE/aurora_crisis:CrisisProtocol.detectar_nivel` — Detecta nivel de crisis automáticamente
- `CORE/aurora_crisis:CrisisProtocol.procesar_crisis` — Procesa detección y respuesta de crisis
- `CORE/aurora_crisis:CrisisProtocol.generar_plan_intervencion` — Genera plan específico de intervención por nivel
- `CORE/aurora_crisis:CrisisProtocol.obtener_recursos_por_nivel` — Retorna recursos disponibles para cada nivel
- `CORE/aurora_crisis_protocol:CrisisProtocol.analyze_message` — Analiza mensaje y determina nivel de crisis
- `CORE/aurora_crisis_protocol:CrisisProtocol.send_silent_alert` — Envía alerta silenciosa a adultos (sin que adolescente se entere)
- `CORE/aurora_crisis_protocol:CrisisProtocol.call_emergency` — Contacta servicios de emergencia (911 o equivalente)
- `CORE/aurora_crisis_protocol:CrisisMonitor.monitor` — Monitorea mensaje y actúa según nivel de crisis
- `CORE/aurora_crisis_protocol:CrisisMonitor.get_crisis_summary` — Retorna resumen de crisis para este usuario
- `CORE/aurora_registry:MotorRegistry.get_motor` — Get motor instance by ID
- `CORE/aurora_registry:MotorRegistry.get_metadata` — Get motor metadata
- `CORE/aurora_registry:MotorRegistry.get_active_motors` — Get list of active motor IDs
- `CORE/aurora_registry:MotorRegistry.execute_motor` — Execute action on motor
- `CORE/aurora_registry:MotorRegistry.list_motors` — List all motors with metadata
- `CORE/aurora_registry:MotorRegistry.get_status` — Get registry status
- `CORE/aurora_registry:get_registry` — Get or create registry instance
- `CORE/aurora_sdk_manager:AuroraSDKManager.call_sdk` — Llama SDK especificado con fallback automático
- `CORE/aurora_sdk_manager:AuroraSDKManager.list_available_sdks` — Lista SDKs disponibles
- `CORE/aurora_sdk_manager:AuroraSDKManager.get_sdk_status` — Retorna estado de cada SDK
- `CORE/aurora_selector:AuroraSelector.select` — Select optimal motor and SDK for message
- `CORE/aurora_selector:get_selector` — Get or create selector instance
- `CORE/buscador_web_profesional:ProductoEncontrado.puntuacion_calidad` — Calcula puntuación de calidad 0-100
- `CORE/buscador_web_profesional:ResultadoBusqueda.obtener_mejor_opcion` — Retorna el mejor producto basado en puntuación
- `CORE/buscador_web_profesional:ResultadoBusqueda.obtener_analisis` — Genera análisis del resultado
- `CORE/buscador_web_profesional:BuscadorWebProfesional.buscar` — Realiza búsqueda en múltiples fuentes en paralelo
- `CORE/buscador_web_profesional:ejemplo_uso` — Ejemplo de cómo usar el buscador profesional
- `CORE/chatbot_wa_profesional:AnalizadorIntenciones.analizar` — Analiza el texto y retorna (intención, confianza)
- `CORE/chatbot_wa_profesional:AnalizadorIntencionesBásico.analizar` — Detecta la intención del usuario
- `CORE/chatbot_wa_profesional:GeneradorRespuestas.generar` — Genera una respuesta según la intención
- `CORE/chatbot_wa_profesional:ChatbotWAProfesional.procesar_mensaje` — Procesa un mensaje entrante y retorna respuesta
- `CORE/chatbot_wa_profesional:ChatbotWAProfesional.enviar_mensaje` — Envía un mensaje vía WhatsApp usando API real
- `CORE/chatbot_wa_profesional:ChatbotWAProfesional.verificar_webhook` — Verifica token del webhook
- `CORE/chatbot_wa_profesional:ChatbotWAProfesional.validar_firma_webhook` — Valida la firma del webhook
- `CORE/chatbot_wa_profesional:ChatbotWAProfesional.obtener_estadisticas` — Obtiene estadísticas de leads
- `CORE/chatbot_wa_profesional:ejemplo_uso` — Ejemplo de cómo usar el chatbot
- `CORE/config:Config.validate` — Valida configuración
- `CORE/config:Config.print_status` — Imprime estado de config
- `CORE/config:Config.get_available_sdks` — Retorna SDKs disponibles
- `CORE/consola_motores:estado` — Lista los cartuchos con su estado (activo/apagado), agrupados.
- `CORE/consola_motores:toggle` — Prende/apaga un cartucho. Los CORE no se pueden apagar.
- `CORE/consola_motores:listar_loadouts` — listar loadouts (consola_motores)
- `CORE/consola_motores:guardar_loadout` — Guarda un perfil: la lista de cartuchos que deben quedar ACTIVOS.
- `CORE/consola_motores:aplicar_loadout` — Aplica un perfil: apaga todo lo apagable que NO esté en la lista del loadout.
- `CORE/consola_motores:motores_desactivados_bus` — Nombres REALES de motores del bus que Anuar apagó (para que el registrador los salte).
- `CORE/consola_motores:eliminar_loadout` — eliminar loadout (consola_motores)
- `CORE/publicador_atf_profesional:CredencialesRed.token_valido` — Verifica si el token sigue siendo válido
- `CORE/publicador_atf_profesional:CredencialesRed.renovar_token_si_necesario` — Renueva el token si está expirado
- `CORE/publicador_atf_profesional:ConfiguracionPublicacion.validar` — Valida la configuración
- `CORE/publicador_atf_profesional:PublicadorATFProfesional.verificar_credenciales` — Verifica y renueva credenciales si es necesario
- `CORE/publicador_atf_profesional:PublicadorATFProfesional.publicar_multi_red` — Publica en múltiples redes simultáneamente
- `CORE/publicador_atf_profesional:PublicadorATFProfesional.obtener_estadisticas` — Obtiene estadísticas de publicaciones
- `CORE/publicador_atf_profesional:ejemplo_uso` — Ejemplo de cómo usar el publicador profesional

### EDITOR (56)

- `EDITOR/conversiones:aligerar_dxf` — Convierte splines a polilíneas y guarda R2000: RDWorks lo lee y pesa menos.
- `EDITOR/conversiones:a_bw_puro` — a bw puro (conversiones)
- `EDITOR/conversiones:a_linea` — a linea (conversiones)
- `EDITOR/conversiones:papercraft_a_dxf` — Renderiza → B&N → vtracer(SVG) → Inkscape(DXF). Honesto: raster vectorizado (imperfecto).
- `EDITOR/conversiones:quitar_fondo` — Recorta el sujeto y elimina el fondo. IA real (rembg). PNG con transparencia.
- `EDITOR/conversiones:foto_a_lineal` — Recorta la persona (rembg) y genera dibujo lineal limpio B&N (XDoG + realce local).
- `EDITOR/conversor_formatos:paginas_pdf` — Número de páginas de un PDF (para conversión por lote).
- `EDITOR/conversor_formatos:formatos` — Qué puede convertir el módulo (para el panel). Transparente con los límites.
- `EDITOR/conversor_formatos:convertir` — Convierte 'entrada' al formato 'a' (svg/png/pdf/dxf/eps/ps).
- `EDITOR/conversor_formatos:convertir_todo` — PDF multipágina → un archivo por página (lote). Ideal SVG/PNG para reeditar/imprimir.
- `EDITOR/corel_core:disponible` — True si CorelDRAW responde por COM ahora mismo.
- `EDITOR/corel_core:info_documento` — Estado real del documento activo en Corel (solo lectura).
- `EDITOR/corel_core:exportar_pdf` — Publica el documento activo a PDF en ruta_salida.
- `EDITOR/corel_core:exportar_bitmap` — Exporta el documento activo a PNG/JPG con el DPI exacto indicado.
- `EDITOR/corel_core:escalar_pagina` — Cambia el tamaño de página (cm) del documento activo.
- `EDITOR/corel_core:preparar_para_lona` — Prepara el mismo diseño del documento activo para impresión de lona/banner:
- `EDITOR/corel_core:cerrar_documento_sin_guardar` — Cierra un documento por nombre SIN guardar (para limpiar documentos de prueba).
- `EDITOR/corel_core:abrir_documento` — Abre un archivo REAL (PDF, CDR, AI, etc.) dentro de CorelDRAW (OpenDocument),
- `EDITOR/corel_core:guardar_copia` — Guarda una COPIA del documento activo en ruta_salida (.cdr) sin tocar
- `EDITOR/corel_core:agregar_imagen_documento_activo` — Importa una imagen al documento ACTIVO (el que ya tienes abierto y
- `EDITOR/corel_core:quitar_fondo_y_agregar` — Flujo real del splash: quita el fondo de la imagen (IA real, rembg) y
- `EDITOR/corel_core:crear_planilla` — Arma una planilla real: repite ruta_pieza tantas veces como quepan en
- `EDITOR/corel_core:extraer_color_pixel` — Gotero real: lee el color exacto del pixel (x,y) de una imagen de
- `EDITOR/corel_core:aplicar_color_seleccion` — Aplica un color RGB real a la forma actualmente SELECCIONADA en Corel
- `EDITOR/corel_core:extraer_y_aplicar_color` — Gotero completo: muestra el pixel (x,y) de ruta_imagen y lo aplica de
- `EDITOR/corel_core:integrar_logo_fondo` — Crea un documento NUEVO, importa la imagen de fondo (ajustada al tamaño
- `EDITOR/cotizador_corte:cotizar_corte` — Cotiza corte láser desde un DXF con precios reales de Milens.
- `EDITOR/escalas_planillas:cm_a_px` — cm a px (escalas_planillas)
- `EDITOR/escalas_planillas:px_a_cm` — px a cm (escalas_planillas)
- `EDITOR/escalas_planillas:formatos_papel` — Lista de formatos disponibles (para el panel).
- `EDITOR/escalas_planillas:info_dpi` — Reporta tamaño en px, DPI embebido y el tamaño físico real al que imprimiría.
- `EDITOR/escalas_planillas:fijar_dpi` — Cambia SOLO el DPI embebido (no remuestrea): ajusta el tamaño de impresión sin tocar píxeles.
- `EDITOR/escalas_planillas:escalar_a_medida` — Lleva una imagen a una medida FÍSICA real (cm) a un DPI dado.
- `EDITOR/escalas_planillas:generar_planilla` — Imposición: llena una hoja con copias de un ítem a medida física exacta.
- `EDITOR/plantillas_taza:r_grad` — r grad (plantillas_taza)
- `EDITOR/plantillas_taza:r_confeti` — r confeti (plantillas_taza)
- `EDITOR/plantillas_taza:r_corazones` — r corazones (plantillas_taza)
- `EDITOR/plantillas_taza:r_estrellas` — r estrellas (plantillas_taza)
- `EDITOR/plantillas_taza:r_lunares` — r lunares (plantillas_taza)
- `EDITOR/plantillas_taza:r_olas` — r olas (plantillas_taza)
- `EDITOR/plantillas_taza:r_geom` — r geom (plantillas_taza)
- `EDITOR/plantillas_taza:r_marmol` — r marmol (plantillas_taza)
- `EDITOR/plantillas_taza:r_nieve` — r nieve (plantillas_taza)
- `EDITOR/plantillas_taza:r_rayas` — r rayas (plantillas_taza)
- `EDITOR/plantillas_taza:r_floral` — r floral (plantillas_taza)
- `EDITOR/plantillas_taza:r_nubes` — r nubes (plantillas_taza)
- `EDITOR/plantillas_taza:r_glow` — r glow (plantillas_taza)
- `EDITOR/plantillas_taza:buscar_fondos` — Búsqueda indexada por ocasión/tema. Vacío = todos.
- `EDITOR/plantillas_taza:temas` — Lista de temas (para el panel).
- `EDITOR/plantillas_taza:componer_taza` — Compone la taza: fondo elegido + (según modo) foto y/o frase.
- `EDITOR/plantillas_taza:generar_hoja_a4` — Imposición: hasta 3 tazas (21x9 cm) apiladas en una hoja A4 lista para imprimir.
- `EDITOR/plantillas_taza:catalogo_fondos` — Hoja de contactos con los 50 fondos agrupados por tema (miniaturas).
- `EDITOR/reeditar_diseno:analizar_pdf` — Inventario real de un PDF: qué trae dentro para decidir cómo reeditarlo.
- `EDITOR/reeditar_diseno:extraer_elementos` — Separa una página en piezas reales dentro de una carpeta:
- `EDITOR/reeditar_diseno:realzar_foto` — Mejora una foto para ampliarla: LANCZOS (factor×) + máscara de nitidez + realce suave.
- `EDITOR/reeditar_diseno:reescalar_a_medida` — Lleva una página del PDF a una medida física NUEVA (cm@DPI) re-rasterizando el PDF original

### FORJA (39)

- `FORJA/motor_diseno:health_check` — Endpoint de salud del motor.
- `FORJA/motor_diseno:get_status` — Obtener estadísticas del motor.
- `FORJA/motor_diseno:get_programs` — Obtener lista de programas soportados y su estado de detección.
- `FORJA/motor_diseno:detect_programs` — Detectar programas de diseño instalados en el sistema.
- `FORJA/motor_diseno:execute` — Endpoint principal de ejecución del motor de diseño.
- `FORJA/motor_forja:diagnose` — Ejecutar diagnóstico de emprendimiento.
- `FORJA/motor_forja:get_profile` — Obtener perfil de emprendedor.
- `FORJA/motor_forja:create_referral` — Crear un enlace de referido.
- `FORJA/motor_forja:get_commissions` — Calcular comisiones MLM.
- `FORJA/motor_forja:coach_message` — Obtener mensaje de coaching de Nathalye.
- `FORJA/motor_forja:generate_plan` — Generar plan de acción de negocio.
- `FORJA/motor_forja:health_check` — health check (motor_forja)
- `FORJA/motor_forja:get_status` — get status (motor_forja)
- `FORJA/motor_forja:diagnostic_questions` — Obtener las 20 preguntas del diagnóstico.
- `FORJA/motor_forja:business_templates` — Obtener plantillas de plan de negocio.
- `FORJA/motor_forja:execute` — execute (motor_forja)
- `FORJA/motor_negocios:add_client` — Agregar un nuevo cliente.
- `FORJA/motor_negocios:get_clients` — Obtener lista de clientes.
- `FORJA/motor_negocios:search_client` — Buscar cliente por nombre, email o teléfono.
- `FORJA/motor_negocios:add_product` — Agregar un nuevo producto.
- `FORJA/motor_negocios:get_products` — Obtener lista de productos.
- `FORJA/motor_negocios:update_stock` — Actualizar stock de un producto.
- `FORJA/motor_negocios:create_order` — Crear una nueva orden de venta.
- `FORJA/motor_negocios:get_orders` — Obtener lista de órdenes.
- `FORJA/motor_negocios:update_order_status` — Actualizar estado de una orden.
- `FORJA/motor_negocios:get_metrics` — Obtener métricas del dashboard.
- `FORJA/motor_negocios:health_check` — Endpoint de salud del motor.
- `FORJA/motor_negocios:get_status` — Obtener estadísticas del motor.
- `FORJA/motor_negocios:get_businesses` — Obtener lista de negocios con sus productos.
- `FORJA/motor_negocios:metrics_endpoint` — Obtener métricas del dashboard.
- `FORJA/motor_negocios:quick_note` — Guardar una nota rápida de negocio.
- `FORJA/motor_negocios:execute` — Endpoint principal de ejecución del motor de negocios.
- `FORJA/motor_social:generate_post` — Generar contenido para redes sociales.
- `FORJA/motor_social:get_calendar` — Obtener calendario de contenido.
- `FORJA/motor_social:save_draft` — Guardar un borrador de post.
- `FORJA/motor_social:generate_hashtags` — Generar hashtags relevantes para un tema.
- `FORJA/motor_social:health_check` — health check (motor_social)
- `FORJA/motor_social:get_status` — get status (motor_social)
- `FORJA/motor_social:execute` — execute (motor_social)

### INTEGRACIONES (14)

- `INTEGRACIONES/email_integration:EmailIntegration.enviar_cotizacion` — Envía cotización por email REAL vía SMTP.
- `INTEGRACIONES/email_integration:EmailIntegration.enviar_confirmacion_pedido` — Envía confirmación de pedido REAL vía SMTP.
- `INTEGRACIONES/email_integration:EmailIntegration.enviar_reporte_diario` — Envía reporte diario a equipo REAL vía SMTP.
- `INTEGRACIONES/email_integration:EmailIntegration.enviar_alerta` — Envía alertas por email REAL vía SMTP.
- `INTEGRACIONES/telegram_integration:TelegramIntegration.enviar_mensaje` — Envía mensaje Telegram REAL vía Bot API.
- `INTEGRACIONES/telegram_integration:TelegramIntegration.enviar_dashboard` — Envía dashboard como mensaje Telegram
- `INTEGRACIONES/telegram_integration:TelegramIntegration.enviar_alerta` — Envía alertas automáticas
- `INTEGRACIONES/telegram_integration:TelegramIntegration.crear_bot_handlers` — Define handlers para comandos del bot
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.enviar_mensaje` — Envia mensaje de texto via Green API (HTTP real).
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.enviar_cotizacion` — Formatea y envia una cotizacion por WhatsApp.
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.enviar_confirmacion_pedido` — Envia confirmacion de pedido al cliente.
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.recibir_mensajes` — Polling de mensajes nuevos desde Green API. Ya NO borra la notificación
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.escuchar` — Bucle de escucha continua. callback(data) se llama con cada mensaje.
- `INTEGRACIONES/whatsapp_integration:WhatsAppIntegration.get_status` — get status (WhatsAppIntegration)

### MANUALES (3)

- `MANUALES/aprendizaje:catalogo` — Herramientas que AURORA puede aprender (para el panel).
- `MANUALES/aprendizaje:aprender` — Busca el manual de 'herramienta', lo descarga (si es PDF) y lo ingiere a la Biblioteca.
- `MANUALES/aprendizaje:ingerir_url` — Ruta manual: Anuar pega la URL exacta del PDF y AURORA lo descarga+ingiere.

### MARKETING (29)

- `MARKETING/analizador_mercado:nichos` — Nichos disponibles para analizar (para poblar el panel).
- `MARKETING/analizador_mercado:analizar` — Análisis de mercado REAL de un nicho: busca en vivo (varias consultas),
- `MARKETING/analizador_mercado:comparar_precios` — Busca un producto en la web (MX) y devuelve los precios/rangos REALES detectados
- `MARKETING/asesor_core:conocimiento` — Devuelve el conocimiento real del algoritmo de una red (o todas).
- `MARKETING/asesor_core:playbook` — Buenas prácticas por flanco: viralizacion | ventas | monetizacion (o todos).
- `MARKETING/asesor_core:mejores_horarios` — Calcula las mejores horas para publicar a partir de datos REALES de actividad
- `MARKETING/asesor_core:diagnostico` — Diagnostica sobre métricas REALES por red y sugiere acciones concretas.
- `MARKETING/asesor_core:construir_brief_para_cerebro` — Arma el contexto (conocimiento + datos reales) para que el cerebro genere el plan.
- `MARKETING/catalogo_compartible:generar_catalogo_pdf` — Genera el PDF del catálogo y devuelve la ruta + conteos.
- `MARKETING/plan_monetizacion:init_db` — init db (plan_monetizacion)
- `MARKETING/plan_monetizacion:listar_videos` — TODOS los videos REALES de Anuar, RECURSIVO (incluye subcarpetas: r11, terminados,
- `MARKETING/plan_monetizacion:catalogo` — UNIFICA y AGRUPA los videos en un índice por carpeta (sin mover ni borrar nada).
- `MARKETING/plan_monetizacion:generar_plan` — Crea/extiende el calendario desde HOY por 'dias'. Idempotente: una fila por fecha.
- `MARKETING/plan_monetizacion:post_de_hoy` — Los posts de HOY: 1 video DISTINTO por red (TikTok/IG/FB/YouTube).
- `MARKETING/plan_monetizacion:marcar_publicado` — Marca UNA red como publicada (avanza la racha si el día queda completo).
- `MARKETING/plan_monetizacion:reservar_publicacion` — Reserva atómicamente un post para publicar (compare-and-set real:
- `MARKETING/plan_monetizacion:liberar_reserva` — Si la subida real falla tras reservar, regresa el post a 'pendiente' para
- `MARKETING/plan_monetizacion:registrar_publicado_historico` — Registro persistente e independiente del archivo físico — ver init_db().
- `MARKETING/plan_monetizacion:marcar_dia` — Marca TODAS las redes de un día como publicadas (por defecto HOY).
- `MARKETING/plan_monetizacion:racha` — Racha: días CONSECUTIVOS donde TODAS las redes del día quedaron publicadas.
- `MARKETING/plan_monetizacion:bloque_pendiente` — El próximo bloque (de hoy en adelante) que NO ha sido aprobado. Para el aviso en pantalla.
- `MARKETING/plan_monetizacion:revisar_bloque` — Todos los posts de un bloque (para revisarlo antes de aprobar).
- `MARKETING/plan_monetizacion:aprobar_post` — Aprueba UNA publicación del bloque.
- `MARKETING/plan_monetizacion:aprobar_bloque` — Aprueba TODO un bloque de un golpe.
- `MARKETING/plan_monetizacion:plan` — Calendario de HOY en adelante, agrupado por día (cada día trae sus redes).
- `MARKETING/plan_monetizacion:copy_borrador` — Borrador REAL de gancho+caption con Groq, para ATF. Anuar lo ajusta al video.
- `MARKETING/publicacion_inteligente:estrategia_ingresos` — EQUIPO INTERACTIVO en una llamada: une conocimiento de algoritmo (asesor) +
- `MARKETING/publicacion_inteligente:preparar_publicacion` — Arma TODO para el post de hoy SIN publicar: qué video, copy nativo por red con
- `MARKETING/publicacion_inteligente:publicar_hoy` — DISPARA la publicación REAL del video de hoy en la red indicada.

### MEMORIA (30)

- `MEMORIA/analitica_marketing:AnaliticaMarketing.inicializar` — inicializar (AnaliticaMarketing)
- `MEMORIA/analitica_marketing:AnaliticaMarketing.registrar_publicacion` — Registra una nueva publicación. Retorna su ID.
- `MEMORIA/analitica_marketing:AnaliticaMarketing.actualizar_metricas` — Actualiza vistas, likes, leads de una publicación después de publicarla.
- `MEMORIA/analitica_marketing:AnaliticaMarketing.top_performers` — top performers (AnaliticaMarketing)
- `MEMORIA/analitica_marketing:AnaliticaMarketing.resumen_plataformas` — resumen plataformas (AnaliticaMarketing)
- `MEMORIA/analitica_marketing:AnaliticaMarketing.consolidar_en_semantica` — Extrae patrones de las publicaciones no consolidadas
- `MEMORIA/analitica_marketing:AnaliticaMarketing.estado` — estado (AnaliticaMarketing)
- `MEMORIA/contexto_usuario:ContextoUsuario.inicializar` — inicializar (ContextoUsuario)
- `MEMORIA/contexto_usuario:ContextoUsuario.obtener` — Retorna el perfil del usuario. Lo crea si es nuevo.
- `MEMORIA/contexto_usuario:ContextoUsuario.actualizar` — Actualiza el perfil del usuario tras cada interacción.
- `MEMORIA/contexto_usuario:ContextoUsuario.leads_calientes` — Retorna leads tibios/calientes sin interacción en 48h (para follow-up).
- `MEMORIA/motor_sueno:MotorSueno.iniciar` — Arranca el bucle de vigilancia en background.
- `MEMORIA/motor_sueno:MotorSueno.detener` — detener (MotorSueno)
- `MEMORIA/motor_sueno:MotorSueno.registrar_actividad` — Llamar cada vez que haya actividad en el sistema para resetear el temporizador.
- `MEMORIA/motor_sueno:MotorSueno.estado` — estado (MotorSueno)
- `MEMORIA/perfil_habilidades:PerfilHabilidades.inicializar` — inicializar (PerfilHabilidades)
- `MEMORIA/perfil_habilidades:PerfilHabilidades.analizar_interaccion` — Analiza una interacción y extrae:
- `MEMORIA/perfil_habilidades:PerfilHabilidades.obtener_perfil` — Perfil completo: habilidades + áreas de oportunidad.
- `MEMORIA/perfil_habilidades:PerfilHabilidades.resumen_para_contexto` — Resumen compacto del perfil para inyectar en el contexto de cada motor.
- `MEMORIA/perfil_habilidades:PerfilHabilidades.sugerencia_proactiva` — Genera una sugerencia proactiva basada en áreas de oportunidad.
- `MEMORIA/perfil_habilidades:PerfilHabilidades.estado` — estado (PerfilHabilidades)
- `MEMORIA/sistema_memoria:SistemaMemoria.inicializar` — inicializar (SistemaMemoria)
- `MEMORIA/sistema_memoria:SistemaMemoria.registrar` — Graba un evento en memoria episódica. Retorna el ID del registro.
- `MEMORIA/sistema_memoria:SistemaMemoria.episodios_recientes` — episodios recientes (SistemaMemoria)
- `MEMORIA/sistema_memoria:SistemaMemoria.marcar_consolidados` — marcar consolidados (SistemaMemoria)
- `MEMORIA/sistema_memoria:SistemaMemoria.purgar_episodios_viejos` — Borra episodios consolidados con más de `dias` — devuelve cuántos borró.
- `MEMORIA/sistema_memoria:SistemaMemoria.aprender` — Escribe o actualiza un conocimiento en memoria semántica.
- `MEMORIA/sistema_memoria:SistemaMemoria.recordar` — Recupera conocimientos de la memoria semántica.
- `MEMORIA/sistema_memoria:SistemaMemoria.estadisticas` — estadisticas (SistemaMemoria)
- `MEMORIA/sistema_memoria:SistemaMemoria.estado` — estado (SistemaMemoria)

### MOTORES (55)

- `MOTORES/adaptadores:MotorOracle.listar_leads` — listar leads (MotorOracle)
- `MOTORES/adaptadores:MotorOracle.crear_lead` — crear lead (MotorOracle)
- `MOTORES/adaptadores:MotorOracle.resumen` — resumen (MotorOracle)
- `MOTORES/adaptadores:MotorOracle.get_status` — get status (MotorOracle)
- `MOTORES/adaptadores:MotorFichas.ficha` — ficha (MotorFichas)
- `MOTORES/adaptadores:MotorFichas.listar_fichas` — listar fichas (MotorFichas)
- `MOTORES/adaptadores:MotorFichas.tecnicas` — tecnicas (MotorFichas)
- `MOTORES/adaptadores:MotorFichas.get_status` — get status (MotorFichas)
- `MOTORES/adaptadores:MotorTaller.convertir_dxf` — convertir dxf (MotorTaller)
- `MOTORES/adaptadores:MotorTaller.vectorizar` — vectorizar (MotorTaller)
- `MOTORES/adaptadores:MotorTaller.catalogo` — catalogo (MotorTaller)
- `MOTORES/adaptadores:MotorTaller.get_status` — get status (MotorTaller)
- `MOTORES/adaptadores:MotorSublimacion.frames_de_video` — frames de video (MotorSublimacion)
- `MOTORES/adaptadores:MotorSublimacion.lienzo_blanco` — lienzo blanco (MotorSublimacion)
- `MOTORES/adaptadores:MotorSublimacion.get_status` — get status (MotorSublimacion)
- `MOTORES/adaptadores:MotorPublicador.publicar` — publicar (MotorPublicador)
- `MOTORES/adaptadores:MotorPublicador.estado_redes` — estado redes (MotorPublicador)
- `MOTORES/adaptadores:MotorPublicador.enviar_whatsapp` — enviar whatsapp (MotorPublicador)
- `MOTORES/adaptadores:MotorPublicador.get_status` — get status (MotorPublicador)
- `MOTORES/adaptadores:MotorVoz.hablar` — hablar (MotorVoz)
- `MOTORES/adaptadores:MotorVoz.get_status` — get status (MotorVoz)
- `MOTORES/adaptadores:MotorAsesor.get_status` — get status (MotorAsesor)
- `MOTORES/adaptadores:MotorEditor.quitar_fondo` — quitar fondo (MotorEditor)
- `MOTORES/adaptadores:MotorEditor.preparar_laser` — preparar laser (MotorEditor)
- `MOTORES/adaptadores:MotorEditor.linea_byn` — linea byn (MotorEditor)
- `MOTORES/adaptadores:MotorEditor.get_status` — get status (MotorEditor)
- `MOTORES/adaptadores:MotorBuscador.get_status` — get status (MotorBuscador)
- `MOTORES/adaptadores:MotorProgramador.get_status` — get status (MotorProgramador)
- `MOTORES/adaptadores:MotorCorel.info_documento` — info documento (MotorCorel)
- `MOTORES/adaptadores:MotorCorel.exportar_pdf` — exportar pdf (MotorCorel)
- `MOTORES/adaptadores:MotorCorel.escalar_pagina` — escalar pagina (MotorCorel)
- `MOTORES/adaptadores:MotorCorel.get_status` — get status (MotorCorel)
- `MOTORES/motor_analisis:MotorAnalisis.analizar` — analizar (MotorAnalisis)
- `MOTORES/motor_analisis:MotorAnalisis.get_status` — get status (MotorAnalisis)
- `MOTORES/motor_coaching:MotorCoaching.coach` — coach (MotorCoaching)
- `MOTORES/motor_coaching:MotorCoaching.get_status` — get status (MotorCoaching)
- `MOTORES/motor_coaching_real:MotorCoachingReal.sesion_coaching` — sesion coaching (MotorCoachingReal)
- `MOTORES/motor_coaching_real:MotorCoachingReal.ejecutar` — ejecutar (MotorCoachingReal)
- `MOTORES/motor_coaching_real:MotorCoachingReal.get_status` — get status (MotorCoachingReal)
- `MOTORES/motor_code_gen:MotorCodeGen.generar` — generar (MotorCodeGen)
- `MOTORES/motor_code_gen:MotorCodeGen.get_status` — get status (MotorCodeGen)
- `MOTORES/motor_cotizador:MotorCotizador.cotizar` — cotizar (MotorCotizador)
- `MOTORES/motor_cotizador:MotorCotizador.get_status` — get status (MotorCotizador)
- `MOTORES/motor_imagenes:MotorImagenes.analizar` — analizar (MotorImagenes)
- `MOTORES/motor_imagenes:MotorImagenes.get_status` — get status (MotorImagenes)
- `MOTORES/motor_marketing:MotorMarketing.generar_contenido` — Genera contenido viral real para la plataforma indicada.
- `MOTORES/motor_marketing:MotorMarketing.estrategia_semanal` — Genera un plan de contenido para 7 días basado en memoria + tendencias.
- `MOTORES/motor_marketing:MotorMarketing.analizar_competencia` — Analiza tendencias del nicho usando web search + LLM.
- `MOTORES/motor_marketing:MotorMarketing.get_status` — get status (MotorMarketing)
- `MOTORES/motor_negocios:MotorNegocios.consultar` — consultar (MotorNegocios)
- `MOTORES/motor_negocios:MotorNegocios.get_status` — get status (MotorNegocios)
- `MOTORES/motor_reasoning:MotorReasoning.razonar` — razonar (MotorReasoning)
- `MOTORES/motor_reasoning:MotorReasoning.get_status` — get status (MotorReasoning)
- `MOTORES/motor_ventas:MotorVentas.procesar` — procesar (MotorVentas)
- `MOTORES/motor_ventas:MotorVentas.get_status` — get status (MotorVentas)

### MOTORES_CUSTOM (5)

- `MOTORES_CUSTOM/conversor_mxn_a_usd:ejecutar` — ejecutar (conversor_mxn_a_usd)
- `MOTORES_CUSTOM/medidor_dxf:ejecutar` — ejecutar (medidor_dxf)
- `MOTORES_CUSTOM/medidor_dxf:obtener_bbox` — obtener bbox (medidor_dxf)
- `MOTORES_CUSTOM/medidor_dxf:calcular_ancho_alto` — calcular ancho alto (medidor_dxf)
- `MOTORES_CUSTOM/medidor_dxf:obtener_estado_sistema` — obtener estado sistema (medidor_dxf)

### ORACLE (15)

- `ORACLE/oracle_core:init_db` — init db (oracle_core)
- `ORACLE/oracle_core:crear_lead` — crear lead (oracle_core)
- `ORACLE/oracle_core:obtener_lead` — obtener lead (oracle_core)
- `ORACLE/oracle_core:listar_leads` — listar leads (oracle_core)
- `ORACLE/oracle_core:actualizar_lead_estado` — actualizar lead estado (oracle_core)
- `ORACLE/oracle_core:crear_orden` — crear orden (oracle_core)
- `ORACLE/oracle_core:obtener_orden` — obtener orden (oracle_core)
- `ORACLE/oracle_core:listar_ordenes` — listar ordenes (oracle_core)
- `ORACLE/oracle_core:actualizar_orden_estado` — actualizar orden estado (oracle_core)
- `ORACLE/oracle_core:convertir_lead_a_orden` — Convierte un lead GANADO en orden, dejando la RELACIÓN registrada (lead_id).
- `ORACLE/oracle_core:ficha_cliente` — Vista 360: el lead con TODAS sus órdenes relacionadas y lo facturado.
- `ORACLE/oracle_core:pronostico_embudo` — PRONÓSTICO: cuánto dinero traes en el embudo por etapa (leads abiertos).
- `ORACLE/oracle_core:fuentes_efectivas` — ¿QUÉ FUENTE TRAE CLIENTES QUE SÍ COMPRAN? (la pregunta que más vale).
- `ORACLE/oracle_core:resumen` — resumen (oracle_core)
- `ORACLE/oracle_core:obtener_conexion` — Enlace publico inyectado por el fix.

### PUBLICADOR (26)

- `PUBLICADOR/auto_publicar_atf:main` — main (auto_publicar_atf)
- `PUBLICADOR/corregir_telefono_atf:traer_videos` — traer videos (corregir_telefono_atf)
- `PUBLICADOR/corregir_telefono_atf:nueva_desc` — Devuelve (nuevo_texto, motivo) o (None, None) si no hay que tocar.
- `PUBLICADOR/corregir_telefono_atf:editar` — editar (corregir_telefono_atf)
- `PUBLICADOR/corregir_telefono_atf:main` — main (corregir_telefono_atf)
- `PUBLICADOR/metricool_conector:estado_metricool` — estado metricool (metricool_conector)
- `PUBLICADOR/metricool_conector:listar_marcas` — Marcas/brands conectadas a la cuenta de Metricool (cada una con su blogId).
- `PUBLICADOR/metricool_conector:publicar_metricool` — Publica/agenda REAL via Metricool a una o varias redes (facebook, tiktok, pinterest, instagram...).
- `PUBLICADOR/metricool_conector:listar_publicaciones` — Publicaciones programadas/publicadas en Metricool en un rango de fechas ISO.
- `PUBLICADOR/metricool_conector:eliminar_publicacion` — eliminar publicacion (metricool_conector)
- `PUBLICADOR/metricool_conector:mejor_hora_publicar` — Mejor horario sugerido por Metricool para publicar (segun tu audiencia real).
- `PUBLICADOR/publicador_core:estado_redes` — estado redes (publicador_core)
- `PUBLICADOR/publicador_core:publicar` — publicar (publicador_core)
- `PUBLICADOR/publicador_core:comentarios_pagina` — Lee comentarios REALES de las publicaciones recientes de la página FB.
- `PUBLICADOR/publicador_core:responder_comentario` — Responde un comentario REAL en Facebook (acción pública: requiere autorización de Anuar).
- `PUBLICADOR/publicador_core:publicar_video_fb` — Sube un VIDEO local a la página de Facebook (Graph API /videos). Publicación REAL.
- `PUBLICADOR/publicador_core:configurar_meta` — AUTOMATIZA la config de Meta: con el token de usuario corto + app_id + secret,
- `PUBLICADOR/publicador_core:estado_whatsapp` — estado whatsapp (publicador_core)
- `PUBLICADOR/publicador_core:enviar_whatsapp` — Envía un WhatsApp REAL vía Green API. Honesto: si no está autorizado, lo dice.
- `PUBLICADOR/social_manager:init_db` — init db (social_manager)
- `PUBLICADOR/social_manager:estado_conexiones` — Estado REAL de cada red. Honesto: si no hay token de API, dice 'falta configurar'.
- `PUBLICADOR/social_manager:agendar` — Agenda una publicación (estado 'pendiente'). NO publica: sólo la deja lista.
- `PUBLICADOR/social_manager:calendario` — Publicaciones de HOY en adelante hasta hoy+dias, ordenadas por fecha y hora.
- `PUBLICADOR/social_manager:marcar_publicado` — Marca una publicación agendada como 'publicado' (registro manual tras aprobar).
- `PUBLICADOR/social_manager:eliminar` — Elimina una publicación de la agenda.
- `PUBLICADOR/social_manager:resumen` — Conteo de agendadas por red/estado + próximas publicaciones pendientes.

### REDES (3)

- `REDES/red_diagnostico:escanear_cast` — Encuentra dispositivos Google Cast/Nest/Home en la red local (puerto 8009).
- `REDES/red_diagnostico:ping_perdida` — Mide pérdida de paquetes y latencia real hacia un dispositivo.
- `REDES/red_diagnostico:diagnosticar` — Diagnóstico REAL de un dispositivo Cast + recomendación según su estado.

### SISTEMA (6)

- `SISTEMA/optimizador:diagnostico` — diagnostico (optimizador)
- `SISTEMA/optimizador:limpiar_temporales` — Borra temporales más viejos que N horas (seguro: no toca archivos en uso reciente).
- `SISTEMA/optimizador:optimizar` — optimizar (optimizador)
- `SISTEMA/organizador_archivos:escanear` — SOLO LECTURA. Cataloga archivos por tipo bajo 'raiz' (por defecto el perfil del usuario),
- `SISTEMA/organizador_archivos:agrupar` — Agrupa archivos SUELTOS de UNA carpeta segura en subcarpetas por tipo (_PDF, _DXF, …).
- `SISTEMA/organizador_archivos:carpetas_seguras` — Carpetas donde SÍ se permite agrupar (para el panel).

### SUBLIMACION (3)

- `SUBLIMACION/sublimacion_core:de_video` — Descarga el video (si es url) y extrae fotogramas. Devuelve la carpeta de frames.
- `SUBLIMACION/sublimacion_core:lienzo_blanco` — Genera el LIENZO en blanco con guías (para armar a mano), 300 DPI: PNG + PDF + preview.
- `SUBLIMACION/sublimacion_core:montar` — Monta una imagen de diseño en el lienzo a medida y exporta LISTO PARA IMPRIMIR

### TALLER (49)

- `TALLER/administracion:listar_precios` — Costo por minuto + lista de materiales/artículos con su precio de hoja.
- `TALLER/administracion:set_costo_minuto` — Actualiza el costo por minuto de máquina.
- `TALLER/administracion:guardar_material` — Agrega un material/artículo nuevo, o actualiza el existente (por nombre).
- `TALLER/administracion:borrar_material` — Elimina un material/artículo por nombre.
- `TALLER/album_catalogo:generar_album` — Genera el álbum de catálogo. Devuelve dict con status y métricas.
- `TALLER/cotizador_servicios:guardar_servicio` — Agrega o actualiza un trabajo/servicio en el catálogo (categoría 'productos').
- `TALLER/cotizador_servicios:borrar_servicio` — Borra un trabajo/servicio del catálogo por nombre (solo de 'productos').
- `TALLER/cotizador_servicios:catalogo_plano` — Aplana el catálogo en una lista de artículos cotizables (precio + costo + unidad).
- `TALLER/cotizador_servicios:cotizar` — carrito = [{"nombre": str, "cantidad": num}]
- `TALLER/inventario:init_db` — init db (inventario)
- `TALLER/inventario:agregar_item` — Alta de un material. Identidad = nombre + categoría + TALLA/MEDIDA + COLOR,
- `TALLER/inventario:editar_item` — Edita los datos de un artículo EXISTENTE (color, talla, unidad, mínimo, costo).
- `TALLER/inventario:borrar_item` — Borra UN artículo del inventario y su historial de movimientos.
- `TALLER/inventario:limpiar_todo` — Vacía TODO el inventario (artículos + movimientos). Acción deliberada.
- `TALLER/inventario:sembrar_catalogo` — Precarga los artículos de Milens y ATF con cantidad 0 (solo faltan cantidades).
- `TALLER/inventario:movimiento` — Entrada(+) / salida(-) de existencias. Registra el movimiento en el historial.
- `TALLER/inventario:listar` — listar (inventario)
- `TALLER/inventario:bajo_minimo` — bajo minimo (inventario)
- `TALLER/inventario:historial` — historial (inventario)
- `TALLER/inventario:resumen` — resumen (inventario)
- `TALLER/ordenes_taller:init_db` — init db (ordenes_taller)
- `TALLER/ordenes_taller:guardar_imagen_bytes` — Guarda bytes de imagen subida. Devuelve la ruta relativa servible.
- `TALLER/ordenes_taller:guardar_imagen_url` — Descarga una imagen desde URL (Pinterest, etc.) y la guarda local.
- `TALLER/ordenes_taller:catalogo` — Combina catalogo_atf.json + fichas_tecnicas.json en una lista buscable.
- `TALLER/ordenes_taller:cotizar` — Busca precio REAL en el catálogo. Determinista, sin LLM, sin inventar.
- `TALLER/ordenes_taller:crear_orden` — crear orden (ordenes_taller)
- `TALLER/ordenes_taller:agregar_imagen_orden` — Añade una imagen (ya guardada) a una orden existente.
- `TALLER/ordenes_taller:listar_ordenes` — listar ordenes (ordenes_taller)
- `TALLER/ordenes_taller:editar_orden` — Edita una orden EXISTENTE (mismo folio). Recalcula saldo y utilidad.
- `TALLER/ordenes_taller:actualizar_estado` — actualizar estado (ordenes_taller)
- `TALLER/ordenes_taller:alertas` — Calcula alertas de entrega en vivo:
- `TALLER/ordenes_taller:contabilidad_mensual` — Balance por mes (por fecha de entrega; si falta, por fecha de creación).
- `TALLER/reportes_bi:resumen_general` — resumen general (reportes_bi)
- `TALLER/reportes_bi:por_mes` — por mes (reportes_bi)
- `TALLER/reportes_bi:top_productos` — top productos (reportes_bi)
- `TALLER/reportes_bi:por_solicitante` — por solicitante (reportes_bi)
- `TALLER/reportes_bi:estados` — estados (reportes_bi)
- `TALLER/reportes_bi:oportunidades` — oportunidades (reportes_bi)
- `TALLER/reportes_bi:reporte_completo` — reporte completo (reportes_bi)
- `TALLER/reportes_bi:requiere_contexto` — requiere contexto (reportes_bi)
- `TALLER/reportes_bi:process_query` — process query (reportes_bi)
- `TALLER/reportes_bi:execute` — execute (reportes_bi)
- `TALLER/taller_core:disponible` — disponible (taller_core)
- `TALLER/taller_core:catalogo` — Indexa la biblioteca de trabajos DXF ya terminados (Downloads\DXF).
- `TALLER/taller_core:convertir_a_dxf` — Convierte SVG/PDF/AI/EPS a DXF para laser.
- `TALLER/taller_core:vectorizar` — Imagen (PNG/JPG B&N) -> SVG vectorial -> DXF, trazando con Inkscape.
- `TALLER/taller_core:caja` — Genera una caja paramétrica para corte láser (boxes.py) en SVG + DXF.
- `TALLER/taller_core:reajustar_grosor` — Escalador de grosor: regenera la pieza al NUEVO grosor de material (ej. 2.7mm)
- `TALLER/taller_core:texto_a_dxf` — Genera un nombre/texto como vector DXF para cortar/grabar.

### VENDEDOR (21)

- `VENDEDOR/seguimiento_ventas:init_db` — init db (seguimiento_ventas)
- `VENDEDOR/seguimiento_ventas:etapas` — Devuelve las etapas del embudo.
- `VENDEDOR/seguimiento_ventas:sincronizar_leads` — Trae leads REALES del Oracle CRM (oracle.db → tabla leads) al embudo.
- `VENDEDOR/seguimiento_ventas:pendientes` — Leads a seguir HOY: etapa abierta y (sin interacción nunca) o
- `VENDEDOR/seguimiento_ventas:mensaje_sugerido` — Redacta (NO envía) un mensaje de seguimiento con Groq: español mexicano, cálido,
- `VENDEDOR/seguimiento_ventas:enviar_seguimiento` — ACCIÓN REAL: envía `mensaje` por WhatsApp al lead vía publicador_core.enviar_whatsapp
- `VENDEDOR/seguimiento_ventas:avanzar_etapa` — Mueve el lead a otra etapa del embudo (validada) y registra la interacción.
- `VENDEDOR/seguimiento_ventas:resumen` — Conteo por etapa + tasa de conversión (ganado / cerrados) sobre datos REALES.
- `VENDEDOR/vendedor_core:listar_fichas` — Lista los equipos del catálogo y si su ficha técnica está COMPLETA o PENDIENTE.
- `VENDEDOR/vendedor_core:ficha` — Devuelve la ficha técnica REAL de un equipo. Si hay campos PENDIENTE, lo dice honesto.
- `VENDEDOR/vendedor_core:tecnicas` — Librería real de técnicas de venta (una o todas).
- `VENDEDOR/vendedor_core:prompt_extraccion` — Prompt para que el cerebro extraiga la ficha SOLO del texto real de la web. Sin inventar.
- `VENDEDOR/vendedor_core:guardar_ficha` — Guarda en fichas_tecnicas.json SOLO los campos con dato real + las fuentes (URLs).
- `VENDEDOR/vendedor_core:editar_ficha` — Editor del PANEL: actualiza una ficha por su ID EXACTO. A diferencia de guardar_ficha,
- `VENDEDOR/vendedor_core:construir_brief` — Arma el contexto para el cerebro. modo: 'cliente' (vender) o 'interno' (asesor técnico de Anuar).
- `VENDEDOR/vendedor_core:init_vendedor_db` — Crea las tablas si no existen y siembra el catálogo desde las fichas reales.
- `VENDEDOR/vendedor_core:registrar_venta_db` — Registra una venta completa (cliente + venta + detalles) en vendedor.db (SQLite).
- `VENDEDOR/vendedor_core:listar_productos_db` — Lista todos los productos del catálogo (sembrado desde las fichas reales).
- `VENDEDOR/vendedor_core:obtener_producto_db` — Obtiene la información de un producto específico por su SKU.
- `VENDEDOR/verificador_core:verificar_ficha` — Devuelve lista de incoherencias detectadas (vacía = ok).
- `VENDEDOR/verificador_core:verificar_todas` — Revisa todo el catálogo. Si degradar=True, baja a PENDIENTE lo incoherente y limpia

### WEB (4)

- `WEB/web_real:buscar` — Busca en internet AHORA (DuckDuckGo vía ddgs) y devuelve títulos, URLs y extractos reales.
- `WEB/web_real:noticias` — Noticias recientes reales sobre un tema.
- `WEB/web_real:leer_pagina` — Abre una URL y extrae su TEXTO real (sin scripts/estilos).
- `WEB/web_real:contexto_para_llm` — Empaqueta resultados reales de la web como contexto para el cerebro.
