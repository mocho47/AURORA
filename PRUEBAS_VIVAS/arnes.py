# -*- coding: utf-8 -*-
"""AURORA · El arnés que le habla como Anuar, 1 a 1, sin omitir nada.

Anuar, 2026-08-10: *«1 a 1 cada funcion 3 formas mias reales por cada una busca
que truene pero que trueno de forma natural no forzada... rapido en automatico
sin omitir 1 sola funcion»*.

POR QUÉ EXISTE
Las 319 pruebas que ya había pasan SIN LEVANTAR EL SERVIDOR: leen código y
comparan nombres. Ninguna escribe una frase en el chat y lee la respuesta. Que
pasen las 319 prueba que las piezas encajan, no que AURORA funcione. La prueba
de eso es que los 4 bugs graves de AURORA los encontró Anuar usándola normal, y
el 422 de ayer se cachó solo porque se CORRIÓ.

DOS CAPAS, PORQUE MIDEN COSAS DISTINTAS

  CAPA 1 · ¿ME ENTIENDE?   (en proceso · 0 riesgo · 0 tokens)
    Recorre _CANDADOS EN SU ORDEN REAL y ve cuál gana la frase, igual que el
    pipeline. No ejecuta nada: solo pregunta «¿este candado la agarra?».
    Atrapa la falla que más veces ha mordido aquí —un candado robándose el
    mensaje de otro—, que es justo por lo que _CANDADOS lleva media pantalla
    de comentarios explicando el orden.

  CAPA 2 · ¿ME CONTESTA BIEN?   (HTTP real contra /chat)
    Manda la frase de verdad y guarda la respuesta entera. Sesión NUEVA en cada
    mensaje: así ninguna acción peligrosa queda pendiente de un turno y se
    confirma sola con el mensaje siguiente.

LO QUE NO HACE, Y POR QUÉ
Tres candados actúan de verdad al primer mensaje —crear_capacidad escribe un
motor en disco, editar_codigo escribe archivos del núcleo, accion_fisica repara
WhatsApp— así que quedan fuera del barrido automático. No es que no importen:
es que se prueban con Anuar presente o no se prueban. Están listados en
frases_anuar.NO_AUTOMATICOS con el motivo, para que nadie crea que se olvidaron.

El reporte se auto-califica (OK / REVISAR / TRUENA) porque el punto de esto es
que Anuar lea 20 renglones, no 99 respuestas.

    python PRUEBAS_VIVAS/arnes.py              # capa 1 + capa 2 (lo seguro)
    python PRUEBAS_VIVAS/arnes.py --capa 1     # solo entendimiento, instantáneo
    python PRUEBAS_VIVAS/arnes.py --con-rastro # incluye los que dejan archivos
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

_RONDA = "2" if "--ronda2" in sys.argv else "1"
if _RONDA == "2":
    # Ronda 2: 90 frases que el módulo de lengua NUNCA vio. Sin esto la
    # medición sería tramposa —quien escribió las familias había visto el
    # examen de la ronda 1—.
    from PRUEBAS_VIVAS.frases_anuar_ronda2 import (  # noqa: E402
        DEJAN_RASTRO, FRASES, NO_AUTOMATICOS)
else:
    from PRUEBAS_VIVAS.frases_anuar import (  # noqa: E402
        DEJAN_RASTRO, FRASES, NO_AUTOMATICOS)

BASE = "http://127.0.0.1:5000"
SALIDA = Path(__file__).resolve().parent / "reportes"

# Señales de que la respuesta NO sirve. Salen de fallas reales de este proyecto,
# no de una lista genérica de "malas palabras".
SENIALES_MALAS = (
    ("no pude", "falló y lo dice"),
    ("error", "error crudo en la cara"),
    ("traceback", "excepción sin atrapar"),
    ("no tengo", "no encontró el dato"),
    ("500", "el servidor tronó"),
)
# Que AURORA pregunte NO es una falla: en la frase incompleta es lo correcto.
SENIALES_PREGUNTA = ("?", "dime", "cual", "cuál", "necesito saber", "me falta")


def _post(ruta: str, cuerpo: dict, timeout: int = 180):
    req = urllib.request.Request(
        BASE + ruta, data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.loads(f.read().decode("utf-8"))


# ── CAPA 1 · ¿me entiende? ───────────────────────────────────────────────

def capa1() -> list:
    """Qué candado gana cada frase, recorriendo _CANDADOS en su orden real."""
    from CEREBRO import consciencia as C
    try:
        from CEREBRO import lengua_anuar as L
    except Exception:
        L = None

    filas = []
    for esperado, (frases, criterio) in FRASES.items():
        for i, frase in enumerate(frases):
            gana = None
            # Se copia el pipeline real, incluida la lengua: si ella reconoce
            # la familia, ese candado manda y los demás se hacen a un lado.
            # Sin esto la capa 1 mediría un sistema que ya no existe.
            intencion = L.intencion(frase) if L else None
            for nombre, trigger, _met, _mid in C._CANDADOS:
                if intencion and nombre != intencion:
                    continue
                try:
                    if trigger(frase) or nombre == intencion:
                        gana = nombre
                        break
                except Exception as ex:                 # un trigger que truena
                    gana = f"TRUENA:{nombre}:{str(ex)[:60]}"
                    break
            # Tres desenlaces distintos, y meterlos en el mismo saco mentiría:
            #   ATRAPA   — el candado correcto la agarró
            #   COLISION — OTRO candado se la robó. Esto SÍ es un bug: la
            #              respuesta va a salir del motor equivocado.
            #   ENRUTADOR— ningún candado la agarró y cae a las 618 herramientas
            #              del enrutador universal. NO es una falla por sí sola:
            #              puede contestar perfecto. Solo la capa 2 lo sabe.
            if gana == esperado:
                clase = "ATRAPA"
            elif gana is None:
                clase = "ENRUTADOR"
            else:
                clase = "COLISION"
            filas.append({
                "candado": esperado, "n": i + 1, "frase": frase,
                "gana": gana or "(enrutador universal)",
                "clase": clase, "ok": clase == "ATRAPA",
                "criterio": criterio,
            })
    return filas


# ── CAPA 2 · ¿me contesta bien? ──────────────────────────────────────────

def _califica(texto: str, motores: list, esperado: str) -> tuple:
    """(veredicto, por_que). Conservador a propósito: ante la duda, REVISAR.

    Prefiere mandar de más a la revisión humana que dar por bueno algo que no
    lo es. Un arnés que se auto-aprueba no sirve para nada.
    """
    t = (texto or "").strip()
    if not t:
        return "TRUENA", "respuesta vacía"
    bajo = t.lower()
    for marca, motivo in SENIALES_MALAS:
        if marca in bajo:
            # "no tengo X guardado, dime cuál" es honestidad, no falla
            if any(p in bajo for p in SENIALES_PREGUNTA):
                return "REVISAR", f"{motivo}, pero pregunta (puede estar bien)"
            return "TRUENA", motivo
    if len(t) < 40:
        return "REVISAR", "respuesta muy corta"
    return "OK", f"{len(t)} ch · motores: {','.join(motores or []) or '—'}"


def _fallidas_previas() -> set:
    """Las frases que fallaron en corridas anteriores, leídas de los reportes.

    Anuar, 2026-08-10: *«corres solo las fraces que fallaron»*. Tiene razón —
    volver a correr las 90 para ver 5 arreglos es tirar diez minutos y su llave
    de Groq. Se leen de los reportes en disco y no de una lista escrita a mano,
    porque una lista a mano se desactualiza en la primera corrida.
    """
    frases = set()
    for r in sorted(SALIDA.glob("reporte_*.md")):
        txt = r.read_text(encoding="utf-8", errors="ignore")
        # las secciones que importan: colisiones, desvíos, y lo que no sirvió
        for m in re.finditer(r"^\| `[\w_]+` \| (.+?) \|", txt, re.M):
            frases.add(m.group(1).strip())
        for bloque in re.finditer(r"### (?:TRUENA|REVISAR).*?(?=\n### |\Z)",
                                  txt, re.S):
            frases |= {q.strip() for q in
                       re.findall(r"^> (.+)$", bloque.group(0), re.M)}
    return frases


def capa2(incluir_rastro: bool, solo_fallidas: bool = False,
          aprender: bool = False) -> list:
    saltar = set(NO_AUTOMATICOS)
    if not incluir_rastro:
        saltar |= set(DEJAN_RASTRO)

    filas, total = [], 0
    pendientes = [(c, f) for c, (fs, _) in FRASES.items()
                  for f in fs if c not in saltar]
    if solo_fallidas:
        previas = _fallidas_previas()
        # el reporte recorta a 60 y 70 caracteres, así que se compara por prefijo
        antes = len(pendientes)
        pendientes = [(c, f) for c, f in pendientes
                      if any(f.startswith(p[:40]) or p.startswith(f[:40])
                             for p in previas)]
        print(f"   solo las que ya habían fallado: {len(pendientes)} "
              f"de {antes}", flush=True)
    print(f"   {len(pendientes)} frases al chat real "
          f"({len(saltar)} candados saltados)\n", flush=True)

    for c, frase in pendientes:
        total += 1
        # sesión nueva en CADA mensaje: sin esto, una acción peligrosa propuesta
        # en la frase 1 se confirmaría sola con la frase 2 y se ejecutaría.
        ses = f"arnes-{total}-{int(time.time()*1000)}"
        t0 = time.time()
        try:
            r = _post("/chat", {"mensaje": frase, "session_id": ses})
            texto = r.get("respuesta") or ""
            motores = r.get("motores_usados") or []
            veredicto, porque = _califica(texto, motores, c)
        except urllib.error.HTTPError as e:
            texto, motores = f"HTTP {e.code}: {e.read().decode()[:200]}", []
            veredicto, porque = "TRUENA", f"HTTP {e.code}"
        except Exception as e:
            texto, motores = str(e)[:200], []
            veredicto, porque = "TRUENA", "no contestó"
        seg = time.time() - t0
        filas.append({"candado": c, "frase": frase, "respuesta": texto,
                      "motores": motores, "veredicto": veredicto,
                      "porque": porque, "seg": round(seg, 1)})
        icono = {"OK": "  ok  ", "REVISAR": " ~rev ", "TRUENA": " TRUENA"}[veredicto]
        print(f"{icono} [{total}/{len(pendientes)}] {c:18s} {seg:5.1f}s  "
              f"{frase[:52]}", flush=True)

        # APRENDER DE LA PRUEBA EN VIVO — idea de Anuar, 2026-08-10.
        # Solo se le enseña lo que NO sirvió, y solo cuando aquí se sabe cuál
        # era la respuesta correcta (el candado que la prueba declara). Se usa
        # el mecanismo que él ya pidió el 2026-08-02 en vez de inventar otro.
        # Honestidad de esto: enseñar frases sueltas es MEMORIZAR, no entender.
        # Vale para lo que de verdad es idiosincrásico suyo; lo que se puede
        # generalizar va en lengua_anuar.py, no aquí. Por eso es opcional y hay
        # que pedirlo: escribe en el aprendizaje real de AURORA.
        if aprender and veredicto != "OK" and c not in NO_AUTOMATICOS:
            try:
                from CEREBRO import aprende_del_usuario as _apr
                _apr.aprender_a_la_primera(frase, c, time.time())
                filas[-1]["aprendido"] = True
            except Exception as e:
                filas[-1]["aprendido"] = f"no se pudo: {str(e)[:60]}"
    return filas


# ── reporte ──────────────────────────────────────────────────────────────

def escribir(c1: list, c2: list, marca: str) -> Path:
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"reporte_{marca}.md"
    p = ["# Arnés · le hablé a AURORA como habla Anuar", ""]

    col = [f for f in c1 if f["clase"] == "COLISION"]
    enr = [f for f in c1 if f["clase"] == "ENRUTADOR"]
    p += [f"## Capa 1 · ¿me entiende? — {len(c1)} frases", "",
          f"**{len(c1)-len(col)-len(enr)} al candado correcto · "
          f"{len(col)} COLISIONES · {len(enr)} caen al enrutador**", "",
          "Una colisión es un bug: contesta el motor equivocado. Caer al "
          "enrutador no lo es por sí solo — lo juzga la capa 2.", ""]
    if col:
        p += ["### Colisiones — otro candado se robó el mensaje", "",
              "| debía contestar | frase | se la quedó |", "|---|---|---|"]
        for f in col:
            p.append(f"| `{f['candado']}` | {f['frase'][:60]} | **{f['gana']}** |")
        p.append("")
    if enr:
        p += ["### Cayeron al enrutador universal", "",
              "| candado que no la agarró | frase |", "|---|---|"]
        for f in enr:
            p.append(f"| `{f['candado']}` | {f['frase'][:70]} |")
        p.append("")

    if c2:
        cuenta = {v: sum(1 for f in c2 if f["veredicto"] == v)
                  for v in ("OK", "REVISAR", "TRUENA")}
        p += [f"## Capa 2 · ¿me contesta bien? — {len(c2)} frases reales",
              "",
              f"**{cuenta['OK']} ok · {cuenta['REVISAR']} a revisar · "
              f"{cuenta['TRUENA']} truenan**", ""]
        for v in ("TRUENA", "REVISAR", "OK"):
            grupo = [f for f in c2 if f["veredicto"] == v]
            if not grupo:
                continue
            p += [f"### {v} ({len(grupo)})", ""]
            for f in grupo:
                p += [f"**`{f['candado']}`** · _{f['porque']}_ · {f['seg']}s",
                      "", f"> {f['frase']}", "",
                      "```", (f["respuesta"] or "")[:900], "```", ""]

    p += ["## No se dispararon solos (a propósito)", ""]
    for c, motivo in NO_AUTOMATICOS.items():
        p.append(f"- **`{c}`** — {motivo}")
    p.append("")
    ruta.write_text("\n".join(p), encoding="utf-8")
    return ruta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capa", type=int, default=0, help="1 = solo entendimiento")
    ap.add_argument("--con-rastro", action="store_true",
                    help="incluye los candados que escriben archivos o abren apps")
    ap.add_argument("--ronda2", action="store_true",
                    help="usa las 90 frases nuevas que el módulo de lengua no vio")
    ap.add_argument("--solo-fallidas", action="store_true",
                    help="reintenta únicamente lo que ya falló en corridas previas")
    ap.add_argument("--aprende", action="store_true",
                    help="le enseña a AURORA las frases que no sirvieron (escribe de verdad)")
    a = ap.parse_args()
    print(f"RONDA {_RONDA} · {sum(len(f) for f, _ in FRASES.values())} frases\n")

    print("CAPA 1 · ¿me entiende? (sin tocar el servidor)")
    c1 = capa1()
    col = [f for f in c1 if f["clase"] == "COLISION"]
    enr = [f for f in c1 if f["clase"] == "ENRUTADOR"]
    print(f"   {len(c1)-len(col)-len(enr)}/{len(c1)} al candado correcto · "
          f"{len(col)} colisiones · {len(enr)} al enrutador")
    for f in col:
        print(f"   COLISION  {f['candado']:16s} se la quedó -> {f['gana']}")
        print(f"             «{f['frase']}»")

    c2 = []
    if a.capa != 1:
        print("\nCAPA 2 · ¿me contesta bien? (chat real)")
        c2 = capa2(a.con_rastro, a.solo_fallidas, a.aprende)

    ruta = escribir(c1, c2, f"ronda{_RONDA}_" + time.strftime("%Y%m%d_%H%M"))
    print(f"\nReporte: {ruta}")


if __name__ == "__main__":
    main()
