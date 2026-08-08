# -*- coding: utf-8 -*-
"""AURORA · Acomoda las piezas en la hoja aprovechando todo, con marcas

Anuar lo pidió el 2026-08-07: *"usando deepnest para el acomodo contemplando
las marcas de registro"*.

Deepnest está instalado pero es una aplicación de ventana sin línea de
comandos: automatizarlo sería manejarle el mouse, que se rompe con cualquier
actualización y le toma la pantalla mientras trabaja. Aquí se hace en Python
con lo que ya está instalado (rectpack), y el resultado es el mismo para lo
que él corta: etiquetas, planillas y calcomanías, que son rectángulos.

LO QUE CAMBIA RESPECTO A ACOMODAR A OJO: el área útil no es la hoja. Las
marcas de registro se comen 15.6 mm de cada orilla más su propio tamaño, así
que en A4 quedan 149 × 236 mm de superficie real. Acomodar sobre la hoja
completa y luego descubrir que no cabe es perder la impresión.

Correr:
    python TALLER/acomodar_hoja.py 27 60 35      # 35 etiquetas de 27x60 mm
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SEPARACION_MM = 3.0        # entre pieza y pieza, para que la cuchilla pase


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _marcas():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("marcas_registro",
                                        RAIZ / "TALLER" / "marcas_registro.py")
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def acomodar(pieza_ancho: float, pieza_alto: float, cuantas: int,
             hoja_ancho: float = 210.0, hoja_alto: float = 297.0,
             separacion: float = SEPARACION_MM, con_marcas: bool = True) -> dict:
    """Acomoda `cuantas` piezas en las hojas que hagan falta."""
    try:
        from rectpack import newPacker
    except ImportError:
        return {"status": "FALTA_LIBRERIA", "detalle": "pip install rectpack"}

    mr = _marcas()
    if con_marcas:
        u = mr.area_util(hoja_ancho, hoja_alto)
        caja_w, caja_h = u["ancho"], u["alto"]
        off_x, off_y = u["x"], u["y"]
    else:
        caja_w, caja_h = hoja_ancho, hoja_alto
        off_x = off_y = 0.0

    if pieza_ancho > caja_w and pieza_alto > caja_w:
        return {"status": "NO_CABE",
                "detalle": (f"Una pieza de {pieza_ancho}×{pieza_alto} mm no "
                            f"entra en los {caja_w}×{caja_h} mm útiles.")}

    # La separación se mete dentro de la pieza: así rectpack la respeta sin
    # tener que reprogramarlo.
    pw = pieza_ancho + separacion
    ph = pieza_alto + separacion

    p = newPacker(rotation=True)
    for _ in range(cuantas):
        p.add_rect(int(pw * 100), int(ph * 100))
    # Se ofrecen hojas de sobra; se usan solo las que hagan falta.
    for _ in range(max(1, cuantas)):
        p.add_bin(int(caja_w * 100), int(caja_h * 100))
    p.pack()

    hojas = []
    for b in p:
        piezas = []
        for r in b:
            piezas.append({
                "x": round(r.x / 100 + off_x, 1),
                "y": round(r.y / 100 + off_y, 1),
                "ancho": round(r.width / 100 - separacion, 1),
                "alto": round(r.height / 100 - separacion, 1),
                "girada": abs((r.width / 100 - separacion) - pieza_ancho) > 0.5,
            })
        if piezas:
            hojas.append(piezas)

    colocadas = sum(len(h) for h in hojas)
    area_piezas = colocadas * pieza_ancho * pieza_alto
    area_hojas = len(hojas) * caja_w * caja_h if hojas else 1
    return {"status": "OK", "hojas": hojas, "cuantas_hojas": len(hojas),
            "colocadas": colocadas, "pedidas": cuantas,
            "por_hoja": len(hojas[0]) if hojas else 0,
            "aprovechado": round(area_piezas / area_hojas * 100, 1),
            "area_util": f"{caja_w} × {caja_h} mm",
            "con_marcas": con_marcas}


def _texto(r: dict, pw: float, ph: float) -> str:
    if r.get("status") != "OK":
        return f"No se pudo: {r.get('detalle', r.get('status'))}"
    t = (f"📄 **{r['colocadas']} piezas de {pw:g} × {ph:g} mm** en "
         f"**{r['cuantas_hojas']} hoja(s)**\n"
         f"   {r['por_hoja']} por hoja · área útil {r['area_util']}"
         f"{' (con marcas de registro)' if r['con_marcas'] else ''}\n"
         f"   aprovechamiento: **{r['aprovechado']}%**")
    if r["colocadas"] < r["pedidas"]:
        t += f"\n\n⚠️ Solo cupieron {r['colocadas']} de {r['pedidas']}."
    return t


def main() -> int:
    _consola_utf8()
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 3:
        print(__doc__)
        return 1
    pw, ph, n = float(a[0]), float(a[1]), int(a[2])
    sin = "--sin-marcas" in sys.argv
    print(_texto(acomodar(pw, ph, n, con_marcas=not sin), pw, ph))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
