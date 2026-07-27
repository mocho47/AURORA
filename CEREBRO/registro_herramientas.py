# -*- coding: utf-8 -*-
"""
REGISTRO UNIVERSAL DE HERRAMIENTAS — descubre TODAS las funciones reales de AURORA
(auto, por AST, sin elegir a mano = sin parcialidad) y las expone al cerebro para que
las LLAME de verdad. El chat usa una función real con tus datos, o dice honesto que no
la tiene conectada. NUNCA inventa. Reemplaza los candados a mano por un solo mecanismo
limpio y escalable.

Descubrimiento por AST (no importa nada hasta que se EJECUTA una herramienta → seguro:
ningún efecto secundario por escanear).
"""
from __future__ import annotations
import ast
import importlib.util
import inspect
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Carpetas de CAPACIDADES reales de AURORA (negocio + núcleo). Se excluye lo que NO es
# capacidad operable: el server HTTP, setup, obsoletos, el subsistema viejo, y este mismo.
CARPETAS = [
    "MOTORES", "MARKETING", "PUBLICADOR", "VENDEDOR", "TALLER", "ORACLE", "EDITOR",
    "MEMORIA", "WEB", "BIBLIOTECA", "SISTEMA", "AGENDA", "REDES", "MANUALES",
    "SUBLIMACION", "AUTH", "CEREBRO", "FORJA", "INTEGRACIONES", "CORE",
]
EXCLUIR_ARCHIVOS = {"aurora_server.py", "registro_herramientas.py", "consciencia.py",
                    "registrador_bus.py", "bus_neuronal.py"}
# SEGURIDAD A PRUEBA DE FALLOS: en vez de listar lo peligroso (siempre se escapa algo —
# 'convertir_lead_a_orden', 'registrar_venta', 'editar_ficha' escriben y se colaban),
# se invierte: SOLO es segura la que empieza con un verbo de LECTURA conocido.
# Todo lo demás se trata como que escribe → el chat pide confirmación antes de ejecutar.
_VERBOS_LECTURA = (
    "listar", "obtener", "consultar", "buscar", "leer", "resumen", "resumir",
    "calcular", "cotizar", "analizar", "comparar", "contar", "estado", "diagnostic",
    "info", "detalle", "catalogo", "catálogo", "existe", "es_", "hay_", "tiene_",
    "total", "listado", "reporte", "revisar", "validar", "verificar",
    "descubrir", "nichos", "playbook", "conocimiento", "mejores_", "prompt_",
    "construir_brief", "post_de_hoy", "racha", "dia", "proximas", "ficha", "fichas",
    "tecnicas", "precios", "plan", "sugerencia", "perfil", "historial", "get_",
)
# Aunque el nombre empiece con un verbo de lectura (ej. "diagnosticar_y_reparar_todo"
# empieza como "diagnostic"), si contiene uno de estos verbos de escritura real en
# CUALQUIER parte del nombre, se fuerza peligrosa=True — encontrado real en la
# auditoría de 2026-07-26: esa función sí modifica archivos y pasaba como "lectura".
_VERBOS_FORZAR_PELIGROSA = (
    "reparar", "editar", "eliminar", "borrar", "instalar", "escribir",
    "modificar", "sobrescribir", "actualizar_archivo", "crear_motor",
)


def _es_peligrosa(nombre: str) -> bool:
    """True si NO se reconoce como lectura pura → se pide confirmación antes de correr."""
    n = _norm(nombre)
    if any(v in n for v in _VERBOS_FORZAR_PELIGROSA):
        return True
    return not any(n.startswith(v) or n == v.rstrip("_") for v in _VERBOS_LECTURA)

_REGISTRO: dict = {}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _doc_primera_linea(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    doc = ast.get_docstring(node) or ""
    return doc.strip().split("\n")[0][:180]


def _params(node) -> list:
    out = []
    for a in node.args.args:
        if a.arg in ("self", "cls"):
            continue
        out.append(a.arg)
    return out


def _params_requeridos(node) -> list:
    """Nombres reales sin valor por default — verificar_capacidad_real y router_universal
    los usan para saber si args= tiene lo mínimo antes de ejecutar a ciegas."""
    args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
    n_defaults = len(node.args.defaults)
    return args if n_defaults == 0 else args[:-n_defaults]


def descubrir(refrescar: bool = False) -> dict:
    """Escanea por AST todas las funciones públicas de las carpetas de capacidades."""
    global _REGISTRO
    if _REGISTRO and not refrescar:
        return _REGISTRO
    reg = {}
    for carp in CARPETAS:
        d = ROOT / carp
        if not d.is_dir():
            continue
        for py in d.rglob("*.py"):
            if py.name in EXCLUIR_ARCHIVOS or "__pycache__" in py.parts:
                continue
            # AUTOMATIONS: flujos venta/marketing/sueño — YA REALES (2026-07-24, conectados a
            # cotizador/oracle/Groq/reportes reales, con confirmar=False anti-efectos). Ya se exponen.
            try:
                arbol = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            # 1) funciones a nivel de módulo (llamables directo)
            for node in arbol.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    doc = _doc_primera_linea(node) or f"{node.name.replace('_', ' ')} ({py.stem})"
                    clave = f"{carp}/{py.stem}:{node.name}"
                    reg[clave] = {
                        "modulo": str(py.relative_to(ROOT)),
                        "funcion": node.name,
                        "clase": None,
                        "doc": doc,
                        "params": _params(node),
                        "requeridos": _params_requeridos(node),
                        "peligrosa": _es_peligrosa(node.name),
                    }
                # 2) métodos públicos dentro de clases (los motores son clases)
                elif isinstance(node, ast.ClassDef):
                    for m in node.body:
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_"):
                            doc = _doc_primera_linea(m) or f"{m.name.replace('_', ' ')} ({node.name})"
                            clave = f"{carp}/{py.stem}:{node.name}.{m.name}"
                            reg[clave] = {
                                "modulo": str(py.relative_to(ROOT)),
                                "funcion": m.name,
                                "clase": node.name,
                                "doc": doc,
                                "params": _params(m),
                                "requeridos": _params_requeridos(m),
                                "peligrosa": _es_peligrosa(m.name),
                            }
    _REGISTRO = reg
    return reg


def total() -> int:
    return len(descubrir())


def buscar(query: str, k: int = 8) -> list:
    """Devuelve las herramientas más relevantes al mensaje (match por nombre+doc)."""
    reg = descubrir()
    q = set(_norm(query).split())
    puntuadas = []
    for clave, h in reg.items():
        texto = _norm(h["funcion"].replace("_", " ") + " " + h["doc"] + " " + h["modulo"])
        score = sum(1 for w in q if len(w) > 2 and w in texto)
        # bonus si una palabra del nombre de la función aparece tal cual
        for parte in h["funcion"].split("_"):
            if len(parte) > 3 and _norm(parte) in q:
                score += 2
        if score > 0:
            puntuadas.append((score, clave, h))
    puntuadas.sort(key=lambda x: -x[0])
    return [{"clave": c, **h} for _, c, h in puntuadas[:k]]


def ejecutar(clave: str, kwargs: dict) -> dict:
    """Carga el módulo REAL bajo demanda y ejecuta la función con sus argumentos."""
    reg = descubrir()
    h = reg.get(clave)
    if not h:
        return {"status": "no_existe", "detalle": f"No hay herramienta '{clave}'."}
    ruta = ROOT / h["modulo"]
    try:
        spec = importlib.util.spec_from_file_location(f"tool_{h['funcion']}", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if h.get("clase"):
            # método de clase: instanciar (constructor sin args). Si necesita args, honesto.
            cls = getattr(mod, h["clase"])
            try:
                inst = cls()
            except Exception:
                return {"status": "necesita_contexto",
                        "detalle": f"'{clave}' es método de {h['clase']}, que necesita inicialización con contexto que aún no auto-resuelvo. No lo invento."}
            fn = getattr(inst, h["funcion"])
        else:
            fn = getattr(mod, h["funcion"])
        # solo pasa los kwargs que la función acepta
        firma = inspect.signature(fn)
        validos = {k: v for k, v in (kwargs or {}).items() if k in firma.parameters}
        res = fn(**validos)
        if inspect.iscoroutine(res):
            # ejecutar() siempre corre dentro de un hilo de asyncio.to_thread (nunca en
            # el hilo principal) — asyncio.get_event_loop() truena ahí (Python 3.12+ no
            # crea un loop automático fuera del hilo principal). new_event_loop() sí
            # funciona sin importar desde qué hilo se llame. Mismo bug real que ya se
            # arregló en motor_corel (COM también lo sufría por la misma razón de fondo).
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                res = loop.run_until_complete(res)
            finally:
                loop.close()
        return {"status": "ok", "resultado": res}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:300]}


if __name__ == "__main__":
    r = descubrir()
    print("Herramientas descubiertas:", len(r))
    for c in list(r)[:15]:
        print("  ", c, "->", r[c]["doc"][:60])
