# -*- coding: utf-8 -*-
"""AURORA · El contorno de corte de una hoja ya impresa (Print & Cut)

Anuar lo pidió el 2026-08-06 con las hojas de los vasos de Luisa ya impresas:
*"quiero un pequeño contorno extra"*. Y es exactamente lo que se hace cuando
se corta sin marcas de registro — el corte no va justo en la orilla del
dibujo, va **un poco por fuera**, para que un desfase de un milímetro no deje
el filito blanco.

El contorno se saca de la TINTA REAL, no del rectángulo donde está puesta la
imagen: una imagen suele traer margen transparente y cortar por ahí dejaría
un borde vacío alrededor de la pieza.

Lo que sí hay que respetar es el hueco entre piezas: si el contorno extra es
más grande que la mitad del hueco, los cortes se tocan y se arruina la hoja.
Por eso se mide el hueco y se avisa antes de escribir nada.

Correr:
    python EDITOR/contorno_de_corte.py "C:\\ruta\\hoja.pdf" 1.5
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Todo lo más oscuro que esto cuenta como tinta impresa.
UMBRAL_TINTA = 235
# Puntos por milímetro al rasterizar. Más alto = más fino, y más lento.
CALIDAD = 4


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
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def generar(ruta: str, extra_mm: float = 1.5, margen_marcas_mm: float = 20.0) -> dict:
    """Saca el contorno de corte de cada pieza impresa, crecido `extra_mm`."""
    p = Path(ruta)
    if not p.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {ruta}"}
    try:
        import cv2
        import fitz
        import numpy as np
        import ezdxf
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    doc = fitz.open(str(p))
    pag = doc[0]
    hoja_w = pag.rect.width / 72 * 25.4
    hoja_h = pag.rect.height / 72 * 25.4

    pm = pag.get_pixmap(matrix=fitz.Matrix(CALIDAD, CALIDAD))
    img = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
    gris = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2GRAY)
    mm_px = 25.4 / 72 / CALIDAD

    # LAS MARCAS DE IMPRENTA SE IGNORAN. En la hoja de Luisa había 8 cuadros y
    # 16 cruces de Corel pegados a las orillas; si se toman por dibujo, el
    # contorno abarcaría toda la hoja y no serviría de nada.
    borde = int(margen_marcas_mm / mm_px)
    gris[:borde, :] = 255
    gris[-borde:, :] = 255
    gris[:, :borde] = 255
    gris[:, -borde:] = 255

    tinta = (gris < UMBRAL_TINTA).astype("uint8") * 255
    # Se cierran los huecos del medio tono para que cada pieza salga entera y
    # no en pedazos.
    cerrar = max(3, int(1.5 / mm_px) | 1)
    tinta = cv2.morphologyEx(tinta, cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                       (cerrar, cerrar)))

    contornos, _ = cv2.findContours(tinta, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    minimo_area = (10 / mm_px) ** 2          # menos de 1 cm² es basura
    piezas = [c for c in contornos if cv2.contourArea(c) > minimo_area]
    if not piezas:
        return {"status": "SIN_PIEZAS",
                "detalle": "No encontré nada impreso que valga la pena cortar."}

    # ¿CABE EL CONTORNO EXTRA? Se mide la distancia entre piezas vecinas.
    cajas = [cv2.boundingRect(c) for c in piezas]
    hueco_min = None
    for i, (x1, y1, w1, h1) in enumerate(cajas):
        for x2, y2, w2, h2 in cajas[i + 1:]:
            dx = max(0, max(x1, x2) - min(x1 + w1, x2 + w2)) * mm_px
            dy = max(0, max(y1, y2) - min(y1 + h1, y2 + h2)) * mm_px
            d = max(dx, dy)
            if d > 0 and (hueco_min is None or d < hueco_min):
                hueco_min = d

    aviso = ""
    if hueco_min is not None and extra_mm * 2 >= hueco_min - 0.3:
        cabe = round(max(0.3, (hueco_min - 0.6) / 2), 1)
        aviso = (f"El hueco más chico entre piezas es de {hueco_min:.1f} mm: "
                 f"con {extra_mm} mm por lado los cortes se tocan. "
                 f"El máximo que cabe aquí es {cabe} mm.")
        return {"status": "NO_CABE", "detalle": aviso,
                "hueco_min": round(hueco_min, 1), "maximo": cabe}

    # Crecer el contorno: se dilata la mancha y se vuelve a trazar. Es más
    # fiel a la forma real que empujar los puntos uno por uno.
    crecer = max(1, int(extra_mm / mm_px)) | 1
    gordo = cv2.dilate(tinta, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                        (crecer * 2, crecer * 2)))
    cont2, _ = cv2.findContours(gordo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cont2 = [c for c in cont2 if cv2.contourArea(c) > minimo_area]

    dxf = ezdxf.new("R2010")
    dxf.layers.add("CORTE", color=1)
    msp = dxf.modelspace()
    for c in cont2:
        # Se simplifica: 0.2 mm de tolerancia quita los dientes del pixel sin
        # deformar la silueta.
        suave = cv2.approxPolyDP(c, 0.2 / mm_px, True)
        pts = [(float(q[0][0]) * mm_px, hoja_h - float(q[0][1]) * mm_px)
               for q in suave]
        if len(pts) > 2:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CORTE"})

    salida = _carpeta("dxf") / f"{p.stem}_CORTE_{extra_mm:g}mm.dxf"
    n = 2
    while salida.exists():
        salida = salida.parent / f"{p.stem}_CORTE_{extra_mm:g}mm__{n}.dxf"
        n += 1
    dxf.saveas(str(salida))

    return {"status": "OK", "archivo": str(salida), "piezas": len(cont2),
            "extra_mm": extra_mm, "hoja": f"{hoja_w:.1f} × {hoja_h:.1f} mm",
            "hueco_min": round(hueco_min, 1) if hueco_min else None,
            "kb": round(salida.stat().st_size / 1024, 1)}


def _texto(r: dict) -> str:
    s = r.get("status")
    if s == "NO_CABE":
        return (f"⚠️ No cabe ese contorno extra.\n   {r['detalle']}\n\n"
                f"_Pídemelo de {r['maximo']} mm y lo saco._")
    if s != "OK":
        return f"No pude sacarlo: {r.get('detalle', s)}"
    t = (f"✂️ **Contorno de corte** — {r['piezas']} piezas, "
         f"{r['extra_mm']} mm por fuera del dibujo\n"
         f"   hoja de {r['hoja']}")
    if r.get("hueco_min"):
        t += f" · hueco entre piezas: {r['hueco_min']} mm"
    return (t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)\n\n"
            "**Corta la primera hoja con la que peor te haya salido.** Sin "
            "marcas de registro la máquina no corrige nada: lo que veas en "
            "esa, va a hacer en todas.")


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    extra = float(args[1]) if len(args) > 1 else 1.5
    print(_texto(generar(args[0], extra)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
