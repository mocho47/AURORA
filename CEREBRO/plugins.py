# -*- coding: utf-8 -*-
"""AURORA · EL REGISTRO DE APPS (plugins)

Anuar lo pidió el 2026-08-16: *"recuerda todo lleva manual de usuario y plugin
para AURORA"*, y luego lo explicó mejor: *"así le doy el manual, que lo
aprenda, o tú integras macros en AURORA o el conocimiento que requiere"*.

**El problema que resuelve.** Cada app que se entrega aparte (plantillas de
prenda, analizador de mercado, buscador de clientes) es un programa completo
que corre solo. Sin esto, AURORA ni sabe que existen: quedan como islas, y
Anuar tendría que acordarse de cada una.

**Cómo lo resuelve.** Cada app deja una ficha en `PLUGINS/*.json` que dice, en
un solo lugar:
  · qué hace y para qué sirve,
  · dónde vive el motor y dónde la app suelta,
  · **dónde está su manual** — que AURORA lee para poder explicarlo,
  · las **frases** con las que la gente la pide de verdad,
  · las **acciones** que se pueden ejecutar, con sus parámetros.

Con eso AURORA puede tres cosas que antes no: reconocer la petición, ejecutar
la acción correcta, y **explicar cómo se usa** citando el manual — sin que
nadie le enseñe nada a mano.

Esto también cierra el pendiente viejo del `motor.json`: es el contrato del
motor, pero escrito para lo que de verdad hacía falta.

Correr:
    python CEREBRO/plugins.py                  → lista lo registrado
    python CEREBRO/plugins.py "cotiza playera" → a quién le toca esa frase
"""
from __future__ import annotations
import io
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "PLUGINS"


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _limpio(t: str) -> str:
    """Sin acentos y en minúsculas: la gente escribe «panalero» y «pañalero»."""
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cargar() -> list:
    """Todas las fichas. Una ficha rota no tumba a las demás."""
    fichas = []
    if not CARPETA.exists():
        return fichas
    for f in sorted(CARPETA.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            d["_ficha"] = str(f)
            fichas.append(d)
        except Exception as e:
            fichas.append({"app": f.stem, "nombre": f.stem, "_ficha": str(f),
                           "error": f"La ficha no se pudo leer: {e}"})
    return fichas


def _pares_acciones(ficha: dict) -> list:
    """Normaliza `acciones` a una lista de (nombre, ficha_accion).

    Las acciones se escriben de dos maneras y las dos son válidas: como
    diccionario {"pliego": {...}} o como lista [{"accion": ...}]. Recorrer un
    diccionario directo devuelve sus CLAVES —texto, no fichas— y eso revienta
    con «'str' object has no attribute 'get'». Se normaliza aquí, en el único
    lugar donde se leen — `catalogo()` tenía el mismo bug sin este arreglo
    porque leía `acciones` por su cuenta en vez de pasar por aquí (2026-08-20).
    """
    acciones = ficha.get("acciones") or {}
    if isinstance(acciones, dict):
        return [(k, v if isinstance(v, dict) else {}) for k, v in acciones.items()]
    return [((a.get("accion") or a.get("nombre") or ""), a)
            for a in acciones if isinstance(a, dict)]


def buscar(frase: str) -> dict:
    """A qué app le toca esa frase, y con qué acción.

    Se puntúa: una frase completa de la ficha vale mucho más que una palabra
    suelta. Es lo que evita que «precio» se lleve todas las peticiones.
    """
    t = _limpio(frase)
    if not t.strip():
        return {"status": "VACIO"}
    mejor, punto_mejor, accion_mejor = None, 0, None
    for p in cargar():
        if p.get("error"):
            continue
        punto = 0
        for f in p.get("frases", []):
            fl = _limpio(f)
            if fl and fl in t:
                punto = max(punto, 10 + len(fl.split()))
        for pal in p.get("palabras", []):
            if _limpio(pal) in t:
                punto += 2
        pares = _pares_acciones(p)

        # Se queda la acción de MÁS peso, no la última que coincidió. Y una
        # frase escrita a propósito pesa el doble que el nombre de la acción:
        # «cuánto cobro por 200 etiquetas» se iba a la acción «etiqueta» solo
        # porque la palabra aparecía en la petición.
        accion, peso_accion = None, 0
        for nombre_accion, a in pares:
            candidatas = [(f, 12) for f in a.get("frases", [])]
            if nombre_accion:
                candidatas.append((str(nombre_accion).replace("_", " "), 5))
            for f, base in candidatas:
                fl = _limpio(f)
                if fl and fl in t:
                    w = base + len(fl.split())
                    if w > peso_accion:
                        accion, peso_accion = {"accion": nombre_accion, **a}, w
        punto += peso_accion
        if punto > punto_mejor:
            mejor, punto_mejor, accion_mejor = p, punto, accion
    if not mejor:
        return {"status": "NINGUNA",
                "detalle": "Ninguna app registrada reconoce esa petición."}
    return {"status": "OK", "app": mejor.get("app"),
            "nombre": mejor.get("nombre"), "puntos": punto_mejor,
            "accion": accion_mejor, "plugin": mejor}


def manual(app: str) -> dict:
    """El manual de una app, para que AURORA lo pueda leer y explicar."""
    for p in cargar():
        if p.get("app") == app or _limpio(p.get("nombre", "")) == _limpio(app):
            f = Path(p.get("manual", ""))
            if f.exists():
                return {"status": "OK", "app": p["app"], "archivo": str(f),
                        "texto": f.read_text(encoding="utf-8",
                                             errors="replace")}
            return {"status": "SIN_MANUAL",
                    "detalle": f"«{p.get('nombre')}» no tiene manual en "
                               f"{p.get('manual', '(no dice dónde)')}"}
    return {"status": "NO_EXISTE", "detalle": f"No tengo registrada «{app}»."}


def ejecutar(app: str, accion: str, **kw) -> dict:
    """Corre una acción de una app. El motor se carga solo cuando se ocupa.

    Se cargan por ruta y no con `import`, a propósito: así una app puede vivir
    fuera de AURORA y seguir sirviendo, que es de lo que se trata entregarlas
    sueltas.
    """
    import importlib.util as ilu
    for p in cargar():
        if p.get("app") != app:
            continue
        motor = Path(p.get("motor", ""))
        if not motor.is_absolute():
            motor = RAIZ / motor
        if not motor.exists():
            return {"status": "SIN_MOTOR", "detalle": f"No existe {motor}"}
        a = next((x for x in p.get("acciones", [])
                  if x.get("nombre") == accion), None)
        if not a:
            return {"status": "SIN_ACCION",
                    "detalle": f"«{app}» no tiene la acción «{accion}». "
                               f"Tiene: " + ", ".join(
                                   x.get("nombre", "?")
                                   for x in p.get("acciones", []))}
        spec = ilu.spec_from_file_location(f"plug_{app}", motor)
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        fn = getattr(m, a.get("funcion", ""), None)
        if not callable(fn):
            return {"status": "SIN_FUNCION",
                    "detalle": f"{motor.name} no tiene «{a.get('funcion')}»"}
        try:
            return {"status": "OK", "app": app, "accion": accion,
                    "resultado": fn(**kw)}
        except TypeError as e:
            return {"status": "PARAMETROS",
                    "detalle": f"{e}. Espera: "
                               + ", ".join(a.get("params", []))}
        except Exception as e:
            return {"status": "TRONO", "detalle": str(e)[:400]}
    return {"status": "NO_EXISTE", "detalle": f"No tengo registrada «{app}»."}


def catalogo() -> str:
    """Lo registrado, en texto — es lo que AURORA contesta si le preguntan."""
    fichas = cargar()
    if not fichas:
        return "No hay ninguna app registrada todavía."
    t = f"🔌 **{len(fichas)} apps registradas**\n"
    for p in fichas:
        if p.get("error"):
            t += f"\n• ⚠️ {p['app']} — {p['error']}"
            continue
        t += f"\n• **{p.get('nombre')}** (`{p.get('app')}`)\n"
        t += f"  {p.get('que_hace', '')}\n"
        acc = ", ".join(nombre or "?" for nombre, _ in _pares_acciones(p))
        if acc:
            t += f"  acciones: {acc}\n"
        if p.get("app_suelta"):
            t += f"  app suelta: `{p['app_suelta']}`\n"
    return t


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        r = buscar(" ".join(args))
        if r["status"] != "OK":
            print(r.get("detalle", r["status"]))
            return 1
        print(f"→ {r['nombre']} ({r['app']}) · {r['puntos']} puntos")
        if r.get("accion"):
            print(f"  acción: {r['accion']['nombre']} — "
                  f"{r['accion'].get('que_hace', '')}")
            print(f"  espera: {', '.join(r['accion'].get('params', []))}")
        return 0
    print(catalogo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
