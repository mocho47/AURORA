# -*- coding: utf-8 -*-
"""AURORA · ARREGLA el PDF de la lona, no solo lo revisa

Anuar fue tajante el 2026-08-05 y tenía razón: *"no quiero que me diga eso, no
me sirve, quiero que lo corrija; es una IA, tiene las herramientas, los
manuales, la libertad del entorno"*.

Antes esto solo diagnosticaba. Ahora arregla las dos cosas por las que su
maquilador le rechaza lonas:

  1. IMÁGENES DE BAJA RESOLUCIÓN
     Se agrandan y se meten de vuelta al PDF (PyMuPDF replace_image).
     No se inventa detalle que no existe —eso es imposible— pero se agranda
     con el mejor método disponible y se afina el resultado, que es lo que
     de verdad se puede hacer.

  2. TEXTO QUE NO ESTÁ EN CURVAS
     Es lo primero que le rechazan: "wey, las letras ciérralas a curvas".
     Si el PDF salió de Corel y Corel está abierto, se cierra a curvas y se
     vuelve a publicar. Si no, se dice exactamente qué hacer (Ctrl+Q).

El original NUNCA se toca: se guarda uno nuevo con el sufijo _ARREGLADO.

Correr:
    python EDITOR/arreglar_pdf.py "C:\\ruta\\lona.pdf"
    python EDITOR/arreglar_pdf.py "C:\\ruta\\lona.pdf" --dpi 100
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _carpeta(ext: str) -> Path:
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


# Más de esto no se agranda: pasado 4x el resultado se ve plástico y pesa de
# más sin verse mejor. Es el límite honesto.
AGRANDE_MAXIMO = 4.0


def _agrandar(img, factor: float):
    """Agranda una imagen lo mejor que se pueda con lo que hay instalado.

    No inventa detalle real —eso no existe— pero LANCZOS conserva los bordes
    mucho mejor que un estirado simple, y un afinado ligero después recupera
    la sensación de nitidez que se pierde al escalar.
    """
    from PIL import Image, ImageFilter
    ancho = max(1, int(img.width * factor))
    alto = max(1, int(img.height * factor))
    grande = img.resize((ancho, alto), Image.LANCZOS)
    # Afinado suave: sin esto queda lavado. Con demasiado, queda con halos.
    return grande.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=3))


def _empaquetar(img) -> bytes:
    """Guarda la imagen del modo que pesa menos SIN que se note en la impresión.

    Guardarlo todo en PNG dejó el PDF de gomitas en 247 MB (2026-08-06): un
    archivo que ninguna maquila acepta y que tarda una eternidad en subir. PNG
    no comprime fotos, comprime dibujos planos. Una foto en JPEG de calidad
    alta pesa ~10 veces menos y a 100 dpi impresos no se distingue.

    La regla: si la imagen tiene transparencia se queda en PNG (JPEG no la
    soporta y saldría con fondo negro, que es justo el error que ya nos costó
    encontrar antes). Si no, va en JPEG.
    """
    buf = io.BytesIO()
    tiene_alfa = img.mode in ("RGBA", "LA", "P")
    if tiene_alfa:
        img.save(buf, format="PNG", optimize=True)
    else:
        # 88 es el punto donde deja de verse la diferencia y todavía pesa poco.
        img.save(buf, format="JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


def _dpi_que_necesita(ancho_cm: float) -> int:
    """Lo que de verdad necesita la pieza según a qué distancia se ve."""
    if ancho_cm >= 150:
        return 40           # lona: se ve desde 3 m
    if ancho_cm >= 80:
        return 72
    if ancho_cm >= 40:
        return 120
    return 300


def arreglar(ruta: str, dpi_objetivo: int = 0) -> dict:
    """Agranda las imágenes que no dan el DPI y guarda un PDF nuevo."""
    p = Path(ruta)
    if not p.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {ruta}"}
    try:
        import fitz
        from PIL import Image
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    try:
        doc = fitz.open(str(p))
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {str(e)[:90]}"}

    arregladas, ya_estaban, no_se_pudo = [], 0, []
    texto_vivo = []

    for n, pag in enumerate(doc, 1):
        ancho_cm = pag.rect.width / 72 * 2.54
        necesita = dpi_objetivo or _dpi_que_necesita(ancho_cm)

        # ¿Hay texto que no está en curvas? Se anota para avisar al final.
        if pag.get_text("text").strip():
            for f in pag.get_fonts(full=True):
                if len(f) > 1 and not f[1]:
                    texto_vivo.append(str(f[3] if len(f) > 3 else "?").split("+")[-1])

        for info in pag.get_images(full=True):
            xref = info[0]
            try:
                datos = doc.extract_image(xref)
                px_ancho, px_alto = datos["width"], datos["height"]
                cajas = pag.get_image_rects(xref)
                caja = cajas[0] if cajas else pag.rect
                puesta_cm = caja.width / 72 * 2.54
                if puesta_cm <= 0:
                    continue
                dpi_real = px_ancho / (puesta_cm / 2.54)
            except Exception:
                continue

            if dpi_real >= necesita * 0.95:
                ya_estaban += 1
                continue

            factor = min(AGRANDE_MAXIMO, necesita / max(dpi_real, 1))
            if factor <= 1.05:
                ya_estaban += 1
                continue

            try:
                img = Image.open(io.BytesIO(datos["image"]))
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                grande = _agrandar(img, factor)
                buf = _empaquetar(grande)
                pag.replace_image(xref, stream=buf)
                arregladas.append({
                    "pagina": n,
                    "antes": f"{px_ancho}×{px_alto} ({dpi_real:.0f} dpi)",
                    "ahora": f"{grande.width}×{grande.height} "
                             f"({dpi_real * factor:.0f} dpi)",
                    "puesta_cm": round(puesta_cm, 1),
                    "alcanza": dpi_real * factor >= necesita * 0.95,
                })
            except Exception as e:
                no_se_pudo.append(f"pág {n}: {type(e).__name__}")

    curvas = _cerrar_curvas_si_se_puede(p, texto_vivo)

    if not arregladas:
        doc.close()
        return {"status": "NADA_QUE_ARREGLAR", "ya_estaban": ya_estaban,
                "texto_vivo": sorted(set(texto_vivo)), "curvas": curvas,
                "detalle": (f"Las {ya_estaban} imágenes ya dan el DPI que "
                            "necesita esta pieza. No toqué nada.")}

    salida = _carpeta("pdf") / f"{p.stem}_ARREGLADO.pdf"
    m = 2
    while salida.exists():
        salida = salida.parent / f"{p.stem}_ARREGLADO__{m}.pdf"
        m += 1
    try:
        doc.save(str(salida), garbage=3, deflate=True)
    except Exception as e:
        doc.close()
        return {"status": "ERROR", "detalle": f"no pude guardarlo: {type(e).__name__}"}
    doc.close()

    return {"status": "OK", "archivo": str(salida),
            "arregladas": arregladas, "ya_estaban": ya_estaban,
            "no_se_pudo": no_se_pudo, "texto_vivo": sorted(set(texto_vivo)),
            "curvas": curvas,
            "kb": round(salida.stat().st_size / 1024, 1)}


def _cerrar_curvas_si_se_puede(pdf: Path, texto_vivo: list) -> dict:
    """Cierra el texto a curvas EN COREL, si el diseño está abierto ahí.

    Desde el PDF no se puede: el texto ya dejó de ser texto. La única forma
    real es en el archivo de Corel, y solo si es el que está abierto. Cuando
    no se puede, se dice por qué — no se calla ni se finge.
    """
    if not texto_vivo:
        return {}
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("corel_core",
                                            RAIZ / "EDITOR" / "corel_core.py")
        cc = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cc)
        if not cc.disponible():
            return {"status": "sin_corel", "detalle": "Corel no está abierto"}
        info = cc.info_documento()
        abierto = str(info.get("nombre") or info.get("Name") or "")
        # Solo se toca el diseño si es EL MISMO. Cerrar a curvas otro documento
        # sería estropear un trabajo distinto sin que nadie lo pidiera.
        if Path(abierto).stem.lower() != pdf.stem.lower():
            return {"status": "otro_documento",
                    "detalle": f"en Corel está abierto «{abierto}», no este"}
        return cc.cerrar_a_curvas_y_publicar()
    except Exception as e:
        return {"status": "error", "detalle": f"{type(e).__name__}: {str(e)[:80]}"}


def _texto(r: dict) -> str:
    s = r.get("status")
    if s in ("NO_EXISTE", "FALTA_LIBRERIA", "ERROR"):
        return f"No pude arreglarlo (no te miento): {r.get('detalle')}"

    aviso_texto = ""
    if r.get("texto_vivo"):
        cur = r.get("curvas") or {}
        if cur.get("status") == "ok":
            # Se hizo, no se pidió que lo hiciera él. Es la diferencia entre
            # avisar y resolver, que es justo lo que Anuar reclamó.
            aviso_texto = (
                "\n\n✅ **El texto ya quedó en curvas** — lo cerré en Corel y "
                "volví a publicar.\n"
                f"   📁 `{cur['ruta']}`  ({cur['kb']} KB)\n"
                "   _Tu .cdr sigue con el texto editable: trabajé sobre una "
                "copia._")
        else:
            aviso_texto = (
                "\n\n⚠️ **El texto NO está en curvas** — es lo primero que te "
                f"rechazan.\n   Tipografías sueltas: "
                f"{', '.join(r['texto_vivo'][:5])}\n")
            porque = cur.get("detalle") or "Corel no tiene ese diseño abierto"
            aviso_texto += (
                f"   No lo pude cerrar yo: {porque}.\n"
                "   → Ábrelo en Corel y pídemelo otra vez, o hazlo a mano con "
                "**Ctrl+A** y **Ctrl+Q**.\n"
                "   _Desde el PDF ya no se puede: ahí el texto dejó de ser "
                "texto._")

    if s == "NADA_QUE_ARREGLAR":
        return f"✅ {r['detalle']}{aviso_texto}"

    lineas = []
    quedan_cortas = 0
    for a in r["arregladas"]:
        marca = "✅" if a["alcanza"] else "⚠️"
        if not a["alcanza"]:
            quedan_cortas += 1
        lineas.append(f"   {marca} {a['antes']} → **{a['ahora']}** "
                      f"(puesta a {a['puesta_cm']} cm)")

    cola = ""
    if quedan_cortas:
        cola = (f"\n\n⚠️ **{quedan_cortas} siguen cortas** aun agrandadas al "
                "máximo. Esas hay que conseguirlas más grandes de origen, o "
                "achicarlas en el diseño. Agrandar no inventa detalle que no "
                "estaba.")

    return (f"✅ **PDF arreglado** — {len(r['arregladas'])} imágenes agrandadas"
            + (f", {r['ya_estaban']} ya estaban bien" if r["ya_estaban"] else "")
            + f"\n{chr(10).join(lineas)}\n\n"
            f"📁 `{r['archivo']}`  ({r['kb']} KB)\n"
            "_El original quedó intacto._" + cola + aviso_texto)


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    dpi = 0
    if "--dpi" in sys.argv:
        dpi = int(sys.argv[sys.argv.index("--dpi") + 1])
    print(_texto(arreglar(args[0], dpi)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
