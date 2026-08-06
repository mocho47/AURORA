# -*- coding: utf-8 -*-
"""AURORA · De una imagen a PDF, con DPI real y a color o blanco y negro

Anuar lo encargó el 2026-08-05 como flujos separados, cada uno se pide solo:

    imagen sin fondo a 300 dpi A COLOR en pdf
    imagen sin fondo a 300 dpi en BLANCO Y NEGRO en pdf

El DPI aquí no es un adorno: manda el TAMAÑO FÍSICO del PDF. Una foto de
3000 px a 300 dpi mide 25.4 cm; la misma a 72 dpi mediría 105 cm. Cuando se
manda a imprimir, esa diferencia lo es todo.

Blanco y negro tiene dos formas, y son distintas:
    "gris"  escala de grises — conserva los tonos (para fotos)
    "puro"  solo negro o blanco — sin grises (para transfer y serigrafía)

Correr:
    python EDITOR/imagen_a_pdf.py "C:\\ruta\\foto.jpg" --dpi 300
    python EDITOR/imagen_a_pdf.py "C:\\ruta\\foto.jpg" --dpi 300 --bn
    python EDITOR/imagen_a_pdf.py "C:\\ruta\\foto.jpg" --dpi 300 --bn --puro
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _carpeta(ext: str) -> Path:
    """Cada tipo a su carpeta — la regla de Anuar del 2026-08-05."""
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("carpetas_por_tipo",
                                            RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de(ext)
    except Exception:
        d = Path.home() / "Downloads" / ext
        d.mkdir(parents=True, exist_ok=True)
        return d


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Cuántos DPI hacen falta según a qué distancia se va a ver. El gran formato
# NO se imprime a 300 dpi: se ve de lejos y el archivo pesaría cientos de MB.
# Anuar lo trajo el 2026-08-05 al decir "300 dpi es gran formato para mandar
# maquilar" — y con su imagen, 300 dpi daban 12.8 cm, o sea NADA de gran formato.
CALIDAD = (
    (300, "impreso de mano", "se ve de cerca: etiquetas, tarjetas, hojas"),
    (150, "poster", "se ve a un metro"),
    (100, "lona chica", "se ve a 2-3 metros"),
    (72,  "lona grande", "se ve a más de 3 metros"),
)
DPI_MINIMO_DECENTE = 60


def calcular(entrada: str, ancho_cm: float = 0, alto_cm: float = 0) -> dict:
    """A qué DPI queda la imagen si se imprime a ese tamaño, y si va a servir.

    Es la cuenta que decide si un archivo aguanta el tamaño que se quiere:
        tamaño_cm = píxeles ÷ dpi × 2.54
    """
    try:
        from PIL import Image
        img = Image.open(entrada)
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}"}

    if ancho_cm:
        dpi = img.width / (ancho_cm / 2.54)
        alto_cm = img.height / dpi * 2.54
    elif alto_cm:
        dpi = img.height / (alto_cm / 2.54)
        ancho_cm = img.width / dpi * 2.54
    else:
        return {"status": "FALTA_DATO", "detalle": "Dime el ancho o el alto en cm."}

    dpi = round(dpi)
    for umbral_dpi, nombre, cuando in CALIDAD:
        if dpi >= umbral_dpi:
            veredicto, uso = nombre, cuando
            break
    else:
        veredicto, uso = "pixeleado", "no alcanza ni para lona grande"

    return {"status": "OK", "dpi": dpi, "px": f"{img.width}×{img.height}",
            "ancho_cm": round(ancho_cm, 1), "alto_cm": round(alto_cm, 1),
            "veredicto": veredicto, "uso": uso,
            "sirve": dpi >= DPI_MINIMO_DECENTE}


def convertir(entrada: str, dpi: int = 300, quitar_fondo: bool = True,
              blanco_negro: bool = False, puro: bool = False,
              umbral: int = 128, ancho_cm: float = 0) -> dict:
    """Imagen → PDF. Cada opción hace UNA cosa y se dice cuál.

    quitar_fondo   con rembg, y sobre BLANCO (el transparente sale negro al
                   imprimirse o al abrirlo en Corel)
    blanco_negro   True = sin color
    puro           True = solo negro o blanco, sin grises (para transfer)
    dpi            manda el tamaño físico del PDF
    """
    origen = Path(entrada)
    if not origen.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {entrada}"}

    try:
        from PIL import Image
    except ImportError:
        return {"status": "FALTA_LIBRERIA", "detalle": "Falta Pillow"}

    # Si se pidió por TAMAÑO, el DPI sale de ahí — es como se piensa de verdad:
    # "lo quiero de 40 cm", no "a 190 dpi".
    aviso_calidad = ""
    if ancho_cm:
        c = calcular(str(origen), ancho_cm=ancho_cm)
        if c.get("status") == "OK":
            dpi = max(1, c["dpi"])
            if not c["sirve"]:
                aviso_calidad = (f"⚠️ A {ancho_cm:g} cm te quedan **{dpi} dpi**: "
                                 "va a verse pixeleado hasta de lejos. "
                                 "Necesitas una imagen más grande.")
            elif dpi < 150:
                aviso_calidad = (f"A {ancho_cm:g} cm quedan {dpi} dpi — sirve "
                                 f"para {c['veredicto']} ({c['uso']}), no para "
                                 "verse de cerca.")

    pasos = []
    trabajo = origen

    if quitar_fondo:
        try:
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location("conversiones",
                                                RAIZ / "EDITOR" / "conversiones.py")
            conv = _ilu.module_from_spec(spec)
            spec.loader.exec_module(conv)
            # sobre_blanco: un PDF con transparencia se imprime NEGRO.
            r = conv.quitar_fondo(str(origen), sobre_blanco=True)
            salida_sf = r.get("salida") or r.get("archivo") or r.get("ruta")
            if r.get("status") in ("OK", "ok") and salida_sf and Path(salida_sf).exists():
                trabajo = Path(salida_sf)
                pasos.append("fondo quitado con rembg, sobre blanco")
            else:
                pasos.append(f"sin quitar fondo ({r.get('detalle', r.get('status', '?'))})")
        except Exception as e:
            pasos.append(f"sin quitar fondo ({type(e).__name__})")

    try:
        img = Image.open(trabajo)
        # Lo transparente a blanco: si no, el PDF lo imprime negro.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[-1])
            img = fondo
        else:
            img = img.convert("RGB")

        if blanco_negro:
            if puro:
                # Sin grises: o hay tinta o no la hay. Es lo que pide el
                # transfer y la serigrafía.
                img = img.convert("L").point(
                    lambda v: 0 if v < umbral else 255).convert("RGB")
                pasos.append("blanco y negro PURO (sin grises)")
            else:
                img = img.convert("L").convert("RGB")
                pasos.append("escala de grises")
        else:
            pasos.append("a color")

        ancho_cm = img.width / dpi * 2.54
        alto_cm = img.height / dpi * 2.54

        etiqueta = ("_bn_puro" if (blanco_negro and puro)
                    else "_bn" if blanco_negro else "_color")
        if quitar_fondo:
            etiqueta = "_sinfondo" + etiqueta
        salida = _carpeta("pdf") / f"{origen.stem}{etiqueta}_{dpi}dpi.pdf"
        n = 2
        while salida.exists():
            salida = salida.parent / f"{origen.stem}{etiqueta}_{dpi}dpi__{n}.pdf"
            n += 1

        # El DPI se escribe en el PDF: es lo que fija el tamaño al imprimir.
        img.save(salida, "PDF", resolution=float(dpi))
        pasos.append(f"guardado a {dpi} dpi")
    except Exception as e:
        return {"status": "ERROR", "pasos": pasos,
                "detalle": f"{type(e).__name__}: {str(e)[:140]}"}

    return {"status": "OK", "archivo": str(salida), "pasos": pasos,
            "aviso": aviso_calidad,
            "px": f"{img.width}×{img.height}",
            "cm": f"{ancho_cm:.1f} × {alto_cm:.1f} cm",
            "dpi": dpi, "kb": round(salida.stat().st_size / 1024, 1)}


def _texto(r: dict) -> str:
    if r.get("status") == "NO_EXISTE":
        return r["detalle"]
    if r.get("status") != "OK":
        hechos = "\n".join(f"   ✓ {p}" for p in r.get("pasos", []))
        return (f"No pude terminarlo (no te miento).\n{hechos}\n"
                f"   ✗ {r.get('detalle', '?')}")
    hechos = "\n".join(f"   ✓ {p}" for p in r["pasos"])
    return (f"✅ **PDF listo**\n{hechos}\n\n"
            f"   📐 **{r['cm']}** al imprimirse ({r['px']} px a {r['dpi']} dpi)\n\n"
            f"📁 `{r['archivo']}`  ({r['kb']} KB)")


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    dpi = 300
    ancho = 0.0
    if "--dpi" in sys.argv:
        dpi = int(sys.argv[sys.argv.index("--dpi") + 1])
    if "--cm" in sys.argv:
        ancho = float(sys.argv[sys.argv.index("--cm") + 1])
    print(_texto(convertir(args[0], dpi=dpi, ancho_cm=ancho,
                           quitar_fondo="--con-fondo" not in sys.argv,
                           blanco_negro="--bn" in sys.argv,
                           puro="--puro" in sys.argv)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
