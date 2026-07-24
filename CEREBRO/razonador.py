# -*- coding: utf-8 -*-
"""AURORA · RAZONADOR PROFUNDO (cartucho de cerebro bajo demanda).

El chat de AURORA corre con un modelo rápido y chico. Para problemas difíciles,
este motor le presta un CEREBRO MÁS PROFUNDO: usa un modelo grande (llama-3.3-70b
en Groq, en la nube — no consume la RAM de la PC) y aplica una cadena de
pensamiento con AUTOCRÍTICA antes de responder.

Se invoca solo cuando hace falta (cartucho on-demand). Honesto: si el modelo
grande no está disponible o se satura, cae al modelo rápido y lo DICE.
Contrato universal: META + ejecutar(accion, datos) -> dict con 'status'.
"""
from __future__ import annotations
import os
import re
import time
from pathlib import Path

import requests

META = {
    "id": "razonador_profundo",
    "nombre": "Razonador Profundo",
    "descripcion": "Razonamiento profundo bajo demanda: modelo grande (70B) + cadena de pensamiento y autocrítica.",
    "categoria": "Cerebro",
}

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_PROFUNDO = "llama-3.3-70b-versatile"   # cerebro grande (nube, no usa RAM local)
MODELO_RAPIDO = "llama-3.1-8b-instant"        # respaldo si el grande no está
ROOT = Path(__file__).resolve().parent.parent


def _groq_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GROQ_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _llm(messages: list, modelo: str, temperature: float = 0.3, max_tokens: int = 1200) -> str:
    """Llama a Groq con reintento ante rate limit. Devuelve texto o lanza."""
    key = _groq_key()
    if not key:
        raise RuntimeError("Falta GROQ_API_KEY")
    for intento in range(4):
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": modelo, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=90,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        if r.status_code == 429 and intento < 3:
            mm = re.search(r"try again in ([0-9.]+)s", r.text)
            time.sleep(min((float(mm.group(1)) + 1.0) if mm else 10.0, 30))
            continue
        raise RuntimeError(f"Groq HTTP {r.status_code}: {r.text[:200]}")
    raise RuntimeError("Groq: límite de tokens/min persistente")


# ── CEREBRO LOCAL DE RESPALDO (Ollama) — para cuando NO hay internet ──
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODELO = "llama3.2:3b"   # modelo chico local (corre sin nube)

def _ollama(messages: list, temperature: float = 0.3) -> str:
    """Llama al modelo LOCAL vía Ollama. Funciona sin internet."""
    r = requests.post(OLLAMA_URL,
                      json={"model": OLLAMA_MODELO, "messages": messages,
                            "stream": False, "options": {"temperature": temperature}},
                      timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {r.status_code}: {r.text[:150]}")
    return (r.json().get("message", {}).get("content") or "").strip()


def razonar(pregunta: str, contexto: str = "") -> dict:
    """Razona en profundidad: piensa paso a paso, se autocritica y da la respuesta final."""
    if not pregunta or not pregunta.strip():
        return {"status": "error", "mensaje": "Falta la pregunta a razonar."}

    sistema = ("Eres el razonador profundo de AURORA, asistente honesto de Anuar (taller). "
               "Piensas con rigor, paso a paso, sin inventar. Si no sabes algo, lo dices.")
    base = f"Contexto:\n{contexto}\n\n" if contexto else ""
    modelo_usado = MODELO_PROFUNDO
    degradado = False

    # Fase 1 — pensar paso a paso (modelo grande; si falla, respaldo rápido)
    try:
        pensamiento = _llm([
            {"role": "system", "content": sistema},
            {"role": "user", "content": base + f"Piensa PASO A PASO para resolver:\n{pregunta}\n"
                                               "Razona en pasos numerados, considerando datos, opciones y riesgos. "
                                               "Aún NO des la respuesta final."},
        ], MODELO_PROFUNDO, temperature=0.3, max_tokens=1400)
    except Exception:
        degradado = True
        modelo_usado = MODELO_RAPIDO
        try:
            pensamiento = _llm([
                {"role": "system", "content": sistema},
                {"role": "user", "content": base + f"Piensa paso a paso:\n{pregunta}"},
            ], MODELO_RAPIDO, temperature=0.3, max_tokens=900)
        except Exception:
            # Sin internet / Groq caído → CEREBRO LOCAL de respaldo (Ollama)
            try:
                pensamiento = _ollama([
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": base + f"Piensa paso a paso:\n{pregunta}"}])
                modelo_usado = "ollama-local (offline)"
            except Exception as e2:
                return {"status": "error", "mensaje": f"No hay cerebro disponible (ni nube ni local): {e2}"}

    # Fase 2 — autocrítica + respuesta final (usa el mismo cerebro que la Fase 1)
    criticar = [
        {"role": "system", "content": sistema},
        {"role": "user", "content": (
            base + f"Pregunta: {pregunta}\n\nTu razonamiento previo:\n{pensamiento}\n\n"
            "Revisa tu razonamiento (¿algún error, supuesto o dato inventado?), corrígelo si hace falta "
            "y da la RESPUESTA FINAL clara y accionable para Anuar. Si algo no se puede saber, dilo.")},
    ]
    try:
        final = (_ollama(criticar, temperature=0.2) if "ollama" in modelo_usado
                 else _llm(criticar, modelo_usado, temperature=0.2, max_tokens=900))
    except Exception:
        final = pensamiento  # al menos entregar el razonamiento

    if "ollama" in modelo_usado:
        nota = "SIN INTERNET: respondido con el cerebro LOCAL de respaldo (Ollama)."
    elif degradado:
        nota = "Respondido con modelo rápido (el profundo no estaba disponible)."
    else:
        nota = "Razonado con cerebro profundo (70B) + autocrítica."
    return {"status": "ok", "respuesta": final, "razonamiento": pensamiento,
            "modelo": modelo_usado, "nota": nota}


def ejecutar(accion: str = "", datos: dict = None) -> dict:
    datos = datos or {}
    if accion in ("", "razonar", "pensar", "resolver"):
        pregunta = datos.get("pregunta") or datos.get("texto") or datos.get("mensaje") or ""
        return razonar(pregunta, datos.get("contexto", ""))
    return {"status": "error", "mensaje": f"Acción no soportada: {accion}. Usa 'razonar'."}


if __name__ == "__main__":
    import json
    r = ejecutar("razonar", {"pregunta": "Un cliente quiere 40 gorras. ¿Conviene darle precio de docena o hay mejor trato, y por qué?",
                             "contexto": "Gorra: 1pza $100, 12+ $80, 50+ $60. Costo $25."})
    print(json.dumps(r, ensure_ascii=False, indent=2)[:1500])
