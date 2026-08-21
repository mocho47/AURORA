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

# Lo grabado va en capa aparte, y separado en dos. Anuar lo pidió así el
# 2026-08-06: **números en ROJO, grabado en AZUL**. Sirve para algo real:
# color distinto es operación distinta, y así Aspire le separa las
# herramientas solo en vez de que él vaya seleccionando a mano.
#
# LO QUE LOS DISTINGUE ES EL TAMAÑO, y es lo único honesto que tengo: un
# número de ensamble mide unos milímetros; un grabado de verdad es más grande.
# AURORA NO sabe leer qué dice un contorno. En estos tres archivos todo lo
# grabado son números, así que sale bien; en uno con dibujo grabado, lo chico
# se irá a rojo aunque no sea un número.
CAPA_NUMEROS = "NUMEROS"
COLOR_NUMEROS = 1      # rojo
CAPA_GRABADO = "GRABADO"
COLOR_GRABADO = 5      # azul
# Por arriba de esto ya no es un numerito de ensamble.
NUMERO_MAX_MM = 12.0


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Qué tan fino se aplana una curva para poder trabajarla. 0.05 mm es menos de
# lo que abre el láser al cortar y menos de lo que ve el ojo: la pieza sale
# igual.
_FINURA_CURVA = 0.05


def _puntos(e) -> list:
    """Los vértices de una entidad, sea del tipo que sea.

    OJO: POLYLINE y LWPOLYLINE se leen distinto. Leer solo LWPOLYLINE dejaba
    fuera casi todos los archivos de Anuar (2026-08-05).

    LAS CURVAS — y no es solo cosa de detectar ranuras (2026-08-14, cabeza de
    toro). Ese archivo son **188 SPLINE y 2 polilíneas**. Al no saber leerlos,
    esta función devolvía vacío y el escalado los SALTABA con un `continue`:
    Anuar pidió el 50% y salió un archivo de 4931 × 2975 mm donde el ancho no
    había cambiado — las 2 polilíneas encogidas y las 188 curvas del tamaño
    original, revueltas. Y arriba decía "✅ el diseño quedó al 50%".

    Leerlas arregla las dos cosas de un golpe:
      · el escalado deja de saltarse el 99% del archivo;
      · las ranuras aparecen — en esa cabeza son **374 lados**, 82 de ellos de
        4.1 mm, donde el motor veía **2**.

    Se aplana la curva a puntos. La pieza que se toque se guardará como
    polilínea (`_reemplazar` ya lo hace para todos), así que la curva se pierde
    solo donde hubo que modificar. Corta idéntico; lo que se pierde es poder
    jalar esa silueta de un nodo más adelante.
    """
    t = e.dxftype()
    try:
        if t == "LWPOLYLINE":
            return [(p[0], p[1]) for p in e.get_points()]
        if t == "POLYLINE":
            return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if t == "LINE":
            return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        if t in ("SPLINE", "ELLIPSE"):
            return [(p[0], p[1]) for p in e.flattening(_FINURA_CURVA)]
    except Exception:
        pass
    return []


def _unir_colineales(pts: list, grados: float = 6.0) -> tuple:
    """Une los tramos casi rectos y dice de dónde salió cada punto que queda.

    POR QUÉ HACE FALTA (2026-08-08, casa de Calamardo). En un diseño con
    curvas, cada lado recto de un encastre viene partido en decenas de
    segmentitos de medio milímetro —lo que dejó el vectorizado de la figura—.
    El buscador de dientes mira tres segmentos seguidos, y con la pieza
    partida así ese patrón no aparece nunca: encontraba **cero** encastres en
    un archivo que los tiene. Uniendo lo casi recto aparecieron **85**, con la
    profundidad de 3.0 mm que es justo el grosor del material.

    Devuelve (puntos_unidos, indices_en_el_original). Los índices importan
    tanto como los puntos: la detección se hace sobre la versión simplificada,
    pero LA MODIFICACIÓN SE APLICA SOBRE EL ORIGINAL. Guardar el simplificado
    dejaría la cabeza de Calamardo hecha un polígono.
    """
    n = len(pts)
    if n < 3:
        return list(pts), list(range(n))
    lim = math.cos(math.radians(grados))
    salida, indices = [pts[0]], [0]
    for i in range(1, n):
        a = salida[-1]
        b = pts[i]
        c = pts[(i + 1) % n]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
        if cos < lim:                       # aquí sí hay una esquina de verdad
            salida.append(b)
            indices.append(i)
    return salida, indices


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
        # Se mide sobre el contorno con los tramos rectos ya unidos: en un
        # diseño con curvas, medir segmento por segmento cuenta los pedacitos
        # del vectorizado y no los lados de los encastres. En Calamardo eso
        # daba 1.5 mm cuando el material es de 3.0 (2026-08-08).
        pts, _ = _unir_colineales(_puntos(e))
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

    # TODOS los grosores del archivo, no solo el más repetido (2026-08-14).
    #
    # La cabeza de toro traía el mismo modelo DOS VECES: una versión para
    # material de 4 mm (ranuras de 4.1 ×140) y otra para 12 mm (ranuras de
    # 10.1 ×93). Lo vio Anuar abriendo el archivo, no mis conteos. Con un solo
    # grosor el motor ajustaba 93 ranuras y dejaba las otras intactas: media
    # cabeza servible y media inservible, con un ✅ arriba.
    #
    # Y su regla, dicha igual de claro: *"si viene o viniera a 2 escalas no me
    # importa, lo que me importa es el resultado, yo pido un resultado"*. O sea
    # que no hay que preguntarle cuál quiere — si pide el archivo para 2.5, se
    # van a 2.5 TODAS las ranuras, midan lo que midan hoy.
    #
    # DOS INTENTOS FALLIDOS, ANOTADOS PARA NO REPETIRLOS (2026-08-14):
    #
    #  1) Pedir la mitad de repeticiones que el más frecuente dejó fuera el
    #     juego de 10.1 mm (93 contra 243) y el motor ajustó 2 ranuras.
    #  2) Quitar el filtro del todo —creyendo que "probar de más es gratis"—
    #     detectó **104 grosores**, del 1.5 al 11.9, y "ajustó" **2497
    #     ranuras**: el archivo entero deformado. No es gratis: con suficientes
    #     medidas candidatas, cualquier tramo coincide con alguna.
    #
    # Se vuelve al criterio prudente. Para archivos con dos juegos de ranuras
    # —como esa cabeza, que trae la versión de 4 mm y la de 12— la detección
    # automática NO alcanza, y está bien que no alcance: para eso Anuar puede
    # decir el grosor («de 4 a 2.5»), que es el camino que sí funciona y el que
    # se arregló el mismo día. Adivinar mal cuesta material; preguntar no.
    piso = max(REPETICIONES_MINIMAS, veces * 0.5)
    grosores = sorted({L for L, n in candidatos if n >= piso})

    return {"status": "OK", "grosor": grosor, "veces": veces,
            "grosores": grosores, "tipos": dict(tipos),
            "otras": medidas.most_common(5)}


def _es_ranura(pts: list, grosor: float, tol: float = 0.35) -> tuple:
    """¿Este contorno cerrado es una ranura del grosor buscado, EN CUALQUIER ÁNGULO?

    Devuelve (es_ranura, direccion) donde direccion es el vector unitario del
    lado CORTO — o sea hacia dónde hay que abrir la ranura para ensancharla.

    ESTO ANTES SOLO VEÍA LAS RANURAS RECTAS. Medía la caja envolvente (el
    ancho en X y el alto en Y), así que una ranura en diagonal tiene caja
    grande en los dos ejes y nunca la detectaba. Anuar lo encontró armando la
    casa de Bob Esponja a mano el 2026-08-06: *"algunas vienen en posición
    diagonal y eso habría que rotarlas para poder ajustar de manera correcta"*.

    Rotar la pieza NO hace falta: se mide la ranura en SU PROPIO eje. Se toman
    sus dos lados, el corto dice el grosor y su dirección dice hacia dónde
    abrir. La pieza no se mueve ni un micrón.
    """
    import math
    if len(pts) < 4:
        return False, None

    # Se quita el punto de cierre si repite el primero.
    p = list(pts)
    if len(p) > 4 and abs(p[0][0] - p[-1][0]) < 1e-6 and abs(p[0][1] - p[-1][1]) < 1e-6:
        p = p[:-1]
    if len(p) != 4:
        return False, None

    lado_a = (p[1][0] - p[0][0], p[1][1] - p[0][1])
    lado_b = (p[2][0] - p[1][0], p[2][1] - p[1][1])
    largo_a = math.hypot(*lado_a)
    largo_b = math.hypot(*lado_b)
    if largo_a <= 0 or largo_b <= 0:
        return False, None

    # Tiene que ser un rectángulo: los lados contiguos, perpendiculares.
    # Un rombo o un trapecio no es una ranura de ensamble.
    coseno = abs(lado_a[0] * lado_b[0] + lado_a[1] * lado_b[1]) / (largo_a * largo_b)
    if coseno > 0.05:                     # ~3° de tolerancia
        return False, None

    if largo_a < largo_b:
        corto, lado_corto = largo_a, lado_a
        largo = largo_b
    else:
        corto, lado_corto = largo_b, lado_b
        largo = largo_a

    if abs(corto - grosor) > tol or largo <= grosor:
        return False, None

    return True, (lado_corto[0] / corto, lado_corto[1] / corto)


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


def _es_grabado(pts: list, grosor: float) -> bool:
    """¿Esto es GRABADO —un número de ensamble, una letra— y no un corte?

    Anuar puso la regla el 2026-08-06 y es la correcta: *"los números son para
    el armado; la ranura es inamovible de lugar, los números yo los
    reubicaría"*. O sea el grabado NUNCA se deforma. Si estorba se mueve
    completo, pero no se le tocan los vértices.

    Esto arregla el destrozo que se vio en la casa de Bob Esponja: al permitir
    que se ajustaran los dientes, el buscador de dientes entró a los contornos
    del "60" y del "10" —que tienen el mismo patrón sale-avanza-regresa por
    todos lados— y dejó los números hechos garabatos. Sin las etiquetas no se
    sabe qué pieza es cuál al armar.

    Un número se reconoce por lo que es: un contorno chico, con muchos
    vértices y segmentos cortísimos. Un contorno de pieza es grande y con
    tramos largos.

    OJO CON LA DIFERENCIA, que Anuar precisó enseguida: *"solo para el caso de
    números; los grabados reales también son inamovibles"*. O sea:

      • NADA grabado se deforma jamás — ni un número ni un dibujo.
      • REUBICAR solo se vale con los números de ensamble, que son etiquetas.
        El grabado real es parte de cómo se ve la pieza y no se mueve ni un
        milímetro.

    Por eso, si una ranura ensanchada llegara a caerle encima a un grabado que
    no es un número, AURORA NO lo resuelve sola: lo reporta y decide él.
    """
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)

    # UN CUADRITO DEL GROSOR ES GRABADO, no un ensamble.
    # Anuar lo dijo el 2026-08-06: *"al igual que los cuadritos de 1.5 son
    # grabados"*. Con eso se explican 4 de las 5 hembras que parecían haberse
    # quedado sin ensanchar: no eran hembras. Una ranura es LARGA —tiene que
    # entrar una tabla— y un cuadrito no lo es.
    #
    # PERO SOLO SI MIDE COMO EL GROSOR. La primera versión decía "cualquier
    # cosa chica" y se llevó a la capa de grabado 61 contornos de MENOS DE UN
    # MILÍMETRO que no son números ni cuadritos: probablemente descargas de
    # esquina, que SÍ hay que cortar. Mandarlas a grabar dejaría el ensamble
    # sin cerrar. Ante la duda no se reclasifica: se deja como corte, que es
    # como venía.
    if (grosor * 0.6 <= ancho <= grosor * 1.6
            and grosor * 0.6 <= alto <= grosor * 1.6):
        return True

    # De aquí para abajo, lo que se busca son letras y números: contornos con
    # muchos vértices. Un rectangulito de 4 puntos nunca es un dígito.
    if len(pts) < 20:
        return False
    # Un número de ensamble mide unos pocos milímetros; una pieza, centímetros.
    if ancho > grosor * 20 or alto > grosor * 20:
        return False
    largos = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
              for i in range(len(pts) - 1)]
    largos = [v for v in largos if v > 1e-9]
    if not largos:
        return False
    # Letras y números: puro segmento corto, porque son curvas discretizadas.
    cortos = sum(1 for v in largos if v < grosor)
    return cortos / len(largos) > 0.6


def _ensanchar_hembra(pts: list, viejo: float, delta: float,
                      tol: float = 0.35) -> tuple:
    """Abre un HUECO cerrado a lo ancho, sea rectángulo, cruz, L o T.

    Anuar lo dejó clarísimo el 2026-08-06: *"solo hay que ajustar los huecos
    donde entra el mdf, sin modificar la contraparte, es decir solo modificar
    las hembras y hacerlo solo del grosor"*.

    El bug que esto arregla: una ranura EN CRUZ tiene 12 puntos, así que no
    pasaba por el camino de las ranuras (que pedía 4) y caía en el de los
    dientes, que le movía las puntas y **la dejaba deformada** — se vio en el
    acercamiento de la casa de Bob Esponja: la cruz dejaba de ser cruz.

    La regla correcta no es mover puntos: es mover LADOS. Un lado se abre solo
    si enfrente, a la distancia del grosor, hay otro lado paralelo mirando al
    revés — o sea si ahí el hueco mide justo lo que mide el material. Así cada
    brazo de la cruz se abre sobre su propio eje y el largo no se toca.
    """
    q = _limpiar(pts)
    # SI LIMPIAR SE COMIÓ MEDIO CONTORNO, ESTO NO ERA UN HUECO RECTO.
    # Fue el destrozo de los números de la casa de Bob Esponja (2026-08-06):
    # un "60" al 50% tiene 82 puntos repartidos en 1.6 mm, o sea segmentos de
    # 0.05 mm. _limpiar —que junta lo que está a menos de 0.25 mm— lo dejaba
    # en 10 puntos, y esta función escribía de vuelta ESA versión: el número
    # quedaba hecho garabato. Una curva no es una ranura; se devuelve intacta.
    if len(q) < len(pts) * 0.8:
        return pts, 0
    if len(q) > 3 and math.hypot(q[0][0] - q[-1][0], q[0][1] - q[-1][1]) < 1e-6:
        q = q[:-1]
    n = len(q)
    if n < 4:
        return pts, 0

    # Hacia dónde es "afuera del hueco" en cada lado. Depende de si el
    # contorno viene en sentido horario o antihorario.
    area = sum(q[i][0] * q[(i + 1) % n][1] - q[(i + 1) % n][0] * q[i][1]
               for i in range(n)) / 2.0
    giro = 1.0 if area > 0 else -1.0

    lados = []
    for i in range(n):
        ax, ay = q[i][0], q[i][1]
        bx, by = q[(i + 1) % n][0], q[(i + 1) % n][1]
        dx, dy = bx - ax, by - ay
        largo = math.hypot(dx, dy)
        if largo < 1e-9:
            lados.append(None)
            continue
        lados.append({"med": ((ax + bx) / 2, (ay + by) / 2),
                      "dir": (dx / largo, dy / largo),
                      "nor": (dy / largo * giro, -dx / largo * giro),
                      "largo": largo})

    def enfrentados(a, b) -> bool:
        """¿'b' está enfrente de 'a', a la distancia del grosor?"""
        # Se miran al revés uno del otro.
        if a["nor"][0] * b["nor"][0] + a["nor"][1] * b["nor"][1] > -0.95:
            return False
        sep = ((b["med"][0] - a["med"][0]) * a["nor"][0]
               + (b["med"][1] - a["med"][1]) * a["nor"][1])
        # Enfrente significa del lado de ADENTRO del hueco: separación negativa.
        if abs(-sep - viejo) > tol:
            return False
        # Y tienen que traslaparse, no estar corridos uno del otro.
        t = ((b["med"][0] - a["med"][0]) * a["dir"][0]
             + (b["med"][1] - a["med"][1]) * a["dir"][1])
        return abs(t) < (a["largo"] + b["largo"]) / 2

    mover = [False] * n
    for i, a in enumerate(lados):
        if not a:
            continue
        for j, b in enumerate(lados):
            if i == j or not b:
                continue
            if enfrentados(a, b):
                mover[i] = True
                break

    if not any(mover):
        return pts, 0

    # Cada punto se corre según los lados suyos que se muevan. En una esquina
    # de la cruz manda la suma de los dos, que es lo que la mantiene cuadrada.
    nuevos = []
    for k in range(n):
        dx = dy = 0.0
        for lado in ((k - 1) % n, k):
            if mover[lado] and lados[lado]:
                dx += lados[lado]["nor"][0] * delta
                dy += lados[lado]["nor"][1] * delta
        nuevos.append((q[k][0] + dx, q[k][1] + dy))

    if len(pts) > len(q):        # venía cerrado: se le devuelve el cierre
        nuevos.append(nuevos[0])
    return nuevos, sum(1 for m in mover if m)


def _adaptar_ranuras_borde(pts: list, viejo: float, nuevo: float,
                           tol: float = 0.3) -> tuple:
    """Ajusta las ranuras TALLADAS EN EL CONTORNO — la hembra del diente.

    `_adaptar_dientes` busca el MACHO: sale perpendicular *el grosor*, avanza,
    y regresa. La hembra es al revés: baja lo que sea (la profundidad), y el
    que mide el grosor es el TRAMO DE CRUCE — el ancho del hueco donde entra
    la otra tabla.

    Nadie buscaba esa forma, y por eso la casa de Calamardo salió con 332
    segmentos en 1.4 mm (2026-08-11). El archivo tiene 314 contornos y solo 4
    son rectángulos sueltos: las piezas vienen dibujadas de un trazo, con
    contornos de hasta 3,280 vértices y los escalones tallados adentro.
    `_es_ranura` exige exactamente 4 puntos, así que **no podía ver el 99%**
    de ese diseño — y aun así el adaptador respondía "adaptado".

    Para ensanchar el hueco se separan sus DOS PAREDES medio delta cada una.
    Mover una sola dejaría el encastre corrido de su sitio.

    Devuelve (puntos_nuevos, cuántas ranuras se ajustaron).
    """
    q, idx = _unir_colineales(pts)
    if len(q) < 5:
        return pts, 0
    delta = nuevo - viejo
    fuera = list(pts)
    ajustadas = 0
    i = 1
    while i < len(q) - 2:
        # baja / cruza / sube  →  el que mide el grosor es el que CRUZA
        a, b, c, d = q[i - 1], q[i], q[i + 1], q[i + 2]
        baja = (b[0] - a[0], b[1] - a[1])
        cruza = (c[0] - b[0], c[1] - b[1])
        sube = (d[0] - c[0], d[1] - c[1])
        l_baja = math.hypot(*baja)
        l_cruza = math.hypot(*cruza)
        l_sube = math.hypot(*sube)
        if l_cruza <= 0 or l_baja <= 0 or l_sube <= 0:
            i += 1
            continue
        # El cruce mide el grosor; las paredes son perpendiculares a él, van en
        # sentidos opuestos, y tienen fondo de verdad (no son un dentado fino).
        if (abs(l_cruza - viejo) <= tol
                and l_baja > 0.5 and l_sube > 0.5
                and abs(baja[0] * cruza[0] + baja[1] * cruza[1]) < 0.2 * l_baja * l_cruza
                and (baja[0] * sube[0] + baja[1] * sube[1]) < 0):
            ux, uy = cruza[0] / l_cruza, cruza[1] / l_cruza
            medio = delta / 2.0
            # Pared de entrada: se recorre HACIA ATRÁS del cruce.
            for k in range(idx[i - 1], idx[i] + 1):
                p = fuera[k]
                fuera[k] = (p[0] - ux * medio, p[1] - uy * medio)
            # Pared de salida: hacia adelante.
            for k in range(idx[i + 1], idx[i + 2] + 1):
                p = fuera[k]
                fuera[k] = (p[0] + ux * medio, p[1] + uy * medio)
            ajustadas += 1
            i += 3
            continue
        i += 1
    return fuera, ajustadas


def _adaptar_dientes(pts: list, viejo: float, nuevo: float, tol: float = 0.3) -> tuple:
    """Ajusta los dientes que van PEGADOS al contorno.

    Un diente es: sale perpendicular al borde una distancia = grosor, avanza a
    lo largo, y regresa. Para cambiarlo de grosor hay que mover la punta del
    diente hacia afuera (o adentro) la diferencia.

    Devuelve (puntos_nuevos, cuántos dientes se ajustaron).
    """
    # Se BUSCA sobre el contorno con los rectos unidos y se MODIFICA sobre el
    # original: así el encastre se ajusta y la curva de la pieza no se toca.
    # OJO: se une sobre los puntos CRUDOS, no sobre los limpiados. `_limpiar`
    # junta lo que está a menos de 0.25 mm y en un contorno vectorizado eso ya
    # deforma el encastre antes de buscarlo: pasando por ahí se encontraban 9
    # dientes en Calamardo, y sobre el crudo aparecen los ~50 reales.
    q, idx = _unir_colineales(pts)
    if len(q) < 5:
        return pts, 0
    delta = nuevo - viejo
    fuera = list(pts)
    ajustados = 0
    i = 1
    while i < len(q) - 2:
        # Tres segmentos seguidos: sale, avanza, regresa.
        a, b, c, d = q[i - 1], q[i], q[i + 1], q[i + 2]
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
            # La punta del diente va de b a c. En el contorno original eso no
            # son dos puntos sino TODO el tramo entre ellos —los pedacitos que
            # dejó el vectorizado—, y hay que mover el tramo completo o la
            # punta se rompe.
            ux, uy = sale[0] / l_sale, sale[1] / l_sale
            for k in range(idx[i], idx[i + 1] + 1):
                p = fuera[k]
                fuera[k] = (p[0] + ux * delta, p[1] + uy * delta)
            ajustados += 1
            i += 3
            continue
        i += 1
    return fuera, ajustados


def contar_medidas(entidades, objetivos: list, tol: float = 0.25) -> dict:
    """Cuántos segmentos miden como cada objetivo. Contabilidad, no criterio.

    A propósito no decide qué es una ranura: cuenta longitudes. Lo que sirve
    NO es el número suelto —en una figura vectorizada hay cientos de tramos de
    contorno que miden igual que el grosor— sino la DIFERENCIA entre contar
    antes y contar después.
    """
    cuenta = {round(o, 2): 0 for o in objetivos}
    for e in entidades:
        pts, _ = _unir_colineales(_puntos(e))
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            if L < MIN_GROSOR or L > 12.0:
                continue
            for o in objetivos:
                if abs(L - o) <= tol:
                    cuenta[round(o, 2)] += 1
                    break
    return cuenta


def verificar_cambio(antes: dict, ruta_salida: Path, viejo: float, nuevo: float,
                     tocadas: int, tol: float = 0.25) -> dict:
    """¿El archivo guardado cambió como el motor DICE que lo cambió?

    POR QUÉ ASÍ Y NO DE OTRA FORMA (2026-08-13). El primer intento medía solo
    el archivo final y reprobaba si quedaba UNA medida del grosor viejo. Probado
    contra el Crustáceo Cascarudo —la pieza que Anuar cortó y armó, y encastra—
    lo reprobó: 444 tramos de 3.0 mm que no son ranuras sino contorno y grabado.
    Un verificador que frena lo bueno hace más daño que no tener ninguno.

    La salida es no intentar reconocer ranuras —ahí es donde el detector ya está
    ciego, y heredar su ceguera no verifica nada— sino comparar dos conteos del
    MISMO archivo antes y después. El ruido de contorno aparece igual en los dos
    lados y se cancela solo. Lo que queda es el movimiento real.

    Y el contraste que importa: el motor dice haber tocado `tocadas`. Si de
    verdad las tocó, la cuenta del grosor viejo tuvo que bajar en proporción. Si
    dice 300 y solo se movieron 5, el motor está mintiendo aunque no truene.
    """
    import ezdxf
    try:
        doc = ezdxf.readfile(str(ruta_salida))
    except Exception as e:
        return {"veredicto": "NO_SE_PUDO_VERIFICAR",
                "detalle": f"{type(e).__name__}: {str(e)[:80]}"}

    despues = contar_medidas(doc.modelspace(), [viejo, nuevo], tol)
    kv, kn = round(viejo, 2), round(nuevo, 2)
    bajo = antes.get(kv, 0) - despues.get(kv, 0)
    subio = despues.get(kn, 0) - antes.get(kn, 0)

    # Se pide que se note al menos la mitad de lo declarado: una ranura mueve
    # dos paredes, pero un mismo tramo puede contarse una sola vez según cómo
    # quede el contorno. Menos de la mitad ya no es margen, es que no pasó.
    minimo = max(1, int(tocadas * 0.5))
    coherente = bajo >= minimo if tocadas else bajo > 0

    return {"veredicto": "OK" if coherente else "NO_CORTAR",
            "declaradas_por_el_motor": tocadas,
            "bajaron_del_grosor_viejo": bajo,
            "subieron_al_grosor_nuevo": subio,
            "minimo_exigido": minimo,
            "antes": {"viejo": antes.get(kv, 0), "nuevo": antes.get(kn, 0)},
            "despues": {"viejo": despues.get(kv, 0), "nuevo": despues.get(kn, 0)},
            "grosor_viejo": viejo, "grosor_pedido": nuevo}


def verificar_salida(ruta: Path, grosor_pedido: float, grosor_viejo: float = 0.0,
                     tol: float = 0.25) -> dict:
    """CONTROL DE CALIDAD del archivo YA ESCRITO — y NO lo hace quien lo escribió.

    POR QUÉ EXISTE (2026-08-13). El adaptador contaba cuántas ranuras había
    tocado y con ese conteo cantaba «✅ Adaptado», sin volver a mirar el archivo
    que acababa de guardar. La casa de Calamardo salió justo así: palomita
    verde, y 59 de 96 ranuras todavía en 1.54 mm — escaladas al 50% y nunca
    ajustadas. Anuar lo descubrió midiéndolas él, con el motor ya diciendo
    «listo». Un motor que se califica solo es una bomba de tiempo en el taller.

    Esto reabre el DXF guardado y mide su geometría desde cero. A propósito NO
    usa `_es_ranura` ni `_adaptar_ranuras_borde`: son los mismos que se quedaron
    ciegos, y un verificador que hereda la ceguera del ejecutor no verifica
    nada. Aquí solo se cuentan medidas, que es lo que se puede comprobar sin
    opinar sobre qué es una ranura.

    Devuelve cuántas medidas quedaron al grosor pedido, cuántas siguen en el
    viejo, y el veredicto. Si queda UNA sola en el viejo: no se corta.
    """
    import ezdxf
    try:
        doc = ezdxf.readfile(str(ruta))
    except Exception as e:
        return {"veredicto": "NO_SE_PUDO_VERIFICAR",
                "detalle": f"{type(e).__name__}: {str(e)[:80]}"}

    al_nuevo, al_viejo = 0, 0
    otras = collections.Counter()
    for e in doc.modelspace():
        pts, _ = _unir_colineales(_puntos(e))
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            if not (MIN_GROSOR <= L <= MAX_GROSOR) or L > 12.0:
                continue
            if abs(L - grosor_pedido) <= tol:
                al_nuevo += 1
            elif grosor_viejo and abs(L - grosor_viejo) <= tol:
                al_viejo += 1
            else:
                otras[round(L, 1)] += 1

    total = al_nuevo + al_viejo
    return {"veredicto": "NO_CORTAR" if al_viejo else "OK",
            "al_grosor_pedido": al_nuevo,
            "al_grosor_viejo": al_viejo,
            "total_medidas_de_ensamble": total,
            "otras_medidas": otras.most_common(5),
            "grosor_pedido": grosor_pedido,
            "grosor_viejo": grosor_viejo}


def adaptar(ruta: Path, grosor_nuevo: float, grosor_viejo: float = 0,
            escala: float = 1.0, tocar_machos: bool = True) -> dict:
    """Deja el diseño listo para OTRO material, y opcionalmente a otro tamaño.

    `escala=0.5` reduce el diseño a la mitad; `grosor_nuevo=2.5` deja las
    ranuras del grosor que de verdad se va a cortar. Se toca SOLO la hembra
    —el hueco donde entra el MDF— y solo a lo ancho, que es como lo hace
    Anuar a mano: *"solo hay que ajustar los huecos donde entra el mdf, sin
    modificar la contraparte"*.
    """
    import ezdxf
    info = detectar_grosor(ruta)
    if info["status"] != "OK" and not grosor_viejo:
        return info

    # TODOS los grosores que trae el archivo, no uno.
    #
    # `grosor_viejo` acepta un número o una lista. Anuar puede decir "de 4 a
    # 2.5" y entonces manda él; si no dice nada, se usan todos los que se
    # detectaron. Su regla es que él pide un resultado, no que elija entre
    # versiones: un archivo con ranuras de 4.1 y de 10.1 pedido para 2.5 sale
    # con TODAS en 2.5 (2026-08-14, cabeza de toro).
    if isinstance(grosor_viejo, (list, tuple, set)):
        viejos = sorted({float(g) for g in grosor_viejo if g})
    elif grosor_viejo:
        viejos = [float(grosor_viejo)]
    else:
        viejos = list(info.get("grosores") or [info["grosor"]])

    # Un grosor que ya es el pedido no se toca; si TODOS lo son, no hay trabajo.
    viejos = [v for v in viejos if abs(v - grosor_nuevo) >= 0.05]
    if not viejos:
        _ya = grosor_viejo or info.get("grosor")
        return {"status": "IGUAL",
                "detalle": f"Ya está para {_ya} mm. No hay nada que cambiar."}
    viejo = viejos[0]        # el principal, para los mensajes y los conteos

    doc = ezdxf.readfile(str(ruta))
    msp = doc.modelspace()

    # ESCALAR Y AJUSTAR SON DOS COSAS DISTINTAS, Y ESE ES TODO EL ASUNTO.
    # Anuar quiere las casas de Bob Esponja al 50% pero en material de 2.5 mm
    # (2026-08-06). Si solo escalas, las ranuras de 3 mm quedan de 1.5 y no
    # entra nada. Por eso se escala primero TODO —la pieza sí debe achicarse—
    # y después se ajustan SOLO las ranuras al grosor real del material.
    if abs(escala - 1.0) > 1e-9:
        saltadas = {}
        for e in list(msp):
            pts = _puntos(e)
            if not pts:
                # Una pieza que no se puede leer NO se puede escalar, y quedaría
                # del tamaño original revuelta con las demás. Antes se saltaba
                # en silencio: así salió la cabeza de toro con las 188 curvas
                # sin encoger y un ✅ arriba (2026-08-14). Ahora se cuenta y se
                # dice; el archivo no se entrega como bueno si falta algo.
                saltadas[e.dxftype()] = saltadas.get(e.dxftype(), 0) + 1
                continue
            _reemplazar(msp, e, [(p[0] * escala, p[1] * escala) + tuple(p[2:])
                                 for p in pts])
        if saltadas:
            detalle = " · ".join(f"{v} {k}" for k, v in saltadas.items())
            return {"status": "NO_PUEDO_ESCALAR",
                    "detalle": (
                        f"No puedo escalar {sum(saltadas.values())} piezas de este "
                        f"archivo ({detalle}), y dejarlas del tamaño original "
                        f"revueltas con las demás te arruinaría el corte. "
                        f"No te entrego un archivo a medias.")}
        # Las ranuras se achicaron con todo lo demás: cada grosor viejo vale
        # ahora lo que valía por la escala.
        viejos = [round(v * escala, 3) for v in viejos]
        viejos = [v for v in viejos if abs(v - grosor_nuevo) >= 0.05]
        if not viejos:
            return {"status": "IGUAL",
                    "detalle": (f"Al {escala*100:.0f}% las ranuras quedan de "
                                f"{round(viejo * escala, 3)} mm, que ya es el "
                                f"grosor pedido.")}
        viejo = viejos[0]

    for _capa, _color in ((CAPA_NUMEROS, COLOR_NUMEROS),
                          (CAPA_GRABADO, COLOR_GRABADO)):
        if _capa not in doc.layers:
            doc.layers.add(_capa, color=_color)

    # FOTO DE CÓMO ESTABA, ANTES DE MOVER UNA SOLA RANURA (2026-08-13).
    # Se toma DESPUÉS de escalar y ANTES de ajustar, para que la comparación
    # mida exactamente el paso de ajuste y no se le mezcle el escalado.
    medidas_antes = contar_medidas(list(msp), [viejo, grosor_nuevo])

    # Valor de arranque para las ramas que no son ranura (dientes, bordes).
    # Cada ranura recalcula el suyo según el grosor con el que coincidió.
    delta = (grosor_nuevo - viejo) / 2.0    # se abre/cierra por los dos lados

    ajustadas, contornos, sin_tocar, dientes, huecos, marcados = 0, 0, 0, 0, 0, 0
    fallos = []
    # SE VUELVE A PASAR HASTA QUE YA NO CAMBIE NADA.
    # Una sola pasada dejaba 16 hembras sin ensanchar de 286 (2026-08-06);
    # volver a pasar las agarraba: 16 -> 5. Repetir es seguro porque una
    # ranura que ya quedó en 2.5 deja de parecerse a 1.5 y se ignora sola:
    # nada se abre dos veces. Es más honesto converger que entregar el 94%
    # y llamarle terminado.
    for _vuelta in range(4):
        antes = ajustadas + dientes
        for e in list(msp):

            pts = _puntos(e)
            if not pts:
                continue
            # PRIMERO SE LIMPIAN LOS PUNTOS SOBRANTES, DESPUÉS SE PREGUNTA.
            # Encontrado por Anuar el 2026-08-13 con la pista de canicas. Él lo
            # sostuvo cuando yo decía lo contrario: *"cómo podrían ser hembras
            # con más de 4 esquinas, eso no es posible"*. Tenía razón.
            #
            # Estas 58 hembras SON rectángulos de 4 esquinas, pero el DXF trae
            # los lados largos PARTIDOS a la mitad — un punto de más en medio de
            # una línea recta. Medido en una: lado 4.85 a 90°, otro 4.85 a 90°,
            # 3.17 a 0°, y otra vez lo mismo. Seis puntos para un rectángulo.
            #
            # `_es_ranura` exige exactamente 4, así que contestaba "no es hembra"
            # y seguía de largo: ajustó 155 y se saltó 58 idénticas. La única
            # diferencia entre unas y otras era cómo las dibujó el diseñador.
            #
            # `_unir_colineales` ya existía y ya se usaba en detectar_grosor y en
            # _adaptar_ranuras_borde; aquí faltaba. Se limpia una sola vez y se
            # reusa: los puntos originales quedan en `pts` para el resto.
            pts_limpios, _ = _unir_colineales(pts)
            # Se prueba contra CADA grosor del archivo. Un archivo con dos
            # versiones —una de 4 mm y otra de 12— tiene ranuras de dos
            # medidas, y probar solo contra una dejaba la mitad sin ajustar
            # (2026-08-14). El delta se saca del grosor que coincidió, no de
            # uno global: cada ranura se abre lo que le toca a ella.
            es, eje, delta = False, None, 0.0
            for _v in viejos:
                es, eje = _es_ranura(pts_limpios, _v)
                if es:
                    delta = (grosor_nuevo - _v) / 2.0
                    break
            if es:
                pts = pts_limpios
            if not es:
                # EL GRABADO NO SE TOCA, POR NINGÚN CAMINO. Este candado estaba
                # solo en la rama de los dientes y por eso los números seguían
                # rompiéndose: se colaban por aquí (2026-08-06).
                if _es_grabado(pts, viejo):
                    # No se toca la geometría, pero sí se MARCA: los números
                    # van a su propia capa en azul. Anuar lo pidió el
                    # 2026-08-06 y sirve para algo real: color distinto es
                    # operación distinta — esto se GRABA, lo demás se CORTA, y
                    # así Aspire los separa solo en dos herramientas en vez de
                    # que él los vaya seleccionando a mano.
                    _xs = [q[0] for q in pts]
                    _ys = [q[1] for q in pts]
                    _grande = max(max(_xs) - min(_xs), max(_ys) - min(_ys))
                    _capa = CAPA_NUMEROS if _grande <= NUMERO_MAX_MM else CAPA_GRABADO
                    try:
                        if e.dxf.layer != _capa:
                            e.dxf.layer = _capa
                            e.dxf.color = 256        # 256 = el color de la capa
                            marcados += 1
                    except Exception:
                        pass
                    sin_tocar += 1
                    continue

                # AQUÍ NO SE BUSCAN HUECOS RAROS, Y ES A PROPÓSITO.
                # Anuar lo zanjó el 2026-08-06: *"si es un rectángulo, la cruz no
                # aplica; siempre es un rectángulo, basta con ver los machos de
                # ensamble"*. Y tiene razón medida: de los 361 rectángulos de la
                # casa de Bob Esponja, 286 miden exactamente el grosor.
                #
                # Lo que parecía una ranura en cruz eran DOS RECTÁNGULOS ENCIMADOS.
                # La rama que trataba huecos de forma libre fue justamente la que
                # destrozó los números grabados, así que se quitó del camino: una
                # hembra es un rectángulo y punto. Menos código, menos que romper.

                # Dientes PEGADOS al contorno: son los MACHOS. Anuar lo decidió el
                # 2026-08-06, y la razón es buena: *"a mano es más práctico
                # [dejarlos], por código es perfecto si los alargas"*. A mano
                # alargar 139 dientes no vale la pena; en código no cuesta nada y
                # la junta queda al ras en vez de hundida.
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                if max(xs) - min(xs) > viejo * 4 or max(ys) - min(ys) > viejo * 4:
                    contornos += 1
                    nuevos, cuantos = pts, 0
                    if tocar_machos:
                        nuevos, cuantos = _adaptar_dientes(pts, viejo, grosor_nuevo)
                    # LAS HEMBRAS TALLADAS EN EL CONTORNO SE AJUSTAN SIEMPRE.
                    # `tocar_machos` decide si se alargan los dientes —eso es
                    # opcional, Anuar a veces los deja—; pero el hueco donde
                    # entra la tabla NO es opcional: si queda angosto, no arma.
                    # Este paso no existía y por eso Calamardo salió pidiendo
                    # material de 1.4 mm (2026-08-11).
                    # Se pasa por CADA grosor del archivo. Las ranuras de la
                    # cabeza de toro no son huecos cerrados sino MUESCAS EN EL
                    # BORDE —la media madera, donde una tabla entra en la otra—
                    # y ese archivo trae dos juegos: el de 4.1 mm y el de 10.1.
                    # Con un solo grosor se ajustaba uno y el otro quedaba tal
                    # cual (2026-08-14). Un grosor que no existe en la pieza no
                    # encuentra nada y no estorba.
                    cuantas_h = 0
                    for _v in viejos:
                        nuevos, _n = _adaptar_ranuras_borde(
                            nuevos, _v, grosor_nuevo)
                        cuantas_h += _n
                    if cuantos or cuantas_h:
                        fallo = _reemplazar(msp, e, nuevos)
                        if fallo:
                            sin_tocar += 1
                            fallos.append(fallo)
                        else:
                            dientes += cuantos
                            ajustadas += cuantas_h
                    else:
                        sin_tocar += 1
                    continue
                sin_tocar += 1
                continue

            # Se abre a lo ancho SOBRE SU PROPIO EJE. Cada punto se empuja hacia
            # afuera medio delta, en la dirección del lado corto. Para una ranura
            # recta esto da exactamente lo mismo que antes; para una diagonal, da
            # lo correcto en vez de nada.
            ux, uy = eje
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            nuevos = []
            for p in pts:
                # De qué lado del centro está, medido a lo ancho de la ranura.
                d = (p[0] - cx) * ux + (p[1] - cy) * uy
                signo = 1.0 if d > 0 else -1.0
                v = list(p)
                v[0] = p[0] + ux * delta * signo
                v[1] = p[1] + uy * delta * signo
                nuevos.append(tuple(v))
            fallo = _reemplazar(msp, e, nuevos)
            if fallo:
                sin_tocar += 1
                fallos.append(fallo)
            else:
                ajustadas += 1

        if ajustadas + dientes == antes:
            break

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

    # NO SE CANTA VICTORIA SIN MEDIR LO QUE SE ESCRIBIÓ (2026-08-13).
    # Hasta hoy el ✅ salía del conteo interno de "cuántas toqué", que es la
    # opinión del propio motor. Ahora el archivo se vuelve a abrir y se mide.
    control = verificar_cambio(medidas_antes, salida, viejo, grosor_nuevo,
                               ajustadas + dientes)

    return {"status": "OK", "archivo": str(salida),
            "grosor_viejo": viejo, "grosor_nuevo": grosor_nuevo,
            "ranuras_ajustadas": ajustadas, "grabados_marcados": marcados, "dientes": dientes,
            "contornos": contornos, "escala": escala,
            "sin_tocar": sin_tocar,
            "control": control,
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
    # QUÉ PASÓ CON EL TAMAÑO, DE VERDAD. Antes esta línea decía siempre «el
    # tamaño NO cambió», escrito a mano — aunque se hubiera escalado al 50%.
    # Es el tipo de frase que hace dudar de todo lo demás: la herramienta hacía
    # bien su trabajo y luego mentía sobre él (2026-08-08).
    esc = r.get("escala", 1.0) or 1.0
    tam = ("el tamaño NO cambió" if abs(esc - 1.0) < 1e-9
           else f"y el diseño quedó al **{esc * 100:g}%**")

    # EL VEREDICTO MANDA SOBRE EL CONTEO INTERNO (2026-08-13). Si al medir el
    # archivo guardado siguen apareciendo ranuras del grosor viejo, no hay
    # palomita: se dice el número y se dice que no se corte. La casa de
    # Calamardo salió con ✅ y 59 ranuras sin ajustar; eso ya no puede pasar.
    ctrl = r.get("control") or {}
    # EL VEREDICTO NO BLOQUEA TODAVÍA, Y ESO ES A PROPÓSITO (2026-08-13).
    # La primera versión decía «⛔ NO LO CORTES» en cuanto quedara una sola
    # medida del grosor viejo. Probada contra el Crustáceo Cascarudo —la pieza
    # que Anuar SÍ cortó y armó— la reprobó: cuenta cualquier segmento que mida
    # como el grosor, y en una figura vectorizada hay cientos que son contorno
    # o grabado, no ensambles. O sea el criterio marca bueno lo malo y malo lo
    # bueno. Hasta calibrarlo (comparando el archivo ANTES contra el DESPUÉS,
    # que es una medida relativa y no exige saber qué es una ranura), esto
    # INFORMA y no decide. Bloquear con un criterio equivocado es peor que no
    # bloquear: le pararía cortes que sí sirven.
    if ctrl.get("veredicto") == "NO_CORTAR":
        aviso += (f"\n\n📏 Medición del archivo guardado (en calibración, "
                  f"todavía NO es un veredicto): quedaron "
                  f"**{ctrl['al_grosor_pedido']}** medidas de "
                  f"{ctrl['grosor_pedido']} mm y **{ctrl['al_grosor_viejo']}** "
                  f"que siguen midiendo {ctrl['grosor_viejo']} mm.\n"
                  "   Este conteo todavía no distingue una ranura de un tramo "
                  "de contorno que mide igual, así que **no lo tomes como que "
                  "está mal** — tómalo como que hay que revisar antes de cortar.")
    if ctrl.get("veredicto") == "NO_SE_PUDO_VERIFICAR":
        return (f"⚠️ Adapté de {r['grosor_viejo']} mm a {r['grosor_nuevo']} mm y "
                f"guardé el archivo, pero **no pude volver a abrirlo para "
                f"comprobarlo** ({ctrl.get('detalle', '')}).\n\n"
                f"📁 `{r['archivo']}`\n\n"
                "No te digo que está listo porque no lo verifiqué. "
                "Revísalo antes de cortar.")

    return (f"✅ Adaptado de **{r['grosor_viejo']} mm** a **{r['grosor_nuevo']} mm**\n"
            f"   {' y '.join(detalle) or 'nada'} · {tam}\n\n"
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

    # --escala 0.5  reduce el diseño a la mitad ANTES de ajustar las ranuras.
    # --de 3        dice de qué grosor venía, cuando la detección no lo saca.
    escala = 1.0
    if "--escala" in sys.argv:
        escala = float(sys.argv[sys.argv.index("--escala") + 1])
        if escala > 3:                      # lo dijo en porcentaje: 50
            escala /= 100.0
    viejo = 0.0
    if "--de" in sys.argv:
        viejo = float(sys.argv[sys.argv.index("--de") + 1])

    print(_texto(adaptar(ruta, float(args[1]), viejo, escala), ruta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
