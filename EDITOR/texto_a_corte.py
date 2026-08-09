# -*- coding: utf-8 -*-
"""AURORA · Texto a vinil de recorte: palabras convertidas en líneas de corte

Anuar lo pidió el 2026-08-08: *"la palabra cocacola y el nombre oswaldo en un
área de 30x20 en vinil DE RECORTE"*.

QUÉ TIENE DE DISTINTO A ESCRIBIR EN CORel: aquí el texto sale ya convertido a
curvas, encajado exacto en el área que se pide, y —lo que de verdad importa—
**medido**: la plotter no sabe de tipografía, sabe de trazos. Un script bonito
con patines de 0.4 mm se corta perfecto y es imposible de despicar. Este
módulo lo dice ANTES de gastar vinil, no después.

LO QUE SE MIDE Y POR QUÉ:
  • grosor de trazo  → menos de 1 mm en vinil de recorte no se despica
  • contornos        → cada hueco (la panza de la «o», de la «a») es material
                       que hay que sacar a mano: son los minutos del trabajo
  • largo de corte   → el tiempo de máquina

Correr:
    python EDITOR/texto_a_corte.py "cocacola" "oswaldo" --area 30x20
    python EDITOR/texto_a_corte.py "oswaldo" --area 300x200 --mm
    python EDITOR/texto_a_corte.py --fuentes
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SALIDA = Path.home() / "Downloads"

# Debajo de esto el vinil de recorte no se despica sin romperse. No es un
# número de manual: es el piso práctico de una Cameo con cuchilla nueva.
TRAZO_MINIMO_MM = 1.0
MARGEN_MM = 3.0          # aire entre el texto y la orilla del área
INTERLINEA = 0.25        # separación entre renglones, en altos de renglón

# Las cursivas que de verdad están instaladas en su PC. La primera es la que
# más se parece al trazo continuo de una etiqueta de refresco.
CURSIVAS = ("Freehand521 BT", "Alex Brush", "Segoe Script", "Ink Free",
            "Gabriola")


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def fuentes(solo_cursivas: bool = False) -> list:
    """Las tipografías instaladas de verdad, no las que debería haber."""
    from matplotlib import font_manager as fm
    hay = sorted({f.name for f in fm.fontManager.ttflist})
    if solo_cursivas:
        return [f for f in CURSIVAS if f in hay]
    return hay


def _archivo_fuente(nombre: str):
    from matplotlib import font_manager as fm
    for f in fm.fontManager.ttflist:
        if f.name.lower() == nombre.lower():
            return f.fname
    return None


def _contornos(texto: str, fuente: str, tam: float = 100.0):
    """Las curvas reales de la palabra: lista de contornos [(x, y), ...]."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties

    ruta = _archivo_fuente(fuente)
    fp = FontProperties(fname=ruta) if ruta else FontProperties(family=fuente)
    tp = TextPath((0, 0), texto, size=tam, prop=fp)
    return [c for c in tp.to_polygons() if len(c) >= 3]


def _caja(contornos):
    xs = [p[0] for c in contornos for p in c]
    ys = [p[1] for c in contornos for p in c]
    return min(xs), min(ys), max(xs), max(ys)


def _poligonos(contornos):
    """Arma los contornos como figuras con hueco, para poder medirlos.

    Un contorno que cae dentro de otro es un hueco (la panza de la «o»), no
    una figura aparte. Sin esto, el grosor de trazo saldría mal.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    brutos = []
    for c in contornos:
        try:
            p = Polygon(c)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty and p.area > 0:
                brutos.append(p)
        except Exception:
            continue
    if not brutos:
        return None
    brutos.sort(key=lambda p: p.area, reverse=True)
    fuera, dentro = [], []
    for p in brutos:
        if any(g.contains(p.representative_point()) for g in fuera):
            dentro.append(p)
        else:
            fuera.append(p)
    forma = unary_union(fuera)
    for h in dentro:
        forma = forma.difference(h)
    return forma


def _anillos(forma):
    """Los contornos ya soldados: la orilla de fuera y cada hueco, nada más.

    Después de unir, lo que queda son las líneas que la plotter debe recorrer.
    Todo lo demás eran empalmes entre letras que no van cortados.
    """
    if forma is None or forma.is_empty:
        return []
    partes = list(getattr(forma, "geoms", [forma]))
    anillos = []
    for p in partes:
        if p.geom_type != "Polygon":
            continue
        anillos.append([(x, y) for x, y in p.exterior.coords])
        for h in p.interiors:
            anillos.append([(x, y) for x, y in h.coords])
    return anillos


def _grosor(forma) -> dict:
    """Qué tan delgado es lo más delgado. Es la pregunta del despicado.

    Se estima con área entre perímetro —para un trazo largo y angosto,
    2·área/perímetro ES el ancho— y se comprueba erosionando: si al comerle
    medio milímetro por lado la figura se parte o desaparece, hay trazos por
    debajo de ese milímetro.
    """
    if forma is None or forma.is_empty:
        return {"promedio": 0.0, "sobrevive": False}
    per = forma.length or 1.0
    prom = 2.0 * forma.area / per
    erosionada = forma.buffer(-TRAZO_MINIMO_MM / 2.0)
    return {"promedio": round(prom, 2),
            "sobrevive": (not erosionada.is_empty)
            and erosionada.area > forma.area * 0.05}


def generar(textos, ancho_mm: float, alto_mm: float,
            fuente: str = "", salida: Path | None = None,
            margen_mm: float = MARGEN_MM) -> dict:
    """Deja los renglones convertidos a curvas y encajados en el área.

    El texto se escala PARA CABER, sin deformarse: el mismo factor en X y en
    Y. Deformar una letra para llenar el rectángulo es el error de principiante
    que se ve a un metro de distancia.
    """
    import ezdxf

    if isinstance(textos, str):
        textos = [textos]
    textos = [t for t in textos if t.strip()]
    if not textos:
        return {"status": "SIN_TEXTO"}

    disponibles = fuentes(solo_cursivas=True) or fuentes()
    if not fuente:
        fuente = disponibles[0]
    elif not _archivo_fuente(fuente):
        return {"status": "SIN_FUENTE", "detalle": fuente,
                "hay": disponibles}

    # 1 · las curvas de cada renglón, todavía en tamaño de trabajo
    renglones = []
    for t in textos:
        c = _contornos(t, fuente)
        if not c:
            return {"status": "SIN_CURVAS", "detalle": t}
        renglones.append(c)

    # 2 · apilarlos centrados, midiendo cada uno por su propia caja
    cajas = [_caja(c) for c in renglones]
    altos = [c[3] - c[1] for c in cajas]
    anchos = [c[2] - c[0] for c in cajas]
    hueco = max(altos) * INTERLINEA
    total_alto = sum(altos) + hueco * (len(renglones) - 1)
    total_ancho = max(anchos)

    puestos, y = [], total_alto
    for c, (x0, y0, x1, y1), an, al in zip(renglones, cajas, anchos, altos):
        y -= al
        dx = (total_ancho - an) / 2.0 - x0      # centrado horizontal
        dy = y - y0
        puestos.append([[(p[0] + dx, p[1] + dy) for p in cont] for cont in c])
        y -= hueco

    # 3 · escalar para caber en el área pedida, sin deformar
    util_w = ancho_mm - 2 * margen_mm
    util_h = alto_mm - 2 * margen_mm
    if util_w <= 0 or util_h <= 0:
        return {"status": "AREA_MUY_CHICA",
                "detalle": f"{ancho_mm}×{alto_mm} mm no deja nada con "
                           f"{margen_mm} mm de margen"}
    k = min(util_w / total_ancho, util_h / total_alto)
    ox = margen_mm + (util_w - total_ancho * k) / 2.0
    oy = margen_mm + (util_h - total_alto * k) / 2.0

    finales = []
    for renglon in puestos:
        for cont in renglon:
            finales.append([(p[0] * k + ox, p[1] * k + oy) for p in cont])

    # 4 · SOLDAR. En una cursiva las letras se encaballan, y cada empalme deja
    # una línea por dentro de la letra. La plotter no sabe que es un empalme:
    # la corta, y parte la letra. Es el «soldar/weld» que se hace a mano en
    # Corel antes de mandar a cortar, y aquí va solo.
    forma = _poligonos(finales)
    soldados = _anillos(forma)
    if soldados:
        antes, finales = len(finales), soldados
    else:
        antes = len(finales)

    # 5 · medir lo que le importa a la plotter
    g = _grosor(forma)
    largo = round(sum(
        sum(((c[i + 1][0] - c[i][0]) ** 2 + (c[i + 1][1] - c[i][1]) ** 2) ** .5
            for i in range(len(c) - 1)) for c in finales) / 10.0, 1)  # cm

    # 6 · el DXF, en milímetros, todo cerrado
    doc = ezdxf.new(setup=True)
    doc.header["$INSUNITS"] = 4                       # 4 = milímetros
    msp = doc.modelspace()
    if "CORTE" not in doc.layers:
        doc.layers.add("CORTE", color=1)
    for c in finales:
        msp.add_lwpolyline([(round(x, 3), round(y, 3)) for x, y in c],
                           close=True, dxfattribs={"layer": "CORTE"})

    base = "_".join(t.strip().replace(" ", "-") for t in textos)[:40]
    dest = Path(salida) if salida else SALIDA / (
        f"{base}_{ancho_mm:g}x{alto_mm:g}mm_recorte.dxf")
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(dest)

    png = _vista_previa(finales, ancho_mm, alto_mm, dest.with_suffix(".png"))

    return {"status": "OK", "archivo": str(dest), "png": png,
            "fuente": fuente, "contornos": len(finales),
            "soldados": antes - len(finales),
            "alto_letra_mm": round(max(altos) * k, 1),
            "ancho_texto_mm": round(total_ancho * k, 1),
            "alto_texto_mm": round(total_alto * k, 1),
            "trazo_mm": g["promedio"], "despicable": g["sobrevive"],
            "largo_corte_cm": largo, "textos": textos,
            "area": f"{ancho_mm:g} × {alto_mm:g} mm"}


def _vista_previa(contornos, ancho_mm, alto_mm, dest: Path) -> str:
    """El PNG para verlo antes de cortar. Fue idea de Rocío para las cajas y
    sirve igual aquí: se ve de un vistazo si el texto quedó chueco o apretado."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon as MplPoly

        fig, ax = plt.subplots(figsize=(ancho_mm / 25.4, alto_mm / 25.4))
        for c in contornos:
            ax.add_patch(MplPoly(c, closed=True, facecolor="#1a1a1a",
                                 edgecolor="#d40000", linewidth=0.4))
        ax.set_xlim(0, ancho_mm)
        ax.set_ylim(0, alto_mm)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.savefig(dest, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return str(dest)
    except Exception:
        return ""


def _texto(r: dict) -> str:
    s = r.get("status")
    if s == "SIN_FUENTE":
        return (f"No tienes instalada «{r['detalle']}».\n"
                f"Cursivas que sí hay: {', '.join(r['hay'])}")
    if s != "OK":
        return f"No se pudo: {r.get('detalle', s)}"

    t = [f"✂️ **{' + '.join(r['textos'])}** listo para vinil de recorte\n",
         f"   {r['archivo']}",
         f"   tipografía **{r['fuente']}** · área {r['area']}",
         f"   texto de **{r['ancho_texto_mm']} × {r['alto_texto_mm']} mm**, "
         f"letra de {r['alto_letra_mm']} mm de alto",
         f"   **{r['contornos']} contornos** · {r['largo_corte_cm']} cm de corte"
         + (f" · soldado: {r['soldados']} empalmes quitados"
            if r.get("soldados") else ""),
         f"   grosor de trazo: **{r['trazo_mm']} mm** en promedio"]
    if r["despicable"]:
        t.append("\n✅ Se despica: no hay trazos por debajo de "
                 f"{TRAZO_MINIMO_MM} mm.")
    else:
        t.append(f"\n⚠️ **Hay trazos más delgados que {TRAZO_MINIMO_MM} mm.** "
                 "En vinil de recorte eso se corta bien pero se rompe al "
                 "despicarlo. Sube el tamaño, usa una letra más gorda, o "
                 "córtalo en impreso en vez de recorte.")
    if r.get("png"):
        t.append(f"\n🖼️ Vista previa: {r['png']}")
    t.append("\n_Corta una prueba en retazo antes de la pieza buena._")
    return "\n".join(t)


def main() -> int:
    _consola_utf8()
    args = sys.argv[1:]
    if "--fuentes" in args:
        print("Cursivas instaladas:")
        for f in fuentes(solo_cursivas=True):
            print("   •", f)
        return 0

    textos, ancho, alto, fuente, en_mm = [], 300.0, 200.0, "", False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--area" and i + 1 < len(args):
            p = args[i + 1].lower().replace(",", ".").split("x")
            ancho, alto = float(p[0]), float(p[1]); i += 1
        elif a == "--fuente" and i + 1 < len(args):
            fuente = args[i + 1]; i += 1
        elif a == "--mm":
            en_mm = True
        elif not a.startswith("--"):
            textos.append(a)
        i += 1

    if not textos:
        print(__doc__)
        return 1
    if not en_mm:                      # sin --mm, los números vienen en cm
        ancho, alto = ancho * 10, alto * 10
    print(_texto(generar(textos, ancho, alto, fuente)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
