# -*- coding: utf-8 -*-
"""AURORA · Partir un DXF grande en varias hojas para mandar a maquilar

Pedido real de Anuar (2026-08-21): un DXF de 900x487.5mm (RUMO) no cabe en
una sola hoja de maquila — hay que partirlo en 3 y mandarlo así. Esto NO es
nesting (acomodar piezas distintas en una hoja): es lo contrario, partir UNA
pieza grande en varios pedazos que sí quepan, con traslape para poder volver
a pegarlos o alinearlos en la maquiladora.

Corta con líneas VERTICALES (parte el ancho en N tiras) por default, porque
así lo pidió él la primera vez. Cada entidad se recorta de verdad contra el
rectángulo de su tira (no se adivina un bounding box) usando shapely.

Correr:  python TALLER/dividir_en_hojas.py "C:\\ruta\\archivo.dxf" 3
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _carpeta_dxf() -> Path:
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("carpetas_por_tipo",
                                            RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de("dxf")
    except Exception:
        d = Path.home() / "Downloads" / "dxf"
        d.mkdir(parents=True, exist_ok=True)
        return d


TABLOIDE_MM = (279.4, 431.8)   # 11x17in - el tamaño real que se manda a maquilar


def dividir(ruta_dxf: str, n_partes: int = None, direccion: str = "vertical",
            traslape_mm: float = 5.0, hoja_mm: tuple = TABLOIDE_MM) -> dict:
    """Parte el DXF en una cuadrícula de hojas que SÍ caben en el tamaño real
    que se manda a maquilar (tabloide por default: 279.4x431.8mm).

    Si se da n_partes, se respeta tal cual (una sola fila o columna, modo
    viejo). Si no, se calcula solo cuántas hojas hacen falta en cada eje para
    que ninguna tira exceda hoja_mm — probando las 2 orientaciones de la hoja
    y quedándose con la que pide menos hojas en total.
    traslape_mm: cuánto se repite entre una hoja y la siguiente, para alinear
    al pegar o mandar a cortar por separado.
    """
    try:
        import ezdxf
        from shapely.geometry import box, LineString, Polygon
        from shapely.ops import unary_union
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    ruta = Path(ruta_dxf)
    if not ruta.exists():
        return {"status": "ERROR", "detalle": f"No existe: {ruta}"}

    src = ezdxf.readfile(str(ruta))
    msp = src.modelspace()

    # Se juntan TODAS las entidades de línea/polilínea como geometrías shapely.
    geoms = []
    for e in msp:
        t = e.dxftype()
        try:
            if t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
            elif t == "POLYLINE":
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            elif t == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            else:
                continue
        except Exception:
            continue
        if len(pts) < 2:
            continue
        cerrada = getattr(e, "is_closed", False) or (
            len(pts) > 2 and pts[0] == pts[-1])
        try:
            geoms.append(Polygon(pts) if cerrada else LineString(pts))
        except Exception:
            geoms.append(LineString(pts))

    if not geoms:
        return {"status": "ERROR", "detalle": "El DXF no trae líneas/polilíneas que partir."}

    todo = unary_union(geoms)
    minx, miny, maxx, maxy = todo.bounds
    ancho_total = maxx - minx
    alto_total = maxy - miny

    salidas = []
    DESTINO = _carpeta_dxf()
    DESTINO.mkdir(parents=True, exist_ok=True)

    if n_partes:
        # modo viejo: una sola fila o columna, tal como se pida.
        if direccion == "vertical":
            paso = ancho_total / n_partes
            for i in range(n_partes):
                x0 = minx + i * paso - (traslape_mm if i > 0 else 0)
                x1 = minx + (i + 1) * paso + (traslape_mm if i < n_partes - 1 else 0)
                tile = box(x0, miny - 1, x1, maxy + 1)
                salidas.append(_escribir_tile(src, geoms, tile, DESTINO, ruta.stem, i, n_partes))
        else:
            paso = alto_total / n_partes
            for i in range(n_partes):
                y0 = miny + i * paso - (traslape_mm if i > 0 else 0)
                y1 = miny + (i + 1) * paso + (traslape_mm if i < n_partes - 1 else 0)
                tile = box(minx - 1, y0, maxx + 1, y1)
                salidas.append(_escribir_tile(src, geoms, tile, DESTINO, ruta.stem, i, n_partes))
        return {"status": "OK", "n_partes": n_partes, "direccion": direccion,
                "tamano_original_mm": (round(ancho_total, 1), round(alto_total, 1)),
                "traslape_mm": traslape_mm, "archivos": salidas}

    # modo cuadrícula: se calcula cuántas hojas hacen falta en cada eje para
    # que ninguna tira exceda hoja_mm, probando las 2 orientaciones de la
    # hoja y quedándose con la que pida menos hojas en total.
    import math as _m
    mejor = None
    for hw, hh in (hoja_mm, (hoja_mm[1], hoja_mm[0])):
        nx = max(1, _m.ceil(ancho_total / hw))
        ny = max(1, _m.ceil(alto_total / hh))
        total = nx * ny
        if mejor is None or total < mejor[2]:
            mejor = (nx, ny, total, (hw, hh))
    nx, ny, total, hoja_usada = mejor

    paso_x = ancho_total / nx
    paso_y = alto_total / ny
    n = 0
    for iy in range(ny):
        for ix in range(nx):
            x0 = minx + ix * paso_x - (traslape_mm if ix > 0 else 0)
            x1 = minx + (ix + 1) * paso_x + (traslape_mm if ix < nx - 1 else 0)
            y0 = miny + iy * paso_y - (traslape_mm if iy > 0 else 0)
            y1 = miny + (iy + 1) * paso_y + (traslape_mm if iy < ny - 1 else 0)
            tile = box(x0, y0, x1, y1)
            n += 1
            salidas.append(_escribir_tile(src, geoms, tile, DESTINO, ruta.stem, n - 1, nx * ny,
                                          fila=iy, col=ix))

    return {"status": "OK", "n_partes": nx * ny, "grid": (nx, ny),
            "hoja_mm": hoja_usada,
            "tamano_original_mm": (round(ancho_total, 1), round(alto_total, 1)),
            "traslape_mm": traslape_mm, "archivos": salidas}

    return {"status": "OK", "n_partes": n_partes, "direccion": direccion,
            "tamano_original_mm": (round(ancho_total, 1), round(alto_total, 1)),
            "traslape_mm": traslape_mm, "archivos": salidas}


def _escribir_tile(src, geoms, tile, destino: Path, stem: str, i: int, n: int,
                    fila: int = None, col: int = None) -> dict:
    import ezdxf
    out = ezdxf.new("R2010")
    out.units = ezdxf.units.MM
    out.header["$INSUNITS"] = 4
    out.layers.add("CORTE", color=1)
    msp = out.modelspace()

    n_ent = 0
    for g in geoms:
        inter = g.intersection(tile)
        if inter.is_empty:
            continue
        partes = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
        for parte in partes:
            if parte.geom_type == "Polygon":
                coords = list(parte.exterior.coords)
                if len(coords) >= 3:
                    msp.add_lwpolyline(coords, close=True, dxfattribs={"layer": "CORTE"})
                    n_ent += 1
            elif parte.geom_type in ("LineString",):
                coords = list(parte.coords)
                if len(coords) >= 2:
                    msp.add_lwpolyline(coords, close=False, dxfattribs={"layer": "CORTE"})
                    n_ent += 1

    if fila is not None:
        salida = destino / f"{stem}_f{fila+1}c{col+1}_de{n}.dxf"
    else:
        salida = destino / f"{stem}_parte{i+1}de{n}.dxf"
    k = 2
    while salida.exists():
        salida = destino / f"{stem}_parte{i+1}de{n}__{k}.dxf"
        k += 1
    out.saveas(str(salida))
    b = tile.bounds
    return {"archivo": str(salida), "n_entidades": n_ent,
            "tamano_mm": (round(b[2] - b[0], 1), round(b[3] - b[1], 1))}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    ruta = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else None
    r = dividir(ruta, n)
    if r.get("status") != "OK":
        print(r.get("detalle"))
    else:
        extra = f"grid {r['grid']}, hoja usada {r['hoja_mm']}" if "grid" in r else \
                f"partido en {r['n_partes']} ({r['direccion']})"
        print(f"Original: {r['tamano_original_mm'][0]} x {r['tamano_original_mm'][1]} mm, "
              f"{extra}, traslape {r['traslape_mm']}mm")
        for a in r["archivos"]:
            print(f"  {a['archivo']}  -> {a['tamano_mm'][0]} x {a['tamano_mm'][1]} mm, "
                  f"{a['n_entidades']} entidades")
