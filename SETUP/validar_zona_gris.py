# -*- coding: utf-8 -*-
"""AURORA · ¿La respuesta REALMENTE sirvió, o solo "no se perdió"?

El barrido de cobertura dice a qué candado llegó cada petición, pero no si el
resultado fue el correcto. Eso deja una zona gris: 59 de 81 peticiones las
atendió "otro candado", y eso puede ser un acierto (pides la contabilidad y
responde el candado de negocio) o un error (pides una cosa y te contesta otra).

Anuar preguntó directo: "¿solo llegan correctamente 18?". La respuesta honesta
era "no sé". Esto lo mide: guarda la respuesta COMPLETA de cada petición para
poder juzgarla, en vez de contar solo el nombre del motor.

Correr:  python SETUP/validar_zona_gris.py
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

CHAT = "http://127.0.0.1:5000/chat"
SALIDA = RAIZ / "_CONTEXTO" / "zona_gris.json"

# Motores que NO tienen manos: si contestó uno de estos, no hizo nada real.
SIN_MANOS = {"motor_analisis", "conversacional", "razonador", "sin_herramienta"}

# Señales de que la respuesta fue honesta al no poder (esto NO es una mentira,
# es el comportamiento correcto) — se cuentan aparte de los aciertos.
_HONESTA = (
    "no encontré cómo", "no encontre como", "no puedo", "esto sí lo puedo",
    "esto si lo puedo", "dime qué necesitas", "dime que necesitas",
    "no tengo", "¿cuál", "cual de", "dime cuál", "no quiero adivinar",
)


def preguntar(mensaje: str, timeout: int = 90) -> dict:
    t0 = time.time()
    try:
        r = requests.post(CHAT, json={"mensaje": mensaje, "session_id": "validacion"},
                          timeout=timeout)
        d = r.json()
        return {"respuesta": d.get("respuesta", ""),
                "motores": d.get("motores_usados", []),
                "segundos": round(time.time() - t0, 1)}
    except Exception as e:
        return {"respuesta": f"__ERROR__ {type(e).__name__}: {e}",
                "motores": [], "segundos": round(time.time() - t0, 1)}


def es_honesta(texto: str) -> bool:
    t = (texto or "").lower()
    return any(s in t for s in _HONESTA)


def main() -> int:
    from CEREBRO import registro_herramientas as rh
    from SETUP.barrido_cobertura import es_interna, frase_humana

    catalogo = rh.descubrir(refrescar=True)
    # Misma muestra que el barrido: una por módulo, saltando la plomería.
    por_modulo: dict = {}
    for clave, h in catalogo.items():
        doc = (h.get("doc") or "")
        if es_interna(clave, doc):
            continue
        por_modulo.setdefault(clave.split(":")[0], []).append((clave, doc))

    muestra = []
    for _mod, items in sorted(por_modulo.items()):
        muestra.extend(items[:4])

    print(f"validando {len(muestra)} peticiones (guardando la respuesta completa)...")
    resultados = []
    for i, (clave, doc) in enumerate(muestra, 1):
        frase = frase_humana(clave, doc)
        r = preguntar(frase)
        usados = {str(m).lower() for m in r["motores"]}
        resultados.append({
            "clave": clave,
            "frase": frase,
            "motores": r["motores"],
            "segundos": r["segundos"],
            "sin_manos": bool(not usados or usados <= SIN_MANOS),
            "honesta": es_honesta(r["respuesta"]),
            "respuesta": (r["respuesta"] or "")[:900],
        })
        if i % 15 == 0:
            print(f"   [{i}/{len(muestra)}]")

    SALIDA.write_text(json.dumps(resultados, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    sin_manos = sum(1 for x in resultados if x["sin_manos"])
    honestas = sum(1 for x in resultados if x["sin_manos"] and x["honesta"])
    print()
    print(f"guardado en {SALIDA}")
    print(f"   total probadas       : {len(resultados)}")
    print(f"   contestó sin manos   : {sin_manos}")
    print(f"   ...y de esas, honestas: {honestas}  (dijo que no podía, no inventó)")
    print(f"   hizo algo real       : {len(resultados) - sin_manos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
