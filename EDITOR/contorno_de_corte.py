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

**Fondo de color plano** (2026-08-14, con el PDF de las K-pop): la imagen venía
recortada pero sobre un gris parejo 114,114,114 que ocupaba el 44% de la hoja.
Como "tinta" era todo lo más oscuro que 235, ese gris contaba como dibujo y el
contorno salió siendo el **rectángulo de la imagen**. Ahora se miran las
esquinas de cada imagen incrustada: si son un color plano, ese color es fondo
y no se corta por él.

**Pestañas** (lo pidió Anuar el mismo día): *"cortarlo y dejar unas pequeñas
pestañas para que no se suelten las piezas"*. La línea de corte se interrumpe
en unos tramitos repartidos por el contorno; la pieza queda sujeta a la hoja y
se desprende a mano al final.

Correr:
    python EDITOR/contorno_de_corte.py "C:\\ruta\\hoja.pdf" 1.5
    python EDITOR/contorno_de_corte.py "C:\\ruta\\hoja.pdf" 3 --pestanas 6 --escala 0.2
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
# Tope del lado mayor del raster, en píxeles. Sin esto, una hoja grande revienta
# la memoria: la de las K-pop mide 165 cm y a calidad 4 pedía un arreglo de
# 18720 × 16416 — 879 MB de un golpe, y ni siquiera aportaba nada, porque a ese
# tamaño cada píxel ya valía 0.09 mm. Con el tope queda en 0.33 mm por píxel,
# que es más fino de lo que cualquier máquina de corte alcanza a seguir.
MAX_PX = 5000


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


def _fondos_planos(doc, pag, img, ancho_px: int, alto_px: int) -> list:
    """Colores de fondo de las imágenes incrustadas (las 4 esquinas iguales).

    Una imagen ya recortada suele venir sobre un color parejo. Ese color NO es
    dibujo: si se corta por ahí sale el rectángulo de la imagen en vez de la
    silueta. Se pide que las 4 esquinas coincidan para no confundirse con un
    dibujo que de casualidad tenga una esquina oscura.
    """
    fondos = []
    try:
        incrustadas = pag.get_images(full=True)
    except Exception:
        return fondos
    esc_x = ancho_px / pag.rect.width
    esc_y = alto_px / pag.rect.height
    for it in incrustadas:
        try:
            rects = pag.get_image_rects(it[0])
        except Exception:
            continue
        for r in rects:
            x0 = max(0, int(r.x0 * esc_x)); x1 = min(ancho_px - 1, int(r.x1 * esc_x))
            y0 = max(0, int(r.y0 * esc_y)); y1 = min(alto_px - 1, int(r.y1 * esc_y))
            if x1 - x0 < 20 or y1 - y0 < 20:
                continue
            m = max(2, int(min(x1 - x0, y1 - y0) * 0.01))
            esq = [img[y0 + m, x0 + m], img[y0 + m, x1 - m],
                   img[y1 - m, x0 + m], img[y1 - m, x1 - m]]
            base = [int(v) for v in esq[0][:3]]
            if all(abs(int(c[k]) - base[k]) <= 12 for c in esq[1:] for k in range(3)):
                if not all(v > 235 for v in base):      # el blanco ya se ignora solo
                    fondos.append((it[0], base))
    return fondos


def _solo_imagenes(doc, pag, ancho_px: int, alto_px: int, xrefs: list):
    """Vuelve a armar la hoja usando SOLO los bitmaps, sin lo vectorial encima.

    En el PDF de las K-pop la figura venía como imagen y encima traía las
    líneas guía del cuadriculado, dibujadas como vectores. Al rasterizar la
    página esas guías eran tinta y salían pegadas al contorno como palos
    rectos. Reconstruyendo la hoja con puro bitmap desaparecen solas — y con
    ellas cualquier marca de registro o texto que el diseñador haya puesto.

    Se asume que la imagen no viene rotada en la página (lo normal).
    """
    import cv2
    import fitz
    import numpy as np
    lienzo = np.full((alto_px, ancho_px, 3), 255, dtype="uint8")
    esc_x = ancho_px / pag.rect.width
    esc_y = alto_px / pag.rect.height
    puestas = 0
    for xref in xrefs:
        pix = fitz.Pixmap(doc, xref)
        if pix.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        bm = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n)
        if pix.n == 1:
            bm = cv2.cvtColor(bm, cv2.COLOR_GRAY2RGB)
        for r in pag.get_image_rects(xref):
            x0 = max(0, int(r.x0 * esc_x)); x1 = min(ancho_px, int(r.x1 * esc_x))
            y0 = max(0, int(r.y0 * esc_y)); y1 = min(alto_px, int(r.y1 * esc_y))
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            lienzo[y0:y1, x0:x1] = cv2.resize(bm, (x1 - x0, y1 - y0),
                                              interpolation=cv2.INTER_AREA)
            puestas += 1
    return lienzo if puestas else None


def _con_pestanas(pts: list, cuantas: int, ancho_mm: float) -> list:
    """Parte un contorno cerrado en tramos, dejando `cuantas` pestañas sin cortar.

    Devuelve una lista de polilíneas ABIERTAS. Si las pestañas no caben en el
    perímetro se devuelve el contorno entero (mejor cerrado que picado).
    """
    if cuantas < 1 or ancho_mm <= 0 or len(pts) < 3:
        return [pts]
    cerrado = list(pts) + [pts[0]]
    largos, total = [], 0.0
    for a, b in zip(cerrado, cerrado[1:]):
        d = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        largos.append(d)
        total += d
    if total <= 0 or cuantas * ancho_mm >= total * 0.5:
        return [pts]

    paso = total / cuantas
    huecos = [(paso * i + paso / 2 - ancho_mm / 2,
               paso * i + paso / 2 + ancho_mm / 2) for i in range(cuantas)]

    def en_hueco(s: float) -> bool:
        return any(a <= s <= b for a, b in huecos)

    def punto(i: int, t: float):
        a, b = cerrado[i], cerrado[i + 1]
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    # Se recorre el contorno partiendo cada lado por donde caen los bordes de
    # las pestañas, y cada pedacito se queda o se salta según dónde está su
    # centro. Hacerlo por pedacitos y no por puntos sueltos es lo que evita
    # que un tramo se cierre antes de tiempo o se repita.
    tramos, actual = [], []
    s = 0.0
    for i, d in enumerate(largos):
        if d <= 0:
            continue
        cortes = sorted({c for a, b in huecos for c in (a, b) if s < c < s + d})
        marcas = [s] + cortes + [s + d]
        for ini, fin in zip(marcas, marcas[1:]):
            if fin - ini <= 1e-9:
                continue
            p_ini = punto(i, (ini - s) / d)
            p_fin = punto(i, (fin - s) / d)
            if en_hueco((ini + fin) / 2):          # este pedazo NO se corta
                if len(actual) > 1:
                    tramos.append(actual)
                actual = []
                continue
            if not actual:
                actual = [p_ini]
            elif actual[-1] != p_ini:
                actual.append(p_ini)
            actual.append(p_fin)
        s += d
    if len(actual) > 1:
        tramos.append(actual)
    # EL PUNTO DE ARRANQUE NO ES UNA PESTAÑA. El recorrido empieza y termina
    # en el mismo punto; si ahí no cae pestaña, el último tramo y el primero
    # son uno solo. Sin esto quedaba un boquete de 4 cm justo en la punta de
    # la estrella de las K-pop, y ahí la pieza se caía sola. Medido.
    if len(tramos) > 1 and not en_hueco(0.0):
        tramos[0] = tramos[-1][:-1] + tramos[0]
        tramos.pop()
    return tramos or [pts]


def generar(ruta: str, extra_mm: float = 1.5, margen_marcas_mm: float = 20.0,
            pestanas: int = 0, pestana_mm: float = 3.0,
            escala: float = 1.0, caber_en_mm=None) -> dict:
    """Saca el contorno de corte de cada pieza impresa, crecido `extra_mm`.

    `pestanas`    — cuántos tramitos se dejan SIN cortar para que no se suelte.
    `escala`      — 0.2 = sacar el contorno al 20% (prueba en hoja chica). El
                    `extra_mm` y la pestaña son milímetros del archivo FINAL.
    `caber_en_mm` — (ancho, alto) de la cama de la máquina. Manda sobre
                    `escala`: se calcula lo más grande que entra sin deformar.
    """
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

    calidad = min(CALIDAD, MAX_PX / max(pag.rect.width, pag.rect.height))
    pm = pag.get_pixmap(matrix=fitz.Matrix(calidad, calidad))
    img = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
    gris = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2GRAY)
    mm_px = 25.4 / 72 / calidad

    # LAS MARCAS DE IMPRENTA SE IGNORAN. En la hoja de Luisa había 8 cuadros y
    # 16 cruces de Corel pegados a las orillas; si se toman por dibujo, el
    # contorno abarcaría toda la hoja y no serviría de nada.
    borde = int(margen_marcas_mm / mm_px)
    gris[:borde, :] = 255
    gris[-borde:, :] = 255
    gris[:, :borde] = 255
    gris[:, -borde:] = 255

    # El fondo plano de una imagen recortada NO es dibujo (ver cabecera).
    fondos = _fondos_planos(doc, pag, img[:, :, :3], pm.width, pm.height)
    rgb = img[:, :, :3]
    if fondos:
        # Es una imagen ya recortada: la hoja se rearma con puro bitmap para
        # que las guías y marcas vectoriales no se peguen al contorno.
        limpio = _solo_imagenes(doc, pag, pm.width, pm.height,
                                [x for x, _ in fondos])
        if limpio is not None:
            rgb = limpio
            gris = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            gris[:borde, :] = 255
            gris[-borde:, :] = 255
            gris[:, :borde] = 255
            gris[:, -borde:] = 255

    tinta = gris < UMBRAL_TINTA
    for _, base in fondos:
        cerca = np.ones(gris.shape, dtype=bool)
        for k in range(3):
            cerca &= np.abs(rgb[:, :, k].astype("int16") - base[k]) <= 18
        tinta &= ~cerca
    tinta = tinta.astype("uint8") * 255
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

    # ¿QUE QUEPA EN LA MÁQUINA? Anuar lo pidió así el 2026-08-14: *"déjala
    # escalada a 120 de alto o que quepa en la cama del láser sin
    # deformarse"*. Se calcula aquí, con el dibujo ya medido, en vez de que
    # él saque el porcentaje a mano.
    escala = float(escala) if escala and escala > 0 else 1.0
    if caber_en_mm:
        cw, ch = float(caber_en_mm[0]), float(caber_en_mm[1])
        x0 = min(c[0] for c in cajas) * mm_px
        y0 = min(c[1] for c in cajas) * mm_px
        x1 = max(c[0] + c[2] for c in cajas) * mm_px
        y1 = max(c[1] + c[3] for c in cajas) * mm_px
        # El contorno crece `extra_mm` por lado: eso también tiene que caber.
        an = (x1 - x0) + extra_mm * 2
        al = (y1 - y0) + extra_mm * 2
        margen = 10.0                       # para no cortar pegado a la orilla
        if an > 0 and al > 0:
            escala = min(1.0, (cw - margen) / an, (ch - margen) / al)
    escala = float(escala) if escala and escala > 0 else 1.0
    extra_aqui = extra_mm / escala

    aviso = ""
    if hueco_min is not None and extra_aqui * 2 >= hueco_min - 0.3:
        cabe = round(max(0.3, (hueco_min - 0.6) / 2) * escala, 1)
        aviso = (f"El hueco más chico entre piezas es de {hueco_min:.1f} mm: "
                 f"con {extra_mm} mm por lado los cortes se tocan. "
                 f"El máximo que cabe aquí es {cabe} mm.")
        return {"status": "NO_CABE", "detalle": aviso,
                "hueco_min": round(hueco_min, 1), "maximo": cabe}

    # Crecer el contorno: se dilata la mancha y se vuelve a trazar. Es más
    # fiel a la forma real que empujar los puntos uno por uno.
    crecer = max(1, int(extra_aqui / mm_px)) | 1
    gordo = cv2.dilate(tinta, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                        (crecer * 2, crecer * 2)))
    cont2, _ = cv2.findContours(gordo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cont2 = [c for c in cont2 if cv2.contourArea(c) > minimo_area]

    dxf = ezdxf.new("R2010")
    dxf.layers.add("CORTE", color=1)
    msp = dxf.modelspace()
    puestas = 0
    for c in cont2:
        # Se simplifica: 0.2 mm de tolerancia quita los dientes del pixel sin
        # deformar la silueta.
        # 0.2 mm de tolerancia, pero nunca menos de un píxel: con hojas
        # grandes el píxel ya vale más que eso y pedir menos no simplifica
        # nada, solo deja los dientes del raster en el corte.
        suave = cv2.approxPolyDP(c, max(1.0, 0.2 / mm_px), True)
        pts = [(float(q[0][0]) * mm_px * escala,
                (hoja_h - float(q[0][1]) * mm_px) * escala) for q in suave]
        if len(pts) <= 2:
            continue
        if pestanas > 0:
            tramos = _con_pestanas(pts, int(pestanas), pestana_mm)
            if len(tramos) > 1:
                puestas += len(tramos)
            for t in tramos:
                msp.add_lwpolyline(t, close=False, dxfattribs={"layer": "CORTE"})
        else:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CORTE"})

    etiqueta = f"{p.stem}_CORTE_{extra_mm:g}mm"
    if pestanas > 0:
        etiqueta += f"_{int(pestanas)}pest"
    if escala != 1.0:
        etiqueta += f"_{escala * 100:g}pct"
    salida = _carpeta("dxf") / f"{etiqueta}.dxf"
    n = 2
    while salida.exists():
        salida = salida.parent / f"{etiqueta}__{n}.dxf"
        n += 1
    dxf.saveas(str(salida))

    r = {"status": "OK", "archivo": str(salida), "piezas": len(cont2),
         "extra_mm": extra_mm, "hoja": f"{hoja_w * escala:.1f} × {hoja_h * escala:.1f} mm",
         "hueco_min": round(hueco_min * escala, 1) if hueco_min else None,
         "kb": round(salida.stat().st_size / 1024, 1)}
    if fondos:
        r["fondo_quitado"] = ", ".join("RGB " + "/".join(str(v) for v in c)
                                       for _, c in fondos)
    if escala != 1.0:
        r["escala"] = escala
    if pestanas > 0:
        r["pestanas"] = int(pestanas)
        r["pestana_mm"] = pestana_mm
        r["tramos"] = puestas
        if puestas == 0:
            r["aviso_pestanas"] = ("El contorno es muy corto para esas "
                                   "pestañas: quedó cerrado, sin cortar.")
    return r


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
    if r.get("escala"):
        t += f" · al {r['escala'] * 100:g}%"
    if r.get("hueco_min"):
        t += f" · hueco entre piezas: {r['hueco_min']} mm"
    if r.get("fondo_quitado"):
        t += f"\n   fondo de color descartado ({r['fondo_quitado']})"
    if r.get("pestanas"):
        t += (f"\n   🔗 {r['pestanas']} pestañas de {r['pestana_mm']:g} mm "
              f"— {r['tramos']} tramos de corte")
    if r.get("aviso_pestanas"):
        t += f"\n   ⚠️ {r['aviso_pestanas']}"
    return (t + f"\n\n📁 `{r['archivo']}`  ({r['kb']} KB)\n\n"
            "**Corta la primera hoja con la que peor te haya salido.** Sin "
            "marcas de registro la máquina no corrige nada: lo que veas en "
            "esa, va a hacer en todas.")


def main() -> int:
    _consola_utf8()
    crudos = sys.argv[1:]
    args = [a for a in crudos if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1

    def _op(nombre: str, por_defecto):
        if f"--{nombre}" in crudos:
            i = crudos.index(f"--{nombre}")
            if i + 1 < len(crudos):
                return type(por_defecto)(crudos[i + 1])
        return por_defecto

    extra = float(args[1]) if len(args) > 1 else 1.5
    print(_texto(generar(args[0], extra,
                         pestanas=_op("pestanas", 0),
                         pestana_mm=_op("pestana_mm", 3.0),
                         escala=_op("escala", 1.0))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
