# -*- coding: utf-8 -*-
"""AURORA · El dibujo lineal de una imagen — para grabar o para estarcido

Anuar lo pidió el 2026-08-14 con el PDF de las K-pop: *"el dibujo lineal sin
color con líneas más anchas para usarlo como grabado o estencil"*.

Ojo con la diferencia, porque son dos trabajos distintos y se confunden:
- **Contorno de corte** (`EDITOR/contorno_de_corte.py`) = la silueta de AFUERA,
  por dónde pasa la máquina para recortar la pieza.
- **Dibujo lineal** (esto) = los trazos de ADENTRO — caras, pelo, ropa —
  convertidos a línea negra sobre blanco.

Tres salidas, según para qué:
- `modo="trazo"`   → PNG, puro contorno, como libro de colorear. Para grabar.
- `modo="silueta"` → PNG con las zonas oscuras rellenas de negro. Se graba más
  rápido y contrasta más, pero el pelo negro sale como manchón.
- `modo="cortar"`  → **DXF**, la línea convertida en banda para cortarla de
  verdad, con puentes para que no se caiga ni una pieza. Es el estarcido: se
  quita el material de la línea, se pone la plantilla encima y se traza.

**Los puentes no son un adorno.** Si la línea rodea por completo un pedazo
—el blanco de un ojo, el hueco de una letra— ese pedazo queda suelto y se cae
en cuanto pasa el láser. Se cruza una rejilla fina que interrumpe la línea
cada tantos milímetros: ahí el material sigue pegado. Después se cuenta cuántas
piezas sueltas quedaron, y si quedó alguna, se dice.

**La resolución no se inventa.** Si la imagen original es chica, ampliarla a
300 DPI no agrega detalle: agrega pixelón grande. Se amplía hasta 4 veces como
mucho y se reporta el DPI REAL que quedó, para que él decida antes de quemar
material.

Correr:
    python EDITOR/dibujo_lineal.py "C:\\ruta\\dibujo.pdf" --ancho_cm 92.7
    python EDITOR/dibujo_lineal.py "C:\\ruta\\foto.png" --grosor_mm 1.5 --modo silueta
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Cuánto se puede ampliar la imagen antes de que sea puro pixelón inventado.
MAX_AMPLIACION = 4.0
# Motas más chicas que esto (en milímetros cuadrados del resultado) se borran:
# son el brillito del glitter y la basura del JPEG, no dibujo.
MOTA_MIN_MM2 = 1.0


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _carpeta(ext: str) -> Path:
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location(
            "carpetas_por_tipo", RAIZ / "CONFIG" / "carpetas_por_tipo.py")
        cpt = _ilu.module_from_spec(spec)
        spec.loader.exec_module(cpt)
        return cpt.carpeta_de(ext)
    except Exception:
        d = Path.home() / "Downloads" / ext
        d.mkdir(parents=True, exist_ok=True)
        return d


def _imagen_de(ruta: Path):
    """El bitmap con el dibujo. De un PDF se saca la imagen incrustada.

    De un PDF NO se rasteriza la página: encima suele traer líneas guía y
    marcas de registro que no son dibujo y ensuciarían todo el trazo. Se toma
    el bitmap tal como venía.
    """
    import cv2
    import numpy as np
    if ruta.suffix.lower() != ".pdf":
        a = cv2.imread(str(ruta), cv2.IMREAD_COLOR)
        return (a, "archivo") if a is not None else (None, "")
    import fitz
    doc = fitz.open(str(ruta))
    mejor, area = None, 0
    for pag in doc:
        for it in pag.get_images(full=True):
            pix = fitz.Pixmap(doc, it[0])
            if pix.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            if pix.width * pix.height <= area:
                continue
            bm = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            if pix.n == 1:
                bm = cv2.cvtColor(bm, cv2.COLOR_GRAY2RGB)
            mejor = cv2.cvtColor(bm, cv2.COLOR_RGB2BGR)
            area = pix.width * pix.height
    if mejor is not None:
        return mejor, "imagen del PDF"
    # Sin imágenes: entonces el PDF sí es vectorial y se rasteriza.
    pag = doc[0]
    pm = pag.get_pixmap(matrix=fitz.Matrix(3, 3))
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
    return cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2BGR), "PDF vectorial"


def _quitar_fondo_plano(a):
    """Marca el fondo si las 4 esquinas son del mismo color. Devuelve máscara."""
    import numpy as np
    h, w = a.shape[:2]
    m = max(2, int(min(h, w) * 0.01))
    esq = [a[m, m], a[m, w - m - 1], a[h - m - 1, m], a[h - m - 1, w - m - 1]]
    base = [int(v) for v in esq[0][:3]]
    if not all(abs(int(c[k]) - base[k]) <= 12 for c in esq[1:] for k in range(3)):
        return None, None
    fondo = np.ones(a.shape[:2], dtype=bool)
    for k in range(3):
        fondo &= np.abs(a[:, :, k].astype("int16") - base[k]) <= 22
    return fondo, base


def _poner_puentes(linea, px_mm: float, puente_mm: float, cada_mm: float):
    """Interrumpe la línea con una rejilla para que nada quede suelto.

    Se borran franjas del ancho del puente cada tantos milímetros, en los dos
    sentidos. Donde se borra la línea, el material de adentro sigue unido al
    de afuera. Es lo mismo que hace cualquiera a mano en un estarcido, nada
    más que parejo y en todo el dibujo.
    """
    import numpy as np
    alto, ancho = linea.shape[:2]
    paso = max(2, int(round(cada_mm * px_mm)))
    grueso = max(1, int(round(puente_mm * px_mm)))
    rejilla = np.zeros_like(linea, dtype=bool)
    for y in range(paso // 2, alto, paso):
        rejilla[y:y + grueso, :] = True
    for x in range(paso // 2, ancho, paso):
        rejilla[:, x:x + grueso] = True
    salida = linea.copy()
    salida[rejilla] = 0
    return salida


def _puentes_dirigidos(linea, grosor_px: int, vueltas: int = 5):
    """Le abre un puente a CADA pieza que se cae, una por una.

    La rejilla es ciega: una isla más chica que el paso se le escapa entera,
    y con las K-pop quedaban 348 pedazos sueltos aunque los puentes fueran
    cada 10 mm. Esto es al revés — primero se busca qué se cae, y a eso se le
    pone el puente. Se repite porque al unir dos islas entre sí el par puede
    seguir suelto; se para cuando ya no queda nada o deja de mejorar.

    Devuelve (línea, puentes puestos, piezas que quedaron sueltas).
    """
    import cv2
    import numpy as np
    alto, ancho = linea.shape[:2]
    radio = max(2, grosor_px + 2)          # tiene que atravesar la banda
    disco = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radio * 2 + 1,) * 2)
    puestos, previas = 0, None
    for _ in range(max(1, vueltas)):
        material = (linea == 0).astype(np.uint8)
        n, et, stats, _c = cv2.connectedComponentsWithStats(material, 4)
        if n <= 1:
            break
        sujeta = set(np.unique(et[0, :])) | set(np.unique(et[-1, :]))
        sujeta |= set(np.unique(et[:, 0])) | set(np.unique(et[:, -1]))
        sujeta.discard(0)
        sueltas = [i for i in range(1, n) if i not in sujeta]
        if not sueltas or (previas is not None and len(sueltas) >= previas):
            return linea, puestos, len(sueltas)
        previas = len(sueltas)
        for i in sueltas:
            x, y, w, h = (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP],
                          stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
            m = radio + 2
            x0, y0 = max(0, x - m), max(0, y - m)
            x1, y1 = min(ancho, x + w + m), min(alto, y + h + m)
            sub_et = et[y0:y1, x0:x1]
            isla = (sub_et == i).astype(np.uint8)
            trozo = linea[y0:y1, x0:x1]
            # La línea pegada a la isla: por ahí se sale hacia el vecino.
            orilla = cv2.dilate(isla, np.ones((3, 3), np.uint8)) & (trozo > 0)
            if not orilla.any():
                continue
            # HACIA DÓNDE. Si el puente se abre hacia otra isla que también se
            # cae, el par sigue cayéndose: con anillos metidos uno dentro de
            # otro todos los puentes se iban para adentro y nada llegaba a la
            # orilla de la hoja. Se busca un vecino que YA esté sujeto.
            cerca = cv2.dilate(isla, disco) > 0
            objetivo = None
            for v in np.unique(sub_et[cerca]):
                if v and v != i and v in sujeta:
                    objetivo = v
                    break
            if objetivo is not None:
                puente = (cv2.dilate((sub_et == objetivo).astype(np.uint8), disco) > 0)
                candidatos = orilla & puente
                if candidatos.any():
                    orilla = candidatos
            ys, xs = np.nonzero(orilla)
            k = len(xs) // 2                      # a media orilla, no en la punta
            cv2.circle(trozo, (int(xs[k]), int(ys[k])), radio, 0, -1)
            puestos += 1
    material = (linea == 0).astype(np.uint8)
    n, et, _s, _c = cv2.connectedComponentsWithStats(material, 4)
    sujeta = set(np.unique(et[0, :])) | set(np.unique(et[-1, :]))
    sujeta |= set(np.unique(et[:, 0])) | set(np.unique(et[:, -1]))
    sujeta.discard(0)
    return linea, puestos, len([i for i in range(1, n) if i not in sujeta])


def _piezas_sueltas(linea):
    """Cuántos pedazos de material quedan sin tocar la orilla de la hoja.

    El material es todo lo que NO es línea. Si un pedazo no llega al borde,
    está rodeado de corte por todos lados y se cae. Contarlo es la única
    manera honesta de decir si el estarcido aguanta.
    """
    import cv2
    import numpy as np
    material = (linea == 0).astype(np.uint8)
    n, et = cv2.connectedComponents(material, 4)
    if n <= 1:
        return 0, 0
    borde = set(np.unique(et[0, :])) | set(np.unique(et[-1, :]))
    borde |= set(np.unique(et[:, 0])) | set(np.unique(et[:, -1]))
    borde.discard(0)
    sueltas = [i for i in range(1, n) if i not in borde]
    return len(sueltas), n - 1


def generar(ruta: str, ancho_cm: float = 0.0, grosor_mm: float = 1.0,
            modo: str = "trazo", detalle: int = 50,
            puente_mm: float = 1.5, cada_mm: float = 25.0,
            caber_en_mm=None) -> dict:
    """Saca el dibujo lineal.

    `ancho_cm` — a qué tamaño se va a usar (0 = el tamaño natural del bitmap).
    `grosor_mm` — qué tan ancha queda la línea A ESE TAMAÑO.
    `modo` — "trazo" / "silueta" (PNG) o "cortar" (DXF con puentes).
    `detalle` — 0 a 100. Más alto, más líneas finas atrapa (y más basura).
    `puente_mm` / `cada_mm` — solo en modo "cortar": qué tan anchas y cada
    cuánto van las uniones que sostienen las piezas.
    """
    p = Path(ruta)
    if not p.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {ruta}"}
    if modo not in ("trazo", "silueta", "cortar"):
        return {"status": "MODO_RARO",
                "detalle": "El modo es 'trazo', 'silueta' o 'cortar'."}
    try:
        import cv2
        import numpy as np
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    a, origen = _imagen_de(p)
    if a is None:
        return {"status": "SIN_IMAGEN",
                "detalle": "No pude leer ninguna imagen de ese archivo."}
    alto0, ancho0 = a.shape[:2]

    # ¿QUE QUEPA EN LA MÁQUINA? Igual que en el contorno de corte: él dice la
    # cama y el ancho sale solo, en vez de sacar el porcentaje a mano.
    if caber_en_mm:
        cw, ch = float(caber_en_mm[0]), float(caber_en_mm[1])
        margen = 10.0
        cabe = min((cw - margen), (ch - margen) * ancho0 / max(1, alto0))
        ancho_cm = cabe / 10.0

    # ¿Cuánto se amplía? Lo que se pueda sin inventar detalle.
    if ancho_cm > 0:
        px_por_mm_deseado = 300 / 25.4
        objetivo = ancho_cm * 10 * px_por_mm_deseado
        factor = min(MAX_AMPLIACION, max(1.0, objetivo / ancho0))
    else:
        factor = 1.0
    # EL FILTRO VA ANTES DE AMPLIAR. Aplanar el color en la imagen ampliada
    # tardaba minutos (20 megapíxeles) y no aportaba nada: el grano que hay
    # que quitar es el del JPEG original, y ahí está, en su tamaño. Hacerlo
    # antes deja el mismo resultado en segundos.
    fondo, color_fondo = _quitar_fondo_plano(a)
    if fondo is not None:
        a[fondo] = (255, 255, 255)
    a = cv2.bilateralFilter(a, 9, 90, 90)

    if factor > 1.001:
        a = cv2.resize(a, None, fx=factor, fy=factor,
                       interpolation=cv2.INTER_CUBIC)
        if fondo is not None:
            fondo = cv2.resize(fondo.astype("uint8"), (a.shape[1], a.shape[0]),
                               interpolation=cv2.INTER_NEAREST).astype(bool)
    alto, ancho = a.shape[:2]

    # px por mm del RESULTADO: con esto el grosor pedido sale en milímetros
    # de verdad y no en píxeles, que no le dicen nada a nadie en el taller.
    px_mm = (ancho / (ancho_cm * 10)) if ancho_cm > 0 else 300 / 25.4
    dpi_real = round(px_mm * 25.4)

    sua = a                        # ya viene aplanado, ver arriba
    gris = cv2.cvtColor(sua, cv2.COLOR_BGR2GRAY)

    if modo == "silueta":
        linea = ((gris < 100) & (~fondo if fondo is not None else True)
                 ).astype(np.uint8) * 255
    else:
        d = max(0, min(100, int(detalle)))
        bajo = int(20 + (100 - d) * 0.9)          # más detalle = umbral más bajo
        alto_u = bajo + 70
        bordes = cv2.Canny(sua, bajo, alto_u)
        # Las manchas muy oscuras (pelo negro, ropa negra) no traen bordes por
        # dentro: se les saca el borde con un gradiente para que la silueta de
        # la mancha quede dibujada en vez de rellenada.
        oscuro = cv2.morphologyEx((gris < 70).astype(np.uint8) * 255,
                                  cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        linea = cv2.bitwise_or(bordes, oscuro)
    if fondo is not None:
        linea[fondo] = 0

    # Fuera las motas: el glitter del fondo dejaba puntitos por toda la hoja.
    mota_px = max(4, int(MOTA_MIN_MM2 * px_mm * px_mm))
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(linea, 8)
    # DE UNA, NO UNA POR UNA. Recorrer los componentes y hacer
    # `linea[etiquetas == i] = 0` en cada vuelta recorre la imagen ENTERA por
    # cada mota: con 20 megapíxeles y miles de motas el proceso se quedaba
    # colgado horas. Con la tabla de áreas indexada es un solo barrido.
    chicas = np.zeros(n, dtype=bool)
    chicas[1:] = stats[1:, cv2.CC_STAT_AREA] < mota_px
    linea[chicas[etiquetas]] = 0
    borradas = int(chicas.sum())

    grosor_px = max(1, int(round(grosor_mm * px_mm)))
    if grosor_px > 1:
        linea = cv2.dilate(linea, cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (grosor_px, grosor_px)))

    if modo == "cortar":
        return _a_dxf(p, linea, px_mm, ancho, alto, grosor_mm, puente_mm,
                      cada_mm, origen, color_fondo, borradas, dpi_real,
                      ancho_cm, ancho0, alto0)

    # BLANCO Y NEGRO PURO, sin grises: es lo que pide el láser. Un gris de en
    # medio lo interpreta cada máquina como se le da la gana.
    salida_img = np.where(linea > 0, 0, 255).astype(np.uint8)

    etiqueta = f"{p.stem}_LINEAL_{modo}_{grosor_mm:g}mm"
    if ancho_cm > 0:
        etiqueta += f"_{ancho_cm:g}cm"
    destino = _carpeta("png") / f"{etiqueta}.png"
    k = 2
    while destino.exists():
        destino = destino.parent / f"{etiqueta}__{k}.png"
        k += 1
    cv2.imwrite(str(destino), salida_img)
    _sellar_dpi(destino, dpi_real)

    r = {"status": "OK", "archivo": str(destino), "modo": modo,
         "origen": origen, "px": f"{ancho} × {alto}",
         "dpi_real": dpi_real, "grosor_mm": grosor_mm,
         "grosor_px": grosor_px, "motas_borradas": borradas,
         "tinta_pct": round(float((linea > 0).mean()) * 100, 1),
         "kb": round(destino.stat().st_size / 1024, 1)}
    if ancho_cm > 0:
        r["mide_cm"] = f"{ancho_cm:.1f} × {ancho_cm * alto / ancho:.1f}"
    if color_fondo:
        r["fondo_quitado"] = "RGB " + "/".join(str(v) for v in reversed(color_fondo))
    if dpi_real < 150:
        r["aviso"] = (f"A ese tamaño quedan {dpi_real} DPI reales. El dibujo "
                      f"original mide {ancho0} × {alto0} píxeles y de ahí no "
                      f"sale más detalle: se va a notar el pixel en las curvas. "
                      f"Para grabado fino haría falta el archivo en vectores.")
    return r


def _a_dxf(p: Path, linea, px_mm: float, ancho: int, alto: int,
           grosor_mm: float, puente_mm: float, cada_mm: float, origen: str,
           color_fondo, borradas: int, dpi_real: int, ancho_cm: float,
           ancho0: int, alto0: int) -> dict:
    """La línea, ya con puentes, convertida en contornos cortables."""
    import cv2
    import ezdxf

    antes, _ = _piezas_sueltas(linea)
    if cada_mm > 0:
        linea = _poner_puentes(linea, px_mm, puente_mm, cada_mm)
    grosor_px_real = max(1, int(round(grosor_mm * px_mm)))
    linea, dirigidos, sueltas = _puentes_dirigidos(linea, grosor_px_real)

    # RETR_CCOMP: los huecos de adentro de cada banda también se cortan, si no
    # la máquina quitaría la línea entera rellena en vez de su contorno.
    contornos, _ = cv2.findContours(linea, cv2.RETR_CCOMP,
                                    cv2.CHAIN_APPROX_SIMPLE)
    mm = 1.0 / px_mm
    # Cuánto se puede desviar el contorno simplificado del original, en mm.
    # Subido de 0.15 a 0.30 el 2026-08-26 por una queja real de Anuar: *"los
    # dxf que los deje ligeros, lo más ligero posible, porque luego se traba
    # RDWorks pensando"*. La silueta de la piñata de Alicia pesaba 1 MB.
    # 0.30 mm sobre una pieza de 67 cm es un 0.045% — invisible a ojo y muy
    # por debajo del kerf de la láser (que ya se come 0.2 mm), pero recorta
    # a la mitad los puntos que RDWorks tiene que masticar.
    TOLERANCIA_MM = 0.30
    tol = max(1.0, TOLERANCIA_MM * px_mm)
    alto_mm = alto * mm

    dxf = ezdxf.new("R2010")
    dxf.layers.add("CORTE", color=1)
    msp = dxf.modelspace()
    largo_total, puestos = 0.0, 0
    for c in contornos:
        if cv2.contourArea(c) < (0.15 * px_mm) ** 2:
            continue
        suave = cv2.approxPolyDP(c, tol, True)
        pts = [(float(q[0][0]) * mm, alto_mm - float(q[0][1]) * mm)
               for q in suave]
        if len(pts) < 3:
            continue
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CORTE"})
        puestos += 1
        cerrado = pts + [pts[0]]
        largo_total += sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                           for a, b in zip(cerrado, cerrado[1:]))

    etiqueta = (f"{p.stem}_LINEAL_cortar_{grosor_mm:g}mm"
                + (f"_{ancho_cm:g}cm" if ancho_cm > 0 else ""))
    destino = _carpeta("dxf") / f"{etiqueta}.dxf"
    k = 2
    while destino.exists():
        destino = destino.parent / f"{etiqueta}__{k}.dxf"
        k += 1
    dxf.saveas(str(destino))

    # 20 mm/s es la velocidad real de su 1390 (CONFIG/maquinas.json). El
    # tiempo se dice SIEMPRE: un dibujo lineal completo puede ser media hora
    # de máquina, y eso decide si el trabajo conviene o no.
    minutos = largo_total / 20.0 / 60.0
    r = {"status": "OK", "archivo": str(destino), "modo": "cortar",
         "origen": origen, "px": f"{ancho} × {alto}", "dpi_real": dpi_real,
         "grosor_mm": grosor_mm, "contornos": puestos,
         "metros_de_corte": round(largo_total / 1000, 1),
         "minutos_corte": round(minutos, 1),
         "puente_mm": puente_mm, "cada_mm": cada_mm,
         "puentes_dirigidos": dirigidos,
         "sueltas_antes": antes, "sueltas": sueltas,
         "motas_borradas": borradas,
         "kb": round(destino.stat().st_size / 1024, 1)}
    if ancho_cm > 0:
        r["mide_cm"] = f"{ancho_cm:.1f} × {ancho_cm * alto / ancho:.1f}"
    if color_fondo:
        r["fondo_quitado"] = "RGB " + "/".join(str(v) for v in reversed(color_fondo))
    if sueltas:
        r["aviso"] = (f"Quedan {sueltas} pedazos que se sueltan al cortar. "
                      f"Son piezas tan chicas que el puente no cabe: bájale al "
                      f"detalle o engrosa la línea, y se pegan solas.")
    if dpi_real < 150:
        r["aviso_dpi"] = (f"{dpi_real} DPI reales: el dibujo original mide "
                          f"{ancho0} × {alto0} píxeles y de ahí no sale más "
                          f"detalle. Las curvas van a salir con escaloncito.")
    return r


def _sellar_dpi(archivo: Path, dpi: int) -> None:
    """Deja el DPI escrito en el PNG para que Corel lo abra al tamaño correcto."""
    try:
        from PIL import Image
        im = Image.open(archivo)
        im.save(archivo, dpi=(dpi, dpi))
    except Exception:
        pass                                  # sin Pillow el PNG sirve igual


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return f"No pude sacarlo: {r.get('detalle', r.get('status'))}"
    if r.get("modo") == "cortar":
        t = (f"✂️ **Dibujo lineal para CORTAR** — línea de {r['grosor_mm']:g} mm\n"
             f"   {r['contornos']} contornos · **{r['metros_de_corte']} m de "
             f"corte ≈ {r['minutos_corte']:g} min** a 20 mm/s")
        if r.get("mide_cm"):
            t += f"\n   mide {r['mide_cm']} cm"
        t += f"\n   🔗 {r['puentes_dirigidos']} puentes puestos pieza por pieza"
        if r.get("cada_mm"):
            t += f" + rejilla de {r['puente_mm']:g} mm cada {r['cada_mm']:g} mm"
        t += f"\n   piezas que se caían: {r['sueltas_antes']} ➜ **{r['sueltas']}**"
        if r.get("fondo_quitado"):
            t += f"\n   fondo de color descartado ({r['fondo_quitado']})"
        for k in ("aviso", "aviso_dpi"):
            if r.get(k):
                t += f"\n\n⚠️ {r[k]}"
        return t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)"
    t = (f"✏️ **Dibujo lineal** ({r['modo']}) — línea de {r['grosor_mm']:g} mm\n"
         f"   {r['px']} px · {r['dpi_real']} DPI reales")
    if r.get("mide_cm"):
        t += f" · para usarse a {r['mide_cm']} cm"
    t += f"\n   negro sobre blanco puro, {r['tinta_pct']}% de tinta"
    if r.get("motas_borradas"):
        t += f" · {r['motas_borradas']} motitas de basura quitadas"
    if r.get("fondo_quitado"):
        t += f"\n   fondo de color descartado ({r['fondo_quitado']})"
    if r.get("aviso"):
        t += f"\n\n⚠️ {r['aviso']}"
    return t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)"


def main() -> int:
    _consola_utf8()
    crudos = sys.argv[1:]
    args = [a for a in crudos if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1

    def _op(nombre, por_defecto):
        if f"--{nombre}" in crudos:
            i = crudos.index(f"--{nombre}")
            if i + 1 < len(crudos):
                return type(por_defecto)(crudos[i + 1])
        return por_defecto

    r = generar(args[0],
                ancho_cm=_op("ancho_cm", 0.0),
                grosor_mm=_op("grosor_mm", 1.0),
                modo=_op("modo", "trazo"),
                detalle=_op("detalle", 50),
                puente_mm=_op("puente_mm", 1.5),
                cada_mm=_op("cada_mm", 25.0))
    print(_texto(r))
    return 0 if r.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
