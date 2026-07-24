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
    "listar", "obtener", "consultar", "buscar", "ver", "leer", "resumen", "resumir",
    "calcular", "cotizar", "analizar", "comparar", "contar", "estado", "diagnostic",
    "info", "detalle", "catalogo", "catálogo", "existe", "es_", "hay_", "tiene_",
    "total", "listado", "reporte", "revisar", "validar", "verificar_credenciales",
    "descubrir", "nichos", "playbook", "conocimiento", "mejores_", "prompt_",
    "construir_brief", "post_de_hoy", "racha", "dia", "proximas", "ficha", "fichas",
    "tecnicas", "precios", "plan", "sugerencia", "perfil", "historial",
)


def _es_peligrosa(nombre: str) -> bool:
    """True si NO se reconoce como lectura pura → se pide confirmación antes de correr."""
    n = _norm(nombre)
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
            # AUTOMATIONS = demos viejos NEXUS que SIMULAN datos (precio $450 fijo, "ingresos"
            # inventados, "publica" sin publicar). Fuera del registro para que el chat NUNCA
            # los invoque y engañe. Los archivos se conservan; se reconstruirán REALES si se pide.
            if "AUTOMATIONS" in py.parts:
                continue
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
            import asyncio
            res = asyncio.get_event_loop().run_until_complete(res)
        return {"status": "ok", "resultado": res}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:300]}


if __name__ == "__main__":
    r = descubrir()
    print("Herramientas descubiertas:", len(r))
    for c in list(r)[:15]:
        print("  ", c, "->", r[c]["doc"][:60])
