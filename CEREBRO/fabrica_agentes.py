# -*- coding: utf-8 -*-
"""
FÁBRICA DE AGENTES — AURORA crea y usa agentes de tarea, con el contexto que Anuar
le da en el chat (pregunta-antes-de-crear). Así no se rompe nada: el humano aporta
el contexto que la máquina no tiene. Evolución de la Fábrica de motores.

Un 'agente' = una tarea con objetivo + contexto + qué hacer con el resultado, que se
puede correr a demanda. Los specs se guardan REALES en disco (AGENTES/*.json).
Bajo autorización de Anuar, como toda la Fábrica.
"""
from __future__ import annotations
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTES_DIR = ROOT / "AGENTES"


def _slug(nombre: str) -> str:
    n = unicodedata.normalize("NFD", (nombre or "").lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    return n or "agente"


def crear_agente(nombre: str, objetivo: str, contexto: str = "") -> dict:
    """Guarda un agente REAL en disco. Devuelve su ficha."""
    AGENTES_DIR.mkdir(exist_ok=True)
    slug = _slug(nombre)
    spec = {
        "slug": slug,
        "nombre": nombre.strip() or slug,
        "objetivo": objetivo.strip(),
        "contexto": contexto.strip(),
        "activo": True,
        "creado": datetime.now().isoformat(timespec="seconds"),
        "ejecuciones": 0,
    }
    (AGENTES_DIR / f"{slug}.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "creado", "agente": spec}


def listar_agentes() -> dict:
    if not AGENTES_DIR.exists():
        return {"status": "ok", "total": 0, "agentes": []}
    ags = []
    for f in sorted(AGENTES_DIR.glob("*.json")):
        try:
            ags.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return {"status": "ok", "total": len(ags), "agentes": ags}


def obtener_agente(nombre: str) -> dict | None:
    slug = _slug(nombre)
    f = AGENTES_DIR / f"{slug}.json"
    if f.is_file():
        return json.loads(f.read_text(encoding="utf-8"))
    # búsqueda laxa por nombre contenido
    for g in listar_agentes()["agentes"]:
        if slug in g.get("slug", "") or _slug(g.get("nombre", "")) in slug:
            return g
    return None


def marcar_ejecucion(slug: str) -> None:
    f = AGENTES_DIR / f"{_slug(slug)}.json"
    if f.is_file():
        try:
            spec = json.loads(f.read_text(encoding="utf-8"))
            spec["ejecuciones"] = spec.get("ejecuciones", 0) + 1
            spec["ultima_ejecucion"] = datetime.now().isoformat(timespec="seconds")
            f.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


def eliminar_agente(nombre: str) -> dict:
    f = AGENTES_DIR / f"{_slug(nombre)}.json"
    if f.is_file():
        f.unlink()
        return {"status": "eliminado", "nombre": nombre}
    return {"status": "no_encontrado", "nombre": nombre}


def prompt_ejecucion(spec: dict, extra_ctx: str = "") -> str:
    """Arma el prompt para que el cerebro EJECUTE el agente con su contexto real."""
    p = [f"Eres el agente '{spec.get('nombre')}' de AURORA, creado por Anuar.",
         f"OBJETIVO: {spec.get('objetivo')}"]
    if spec.get("contexto"):
        p.append(f"CONTEXTO que te dio Anuar: {spec['contexto']}")
    if extra_ctx:
        p.append(f"DATOS REALES disponibles: {extra_ctx}")
    p.append("Cumple el objetivo con lo que tienes. Sé concreto y honesto: si te falta un "
             "dato real, dilo en vez de inventarlo. Responde en español, directo.")
    return "\n".join(p)
