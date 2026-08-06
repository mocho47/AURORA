# -*- coding: utf-8 -*-
"""AURORA · Qué trae tu PDF adentro y si aguanta el tamaño de impresión

Anuar lo preguntó el 2026-08-05: arma una lona en Corel, la guarda como PDF, y
quiere saber si va a salir pixeleada — sin dejar de trabajar mientras.

Lo que de verdad importa antes de mandar a maquilar no es el DPI que dice el
archivo: es el **DPI EFECTIVO de cada imagen pegada adentro**, o sea cuántos
píxeles reales tiene esa foto repartidos en el tamaño al que se va a imprimir.
Una foto de 800 px estirada a 2 metros da 10 dpi por más que el PDF diga 300.

Esto SOLO LEE. No modifica el PDF ni toca el original.

Distingue lo que hay que distinguir:
  • Texto y formas de Corel = VECTOR: se imprimen perfectos a cualquier tamaño
  • Fotos pegadas = PÍXELES: esas son las que pueden pixelearse

Correr:  python EDITOR/revisar_pdf.py "C:\\ruta\\lona.pdf"
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# A qué distancia se ve, cuántos DPI hacen falta. Mismo criterio que en PDF.
CALIDAD = (
    (300, "impreso de mano"),
    (150, "poster a un metro"),
    (100, "lona a 2-3 metros"),
    (72,  "lona a más de 3 metros"),
)
DPI_MINIMO = 60


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _dpi_que_necesita(ancho_cm: float) -> tuple:
    """Cuántos DPI hacen falta SEGÚN EL TAMAÑO de la pieza.

    Una lona de 2 metros se ve desde 3 metros o más, y a esa distancia el ojo
    distingue apenas 30-40 dpi. Pedirle 300 a una lona es tirar el archivo a
    500 MB sin que se vea mejor.

    Anuar lo trajo el 2026-08-05: su maquilador le dice "sube los dpi a 300",
    que es la regla de la hoja de papel aplicada a una lona. Muchas maquilas
    en realidad piden el archivo a ESCALA 1:10 a 300 dpi — que a tamaño real
    son 30 dpi. Es la misma cuenta dicha de otro modo.
    """
    if ancho_cm >= 150:
        return 40, "una lona: se ve desde 3 m o más"
    if ancho_cm >= 80:
        return 72, "un cartel grande: se ve desde 2 m"
    if ancho_cm >= 40:
        return 120, "un poster: se ve desde 1 m"
    return 300, "algo que se ve de cerca"


def _veredicto(dpi: float, necesita: float = 0) -> tuple:
    if necesita:
        # 5% de tolerancia: 299 dpi contra 300 no es un problema, y marcarlo
        # como "NO PASA" hace desconfiar de todo el reporte (2026-08-05).
        pasa = dpi >= necesita * 0.95
        return ("pasa" if pasa else "NO PASA"), pasa
    for umbral, nombre in CALIDAD:
        if dpi >= umbral:
            return nombre, True
    return "PIXELEADO", dpi >= DPI_MINIMO


def revisar(ruta: str) -> dict:
    """Qué hay dentro del PDF y a qué DPI real queda cada imagen."""
    p = Path(ruta)
    if not p.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {ruta}"}
    try:
        import fitz          # PyMuPDF
    except ImportError:
        return {"status": "FALTA_LIBRERIA",
                "detalle": "Falta PyMuPDF: pip install pymupdf"}

    try:
        doc = fitz.open(str(p))
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {str(e)[:90]}"}

    paginas = []
    for n, pag in enumerate(doc, 1):
        # El tamaño del PDF viene en puntos: 72 puntos = 1 pulgada = 2.54 cm.
        ancho_cm = pag.rect.width / 72 * 2.54
        alto_cm = pag.rect.height / 72 * 2.54

        # Cuántos DPI necesita ESTA pieza según su tamaño real.
        necesita, por_que = _dpi_que_necesita(ancho_cm)

        vectores = len(pag.get_drawings())
        texto = len(pag.get_text("text").strip())

        # ¿EL TEXTO ESTÁ EN CURVAS?
        # Es lo PRIMERO que revisa el maquilador de Anuar y por lo que le
        # rechaza lonas: "wey, las letras ciérralas a curvas". Si el texto sigue
        # vivo y la maquila no tiene esa tipografía, se la cambia por otra y la
        # lona sale con letras distintas. En curvas ya son dibujos y no dependen
        # de nada. (Anuar lo contó el 2026-08-05.)
        fuentes_vivas = []
        try:
            for f in pag.get_fonts(full=True):
                nombre = f[3] if len(f) > 3 else "?"
                # El 6º campo dice si la fuente va incrustada en el archivo.
                incrustada = bool(f[1]) if len(f) > 1 else False
                fuentes_vivas.append({"nombre": str(nombre).split("+")[-1],
                                      "incrustada": incrustada})
        except Exception:
            pass

        imagenes = []
        for info in pag.get_images(full=True):
            xref = info[0]
            try:
                datos = doc.extract_image(xref)
                px_ancho, px_alto = datos["width"], datos["height"]
            except Exception:
                continue
            # Dónde y de qué tamaño está PUESTA en la página: eso decide el DPI
            # real, no el tamaño del archivo original.
            try:
                cajas = pag.get_image_rects(xref)
                caja = cajas[0] if cajas else pag.rect
            except Exception:
                caja = pag.rect
            puesta_cm = caja.width / 72 * 2.54
            if puesta_cm <= 0:
                continue
            dpi_real = px_ancho / (puesta_cm / 2.54)
            nombre, sirve = _veredicto(dpi_real, necesita)
            imagenes.append({
                "px": f"{px_ancho}×{px_alto}",
                "puesta_cm": round(puesta_cm, 1),
                "dpi_real": round(dpi_real),
                "veredicto": nombre, "sirve": sirve,
            })

        paginas.append({
            "pagina": n,
            "cm": f"{ancho_cm:.1f} × {alto_cm:.1f} cm",
            "vectores": vectores, "letras": texto,
            "fuentes": fuentes_vivas,
            "necesita_dpi": necesita, "por_que": por_que,
            "imagenes": imagenes,
        })

    doc.close()
    malas = [i for pg in paginas for i in pg["imagenes"] if not i["sirve"]]
    sin_curvas = [f for pg in paginas for f in pg["fuentes"] if not f["incrustada"]]
    return {"status": "OK", "archivo": str(p), "paginas": paginas,
            "total_paginas": len(paginas), "problemas": len(malas),
            "fuentes_riesgo": len(sin_curvas)}


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return r.get("detalle", "No pude revisarlo.")
    partes = [f"📄 **{Path(r['archivo']).name}** — {r['total_paginas']} página(s)\n"]
    for pg in r["paginas"]:
        partes.append(f"**Página {pg['pagina']}** — {pg['cm']}")
        _n = pg['necesita_dpi']
        partes.append(f"   _Es {pg['por_que']} → necesita **{_n} dpi**"
                      + ("._" if _n >= 300 else ", no 300._"))
        if pg["vectores"]:
            partes.append(f"   ✅ {pg['vectores']} formas vectoriales — "
                          "se imprimen perfectas a cualquier tamaño")
        # Lo PRIMERO que revisa el maquilador: "las letras ciérralas a curvas".
        if pg["letras"]:
            sueltas = [f["nombre"] for f in pg["fuentes"] if not f["incrustada"]]
            if sueltas:
                partes.append(
                    f"   ⚠️ **HAY TEXTO VIVO, no en curvas** "
                    f"({pg['letras']} caracteres)\n"
                    f"      Tipografías que NO van dentro del archivo: "
                    f"{', '.join(sorted(set(sueltas))[:5])}\n"
                    f"      → En Corel: selecciona todo y **Ctrl+Q** "
                    f"(Objeto → Convertir a curvas) antes de publicar.")
            else:
                partes.append(f"   ✅ {pg['letras']} caracteres de texto, con las "
                              "tipografías incrustadas — no se van a cambiar")
        elif pg["fuentes"]:
            partes.append("   ✅ Sin texto vivo: las letras ya están en curvas")
        if not pg["imagenes"]:
            partes.append("   ✅ Sin fotos pegadas: es 100% vectorial.")
        for i, im in enumerate(pg["imagenes"], 1):
            marca = "✅" if im["sirve"] else "⚠️"
            partes.append(
                f"   {marca} Foto {i}: {im['px']} px puesta a {im['puesta_cm']} cm "
                f"→ **{im['dpi_real']} dpi** ({im['veredicto']})")
        partes.append("")
    if r["problemas"]:
        partes.append(f"⚠️ **{r['problemas']} imagen(es) van a salir pixeleadas.** "
                      "Consigue esas fotos más grandes, o achícalas en el diseño.")
    else:
        partes.append("✅ **Todo aguanta el tamaño.** Se puede mandar a maquilar.")
    partes.append("\n_Ojo: vectorizar una FOTO no la mejora, la vuelve manchas. "
                  "Vectorizar solo sirve para logos y formas planas._")
    return "\n".join(partes)


def main() -> int:
    _consola_utf8()
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    print(_texto(revisar(sys.argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
