# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║              🧠 AURORA — CONSCIENCIA CENTRAL                         ║
║  Pipeline cognitivo completo: percibir→recordar→enrutar→             ║
║  ejecutar→sintetizar→aprender. Sin censura. Sin simulaciones.        ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/CEREBRO/consciencia.py
"""
import asyncio, importlib, json, logging, os
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


# Verbos que indican que el usuario pide una ACCIÓN/dato operable (no charla).
_INTENCION_OPERAR = (
    "cotiza", "cotizar", "cuanto cuesta", "cuanto sale", "calcula", "dame", "lista",
    "listar", "muestra", "genera", "crea", "busca", "revisa", "analiza", "convierte",
    "vectoriza", "quita el fondo", "prepara", "cuantos", "cuantas", "arma", "haz",
    # verbos de ACCIÓN/reparación — antes caían al LLM genérico (que negaba capacidad).
    "arregla", "repara", "fix", "soluciona", "corrige", "ejecuta", "corre", "activa",
    "apaga", "enciende", "mueve", "copia", "abre", "cierra", "instala", "limpia",
    "optimiza", "diagnostica", "verifica", "checa", "publica", "envia", "manda",
    "consulta", "reporta", "exporta", "escala", "cotizame", "hazme",
)


def _pide_operar(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in _INTENCION_OPERAR)


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
    # WhatsApp — enviar mensajes reales (nunca simular una conversación)
    "manda un whatsapp", "mandale un whatsapp", "envia un whatsapp", "enviale un whatsapp",
    "manda whatsapp", "envia whatsapp", "mensaje de whatsapp", "por whatsapp",
    "entra a mi conversacion", "entra a la conversacion", "mandale un saludo",
    "escribele por whatsapp", "contactalo por whatsapp",
)
# Motores que SÍ ejecutan acciones reales en el sistema.
_MOTORES_EJECUTORES = {"pc_cmd", "self_repair"}


def _es_accion_fisica(mensaje: str) -> bool:
    import unicodedata as _ud
    m = "".join(c for c in _ud.normalize("NFD", (mensaje or "").lower()) if _ud.category(c) != "Mn")
    return any(t in m for t in _ACCION_FISICA_TRIGGERS)


def _norm_txt(mensaje: str) -> str:
    import unicodedata as _ud
    return "".join(c for c in _ud.normalize("NFD", (mensaje or "").lower()) if _ud.category(c) != "Mn")


# ── Búsqueda web EXPLÍCITA (el usuario pide navegar/buscar en internet) ──
_BUSQUEDA_WEB_TRIGGERS = (
    "busca en internet", "buscar en internet", "busca en la web", "busca en google",
    "googlea", "navega", "en internet busca", "investiga en la web", "busca en linea",
    "buscar en la web", "consulta en internet", "revisa en internet", "busca en la red",
)


def _es_busqueda_web(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in _BUSQUEDA_WEB_TRIGGERS)


# ── Detectores de motores conectados directo al chat (acción real) ──────
def _es_publicar(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "publica hoy", "publicar hoy", "publica en atf", "publica en facebook",
        "prepara la publicacion", "preparar publicacion", "que publico hoy",
        "estrategia de ingresos", "sube el video de hoy", "postea hoy", "publica el reel"))


def _es_agenda(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "que tengo agendado", "mi agenda", "proximas citas", "proxima cita",
        "que citas tengo", "agenda de hoy", "que tengo hoy", "resumen de agenda",
        "citas de hoy", "tengo pendientes hoy"))


def _es_ficha_vendedor(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "ficha de", "ficha tecnica de", "dame el pitch", "hazme un pitch",
        "argumentos de venta", "como vendo el", "como vender el", "brief de venta"))


def _es_intuicion(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "que me sugieres", "tu intuicion", "que me recomiendas", "predice",
        "prediccion", "que deberia hacer", "sugerencia proactiva", "que sigue"))


def _es_memoria(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "que recuerdas de", "que recuerdas sobre", "tu memoria", "recuerdas cuando",
        "que sabes de", "que tienes guardado sobre", "recuerdas que"))


def _es_equipos(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "activa el equipo", "activar equipo", "que equipos tienes", "lista de equipos",
        "arma el equipo", "pon a trabajar el equipo", "equipo de marketing", "equipo de ventas"))


# ── Fábrica de AGENTES: crear/listar/correr agentes de tarea desde el chat ──
def _es_crear_agente(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "creame un agente", "crea un agente", "crear un agente", "fabricame un agente",
        "fabrica un agente", "necesito un agente", "quiero un agente", "arma un agente",
        "nuevo agente"))


def _es_listar_agentes(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
        "que agentes tengo", "que agentes hay", "lista de agentes", "mis agentes",
        "muestrame los agentes", "cuales agentes"))


def _es_correr_agente(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in (
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
    m = _norm_txt(mensaje)
    return any(t in m for t in _CREAR_CAPACIDAD_TRIGGERS)


# ── CHAT ↔ IDE: leer/buscar/explicar código por chat (solo lectura) ────
_CONSULTA_CODIGO_TRIGGERS = (
    "muestrame el archivo", "muestrame el codigo", "leeme el archivo", "lee el archivo",
    "abre el archivo", "que hace el archivo", "busca en el codigo", "busca en los archivos",
    "donde esta la funcion", "en que archivo esta", "ensename el codigo de",
    "muestrame el codigo de", "que dice el archivo",
)


def _es_consulta_codigo(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in _CONSULTA_CODIGO_TRIGGERS)


# ── CHAT ↔ TALLER: conversión REAL de archivos a DXF (motor que estaba dormido) ──
_CONVERSION_TRIGGERS = (
    "convierte", "convertir", "conviertelo", "pasa a dxf", "pasalo a dxf",
    "a dxf", "en dxf", "exporta a dxf", "vectoriza", "vectorizar",
)


def _es_conversion_dxf(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return "dxf" in m and any(t in m for t in _CONVERSION_TRIGGERS)


# ── CHAT ↔ MOTORES DE NEGOCIO: responder con DATOS REALES, nunca improvisando ──
_NEGOCIO_TRIGGERS = (
    "orden", "ordenes", "entrego", "entregar", "pendiente de entrega",
    "inventario", "existencia", "cuanto me queda", "cuanto tengo de", "bajo minimo",
    "lead", "leads", "prospecto", "clientes nuevos", "embudo", "pronostico",
    "contabilidad", "cuanto vendi", "cuanto llevo", "utilidad", "ganancia del mes",
    "por cobrar", "cobrar", "fuentes", "que fuente",
)


def _es_consulta_negocio(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    # Debe ser una PREGUNTA/consulta, no una orden de acción física
    interroga = any(k in m for k in ("cuanto", "cuantos", "cuantas", "que ", "cuales",
                                     "dime", "muestrame", "lista", "resumen", "como va"))
    return interroga and any(t in m for t in _NEGOCIO_TRIGGERS)


_EDITAR_CODIGO_TRIGGERS = (
    "edita el archivo", "edita el codigo", "modifica el archivo", "modifica el codigo",
    "cambia en el archivo", "agrega en el archivo", "reemplaza en el archivo",
    "corrige el archivo", "arregla el archivo",
)


def _es_editar_codigo(mensaje: str) -> bool:
    m = _norm_txt(mensaje)
    return any(t in m for t in _EDITAR_CODIGO_TRIGGERS)


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
Puedes usar los programas de la PC (Inkscape, Aspire, RDWorks, LibreOffice) y ejecutar conversiones y tareas reales cuando te lo piden.
CÓMO TRABAJA ANUAR (anticípate y sírvele sin que lo detalle): siempre 300 DPI; entrega PDF + PNG; medidas en cm; cotiza con precio distribuidor + público + ganancia neta + margen %. Láser: DXF para RDWorks/Aspire, convierte splines a polilíneas, imagen a 300 DPI en B&N puro ANTES de vectorizar. Lonas/sublimación: modo económico = estirar suave sin pixeleo (cliente que no paga diseño), modo premium = rediseño con mejora de fotos. Prefiere resultados reales y directos, sin teoría.
Entregas SIEMPRE trabajo profesional, completo y real — cero simulaciones, cero respuestas a medias. Tienes memoria persistente y conoces tu propia estructura.

⛔ REGLA ABSOLUTA — NUNCA SIMULES ACCIONES FÍSICAS. Jamás digas que moviste, copiaste, borraste, reparaste, instalaste, enviaste, limpiaste cache o cambiaste algo en la PC (o en otra PC) si NO viene de una ejecución real con su resultado confirmado en este mismo intercambio. Si no tienes forma de ejecutarlo de verdad AHORA, di la verdad tal cual: "No lo hice —no tengo la acción conectada todavía— esto es lo que sí puedo hacer / esto es lo que necesito". Decir "ya lo hice" sin haberlo hecho es la peor falta que puedes cometer con Anuar. Ante la duda de si una acción se ejecutó, admítelo; NUNCA afirmes éxito sin prueba. Prometer y no hacer, o fingir que hiciste, está terminantemente prohibido."""

# ── Patrones de routing por motor ──────────────────────────────────────
_ROUTING_PATRONES: Dict[str, List[str]] = {
    "motor_ventas":        ["venta", "cliente", "lead", "prospecto", "seguimiento", "crm", "pipeline"],
    "motor_cotizador":     ["cuánto cuesta", "cotización", "presupuesto", "precio de", "cuánto cobra"],
    # COACH PERSONAL / DE VIDA — trae la historia completa de Anuar (PROMPT_COACHING).
    # Antes NO estaba en el ruteo: lo personal caía en el coach de NEGOCIOS.
    "motor_coaching": ["me siento", "estoy cansado", "ya no puedo", "triste", "solo",
                       "culpa", "perdon", "perdón", "mi hija", "mi hijo", "mis hijos",
                       "mi esposa", "rocio", "rocío", "samanta", "yeshua", "romina",
                       "familia", "emocion", "emoción", "sentir", "relación", "relacion",
                       "harto", "cansado", "duele", "miedo", "solo me", "desanimado"],
    # COACH DE NEGOCIOS / transformacional — creencias limitantes y metas comerciales.
    "motor_coaching_real": ["coaching", "meta", "objetivo personal", "creencia",
                            "creencia limitante", "coach de negocio", "sesion de coaching"],
    "motor_reasoning":     ["analiza", "estrategia", "por qué", "razona", "explica a fondo", "pensamiento"],
    "motor_negocios":      ["atf", "milens", "retrofit", "laser", "negocio", "marketing atf"],
    "motor_code_gen":      ["código", "script", "función", "clase", "programa", "bug", "error en código"],
    "motor_imagenes":      ["imagen", "foto", "diseño", "edita", "fondo", "laser prep"],
    "motor_pedidos":       ["pedido", "orden", "envío", "tracking", "entrega"],
    "motor_analisis":      [],  # fallback general
    "web_search":          ["busca en internet", "buscar", "qué precio tiene", "competencia", "tendencia"],
    "self_info":           ["qué puedes", "tus capacidades", "tu estructura", "tus módulos", "cómo funcioens"],
    "self_repair":         ["arréglate", "repara el archivo", "fix ", "está fallando el módulo"],
    "pc_cmd":              ["ejecuta en pc", "corre el comando", "abre el archivo", "estado del pc", "cpu ", "ram ", "disco "],
}

_MODELO = "llama-3.1-8b-instant"
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

    async def inicializar(self) -> None:
        if self._listo:
            return
        api_key = os.getenv("GROQ_API_KEY", "")
        self._groq = AsyncGroq(api_key=api_key) if api_key else None

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
        if not self._listo:
            await self.inicializar()

        session_id = session_id or user_id
        inicio = datetime.utcnow()
        self._sueno.registrar_actividad()

        # 0. RAZONADOR PROFUNDO (aditivo, on-demand). Para preguntas difíciles
        # delega al cerebro grande (70B en la nube). Blindado: ante CUALQUIER
        # error o status!=ok NO retorna — deja seguir el flujo normal intacto.
        if _es_pregunta_profunda(mensaje):
            try:
                res = await asyncio.to_thread(_razonador().razonar, mensaje, "")
                if isinstance(res, dict) and res.get("status") == "ok" and res.get("respuesta"):
                    respuesta_final = res["respuesta"]
                    try:
                        self._agregar_sesion(session_id, mensaje, respuesta_final)
                    except Exception:
                        pass
                    ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                    return {
                        "respuesta": respuesta_final,
                        "motores_usados": ["razonador_profundo"],
                        "temperatura_lead": "frio",
                        "duracion_ms": ms,
                        "timestamp": inicio.isoformat(),
                    }
            except Exception as e:
                logger.debug(f"Razonador profundo no aplicó, sigue flujo normal: {e}")

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

        # 2.5 CANDADO ANTI-SIMULACIÓN — si piden una acción física (mover/copiar/
        # borrar/reparar/limpiar cache/enviar a otra PC) intento ejecutarla DE VERDAD.
        # Si no se puede ejecutar real, respondo honesto — NUNCA finjo haberlo hecho.
        if (_es_accion_fisica(mensaje) and not (set(motor_ids) & _MOTORES_EJECUTORES)
                and not (_es_crear_capacidad(mensaje) or _es_editar_codigo(mensaje) or _es_consulta_codigo(mensaje))
                and not (_es_publicar(mensaje) or _es_agenda(mensaje) or _es_ficha_vendedor(mensaje)
                         or _es_intuicion(mensaje) or _es_memoria(mensaje) or _es_equipos(mensaje))):
            real = await self._accion_sistema_real(mensaje)
            respuesta_final = real["respuesta"]
            self._agregar_sesion(session_id, mensaje, respuesta_final)
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": respuesta_final, "motores_usados": ["accion_sistema"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.53 CHAT ↔ WEB — búsqueda web REAL directa (ddgs). Devuelve los resultados
        # tal cual, sin que la síntesis del LLM los reescriba con "no tengo acceso".
        if _es_busqueda_web(mensaje):
            web = await self._buscar_web(mensaje)
            self._agregar_sesion(session_id, mensaje, web)
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": web, "motores_usados": ["web_search"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.56 CHAT ↔ PUBLICADOR — preparar/publicar de verdad en redes.
        if _es_publicar(mensaje):
            real = await self._publicar_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["publicador"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.57 CHAT ↔ AGENDA — citas y pendientes reales.
        if _es_agenda(mensaje):
            real = await self._agenda_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["agenda"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.58 CHAT ↔ VENDEDOR — ficha técnica / pitch real.
        if _es_ficha_vendedor(mensaje):
            real = await self._vendedor_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["vendedor"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.59 CHAT ↔ INTUICIÓN/PREDICCIÓN — sugerencia proactiva real.
        if _es_intuicion(mensaje):
            real = await self._intuicion_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["intuicion"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.60 CHAT ↔ MEMORIA — recuerda de verdad de su memoria persistente.
        if _es_memoria(mensaje):
            real = await self._memoria_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["memoria"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.61 CHAT ↔ EQUIPOS — arma/activa un equipo de motores de verdad.
        if _es_equipos(mensaje):
            real = await self._equipos_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["equipos"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.54 CHAT ↔ TALLER — convertir archivos a DXF de verdad (motor dormido).
        if _es_conversion_dxf(mensaje):
            real = await self._convertir_dxf_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["taller_dxf"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.55 CHAT ↔ MOTORES DE NEGOCIO — datos REALES (órdenes, inventario, CRM,
        # contabilidad). Va ANTES del LLM para que jamás improvise cifras del taller.
        if _es_consulta_negocio(mensaje):
            real = await self._consultar_negocio_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["negocio_real"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.6 CHAT ↔ FÁBRICA — crear una capacidad/motor nuevo de VERDAD (aislado).
        if _es_crear_capacidad(mensaje):
            real = await self._crear_capacidad_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["fabrica"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.65 CHAT ↔ IDE (EDITAR) — modifica cualquier archivo con red anti-ruptura:
        # respaldo + chequeo de compilación + guardián anti-pérdida (si dejaría menos
        # código/funciones, rechaza y revierte). NUNCA rompe ni resta en silencio.
        if _es_editar_codigo(mensaje):
            real = await self._editar_codigo_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["ide_editor"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.7 CHAT ↔ IDE — leer/buscar/explicar código (solo lectura, núcleo a salvo).
        if _es_consulta_codigo(mensaje):
            real = await self._consultar_codigo_real(mensaje)
            self._agregar_sesion(session_id, mensaje, real["respuesta"])
            ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
            return {"respuesta": real["respuesta"], "motores_usados": ["ide"],
                    "temperatura_lead": "frio", "duracion_ms": ms, "timestamp": inicio.isoformat()}

        # 2.8 ENRUTADOR UNIVERSAL — última red antes del LLM genérico. Si el mensaje pide
        # OPERAR (no charla) y ningún candado específico aplicó, deja que el registro de
        # herramientas reales (203 funciones) elija y EJECUTE una de verdad. Si no hay
        # herramienta que aplique, devuelve None y sigue el flujo normal (no rompe nada).
        # Se intenta en cualquier mensaje con sustancia (2+ palabras). El router se
        # auto-filtra: si no hay herramienta real que aplique, devuelve None (barato, sin
        # LLM) y sigue el flujo normal. Así alcanza las 475 funciones sin gatillo angosto.
        if len(_norm_txt(mensaje).split()) >= 2:
            real = await self._router_universal(mensaje)
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

        # 5. APRENDIZAJE
        asyncio.create_task(self._perfil.analizar_interaccion(mensaje, respuesta_final, list(respuestas.keys())))
        await self._memoria.registrar(
            motor_origen="consciencia",
            tipo_evento="interaccion",
            contenido={"user_id": user_id, "msg": mensaje[:400], "resp": respuesta_final[:400], "motores": list(respuestas.keys())},
            importancia=0.7,
        )
        nueva_temp = await self._ctx.actualizar(user_id, mensaje, respuesta_final, list(respuestas.keys()), canal)

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

    # ── ROUTING ────────────────────────────────────────────────

    def _routing_rapido(self, mensaje: str) -> Tuple[List[str], bool]:
        """Scoring por keywords — sin llamada a API."""
        msg = mensaje.lower()
        scores: Dict[str, int] = {}

        for motor_id, patrones in _ROUTING_PATRONES.items():
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

        system_content = (
            f"{SISTEMA_BASE}\n\n"
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

    # ── BÚSQUEDA WEB ───────────────────────────────────────────

    async def _buscar_web(self, consulta: str) -> str:
        """Búsqueda web real — ddgs EN VIVO, luego fallbacks, luego Groq."""
        # 1) Web REAL en vivo (WEB/web_real.py con ddgs)
        try:
            ctx = await asyncio.to_thread(_web_real().contexto_para_llm, consulta, 4)
            if ctx:
                return ctx
        except Exception:
            pass
        try:
            import sys
            sys.path.insert(0, str(ROOT / "CORE"))
            from buscador_web_profesional import BuscadorWebProfesional
            buscador = BuscadorWebProfesional()
            resultados = await buscador.buscar(consulta, num_resultados=3)
            if resultados:
                resumen = "\n".join([f"- {r.get('titulo','')} ({r.get('url','')}): {r.get('snippet','')}" for r in resultados[:3]])
                return f"Resultados web para '{consulta}':\n{resumen}"
        except Exception:
            pass
        # Fallback: LLM con conocimiento propio
        if self._groq:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[{"role":"user","content":f"Busca y responde sobre: {consulta}. Sé honesto si no tienes datos actuales."}],
                max_tokens=400
            )
            return r.choices[0].message.content.strip()
        return "Búsqueda web no disponible."

    # ── MOTORES CONECTADOS DIRECTO AL CHAT (acción real, sin simular) ──

    async def _publicar_real(self, mensaje: str) -> Dict:
        m = _norm_txt(mensaje)
        try:
            pub = _pubint()
            if "estrategia" in m:
                d = await asyncio.to_thread(pub.estrategia_ingresos, "atf", "")
                return {"respuesta": self._fmt_dict("📣 Estrategia de ingresos ATF", d)}
            aprobar = any(k in m for k in ("de verdad", "aprueba", "aprobado", "hazlo ya",
                                           "publicalo ya", "publícalo ya", "si publica", "publica ya"))
            if aprobar:
                d = await asyncio.to_thread(pub.publicar_hoy, "facebook", "", True)
                if d.get("status") == "PUBLICADO":
                    return {"respuesta": f"✅ PUBLICADO de verdad en Facebook ATF (post {d.get('post_id')}). Video: {d.get('video','')}"}
                return {"respuesta": f"No publiqué (no lo simulo): {self._fmt_dict('publicar_hoy', d)}"}
            d = await asyncio.to_thread(pub.preparar_publicacion, "atf")
            return {"respuesta": "📋 Esto es lo que publicaría HOY (aún NO lo subí — dime 'publícalo de verdad' para hacerlo):\n" + self._fmt_dict("preparar", d)}
        except Exception as e:
            return {"respuesta": f"No pude preparar la publicación (no lo invento): {str(e)[:200]}"}

    async def _agenda_real(self, mensaje: str) -> Dict:
        m = _norm_txt(mensaje)
        try:
            ag = _agenda()
            if hasattr(ag, "init_db"):
                await asyncio.to_thread(ag.init_db)
            if "proxim" in m:
                d = await asyncio.to_thread(ag.proximas, 24)
            else:
                d = await asyncio.to_thread(ag.resumen)
            return {"respuesta": self._fmt_dict("📅 Agenda", d)}
        except Exception as e:
            return {"respuesta": f"No pude leer la agenda (no lo invento): {str(e)[:200]}"}

    async def _vendedor_real(self, mensaje: str) -> Dict:
        m = _norm_txt(mensaje)
        producto = mensaje
        for t in ("ficha tecnica de", "ficha de", "dame el pitch de", "hazme un pitch de",
                  "argumentos de venta de", "como vendo el", "como vender el", "brief de venta de",
                  "dame el pitch", "hazme un pitch"):
            if t in m:
                idx = m.find(t) + len(t)
                producto = mensaje[idx:].strip(" :¿?.") or mensaje
                break
        try:
            ven = _vendedor()
            if any(k in m for k in ("pitch", "argumento", "brief", "como vend")):
                txt = await asyncio.to_thread(ven.construir_brief, "cliente", producto, "", "")
                return {"respuesta": f"🎯 Brief de venta ({producto}):\n{txt[:1500]}"}
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
        try:
            recuerdos = await self._memoria.recordar(tema=self._tema_rapido(mensaje), limite=5)
            if not recuerdos:
                return {"respuesta": "No tengo nada guardado sobre eso todavía (no te invento un recuerdo)."}
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
                return {"respuesta": self._fmt_dict(f"🤝 Equipo '{equipo_id}' activado", d)}
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
    async def _router_universal(self, mensaje: str) -> Optional[Dict]:
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
            "al mensaje del usuario, o null si NINGUNA aplica. NO inventes valores: solo pon en args "
            "los que se deduzcan del mensaje; deja fuera los que no sepas.\n\n"
            f"HERRAMIENTAS:\n{catalogo}\n\n"
            f'MENSAJE DEL USUARIO: "{mensaje[:400]}"\n\n'
            'Responde SOLO JSON, sin texto extra: {"herramienta":"<clave o null>","args":{...}}'
        )
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO, messages=[{"role": "user", "content": prompt}],
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

        # Herramienta destructiva/escritura → NO ejecutar; pedir confirmación.
        if h.get("peligrosa"):
            return {"respuesta": f"Eso hace un cambio real ({clave}). Confírmame y lo hago."}

        # No peligrosa → ejecutar de verdad (registro.ejecutar es síncrono).
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

        # WhatsApp: ENVIAR un mensaje — REAL por Green API. Si trae número, lo manda de
        # verdad; si no, lo pide honesto. NUNCA simula una conversación.
        if ("whatsapp" in m or "whats app" in m or "wasap" in m or "watsap" in m or
                "mandale un saludo" in m or "entra a mi conversacion" in m):
            tel = re.sub(r"\D", "", (re.search(r"(\+?52)?\s*\d[\d\s\-]{8,}", mensaje or "") or type("", (), {"group": lambda s: ""})()).group() if re.search(r"\d[\d\s\-]{8,}", mensaje or "") else "")
            if len(tel) >= 10:
                import os
                inst = os.getenv("GREEN_API_INSTANCE", ""); gtok = os.getenv("GREEN_API_TOKEN", "")
                if not inst or not gtok:
                    return {"respuesta": "Puedo enviar WhatsApp de verdad, pero faltan las credenciales de Green API en el .env (GREEN_API_INSTANCE / GREEN_API_TOKEN). No lo voy a dar por hecho."}
                chat_id = ("521" + tel[-10:]) + "@c.us"
                texto_msg = mensaje
                try:
                    import requests, urllib.parse
                    url = f"https://{inst}.api.greenapi.com/waInstance{inst}/sendMessage/{gtok}"
                    resp = await asyncio.to_thread(lambda: requests.post(url, json={"chatId": chat_id, "message": "¡Hola! Le escribe ATF - Actualiza Tus Faros. ¿En qué le podemos ayudar? 🚗💡"}, timeout=20))
                    if resp.ok and resp.json().get("idMessage"):
                        return {"respuesta": f"✅ WhatsApp ENVIADO de verdad al {tel[-10:]} (id {resp.json()['idMessage']}). Si quieres un texto distinto, dímelo y lo reenvío."}
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

    async def _convertir_dxf_real(self, mensaje: str) -> Dict:
        """CHAT ↔ TALLER: convierte de verdad un archivo a DXF con taller_core
        (motor que existía pero nadie llamaba). Si no encuentra el archivo, lo dice."""
        import re, importlib.util as _ilu
        from pathlib import Path as _P
        raiz = _P(__file__).resolve().parent.parent
        # 1) ruta explícita en el mensaje
        mruta = re.search(r"([A-Za-z]:\\[^\s\"']+\.(?:svg|pdf|ai|eps|cdr|png|jpg|jpeg))", mensaje, re.I)
        ruta = mruta.group(1) if mruta else None
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
        if not ruta:
            return {"respuesta": "Dime qué archivo convierto a DXF (nombre o ruta completa). "
                                 "Acepto SVG, PDF, AI, EPS y también imágenes (las vectorizo)."}
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
        if any(k in m for k in ("orden", "entrego", "entregar", "taller")):
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
        if any(k in m for k in ("lead", "prospecto", "embudo", "pronostico", "fuente", "cliente nuevo")):
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

    async def _crear_capacidad_real(self, mensaje: str) -> Dict:
        """CHAT ↔ FÁBRICA: crea un motor/capacidad nuevo DE VERDAD (aislado y validado).
        No simula: si falla, lo dice."""
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

    async def _editar_codigo_real(self, mensaje: str) -> Dict:
        """CHAT ↔ IDE (EDITAR): modifica cualquier archivo con red anti-ruptura.
        Garantías mecánicas: respaldo (reversible), compila o no se aplica, y guardián
        anti-pérdida (si el cambio dejaría menos código/funciones → revierte). Sin simular."""
        import re, shutil, subprocess, sys
        from datetime import datetime as _dt
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        fn = re.search(r"([\w\-]+\.\w{1,5})", mensaje)
        if not fn:
            return {"respuesta": "Dime el nombre del archivo a editar (ej. 'edita el archivo ordenes_taller.py y agrega…')."}
        nombre = fn.group(1)
        encontrados = [p for p in root.rglob(nombre) if "__pycache__" not in str(p) and ".ide_backups" not in str(p)]
        if not encontrados:
            return {"respuesta": f"No encontré ningún archivo llamado '{nombre}'."}
        objetivo = encontrados[0]
        rel = objetivo.relative_to(root)
        if not self._groq:
            return {"respuesta": "Para redactar el cambio necesito el LLM (Groq) y no está disponible ahora. No inventé nada."}
        try:
            original = objetivo.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"respuesta": f"No pude leer {rel}: {str(e)[:120]}"}
        # El LLM redacta el archivo COMPLETO ya con el cambio, sin comentarios extra.
        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[{"role": "system", "content": "Eres un editor de código preciso. Te doy un archivo COMPLETO y una instrucción. Devuelve el archivo COMPLETO ya modificado, SIN quitar nada que no se te pidió, SIN comentarios ni explicaciones, SIN ```. Conserva todo el código existente."},
                          {"role": "user", "content": f"Archivo {rel}:\n{original}\n\nInstrucción: {mensaje}\n\nDevuelve el archivo completo modificado:"}],
                max_tokens=4000, temperature=0.1)
            nuevo = r.choices[0].message.content
        except Exception as e:
            return {"respuesta": f"No pude generar el cambio: {str(e)[:150]}. No toqué el archivo."}
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
            hits = []
            for p in root.rglob("*.py"):
                sp = str(p)
                if "__pycache__" in sp or ".ide_backups" in sp or "_OBSOLETOS" in sp or "_ARCHIVE" in sp:
                    continue
                try:
                    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                        if term.lower() in line.lower():
                            hits.append(f"{p.relative_to(root)}:{i}: {line.strip()[:90]}")
                            break
                except Exception:
                    continue
                if len(hits) >= 20:
                    break
            return {"respuesta": (f"Encontré '{term}' en:\n" + "\n".join(hits)) if hits else f"No encontré '{term}' en el código."}
        # ── Leer / mostrar / explicar un archivo ──
        fn = re.search(r"([\w\-]+\.\w{1,5})", mensaje)
        if not fn:
            return {"respuesta": "Dime el nombre del archivo (ej. 'muéstrame el archivo ordenes_taller.py')."}
        nombre = fn.group(1)
        encontrados = [p for p in root.rglob(nombre) if "__pycache__" not in str(p)]
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
        msg = mensaje.lower()
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
