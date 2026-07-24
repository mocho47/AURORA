# -*- coding: utf-8 -*-
"""
AURORA · CONSOLA DE MOTORES (la visión "cartuchos" hecha panel)
Anuar activa/desactiva/agrupa cartuchos y guarda LOADOUTS (perfiles), sin tocar código.
- Cartuchos CORE (dashboard, chat, bus, memoria, la consola) no se apagan: son el chasis.
- Desactivar un cartucho lo OCULTA del panel (no rompe el servidor; la ruta sigue viva pero
  fuera de la vista). Es reversible al instante.
- Loadouts = perfiles ("modo Taller", "modo Marketing"): un clic cambia qué cartuchos ves.
Estado persistido en CONFIG/consola_motores.json.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "CONFIG" / "consola_motores.json"

# Manifiesto de cartuchos. 'tab' = id de la pestaña del panel. core=True no se puede apagar.
CARTUCHOS = [
    # Núcleo (chasis)
    {"id": "dash",         "nombre": "Dashboard",            "icono": "◈", "grupo": "Núcleo",       "core": True,  "desc": "Vista general y salud del sistema."},
    {"id": "chat",         "nombre": "Chat AURORA",          "icono": "◉", "grupo": "Núcleo",       "core": True,  "desc": "Conversación con el bus neuronal."},
    {"id": "bus",          "nombre": "Bus Neuronal",         "icono": "◈", "grupo": "Núcleo",       "core": True,  "desc": "Motores registrados en el bus."},
    {"id": "memoria",      "nombre": "Memoria",              "icono": "◉", "grupo": "Núcleo",       "core": True,  "desc": "Memoria persistente de AURORA."},
    # Taller
    {"id": "taller",       "nombre": "Órdenes Taller",       "icono": "◧", "grupo": "Taller",       "core": False, "desc": "Órdenes de trabajo, cotizador, imágenes, alertas."},
    {"id": "tprecios",     "nombre": "Precios y Cotizar",    "icono": "$", "grupo": "Taller",       "core": False, "desc": "Materiales/costos + cotizar prendas y láser."},
    {"id": "contabilidad", "nombre": "Contabilidad",         "icono": "▦", "grupo": "Taller",       "core": False, "desc": "Balance mensual real de tus órdenes."},
    {"id": "agenda",       "nombre": "Agenda / Citas",       "icono": "📅", "grupo": "Taller",       "core": False, "desc": "Instalaciones, entregas y citas (.ics)."},
    {"id": "inventario",   "nombre": "Inventario",           "icono": "📦", "grupo": "Taller",       "core": False, "desc": "Existencias, movimientos y alertas de stock."},
    # Ventas
    {"id": "crm",          "nombre": "CRM · Leads",          "icono": "◎", "grupo": "Ventas",       "core": False, "desc": "Leads capturados (Oracle CRM)."},
    {"id": "vendedor",     "nombre": "Vendedor · Fichas",    "icono": "◆", "grupo": "Ventas",       "core": False, "desc": "Fichas técnicas + técnicas de venta."},
    {"id": "seguimiento",  "nombre": "Ventas · Seguimiento", "icono": "🎯", "grupo": "Ventas",       "core": False, "desc": "Embudo leads→ventas + seguimiento WhatsApp."},
    {"id": "reportes",     "nombre": "Reportes / BI",        "icono": "📈", "grupo": "Ventas",       "core": False, "desc": "KPIs, márgenes y oportunidades del taller."},
    # Marketing
    {"id": "marketing",    "nombre": "Marketing IA",         "icono": "◔", "grupo": "Marketing",    "core": False, "desc": "Contenido con algoritmo real + IA."},
    {"id": "monetiza",     "nombre": "Monetización",         "icono": "◉", "grupo": "Marketing",    "core": False, "desc": "El post del día, plan a 1 año, racha."},
    {"id": "mercado",      "nombre": "Analizador de Mercado","icono": "📊", "grupo": "Marketing",    "core": False, "desc": "Tendencias, competencia y precios (web + IA)."},
    {"id": "social",       "nombre": "Redes Sociales",       "icono": "📅", "grupo": "Marketing",    "core": False, "desc": "Agenda multi-cuenta + estado de conexiones."},
    {"id": "redes",        "nombre": "Redes · Publicador",   "icono": "◕", "grupo": "Marketing",    "core": False, "desc": "Estado de redes + publicar (tú apruebas)."},
    # Diseño
    {"id": "editor",       "nombre": "Editor · Herramientas","icono": "✎", "grupo": "Diseño",       "core": False, "desc": "Convertir, escalar, planillas, B&N, línea, IA."},
    # Conocimiento
    {"id": "biblioteca",   "nombre": "Biblioteca",           "icono": "▤", "grupo": "Conocimiento", "core": False, "desc": "Manuales y PDFs que AURORA consulta."},
    {"id": "web",          "nombre": "Web en vivo",          "icono": "◍", "grupo": "Conocimiento", "core": False, "desc": "Búsqueda y navegación real en vivo."},
    # Sistema
    {"id": "sistema",      "nombre": "Sistema · PC",         "icono": "⚙", "grupo": "Sistema",      "core": False, "desc": "Diagnóstico y optimización del equipo."},
    {"id": "red",          "nombre": "Red · Dispositivos",   "icono": "⛁", "grupo": "Sistema",      "core": False, "desc": "Escanea/diagnostica dispositivos de la red."},
    {"id": "pc",           "nombre": "PC · Control",         "icono": "▣", "grupo": "Sistema",      "core": False, "desc": "Control del equipo (blindado con PIN)."},
    {"id": "cerebro",      "nombre": "Cerebro (autónomos)",  "icono": "🧠", "grupo": "Sistema",      "core": False, "desc": "Estado de autoconocimiento, sueño, reparación y voz."},

    # ── Pestañas que existían en el panel pero NO estaban declaradas aquí ──
    {"id": "consola",      "nombre": "Consola de Motores",   "icono": "🎛", "grupo": "Núcleo",       "core": True,  "desc": "Este panel: enciende/apaga cartuchos y guarda loadouts."},
    {"id": "codigo",       "nombre": "Código · IDE",         "icono": "🧩", "grupo": "Sistema",      "core": False, "desc": "Editor del sistema con respaldo, chequeo de sintaxis y PIN."},
    {"id": "fabrica",      "nombre": "Fábrica de Motores",   "icono": "🏭", "grupo": "Sistema",      "core": False, "desc": "Crea cartuchos nuevos (exclusivo del dueño, con PIN)."},
    {"id": "razonar",      "nombre": "Razonar (profundo)",   "icono": "🧠", "grupo": "Conocimiento", "core": False, "desc": "Razonamiento profundo con el cerebro grande."},
    {"id": "taza",         "nombre": "Plantillas de Taza",   "icono": "🎨", "grupo": "Diseño",       "core": False, "desc": "Generador de fondos para sublimación de tazas."},

    # ── Motores del Bus (cerebro): sin pestaña propia; los invoca el chat/bus.
    #    'motor' = nombre real en el registrador. Toggle REAL: si se apaga, el bus lo salta al reiniciar.
    {"id": "m_reasoning",  "nombre": "Razonamiento",         "icono": "🧠", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_reasoning",   "desc": "Motor de razonamiento profundo. (aplica al reiniciar)"},
    {"id": "m_codegen",    "nombre": "Generador de código",  "icono": "⌨", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_code_gen",   "desc": "Genera y corrige código. (aplica al reiniciar)"},
    {"id": "m_negocios",   "nombre": "Consultor de negocios","icono": "📈", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_negocios",   "desc": "Estrategia y consultoría de negocio. (aplica al reiniciar)"},
    {"id": "m_analisis",   "nombre": "Análisis",             "icono": "🔬", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_analisis",   "desc": "Análisis de datos y texto. (aplica al reiniciar)"},
    {"id": "m_imagenes",   "nombre": "Análisis de imágenes", "icono": "🖼", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_imagenes",   "desc": "Interpreta imágenes. (aplica al reiniciar)"},
    {"id": "m_coaching",   "nombre": "Coaching",             "icono": "🎯", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_coaching",   "desc": "Coaching y motivación. (aplica al reiniciar)"},
    {"id": "m_ventas",     "nombre": "Motor de ventas",      "icono": "💼", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_ventas",     "desc": "Lógica de ventas del bus. (aplica al reiniciar)"},
    {"id": "m_cotizador",  "nombre": "Cotizador (motor)",    "icono": "🧮", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_cotizador",  "desc": "Motor de cotización del bus. (aplica al reiniciar)"},
    {"id": "m_verificador","nombre": "Verificador",          "icono": "✔", "grupo": "Inteligencia (Bus)", "core": True,  "bus": True, "motor": "verificador_core", "desc": "Verifica hechos/coherencia. Activo en el bus."},
    {"id": "m_sublimacion","nombre": "Sublimación",          "icono": "🖨", "grupo": "Inteligencia (Bus)", "core": True,  "bus": True, "motor": "sublimacion_core", "desc": "Conocimiento de sublimación. Activo en el bus."},
    {"id": "m_voz",        "nombre": "Voz (Google)",         "icono": "🔊", "grupo": "Canales (Bus)",      "core": True,  "bus": True, "motor": "voz_google",       "desc": "Síntesis de voz. Activo en el bus."},
    {"id": "m_telegram",   "nombre": "Telegram",             "icono": "✈", "grupo": "Canales (Bus)",      "core": True,  "bus": True, "motor": "telegram",         "desc": "Canal Telegram. Activo en el bus."},
    {"id": "m_email",      "nombre": "Email",                "icono": "✉", "grupo": "Canales (Bus)",      "core": True,  "bus": True, "motor": "email",            "desc": "Canal Email. Activo en el bus."},
    {"id": "m_autoconoc",  "nombre": "Auto-conocimiento",    "icono": "🧩", "grupo": "Autónomos (Bus)",    "core": True,  "bus": True, "motor": "auto_conocimiento","desc": "AURORA se auto-inventaría. Activo en el bus."},
    # Autónomos críticos = núcleo (no se apagan para no dañar el sistema)
    {"id": "m_sueno",      "nombre": "Consolidación (sueño)","icono": "🌙", "grupo": "Autónomos (Bus)",    "core": True,  "bus": True, "motor": "motor_sueno",      "desc": "Consolida memoria en segundo plano. Núcleo."},
    {"id": "m_autorep",    "nombre": "Auto-reparación",      "icono": "🛠", "grupo": "Autónomos (Bus)",    "core": True,  "bus": True, "motor": "auto_reparacion",  "desc": "Se auto-repara ante fallos. Núcleo."},

    # ── MOTORES DE NEGOCIO del bus: estaban CARGADOS pero invisibles en la consola.
    #    Son los que mueven dinero real (taller, CRM, vendedor, publicación, WhatsApp).
    {"id": "m_taller",     "nombre": "Taller (motor)",       "icono": "◧", "grupo": "Negocio (Bus)",      "core": True,  "bus": True, "motor": "taller_core",        "desc": "Vectores/DXF y lógica del taller. Núcleo del negocio."},
    {"id": "m_oraclecore", "nombre": "CRM Oracle (motor)",   "icono": "◎", "grupo": "Negocio (Bus)",      "core": True,  "bus": True, "motor": "oracle_core",        "desc": "Leads, órdenes y relación lead↔orden. Núcleo del negocio."},
    {"id": "m_oracle",     "nombre": "Oracle (consultas)",   "icono": "🔮", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "motor_oracle",       "desc": "Consultas del CRM desde el bus."},
    {"id": "m_vendedor",   "nombre": "Vendedor (motor)",     "icono": "◆", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "vendedor_core",      "desc": "Fichas técnicas y pitch de venta."},
    {"id": "m_publicador", "nombre": "Publicador (motor)",   "icono": "◕", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "publicador_core",    "desc": "Publica en redes (FB/IG) y videos."},
    {"id": "m_marketing",  "nombre": "Marketing (motor)",    "icono": "◔", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "motor_marketing",    "desc": "Generación de contenido con IA."},
    {"id": "m_asesormkt",  "nombre": "Asesor de Marketing",  "icono": "📣", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "asesor_marketing",   "desc": "Estrategia y plan de marketing."},
    {"id": "m_analitica",  "nombre": "Analítica Marketing",  "icono": "📊", "grupo": "Negocio (Bus)",      "core": False, "bus": True, "motor": "analitica_marketing","desc": "Métricas y desempeño de contenido."},
    {"id": "m_coachneg",   "nombre": "Coaching de negocios", "icono": "💼", "grupo": "Inteligencia (Bus)", "core": False, "bus": True, "motor": "motor_coaching_real","desc": "Coach transformacional de negocio (creencias y metas)."},
    {"id": "m_whatsapp",   "nombre": "WhatsApp",             "icono": "💬", "grupo": "Canales (Bus)",      "core": True,  "bus": True, "motor": "whatsapp",           "desc": "Canal WhatsApp (Green API). Activo en el bus."},
    {"id": "m_memoria",    "nombre": "Memoria (motor)",      "icono": "🧠", "grupo": "Autónomos (Bus)",    "core": True,  "bus": True, "motor": "sistema_memoria",    "desc": "Memoria persistente del sistema. Núcleo."},
]

_IDS = {c["id"] for c in CARTUCHOS}
_APAGABLES = {c["id"] for c in CARTUCHOS if not c["core"]}


def _load() -> dict:
    if STATE.exists():
        try:
            d = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            d = {}
    else:
        d = {}
    d.setdefault("desactivados", [])
    d.setdefault("loadouts", {})
    # limpia ids que ya no existen o que son core (nunca se apagan)
    d["desactivados"] = [i for i in d["desactivados"] if i in _APAGABLES]
    return d


def _save(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def estado() -> dict:
    """Lista los cartuchos con su estado (activo/apagado), agrupados."""
    d = _load()
    off = set(d["desactivados"])
    items = [{**c, "activo": c["id"] not in off} for c in CARTUCHOS]
    grupos: dict = {}
    for c in items:
        grupos.setdefault(c["grupo"], []).append(c)
    return {"status": "ok", "cartuchos": items, "grupos": grupos,
            "desactivados": sorted(off), "total": len(items),
            "activos": sum(1 for c in items if c["activo"]),
            "loadouts": sorted(d["loadouts"].keys())}


def toggle(cid: str, activo: bool) -> dict:
    """Prende/apaga un cartucho. Los CORE no se pueden apagar."""
    if cid not in _IDS:
        return {"status": "error", "detalle": f"Cartucho '{cid}' no existe."}
    if cid not in _APAGABLES and not activo:
        return {"status": "error", "detalle": f"'{cid}' es núcleo: no se puede apagar."}
    d = _load()
    off = set(d["desactivados"])
    off.discard(cid) if activo else off.add(cid)
    d["desactivados"] = sorted(off & _APAGABLES)
    _save(d)
    return {"status": "ok", "id": cid, "activo": activo, "desactivados": d["desactivados"]}


def listar_loadouts() -> dict:
    d = _load()
    return {"status": "ok", "loadouts": d["loadouts"]}


def guardar_loadout(nombre: str, activos: list) -> dict:
    """Guarda un perfil: la lista de cartuchos que deben quedar ACTIVOS."""
    nombre = (nombre or "").strip()
    if not nombre:
        return {"status": "error", "detalle": "Ponle un nombre al loadout."}
    activos_validos = [i for i in (activos or []) if i in _IDS]
    d = _load()
    d["loadouts"][nombre] = activos_validos
    _save(d)
    return {"status": "ok", "nombre": nombre, "activos": activos_validos}


def aplicar_loadout(nombre: str) -> dict:
    """Aplica un perfil: apaga todo lo apagable que NO esté en la lista del loadout."""
    d = _load()
    if nombre not in d["loadouts"]:
        return {"status": "no_encontrado", "detalle": f"No existe el loadout '{nombre}'."}
    activos = set(d["loadouts"][nombre]) | {c["id"] for c in CARTUCHOS if c["core"]}
    d["desactivados"] = sorted(i for i in _APAGABLES if i not in activos)
    _save(d)
    return {"status": "ok", "nombre": nombre, **estado()}


def motores_desactivados_bus() -> set:
    """
    Nombres REALES de motores del bus que Anuar apagó (para que el registrador los salte).
    Solo aplica a cartuchos 'bus' apagables; los núcleo nunca entran aquí.
    """
    d = _load()
    off = set(d["desactivados"])
    return {c["motor"] for c in CARTUCHOS
            if c.get("bus") and not c.get("core") and c["id"] in off and c.get("motor")}


def eliminar_loadout(nombre: str) -> dict:
    d = _load()
    if nombre in d["loadouts"]:
        del d["loadouts"][nombre]
        _save(d)
        return {"status": "ok", "eliminado": nombre}
    return {"status": "no_encontrado", "nombre": nombre}
