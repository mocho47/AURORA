# -*- coding: utf-8 -*-
"""AURORA · Adaptar un DXF a otro grosor de material

Anuar lo planteó el 2026-08-05: tiene diseños gratuitos hechos para un grosor y
quiere cortarlos en otro. El problema real no es escalar —eso es fácil— es que
al escalar, las RANURAS también crecen y ya no encajan con su material.

Y él mismo dio la clave: *"a no ser que por el tamaño en cada uno los pudieran
conocer"*. Exacto. Los diseños gratuitos no traen los ensambles separados por
capa ni por color, pero **la medida del grosor se repite decenas de veces** en
las ranuras. Esa repetición es la firma que los delata.

Comprobado con sus archivos reales:
    10x10x10.dxf   2.4 mm repetido 24 veces
    15x15.dxf      2.4 mm repetido 32 veces
(2.4 mm = MDF de 3 mm menos el kerf del láser.)

QUÉ SÍ HACE:
  • Detecta el grosor del diseño contando medidas repetidas
  • Ensancha o angosta las RANURAS RECTANGULARES sueltas al grosor nuevo,
    sin tocar el tamaño de la pieza
  • Deja el original intacto y guarda uno nuevo

QUÉ NO HACE, y lo dice:
  • Dientes que son parte del contorno (finger joints): avisa que quedaron sin
    tocar. Eso necesita mano.
  • Diseños de curvas (SPLINE) o imágenes vectorizadas: no hay ranuras que
    detectar y lo reporta.

REGLA DE ORO: la primera pieza se corta en RETAZO. Esto ajusta geometría, no
adivina cómo quedó el ensamble en la vida real.

Correr:
    python TALLER/adaptar_grosor.py "C:\\ruta\\caja.dxf" 5.5
    python TALLER/adaptar_grosor.py "C:\\ruta\\caja.dxf" --solo-revisar
"""
from __future__ import annotations
import collections
import io
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DESTINO = Path.home() / "Downloads" / "dxf"

# Un grosor de material está entre esto. Fuera de aquí es otra cosa.
MIN_GROSOR = 1.5
MAX_GROSOR = 25.0
# Cuántas veces debe repetirse una medida para creerle que es el grosor.
REPETICIONES_MINIMAS = 6


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _puntos(e) -> list:
    """Los vértices de una entidad, sea del tipo que sea.

    OJO: POLYLINE y LWPOLYLINE se leen distinto. Leer solo LWPOLYLINE dejaba
    fuera casi todos los archivos de Anuar (2026-08-05).
    """
    t = e.dxftype()
    try:
        if t == "LWPOLYLINE":
            return [(p[0], p[1]) for p in e.get_points()]
        if t == "POLYLINE":
            return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if t == "LINE":
            return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    except Exception:
        pass
    return []


def detectar_grosor(ruta: Path) -> dict:
    """Qué grosor de material usa este diseño, por repetición de medidas."""
    import ezdxf
    try:
        doc = ezdxf.readfile(str(ruta))
    except Exception as e:
        return {"status": "NO_SE_LEE", "detalle": f"{type(e).__name__}: {str(e)[:80]}"}

    msp = doc.modelspace()
    medidas = collections.Counter()
    tipos = collections.Counter()
    for e in msp:
        tipos[e.dxftype()] += 1
        pts = _puntos(e)
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            if MIN_GROSOR <= L <= MAX_GROSOR:
                medidas[round(L, 1)] += 1

    if not medidas:
        curvas = tipos.get("SPLINE", 0) + tipos.get("ARC", 0) + tipos.get("CIRCLE", 0)
        return {"status": "SIN_RANURAS", "tipos": dict(tipos),
                "detalle": ("No encontré medidas repetidas que parezcan ranuras. "
                            + ("Este diseño es de curvas (SPLINE), probablemente "
                               "una imagen vectorizada y no una pieza armable."
                               if curvas else
                               "Puede ser una pieza de una sola parte, sin ensambles."))}

    # El grosor es la medida CHICA que más se repite. Las medidas grandes
    # repetidas son los dientes, no el grosor.
    candidatos = [(L, n) for L, n in medidas.items()
                  if n >= REPETICIONES_MINIMAS and L <= 12.0]
    if not candidatos:
        return {"status": "DUDOSO", "medidas": medidas.most_common(6),
                "detalle": ("Ninguna medida se repite lo suficiente para "
                            "asegurar que es el grosor. Dímelo tú y lo adapto.")}

    candidatos.sort(key=lambda x: (-x[1], x[0]))
    grosor, veces = candidatos[0]
    return {"status": "OK", "grosor": grosor, "veces": veces,
            "tipos": dict(tipos), "otras": medidas.most_common(5)}


def _es_ranura(pts: list, grosor: float, tol: float = 0.35) -> tuple:
    """¿Este contorno cerrado es una ranura rectangular del grosor buscado?

    Devuelve (es_ranura, eje_corto) donde eje_corto es 'x' o 'y'.
    """
    if len(pts) < 4:
        return False, ""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    if ancho <= 0 or alto <= 0:
        return False, ""
    # Rectángulo: 4 o 5 puntos (el último repite el primero)
    if len(pts) > 6:
        return False, ""
    if abs(ancho - grosor) <= tol and alto > grosor:
        return True, "x"
    if abs(alto - grosor) <= tol and ancho > grosor:
        return True, "y"
    return False, ""


def _reemplazar(msp, e, nuevos: list) -> str:
    """Cambia una entidad por su versión ajustada, respetando la versión del DXF.

    Muchos diseños bajados de internet vienen en DXF R12, que NO soporta
    LWPOLYLINE. Escribirla ahí tira DXFVersionError — y con un `except` genérico
    eso se traga en silencio y parece que "no había dientes" (2026-08-05:
    28 dientes detectados y 0 escritos, sin un solo mensaje de error).

    Devuelve "" si salió bien, o el motivo si falló.
    """
    try:
        capa = e.dxf.layer
    except Exception:
        capa = "0"
    try:
        msp.delete_entity(e)
    except Exception as ex:
        return f"no se pudo quitar la vieja: {type(ex).__name__}"
    # Primero como venía; si el archivo es viejo, se usa POLYLINE.
    try:
        msp.add_lwpolyline(nuevos, close=True, dxfattribs={"layer": capa})
        return ""
    except Exception:
        pass
    try:
        p = msp.add_polyline2d(nuevos, dxfattribs={"layer": capa})
        p.close(True)
        return ""
    except Exception as ex:
        return f"{type(ex).__name__}: {str(ex)[:90]}"


def _limpiar(pts: list, minimo: float = 0.25) -> list:
    """Quita los puntos casi pegados que traen los diseños bajados de internet.

    El contorno de 15x15.dxf trae segmentos de 0.01 a 0.13 mm entre los buenos:
    esquinas redondeadas y basura del programa que lo exportó. Se colaban en
    medio del patrón del diente y lo rompían:
        19.90 H · 2.40 V · [0.13 basura] · 50.02 H · [0.13 basura] · 2.42 V
    Con 0.1 de umbral los 0.13 sobrevivían y no se reconocía ni un diente.

    0.25 mm es seguro: el kerf del propio láser ya es de 0.1 a 0.2 mm, así que
    quitar puntos a esa distancia no cambia nada que se pueda cortar.
    """
    if len(pts) < 2:
        return pts
    salida = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, salida[-1]) >= minimo:
            salida.append(p)
    return salida


def _adaptar_dientes(pts: list, viejo: float, nuevo: float, tol: float = 0.3) -> tuple:
    """Ajusta los dientes que van PEGADOS al contorno.

    Un diente es: sale perpendicular al borde una distancia = grosor, avanza a
    lo largo, y regresa. Para cambiarlo de grosor hay que mover la punta del
    diente hacia afuera (o adentro) la diferencia.

    Devuelve (puntos_nuevos, cuántos dientes se ajustaron).
    """
    q = _limpiar(pts)
    if len(q) < 5:
        return pts, 0
    delta = nuevo - viejo
    fuera = list(q)
    ajustados = 0
    i = 1
    while i < len(fuera) - 2:
        # Tres segmentos seguidos: sale, avanza, regresa.
        a, b, c, d = fuera[i - 1], fuera[i], fuera[i + 1], fuera[i + 2]
        sale = (b[0] - a[0], b[1] - a[1])
        avanza = (c[0] - b[0], c[1] - b[1])
        regresa = (d[0] - c[0], d[1] - c[1])
        l_sale = math.hypot(*sale)
        l_regresa = math.hypot(*regresa)
        l_avanza = math.hypot(*avanza)
        # Sale y regresa miden el grosor, en direcciones opuestas, y son
        # perpendiculares al avance.
        if (abs(l_sale - viejo) <= tol and abs(l_regresa - viejo) <= tol
                and l_avanza > 0.5
                and abs(sale[0] * avanza[0] + sale[1] * avanza[1]) < 0.2 * l_sale * l_avanza
                and (sale[0] * regresa[0] + sale[1] * regresa[1]) < 0):
            # La punta del diente son b y c: se mueven en la dirección de salida.
            ux, uy = sale[0] / l_sale, sale[1] / l_sale
            fuera[i] = (b[0] + ux * delta, b[1] + uy * delta)
            fuera[i + 1] = (c[0] + ux * delta, c[1] + uy * delta)
            ajustados += 1
            i += 3
            continue
        i += 1
    return fuera, ajustados


def adaptar(ruta: Path, grosor_nuevo: float, grosor_viejo: float = 0) -> dict:
    """Cambia las ranuras al grosor nuevo, SIN cambiar el tamaño de la pieza."""
    import ezdxf
    info = detectar_grosor(ruta)
    if info["status"] != "OK" and not grosor_viejo:
        return info
    viejo = grosor_viejo or info["grosor"]
    if abs(viejo - grosor_nuevo) < 0.05:
        return {"status": "IGUAL",
                "detalle": f"Ya está para {viejo} mm. No hay nada que cambiar."}

    doc = ezdxf.readfile(str(ruta))
    msp = doc.modelspace()
    delta = (grosor_nuevo - viejo) / 2.0    # se abre/cierra por los dos lados

    ajustadas, contornos, sin_tocar, dientes = 0, 0, 0, 0
    fallos = []
    for e in list(msp):
        pts = _puntos(e)
        if not pts:
            continue
        es, eje = _es_ranura(pts, viejo)
        if not es:
            # Contorno grande: puede traer los dientes PEGADOS al borde, que es
            # como arman la mayoría de los diseños bajados de internet. Esos sí
            # se ajustan, moviendo la punta de cada diente.
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if max(xs) - min(xs) > viejo * 4 or max(ys) - min(ys) > viejo * 4:
                contornos += 1
                nuevos, cuantos = _adaptar_dientes(pts, viejo, grosor_nuevo)
                if cuantos:
                    fallo = _reemplazar(msp, e, nuevos)
                    if fallo:
                        sin_tocar += 1
                        fallos.append(fallo)
                    else:
                        dientes += cuantos
            else:
                sin_tocar += 1
            continue

        i = 0 if eje == "x" else 1
        vals = [p[i] for p in pts]
        centro = (max(vals) + min(vals)) / 2.0
        nuevos = []
        for p in pts:
            v = list(p)
            v[i] = v[i] + (delta if v[i] > centro else -delta)
            nuevos.append(tuple(v))
        fallo = _reemplazar(msp, e, nuevos)
        if fallo:
            sin_tocar += 1
            fallos.append(fallo)
        else:
            ajustadas += 1

    # Si no se ajustó NADA, no se guarda un archivo que dice "5.5mm" y es
    # idéntico al original: eso es mentirle a quien lo va a cortar.
    # Encontrado el 2026-08-05 con 15x15.dxf, que arma con dientes en el
    # contorno y no con ranuras sueltas.
    if not ajustadas and not dientes:
        return {"status": "NO_HAY_RANURAS_SUELTAS",
                "grosor_viejo": viejo, "grosor_nuevo": grosor_nuevo,
                "contornos": contornos,
                "detalle": (
                    f"Detecté el grosor ({viejo} mm) pero este diseño NO arma "
                    f"con ranuras sueltas: sus {contornos} piezas llevan los "
                    "dientes pegados al contorno.\n\n"
                    "No guardé nada, porque un archivo que diga "
                    f"«{grosor_nuevo} mm» siendo idéntico al original te haría "
                    "cortar mal."
                    + ("\n\nMotivo técnico: " + fallos[0] if fallos else ""))}

    DESTINO.mkdir(parents=True, exist_ok=True)
    salida = DESTINO / f"{ruta.stem}__{grosor_nuevo:g}mm.dxf"
    n = 2
    while salida.exists():
        salida = DESTINO / f"{ruta.stem}__{grosor_nuevo:g}mm__{n}.dxf"
        n += 1
    doc.saveas(str(salida))

    return {"status": "OK", "archivo": str(salida),
            "grosor_viejo": viejo, "grosor_nuevo": grosor_nuevo,
            "ranuras_ajustadas": ajustadas, "dientes": dientes,
            "contornos": contornos,
            "sin_tocar": sin_tocar,
            "kb": round(salida.stat().st_size / 1024, 1)}


def _texto(r: dict, ruta: Path = None) -> str:
    s = r.get("status")
    if s == "NO_SE_LEE":
        return f"No pude leer el DXF (no lo invento): {r['detalle']}"
    if s == "SIN_RANURAS":
        return (f"🔍 {r['detalle']}\n\n"
                "Si de todas formas quieres cambiarle el tamaño, dime "
                "«escala <archivo> a X cm» — pero no hay ensambles que ajustar.")
    if s == "DUDOSO":
        m = " · ".join(f"{L}mm×{n}" for L, n in r["medidas"])
        return (f"🔍 No estoy seguro del grosor. Las medidas que más se repiten "
                f"son:\n   {m}\n\nDime cuál es el grosor real y lo adapto.")
    if s == "IGUAL":
        return r["detalle"]
    if "grosor" in r and "archivo" not in r:
        return (f"🔍 **{ruta.name if ruta else ''}**\n"
                f"   Grosor detectado: **{r['grosor']} mm** "
                f"(esa medida se repite {r['veces']} veces)\n"
                f"   Otras medidas: "
                + " · ".join(f"{L}mm×{n}" for L, n in r["otras"][:4]) + "\n\n"
                "Dime a qué grosor lo quieres y lo adapto.")
    if s == "NO_HAY_RANURAS_SUELTAS":
        return f"🔍 {r['detalle']}"
    aviso = ""
    if r.get("contornos") and not r.get("dientes"):
        aviso = (f"\n\n⚠️ Hay **{r['contornos']} contornos** cuyos dientes no "
                 "reconocí. Revísalos antes de cortar.")
    detalle = []
    if r.get("ranuras_ajustadas"):
        detalle.append(f"{r['ranuras_ajustadas']} ranuras")
    if r.get("dientes"):
        detalle.append(f"{r['dientes']} dientes del contorno")
    return (f"✅ Adaptado de **{r['grosor_viejo']} mm** a **{r['grosor_nuevo']} mm**\n"
            f"   {' y '.join(detalle) or 'nada'} · el tamaño NO cambió\n\n"
            f"📁 `{r['archivo']}`  ({r['kb']} KB)\n"
            f"_El original quedó intacto._{aviso}\n\n"
            "**Corta la primera en retazo.** Esto ajusta la geometría, no "
            "adivina cómo queda el ensamble en la vida real.")


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    ruta = Path(args[0])
    if not ruta.exists():
        print(f"No existe: {ruta}")
        return 1
    if "--solo-revisar" in sys.argv or len(args) < 2:
        print(_texto(detectar_grosor(ruta), ruta))
        return 0
    print(_texto(adaptar(ruta, float(args[1])), ruta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
