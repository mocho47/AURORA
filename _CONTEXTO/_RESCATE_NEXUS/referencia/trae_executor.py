import os
import time
import webbrowser
import sqlite3
from narrador import narrar, establecer_modo_narracion
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, 'marketing')
os.makedirs(OUT_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, 'marketing.db')
APP_NAME = "nexus"
APP_DIR = os.path.join(os.path.expanduser("~"), APP_NAME)
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

def _db_init():
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, tema TEXT, contenido TEXT, ts INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, texto TEXT, ts INTEGER, done INTEGER DEFAULT 0)")
        con.commit()
        con.close()
    except Exception:
        pass

_db_init()

def _load_cfg() -> dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

CFG = _load_cfg()

def ejecutar_comando_trae(comando: str):
    c = (comando or '').lower().strip()
    if not c:
        return
    # Comandos personalizados desde config.json
    try:
        links = CFG.get('enlaces') or CFG.get('custom_links') or {}
        for k, url in (links.items() if isinstance(links, dict) else []):
            if k and (k in c or c == k):
                _abrir_url(url)
                narrar(f"Abriendo {k}")
                return
    except Exception:
        pass
    if 'abre facebook' in c or c == 'facebook':
        _abrir_url('https://facebook.com')
        narrar('Abriendo Facebook')
        return
    if 'abre instagram' in c or c == 'instagram':
        _abrir_url('https://instagram.com')
        narrar('Abriendo Instagram')
        return
    if 'abre tiktok' in c or c == 'tiktok':
        _abrir_url('https://tiktok.com')
        narrar('Abriendo TikTok')
        return
    if 'abre youtube' in c or c == 'youtube':
        _abrir_url('https://youtube.com')
        narrar('Abriendo YouTube')
        return
    if 'abre linkedin' in c or c == 'linkedin':
        _abrir_url('https://www.linkedin.com')
        narrar('Abriendo LinkedIn')
        return
    if 'abre twitter' in c or c == 'twitter':
        _abrir_url('https://twitter.com')
        narrar('Abriendo Twitter')
        return
    if 'activa modo legado' in c:
        establecer_modo_narracion('legado')
        narrar('Modo legado activado')
        return
    if 'activa modo seguro' in c:
        establecer_modo_narracion('seguro')
        narrar('Modo seguro activado')
        return
    if 'activa modo fluido' in c:
        establecer_modo_narracion('fluido')
        narrar('Modo fluido activado')
        return
    if 'mostrar logs' in c:
        _mostrar_logs()
        narrar('Mostrando estado del sistema')
        return
    if ('genera copy' in c) or ('crea copy' in c) or ('copy' in c):
        _generar_copy(c)
        narrar('Copy generado')
        return
    if ('genera hashtag' in c) or ('hashtags' in c) or ('hashtag' in c):
        _generar_hashtags(c)
        narrar('Hashtags generados')
        return
    if ('genera titulo' in c) or ('titulo' in c):
        _generar_titulos(c)
        narrar('Títulos generados')
        return
    if ('genera guion' in c) or ('guion' in c):
        _generar_guion(c)
        narrar('Guion generado')
        return
    if ('plan semanal' in c) or ('plan contenido' in c) or ('planifica' in c):
        _plan_contenido(c)
        narrar('Plan de contenido generado')
        return
    if ('estudio mercado' in c) or ('estudia mercado' in c) or ('analiza mercado' in c):
        _estudio_mercado(c)
        narrar('Estudio de mercado generado')
        return
    if ('plan ventas' in c) or ('ventas' in c):
        _plan_ventas(c)
        narrar('Plan de ventas generado')
        return
    if ('plan anuncios' in c) or ('anuncios' in c):
        _plan_anuncios(c)
        narrar('Plan de anuncios generado')
        return
    if ('brief' in c):
        _generar_brief(c)
        narrar('Brief creativo generado')
        return
    # Configurar/activar marcas y sincronización
    if c.startswith('configura marca') or c.startswith('configurar marca'):
        _configurar_marca(c)
        return
    if c.startswith('activar pagina') or c.startswith('activar página'):
        _configurar_marca(c)
        return
    if ('sincronizar redes' in c) or ('sincroniza redes' in c):
        _sincronizar_redes(c)
        narrar('Guía de sincronización abierta')
        return
    if c.startswith('recordar'):
        _recordar(c)
        narrar('Hecho, lo recordaré')
        return
    if ('recordatorios' in c):
        _listar_recordatorios()
        return
    if ('avanzar proyecto' in c):
        _avanzar_proyecto()
        return
    if ('calendario redes' in c) or ('calendario publicaciones' in c):
        _calendario_publicaciones(c)
        narrar('Calendario de publicaciones generado')
        return
    if ('lote contenidos' in c) or ('lote de contenidos' in c):
        _generar_lote_contenidos(c)
        narrar('Lote de contenidos generado')
        return
    if ('crear tienda' in c):
        _crear_tienda_links()
        narrar('Abriendo creadores de tienda')
        return
    if ('mercadopago' in c) or ('abre mercadopago' in c) or ('mercado pago' in c):
        _abrir_url('https://www.mercadopago.com')
        narrar('Abriendo Mercado Pago')
        return
    if ('aliexpress' in c) or ('ali express' in c) or ('abre aliexpress' in c):
        _abrir_url('https://www.aliexpress.com')
        narrar('Abriendo AliExpress')
        return
    if ('pinterest' in c) or ('abre pinterest' in c):
        _abrir_url('https://www.pinterest.com')
        narrar('Abriendo Pinterest')
        return
    if ('reddit' in c) or ('abre reddit' in c):
        _abrir_url('https://www.reddit.com')
        narrar('Abriendo Reddit')
        return
    if ('telegram' in c) or ('abre telegram' in c):
        _abrir_url('https://web.telegram.org')
        narrar('Abriendo Telegram')
        return
    if ('outlook' in c) or ('hotmail' in c) or ('abre outlook' in c):
        _abrir_url('https://outlook.live.com/mail/')
        narrar('Abriendo Outlook')
        return
    if ('rdw' in c) or ('abre rdw' in c):
        _abrir_url('https://www.rdw.nl')
        narrar('Abriendo RDW')
        return
    if ('tor' in c) or ('dark web' in c):
        _abrir_url('https://www.torproject.org/')
        narrar('Abriendo Tor Project')
        return
    if ('dxf' in c) or ('descarga dxf' in c) or ('dxf download' in c):
        _abrir_url('https://www.google.com/search?q=DXF+download+3+axis')
        narrar('Buscando DXF 3 axis')
        return
    if ('abre gmail' in c) or ('gmail' in c) or ('abre correo' in c) or ('correo' in c) or ('email' in c):
        _abrir_url('https://mail.google.com')
        narrar('Abriendo Gmail')
        return
    if ('abre google' in c) or (c == 'google'):
        _abrir_url('https://www.google.com')
        narrar('Abriendo Google')
        return
    if ('abre maps' in c) or ('maps' in c) or ('abre mapa' in c):
        _abrir_url('https://maps.google.com')
        narrar('Abriendo Maps')
        return
    if ('abre whatsapp' in c) or ('whatsapp' in c) or ('wasap' in c) or ('whatsap' in c):
        _abrir_url('https://web.whatsapp.com')
        narrar('Abriendo WhatsApp')
        return
    if ('abre calendar' in c) or ('calendario' in c):
        _abrir_url('https://calendar.google.com')
        narrar('Abriendo Calendario')
        return
    if ('abre drive' in c) or ('drive' in c):
        _abrir_url('https://drive.google.com')
        narrar('Abriendo Drive')
        return
    if ('abre sheets' in c) or ('hoja de calculo' in c) or ('hojas' in c):
        _abrir_url('https://docs.google.com/spreadsheets')
        narrar('Abriendo Hojas de cálculo')
        return
    if ('abre docs' in c) or ('documentos' in c) or ('documento' in c):
        _abrir_url('https://docs.google.com/document')
        narrar('Abriendo Documentos')
        return
    if ('abre slides' in c) or ('presentaciones' in c):
        _abrir_url('https://docs.google.com/presentation')
        narrar('Abriendo Presentaciones')
        return
    if ('abre meet' in c) or ('meet' in c):
        _abrir_url('https://meet.google.com')
        narrar('Abriendo Meet')
        return
    if ('abre zoom' in c) or ('zoom' in c):
        _abrir_url('https://zoom.us')
        narrar('Abriendo Zoom')
        return
    if ('abre teams' in c) or ('teams' in c):
        _abrir_url('https://teams.microsoft.com')
        narrar('Abriendo Teams')
        return
    if ('abre spotify' in c) or ('spotify' in c):
        _abrir_url('https://open.spotify.com')
        narrar('Abriendo Spotify')
        return
    if ('abre noticias' in c) or ('noticias' in c) or ('news' in c):
        _abrir_url('https://news.google.com')
        narrar('Abriendo Noticias')
        return
    if ('abre banco' in c) or ('banco' in c) or ('banca' in c):
        _abrir_url('https://www.bbva.com')
        narrar('Abriendo Banco')
        return
    if ('abre analytics' in c) or ('analytics' in c):
        _abrir_url('https://analytics.google.com')
        narrar('Abriendo Analytics')
        return
    if ('abre ads' in c) or ('ads' in c) or ('google ads' in c):
        _abrir_url('https://ads.google.com')
        narrar('Abriendo Google Ads')
        return
    if ('facebook ads' in c) or ('adsfacebook' in c):
        _abrir_url('https://business.facebook.com')
        narrar('Abriendo Facebook Ads')
        return
    if ('abre crm' in c) or ('crm' in c):
        _abrir_url('https://app.hubspot.com')
        narrar('Abriendo CRM')
        return
    if ('abre shopify' in c) or ('shopify' in c):
        _abrir_url('https://shopify.com')
        narrar('Abriendo Shopify')
        return
    if ('abre mercado libre' in c) or ('mercadolibre' in c):
        _abrir_url('https://mercadolibre.com')
        narrar('Abriendo Mercado Libre')
        return
    if ('abre explorador' in c) or ('explorador' in c):
        try:
            os.startfile(os.path.expanduser('~'))
        except Exception:
            pass
        narrar('Abriendo Explorador')
        return
    if ('abre navegador' in c) or ('navegador' in c) or ('chrome' in c) or ('edge' in c):
        _abrir_url('https://www.google.com')
        narrar('Abriendo Navegador')
        return
    if ('abre bloc de notas' in c) or ('notepad' in c):
        try:
            os.system('start notepad')
        except Exception:
            pass
        narrar('Abriendo Bloc de notas')
        return
    if ('abre calculadora' in c) or ('calculadora' in c):
        try:
            os.system('start calc')
        except Exception:
            pass
        narrar('Abriendo Calculadora')
        return
    if ('genera factura' in c) or ('factura' in c) or ('facturación' in c):
        _guardar_texto('factura', 'Factura preliminar: cliente, items, subtotal, impuestos, total')
        narrar('Factura generada')
        return
    if ('reporte ventas' in c) or ('reporte inventario' in c) or ('reporte finanzas' in c) or ('informe' in c) or ('reporte' in c):
        _guardar_texto('reporte', 'Reporte: ventas, inventario y finanzas con KPIs básicos')
        narrar('Reporte generado')
        return
    if ('lista precios' in c) or ('precio' in c):
        _guardar_texto('precios', 'Lista de precios: producto, precio, promo, notas')
        narrar('Lista de precios generada')
        return
    if ('clientes' in c):
        _guardar_texto('clientes', 'Clientes: nombre, contacto, status, próxima acción')
        narrar('Listado de clientes generado')
        return
    if ('proveedores' in c):
        _guardar_texto('proveedores', 'Proveedores: nombre, insumos, condiciones, notas')
        narrar('Listado de proveedores generado')
        return
    if ('nexus info' in c) or ('que es nexus' in c) or ('qué es nexus' in c):
        _nexus_info()
        narrar('Nexus explicado')
        return
    if ('nexus titulos' in c) or ('titulos nexus' in c) or ('títulos nexus' in c):
        _nexus_titulos()
        narrar('Títulos de Nexus generados')
        return
    narrar('Comando no reconocido')

def _abrir_url(url: str):
    import webbrowser
    try:
        webbrowser.open(url, new=2)
    except Exception:
        pass

def _mostrar_logs():
    try:
        path = os.path.join(BASE_DIR, 'logs', 'voice.log')
        os.startfile(path)
    except Exception:
        pass

def _crear_tienda_links():
    # Abre páginas de creación de tiendas y marketplaces populares
    for url in [
        'https://www.shopify.com/start',
        'https://www.mercadolibre.com.ar/publicar',
        'https://sellercentral.amazon.com',
        'https://seller.alibaba.com',
    ]:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass

def _guardar_texto(nombre: str, contenido: str):
    ts = int(time.time())
    fname = f"{nombre}_{ts}.txt"
    path = os.path.join(OUT_DIR, fname)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        os.startfile(path)
    except Exception:
        pass
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("INSERT INTO items (tipo, tema, contenido, ts) VALUES (?, ?, ?, ?)", (nombre, _extract_topic_from_content(contenido), contenido, ts))
        con.commit()
        con.close()
    except Exception:
        pass

def _extract_topic_from_content(contenido: str) -> str:
    t = contenido.split('\n', 1)[0]
    return (t or 'tema').strip()

def _extraer_tema(c: str) -> str:
    k = c.replace('genera', '').replace('crea', '').replace('copy', '').replace('guion', '').replace('titulo', '').replace('hashtags', '').replace('hashtag', '').strip()
    if not k:
        return 'campaña'
    return k

def _guardar_brand(nombre: str, email: str = ''):
    nombre = (nombre or '').strip()
    if not nombre:
        return
    try:
        cfg = _load_cfg()
        brands = cfg.get('brands', {})
        b = brands.get(nombre, {})
        if (not email) and nombre == 'actualiza tus faros':
            email = 'anuarm17@gmail.com'
        if (not email) and nombre == 'creaciones milens':
            email = 'rocio3enciso@gmail.com'
        b.setdefault('email', email or b.get('email', ''))
        b.setdefault('fb_page_id', b.get('fb_page_id', ''))
        b.setdefault('ig_account_id', b.get('ig_account_id', ''))
        b.setdefault('fb_token', b.get('fb_token', ''))
        b.setdefault('ig_token', b.get('ig_token', ''))
        b['status'] = 'pendiente'
        brands[nombre] = b
        cfg['brands'] = brands
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    except Exception:
        pass

def _configurar_marca(c: str):
    t = c
    for k in ['configura marca', 'configurar marca', 'activar pagina', 'activar página']:
        if k in t:
            t = t.replace(k, '')
    nombre = t.strip()
    if not nombre:
        nombre = 'actualiza tus faros'
    _guardar_brand(nombre)
    pasos = [
        f"Marca: {nombre}",
        "1) Crear/activar la Página de Facebook",
        "2) Convertir Instagram a cuenta profesional y vincular a la Página",
        "3) Crear App en Facebook Developers y generar tokens con permisos",
        "4) Obtener Page ID y Instagram Business ID",
        "5) Probar publicación con Graph API",
    ]
    _guardar_texto('setup_marca', '\n'.join(pasos))
    # Abrir recursos
    for url in [
        'https://www.facebook.com/pages/create/',
        'https://business.facebook.com/',
        'https://developers.facebook.com/apps/',
        'https://developers.facebook.com/docs/graph-api',
        'https://developers.facebook.com/docs/instagram-api',
    ]:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass
    narrar('Guía y enlaces de configuración abiertos')

def _sincronizar_redes(c: str):
    try:
        for url in [
            'https://www.facebook.com/business/help/316494535442142?id=735435806053126',
            'https://help.instagram.com/570318403107710',
            'https://business.facebook.com/latest/settings/linked_accounts',
        ]:
            webbrowser.open(url, new=2)
    except Exception:
        pass

def _cerrar_sesion():
    try:
        os._exit(0)
    except Exception:
        pass

def _generar_manual():
    _guardar_texto('manual', 'Manual no disponible en esta edición')

def _activar_comandos_sociales():
    _guardar_texto('social', 'Comandos sociales listos')

def _generar_copy(c: str):
    tema = _extraer_tema(c)
    base = [
        f"Descubre {tema} y potencia tu marca.",
        f"{tema.capitalize()} que convierte: dale clic y actúa.",
        f"Haz crecer tu comunidad con {tema} hoy mismo.",
    ]
    base += _ajustar_industria_lineas(tema, 'copy')
    _guardar_texto('copy', '\n'.join(base))

def _generar_hashtags(c: str):
    tema = _extraer_tema(c).replace(' ', '')
    hs = [f"#{tema}", f"#{tema}Tips", f"#{tema}2025", f"#{tema}Growth", f"#{tema}Viral"]
    _guardar_texto('hashtags', ' '.join(hs))

def _generar_titulos(c: str):
    tema = _extraer_tema(c)
    ts = [
        f"{tema.capitalize()}: 7 claves para crecer",
        f"Cómo dominar {tema} en 24 horas",
        f"El error #1 en {tema} y cómo evitarlo",
    ]
    ts += _ajustar_industria_lineas(tema, 'titulos')
    _guardar_texto('titulos', '\n'.join(ts))

def _generar_guion(c: str):
    tema = _extraer_tema(c)
    g = [
        "Hook: pregunta directa al dolor.",
        f"Contexto: por qué {tema} importa.",
        "Valor: 3 tips accionables.",
        "CTA: suscríbete y comparte.",
    ]
    _guardar_texto('guion', '\n'.join(g))

def _nexus_info():
    desc = [
        "Nexus es un asistente empresarial autónomo.",
        "Escucha tu voz, entiende tus órdenes y ejecuta acciones útiles.",
        "Funciona como panel de control para tu operación diaria.",
        "Automatiza publicaciones, apertura de herramientas y generación de contenidos.",
        "Se integra con tus marcas y simplifica flujos con preguntas simples de sí/no.",
        "Diseñado para que no tengas que revisar nada: confirma y listo.",
    ]
    _guardar_texto('nexus', '\n'.join(desc))

def _nexus_titulos():
    ts = [
        "Nexus: asistente empresarial autónomo",
        "Nexus: sistema de automatización por voz",
        "Nexus: panel de control de tu negocio",
        "Nexus: orquestador de contenidos y campañas",
        "Nexus: copiloto para ventas y marketing",
        "Nexus: flujo simple, resultados reales",
        "Nexus: ejecuta por ti, confirma y listo",
        "Nexus: publica, mide y optimiza",
        "Nexus: activa marcas y sincroniza redes",
        "Nexus: gestión diaria sin fricción",
        "Nexus: productividad que se vende sola",
        "Nexus: impulsa tu negocio con voz",
    ]
    _guardar_texto('nexus_titulos', '\n'.join(ts))

def _plan_contenido(c: str):
    tema = _extraer_tema(c)
    plan = [
        f"Lunes: historia de marca sobre {tema}",
        f"Martes: reel tip rápido de {tema}",
        f"Miércoles: carrusel educativo de {tema}",
        f"Jueves: testimonio aplicando {tema}",
        f"Viernes: directo Q&A de {tema}",
        "Sábado: resumen semanal",
        "Domingo: teaser de la próxima semana",
    ]
    plan += _ajustar_industria_lineas(tema, 'plan')
    _guardar_texto('plan', '\n'.join(plan))

def _calendario_publicaciones(c: str):
    tema = _extraer_tema(c)
    dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    slots = ['Mañana','Tarde','Noche']
    filas = ["día,franja,formato,título,copy,hashtag"]
    base_hashtag = tema.replace(' ', '') or 'marca'
    for d in dias:
        for s in slots:
            formato = 'reel' if s=='Tarde' else ('post' if s=='Mañana' else 'story')
            titulo = f"{tema.capitalize()} - {d} {s}"
            copy = f"Tip de {tema}: acción simple para hoy."
            hashtag = f"#{base_hashtag} #{base_hashtag}Tips #{base_hashtag}2025"
            filas.append(f"{d},{s},{formato},{titulo},{copy},{hashtag}")
    try:
        ts = int(time.time())
        path = os.path.join(OUT_DIR, f"calendario_{ts}.csv")
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filas))
        os.startfile(path)
    except Exception:
        pass

def _generar_lote_contenidos(c: str):
    tema = _extraer_tema(c)
    piezas = []
    for i in range(1, 31):
        titulo = f"{tema.capitalize()} #{i}: idea clave"
        copy = f"{tema} — Punto #{i}: beneficio + CTA."
        hashtags = f"#{tema.replace(' ', '')} #{tema.replace(' ', '')}Growth #{tema.replace(' ', '')}Viral"
        piezas.append(f"{titulo}\n{copy}\n{hashtags}\n")
    _guardar_texto('lote', '\n\n'.join(piezas))

def _estudio_mercado(c: str):
    tema = _extraer_tema(c)
    contenido = []
    contenido.append(f"Producto/Servicio: {tema}")
    contenido.append("Segmentos: primario, secundario, nichos")
    contenido.append("Buyer persona: perfil, objetivos, dolor")
    contenido.append("Competencia: top 5, ventajas, brechas")
    contenido.append("Propuesta de valor: diferenciadores claros")
    contenido.append("Precio: referencia de mercado y estrategia")
    contenido.append("Canales: orgánico, pago, partnership")
    contenido.append("SWOT: fortalezas, oportunidades, debilidades, amenazas")
    contenido.append("KPIs: alcance, leads, conversión, LTV, CAC")
    contenido.append("Plan de acción: 4 semanas, tareas concretas")
    contenido += _ajustar_industria_lineas(tema, 'estudio')
    _guardar_texto('estudio', '\n'.join(contenido))

def _plan_ventas(c: str):
    tema = _extraer_tema(c)
    contenido = []
    contenido.append(f"Meta: ventas {tema} trimestral")
    contenido.append("Funnel: awareness → interés → decisión → compra")
    contenido.append("Actividades: llamadas, demos, follow-ups, campañas")
    contenido.append("Script: apertura, valor, manejo de objeciones, cierre")
    contenido.append("Calendario: semanal por equipo y canal")
    contenido.append("KPIs: tasa respuesta, demos, cierre, ticket medio")
    contenido.append("Herramientas: CRM local, automatizaciones básicas")
    contenido += _ajustar_industria_lineas(tema, 'ventas')
    _guardar_texto('ventas', '\n'.join(contenido))

def _plan_anuncios(c: str):
    tema = _extraer_tema(c)
    contenido = []
    contenido.append(f"Campaña: {tema}")
    contenido.append("Canales: Meta Ads, Google Ads, TikTok Ads")
    contenido.append("Segmentación: intereses, lookalike, retargeting")
    contenido.append("Creatividades: imagen, video corto, carrusel")
    contenido.append("Presupuesto: diario y tope mensual")
    contenido.append("KPIs: CTR, CPC, CPA, ROAS")
    contenido.append("Iteración: pruebas A/B y optimización semanal")
    contenido += _ajustar_industria_lineas(tema, 'anuncios')
    _guardar_texto('anuncios', '\n'.join(contenido))

def _generar_brief(c: str):
    tema = _extraer_tema(c)
    contenido = []
    contenido.append(f"Objetivo: {tema}")
    contenido.append("Público: perfil y necesidades")
    contenido.append("Propuesta: mensaje clave y tono")
    contenido.append("Entregables: piezas, formatos, fechas")
    contenido.append("Restricciones: marca y legales")
    contenido.append("Métricas: éxito esperado y revisión")
    contenido += _ajustar_industria_lineas(tema, 'brief')
    _guardar_texto('brief', '\n'.join(contenido))

def _ajustar_industria_lineas(tema: str, tipo: str):
    t = (tema or '').lower()
    res = []
    if 'corte laser' in t:
        if tipo in ('anuncios','ventas','brief','estudio','plan','titulos','copy'):
            res += [
                'Máquinas y materiales: CO2, fibra, acrílico, MDF',
                'Casos de uso: señalética, decoración, prototipado',
                'Oferta: precisión, velocidad y personalización',
            ]
    if 'sublimacion' in t:
        if tipo in ('anuncios','ventas','brief','estudio','plan','titulos','copy'):
            res += [
                'Productos: tazas, textiles, promocionales',
                'Temporadas: back to school, navidad, eventos',
                'Diferenciador: calidad de impresión y tiempos de entrega',
            ]
    if 'iluminacion automotriz' in t or 'iluminación automotriz' in t:
        if tipo in ('anuncios','ventas','brief','estudio','plan','titulos','copy'):
            res += [
                'Segmentos: entusiastas, flotillas, seguridad',
                'Regulación: homologación y garantías',
                'Beneficio: visibilidad, estética y durabilidad',
            ]
    return res

def limpiar_duplicados_marketing():
    import hashlib
    seen = {}
    removed = []
    for f in os.listdir(OUT_DIR):
        p = os.path.join(OUT_DIR, f)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, 'rb') as fh:
                h = hashlib.sha256(fh.read()).hexdigest()
            if h in seen:
                try:
                    os.remove(p)
                    removed.append(f)
                except Exception:
                    pass
            else:
                seen[h] = f
        except Exception:
            pass
    if removed:
        try:
            _guardar_texto('dedup', '\n'.join(removed))
        except Exception:
            pass

def _recordar(c: str):
    texto = c.replace('recordar', '').strip()
    if not texto:
        texto = 'tarea pendiente'
    ts = int(time.time())
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("INSERT INTO reminders (texto, ts, done) VALUES (?, ?, 0)", (texto, ts))
        con.commit()
        con.close()
    except Exception:
        pass

def _listar_recordatorios():
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, texto, done FROM reminders ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        con.close()
        texto = []
        for r in rows:
            estado = 'hecho' if r[2] else 'pendiente'
            texto.append(f"[{estado}] {r[0]}: {r[1]}")
        _guardar_texto('recordatorios', '\n'.join(texto) or 'sin recordatorios')
    except Exception:
        pass

def _avanzar_proyecto():
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT tipo, tema FROM items ORDER BY ts DESC LIMIT 50")
        items = cur.fetchall()
        con.close()
        pasos = []
        if any(t[0] == 'estudio' for t in items):
            pasos.append('Refinar propuesta de valor y pricing')
        if any(t[0] == 'plan' for t in items):
            pasos.append('Calendarizar publicaciones y responsables')
        if any(t[0] == 'ventas' for t in items):
            pasos.append('Activar CRM y secuencias de contacto')
        if any(t[0] == 'copy' for t in items):
            pasos.append('Probar A/B en copies y landings')
        if not pasos:
            pasos = ['Generar estudio mercado', 'Crear plan de contenido', 'Definir plan de ventas']
        _guardar_texto('proyecto', '\n'.join(pasos))
        narrar('Siguiente paso definido')
    except Exception:
        pass
