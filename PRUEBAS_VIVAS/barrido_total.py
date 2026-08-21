# -*- coding: utf-8 -*-
"""AURORA · Las 860 cosas, una por una, habladas como Anuar.

Anuar, 2026-08-10: *«corre las 860 cosas con mi lenguaje 1 a una completo»*.

QUÉ SON LAS 860
  · 33 candados directos del chat  → 180 frases ESCRITAS A MANO (rondas 1 y 2)
  · 625 herramientas del enrutador → 3 frases GENERADAS de su estilo c/u
  · 202 endpoints HTTP             → los 88 GET sin datos, llamados directo

LO QUE NO SE PRUEBA, Y POR QUÉ — dicho aquí y no escondido
  · 3 candados que ACTÚAN al primer mensaje: crear_capacidad escribe un motor
    en disco, editar_codigo escribe en el núcleo, accion_fisica repara WhatsApp
    de verdad. Se prueban con Anuar presente o no se prueban.
  · 111 endpoints POST: exigen datos reales y varios ejecutan. Mandarles un
    cuerpo vacío para «ver si contestan» sería inventar la prueba.
  · Las 420 herramientas peligrosas SÍ entran: se verificó en el código que
    proponen y esperan un «sí». Sesión nueva en cada mensaje para que ninguna
    se confirme sola con el mensaje siguiente, y jamás se manda confirmación.

HONESTIDAD SOBRE LAS FRASES GENERADAS
Las 180 del chat son suyas, escritas copiando su forma real. Las 1,875 del
enrutador salen de un molde con su vocabulario —sin acentos, «cotisa», «dame»,
«sacame», «checa», «a como»—. No son idénticas a como él hablaría; son lo más
cerca que se puede llegar sin escribir 1,875 frases a mano. Se dice para que
nadie lea el resultado como si fueran suyas.

REANUDABLE A PROPÓSITO
Escribe cada resultado a un .jsonl en el momento. Si se corta la luz, la
sesión o el servidor, se vuelve a lanzar y sigue donde iba. Un barrido de tres
horas que hay que empezar de cero cuando falla es un barrido que nunca termina.

    python PRUEBAS_VIVAS/barrido_total.py                 # todo
    python PRUEBAS_VIVAS/barrido_total.py --solo endpoints # solo los GET
    python PRUEBAS_VIVAS/barrido_total.py --resumen        # lee lo ya corrido
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

BASE = "http://127.0.0.1:5000"
SALIDA = Path(__file__).resolve().parent / "reportes"
CRUDO = SALIDA / "barrido_total.jsonl"

# Nombres de endpoint GET que NO se tocan aunque sean GET: disparan algo real.
GET_PROHIBIDOS = re.compile(
    r"publicar|enviar|borrar|eliminar|reparar|apagar|reiniciar|ejecutar|"
    r"activar|instalar|arrancar|detener", re.I)

# ── CÓMO HABLA ANUAR, aplicado a una herramienta cualquiera ──────────────
# Sale de sus 72 peticiones reales: pide con «dame/sacame/checa/hazme», casi
# nunca con el nombre técnico, y pregunta el precio con «a como» o «cuanto».
VERBOS = {
    "listar":   ("dame la lista de {o}", "que {o} hay", "sacame los {o}"),
    "obtener":  ("dame {o}", "cual es {o}", "pasame {o}"),
    "get":      ("dame {o}", "como esta {o}", "checa {o}"),
    "buscar":   ("buscame {o}", "hay {o}", "encuentrame {o}"),
    "crear":    ("hazme {o}", "necesito {o}", "armame {o}"),
    "generar":  ("generame {o}", "hazme {o}", "sacame {o}"),
    "guardar":  ("guarda {o}", "apunta {o}", "registra {o}"),
    "actualizar": ("actualiza {o}", "cambia {o}", "corrige {o}"),
    "borrar":   ("quita {o}", "borra {o}", "elimina {o}"),
    "cotizar":  ("cotisa {o}", "a como sale {o}", "cuanto por {o}"),
    "analizar": ("analizame {o}", "checa {o}", "que ves en {o}"),
    "calcular": ("calculame {o}", "cuanto da {o}", "sacame el calculo de {o}"),
    "enviar":   ("manda {o}", "envia {o}", "mandale {o}"),
    "preparar": ("preparame {o}", "dejame listo {o}", "arma {o}"),
    "convertir": ("convierte {o}", "pasa {o}", "pasame {o} convertido"),
    "resumen":  ("dame el resumen de {o}", "como va {o}", "que tal {o}"),
    "estado":   ("como esta {o}", "que onda con {o}", "checa {o}"),
}
GENERICO = ("dame {o}", "necesito {o}", "checa {o}")

# Su ortografía real, para que las frases no salgan de laboratorio.
COMO_ESCRIBE = (("cotiza", "cotisa"), ("impresión", "imprecion"),
                ("plotter", "ploter"), ("diseño", "diseno"),
                ("está", "esta"), ("qué", "que"), ("cuánto", "cuanto"))


def _legible(clave: str, meta: dict) -> str:
    """El nombre de la herramienta, dicho como lo diría una persona."""
    fn = meta.get("funcion") or clave.split(":")[-1]
    obj = re.sub(r"^(listar|obtener|get|buscar|crear|generar|guardar|"
                 r"actualizar|borrar|cotizar|analizar|calcular|enviar|"
                 r"preparar|convertir)_?", "", fn)
    obj = obj.replace("_", " ").strip()
    if not obj:
        # sin objeto en el nombre, se usa el módulo: "ordenes_taller" → "ordenes taller"
        obj = Path(meta.get("modulo", "")).stem.replace("_", " ")
    return obj or "eso"


def _frases_de(clave: str, meta: dict) -> list:
    fn = (meta.get("funcion") or "").lower()
    obj = _legible(clave, meta)
    molde = GENERICO
    for v, plantillas in VERBOS.items():
        if fn.startswith(v) or v in fn:
            molde = plantillas
            break
    fs = []
    for i, p in enumerate(molde):
        f = p.format(o=obj)
        if i == 2:                       # la tercera con su ortografía real
            for bien, suyo in COMO_ESCRIBE:
                f = f.replace(bien, suyo)
        fs.append(f)
    return fs


# ── plomería ─────────────────────────────────────────────────────────────

def _hechas() -> set:
    if not CRUDO.exists():
        return set()
    hechas = set()
    for linea in CRUDO.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            hechas.add(json.loads(linea)["id"])
        except Exception:
            pass
    return hechas


def _anota(fila: dict) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    with CRUDO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def _chat(frase: str, n: int, timeout: int = 90) -> dict:
    ses = f"barrido-{n}-{int(time.time()*1000)}"    # sesión nueva SIEMPRE
    req = urllib.request.Request(
        BASE + "/chat",
        data=json.dumps({"mensaje": frase, "session_id": ses}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.loads(f.read().decode("utf-8"))


def _califica(texto: str) -> tuple:
    t = (texto or "").strip()
    if not t:
        return "TRUENA", "respuesta vacía"
    b = t.lower()
    if "no tengo una herramienta que haga eso" in b:
        return "NO SABE", "dice que no puede"
    for marca in ("traceback", "internal server error", "500"):
        if marca in b:
            return "TRUENA", marca
    if len(t) < 40:
        return "REVISAR", "muy corta"
    return "OK", f"{len(t)} ch"


# ── los tres universos ───────────────────────────────────────────────────

def barrido_endpoints(hechas: set) -> int:
    from CORE import aurora_server  # noqa: F401  (solo para asegurar import)
    src = (RAIZ / "CORE" / "aurora_server.py").read_text(encoding="utf-8",
                                                         errors="ignore")
    gets = [g for g in re.findall(r'@app\.get\("([^"]+)"', src)
            if "{" not in g and not GET_PROHIBIDOS.search(g)]
    n = 0
    for ruta in gets:
        ident = f"endpoint:{ruta}"
        if ident in hechas:
            continue
        n += 1
        t0 = time.time()
        try:
            with urllib.request.urlopen(BASE + ruta, timeout=60) as f:
                code, cuerpo = f.status, f.read()[:400].decode("utf-8", "ignore")
            veredicto = "OK" if code == 200 else "REVISAR"
        except urllib.error.HTTPError as e:
            code, cuerpo = e.code, e.read()[:200].decode("utf-8", "ignore")
            veredicto = "TRUENA" if code >= 500 else "REVISAR"
        except Exception as e:
            code, cuerpo, veredicto = 0, str(e)[:200], "TRUENA"
        _anota({"id": ident, "universo": "endpoint", "ruta": ruta,
                "http": code, "veredicto": veredicto,
                "seg": round(time.time() - t0, 1), "muestra": cuerpo[:300]})
        print(f"  {veredicto:8s} {code:4} {ruta}", flush=True)
    return n


def barrido_candados(hechas: set) -> int:
    from PRUEBAS_VIVAS import frases_anuar as R1
    from PRUEBAS_VIVAS import frases_anuar_ronda2 as R2
    fuera = set(R1.NO_AUTOMATICOS)
    n = 0
    for ronda, mod in (("1", R1), ("2", R2)):
        for cand, (frases, _crit) in mod.FRASES.items():
            if cand in fuera:
                continue
            for i, frase in enumerate(frases):
                ident = f"candado:{ronda}:{cand}:{i}"
                if ident in hechas:
                    continue
                n += 1
                t0 = time.time()
                try:
                    r = _chat(frase, n, timeout=200)
                    texto, motores = r.get("respuesta") or "", r.get("motores_usados") or []
                    veredicto, porque = _califica(texto)
                    if veredicto == "OK" and cand not in motores:
                        veredicto, porque = "OTRO MOTOR", f"contestó {motores}"
                except Exception as e:
                    texto, motores = str(e)[:200], []
                    veredicto, porque = "TRUENA", "no contestó"
                _anota({"id": ident, "universo": "candado", "esperado": cand,
                        "frase": frase, "motores": motores,
                        "veredicto": veredicto, "porque": porque,
                        "seg": round(time.time() - t0, 1),
                        "respuesta": texto[:600]})
                print(f"  {veredicto:10s} r{ronda} {cand:18s} "
                      f"{time.time()-t0:5.1f}s  {frase[:44]}", flush=True)
    return n


def barrido_enrutador(hechas: set, limite: int = 0) -> int:
    from CEREBRO.registro_herramientas import descubrir
    h = descubrir()
    claves = sorted(h)
    if limite:
        claves = claves[:limite]
    n = 0
    for c, clave in enumerate(claves):
        meta = h[clave]
        for i, frase in enumerate(_frases_de(clave, meta)):
            ident = f"tool:{clave}:{i}"
            if ident in hechas:
                continue
            n += 1
            t0 = time.time()
            try:
                r = _chat(frase, n, timeout=120)
                texto, motores = r.get("respuesta") or "", r.get("motores_usados") or []
                veredicto, porque = _califica(texto)
            except Exception as e:
                texto, motores = str(e)[:200], []
                veredicto, porque = "TRUENA", "no contestó"
            _anota({"id": ident, "universo": "enrutador", "herramienta": clave,
                    "peligrosa": bool(meta.get("peligrosa")), "frase": frase,
                    "motores": motores, "veredicto": veredicto, "porque": porque,
                    "seg": round(time.time() - t0, 1), "respuesta": texto[:400]})
            if n % 25 == 0 or veredicto in ("TRUENA",):
                print(f"  [{c+1}/{len(claves)}] {veredicto:8s} {clave[:44]:46s} "
                      f"{frase[:36]}", flush=True)
    return n


def resumen() -> None:
    if not CRUDO.exists():
        print("Todavía no hay nada corrido.")
        return
    from collections import Counter
    porUni = {}
    for linea in CRUDO.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            d = json.loads(linea)
        except Exception:
            continue
        porUni.setdefault(d["universo"], Counter())[d["veredicto"]] += 1
    print(f"{'universo':12s} " + "  ".join(f"{v:>10s}" for v in
          ("OK", "REVISAR", "NO SABE", "OTRO MOTOR", "TRUENA")))
    for uni, c in porUni.items():
        tot = sum(c.values())
        print(f"{uni:12s} " + "  ".join(f"{c.get(v,0):10d}" for v in
              ("OK", "REVISAR", "NO SABE", "OTRO MOTOR", "TRUENA"))
              + f"   total {tot}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["endpoints", "candados", "enrutador"])
    ap.add_argument("--limite", type=int, default=0,
                    help="solo las primeras N herramientas (para probar el barrido)")
    ap.add_argument("--resumen", action="store_true")
    a = ap.parse_args()

    if a.resumen:
        resumen()
        return

    hechas = _hechas()
    print(f"Ya corridas antes: {len(hechas)} (se saltan)\n", flush=True)
    t0 = time.time()

    if a.solo in (None, "endpoints"):
        print("── ENDPOINTS GET (sin Groq, gratis) ──", flush=True)
        print(f"   {barrido_endpoints(hechas)} nuevos\n", flush=True)
    if a.solo in (None, "candados"):
        print("── 33 CANDADOS · frases escritas a mano ──", flush=True)
        print(f"   {barrido_candados(hechas)} nuevas\n", flush=True)
    if a.solo in (None, "enrutador"):
        print("── 625 HERRAMIENTAS · frases de su estilo ──", flush=True)
        print(f"   {barrido_enrutador(hechas, a.limite)} nuevas\n", flush=True)

    print(f"\nTerminó en {(time.time()-t0)/60:.1f} min")
    resumen()


if __name__ == "__main__":
    main()
