# -*- coding: utf-8 -*-
"""AURORA · Genera cajas para corte láser dando solo las medidas

Anuar lo recordó el 2026-08-05: uno de sus proyectos viejos podía crear cajas
desde el chat dándole las medidas, y cotizarlas. Tenía razón en que se puede
hacer nativo — es geometría, no hace falta ningún programa externo.

Genera el DXF real con dientes de ensamble (finger joints), que es lo que hace
que la caja se arme sola sin clavos: cada pieza encaja en la siguiente.

Y de una vez calcula los metros de corte, el tiempo y el precio con los números
reales de Anuar: $8.00 por minuto a 25 mm/s.

Correr:
    python TALLER/generar_caja.py 40 30 7
    python TALLER/generar_caja.py 40 30 7 --grosor 5.5 --divisiones 2 --tapa
"""
from __future__ import annotations
import io
import math
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DESTINO = Path.home() / "Downloads" / "dxf"

# Los números de Anuar se PIDEN, no se copian (arreglo 2026-08-26). Este
# archivo tenía su propia copia y se había quedado en 25 mm/s cuando él ya
# había dictado 20: cada caja que se cotizara desde aquí salía con el tiempo
# de máquina —y el precio— equivocados. Ahora vienen de TALLER/formula_precios,
# que es el único lugar donde viven.
def _numero(clave: str) -> float:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "formula_precios", RAIZ / "TALLER" / "formula_precios.py")
    _fp = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_fp)
    return _fp.numero(clave)


COSTO_MINUTO = _numero("minuto_corte")
VELOCIDAD_MM_S = _numero("velocidad_mm_s")
PRECIO_HOJA = {2.7: _numero("hoja_mdf_2_7"),
               5.5: _numero("hoja_mdf_5_5"),
               4.0: _numero("hoja_mdf_4_0")}
HOJA_CM2 = _numero("hoja_cm2")


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _dientes(largo_mm: float, grosor_mm: float) -> list:
    """Reparte los dientes a lo largo de un borde.

    Devuelve la lista de (inicio, fin) de cada diente que SOBRESALE. Se usa un
    número IMPAR para que el borde empiece y termine con diente: así la esquina
    queda cerrada y la caja no se abre por las puntas.
    """
    ancho_ideal = grosor_mm * 3          # regla de taller: diente = 3x el grosor
    n = max(3, int(largo_mm / ancho_ideal))
    if n % 2 == 0:
        n -= 1                            # impar: empieza y termina con diente
    paso = largo_mm / n
    return [(i * paso, (i + 1) * paso) for i in range(0, n, 2)]


def _borde_dentado(x0: float, y0: float, largo: float, grosor: float,
                   horizontal: bool, hacia_afuera: bool) -> list:
    """Puntos de un borde con dientes. Empieza en (x0,y0) y avanza `largo`."""
    pts = [(x0, y0)]
    d = grosor if hacia_afuera else -grosor
    pos = 0.0
    for ini, fin in _dientes(largo, grosor):
        if horizontal:
            pts += [(x0 + ini, y0), (x0 + ini, y0 + d),
                    (x0 + fin, y0 + d), (x0 + fin, y0)]
        else:
            pts += [(x0, y0 + ini), (x0 + d, y0 + ini),
                    (x0 + d, y0 + fin), (x0, y0 + fin)]
        pos = fin
    pts.append((x0 + largo, y0) if horizontal else (x0, y0 + largo))
    return pts


def _cara(ancho: float, alto: float, grosor: float,
          dentados: tuple = (True, True, True, True)) -> list:
    """Una cara rectangular con dientes en los lados que se le indiquen.

    dentados = (abajo, derecha, arriba, izquierda)
    """
    pts = []
    ab, de, ar, iz = dentados
    # abajo, de izquierda a derecha
    pts += _borde_dentado(0, 0, ancho, grosor, True, False) if ab else [(0, 0), (ancho, 0)]
    # derecha, de abajo hacia arriba
    pts += _borde_dentado(ancho, 0, alto, grosor, False, True) if de else [(ancho, 0), (ancho, alto)]
    # arriba, de derecha a izquierda
    if ar:
        arriba = _borde_dentado(0, alto, ancho, grosor, True, True)
        pts += list(reversed(arriba))
    else:
        pts += [(ancho, alto), (0, alto)]
    # izquierda, de arriba hacia abajo
    if iz:
        izq = _borde_dentado(0, 0, alto, grosor, False, False)
        pts += list(reversed(izq))
    else:
        pts += [(0, alto), (0, 0)]
    return pts


def generar(ancho_cm: float, alto_cm: float, profundidad_cm: float,
            grosor_mm: float = 2.7, divisiones: int = 0,
            con_tapa: bool = False, nombre: str = "") -> dict:
    """Genera el DXF real de la caja y calcula su precio.

    ancho x alto = la BASE vista desde arriba. profundidad = qué tan honda.
    """
    try:
        import ezdxf
    except ImportError:
        return {"status": "FALTA_LIBRERIA",
                "detalle": "Falta ezdxf: pip install ezdxf"}

    A, L, P = ancho_cm * 10.0, alto_cm * 10.0, profundidad_cm * 10.0   # a mm
    g = float(grosor_mm)

    doc = ezdxf.new("R2010")
    doc.units = 4                      # milímetros
    msp = doc.modelspace()

    sep = 15.0                         # separación entre piezas en la hoja
    cursor_y = 0.0
    piezas = []

    def poner(pts, etiqueta, dx=0.0, dy=0.0):
        msp.add_lwpolyline([(x + dx, y + dy) for x, y in pts], close=True)
        piezas.append(etiqueta)

    # Base (y tapa, si lleva): dientes en los 4 lados.
    base = _cara(A, L, g)
    poner(base, "base", 0, cursor_y)
    cursor_y += L + g * 2 + sep
    if con_tapa:
        poner(base, "tapa", 0, cursor_y)
        cursor_y += L + g * 2 + sep

    # Paredes largas (2): ancho A x profundidad P
    pared_larga = _cara(A, P, g)
    for i in range(2):
        poner(pared_larga, f"pared larga {i+1}", 0, cursor_y)
        cursor_y += P + g * 2 + sep

    # Paredes cortas (2): alto L x profundidad P
    pared_corta = _cara(L, P, g)
    for i in range(2):
        poner(pared_corta, f"pared corta {i+1}", 0, cursor_y)
        cursor_y += P + g * 2 + sep

    # Divisiones internas: van a lo ancho, con dientes solo en los costados.
    for i in range(max(0, int(divisiones))):
        div = _cara(L, P, g, dentados=(False, True, False, True))
        poner(div, f"division {i+1}", 0, cursor_y)
        cursor_y += P + g * 2 + sep

    # ── Metros de corte reales del dibujo generado ────────────────────
    mm_total = 0.0
    for e in msp:
        pts = [(p[0], p[1]) for p in e.get_points()]
        mm_total += sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        mm_total += math.dist(pts[-1], pts[0])

    metros = round(mm_total / 1000.0, 2)
    minutos = round(mm_total / VELOCIDAD_MM_S / 60.0, 1)
    costo_corte = round(minutos * COSTO_MINUTO, 2)

    # Material: el área que ocupa el acomodo, con 25% de merma.
    area_cm2 = (max(A, L) / 10.0) * (cursor_y / 10.0)
    precio_hoja = PRECIO_HOJA.get(round(g, 1), 110.0)
    material = round(area_cm2 / HOJA_CM2 * precio_hoja * 1.25, 2)

    costo = round(costo_corte + material, 2)
    precio = max(round(costo * 3, -1), 450 if divisiones or con_tapa else 180)

    DESTINO.mkdir(parents=True, exist_ok=True)
    base_nombre = nombre or (f"caja_{ancho_cm:g}x{alto_cm:g}x{profundidad_cm:g}"
                             f"_{grosor_mm:g}mm"
                             + (f"_{divisiones}div" if divisiones else "")
                             + ("_tapa" if con_tapa else ""))
    salida = DESTINO / f"{base_nombre}.dxf"
    n = 2
    while salida.exists():
        salida = DESTINO / f"{base_nombre}__{n}.dxf"
        n += 1
    doc.saveas(str(salida))

    return {
        "status": "OK",
        "archivo": str(salida),
        "piezas": len(piezas),
        "detalle_piezas": piezas,
        "medidas": f"{ancho_cm} × {alto_cm} × {profundidad_cm} cm",
        "grosor_mm": g,
        "metros_corte": metros,
        "minutos": minutos,
        "costo_corte": costo_corte,
        "material": material,
        "costo": costo,
        "precio_sugerido": precio,
        "generado": datetime.now().isoformat(timespec="seconds"),
    }


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return r.get("detalle", "No pude generar la caja.")
    return (
        f"📦 **Caja {r['medidas']}** en MDF de {r['grosor_mm']:g} mm\n"
        f"   {r['piezas']} piezas con dientes de ensamble (se arma sola)\n\n"
        f"✂️ **{r['metros_corte']} m** de corte · **{r['minutos']} min**\n\n"
        f"   corte     ${r['costo_corte']:.2f}\n"
        f"   material  ${r['material']:.2f}\n"
        f"   **COSTO   ${r['costo']:.2f}**\n\n"
        f"💰 **PRECIO SUGERIDO: ${r['precio_sugerido']:.0f}**\n\n"
        f"📁 `{r['archivo']}`\n"
        f"_Ábrelo en Corel o mándalo directo a RDWorks._"
    )


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        print(__doc__)
        return 1
    ancho, alto, prof = float(args[0]), float(args[1]), float(args[2])
    grosor = 2.7
    divisiones = 0
    if "--grosor" in sys.argv:
        grosor = float(sys.argv[sys.argv.index("--grosor") + 1])
    if "--divisiones" in sys.argv:
        divisiones = int(sys.argv[sys.argv.index("--divisiones") + 1])
    r = generar(ancho, alto, prof, grosor, divisiones, "--tapa" in sys.argv)
    print(_texto(r))
    return 0 if r.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
