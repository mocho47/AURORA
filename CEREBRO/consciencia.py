# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║              🧠 AURORA — CONSCIENCIA CENTRAL                         ║
║  Pipeline cognitivo completo: percibir→recordar→enrutar→             ║
║  ejecutar→sintetizar→aprender. Sin censura. Sin simulaciones.        ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/CEREBRO/consciencia.py
"""
import asyncio, importlib, json, logging, os, re
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


def _es_intencion_operativa(mensaje: str) -> bool:
    """True si el mensaje pide operar algo real (archivo/sistema/web/herramienta)."""
    if not mensaje:
        return False
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


def _norm_txt(mensaje: str) -> str:
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


def _es_abrir_navegador(mensaje: str) -> bool:
    if not _DOMINIO_RE.search(mensaje):
        return False
    return _contiene_trigger(_norm_txt(mensaje), _ABRIR_NAVEGADOR_TRIGGERS)


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


def _es_busqueda_web(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    if _contiene_trigger(m, _BUSQUEDA_WEB_TRIGGERS):
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
        "nueva cita", "crear cita", "agenda del dia"))


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


def _es_ficha_vendedor(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "ficha de", "ficha tecnica de", "dame el pitch", "hazme un pitch",
        "argumentos de venta", "como vendo el", "como vender el", "brief de venta"))


def _es_intuicion(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "que me sugieres", "tu intuicion", "que me recomiendas", "predice",
        "prediccion", "que deberia hacer", "sugerencia proactiva", "que sigue"))


def _es_memoria(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), (
        "que recuerdas de", "que recuerdas sobre", "tu memoria", "recuerdas cuando",
        "que sabes de", "que tienes guardado sobre", "recuerdas que"))


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


def _es_consulta_codigo(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _CONSULTA_CODIGO_TRIGGERS)


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
    # Nota: formas como "guardarlo"/"ábrelo"/"exportarlo" (verbo + pronombre pegado)
    # ya NO necesitan su propia entrada aquí — _contiene_trigger() ahora reconoce el
    # mismo verbo con "-lo/-la/-los/-las/-le/-les/-se" pegado como la misma palabra
    # (arreglo estructural 2026-07-27, cierra esta clase de hueco para los 14
    # dominios de una vez, no verbo por verbo).
)


def _es_comando_corel(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
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
)


def _es_consulta_negocio(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    # Debe ser una PREGUNTA/consulta, no una orden de acción física
    interroga = _contiene_trigger(m, ("cuanto", "cuantos", "cuantas", "cuales",
                                      "dime", "muestrame", "lista", "resumen")) or "que " in m or "como va" in m
    return interroga and _contiene_trigger(m, _NEGOCIO_TRIGGERS)


_EDITAR_CODIGO_TRIGGERS = (
    "edita el archivo", "edita el codigo", "modifica el archivo", "modifica el codigo",
    "cambia en el archivo", "agrega en el archivo", "reemplaza en el archivo",
    "corrige el archivo", "arregla el archivo",
)


def _es_editar_codigo(mensaje: str) -> bool:
    return _contiene_trigger(_norm_txt(mensaje), _EDITAR_CODIGO_TRIGGERS)


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
_RE_RUTA_SOLA = re.compile(r'^["\'\s]*([A-Za-z]:\\[^\r\n"\']+?\.[A-Za-z0-9]{2,5})["\'\s.]*$')


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
    ("ruta_sola",       _es_ruta_sola,         "_ruta_sola_real",         "contexto_archivo"),
    ("abrir_navegador", _es_abrir_navegador,  "_abrir_navegador_real",  "pc_access"),
    ("acerca_de",       _es_acerca_de,         "_acerca_de_real",         "auto_conocimiento"),
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
        self._groq = AsyncGroq(api_key=api_key, max_retries=1) if api_key else None

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
        # Si el mensaje habla del propio sistema, los candados de VENTA no lo tocan.
        # Un cliente no escribe "consciencia.py" ni "plugin instalado"; Anuar sí,
        # porque usa AURORA de las dos formas y los dos chats se estaban pisando.
        _tema_sistema = _es_tema_del_sistema(mensaje)

        for _nombre_candado, _trigger, _metodo_candado, _motor_id_candado in _CANDADOS:
            if _nombre_candado == "accion_fisica" and (set(motor_ids) & _MOTORES_EJECUTORES):
                continue
            if _tema_sistema and _nombre_candado in _CANDADOS_DE_VENTA:
                continue
            if not _trigger(mensaje):
                continue
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
            else:
                real = await getattr(self, _metodo_candado)(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
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
            if real is not None:
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
            respuesta_final = (
                "No ejecuté ninguna acción real para ese pedido. "
                "No voy a simular resultado. Reescríbelo con el objetivo directo "
                "(ej. abrir/convertir/buscar en web con ruta o dato concreto) y lo ejecuto de verdad."
            )

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
        if not respuesta:
            return respuesta
        import re as _re
        baja = respuesta.lower()
        if not any(_re.search(p, baja) for p in self._PATRONES_NEGACION_FALSA):
            return respuesta
        try:
            reg = _registro()
            candidatos = await asyncio.to_thread(reg.buscar, mensaje, 4)
        except Exception:
            return respuesta
        if not candidatos:
            return respuesta  # de verdad no hay herramienta real — la negación queda tal cual
        reales = "\n".join(
            f"- {c.get('clave', c.get('funcion',''))}: {(c.get('doc') or '')[:100]}"
            for c in candidatos[:4]
        )
        return (respuesta.strip() +
                f"\n\n(Corrección real antes de enviarte esto: lo de arriba no es del todo "
                f"cierto — SÍ tengo herramientas conectadas que aplican aquí:\n{reales}\n"
                f"Pídemelo de nuevo directo y las uso de verdad.)")

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
        dominio = _DOMINIO_RE.search(mensaje)
        if not dominio:
            return {"respuesta": "Dame el dominio o la URL exacta (ej. ameede.com) y la abro de verdad."}
        r = await pc_access.abrir_url(dominio.group(0))
        if r.get("status") == "OK":
            return {"respuesta": f"✅ Abierta real en el navegador: {dominio.group(0)}."}
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

    async def _buscar_web_candado(self, mensaje: str) -> Dict:
        """Envoltorio delgado para que _buscar_web calce con la firma uniforme
        del pipeline de candados (todos regresan {"respuesta": ...})."""
        return {"respuesta": await self._buscar_web(mensaje)}

    async def _buscar_web(self, consulta: str) -> str:
        """Búsqueda web real — ddgs EN VIVO, luego fallbacks, luego Groq."""
        # 1) Web REAL en vivo (WEB/web_real.py con ddgs)
        try:
            ctx = await asyncio.to_thread(_web_real().contexto_para_llm, consulta, 4)
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

    async def _ruta_sola_real(self, mensaje: str, session_id: str = "", canal: str = "api") -> Dict:
        """Llegó solo una ruta. Es el dato que faltaba para lo que se pidió antes.

        Se pega la ruta al último mensaje de la sesión y se reprocesa: si antes
        dijo "abre esta imagen en corel", el combinado SÍ calza con el candado de
        Corel y se ejecuta de verdad. Sin contexto previo, se ofrece lo que
        REALMENTE se puede hacer con ese tipo de archivo — nunca un "no puedo".
        """
        ruta = _RE_RUTA_SOLA.match(mensaje.strip()).group(1)
        existe = Path(ruta).exists()
        ext = Path(ruta).suffix.lower().lstrip(".")

        if not existe:
            return {"respuesta": f"No encontré ese archivo en el disco:\n`{ruta}`\n"
                                 "Revisa la ruta y te lo trabajo."}

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
        return await self._ejecutar_herramienta_real(reg, clave, args, h)

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
            # El docstring suele venir conjugado en tercera persona ("Genera el
            # contenido...") y pegarlo tal cual daba "Voy a genera contenido".
            # Se pasa a infinitivo el primer verbo.
            primera, _, resto = frase.partition(" ")
            for terminacion, inf in (("a", "ar"), ("e", "er"), ("e", "ir")):
                if primera.endswith(terminacion) and len(primera) > 3:
                    primera = primera[:-1] + inf
                    break
            frase = (primera + " " + resto).strip()
            base = f"Voy a {frase}."
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
        # El LLM redacta el archivo COMPLETO ya con el cambio, sin comentarios extra.
        # max_tokens subido de 4000 a 7800 (medido: consciencia.py necesitaria ~30,000
        # tokens para reproducirse completo, asi que ni esto alcanza para los archivos
        # mas grandes del nucleo — por eso el chequeo de finish_reason de abajo es la
        # proteccion real, no el numero en si).
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
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
