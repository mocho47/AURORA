# -*- coding: utf-8 -*-
"""AURORA · De una foto a DXF, en un solo paso

Anuar lo pidió el 2026-08-05 después de probarlo en el chat. Su flujo real es
siempre el mismo —foto → sin fondo → vectorizar → DXF— y AURORA lo obligaba a
pedirlo en tres mensajes distintos, repitiendo la ruta cada vez. Peor: en el
segundo mensaje ya se le había olvidado cuál era el archivo.

Y el camino que usaba (Inkscape) se pasó de 180 segundos y se rindió. Aquí se
usa vtracer + svgpathtools, que hacen lo mismo en segundos.

La cadena:
    1. rembg      quita el fondo de verdad (IA)
    2. blanco y negro puro   el láser no entiende grises
    3. vtracer    traza el contorno a SVG
    4. svgpathtools → ezdxf  pasa el SVG a DXF sin abrir Inkscape

Cada paso dice si funcionó. Si uno falla, se dice CUÁL — no un "no se pudo"
genérico.

Correr:  python EDITOR/imagen_a_dxf.py "C:\\ruta\\foto.jpg"
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Cada tipo a su carpeta (regla de Anuar, 2026-08-05): el DXF a Descargas\dxf
# y el SVG intermedio a Descargas\svg. Antes los dos caían en dxf.
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


DESTINO = _carpeta("dxf")
DESTINO_SVG = _carpeta("svg")

# Cuántos puntos por curva al pasar de SVG a DXF. Más = más fiel y más pesado.
PUNTOS_POR_CURVA = 24


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Cuanto se permite que un punto se aparte de la linea antes de conservarlo.
# En pixeles del SVG (que salen de la imagen reducida a 1000 px de lado): a
# 0.35 px la diferencia es invisible incluso ampliando la pieza a 90 cm, y el
# archivo baja varias veces de tamano.
TOLERANCIA_PX = 0.35


def _adelgazar(pts: list, tol: float) -> list:
    """Douglas-Peucker sin librerias: conserva la forma, tira los puntos de mas.

    Iterativo a proposito: una polilinea de un dibujo lineal puede traer miles
    de puntos y la version recursiva revienta la pila de Python.
    """
    if len(pts) < 3 or tol <= 0:
        return pts
    guardar = [False] * len(pts)
    guardar[0] = guardar[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        ini, fin = pila.pop()
        if fin <= ini + 1:
            continue
        x1, y1 = pts[ini]
        x2, y2 = pts[fin]
        dx, dy = x2 - x1, y2 - y1
        norma = (dx * dx + dy * dy) ** 0.5
        peor, idx = 0.0, -1
        for i in range(ini + 1, fin):
            x0, y0 = pts[i]
            if norma < 1e-12:
                d = ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5
            else:
                d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / norma
            if d > peor:
                peor, idx = d, i
        if peor > tol and idx > 0:
            guardar[idx] = True
            pila.append((ini, idx))
            pila.append((idx, fin))
    return [p for p, g in zip(pts, guardar) if g]


def svg_a_dxf(svg: Path, salida: Path) -> dict:
    """SVG → DXF sin Inkscape.

    Inkscape tarda minutos y se rinde (180 s con la foto de Anuar el
    2026-08-05). Esto lee las curvas del SVG y las escribe como polilíneas.
    """
    try:
        from svgpathtools import svg2paths
        import ezdxf
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}

    try:
        paths, _atrib = svg2paths(str(svg))
    except Exception as e:
        return {"status": "ERROR", "detalle": f"no pude leer el SVG: {type(e).__name__}"}

    doc = ezdxf.new("R2000")
    doc.units = 4                      # milímetros
    msp = doc.modelspace()

    # DOS CAPAS, y esta es la parte que importa. Anuar lo dijo el 2026-08-05:
    # "es un trailer, si cortara todo quedaría hecho pedazos". Al vectorizar
    # una foto salen TODOS los contornos: la silueta de afuera y cada detalle
    # de adentro. Cortarlos todos destruye la pieza.
    #   CORTE   = el contorno de afuera (la silueta)
    #   GRABADO = todo el detalle de adentro (el dibujo lineal)
    # Así RDWorks los trata distinto y él decide qué hacer con cada uno.
    doc.layers.add("CORTE", color=1)      # rojo
    doc.layers.add("GRABADO", color=5)    # azul

    trazados = []
    for p in paths:
        pts = []
        for seg in p:
            # Las rectas solo necesitan sus dos puntos; las curvas se parten.
            n = 1 if seg.__class__.__name__ == "Line" else PUNTOS_POR_CURVA
            for i in range(n + 1):
                z = seg.point(i / n)
                # El eje Y del SVG va al revés que el del DXF.
                pts.append((z.real, -z.imag))
        limpio = [pts[0]] if pts else []
        for q in pts[1:]:
            if abs(q[0] - limpio[-1][0]) > 1e-6 or abs(q[1] - limpio[-1][1]) > 1e-6:
                limpio.append(q)
        # ALIGERAR: se quitan los puntos que no cambian la forma.
        # Anuar, 2026-08-26: *"los dxf que los deje ligeros, lo mas ligero
        # posible, por que luego se traba RDWorks pensando"*. Y tiene razon:
        # el DXF de su escudo pesaba 1.59 MB porque cada curva se partia en 24
        # puntos, sin mirar si la curva era grande o un rizo de 2 mm. Un punto
        # que cae sobre la linea que unen sus vecinos no aporta nada a la
        # maquina y si la hace pensar. Se quitan con Douglas-Peucker, que es
        # exactamente eso: conservar la forma, tirar lo que sobra.
        limpio = _adelgazar(limpio, TOLERANCIA_PX)
        if len(limpio) >= 2:
            xs = [a[0] for a in limpio]
            ys = [a[1] for a in limpio]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            # El dibujo lineal deja MUCHOS trazos abiertos, y svgpathtools
            # revienta al preguntarles si están cerrados (AssertionError,
            # 2026-08-05). Se decide por la geometría: si el último punto cae
            # sobre el primero, está cerrado.
            try:
                cerrado = p.isclosed()
            except Exception:
                cerrado = (abs(limpio[0][0] - limpio[-1][0]) < 0.01
                           and abs(limpio[0][1] - limpio[-1][1]) < 0.01)
            trazados.append((area, limpio, cerrado))

    if not trazados:
        return {"status": "VACIO",
                "detalle": "El SVG no traía ningún trazo que convertir."}

    # El contorno más grande es la silueta: ese va a CORTE, el resto a GRABADO.
    trazados.sort(key=lambda x: -x[0])
    for i, (_a, pts, cerrado) in enumerate(trazados):
        capa = "CORTE" if i == 0 else "GRABADO"
        msp.add_lwpolyline(pts, close=cerrado, dxfattribs={"layer": capa})

    salida.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(salida))
    return {"status": "OK", "trazos": len(trazados), "archivo": str(salida),
            "corte": 1, "grabado": len(trazados) - 1}


def _ya_tiene_fondo_quitado(ruta: Path) -> bool:
    """¿El PNG YA trae transparencia real (alpha 0-255), o es un flat RGB/JPG?

    Encontrado el 2026-08-22 con el sticker de Alicia: rembg tardó más de 10
    minutos (CPU real, no colgado — se midió el CPU time subiendo) sobre una
    imagen que YA era un recorte con fondo transparente de verdad. Correrle
    IA de segmentación a algo que ya está aislado es puro tiempo perdido, y
    con cliente esperando en el chat 10 minutos no es "listo", es inservible.
    """
    try:
        from PIL import Image
        img = Image.open(ruta)
        if img.mode not in ("RGBA", "LA"):
            return False
        alpha = img.split()[-1]
        lo, hi = alpha.getextrema()
        return lo < 10 and hi > 245        # de verdad hay zonas transparentes Y opacas
    except Exception:
        return False


def _fondo_ya_plano(ruta: Path) -> bool:
    """¿La imagen ya viene sobre un fondo parejo, sin nada que recortar?

    Medido el 2026-08-26 con el escudo de Peugeot: la cadena completa tardaba
    66 s y **48 de esos eran rembg** — la IA que separa el sujeto del fondo,
    corriendo sobre una imagen que ya era un logo negro sobre blanco liso. No
    tenia nada que separar: gastaba 48 s para devolver la misma imagen.

    `_ya_es_dibujo_lineal` no lo cachaba porque ese escudo es medio negro
    (pide menos del 25% oscuro) — mide otra cosa: si es un dibujo de lineas.
    Aqui se mira lo unico que importa para esta decision: **la orilla**. Si
    todo el marco de la imagen es un mismo color parejo, no hay fondo que
    quitar; lo que haya adentro ya esta recortado.

    Se mira solo el borde: son unos miles de pixeles, cuesta milisegundos.
    """
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(ruta).convert("RGB")
        a = np.array(img)
        if a.shape[0] < 8 or a.shape[1] < 8:
            return False
        g = max(2, min(a.shape[0], a.shape[1]) // 100)      # grosor del marco
        orilla = np.concatenate([
            a[:g, :, :].reshape(-1, 3), a[-g:, :, :].reshape(-1, 3),
            a[:, :g, :].reshape(-1, 3), a[:, -g:, :].reshape(-1, 3)])
        # El color mas repetido de la orilla, y que tan parejo es todo lo demas.
        color = np.median(orilla, axis=0)
        cerca = (np.abs(orilla.astype(int) - color).max(axis=1) <= 12).mean()
        # 0.85 y no 0.97: el escudo de Peugeot llega hasta la orilla, así que
        # el 10% del marco es dibujo y aun así el fondo es blanco liso.
        if cerca < 0.85:
            return False
        # Segunda comprobación, para no confundir una FOTO con fondo parejo
        # (una pieza sobre la mesa) con un dibujo ya recortado: una ilustración
        # tiene pocos colores planos repetidos; una foto tiene miles y ninguno
        # domina. Si los 12 colores más usados no cubren ni el 60%, es foto y
        # sí hay que recortarla con rembg.
        chica = img.copy()
        chica.thumbnail((300, 300))
        b = (np.array(chica) // 24 * 24).reshape(-1, 3)
        _u, c = np.unique(b, axis=0, return_counts=True)
        return bool(np.sort(c)[::-1][:12].sum() / b.shape[0] >= 0.60)
    except Exception:
        return False


def _ya_es_dibujo_lineal(ruta: Path) -> bool:
    """¿La imagen YA es un dibujo de líneas, o es una foto?

    Anuar mandó un blueprint de un Volvo el 2026-08-05: líneas negras sobre
    blanco. A eso NO hay que quitarle el fondo (no hay fondo que quitar) NI
    detectarle bordes — detectar bordes sobre una línea que ya existe genera
    DOS líneas, una por cada lado del trazo. Solo hay que trazar lo negro.

    Se reconoce porque casi todo es blanco y lo poco oscuro son trazos finos.
    """
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(ruta).convert("L")
        # Se mide en la imagen COMPLETA. Achicarla difumina las líneas finas en
        # gris y el blueprint del Volvo daba False aunque cumplía los dos
        # números (2026-08-05). numpy lo resuelve al instante de todos modos.
        a = np.array(img)
        claro = float((a > 235).mean())
        oscuro = float((a < 90).mean())
        # Un dibujo técnico: fondo casi todo blanco, y las líneas son poca área.
        return claro > 0.70 and oscuro < 0.25
    except Exception:
        return False


# ── CRONÓMETRO POR ETAPA ────────────────────────────────────────────────
# Se enciende con la variable de entorno AURORA_TIEMPOS=1 y escribe a stderr,
# nunca a stdout (AURORA lee stdout con json.loads: una línea de más ahí la
# deja sin respuesta). Existe porque el 2026-08-26 esta cadena se pasaba de
# los 150 s del chat y no había forma de saber en qué paso se iba el tiempo:
# medir a mano por fuera daba 32 s y adentro tardaba 8 minutos.
def _cronometro():
    import os, sys, time
    if not os.getenv("AURORA_TIEMPOS"):
        return lambda _q: None
    t0 = time.time()

    def marca(q: str) -> None:
        print(f"[tiempos] {q:<38} {time.time() - t0:6.1f}s", file=sys.stderr, flush=True)
    return marca


def convertir(entrada: str, quitar_fondo: bool = True,
              umbral: int = 128, modo: str = "auto") -> dict:
    """Foto → DXF listo para la láser. Cada paso reporta si sirvió.

    modo="lineal"   dibujo lineal: se ven los detalles de adentro (el default)
    modo="silueta"  solo el contorno relleno, para cortar la forma
    """
    origen = Path(entrada)
    if not origen.exists():
        return {"status": "NO_EXISTE", "detalle": f"No encontré: {entrada}"}

    _marca = _cronometro()
    pasos = []
    trabajo = origen

    # ── SI ESTA IMAGEN YA SE VECTORIZÓ, SE REUSA. ───────────────────────
    # Encontrado el 2026-08-26: el mismo archivo tardó 21 s a las 6:20 y más
    # de 180 s a las 6:30. El código no cambió — cambió que la PC de Anuar
    # tenía 1 GB libre con Corel, Aspire, RDWorks y el navegador abiertos.
    # Mientras tanto él reintentaba, y cada reintento volvía a hacer TODO el
    # trabajo desde cero: cargar el modelo, recortar, trazar, escribir.
    # Si el DXF de esa misma imagen ya existe y es más nuevo que la imagen,
    # es EL MISMO resultado: se devuelve y se acabó. Si él cambia la imagen,
    # la fecha cambia y se rehace. Nunca entrega un DXF de otra foto.
    _previo = DESTINO / f"{origen.stem}.dxf"
    try:
        if (_previo.exists()
                and _previo.stat().st_mtime >= origen.stat().st_mtime
                and _previo.stat().st_size > 1024):
            import ezdxf as _ez
            _n = sum(1 for _ in _ez.readfile(str(_previo)).modelspace())
            if _n > 0:
                return {"status": "OK", "archivo": str(_previo), "trazos": _n,
                        "corte": 1, "grabado": max(0, _n - 1), "reusado": True,
                        "pasos": [f"ya estaba vectorizada: reusé {_previo.name} "
                                  f"({_n} trazos). Si cambiaste la imagen, "
                                  f"guárdala de nuevo y la rehago."],
                        "kb": round(_previo.stat().st_size / 1024, 1)}
    except Exception:
        pass    # si el DXF viejo está dañado, se rehace y ya

    # ── SE REDUCE LA FOTO ANTES DE TRABAJARLA (2026-08-26) ────────────────
    # Todo lo que sigue —quitar fondo, detectar bordes, contar contornos,
    # escribir el DXF— cuesta en proporción a los píxeles, y para cortar no
    # hacen falta. La piñata de Alicia llegó de 1086x1448: a 90 cm de alto
    # eso es 0.6 mm por píxel, mucho más fino que lo que la láser puede
    # cortar. Con la máquina ocupada (Corel + Aspire + el navegador abiertos)
    # la cadena completa se pasaba de los 150 s del chat y Anuar recibía
    # "mándame el DXF" en vez de su piñata. Reducir el lado largo a 1000 px
    # deja ~0.9 mm por píxel a 90 cm: sigue siendo más fino que el corte, y
    # el trabajo baja a menos de la mitad. El DXF se escala al tamaño que él
    # pida de todos modos, así que no se pierde nada real.
    LADO_MAX = 1000
    try:
        from PIL import Image as _Im
        _o = _Im.open(origen)
        if max(_o.size) > LADO_MAX:
            _o = _o.convert("RGB")
            _antes = _o.size
            _o.thumbnail((LADO_MAX, LADO_MAX), _Im.LANCZOS)
            _chica = DESTINO / f"_tmp_{origen.stem}_chica.png"
            _chica.parent.mkdir(parents=True, exist_ok=True)
            _o.save(_chica)
            trabajo = _chica
            pasos.append(f"foto reducida de {_antes[0]}x{_antes[1]} a "
                         f"{_o.size[0]}x{_o.size[1]} (de sobra para cortar)")
    except Exception as e:
        pasos.append(f"sin reducir ({type(e).__name__})")

    _marca("reducir")
    # ¿Es un dibujo técnico o una foto? Cambia TODO el tratamiento.
    lineal_de_origen = _ya_es_dibujo_lineal(trabajo)
    if modo == "auto":
        modo = "trazar" if lineal_de_origen else "lineal"
    if lineal_de_origen:
        # A un blueprint no se le quita el fondo: no hay fondo que quitar, y
        # rembg lo puede destrozar (2026-08-05, el Volvo de Anuar).
        quitar_fondo = False
        pasos.append("es un dibujo de líneas: se traza tal cual")
    elif quitar_fondo and _fondo_ya_plano(trabajo):
        # Ya viene sobre un fondo parejo: rembg no tiene nada que hacer y
        # cuesta 48 s (medido con el escudo de Peugeot el 2026-08-26).
        quitar_fondo = False
        pasos.append("la imagen ya venía sobre fondo parejo: no hizo falta recortarla")
    elif quitar_fondo and _ya_tiene_fondo_quitado(trabajo):
        # Ya viene con alpha real (recorte tipo sticker): correrle rembg
        # encima es tiempo perdido de verdad, no cosmético (ver cabecera de
        # _ya_tiene_fondo_quitado).
        quitar_fondo = False
        pasos.append("el PNG ya traía fondo transparente: se usa tal cual")

    _marca("decidir tratamiento")
    # 1) Quitar el fondo con rembg
    if quitar_fondo:
        try:
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location("conversiones",
                                                RAIZ / "EDITOR" / "conversiones.py")
            conv = _ilu.module_from_spec(spec)
            spec.loader.exec_module(conv)
            # sobre_blanco=True: el PNG transparente se ve NEGRO al abrirlo en
            # Corel — Anuar lo reportó el 2026-08-05 con bunzo.jpg: "si lo abro
            # en corel sigue teniendo fondo, pero negro". Con fondo blanco se
            # ve como debe y además el paso siguiente (B&N) sale limpio.
            # modelo="u2net" (objetos) y no el de personas: lo que se manda a
            # cortar es una piñata, un logo, una pieza. Medido el 2026-08-26 con
            # la piñata de Alicia: 14 s contra 42 s, y recorta igual de bien.
            r = conv.quitar_fondo(str(trabajo), sobre_blanco=True, modelo="u2net")
            ruta_sin_fondo = r.get("salida") or r.get("archivo") or r.get("ruta")
            if r.get("status") in ("OK", "ok") and ruta_sin_fondo and Path(ruta_sin_fondo).exists():
                trabajo = Path(ruta_sin_fondo)
                pasos.append("fondo quitado con rembg")
            else:
                pasos.append(f"sin quitar fondo ({r.get('detalle', r.get('status', '?'))})")
        except Exception as e:
            pasos.append(f"sin quitar fondo ({type(e).__name__})")

    _marca("quitar fondo")
    # 2) DIBUJO LINEAL, no silueta rellena.
    #    Encontrado el 2026-08-05: pasar a blanco y negro puro dejaba el trailer
    #    como una mancha sólida — 1 solo trazo, la pura silueta, sin nada de
    #    detalle adentro. Anuar lo pidió claro: "mejor que deje el dibujo
    #    lineal". Para eso hay que DETECTAR BORDES, no rellenar.
    try:
        from PIL import Image
        img = Image.open(trabajo)
        if img.mode in ("RGBA", "LA"):
            # Lo que quedó transparente se vuelve blanco, para que el borde del
            # sujeto salga limpio.
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[-1])
            img = fondo
        gris = img.convert("L")

        if modo == "trazar":
            # Ya es un dibujo de líneas: se traza lo negro tal cual. Detectarle
            # bordes generaría DOS líneas por cada trazo — el error del Volvo.
            bn = gris.point(lambda v: 0 if v < 200 else 255, mode="1")
            pasos.append("trazos tomados directo del dibujo")
        elif modo == "lineal":
            import numpy as np
            try:
                import cv2
                arr = np.array(gris)
                # BILATERAL, no Gaussian (2026-08-22, sticker de Alicia con
                # degradados en pelo/piel): un blur normal difumina parejo,
                # pero el degradado sigue generando bandas de contraste que
                # Canny lee como líneas — cientos de anillos falsos. El
                # bilateral alisa el degradado SIN tocar los bordes de
                # verdad (cejas, ojos, contorno), que es justo lo que hace
                # falta: quitar la banda, no la línea.
                suave = cv2.bilateralFilter(arr, 9, 90, 90)
                bordes = cv2.Canny(suave, 80, 200)
                # FILTRO DE BASURITAS: sin esto, cada chispita/brillo suelto
                # salía como un contorno cerrado propio — miles de trazos que
                # ni cortan nada útil y dejaban a svgpathtools 7+ minutos
                # procesando basura. Mismo criterio que ya usa
                # EDITOR/contorno_de_corte.py: se descarta lo menor a un
                # área mínima ANTES de vectorizar, no después.
                cont, _ = cv2.findContours(bordes, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                area_min = max(9, (min(arr.shape) * 0.006) ** 2)   # ~ manchitas de <0.6% del lado corto
                largo_min = min(arr.shape) * 0.02
                candidatos = [c for c in cont
                             if cv2.contourArea(c) >= area_min or cv2.arcLength(c, False) >= largo_min]
                descartadas = len(cont) - len(candidatos)
                # TOPE DURO: pase lo que pase con el contenido de la imagen,
                # nunca se mandan más de 400 trazos a vectorizar. Es lo que
                # de verdad evita que esto vuelva a tardar minutos con
                # cliente esperando en el chat — un límite en tiempo real,
                # no una esperanza de que el filtro de arriba baste siempre.
                TOPE_TRAZOS = 400
                if len(candidatos) > TOPE_TRAZOS:
                    candidatos.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)
                    descartadas += len(candidatos) - TOPE_TRAZOS
                    candidatos = candidatos[:TOPE_TRAZOS]
                limpio = np.zeros_like(bordes)
                cv2.drawContours(limpio, candidatos, -1, 255, 1)
                # Los bordes salen blancos sobre negro; se invierte porque
                # vtracer traza lo NEGRO.
                bn = Image.fromarray(255 - limpio).convert("1")
                pasos.append("dibujo lineal por detección de bordes"
                            + (f" ({descartadas} basuritas descartadas)" if descartadas else ""))
            except ImportError:
                bn = gris.point(lambda v: 0 if v < umbral else 255, mode="1")
                pasos.append("blanco y negro puro (falta OpenCV para el lineal)")
        else:
            bn = gris.point(lambda v: 0 if v < umbral else 255, mode="1")
            pasos.append("silueta en blanco y negro puro")

        tmp_bn = DESTINO / f"_tmp_{origen.stem}_bn.png"
        tmp_bn.parent.mkdir(parents=True, exist_ok=True)
        # SE GUARDA EN RGB, NO en 1 bit. Encontrado el 2026-08-05: guardarlo
        # como mode="1" hacía que vtracer devolviera 3 trazos de un blueprint
        # con cientos de líneas — el DXF salía basura y solo se vio al mirar la
        # vista previa (la idea de Rocío, que ya sirvió el mismo día).
        bn.convert("RGB").save(tmp_bn)
        _marca("preparar blanco y negro")
    except Exception as e:
        return {"status": "ERROR", "pasos": pasos,
                "detalle": f"no pude prepararlo: {type(e).__name__}: {e}"}

    # 3) Trazar con vtracer (segundos, no minutos)
    try:
        import vtracer
        tmp_svg = DESTINO_SVG / f"{origen.stem}.svg"
        vtracer.convert_image_to_svg_py(str(tmp_bn), str(tmp_svg),
                                        colormode="binary")
        pasos.append("trazado con vtracer")
        _marca("vtracer")
    except Exception as e:
        return {"status": "ERROR", "pasos": pasos,
                "detalle": f"vtracer falló: {type(e).__name__}: {str(e)[:120]}"}

    # 4) SVG → DXF, sin Inkscape
    # UN DXF POR IMAGEN, y se sobreescribe. Antes se iba numerando
    # (`__2`, `__3`...) para no pisar nada, pero con el reuso de arriba eso
    # rompe la cuenta: el reuso mira `nombre.dxf` y los reintentos escribían
    # `nombre__7.dxf`, así que nunca coincidían y volvía a hacer todo. Si
    # llegamos aquí es porque la imagen cambió o no había DXF: el viejo ya no
    # sirve para esa imagen.
    salida = DESTINO / f"{origen.stem}.dxf"
    r = svg_a_dxf(tmp_svg, salida)
    _marca("svg a dxf")
    if r.get("status") != "OK":
        return {"status": "ERROR", "pasos": pasos,
                "detalle": f"al pasar a DXF: {r.get('detalle')}"}
    pasos.append(f"{r['trazos']} trazos escritos al DXF")

    for tmp in (tmp_bn,):
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass

    # Vista previa: para no tener que abrir Corel solo para ver si quedó bien.
    vista = vista_previa(salida)
    return {"status": "OK", "archivo": str(salida), "svg": str(tmp_svg),
            "vista": vista.get("archivo", ""), "medidas": vista.get("medidas", ""),
            "trazos": r["trazos"], "pasos": pasos,
            # Se pasan los conteos por capa: sin esto el reporte decía
            # "GRABADO 0 trazos" aunque sí los hubiera (2026-08-05).
            "corte": r.get("corte", 1), "grabado": r.get("grabado", 0),
            "kb": round(salida.stat().st_size / 1024, 1)}


def vista_previa(dxf: Path, ancho_px: int = 900) -> dict:
    """Dibuja el DXF como PNG para verlo sin abrir nada.

    La idea es de ROCÍO, la esposa de Anuar (2026-08-05): *"una buena opción es
    que tenga visualizador previo del archivo"*. Y tiene toda la razón — abrir
    Corel solo para ver si el trazado quedó bien es medio minuto cada vez, y
    muchas veces se ve al instante que hay que rehacerlo.

    Se dibuja con los MISMOS colores de las capas: rojo lo que va a corte, azul
    lo que va a grabado. Así se ve de un vistazo si el reparto quedó bien.
    """
    try:
        import ezdxf
        from PIL import Image, ImageDraw
    except ImportError as e:
        return {"status": "FALTA_LIBRERIA", "detalle": str(e)}
    try:
        doc = ezdxf.readfile(str(dxf))
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}"}

    msp = doc.modelspace()
    trazos = []
    for e in msp:
        try:
            if e.dxftype() == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
            elif e.dxftype() == "POLYLINE":
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            elif e.dxftype() == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            else:
                continue
            if len(pts) >= 2:
                trazos.append((pts, getattr(e.dxf, "layer", "0")))
        except Exception:
            continue
    if not trazos:
        return {"status": "VACIO", "detalle": "El DXF no trae nada dibujable."}

    xs = [p[0] for t, _c in trazos for p in t]
    ys = [p[1] for t, _c in trazos for p in t]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    if ancho <= 0 or alto <= 0:
        return {"status": "VACIO", "detalle": "El dibujo no tiene tamaño."}

    escala = ancho_px / ancho
    borde = 20
    img = Image.new("RGB", (int(ancho * escala) + borde * 2,
                            int(alto * escala) + borde * 2), "white")
    d = ImageDraw.Draw(img)
    for pts, capa in trazos:
        # Los mismos colores de las capas: rojo corta, azul graba.
        color = (200, 30, 30) if capa.upper() == "CORTE" else (30, 90, 200)
        grosor = 2 if capa.upper() == "CORTE" else 1
        plano = [(borde + (x - min(xs)) * escala,
                  borde + (max(ys) - y) * escala) for x, y in pts]
        d.line(plano, fill=color, width=grosor)

    salida = _carpeta("imagenes") / f"{dxf.stem}_vista.png"
    n = 2
    while salida.exists():
        salida = salida.parent / f"{dxf.stem}_vista__{n}.png"
        n += 1
    img.save(salida)
    return {"status": "OK", "archivo": str(salida),
            "medidas": f"{ancho:.0f} × {alto:.0f} mm", "trazos": len(trazos)}


def _texto(r: dict) -> str:
    if r.get("status") == "NO_EXISTE":
        return r["detalle"]
    if r.get("status") != "OK":
        hechos = "\n".join(f"   ✓ {p}" for p in r.get("pasos", []))
        return (f"No pude terminarlo (no te miento).\n{hechos}\n"
                f"   ✗ {r.get('detalle', 'error desconocido')}")
    hechos = "\n".join(f"   ✓ {p}" for p in r["pasos"])
    return (f"✅ **Listo, en DOS capas**\n{hechos}\n\n"
            f"   🔴 **CORTE** — el contorno de afuera (1 trazo)\n"
            f"   🔵 **GRABADO** — el dibujo lineal de adentro "
            f"({r.get('grabado', 0)} trazos)\n\n"
            f"📁 `{r['archivo']}`  ({r['kb']} KB)\n"
            f"   _SVG también: `{Path(r['svg']).name}`_\n\n"
            "**Están separadas a propósito.** Si cortaras todo, la pieza "
            "quedaría hecha pedazos: el detalle de adentro va para GRABAR, no "
            "para cortar. En RDWorks le pones a cada capa lo suyo.\n\n"
            "_Ábrelo antes de mandarlo: vectorizar una foto siempre deja "
            "algún trazo suelto que conviene limpiar._")


if __name__ == "__main__":
    _consola_utf8()
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    # --json (2026-08-22): AURORA lo llama como SUBPROCESO aparte, no en un
    # hilo dentro de su propio proceso — con 35 motores + listeners de
    # WhatsApp corriendo, el trazado (CPU real, bilateral+Canny+vtracer)
    # competía por el mismo CPU limitado y lo que aislado tardaba 15s
    # llegaba a tardar minutos dentro del servidor. Un proceso aparte no
    # comparte ese CPU compartido de la misma forma y se puede matar limpio
    # si se pasa de tiempo, sin dejar hilos huérfanos corriendo.
    if "--json" in sys.argv:
        import json as _json
        args = [a for a in sys.argv[1:] if a != "--json"]
        modo_cli = args[1] if len(args) > 1 else "auto"
        print(_json.dumps(convertir(args[0], True, 128, modo_cli), ensure_ascii=False))
    else:
        print(_texto(convertir(sys.argv[1])))
