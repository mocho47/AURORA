# -*- coding: utf-8 -*-
"""AURORA · Los 189 generadores de boxes.py, con el vocabulario de Anuar

Anuar lo recordó el 2026-08-05: boxes.py tiene caja corazón, con flex, con
bisagras — no un solo modelo. Y marcó la prioridad: *"que TÚ la enseñes a usar
boxes.py, no que ella aprenda con el uso"*. Por eso esto NO descubre nada solo:
trae el mapa escrito de qué generador corresponde a cómo él pide las cajas.

Bug que costó encontrarlo (2026-08-05): `Boxes.close()` DEVUELVE los datos en un
BytesIO, no escribe el archivo. Por eso la primera prueba no generaba nada y
tampoco tiraba error.

Salidas de boxes.py: svg, ps, lbrn2 — **no exporta DXF**. El SVG lo abre Corel
y RDWorks, así que sirve directo; si se necesita DXF se convierte después.

Correr:  python TALLER/cajas_boxes.py "caja corazon con tapa de agujero de 45x7"
         python TALLER/cajas_boxes.py --lista
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DESTINO = Path.home() / "Downloads" / "dxf"

# Los mismos números reales del taller.
COSTO_MINUTO = 8.0
VELOCIDAD_MM_S = 25.0


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ── CÓMO PIDE ANUAR LAS CAJAS → QUÉ GENERADOR ES ────────────────────────
# Esto es lo que él pidió que yo le enseñara, en vez de que lo descubriera.
# Cada entrada: (palabras que él usa, generador de boxes.py, qué es).
CATALOGO = (
    (("corazon", "corazón", "heart"), "HeartBox", "caja con forma de corazón"),
    (("flex", "flexible", "curva", "doblada", "redondeada"), "FlexBox",
     "caja con pared flexible (kerf bending)"),
    (("bisagra", "bisagras", "hinge", "con tapa abatible"), "HingeBox",
     "caja con bisagras integradas"),
    (("divisiones", "division", "compartimentos", "separadores",
      "para chocolates", "organizador"), "TypeTray",
     "bandeja con divisiones"),
    (("divisor", "divisoria", "divider"), "DividerTray",
     "bandeja con divisiones movibles"),
    # OJO con el orden: "tapa deslizante" es una caja con tapa CORREDIZA
    # (SlidingLidBox), no un cajón. Encontrado el 2026-08-05 con la frase real
    # de Anuar: "crea una caja con tapa deslizante de 15x15x3" daba un cajón.
    (("tapa deslizante", "tapa corrediza", "tapa que desliza",
      "tapa deslizable", "sliding lid"), "SlidingLidBox",
     "caja con tapa corrediza"),
    (("cajon", "cajón", "gaveta", "que se desliza", "corredizo"), "SlidingDrawer",
     "cajón que se desliza"),
    (("redonda", "redondeada", "esquinas redondas"), "RoundedBox",
     "caja de esquinas redondeadas"),
    (("hexagonal", "hexagono", "hexágono"), "RoundedRegularBox",
     "caja de lados regulares"),
    (("dados", "dado", "dice"), "DiceBox", "caja para dados"),
    (("cartas", "naipes", "card"), "CardBox", "caja para cartas"),
    (("libro", "book"), "FlexBook", "caja tipo libro"),
    (("castillo", "castle"), "Castle", "castillo armable"),
    (("casa de pajaros", "pajarera", "birdhouse"), "BirdHouse", "casa de pájaros"),
    (("moneda", "alcancia", "alcancía"), "CoinBankSafe", "alcancía con caja fuerte"),
    (("bandeja", "charola", "tray"), "BinTray", "bandeja simple"),
    (("compartimento", "compartimentos"), "CompartmentBox",
     "caja con compartimentos"),
    (("cerrada", "cerrado", "closed"), "ClosedBox", "caja cerrada por todos lados"),
    (("caja", "cajita", "box"), "ClosedBox", "caja rectangular"),   # el default
)

# Cómo pide la TAPA. boxes.py usa: closed / hole / lid
TAPAS = (
    (("agujero", "hoyo", "abierta arriba", "sin tapa arriba", "hole",
      "boca", "sin tapa"), "hole"),
    # "sobrepuesta" es como Anuar la pide (2026-08-05): tapa que se pone
    # encima, aparte de la caja. En boxes.py eso es "lid".
    (("sobrepuesta", "sobre puesta", "encimada", "tapa suelta", "tapa aparte",
      "con tapa", "lid", "tapa independiente"), "lid"),
    (("cerrada", "closed", "sellada", "sin abrir"), "closed"),
)


def que_generador(pedido: str) -> tuple:
    """Del pedido en español al generador. Devuelve (nombre, descripción)."""
    p = (pedido or "").lower()
    for claves, gen, desc in CATALOGO:
        if any(k in p for k in claves):
            return gen, desc
    return "", ""


def que_tapa(pedido: str) -> str:
    p = (pedido or "").lower()
    for claves, valor in TAPAS:
        if any(k in p for k in claves):
            return valor
    return "closed"


def que_medidas(pedido: str) -> dict:
    """Saca las medidas del pedido. Anuar las dice en CM, boxes.py pide MM.

    Formas reales suyas: "de 45x7", "40x30x7 cm", "de 45 cm x 7 cm".
    """
    p = (pedido or "").lower().replace("×", "x")
    nums = [float(n) for n in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:cm)?\s*(?=x|\b)",
                                         p.replace(",", "."))]
    # Se descartan los que claramente no son medidas (año, cantidades sueltas).
    nums = [n for n in nums if 1 <= n <= 300]
    return {"x": nums[0] * 10 if len(nums) >= 1 else 0,      # cm → mm
            "h": nums[-1] * 10 if len(nums) >= 2 else 0,
            "y": nums[1] * 10 if len(nums) >= 3 else 0}


def generar(pedido: str, grosor_mm: float = 2.7) -> dict:
    """Genera la caja que se pidió en español. No adivina: si falta algo, lo dice."""
    gen, desc = que_generador(pedido)
    if not gen:
        return {"status": "NO_SE_CUAL",
                "detalle": ("No supe qué caja es. Dime el tipo: corazón, con "
                            "divisiones, con bisagras, redondeada, tipo libro, "
                            "para dados, para cartas...")}

    med = que_medidas(pedido)
    if not med["x"]:
        return {"status": "FALTAN_MEDIDAS",
                "generador": gen,
                "detalle": (f"Sí puedo hacer la {desc}, pero necesito las "
                            "medidas. Dímelas así: «45x7» (ancho x alto en cm).")}

    try:
        import boxes.generators
    except ImportError:
        return {"status": "FALTA_LIBRERIA",
                "detalle": "Falta boxes.py: pip install boxes"}

    gens = boxes.generators.getAllBoxGenerators()
    clase = next((v for k, v in gens.items() if k.split(".")[-1] == gen), None)
    if clase is None:
        return {"status": "ERROR", "detalle": f"boxes.py no trae '{gen}'."}

    tapa = que_tapa(pedido)
    b = clase()
    # Cada generador acepta parámetros distintos: TypeTray usa sx/sy, HeartBox
    # usa x/h. Se arma la lista y se filtra POR PARES — la primera versión
    # quitaba la bandera y dejaba el valor huérfano, y boxes.py se quejaba con
    # "unrecognized arguments: 400 300" (2026-08-05).
    acepta = {a.dest for a in b.argparser._actions}
    deseados = [("thickness", str(grosor_mm)), ("x", str(int(med["x"])))]
    if med["h"]:
        deseados.append(("h", str(int(med["h"]))))
    if med["y"]:
        deseados.append(("y", str(int(med["y"]))))
    if "top" in acepta:
        deseados.append(("top", tapa))
    # Las bandejas piden el tamaño por celdas, no por lados.
    if "sx" in acepta and med["x"]:
        deseados.append(("sx", f"{int(med['x'])/3:.0f}*3"))
    if "sy" in acepta and (med["y"] or med["h"]):
        lado = med["y"] or med["h"]
        deseados.append(("sy", f"{int(lado)/2:.0f}*2"))

    args = []
    for clave, valor in deseados:
        if clave in acepta:
            args += [f"--{clave}", valor]

    try:
        b.parseArgs(args)
        b.open()
        b.render()
        datos = b.close()
    except SystemExit:
        # argparse llama a sys.exit cuando no le gustan los argumentos: eso
        # mataría el proceso de AURORA entero si no se atrapa aquí.
        return {"status": "ERROR",
                "detalle": (f"El generador '{gen}' no aceptó esas medidas. "
                            "Dímelas de otra forma, o pide otro tipo de caja.")}
    except Exception as e:
        return {"status": "ERROR",
                "detalle": f"boxes.py no pudo generarla: {type(e).__name__}: {str(e)[:150]}"}

    # close() DEVUELVE los datos (BytesIO), no escribe el archivo. Ese fue el
    # bug que hacía que "se generara" sin dejar nada en el disco.
    crudo = datos.getvalue() if hasattr(datos, "getvalue") else datos
    if not crudo:
        return {"status": "ERROR", "detalle": "boxes.py no devolvió nada."}

    DESTINO.mkdir(parents=True, exist_ok=True)
    base = (f"{gen}_{int(med['x']/10)}x{int(med['h']/10) if med['h'] else 0}"
            f"_{grosor_mm:g}mm" + (f"_{tapa}" if tapa != "closed" else ""))
    salida = DESTINO / f"{base}.svg"
    n = 2
    while salida.exists():
        salida = DESTINO / f"{base}__{n}.svg"
        n += 1
    salida.write_bytes(crudo if isinstance(crudo, bytes) else str(crudo).encode())

    # Se muestran las TRES medidas cuando las hay: esconder el fondo hacía
    # dudar de si se había usado. "10 x 9 x 7" salía como "10 × 7" (2026-08-05).
    partes = [f"{med['x']/10:g}"]
    if med["y"]:
        partes.append(f"{med['y']/10:g}")
    if med["h"]:
        partes.append(f"{med['h']/10:g}")
    return {"status": "OK", "generador": gen, "que_es": desc, "tapa": tapa,
            "archivo": str(salida), "kb": round(salida.stat().st_size / 1024, 1),
            "medidas_cm": " × ".join(partes)}


def _texto(r: dict) -> str:
    if r.get("status") == "OK":
        return (f"📦 **{r['que_es'].capitalize()}** — {r['medidas_cm']} cm\n"
                f"   generador: `{r['generador']}` · tapa: {r['tapa']}\n\n"
                f"📁 `{r['archivo']}`  ({r['kb']} KB)\n"
                f"_Es SVG: lo abre Corel y RDWorks directo. "
                f"Ábrelo para revisarlo antes de cortar._")
    return r.get("detalle", "No pude generarla.")


def listar() -> str:
    lineas = ["Cajas que puedo generar, y cómo pedírmelas:\n"]
    vistos = set()
    for claves, gen, desc in CATALOGO:
        if gen in vistos:
            continue
        vistos.add(gen)
        lineas.append(f"  • **{desc}** — di «{claves[0]}»")
    lineas.append("\nEjemplo: «caja corazón con tapa de agujero de 45x7»")
    return "\n".join(lineas)


if __name__ == "__main__":
    _consola_utf8()
    if "--lista" in sys.argv:
        print(listar())
    elif len(sys.argv) > 1:
        print(_texto(generar(" ".join(sys.argv[1:]))))
    else:
        print(__doc__)
