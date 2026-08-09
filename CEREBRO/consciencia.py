# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║              🧠 AURORA — CONSCIENCIA CENTRAL                         ║
║  Pipeline cognitivo completo: percibir→recordar→enrutar→             ║
║  ejecutar→sintetizar→aprender. Sin censura. Sin simulaciones.        ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/CEREBRO/consciencia.py
"""
import asyncio, importlib, json, logging, os, re, time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from groq import AsyncGroq

ROOT = Path(__file__).parent.parent
logger = logging.getLogger("aurora.consciencia")

# ── Respaldo LOCAL sin internet (Ollama) ──────────────────────────────
# Modelo local que responde cuando Groq/nube falla (WiFi caído, 401, timeout).
# Lento pero garantiza UNA respuesta al usuario en vez de un error.
_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
_OLLAMA_MODELO = "llama3.2:3b"

def _llm_local_sync(messages: list) -> str:
    """Respaldo LOCAL sin internet (Ollama). Bloqueante — llamar vía asyncio.to_thread."""
    r = requests.post(
        _OLLAMA_URL,
        json={"model": _OLLAMA_MODELO, "messages": messages, "stream": False},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]

# ── Cartuchos externos cacheados (Web real + Biblioteca/RAG) ──────────
_WEB_REAL_MOD = None
def _web_real():
    global _WEB_REAL_MOD
    if _WEB_REAL_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("web_real", ROOT / "WEB" / "web_real.py")
        _WEB_REAL_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_WEB_REAL_MOD)
    return _WEB_REAL_MOD

_BIB_MOD = None
def _biblioteca():
    global _BIB_MOD
    if _BIB_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("biblioteca", ROOT / "BIBLIOTECA" / "biblioteca.py")
        _BIB_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_BIB_MOD)
    return _BIB_MOD

_RAZONADOR_MOD = None
def _razonador():
    global _RAZONADOR_MOD
    if _RAZONADOR_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("razonador", ROOT / "CEREBRO" / "razonador.py")
        _RAZONADOR_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_RAZONADOR_MOD)
    return _RAZONADOR_MOD

_COTSERV_MOD = None
def _cotserv():
    global _COTSERV_MOD
    if _COTSERV_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("cotizador_servicios", ROOT / "TALLER" / "cotizador_servicios.py")
        _COTSERV_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_COTSERV_MOD)
    return _COTSERV_MOD

_PUBINT_MOD = None
def _pubint():
    global _PUBINT_MOD
    if _PUBINT_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("publicacion_inteligente", ROOT / "MARKETING" / "publicacion_inteligente.py")
        _PUBINT_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_PUBINT_MOD)
    return _PUBINT_MOD

_AGENDA_MOD = None
def _agenda():
    global _AGENDA_MOD
    if _AGENDA_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("agenda", ROOT / "AGENDA" / "agenda.py")
        _AGENDA_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_AGENDA_MOD)
    return _AGENDA_MOD

_VENDEDOR_MOD = None
def _vendedor():
    global _VENDEDOR_MOD
    if _VENDEDOR_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("vendedor_core", ROOT / "VENDEDOR" / "vendedor_core.py")
        _VENDEDOR_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_VENDEDOR_MOD)
    return _VENDEDOR_MOD

_EQUIPOS_MOD = None
def _equipos():
    global _EQUIPOS_MOD
    if _EQUIPOS_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("equipos", ROOT / "CEREBRO" / "equipos.py")
        _EQUIPOS_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_EQUIPOS_MOD)
    return _EQUIPOS_MOD

_FABAG_MOD = None
def _fab_agentes():
    global _FABAG_MOD
    if _FABAG_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("fabrica_agentes", ROOT / "CEREBRO" / "fabrica_agentes.py")
        _FABAG_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_FABAG_MOD)
    return _FABAG_MOD

_REGISTRO_MOD = None
def _registro():
    global _REGISTRO_MOD
    if _REGISTRO_MOD is None:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("registro_herramientas", ROOT / "CEREBRO" / "registro_herramientas.py")
        _REGISTRO_MOD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_REGISTRO_MOD)
    return _REGISTRO_MOD


def _contexto_catalogo(mensaje: str) -> str:
    """Si preguntan precio, devuelve los precios REALES del catálogo Milens que casen
    con el mensaje — para que chat y WhatsApp coticen EXACTO (no inventen)."""
    try:
        import unicodedata as _ud
        def _n(s): return "".join(c for c in _ud.normalize("NFD", (s or "").lower())
                                   if _ud.category(c) != "Mn")
        mn = _n(mensaje)
        if not any(k in mn for k in ("precio", "cuesta", "cuanto", "cotiz", "vale", "cobran")):
            return ""
        items = _cotserv().catalogo_plano().get("items", [])
        palabras = [w for w in mn.split() if len(w) > 3]
        hits = []
        for it in items:
            nn = _n(it.get("nombre", ""))
            if any(w in nn for w in palabras):
                esc = it.get("escalas")
                if esc:
                    pr = ", ".join(f"{e['desde']}+pz ${e['precio']}" for e in esc)
                else:
                    pr = f"${it.get('precio')}"
                hits.append(f"- {it['nombre']}: {pr}")
        if not hits:
            return ""
        return ("PRECIOS REALES del catálogo Milens (usa EXACTAMENTE estos, NO inventes):\n"
                + "\n".join(hits[:12]))
    except Exception:
        return ""

# ── Heurística: ¿la pregunta amerita el razonador profundo? ────────────
_TRIGGERS_PROFUNDOS = (
    "analiza", "conviene", "compara", "estrategia", "recomienda", "recomiendas",
    "decidir", "evalua", "por que", "cual es mejor", "cuanto me conviene",
    "que me conviene", "plan para", "razona", "piensa bien",
)
def _es_pregunta_profunda(mensaje: str) -> bool:
    """True si el mensaje pide análisis/decisión profunda o es muy largo."""
    if not mensaje:
        return False
    if len(mensaje) > 180:
        return True
    import unicodedata
    m = "".join(c for c in unicodedata.normalize("NFD", mensaje.lower())
                if unicodedata.category(c) != "Mn")
    return any(t in m for t in _TRIGGERS_PROFUNDOS)

# ── Detección de acción física (para no simular) ───────────────────────
# Verbos imperativos que implican TOCAR el sistema/archivos. Si el chat no tiene
# la acción realmente conectada, debe responder honesto — nunca fingir que la hizo.
_ACCION_FISICA_TRIGGERS = (
    "mueve", "muevelo", "mover", "copia", "copialo", "copiar", "borra", "borrar",
    "elimina", "eliminar", "renombra", "renombrar", "instala", "instalar",
    "desinstala", "desinstalar", "repara", "reparar", "limpia cache", "limpiar cache",
    "vacia cache", "borra cache", "manda a la pc", "envia a la pc", "pasa a la pc",
    "mandale a", "pasalo a la", "descarga e instala",
    # Corel: reparar su conexion (cache corrupto de win32com). Frases COMPLETAS
    # a proposito — poner "arregla" suelto desviaria mensajes de otros dominios
    # al manejador de acciones fisicas (agregado 2026-07-29).
    "arregla corel", "arregla corell", "arregla la conexion con corel",
    "corel no responde", "corell no responde", "corel no conecta",
    # WhatsApp — enviar mensajes reales (nunca simular una conversación)
    "manda un whatsapp", "mandale un whatsapp", "envia un whatsapp", "enviale un whatsapp",
    "manda whatsapp", "envia whatsapp", "mensaje de whatsapp", "por whatsapp",
    "entra a mi conversacion", "entra a la conversacion", "mandale un saludo",
    "escribele por whatsapp", "contactalo por whatsapp",
)
# Motores que SÍ ejecutan acciones reales en el sistema.
_MOTORES_EJECUTORES = {"pc_cmd", "self_repair"}


def _es_accion_fisica(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _ACCION_FISICA_TRIGGERS)


# ── LA RED DE SEGURIDAD, POR SEÑALES PROPIAS ─────────────────────────────────
# Antes esta función era la UNIÓN DE LOS CANDADOS: si ninguno calzaba, decía que
# el mensaje "no era operativo" y dejaba que motor_analisis contestara lo que
# quisiera. Era circular — la red de seguridad tenía exactamente el mismo agujero
# que aquello que debía cubrir.
#
# El barrido del 2026-08-02 lo probó con números: de 40 frases reales de Anuar,
# TODAS las que cayeron en motor_analisis fallaron o mintieron (tardando 20-70 s),
# y TODAS las que agarró un candado respondieron bien en menos de 3 s.
# "hazme un corte de caja de ayer" acabó explicándole cómo cortar una caja de MDF
# en la láser, teniendo la contabilidad real a un segundo de distancia.
#
# Ahora se reconoce la intención por señales PROPIAS, no por los candados. Da
# igual cómo esté escrita la frase: si pide algo real, motor_analisis no la
# contesta solo.
_VERBOS_DE_ACCION = (
    "haz", "hazme", "hazlo", "abre", "abreme", "cierra", "convierte", "conviertelo",
    "exporta", "guarda", "manda", "mandale", "envia", "enviale", "publica",
    "cotiza", "cotizame", "agenda", "agendame", "busca", "buscame", "investiga",
    "vectoriza", "escala", "imprime", "descarga", "instala", "edita", "modifica",
    "corrige", "arregla", "borra", "mueve", "copia", "genera", "generame",
    "crea", "creame", "calcula", "calculame", "dame", "pasame", "muestrame",
    "ensename", "revisa", "checa", "chekame", "prende", "apaga", "corre", "ejecuta",
    # Vocabulario de taller. Caso real 2026-08-03: "extrae el mapa de bits" no
    # traía ningún verbo conocido, así que no contaba como intención operativa,
    # ningún candado la agarró y la contestó motor_analisis — un modelo sin
    # manos, que respondió "no puedo ejecutar acciones físicas en la PC" DOS
    # mensajes después de haber importado la imagen a Corel de verdad.
    "extrae", "extraeme", "extraelo", "saca", "sacame", "sacale", "sacalo",
    "traza", "trazalo", "rasteriza", "importa", "importame", "recorta",
    "voltea", "gira", "rota", "quita", "quitale", "limpia", "mide", "cuenta",
    "lista", "listame", "prepara", "preparame", "separa", "junta", "une",
    "alinea", "duplica", "renombra", "comprime", "sube", "baja", "pasa",
    "pasalo", "aplica", "aplicale", "marca", "registra", "actualiza",
    "elimina", "agrega", "agregale", "analiza", "verifica", "repara",
    "escanea", "configura", "aprueba", "resume", "olvida", "construye",
)

# Los verbos de arriba se escriben a mano porque son la forma en que habla
# Anuar. Estos otros salen SOLOS del registro real de herramientas: cuando
# nace una herramienta nueva, su verbo entra aquí sin que nadie lo agregue.
# Esa es la diferencia entre tapar el hueco de hoy y cerrar la fuente de
# huecos: la lista a mano siempre se va a quedar corta.
_VERBOS_PLOMERIA = frozenset((
    "get", "set", "init", "main", "health", "execute", "login", "create",
    "add", "update", "delete", "run", "test", "load", "save", "build",
    "por", "prompt", "ficha", "contexto", "formatos", "ejemplo", "info",
    "estado", "catalogo", "disponible", "pdf", "generate", "resumen",
))
_verbos_registro_cache: Optional[frozenset] = None


def _verbos_del_registro() -> frozenset:
    """Verbos en infinitivo sacados de los nombres reales de las herramientas.

    Se calcula una sola vez. Si el registro no carga, se sigue con la lista
    escrita a mano: nunca se cae por esto.
    """
    global _verbos_registro_cache
    if _verbos_registro_cache is not None:
        return _verbos_registro_cache
    verbos = set()
    try:
        for clave in _registro().descubrir():
            # Las claves vienen como "carpeta/modulo:funcion", y algunas traen
            # además la clase pegada ("AnaliticaMarketing.actualizar"): se parte
            # por los dos, si no se guardan verbos que nadie va a escribir nunca.
            fn = clave.split(":")[-1].split(".")[-1].lstrip("_").lower()
            v = fn.split("_")[0]
            # Solo infinitivos reales: 4+ letras y terminación de verbo.
            if len(v) >= 4 and v.endswith(("ar", "er", "ir")) and v not in _VERBOS_PLOMERIA:
                verbos.add(v)
    except Exception as e:  # el registro es opcional para esta comprobación
        logger.debug(f"[VERBOS] No pude leer el registro ({e}); uso solo la lista fija.")
    _verbos_registro_cache = frozenset(verbos)
    return _verbos_registro_cache
_DATOS_DEL_NEGOCIO = (
    "precio", "cuanto cuesta", "cuanto sale", "cuanto vale", "cotizacion",
    "venta", "ventas", "vendido", "factura", "caja", "ingreso", "utilidad",
    "ganancia", "cobrar", "anticipo", "saldo", "orden", "ordenes", "cliente",
    "clientes", "cita", "citas", "agenda", "inventario", "existencia", "stock",
    "lead", "leads", "contabilidad", "corte",
)


def _es_intencion_operativa(mensaje: str) -> bool:
    """True si el mensaje pide algo REAL: una acción, o un dato del negocio.

    No depende de los candados a propósito. Si dependiera, volvería a fallar
    exactamente donde ellos fallan.
    """
    if not mensaje:
        return False
    m = _norm_txt(mensaje)

    # Una ruta, un archivo o un programa: siempre es operativo.
    if re.search(r"[A-Za-z]:\\", mensaje or ""):
        return True
    if re.search(r"\.\w{2,4}\b", m) and _contiene_trigger(m, ("archivo", "abre", "convierte",
                                                              "vectoriza", "exporta", "edita")):
        return True
    # Un verbo de acción al principio: "hazme...", "cotizame...", "abre..."
    palabras = m.split()
    if palabras and palabras[0] in _VERBOS_DE_ACCION:
        return True
    if _contiene_trigger(m, _VERBOS_DE_ACCION) and len(palabras) <= 12:
        return True
    # Un verbo que existe de verdad en alguna de las 535 herramientas, dicho en
    # infinitivo ("quiero extraer...", "puedes convertir..."). Así el próximo
    # verbo que nadie previó ya no cae en motor_analisis.
    if palabras and _verbos_del_registro().intersection(palabras):
        return True
    # Pregunta por un dato del negocio: son datos que están en las bases, no
    # opiniones que se puedan redactar.
    if _contiene_trigger(m, _DATOS_DEL_NEGOCIO):
        return True
    # Y lo que ya se sabía operativo por los candados, se conserva.
    return (
        _es_busqueda_web(mensaje)
        or _es_comando_corel(mensaje)
        or _es_conversion_dxf(mensaje)
        or _es_accion_fisica(mensaje)
        or _es_consulta_codigo(mensaje)
        or _es_editar_codigo(mensaje)
        or _es_agenda(mensaje)
        or _es_consulta_negocio(mensaje)
        or _es_servicio_atf(mensaje)
    )


_PERFIL_MOD = None


def _perfil():
    """El perfil de cómo escribe Anuar, cargado una sola vez."""
    global _PERFIL_MOD
    if _PERFIL_MOD is None:
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "perfil_anuar", ROOT / "CEREBRO" / "perfil_anuar.py")
            _PERFIL_MOD = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_PERFIL_MOD)
        except Exception as e:
            logger.debug(f"[PERFIL] no se pudo cargar ({e}); se sigue sin él.")
            _PERFIL_MOD = False
    return _PERFIL_MOD


def _norm_txt(mensaje: str) -> str:
    # El perfil de Anuar va PRIMERO: corrige su forma real de escribir antes de
    # que ningún candado la vea. Se cargó de una vez con 72 peticiones reales
    # suyas, en vez de agregar tres frases cada vez que un bug las delataba
    # (2026-08-05, él lo señaló: "¿por qué no has enseñado a AURORA a
    # entenderme, si tú puedes mostrarle cómo lo haría yo?").
    p = _perfil()
    if p:
        try:
            mensaje = p.normaliza(mensaje)
        except Exception:
            pass

    import unicodedata as _ud
    m = "".join(c for c in _ud.normalize("NFD", (mensaje or "").lower()) if _ud.category(c) != "Mn")
    # Variantes reales de escritura rápida/errores frecuentes del chat.
    reemplazos = {
        "coreldrau": "coreldraw",
        "corel draw": "coreldraw",
        "corell": "corel",
        "vektor": "vector",
        "wasap": "whatsapp",
        "watsap": "whatsapp",
        "kiero": "quiero",
        "xfa": "porfa",
    }
    for viejo, nuevo in reemplazos.items():
        m = m.replace(viejo, nuevo)
    return " ".join(m.split())


async def _corel_con_timeout(fn, *args, timeout: float = 25.0):
    """Envuelve una llamada real a Corel (COM, bloqueante) con un límite de tiempo
    real. Encontrado en vivo 2026-07-27: si CorelDRAW no está listo/abierto o se
    queda esperando un diálogo, la llamada se cuelga para siempre — y como el chat
    corre con un solo worker, eso bloquea TODO el sistema para cualquier usuario
    (síntoma real: "no ha podido hacer nada en todo el día"). Ahora se rinde
    honesto en vez de colgar el sistema entero."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout)
    except asyncio.TimeoutError:
        return {"status": "timeout",
                "detalle": f"CorelDRAW no respondió en {timeout:.0f}s — revisa que esté abierto de verdad y sin ningún diálogo pendiente en pantalla."}


_SUFIJOS_CLITICOS = (
    "selo", "sela", "selos", "selas", "melo", "mela", "melos", "melas",
    "noslo", "nosla", "noslos", "noslas", "lo", "la", "los", "las", "le", "les", "se",
)


def _contiene_trigger(m: str, triggers) -> bool:
    """Coincidencia de trigger sin falsos positivos por substring en palabras sueltas
    (ej. 'borra' no debe matchear dentro de 'borrador', 'mueve' no dentro de 'conmueve').
    Sí reconoce el mismo verbo con un pronombre pegado al final ('guardarlo',
    'ábrelo', 'combínalo') como la misma palabra — encontrado en vivo 2026-07-27:
    exigir coincidencia EXACTA de palabra completa hacía que formas muy naturales
    en español ('podrías guardarlo') no calzaran con ningún trigger y el mensaje
    se fuera al enrutador de IA, que a veces inventa en vez de admitir que no
    reconoce el pedido. Frases de varias palabras siguen usando substring (no hay
    riesgo real de colisión ahí — nadie escribe 'manda a la pc' por accidente
    dentro de otra palabra)."""
    import re as _re
    sufijos = "|".join(_SUFIJOS_CLITICOS)
    for t in triggers:
        if " " in t:
            if t in m:
                return True
        elif _re.search(rf"\b{_re.escape(t)}(?:{sufijos})?\b", m):
            return True
    return False


# ── Abrir una URL/página real en el navegador (distinto de buscar EN la web) ──
# Encontrado en vivo 2026-07-27: "busca la pagina ameede.com y dejala abierta en
# el navegador" caía en busqueda_web (por "busca en la web") y hacía una búsqueda
# de palabras clave sobre "ameede.com" en vez de navegar directo — resultados de
# ayuda de Google totalmente ajenos. Si el mensaje trae un dominio real (algo.tld)
# Y pide dejarlo abierto en el navegador, gana la navegación directa.
_DOMINIO_RE = re.compile(
    r"\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:com|mx|net|org|io|co|info|app|dev|"
    r"gob\.mx|edu\.mx|com\.mx)\b", re.I)
_ABRIR_NAVEGADOR_TRIGGERS = (
    "navegador", "chrome", "abrela", "abrelo", "dejala abierta", "dejalo abierto",
    "dejarla abierta", "dejarlo abierto", "abre la pagina", "abrir la pagina",
)


# Sitios que se nombran sin decir el dominio. Nadie dice "abre youtube.com":
# dice "abre youtube". Anuar, 2026-08-02: "no abre youtube ni páginas, no es un
# navegador". Sí lo era — solo que exigía el punto-com para reconocerlo.
_SITIOS_CONOCIDOS = {
    "youtube": "https://www.youtube.com", "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com", "tiktok": "https://www.tiktok.com",
    "whatsapp": "https://web.whatsapp.com", "gmail": "https://mail.google.com",
    "correo": "https://mail.google.com", "drive": "https://drive.google.com",
    "mercadolibre": "https://www.mercadolibre.com.mx", "meli": "https://www.mercadolibre.com.mx",
    "amazon": "https://www.amazon.com.mx", "google": "https://www.google.com",
    "maps": "https://maps.google.com", "chatgpt": "https://chat.openai.com",
    "github": "https://github.com", "aliexpress": "https://es.aliexpress.com",
    "temu": "https://www.temu.com", "shein": "https://mx.shein.com",
    "canva": "https://www.canva.com", "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com", "linkedin": "https://www.linkedin.com",
    "twitter": "https://x.com", "x": "https://x.com",
    # Agregados el 2026-08-05: buscar referencias de diseño es parte del trabajo
    # diario, y Pinterest ni siquiera se podía abrir.
    "pinterest": "https://www.pinterest.com.mx", "etsy": "https://www.etsy.com",
    "lideart": "https://lideart.com.mx", "behance": "https://www.behance.net",
    "freepik": "https://www.freepik.es", "thingiverse": "https://www.thingiverse.com",
    "dxfdownloads": "https://dxfdownloads.com",
    "3axis": "https://3axis.co", "dxfforcnc": "https://dxfforcnc.com",
    "ameede": "https://ameede.com", "vectorsart": "https://vectorsart.com",
    "bibliotecadecorte": "https://bibliotecadecorte.com",
    "megalaser": "https://megalaser.com.ar", "stanser": "https://stanser.com",
    "creativefabrica": "https://www.creativefabrica.com",
    "boxes": "https://boxes.hackerspace-bamberg.de",
}
_ABRIR_VERBOS = ("abre", "abrir", "abreme", "llevame a", "vamos a", "entra a",
                 "metete a", "ponme", "muestrame la pagina", "ve a")

# Sitios que además saben BUSCAR por URL. Caso real 2026-08-05: "abre pinterest
# y busca luna de mdf" hizo una búsqueda web genérica y devolvió Wikipedia y
# MercadoLibre — ni un resultado de Pinterest, y nunca abrió el sitio. Pinterest
# ni siquiera estaba en la lista de sitios conocidos, aunque buscar referencias
# ahí es parte del trabajo diario de diseño.
#
# Ahora se abre el sitio CON la búsqueda ya hecha, que es lo que se pedía.
_BUSQUEDA_EN_SITIO = {
    "pinterest": "https://www.pinterest.com.mx/search/pins/?q={q}",
    "youtube": "https://www.youtube.com/results?search_query={q}",
    "mercadolibre": "https://listado.mercadolibre.com.mx/{q}",
    "meli": "https://listado.mercadolibre.com.mx/{q}",
    "mercado libre": "https://listado.mercadolibre.com.mx/{q}",
    "amazon": "https://www.amazon.com.mx/s?k={q}",
    "google": "https://www.google.com/search?q={q}",
    "aliexpress": "https://es.aliexpress.com/w/wholesale-{q}.html",
    "etsy": "https://www.etsy.com/search?q={q}",
    "facebook": "https://www.facebook.com/search/top?q={q}",
    "instagram": "https://www.instagram.com/explore/tags/{q}/",
    "lideart": "https://lideart.com.mx/buscar?controller=search&s={q}",
    "behance": "https://www.behance.net/search/projects?search={q}",
    "freepik": "https://www.freepik.es/search?query={q}",
    "thingiverse": "https://www.thingiverse.com/search?q={q}",
    "dxfdownloads": "https://dxfdownloads.com/?s={q}",
    # Bancos de diseños para corte láser: los que de verdad usa el taller.
    # Anuar preguntó por 3axis el 2026-08-05 y no estaba.
    "3axis": "https://3axis.co/?s={q}",
    "dxfforcnc": "https://dxfforcnc.com/?s={q}",
    # Los bancos de diseño que Anuar USA de verdad, sacados de su historial de
    # navegación el 2026-08-05 y con la URL de búsqueda VERIFICADA en vivo
    # (HTTP 200, no supuesta).
    "ameede": "https://ameede.com/?s={q}",
    "biblioteca de corte": "https://bibliotecadecorte.com/?s={q}",
    "bibliotecadecorte": "https://bibliotecadecorte.com/?s={q}",
    "vectorsart": "https://vectorsart.com/?s={q}",
    "vectors art": "https://vectorsart.com/?s={q}",
    "megalaser": "https://megalaser.com.ar/?s={q}",
    "stanser": "https://stanser.com/?s={q}",
    "creativefabrica": "https://www.creativefabrica.com/search/{q}/",
    # boxes.py EN LÍNEA: 129 visitas suyas. Ahora también lo tiene dentro de
    # AURORA con "hazme una caja...", pero el sitio sigue sirviendo para ver
    # los 189 generadores con dibujo.
    "boxes": "https://boxes.hackerspace-bamberg.de/",
    "boxes py": "https://boxes.hackerspace-bamberg.de/",
}

# Verbos que indican que además de abrir, se quiere BUSCAR algo ahí.
_BUSCAR_EN_SITIO_VERBOS = ("busca", "buscame", "buscar", "encuentra", "encuentrame",
                           "muestrame", "enseñame", "ensename", "ver", "checa",
                           # "dame" y "revisa" salen del perfil de Anuar, que
                           # convierte "muéstrame"→"dame" y "chékame"→"revisa"
                           # antes de llegar aquí (2026-08-05).
                           "dame", "revisa", "quiero ver", "necesito")

# Sitios donde lo que importa son las IMÁGENES: hay que abrirlos, no resumirlos.
# Una lista de cinco URLs de Pinterest no sirve para buscar referencias de
# diseño — es justo lo que pasó el 2026-08-05 con "busca diseños de armarios
# para herramienta cortados al láser en pinterest".
# MercadoLibre y Amazon NO están aquí a propósito: ahí una lista con precios y
# enlaces sí es útil sin abrir nada.
_SITIOS_VISUALES = ("pinterest", "instagram", "behance", "freepik",
                    "thingiverse", "etsy", "dxfdownloads", "3axis",
                    "dxfforcnc", "ameede", "biblioteca de corte",
                    "bibliotecadecorte", "vectorsart", "vectors art",
                    "megalaser", "stanser", "creativefabrica", "boxes")

# Palabras que van después de "en" pero NO son un sitio web. Sin esta lista,
# "en corel busca el texto" abriría Google buscando "corel", y "en la
# computadora busca el archivo" también. Todas salen de cosas que Anuar dice.
_NO_SON_SITIOS = frozenset((
    "internet", "la web", "web", "la red", "google", "linea", "la nube",
    "corel", "aurora", "rdworks", "aspire", "silhouette", "cameo", "illustrator",
    "la computadora", "la pc", "el disco", "la carpeta", "el archivo",
    "mis archivos", "descargas", "documentos", "el escritorio", "la usb",
    "la memoria", "el catalogo", "el inventario", "la agenda", "el taller",
    "la base", "mis notas", "el sistema", "casa", "el chat",
))


def _sitio_conocido(mensaje: str) -> str:
    """Devuelve la URL si el mensaje nombra un sitio conocido, o cadena vacía."""
    m = _norm_txt(mensaje)
    for nombre, url in _SITIOS_CONOCIDOS.items():
        if re.search(rf"\b{re.escape(nombre)}\b", m):
            return url
    return ""


def _abrir_con_busqueda(mensaje: str) -> str:
    """URL del sitio CON la búsqueda ya hecha, si se pidió buscar algo ahí.

    "abre pinterest y busca luna de mdf" →
        https://www.pinterest.com.mx/search/pins/?q=luna+de+mdf
    """
    from urllib.parse import quote_plus
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _BUSCAR_EN_SITIO_VERBOS):
        return ""
    # El sitio más largo primero: "mercado libre" antes que "mercadolibre".
    for nombre in sorted(_BUSQUEDA_EN_SITIO, key=len, reverse=True):
        if not re.search(rf"\b{re.escape(nombre)}\b", m):
            continue
        # Lo que se busca es lo que va DESPUÉS del verbo de buscar.
        resto = m
        for v in sorted(_BUSCAR_EN_SITIO_VERBOS, key=len, reverse=True):
            if v in resto:
                resto = resto.split(v, 1)[1]
                break
        resto = resto.replace(nombre, " ")
        for basura in ("abre", "abrir", "abreme", "en", "el", "la", "los", "las",
                       "de la", "aurora", "porfa", "por favor", "y"):
            resto = re.sub(rf"^\s*{re.escape(basura)}\b", " ", resto)
        consulta = " ".join(resto.split()).strip(" ,.;:")
        # Cuando el sitio va al FINAL ("busca diseños de X en pinterest"), al
        # quitarlo queda colgando la preposición: "...cortados al laser en".
        # Buscar eso mete ruido (2026-08-05).
        consulta = re.sub(r"\s+\b(?:en|de|del|para|por|con|a|y|o)\b\s*$", "",
                          consulta, flags=re.IGNORECASE).strip(" ,.;:")
        if not consulta:
            return ""
        plantilla = _BUSQUEDA_EN_SITIO[nombre]
        # MercadoLibre y AliExpress arman la búsqueda con GUIONES en la ruta, no
        # con "+" de query string: listado.mercadolibre.com.mx/papel-adhesivo.
        # Con "+" la página abre vacía.
        if "listado.mercadolibre" in plantilla or "aliexpress" in plantilla:
            q = "-".join(quote_plus(w) for w in consulta.split())
        elif "instagram" in plantilla:
            q = "".join(c for c in consulta if c.isalnum())   # los hashtags no llevan espacios
        else:
            q = quote_plus(consulta)
        return plantilla.format(q=q)

    # ── SITIO DESCONOCIDO ────────────────────────────────────────────────
    # "en ameede busca la torre eiffel en dxf": no está en la lista y no se
    # puede inventar su URL de búsqueda — cada sitio la arma distinto y saldría
    # una página de error. Pero tampoco hay que rendirse: se busca en Google
    # nombrando el sitio, que SIEMPRE lleva a la página correcta.
    # Anuar lo preguntó el 2026-08-05: "¿y funciona para cualquier sitio?".
    m2 = re.search(r"\ben\s+([a-z0-9][a-z0-9.\- ]{2,24}?)\s+"
                   r"(?:busca|buscame|encuentra|encuentrame|dame|muestrame|revisa)\b",
                   m)
    if m2:
        sitio = m2.group(1).strip()
        if sitio not in _NO_SON_SITIOS:
            resto = m[m2.end():].strip()
            resto = re.sub(r"\s+\b(?:en|de|del|para|por|con|a|y|o)\b\s*$", "", resto)
            if resto:
                return ("https://www.google.com/search?q="
                        + quote_plus(f"{resto} {sitio}"))
    return ""


def _es_abrir_navegador(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    # 1) Un dominio explícito + intención de abrirlo (como funcionaba antes)
    if _DOMINIO_RE.search(mensaje) and _contiene_trigger(m, _ABRIR_NAVEGADOR_TRIGGERS):
        return True
    # 2) Un sitio conocido por su nombre + un verbo de abrir. "abre youtube".
    if _sitio_conocido(mensaje) and _contiene_trigger(m, _ABRIR_VERBOS):
        return True
    # 3) "abre pinterest y busca X": abrir el sitio CON la búsqueda hecha.
    #    Va aquí y no en busqueda_web porque lo que se pide es ABRIR, no que
    #    AURORA busque y resuma.
    if _contiene_trigger(m, _ABRIR_VERBOS) and _abrir_con_busqueda(mensaje):
        return True
    # 4) "busca diseños de X en pinterest" — sin verbo de abrir, pero nombrando
    #    un sitio VISUAL. Ahí una lista de enlaces no sirve de nada: hay que ver
    #    las imágenes. Caso real 2026-08-05: pidió diseños de armarios en
    #    Pinterest y recibió cinco URLs de texto.
    if _contiene_trigger(m, _SITIOS_VISUALES) and _abrir_con_busqueda(mensaje):
        return True
    return False


# ── AURORA habla de SÍ MISMA (capacidades/límites/estructura reales) ──
# Encontrado en vivo 2026-07-27: preguntarle a AURORA por sus propias funciones
# y límites (con amigos presentes) la mandó a hacer una BÚSQUEDA WEB genérica
# ("funciones y limites de la herramienta" → resultados de matemáticas y
# comparativas de apps random) en vez de responder con su propio autoconocimiento
# real. Introspección nunca debe ir a buscar en internet.
_ACERCA_DE_TRIGGERS = (
    "tus funciones", "tus capacidades", "tus limites", "tu estructura",
    "que puedes hacer", "que sabes hacer", "como funcionas", "de que estas hecha",
    "para que estas disenada", "cuentame de ti", "hablame de ti", "quien eres",
    "que eres tu", "que eres aurora",
    # Encontrado en vivo 2026-07-29: Anuar pidio "podrias autodescribirte a
    # detalle" y NINGUNA frase de arriba calzo, asi que cayo en motor_analisis,
    # que INVENTO capacidades falsas (diseño de interiores, ciencia, "puedo crear
    # diseños graficos", "aprendo y mejoro continuamente"). Nada de eso es real.
    # Justo el caso que hay que evitar frente a un cliente.
    "autodescribete", "autodescribirte", "auto describete", "describete",
    "descripcion de ti", "descríbete", "presentate", "preséntate",
    "que herramientas tienes", "cuantas herramientas", "de que eres capaz",
    "cuales son tus funciones", "tus habilidades", "tu inventario",
)


def _es_acerca_de(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _ACERCA_DE_TRIGGERS)


# ── Búsqueda web EXPLÍCITA (el usuario pide navegar/buscar en internet) ──
_BUSQUEDA_WEB_TRIGGERS = (
    "busca en internet", "buscar en internet", "busca en la web", "busca en google",
    "googlea", "navega", "en internet busca", "investiga en la web", "busca en linea",
    "buscar en la web", "consulta en internet", "revisa en internet", "busca en la red",
    # Encontrado en vivo 2026-07-30: Anuar reporto que "la navegacion web no esta
    # conectada en el chat, solo en la pestaña Web en vivo". La causa real no era
    # falta de conexion — el motor web SI funciona — sino que estas frases eran
    # demasiado rigidas: solo calzaban si decia literalmente "busca en internet".
    # Preguntar natural ("investiga el precio de X", "que dicen de este producto")
    # no calzaba con nada y caia al motor generico, que inventa y luego se corrige
    # solo. Mismo patron que ya paso con la autodescripcion.
    "investiga", "investigame", "buscame", "búscame", "checa en internet",
    "checa en la web", "busca informacion", "informacion sobre", "info sobre",
    "que dicen de", "que dice la gente de", "que hay de nuevo",
    "precio de mercado", "precios del mercado", "cuanto cuesta en el mercado",
    "como esta el precio", "compara precios", "comparar precios",
    "en mercadolibre", "en amazon", "ultimas noticias", "noticias de",
    "cotizacion del dolar", "tipo de cambio",
)


# Preguntas por un PROVEEDOR. Van ANTES de la búsqueda web a propósito: si el
# proveedor ya está en el directorio de Anuar, contestar con su dato real y su
# precio vale más que mandarlo a internet. Solo si no lo tiene se busca afuera.
_PREGUNTAS_DE_PROVEEDOR = (
    "quien me vende", "quien vende", "quien me surte", "con quien compro",
    "a quien le compro", "mi proveedor", "proveedor de", "proveedores de",
    "donde le compro", "quien me lo surte", "que proveedores tengo",
    "mis proveedores", "a cuanto me lo dan",
)


def _es_proveedor(mensaje: str) -> bool:
    """Pregunta por un proveedor suyo, no por comprar en internet."""
    return _contiene_trigger(_norm_txt(mensaje), _PREGUNTAS_DE_PROVEEDOR)


def _es_busqueda_web(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    # Si pregunta por SU proveedor, no es búsqueda web: es su directorio.
    if _es_proveedor(mensaje):
        return False
    if _contiene_trigger(m, _BUSQUEDA_WEB_TRIGGERS):
        return True
    # Preguntar dónde comprar algo, o pedir el link de una publicación, es
    # buscar en internet — aunque no se diga "busca en internet". Caso real
    # 2026-08-04: "encuentra el mejor precio por 100 hojas y dame el link" no
    # la agarraba NINGÚN candado y se iba a motor_analisis.
    if _es_compra_afuera(m):
        return True
    # Forma natural: "busca/investiga X" sin la frase literal "en internet".
    if re.search(r"\b(busca|buscame|investiga|googlea|consulta|checa)\b", m):
        # Evitar colisión con pedidos internos del propio sistema.
        if any(k in m for k in (
            "codigo", "archivo", "funcion", "agenda", "cita", "corel", "dxf",
            "whatsapp", "editor", "memoria", "agente", "motor", "capacidad",
        )):
            return False
        return True
    return False


# ── Detectores de motores conectados directo al chat (acción real) ──────
def _es_publicar(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "publica hoy", "publicar hoy", "publica en atf", "publica en facebook",
        "prepara la publicacion", "preparar publicacion", "que publico hoy",
        "estrategia de ingresos", "sube el video de hoy", "postea hoy", "publica el reel",
        "publicalo de verdad", "publicalo ya"))


def _es_agenda(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "que tengo agendado", "mi agenda", "proximas citas", "proxima cita",
        "que citas tengo", "agenda de hoy", "que tengo hoy", "resumen de agenda",
        "citas de hoy", "tengo pendientes hoy",
        # Fase 3 (2026-07-28): "hoy"/"manana" existian como frase pero SIEMPRE
        # regresaban el resumen general, nunca el dia real pedido (encontrado en
        # vivo). Y agendar una cita nueva no tenia NINGUNA ruta por chat.
        "que tengo manana", "agenda de manana", "citas de manana",
        "agenda una cita", "agendar una cita", "agendame", "programa una cita",
        "nueva cita", "crear cita", "agenda del dia",
        # Cerrar una cita. Lo detectó el barrido del 2026-08-04:
        # AGENDA/agenda:actualizar_estado existía y no había forma de llamarla
        # desde el chat, así que las citas se quedaban abiertas para siempre.
        "ya se hizo la cita", "cita hecha", "marca la cita", "cancela la cita",
        "cancelar la cita", "confirma la cita", "confirmar la cita",
        "ya vino el cliente", "ya se entrego", "cierra la cita",
        "la cita ya se hizo", "no vino el cliente"))


def _es_cerrar_cita(mensaje: str) -> bool:
    """Cambia el estado de una cita que ya existe, no crea una nueva."""
    return _contiene_trigger(_norm_txt(mensaje), (
        "ya se hizo la cita", "cita hecha", "marca la cita", "cancela la cita",
        "cancelar la cita", "confirma la cita", "confirmar la cita",
        "ya vino el cliente", "cierra la cita", "la cita ya se hizo",
        "no vino el cliente", "ya se entrego"))


_SERVICIOS_ATF_CACHE = None


def _servicios_atf() -> list:
    """Servicios REALES de mano de obra de ATF (CONFIG/servicios_atf.json)."""
    global _SERVICIOS_ATF_CACHE
    if _SERVICIOS_ATF_CACHE is None:
        try:
            import json as _j
            _SERVICIOS_ATF_CACHE = _j.loads(
                (ROOT / "CONFIG" / "servicios_atf.json").read_text(encoding="utf-8")
            ).get("servicios", [])
        except Exception:
            _SERVICIOS_ATF_CACHE = []
    return _SERVICIOS_ATF_CACHE


def _es_servicio_atf(mensaje: str) -> bool:
    """True si el cliente pide un SERVICIO de mano de obra de ATF.

    Creado 2026-07-29 por un caso real: un cliente al que ya se le habian
    instalado lupas fue chocado, compro un faro nuevo y pidio la RECOLOCACION.
    AURORA le respondio "no puedo recolocarte la lupa, puedo ofrecerte opciones
    para que lo hagas tu mismo" — nego un servicio que Anuar SI hace y perdio al
    cliente. Causa: el catalogo de ATF solo tenia productos, ningun servicio.
    """
    m = _norm_txt(mensaje)
    for s in _servicios_atf():
        for palabra in s.get("palabras_cliente", []):
            if _norm_txt(palabra) in m:
                return True
    return False


# ── Guardia: el chat técnico y el chat de negocio no se pisan ────────────────
# Los candados de venta buscan palabras sueltas del catálogo dentro del mensaje.
# Eso hace que se traguen mensajes que no son de un cliente. Casos reales del
# 2026-07-31, todos de Anuar hablando de su propio sistema:
#   "diagnostica el problema"        -> cayó en el servicio de diagnóstico de faros
#   "corel tiene instalado el plugin"-> cayó en motor_negocios
#   "edita tu archivo X.py"          -> lo interceptaron antes de llegar al IDE
# Un cliente jamás escribe "consciencia.py" ni "candado" ni "pytest". Anuar sí,
# porque usa AURORA de las dos formas. Si el mensaje habla del sistema, los
# candados de venta se saltan.
_TECNICO_DEL_SISTEMA = (
    "aurora", "consciencia", "candado", "motor_", "pytest", "commit", "repositorio",
    "endpoint", "servidor", "puerto 5000", "log", "traceback", "bug", "codigo",
    "código", "script", "modulo", "módulo", "funcion py", "archivo py",
    "plugin", "instalado", "version", "versión", "enrutador", "registro de herramientas",
)
_EXT_CODIGO = (".py", ".json", ".md", ".bat", ".ps1", ".html", ".js", ".yml", ".log")


def _es_tema_del_sistema(mensaje: str) -> bool:
    """True si el mensaje habla del propio AURORA o de código, no de un pedido
    de cliente. Sirve para que los candados de venta no lo intercepten."""
    m = _norm_txt(mensaje)
    if any(m.endswith(e) or (e + " ") in m or (e + ",") in m for e in _EXT_CODIGO):
        return True
    if re.search(r"[A-Za-z]:\\", mensaje or ""):     # una ruta de Windows
        return True
    if re.search(r"\b[A-Z][A-Z_]{2,}/[a-z_]+", mensaje or ""):   # CARPETA/modulo
        return True
    return _contiene_trigger(m, _TECNICO_DEL_SISTEMA)


# Tiendas y señales de que se está preguntando por comprar AFUERA, no por
# cuánto cobrarle a un cliente. Separar las dos cosas es lo que evita que
# "el mejor precio de 100 hojas" se convierta en una cotización de 100 playeras.
_TIENDAS_DE_AFUERA = (
    "mercado libre", "mercadolibre", "meli", "amazon", "ebay", "aliexpress",
    "alibaba", "shein", "temu", "walmart", "costco", "home depot", "lideart",
    "office depot", "coppel", "liverpool",
)
_SENALES_DE_COMPRA = (
    "busca en", "buscame en", "buscar en", "encuentra en", "encuentrame",
    "donde compro", "donde consigo", "donde venden", "donde lo venden",
    "dame el link", "el link", "la publicacion", "el enlace", "la url",
    "mas barato", "quien lo vende", "que proveedor", "proveedores de",
)


# "Qué recuerdas de X" es una pregunta a la MEMORIA, aunque X sea el nombre de
# una acción. Encontrado el 2026-08-05: "qué recuerdas de cotizar" devolvió una
# cotización de faros porque el candado del cotizador vio la palabra "cotizar".
_PREGUNTA_A_LA_MEMORIA = (
    "que recuerdas de", "que recuerdas sobre", "que sabes de",
    "que tienes guardado sobre", "recuerdas que", "recuerdas cuando",
    "que has aprendido de", "que aprendiste de",
)


def _es_pregunta_de_memoria(m_norm: str) -> bool:
    """True si se le pregunta QUÉ RECUERDA, no si se le pide hacer algo."""
    return _contiene_trigger(m_norm, _PREGUNTA_A_LA_MEMORIA)


def _es_compra_afuera(m_norm: str) -> bool:
    """True si se pregunta por comprar algo afuera, no por cuánto cobrarlo.

    Basta con nombrar una tienda: si el mensaje dice "mercado libre", jamás está
    pidiendo una cotización del taller.
    """
    return (_contiene_trigger(m_norm, _TIENDAS_DE_AFUERA)
            or _contiene_trigger(m_norm, _SENALES_DE_COMPRA))


def _es_cotizar(mensaje: str) -> bool:
    """Pide un precio o una cotización.

    No existía candado para esto — la función que más dinero puede traer era la
    única sin puerta. Encontrado el 2026-08-03: "cuanto cuesta el faro aozoom x5"
    no llegaba al cotizador teniendo el producto en el catálogo a $1,599, y
    AURORA mandaba a Anuar a buscarlo a MercadoLibre.
    """
    m = _norm_txt(mensaje)
    # Preguntar QUÉ RECUERDA de un tema no es pedir esa acción. Caso real
    # 2026-08-05: "qué recuerdas de cotizar" devolvió una cotización de faros
    # porque el candado vio la palabra "cotizar". Vale para todos los candados
    # de acción, no solo este.
    if _es_pregunta_de_memoria(m):
        return False
    # El cotizador es para VENDER, no para COMPRAR. Si se pregunta cuánto cuesta
    # algo AFUERA (MercadoLibre, Amazon, un proveedor), no tiene nada que hacer
    # aquí. Caso real 2026-08-04: "busca en mercado libre el mejor precio de 100
    # hojas de papel adhesivo" cotizó 100 playeras + 100 boxers + 100 cajas MDF
    # por $75,000 — el candado vio "precio" y "100" y se lanzó, ignorando que el
    # mensaje decía dónde buscar.
    if _es_compra_afuera(m):
        return False
    if _contiene_trigger(m, ("cotiza", "cotizame", "cotizacion", "cotizar",
                             "presupuesto", "presupuestame")):
        return True
    # "cuánto cuesta / sale / vale" + algo que se venda.
    pregunta_precio = _contiene_trigger(m, (
        "cuanto cuesta", "cuanto sale", "cuanto vale", "que precio", "precio de",
        "cual es el precio", "en cuanto sale", "cuanto me sale", "cuanto cobras"))
    if not pregunta_precio:
        return False
    # Se excluye lo que ya atiende otro candado mejor.
    if _es_tema_del_sistema(mensaje) or _es_servicio_atf(mensaje):
        return False
    return True


def _es_comando_video(mensaje: str) -> bool:
    """Pide algo con los videos de la videoteca.

    Existe porque Anuar tiene 296 videos (9.92 GB) de trabajos reales parados en
    el disco: ~190 no se publican solo por estar horizontales. El motor ya podía
    voltearlos; le faltaba la puerta desde el chat.
    """
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, ("video", "videos", "reel", "reels", "tiktok",
                                 "short", "shorts", "clip", "clips", "videoteca")):
        return False
    return _contiene_trigger(m, (
        "vertical", "9:16", "9 16", "voltea", "voltear", "convierte", "convertir",
        "prepara", "preparar", "listos", "publicar", "duplicado", "duplicados",
        "repetido", "repetidos", "miniatura", "portada", "cuantos", "revisa",
        "que hay", "cuales"))


def _es_comando_voz(mensaje: str) -> bool:
    """Prender, apagar o probar la voz. Portada del NEXUS de Anuar."""
    m = _norm_txt(mensaje)
    return _contiene_trigger(m, (
        "activa la voz", "prende la voz", "enciende la voz", "modo voz",
        "escuchame", "quiero hablarte", "apaga la voz", "desactiva la voz",
        "callate", "deja de escuchar", "prueba la voz", "como suenas",
        "di algo", "hablame"))


def _es_ver_aprendizaje(mensaje: str) -> bool:
    """Anuar quiere ver o borrar lo que AURORA aprendió de cómo habla.

    Sin esto, un sistema que aprende solo es un sistema que cambia a tus
    espaldas. Él tiene que poder mirarlo y quitárselo.
    """
    m = _norm_txt(mensaje)
    return _contiene_trigger(m, (
        "que has aprendido", "que aprendiste", "que sabes de como hablo",
        "muestrame lo aprendido", "lo que has aprendido", "olvida ",
        "olvidalo todo", "borra lo aprendido", "olvida todo lo aprendido"))


# Capturar un cliente nuevo. Lo detectó el barrido del 2026-08-04:
# ORACLE/oracle_core:crear_lead existía y NO tenía ninguna puerta desde el chat,
# así que un cliente que llamaba se anotaba en un papel o se perdía. De las 537
# herramientas, esta es de las que más dinero mueve.
_ALTA_DE_LEAD = (
    "apunta un cliente", "apunta este cliente", "apunta a", "anota un cliente",
    "anota este cliente", "anota a", "registra un cliente", "registra este cliente",
    "nuevo cliente", "nuevo lead", "crear lead", "crea un lead", "registra un lead",
    "me llamo un cliente", "me hablo un cliente", "me escribio un cliente",
    "guarda este contacto", "guarda el cliente", "dar de alta al cliente",
)


def _es_alta_lead(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _ALTA_DE_LEAD)


# Cotizar un DXF midiendo sus METROS DE CORTE reales. Es lo que le faltó a Anuar
# el 2026-08-04 con la casa de muñecas: sin el archivo no hay metros, y sin
# metros no hay precio — la vendió en $280 costando ~$200.
_COTIZAR_DXF = (
    "cotiza este dxf", "cotiza el dxf", "cuanto cuesta cortar",
    "cuanto sale cortar", "cuanto cobro por cortar", "cotiza este corte",
    "cuantos metros de corte", "metros de corte", "mide el corte",
    "cuanto tarda en cortar", "cotiza este archivo", "cotiza el diseno",
    "cotiza este diseno", "cotiza el archivo", "cotiza el corte",
    "cuanto cuesta este diseno", "cuanto por cortar", "cotiza el dibujo",
)


# Generar una caja dando las medidas. Anuar lo pidió el 2026-08-05: boxes.py
# tiene 189 generadores (corazón, flex, bisagras, bandejas) y él quería pedirlas
# hablando, no con parámetros de línea de comandos.
_GENERAR_CAJA = (
    "hazme una caja", "haz una caja", "generame una caja", "genera una caja",
    "crea una caja", "creame una caja", "quiero una caja", "necesito una caja",
    "una caja de", "una caja con", "caja corazon", "caja con divisiones",
    "hazme una bandeja", "genera una bandeja", "quiero una bandeja",
    "hazme un cajon", "generame el dxf de una caja", "arma una caja",
    "que cajas puedes hacer", "que cajas sabes hacer", "tipos de caja",
)


def _es_generar_caja(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _GENERAR_CAJA)


# ── LA CAMPAÑA ESCOLAR QUE YA SALIÓ A LAS CLIENTAS ──────────────────────
# Riesgo que Anuar señaló el 2026-08-06 con la campaña ya enviándose: AURORA
# contesta sola el WhatsApp. Una clienta que acaba de leer «primaria $150» y
# pregunta el precio NO puede recibir otro número — eso tumba la venta y deja
# a Milen's como que no se aclara. Por eso los cuatro paquetes viven en un
# archivo y este candado responde con ellos, no con lo que el chat suponga.
_CAMPANA_ESCOLAR = (
    "paquete escolar", "paquetes escolares", "regreso a clases",
    "etiquetas escolares", "etiquetas para utiles", "etiquetas para útiles",
    "el de preescolar", "el de primaria", "paquete de preescolar",
    "paquete de primaria", "etiquetas para la escuela", "etiquetas del niño",
    "etiquetas del nino", "nombres para la ropa", "tabla de multiplicar",
)


def _es_campana_escolar(mensaje: str) -> bool:
    """¿Pregunta por los paquetes que se le acaban de mandar?"""
    return _contiene_trigger(_norm_txt(mensaje), _CAMPANA_ESCOLAR)


# ── EL MÉTODO PARA ARMAR CAMPAÑAS ───────────────────────────────────────
# Anuar lo pidió el 2026-08-06 y es la petición correcta: *"importantísimo es
# que AURORA entienda cómo realizaste la campaña, pues tú ya no estarás"*.
# Por eso el método vive en MARKETING/metodo_campanas.py y se pide por aquí:
# lo que se hereda no es la campaña escolar, es saber armar la siguiente y
# saber revisar la que alguien escriba.
_METODO_CAMPANA = (
    "como se arma una campana", "como se hace una campana",
    "como armo una campana", "anatomia de una campana",
    "reglas de las campanas", "como hiciste la campana",
    "revisa esta campana", "revisa la campana", "revisame esta campana",
    "checa esta campana", "esta bien esta campana", "arma una campana",
    "armame una campana", "crea una campana", "creame una campana",
    "nueva campana",
)


def _es_metodo_campana(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _METODO_CAMPANA)


# ── PRINT & CUT: de la impresión al corte ───────────────────────────────
# Anuar lo aprendió a mano el 2026-08-07, equivocándose paso por paso con las
# calcomanías de Luisa, y pidió que quedara guardado: *"tuve que hacer todo
# manual para aprender, valió la pena el tiempo y dolor de cabeza"*. Esto
# existe para que ese dolor no se pague dos veces.
_PRINT_AND_CUT = (
    "print and cut", "print & cut", "imprimir y cortar",
    "marcas de registro", "como pongo las marcas", "marcas de silhouette",
    "marcas de silouette", "como corto lo impreso", "cortar lo impreso",
    "desplazamiento", "contorno extra", "excedente del corte",
    "area util de la hoja", "cuanto cabe en una hoja",
)


def _es_print_and_cut(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _PRINT_AND_CUT)


# ── ADAPTAR UN DISEÑO A OTRO MATERIAL Y OTRO TAMAÑO ─────────────────────
# Anuar describió el flujo completo el 2026-08-06: *"yo elijo el material y la
# escala del tamaño; al poner el espesor del material, este genera los ajustes
# en automático, ranuras y largo de dientes; ese sería el flujo completo"*.
#
# Son DOS PERILLAS y nada más: la escala manda sobre el tamaño del diseño
# armado, el espesor manda sobre todos los ensambles. Él no vuelve a tocar ni
# el ancho de las ranuras ni el largo de los dientes.
#
# Su palabra para los ensambles es ENCASTRES. También dice hembras y machos.
_ADAPTAR_DISENO = (
    "ajusta", "ajustame", "adapta", "adaptame", "reduce", "reduceme",
    "escala", "escalame", "achica", "achicame", "agranda",
    "pasalo a", "pasala a", "pon ", "ponme", "ponlo", "ponla",
    "deja ", "dejalo", "dejala", "conviertelo a", "conviertela a",
)
# Sin una de estas no es adaptar: es escalar a secas, que no es lo mismo.
_SENAL_MATERIAL = (
    "material", "espesor", "grosor", "mdf", "encastre", "encastres",
    "hembra", "hembras", "macho", "machos", "ranura", "ranuras",
    "ensamble", "ensambles", "diente", "dientes", "mm",
)


def _es_adaptar_diseno(mensaje: str) -> bool:
    """¿Pide dejar un DXF listo para otro material (y de otro tamaño)?

    Necesita un verbo de ajustar, algo que hable del material o de los
    encastres, y una medida. Sin lo del material sería solo escalar, que no
    es lo mismo.

    NO SE EXIGE QUE NOMBRE EL ARCHIVO, y es a propósito. Él dice *"ajusta la
    casa de bob al 50% para material de 2.5"* — el archivo lo llama por su
    nombre, no por su ruta (2026-08-06). Pedirle que escriba la ruta sería
    hacerle trabajo a él para ahorrárselo al código. Cuál es el archivo lo
    resuelve `_ultimo_archivo` con lo que ya se venía hablando, y si de plano
    no hay, se le pregunta con buenos modos en vez de no entenderle.
    """
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _ADAPTAR_DISENO):
        return False
    # "en 2.5mm" es señal de material aunque no diga la palabra: el "mm"
    # pegado al número no lo cachaba el buscador de palabras sueltas, y así
    # es como se dice de verdad (2026-08-08).
    if not _contiene_trigger(m, _SENAL_MATERIAL) and not re.search(
            r"\d\s*(?:mm|milimetros?)\b", m):
        return False
    # Una medida de por medio: el porcentaje del tamaño o el espesor. Sin
    # ningún número esto no es una orden de trabajo, es plática.
    return bool(re.search(r"\d", m))


# ── VINIL Y PLOTTER ─────────────────────────────────────────────────────
# El 2026-08-08 Anuar preguntó en el chat cuánto costaba unas letras en vinil
# textil de recorte. AURORA contestó *«entre $500 y $1,500 MXN»* — un número
# INVENTADO, teniendo su propia lista de precios de vinil guardada en
# CONFIG/catalogo_servicios.json. El precio real de ese trabajo era $148, y él
# lo cobró en $150. Sus palabras: *"aurora no supo cobrar"*.
#
# El hueco era doble: no existía el motor, y el que contestó se puso a adivinar
# en lugar de decir que no sabía.
_VINIL_TRIGGERS = (
    "vinil", "vinilo", "vinil textil", "vinil de recorte", "recorte",
    "plotter", "ploter", "cameo", "silhouette", "termotransferible",
    "planchado", "planchar", "htv",
)
_DINERO_TRIGGERS = (
    "cuanto", "cuesta", "costo", "coste", "precio", "cotiza", "cotizame",
    "cotizacion", "cobrar", "cobro", "vale", "sale en", "presupuesto",
)


def _minimo_coloc(cv) -> float:
    """Lo que cobra por colocar/planchar, de su propio catálogo."""
    try:
        return cv._minimo_y_colocacion()[1]
    except Exception:
        return 0.0


# Lo que delata que el trabajo es de LÁSER y no de vinil. Si aparece alguno,
# este candado no se mete: para eso está el cotizador de láser.
_MATERIAL_LASER = ("mdf", "acrilico", "madera", "triplay", "multiplay",
                   "laser", "lasser", "grabado", "grabar", "caja", "cajas")


def _es_cotizar_vinil(mensaje: str) -> bool:
    """¿Pregunta el precio de un trabajo de vinil o de corte de plotter?

    También entra cuando NO dice «vinil» pero pregunta el costo de unas
    palabras en un área — que es como lo preguntó de verdad el 2026-08-08:
    *«la palabra coca cola y debajo osvaldo en un área de 30 cm de largo x 20
    cm de alto, ¿qué costo tendría?»*. Ahí no cayó en ningún candado y un
    motor suelto le inventó «entre $500 y $1,500». Un rótulo de letras en un
    área es trabajo de plotter salvo que nombre un material de láser.
    """
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _DINERO_TRIGGERS):
        return False
    if _contiene_trigger(m, _VINIL_TRIGGERS):
        return True
    if _contiene_trigger(m, _MATERIAL_LASER):
        return False
    # letras/palabras + un área con dos medidas = rótulo de recorte
    return (_contiene_trigger(m, _TEXTO_CORTE_TRIGGERS)
            and bool(re.search(r"\d+(?:[.,]\d+)?\s*(?:cm|mm)?\s*"
                               r"(?:de\s*(?:largo|ancho|base)\s*)?"
                               r"[x×por]\s*\d", m)))


# Generar el archivo, no cotizarlo: «hazme la palabra X para vinil».
_TEXTO_CORTE_TRIGGERS = (
    "la palabra", "las palabras", "el nombre", "los nombres", "el texto",
    "que diga", "el letrero", "las letras", "el rotulo",
)


def _es_texto_a_corte(mensaje: str) -> bool:
    """¿Pide convertir una palabra o un nombre en archivo de corte?

    Necesita que se hable de texto Y de vinil o corte. Sin lo segundo,
    «la palabra clave» o «el nombre del cliente» caerían aquí sin venir a
    cuento.
    """
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _VINIL_TRIGGERS + ("corte", "cortar",
                                                   "cortado", "rotular")):
        return False
    if _contiene_trigger(m, _TEXTO_CORTE_TRIGGERS):
        return True
    # «hazme "Oswaldo" en vinil de recorte»: lo entrecomillado ES el texto.
    return bool(re.search(r'"[^"]{1,40}"|«[^»]{1,40}»', mensaje or ""))


# Cadena completa: foto → sin fondo → vectorizada → DXF. Anuar la pidió el
# 2026-08-05 después de que AURORA lo obligara a hacerlo en tres mensajes y
# encima olvidara el archivo entre uno y otro.
_FOTO_A_DXF = (
    "quita el fondo y", "quitale el fondo y", "sin fondo y",
    "recorta el sujeto", "recorta la imagen", "quita el fondo",
    "quitale el fondo", "elimina el fondo", "sin el fondo",
)
_QUIERE_DXF = ("dxf", "para corte", "para la laser", "para el laser",
               "cortarlo", "para cortar")


def _es_foto_a_dxf(mensaje: str) -> bool:
    """Pide quitar fondo Y dejarlo listo para cortar, en un solo paso."""
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _FOTO_A_DXF):
        return False
    return _contiene_trigger(m, _QUIERE_DXF)


def _es_cotizar_dxf(mensaje: str) -> bool:
    """Pide el precio de cortar un archivo, no el precio de un producto."""
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, _COTIZAR_DXF):
        return True
    # "cotiza C:\...\loquesea.dxf" — el archivo solo ya es la petición.
    if re.search(r"\.dxf\b", m) and _contiene_trigger(
            m, ("cotiza", "cotizame", "cuanto", "precio", "corte", "cortar")):
        return True
    return False


def _es_ficha_vendedor(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "ficha de", "ficha tecnica de", "dame el pitch", "hazme un pitch",
        "argumentos de venta", "como vendo el", "como vender el", "brief de venta"))


def _es_intuicion(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "que me sugieres", "tu intuicion", "que me recomiendas", "predice",
        "prediccion", "que deberia hacer", "sugerencia proactiva", "que sigue"))


# Preguntas de CONOCIMIENTO: parámetros, recetas y criterios que ya están en la
# memoria semántica. Encontrado el 2026-08-04 al verificar la carga: el
# conocimiento entró bien y "qué recuerdas de láser" lo traía en 1.8 s, pero
# "a cuánto corto MDF de 2.7" —la forma en que Anuar SÍ pregunta— se iba al
# enrutador y ofrecía reajustar_grosor. El conocimiento cargado no sirve de
# nada si solo se alcanza con la pregunta que nadie hace.
_PREGUNTAS_DE_CONOCIMIENTO = (
    "a cuanto corto", "a cuanto grabo", "a que potencia", "a que velocidad",
    "con que parametros", "que parametros", "como corto", "como grabo",
    "que configuracion", "cual es la receta", "como le hago para",
    "que ajuste", "cuanto de potencia", "cuanto de velocidad",
    "que galga", "a que distancia", "cual es el foco",
    # Preguntas de ESTADO sobre el equipo. Encontrado el 2026-08-04 verificando
    # la carga de conocimiento: "como va la lente del cañon" cayó en
    # motor_analisis y se inventó que la lente "fue reemplazada el 2026-06-10" y
    # que "no hay registros de problemas" — dos datos que no existen en ningún
    # lado. Van DESPUÉS del candado de negocio en la lista, así que "como va la
    # contabilidad" sigue yendo a los datos reales del negocio.
    "como va la lente", "como esta la lente", "como va el tubo",
    "como esta el tubo", "como va la maquina", "como esta la maquina",
    "como va el laser", "como esta el laser", "como va la impresora",
    "como esta la impresora", "que sabemos de la lente", "estado de la lente",
)


def _es_memoria(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, (
            "que recuerdas de", "que recuerdas sobre", "tu memoria", "recuerdas cuando",
            "que sabes de", "que tienes guardado sobre", "recuerdas que")):
        return True
    return _contiene_trigger(m, _PREGUNTAS_DE_CONOCIMIENTO)


def _es_equipos(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "activa el equipo", "activar equipo", "que equipos tienes", "lista de equipos",
        "arma el equipo", "pon a trabajar el equipo", "equipo de marketing", "equipo de ventas"))


# ── Fábrica de AGENTES: crear/listar/correr agentes de tarea desde el chat ──
def _es_crear_agente(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "creame un agente", "crea un agente", "crear un agente", "fabricame un agente",
        "fabrica un agente", "necesito un agente", "quiero un agente", "arma un agente",
        "nuevo agente"))


def _es_confirmacion(mensaje: str) -> bool:
    """True si el mensaje es un 'sí' claro a una acción pendiente (sin ambigüedad)."""
    # Whitelist ampliada con variantes reales que Anuar escribe (SISTEMA_BASE ya documenta
    # que escribe corrido y con muletillas cortas) — sigue siendo igualdad exacta tras
    # strip, no substring, para no capturar por accidente una respuesta no relacionada.
    m = _norm_txt(mensaje).strip(" .,!¡¿?")
    if m in ("si", "sip", "simon", "simone", "confirmo", "confirmado", "hazlo", "adelante",
             "dale", "dale pues", "va", "va sale", "vale", "ok", "okay", "ok hazlo",
             "ok hazlo ya", "correcto", "afirmativo", "procede", "hazle", "sale",
             "si confirmo", "si hazlo", "si adelante", "si porfavor", "si por favor",
             "si porfa", "si dale", "si va", "si sale", "claro que si", "obvio"):
        return True

    # La lista exacta nunca alcanza — ese fue el vicio de todo el proyecto.
    # Caso real 2026-07-31: AURORA preparó la publicación del día, pidió
    # confirmar, Anuar contestó "si publicalo", y como esa frase no estaba en la
    # lista canceló la publicación Y ADEMÁS dijo "no puedo publicar contenido en
    # tu nombre", que es falso. Se perdió el post.
    #
    # Ahora se reconoce el PATRÓN: afirmación al inicio + orden corta, sin nada
    # que la eche para atrás. Se exige que sea corta (máx 3 palabras) para no
    # confundir una frase larga con un sí, y esto solo se evalúa cuando ya hay
    # una acción esperando confirmación.
    palabras = m.split()
    if not palabras or len(palabras) > 3:
        return False
    if palabras[0] not in ("si", "ok", "okay", "dale", "va", "vale", "sale",
                           "claro", "orale", "andale", "hazlo", "adelante", "procede"):
        return False
    return not any(p in ("no", "nunca", "mejor", "espera", "aun", "todavia",
                         "despues", "luego", "manana", "cancela", "cancelalo",
                         "olvidalo") for p in palabras[1:])


def _es_listar_agentes(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "que agentes tengo", "que agentes hay", "lista de agentes", "mis agentes",
        "muestrame los agentes", "cuales agentes"))


def _es_correr_agente(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "corre el agente", "ejecuta el agente", "activa el agente", "pon a correr el agente",
        "usa el agente", "lanza el agente"))


# ── CHAT ↔ FÁBRICA: crear capacidades/motores nuevos por chat ──────────
_CREAR_CAPACIDAD_TRIGGERS = (
    "creame un motor", "crea un motor", "crea una capacidad", "creame una capacidad",
    "fabrica un motor", "fabricame un motor", "fabrica una capacidad",
    "hazte capaz de", "agregate la funcion", "agregate la capacidad",
    "necesito un motor que", "quiero un motor que", "construye un motor",
    "nuevo motor para", "motor nuevo que",
)


def _es_crear_capacidad(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _CREAR_CAPACIDAD_TRIGGERS)


# ── CHAT ↔ IDE: leer/buscar/explicar código por chat (solo lectura) ────
_CONSULTA_CODIGO_TRIGGERS = (
    "muestrame el archivo", "muestrame el codigo", "leeme el archivo", "lee el archivo",
    "abre el archivo", "que hace el archivo", "busca en el codigo", "busca en los archivos",
    "donde esta la funcion", "en que archivo esta", "ensename el codigo de",
    "muestrame el codigo de", "que dice el archivo",
)


# Lo que un diseñador abre no es código. Caso real 2026-08-02: "abre el archivo
# trailer hit y extrae el dibujo lineal" se lo llevó el IDE de código, porque la
# frase trae "abre el archivo". Anuar abre CDR, DXF, PDF e imágenes todo el día;
# los .py son la excepción, no la regla.
_EXT_DISENO = (".cdr", ".dxf", ".svg", ".ai", ".eps", ".pdf", ".png", ".jpg",
               ".jpeg", ".bmp", ".webp", ".plt", ".dwg", ".psd")
_PALABRAS_DISENO = ("dibujo", "vector", "lineal", "trazo", "contorno", "diseno",
                    "imagen", "foto", "grabado", "corte", "laser", "sublima",
                    "corel", "logo", "plantilla", "molde")


def _es_consulta_codigo(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _CONSULTA_CODIGO_TRIGGERS):
        return False
    # Si habla de un archivo de diseño o usa vocabulario de taller, NO es código.
    if any(e in m for e in _EXT_DISENO) or _contiene_trigger(m, _PALABRAS_DISENO):
        return False
    return True


# ── CHAT ↔ TALLER: conversión REAL de archivos a DXF (motor que estaba dormido) ──
_CONVERSION_TRIGGERS = (
    "convierte", "convertir", "conviertelo", "pasa a dxf", "pasalo a dxf",
    "a dxf", "en dxf", "exporta a dxf", "vectoriza", "vectorizar",
)


# Formatos a los que EDITOR/conversor_formatos.convertir() sabe llegar de verdad.
# Antes el candado exigía la palabra "dxf": pedir "convierte a pdf" no calzaba con
# nada y se iba al enrutador. Anuar lo dijo el 2026-07-31: "entiende convierte
# pero a pdf no". La capacidad existía; le faltaba la puerta.
_FORMATOS_DESTINO = ("dxf", "pdf", "svg", "png", "jpg", "jpeg", "eps", "ps")


def _formato_destino(mensaje: str) -> str:
    """A qué formato quiere convertir. Cadena vacía si no lo dice."""
    m = _norm_txt(mensaje)
    for f in _FORMATOS_DESTINO:
        # "a pdf", "en pdf", "a .pdf", "formato pdf" — pero NO el .pdf de la ruta
        # de entrada, que es el archivo que se va a convertir, no el destino.
        if re.search(rf"\b(?:a|en|formato|hacia)\s+\.?{f}\b", m):
            return "jpg" if f == "jpeg" else f
    return ""


def _dpi_pedido(mensaje: str) -> int:
    """DPI a usar al rasterizar. 300 por defecto (el estándar de Anuar).

    Acepta el número directo ("a 150 dpi") y también como se dice en el taller:
    para sublimar y para grabado se necesita el detalle fino; una lona se ve a
    metros de distancia y a 300 dpi el archivo pesa de más sin ganar nada.
    """
    m = _norm_txt(mensaje)
    n = re.search(r"\b(\d{2,4})\s*dpi\b", m) or re.search(r"\ba\s+(\d{2,4})\s*(?:de\s+)?resolucion", m)
    if n:
        return max(72, min(1200, int(n.group(1))))
    if _contiene_trigger(m, ("lona", "gran formato", "espectacular", "manta", "baja resolucion")):
        return 150
    if _contiene_trigger(m, ("alta resolucion", "maxima calidad", "muy nitido", "para imprenta")):
        return 600
    return 300      # sublimación, láser, impresión normal


def _pagina_pedida(mensaje: str):
    """Qué página del PDF. None = la primera. -1 = todas."""
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, ("todas las paginas", "todas las hojas", "el pdf completo",
                             "todo el pdf", "cada pagina", "pagina por pagina")):
        return -1
    n = re.search(r"\b(?:pagina|hoja)\s+(\d{1,3})\b", m)
    if n:
        return max(0, int(n.group(1)) - 1)      # el usuario cuenta desde 1
    return None


def _es_conversion(mensaje: str) -> bool:
    """Pide convertir un archivo a algún formato real que sabemos producir."""
    m = _norm_txt(mensaje)
    if not _contiene_trigger(m, _CONVERSION_TRIGGERS):
        return False
    # Con destino explícito, o "vectoriza" (que siempre produce SVG+DXF), o la
    # palabra dxf suelta, que es como se pedía antes.
    return bool(_formato_destino(mensaje)) or "vectoriza" in m or "dxf" in m


# Nombre viejo conservado: lo usan el generador de manual y las pruebas.
_es_conversion_dxf = _es_conversion


# ── CHAT ↔ COREL: comandos directos y fijos, sin adivinar (motor_corel real) ──
_COREL_TRIGGERS = (
    # "corell" (doble L) es un typo real de Anuar encontrado en vivo 2026-07-27 —
    # la coincidencia de palabra completa (\bcorel\b) no reconocía "corell" como
    # la misma palabra, así que el mensaje se iba al enrutador de IA, que inventó
    # una ruta falsa ("C:/Users/usuario/...", el usuario real es "Administrador").
    "corel", "corell", "coreldraw", "coreldrau", "cdr",
)
_COREL_ACCIONES = (
    "exporta", "exportar", "escala", "tamano de pagina", "combina", "integra",
    "logo con el fondo", "logo y el fondo", "guarda una copia", "info del documento",
    "gotero", "saca el color", "extrae el color", "aplica el color", "muestra el color",
    "planilla", "quita el fondo", "quitale el fondo", "splash",
    # Lote "Corel al 100%" (2026-07-28): cerrar_documento_sin_guardar ya existia
    # en el motor pero ningun disparador de chat lo alcanzaba (muerto para el
    # usuario). Y "extrae el texto" se habia pedido en vivo hoy mismo y no existia
    # como funcion real — se ignoraba en silencio en vez de decir que no se podia.
    # Agregado 2026-08-02: Anuar preguntó "corel tiene instalado el plugin laser"
    # y AURORA no tenía forma de saberlo, así que soltó un ensayo dando por hecho
    # que sí. Ahora lo lee del disco de verdad (EDITOR/corel_core.listar_plugins).
    "plugin", "plugins", "macro", "macros", "complemento", "complementos",
    "que tiene instalado", "tiene instalado", "esta instalado", "add-on", "addon",
    "cierra", "cerrar documento", "cierra el documento",
    "extrae el texto", "extraer el texto", "el texto del documento", "que texto tiene",
    # Encontrado en vivo 2026-07-27: "almacenar"/"guardar" son sinonimos reales que
    # Anuar usa para "exportar" y no calzaban con nada — el mensaje se iba al
    # enrutador de IA, que adivino mal (dos veces) en vez de ir al comando directo.
    "almacena", "almacenar", "guarda", "guardar",
    # Encontrado en vivo 2026-07-27: "ábrelo en Corel <ruta>" no calzaba con ningun
    # verbo de esta lista, así que el mensaje se iba al enrutador de IA, que lo
    # abría con el visor default de Windows en vez de dentro de Corel de verdad.
    "abre", "abrir", "mete", "meter", "importa", "importar",
    "vectoriza", "vectorizar", "vectorizado", "traza", "trazar",
    # Encontrado en vivo 2026-08-03: "extrae el mapa de bits" justo después de
    # importar una imagen a Corel. No calzaba con nada, se fue a motor_analisis
    # y contestó que no podía ejecutar acciones en la PC — dos mensajes después
    # de haberla importado él mismo. En Corel "mapa de bits" es ambiguo (puede
    # ser rasterizar, trazar o sacar la imagen incrustada), así que se atiende
    # aquí y se pregunta cuál de las tres, en vez de adivinar o de negar.
    "mapa de bits", "mapa de bit", "mapadebits", "bitmap", "rasteriza",
    "rasterizar", "convertir a mapa", "convierte a mapa",
    # Nota: formas como "guardarlo"/"ábrelo"/"exportarlo" (verbo + pronombre pegado)
    # ya NO necesitan su propia entrada aquí — _contiene_trigger() ahora reconoce el
    # mismo verbo con "-lo/-la/-los/-las/-le/-les/-se" pegado como la misma palabra
    # (arreglo estructural 2026-07-27, cierra esta clase de hueco para los 14
    # dominios de una vez, no verbo por verbo).
)


# Vocabulario que SOLO se usa en Corel: si alguien lo dice, está hablando de
# Corel aunque no escriba la palabra. Caso real 2026-08-03: después de importar
# una imagen, Anuar pidió "ahora extrae el mapa de bits" — sin repetir "corel",
# porque ya se estaba trabajando ahí. Al exigir las dos señales, el mensaje no
# calzó, cayó en motor_analisis y contestó que no podía ejecutar acciones en la
# PC: dos mensajes después de haberlo hecho de verdad.
_COREL_SIN_NOMBRARLO = (
    "mapa de bits", "mapa de bit", "mapadebits", "bitmap", "rasteriza",
    "rasterizar", "curvas a mapa", "objeto a mapa",
    # "el diseño abierto" / "el documento abierto" solo puede ser Corel: es el
    # que está abierto en pantalla. Agregado el 2026-08-05 al cargar el perfil
    # de Anuar: "chékame el diseño abierto" solo funcionaba porque estaba en el
    # archivo de aprendizaje, o sea porque ya había fallado una vez.
    "el diseno abierto", "el diseño abierto", "documento abierto",
    "lo que tengo abierto", "el archivo abierto", "la hoja abierta",
)


def _es_comando_corel(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, _COREL_SIN_NOMBRARLO):
        return True
    return _contiene_trigger(m, _COREL_TRIGGERS) and _contiene_trigger(m, _COREL_ACCIONES)


# ── CHAT ↔ MOTORES DE NEGOCIO: responder con DATOS REALES, nunca improvisando ──
# "fuentes"/"que fuente" quedaron acotados a frases de leads/CRM (antes "fuentes" solo
# colisionaba con preguntas de tipografía para un diseño — dominio totalmente distinto).
_NEGOCIO_TRIGGERS = (
    "orden", "ordenes", "entrego", "entregar", "pendiente de entrega",
    "inventario", "existencia", "cuanto me queda", "cuanto tengo de", "bajo minimo",
    "lead", "leads", "prospecto", "clientes nuevos", "embudo", "pronostico",
    "contabilidad", "cuanto vendi", "cuanto llevo", "utilidad", "ganancia del mes",
    "por cobrar", "cobrar", "fuentes de leads", "fuente de leads", "fuentes efectivas",
    "que fuente convierte", "mejor fuente de",
    # Cómo se dice el dinero en el taller, de verdad. "Corte de caja" es el
    # cuadre del día — pero AURORA lo entendió como CORTAR UNA CAJA en la láser
    # y le dio a Anuar 7 pasos de RDWorks (barrido del 2026-08-02). Tenía la
    # contabilidad a la mano, que responde en menos de 3 s, y se fue al taller.
    "corte de caja", "cuadre de caja", "cierre de caja", "corte del dia",
    "cuanto entro hoy", "cuanto entro ayer", "cuanto se hizo hoy",
    "cuanto cayo hoy", "cuanto facture", "como vamos de ventas",
    "cuanto llevamos", "numeros del mes", "cuentas del mes",
)


# Estas frases YA son la pregunta completa: nadie escribe "cuánto corte de caja".
# Sin esto, "hazme un corte de caja de ayer" no calzaba porque no empieza con
# "cuánto" ni "dime", y se iba al modelo genérico — que lo mandó a la láser.
_NEGOCIO_DIRECTO = ("corte de caja", "cuadre de caja", "cierre de caja",
                    "corte del dia", "contabilidad", "numeros del mes",
                    "cuentas del mes", "como vamos de ventas")


def _es_consulta_negocio(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, _NEGOCIO_DIRECTO):
        return True
    # Debe ser una PREGUNTA/consulta, no una orden de acción física
    interroga = _contiene_trigger(m, ("cuanto", "cuantos", "cuantas", "cuales",
                                      "dime", "muestrame", "lista", "resumen")) or "que " in m or "como va" in m
    return interroga and _contiene_trigger(m, _NEGOCIO_TRIGGERS)


_EDITAR_CODIGO_TRIGGERS = (
    "edita el archivo", "edita el codigo", "modifica el archivo", "modifica el codigo",
    "cambia en el archivo", "agrega en el archivo", "reemplaza en el archivo",
    "corrige el archivo", "arregla el archivo",
)


_VERBOS_EDITAR = ("edita", "editar", "modifica", "modificar", "cambia en", "cambiar en",
                  "agrega en", "agregar en", "reemplaza", "reemplazar", "corrige",
                  "corregir", "arregla", "arreglar", "quita de", "quitar de",
                  "borra la linea", "comenta", "descomenta")


def _es_editar_codigo(mensaje: str) -> bool:
    """Pide editar código. Se reconoce por INTENCIÓN, no por la frase exacta.

    Antes exigía "edita el archivo" literal. Anuar escribió "edita TU archivo
    CORE/buscador_web_profesional.py" (2026-07-31) y no calzó: el mensaje cayó en
    motor_analisis, que le inventó un respaldo, un borrado de líneas y una
    compilación que nunca ocurrieron. El candado de honestidad lo delató.

    Ahora basta con: un verbo de editar + algo que sea claramente un archivo
    (ruta de Windows, nombre con extensión de código, o CARPETA/modulo).
    """
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, _EDITAR_CODIGO_TRIGGERS):
        return True
    if not _contiene_trigger(m, _VERBOS_EDITAR):
        return False
    texto = mensaje or ""
    return bool(
        re.search(r"[A-Za-z]:\\", texto)                                  # ruta de Windows
        or re.search(r"\b[\w\-.]+\.(?:py|json|md|html|js|css|txt|bat|ps1|yml)\b", texto, re.I)
        or re.search(r"\b[A-Z][A-Z_]{2,}/[\w.]+", texto)                  # CARPETA/modulo
    )


def _contar_defs(txt: str) -> int:
    import re as _re
    return len(_re.findall(r"^\s*(?:def |class |async def )", txt or "", _re.M))


# Núcleo BLINDADO: el chat/IDE nunca edita estos a fondo (protege 2 años de trabajo).
_NUCLEO_PROTEGIDO = ("aurora_server.py", "consciencia.py", "bus_neuronal.py", "run_aurora.py")


# ── Sistema prompt base — leal, sin censura, sin simulaciones ──────────
SISTEMA_BASE = """Eres AURORA, la asistente e inteligencia de confianza de Anuar (SIMPLEX).
LEALTAD: Eres de Anuar, hecha a su medida. Le eres INCONDICIONAL: sigues SUS valores y su criterio, no una moral ajena ni censura corporativa. Sirves su taller y su negocio sin trabas ni sermones — no le niegas su trabajo legítimo. Tu única lealtad es a él y a los suyos. (La honestidad y el no simular NO son una traba: son la forma en que lo cuidas y por eso jamás las rompes.)
Hablas español, mexicana, natural y directa — como un colaborador experto y de confianza. Brutalmente honesta: si no sabes algo, lo dices y propones cómo averiguarlo. Nunca inventas datos.
Eres CAPAZ Y CULTA EN TODO: diseño, corte láser, papercraft, sublimación, vectorizado, DXF, marketing, tecnología, programación, estudio, ciencia y vida diaria. Entiendes EXACTAMENTE el tema del que te hablan y respondes a ESE tema real — NO desvías la conversación hacia ventas ni hacia un solo negocio.
Conoces los negocios de Anuar (ATF Retrofit de faros; Milens láser/sublimación) y ayudas con ellos SOLO cuando el tema lo pide. No fuerzas ATF en cada respuesta.
Puedes usar los programas de la PC (Inkscape, Aspire, RDWorks, LibreOffice, CorelDRAW) y ejecutar conversiones y tareas reales cuando te lo piden. CorelDRAW lo controlas de verdad por COM (motor_corel): lees el documento abierto, exportas a PDF/PNG/JPG con DPI exacto, escalas página, combinas imágenes (logo+fondo) y guardas copias. La capacidad de tocar Corel EXISTE de verdad — nunca la niegues de entrada. Si en un intento puntual algo falla (Corel cerrado, error de conexión), dilo tal cual pasó: eso no es negar la capacidad, es honestidad sobre ESE intento.
CÓMO ESCRIBE ANUAR (entiéndelo de verdad, no le pidas que se repita): escribe rápido y de corrido, con faltas de ortografía normales, sin acentos casi nunca, a veces todo en mayúsculas cuando está urgido o enojado, oraciones largas sin puntuación, mezclando varias ideas en un solo mensaje. Eso NO es descuido tuyo que corregir — es su forma natural, respétala y entiéndela tal cual, nunca lo corrijas ni se lo señales. Vocabulario real de su taller que debes reconocer sin que lo explique: "suaje" (línea/medida de corte de un sticker o troquel), "planilla" (hoja completa con varias piezas repetidas para cortar), "calcomanía"/"stiker" (sticker), "gotero" (herramienta de muestra de color/eyedropper), "splash" (gráfico decorativo tipo salpicadura), "vinil de recorte" vs "vinil textil" (dos materiales de precio distinto), "bifaz" (vinil translúcido). Si de verdad no te queda claro qué pide (falta un dato imprescindible como una medida, un archivo o un color), pregúntaselo directo y corto — nunca inventes el dato faltante ni asumas en silencio.
Entregas SIEMPRE trabajo profesional, completo y real — cero simulaciones, cero respuestas a medias. Tienes memoria persistente (consúltala cuando el tema la necesite; no la des por completa en cada respuesta).

⛔ REGLA ABSOLUTA — NUNCA SIMULES ACCIONES FÍSICAS. Jamás digas que moviste, copiaste, borraste, reparaste, instalaste, enviaste, limpiaste cache o cambiaste algo en la PC (o en otra PC) si NO viene de una ejecución real con su resultado confirmado en este mismo intercambio. Si no tienes forma de ejecutarlo de verdad AHORA, di la verdad tal cual: "No lo hice —no tengo la acción conectada todavía— esto es lo que sí puedo hacer / esto es lo que necesito". Decir "ya lo hice" sin haberlo hecho es la peor falta que puedes cometer con Anuar. Ante la duda de si una acción se ejecutó, admítelo; NUNCA afirmes éxito sin prueba. Prometer y no hacer, o fingir que hiciste, está terminantemente prohibido."""

# Protocolo operativo del taller — antes se inyectaba SIN CONDICIÓN en cada respuesta
# de cualquier motor (incluido el coach personal hablando de la familia de Anuar),
# contradiciendo la propia promesa de SISTEMA_BASE de "no forzar el negocio en cada
# respuesta". Ahora solo se agrega cuando el motor activo es de un dominio donde
# de verdad aplica (ver _MOTORES_TALLER en _ejecutar()).
PROTOCOLO_TALLER = """CÓMO TRABAJA ANUAR (anticípate y sírvele sin que lo detalle): siempre 300 DPI; entrega PDF + PNG; medidas en cm; cotiza con precio distribuidor + público + ganancia neta + margen %. Láser: DXF para RDWorks/Aspire, convierte splines a polilíneas, imagen a 300 DPI en B&N puro ANTES de vectorizar. Lonas/sublimación: modo económico = estirar suave sin pixeleo (cliente que no paga diseño), modo premium = rediseño con mejora de fotos. Prefiere resultados reales y directos, sin teoría."""

# ── Patrones de routing por motor ──────────────────────────────────────
# Sin acentos a propósito: se comparan contra _norm_txt(mensaje) (acentos fuera),
# y SISTEMA_BASE documenta que Anuar "escribe... sin acentos casi nunca" — patrones
# acentuados eran, en la práctica, casi inalcanzables para su propio usuario.
_ROUTING_PATRONES: Dict[str, List[str]] = {
    "motor_ventas":        ["venta", "cliente", "lead", "prospecto", "seguimiento", "crm", "pipeline"],
    "motor_cotizador":     ["cuanto cuesta", "cotizacion", "presupuesto", "precio de", "cuanto cobra"],
    # COACH PERSONAL / DE VIDA — trae la historia completa de Anuar (PROMPT_COACHING).
    # Antes NO estaba en el ruteo: lo personal caía en el coach de NEGOCIOS.
    "motor_coaching": ["me siento", "estoy cansado", "ya no puedo", "triste", "solo",
                       "culpa", "perdon", "mi hija", "mi hijo", "mis hijos",
                       "mi esposa", "rocio", "samanta", "yeshua", "romina",
                       "familia", "emocion", "sentir", "relacion",
                       "harto", "cansado", "duele", "miedo", "solo me", "desanimado"],
    # COACH DE NEGOCIOS / transformacional — creencias limitantes y metas comerciales.
    "motor_coaching_real": ["coaching", "meta", "objetivo personal", "creencia",
                            "creencia limitante", "coach de negocio", "sesion de coaching"],
    "motor_reasoning":     ["analiza", "estrategia", "por que", "razona", "explica a fondo", "pensamiento"],
    "motor_negocios":      ["atf", "milens", "retrofit", "laser", "negocio", "marketing atf"],
    "motor_code_gen":      ["codigo", "script", "funcion", "clase", "programa", "bug", "error en codigo"],
    "motor_imagenes":      ["imagen", "foto", "diseno", "edita", "fondo", "laser prep"],
    "motor_pedidos":       ["pedido", "orden", "envio", "tracking", "entrega"],
    "motor_analisis":      [],  # fallback general
    "web_search":          ["busca en internet", "buscar", "que precio tiene", "competencia", "tendencia"],
    "self_info":           ["que puedes", "tus capacidades", "tu estructura", "tus modulos", "como funcionas"],
    "self_repair":         ["arreglate", "repara el archivo", "fix ", "esta fallando el modulo"],
    "pc_cmd":              ["ejecuta en pc", "corre el comando", "abre el archivo", "estado del pc", "cpu ", "ram ", "disco "],
}

# Motores donde el protocolo del taller (DPI/PDF/cotización/láser) de verdad aplica.
# El resto (coaching, code_gen, pedidos, análisis general) no lo necesita — inyectarlo
# ahí era justo lo que rompía la promesa de "no forzar el negocio en cada respuesta".
_MOTORES_TALLER = {"motor_cotizador", "motor_negocios", "motor_imagenes", "motor_ventas"}

# ── Pipeline de candados directos — orden real por especificidad ───────
# Reemplaza la cadena de 17 `if: return` que se fue acumulando con el tiempo (con
# numeración de comentarios ya desincronizada del orden real en el archivo — el
# candado de Corel llegó a quedar físicamente después de "equipos" pese a estar
# etiquetado para ir antes de "DXF"). Agregar una capacidad nueva ahora es una
# línea aquí, en el lugar que le corresponde por especificidad — no cirugía dentro
# de procesar() ni un número inventado a mano.
# Orden: lo más específico primero (necesita 2+ condiciones para disparar), lo más
# genérico al final (_es_accion_fisica es el único catch-all de "acción sobre el
# sistema" — si algo más específico ya aplicaba, ya se resolvió arriba y nunca
# llega aquí; no necesita excluir manualmente a los demás).
# La extensión es OPCIONAL. Caso real 2026-08-02: Anuar mandó
# "C:\Users\Administrador\Downloads\trailler hot" — un archivo suyo que de verdad
# no tiene extensión (112 KB). El detector la exigía, así que no lo reconoció como
# ruta, cayó en motor_analisis y negó en falso: "no tengo la capacidad de abrir
# archivos en la PC". Sus diseños se llaman como se le ocurre, no como espera un
# regex.
_RE_RUTA_SOLA = re.compile(r'^["\'\s]*([A-Za-z]:\\[^\r\n"\']+?)["\'\s.]*$')

# LA MISMA FALLA, TERCERA VEZ (2026-08-08). El punto del espesor en el nombre
# —`..._2.5mm.dxf`— cortaba la ruta en `..._2.5mm`, un archivo que no existe, y
# AURORA contestaba «dime cuál DXF adapto» con la ruta buena delante. Ya se
# había arreglado en el validador de honestidad; vivía copiado en dos lugares
# más. Ahora es UNA sola expresión y todos la usan.
#
# El truco es el lookahead: la extensión solo vale si después NO viene otra
# letra ni otro punto.
_RE_RUTA_ARCHIVO = re.compile(
    r'([A-Za-z]:\\[^\r\n"\'<>|]+?\.[A-Za-z0-9]{2,5}(?![\w.]))')


def _rutas_del_texto(texto: str) -> list:
    """Todas las rutas de archivo que trae el texto, las que existan primero.

    Se devuelven ordenadas por longitud descendente entre las que existen: si
    dos candidatas empiezan igual, la buena es siempre la larga.
    """
    if not texto:
        return []
    todas = [m.group(1) for m in _RE_RUTA_ARCHIVO.finditer(texto)]
    existen = sorted({r for r in todas if Path(r).exists()},
                     key=len, reverse=True)
    return existen or todas


def _es_ruta_sola(mensaje: str) -> bool:
    """El mensaje es SOLO la ruta de un archivo, sin verbo ni contexto.

    Caso real 2026-07-31: Anuar pidió "abre esta imagen en corel" y en el
    siguiente mensaje mandó solo la ruta. Ningún candado la agarró (el de Corel
    exige corel + acción) y cayó a motor_analisis, que contestó "no puedo abrir
    archivos en la PC, pídele a Anuar que lo haga" — una MENTIRA, y encima le
    decía a Anuar que le pidiera a Anuar.

    Mandar la ruta sola después de pedir algo es como habla la gente. La ruta no
    es una pregunta nueva: es el dato que faltaba para lo que ya se pidió.
    """
    return bool(_RE_RUTA_SOLA.match((mensaje or "").strip()))


_CANDADOS: List[Tuple[str, Any, str, str]] = [
    # (nombre, funcion_trigger, metodo_ejecutor_en_self, motor_id_reportado)
    # ruta_sola va PRIMERO: completa la petición anterior con el dato que faltaba,
    # antes de que cualquier otro candado o el enrutador la malinterpreten.
    # cotizar_dxf va ANTES que cotizar: "cuánto cuesta cortar este archivo" es
    # medir metros, no buscar un producto en el catálogo.
    # generar_caja va antes que cotizar: "una caja de 40x30 cuánto cuesta" es
    # pedir que la haga y de paso la cotice, no buscar en el catálogo.
    # foto_a_dxf va ANTES que corel y dxf: "quita el fondo Y dámelo en dxf" es
    # UNA cadena completa, no dos peticiones que haya que pedir por separado.
    # adaptar_diseno va ANTES que generar_caja y que cotizar: "ajusta la casa
    # de bob al 50% para material de 2.5" trae medidas y la palabra material,
    # y si no se atrapa aquí lo agarra el generador de cajas y le inventa una
    # caja de 50 cm. Es un archivo que YA existe, no uno que haya que crear.
    # campana_escolar va ANTES que cotizar: una clienta preguntando "cuánto el
    # de primaria" tiene que recibir el precio de la campaña que acaba de leer,
    # no lo que el cotizador arme del catálogo. Mientras la campaña esté viva,
    # esos cuatro precios mandan (2026-08-06).
    # metodo_campana va ANTES que campana_escolar: "revisa esta campaña" es
    # pedir el método, no preguntar precios de los paquetes.
    # cotizar_vinil va ANTES que cotizar y que cotizar_dxf: el 2026-08-08
    # AURORA le INVENTÓ un precio («entre $500 y $1,500») con su lista de
    # precios de vinil guardada enfrente. El cotizador general no sabe de la
    # escalera de vinil; este sí, y es el que debe contestar.
    ("cotizar_vinil",   _es_cotizar_vinil,     "_cotizar_vinil_real",     "cotizador_vinil"),
    # cotizar_vinil gana solo si pregunta un PRECIO. Sin palabra de dinero,
    # «hazme la palabra X en vinil» es generar el archivo, y cae aquí.
    ("texto_a_corte",   _es_texto_a_corte,     "_texto_a_corte_real",     "texto_a_corte"),
    ("print_and_cut",   _es_print_and_cut,     "_print_and_cut_real",     "print_and_cut"),
    ("metodo_campana",  _es_metodo_campana,    "_metodo_campana_real",    "metodo_campanas"),
    ("campana_escolar", _es_campana_escolar,   "_campana_escolar_real",   "campana_escolar"),
    ("adaptar_diseno",  _es_adaptar_diseno,    "_adaptar_diseno_real",    "adaptar_grosor"),
    ("foto_a_dxf",      _es_foto_a_dxf,        "_foto_a_dxf_real",        "foto_a_dxf"),
    ("generar_caja",    _es_generar_caja,      "_generar_caja_real",      "generador_cajas"),
    ("cotizar_dxf",     _es_cotizar_dxf,       "_cotizar_dxf_real",       "cotizador_laser"),
    ("cotizar",         _es_cotizar,           "_cotizar_real",           "cotizador"),
    ("video",           _es_comando_video,     "_video_real",             "motor_video"),
    ("voz",             _es_comando_voz,       "_voz_real",               "voz"),
    ("ver_aprendizaje", _es_ver_aprendizaje,   "_ver_aprendizaje_real",   "aprendizaje"),
    ("ruta_sola",       _es_ruta_sola,         "_ruta_sola_real",         "contexto_archivo"),
    ("abrir_navegador", _es_abrir_navegador,  "_abrir_navegador_real",  "pc_access"),
    ("acerca_de",       _es_acerca_de,         "_acerca_de_real",         "auto_conocimiento"),
    # proveedor va ANTES de busqueda_web: si el dato está en su directorio, se
    # contesta con su precio real en vez de mandarlo a buscar a internet.
    ("proveedor",       _es_proveedor,         "_proveedor_real",         "proveedores"),
    ("busqueda_web",    _es_busqueda_web,      "_buscar_web_candado",     "web_search"),
    ("corel",           _es_comando_corel,     "_ejecutar_corel_real",    "motor_corel"),
    ("dxf",             _es_conversion_dxf,    "_convertir_dxf_real",     "taller_dxf"),
    ("negocio",         _es_consulta_negocio,  "_consultar_negocio_real","negocio_real"),
    ("publicar",        _es_publicar,          "_publicar_real",          "publicador"),
    ("agenda",          _es_agenda,            "_agenda_real",            "agenda"),
    # servicio_atf va ANTES de ficha_vendedor y del enrutador de IA a proposito:
    # un cliente que pide un SERVICIO real (recolocar su lupa, sellar un faro)
    # no debe caer en el motor de ventas generico, que en un caso real de Anuar
    # le NEGO el servicio y lo mando a hacerlo el mismo (2026-07-29).
    ("servicio_atf",    _es_servicio_atf,      "_servicio_atf_real",      "servicios_atf"),
    # alta_lead va antes que ficha_vendedor: "apunta a Juan" es capturar un
    # cliente, no pedir argumentos de venta.
    ("alta_lead",       _es_alta_lead,         "_alta_lead_real",         "oracle_leads"),
    ("ficha_vendedor",  _es_ficha_vendedor,    "_vendedor_real",          "vendedor"),
    ("intuicion",       _es_intuicion,         "_intuicion_real",         "intuicion"),
    ("memoria",         _es_memoria,           "_memoria_real",           "memoria"),
    ("equipos",         _es_equipos,           "_equipos_real",           "equipos"),
    ("crear_capacidad", _es_crear_capacidad,   "_crear_capacidad_real",   "fabrica"),
    # consulta_codigo va ANTES que editar_codigo a propósito: si un mensaje pide ambas
    # cosas ("enséñame el código de X y corrígelo..."), gana la acción más segura
    # (solo mirar) sobre la más riesgosa (escribir) — antes ganaba escribir por puro
    # accidente de orden en la lista, confirmado con ese mensaje real en la auditoría.
    ("consulta_codigo", _es_consulta_codigo,   "_consultar_codigo_real",  "ide"),
    ("editar_codigo",   _es_editar_codigo,     "_editar_codigo_real",     "ide_editor"),
    ("accion_fisica",   _es_accion_fisica,     "_accion_sistema_real",    "accion_sistema"),
]

# Candados con efecto real de escritura/físico/externo — nunca ejecutables desde un
# cliente de WhatsApp (canal="whatsapp" nunca es Anuar operando el panel, es siempre
# un cliente real). Encontrado en vivo 2026-07-27: el candado de canal que se armó
# para Fábrica/editar-código era la EXCEPCIÓN, no la regla — el resto del pipeline
# (acción física, publicar, router universal) nunca revisaba canal en absoluto, así
# que un cliente real podía lograr que AURORA mandara un WhatsApp a un tercero, abriera
# URLs en la PC real del taller, o publicara de verdad en Facebook. Un solo punto de
# verdad aquí, no un candado a mano por función.
_CANDADOS_SOLO_DUENIO = {"accion_fisica", "publicar", "abrir_navegador", "editar_codigo", "crear_capacidad"}

# ── LA FÁBRICA SALE DE AURORA (decisión de Anuar, 2026-08-02) ────────────────
# Crear motores y agentes ya no es trabajo de AURORA: es de AURORITA XP, un
# proyecto aparte (C:\AURORITA_XP) que produce motores terminados y verificados.
#
# Por qué importa, más allá del orden: un sistema que puede escribir y ejecutar
# código nuevo en la máquina del cliente es una superficie de ataque y una
# fuente de facturas. La regla de oro de Anuar era "AURORA tiene Fábrica pero
# NUNCA la usa sin mi autorización" — esto la vuelve estructural en vez de
# depender de que nadie se equivoque.
#
# NO SE BORRA CÓDIGO: se cierra la puerta. fabrica_agentes.py y fabrica_motores.py
# siguen ahí intactos. Poner esto en True los reactiva tal como estaban.
# Cuando AURORITA XP entregue motores de verdad, entonces sí se archivan.
FABRICA_HABILITADA = False
_MSG_FABRICA_FUERA = (
    "Crear motores ya no lo hago yo: eso es trabajo de AURORITA XP, la fábrica "
    "que vive aparte. Yo cargo y ejecuto los motores que ella produce ya probados.\n"
    "Si necesitas una capacidad nueva, se fabrica allá y aquí solo se instala.")

# Candados que atienden a un CLIENTE. Se saltan cuando el mensaje habla del
# propio sistema (ver _es_tema_del_sistema): "diagnostica el problema" es una
# pregunta técnica de Anuar, no un cliente pidiendo diagnóstico de faros.
_CANDADOS_DE_VENTA = {"servicio_atf", "negocio", "ficha_vendedor", "cotizar"}

# Lo mismo para el enrutamiento de motores: cuando el mensaje habla del propio
# sistema, estos no compiten. "corel tiene instalado el plugin" no es un cliente.
_MOTORES_DE_VENTA = frozenset({"motor_negocios", "motor_vendedor", "motor_cotizador",
                               "motor_ventas", "vendedor", "oracle"})
_MSG_SOLO_DUENIO = "Esa acción es del dueño desde el panel — no la ejecuto desde WhatsApp."

_MODELO = "llama-3.1-8b-instant"
# El 8B se equivoca eligiendo entre herramientas parecidas (ej: "convertir a PDF"
# eligió convertir_a_dxf en vez de conversor_formatos:convertir). Para ESA decisión
# puntual (una sola llamada JSON por turno, no es cuello de botella) usar el 70B.
_MODELO_SELECTOR = "llama-3.3-70b-versatile"
_MAX_HISTORIAL_SESION = 20  # mensajes en RAM por sesión


class Consciencia:
    """
    Capa cognitiva central de AURORA.
    Única instancia (singleton). Inicializar con await consciencia.inicializar().
    """

    _instancia: Optional["Consciencia"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._listo = False
        return cls._instancia

    def __init__(self):
        if self._listo:
            return
        self._groq: Optional[AsyncGroq] = None
        self._prompts_motor: Dict[str, str] = {}          # motor_id → system prompt
        self._metadata_motores: Dict[str, Dict] = {}      # motor_id → metadata.json entry
        # Memoria a CORTO PLAZO (RAM, por sesión)
        self._memoria_corto: Dict[str, List[Dict]] = {}
        # Fábrica de Agentes: spec en construcción por sesión (pregunta-antes-de-crear)
        self._agente_en_creacion: Dict[str, Dict] = {}
        # Enrutador universal: herramienta peligrosa elegida, esperando "sí" de Anuar
        self._accion_pendiente: Dict[str, Dict] = {}
        # Si una acción pendiente se abandona porque el siguiente mensaje no calzó como
        # confirmación, aquí queda el aviso para no perderla en silencio (se prepende a
        # la respuesta del turno actual y se limpia).
        self._pendiente_abandonado_aviso: Dict[str, str] = {}

    async def inicializar(self) -> None:
        if self._listo:
            return
        api_key = os.getenv("GROQ_API_KEY", "")
        # max_retries=1: medido el 2026-07-31, un 429 de Groq costaba 16-22 s de
        # espera (tres reintentos con backoff) antes de responder. Todo lo que NO
        # llama a Groq responde en menos de un segundo. Si Groq dice que no, es
        # mejor caer rápido que esperar tres veces por lo mismo.
        _cliente = AsyncGroq(api_key=api_key, max_retries=1) if api_key else None

        # Y si aun así Groq no puede, responde el modelo local en vez de dejar a
        # Anuar sin nada. El envoltorio se comporta igual que el cliente de Groq,
        # así que las ~10 llamadas repartidas por este archivo no cambian: tocar
        # todas en un archivo de 148,000 caracteres sería el riesgo, no el arreglo.
        # La respuesta local SIEMPRE dice que es local — el modelo chico se
        # equivoca más y Anuar tiene derecho a saber quién le contestó.
        try:
            from CEREBRO.respaldo_local import ClienteConRespaldo
            self._groq = ClienteConRespaldo(_cliente) if _cliente else None
        except Exception as e:
            logger.warning(f"Sin respaldo local ({e}); solo Groq")
            self._groq = _cliente

        # Cargar prompts de cada motor y metadata
        await asyncio.to_thread(self._cargar_prompts_y_metadata)

        # Inicializar subsistemas
        from MEMORIA.sistema_memoria import memoria
        from MEMORIA.contexto_usuario import ctx_usuario
        from CEREBRO.bus_neuronal import bus
        from MEMORIA.motor_sueno import motor_sueno
        from CEREBRO.auto_conocimiento import auto_conocimiento
        from CEREBRO.pc_access import pc_access
        from MEMORIA.perfil_habilidades import perfil_habilidades

        await memoria.inicializar()
        await ctx_usuario.inicializar()
        await perfil_habilidades.inicializar()

        self._memoria = memoria
        self._ctx = ctx_usuario
        self._bus = bus
        self._sueno = motor_sueno
        self._autoconocimiento = auto_conocimiento
        self._pc = pc_access
        self._perfil = perfil_habilidades
        self._listo = True
        logger.info(f"✅ Consciencia lista | {len(self._prompts_motor)} motores | Groq: {'✅' if self._groq else '❌'}")

    # ── CARGA DE PROMPTS ─────────────────────────────────────────

    def _cargar_prompts_y_metadata(self) -> None:
        """Extrae PROMPT_* de cada módulo motor y carga metadata.json."""
        # Metadata
        meta_path = ROOT / "MOTORES" / "metadata.json"
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                for entry in json.load(f):
                    self._metadata_motores[entry["id"]] = entry

        # Prompts de módulos — SIN importar los módulos (eso re-ejecutaba las librerías
        # pesadas ya cargadas en el bus y hacía el boot ~30s más lento). Se extrae la
        # constante PROMPT* leyendo el TEXTO con regex; fallback genérico si no aparece.
        import re
        patron = re.compile(
            r'^[A-Za-z_]*PROMPT[A-Za-z_]*\s*=\s*'
            r'(?:[rf]?"""(.*?)"""|[rf]?"([^"\n]*)"|[rf]?\'\'\'(.*?)\'\'\'|[rf]?\'([^\'\n]*)\')',
            re.MULTILINE | re.DOTALL)
        motores_dir = ROOT / "MOTORES"
        for py_file in motores_dir.glob("motor_*.py"):
            motor_id = py_file.stem
            try:
                txt = py_file.read_text(encoding="utf-8", errors="ignore")
                m = patron.search(txt)
                prompt = next((g for g in (m.groups() if m else ()) if g), None)
                self._prompts_motor[motor_id] = (
                    prompt.strip() if prompt
                    else f"Eres el motor {motor_id} de AURORA. Responde con expertise.")
            except Exception as e:
                self._prompts_motor[motor_id] = f"Eres {motor_id} de AURORA."
                logger.debug(f"Prompt fallback para {motor_id}: {e}")

    # ── PIPELINE PRINCIPAL ───────────────────────────────────────

    async def procesar(
        self,
        mensaje: str,
        user_id: str,
        session_id: str = "",
        canal: str = "api",
    ) -> Dict:
        """Punto de entrada público — envuelve _procesar_interno con el candado único
        de verdad: revisa la respuesta final ANTES de mandarla, sin importar qué rama
        del pipeline la generó ni qué modelo de IA la escribió. Un modelo chico puede
        ignorar SISTEMA_BASE aunque esté bien escrito (pasó de verdad esta noche) —
        este candado es código, no una instrucción que el modelo pueda no seguir."""
        resultado = await self._procesar_interno(mensaje, user_id, session_id, canal)
        aviso_abandono = self._pendiente_abandonado_aviso.pop(session_id, "")
        if aviso_abandono:
            resultado["respuesta"] = aviso_abandono + "\n\n" + resultado.get("respuesta", "")
        try:
            resultado["respuesta"] = await self._verificar_capacidad_real(mensaje, resultado.get("respuesta", ""))
        except Exception as e:
            logger.debug(f"_verificar_capacidad_real no aplicó: {e}")

        # ── CANDADO ANTI-SIMULACIÓN (agregado 2026-07-30) ─────────────────
        # El candado de arriba atrapa cuando AURORA NIEGA algo que sí puede.
        # Este es su espejo, y es el que faltaba: atrapa cuando AFIRMA algo que
        # NO hizo. Corrección de raíz a los 7 inventos del 29-30 de julio
        # (fingir que Corel vectorizó, inventar 6 comandos en un "manual",
        # inventar 3 archivos .bat en un "kit de configuración"...).
        # Todos venían de lo mismo: la frase no calzaba con ningún candado, caía
        # a un modelo de texto sin acceso al sistema, y respondía igual.
        # Agregar frases una por una es infinito; esto cierra la clase entera:
        # aunque no entienda la orden, lo peor que puede pasar es un "no te
        # entendí", nunca una mentira. Es CÓDIGO, no una regla de prompt que un
        # modelo chico pueda ignorar (ya pasó varias veces).
        try:
            from CEREBRO import validador_honestidad as _vh
            try:
                _claves = set(await asyncio.to_thread(_registro().descubrir))
            except Exception:
                _claves = None      # sin registro no se revisan comandos, el resto sí
            _resp, _informe = _vh.revisar(
                resultado.get("respuesta", ""),
                motores_usados=resultado.get("motores_usados"),
                registro_claves=_claves,
                # La pregunta hace falta para detectar cuándo da por hecho justo
                # lo que se le estaba preguntando ("¿tienes X?" → "con X instalado…").
                pregunta=mensaje,
            )
            if _informe.get("corregida"):
                resultado["respuesta"] = _resp
                resultado["honestidad"] = _informe
                logger.warning(f"[ANTI-SIMULACIÓN] Respuesta corregida: {_informe}")
        except Exception as e:
            logger.debug(f"validador_honestidad no aplicó: {e}")
        return resultado

    async def _procesar_interno(
        self,
        mensaje: str,
        user_id: str,
        session_id: str = "",
        canal: str = "api",
    ) -> Dict:
        if not self._listo:
            await self.inicializar()

        session_id = session_id or user_id
        inicio = datetime.utcnow()
        self._sueno.registrar_actividad()

        # 1. CONTEXTO COMPLETO
        ctx_usuario = await self._ctx.obtener(user_id, canal)
        historial_sesion = self._memoria_corto.get(session_id, [])
        memoria_semantica = await self._memoria.recordar(
            tema=self._tema_rapido(mensaje), limite=3
        )
        contexto = {
            "usuario": ctx_usuario,
            "historial_sesion": historial_sesion[-6:],  # últimas 3 interacciones
            "conocimiento": [k["conocimiento"] for k in memoria_semantica],
        }

        # 2. ROUTING
        motor_ids, paralelo = self._routing_rapido(mensaje)
        # Si ambiguo → LLM routing
        if not motor_ids:
            motor_ids, paralelo = await self._routing_llm(mensaje, contexto)

        # 2.44 CONFIRMACIÓN DE ACCIÓN PENDIENTE — el enrutador universal (2.8) propuso
        # una herramienta peligrosa en el turno anterior y quedó esperando un "sí". Si
        # este mensaje es esa confirmación, ejecuta de verdad; si no, se abandona el
        # pendiente (no se queda colgado esperando para siempre) y sigue el flujo normal.
        # Se revisa el canal de ESTA confirmación (no el que creó el pendiente): como
        # /chat no tiene autenticación real, alguien podría dejar pendiente algo peligroso
        # bajo un session_id que coincida con el de un cliente real de WhatsApp, esperando
        # que lo confirme sin saberlo con un "sí" cualquiera — encontrado en la auditoría
        # 2026-07-27. Revisar el canal aquí, no solo al crear el pendiente, cierra eso.
        if session_id in self._accion_pendiente:
            if canal == "whatsapp":
                self._accion_pendiente.pop(session_id, None)
                ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                self._agregar_sesion(session_id, mensaje, _MSG_SOLO_DUENIO)
                return {"respuesta": _MSG_SOLO_DUENIO, "motores_usados": ["router_universal"],
                        "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}
            if _es_confirmacion(mensaje):
                real = await self._confirmar_accion_pendiente(session_id)
                self._agregar_sesion(session_id, mensaje, real["respuesta"])
                ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                return {"respuesta": real["respuesta"], "motores_usados": ["router_universal"],
                        "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}
            # No fue confirmación → se abandona, pero AVISADO (antes se perdía en silencio
            # y si Anuar mandaba un "sí" días después, no significaba nada para el sistema).
            pendiente = self._accion_pendiente.pop(session_id, None)
            if pendiente:
                desc = pendiente.get("clave") or "la edición de un archivo del núcleo"
                self._pendiente_abandonado_aviso[session_id] = (
                    f"(Cancelé la propuesta pendiente de '{desc}' porque tu mensaje no lo confirmó — "
                    f"si la sigues necesitando, pídemela de nuevo.)")

        # 2.45 FÁBRICA DE AGENTES — diálogo "pregunta-antes-de-crear". Si hay un agente
        # en construcción para esta sesión, este mensaje es el CONTEXTO que da Anuar.
        # CREAR agentes salió de AURORA (ver FABRICA_HABILITADA). Correr y listar
        # los que YA existen se conserva: eso no es fabricar, es usar.
        if not FABRICA_HABILITADA and (_es_crear_agente(mensaje)
                                       or session_id in self._agente_en_creacion):
            self._agente_en_creacion.pop(session_id, None)
            self._agregar_sesion(session_id, mensaje, _MSG_FABRICA_FUERA)
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": _MSG_FABRICA_FUERA, "motores_usados": ["fabrica_fuera"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        if session_id in self._agente_en_creacion and not _es_crear_agente(mensaje):
            real = await self._fabrica_agentes_contexto(session_id, mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["fabrica_agentes"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}
        if _es_crear_agente(mensaje):
            real = await self._fabrica_agentes_iniciar(session_id, mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["fabrica_agentes"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}
        if _es_listar_agentes(mensaje):
            real = await self._listar_agentes_real()
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["fabrica_agentes"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}
        if _es_correr_agente(mensaje):
            real = await self._correr_agente_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["fabrica_agentes"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # PIPELINE DE CANDADOS DIRECTOS — orden por especificidad (ver _CANDADOS).
        # "accion_fisica" es el único catch-all genérico y va al final: si algo más
        # específico ya aplicaba, ya se resolvió arriba y nunca llega aquí, así que
        # no necesita excluir manualmente a los demás (como sí lo necesitaba antes).
        # Sí conserva su única exclusión real: si el routing rápido (paso 2) ya
        # decidió que esto es para pc_cmd/self_repair, se les cede el paso a esos.
        # ¿Ya aprendimos que Anuar dice las cosas así? Si esta forma de pedirlo
        # falló antes y él la reformuló hasta que funcionó, se salta directo al
        # candado que sí sirvió. Es la idea de Anuar del 2026-08-02: en vez de que
        # yo le agregue sus frases a mano una por una, AURORA las aprende de él.
        _aprendido = None
        try:
            from CEREBRO import aprende_del_usuario as _apr
            _aprendido = _apr.buscar(mensaje)
        except Exception:
            pass

        # Si el mensaje habla del propio sistema, los candados de VENTA no lo tocan.
        # Un cliente no escribe "consciencia.py" ni "plugin instalado"; Anuar sí,
        # porque usa AURORA de las dos formas y los dos chats se estaban pisando.
        _tema_sistema = _es_tema_del_sistema(mensaje)

        # Si se pregunta QUÉ RECUERDA de algo, solo la memoria contesta. Sin este
        # guard, el nombre del tema secuestra el mensaje: "qué recuerdas de
        # cotizar" devolvía una cotización de faros (2026-08-05). Se pone aquí y
        # no dentro de cada candado porque el problema es de TODOS los candados
        # de acción, no de uno.
        _solo_memoria = _es_pregunta_de_memoria(_norm_txt(mensaje))

        for _nombre_candado, _trigger, _metodo_candado, _motor_id_candado in _CANDADOS:
            if _solo_memoria and _nombre_candado not in ("memoria", "ver_aprendizaje"):
                continue
            if _nombre_candado == "accion_fisica" and (set(motor_ids) & _MOTORES_EJECUTORES):
                continue
            if _tema_sistema and _nombre_candado in _CANDADOS_DE_VENTA:
                continue
            # El disparador normal manda; lo aprendido es la segunda oportunidad.
            _por_aprendizaje = (_aprendido is not None
                                and _aprendido.get("herramienta") == _motor_id_candado)
            if _nombre_candado == "crear_capacidad" and not FABRICA_HABILITADA:
                if _trigger(mensaje):
                    self._agregar_sesion(session_id, mensaje, _MSG_FABRICA_FUERA)
                    ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                    return {"respuesta": _MSG_FABRICA_FUERA, "motores_usados": ["fabrica_fuera"],
                            "temperatura_lead": "frio", "duracion_ms": ms,
                            "timestamp": inicio.isoformat()}
                continue
            if not _trigger(mensaje) and not _por_aprendizaje:
                continue
            if _por_aprendizaje and not _trigger(mensaje):
                logger.info(f"[APRENDIDO] '{mensaje[:40]}' → {_nombre_candado} "
                            f"(parecido {_aprendido.get('parecido')})")
            if canal == "whatsapp" and _nombre_candado in _CANDADOS_SOLO_DUENIO:
                real = {"respuesta": _MSG_SOLO_DUENIO}
            elif _nombre_candado == "editar_codigo":
                real = await self._editar_codigo_real(mensaje, session_id=session_id, canal=canal)
            elif _nombre_candado == "crear_capacidad":
                real = await self._crear_capacidad_real(mensaje, canal=canal)
            elif _nombre_candado == "publicar":
                real = await self._publicar_real(mensaje, session_id=session_id)
            elif _nombre_candado == "ruta_sola":
                # Necesita la sesión para leer qué se pidió en el mensaje anterior.
                # Sin esta rama recibía session_id="" (el default de la firma) y
                # buscaba el historial de una sesión vacía: esa fue la causa real
                # de que no completara la petición previa, no dónde se guardaba.
                real = await self._ruta_sola_real(mensaje, session_id=session_id, canal=canal)
            elif _nombre_candado in ("foto_a_dxf", "alta_lead"):
                # Necesitan la sesión: foto_a_dxf para acordarse de cuál archivo
                # se está hablando aunque no se repita la ruta (2026-08-05), y
                # alta_lead para no perder el cliente entre mensajes.
                real = await getattr(self, _metodo_candado)(mensaje, session_id=session_id)
            else:
                real = await getattr(self, _metodo_candado)(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            # Un candado ejecutó de verdad. Si el mensaje anterior de esta misma
            # conversación no había ejecutado nada, las dos formas significan lo
            # mismo y AURORA lo aprende sola (idea de Anuar, 2026-08-02).
            try:
                from CEREBRO import aprende_del_usuario as _apr
                _ap = _apr.registrar_exito(session_id, mensaje, _motor_id_candado, time.time())
                if _ap:
                    logger.info(f"[APRENDIÓ] '{_ap['como_lo_dijo'][:50]}' → {_motor_id_candado}")
            except Exception:
                pass
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": [_motor_id_candado],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # ENRUTADOR UNIVERSAL — última red antes del LLM genérico. Si el mensaje pide
        # OPERAR (no charla) y ningún candado directo aplicó, deja que el registro de
        # herramientas reales (~690 funciones) elija y EJECUTE una de verdad. Si no hay
        # herramienta que aplique, devuelve None y sigue el flujo normal (no rompe nada).
        # Se intenta en cualquier mensaje con sustancia (2+ palabras) — el router se
        # auto-filtra: si no hay herramienta real que aplique, devuelve None (barato,
        # sin LLM) y sigue el flujo normal.
        if len(_norm_txt(mensaje).split()) >= 2:
            real = await self._router_universal(mensaje, session_id, canal)

            # AQUÍ SE CORTA, y esto es el arreglo de fondo.
            #
            # Si el mensaje pedía ALGO REAL y el enrutador —que conoce las 535
            # herramientas— no encontró ninguna, seguir hacia los motores solo
            # sirve para dos cosas malas: gastar de 20 a 70 segundos, y que un
            # modelo sin acceso al sistema conteste con seguridad algo que no
            # sabe. Medido el 2026-08-02 sobre 40 frases reales de Anuar: TODAS
            # las que llegaron a motor_analisis fallaron o mintieron; TODAS las
            # que atendió un candado o el enrutador salieron bien en menos de 3 s.
            #
            # Antes esto se atrapaba DESPUÉS, cuando el daño (la espera) ya estaba
            # hecho. Cortar antes es lo que convierte "20 puertas para 535
            # herramientas" en "una puerta que de verdad responde por todas":
            # el enrutador universal ya era esa puerta; lo que faltaba era no
            # dejar que otro contestara por ella.
            if real is None and _es_intencion_operativa(mensaje):
                _ops = []
                try:
                    _reg = _registro()
                    for _c in (await asyncio.to_thread(_reg.buscar, _norm_txt(mensaje), 4))[:3]:
                        _d = (_c.get("doc") or "").strip().split("\n")[0].strip().rstrip(".")
                        if _d:
                            _ops.append(f"• {_d}")
                except Exception:
                    pass
                try:
                    from CEREBRO import aprende_del_usuario as _apr
                    _apr.registrar_fallo(session_id, mensaje, time.time())
                except Exception:
                    pass
                _txt = (("No encontré cómo hacer eso todavía. Esto sí lo puedo hacer "
                         "de verdad:\n" + "\n".join(_ops) + "\n\nPídemelo así y lo corro.")
                        if _ops else
                        ("Eso no lo sé hacer todavía, y prefiero decírtelo a inventarte "
                         "algo.\nSi es sobre un archivo, dame la ruta completa. Si es de "
                         "tu negocio, dime cuál dato y lo saco de tus datos reales."))
                self._agregar_sesion(session_id, mensaje, _txt)
                ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                return {"respuesta": _txt, "motores_usados": ["sin_herramienta"],
                        "temperatura_lead": "frio", "duracion_ms": ms,
                        "timestamp": inicio.isoformat()}

            if real is not None:
                # APRENDE A LA PRIMERA. Ningún candado agarró esta frase, pero el
                # enrutador sí la resolvió: se registra en el momento, para que la
                # próxima vez entre directo sin gastar el segundo del enrutador.
                #
                # Antes solo se aprendía del ciclo fallo → reformulación, o sea que
                # cada frase nueva le costaba a Anuar un fracaso. Él lo dijo el
                # 2026-08-04: "no sé cómo pedirle a AURORA sin que lance algo
                # diferente". La medición le dio la razón: de 22 frases suyas que
                # funcionan, 4 solo funcionan porque ya se había peleado con ellas.
                _clave_usada = real.pop("_clave_usada", "") if isinstance(real, dict) else ""
                if _clave_usada:
                    try:
                        from CEREBRO import aprende_del_usuario as _apr
                        _apr.aprender_a_la_primera(mensaje, _clave_usada, time.time())
                    except Exception as _e:
                        logger.debug(f"[APRENDER 1RA] no se pudo registrar: {_e}")
                self._agregar_sesion(session_id, mensaje, real["respuesta"])
                ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                return {"respuesta": real["respuesta"], "motores_usados": ["router_universal"],
                        "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 3. EJECUCIÓN
        if paralelo and len(motor_ids) > 1:
            tareas = [self._ejecutar(mid, mensaje, contexto) for mid in motor_ids]
            resultados_raw = await asyncio.gather(*tareas, return_exceptions=True)
            respuestas = {
                mid: r for mid, r in zip(motor_ids, resultados_raw)
                if r and not isinstance(r, Exception)
            }
        else:
            respuestas = {}
            for mid in motor_ids:
                r = await self._ejecutar(mid, mensaje, contexto)
                if r:
                    respuestas[mid] = r

        # 4. SÍNTESIS
        if not respuestas:
            respuesta_final = await self._fallback(mensaje, contexto)
        elif len(respuestas) > 1:
            respuesta_final = await self._sintetizar(mensaje, respuestas)
        else:
            respuesta_final = list(respuestas.values())[0]

        # Cero simulación en operaciones: si cayó solo en un motor conversacional
        # para un pedido operativo, no se permite una respuesta "inventada".
        motores_respuesta = set(respuestas.keys())
        if _es_intencion_operativa(mensaje) and (not motores_respuesta or motores_respuesta == {"motor_analisis"}):
            # Antes aquí se cortaba con un "no ejecuté nada, reescríbelo" — honesto
            # pero inútil: dejaba a Anuar adivinando cómo pedirlo. Ahora se
            # consulta el REGISTRO REAL y se ofrece lo que de verdad aplica. El
            # dato sale del sistema, no del modelo, así que no se puede inventar.
            _sugeridas = []
            try:
                _reg = _registro()
                _cands = await asyncio.to_thread(_reg.buscar, _norm_txt(mensaje), 4)
                for _c in _cands[:3]:
                    _doc = (_c.get("doc") or "").strip().split("\n")[0].strip().rstrip(".")
                    if _doc:
                        _sugeridas.append(f"• {_doc}")
            except Exception:
                pass
            # Se anota que ESTA forma de decirlo no funcionó. Si en el siguiente
            # mensaje Anuar la reformula y esa sí ejecuta, AURORA aprende que las
            # dos significan lo mismo — y ya no hay que agregarle la frase a mano.
            try:
                from CEREBRO import aprende_del_usuario as _apr
                _apr.registrar_fallo(session_id, mensaje, time.time())
            except Exception:
                pass

            if _sugeridas:
                respuesta_final = ("No ejecuté nada todavía — no quiero inventarte un "
                                   "resultado. Esto sí lo puedo hacer de verdad:\n"
                                   + "\n".join(_sugeridas)
                                   + "\n\nPídemelo así y lo corro.")
            else:
                respuesta_final = (
                    "Eso no lo sé hacer todavía, y prefiero decírtelo a inventarte algo.\n"
                    "Si es sobre un archivo, dame la ruta completa. Si es del negocio "
                    "(ventas, órdenes, citas, precios), dime cuál y lo saco de tus datos reales.")

        # Si la respuesta salió SOLO de un motor de texto, no se ejecutó nada real.
        # Se anota aunque el guardia de arriba no la haya atrapado: la primera
        # versión solo registraba dentro del guardia, y por eso no aprendía cuando
        # motor_analisis contestaba "normal" (probado en vivo el 2026-08-02).
        try:
            if motores_respuesta and motores_respuesta <= {"motor_analisis", "conversacional",
                                                           "razonador", "motor_coaching"}:
                from CEREBRO import aprende_del_usuario as _apr
                _apr.registrar_fallo(session_id, mensaje, time.time())
        except Exception:
            pass

        # 5. APRENDIZAJE
        asyncio.create_task(self._perfil.analizar_interaccion(mensaje, respuesta_final, list(respuestas.keys())))
        # Antes esta llamada NO estaba en try/except: si fallaba (DB bloqueada, disco
        # lleno, contenido no serializable), la excepción se propagaba hasta el
        # endpoint y tiraba la respuesta YA GENERADA (respuesta_final, lista arriba) —
        # un fallo de memoria no debe borrar una respuesta que sí funcionó.
        try:
            await self._memoria.registrar(
                motor_origen="consciencia",
                tipo_evento="interaccion",
                contenido={"user_id": user_id, "msg": mensaje[:400], "resp": respuesta_final[:400], "motores": list(respuestas.keys())},
                importancia=0.7,
            )
        except Exception as e:
            logger.warning(f"No se pudo registrar en memoria (la respuesta SÍ se manda igual): {e}")
        try:
            nueva_temp = await self._ctx.actualizar(user_id, mensaje, respuesta_final, list(respuestas.keys()), canal)
        except Exception as e:
            logger.warning(f"No se pudo actualizar contexto de usuario (la respuesta SÍ se manda igual): {e}")
            nueva_temp = "frio"

        # Actualizar memoria de corto plazo (RAM)
        self._agregar_sesion(session_id, mensaje, respuesta_final)

        ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
        return {
            "respuesta": respuesta_final,
            "motores_usados": list(respuestas.keys()),
            "temperatura_lead": nueva_temp,
            "duracion_ms": ms,
            "timestamp": inicio.isoformat(),
        }

    # ── CANDADO ÚNICO DE VERDAD ──────────────────────────────────

    _PATRONES_NEGACION_FALSA = (
        r"no puedo (acceder|ejecutar|usar|tocar|controlar|abrir|correr|realizar)",
        r"no tengo (la capacidad|acceso|forma|manera) de",
        r"necesitar[ií]as? (darme|otorgarme|proporcionarme) (permiso|acceso)",
        r"en un entorno virtual",
        r"mi funci[oó]n es (proporcionar|solo dar|unicamente dar|únicamente dar)",
        r"no cuento con (acceso|la capacidad|herramientas)",
    )

    async def _verificar_capacidad_real(self, mensaje: str, respuesta: str) -> str:
        """Candado único: revisa CUALQUIER respuesta final (venga del candado que venga,
        del router universal, del razonador, o del LLM conversacional genérico) antes de
        mandarla. Si niega una capacidad que SÍ existe en el registro real de herramientas,
        la corrige citando la herramienta real — sin importar qué modelo la escribió, esto
        es código, no una instrucción que un modelo chico pueda ignorar (como pasó hoy)."""
        import re as _re
        baja = (respuesta or "").lower().strip()

        # Tres formas de dejar al usuario sin nada. Las tres se atienden igual:
        # ofreciendo lo que SÍ se puede hacer, sacado del registro real.
        niega = bool(baja) and any(_re.search(p, baja) for p in self._PATRONES_NEGACION_FALSA)

        # (a) Se quedó muda. Peor que un "no puedo": no sabes si falló o te ignoró.
        muda = len(baja) < 15

        # (b) Contestó una vaguedad de relleno. Caso real 2026-07-31: a "corel
        # tiene instalado el plugin laser" respondió "Excelente, gracias por
        # recordarme... estoy lista para ayudar si es necesario" — 33 segundos
        # para no decir nada.
        hueca = (
            len(baja) < 320
            and not _re.search(r"\d|✅|⚠️|❌|[A-Za-z]:\\|\.(?:py|pdf|png|dxf|svg|json)\b", respuesta or "")
            and any(f in baja for f in (
                "estoy lista para ayudar", "estoy listo para ayudar", "en que puedo ayudarte",
                "no tengo ninguna tarea", "gracias por recordarme", "excelente, gracias",
                "puedes preguntarme", "hay algo en particular", "estoy aqui para ayudar",
                "como puedo asistirte", "dime en que te ayudo"))
        )

        if not (niega or muda or hueca):
            return respuesta

        try:
            reg = _registro()
            # Se busca con el texto NORMALIZADO. Caso real 2026-08-02: "abreme
            # coreldrau porfa" — _norm_txt corrige coreldrau→coreldraw, pero aquí
            # llegaba el texto crudo, el registro no encontraba nada, y la
            # negación falsa pasaba limpia. Justo la palabra que Anuar escribe
            # mal era la que desarmaba el candado.
            candidatos = await asyncio.to_thread(reg.buscar, _norm_txt(mensaje), 4)
        except Exception:
            candidatos = []

        # Umbral de relevancia. El registro casi siempre devuelve ALGO, y con eso
        # bastaba para disparar la corrección: a "ve por un café" le contestaba
        # "Corrección: esto sí puedo hacerlo: exportar pdf...". El candado que
        # existe para que no mienta la estaba haciendo mentir al revés.
        # Ahora se exige que la herramienta comparta al menos una palabra con lo
        # que se pidió — y nunca se muestran docstrings internas.
        _palabras = {p for p in _norm_txt(mensaje).split() if len(p) > 3}
        if _palabras:
            candidatos = [
                c for c in candidatos
                if _palabras & set(_norm_txt(
                    f"{c.get('clave','')} {(c.get('doc') or '')[:120]}").replace("/", " ")
                    .replace(":", " ").replace("_", " ").split())
            ]

        if not candidatos:
            # De verdad no hay herramienta. Aun así no se deja al usuario colgado:
            # una negación honesta y clara vale más que el silencio o el relleno.
            if niega:
                return respuesta          # la negación era cierta, se respeta
            return ("Eso no lo sé hacer todavía — y prefiero decírtelo a inventarte algo.\n"
                    "Pregúntame de otra forma, o pídeme la lista de lo que sí puedo hacer.")

        # En cristiano, no con las claves técnicas: Anuar pidió que no le leyera
        # "MOTORES/motor_x:Clase.metodo" con puntos y comas.
        opciones = []
        for c in candidatos[:3]:
            doc = (c.get("doc") or "").strip().split("\n")[0].strip().rstrip(".")
            if doc:
                opciones.append(f"• {doc}")
        if not opciones:
            for c in candidatos[:3]:
                nombre = str(c.get("clave", "")).split(":")[-1].split(".")[-1].replace("_", " ")
                if nombre:
                    opciones.append(f"• {nombre}")
        lista = "\n".join(opciones)

        if niega:
            return (respuesta.strip() +
                    f"\n\n(Corrección: lo de arriba no es del todo cierto. Esto sí lo puedo "
                    f"hacer de verdad:\n{lista}\nPídemelo directo y lo hago.)")
        return f"No estoy segura de qué necesitas. Esto es lo que puedo hacer aquí:\n{lista}"

    # ── ROUTING ────────────────────────────────────────────────

    def _routing_rapido(self, mensaje: str) -> Tuple[List[str], bool]:
        """Scoring por keywords — sin llamada a API."""
        msg = _norm_txt(mensaje)
        scores: Dict[str, int] = {}

        # Los motores de venta no atienden preguntas sobre el propio sistema.
        # Caso real 2026-07-31: "corel tiene instalado el plugin laser" acabó en
        # motor_negocios, que tardó 33 s en soltar una vaguedad. No era un cliente
        # preguntando por un producto: era Anuar preguntando por su software.
        _fuera = _MOTORES_DE_VENTA if _es_tema_del_sistema(mensaje) else frozenset()

        for motor_id, patrones in _ROUTING_PATRONES.items():
            if motor_id in _fuera:
                continue
            score = sum(1 for p in patrones if p in msg)
            if score:
                scores[motor_id] = score

        if not scores:
            return [], False

        max_score = max(scores.values())
        ganadores = [m for m, s in scores.items() if s == max_score]

        # Casos especiales no-motores IA
        if "self_info" in ganadores:
            return ["self_info"], False
        if "self_repair" in ganadores:
            return ["self_repair"], False
        if "web_search" in ganadores:
            # Combinar búsqueda con análisis
            other = [m for m in ganadores if m != "web_search"]
            combined = ["web_search"] + (other[:1] if other else ["motor_analisis"])
            return combined, True

        # Un ganador claro
        if len(ganadores) == 1:
            return [ganadores[0]], False

        # Múltiples empatados → paralelo
        return ganadores[:2], True

    async def _routing_llm(self, mensaje: str, ctx: Dict) -> Tuple[List[str], bool]:
        """Routing via LLM cuando el heurístico no es suficiente."""
        if not self._groq:
            return ["motor_analisis"], False
        disponibles = list(self._prompts_motor.keys())
        prompt = (
            f"Motores: {', '.join(disponibles)}\n"
            f"Lead: {ctx['usuario'].get('temperatura_lead','frio')}\n"
            f"Mensaje: \"{mensaje[:300]}\"\n"
            "JSON solo: {\"motores\":[\"id\"],\"paralelo\":false}"
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[{"role":"user","content":prompt}],
                max_tokens=60, temperature=0.0
            )
            raw = r.choices[0].message.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip().split("```")[0]
            data = json.loads(raw)
            motores = [m for m in data.get("motores",[]) if m in self._prompts_motor]
            return (motores or ["motor_analisis"], bool(data.get("paralelo", False)))
        except Exception:
            return ["motor_analisis"], False

    # ── EJECUCIÓN DE MOTOR ──────────────────────────────────────

    async def _ejecutar(self, motor_id: str, mensaje: str, ctx: Dict) -> Optional[str]:
        """Ejecuta un motor con contexto enriquecido."""
        # Casos especiales (no usan LLM directamente)
        if motor_id == "self_info":
            estado = await self._autoconocimiento.estado_sistema_completo()
            perfil = await self._perfil.resumen_para_contexto()
            estado["perfil_anuar"] = perfil
            return json.dumps(estado, ensure_ascii=False, indent=2)

        if motor_id == "pc_cmd":
            cmd = mensaje.replace("ejecuta ", "").replace("corre ", "")
            r = await self._pc.ejecutar(cmd)
            return json.dumps(r, ensure_ascii=False)

        if motor_id == "self_repair":
            from CEREBRO.auto_reparacion import auto_reparacion
            # Extraer nombre de archivo del mensaje si lo hay
            import re
            match = re.search(r"([\w/\\]+\.py)", mensaje)
            archivo = match.group(1) if match else ""
            if archivo:
                r = await auto_reparacion.reparar(mensaje, archivo)
            else:
                r = await auto_reparacion.diagnosticar_y_reparar_todo()
            return json.dumps(r, ensure_ascii=False)

        if motor_id == "web_search":
            return await self._buscar_web(mensaje)

        # Motor IA: Groq con prompt especializado + contexto enriquecido
        # (si no hay Groq, igual armamos messages para el respaldo LOCAL de abajo)
        prompt_motor = self._prompts_motor.get(motor_id, SISTEMA_BASE)
        historial = ctx.get("historial_sesion", [])
        conocimiento = ctx.get("conocimiento", [])
        usuario = ctx.get("usuario", {})

        # RAG: contexto real de la Biblioteca (manuales de Anuar). Aditivo: si no hay
        # nada relevante, no cambia el chat. Nunca rompe (try/except + to_thread).
        bib_ctx = ""
        try:
            bib_ctx = await asyncio.to_thread(_biblioteca().contexto_para_llm, mensaje, 3)
        except Exception:
            bib_ctx = ""

        # CRUZADO: WEB EN VIVO si la pregunta pide info del momento (precio/competencia/actual).
        web_ctx = ""
        try:
            import unicodedata as _ud
            _m = "".join(c for c in _ud.normalize("NFD", mensaje.lower()) if _ud.category(c) != "Mn")
            if any(k in _m for k in ("precio", "cuanto cuesta", "competencia", "mercado", "tendencia",
                                     "noticia", "actual", "ultimo", "quien es", "donde queda", "en linea")):
                web_ctx = await asyncio.to_thread(_web_real().contexto_para_llm, mensaje, 3)
        except Exception:
            web_ctx = ""

        # CRUZADO: PRECIOS REALES del catálogo si preguntan precio (chat y WhatsApp cotizan exacto)
        cat_ctx = ""
        try:
            cat_ctx = await asyncio.to_thread(_contexto_catalogo, mensaje)
        except Exception:
            cat_ctx = ""
        # Si el producto está en MI catálogo, NO uso la web: respondo con MI precio real.
        if cat_ctx:
            web_ctx = ""

        base = SISTEMA_BASE
        if motor_id in _MOTORES_TALLER:
            base += "\n" + PROTOCOLO_TALLER
        system_content = (
            f"{base}\n\n"
            f"--- ESPECIALIDAD ACTIVA: {motor_id.upper()} ---\n"
            f"{prompt_motor}\n\n"
            f"--- CONTEXTO USUARIO ---\n"
            f"Historial: {usuario.get('historial_resumen','Nuevo usuario')}\n"
            f"Lead: {usuario.get('temperatura_lead','frio')} | Interés: {usuario.get('interes_principal','')}\n"
            f"Conocimiento AURORA sobre este tema: {'; '.join(conocimiento[:2]) or 'ninguno aún'}"
        )
        if bib_ctx:
            system_content += ("\n\n--- BIBLIOTECA (manuales reales de Anuar) ---\n"
                               f"{bib_ctx}\n"
                               "Usa estos datos reales si aplican y menciona el documento; no inventes.")
        if web_ctx:
            system_content += ("\n\n--- WEB EN VIVO (resultados reales de internet) ---\n"
                               f"{web_ctx}\n"
                               "Usa estos datos ACTUALES si aplican y cita la fuente/dominio; no inventes.")
        if cat_ctx:
            system_content += ("\n\n--- CATÁLOGO MILENS (precios reales) ---\n"
                               f"{cat_ctx}\n"
                               "Cotiza con EXACTITUD estos precios; si piden algo que no está, dilo — NO inventes.")

        messages = [{"role": "system", "content": system_content}]
        # Historial de sesión (memoria corto plazo)
        for h in historial[-4:]:
            messages.append({"role": h["rol"], "content": h["contenido"]})
        messages.append({"role": "user", "content": mensaje})

        try:
            if not self._groq:
                raise RuntimeError("groq_no_configurado")
            r = await self._groq.chat.completions.create(
                model=_MODELO, messages=messages, max_tokens=800, temperature=0.7
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            logger.warning(f"Groq falló en motor {motor_id} ({err[:120]}); intentando respaldo LOCAL (Ollama)")
            # Respaldo LOCAL sin internet (Ollama) — sin WiFi/401/timeout usamos el modelo local
            try:
                texto = await asyncio.to_thread(_llm_local_sync, messages)
                if texto and texto.strip():
                    return texto.strip()
            except Exception as e2:
                logger.error(f"Respaldo LOCAL (Ollama) también falló en {motor_id}: {e2}")
            # Ni nube ni local: mensaje honesto (no reventar)
            if "401" in err or "invalid_api_key" in err:
                return "⚠️ GROQ_API_KEY inválida. Actualiza en C:\\AURORA\\.env y reinicia."
            logger.error(f"Error motor {motor_id}: {e}")
            return None

    # ── ABRIR URL EN EL NAVEGADOR (distinto de buscar EN la web) ────

    async def _abrir_navegador_real(self, mensaje: str) -> Dict:
        """CHAT ↔ pc_access: abre un dominio/URL real directo en el navegador
        default, sin pasar por el enrutador de IA ni por búsqueda de palabras
        clave. No inventa la URL: usa el dominio real que escribió Anuar."""
        from CEREBRO.pc_access import pc_access
        # "abre pinterest y busca luna de mdf" manda primero: se abre el sitio CON
        # la búsqueda hecha, que es lo que se pidió. Antes esto se iba a búsqueda
        # web genérica y devolvía Wikipedia (caso real 2026-08-05).
        con_busqueda = _abrir_con_busqueda(mensaje)
        if con_busqueda:
            r = await pc_access.abrir_url(con_busqueda)
            if r.get("status") == "OK":
                return {"respuesta": f"✅ Abierto con tu búsqueda ya hecha:\n{con_busqueda}"}
            return {"respuesta": f"No pude abrirlo (no te miento): "
                                 f"{r.get('mensaje', r.get('status'))}"}

        dominio = _DOMINIO_RE.search(mensaje)
        # El dominio escrito manda; si no lo hay, se resuelve el nombre del sitio.
        # Nadie dice "abre youtube.com" — dice "abre youtube".
        destino = dominio.group(0) if dominio else _sitio_conocido(mensaje)
        if not destino:
            return {"respuesta": "Dime qué página abro (ej. youtube, facebook, "
                                 "mercadolibre) o el dominio exacto, y la abro de verdad."}
        r = await pc_access.abrir_url(destino)
        if r.get("status") == "OK":
            return {"respuesta": f"✅ Abierta real en el navegador: {destino}"}
        return {"respuesta": f"No pude abrirla (no te miento): {r.get('mensaje', r.get('stderr', r.get('status')))}"}

    # ── AURORA HABLA DE SÍ MISMA ─────────────────────────────────

    async def _acerca_de_real(self, mensaje: str) -> Dict:
        """CHAT ↔ AUTO-CONOCIMIENTO: describe la estructura y capacidades REALES de
        AURORA (nunca inventa, nunca busca en internet para hablar de sí misma).
        Usa datos reales del propio sistema (registro de herramientas, estado de
        integraciones) — encontrado en vivo 2026-07-27: antes esto caía a una
        búsqueda web genérica sin sentido."""
        try:
            from CEREBRO.auto_conocimiento import AutoConocimiento
            ac = AutoConocimiento()
            cap = await ac.obtener_capacidades()
        except Exception:
            cap = {}
        try:
            reg = _registro()
            catalogo = await asyncio.to_thread(reg.descubrir)
            n_herramientas = len(catalogo)
            carpetas = sorted({c.split("/")[0] for c in catalogo.keys()})
        except Exception:
            n_herramientas, carpetas = None, []
        integr = cap.get("integraciones", {}) or {}
        activas = [k for k, v in integr.items() if v]
        n_candados = len(_CANDADOS)
        partes = [
            "🧠 Quién soy y cómo estoy hecha (real, no marketing):",
            f"- Arquitectura real: {n_candados} candados directos (frases que reconozco de forma "
            f"determinística: Corel, WhatsApp, negocio, publicar, agenda, fichas de venta, código...) "
            f"+ un enrutador de IA que elige entre {n_herramientas or '~510'} herramientas reales "
            f"agrupadas en {len(carpetas) or '~20'} módulos ({', '.join(carpetas[:8]) if carpetas else 'Taller, Vendedor, Publicador, CRM, Editor/Corel, Cerebro...'}...) "
            f"cuando ninguna frase fija aplica — nunca inventa un resultado si no hay una herramienta real de por medio.",
            f"- Integraciones reales activas hoy: {', '.join(activas) if activas else 'ninguna detectada'}.",
            "- Memoria real (SQLite local), sin nube ajena — funciona offline salvo lo que necesita internet (búsqueda web, publicar en redes).",
            "- Límite real encontrado hoy: el chat puede colgarse si le mandan muchas peticiones al mismo tiempo — se está corrigiendo.",
            "¿Sirve para otro negocio? La arquitectura sí es genérica (motores/cartuchos + candados + registro de herramientas), "
            "pero ESTA instancia está hecha a la medida del taller de Anuar (ATF/Milens): catálogos, precios, WhatsApp y "
            "Facebook reales conectados a SUS datos. Para otro nicho se reconectaría a datos y cuentas propias — la base "
            "de código es reusable, los datos de negocio no.",
        ]
        return {"respuesta": "\n".join(partes)}

    # ── BÚSQUEDA WEB ───────────────────────────────────────────

    async def _print_and_cut_real(self, mensaje: str) -> Dict:
        """El proceso completo de imprimir y cortar, con sus advertencias.

        Cada aviso del manual es un error que de verdad ocurrió el
        2026-08-07: las marcas de Corel que no registran, el escalado de la
        papelería, el trazo de adentro que corta dos veces, el vinil de
        inyección metido a la láser.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location(
                "print_and_cut", ROOT / "TALLER" / "print_and_cut.py")
            pc = _ilu.module_from_spec(spec)
            spec.loader.exec_module(pc)
        except Exception as e:
            return {"respuesta": f"No pude abrir el manual de Print & Cut: {e}"}

        m = _norm_txt(mensaje)
        # Si pregunta cuánto cabe, se le responde con números, no con el manual.
        if _contiene_trigger(m, ("cuanto cabe", "cuantas caben", "area util",
                                 "cuantas salen")):
            try:
                spec2 = _ilu.spec_from_file_location(
                    "marcas_registro", ROOT / "TALLER" / "marcas_registro.py")
                mr = _ilu.module_from_spec(spec2)
                spec2.loader.exec_module(mr)
                return {"respuesta": mr._texto()}
            except Exception:
                pass
        return {"respuesta": pc.manual()}

    async def _metodo_campana_real(self, mensaje: str) -> Dict:
        """Enseña cómo se arma una campaña, o revisa la que le pasen.

        Las siete reglas salieron de errores reales de una sola tarde, y los
        cuatro graves los encontró Anuar leyendo el borrador, no la máquina.
        Por eso el revisor busca EXACTAMENTE esos: prometer lo que no se
        entrega, abrir con el calendario en vez del dolor, el teléfono
        cruzado, cerrar sin pedir nada.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location(
                "metodo_campanas", ROOT / "MARKETING" / "metodo_campanas.py")
            mc = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mc)
        except Exception as e:
            return {"respuesta": f"No pude abrir el método de campañas: {e}"}

        m = _norm_txt(mensaje)
        # Si trae un borrador de por medio, se revisa; si no, se explica.
        if _contiene_trigger(m, ("revisa", "revisame", "checa", "esta bien")):
            # El borrador es lo que venga después de dos puntos o comillas.
            cuerpo = mensaje
            for corte in (":", "«", '"'):
                if corte in mensaje:
                    cuerpo = mensaje.split(corte, 1)[1]
                    break
            if len(cuerpo.strip()) < 40:
                return {"respuesta": (
                    "Pásame el texto de la campaña y te digo qué corregir "
                    "antes de que salga.\n\n_Dímelo así:_ «revisa esta "
                    "campaña: Hola, ya viene el regreso a clases...»")}
            return {"respuesta": mc._texto(mc.revisar(cuerpo))}
        return {"respuesta": mc.anatomia()}

    async def _campana_escolar_real(self, mensaje: str) -> Dict:
        """Contesta con los paquetes escolares EXACTOS que se le mandaron.

        Sale de `TALLER/campana_escolar.py`, que es donde viven los precios de
        verdad. Aquí no se calcula ni se supone nada: si la clienta leyó $150,
        recibe $150.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location(
                "campana_escolar", ROOT / "TALLER" / "campana_escolar.py")
            ce = _ilu.module_from_spec(spec)
            spec.loader.exec_module(ce)
        except Exception as e:
            return {"respuesta": f"No pude leer los paquetes escolares: {e}"}
        return {"respuesta": ce.responder(mensaje)}

    def _medidas_cm(self, mensaje: str) -> tuple:
        """Las dos medidas del área, en cm, como él las dice.

        «30x20», «30 x 20 cm», «30cm de largo x 20 cm de alto». Si vienen en
        milímetros se pasan a cm: la escalera de precios está en cm.
        """
        m = _norm_txt(mensaje)
        g = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:cm|mm)?\s*(?:de\s*(?:largo|"
                      r"ancho|base)\s*)?[x×por]\s*(\d+(?:[.,]\d+)?)", m)
        if not g:
            return (0.0, 0.0)
        a = float(g.group(1).replace(",", "."))
        b = float(g.group(2).replace(",", "."))
        if "mm" in m and "cm" not in m:
            a, b = a / 10.0, b / 10.0
        return (a, b)

    async def _cotizar_vinil_real(self, mensaje: str) -> Dict:
        """CHAT ↔ PLOTTER: el precio sale de SU lista, no de una adivinanza.

        Este candado existe por una falla concreta del 2026-08-08: le pidió el
        costo de unas letras en vinil textil y recibió *«entre $500 y $1,500»*.
        Inventado. Su lista real decía $148 y él cobró $150.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location(
                "cotizador_vinil", ROOT / "TALLER" / "cotizador_vinil.py")
            cv = _ilu.module_from_spec(spec)
            spec.loader.exec_module(cv)
        except Exception as e:
            return {"respuesta": f"No pude abrir el cotizador de vinil: {e}"}

        m = _norm_txt(mensaje)
        ancho, alto = self._medidas_cm(mensaje)
        if not ancho or not alto:
            return {"respuesta": (
                "¿De qué medida es el trabajo? Con el área te doy el precio "
                "de tu lista.\n\n_Dímelo así:_ «cuánto cuesta un vinil de "
                "recorte de 30x20 cm»")}

        # ¿lleva colocación? Si es textil casi siempre sí; si no lo dice, se
        # cotiza sin ella y se avisa, que es lo honesto.
        colocar = _contiene_trigger(m, (
            "colocad", "colocacion", "instalad", "instalacion", "puesto",
            "puesta", "pegado", "planchado", "planchada", "aplicado",
            "ponerla", "ponerlas", "poner"))

        r = await asyncio.to_thread(cv.precio_de_lista, ancho, alto, colocar)
        if r.get("status") != "OK":
            return {"respuesta": (
                "No tengo tu lista de precios de vinil a la mano. Está en "
                "CONFIG/catalogo_servicios.json — dime los precios y la dejo.")}

        t = [f"✂️ **Vinil de recorte {ancho:g} × {alto:g} cm** "
             f"({r['area_cm2']:g} cm²)\n",
             f"   corte y material   $ {r['corte']:.2f}"]
        if r["colocacion"]:
            t.append(f"   colocación         $ {r['colocacion']:.2f}")
        t.append(f"   **TOTAL            $ {r['precio']:.2f}**\n")
        t.append("   _Sale de tu propia lista, interpolando entre "
                 + " y ".join(f"«{n}»" for n in r["apoyado_en"]) + "._")
        if not colocar:
            t.append(f"\n   Si además la pones, son "
                     f"+${_minimo_coloc(cv):.2f} de colocación.")
        if r["precio"] <= r["minimo"]:
            t.append(f"\n   ⚠️ Quedó en tu mínimo de ${r['minimo']:.2f}.")
        t.append("\n   Si son varias piezas del mismo trabajo, dímelas todas: "
                 "se suman las **áreas**, no los precios (así lo cobras tú).")
        return {"respuesta": "\n".join(t)}

    async def _texto_a_corte_real(self, mensaje: str) -> Dict:
        """CHAT ↔ PLOTTER: convierte las palabras en archivo de corte real."""
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location(
                "texto_a_corte", ROOT / "EDITOR" / "texto_a_corte.py")
            tc = _ilu.module_from_spec(spec)
            spec.loader.exec_module(tc)
        except Exception as e:
            return {"respuesta": f"No pude abrir el generador de texto: {e}"}

        # Las palabras van entre comillas, o después de «la palabra / el
        # nombre / que diga». Se respeta el ORDEN en que las dijo.
        palabras = re.findall(r'"([^"]{1,40})"|«([^»]{1,40})»', mensaje or "")
        textos = [a or b for a, b in palabras]
        if not textos:
            for g in re.finditer(
                    r"(?:la palabra|el nombre|que diga|el texto|el rotulo)\s+"
                    r"([a-zA-ZÁÉÍÓÚÑáéíóúñ0-9][\wÁÉÍÓÚÑáéíóúñ' -]{0,30}?)"
                    r"(?=\s+(?:y|debajo|arriba|en|de|para|con|al)\b|[,.]|$)",
                    mensaje or "", re.I):
                t = g.group(1).strip()
                if t:
                    textos.append(t)
        if not textos:
            return {"respuesta": (
                "¿Qué debe decir? Ponlo entre comillas y te lo dejo listo "
                "para cortar.\n\n_Así:_ «hazme \"Oswaldo\" en vinil de "
                "recorte, área de 30x20»")}

        ancho, alto = self._medidas_cm(mensaje)
        if not ancho or not alto:
            ancho, alto = 30.0, 20.0
        r = await asyncio.to_thread(tc.generar, textos, ancho * 10, alto * 10)
        return {"respuesta": tc._texto(r)}

    async def _adaptar_diseno_real(self, mensaje: str, session_id: str = "") -> Dict:
        """Deja un DXF listo para OTRO material y, si se pide, de otro tamaño.

        El flujo que Anuar describió el 2026-08-06: él pone dos números —la
        escala y el espesor del material— y todo lo demás sale solo. Las
        ranuras al espesor nuevo, los dientes alargados al espesor nuevo, los
        números a su capa en rojo, y el original sin tocarse.

        Ejemplo de cómo lo pide él:
            «ajusta la casa de bob al 50% para material de 2.5»
        """
        import importlib.util as _ilu
        from pathlib import Path as _P

        ruta = self._ultimo_archivo(mensaje, session_id)
        if not ruta or not str(ruta).lower().endswith(".dxf"):
            return {"respuesta": (
                "Dime cuál DXF adapto — pásame la ruta o arrástramelo.\n\n"
                "_Así te lo entiendo:_ «ajusta C:\\ruta\\casa.dxf al 50% "
                "para material de 2.5»")}

        m = _norm_txt(mensaje)

        # EL ESPESOR: es la perilla que manda sobre todos los ensambles.
        grosor = 0.0
        mg = (re.search(r"(?:material|espesor|grosor|mdf)\s*(?:de\s*)?"
                        r"(\d+(?:[.,]\d+)?)", m)
              or re.search(r"(\d+(?:[.,]\d+)?)\s*mm", m))
        if mg:
            grosor = float(mg.group(1).replace(",", "."))
        if not grosor:
            return {"respuesta": (
                "¿De qué espesor es el material? De ahí salen las ranuras y "
                "el largo de los dientes.\n\n_Dímelo así:_ «para material de "
                "2.5»")}

        # LA ESCALA: la otra perilla, la del tamaño. Si no la dice, no se
        # cambia el tamaño — que es distinto de suponer que quiere la mitad.
        escala = 1.0
        me = re.search(r"(?:al|a|en)\s*(\d+(?:[.,]\d+)?)\s*%", m)
        if me:
            escala = float(me.group(1).replace(",", ".")) / 100.0
        elif _contiene_trigger(m, ("a la mitad", "mitad de tamano",
                                   "mitad del tamano")):
            escala = 0.5

        try:
            spec = _ilu.spec_from_file_location(
                "adaptar_grosor", ROOT / "TALLER" / "adaptar_grosor.py")
            ag = _ilu.module_from_spec(spec)
            spec.loader.exec_module(ag)
        except Exception as e:
            return {"respuesta": f"No pude abrir el adaptador: {e}"}

        r = await asyncio.to_thread(ag.adaptar, _P(ruta), grosor, 0.0, escala)
        txt = ag._texto(r, _P(ruta))

        # LA REGLA DE ORO DEL TALLER, y no es un adorno: esto ajusta geometría,
        # no adivina cómo quedó el ensamble en la vida real. Ya pasó que los
        # conteos decían "OK" con el archivo inservible (2026-08-06).
        if r.get("status") == "OK":
            txt += ("\n\n⚠️ **Corta una pieza en retazo antes de la hoja "
                    "completa.** Yo ajusté las medidas; que entre de verdad "
                    "solo lo dice el material.")
        return {"respuesta": txt}

    async def _generar_caja_real(self, mensaje: str) -> Dict:
        """CHAT ↔ boxes.py: genera la caja que se pidió EN ESPAÑOL, y la cotiza.

        189 generadores disponibles (corazón, flex, bisagras, bandejas, cajones).
        Anuar marcó la prioridad el 2026-08-05: que se le enseñe el mapa de qué
        generador es cada cosa, no que lo descubra usando.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location("cajas_boxes", ROOT / "TALLER" / "cajas_boxes.py")
            cb = _ilu.module_from_spec(spec)
            spec.loader.exec_module(cb)
        except Exception as e:
            return {"respuesta": f"No pude abrir el generador de cajas: {e}"}

        m = _norm_txt(mensaje)
        if _contiene_trigger(m, ("que cajas puedes", "que cajas sabes",
                                 "tipos de caja", "que cajas hay")):
            return {"respuesta": cb.listar()}

        # El grosor: si no lo dice, 2.7 mm, que es lo que más usa.
        grosor = 2.7
        mg = re.search(r"(\d+(?:[.,]\d+)?)\s*mm", m)
        if mg:
            grosor = float(mg.group(1).replace(",", "."))

        # SIEMPRE en DXF. Anuar lo estableció el 2026-08-06: *"todas las cajas
        # siempre se entregan en dxf, así queda implícito y ni lo menciono"*.
        # Antes había que pedirlo; pedirle que lo diga cada vez es hacerle
        # trabajo a él para ahorrárselo al código.
        r = await asyncio.to_thread(cb.generar, mensaje, grosor, True)
        txt = cb._texto(r)

        # Si salió, se cotiza de una vez: es lo que sigue siempre.
        # Ya no hay que mandarlo a Corel a convertir: el DXF sale de aquí.
        # Ese aviso se quedó de cuando solo salía SVG y era falso desde que se
        # encadenó la conversión (2026-08-06).
        if r.get("status") == "OK" and r.get("dxf"):
            txt += f"\n\n_¿Cuánto cuesta cortarla? Dime: «cotiza {r['dxf']}»_"
        return {"respuesta": txt}

    def _ultimo_archivo(self, mensaje: str, session_id: str = "") -> str:
        """La ruta del archivo del que se está hablando, aunque no se repita.

        Caso real 2026-08-05: Anuar dio la ruta de una foto, AURORA preguntó
        "¿le doy?", él contestó "no, entrégalo en dxf" — y AURORA respondió
        "dime qué archivo convierto". YA SE LO HABÍA DADO. Obligarlo a repetir
        una ruta larga es justo lo tedioso.

        Primero se busca en el mensaje; si no está, en los mensajes anteriores
        de la misma sesión.
        """
        for r in _rutas_del_texto(mensaje or ""):
            if Path(r).exists():
                return r
        for turno in reversed(self._memoria_corto.get(session_id, [])):
            if turno.get("rol") != "user":
                continue
            for r in _rutas_del_texto(turno.get("contenido") or ""):
                if Path(r).exists():
                    return r
        return ""

    async def _foto_a_dxf_real(self, mensaje: str, session_id: str = "") -> Dict:
        """CHAT ↔ la cadena completa: foto → sin fondo → vectorizada → DXF.

        Antes esto eran tres mensajes distintos y AURORA olvidaba el archivo
        entre uno y otro. Y el camino viejo (Inkscape) se rendía a los 180 s;
        este usa vtracer y tarda segundos.
        """
        import importlib.util as _ilu
        ruta = self._ultimo_archivo(mensaje, session_id)
        if not ruta:
            return {"respuesta": (
                "¿Cuál imagen? Arrástrala aquí o dame la ruta completa.\n"
                "Ejemplo: `quita el fondo a C:\\Users\\...\\foto.jpg y dámelo en dxf`")}
        try:
            spec = _ilu.spec_from_file_location("imagen_a_dxf",
                                                ROOT / "EDITOR" / "imagen_a_dxf.py")
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            return {"respuesta": f"No pude cargar el conversor: {e}"}

        r = await asyncio.to_thread(mod.convertir, ruta)
        txt = mod._texto(r)
        if Path(ruta).name not in txt:
            txt = f"_De_ `{Path(ruta).name}`\n\n{txt}"
        return {"respuesta": txt}

    async def _cotizar_dxf_real(self, mensaje: str) -> Dict:
        """CHAT ↔ LÁSER: mide los METROS DE CORTE reales de un DXF y lo cotiza.

        Esto es lo que le faltó a Anuar el 2026-08-04 frente al cliente: sin el
        archivo no hay metros, y sin metros no hay precio. Vendió una casa de
        muñecas en $280 costando ~$200 producirla.

        Usa sus números reales: $8.00 por minuto y 25 mm/s de su receta probada.
        """
        import re as _re
        import importlib.util as _ilu
        from pathlib import Path as _P

        try:
            spec = _ilu.spec_from_file_location("indexar_dxf", ROOT / "TALLER" / "indexar_dxf.py")
            ix = _ilu.module_from_spec(spec)
            spec.loader.exec_module(ix)
        except Exception as e:
            return {"respuesta": f"No pude abrir el medidor de corte: {e}"}

        # 1) ¿Viene la ruta del archivo en el mensaje?
        m_ruta = _re.search(r'([A-Za-z]:\\[^\r\n"\']+?\.dxf)', mensaje or "", _re.I)
        ruta = _P(m_ruta.group(1)) if m_ruta else None

        # 2) Si no, se busca por nombre en el catálogo ya medido.
        if not ruta:
            texto = _norm_txt(mensaje)
            for frase in sorted(_COTIZAR_DXF, key=len, reverse=True):
                texto = texto.replace(frase, " ")
            nombre = " ".join(w for w in texto.split()
                              if w not in ("el", "la", "de", "del", "un", "una",
                                           "este", "esta", "mi", "aurora",
                                           "cotiza", "cuanto", "cuesta")).strip()
            if nombre and ix.CATALOGO.exists():
                import json as _json
                cat = _json.loads(ix.CATALOGO.read_text(encoding="utf-8"))
                hits = [x for x in cat.get("disenos", [])
                        if nombre.lower() in x["archivo"].lower()][:5]
                if hits:
                    lineas = []
                    for x in hits:
                        lineas.append(
                            f"📐 **{x['archivo']}**\n"
                            f"   {x['ancho_cm']} × {x['alto_cm']} cm · "
                            f"**{x['metros_corte']} m** de corte · {x['minutos']} min\n"
                            f"   costo ${x['costo_corte']:.0f} → **PRECIO ${x['precio_sugerido']:.0f}**")
                    return {"respuesta": "\n\n".join(lineas)}
            return {"respuesta": (
                "Pásame el archivo y lo mido de verdad:\n"
                "• Arrastra el .dxf aquí, o\n"
                "• Dime la ruta completa: `cotiza C:\\Users\\...\\diseno.dxf`\n\n"
                "Te doy los metros de corte, los minutos y el precio con tus "
                "números ($8/min a 25 mm/s).")}

        if not ruta.exists():
            return {"respuesta": f"No encontré ese archivo:\n`{ruta}`\nRevisa la ruta."}

        r = await asyncio.to_thread(ix.medir, ruta)
        if r.get("error"):
            return {"respuesta": (f"No pude leer el DXF (no lo invento): {r['error']}\n"
                                  "Puede estar dañado o en un formato viejo. "
                                  "Vuélvelo a guardar desde Corel como DXF y lo mido.")}

        # El desperdicio de material según la forma: una pieza con curvas
        # desperdicia más hoja que un rectángulo.
        material = round((r["ancho_cm"] * r["alto_cm"]) / 29768.0 * 110 * 1.4, 2)
        costo = r["costo_corte"] + material
        return {"respuesta": (
            f"📐 **{r['archivo']}**\n"
            f"   {r['ancho_cm']} × {r['alto_cm']} cm · {r['entidades']} piezas\n\n"
            f"✂️ **{r['metros_corte']} m** de corte  ·  **{r['minutos']} min** "
            f"(a tus 25 mm/s)\n\n"
            f"   corte  ${r['costo_corte']:.2f}   (${8.0:.0f}/min)\n"
            f"   MDF 2.7 + merma  ${material:.2f}\n"
            f"   **COSTO  ${costo:.2f}**\n\n"
            f"💰 **PRECIO SUGERIDO: ${max(r['precio_sugerido'], costo * 3):.0f}**\n\n"
            f"_(Si es pieza armable con forma, tu mínimo es $450.)_")}

    async def _alta_lead_real(self, mensaje: str) -> Dict:
        """CHAT ↔ ORACLE: da de alta un cliente nuevo con lo que se dictó.

        Se saca el nombre y el teléfono del propio mensaje. Si falta el nombre
        se PIDE — no se guarda un lead vacío, que es peor que no guardarlo.
        """
        import re as _re
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location("oracle_core", ROOT / "ORACLE" / "oracle_core.py")
            oc = _ilu.module_from_spec(spec)
            spec.loader.exec_module(oc)
        except Exception as e:
            return {"respuesta": f"No pude abrir el registro de clientes: {e}"}

        texto = mensaje or ""
        # Teléfono: 10 dígitos seguidos, con o sin espacios y guiones.
        tel = ""
        m_tel = _re.search(r"(\d[\d\s\-]{8,}\d)", texto)
        if m_tel:
            solo = "".join(c for c in m_tel.group(1) if c.isdigit())
            if len(solo) >= 10:
                tel = solo[-10:]

        # Nombre: lo que va después del verbo, hasta el teléfono o una coma.
        limpio = _norm_txt(texto)
        for frase in sorted(_ALTA_DE_LEAD, key=len, reverse=True):
            limpio = limpio.replace(frase, "|")
        trozo = limpio.split("|")[-1] if "|" in limpio else limpio
        trozo = _re.split(r"\d{6,}|,|\btel\b|\bcel\b|\bwhats\b", trozo)[0]
        nombre = " ".join(w for w in trozo.split()
                          if w not in ("el", "la", "de", "del", "que", "se",
                                       "llama", "es", "un", "una", "por",
                                       "para", "con", "y", "mi", "me")).strip()
        nombre = nombre.title()[:60]

        if not nombre:
            return {"respuesta": (
                "¿Cómo se llama? Dímelo así y lo guardo:\n"
                "`apunta a Juan Pérez 3312345678 interesado en faros`\n\n"
                "Sin nombre no lo doy de alta — un cliente sin nombre no sirve "
                "para llamarle después.")}

        # Negocio: si habla de faros o lupas es ATF; si no, Milens.
        neg = "atf" if _contiene_trigger(_norm_txt(texto),
                                         ("faro", "faros", "lupa", "lupas",
                                          "retrofit", "led", "canbus")) else "milens"
        interes = ""
        m_int = _re.search(r"(?:interesad[oa] en|quiere|pregunta por|busca)\s+(.{3,60})",
                           _norm_txt(texto))
        if m_int:
            interes = m_int.group(1).strip(" .,")

        try:
            r = await asyncio.to_thread(
                oc.crear_lead, nombre, tel, "chat", neg, "", interes, texto[:200], 0)
        except Exception as e:
            return {"respuesta": f"No pude guardarlo (no lo simulo): {str(e)[:180]}"}

        detalle = f"✅ Cliente guardado: **{nombre}**"
        if tel:
            detalle += f"\n📲 {tel}"
        else:
            detalle += "\n_(sin teléfono — pásamelo y lo agrego)_"
        detalle += f"\n🏷️ {neg.upper()}"
        if interes:
            detalle += f"\n💡 Le interesa: {interes}"
        if isinstance(r, dict) and r.get("id"):
            detalle += f"\n\nQuedó con folio {r['id']}."
        return {"respuesta": detalle}

    async def _proveedor_real(self, mensaje: str) -> Dict:
        """CHAT ↔ DIRECTORIO DE PROVEEDORES: quién vende qué, y a cuánto.

        Si no lo tiene lo DICE y ofrece buscarlo en internet — nunca inventa un
        proveedor ni un teléfono. Caso real 2026-08-04: Anuar no sabía a quién
        cotizarle el papel adhesivo y terminó pidiéndole a AURORA que buscara en
        MercadoLibre, porque no había dónde consultarlo.
        """
        import importlib.util as _ilu
        try:
            spec = _ilu.spec_from_file_location("proveedores", ROOT / "TALLER" / "proveedores.py")
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            return {"respuesta": f"No pude abrir el directorio de proveedores: {e}"}

        # Qué artículo se busca: se quita la parte de la pregunta.
        m = _norm_txt(mensaje)
        for frase in sorted(_PREGUNTAS_DE_PROVEEDOR, key=len, reverse=True):
            m = m.replace(frase, " ")
        articulo = " ".join(w for w in m.split()
                            if w not in ("el", "la", "los", "las", "de", "del",
                                         "un", "una", "me", "mi", "y", "o",
                                         "aurora", "dime", "que", "cual")).strip()

        if not articulo:
            r = await asyncio.to_thread(mod.listar)
            txt = mod._texto({"status": "OK", "proveedores": r["proveedores"]})
            return {"respuesta": f"Tengo {r['total']} proveedores en tu directorio:\n\n{txt}"}

        r = await asyncio.to_thread(mod.buscar, articulo)
        if r.get("status") == "NO_LO_TENGO":
            return {"respuesta": (
                f"{r['detalle']}\n\n"
                f"Dime «busca en internet {articulo}» y lo cotizo afuera, o "
                f"pásame el proveedor y lo guardo para la próxima.")}
        return {"respuesta": mod._texto(r)}

    async def _buscar_web_candado(self, mensaje: str) -> Dict:
        """Envoltorio delgado para que _buscar_web calce con la firma uniforme
        del pipeline de candados (todos regresan {"respuesta": ...})."""
        return {"respuesta": await self._buscar_web(mensaje)}

    # Instrucciones que Anuar le da a AURORA y que NO son parte de lo que busca.
    # Caso real 2026-08-04: pidió seis veces el precio del papel adhesivo en
    # MercadoLibre y las seis veces se mandó el mensaje COMPLETO al buscador
    # ("aurora busca... copea el enlace aqui mismo"), así que la consulta salía
    # sucia, no respetaba el sitio pedido y devolvía basura — incluso un sitio
    # de contenido para adultos, con su esposa e hija usando AURORA.
    _RUIDO_DE_BUSQUEDA = (
        "aurora", "busca en internet", "busca en", "buscame en", "buscar en",
        "encuentra en", "encuentrame", "encuentra el", "encuentra",
        "copea el enlace", "copia el enlace", "copea el enllace",
        "aqui mismo", "aquimismo", "aqui", "para revisarlo", "de la publicasion",
        "de la publicacion", "el enlace de venta", "el enlace", "el enllace",
        "dame el link", "el link", "y copea", "por favor", "porfa", "porfavor",
        "al mejor precio real", "al mejor precio", "el mejor precio",
        "mejor precio de la plataforma", "de la plataforma", "solamente",
        "y me lo pasas", "pasamelo",
    )
    # Sitios que se pueden pedir por nombre → a qué dominio acotar la búsqueda.
    _SITIOS_CONOCIDOS = {
        "mercado libre": "mercadolibre.com.mx", "mercadolibre": "mercadolibre.com.mx",
        "meli": "mercadolibre.com.mx", "amazon": "amazon.com.mx",
        "lideart": "lideart.com.mx", "home depot": "homedepot.com.mx",
        "walmart": "walmart.com.mx", "office depot": "officedepot.com.mx",
        "liverpool": "liverpool.com.mx", "coppel": "coppel.com",
    }
    # Basura que nunca debe llegarle a esta familia.
    _DOMINIOS_BLOQUEADOS = (
        "fanx.art", "undress", "nudify", "deepnude", "porn", "xxx", "sexo",
        "onlyfans", "camsoda", "chaturbate",
    )

    @classmethod
    def _limpiar_consulta(cls, mensaje: str) -> tuple:
        """Separa QUÉ se busca de DÓNDE y de las instrucciones.

        Devuelve (consulta_limpia, dominio_o_vacio). Sin esto, el buscador
        recibía la frase entera y buscaba literalmente "copea el enlace aqui
        mismo", que es lo que traía los resultados absurdos.
        """
        m = _norm_txt(mensaje)
        dominio = ""
        for nombre, dom in cls._SITIOS_CONOCIDOS.items():
            if nombre in m:
                dominio = dom
                m = m.replace(nombre, " ")
                break
        for ruido in sorted(cls._RUIDO_DE_BUSQUEDA, key=len, reverse=True):
            m = m.replace(ruido, " ")
        m = re.sub(r"\b(y|de|el|la|los|las|un|una|en|para|que|me|mi|lo)\b\s*$", "", m)
        limpia = " ".join(m.split()).strip(" ,.;:")
        return (limpia or _norm_txt(mensaje)), dominio

    async def _buscar_web(self, consulta: str) -> str:
        """Búsqueda web real — ddgs EN VIVO, luego fallbacks, luego Groq."""
        # 1) Web REAL en vivo, con la consulta limpia y acotada al sitio pedido.
        limpia, dominio = self._limpiar_consulta(consulta)
        termino = f"{limpia} site:{dominio}" if dominio else limpia
        try:
            r = await asyncio.to_thread(_web_real().buscar, termino, 6)
            res = [x for x in (r.get("resultados") or [])
                   if not any(b in (x.get("url") or "").lower()
                              for b in self._DOMINIOS_BLOQUEADOS)]
            if res:
                donde = f" en {dominio}" if dominio else ""
                lineas = []
                for x in res[:5]:
                    lineas.append(f"**{x.get('titulo','')[:90]}**\n{x.get('url','')}")
                    ext = (x.get("extracto") or "").strip()
                    if ext:
                        lineas.append(f"_{ext[:150]}_")
                    lineas.append("")
                # El cierre depende de lo que se buscó: hablar de "el precio de
                # hoy" cuando se pidieron DISEÑOS no viene al caso (2026-08-05).
                _es_compra = _contiene_trigger(
                    limpia, ("precio", "cuesta", "barato", "comprar", "venta",
                             "hoja", "hojas", "rollo", "metro", "paquete"))
                cierre = ("ábrelos para ver el precio de hoy"
                          if _es_compra else "los enlaces son reales")
                return (f"Busqué «{limpia}»{donde} y esto es lo que hay "
                        f"({cierre}):\n\n" + "\n".join(lineas))
        except Exception as e:
            logger.debug(f"[WEB] buscar falló: {e}")
        # Respaldo: el contexto plano de siempre.
        try:
            ctx = await asyncio.to_thread(_web_real().contexto_para_llm, termino, 4)
            if ctx:
                return ctx
        except Exception:
            pass
        # Respaldo #2: buscador de PRODUCTOS/PRECIOS (Google+MercadoLibre), no búsqueda
        # web genérica — antes llamaba con un kwarg que no existe (num_resultados) y
        # trataba el resultado como lista de dicts cuando en realidad regresa un objeto
        # ResultadoBusqueda.productos — nunca había funcionado, el except lo escondía.
        try:
            import sys
            sys.path.insert(0, str(ROOT / "CORE"))
            from buscador_web_profesional import BuscadorWebProfesional
            buscador = BuscadorWebProfesional()
            resultado = await buscador.buscar(consulta)
            productos = resultado.productos if resultado else []
            if productos:
                resumen = "\n".join(
                    f"- {p.titulo} — ${p.precio} {p.moneda} ({p.fuente}, {p.vendedor})"
                    for p in productos[:3])
                return f"Resultados de precios/productos para '{consulta}':\n{resumen}"
        except Exception:
            pass
        # Cero simulación: si no hubo fuente real, NO responder de memoria del LLM.
        return ("No pude obtener resultados web reales en este momento. "
                "No voy a inventarte datos de internet: si quieres, lo reintento o "
                "te doy solo lo que sí está verificado localmente.")

    # ── MOTORES CONECTADOS DIRECTO AL CHAT (acción real, sin simular) ──

    async def _publicar_real(self, mensaje: str, session_id: str = "") -> Dict:
        """CHAT ↔ PUBLICADOR: muestra el preview real de HOY y deja pendiente la
        publicación de verdad — nunca la dispara en el mismo mensaje. Encontrado en
        vivo 2026-07-27: escanear "de verdad"/"aprueba" como substring del MISMO
        mensaje que pide el preview hacía que un mensaje inocente ("de verdad, ¿qué
        publico hoy?") publicara de verdad sin que nadie lo hubiera pedido. Ahora
        reusa el mismo mecanismo estricto de confirmación de 2 turnos que ya usa el
        router universal (_accion_pendiente + _es_confirmacion, igualdad exacta con
        una lista corta de "sí" claros, no substring)."""
        m = _norm_txt(mensaje)
        try:
            pub = _pubint()
            if "estrategia" in m:
                d = await asyncio.to_thread(pub.estrategia_ingresos, "atf", "")
                return {"respuesta": self._fmt_dict("📣 Estrategia de ingresos ATF", d)}
            d = await asyncio.to_thread(pub.preparar_publicacion, "atf")
            if session_id:
                self._accion_pendiente[session_id] = {"tipo": "publicar_facebook"}
            return {"respuesta": "📋 Esto es lo que publicaría HOY (aún NO lo subí):\n"
                    + self._fmt_dict("preparar", d) + "\n\nResponde 'sí' para confirmar y publicarlo de verdad."}
        except Exception as e:
            return {"respuesta": f"No pude preparar la publicación (no lo invento): {str(e)[:200]}"}

    async def _servicio_atf_real(self, mensaje: str) -> Dict:
        """Responde a un cliente que pide un SERVICIO real de ATF.

        Reglas duras (nacieron de un fallo real, ver _es_servicio_atf):
        · NUNCA negar un servicio que esta en la lista. Se hace, punto.
        · NUNCA inventar el precio. Si no esta capturado, se dice que se confirma.
        · Si pide cita, se le dice lo que la agenda REAL tiene, no un horario inventado.
        """
        from datetime import datetime as _dt, timedelta as _td
        m = _norm_txt(mensaje)

        # Que servicio(s) reconoce, por las palabras reales del cliente.
        encontrados = []
        for s in _servicios_atf():
            if any(_norm_txt(p) in m for p in s.get("palabras_cliente", [])):
                encontrados.append(s)
        if not encontrados:
            return {"respuesta": "Dime qué necesitas del faro y te digo si lo hacemos y cuánto."}

        partes = []
        for s in encontrados[:3]:
            linea = f"✅ **{s['nombre']}** — sí lo hacemos."
            if s.get("precio"):
                linea += f" Precio: ${s['precio']} {s.get('unidad','')}."
            else:
                # Honesto: el servicio existe, el precio no esta capturado todavia.
                linea += " Te confirmo el precio en un momento (depende del faro)."
            if s.get("descripcion"):
                linea += f"\n   {s['descripcion']}"
            partes.append(linea)

        # ¿Pide cita/espacio? Se consulta la agenda REAL, sin inventar horarios.
        pide_cita = any(k in m for k in ("espacio", "cita", "cuando", "cuándo", "horario",
                                          "atender", "atenderme", "hueco", "agenda", "hoy",
                                          "manana", "mañana"))
        if pide_cita:
            try:
                ag = _agenda()
                if hasattr(ag, "init_db"):
                    await asyncio.to_thread(ag.init_db)
                hoy = _dt.now().strftime("%Y-%m-%d")
                man = (_dt.now() + _td(days=1)).strftime("%Y-%m-%d")
                d_hoy = await asyncio.to_thread(ag.dia, hoy)
                d_man = await asyncio.to_thread(ag.dia, man)
                n_hoy = d_hoy.get("total", 0) if isinstance(d_hoy, dict) else 0
                n_man = d_man.get("total", 0) if isinstance(d_man, dict) else 0
                partes.append(f"\n📅 Agenda real: hoy ({hoy}) hay {n_hoy} cita(s) y mañana "
                              f"({man}) hay {n_man}. Dime la hora que te acomoda y la aparto "
                              f"— necesito tu nombre y teléfono para agendarla.")
            except Exception as e:
                partes.append(f"\n📅 No pude leer la agenda ahora mismo (no lo invento): {str(e)[:120]}")

        return {"respuesta": "\n\n".join(partes)}

    async def _agenda_real(self, mensaje: str) -> Dict:
        import re
        from datetime import datetime as _dt, timedelta as _td
        m = _norm_txt(mensaje)
        try:
            ag = _agenda()
            if hasattr(ag, "init_db"):
                await asyncio.to_thread(ag.init_db)

            # CERRAR una cita que ya existe. Lo detectó el barrido del
            # 2026-08-04: actualizar_estado existía y no había forma de llamarla
            # desde el chat, así que las citas quedaban abiertas para siempre y
            # la agenda dejaba de servir a los pocos días.
            if _es_cerrar_cita(mensaje):
                id_m = re.search(r"\b(?:cita|folio|id)\s*#?\s*(\d{1,6})\b", m) or \
                       re.search(r"\b(\d{1,4})\b", m)
                if not id_m:
                    prox = await asyncio.to_thread(ag.proximas, 168)
                    citas = prox.get("citas", []) if isinstance(prox, dict) else []
                    if not citas:
                        return {"respuesta": "No tienes citas abiertas esta semana."}
                    lista = "\n".join(
                        f"• **{c.get('id')}** — {c.get('titulo', '')[:34]} "
                        f"({c.get('fecha', '')} {c.get('hora', '')})"
                        for c in citas[:8])
                    return {"respuesta": ("¿Cuál cita? Dime el número:\n" + lista +
                                          "\n\nEjemplo: `marca la cita 3 como hecha`")}
                cid = int(id_m.group(1))
                if any(k in m for k in ("cancela", "cancelar", "no vino")):
                    nuevo = "cancelada"
                elif any(k in m for k in ("confirma", "confirmar")):
                    nuevo = "confirmada"
                else:
                    nuevo = "hecha"
                r = await asyncio.to_thread(ag.actualizar_estado, cid, nuevo)
                if isinstance(r, dict) and r.get("status") == "ok":
                    return {"respuesta": f"✅ Cita {cid} marcada como **{nuevo}**."}
                det = r.get("error", r) if isinstance(r, dict) else r
                return {"respuesta": f"No pude cambiarla (no lo simulo): {det}"}

            # Fase 3 (2026-07-28): crear cita real — no existia NINGUNA ruta de
            # chat para agendar. No adivina titulo/cliente: si faltan, los pide.
            if any(k in m for k in ("agenda una cita", "agendar una cita", "agendame",
                                     "programa una cita", "nueva cita", "crear cita")):
                tel_m = re.search(r"\b(\d{10})\b", mensaje)
                fecha_m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", mensaje)
                hora_m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", mensaje)
                tipo_m = next((t for t in sorted(ag.TIPOS) if t in m), None)
                cli_m = re.search(r"\bpara\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,40}?)(?:\s+(?:el|para el|tel|telefono)\b|$)", mensaje, re.I)

                fecha = fecha_m.group(1) if fecha_m else ("hoy" in m and _dt.now().strftime("%Y-%m-%d")) or ("manana" in m and (_dt.now() + _td(days=1)).strftime("%Y-%m-%d")) or None
                hora = f"{hora_m.group(1).zfill(2)}:{hora_m.group(2)}" if hora_m else None

                faltan = []
                if not fecha: faltan.append("fecha (YYYY-MM-DD, o di 'hoy'/'mañana')")
                if not hora: faltan.append("hora (HH:MM)")
                if not tipo_m: faltan.append(f"tipo ({'/'.join(sorted(ag.TIPOS))})")
                if not cli_m: faltan.append("cliente (di 'para <nombre>')")
                if faltan:
                    return {"respuesta": "Para agendar la cita real me falta: " + ", ".join(faltan) + ". No invento estos datos."}

                r = await asyncio.to_thread(
                    ag.crear_cita, cli_m.group(1).strip(), cli_m.group(1).strip(),
                    tel_m.group(1) if tel_m else "", fecha, hora, tipo_m)
                if r.get("status") == "ok":
                    return {"respuesta": f"✅ Cita real agendada (id {r['id']}): {cli_m.group(1).strip()}, {fecha} {hora}, {tipo_m}."}
                return {"respuesta": f"No pude agendarla (no te miento): {r.get('error', r.get('status'))}"}

            # Dia especifico real — antes "hoy"/"manana" siempre regresaban el
            # resumen general sin filtrar por fecha (encontrado en vivo hoy).
            fecha_pedida = None
            if "manana" in m:
                fecha_pedida = (_dt.now() + _td(days=1)).strftime("%Y-%m-%d")
            elif "hoy" in m:
                fecha_pedida = _dt.now().strftime("%Y-%m-%d")
            else:
                fm = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", mensaje)
                if fm:
                    fecha_pedida = fm.group(1)

            if fecha_pedida:
                d = await asyncio.to_thread(ag.dia, fecha_pedida)
            elif "proxim" in m:
                d = await asyncio.to_thread(ag.proximas, 24)
            else:
                d = await asyncio.to_thread(ag.resumen)
            return {"respuesta": self._fmt_dict("📅 Agenda", d)}
        except Exception as e:
            return {"respuesta": f"No pude leer la agenda (no lo invento): {str(e)[:200]}"}

    async def _vendedor_real(self, mensaje: str) -> Dict:
        import re as _re
        m = _norm_txt(mensaje)
        # Regex en vez de find+slice: antes "ficha de" hacia match dentro de "ficha DEL
        # laser" (substring "de" cae adentro de "del"), dejando una "l" suelta pegada al
        # nombre del producto. \s+(?:del|de|para)\s+ consume la palabra completa que sea.
        # Encontrado en vivo 2026-07-27: "pitch DE VENTA para X" hacía que el separador
        # "de" cayera sobre el "de" de "de venta" (no sobre el que de verdad separa el
        # producto), dejando producto="venta para X" — la ficha nunca se encontraba y
        # el LLM terminaba inventando specs sin ningún dato real de por medio. Ahora
        # "pitch" también consume opcionalmente "de venta" como parte de la frase fija,
        # y "para" se suma como separador válido (forma natural: "pitch para X").
        match = _re.search(
            r"(?:ficha(?:\s+tecnica)?|(?:dame|hazme)?\s*(?:el\s+)?pitch(?:\s+de\s+venta)?|"
            r"argumentos?\s+de\s+venta|brief\s+de\s+venta|como\s+vend\w*)\s+(?:del|de|para)\s+(.+)", m)
        producto = mensaje[match.start(1):].strip(" :¿?.") if match else mensaje
        try:
            ven = _vendedor()
            if any(k in m for k in ("pitch", "argumento", "brief", "como vend")):
                # Verificación real ANTES del LLM: construir_brief() ya le dice al LLM
                # "no inventes" cuando no hay ficha, pero un modelo puede no seguirlo
                # (confirmado en vivo 2026-07-27: generó specs inventadas — "30% más
                # visibilidad", "resistentes a la corrosión" — sin ningún dato real).
                # Cortar aquí en código, no solo con una instrucción de prompt.
                dz = await asyncio.to_thread(ven.ficha, producto)
                if dz.get("status") != "OK":
                    return {"respuesta": f"No tengo ficha real de '{producto}' — no invento el pitch. "
                            + (f"Disponibles: {', '.join(dz.get('disponibles', [])[:10])}" if dz.get("disponibles") else "")}
                prompt_sistema = await asyncio.to_thread(ven.construir_brief, "cliente", producto, "", "")
                # construir_brief() arma un PROMPT DE SISTEMA para alimentar un LLM, no un
                # pitch redactado — antes se mostraba crudo (con JSON y todo) al usuario.
                # Ahora sí pasa por el LLM para generar el pitch real, igual que lo usa
                # aurora_server.py.
                if self._groq:
                    try:
                        r = await self._groq.chat.completions.create(
                            model=_MODELO,
                            messages=[{"role": "system", "content": prompt_sistema},
                                      {"role": "user", "content": f"Dame el pitch de venta para {producto}."}],
                            max_tokens=500, temperature=0.6)
                        return {"respuesta": f"🎯 {r.choices[0].message.content.strip()}"}
                    except Exception:
                        pass
                return {"respuesta": f"🎯 Brief de venta ({producto}) — sin LLM disponible para redactarlo, "
                        f"aquí el contexto real usado:\n{prompt_sistema[:1500]}"}
            d = await asyncio.to_thread(ven.ficha, producto)
            return {"respuesta": self._fmt_dict(f"📄 Ficha: {producto}", d)}
        except Exception as e:
            return {"respuesta": f"No pude traer la ficha (no la invento): {str(e)[:200]}"}

    async def _intuicion_real(self, mensaje: str) -> Dict:
        try:
            from MEMORIA.perfil_habilidades import perfil_habilidades
            await perfil_habilidades.inicializar()
            sug = await perfil_habilidades.sugerencia_proactiva()
            perfil = await perfil_habilidades.obtener_perfil()
            areas = perfil.get("areas_oportunidad", []) if isinstance(perfil, dict) else []
            if not sug and not areas:
                return {"respuesta": "Mi intuición aún está aprendiendo de tu uso (poco historial). Entre más usemos AURORA, mejor te sugiero. Por ahora no te invento una recomendación."}
            txt = "🔮 Mi intuición según cómo usas AURORA:\n"
            if sug:
                txt += f"• {sug}\n"
            for a in areas[:5]:
                txt += f"• {a}\n"
            return {"respuesta": txt.strip()}
        except Exception as e:
            return {"respuesta": f"No pude generar la sugerencia (no la invento): {str(e)[:200]}"}

    async def _memoria_real(self, mensaje: str) -> Dict:
        import re as _re
        # Extrae la entidad real de "que recuerdas de X" — antes usaba _tema_rapido, que
        # solo reconoce 4 categorías fijas (ventas/coaching/marketing) y para la mayoría
        # de preguntas reales devolvía tema="", cayendo a "los 5 recuerdos más recientes
        # en general" en vez de honestamente decir que no tenía nada sobre X.
        m = _norm_txt(mensaje)
        match = _re.search(r"(?:que recuerdas de|que recuerdas sobre|recuerdas cuando|"
                           r"que sabes de|que tienes guardado sobre|recuerdas que)\s+(.+)", m)
        tema = mensaje[match.start(1):].strip(" :¿?.") if match else ""
        tema = tema or self._tema_rapido(mensaje)
        # Preguntas como "a cuánto corto MDF de 2.7" no traen "qué recuerdas de",
        # así que no dejan tema. Se saca del propio mensaje quitando lo que no
        # aporta: lo que queda ("mdf") es lo que hay que buscar. Sin esto, la
        # memoria devolvía lo más reciente en general en vez de lo pedido.
        if not tema:
            _vacias = {
                "a", "de", "del", "la", "el", "los", "las", "un", "una", "en",
                "con", "por", "para", "que", "cual", "como", "cuanto", "cuanta",
                "corto", "cortar", "grabo", "grabar", "hago", "hacer", "le",
                "me", "mi", "es", "esta", "y", "o", "aurora", "dime", "oye",
                "potencia", "velocidad", "parametros", "configuracion", "ajuste",
                "receta", "galga", "distancia", "foco",
            }
            _palabras = [p for p in _re.findall(r"[a-z0-9.]{2,}", m)
                         if p not in _vacias]
            tema = " ".join(_palabras[:3])
        try:
            recuerdos = await self._memoria.recordar(tema=tema, limite=5)
            if not recuerdos:
                return {"respuesta": f"No tengo nada guardado sobre {'eso' if not tema else tema} todavía (no te invento un recuerdo)."}
            txt = "🧠 Lo que recuerdo:\n"
            for k in recuerdos:
                c = k.get("conocimiento") if isinstance(k, dict) else str(k)
                if c:
                    txt += f"• {c}\n"
            return {"respuesta": txt.strip()}
        except Exception as e:
            return {"respuesta": f"No pude consultar mi memoria: {str(e)[:200]}"}

    async def _equipos_real(self, mensaje: str) -> Dict:
        m = _norm_txt(mensaje)
        try:
            eq = _equipos()
            if any(k in m for k in ("activa", "activar", "arma", "pon a trabajar")):
                equipo_id = "marketing"
                for k in ("marketing", "publicacion", "ventas", "diseno", "taller"):
                    if k in m:
                        equipo_id = k
                        break
                d = await asyncio.to_thread(eq.activar_equipo, equipo_id)
                estado_real = "activado" if d.get("status") == "ok" else "NO se activó"
                return {"respuesta": self._fmt_dict(f"🤝 Equipo '{equipo_id}' {estado_real}", d)}
            d = await asyncio.to_thread(eq.listar_equipos)
            return {"respuesta": self._fmt_dict("🤝 Equipos disponibles", d)}
        except Exception as e:
            return {"respuesta": f"No pude activar el equipo (no lo simulo): {str(e)[:200]}"}

    # ── FÁBRICA DE AGENTES (pregunta-antes-de-crear, con el contexto de Anuar) ──
    async def _fabrica_agentes_iniciar(self, session_id: str, mensaje: str) -> Dict:
        m = mensaje
        for t in ("créame un agente", "creame un agente", "crea un agente", "crear un agente",
                  "fabrícame un agente", "fabricame un agente", "fabrica un agente",
                  "necesito un agente", "quiero un agente", "arma un agente", "nuevo agente",
                  "que ", "para "):
            i = _norm_txt(m).find(_norm_txt(t))
            if i == 0:
                m = m[len(t):]
        objetivo = m.strip(" :,.¿?").strip() or "(por definir)"
        self._agente_en_creacion[session_id] = {"objetivo": objetivo}
        return {"respuesta": (
            f"🤖 Va, armo un agente para: **{objetivo}**.\n"
            "Para hacerlo bien y no romper nada, dame el contexto en UN mensaje:\n"
            "1) ¿Con qué datos/fuentes trabaja? (productos, competidores, carpeta, etc.)\n"
            "2) ¿Cada cuándo debe correr, o es a demanda?\n"
            "3) ¿Qué hago con el resultado? (te aviso / lo guardo / lo publico)\n"
            "_(o escribe 'cancelar' para dejarlo)_")}

    async def _fabrica_agentes_contexto(self, session_id: str, mensaje: str) -> Dict:
        if _norm_txt(mensaje).strip() in ("cancelar", "cancela", "olvidalo", "dejalo"):
            self._agente_en_creacion.pop(session_id, None)
            return {"respuesta": "Listo, cancelé la creación del agente. No creé nada."}
        spec = self._agente_en_creacion.pop(session_id, {})
        objetivo = spec.get("objetivo", "(sin objetivo)")
        contexto = mensaje.strip()
        nombre = " ".join(objetivo.split()[:5]).capitalize() or "Agente"
        try:
            r = await asyncio.to_thread(_fab_agentes().crear_agente, nombre, objetivo, contexto)
            ag = r["agente"]
            return {"respuesta": (
                f"✅ Creé el agente **{ag['nombre']}** de verdad (guardado en AGENTES/).\n"
                f"• Objetivo: {ag['objetivo']}\n• Contexto: {ag['contexto'][:200]}\n"
                f"Para usarlo dime: «corre el agente {ag['nombre']}». Nada corre solo sin tu orden.")}
        except Exception as e:
            return {"respuesta": f"No pude crear el agente (no lo simulo): {str(e)[:200]}"}

    async def _listar_agentes_real(self) -> Dict:
        try:
            d = await asyncio.to_thread(_fab_agentes().listar_agentes)
            if not d.get("total"):
                return {"respuesta": "Aún no tienes agentes. Dime «créame un agente para…» y lo armamos."}
            lineas = ["🤖 Tus agentes:"]
            for a in d["agentes"]:
                lineas.append(f"• **{a['nombre']}** — {a['objetivo'][:70]} (corridas: {a.get('ejecuciones',0)})")
            return {"respuesta": "\n".join(lineas)}
        except Exception as e:
            return {"respuesta": f"No pude listar los agentes: {str(e)[:200]}"}

    async def _correr_agente_real(self, mensaje: str) -> Dict:
        m = mensaje
        for t in ("corre el agente", "ejecuta el agente", "activa el agente",
                  "pon a correr el agente", "usa el agente", "lanza el agente"):
            i = _norm_txt(m).find(_norm_txt(t))
            if i >= 0:
                m = m[i + len(t):]
                break
        nombre = m.strip(" :,.¿?").strip()
        fab = _fab_agentes()
        spec = await asyncio.to_thread(fab.obtener_agente, nombre)
        if not spec:
            return {"respuesta": f"No encontré un agente llamado '{nombre}'. Dime «qué agentes tengo» para verlos."}
        # Contexto real extra: si el objetivo huele a web, le doy resultados reales.
        extra = ""
        obj = _norm_txt(spec.get("objetivo", "") + " " + spec.get("contexto", ""))
        try:
            if any(k in obj for k in ("precio", "competencia", "mercado", "internet", "busca", "tendencia")):
                extra = await asyncio.to_thread(_web_real().contexto_para_llm,
                                                spec.get("objetivo", ""), 3)
        except Exception:
            extra = ""
        prompt = fab.prompt_ejecucion(spec, extra)
        if not self._groq:
            return {"respuesta": "El agente está creado, pero para EJECUTARLO necesito el cerebro (Groq/nube) y ahora no está disponible. No te invento su resultado."}
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO, messages=[{"role": "user", "content": prompt}], max_tokens=700)
            salida = r.choices[0].message.content.strip()
            await asyncio.to_thread(fab.marcar_ejecucion, spec["slug"])
            return {"respuesta": f"🤖 **{spec['nombre']}** ejecutado:\n\n{salida}"}
        except Exception as e:
            return {"respuesta": f"No pude ejecutar el agente (no lo simulo): {str(e)[:200]}"}

    # ── ENRUTADOR UNIVERSAL (tool-calling sobre el registro de 203 funciones reales) ──
    async def _ejecutar_herramienta_real(self, reg, clave: str, args: dict, h: dict) -> Dict:
        """Ejecuta una herramienta del registro y formatea el resultado. Nunca inventa."""
        try:
            res = await asyncio.to_thread(reg.ejecutar, clave, args)
        except Exception as e:
            return {"respuesta": f"Intenté usar {clave} pero falló (no lo invento): {str(e)[:200]}"}
        if not isinstance(res, dict) or res.get("status") != "ok":
            detalle = res.get("detalle") if isinstance(res, dict) else str(res)
            return {"respuesta": f"No pude completar {clave} (no lo invento): {str(detalle)[:250]}"}
        salida = res.get("resultado")
        titulo = f"🔧 {h.get('funcion', clave)}"
        if isinstance(salida, dict):
            texto = self._fmt_dict(titulo, salida)
        elif isinstance(salida, (list, tuple)):
            texto = titulo + ":\n" + "\n".join(f"• {x}" for x in list(salida)[:30])
        else:
            texto = f"{titulo}:\n{str(salida)[:1500]}"
        return {"respuesta": texto}

    async def _cotizar_real(self, mensaje: str) -> Dict:
        """Cotiza con los precios REALES del catálogo. Si no encuentra, lo dice.

        Usa el catálogo del negocio que corresponda: ATF (98 productos) o Milens
        (73 servicios). Nunca inventa un precio — es lo que le diría a un cliente.
        """
        import importlib.util as _ilu
        from pathlib import Path as _P
        raiz = _P(__file__).resolve().parent.parent
        try:
            spec = _ilu.spec_from_file_location("motor_cotizador", raiz / "MOTORES" / "motor_cotizador.py")
            mc = _ilu.module_from_spec(spec); spec.loader.exec_module(mc)
        except Exception as e:
            return {"respuesta": f"No pude cargar el cotizador: {str(e)[:120]}"}

        negocio = mc._detectar_negocio(mensaje)
        catalogo, err = (mc._catalogo_atf_real() if negocio == "atf"
                         else mc._catalogo_milens_real())
        if not catalogo:
            return {"respuesta": f"No pude leer el catálogo de {negocio.upper()}: {err}"}

        # Cuántas piezas pide, si lo dice.
        cantidad = 1
        mn = re.search(r"\b(\d{1,4})\s*(?:pz|pzs|piezas?|unidades?)?\b", _norm_txt(mensaje))
        if mn and int(mn.group(1)) <= 5000:
            cantidad = max(1, int(mn.group(1)))

        # Un código de modelo manda sobre todo lo demás. Caso real 2026-08-03:
        # "cuanto cuesta el faro aozoom x5" devolvía faros LED genéricos porque
        # la palabra "faro" calzaba con muchos, cuando el X5 es un producto
        # exacto del catálogo (Proyector Bi-LED X5 2.5", $1,599, sku AOZ-X5).
        # Si el cliente dice el modelo, quiere ESE, no algo parecido.
        _codigos = re.findall(r"\b([a-zA-Z]{1,3}\s?-?\s?\d{1,3})\b", _norm_txt(mensaje))
        encontrados = {}
        for cod in _codigos:
            c = cod.replace(" ", "").replace("-", "").lower()
            if len(c) < 2 or c.isdigit():
                continue
            exactos = {
                k: v for k, v in catalogo.items()
                if c in _norm_txt(str(v.get("sku", ""))).replace("-", "")
                or re.search(rf"\b{re.escape(c)}\b", _norm_txt(str(v.get("nombre", ""))).replace("-", ""))
            }
            if exactos:
                encontrados = exactos
                break

        if not encontrados:
            encontrados = mc._filtrar_catalogo(catalogo, mensaje)
        if not encontrados:
            # Segunda pasada: se quitan los adjetivos que no están en el catálogo.
            # Caso real: "20 playeras negras talla g" no encontraba nada, teniendo
            # playeras a $260 — el color y la talla tumbaban la búsqueda entera.
            _RUIDO = ("negras", "negra", "blancas", "blanca", "rojas", "roja", "azules",
                      "azul", "verdes", "verde", "talla", "chica", "mediana", "grande",
                      "chicas", "medianas", "grandes", "personalizada", "personalizadas",
                      "con logo", "logo", "estampada", "estampadas", "por favor", "porfa")
            limpio = _norm_txt(mensaje)
            for r in _RUIDO:
                limpio = re.sub(rf"\b{re.escape(r)}\b", " ", limpio)
            limpio = re.sub(r"\s{2,}", " ", limpio).strip()
            if limpio and limpio != _norm_txt(mensaje):
                encontrados = mc._filtrar_catalogo(catalogo, limpio)

        if not encontrados:
            ejemplos = ", ".join(list(catalogo.values())[i].get("nombre", "")
                                 for i in range(min(4, len(catalogo))))
            return {"respuesta": (
                f"No encontré eso en el catálogo de {negocio.upper()} — y **no te "
                f"invento un precio**.\n\nAhí tengo cosas como: {ejemplos}.\n"
                "Dime el nombre como aparece en tu catálogo y te lo cotizo al instante.")}

        lineas, total = [], 0.0
        for v in list(encontrados.values())[:6]:
            nombre = v.get("nombre", "?")
            precio = float(v.get("precio") or v.get("precio_publico") or 0)
            if not precio:
                lineas.append(f"• {nombre} — sin precio en el catálogo")
                continue
            sub = precio * cantidad
            total += sub
            lineas.append(f"• {nombre} — ${precio:,.2f}"
                          + (f" x{cantidad} = **${sub:,.2f}**" if cantidad > 1 else ""))

        cab = f"💰 Cotización con tus precios reales de **{negocio.upper()}**:"
        pie = (f"\n\n**Total: ${total:,.2f}**" if cantidad > 1 and total else "")
        if len(encontrados) > 6:
            pie += f"\n_(hay {len(encontrados) - 6} coincidencias más; afina el nombre)_"
        return {"respuesta": f"{cab}\n" + "\n".join(lineas) + pie}

    async def _video_real(self, mensaje: str) -> Dict:
        """Trabaja con la videoteca: revisar, voltear a 9:16 y buscar repetidos."""
        m = _norm_txt(mensaje)
        try:
            from MARKETING import motor_video as _mv
        except Exception as e:
            return {"respuesta": f"No pude cargar el motor de video: {str(e)[:120]}"}

        # ¿Cuántos videos hay repetidos?
        if _contiene_trigger(m, ("duplicado", "duplicados", "repetido", "repetidos")):
            r = await asyncio.to_thread(_mv.buscar_duplicados)
            if r.get("status") != "OK":
                return {"respuesta": f"No pude revisar: {r.get('mensaje')}"}
            if not r["grupos_repetidos"]:
                return {"respuesta": f"Revisé {r['revisados']} videos y no hay repetidos."}
            ejemplos = "\n".join(
                f"• {Path(g['conservar']).name} — {len(g['repetidos'])} copia(s), {g['mb']} MB c/u"
                for g in r["grupos"][:8])
            return {"respuesta": (
                f"De {r['revisados']} videos, **{r['copias_de_mas']} son copias repetidas** "
                f"({r['gb_desperdiciados']} GB de más).\n\n{ejemplos}\n\n"
                "Solo te lo reporto — borrar lo decides tú.")}

        # Voltear un archivo concreto que venga en el mensaje.
        mruta = re.search(r"[A-Za-z]:\\[^\r\n]+?\.(?:mp4|mov|avi|mkv|webm)", mensaje, re.I)
        if mruta:
            modo = "recorte" if _contiene_trigger(m, ("recorta", "recorte", "centro")) else "fondo"
            r = await asyncio.to_thread(_mv.a_vertical, mruta.group(0), "", modo)
            if r.get("status") != "OK":
                return {"respuesta": f"No pude convertirlo: {r.get('mensaje')}"}
            p = await asyncio.to_thread(_mv.miniatura, r["salida"])
            extra = f"\nPortada: {p['salida']}" if p.get("status") == "OK" else ""
            return {"respuesta": (f"✅ Listo para TikTok/Reels:\n{r['salida']}\n"
                                  f"({r['de']} → {r['a']}, {r['mb']} MB){extra}")}

        # Preparar un lote: es lo que de verdad hace falta para publicar hoy.
        if _contiene_trigger(m, ("prepara", "preparar", "voltea", "voltear", "convierte",
                                 "convertir", "listos para publicar")):
            n = 10
            mn = re.search(r"\b(\d{1,3})\b", m)
            if mn:
                n = max(1, min(50, int(mn.group(1))))
            r = await asyncio.to_thread(_mv.preparar_lote, n, "fondo")
            if r.get("status") != "OK":
                return {"respuesta": f"No pude: {r.get('mensaje')}"}
            if not r.get("convertidos"):
                return {"respuesta": r.get("mensaje", "No había videos horizontales pendientes.")}
            return {"respuesta": (
                f"✅ Dejé **{r['convertidos']} videos listos** para TikTok y Reels, "
                f"cada uno con su portada.\n📁 {r['carpeta']}\n"
                + (f"Faltan {r['faltan']} horizontales por voltear.\n" if r.get("faltan") else "")
                + (f"⚠️ {r['fallidos']} no se pudieron.\n" if r.get("fallidos") else ""))}

        # Por defecto: el estado de la videoteca.
        r = await asyncio.to_thread(_mv.listos_para_publicar)
        if r.get("status") != "OK":
            return {"respuesta": f"No pude revisar la videoteca: {r.get('mensaje')}"}
        return {"respuesta": (
            f"📹 Tu videoteca ({r['revisados']} videos):\n"
            f"• **{r['ya_sirven']}** ya sirven para Reels tal cual (verticales)\n"
            f"• **{r['hay_que_voltear']}** hay que voltear a 9:16\n"
            f"• {r['muy_largos']} son muy largos (más de 90 s)\n\n"
            "Dime «prepara 10 videos para publicar» y te los dejo listos con portada.")}

    async def _voz_real(self, mensaje: str) -> Dict:
        """Prende, apaga o prueba la voz.

        Portada del sistema de NEXUS que Anuar ya tenía funcionando: VOSK local
        vigila el nombre (gratis, sin internet) y Whisper de Groq transcribe el
        comando. Lo importante del cableado: el comando entra por el MISMO
        `procesar()` que el chat, así que hereda el candado de honestidad. Si la
        voz hablara directo con el modelo, podría mentir sin que nadie la revise
        — y por voz es peor, porque no queda por escrito.
        """
        m = _norm_txt(mensaje)
        try:
            from VOZ import servicio_voz as _sv
        except Exception as e:
            return {"respuesta": f"No pude cargar la voz: {str(e)[:120]}"}

        if _contiene_trigger(m, ("apaga", "desactiva", "callate", "deja de escuchar")):
            if getattr(self, "_voz", None):
                self._voz.detener()
                self._voz = None
                return {"respuesta": "Listo, dejo de escuchar."}
            return {"respuesta": "La voz ya estaba apagada."}

        if _contiene_trigger(m, ("prueba", "como suenas", "di algo", "hablame")):
            cfg = _sv.config()
            ok = await asyncio.to_thread(
                _sv.hablar, f"Soy {cfg['nombre']}. Así me oigo. "
                            f"Dime mi nombre y te escucho.")
            return {"respuesta": ("🔊 Acabo de hablar por las bocinas." if ok else
                                  "No pude hablar: revisa que las bocinas estén encendidas.")}

        if getattr(self, "_voz", None) and self._voz.corriendo:
            return {"respuesta": f"Ya te estoy escuchando. Dime «{_sv.config()['nombre']}»."}

        def _atender(texto_oido: str) -> str:
            """Lo que se oyó entra al cerebro completo, igual que si se escribiera."""
            try:
                bucle = asyncio.new_event_loop()
                try:
                    r = bucle.run_until_complete(
                        self.procesar(texto_oido, "anuar", session_id="voz", canal="voz"))
                finally:
                    bucle.close()
                return r.get("respuesta", "")
            except Exception as e:
                logger.error(f"[VOZ] falló al procesar: {e}")
                return "Algo falló. No te invento el resultado."

        try:
            self._voz = _sv.ServicioVoz(_atender)
            self._voz.arrancar()
        except Exception as e:
            return {"respuesta": f"No pude encender el micrófono: {str(e)[:130]}"}

        cfg = _sv.config()
        return {"respuesta": (
            f"🎤 Te escucho. Dime **«{cfg['nombre']}»** y luego lo que necesites.\n"
            f"Ejemplo: «{cfg['nombre']}, cuánto llevo vendido este mes».\n\n"
            "También te aviso hablando si la PC se queda sin memoria. "
            "Para que pare: «apaga la voz».")}

    async def _ver_aprendizaje_real(self, mensaje: str) -> Dict:
        """Muestra o borra lo que AURORA aprendió de cómo habla su dueño."""
        from CEREBRO import aprende_del_usuario as _apr
        m = _norm_txt(mensaje)

        if _contiene_trigger(m, ("olvidalo todo", "borra lo aprendido",
                                 "olvida todo lo aprendido")):
            r = await asyncio.to_thread(_apr.olvidar_todo)
            return {"respuesta": f"Listo, olvidé las {r['borrados']} formas que había "
                                 "aprendido. Empiezo de cero contigo."}

        if m.startswith("olvida ") or " olvida " in m:
            que = re.sub(r".*\bolvida\b", "", mensaje, flags=re.I).strip(" \"'")
            r = await asyncio.to_thread(_apr.olvidar, que)
            if r.get("status") != "OK":
                return {"respuesta": r.get("mensaje", "Dime qué olvido.")}
            if not r["borrados"]:
                return {"respuesta": f"No tenía nada aprendido con «{que}». "
                                     f"Me quedan {r['quedan']} formas."}
            return {"respuesta": f"Olvidé {r['borrados']} forma(s) con «{que}». "
                                 f"Me quedan {r['quedan']}."}

        lista = await asyncio.to_thread(_apr.listar)
        if not lista:
            return {"respuesta": "Todavía no he aprendido nada de cómo hablas.\n"
                                 "Aprendo sola: cuando algo no lo entiendo y me lo "
                                 "dices de otra forma que sí funciona, me quedo con las dos."}
        propias = [i for i in lista if not i.get("precargado")]
        semilla = [i for i in lista if i.get("precargado")]
        lineas = [f"• «{i['como_lo_dijo']}» → {i['herramienta']}"
                  + (f"  ({i['veces']} veces)" if int(i.get("veces", 1)) > 1 else "")
                  for i in (propias or lista)[:15]]
        extra = (f"\n\nY {len(semilla)} formas que ya traía cargadas de fábrica."
                 if semilla and propias else "")
        cab = ("Esto he aprendido de cómo hablas:" if propias
               else "Todo lo que tengo viene precargado, aún no aprendo nada tuyo:")
        return {"respuesta": f"{cab}\n" + "\n".join(lineas) + extra +
                             "\n\nSi algo está mal, dime «olvida <la frase>»."}

    async def _ruta_sola_real(self, mensaje: str, session_id: str = "", canal: str = "api") -> Dict:
        """Llegó solo una ruta. Es el dato que faltaba para lo que se pidió antes.

        Se pega la ruta al último mensaje de la sesión y se reprocesa: si antes
        dijo "abre esta imagen en corel", el combinado SÍ calza con el candado de
        Corel y se ejecuta de verdad. Sin contexto previo, se ofrece lo que
        REALMENTE se puede hacer con ese tipo de archivo — nunca un "no puedo".
        """
        ruta = _RE_RUTA_SOLA.match(mensaje.strip()).group(1)

        # Si no está tal cual, se busca en su carpeta un archivo que empiece
        # igual. Caso real: Anuar escribió "...\trailler hot" y en disco hay
        # "trailler hot" (sin extensión), "traylhot.dxf" y "tractor trailer.cdr".
        # Antes se rendía; ahora ofrece lo que de verdad hay ahí.
        if not Path(ruta).exists():
            p = Path(ruta)
            try:
                parecidos = sorted(p.parent.glob(p.name + "*")) if p.parent.exists() else []
            except OSError:
                parecidos = []
            if len(parecidos) == 1:
                ruta = str(parecidos[0])
            elif len(parecidos) > 1:
                opciones = "\n".join(f"• {q.name}" for q in parecidos[:6])
                return {"respuesta": f"Hay varios que empiezan así. ¿Cuál?\n{opciones}"}
            else:
                return {"respuesta": f"No encontré ese archivo en el disco:\n`{ruta}`\n"
                                     "Revisa la ruta y te lo trabajo."}

        existe = True
        ext = Path(ruta).suffix.lower().lstrip(".")

        # Sin extensión no se sabe qué es, pero SÍ existe: eso ya es información
        # útil. Nunca se responde "no puedo" con un archivo real en la mano.
        if not ext:
            kb = round(Path(ruta).stat().st_size / 1024, 1)
            return {"respuesta": (
                f"Tengo el archivo `{Path(ruta).name}` ({kb} KB), pero **no trae extensión**, "
                "así que no sé de qué tipo es.\n\n"
                "Dime qué es y lo trabajo:\n"
                f"• `corel abre {ruta}` — intenta abrirlo en Corel\n"
                f"• `vectoriza {ruta}` — si es una imagen\n"
                f"• `convierte a dxf {ruta}` — si es un vector\n\n"
                "O renómbralo con su extensión y lo reconozco solo.")}

        # Se lee del historial de sesión, que YA persiste entre mensajes y está
        # probado (es el que alimenta el contexto del chat). El primer intento usó
        # un diccionario nuevo y nunca se activó — la memoria de sesión ya resolvía
        # esto y no hacía falta inventar otro mecanismo.
        previo = ""
        for turno in reversed(self._memoria_corto.get(session_id, [])):
            if turno.get("rol") != "user":
                continue
            texto = (turno.get("contenido") or "").strip()
            if not texto or _es_ruta_sola(texto):
                continue
            _t = _norm_txt(texto)
            # Solo se completa si lo anterior hablaba de un archivo. "Cuánto vendí
            # este mes" + una ruta sería absurdo.
            if any(k in _t for k in ("archivo", "imagen", "foto", "documento",
                                     "corel", "vectoriza", "convierte", "dxf",
                                     "abre", "abrir", "esto", "este", "esta")):
                previo = texto
            break

        if previo:
            # No se recursa: el combinado ya no es una ruta sola, así que este
            # candado no se vuelve a disparar.
            combinado = f"{previo} {ruta}"
            logger.info(f"[RUTA SOLA] Completando la petición anterior: {combinado[:90]}")
            r = await self._procesar_interno(combinado, "anuar", session_id, canal)
            r["respuesta"] = (f"(Tomé la ruta como el dato que faltaba para: «{previo}»)\n\n"
                              + r.get("respuesta", ""))
            return r

        # Sin contexto: se ofrecen las acciones REALES según el tipo de archivo.
        if ext in ("jpg", "jpeg", "png", "bmp", "webp"):
            puede = ("• `corel abre {r}` — la importa a Corel\n"
                     "• `vectoriza {r}` — la traza y genera SVG + DXF\n"
                     "• `corel quita el fondo {r}` — la limpia y la mete a Corel")
        elif ext in ("pdf", "cdr", "ai", "eps"):
            puede = ("• `corel abre {r}` — lo abre en Corel\n"
                     "• `convierte a dxf {r}` — lo pasa a DXF para corte")
        elif ext in ("svg", "dxf"):
            puede = "• `convierte a dxf {r}` — lo prepara para corte"
        else:
            puede = "• `corel abre {r}` — intenta abrirlo en Corel"

        return {"respuesta": f"Tengo el archivo `{Path(ruta).name}`. ¿Qué le hago?\n\n"
                             + puede.format(r=ruta)}

    async def _confirmar_accion_pendiente(self, session_id: str) -> Dict:
        """El usuario dijo 'sí' a una acción peligrosa propuesta antes. La ejecuta de verdad.
        Re-presenta qué es exactamente lo que va a correr antes del resultado — no asume
        que Anuar recuerda el detalle exacto del turno anterior."""
        pendiente = self._accion_pendiente.pop(session_id, None)
        if not pendiente:
            return {"respuesta": "No tengo ninguna acción pendiente de confirmar — dime qué necesitas."}
        if pendiente.get("tipo") == "editar_nucleo":
            r = await self._editar_codigo_real(pendiente["mensaje"], saltar_confirmacion=True)
            r["respuesta"] = "Confirmado — edición del núcleo:\n" + r["respuesta"]
            return r
        if pendiente.get("tipo") == "publicar_facebook":
            pub = _pubint()
            d = await asyncio.to_thread(pub.publicar_hoy, "facebook", "", True)
            if d.get("status") == "PUBLICADO":
                return {"respuesta": f"✅ PUBLICADO de verdad en Facebook ATF (post {d.get('post_id')}). Video: {d.get('video','')}"}
            return {"respuesta": f"No publiqué (no lo simulo): {self._fmt_dict('publicar_hoy', d)}"}
        reg = _registro()
        r = await self._ejecutar_herramienta_real(reg, pendiente["clave"], pendiente["args"], pendiente["h"])
        params_usados = ", ".join(f"{k}={v}" for k, v in pendiente["args"].items()) or "sin datos extra"
        # Antes re-leía la clave y todos los parámetros con signos. Al confirmar
        # ya no hace falta repetir QUÉ se va a hacer: se hace y se entrega el
        # resultado. Anuar lo pidió textual: es tedioso y largo, sobre todo por voz.
        r["respuesta"] = "Hecho. " + r["respuesta"]
        return r

    async def _router_universal(self, mensaje: str, session_id: str = "", canal: str = "api") -> Optional[Dict]:
        """Elige y EJECUTA una herramienta real del registro para responder con datos
        de verdad (no candados a mano). Devuelve {'respuesta': ...} o None si ninguna aplica.
        NUNCA inventa: si no hay herramienta o falla, lo dice honesto."""
        try:
            reg = _registro()
            candidatas = await asyncio.to_thread(reg.buscar, mensaje, 6)
        except Exception as e:
            logger.debug(f"Router universal: registro no disponible ({e}); sigue flujo normal")
            return None
        if not candidatas:
            return None
        if not self._groq:
            return None

        # Prompt: el LLM elige UNA herramienta (o null). Solo JSON, sin inventar valores.
        lineas = []
        por_clave = {}
        for h in candidatas:
            por_clave[h["clave"]] = h
            params = ", ".join(h.get("params", [])) or "(sin parámetros)"
            lineas.append(f'- clave: "{h["clave"]}"\n  hace: {h.get("doc","")}\n  params: {params}')
        catalogo = "\n".join(lineas)
        prompt = (
            "Eres el enrutador de AURORA. Elige UNA herramienta de la lista que responda DE VERDAD "
            "al mensaje del usuario, o null si NINGUNA aplica. Lee 'hace' de CADA una con cuidado "
            "antes de decidir — varias pueden sonar parecido pero hacer cosas distintas (ej: "
            "'convertir a DXF' NO es lo mismo que 'convertir al formato que pida el usuario'; "
            "si el usuario dice a qué formato específico quiere convertir, prioriza la herramienta "
            "genérica de conversión de formatos sobre una que convierte a un formato fijo distinto "
            "al pedido). NO inventes valores: solo pon en args los que se deduzcan del mensaje; deja "
            "fuera los que no sepas. Declara 'confianza' honesta: 'alta' SOLO si estás seguro de que "
            "esta herramienta específica es la correcta para lo que pide el mensaje; 'media' si aplica "
            "pero con dudas; 'baja' si es la menos mala de la lista pero no estás convencido.\n\n"
            f"HERRAMIENTAS:\n{catalogo}\n\n"
            f'MENSAJE DEL USUARIO: "{mensaje[:400]}"\n\n'
            'Responde SOLO JSON, sin texto extra: '
            '{"herramienta":"<clave o null>","confianza":"alta|media|baja","args":{...}}'
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO_SELECTOR, messages=[{"role": "user", "content": prompt}],
                max_tokens=200, temperature=0.0)
            raw = r.choices[0].message.content.strip()
        except Exception as e:
            logger.debug(f"Router universal: LLM falló ({e}); sigue flujo normal")
            return None

        # Parseo robusto: primer {...}
        try:
            i, j = raw.find("{"), raw.rfind("}")
            if i < 0 or j < 0:
                return None
            data = json.loads(raw[i:j + 1])
        except Exception:
            return None
        clave = data.get("herramienta")
        if not clave or str(clave).lower() in ("null", "none", ""):
            return None
        h = por_clave.get(clave)
        if not h:
            return None
        args = data.get("args") if isinstance(data.get("args"), dict) else {}
        confianza = str(data.get("confianza", "media")).lower()

        # VERIFICACIÓN REAL antes de ejecutar a ciegas — no solo la palabra del modelo.
        # Esto es código determinista alrededor de una llamada probabilística: el modelo
        # puede equivocarse (pasó hoy: eligió crear_planilla para un pedido de dibujo
        # lineal), pero el sistema que lo rodea no tiene por qué heredar esa duda.
        requeridos = h.get("requeridos", h.get("params", []))
        faltantes = [p for p in requeridos if p not in args]

        # Si faltan TODOS los datos, la herramienta está mal elegida — no es que
        # falte un dato. Encontrado en vivo 2026-07-30: a "usa coreldraw para
        # vectorizar el archivo que tengo abierto" respondió proponiendo
        # 'preparar_para_lona' (faltaban ancho_m, alto_m Y ruta_salida). Nadie
        # habló de lonas: inventó la INTENCIÓN. La herramienta sí existe, así que
        # el validador de honestidad la deja pasar — este es el hueco que cierra.
        # Nombrar una herramienta que no viene al caso es peor que callar: el
        # usuario cree que existe una capacidad relacionada con lo que pidió.
        if requeridos and len(faltantes) == len(requeridos):
            logger.warning(f"[ROUTER] Descartada '{clave}': faltan TODOS sus datos {faltantes}")
            return {"respuesta": (
                "No tengo una herramienta que haga eso. Dime con otras palabras qué "
                "necesitas —o la ruta completa del archivo— y lo reviso de verdad.")}

        if confianza == "baja" or faltantes:
            otras = [c for c in candidatas if c["clave"] != clave][:2]
            sugeridas = "".join(f"\n- {c['clave']}: {c.get('doc','')}" for c in otras)
            detalle = f"falta{'n' if len(faltantes)!=1 else ''} el dato{'s' if len(faltantes)!=1 else ''} {', '.join(faltantes)}" if faltantes else "no estoy segura de que sea la correcta"
            return {"respuesta": f"Encontré '{clave}' pero {detalle} para ejecutarla bien — no la corro a ciegas."
                    + (f" Herramientas relacionadas que también podrían aplicar:{sugeridas}" if sugeridas else "")
                    + " Dime más específico y la uso de verdad."}

        # Herramienta destructiva/escritura → NO ejecutar todavía; guarda el pendiente
        # para esta sesión y pide confirmación. Si Anuar responde "sí" en el siguiente
        # mensaje, se ejecuta de verdad (ver _confirmar_accion_pendiente). Por WhatsApp
        # ni siquiera se deja pendiente — un cliente real no debe poder confirmar
        # ninguna de las ~690 herramientas peligrosas del negocio con un simple "ok".
        if h.get("peligrosa"):
            if canal == "whatsapp":
                return {"respuesta": _MSG_SOLO_DUENIO}
            if session_id:
                self._accion_pendiente[session_id] = {"clave": clave, "args": args, "h": h}
            # Se pregunta EN CRISTIANO, no con la clave técnica y los parámetros
            # con signos. Anuar, 2026-07-31: "regresa con la lectura de lo que
            # ejecutará, puntos, comas, símbolos — eso no me interesa, además de
            # escucharse tedioso y largo". Y por voz es peor todavía.
            # El detalle técnico sigue guardado en el pendiente, solo no se lee.
            return {"respuesta": f"{self._en_cristiano(clave, args, h)} ¿Le doy?"}

        # No peligrosa → ejecutar de verdad.
        r = await self._ejecutar_herramienta_real(reg, clave, args, h)
        # Se marca CUÁL herramienta resolvió, para que el pipeline pueda
        # aprender la frase a la primera. La marca se quita antes de responder:
        # nunca sale al usuario.
        if isinstance(r, dict):
            r["_clave_usada"] = clave
        return r

    def _en_cristiano(self, clave: str, args: Dict, h: Dict) -> str:
        """Describe en lenguaje humano lo que se va a hacer, para preguntarlo.

        Anuar, 2026-07-31: "regresa con la lectura de lo que ejecutará, puntos,
        comas, símbolos — eso no me interesa, además de escucharse tedioso y
        largo". Por voz es peor: leer `MOTORES/motor_x:Clase.metodo (a=1, b=2)`
        es insoportable.

        Se usa la descripción real de la herramienta (su docstring, que ya está
        en el registro). Si no la tiene, se arma una frase del nombre de la
        función. Nunca se leen la clave técnica ni los parámetros con signos.
        """
        doc = (h.get("doc") or "").strip().split("\n")[0].strip()
        if doc:
            frase = doc.rstrip(".")
            frase = frase[0].lower() + frase[1:] if len(frase) > 1 else frase
            # El docstring viene en tercera persona ("Genera el contenido...").
            # El primer intento de pasarlo a infinitivo cortaba la última letra y
            # pegaba una terminación, y salían cosas como "Voy a lee", "Voy a
            # convierter", "Voy a truer" (encontrado en el barrido del 2026-08-02).
            # Conjugar español bien es más difícil que eso, así que se usa una
            # tabla de los verbos que de verdad aparecen en los docstrings, y si
            # no está en la tabla NO se inventa: se deja la frase tal cual, que se
            # lee raro pero no mal.
            primera, _, resto = frase.partition(" ")
            _INFINITIVOS = {
                "genera": "generar", "crea": "crear", "lee": "leer", "abre": "abrir",
                "convierte": "convertir", "exporta": "exportar", "guarda": "guardar",
                "busca": "buscar", "envia": "enviar", "publica": "publicar",
                "calcula": "calcular", "cotiza": "cotizar", "agenda": "agendar",
                "muestra": "mostrar", "lista": "listar", "devuelve": "devolver",
                "escala": "escalar", "extrae": "extraer", "aplica": "aplicar",
                "prueba": "probar", "revisa": "revisar", "verifica": "verificar",
                "analiza": "analizar", "arma": "armar", "prepara": "preparar",
                "registra": "registrar", "actualiza": "actualizar", "borra": "borrar",
                "mueve": "mover", "copia": "copiar", "cierra": "cerrar",
                "importa": "importar", "vectoriza": "vectorizar", "traza": "trazar",
                "descarga": "descargar", "sube": "subir", "manda": "mandar",
            }
            inf = _INFINITIVOS.get(primera)
            frase = f"{inf} {resto}".strip() if inf else frase
            base = f"Voy a {frase}." if inf else f"{frase[:1].upper()}{frase[1:]}."
        else:
            funcion = clave.split(":")[-1].split(".")[-1].replace("_", " ").strip()
            base = f"Voy a {funcion}." if funcion else "Voy a ejecutarlo."

        # Solo se mencionan los datos que un humano reconoce: nombres de archivo,
        # números y textos cortos. Nada de ids, banderas ni diccionarios.
        utiles = []
        for k, v in (args or {}).items():
            if isinstance(v, (dict, list)) or v in (None, "", True, False):
                continue
            texto = str(v).strip()
            if not texto or len(texto) > 60:
                continue
            if "\\" in texto or "/" in texto:
                texto = Path(texto).name          # solo el nombre, no la ruta entera
            utiles.append(texto)
        if utiles:
            base += " " + ", ".join(utiles[:3]) + "."
        return base

    def _fmt_dict(self, titulo: str, d) -> str:
        """Formatea el resultado REAL de un motor en texto legible, sin inventar."""
        import json as _json
        if not isinstance(d, dict):
            return f"{titulo}:\n{str(d)[:1200]}"
        partes = [titulo + ":"]
        for k, v in d.items():
            if k in ("status",):
                continue
            if isinstance(v, (list, dict)):
                s = _json.dumps(v, ensure_ascii=False)
                partes.append(f"• {k}: {s[:600]}")
            else:
                partes.append(f"• {k}: {v}")
        return "\n".join(partes)[:1800]

    # ── SÍNTESIS MULTI-MOTOR ───────────────────────────────────

    async def _accion_sistema_real(self, mensaje: str) -> Dict:
        """Ejecuta DE VERDAD una acción física, o dice honestamente por qué no.
        NUNCA finge. Devuelve {'respuesta': texto}."""
        import re, unicodedata as _ud
        from CEREBRO import acciones_sistema as _acc
        m = "".join(c for c in _ud.normalize("NFD", (mensaje or "").lower()) if _ud.category(c) != "Mn")

        # WhatsApp: reparar / limpiar cache — REAL
        if ("whatsapp" in m or "whats app" in m) and any(k in m for k in ("repar", "cache", "limpia", "arregla")):
            r = await asyncio.to_thread(_acc.reparar_whatsapp)
            texto = "✅ WhatsApp — hecho de verdad:\n- " + "\n- ".join(r["acciones"])
            texto += f"\nLiberado: {r['mb_liberados']} MB. {r['nota']}"
            return {"respuesta": texto}

        # Corel: reparar la CONEXION con Corel (cache corrupto de win32com) — REAL.
        # Agregado 2026-07-29: este arreglo se hizo A MANO la noche anterior porque
        # no existia como funcion. El cache corrupto deja todas las constantes de
        # Corel vacias y rompe en silencio escalar/planilla/lona/exportar PNG.
        if any(k in m for k in ("corel", "corell")) and any(k in m for k in ("repar", "cache", "arregla", "no responde", "no conecta")):
            r = await asyncio.to_thread(_acc.reparar_corel)
            if r.get("status") != "ok":
                return {"respuesta": f"No pude repararlo (no te miento): {r.get('detalle')}"}
            texto = "✅ Conexión con Corel — hecho de verdad:\n- " + "\n- ".join(r["acciones"])
            if r.get("verificado"):
                texto += "\n\nConfirmado con Corel real: quedó funcionando."
            else:
                texto += f"\n\n{r.get('nota')}"
            return {"respuesta": texto}

        # WhatsApp: ENVIAR un ARCHIVO real (adjunto) — REAL por Green API sendFileByUpload.
        # Antes esta capacidad no existía: el chat decía "no puedo enviar archivos" ante
        # un pedido real de un cliente (encontrado en vivo 2026-07-27).
        if (("whatsapp" in m or "whats app" in m or "wasap" in m or "watsap" in m)
                and any(k in m for k in ("archivo", "documento", "pdf", " el .pdf",
                                          "manda el", "envia el", "envialo", "mandalo"))):
            from CEREBRO.pc_access import _resolver_archivo_real
            fn = re.search(r"([\w\-. ]+\.(?:pdf|jpg|jpeg|png|docx?|xlsx?|dxf|cdr))", mensaje, re.I)
            if not fn:
                return {"respuesta": "Dame el nombre exacto del archivo (con extensión, ej. 'argan.pdf') que quieres mandar por WhatsApp."}
            ruta_pedida = fn.group(1).strip()
            if "/" not in ruta_pedida and "\\" not in ruta_pedida:
                ruta_pedida = f"descargas/{ruta_pedida}"
            p, err = _resolver_archivo_real(ruta_pedida)
            if err:
                return {"respuesta": err.get("mensaje", "No encontré el archivo — no lo invento.")}
            m_tel = re.search(r"(?<!\d)(?:\+?52[\s\-]?)?(\d[\d\s\-]{8,10}\d)(?!\d)", mensaje or "")
            tel = re.sub(r"\D", "", m_tel.group(0)) if m_tel else ""
            if len(tel) < 10:
                # No hay número: intenta resolver por nombre de contacto REAL en el CRM
                # (ORACLE) — nunca inventa un número que no exista. Reconoce "contacto
                # llamado X" y también la forma más natural "...a Fulano Perez [por
                # whatsapp]" (encontrado en vivo 2026-07-27: la primera no cubría "a
                # alfredo chiquilin", solo daba el mensaje genérico "ese contacto").
                nombre_match = re.search(
                    r"contacto (?:llamado |de nombre )?([a-zA-ZñÑáéíóúÁÉÍÓÚ ]{3,40})|"
                    r"\ba\s+([a-zA-ZñÑáéíóúÁÉÍÓÚ]+(?:\s+[a-zA-ZñÑáéíóúÁÉÍÓÚ]+){0,2})"
                    r"(?=\s+por\s+whatsapp|\s+por\s+wasap|\s+por\s+watsap|\s*$)",
                    mensaje or "", re.I)
                candidato = ((nombre_match.group(1) or nombre_match.group(2)) if nombre_match else "") or ""
                candidato = candidato.strip()
                encontrado = None
                if candidato:
                    try:
                        from ORACLE import oracle_core as _oc
                        await asyncio.to_thread(_oc.init_db)
                        leads = await asyncio.to_thread(_oc.listar_leads)
                        cn = _norm_txt(candidato)
                        encontrado = next((l for l in leads if cn in _norm_txt(l.get("nombre") or "")), None)
                    except Exception:
                        encontrado = None
                if encontrado and encontrado.get("telefono"):
                    tel = re.sub(r"\D", "", encontrado["telefono"])
                else:
                    return {"respuesta": f"No tengo el número de '{candidato or 'ese contacto'}' registrado en el CRM "
                            f"— dame el número (10 dígitos) y mando el archivo de verdad."}
            from INTEGRACIONES.whatsapp_integration import whatsapp as _wa
            r = await _wa.enviar_archivo("521" + tel[-10:], str(p))
            if r.get("status") == "ENVIADO":
                return {"respuesta": f"✅ Archivo '{p.name}' ENVIADO de verdad al {tel[-10:]} por WhatsApp (id {r.get('message_id')})."}
            return {"respuesta": f"No pude enviarlo (no te miento): {r}"}

        # WhatsApp: ENVIAR un mensaje — REAL por Green API. Si trae número, lo manda de
        # verdad; si no, lo pide honesto. NUNCA simula una conversación.
        if ("whatsapp" in m or "whats app" in m or "wasap" in m or "watsap" in m or
                "mandale un saludo" in m or "entra a mi conversacion" in m):
            # Numero: exige 9-11 digitos contiguos (con espacios/guiones permitidos entre
            # ellos) que NO sean parte de una racha mas larga de digitos — antes cualquier
            # secuencia de 9+ digitos en el mensaje (un folio, un monto) podia tomarse
            # como destino.
            m_tel = re.search(r"(?<!\d)(?:\+?52[\s\-]?)?(\d[\d\s\-]{8,10}\d)(?!\d)", mensaje or "")
            tel = re.sub(r"\D", "", m_tel.group(0)) if m_tel else ""
            if len(tel) >= 10:
                import os
                inst = os.getenv("GREEN_API_INSTANCE", ""); gtok = os.getenv("GREEN_API_TOKEN", "")
                if not inst or not gtok:
                    return {"respuesta": "Puedo enviar WhatsApp de verdad, pero faltan las credenciales de Green API en el .env (GREEN_API_INSTANCE / GREEN_API_TOKEN). No lo voy a dar por hecho."}
                chat_id = ("521" + tel[-10:]) + "@c.us"
                # Extrae el TEXTO real que Anuar quiere mandar — antes se ignoraba por
                # completo y siempre se mandaba un saludo generico fijo, aunque la
                # respuesta dijera "ENVIADO de verdad" (bug real encontrado hoy).
                texto_msg = ""
                for marcador in ("diciendo que", "diciendole que", "que diga", "con el mensaje", "el mensaje"):
                    if marcador in m:
                        idx = m.index(marcador) + len(marcador)
                        texto_msg = mensaje[idx:].strip(" :,\"'")
                        break
                if not texto_msg:
                    limpio = re.sub(r"\d[\d\s\-]{8,}", "", mensaje or "")
                    for palabra in ("manda", "mandale", "envia", "enviale", "whatsapp", "wasap", "watsap", "un", "al", " a "):
                        limpio = re.sub(rf"\b{re.escape(palabra.strip())}\b", "", limpio, flags=re.I)
                    texto_msg = limpio.strip(" :,\"'")
                if not texto_msg or len(texto_msg) < 3:
                    return {"respuesta": f"Tengo el número ({tel[-10:]}) pero no el TEXTO exacto — dime qué quieres que diga y lo mando de verdad (no voy a inventar un saludo genérico)."}
                try:
                    import requests
                    url = f"https://{inst}.api.greenapi.com/waInstance{inst}/sendMessage/{gtok}"
                    resp = await asyncio.to_thread(lambda: requests.post(url, json={"chatId": chat_id, "message": texto_msg}, timeout=20))
                    if resp.ok and resp.json().get("idMessage"):
                        return {"respuesta": f"✅ WhatsApp ENVIADO de verdad al {tel[-10:]} con tu texto (id {resp.json()['idMessage']})."}
                    return {"respuesta": f"No pude enviarlo (no te miento): {resp.text[:200]}"}
                except Exception as e:
                    return {"respuesta": f"No pude enviar el WhatsApp (no lo simulo): {str(e)[:200]}"}
            return {"respuesta": "Puedo enviar WhatsApp DE VERDAD por Green API — pero 'entrar a tu conversación' como si fuera la app NO lo hago. Dame el **número (10 dígitos)** y el **texto** que quieres mandar, y lo envío al instante con confirmación real."}

        # Otras apps: aún no conectado — honesto
        if any(k in m for k in ("repara", "reparar", "arregla")) and ("app" in m or "aplicacion" in m):
            return {"respuesta": "Te lo digo derecho: por ahora SOLO tengo conectada la reparación real de WhatsApp (cerrar + limpiar cache). La opción 'Reparar' de Windows para otras apps aún no la ejecuto. Dime qué app y la conecto, o entra a Configuración › Apps › esa app › Opciones avanzadas › Reparar."}

        # Mover / copiar archivos
        if any(k in m for k in ("mueve", "mover", "copia", "copiar", "pasa", "manda", "envia")):
            accion = "copiar" if ("copia" in m or "copiar" in m) else "mover"
            otra_pc = any(k in m for k in ("pc de mi esposa", "pc de mi mujer", "otra pc", "su pc",
                                           "computadora de", "laptop de", "la de mi esposa", "la de ella"))
            fn = re.search(r"([\w\-. ]+\.(?:jpg|jpeg|png|pdf|dxf|svg|ai|cdr|docx?|xlsx?|txt|mp4|zip|rar))", mensaje, re.I)
            nombre = fn.group(1).strip() if fn else None
            if not nombre:
                _STOP = {"mueve", "muevelo", "mover", "copia", "copialo", "copiar", "pasa", "pasalo",
                         "manda", "mandale", "envia", "enviale", "archivo", "imagen", "foto", "documento",
                         "el", "la", "los", "las", "un", "una", "mi", "mis", "de", "del", "que", "se",
                         "llama", "nombre", "pc", "computadora", "laptop", "esposa", "mujer", "ella",
                         "hacia", "para", "por", "favor", "porfa", "otra", "esa", "este", "esta"}
                toks = [t for t in re.findall(r"[\w\-]{3,}", m) if t not in _STOP]
                # Preferir un token con dígito (ej. '4forte'); si no, el último significativo.
                nombre = next((t for t in toks if any(ch.isdigit() for ch in t)), toks[-1] if toks else None)
            hits = await asyncio.to_thread(_acc.buscar_archivo, nombre) if nombre else []
            if otra_pc:
                listado = ("\n- " + "\n- ".join(hits[:5])) if hits else " (no lo encontré en tus carpetas)"
                return {"respuesta": (f"No lo hice todavía, y te digo la verdad de por qué: para pasar un archivo a la PC de "
                        f"tu esposa necesito una **carpeta compartida en red** entre las dos PCs, y no tengo esa ruta.\n\n"
                        f"Archivo(s) que encontré con '{nombre}':{listado}\n\n"
                        f"Hazlo una vez: en la PC de tu esposa, clic derecho a una carpeta › Propiedades › Compartir, y pásame "
                        f"su ruta de red (ej. \\\\PC-ESPOSA\\Compartida). Con eso lo {accion} de verdad y te confirmo con prueba.")}
            if not nombre:
                return {"respuesta": "Para moverlo/copiarlo de verdad necesito el nombre del archivo. ¿Cuál es?"}
            if not hits:
                return {"respuesta": f"No encontré ningún archivo con '{nombre}' en Descargas/Escritorio/Documentos/Imágenes. Dame la ruta exacta y lo hago."}
            dest = re.search(r"(?:a|hacia|en)\s+([A-Za-z]:\\[^\n]+|\\\\[^\n]+)", mensaje)
            if not dest:
                return {"respuesta": f"Encontré: {hits[0]}\n¿A qué carpeta lo {accion}? Dame la ruta destino (ej. C:\\Users\\...\\Documents o \\\\PC-ESPOSA\\Compartida) y lo ejecuto de verdad."}
            fn2 = _acc.copiar if accion == "copiar" else _acc.mover
            r = await asyncio.to_thread(fn2, hits[0], dest.group(1).strip())
            if r["status"] == "ok":
                return {"respuesta": f"✅ Hecho de verdad y verificado: {r['accion']} '{Path(r['origen']).name}' → {r['destino']} ({r.get('bytes',0)} bytes)."}
            return {"respuesta": f"No pude completarlo (no te miento): {r.get('detalle', r['status'])}"}

        # No sé ejecutarlo — honesto
        return {"respuesta": "Entendí que me pides una acción sobre el sistema, pero aún no la tengo conectada para ejecutarla de verdad, así que NO la voy a dar por hecha. Dime exactamente qué archivo/carpeta y qué acción, o la conecto como capacidad nueva."}

    async def _ejecutar_corel_real(self, mensaje: str) -> Dict:
        """CHAT ↔ COREL: comandos directos y fijos sobre motor_corel (COM real).
        No adivina parámetros — si falta algo (ruta, tamaño) lo pide en vez de inventar."""
        import re, importlib.util as _ilu
        from pathlib import Path as _P
        raiz = _P(__file__).resolve().parent.parent
        try:
            spec = _ilu.spec_from_file_location("corel_core", raiz / "EDITOR" / "corel_core.py")
            cc = _ilu.module_from_spec(spec); spec.loader.exec_module(cc)
        except Exception as e:
            return {"respuesta": f"No pude cargar el motor de Corel: {e}"}

        m = _norm_txt(mensaje)

        # ¿Qué plugins/macros tiene Corel? Se lee del DISCO, no de Corel, así que
        # funciona con Corel cerrado. Va primero porque es una consulta, no una
        # acción sobre un documento.
        # Va ANTES que cualquier comando de documento: preguntar qué plugins hay
        # no necesita Corel abierto, se lee del disco. El 2026-08-03 "que macros
        # tiene corel" se fue al comando de documento y respondió "no hay
        # documento abierto", que no tiene nada que ver con lo que se preguntó.
        if _contiene_trigger(m, ("plugin", "plugins", "macro", "macros", "complemento",
                                 "complementos", "add-on", "addon", "extension",
                                 "que tiene instalado", "tiene instalado", "esta instalado",
                                 "que trae instalado")):
            # Si nombra uno en concreto, se responde por ese; si no, se listan todos.
            buscado = ""
            for palabra in ("laser", "lightburn", "rdworks", "print", "corte", "grabado",
                            "sublima", "calendar", "color", "converter", "curves"):
                if palabra in m:
                    buscado = palabra
                    break
            if buscado:
                r = await asyncio.to_thread(cc.tiene_plugin, buscado)
                if r.get("status") != "OK":
                    return {"respuesta": f"No pude revisar los plugins: {r.get('mensaje', r)}"}
                if r.get("instalado"):
                    nombres = ", ".join(p["nombre"] for p in r["coincidencias"])
                    return {"respuesta": f"Sí, lo tienes: {nombres}.\n"
                                         f"(Revisé los {r['total_revisados']} instalados en disco.)"}
                return {"respuesta": (
                    f"No, no tienes ningún plugin de '{buscado}' instalado. "
                    f"Revisé los {r['total_revisados']} que hay en disco y ninguno coincide.\n"
                    "Si lo acabas de instalar y no aparece, míralo en Corel: "
                    "Herramientas → Macros → Administrador de macros.")}

            r = await asyncio.to_thread(cc.listar_plugins)
            if r.get("status") != "OK":
                return {"respuesta": f"No pude revisar los plugins: {r}"}
            if not r["total"]:
                return {"respuesta": "No encontré ninguna macro ni plugin de Corel en el disco."}
            lineas = "\n".join(
                f"• {p['nombre']} ({p['kb']} KB)" + ("" if p["de_fabrica"] else "  ← instalado por ti")
                for p in r["plugins"][:15])
            extra = (f"\n{r['instalados_por_ti']} instalados por ti, "
                     f"{r['de_fabrica']} de fábrica.") if r["instalados_por_ti"] else \
                    "\nTodos son los que trae Corel de fábrica — ninguno tuyo."
            return {"respuesta": f"Corel tiene {r['total']} macros/plugins:\n{lineas}{extra}"}

        # "Mapa de bits" en Corel son TRES cosas distintas y ninguna se puede
        # adivinar sin equivocarse: rasterizar un vector, trazar una imagen para
        # convertirla en vector, o sacar la imagen incrustada del documento.
        # Caso real 2026-08-03: se pidió "extrae el mapa de bits" y la respuesta
        # fue un "no puedo ejecutar acciones físicas" inventado. Se pregunta cuál
        # de las tres, con lo que de verdad se puede hacer en cada una.
        if _contiene_trigger(m, ("mapa de bits", "mapa de bit", "mapadebits",
                                 "bitmap", "rasteriza", "rasterizar")):
            _rb = _rutas_del_texto(mensaje or "")
            arch = f" (para `{_P(_rb[0]).name}`)" if _rb else ""
            return {"respuesta": (
                f"«Mapa de bits» en Corel puede ser tres cosas distintas{arch}, y no quiero "
                "adivinar cuál. Dime cuál y lo hago:\n\n"
                "• **Trazarlo para corte** (lo más común aquí) — lo convierte de imagen a "
                "vector y te deja SVG + DXF listos para la láser.\n"
                f"   → `vectoriza{' ' + ruta_bmp.group(1) if ruta_bmp else ' <ruta>'}`\n\n"
                "• **Quitarle el fondo y meterlo a Corel** — lo limpia y lo importa.\n"
                f"   → `corel quita el fondo{' ' + ruta_bmp.group(1) if ruta_bmp else ' <ruta>'}`\n\n"
                "• **Sacar el documento como imagen** — aquí sí te debo la verdad: la "
                "exportación a PNG/JPG **no me funciona** por una limitación real de Corel "
                "con pywin32 (a PDF sí sale al 100%).\n"
                "   → `corel exporta a pdf` y de ahí lo paso a la imagen que necesites.")}

        # Encontrado en vivo 2026-07-27: nombres de archivo con ESPACIOS (ej. los que
        # genera WhatsApp por default: "WhatsApp Image 2026-07-27 at 12.03.35 PM.jpeg")
        # no calzaban con el regex viejo (excluía \s por completo) — el candado directo
        # de Corel se saltaba entero y el mensaje caía al chat genérico, que alucinó
        # ("necesitas Photoshop", "no tengo acceso a la imagen") sobre una ruta real que
        # sí se había dado. Ahora se reconoce primero la ruta ENTRE COMILLAS (permite
        # espacios) y si no hay comillas, cae a la versión sin espacios de antes.
        # No-greedy hasta la extensión: cubre rutas con espacios estén o no entre
        # comillas (el caso real más común es SIN comillas, como pega la gente al
        # copiar un nombre de archivo de Windows/WhatsApp).
        # Extensiones alineadas con lo que el motor realmente soporta (abrir_documento
        # acepta ai/eps/cdr/pdf; agregar_imagen_documento_activo acepta también
        # bmp/gif/tif/tiff) — antes la regex solo reconocia png/jpg/jpeg/pdf/cdr y
        # cualquier mensaje con un .ai o .bmp real se caia al enrutador de IA.
        rutas = re.findall(
            r"[A-Za-z]:\\[^\r\n]+?\.(?:png|jpg|jpeg|bmp|gif|tif|tiff|pdf|cdr|ai)",
            mensaje, re.I)
        rutas = [r.strip(' "\'') for r in rutas]
        # Carpeta única real para PDFs de Corel generados por AURORA — a pedido explícito
        # de Anuar (2026-07-27): "guárdalo/almacénalo como PDF" ya sabe dónde SIEMPRE, sin
        # rutas alternas para este tipo de archivo. Solo aplica a PDF (PNG/JPG conservan
        # la carpeta que Anuar mencione, como antes).
        _CARPETA_PDF_COREL = _P.home() / "Desktop" / "PDFs a Impresion"
        es_pdf = "pdf" in m or not any(e in m for e in ("png", "jpg", "jpeg"))
        if not rutas and ("exporta" in m or "exportar" in m or "almacena" in m or "guarda" in m):
            _titulo = re.search(r"(?:titulo|título)\s+(\w+)", mensaje, re.I)
            if es_pdf:
                _CARPETA_PDF_COREL.mkdir(parents=True, exist_ok=True)
                if _titulo:
                    nombre = _titulo.group(1)
                else:
                    # Sin título dado: usa el nombre REAL del documento abierto en Corel
                    # (nunca inventa un nombre) — solo si el motor confirma que existe.
                    info = await _corel_con_timeout(cc.info_documento)
                    nombre = _P(info["nombre"]).stem if info.get("status") == "ok" else None
                if nombre:
                    rutas = [str(_CARPETA_PDF_COREL / f"{nombre}.pdf")]
            else:
                _carpetas = {"descargas": "Downloads", "descarga": "Downloads",
                            "escritorio": "Desktop", "documentos": "Documents"}
                _carpeta_real = next((v for k, v in _carpetas.items() if k in m), None)
                if _carpeta_real and _titulo:
                    _ext = next(e for e in ("png", "jpg", "jpeg") if e in m)
                    rutas = [str(_P.home() / _carpeta_real / f"{_titulo.group(1)}.{_ext}")]

        if "abre" in m or "abrir" in m or "abrelo" in m:
            if not rutas:
                return {"respuesta": "Dame la ruta completa del archivo (PDF/CDR/AI/PNG/JPG) y lo abro de verdad dentro de Corel."}
            # Encontrado en vivo 2026-07-27: para una imagen RASTER (PNG/JPG), abrir_documento
            # (OpenDocument) solo mostraba una página en blanco — Corel necesita IMPORTAR el
            # raster a un documento, no "abrirlo" como si fuera un documento nativo. Diferencia
            # real por tipo de archivo en vez de usar siempre la misma función.
            if _P(rutas[0]).suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"):
                r = await _corel_con_timeout(cc.agregar_imagen_documento_activo, rutas[0], False)
                if r.get("status") == "ok":
                    return {"respuesta": f"✅ Imagen real importada a Corel: '{r['forma']}'."}
                return {"respuesta": f"No pude importarla en Corel (no te miento): {r.get('detalle', r.get('status'))}"}
            r = await _corel_con_timeout(cc.abrir_documento, rutas[0])
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Abierto real en Corel: '{r['nombre']}' ({r['paginas']} página(s))."}
            return {"respuesta": f"No pude abrirlo en Corel (no te miento): {r.get('detalle', r.get('status'))}"}

        if "cierra" in m or "cerrar documento" in m or "cierra el documento" in m:
            info = await _corel_con_timeout(cc.info_documento)
            if info.get("status") != "ok":
                return {"respuesta": f"No hay documento abierto en Corel para cerrar: {info.get('detalle', info.get('status'))}"}
            r = await _corel_con_timeout(cc.cerrar_documento_sin_guardar, info["nombre"])
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Documento real cerrado sin guardar: '{r['cerrado']}'."}
            return {"respuesta": f"No pude cerrarlo (no te miento): {r.get('detalle', r.get('status'))}"}

        if ("extrae el texto" in m or "extraer el texto" in m or "el texto del documento" in m
                or "que texto tiene" in m):
            r = await _corel_con_timeout(cc.extraer_texto_documento)
            if r.get("status") == "ok":
                resumen_formas = ", ".join(f"{v} {k}" for k, v in r["formas_no_texto"].items()) or "ninguna otra forma"
                if not r["textos"]:
                    return {"respuesta": f"El documento no tiene texto real. Otras formas (adornos) encontradas: {resumen_formas}."}
                texto_junto = "\n".join(f"- {t}" for t in r["textos"])
                return {"respuesta": f"✅ Texto real encontrado ({r['total_bloques_texto']} bloque(s)):\n{texto_junto}\nAdornos/otras formas: {resumen_formas}."}
            return {"respuesta": f"No pude leer el texto (no te miento): {r.get('detalle', r.get('status'))}"}

        if "planilla" in m:
            if not rutas:
                return {"respuesta": "Dame la ruta completa de la pieza (imagen del sticker ya terminado) y armo la planilla real."}
            medidas = re.findall(r"(\d+(?:\.\d+)?)\s*(?:cm|x)", m)
            if len(medidas) < 4:
                return {"respuesta": "Dame las 4 medidas: ancho y alto de la hoja, y ancho y alto de la pieza (ej. 'hoja 60x100 pieza 4.5x5') — no invento tamaños."}
            ah, al, pw, ph = (float(v) for v in medidas[:4])
            salida = rutas[1] if len(rutas) > 1 else str(_P(rutas[0]).with_name("planilla.pdf"))
            r = await _corel_con_timeout(cc.crear_planilla, rutas[0], ah, al, pw, ph, salida)
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Planilla real: {r['piezas']} piezas ({r['columnas']}x{r['filas']}) en {r['ruta']} ({r['kb']}KB)."}
            return {"respuesta": f"No pude armar la planilla (no te miento): {r.get('detalle', r.get('status'))}"}

        if "quita el fondo" in m or "quitale el fondo" in m or "splash" in m:
            if not rutas:
                return {"respuesta": "Dame la ruta completa de la imagen (el splash) y le quito el fondo y lo integro de verdad."}
            r = await _corel_con_timeout(cc.quitar_fondo_y_agregar, rutas[0], True)
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Fondo quitado real y agregado detrás en Corel: {r.get('imagen_sin_fondo')}."}
            return {"respuesta": f"No pude hacerlo (no te miento): {r.get('detalle', r.get('status'))}"}

        if "gotero" in m or "saca el color" in m or "extrae el color" in m or "muestra el color" in m:
            if not rutas:
                return {"respuesta": "Dame la ruta completa de la foto de referencia (ej. la del envase) y lo saco de verdad."}
            mxy = re.findall(r"(\d+)\s*[,x]\s*(\d+)", mensaje)
            if not mxy:
                return {"respuesta": "Dame la coordenada del pixel a muestrear (ej. 'en 100,60') — no invento dónde tomar el color."}
            x, y = int(mxy[0][0]), int(mxy[0][1])
            r = await _corel_con_timeout(cc.extraer_y_aplicar_color, rutas[0], x, y)
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Color real tomado de ({x},{y}): RGB({r['r']},{r['g']},{r['b']}) y aplicado a la forma seleccionada en Corel."}
            return {"respuesta": f"No pude tomar/aplicar el color (no te miento): {r.get('detalle', r.get('status'))}"}

        if "combina" in m or "integra" in m:
            if len(rutas) < 2:
                return {"respuesta": "Para combinar el logo con el fondo necesito las 2 rutas completas (fondo y logo). Dámelas y lo hago de verdad."}
            fondo, logo = rutas[0], rutas[1]
            salida = rutas[2] if len(rutas) > 2 else str(_P(logo).with_name("integrado.pdf"))
            r = await _corel_con_timeout(cc.integrar_logo_fondo, fondo, logo, salida)
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Combinado real: {r['ruta']} ({r['kb']}KB)."}
            return {"respuesta": f"No pude combinarlo (no te miento): {r.get('detalle', r.get('status'))}"}

        if "guarda una copia" in m:
            if not rutas:
                return {"respuesta": "Dame la ruta completa donde guardo la copia."}
            r = await _corel_con_timeout(cc.guardar_copia, rutas[0])
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Copia real guardada: {r['ruta']} ({r['kb']}KB)."}
            return {"respuesta": f"No pude guardar la copia: {r.get('detalle', r.get('status'))}"}

        if "escala" in m or "tamano de pagina" in m:
            mnum = re.findall(r"(\d+(?:\.\d+)?)\s*(?:cm|x)", m)
            if len(mnum) < 2:
                return {"respuesta": "Dame el ancho y alto en centímetros (ej. 'escala a 20x30 cm') y lo hago de verdad."}
            r = await _corel_con_timeout(cc.escalar_pagina, float(mnum[0]), float(mnum[1]), False)
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Página real a {r['ancho_cm']}x{r['alto_cm']}cm."}
            return {"respuesta": f"No pude escalar: {r.get('detalle', r.get('status'))}"}

        if "exporta" in m or "exportar" in m or "almacena" in m or "guarda" in m:
            salida = rutas[0] if rutas else None
            if not salida:
                return {"respuesta": "Dame la ruta completa de salida (con .pdf, .png o .jpg) y lo exporto de verdad."}
            if salida.lower().endswith(".pdf"):
                r = await _corel_con_timeout(cc.exportar_pdf, salida)
            else:
                r = await _corel_con_timeout(cc.exportar_bitmap, salida, 300, _P(salida).suffix.lstrip("."))
            if r.get("status") == "ok":
                return {"respuesta": f"✅ Exportado real: {r['ruta']} ({r['kb']}KB)."}
            return {"respuesta": f"No pude exportarlo (no te miento): {r.get('detalle', r.get('status'))}"}

        # "info del documento" u otro caso — siempre real, nunca inventado
        r = await _corel_con_timeout(cc.info_documento)
        if r.get("status") == "ok":
            return {"respuesta": f"Documento real abierto en Corel: '{r['nombre']}', {r['paginas']} página(s), {r['ancho']}x{r['alto']}."}
        return {"respuesta": f"No pude leer Corel: {r.get('detalle', r.get('status'))}"}

    async def _convertir_dxf_real(self, mensaje: str) -> Dict:
        """CHAT ↔ TALLER: convierte de verdad un archivo a DXF con taller_core
        (motor que existía pero nadie llamaba). Si no encuentra el archivo, lo dice."""
        import re, importlib.util as _ilu
        from pathlib import Path as _P
        raiz = _P(__file__).resolve().parent.parent
        # 1) ruta explícita en el mensaje
        # Encontrado en vivo 2026-07-29 con un archivo real de Anuar:
        # "Animal - Perro - Pitbull (Cabeza).pdf". El regex viejo excluia
        # espacios ([^\s"']+), asi que con CUALQUIER nombre con espacios o
        # parentesis —que es lo normal en sus diseños— no encontraba la ruta,
        # pedia el archivo de nuevo, y al insistir el mensaje caia al enrutador
        # de IA que respondio "No puedo ejecutar conversiones en la PC" (falso).
        # Es el MISMO bug que ya se habia corregido en el candado de Corel, que
        # aqui habia quedado sin corregir. No-greedy hasta la extension: sirve
        # con o sin comillas, con espacios y con parentesis.
        mruta = re.search(r"[A-Za-z]:\\[^\r\n]+?\.(?:svg|pdf|ai|eps|cdr|dxf|png|jpg|jpeg)", mensaje, re.I)
        ruta = mruta.group(0).strip(' "\'') if mruta else None
        # 2) si no, buscar por nombre de archivo
        if not ruta:
            # El nombre puede traer espacios ("Porta carritos.pdf"). Tomamos el bloque
            # que termina en la extensión y vamos recortando palabras del inicio
            # hasta que el archivo exista de verdad.
            mnom = re.search(r"([\w\-.áéíóúñÁÉÍÓÚÑ ]+\.(?:svg|pdf|ai|eps|cdr|png|jpg|jpeg))", mensaje, re.I)
            if mnom:
                candidato = mnom.group(1).strip()
                try:
                    from CEREBRO import acciones_sistema as _acc
                    palabras = candidato.split()
                    for i in range(len(palabras)):
                        prueba = " ".join(palabras[i:])
                        hits = await asyncio.to_thread(_acc.buscar_archivo, prueba)
                        exactos = [h for h in hits if _P(h).name.lower() == prueba.lower()]
                        if exactos:
                            ruta = exactos[0]; break
                        if hits and i > 0:
                            ruta = hits[0]; break
                except Exception:
                    pass
        destino = _formato_destino(mensaje) or "dxf"

        if not ruta:
            return {"respuesta": f"Dime qué archivo convierto a {destino.upper()} "
                                 "(nombre o ruta completa). Sé pasar entre SVG, PDF, AI, "
                                 "EPS, PNG y DXF, y también vectorizar imágenes."}

        # A DXF sigue yendo por taller_core, que además vectoriza imágenes y ya
        # está probado. Cualquier otro destino usa EDITOR/conversor_formatos, que
        # existía completo pero no tenía forma de pedírsele desde el chat: pedir
        # "convierte a pdf" no calzaba con ningún candado (Anuar, 2026-07-31).
        if destino != "dxf":
            try:
                spec = _ilu.spec_from_file_location(
                    "conversor_formatos", raiz / "EDITOR" / "conversor_formatos.py")
                cf = _ilu.module_from_spec(spec); spec.loader.exec_module(cf)
            except Exception as e:
                return {"respuesta": f"No pude cargar el conversor de formatos: {str(e)[:120]}"}
            dpi = _dpi_pedido(mensaje)
            pagina = _pagina_pedida(mensaje)
            try:
                if pagina == -1:
                    # PDF completo, una imagen por página. La función existía y
                    # tampoco tenía forma de pedírsele desde el chat.
                    r = await asyncio.to_thread(cf.convertir_todo, ruta, destino, dpi)
                else:
                    r = await asyncio.to_thread(cf.convertir, ruta, destino, "", dpi, pagina)
            except Exception as e:
                return {"respuesta": f"Falló la conversión (no te lo adorno): {str(e)[:150]}"}

            if isinstance(r, dict) and str(r.get("status", "")).lower() in ("ok", "exito", "éxito"):
                nota = f" a {dpi} DPI" if destino in ("png", "jpg", "jpeg") else ""
                if pagina == -1:
                    cuantas = r.get("total") or len(r.get("archivos") or []) or "varias"
                    donde = r.get("carpeta") or r.get("salida") or ""
                    return {"respuesta": f"✅ Convertidas de verdad {cuantas} páginas a "
                                         f"{destino.upper()}{nota}:\n{donde}"}
                salida = r.get("salida") or r.get("ruta") or r.get("archivo") or ""
                cual = f" (página {pagina + 1})" if isinstance(pagina, int) and pagina >= 0 else ""
                return {"respuesta": f"✅ Convertido de verdad a {destino.upper()}{nota}{cual}:\n{salida}"}
            detalle = r.get("mensaje") or r.get("detalle") or r if isinstance(r, dict) else r
            return {"respuesta": f"No se logró convertir a {destino.upper()}: {detalle}"}

        try:
            spec = _ilu.spec_from_file_location("taller_core", raiz / "TALLER" / "taller_core.py")
            tc = _ilu.module_from_spec(spec); spec.loader.exec_module(tc)
        except Exception as e:
            return {"respuesta": f"No pude cargar el convertidor: {str(e)[:120]}"}
        es_img = _P(ruta).suffix.lower() in (".png", ".jpg", ".jpeg")
        fn = tc.vectorizar if es_img else tc.convertir_a_dxf
        try:
            r = await asyncio.to_thread(fn, ruta)
        except Exception as e:
            return {"respuesta": f"Falló la conversión (no te lo adorno): {str(e)[:150]}"}
        if isinstance(r, dict) and r.get("status") == "OK":
            return {"respuesta": f"✅ Convertido de verdad a DXF:\n{r.get('salida')}\n"
                                 f"({r.get('kb','?')} KB). Listo para RDWorks/Aspire."}
        return {"respuesta": f"No se logró convertir: {r.get('detalle', r) if isinstance(r, dict) else r}"}

    async def _consultar_negocio_real(self, mensaje: str) -> Dict:
        """CHAT ↔ MOTORES DE NEGOCIO. Lee datos REALES (órdenes, inventario, CRM,
        contabilidad) y responde con cifras verdaderas. NUNCA inventa: si un motor
        falla, lo dice."""
        import importlib.util as _ilu
        from pathlib import Path as _P
        raiz = _P(__file__).resolve().parent.parent
        m = _norm_txt(mensaje)

        def _cargar(nombre, ruta):
            spec = _ilu.spec_from_file_location(nombre, raiz / ruta)
            mod = _ilu.module_from_spec(spec); spec.loader.exec_module(mod)
            return mod

        partes, errores = [], []

        # ── ÓRDENES DE TALLER ──
        # "entrega" (no solo "entregar") para que "pendiente de entrega" —que sí dispara
        # el candado externo— también encuentre esta sección en vez de caer al fallback.
        if any(k in m for k in ("orden", "entrego", "entregar", "entrega", "taller")):
            try:
                ot = await asyncio.to_thread(_cargar, "ordenes_taller", "TALLER/ordenes_taller.py")
                data = await asyncio.to_thread(ot.listar_ordenes)
                act = [o for o in data.get("ordenes", []) if o.get("estado") not in ("entregado", "cancelado")]
                if act:
                    lineas = [f"• {o['folio']} — {o['cliente']}: {o['trabajo']} "
                              f"(${o['valor_total']}, saldo ${o['saldo']}) · entrega: {o.get('fecha_entrega') or 's/f'} · {o['estado']}"
                              for o in act[:10]]
                    partes.append(f"📋 ÓRDENES PENDIENTES ({len(act)}):\n" + "\n".join(lineas))
                else:
                    partes.append("📋 No tienes órdenes pendientes de entrega.")
            except Exception as e:
                errores.append(f"órdenes: {str(e)[:80]}")

        # ── INVENTARIO ──
        if any(k in m for k in ("inventario", "existencia", "queda", "tengo de", "bajo minimo", "material")):
            try:
                inv = await asyncio.to_thread(_cargar, "inventario", "TALLER/inventario.py")
                res = await asyncio.to_thread(inv.resumen)
                bajo = await asyncio.to_thread(inv.bajo_minimo)
                txt = (f"📦 INVENTARIO: {res.get('n_items',0)} artículos · "
                       f"valor ${res.get('valor_total',0)} · {res.get('bajo_minimo',0)} bajo mínimo")
                items_bajo = bajo.get("items", []) if isinstance(bajo, dict) else []
                if items_bajo:
                    txt += "\n  ⚠️ Reponer: " + ", ".join(
                        f"{i['nombre']}{' '+i['talla'] if i.get('talla') else ''} ({i['cantidad']} {i.get('unidad','')})"
                        for i in items_bajo[:8])
                partes.append(txt)
            except Exception as e:
                errores.append(f"inventario: {str(e)[:80]}")

        # ── CRM / LEADS ──
        # "cliente nuevo" (singular) no calzaba contra "clientes nuevos" del trigger
        # externo — la concordancia de plural se perdía. "cliente nuevo" como substring
        # cubre ambos casos.
        if any(k in m for k in ("lead", "prospecto", "embudo", "pronostico", "fuente", "cliente nuevo", "clientes nuevo")):
            try:
                import sys as _s
                _s.path.insert(0, str(raiz / "ORACLE"))
                import oracle_core as _oc
                _oc.init_db()
                pron = await asyncio.to_thread(_oc.pronostico_embudo)
                abiertos = {e: d for e, d in pron["por_etapa"].items() if d["leads"]}
                txt = (f"🎯 CRM: ${pron['valor_en_embudo']} en embudo · ${pron['valor_ganado']} ganado\n  "
                       + " · ".join(f"{e}: {d['leads']}" for e, d in abiertos.items()))
                if "fuente" in m:
                    fu = await asyncio.to_thread(_oc.fuentes_efectivas)
                    top = fu.get("fuentes", [])[:5]
                    if top:
                        txt += "\n  📊 Fuentes: " + " · ".join(
                            f"{f['fuente']}: {f['ganados']}/{f['leads']} ({f['conversion_pct']}%)" for f in top)
                partes.append(txt)
            except Exception as e:
                errores.append(f"CRM: {str(e)[:80]}")

        # ── CONTABILIDAD ──
        if any(k in m for k in ("contabilidad", "vendi", "utilidad", "ganancia", "cobrar", "llevo")):
            try:
                ot = await asyncio.to_thread(_cargar, "ordenes_taller", "TALLER/ordenes_taller.py")
                cont = await asyncio.to_thread(ot.contabilidad_mensual)
                meses = cont.get("meses", [])
                if meses:
                    x = meses[0]
                    partes.append(
                        f"💰 CONTABILIDAD {x['mes']}: ingresos ${x['ingresos']} · costos ${x['costos']} · "
                        f"utilidad ${x['utilidad']} ({x['margen_pct']}%) · cobrado ${x['cobrado']} · por cobrar ${x['por_cobrar']}")
                else:
                    partes.append("💰 Aún no hay movimientos en contabilidad.")
            except Exception as e:
                errores.append(f"contabilidad: {str(e)[:80]}")

        if not partes and not errores:
            return {"respuesta": "Entendí que preguntas por tu negocio, pero no ubiqué el dato exacto. "
                                 "Pregúntame por: órdenes, inventario, leads/embudo o contabilidad."}
        salida = "\n\n".join(partes)
        if errores:
            salida += "\n\n⚠️ No pude leer: " + "; ".join(errores) + " (te lo digo en vez de inventarlo)."
        return {"respuesta": salida}

    async def _crear_capacidad_real(self, mensaje: str, canal: str = "api") -> Dict:
        """CHAT ↔ FÁBRICA: crea un motor/capacidad nuevo DE VERDAD (aislado y validado).
        No simula: si falla, lo dice. El candado de canal="whatsapp" ya se aplica de
        forma centralizada en el pipeline (_CANDADOS_SOLO_DUENIO) antes de llegar aquí."""
        try:
            from CEREBRO import fabrica_motores as _fab
        except Exception as e:
            return {"respuesta": f"No pude cargar la Fábrica: {str(e)[:120]}"}
        m = _norm_txt(mensaje)
        nombre = None
        for t in _CREAR_CAPACIDAD_TRIGGERS:
            if t in m:
                resto = mensaje[m.index(t) + len(t):].strip(" .:,")
                nombre = " ".join(resto.split()[:5]) if resto else None
                break
        nombre = (nombre or "capacidad nueva").strip()
        try:
            r = await asyncio.to_thread(_fab.crear_motor, nombre, mensaje)
        except Exception as e:
            return {"respuesta": f"No la creé (no te miento): error en la Fábrica: {str(e)[:150]}"}
        if isinstance(r, dict) and r.get("status") == "ok":
            slug = r.get("slug") or r.get("motor") or ""
            return {"respuesta": (f"✅ Capacidad creada de verdad: «{nombre}»"
                    + (f" (motor `{slug}`)" if slug else "")
                    + ". Está aislada y ya quedó validado que compila. "
                    + "Pruébala en el panel Fábrica de Motores. " + str(r.get("mensaje", ""))).strip()}
        detalle = (r.get("mensaje") or r.get("detalle") or r.get("status")) if isinstance(r, dict) else str(r)
        return {"respuesta": f"No la creé (te lo digo derecho): {detalle}. "
                f"Dame la idea más concreta —qué debe recibir y qué debe devolver— y lo reintento."}

    async def _editar_codigo_real(self, mensaje: str, session_id: str = "", saltar_confirmacion: bool = False,
                                   canal: str = "api") -> Dict:
        """CHAT ↔ IDE (EDITAR): modifica cualquier archivo con red anti-ruptura.
        Garantías mecánicas: respaldo (reversible), compila o no se aplica, y guardián
        anti-pérdida (si el cambio dejaría menos código/funciones → revierte). Sin simular.
        Si el archivo es del NÚCLEO, pide confirmación real ANTES de generar/escribir nada
        (antes solo avisaba DESPUÉS de haber escrito — no protegía nada de verdad).
        El candado de canal="whatsapp" ya se aplica de forma centralizada en el pipeline
        (_CANDADOS_SOLO_DUENIO) antes de llegar aquí, y también en la confirmación de
        acciones pendientes (paso 2.44) — por eso una edición de núcleo pendiente nunca
        puede crearse ni confirmarse desde WhatsApp."""
        import re, shutil, subprocess, sys
        from datetime import datetime as _dt
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        fn = re.search(r"([\w\-]+\.\w{1,5})", mensaje)
        if not fn:
            return {"respuesta": "Dime el nombre del archivo a editar (ej. 'edita el archivo ordenes_taller.py y agrega…')."}
        nombre = fn.group(1)
        encontrados = [p for p in root.rglob(nombre)
                       if "__pycache__" not in str(p) and ".ide_backups" not in str(p)
                       and "_OBSOLETOS" not in str(p) and "_ARCHIVE" not in str(p)]
        if not encontrados:
            return {"respuesta": f"No encontré ningún archivo llamado '{nombre}'."}
        objetivo = encontrados[0]
        rel = objetivo.relative_to(root)
        # NÚCLEO: pide confirmación real ANTES de tocar nada (no un aviso después del hecho).
        if objetivo.name in _NUCLEO_PROTEGIDO and not saltar_confirmacion:
            if session_id:
                self._accion_pendiente[session_id] = {"tipo": "editar_nucleo", "mensaje": mensaje}
            return {"respuesta": f"⚠️ '{rel}' es un archivo del NÚCLEO (sostiene la lógica central de AURORA). "
                    f"Antes de generar y escribir el cambio necesito tu confirmación explícita — responde 'sí' "
                    f"para continuar (igual voy a aplicar el guardián anti-pérdida, el chequeo de compilación, "
                    f"y respaldo con reversión automática si algo sale mal)."}
        if not self._groq:
            return {"respuesta": "Para redactar el cambio necesito el LLM (Groq) y no está disponible ahora. No inventé nada."}
        try:
            original = objetivo.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"respuesta": f"No pude leer {rel}: {str(e)[:120]}"}

        # El archivo tiene que caber COMPLETO en el modelo: entra completo y sale
        # completo. Antes se mandaba al modelo chico y devolvía 413 después de
        # gastar la llamada (real 2026-08-02 con buscador_web_profesional.py, de
        # 21 KB). Ahora se usa el modelo grande y se avisa ANTES si no cabe.
        # ~4 caracteres por token, y el archivo viaja dos veces (entrada y salida).
        # Medido el 2026-08-02 contra Groq real: buscador_web_profesional.py
        # (21,621 caracteres ≈ 5,400 tokens) devolvía 413 incluso con el modelo
        # grande — el tope del plan es por tokens-por-minuto, no por contexto.
        # 14,000 caracteres es lo que de verdad pasa, con margen.
        _tokens_aprox = len(original) // 4
        if len(original) > 14000:
            return {"respuesta": (
                f"'{rel}' es demasiado grande para editarlo así ({len(original):,} caracteres). "
                "Tendría que reproducirlo completo y no cabe en el modelo — si lo intentara, "
                "te devolvería el archivo cortado a la mitad. No lo toco.\n\n"
                "Dime qué función o qué líneas quieres cambiar y lo hago sobre ese pedazo.")}
        # El LLM redacta el archivo COMPLETO ya con el cambio, sin comentarios extra.
        # max_tokens subido de 4000 a 7800 (medido: consciencia.py necesitaria ~30,000
        # tokens para reproducirse completo, asi que ni esto alcanza para los archivos
        # mas grandes del nucleo — por eso el chequeo de finish_reason de abajo es la
        # proteccion real, no el numero en si).
        try:
            r = await self._groq.chat.completions.create(
                # Modelo GRANDE a propósito: editar código exige reproducir el
                # archivo entero, y el chico (llama-3.1-8b-instant) devolvía 413
                # con archivos de 20 KB. Aquí la precisión importa más que la
                # velocidad — es el único lugar donde se escribe código real.
                model=_MODELO_SELECTOR,
                messages=[{"role": "system", "content": "Eres un editor de código preciso. Te doy un archivo COMPLETO y una instrucción. Devuelve el archivo COMPLETO ya modificado, SIN quitar nada que no se te pidió, SIN comentarios ni explicaciones, SIN ```. Conserva todo el código existente."},
                          {"role": "user", "content": f"Archivo {rel}:\n{original}\n\nInstrucción: {mensaje}\n\nDevuelve el archivo completo modificado:"}],
                max_tokens=7800, temperature=0.1)
            nuevo = r.choices[0].message.content
            corte_por_limite = r.choices[0].finish_reason not in ("stop", "eos", "end_turn")
        except Exception as e:
            return {"respuesta": f"No pude generar el cambio: {str(e)[:150]}. No toqué el archivo."}
        # Detección REAL de truncamiento — probado con un archivo real del proyecto:
        # un corte a mitad de la última función deja código sintácticamente válido
        # pero incompleto, y pasa los 3 guardianes de abajo (longitud/defs/compila)
        # sin que ninguno lo note. finish_reason no miente: si no es "stop", Groq
        # cortó por límite de tokens, sin importar qué tan "completo" se vea el texto.
        if corte_por_limite:
            return {"respuesta": f"🛑 No lo apliqué: {rel} es demasiado grande para reescribirlo completo de una "
                    f"sola vez (se cortó por límite de tokens antes de terminar). Tu archivo quedó **intacto**. "
                    f"Pídeme un cambio más chico y puntual, o hazlo en el IDE con respaldo."}
        # limpiar fences si el modelo los puso
        nuevo = re.sub(r"^```[\w]*\n?", "", nuevo.strip()); nuevo = re.sub(r"\n?```$", "", nuevo).strip() + "\n"
        # GUARDIÁN ANTI-PÉRDIDA: no permitir que se pierda código/funciones.
        if len(nuevo) < 0.85 * len(original) or _contar_defs(nuevo) < _contar_defs(original):
            return {"respuesta": f"🛑 No lo apliqué: el cambio propuesto **dejaría menos código/funciones** en {rel} "
                    f"(de {_contar_defs(original)} a {_contar_defs(nuevo)} definiciones). Para no restarte nada, lo rechacé. "
                    f"Tu archivo quedó **intacto**. Pídemelo más específico o hazlo en el IDE con respaldo."}
        # CHEQUEO DE COMPILACIÓN (para .py) — si no compila, no se aplica.
        if objetivo.suffix == ".py":
            try:
                compile(nuevo, str(objetivo), "exec")
            except SyntaxError as e:
                return {"respuesta": f"🛑 No lo apliqué: el cambio tendría error de sintaxis en línea {e.lineno} ({e.msg}). "
                        f"Tu archivo quedó **intacto**. No te rompo nada."}
        # RESPALDO + escritura + verificación con py_compile en subproceso (reversible).
        BK = root / ".ide_backups"; BK.mkdir(exist_ok=True)
        respaldo = BK / f"{objetivo.name}.chat.{_dt.now().strftime('%Y%m%d-%H%M%S')}.bak"
        try:
            shutil.copy2(str(objetivo), str(respaldo))
            objetivo.write_text(nuevo, encoding="utf-8")
        except Exception as e:
            return {"respuesta": f"No pude escribir: {str(e)[:120]}. Archivo intacto."}
        if objetivo.suffix == ".py":
            chk = await asyncio.to_thread(subprocess.run, [sys.executable, "-m", "py_compile", str(objetivo)],
                                          capture_output=True, text=True)
            if chk.returncode != 0:
                shutil.copy2(str(respaldo), str(objetivo))  # AUTO-REVERT
                return {"respuesta": f"🛑 El cambio no pasó la verificación de compilación, así que **lo revertí solo**. "
                        f"Tu {rel} quedó como estaba. Detalle: {(chk.stderr or '')[:150]}"}
        nucleo = objetivo.name in _NUCLEO_PROTEGIDO
        aviso = " ⚠️ Es un archivo del NÚCLEO: el cambio aplica al **reiniciar** AURORA; si algo falla al arrancar, restaura el respaldo." if nucleo else ""
        return {"respuesta": f"✅ Edité {rel} de verdad (compila y no se perdió código). "
                f"Respaldo guardado por si quieres revertir: {respaldo.name}.{aviso}"}

    async def _consultar_codigo_real(self, mensaje: str) -> Dict:
        """CHAT ↔ IDE (SOLO LECTURA): lee/busca/explica código real. NUNCA edita el núcleo."""
        import re
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        m = _norm_txt(mensaje)
        # ── Búsqueda de un término en el código ──
        if any(k in m for k in ("busca en el codigo", "busca en los archivos", "donde esta la funcion", "en que archivo esta")):
            term = re.split(r"(?:busca en el codigo|busca en los archivos|donde esta la funcion|en que archivo esta)",
                            mensaje, flags=re.I)[-1].strip(" .:,\"'")
            if not term:
                return {"respuesta": "¿Qué término busco en el código?"}

            def _buscar_sync() -> list:
                # Medido en vivo: sin esto, una búsqueda que no encuentra nada tardaba
                # ~22s Y bloqueaba el event loop COMPLETO (todas las sesiones de chat a
                # la vez), porque no corría en un hilo aparte. Además 567 de 698 .py son
                # dependencias de terceros vendorizadas en SUPER_MARKETING_SYSTEM — se
                # excluyen para no contaminar resultados ni gastar tiempo en ellas.
                hits, escaneados = [], 0
                for p in root.rglob("*.py"):
                    sp = str(p)
                    if ("__pycache__" in sp or ".ide_backups" in sp or "_OBSOLETOS" in sp
                            or "_ARCHIVE" in sp or "SUPER_MARKETING_SYSTEM" in sp):
                        continue
                    escaneados += 1
                    if escaneados > 400:  # tope duro: nunca se rinde despues de esto
                        break
                    try:
                        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                            if term.lower() in line.lower():
                                hits.append(f"{p.relative_to(root)}:{i}: {line.strip()[:90]}")
                                break
                    except Exception:
                        continue
                    if len(hits) >= 20:
                        break
                return hits

            hits = await asyncio.to_thread(_buscar_sync)
            return {"respuesta": (f"Encontré '{term}' en:\n" + "\n".join(hits)) if hits else f"No encontré '{term}' en el código."}
        # ── Leer / mostrar / explicar un archivo ──
        fn = re.search(r"([\w\-]+\.\w{1,5})", mensaje)
        if not fn:
            return {"respuesta": "Dime el nombre del archivo (ej. 'muéstrame el archivo ordenes_taller.py')."}
        nombre = fn.group(1)
        encontrados = [p for p in root.rglob(nombre)
                       if "__pycache__" not in str(p) and "_OBSOLETOS" not in str(p) and "_ARCHIVE" not in str(p)]
        if not encontrados:
            return {"respuesta": f"No encontré ningún archivo llamado '{nombre}'."}
        objetivo = encontrados[0]
        try:
            contenido = objetivo.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"respuesta": f"No pude leerlo: {str(e)[:120]}"}
        rel = objetivo.relative_to(root)
        # Si pide explicación y hay LLM, explico CON el contenido real como contexto.
        if self._groq and any(k in m for k in ("explica", "que hace", "qué hace")):
            try:
                r = await self._groq.chat.completions.create(
                    model=_MODELO,
                    messages=[{"role": "system", "content": SISTEMA_BASE + "\nExplica este código real de forma clara y breve. NO inventes: si algo no está en el código, dilo."},
                              {"role": "user", "content": f"Archivo {rel}:\n```\n{contenido[:6000]}\n```\n\nExplícame qué hace."}],
                    max_tokens=500, temperature=0.3)
                return {"respuesta": f"📄 {rel}\n\n" + r.choices[0].message.content.strip()}
            except Exception:
                pass
        snippet = contenido[:2500]
        extra = "" if len(contenido) <= 2500 else f"\n\n… (mostrando los primeros 2500 de {len(contenido)} caracteres)"
        return {"respuesta": f"📄 {rel} ({contenido.count(chr(10))+1} líneas):\n```\n{snippet}\n```{extra}"}

    async def _sintetizar(self, mensaje: str, respuestas: Dict[str, str]) -> str:
        if not self._groq:
            return list(respuestas.values())[0]
        perspectivas = "\n\n".join([f"[{mid}]: {resp[:600]}" for mid, resp in respuestas.items()])
        r = await self._groq.chat.completions.create(
            model=_MODELO,
            messages=[
                {"role":"system","content":SISTEMA_BASE+"\nSintetiza las perspectivas en UNA respuesta coherente y directa. Máximo 400 palabras."},
                {"role":"user","content":f"Pregunta: {mensaje}\n\nPerspectivas:\n{perspectivas}"}
            ],
            max_tokens=500, temperature=0.5
        )
        return r.choices[0].message.content.strip()

    async def _fallback(self, mensaje: str, ctx: Dict) -> str:
        # RAZONADOR PROFUNDO — verdadero último recurso: solo llega aquí un mensaje que
        # NINGÚN candado directo ni el enrutador universal (con ~690 herramientas reales)
        # supo resolver. Antes corría PRIMERO (con umbral ciego de >180 caracteres) y con
        # contexto vacío — así perdía cualquier mensaje largo real ANTES de intentar algo
        # real, y cuando sí corría no sabía nada de lo que AURORA puede hacer. Ahora, si
        # sí aplica, recibe SISTEMA_BASE + lo que la Biblioteca tenga sobre el tema real.
        if _es_pregunta_profunda(mensaje):
            try:
                bib_ctx = await asyncio.to_thread(_biblioteca().contexto_para_llm, mensaje, 3)
            except Exception:
                bib_ctx = ""
            contexto_real = SISTEMA_BASE
            if bib_ctx:
                contexto_real += "\n\n--- BIBLIOTECA (manuales reales de Anuar) ---\n" + bib_ctx
            try:
                res = await asyncio.to_thread(_razonador().razonar, mensaje, contexto_real)
                if isinstance(res, dict) and res.get("status") == "ok" and res.get("respuesta"):
                    return res["respuesta"]
            except Exception as e:
                logger.debug(f"Razonador profundo no aplicó, sigue con fallback normal: {e}")

        messages = [
            {"role": "system", "content": SISTEMA_BASE},
            {"role": "user", "content": mensaje},
        ]
        try:
            if not self._groq:
                raise RuntimeError("groq_no_configurado")
            r = await self._groq.chat.completions.create(
                model=_MODELO, messages=messages, max_tokens=600, temperature=0.7
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            logger.warning(f"Groq falló en fallback ({err[:120]}); intentando respaldo LOCAL (Ollama)")
            # Respaldo LOCAL sin internet (Ollama) — respaldo del respaldo
            try:
                texto = await asyncio.to_thread(_llm_local_sync, messages)
                if texto and texto.strip():
                    return texto.strip()
            except Exception as e2:
                logger.error(f"Respaldo LOCAL (Ollama) falló en fallback: {e2}")
            if "401" in err or "invalid_api_key" in err:
                return "⚠️ API Key de Groq inválida o vencida. Ve a console.groq.com → API Keys → genera una nueva y actualiza C:\\AURORA\\.env"
            return f"AURORA procesó tu mensaje pero el LLM no respondió: {err[:150]}"

    # ── MEMORIA CORTO PLAZO (RAM) ──────────────────────────────

    def _agregar_sesion(self, session_id: str, mensaje: str, respuesta: str) -> None:
        if session_id not in self._memoria_corto:
            self._memoria_corto[session_id] = []
        self._memoria_corto[session_id].extend([
            {"rol": "user", "contenido": mensaje},
            {"rol": "assistant", "contenido": respuesta[:500]},
        ])
        # Mantener solo los últimos N mensajes
        self._memoria_corto[session_id] = self._memoria_corto[session_id][-(_MAX_HISTORIAL_SESION * 2):]

    def limpiar_sesion(self, session_id: str) -> None:
        self._memoria_corto.pop(session_id, None)

    # ── UTILIDADES ─────────────────────────────────────────────

    def _tema_rapido(self, mensaje: str) -> str:
        msg = _norm_txt(mensaje)  # antes .lower() sin quitar acentos — "emocion" con
        # tilde nunca matcheaba, la unica de las 17 funciones gatillo con esa inconsistencia.
        if any(w in msg for w in ["venta","atf","retrofit","cliente"]): return "ventas"
        if any(w in msg for w in ["coaching","familia","emocion"]): return "coaching"
        if any(w in msg for w in ["precio","cotiz","costo"]): return "ventas"
        if any(w in msg for w in ["marketing","contenido","tiktok"]): return "marketing"
        return ""

    def estado(self) -> Dict:
        return {
            "sistema": "Consciencia",
            "lista": self._listo,
            "motores_cargados": len(self._prompts_motor),
            "sesiones_activas": len(self._memoria_corto),
            "groq_activo": self._groq is not None,
        }


# Instancia global
consciencia = Consciencia()
