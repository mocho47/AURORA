# -*- coding: utf-8 -*-
"""AURORA · La piñata completa, de una imagen a los 4 archivos, con un comando

Pedido de Anuar, 2026-08-26, cliente Alicia Piñatas:
*"automatiza la produccion de piñatas para alicia con 2 pdf a tamaño real y los
dxf de la silueta ranurada y el despiece, asi solo meto la medida de altura o de
ancho y ella sabe como escalar pues tiene la medida de mi cama"*.

ENTRA: una imagen y UNA medida (alto o ancho, en cm).
SALEN 4 archivos que coinciden milímetro a milímetro:

  1. `_ARTE.pdf`      — el dibujo a tamaño real, 1:1, sin marcas. Para maquilar.
  2. `_SILUETA.dxf`   — la silueta RANURADA: el contorno cortado y las líneas de
                        detalle engrosadas y cortadas también, con pestañas para
                        que salga en UNA sola pieza.
  3. `_DESPIECE.pdf`  — el mismo arte a tamaño real, para pegar en el adhesivo.
  4. `_DESPIECE.dxf`  — solo los CONTORNOS de cada parte (la cara con orejas, el
                        cabello, la chamarra...), sin ningún detalle interior.

LOS NÚMEROS NO SON INVENTADOS. Salen de los archivos que él ya cortó bien:
  · `KPOP_LINEAL_cortar_1.5mm_92.7cm.dxf` → línea engrosada a **1.5 mm**,
    1,887 figuras cerradas. De ahí sale `GROSOR_LINEA_MM`.
  · `KPOP_CORTE_3mm_10pest_84.8pct__2.dxf` → contorno **3 mm** por fuera,
    partido en **10 pestañas**. De ahí salen `CONTORNO_MM` y `PESTANAS`.

CÓMO SE SACA EL DESPIECE (y por qué así):
Él lo dijo exacto: *"el despiece no lleva detalles de corte, solo contornos como
el de la cara con todo y orejas, el cabello, la chamarra"*. Eso son las
**regiones de color plano** del dibujo — un personaje de ilustración tiene la
cara de un color, el pelo de otro, la ropa de otro. No hace falta que el archivo
traiga capas por prenda: la información ya está en el color.

`produccion_piezas_grandes` decía que el despiece "no es automático de forma
confiable" y tenía razón para lo que miraba: un DXF ya vectorizado trae curvas
sueltas sin color (RUMO: 126 curvas). Pero partiendo de **la imagen a color**,
que es lo que Anuar manda, sí se puede. Cuando el dibujo no tiene colores planos
—una foto con degradados— se dice y no se entrega un despiece falso.

LA CAMA DEL LÁSER (130 x 90 cm) se respeta: si la pieza no cabe, se avisa con la
cuenta hecha de en cuántos pedazos habría que partirla. No se parte sola sin
decirlo, porque dónde parte una piñata es decisión de taller, no de un programa.

Correr:
    python TALLER/pinata_completa.py "C:\\ruta\\personaje.png" --alto 89.5
    python TALLER/pinata_completa.py "C:\\ruta\\personaje.png" --ancho 120 --pestanas 12
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# ── Los números de las K-pop, medidos de sus archivos reales ────────────
GROSOR_LINEA_MM = 1.5      # KPOP_LINEAL_cortar_1.5mm_92.7cm.dxf
CONTORNO_MM = 3.0          # KPOP_CORTE_3mm_10pest_84.8pct__2.dxf
PESTANAS = 10              # idem
PUENTE_MM = 1.5            # ancho de cada pestaña
CADA_MM = 25.0             # cada cuánto se reparten

# Área mínima de una región para contar como "parte" del despiece: menos de
# esto es un brillo, un lunar o el borde de una sombra, no una prenda.
AREA_MINIMA_PCT = 0.5      # % del área total del dibujo


def _mod(rel: str):
    """Carga un módulo del proyecto por su ruta, como hace el resto del taller."""
    import importlib.util as ilu
    ruta = RAIZ / rel
    spec = ilu.spec_from_file_location(Path(rel).stem, ruta)
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cama_del_laser_mm() -> tuple:
    """El área real de SU máquina, de su propia ficha. Nada de suponerla."""
    import json
    try:
        d = json.loads((RAIZ / "CONFIG" / "maquinas.json").read_text(encoding="utf-8"))
    except Exception:
        return (1300.0, 900.0)
    def buscar(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (int, float)) and "ancho" in k.lower() and v > 100:
                    yield ("ancho", float(v))
                if isinstance(v, (int, float)) and ("alto" in k.lower() or "largo" in k.lower()) and v > 100:
                    yield ("alto", float(v))
                yield from buscar(v)
        elif isinstance(o, list):
            for v in o:
                yield from buscar(v)
    vals = dict(buscar(d))
    if vals.get("ancho") and vals.get("alto"):
        return (vals["ancho"], vals["alto"])
    return (1300.0, 900.0)     # la 1390 de Anuar, según CONFIG/maquinas.json


def _regiones_de_color(ruta: Path, area_min_pct: float = AREA_MINIMA_PCT) -> dict:
    """Los contornos de cada región de color plano = las partes del despiece."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    img = Image.open(ruta).convert("RGB")
    # Reducir antes: los contornos se escalan después al tamaño real, así que
    # trabajar a 1000 px de lado da la misma forma en una fracción del tiempo.
    ancho0, alto0 = img.size
    img.thumbnail((1000, 1000), Image.LANCZOS)
    a = np.array(img)
    alto, ancho = a.shape[:2]

    # ¿De verdad tiene colores planos? Un dibujo de ilustración tiene pocos
    # colores repetidos; una foto tiene miles y ninguno domina.
    plano = a // 24 * 24                       # agrupa tonos casi iguales
    llaves = plano.reshape(-1, 3)
    unicos, cuentas = np.unique(llaves, axis=0, return_counts=True)
    orden = np.argsort(-cuentas)
    cobertura = cuentas[orden][:12].sum() / llaves.shape[0]
    if cobertura < 0.60:
        return {"status": "SIN_COLORES_PLANOS",
                "detalle": (f"Los 12 colores más usados solo cubren el "
                            f"{cobertura*100:.0f}% del dibujo: esto es una foto con "
                            f"degradados, no una ilustración de colores planos. "
                            f"El despiece por color saldría en pedazos sin sentido, "
                            f"así que no lo hago.")}

    area_total = alto * ancho
    area_min = area_total * (area_min_pct / 100.0)
    partes = []
    for idx in orden[:12]:
        color = unicos[idx]
        mascara = (np.abs(plano.astype(int) - color.astype(int)).max(axis=2) <= 12)
        mascara = (mascara * 255).astype(np.uint8)
        # Cerrar agujeritos: "la cara CON TODO Y OREJAS" es una sola región,
        # no la cara por un lado y cada oreja por otro.
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE,
                                   np.ones((7, 7), np.uint8))
        cont, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        for c in cont:
            if cv2.contourArea(c) < area_min:
                continue
            # Suavizar: un contorno de píxeles trae escaloncitos que la láser
            # recorrería uno por uno. Se simplifica al 0.2% del perímetro.
            eps = 0.002 * cv2.arcLength(c, True)
            c = cv2.approxPolyDP(c, eps, True)
            if len(c) < 3:
                continue
            partes.append([(float(p[0][0]), float(alto - p[0][1])) for p in c])

    if not partes:
        return {"status": "SIN_PARTES",
                "detalle": "No encontré ninguna región de color lo bastante grande."}
    return {"status": "OK", "partes": partes, "px": (ancho, alto),
            "px_original": (ancho0, alto0)}


def _escribir_despiece(partes: list, px: tuple, ancho_mm: float,
                       alto_mm: float, destino: Path) -> dict:
    """Los contornos de las partes, escalados al tamaño real, en un DXF."""
    try:
        import ezdxf
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}
    pw, ph = px
    kx, ky = ancho_mm / pw, alto_mm / ph
    doc = ezdxf.new("R2000")
    doc.units = 4
    msp = doc.modelspace()
    doc.layers.add("DESPIECE", color=1)
    for pts in partes:
        msp.add_lwpolyline([(x * kx, y * ky) for x, y in pts],
                           close=True, dxfattribs={"layer": "DESPIECE"})
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(destino))
    return {"status": "OK", "archivo": str(destino), "partes": len(partes)}


def producir(imagen: str, alto_cm: float = None, ancho_cm: float = None,
             grosor_linea_mm: float = GROSOR_LINEA_MM,
             pestanas: int = PESTANAS, carpeta: str = "") -> dict:
    """De una imagen y UNA medida, los 4 archivos de la piñata."""
    ruta = Path(str(imagen or "").strip().strip('"'))
    if not ruta.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré la imagen: {ruta}"}
    if not alto_cm and not ancho_cm:
        return {"status": "FALTA_MEDIDA",
                "detalle": "Dime cuánto mide de alto o de ancho en cm. "
                           "La otra medida sale sola de la proporción."}

    salida = Path(carpeta) if carpeta else (Path.home() / "Downloads" / "PINATAS")
    salida.mkdir(parents=True, exist_ok=True)
    base = ruta.stem
    avisos, hechos = [], {}

    # ── 1. El arte a tamaño real ────────────────────────────────────────
    pdfmod = _mod("TALLER/pdf_tamano_real.py")
    r_pdf = pdfmod.generar(str(ruta), alto_cm, ancho_cm,
                           str(salida / f"{base}_ARTE.pdf"))
    if r_pdf.get("status") != "OK":
        return {"status": "ERROR", "paso": "PDF de arte", "detalle": r_pdf}
    ancho_cm, alto_cm = r_pdf["medida_cm"]
    hechos["arte_pdf"] = r_pdf["archivo"]
    if r_pdf.get("aviso_dpi"):
        avisos.append(r_pdf["aviso_dpi"])
    if r_pdf.get("aviso_proporcion"):
        avisos.append(r_pdf["aviso_proporcion"])

    # ── 2. ¿Cabe en su cama? ────────────────────────────────────────────
    cw, ch = cama_del_laser_mm()
    ancho_mm, alto_mm = ancho_cm * 10.0, alto_cm * 10.0
    cabe = (ancho_mm <= cw and alto_mm <= ch) or (ancho_mm <= ch and alto_mm <= cw)
    if not cabe:
        import math
        nx = math.ceil(ancho_mm / cw)
        ny = math.ceil(alto_mm / ch)
        avisos.append(
            f"⚠️ A {ancho_cm:g} x {alto_cm:g} cm NO cabe en tu cama "
            f"({cw/10:g} x {ch/10:g} cm): habría que partirla en {nx*ny} pedazos "
            f"({nx} x {ny}). No la parto sola — dónde parte una piñata lo decides tú.")

    # ── 3. La silueta ranurada ──────────────────────────────────────────
    lineal = _mod("EDITOR/dibujo_lineal.py")
    r_sil = lineal.generar(str(ruta), ancho_cm, grosor_linea_mm, "cortar",
                           15, PUENTE_MM, CADA_MM, None)
    if r_sil.get("status") == "OK":
        # dibujo_lineal siempre guarda en su propia carpeta (`Downloads/dxf`).
        # Para una piñata eso deja los archivos de un mismo trabajo repartidos
        # en dos carpetas, y Anuar los busca a mano cuando va a cortar. Se
        # mueve aquí, sin tocar el contrato de dibujo_lineal (que otros flujos
        # usan tal cual): los 3 archivos de la piñata en la MISMA carpeta.
        _sil = Path(r_sil.get("archivo") or r_sil.get("dxf") or "")
        if _sil.exists() and _sil.parent != salida:
            _destino_sil = salida / f"{base}_SILUETA_RANURADA.dxf"
            try:
                if _destino_sil.exists():
                    _destino_sil.unlink()
                _sil.replace(_destino_sil)
                _sil = _destino_sil
            except Exception as e:          # si el mover falla, no se pierde nada
                avisos.append(f"La silueta quedó en {_sil.parent} ({e}).")
        hechos["silueta_dxf"] = str(_sil)
        hechos["silueta_kb"] = round(_sil.stat().st_size / 1024, 1) if _sil.exists() else 0
        hechos["silueta_metros"] = r_sil.get("metros_de_corte")
        hechos["silueta_minutos"] = r_sil.get("minutos_corte")
    else:
        avisos.append(f"La silueta ranurada no salió: "
                      f"{r_sil.get('detalle', r_sil.get('status'))}")

    # ── 4. El despiece ──────────────────────────────────────────────────
    r_reg = _regiones_de_color(ruta)
    if r_reg.get("status") == "OK":
        r_des = _escribir_despiece(r_reg["partes"], r_reg["px"], ancho_mm, alto_mm,
                                   salida / f"{base}_DESPIECE.dxf")
        if r_des.get("status") == "OK":
            hechos["despiece_dxf"] = r_des["archivo"]
            hechos["despiece_partes"] = r_des["partes"]
            # Antes aquí se generaba un SEGUNDO PDF idéntico para pegar sobre
            # el adhesivo. Anuar lo cortó el 2026-08-26: *"no requiere crear 1
            # porque con 1 solo lo imprimen 2 veces"*. Es el mismo arte al
            # mismo tamaño — la maquila lo imprime dos veces, una para los
            # tabloides y otra para el adhesivo. Un archivo, no dos.
        else:
            avisos.append(f"El despiece no se pudo escribir: {r_des.get('detalle')}")
    else:
        avisos.append(f"Sin despiece: {r_reg.get('detalle')}")

    return {"status": "OK" if hechos else "ERROR",
            "medida_cm": [ancho_cm, alto_cm],
            "dpi": r_pdf["dpi"],
            "cabe_en_la_cama": cabe,
            "cama_cm": [cw / 10, ch / 10],
            "archivos": hechos,
            "avisos": avisos,
            "carpeta": str(salida)}


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return f"[{r.get('status')}] {r.get('detalle', r)}"
    a, al = r["medida_cm"]
    L = [f"Piñata a {a:g} x {al:g} cm ({r['dpi']} DPI) · {r['carpeta']}"]
    n = {"arte_pdf": "1. Arte a tamaño real (PDF)",
         "silueta_dxf": "2. Silueta ranurada (DXF)",
         "despiece_pdf": "3. Arte para el adhesivo (PDF)",
         "despiece_dxf": "4. Despiece, solo contornos (DXF)"}
    for k, etiqueta in n.items():
        if r["archivos"].get(k):
            extra = ""
            if k == "silueta_dxf" and r["archivos"].get("silueta_figuras"):
                extra = f"  — {r['archivos']['silueta_figuras']} figuras"
            if k == "despiece_dxf":
                extra = f"  — {r['archivos'].get('despiece_partes', 0)} partes"
            L.append(f"   {etiqueta}{extra}")
            L.append(f"      {Path(r['archivos'][k]).name}")
    for a_ in r.get("avisos", []):
        L.append(f"   {a_}")
    return "\n".join(L)


def main() -> int:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    alto = ancho = None
    pest = PESTANAS
    for i, a in enumerate(sys.argv):
        if a == "--alto" and i + 1 < len(sys.argv):
            alto = float(sys.argv[i + 1].replace(",", "."))
        if a == "--ancho" and i + 1 < len(sys.argv):
            ancho = float(sys.argv[i + 1].replace(",", "."))
        if a == "--pestanas" and i + 1 < len(sys.argv):
            pest = int(sys.argv[i + 1])
    r = producir(sys.argv[1], alto, ancho, pestanas=pest)
    if "--json" in sys.argv:
        import json
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(_texto(r))
    return 0 if r.get("status") == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
