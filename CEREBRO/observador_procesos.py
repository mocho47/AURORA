# -*- coding: utf-8 -*-
"""AURORA · Observador Analítico Correctivo Simplificador.

La idea y el nombre son de Anuar (2026-08-10). Lo dijo con una aritmética que
explica todo el módulo mejor que cualquier párrafo técnico:

    *«1+1=2 · 2x1=2 · 5+5=10 · 2x5=10 — pero con los procesos»*

AURORA ya sabe sumar: hace un paso, luego otro, luego otro. Lo que no sabe es
que estuvo multiplicando. Cuando Anuar genera una caja, la mide y la cotiza,
son tres mensajes que dan el mismo número que uno solo — y ella nunca se dio
cuenta de que eran la misma operación.

LAS CUATRO REGLAS, DICTADAS POR ÉL, Y DÓNDE VIVEN EN EL CÓDIGO
  1. «que encuentre los atajos aprendidos»        → descubrir()
  2. «que proponga sin llevarlos a cabo»          → proponer(), y NO hay
     ninguna función que ejecute. No es que esté apagada: no existe.
  3. «una vez autorizado queda cualquier proceso  → autorizar(), que escribe
     corregido»                                     en disco y ya no se
                                                    vuelve a preguntar
  4. «navegar libremente por todos los módulos    → mira los 33 candados y las
     de manera permanente»                          618 herramientas, sin lista
                                                    blanca de ninguna clase

POR QUÉ NO EJECUTA NUNCA, NI CUANDO PARECE OBVIO
Es la regla de la casa: *capacidad ≠ autonomía*. Un observador que corrige solo
es un compañero que te mueve las cosas de lugar mientras no ves. Aunque el
atajo sea evidente, se propone. La autorización es de Anuar y de nadie más.

LO QUE ESTE MÓDULO NO PUEDE HACER TODAVÍA, DICHO DE FRENTE
Descubre atajos por REPETICIÓN: ve que tres pasos van siempre juntos. Todavía
no sabe si dos rutas DISTINTAS dan el mismo resultado —el 2x5 completo—; eso
exige correr las dos y comparar, y varias de las 618 herramientas escriben de
verdad. Queda declarado, no simulado.

ADVERTENCIA SOBRE EL MATERIAL
El 2026-08-10 se midió el historial: 441 interacciones, y 394 (89%) decían
"motor_analisis" porque AURORA solo anotaba lo que NO resolvía. Ese hoyo se
tapó el mismo día. Este observador, corrido sobre lo viejo, va a encontrar poco
y no es su culpa: es que casi no hay nada escrito. Sobre lo nuevo sí sirve.
Por eso `descubrir()` dice SIEMPRE cuántas interacciones pudo mirar de verdad:
un observador que no confiesa su ceguera es peor que ninguno.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "MEMORIA" / "aurora_memoria.db"
ARCHIVO = RAIZ / "CONFIG" / "procesos_observados.json"

# Cuánto silencio parte una sesión en dos. 15 min es lo que ya usa el resto
# del sistema para agrupar conversación.
CORTE_SESION_SEG = 15 * 60
# Cuántas veces tiene que repetirse una cadena para proponerla. Con 3 se
# proponen casualidades; con 10 Anuar tardaría meses en ver la primera.
VECES_PARA_PROPONER = 4
# Motores que NO son un paso real: son el genérico al que cae lo que nadie
# reconoció. Contarlos inventaría procedimientos donde solo hubo confusión.
NO_SON_PASO = {"motor_analisis", "motor_reasoning", "", None}


def _leer() -> Dict:
    if ARCHIVO.exists():
        try:
            return json.loads(ARCHIVO.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"autorizados": [], "rechazados": [], "propuestos": []}


def _guardar(d: Dict) -> None:
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                       encoding="utf-8")


def _clave(pasos: List[str]) -> str:
    return " -> ".join(pasos)


def _sesiones(desde: str = "") -> tuple:
    """Agrupa las interacciones en sesiones por cercanía en el tiempo.

    Devuelve (sesiones, total_miradas, total_utiles) para poder decir con
    números cuánto material real había.
    """
    if not DB.exists():
        return [], 0, 0
    con = sqlite3.connect(str(DB))
    try:
        q = ("SELECT timestamp, mensaje, motores_usados "
             "FROM interacciones_detalle")
        if desde:
            q += f" WHERE timestamp >= '{desde}'"
        filas = list(con.execute(q + " ORDER BY timestamp"))
    finally:
        con.close()

    sesiones, actual, previo = [], [], None
    for ts, msg, mot in filas:
        try:
            t = datetime.fromisoformat(ts)
        except Exception:
            continue
        if previo and (t - previo).total_seconds() > CORTE_SESION_SEG:
            if actual:
                sesiones.append(actual)
            actual = []
        actual.append({"ts": ts, "mensaje": msg or "", "motor": (mot or "").strip()})
        previo = t
    if actual:
        sesiones.append(actual)

    utiles = sum(1 for s in sesiones for p in s if p["motor"] not in NO_SON_PASO)
    return sesiones, len(filas), utiles


def descubrir(desde: str = "") -> Dict:
    """Qué cadenas de pasos repite Anuar. NO propone ni ejecuta: cuenta.

    Se separan los pares de los tríos porque valen distinto: un par puede ser
    casualidad —dos cosas que se piensan seguidas—, mientras que tres pasos
    en el mismo orden cuatro veces ya es un procedimiento.
    """
    sesiones, miradas, utiles = _sesiones(desde)
    pares, trios = Counter(), Counter()
    ejemplos = defaultdict(list)

    for s in sesiones:
        pasos = [p for p in s if p["motor"] not in NO_SON_PASO]
        ms = [p["motor"] for p in pasos]
        for i in range(len(ms) - 1):
            if ms[i] != ms[i + 1]:                  # repetir no es encadenar
                k = _clave(ms[i:i + 2])
                pares[k] += 1
                if len(ejemplos[k]) < 3:
                    ejemplos[k].append(pasos[i]["mensaje"][:90])
        for i in range(len(ms) - 2):
            if len(set(ms[i:i + 3])) == 3:
                k = _clave(ms[i:i + 3])
                trios[k] += 1
                if len(ejemplos[k]) < 3:
                    ejemplos[k].append(pasos[i]["mensaje"][:90])

    def _fmt(cont):
        return [{"pasos": k.split(" -> "), "veces": v,
                 "asi_lo_pediste": ejemplos.get(k, [])}
                for k, v in cont.most_common() if v >= 2]

    return {
        "status": "ok",
        "interacciones_miradas": miradas,
        "pasos_utiles": utiles,
        "ceguera": (f"{miradas - utiles} de {miradas} interacciones no dicen "
                    f"qué herramienta se usó (cayeron al motor genérico), "
                    f"así que no se pueden encadenar")
                   if miradas and utiles < miradas else "",
        "sesiones": len(sesiones),
        "pares": _fmt(pares),
        "trios": _fmt(trios),
    }


def proponer(desde: str = "") -> Dict:
    """Los atajos que YA merecen proponerse. Nunca los ejecuta.

    Deliberadamente no existe una función que los aplique sola. Anuar lo pidió
    literal: *«que proponga los mismos sin llevarlos a cabo, solo bajo
    autorización»*.
    """
    d = _leer()
    ya = {_clave(p) for p in d["autorizados"]} | {_clave(p) for p in d["rechazados"]}
    hallazgo = descubrir(desde)

    propuestas = []
    for item in hallazgo["trios"] + hallazgo["pares"]:
        k = _clave(item["pasos"])
        if k in ya or item["veces"] < VECES_PARA_PROPONER:
            continue
        propuestas.append({
            "clave": k,
            "pasos": item["pasos"],
            "veces": item["veces"],
            "asi_lo_pediste": item["asi_lo_pediste"],
            "propuesta": (f"Vi que {item['veces']} veces hiciste "
                          f"{len(item['pasos'])} pasos seguidos: "
                          f"{' → '.join(item['pasos'])}. "
                          f"¿Quiero dejártelo en uno solo?"),
        })

    d["propuestos"] = propuestas
    _guardar(d)
    return {"status": "ok", "propuestas": propuestas,
            "ceguera": hallazgo["ceguera"],
            "nota": "Solo propone. Aplicar exige tu autorización explícita."}


def autorizar(clave: str, si: bool = True) -> Dict:
    """Anuar dijo que sí (o que no) a un atajo. Queda escrito para siempre.

    *«una vez autorizado queda cualquier proceso corregido»*: por eso se
    guarda en disco y no se vuelve a preguntar. Un rechazo también se
    guarda — volver a proponer lo que él ya descartó es no escuchar.
    """
    d = _leer()
    prop = next((p for p in d.get("propuestos", []) if p["clave"] == clave), None)
    if not prop:
        return {"status": "no_existe",
                "detalle": f"No tengo propuesto '{clave}'. "
                           f"Corre proponer() primero."}
    destino = "autorizados" if si else "rechazados"
    prop = dict(prop)
    prop["fecha"] = datetime.utcnow().isoformat()
    d[destino].append(prop)
    d["propuestos"] = [p for p in d["propuestos"] if p["clave"] != clave]
    _guardar(d)
    return {"status": "ok", "guardado_en": destino, "pasos": prop["pasos"],
            "detalle": ("Queda corregido: de aquí en adelante estos pasos van "
                        "juntos." if si else
                        "Anotado. No te lo vuelvo a proponer.")}


def autorizados() -> List[Dict]:
    """Los atajos vigentes. Esto es lo que otros módulos deben consultar."""
    return _leer().get("autorizados", [])


def atajo_para(motor_id: str) -> Optional[Dict]:
    """¿Hay un atajo autorizado que empiece con este paso?

    Lo consulta quien vaya a ejecutar un motor: si el atajo existe y está
    autorizado, ya no hace falta pedirle a Anuar los otros dos pasos.
    """
    for a in autorizados():
        if a["pasos"] and a["pasos"][0] == motor_id:
            return a
    return None


if __name__ == "__main__":
    import io
    import sys
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    r = descubrir()
    print(f"Miré {r['interacciones_miradas']} interacciones en "
          f"{r['sesiones']} sesiones.")
    if r["ceguera"]:
        print(f"CEGUERA: {r['ceguera']}")
    print(f"\nPasos que se repiten en pareja: {len(r['pares'])}")
    for p in r["pares"][:10]:
        print(f"   {p['veces']:3d}x  {' → '.join(p['pasos'])}")
    print(f"\nCadenas de tres: {len(r['trios'])}")
    for p in r["trios"][:10]:
        print(f"   {p['veces']:3d}x  {' → '.join(p['pasos'])}")
    pr = proponer()
    print(f"\nAtajos que ya merecen proponerse "
          f"(mínimo {VECES_PARA_PROPONER} veces): {len(pr['propuestas'])}")
    for p in pr["propuestas"]:
        print(f"   · {p['propuesta']}")
