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

# Cada tipo a su carpeta: boxes.py entrega SVG, así que va a Descargas\svg.
# Anuar lo pidió el 2026-08-05: "los dxf a la carpeta dxf, los pdf a pdf y así
# sucesivamente, siempre". Antes esto guardaba SVG dentro de la carpeta dxf.
def _destino_svg() -> Path:
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("carpetas_por_tipo",
                                            RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de("svg")
    except Exception:
        d = Path.home() / "Downloads" / "svg"
        d.mkdir(parents=True, exist_ok=True)
        return d


DESTINO = _destino_svg()

# Lo que el láser se come del material al cortar. Anuar lo tiene medido en la
# práctica: mete 2.5 mm cuando su MDF es de 2.7 y las cejas entran justas.
KERF_MM = 0.2

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
    # "cofre" caía en la caja rectangular genérica (2026-08-05). boxes.py sí
    # trae uno: PirateChest, con la tapa curva de cofre.
    (("cofre", "cofrecito", "baul", "baúl", "tesoro", "pirata", "chest"),
     "PirateChest", "cofre con tapa curva"),
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

    EL ORDEN ES LEY, él lo fijó el 2026-08-06: *"siempre daré la medida de X al
    inicio, luego Y, y al final H"*. O sea "20x15x7" es ancho 20, fondo 15,
    alto 7 — nunca al revés. Esto no se adivina ni se reordena "por lógica":
    si una caja sale de 7 cm de ancho cuando él pidió 20, el DXF va a la basura
    y el material también.

    Con solo dos números ("45x7") es ancho y alto, que es como pide las cajas
    planas. Formas reales suyas: "de 45x7", "20x15x7 cm", "de 45 cm x 7 cm".
    """
    p = (pedido or "").lower().replace("×", "x")
    nums = [float(n) for n in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:cm)?\s*(?=x|\b)",
                                         p.replace(",", "."))]
    # Se descartan los que claramente no son medidas (año, cantidades sueltas).
    nums = [n for n in nums if 1 <= n <= 300]
    return {"x": nums[0] * 10 if len(nums) >= 1 else 0,      # cm → mm
            "h": nums[-1] * 10 if len(nums) >= 2 else 0,
            "y": nums[1] * 10 if len(nums) >= 3 else 0}


def generar(pedido: str, grosor_mm: float = 2.7,
            quiere_dxf: bool = True) -> dict:
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
    # LOS DOS AJUSTES QUE ANUAR HACE SIEMPRE A MANO (2026-08-06, dichos por él):
    #
    # 1) GROSOR 2.5 PARA MATERIAL DE 2.7 — no es un error, es COMPENSACIÓN DE
    #    KERF. El láser se come ~0.1 mm por lado, así que la ranura cortada a
    #    2.5 termina midiendo 2.7 real y la ceja entra justa. Sus palabras:
    #    "el material lo dejo en 2.5 aunque mi material es 2.7, queda perfecto".
    #    Por eso aquí entra el grosor REAL y la compensación se aplica sola: si
    #    algún día corta 3 mm, sale 2.8 sin que él tenga que acordarse.
    #
    # 2) DEDOS MÁS GRANDES — boxes.py trae 2.0 y él "le quita el punto" → 20.
    #    Menos dedos = menos arranques y frenadas del cabezal = menos tiempo de
    #    corte, que es lo que de verdad cuesta dinero en el taller.
    grosor_corte = round(max(0.5, grosor_mm - KERF_MM), 2)
    deseados = [("thickness", str(grosor_corte)), ("x", str(int(med["x"])))]
    #    OJO: no es un número fijo. Él lo corrigió el 2026-08-06: *"como en esta
    #    última caja tenía 1.0 el parámetro, yo solo quito el punto"*. O sea la
    #    regla es sobre lo que traiga ESE generador: 1.0→10, 2.0→20. Por eso se
    #    lee el default real en vez de escribir un número a mano.
    dedos_default = next((a.default for a in b.argparser._actions
                          if a.dest == "FingerJoint_finger"), None)
    dedos = None
    if dedos_default is not None:
        dedos = round(float(dedos_default) * 10, 2)
        deseados.append(("FingerJoint_finger", str(dedos)))
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
    # El nombre lleva las medidas EN SU ORDEN (x, y, h) y el grosor CON EL QUE
    # SE CORTÓ —2.5, no 2.7—, que es el dato que sirve para volver a cortarla
    # igual. Él lo pidió así el 2026-08-06: "es 2.5".
    lados = [str(int(med["x"] / 10))]
    if med["y"]:
        lados.append(str(int(med["y"] / 10)))
    if med["h"]:
        lados.append(str(int(med["h"] / 10)))
    base = (f"{gen}_{'x'.join(lados)}_{grosor_corte:g}mm"
            + (f"_{tapa}" if tapa != "closed" else ""))
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
    r = {"status": "OK", "generador": gen, "que_es": desc, "tapa": tapa,
         "archivo": str(salida), "kb": round(salida.stat().st_size / 1024, 1),
         "medidas_cm": " × ".join(partes),
         "grosor_material": grosor_mm, "grosor_corte": grosor_corte,
         "dedos": dedos}

    # SI SE PIDIÓ DXF, SE ENTREGA DXF. Anuar pidió "entrégala en dxf" y recibió
    # un SVG con la explicación de por qué (2026-08-05). Explicar la limitación
    # no es entregar el trabajo: el conversor ya existe, solo faltaba usarlo.
    if quiere_dxf:
        try:
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location("imagen_a_dxf",
                                                RAIZ / "EDITOR" / "imagen_a_dxf.py")
            iad = _ilu.module_from_spec(spec)
            spec.loader.exec_module(iad)
            dxf = iad._carpeta("dxf") / f"{salida.stem}.dxf"
            k = 2
            while dxf.exists():
                dxf = dxf.parent / f"{salida.stem}__{k}.dxf"
                k += 1
            rd = iad.svg_a_dxf(salida, dxf)
            if rd.get("status") == "OK":
                r["dxf"] = str(dxf)
                r["kb_dxf"] = round(dxf.stat().st_size / 1024, 1)
                # Y la vista previa, para verla sin abrir Corel (idea de Rocío).
                v = iad.vista_previa(dxf)
                if v.get("status") == "OK":
                    r["vista"] = v["archivo"]
            else:
                r["dxf_fallo"] = rd.get("detalle", "no se pudo convertir")
        except Exception as e:
            r["dxf_fallo"] = f"{type(e).__name__}: {str(e)[:90]}"
    return r


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return r.get("detalle", "No pude generarla.")

    t = (f"📦 **{r['que_es'].capitalize()}** — {r['medidas_cm']} cm\n"
         f"   generador: `{r['generador']}` · tapa: {r['tapa']}\n"
         f"   cortada a **{r['grosor_corte']} mm** para tu material de "
         f"{r['grosor_material']} mm _(compensación del láser)_\n\n")
    # El DXF va primero porque es el que él usa. El SVG queda de respaldo.
    if r.get("dxf"):
        t += (f"📁 **DXF:** `{r['dxf']}`  ({r['kb_dxf']} KB)\n"
              f"   _SVG también: `{r['archivo']}`_\n")
    else:
        t += f"📁 `{r['archivo']}`  ({r['kb']} KB)\n"
    if r.get("vista"):
        t += f"👁️ **Míralo sin abrir nada:** `{r['vista']}`\n"
    if r.get("dxf_fallo"):
        t += f"\n⚠️ No pude pasarlo a DXF: {r['dxf_fallo']}\n"
    return t + "\n_Ábrelo para revisarlo antes de cortar._"


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
