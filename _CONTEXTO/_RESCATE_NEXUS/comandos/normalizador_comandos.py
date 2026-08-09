NORMALIZACIONES_COMANDO = {
    "fase book": "facebook",
    "fasebuk": "facebook",
    "yutuf": "youtube",
    "guatsap": "whatsapp",
    "guasap": "whatsapp",
    "insta": "instagram",
    "tik tok": "tiktok",
    "bloc de notas": "notepad",
    "calculadora": "calculadora",
    "navegador": "navegador",
    "explorador": "explorador",
    "modo oscuro": "modo oscuro",
    "modo seguro": "modo seguro",
    "voz segura": "voz segura",
    "modo narrado": "modo narrado",
    "modo legado": "modo legado",
    "volumen": "volumen",
    "brillo": "brillo",
    "intensidad": "intensidad",
    "voz": "voz",
    "campaña": "campaña",
    "campanas": "campana",
    "contenido": "contenido",
    "copy": "copy",
    "copi": "copy",
    "has tag": "hashtag",
    "hash tag": "hashtag",
    "hash tags": "hashtag",
    "hashtags": "hashtag",
    "titulo": "titulo",
    "titular": "titulo",
    "guion": "guion",
    "gui\u00f3n": "guion",
    "idea": "idea",
    "ideas": "idea",
    "plan semanal": "plan semanal",
    "plan de contenido": "plan contenido",
    "instagram": "instagram",
    "facebook": "facebook",
    "tiktok": "tiktok",
    "youtube": "youtube",
    "linkedin": "linkedin",
    "twitter": "twitter",
    "estudio de mercado": "estudio mercado",
    "estudios de mercado": "estudio mercado",
    "analisis de mercado": "estudio mercado",
    "análisis de mercado": "estudio mercado",
    "plan de ventas": "plan ventas",
    "planes de ventas": "plan ventas",
    "precio": "precio",
    "competencia": "competencia",
    "segmento": "segmento",
    "buyer persona": "buyer persona",
    "recordar": "recordar",
    "recordatorios": "recordatorios",
    "avanzar proyecto": "avanzar proyecto",
    "plan de anuncios": "plan anuncios",
    "anuncios": "plan anuncios",
    "brief": "brief",
    "brief creativo": "brief",
    "corte láser": "corte laser",
    "sublimación": "sublimacion",
    "iluminación automotriz": "iluminacion automotriz",
    "google": "google",
    "google maps": "maps",
    "maps": "maps",
    "mapa": "maps",
    "correo": "gmail",
    "email": "gmail",
    "gmail": "gmail",
    "calendar": "calendar",
    "calendario": "calendar",
    "drive": "drive",
    "documentos": "docs",
    "documento": "docs",
    "docs": "docs",
    "hojas": "sheets",
    "hoja de calculo": "sheets",
    "sheets": "sheets",
    "presentaciones": "slides",
    "slides": "slides",
    "meet": "meet",
    "zoom": "zoom",
    "teams": "teams",
    "wasap": "whatsapp",
    "whatsap": "whatsapp",
    "whatsapp": "whatsapp",
    "spotify": "spotify",
    "noticias": "news",
    "news": "news",
    "banco": "bank",
    "banca": "bank",
    "explorador": "explorador",
    "navegador": "navegador",
    "chrome": "chrome",
    "edge": "edge",
    "bloc de notas": "notepad",
    "nota": "notepad",
    "calculadora": "calculadora",
    "reloj": "reloj",
    "captura": "captura",
    "pantalla": "pantalla",
    "crm": "crm",
    "analytics": "analytics",
    "ads": "ads",
    "facebook ads": "adsfacebook",
    "google ads": "adsgoogle",
    "shopify": "shopify",
    "mercado libre": "mercadolibre",
    "meli": "mercadolibre",
    "mercado pago": "mercadopago",
    "mpago": "mercadopago",
    "aliexpress": "aliexpress",
    "ali express": "aliexpress",
    "pinterest": "pinterest",
    "reddit": "reddit",
    "telegram": "telegram",
    "outlook": "outlook",
    "hotmail": "outlook",
    "rdw": "rdw",
    "tor": "tor",
    "dark web": "tor",
    "dxf": "dxf",
    "factura": "factura",
    "facturación": "factura",
    "inventario": "inventario",
    "finanzas": "finanzas",
    "ventas": "ventas",
    "reporte": "reporte",
    "informe": "reporte",
    "precio": "precio",
    "clientes": "clientes",
    "proveedores": "proveedores",
    "agenda": "calendar",
    "que es nexus": "nexus info",
    "qué es nexus": "nexus info",
    "titulos nexus": "nexus titulos",
    "títulos nexus": "nexus titulos",
}

def normalizar_verbo(texto, variantes, canonico):
    texto = (texto or "").lower().strip()
    for variante in variantes:
        if texto.startswith(variante + " "):
            return texto.replace(variante, canonico, 1)
    return texto

def normalizar_comando(texto):
    texto = (texto or "").lower().strip()
    texto = normalizar_verbo(texto, ["abrir", "abri", "abree", "abres", "abré", "abrí", "abríe"], "abre")
    texto = normalizar_verbo(texto, ["activar", "actibar", "activae", "activá", "actibe", "actibá", "activé"], "activa")
    texto = normalizar_verbo(texto, ["subir", "suba", "subé", "subí", "subíe"], "sube")
    texto = normalizar_verbo(texto, ["bajar", "baja", "bajá", "bajé", "bají", "baje"], "baja")
    texto = normalizar_verbo(texto, ["generar", "genera", "gene", "genere", "genere"], "genera")
    texto = normalizar_verbo(texto, ["crear", "crea", "cree", "creé"], "crea")
    texto = normalizar_verbo(texto, ["planificar", "planifica", "planifique"], "planifica")
    texto = normalizar_verbo(texto, ["estudiar", "estudia", "analiza", "analizar"], "estudia")
    texto = normalizar_verbo(texto, ["vender", "vende", "ventas"], "ventas")
    texto = normalizar_verbo(texto, ["recordar", "recuerda"], "recordar")
    texto = normalizar_verbo(texto, ["enviar", "envía", "envia"], "envia")
    texto = normalizar_verbo(texto, ["programar", "agenda"], "agenda")
    texto = normalizar_verbo(texto, ["calendario", "calendariza"], "calendario")
    texto = normalizar_verbo(texto, ["crear tienda", "crear tiendas"], "crear tienda")
    texto = normalizar_verbo(texto, ["lote contenidos", "lote de contenidos"], "lote contenidos")
    texto = normalizar_verbo(texto, ["configurar", "configura", "configurae", "configurá"], "configura")
    texto = normalizar_verbo(texto, ["activar", "activa", "activá"], "activa")
    # normaliza marcas específicas
    if "actualiza tus faros" in texto:
        texto = texto.replace("actualiza tus faros", "actualiza tus faros")
    if "creaciones milens" in texto:
        texto = texto.replace("creaciones milens", "creaciones milens")
    for variante, canonico in NORMALIZACIONES_COMANDO.items():
        if variante in texto:
            texto = texto.replace(variante, canonico)
    return texto
