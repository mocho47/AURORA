# -*- coding: utf-8 -*-
"""
AURORA · ANALIZADOR DE MERCADO MULTI-NICHO (cartucho MARKETING)

Investiga el mercado REAL de cada nicho del taller de Anuar usando búsqueda web
en vivo (cartucho WEB/web_real) y resume con IA (Groq). Regla de oro (Anuar):
0 simulaciones. El LLM SOLO puede usar los extractos web reales que se le pasan;
si un dato no aparece en la web, se reporta honesto ("no visto en las fuentes").

Nichos: retrofit de faros (ATF), corte/grabado láser (Milens), sublimación,
DTF/prendas.

Self-contained: carga sus dependencias por ruta (importlib), no importa nada del
servidor. Cartucho ausente/roto no debe tumbar AURORA.
"""
from __future__ import annotations
import os
import re
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # C:\AURORA.worktrees

# ------------------------------------------------------------------ nichos ----
NICHOS = {
    "retrofit_faros": {
        "nombre": "Retrofit de faros (ATF)",
        "descripcion": "Instalación de proyectores Bi-LED/láser en faros de auto, "
                       "morphose/retrofit, mejora de luz para ver de noche.",
        "consultas": [
            "retrofit faros bi-led proyector auto precio México",
            "instalación bi-led morphose faros taller México",
            "kit bi-led lente proyector faros precio 2026",
        ],
    },
    "laser": {
        "nombre": "Corte y grabado láser (Milens)",
        "descripcion": "Corte y grabado láser CO2 en MDF, acrílico y madera: cajas, "
                       "souvenirs, letreros, artículos personalizados.",
        "consultas": [
            "corte grabado láser MDF acrílico personalizado precio México",
            "cajas MDF grabado láser souvenirs boda precio México",
            "servicio corte láser acrílico letrero precio México 2026",
        ],
    },
    "sublimacion": {
        "nombre": "Sublimación",
        "descripcion": "Sublimación en tazas, playeras, termos, mousepads y artículos "
                       "personalizados por transferencia de tinta a poliéster.",
        "consultas": [
            "sublimación tazas termos personalizados precio México",
            "playera sublimada full print precio negocio México",
            "sublimación productos más vendidos tendencia México 2026",
        ],
    },
    "dtf_prendas": {
        "nombre": "DTF / Prendas",
        "descripcion": "Impresión DTF (Direct To Film) y estampado en playeras, "
                       "sudaderas y prendas de algodón/mezcla.",
        "consultas": [
            "impresión DTF playeras precio México",
            "estampado DTF sudadera personalizada precio negocio México",
            "DTF vs serigrafía tendencia prendas México 2026",
        ],
    },
}


# ---------------------------------------------------------------- helpers ----
def _mod(nombre: str, ruta: Path):
    """Carga un módulo por ruta absoluta (patrón del proyecto)."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _web():
    return _mod("web_real", ROOT / "WEB" / "web_real.py")


# regex de precios en MXN vistos en los extractos ($1,234.56 / 1 234 pesos / MXN 900)
_RE_PRECIO = re.compile(
    r"(?:\$|MXN\s*|mx\$\s*)\s?(\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?)"
    r"|(\d{2,3}(?:[.,]\d{3})*)\s?(?:pesos|mxn)",
    re.IGNORECASE,
)


def _num(s: str):
    """Normaliza un texto de precio a float MXN (o None si es basura)."""
    if not s:
        return None
    s = s.replace(" ", "")
    # decide separador decimal: si hay coma y punto, el último es decimal
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # coma como miles si 3 dígitos después, si no decimal
        s = s.replace(",", "") if re.search(r",\d{3}\b", s) else s.replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    # filtra ruido: precios de taller MXN plausibles
    if v < 5 or v > 500000:
        return None
    return v


def _extraer_precios(texto: str) -> list:
    vals = []
    for m in _RE_PRECIO.finditer(texto or ""):
        v = _num(m.group(1) or m.group(2))
        if v is not None:
            vals.append(v)
    return vals


def _groq(prompt: str, temperature: float = 0.4) -> dict:
    """Llama a Groq (patrón plan_monetizacion.copy_borrador). Devuelve texto o error."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return {"status": "sin_llm", "detalle": "Falta GROQ_API_KEY en .env."}
    try:
        import requests
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "openai/gpt-oss-20b",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": temperature},
            timeout=40,
        )
        if not r.ok:
            return {"status": "error", "detalle": f"Groq HTTP {r.status_code}: {r.text[:180]}"}
        return {"status": "ok", "texto": r.json()["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


# ------------------------------------------------------------------ API -------
def nichos() -> dict:
    """Nichos disponibles para analizar (para poblar el panel)."""
    return {"status": "ok",
            "nichos": {k: {"nombre": v["nombre"], "descripcion": v["descripcion"]}
                       for k, v in NICHOS.items()}}


def analizar(nicho: str) -> dict:
    """
    Análisis de mercado REAL de un nicho: busca en vivo (varias consultas),
    junta los extractos reales y los resume con Groq (tendencias, competidores,
    rango de precios visto, oportunidades). El LLM SOLO usa los extractos reales.
    """
    clave = (nicho or "").lower().strip()
    if not clave:
        return {"status": "error", "detalle": "Escribe un nicho o tema a analizar."}
    n = NICHOS.get(clave)
    if not n:
        # NICHO LIBRE: cualquier tema/mercado que Anuar quiera explorar (no solo sus negocios).
        # Se arman consultas web genéricas a partir del texto; el resto del análisis es idéntico.
        t = nicho.strip()
        n = {"nombre": t,
             "descripcion": f"Mercado explorado libremente: {t}",
             "consultas": [
                 f"{t} precio México 2026",
                 f"{t} negocio rentable México",
                 f"cuánto cuesta {t} Guadalajara",
                 f"{t} competencia proveedores México",
                 f"{t} tendencia demanda mercado",
             ]}

    web = _web()
    fuentes, extractos, precios = [], [], []
    vistos = set()
    fallos = []
    for q in n["consultas"]:
        r = web.buscar(q, n=6, region="mx-es")
        if r.get("status") != "ok":
            fallos.append({"consulta": q, "mensaje": r.get("mensaje")})
            continue
        for it in r.get("resultados", []):
            url = it.get("url", "")
            extracto = (it.get("extracto") or "").strip()
            if not extracto or url in vistos:
                continue
            vistos.add(url)
            fuentes.append({"titulo": it.get("titulo", ""), "url": url,
                            "dominio": it.get("dominio", "")})
            extractos.append(f"- {it.get('titulo','')} ({it.get('dominio','')}): {extracto}")
            precios += _extraer_precios(extracto)

    if not extractos:
        return {"status": "sin_datos", "nicho": n["nombre"],
                "detalle": "La búsqueda web no devolvió extractos usables ahora mismo.",
                "fallos": fallos}

    contexto = "\n".join(extractos[:18])
    precios_ord = sorted(set(round(p) for p in precios))
    prompt = (
        f"Eres analista de mercado para un taller en Guadalajara, México. "
        f"Nicho: {n['nombre']} — {n['descripcion']}.\n"
        f"A continuación tienes EXTRACTOS REALES de resultados de búsqueda web de HOY. "
        f"REGLA ESTRICTA: básate ÚNICAMENTE en estos extractos. NO inventes precios, "
        f"marcas ni datos. Si algo no aparece en los extractos, escribe explícitamente "
        f"'no visto en las fuentes'.\n\n"
        f"EXTRACTOS:\n{contexto}\n\n"
        f"Responde en español mexicano, en JSON con estas claves: "
        f"tendencias (lista), competidores (lista de nombres/tipos vistos), "
        f"rango_precios (texto con lo observado en las fuentes), "
        f"oportunidades (lista de ideas accionables para el taller). "
        f"Solo el JSON."
    )
    ia = _groq(prompt, temperature=0.4)

    resultado = {
        "status": "ok",
        "nicho": n["nombre"],
        "nicho_clave": clave,
        "fuentes": [f["url"] for f in fuentes],
        "fuentes_detalle": fuentes,
        "precios_detectados_mxn": precios_ord,
        "consultas_usadas": n["consultas"],
    }
    if ia.get("status") == "ok":
        resultado["analisis"] = ia["texto"]
    else:
        resultado["status"] = "ok_sin_ia"
        resultado["analisis"] = None
        resultado["ia_error"] = ia.get("detalle") or ia.get("status")
    if fallos:
        resultado["fallos_busqueda"] = fallos
    return resultado


def comparar_precios(producto: str) -> dict:
    """
    Busca un producto en la web (MX) y devuelve los precios/rangos REALES detectados
    en los extractos, con sus fuentes. Nada inventado: si no hay precios, lo dice.
    """
    prod = (producto or "").strip()
    if not prod:
        return {"status": "error", "detalle": "Producto vacío."}

    web = _web()
    r = web.buscar(f"{prod} precio México", n=8, region="mx-es")
    if r.get("status") != "ok":
        return {"status": "error", "producto": prod,
                "detalle": f"Búsqueda falló: {r.get('mensaje')}"}

    hallazgos, todos = [], []
    for it in r.get("resultados", []):
        extracto = it.get("extracto") or ""
        precios = _extraer_precios(extracto)
        if precios:
            todos += precios
            hallazgos.append({
                "titulo": it.get("titulo", ""),
                "dominio": it.get("dominio", ""),
                "url": it.get("url", ""),
                "precios_mxn": sorted(set(round(p) for p in precios)),
                "extracto": extracto[:220],
            })

    if not todos:
        return {"status": "sin_precios", "producto": prod,
                "detalle": "No se detectaron precios en los extractos de la web ahora mismo.",
                "fuentes": [{"titulo": it.get("titulo", ""), "url": it.get("url", "")}
                            for it in r.get("resultados", [])[:6]]}

    return {
        "status": "ok",
        "producto": prod,
        "rango_mxn": {"min": round(min(todos)), "max": round(max(todos)),
                      "promedio": round(sum(todos) / len(todos))},
        "muestras": len(todos),
        "hallazgos": hallazgos,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) >= 3 and sys.argv[1] == "precio":
        print(json.dumps(comparar_precios(" ".join(sys.argv[2:])), ensure_ascii=False, indent=2))
    else:
        arg = sys.argv[1] if len(sys.argv) > 1 else "laser"
        print(json.dumps(analizar(arg), ensure_ascii=False, indent=2))
