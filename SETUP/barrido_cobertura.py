# -*- coding: utf-8 -*-
"""
AURORA · BARRIDO DE COBERTURA — ¿a cuántas de sus 535 herramientas se llega?
============================================================================

POR QUÉ EXISTE
--------------
Anuar, 2026-08-03: *"qué requieres para que AURORA entienda y ejecute todo lo
que tiene en su código? para qué seguir creando parciales?"*

Tenía razón en el fondo: durante dos días el método fue **reaccionar** —él
encontraba un fallo, se arreglaba, y otra vez. Eso nunca termina y se siente
como repetir el proceso, porque lo es.

AURORA tiene **535 herramientas** en su registro. Nadie sabía cuántas se pueden
alcanzar hablando. **Y lo que no se mide, no se sabe que está roto** — por eso
los fallos los descubría él usándola, y no una auditoría.

Esto produce un NÚMERO, no una promesa: *"X de 535 alcanzables"*. Con evidencia
por cada una, y repetible: si algo se rompe, la cobertura baja y se nota.

CÓMO MIDE
---------
Por cada herramienta se arma la frase con que un humano la pediría —sacada de su
propia descripción, no inventada— y se manda al chat de verdad. Después se mira
a dónde llegó:

  LLEGO    ejecutó esa herramienta, o la propuso para confirmar
  OTRA     lo atendió otro candado. **No siempre es un error**: pedir la
           contabilidad y que responda el candado de negocio está bien
  PERDIDA  cayó en el motor de texto o se quedó sin herramienta ← el problema
  ERROR    la petición falló

Uso:
    python SETUP/barrido_cobertura.py            # muestra por carpeta (rápido)
    python SETUP/barrido_cobertura.py --todas    # las 535 (tarda)
    python SETUP/barrido_cobertura.py --carpeta TALLER
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

CHAT = "http://127.0.0.1:5000/chat"
SALIDA = RAIZ / "_CONTEXTO" / "COBERTURA.md"

# Motores de texto: si la respuesta salió solo de aquí, no se ejecutó nada real.
SIN_MANOS = {"motor_analisis", "conversacional", "razonador", "sin_herramienta"}


def _preguntar(mensaje: str, timeout: int = 90) -> tuple[str, list, float]:
    cuerpo = json.dumps({"mensaje": mensaje, "session_id": "barrido",
                         "canal": "api"}).encode()
    req = urllib.request.Request(CHAT, data=cuerpo,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        return d.get("respuesta", ""), d.get("motores_usados") or [], time.time() - t0
    except Exception as e:
        return f"__ERROR__ {type(e).__name__}", [], time.time() - t0


# Funciones INTERNAS: existen para que el sistema funcione, no para que alguien
# se las pida hablando. Nadie le dice a AURORA "inicializa la base de datos".
# La primera versión del barrido las contaba como fallas y inflaba el problema:
# medía mi capacidad de inventar frases, no la de AURORA de entenderlas.
_INTERNAS = (
    "init_db", "init", "main", "inicializar", "setup", "configurar_logging",
    "get_status", "_", "ejecutar", "run", "start", "stop", "close", "reset",
    "to_dict", "from_dict", "serializar", "cargar_config", "guardar_config",
    "conectar", "desconectar", "migrar", "crear_tablas", "sincronizar",
)


def es_interna(clave: str, doc: str) -> bool:
    """True si es plomería del sistema y no algo que un humano pediría."""
    funcion = clave.split(":")[-1].split(".")[-1].lower()
    if funcion in _INTERNAS or funcion.startswith("_"):
        return True
    # Sin descripción y con nombre de una sola palabra genérica: no es un comando.
    d = (doc or "").strip()
    if not d and len(funcion) <= 8 and "_" not in funcion:
        return True
    return False


def frase_humana(clave: str, doc: str) -> str:
    """Cómo pediría esto una persona, sacado de la propia descripción.

    No se inventa: si la herramienta dice "Cotiza corte láser desde un DXF", la
    frase es "cotiza corte láser desde un dxf". Si no tiene descripción, se usa
    el nombre de la función en palabras — que es lo mejor que hay.
    """
    d = (doc or "").strip().split("\n")[0].strip()
    d = re.sub(r"^(CHAT\s*↔\s*[A-ZÁÉÍÓÚÑ ]+[:.]?\s*)", "", d)
    d = re.sub(r"\(.*?\)", " ", d)                    # quita paréntesis técnicos
    d = re.sub(r"[`'\"]", " ", d)
    d = re.sub(r"\s{2,}", " ", d).strip(" .:—-")

    if len(d) < 12 or d.lower().startswith(("devuelve", "retorna", "true si", "helper")):
        # Sin descripción usable: se arma una petición con el nombre de la
        # función Y su carpeta, que da el contexto que falta. "listar" solo no
        # es nada; "quiero listar de agenda" sí se puede enrutar. La primera
        # versión mandaba la palabra suelta y medía mi generador, no a AURORA.
        funcion = clave.split(":")[-1].split(".")[-1].replace("_", " ").strip()
        carpeta = (clave.split("/")[0] if "/" in clave else "").lower()
        tema = {"agenda": "de la agenda", "taller": "del taller",
                "vendedor": "de ventas", "marketing": "de marketing",
                "publicador": "de publicaciones", "memoria": "de la memoria",
                "web": "en internet", "sistema": "del sistema",
                "auth": "de usuarios", "oracle": "de leads",
                "editor": "de diseño", "sublimacion": "de sublimación",
                "biblioteca": "de la biblioteca", "cerebro": "del sistema",
                "integraciones": "de integraciones", "redes": "de la red",
                "manuales": "de los manuales", "core": "del sistema"}.get(carpeta, "")
        d = f"quiero {funcion} {tema}".strip()

    palabras = d.split()
    if len(palabras) > 14:
        d = " ".join(palabras[:14])
    return d[0].lower() + d[1:] if d else clave


def clasificar(clave: str, motores: list, respuesta: str) -> str:
    if respuesta.startswith("__ERROR__"):
        return "ERROR"
    usados = {str(m).lower() for m in motores}
    if not usados or usados <= SIN_MANOS:
        return "PERDIDA"
    # ¿Se nombró la herramienta pedida, o su módulo?
    modulo = clave.split(":")[0].split("/")[-1].lower()
    funcion = clave.split(":")[-1].split(".")[-1].lower()
    texto = (respuesta or "").lower()
    if clave.lower() in texto or funcion in texto or funcion in " ".join(usados):
        return "LLEGO"
    if any(modulo in u for u in usados):
        return "LLEGO"
    return "OTRA"


def main() -> int:
    from CEREBRO import registro_herramientas as rh

    catalogo = rh.descubrir(refrescar=True)
    print(f"El registro tiene {len(catalogo)} herramientas.\n")

    args = sys.argv[1:]
    todas = "--todas" in args
    filtro = ""
    if "--carpeta" in args:
        i = args.index("--carpeta")
        filtro = args[i + 1].upper() if i + 1 < len(args) else ""

    # Se agrupa por carpeta para poder medir una muestra representativa.
    por_carpeta = defaultdict(list)
    for clave, meta in catalogo.items():
        carpeta = clave.split("/")[0] if "/" in clave else clave.split(":")[0]
        if filtro and carpeta.upper() != filtro:
            continue
        por_carpeta[carpeta].append((clave, meta))

    objetivo, internas = [], 0
    for carpeta, items in sorted(por_carpeta.items()):
        # Se descartan las internas ANTES de elegir la muestra: si no, la muestra
        # se llena de plomería y el número sale mal.
        utiles = []
        for clave, meta in items:
            if es_interna(clave, meta.get("doc", "")):
                internas += 1
            else:
                utiles.append((clave, meta))
        objetivo.extend(utiles if (todas or filtro) else utiles[:4])

    print(f"Se saltan {internas} funciones internas (init_db, main, ejecutar…):")
    print("  no son comandos, son plomería del sistema. Que no se alcancen desde")
    print("  el chat es CORRECTO, y contarlas como fallas infla el problema.\n")
    print(f"Se van a probar {len(objetivo)} herramientas de verdad"
          f"{' (todas)' if todas else ' (muestra por carpeta)'}.")
    print("Cada una se manda al chat DE VERDAD. Esto tarda.\n")

    resultados, cuenta = [], defaultdict(int)
    t_inicio = time.time()
    for n, (clave, meta) in enumerate(objetivo, 1):
        frase = frase_humana(clave, meta.get("doc", ""))
        resp, motores, seg = _preguntar(frase)
        estado = clasificar(clave, motores, resp)
        cuenta[estado] += 1
        resultados.append({
            "clave": clave, "frase": frase, "estado": estado,
            "motores": motores, "segundos": round(seg, 1),
            "respuesta": (resp or "")[:160].replace("\n", " "),
        })
        marca = {"LLEGO": "OK ", "OTRA": " ~ ", "PERDIDA": "MAL", "ERROR": "ERR"}[estado]
        print(f"[{n:4d}/{len(objetivo)}] {marca} {seg:5.1f}s  {clave[:52]}")
        if n % 25 == 0:
            hechos = time.time() - t_inicio
            faltan = (hechos / n) * (len(objetivo) - n)
            print(f"           ... {cuenta['LLEGO']} llegan, {cuenta['PERDIDA']} perdidas"
                  f" · faltan ~{faltan/60:.0f} min")

    total = len(resultados)
    alcanzables = cuenta["LLEGO"] + cuenta["OTRA"]
    print("\n" + "=" * 68)
    print(f"LLEGAN A SU HERRAMIENTA : {cuenta['LLEGO']:4d}")
    print(f"LAS ATIENDE OTRO CANDADO: {cuenta['OTRA']:4d}   (no siempre es error)")
    print(f"SE PIERDEN              : {cuenta['PERDIDA']:4d}   <- el problema real")
    print(f"FALLARON                : {cuenta['ERROR']:4d}")
    print(f"\nCOBERTURA: {alcanzables} de {total} = {alcanzables/total*100:.1f}%")
    print("=" * 68)

    _escribir_informe(resultados, cuenta, total, len(catalogo), todas or bool(filtro))
    print(f"\nDetalle en: {SALIDA}")
    return 0


def _escribir_informe(resultados, cuenta, total, en_registro, completo) -> None:
    perdidas = [r for r in resultados if r["estado"] == "PERDIDA"]
    lentas = sorted(resultados, key=lambda r: -r["segundos"])[:15]
    alcanzables = cuenta["LLEGO"] + cuenta["OTRA"]

    L = ["# 📊 Cobertura real de AURORA",
         f"### Medido el {time.strftime('%Y-%m-%d %H:%M')} · "
         f"{'todas las herramientas' if completo else 'muestra por carpeta'}",
         "",
         "> Cada línea de aquí se mandó al chat **de verdad** y se miró a dónde",
         "> llegó. No es una estimación.",
         "",
         "## El número",
         "",
         "| | |",
         "|---|---|",
         f"| Herramientas en el registro | **{en_registro}** |",
         f"| Probadas en este barrido | {total} |",
         f"| Llegan a su herramienta | **{cuenta['LLEGO']}** |",
         f"| Las atiende otro candado | {cuenta['OTRA']} |",
         f"| **Se pierden** | **{cuenta['PERDIDA']}** |",
         f"| Fallaron | {cuenta['ERROR']} |",
         f"| **Cobertura** | **{alcanzables/total*100:.1f}%** |",
         "",
         "*«Las atiende otro candado» no siempre es un error: pedir la",
         "contabilidad y que responda el candado de negocio está bien.*",
         ""]

    if perdidas:
        L += ["---", "", f"## ❌ Las {len(perdidas)} que se pierden", "",
              "Son las que hay que conectar: la capacidad existe y no hay forma",
              "de pedirla hablando.", "",
              "| Herramienta | Se pidió así | Contestó |", "|---|---|---|"]
        for r in perdidas[:60]:
            L.append(f"| `{r['clave']}` | {r['frase'][:50]} | {r['respuesta'][:70]} |")
        if len(perdidas) > 60:
            L.append(f"\n*(y {len(perdidas) - 60} más)*")
        L.append("")

    L += ["---", "", "## ⏱️ Las 15 más lentas", "",
          "| Segundos | Herramienta | Motor |", "|---|---|---|"]
    for r in lentas:
        L.append(f"| {r['segundos']} | `{r['clave'][:44]}` | {', '.join(map(str, r['motores']))[:28]} |")

    L += ["", "---", "",
          "## Cómo se repite", "",
          "```",
          "python SETUP/barrido_cobertura.py            # muestra rápida",
          "python SETUP/barrido_cobertura.py --todas    # las 535",
          "python SETUP/barrido_cobertura.py --carpeta TALLER",
          "```", "",
          "Si la cobertura baja de una medición a otra, algo se rompió.",
          ""]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
