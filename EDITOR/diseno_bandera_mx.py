# -*- coding: utf-8 -*-
"""AURORA · El diseño de bandera mexicana para sublimar, hecho desde cero

Anuar pidió el 2026-08-16 "fusilar" a 300 DPI un jersey de béisbol de la foto
de una tienda. De una foto de producto de 890 × 1200 px, con la tela arrugada
y en perspectiva, eso no existe: el panel de un jersey talla M a 300 DPI son
6496 × 8858 píxeles. Ampliar la foto da pixelón, no diseño.

Así que no se copia la foto — se rehace el diseño con piezas que sí aguantan
el tamaño: el **escudo en vector** (dominio público, `BIBLIOTECA/vectores/`)
y las **grecas dibujadas**, que por ser geometría salen limpias a cualquier
medida.

La greca es la **xicalcoliuhqui**, la espiral escalonada — la de los muros de
Mitla. Se dibuja, no se copia de ningún lado: no hay problema de derechos y
no hay resolución que la limite.

**El escudo nacional**: es dominio público (Ley Federal del Derecho de Autor,
art. 14 VII). Aparte de eso, la Ley sobre el Escudo, la Bandera y el Himno
Nacionales regula su reproducción; en prendas se usa todos los días en todo
México, pero el dato queda escrito aquí para que él lo sepa, no para
decidirle nada.

Correr:
    python EDITOR/diseno_bandera_mx.py --talla M --prueba
    python EDITOR/diseno_bandera_mx.py --talla M --panel frente
"""
from __future__ import annotations
import io
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

VERDE = (0, 104, 71)          # verde bandera oficial
ROJO = (206, 17, 38)          # rojo bandera oficial
VERDE_HONDO = (0, 58, 40)
ROJO_HONDO = (128, 10, 24)
ESCUDO_SVG = RAIZ / "BIBLIOTECA" / "vectores" / "escudo_nacional_mexico.svg"


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _plantilla():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location(
        "plantilla_prenda", RAIZ / "EDITOR" / "plantilla_prenda.py")
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _greca(lado: int, color, fondo, grosor: int):
    """Un cuadro de greca escalonada, para repetir sin que se note la unión.

    Se dibuja de un solo trazo que entra girando hacia el centro. El truco
    para que empalme es que arranca y termina en la orilla, a la misma altura.
    """
    from PIL import Image, ImageDraw
    t = Image.new("RGB", (lado, lado), fondo)
    d = ImageDraw.Draw(t)
    paso = max(grosor * 2, lado // 6)
    x, y = 0, lado // 2
    pts = [(x, y)]
    ancho, largo = lado, lado // 2
    # Espiral cuadrada hacia adentro: derecha, arriba, izquierda, abajo…
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    i, avance = 0, lado - paso
    while avance > paso:
        dx, dy = dirs[i % 4]
        x, y = x + dx * avance, y + dy * avance
        pts.append((x, y))
        if i % 2 == 1:
            avance -= paso * 2
        i += 1
    d.line(pts, fill=color, width=grosor, joint="curve")
    return t


def _mosaico(w: int, h: int, lado: int, color, fondo, grosor: int):
    from PIL import Image
    t = _greca(lado, color, fondo, grosor)
    m = Image.new("RGB", (w, h), fondo)
    for yy in range(0, h, lado):
        for xx in range(0, w, lado):
            m.paste(t, (xx, yy))
    return m


def _borde_rasgado(w: int, h: int, x_en_0: float, x_en_1: float,
                   amplitud: float, semilla: int = 7):
    """Máscara con la orilla rota, como el desgarrón del diseño original.

    La orilla se mueve con varias ondas de distinto tamaño encimadas: una
    sola onda se ve a rayas de máquina, y una línea recta no se parece en
    nada al rasgado que él quiere.
    """
    from PIL import Image, ImageDraw
    msk = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(msk)
    pts = [(0, 0)]
    n = 260
    for i in range(n + 1):
        v = i / n
        base = x_en_0 + (x_en_1 - x_en_0) * v
        r = 0.0
        for k, (frec, amp) in enumerate(((3.1, 1.0), (7.7, 0.45),
                                         (17.3, 0.22), (37.1, 0.11))):
            r += math.sin(v * frec * math.pi * 2 + semilla * (k + 1)) * amp
        pts.append((base * w + r * amplitud * w, v * h))
    pts += [(0, h)]
    d.polygon(pts, fill=255)
    return msk


def _escudo(alto_px: int):
    """El escudo en vector, rasterizado al alto que se pida. None si no se puede."""
    import subprocess
    import tempfile
    from PIL import Image
    if not ESCUDO_SVG.exists():
        return None
    ink = Path(r"C:\Program Files\Inkscape\bin\inkscape.exe")
    if not ink.exists():
        return None
    out = Path(tempfile.gettempdir()) / f"_escudo_{alto_px}.png"
    if not out.exists():
        try:
            subprocess.run([str(ink), "--export-type=png",
                            f"--export-filename={out}",
                            f"--export-height={alto_px}",
                            "--export-background-opacity=0",
                            str(ESCUDO_SVG)],
                           check=True, capture_output=True, timeout=300)
        except Exception:
            return None
    return Image.open(out).convert("RGBA") if out.exists() else None


def _fuente(px: int):
    from PIL import ImageFont
    for nom in ("impact.ttf", "arialbd.ttf", "seguibl.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(nom, px)
        except Exception:
            continue
    return ImageFont.load_default()


def generar(talla="M", panel="frente", prueba=False, texto="MEXICO",
            sangrado_cm=2.0, prenda="jersey") -> dict:
    """Arma el diseño completo sobre el panel de la talla que se pida."""
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    pl = _plantilla()
    t = (talla or "M").upper().strip()
    p = (panel or "frente").lower().strip()
    med = pl.medidas(prenda, t, p)
    if not med:
        return {"status": "NO_HAY_ESA_MEDIDA",
                "detalle": (f"No tengo «{prenda}» talla «{talla}» panel "
                            f"«{panel}».\n\n" + pl.catalogo())}
    an_cm = med[0] + sangrado_cm * 2
    al_cm = med[1] + sangrado_cm * 2
    W, H = pl._cm_px(an_cm), pl._cm_px(al_cm)
    # La prueba sale a 1/6: se ve igual y tarda segundos en vez de minutos.
    # Sirve para decidir, NUNCA para imprimir.
    div = 6 if prueba else 1
    W, H = max(60, W // div), max(60, H // div)
    px_cm = W / an_cm

    lienzo = Image.new("RGB", (W, H), (255, 255, 255))

    lado = max(20, int(px_cm * 3.0))          # el cuadro de greca, ~3 cm
    grosor = max(2, int(px_cm * 0.4))
    verde = _mosaico(W, H, lado, VERDE_HONDO, VERDE, grosor)
    rojo = _mosaico(W, H, lado, ROJO_HONDO, ROJO, grosor)

    # LA DIAGONAL. El verde entra por la izquierda, el rojo por la derecha, y
    # en medio queda la tela blanca en diagonal — que es lo que hace el
    # diseño. La primera vez el rojo se comió la hoja entera: `_borde_rasgado`
    # rellena SIEMPRE del lado izquierdo, así que para el rojo hay que
    # invertir la máscara, no espejearla.
    amp = 0.03
    m_verde = _borde_rasgado(W, H, 0.40, 0.12, amp, semilla=3)
    lienzo.paste(verde, (0, 0), m_verde)
    m_rojo = ImageOps.invert(_borde_rasgado(W, H, 0.70, 0.46, amp, semilla=11))
    lienzo.paste(rojo, (0, 0), m_rojo)

    avisos = []
    # EL ESCUDO GRANDE, montado sobre el verde y saliéndose al blanco: es lo
    # que le da el aire del diseño original sin copiarle nada.
    esc_g = _escudo(int(H * 0.30))
    if esc_g:
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        capa.paste(esc_g, (int(W * 0.03), int(H * 0.24)), esc_g)
        lienzo = Image.alpha_composite(lienzo.convert("RGBA"), capa).convert("RGB")
    else:
        avisos.append("No pude rasterizar el escudo (falta Inkscape o el SVG).")

    # EL ESCUDO DEL PECHO + el texto, en la franja blanca del centro.
    esc_p = _escudo(int(H * 0.10))
    if esc_p:
        cx = int(W * 0.52 - esc_p.width / 2)
        lienzo.paste(esc_p, (cx, int(H * 0.10)), esc_p)
        d = ImageDraw.Draw(lienzo)
        f = _fuente(max(10, int(px_cm * 2.2)))
        caja = d.textbbox((0, 0), texto, font=f)
        d.text((int(W * 0.52 - (caja[2] - caja[0]) / 2),
                int(H * 0.10) + esc_p.height + int(px_cm * 0.3)),
               texto, font=f, fill=VERDE)

    etiqueta = (f"BANDERAMX_{pl._cual_prenda(prenda).upper()}_{p}_{t}_{an_cm:g}x{al_cm:g}cm"
                + ("_PRUEBA" if prueba else "_300dpi"))
    destino = pl._carpeta("png") / f"{etiqueta}.png"
    k = 2
    while destino.exists():
        destino = destino.parent / f"{etiqueta}__{k}.png"
        k += 1
    dpi = int(round(W / (an_cm / 2.54)))
    lienzo.save(destino, dpi=(dpi, dpi))

    r = {"status": "OK", "archivo": str(destino), "talla": t, "panel": p,
         "prenda": pl._cual_prenda(prenda),
         "mide_cm": f"{an_cm:g} × {al_cm:g}", "px": f"{W} × {H}", "dpi": dpi,
         "prueba": prueba, "kb": round(destino.stat().st_size / 1024, 1)}
    if prueba:
        r["aviso"] = ("Es la PRUEBA a 1/6. Sirve para verlo, no para imprimir: "
                      "pídemelo sin --prueba y sale a 300 DPI.")
    if avisos:
        r["avisos"] = avisos
    return r


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return f"No pude armarlo: {r.get('detalle', r.get('status'))}"
    t = (f"🇲🇽 **Jersey bandera — {r['panel']} talla {r['talla']}**\n"
         f"   {r['mide_cm']} cm · {r['px']} px a **{r['dpi']} DPI**")
    if r.get("aviso"):
        t += f"\n\n⚠️ {r['aviso']}"
    for a in r.get("avisos", []):
        t += f"\n⚠️ {a}"
    return t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)"


def main() -> int:
    _consola_utf8()
    crudos = sys.argv[1:]

    def _op(nombre, por_defecto):
        if f"--{nombre}" in crudos:
            i = crudos.index(f"--{nombre}")
            if i + 1 < len(crudos):
                return type(por_defecto)(crudos[i + 1])
        return por_defecto

    print(_texto(generar(talla=_op("talla", "M"), panel=_op("panel", "frente"),
                         prueba="--prueba" in crudos,
                         texto=_op("texto", "MEXICO"),
                         prenda=_op("prenda", "jersey"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
