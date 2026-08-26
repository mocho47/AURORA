# -*- coding: utf-8 -*-
"""AURORA · Los 189 generadores de boxes.py, con el vocabulario de Anuar

Anuar lo recordó el 2026-08-05: boxes.py tiene caja corazón, con flex, con
bisagras — no un solo modelo. Y marcó la prioridad: *"que TÚ la enseñes a usar
boxes.py, no que ella aprenda con el uso"*. Por eso esto NO descubre nada solo:
trae el mapa escrito de qué generador corresponde a cómo él pide las cajas.

Bug que costó encontrarlo (2026-08-05): `Boxes.close()` DEVUELVE los datos en un
BytesIO, no escribe el archivo. Por eso la primera prueba no generaba nada y
tampoco tiraba error.

Salidas nativas de boxes.py: svg, ps, lbrn2 — no trae DXF de fábrica. Pero
`generar()` SÍ entrega DXF real: convierte el SVG con `EDITOR/imagen_a_dxf.py`
(Inkscape por dentro), con unidades en mm declaradas y capas CORTE/GRABADO
separadas. El SVG se conserva de respaldo, no como salida final.

Correr:  python TALLER/cajas_boxes.py "caja corazon con tapa de agujero de 45x7"
         python TALLER/cajas_boxes.py --lista
"""
from __future__ import annotations
import io
import math
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
# LOS NUMEROS DE ANUAR NO SE ESCRIBEN AQUI.
#
# Aqui decia `VELOCIDAD_MM_S = 25.0` y `COSTO_MINUTO = 8.0`, copiados a mano.
# El 13-ago Anuar dicto 20 mm/s -y lo dejo escrito en el catalogo, resolviendo
# el conflicto entre el 15 que decia el catalogo y el 25 que usaba el
# cotizador- pero esta copia se quedo en 25. Resultado real: cada caja generada se cotizaba con 20% menos de tiempo de corte
# del real. Este archivo SI se usa: es el que llama el chat.
#
# Se leen de TALLER/formula_precios.py, que a su vez los lee de
# CONFIG/catalogo_servicios.json, donde el los dicto. Si manana cambia el
# minuto de laser, cambia en un lugar y el sistema entero queda parejo.
def _numero(clave: str) -> float:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "formula_precios", RAIZ / "TALLER" / "formula_precios.py")
    _fp = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_fp)
    return _fp.numero(clave)


VELOCIDAD_MM_S = _numero("velocidad_mm_s")
COSTO_MINUTO = _numero("minuto_corte")


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
    # Añadido el 2026-08-20: de los 189 generadores de boxes.py solo 20 tenían
    # palabra en español. Estos son los que de verdad sirven para vender
    # (exhibidores, marcos, organizadores) — verificados uno por uno contra
    # boxes.generators para confirmar que aceptan x/y/h antes de agregarlos.
    (("marco de fotos", "portarretrato", "porta retrato"), "PhotoFrame",
     "marco para fotos"),
    (("vitrina", "caja vitrina"), "DisplayCase",
     "vitrina cerrada para exhibir"),
    (("marco con fondo", "shadowbox", "cuadro para figuras", "cuadro sombra"),
     "Shadowbox", "marco tipo shadowbox, con fondo para pegar figuras"),
    (("exhibidor de monedas", "presumidero de monedas"), "CoinDisplay",
     "exhibidor de monedas"),
    (("repisa exhibidora", "anaquel exhibidor"), "DisplayShelf",
     "repisa exhibidora"),
    (("revistero", "organizador de revistas"), "MagazineFile", "revistero"),
    (("cubertero", "organizador de cubiertos"), "Silverware",
     "organizador de cubiertos"),
    (("lampara triangular", "lámpara triangular"), "TriangleLamp",
     "lámpara triangular"),
    (("contenedor apilable", "bin apilable"), "StackableBin",
     "contenedor apilable para organizar"),
    (("carpeta organizadora", "sobre organizador"), "Folder",
     "carpeta/sobre organizador"),
    (("caja para hojas", "caja de papel"), "PaperBox",
     "caja para papel u hojas"),
    (("charola de piezas pequeñas", "organizador de tornillos"),
     "SmallPartsTray", "charola para piezas pequeñas (tornillos, tuercas)"),
    (("insert organizador", "charola insert"), "TrayInsert",
     "insert organizador para meter dentro de otra caja"),
    # Segunda tanda, mismo día 2026-08-20 — mismo criterio: solo lo que acepta
    # x/y/h directo (nada de generadores que solo aceptan radius/diameter o que
    # no traen ningún parámetro de tamaño; esos quedan pendientes de raíz).
    (("caja de dos piezas", "tapa que cubre la base", "caja tapa y base"),
     "TwoPiece", "caja de regalo de dos piezas (la tapa cubre la base)"),
    (("atril para volantes", "exhibidor de folletos", "porta volantes"),
     "Display", "exhibidor de pie para volantes o folletos"),
    (("huacal", "cajon con asas", "cajón con asas", "caja tipo huacal"),
     "Crate", "huacal con asas, se puede hacer apilable"),
    (("dispensador", "dispensador de servilletas"), "Dispenser",
     "dispensador para cosas planas apiladas (servilletas, posavasos)"),
    # "caja abierta" tiene que ir ANTES del catch-all genérico de "caja" de más
    # abajo — si no, cualquier "caja abierta..." caería en ClosedBox primero.
    (("caja abierta", "charola abierta"), "OpenBox",
     "caja con la tapa y el frente abiertos"),
    (("consola de pared", "repisa con panel inclinado"), "Console",
     "consola de pared con panel inclinado"),
    (("caja con cortina enrollable", "caja persiana", "caja rolltop"),
     "ShutterBox", "caja con cortina enrollable tipo persiana"),
    (("porta notas", "organizador de papel apilado", "porta posavasos"),
     "NotesHolder", "organizador para una pila de papel o posavasos"),
    (("contenedor de pared apilable", "bin de pared"), "WallStackableBin",
     "contenedor de pared, apilable o colgante"),
    (("vinatera", "botellero", "portabotellas de vino"), "WineRack",
     "vinatera / portabotellas"),
    # BreadBox ("panera") NO se agregó: probado en vivo el 2026-08-20, su SVG
    # cuelga a Inkscape de verdad al convertirlo a DXF (reproducido aislado,
    # >40s sin terminar, no es lentitud normal). Bug real de la geometría
    # curva de ese generador contra el exportador DXF de Inkscape, sin
    # resolver — no agregar hasta encontrar la causa o un conversor distinto.
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


# ── LÁMPARA DE MEDIA LUNA — no es un generador de boxes.py, es una pieza
# custom (pedido real de una clienta, 2026-08-21: "1m de diámetro x 50 de
# altura, 4 tiras LED (2 cálidas, 2 frías), doble apagador, puerto USB,
# soporte de celular integrado"). Se resuelve aparte, con ezdxf directo,
# porque boxes.py no trae ningún generador de arco/media luna (confirmado
# contra boxes.generators, ninguno de los 189 sirve).
_MEDIA_LUNA_TRIGGERS = ("media luna", "medialuna", "lampara de arco",
                        "lampara arco", "half moon")


def _medida_mm(texto: str, i: int, default: float = 0.0) -> float:
    """i-ésimo número del texto, en mm. Entiende m/metro y cm (cm es el default)."""
    nums = re.findall(r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m\b|metro[s]?)?", texto)
    nums = [(float(n.replace(",", ".")), u) for n, u in nums if n]
    if i >= len(nums):
        return default
    val, unidad = nums[i]
    if unidad in ("m", "metro", "metros"):
        return val * 1000
    if unidad == "mm":
        return val
    return val * 10  # cm, o sin unidad (default de Anuar)


def _generar_lampara_media_luna(pedido: str, grosor_mm: float = 9.0) -> dict:
    """Cuerpo de madera en forma de media luna: 2 costados + costillas + base.

    El difusor (acrílico delgado que cubre las tiras LED) NO se corta en
    madera — se entrega la medida real para que Anuar lo consiga y lo doble
    en caliente sobre el arco, que es como se hace este tipo de lámpara.
    """
    diametro = _medida_mm(pedido, 0, default=1000.0)
    altura = _medida_mm(pedido, 1, default=diametro / 2)
    # El cuerpo de una lámpara así carga su propio peso de pie: 2.7mm (el
    # grosor genérico de las cajas) se vencería. Si nadie pidió un grosor
    # real (>4mm) en la frase, se usa 9mm de madera y se le aplica el MISMO
    # kerf que a las cajas (el láser se come ~0.2mm por lado).
    grosor_material = grosor_mm if grosor_mm > 4.0 else 9.0
    T = round(max(0.5, grosor_material - KERF_MM), 2)
    R_OUT = diametro / 2
    R_IN = R_OUT - diametro * 0.07          # banda ~7% del diámetro
    DEPTH = diametro * 0.07                 # profundidad del cuerpo
    RIB_W = 25.0
    N_RIBS = 7
    ANG_INI, ANG_FIN = 20, 160

    try:
        import ezdxf
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    out = ezdxf.new("R2010")
    out.units = ezdxf.units.MM
    out.header["$INSUNITS"] = 4
    for name, color in (("COSTADO", 1), ("BASE", 3), ("COSTILLAS", 5)):
        out.layers.add(name, color=color)
    msp = out.modelspace()

    def arco_pts(r, a0, a1, n=80):
        return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]

    def costado(offset_x):
        pts = [(R_OUT, 0)] + arco_pts(R_OUT, 0, 180) + [(-R_IN, 0)] \
            + arco_pts(R_IN, 180, 0) + [(R_OUT, 0)]
        msp.add_lwpolyline([(x + offset_x, y) for x, y in pts], close=True,
                            dxfattribs={"layer": "COSTADO"})
        r_mid = (R_OUT + R_IN) / 2
        for i in range(N_RIBS):
            ang = math.radians(ANG_INI + (ANG_FIN - ANG_INI) * i / (N_RIBS - 1))
            cx, cy = r_mid * math.cos(ang), r_mid * math.sin(ang)
            tx, ty = -math.sin(ang), math.cos(ang)
            rx, ry = math.cos(ang), math.sin(ang)
            hw = RIB_W / 2
            esq = [(cx - hw * tx - T / 2 * rx, cy - hw * ty - T / 2 * ry),
                   (cx + hw * tx - T / 2 * rx, cy + hw * ty - T / 2 * ry),
                   (cx + hw * tx + T / 2 * rx, cy + hw * ty + T / 2 * ry),
                   (cx - hw * tx + T / 2 * rx, cy - hw * ty + T / 2 * ry)]
            msp.add_lwpolyline([(x + offset_x, y) for x, y in esq], close=True,
                                dxfattribs={"layer": "COSTADO"})

    costado(0)
    costado(diametro + 300)   # el 2do costado (idéntico) aparte, para cortar 2 piezas

    rib_len = DEPTH + 2 * T
    for i in range(N_RIBS):
        x0 = 2 * (diametro + 300) + i * (RIB_W + 15)
        msp.add_lwpolyline([(x0, 0), (x0 + RIB_W, 0), (x0 + RIB_W, rib_len),
                            (x0, rib_len)], close=True, dxfattribs={"layer": "COSTILLAS"})

    base_w = diametro + 80
    base_d = DEPTH + 90
    bx0, by0 = 0, -(R_OUT + 150)
    msp.add_lwpolyline([(bx0, by0), (bx0 + base_w, by0), (bx0 + base_w, by0 + base_d),
                        (bx0, by0 + base_d)], close=True, dxfattribs={"layer": "BASE"})
    cx_base = bx0 + base_w / 2
    for side_off in (-DEPTH / 2, DEPTH / 2):
        for foot_cx in (cx_base - (R_OUT - 35), cx_base + (R_OUT - 35)):
            y_c = by0 + base_d / 2 + side_off
            msp.add_lwpolyline([(foot_cx - 35, y_c - T / 2), (foot_cx + 35, y_c - T / 2),
                                (foot_cx + 35, y_c + T / 2), (foot_cx - 35, y_c + T / 2)],
                                close=True, dxfattribs={"layer": "BASE"})
    # soporte de celular: ranura angulada al frente de la base
    ang_ph = math.radians(75)
    dx, dy = math.cos(ang_ph) * 60, math.sin(ang_ph) * 60
    px, py = cx_base, by0 + 15
    msp.add_lwpolyline([(px - 9, py), (px + 9, py), (px + 9 + dx, py + dy),
                        (px - 9 + dx, py + dy)], close=True, dxfattribs={"layer": "BASE"})
    # 2 apagadores (mini rocker 19.2x13mm) + 1 puerto USB (13x7mm) — AJUSTAR a la pieza real que compre
    sw_y = by0 + base_d - 20
    for swx in (cx_base - 120, cx_base - 60):
        msp.add_lwpolyline([(swx - 9.6, sw_y - 6.5), (swx + 9.6, sw_y - 6.5),
                            (swx + 9.6, sw_y + 6.5), (swx - 9.6, sw_y + 6.5)],
                            close=True, dxfattribs={"layer": "BASE"})
    msp.add_lwpolyline([(cx_base + 53.5, sw_y - 3.5), (cx_base + 66.5, sw_y - 3.5),
                        (cx_base + 66.5, sw_y + 3.5), (cx_base + 53.5, sw_y + 3.5)],
                        close=True, dxfattribs={"layer": "BASE"})

    DESTINO_DXF = _destino_dxf()
    DESTINO_DXF.mkdir(parents=True, exist_ok=True)
    salida = DESTINO_DXF / f"lampara_media_luna_{int(diametro/10)}x{int(altura/10)}cm.dxf"
    n = 2
    while salida.exists():
        salida = salida.parent / f"lampara_media_luna_{int(diametro/10)}x{int(altura/10)}cm__{n}.dxf"
        n += 1
    out.saveas(str(salida))

    difusor_mm = math.pi * ((R_OUT + R_IN) / 2)

    r = {"status": "OK", "generador": "lampara_media_luna",
         "que_es": "lámpara de media luna con canal para difusor LED",
         "tapa": "-", "archivo": str(salida), "dxf": str(salida),
         "kb": round(salida.stat().st_size / 1024, 1),
         "kb_dxf": round(salida.stat().st_size / 1024, 1),
         "medidas_cm": f"{diametro/10:g} diámetro × {altura/10:g} alto",
         "grosor_material": grosor_material, "grosor_corte": T, "dedos": None,
         "difusor_mm": round(difusor_mm, 1),
         "n_costillas": N_RIBS, "profundidad_mm": round(DEPTH, 1)}

    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("imagen_a_dxf", RAIZ / "EDITOR" / "imagen_a_dxf.py")
        iad = _ilu.module_from_spec(spec)
        spec.loader.exec_module(iad)
        v = iad.vista_previa(salida)
        if v.get("status") == "OK":
            r["vista"] = v["archivo"]
    except Exception as e:
        r["dxf_fallo"] = f"vista previa: {type(e).__name__}: {str(e)[:90]}"

    return r


def _destino_dxf() -> Path:
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("carpetas_por_tipo",
                                            RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de("dxf")
    except Exception:
        d = Path.home() / "Downloads" / "dxf"
        d.mkdir(parents=True, exist_ok=True)
        return d


def generar(pedido: str, grosor_mm: float = 2.7,
            quiere_dxf: bool = True) -> dict:
    """Genera la caja que se pidió en español. No adivina: si falta algo, lo dice."""
    p_bajo = (pedido or "").lower()
    if any(k in p_bajo for k in _MEDIA_LUNA_TRIGGERS) and "lampara" in p_bajo.replace("á", "a"):
        return _generar_lampara_media_luna(pedido, grosor_mm)

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


def _liga(ruta: str) -> str:
    """El enlace para BAJARLO, para quien no está en esta computadora.

    Rocío trabaja desde su PC (2026-08-06): la ruta de disco no le sirve de
    nada, necesita poder bajar el archivo. Aquí no se sabe la IP del servidor,
    así que se deja relativa: el navegador la resuelve contra el mismo lugar
    de donde cargó el panel, sea 127.0.0.1 o 192.168.1.38.
    """
    from urllib.parse import quote
    return f"  · [⬇️ bajar](/descargar?ruta={quote(str(ruta))})"


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return r.get("detalle", "No pude generarla.")

    t = (f"📦 **{r['que_es'].capitalize()}** — {r['medidas_cm']} cm\n"
         f"   generador: `{r['generador']}` · tapa: {r['tapa']}\n"
         f"   cortada a **{r['grosor_corte']} mm** para tu material de "
         f"{r['grosor_material']} mm _(compensación del láser)_\n\n")
    # El DXF va primero porque es el que él usa. El SVG queda de respaldo.
    if r.get("dxf"):
        t += (f"📁 **DXF:** `{r['dxf']}`  ({r['kb_dxf']} KB)"
              f"{_liga(r['dxf'])}\n"
              f"   _SVG también: `{r['archivo']}`_\n")
    else:
        t += f"📁 `{r['archivo']}`  ({r['kb']} KB){_liga(r['archivo'])}\n"
    if r.get("vista"):
        t += (f"👁️ **Míralo sin abrir nada:** `{r['vista']}`"
              f"{_liga(r['vista'])}\n")
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
