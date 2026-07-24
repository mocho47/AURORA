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

def _ink(args, timeout=120):
    try:
        r = subprocess.run([INK] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
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

def convertir_a_dxf(ruta: str) -> dict:
    """Convierte SVG/PDF/AI/EPS a DXF para laser."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
    dst = OUT / (Path(ruta).stem + ".dxf")
    code, log = _ink([ruta, "--export-type=dxf", f"--export-filename={dst}"])
    if dst.exists():
        return {"status": "OK", "salida": str(dst), "kb": round(dst.stat().st_size/1024, 1)}
    return {"status": "ERROR", "detalle": log[-300:]}

def vectorizar(ruta: str) -> dict:
    """Imagen (PNG/JPG B&N) -> SVG vectorial -> DXF, trazando con Inkscape."""
    ruta = _clean(ruta)
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}
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
    if dxf.exists():
        res["dxf"] = str(dxf); res["kb"] = round(dxf.stat().st_size/1024, 1)
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
        _ink([str(svg), "--export-type=dxf", f"--export-filename={dxf}"])
        res = {"status": "OK", "generador": generador, "medidas": f"{x}x{y}x{h}cm... mm",
               "svg": str(svg)}
        if dxf.exists():
            res["dxf"] = str(dxf); res["kb"] = round(dxf.stat().st_size/1024, 1)
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
