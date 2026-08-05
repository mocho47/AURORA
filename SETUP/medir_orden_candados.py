# -*- coding: utf-8 -*-
"""AURORA · ¿Qué pasa si el enrutador con IA decide ANTES que los candados?

Anuar lo dijo claro el 2026-08-04: "no sé cómo pedirle a AURORA sin que lance
algo diferente". Tiene razón, y la causa es de arquitectura: los candados son
listas de palabras rígidas que corren PRIMERO, así que interceptan el mensaje
antes de que la parte que sí razona (el enrutador universal, que conoce las 537
herramientas) lo vea.

Esto NO cambia nada todavía. Solo MIDE, sobre frases reales, cuántas atiende
cada camino y en qué se contradicen. Sin este número, invertir el orden sería
apostar con lo único que hoy le funciona al negocio.

Correr:  python SETUP/medir_orden_candados.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y truena con acentos y emojis.

    Se llama SOLO al correr el script directo. Hacerlo al importar le rompía la
    salida a quien lo importara — incluida AURORA (2026-08-05).
    """
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Frases REALES de Anuar. Cada una se escribió de verdad en el chat, y varias
# fallaron alguna vez. No son inventadas para que salga bonito el número.
FRASES_REALES = [
    # (frase, qué debería atenderla)
    ("cuanto cuesta el faro aozoom x5", "cotizador"),
    ("cotizame 20 playeras", "cotizador"),
    ("hazme un corte de caja", "negocio_real"),
    ("cuanto cayo hoy", "negocio_real"),
    ("como va la contabilidad", "negocio_real"),
    ("abreme coreldrau porfa", "motor_corel"),
    ("chekame el diseno abierto", "motor_corel"),
    ("ahora extrae el mapa de bits", "motor_corel"),
    ("que macros tiene corel", "motor_corel"),
    ("pasalo a corte", "taller_dxf"),
    ("sacale el dibujo lineal", "router_universal"),
    ("mandale un wats al cliente", "accion_sistema"),
    ("cuanto sale la instalacion de lupas", "servicios_atf"),
    ("busca en mercado libre el mejor precio de 100 hojas", "web_search"),
    ("encuentra el mejor precio por 100 hojas y dame el link", "web_search"),
    ("donde compro papel adhesivo mas barato", "web_search"),
    ("busca en internet precios de vinil textil", "web_search"),
    ("que tengo agendado hoy", "agenda"),
    ("voltea los videos a vertical", "motor_video"),
    ("cuantos videos duplicados tengo", "motor_video"),
    ("abre youtube", "pc_access"),
    ("que has aprendido de mi", "aprendizaje"),
    ("que sabes hacer", "auto_conocimiento"),
]


def candado_que_gana(mod, frase: str) -> tuple:
    """Qué atiende la frase HOY, por el MISMO camino que usa el chat real.

    Son dos vías, y medir solo la primera da un número falsamente malo:
      1. el disparador del candado (lista de palabras)
      2. lo APRENDIDO de Anuar — si él ya reformuló esa frase hasta que
         funcionó, se salta directo al candado que sirvió (consciencia:1522)
    """
    aprendido = None
    try:
        from CEREBRO import aprende_del_usuario as _apr
        aprendido = _apr.buscar(frase)
    except Exception:
        pass

    for _n, trig, _m, motor in mod._CANDADOS:
        por_aprendizaje = (aprendido is not None
                           and aprendido.get("herramienta") == motor)
        try:
            if trig(frase):
                return motor, "trigger"
        except TypeError:
            pass
        if por_aprendizaje:
            return motor, "aprendido"
    return "", ""


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_c", RAIZ / "CEREBRO" / "consciencia.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_c"] = mod
    spec.loader.exec_module(mod)

    print("LÍNEA BASE — cómo llega HOY cada frase real de Anuar")
    print("(trigger = la lista de palabras · aprendido = porque él ya la reformuló)")
    print("=" * 78)
    aciertos, fallos, sin_candado, por_aprendizaje = 0, [], [], 0

    for frase, esperado in FRASES_REALES:
        real, via = candado_que_gana(mod, frase)
        if not real:
            sin_candado.append((frase, esperado))
            marca = "SIN CANDADO"
        elif real == esperado:
            aciertos += 1
            if via == "aprendido":
                por_aprendizaje += 1
            marca = "OK"
        else:
            fallos.append((frase, esperado, real))
            marca = "MAL"
        print(f"  {marca:12} {frase[:44]:46} -> {(real or '(nada)'):18} {via}")

    total = len(FRASES_REALES)
    print()
    print("=" * 78)
    print(f"  ACIERTAN            : {aciertos}/{total}  ({aciertos*100//total}%)")
    print(f"     ...de esas, {por_aprendizaje} solo funcionan porque Anuar YA las reformuló antes")
    print(f"  VAN AL MOTOR ERRADO : {len(fallos)}")
    print(f"  NO LAS AGARRA NADIE : {len(sin_candado)}   <- estas caen en motor_analisis")
    print("=" * 78)

    if fallos:
        print("\nAL MOTOR EQUIVOCADO (lo más peligroso: contesta con seguridad algo ajeno):")
        for f, esp, real in fallos:
            print(f"  «{f[:52]}»\n      debía: {esp}   |   fue a: {real}")
    if sin_candado:
        print("\nSIN CANDADO (se van al modelo sin manos, que es donde inventa):")
        for f, esp in sin_candado:
            print(f"  «{f[:52]}»   debía: {esp}")

    print("\nQué significa: cada 'MAL' y cada 'SIN CANDADO' es una vez que Anuar")
    print("tuvo que adivinar cómo reformular. Ese es el número a mejorar si el")
    print("enrutador con IA decide primero.")
    return 0


if __name__ == "__main__":
    _consola_utf8()
    raise SystemExit(main())
