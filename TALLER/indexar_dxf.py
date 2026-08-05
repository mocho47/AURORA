# -*- coding: utf-8 -*-
"""AURORA · Catálogo de los DXF que Anuar YA tiene, con su precio calculado

El 2026-08-04 le pidieron una casa de muñecas y no pudo cotizarla frente al
cliente: no tenía el DXF a la mano, así que no había metros de corte, y sin
metros no hay precio. La vendió en $280 cuando costaba ~$200 producirla.

Y resulta que ya tiene **665 archivos DXF** en el disco. El problema nunca fue
falta de diseños: es que no sabe qué tiene ni cuánto cuesta cada uno.

Esto recorre todos, mide los METROS LINEALES DE CORTE reales (no solo el ancho
y alto, que es lo único que medía medidor_dxf) y calcula tiempo, costo y precio
con los datos reales de Anuar: $8.00 por minuto de láser y 25 mm/s en MDF 2.7.

Correr:   python TALLER/indexar_dxf.py
Buscar:   python TALLER/indexar_dxf.py --buscar casa
"""
from __future__ import annotations
import io
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CATALOGO = RAIZ / "CONFIG" / "catalogo_dxf.json"

# Datos REALES de Anuar (CONFIG/precios_base.json y su recetario probado).
COSTO_MINUTO = 8.0
VELOCIDAD_MM_S = 25.0        # su 60%/25 mm/s probado en MDF 2.7
MARGEN = 3.0                 # precio = costo x3, la cuenta que se hace en la cabeza

# Carpetas que no son biblioteca de diseños.
_IGNORAR = ("_OBSOLETOS", "_ARCHIVE", "_RESCATE", "node_modules", "site-packages",
            "__pycache__", ".git", "AppData", "_BACKUP")


def _largo_entidad(e) -> float:
    """Largo de corte de una entidad, en milímetros. 0 si no se puede medir."""
    try:
        t = e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return math.dist((a.x, a.y), (b.x, b.y))
        if t == "CIRCLE":
            return 2 * math.pi * e.dxf.radius
        if t == "ARC":
            ang = (e.dxf.end_angle - e.dxf.start_angle) % 360
            return 2 * math.pi * e.dxf.radius * (ang / 360.0)
        if t in ("LWPOLYLINE", "POLYLINE"):
            pts = [(p[0], p[1]) for p in e.get_points()] if t == "LWPOLYLINE" else \
                  [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            if len(pts) < 2:
                return 0.0
            largo = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
            if getattr(e, "closed", False) or e.dxf.get("flags", 0) & 1:
                largo += math.dist(pts[-1], pts[0])
            return largo
        if t == "SPLINE":
            # Se aproxima por sus puntos de control: suficiente para cotizar.
            pts = [(p[0], p[1]) for p in e.control_points]
            return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        if t == "ELLIPSE":
            a = e.dxf.major_axis.magnitude
            b = a * e.dxf.ratio
            return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    except Exception:
        pass
    return 0.0


def medir(ruta: Path) -> dict:
    """Metros de corte, medidas y precio de un DXF. Nada estimado a ojo."""
    import ezdxf
    try:
        doc = ezdxf.readfile(str(ruta))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:60]}"}

    msp = doc.modelspace()
    mm_total, piezas = 0.0, 0
    xs, ys = [], []
    for e in msp:
        largo = _largo_entidad(e)
        if largo > 0:
            mm_total += largo
            piezas += 1
        try:
            if e.dxftype() == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif e.dxftype() in ("CIRCLE", "ARC"):
                c, r = e.dxf.center, e.dxf.radius
                xs += [c.x - r, c.x + r]
                ys += [c.y - r, c.y + r]
        except Exception:
            pass

    metros = round(mm_total / 1000.0, 2)
    minutos = round(mm_total / VELOCIDAD_MM_S / 60.0, 1)
    costo_corte = round(minutos * COSTO_MINUTO, 2)
    ancho = round((max(xs) - min(xs)) / 10.0, 1) if xs else 0.0   # a cm
    alto = round((max(ys) - min(ys)) / 10.0, 1) if ys else 0.0

    return {
        "archivo": ruta.name,
        "ruta": str(ruta),
        "ancho_cm": ancho,
        "alto_cm": alto,
        "entidades": piezas,
        "metros_corte": metros,
        "minutos": minutos,
        "costo_corte": costo_corte,
        "precio_sugerido": round(costo_corte * MARGEN, -1) or 60.0,
    }


def indexar(raiz: Path = None) -> dict:
    raiz = raiz or Path.home()
    archivos = [p for p in raiz.rglob("*.dxf")
                if not any(x in str(p) for x in _IGNORAR)]
    print(f"Encontrados {len(archivos)} DXF. Midiendo metros de corte reales...")
    print("=" * 78)

    catalogo, fallidos = [], 0
    for i, p in enumerate(archivos, 1):
        d = medir(p)
        if d.get("error"):
            fallidos += 1
            continue
        catalogo.append(d)
        if i % 50 == 0:
            print(f"   [{i}/{len(archivos)}]")

    catalogo.sort(key=lambda x: -x["metros_corte"])
    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_text(json.dumps({
        "nota": ("Catálogo de los DXF de Anuar con metros de corte REALES medidos "
                 "con ezdxf. Precio = minutos x $8 x 3. Regenerar con "
                 "python TALLER/indexar_dxf.py"),
        "costo_minuto": COSTO_MINUTO,
        "velocidad_mm_s": VELOCIDAD_MM_S,
        "total": len(catalogo),
        "disenos": catalogo,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 78)
    print(f"  Catalogados : {len(catalogo)}")
    print(f"  No se pudo  : {fallidos}")
    print(f"  Guardado en : {CATALOGO}")
    print()
    print("  LOS 12 MÁS GRANDES (los que más cuestan de cortar):")
    for d in catalogo[:12]:
        print(f"    {d['archivo'][:38]:40} {d['metros_corte']:7.2f} m  "
              f"{d['minutos']:5.1f} min  ${d['precio_sugerido']:>7.0f}")
    return {"total": len(catalogo)}


def buscar(que: str) -> list:
    """Busca por nombre. Para cotizar frente al cliente sin abrir el archivo."""
    if not CATALOGO.exists():
        print("Todavía no hay catálogo. Corre: python TALLER/indexar_dxf.py")
        return []
    d = json.loads(CATALOGO.read_text(encoding="utf-8"))
    q = (que or "").lower()
    hallados = [x for x in d["disenos"] if q in x["archivo"].lower()]
    if not hallados:
        print(f"Ningún diseño con '{que}' entre los {d['total']} catalogados.")
        return []
    print(f"{len(hallados)} diseño(s) con '{que}':\n")
    for x in hallados[:15]:
        print(f"  {x['archivo']}")
        print(f"     {x['ancho_cm']} x {x['alto_cm']} cm · {x['metros_corte']} m de corte · "
              f"{x['minutos']} min")
        print(f"     costo de corte ${x['costo_corte']}  →  PRECIO ${x['precio_sugerido']:.0f}")
        print(f"     {x['ruta']}")
        print()
    return hallados


if __name__ == "__main__":
    if "--buscar" in sys.argv:
        i = sys.argv.index("--buscar")
        buscar(" ".join(sys.argv[i + 1:]))
    else:
        indexar()
