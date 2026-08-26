# -*- coding: utf-8 -*-
"""AURORA · El PDF a TAMAÑO REAL para mandar a maquilar

Pedido de Anuar, 2026-08-26, con las piñatas de Alicia:
*"solo que sea el puro pdf de tamaño real sin traslape y la maquila que lo
divida en pdf sin ajustar a página"*.

Es la petición correcta y es la más simple: **una sola página del tamaño de la
pieza**, con el dibujo a 1:1. La maquiladora la parte en sus hojas con su propio
RIP; ellos ya saben hacerlo y lo hacen mejor. Lo único que no pueden arreglar es
que el PDF venga con la escala mal.

QUÉ NO LLEVA, Y ES A PROPÓSITO:
  · **Ni una marca.** Nada de recuadros, guías, márgenes ni cruces. Todo lo que
    se dibuje en el PDF se imprime. `SUBLIMACION/sublimacion_core.montar` sí
    dibuja un recuadro gris y una línea al centro —está bien para una banda de
    sublimación, pero acabarían impresas en la piñata—, y además rasteriza un
    lienzo a 300 DPI: a 89.5 cm eso son 10,570 px de lado y no cabe en la RAM
    de su PC. Por eso esto es un archivo aparte y no una opción de aquél.
  · **Ni traslape.** Él lo quitó del pedido: lo hace la maquila.
  · **Ni reencuadre.** La imagen va del borde al borde de la página.

LA MEDIDA:
Se da UNA sola —alto o ancho— y la otra sale de la proporción de la imagen, que
es lo que garantiza que no se deforme. Si se dan las dos y no cuadran con la
proporción, se avisa y **manda la proporción**: una piñata estirada no se vende.

EL DPI SE DICE SIEMPRE:
Una imagen chica estirada a 90 cm se ve pixeleada, y eso no se descubre hasta
que la maquila ya imprimió y ya se pagó. Aquí se calcula el DPI real que va a
salir y se dice claro. No se bloquea nada —él decide, es su cliente y su
dinero— pero no se entrega en silencio algo que va a salir mal.

Correr:
    python TALLER/pdf_tamano_real.py "C:\\ruta\\imagen.png" --alto 89.5
    python TALLER/pdf_tamano_real.py "C:\\ruta\\imagen.png" --ancho 120
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# Debajo de esto, la impresión se ve pixeleada de cerca. No es un capricho: en
# gran formato se ve a distancia y 100–150 DPI alcanza; abajo de 72 ya se nota
# aunque te alejes. Se avisa, no se prohíbe.
DPI_MINIMO = 72
DPI_COMODO = 150


def _carpeta() -> Path:
    """La misma carpeta de salida que usa el resto del taller."""
    d = Path.home() / "Downloads" / "pdf"
    d.mkdir(parents=True, exist_ok=True)
    return d


def generar(imagen: str, alto_cm: float = None, ancho_cm: float = None,
            salida: str = "") -> dict:
    """Una imagen → un PDF de UNA página, del tamaño real, a 1:1.

    alto_cm / ancho_cm: se da UNA. La otra sale de la proporción de la imagen.
    """
    ruta = Path(str(imagen or "").strip().strip('"'))
    if not ruta.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré la imagen: {ruta}"}
    if not alto_cm and not ancho_cm:
        return {"status": "FALTA_MEDIDA",
                "detalle": "Dime cuánto mide de alto o de ancho en cm "
                           "(ej: «a 89.5 de alto»). La otra medida la saco sola."}

    try:
        from PIL import Image
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}
    try:
        from reportlab.pdfgen import canvas as rc
        from reportlab.lib.units import cm as CM
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA",
                "detalle": f"Falta reportlab para escribir el PDF: {e}"}

    try:
        with Image.open(ruta) as im:
            px_w, px_h = im.size
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude abrir la imagen: {type(e).__name__}"}
    if not px_w or not px_h:
        return {"status": "ERROR", "detalle": "La imagen no tiene tamaño."}

    proporcion = px_h / px_w          # alto / ancho, tal como viene la imagen
    aviso_proporcion = ""
    if alto_cm and ancho_cm:
        esperado = round(ancho_cm * proporcion, 2)
        if abs(esperado - alto_cm) > 0.5:
            aviso_proporcion = (
                f"Diste {ancho_cm}x{alto_cm} cm pero la imagen es {px_w}x{px_h} px: "
                f"a {ancho_cm} cm de ancho le tocan {esperado} cm de alto. "
                f"Usé la proporción de la imagen para que no salga estirada.")
            alto_cm = esperado
    elif alto_cm:
        ancho_cm = round(alto_cm / proporcion, 2)
    else:
        alto_cm = round(ancho_cm * proporcion, 2)

    # El DPI que de verdad va a salir impreso.
    dpi_ancho = px_w / (ancho_cm / 2.54)
    dpi_alto = px_h / (alto_cm / 2.54)
    dpi = round(min(dpi_ancho, dpi_alto))

    destino = Path(salida) if salida else _carpeta() / (
        f"{ruta.stem}_{ancho_cm:g}x{alto_cm:g}cm.pdf")
    destino.parent.mkdir(parents=True, exist_ok=True)

    try:
        c = rc.Canvas(str(destino), pagesize=(ancho_cm * CM, alto_cm * CM))
        # De borde a borde, sin margen y sin una sola marca. preserveAspectRatio
        # queda en False A PROPÓSITO: la página YA se calculó con la proporción
        # de la imagen, así que aquí cuadran exacto; dejarlo en True volvería a
        # "contener" y podría dejar una franja blanca de un lado.
        c.drawImage(str(ruta), 0, 0, width=ancho_cm * CM, height=alto_cm * CM,
                    preserveAspectRatio=False, mask="auto")
        c.save()
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude escribir el PDF: {type(e).__name__}: {e}"}

    kb = round(destino.stat().st_size / 1024, 1)
    aviso_dpi = ""
    if dpi < DPI_MINIMO:
        aviso_dpi = (f"⚠️ A ese tamaño la imagen queda en {dpi} DPI: se va a ver "
                     f"pixeleada aunque te alejes. Consigue el archivo más grande "
                     f"antes de mandarlo a imprimir.")
    elif dpi < DPI_COMODO:
        aviso_dpi = (f"A ese tamaño quedan {dpi} DPI. Para gran formato visto a "
                     f"distancia pasa, de cerca se nota el pixel.")

    return {
        "status": "OK",
        "archivo": str(destino),
        "kb": kb,
        "medida_cm": [ancho_cm, alto_cm],
        "imagen_px": [px_w, px_h],
        "dpi": dpi,
        "aviso_dpi": aviso_dpi,
        "aviso_proporcion": aviso_proporcion,
        "para_la_maquila": ("Imprimir a TAMAÑO REAL (100%), sin «ajustar a página». "
                            f"La página del PDF ya mide {ancho_cm:g} x {alto_cm:g} cm. "
                            "Ustedes lo dividen en sus hojas."),
    }


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return f"[{r.get('status')}] {r.get('detalle', '')}"
    a, al = r["medida_cm"]
    t = (f"PDF a tamaño real listo: {a:g} x {al:g} cm ({r['dpi']} DPI, {r['kb']} KB)\n"
         f"{r['archivo']}\n{r['para_la_maquila']}")
    if r.get("aviso_proporcion"):
        t += f"\n{r['aviso_proporcion']}"
    if r.get("aviso_dpi"):
        t += f"\n{r['aviso_dpi']}"
    return t


def main() -> int:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    imagen = sys.argv[1]
    alto = ancho = None
    for i, a in enumerate(sys.argv):
        if a == "--alto" and i + 1 < len(sys.argv):
            alto = float(sys.argv[i + 1].replace(",", "."))
        if a == "--ancho" and i + 1 < len(sys.argv):
            ancho = float(sys.argv[i + 1].replace(",", "."))
    r = generar(imagen, alto, ancho)
    if "--json" in sys.argv:
        import json
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(_texto(r))
    return 0 if r.get("status") == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
