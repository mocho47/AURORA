# -*- coding: utf-8 -*-
"""TALLER de AURORA: genera vectores/DXF para corte laser manejando Inkscape por linea de comandos.
Replica el flujo de Anuar: imagen->vector, convertir a DXF, nombres a DXF. Todo legal (Inkscape gratis)."""
import os, subprocess
from pathlib import Path

INK = r"C:\Program Files\Inkscape\bin\inkscape.com"
# Salida RELATIVA a la raíz de AURORA (antes estaba quemada a C:\AURORA\TALLER_OUT,
# que es la carpeta del proyecto viejo: los DXF se generaban fuera de AURORA).
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "TALLER_OUT"
OUT.mkdir(parents=True, exist_ok=True)

# Timeout medido en vivo 2026-07-29 con un PDF real de Anuar ("Animal - Perro -
# Pitbull (Cabeza).pdf"): Inkscape se paso de 120s convirtiendo a DXF y la
# conversion murio. Su arranque en frio ya se habia medido pasando de 60s, y un
# PDF con detalle real tarda mucho mas que eso. 120s era demasiado corto para
# trabajo de verdad; 300s da margen sin colgar el chat para siempre.
def _ink(args, timeout=300):
    try:
        r = subprocess.run([INK] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        # Error honesto y accionable, no un volcado tecnico incomprensible.
        return 1, (f"Inkscape se pasó de {timeout}s convirtiendo el archivo. Suele pasar con "
                   f"PDFs de mucho detalle o si Inkscape arranca en frío. Vuelve a pedirlo "
                   f"(la segunda vez es más rápida) o simplifica el diseño.")
    except Exception as e:
        return 1, str(e)

def disponible() -> bool:
    return os.path.isfile(INK)

def _clean(ruta: str) -> str:
    """Acepta rutas con o sin comillas (ej. 'Copiar como ruta de acceso' de Windows)."""
    return (ruta or "").strip().strip('"').strip("'").strip()

def catalogo() -> dict:
    """Indexa la biblioteca de trabajos DXF ya terminados (Downloads\\DXF)."""
    libs = [r"C:\Users\Administrador\Downloads\DXF", r"C:\AURORA\TALLER_OUT"]
    items = []
    for lib in libs:
        p = Path(lib)
        if p.exists():
            for f in sorted(p.glob("*.dxf")):
                items.append({"nombre": f.name, "kb": round(f.stat().st_size/1024, 1),
                              "carpeta": lib, "ruta": str(f)})
    return {"status": "OK", "total": len(items), "trabajos": items[:200]}

def pdf_tiene_vectores(ruta: str) -> dict:
    """¿El PDF trae dibujo VECTORIAL de verdad, o solo una imagen adentro?

    Encontrado en vivo 2026-07-29 con un PDF real de Anuar ("Animal - Perro -
    Pitbull (Cabeza).pdf", 10 páginas): tenía 0 dibujos vectoriales y 1 imagen
    raster. Inkscape no puede exportar vectores que no existen, así que generaba
    un DXF de 0.2 KB con CERO entidades y aun así se reportaba "OK". Un PDF así
    hay que VECTORIZARLO (trazar la imagen), no convertirlo.
    """
    try:
        import fitz
        d = fitz.open(ruta)
        pag = d[0]
        info = {"status": "ok", "paginas": len(d),
                "vectores": len(pag.get_drawings()),
                "imagenes": len(pag.get_images())}
        info["es_solo_imagen"] = info["vectores"] == 0 and info["imagenes"] > 0
        d.close()
        return info
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:150], "es_solo_imagen": False}


def _dxf_tiene_contenido(ruta) -> int:
    """Cuántas entidades REALES trae un DXF. 0 = archivo inútil para cortar.
    Existe porque un DXF vacío pesa ~0.2 KB y 'existe', y sin esto se reportaba
    como éxito un archivo que no sirve."""
    try:
        import ezdxf
        return sum(1 for _ in ezdxf.readfile(str(ruta)).modelspace())
    except Exception:
        return 0


def convertir_a_dxf(ruta: str) -> dict:
    """Convierte SVG/PDF/AI/EPS a DXF para laser.
    Si el PDF resulta ser solo una imagen (sin vectores), lo dice claro y manda
    a vectorizar — antes devolvia un DXF vacio diciendo 'OK'."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}

    # Aviso ANTES de gastar minutos en una conversion que no puede funcionar.
    if Path(ruta).suffix.lower() == ".pdf":
        info = pdf_tiene_vectores(ruta)
        if info.get("es_solo_imagen"):
            return {"status": "ERROR", "paso": "diagnostico",
                    "detalle": (f"Ese PDF no tiene dibujo vectorial: trae {info['imagenes']} imagen(es) "
                                f"adentro y 0 vectores"
                                + (f" (son {info['paginas']} páginas)" if info.get("paginas", 1) > 1 else "")
                                + ". Convertirlo daría un DXF vacío. Hay que VECTORIZARLO "
                                  "(trazar la imagen) — pídemelo como 'vectoriza este archivo'."),
                    "sugerencia": "vectorizar", **{k: v for k, v in info.items() if k != "status"}}

    dst = OUT / (Path(ruta).stem + ".dxf")
    code, log = _ink([ruta, "--export-type=dxf", f"--export-filename={dst}"])
    if dst.exists():
        n = _dxf_tiene_contenido(dst)
        if n == 0:
            # Honesto: el archivo existe pero NO sirve para cortar.
            return {"status": "ERROR", "paso": "conversion_vacia",
                    "detalle": ("Se generó el DXF pero salió VACÍO (0 entidades), o sea no sirve "
                                "para cortar. Suele pasar cuando el origen no tiene vectores reales. "
                                "Prueba vectorizándolo en vez de convertirlo."),
                    "salida": str(dst)}
        return {"status": "OK", "salida": str(dst), "entidades": n,
                "kb": round(dst.stat().st_size/1024, 1)}
    return {"status": "ERROR", "detalle": log[-300:]}

def pdf_pagina_a_imagen(ruta: str, pagina: int = 1, dpi: int = 300) -> dict:
    """Saca UNA página de un PDF como imagen PNG, lista para vectorizar.

    Agregado 2026-07-29: los packs de diseños de Anuar vienen en PDFs de varias
    páginas (el del pitbull trae 10, cada una un diseño distinto) y con solo una
    imagen adentro por página. Antes no había forma de sacar la página 7 — se
    convertía la 1 y se perdían las otras 9.
    """
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    try:
        import fitz
        doc = fitz.open(ruta)
        total = len(doc)
        if pagina < 1 or pagina > total:
            doc.close()
            return {"status": "ERROR",
                    "detalle": f"Ese PDF tiene {total} página(s); pediste la {pagina}."}
        pg = doc[pagina - 1]
        pix = pg.get_pixmap(dpi=dpi)
        salida = OUT / f"{Path(ruta).stem}_p{pagina}.png"
        OUT.mkdir(parents=True, exist_ok=True)
        pix.save(str(salida))
        doc.close()
        return {"status": "OK", "salida": str(salida), "pagina": pagina,
                "total_paginas": total, "dpi": dpi,
                "kb": round(salida.stat().st_size / 1024, 1)}
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude extraer la página: {str(e)[:200]}"}


def vectorizar(ruta: str, pagina: int = 1) -> dict:
    """Imagen (PNG/JPG B&N) -> SVG vectorial -> DXF, trazando con Inkscape.
    Si le das un PDF, saca primero la página indicada como imagen y la traza
    (antes un PDF de varias páginas no se podía vectorizar por página)."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}

    nota_pagina = ""
    if Path(ruta).suffix.lower() == ".pdf":
        r_pag = pdf_pagina_a_imagen(ruta, pagina)
        if r_pag.get("status") != "OK":
            return r_pag
        nota_pagina = f"Página {r_pag['pagina']} de {r_pag['total_paginas']} extraída a 300 DPI. "
        ruta = r_pag["salida"]

    svg = OUT / (Path(ruta).stem + "_vector.svg")
    # trazar bitmap a vector y exportar SVG
    code, log = _ink([ruta, "--actions=select-all;trace-bitmap;export-filename:" + str(svg) + ";export-do",
                      "--batch-process"], timeout=180)
    if not svg.exists():
        return {"status": "ERROR", "paso": "trazo", "detalle": log[-300:]}
    # convertir el SVG a DXF
    dxf = OUT / (Path(ruta).stem + "_vector.dxf")
    _ink([str(svg), "--export-type=dxf", f"--export-filename={dxf}"])
    res = {"status": "OK", "svg": str(svg)}
    if nota_pagina:
        res["nota"] = nota_pagina.strip()
    if dxf.exists():
        # Mismo candado honesto que en convertir_a_dxf: un DXF vacio pesa ~0.2 KB,
        # "existe", y sin revisar entidades se reportaba como exito algo inservible.
        n = _dxf_tiene_contenido(dxf)
        res["dxf"] = str(dxf)
        res["entidades"] = n
        res["kb"] = round(dxf.stat().st_size / 1024, 1)
        if n == 0:
            res["status"] = "PARCIAL"
            res["aviso"] = ("El SVG SÍ se generó, pero el DXF salió vacío (0 entidades) y no sirve "
                            "para cortar. Usa el SVG, o pásalo a DXF desde Inkscape a mano.")
    else:
        res["status"] = "PARCIAL"
        res["aviso"] = "Se generó el SVG pero no el DXF. Usa el SVG mientras tanto."
    return res

PY = r"C:\Program Files\Python312\python.exe"
BOXES_DIR = r"C:\NEXUS-original\TOOLS\boxes"
BOXES_MAIN = r"C:\NEXUS-original\TOOLS\boxes\boxes\scripts\boxes_main.py"

GENERADORES_CAJA = ["UniversalBox", "ClosedBox", "TypeTray", "CompartmentBox",
                    "HingeBox", "DisplayShelf", "DividerTray", "AngledBox"]

def caja(x: float = 80, y: float = 50, h: float = 40, thickness: float = 3,
         generador: str = "UniversalBox", dedos: float = 2.0, burn: float = 0.1) -> dict:
    """Genera una caja paramétrica para corte láser (boxes.py) en SVG + DXF."""
    if not os.path.isfile(BOXES_MAIN):
        return {"status": "ERROR", "detalle": "boxes.py no disponible"}
    svg = OUT / f"caja_{generador}_{int(x)}x{int(y)}x{int(h)}.svg"
    env = dict(os.environ); env["PYTHONPATH"] = BOXES_DIR
    args = [PY, BOXES_MAIN, generador, "--x", str(x), "--y", str(y), "--h", str(h),
            "--thickness", str(thickness), "--burn", str(burn),
            "--FingerJoint_finger", str(dedos), "--output", str(svg)]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120, env=env)
        if not svg.exists():
            return {"status": "ERROR", "detalle": (r.stderr or r.stdout)[-300:]}
        dxf = OUT / (svg.stem + ".dxf")
        # Encontrado en vivo 2026-07-29 (Fase 3): el resultado de _ink se ignoraba
        # por completo — si Inkscape fallaba o tardaba de mas (su arranque en frio
        # puede pasar de 60s), la funcion igual respondia "OK" sin DXF y sin decir
        # nada. Ahora se revisa de verdad y se reporta honesto. Timeout mas amplio
        # por el arranque en frio real de Inkscape.
        _code, _salida = _ink([str(svg), "--export-type=dxf", f"--export-filename={dxf}"],
                              timeout=240)
        # boxes.py trabaja en MILIMETROS. La etiqueta anterior decia "cm... mm", que
        # es peligrosamente confuso: pedir "80x50x40" pensando en centimetros daba
        # una caja de 8x5x4 cm (verificado real: el SVG salio de 151.90mm x 165.30mm).
        res = {"status": "OK", "generador": generador,
               "medidas_mm": f"{x} x {y} x {h} mm",
               "medidas_cm": f"{x/10:g} x {y/10:g} x {h/10:g} cm",
               "svg": str(svg)}
        if dxf.exists():
            res["dxf"] = str(dxf); res["kb"] = round(dxf.stat().st_size/1024, 1)
        else:
            res["dxf"] = None
            res["aviso_dxf"] = ("El SVG SI se genero, pero la conversion a DXF con Inkscape "
                                f"no produjo archivo (codigo {_code}). Detalle: {(_salida or '')[-200:]}")
        return res
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}

def reajustar_grosor(x: float, y: float, h: float, nuevo_grosor: float,
                     generador: str = "UniversalBox", dedos: float = 2.0) -> dict:
    """Escalador de grosor: regenera la pieza al NUEVO grosor de material (ej. 2.7mm)
    manteniendo el MISMO tamaño del artículo (x,y,h). Los encastres/dedos ajustan al material."""
    r = caja(x, y, h, nuevo_grosor, generador, dedos)
    if r.get("status") == "OK":
        r["nota"] = f"Artículo {x}x{y}x{h} mm intacto; encastres ajustados a {nuevo_grosor} mm"
    return r

def texto_a_dxf(texto: str, alto_cm: float = 5.0, fuente: str = "Arial") -> dict:
    """Genera un nombre/texto como vector DXF para cortar/grabar."""
    if not texto.strip():
        return {"status": "ERROR", "detalle": "Texto vacio"}
    mm = alto_cm * 10
    fs = mm * 1.4  # font-size aprox para que la altura de mayusculas ~ alto pedido
    ancho = mm * (len(texto) * 0.75) + 40
    svg_txt = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}mm" height="{mm*1.6}mm" '
               f'viewBox="0 0 {ancho} {mm*1.6}">'
               f'<text x="10" y="{mm*1.2}" font-family="{fuente}" font-size="{fs}" '
               f'fill="none" stroke="black" stroke-width="0.5">{texto}</text></svg>')
    base = "".join(c for c in texto if c.isalnum()) or "texto"
    svg = OUT / (base + ".svg")
    svg.write_text(svg_txt, encoding="utf-8")
    # convertir texto a trazo (curvas) y exportar DXF
    dxf = OUT / (base + ".dxf")
    code, log = _ink([str(svg), "--actions=select-all;object-to-path;export-filename:" + str(dxf) + ";export-type:dxf;export-do",
                      "--batch-process"], timeout=120)
    if not dxf.exists():
        # fallback: export directo
        _ink([str(svg), "--export-type=dxf", f"--export-filename={dxf}"])
    if dxf.exists():
        return {"status": "OK", "dxf": str(dxf), "kb": round(dxf.stat().st_size/1024, 1), "alto_cm": alto_cm}
    return {"status": "ERROR", "detalle": log[-300:]}
