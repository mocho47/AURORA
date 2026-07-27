# -*- coding: utf-8 -*-
"""
Genera MANUALES/manual_comandos_aurora.md a partir del código REAL de
CEREBRO/consciencia.py (los 14 candados directos y sus funciones _es_X) y del
registro real de herramientas (~690 funciones, CEREBRO/registro_herramientas.py).

Nunca se escribe a mano: si un trigger cambia en el código, correr este script
de nuevo regenera el manual y queda al día — mismo problema que ya se vio 3 veces
esta noche con los candados de Corel (el manual a mano se desincroniza apenas
alguien toca un trigger).

Uso:  python CEREBRO/generar_manual.py
"""
from __future__ import annotations
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from CEREBRO import consciencia as _c  # noqa: E402
from CEREBRO import registro_herramientas as _rh  # noqa: E402

SALIDA = ROOT / "MANUALES" / "manual_comandos_aurora.md"

# Candado -> grupo de trabajo real del panel (mismos 6 .nav-group de
# TEMPLATES/panel-completo.html). Se mantiene a mano (solo 14 líneas, no 690)
# porque el nombre del candado no trae el grupo codificado en ningún lado.
_GRUPO = {
    "busqueda_web": "Conocimiento", "corel": "Diseño", "dxf": "Diseño",
    "negocio": "Taller", "publicar": "Marketing", "agenda": "Taller",
    "ficha_vendedor": "Ventas", "intuicion": "Cerebro y Sistema",
    "memoria": "Cerebro y Sistema", "equipos": "Cerebro y Sistema",
    "crear_capacidad": "Cerebro y Sistema", "consulta_codigo": "Cerebro y Sistema",
    "editar_codigo": "Cerebro y Sistema", "accion_fisica": "Cerebro y Sistema",
    "abrir_navegador": "Cerebro y Sistema",
}
_ORDEN_GRUPOS = ["Taller", "Ventas", "Marketing", "Diseño", "Conocimiento", "Cerebro y Sistema"]

_STR_RE = re.compile(r'''["']([^"']{2,60})["']''')
_NOMBRE_CONST_RE = re.compile(r"\b(_[A-Z][A-Z0-9_]*)\b")


def _extraer_triggers(fn) -> list:
    """Frases/triggers reales que reconoce una función _es_X: literales de texto
    en su propio código fuente + cualquier tupla de módulo que referencie
    (ej. _COREL_ACCIONES). No depende de un mapeo a mano por candado."""
    try:
        src = inspect.getsource(fn)
    except Exception:
        return []
    triggers = set()
    for m in _STR_RE.finditer(src):
        s = m.group(1).strip()
        if not s or s.startswith("_") or not any(c.isalpha() for c in s):
            continue
        if len(s.split()) <= 6:  # descarta prosa larga (docstrings, mensajes)
            triggers.add(s)
    for m in _NOMBRE_CONST_RE.finditer(src):
        val = getattr(_c, m.group(1), None)
        if isinstance(val, tuple):
            triggers.update(t for t in val if isinstance(t, str) and len(t.split()) <= 6)
    return sorted(triggers)


def _descripcion_handler(metodo: str) -> str:
    fn = getattr(_c.Consciencia, metodo, None)
    doc = (inspect.getdoc(fn) or "").strip() if fn else ""
    if not doc:
        return "(sin descripción en el código)"
    return doc.split("\n")[0].strip()


def _seccion_candados_directos() -> dict:
    """Agrupa los 14 candados de consciencia.py por grupo de trabajo."""
    por_grupo: dict = {g: [] for g in _ORDEN_GRUPOS}
    for nombre, trigger_fn, metodo, motor_id in _c._CANDADOS:
        grupo = _GRUPO.get(nombre, "Cerebro y Sistema")
        triggers = _extraer_triggers(trigger_fn)
        desc = _descripcion_handler(metodo)
        por_grupo[grupo].append({
            "nombre": nombre, "motor_id": motor_id,
            "descripcion": desc, "triggers": triggers,
        })
    return por_grupo


def _seccion_herramientas_router() -> dict:
    """Agrupa las ~690 herramientas reales del router universal por carpeta
    (el propio 'clave' del registro ya trae el prefijo carpeta/modulo:funcion)."""
    catalogo = _rh.descubrir(refrescar=True)
    por_carpeta: dict = {}
    for clave, meta in catalogo.items():
        carpeta = clave.split("/")[0] if "/" in clave else clave.split(":")[0]
        por_carpeta.setdefault(carpeta, []).append({
            "clave": clave, "doc": (meta.get("doc") or "").split("\n")[0].strip(),
            "params": meta.get("params", []),
        })
    return dict(sorted(por_carpeta.items()))


def generar() -> Path:
    candados = _seccion_candados_directos()
    herramientas = _seccion_herramientas_router()

    partes = [
        "# Manual de comandos reales de AURORA",
        "",
        "Generado automáticamente del código real (no escrito a mano) — si algo cambia en el "
        "código, este manual se regenera corriendo `python CEREBRO/generar_manual.py` y queda "
        "al día. Cada frase de ejemplo listada aquí es una que AURORA reconoce de verdad hoy.",
        "",
        "**Aviso real** (encontrado probando en vivo, 2026-07-27): algunos candados combinan "
        "DOS categorías de frases a la vez (ej. `negocio` necesita una palabra de pregunta "
        "como \"cuánto\"/\"cómo va\" JUNTO CON una palabra de dominio como \"inventario\"/"
        "\"contabilidad\" en el MISMO mensaje; `corel` necesita \"corel\"/\"cdr\" JUNTO CON una "
        "acción como \"exporta\"). Una sola frase suelta de la lista puede no bastar por sí sola "
        "— este generador aún no distingue esa lógica compuesta, es una mejora pendiente.",
        "",
        "**Aviso real 2** (mismo día): dentro de `dxf`, la frase \"vectoriza\"/\"vectorizar\" no "
        "ejecuta directo como las demás (\"convierte a dxf\", \"pásalo a dxf\") — pasa por el "
        "enrutador de IA y pide confirmación aparte antes de correr. Mismo candado, comportamiento "
        "distinto según la frase exacta usada — verificado en vivo, no corregido todavía.",
        "",
        "## Índice por grupo de trabajo (comandos directos)",
        "",
    ]
    total_candados = 0
    for grupo in _ORDEN_GRUPOS:
        items = candados.get(grupo, [])
        if not items:
            continue
        partes.append(f"### {grupo}")
        partes.append("")
        for it in items:
            total_candados += 1
            partes.append(f"**{it['nombre']}** ({it['motor_id']})")
            partes.append(f"- Qué hace: {it['descripcion']}")
            if it["triggers"]:
                ejemplos = ", ".join(f"«{t}»" for t in it["triggers"][:12])
                partes.append(f"- Frases que reconoce: {ejemplos}")
            else:
                partes.append("- Frases que reconoce: (no se detectaron literales — revisar a mano)")
            partes.append("")
        partes.append("")

    partes.append("## Herramientas del enrutador universal (~%d funciones reales)" % sum(len(v) for v in herramientas.values()))
    partes.append("")
    partes.append(
        "Estas no se activan por una frase fija — el enrutador de IA elige la que mejor "
        "responda a lo que pidas, verificando que existan los datos necesarios antes de "
        "ejecutarla de verdad (nunca la adivina a ciegas)."
    )
    partes.append("")
    for carpeta, items in herramientas.items():
        partes.append(f"### {carpeta} ({len(items)})")
        partes.append("")
        for it in items:
            partes.append(f"- `{it['clave']}` — {it['doc'] or '(sin descripción)'}")
        partes.append("")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"Manual generado: {SALIDA} ({total_candados} candados directos, "
          f"{sum(len(v) for v in herramientas.values())} herramientas del router)")
    return SALIDA


if __name__ == "__main__":
    generar()
