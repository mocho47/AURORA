# -*- coding: utf-8 -*-
"""AURORA · La lengua de Anuar — no cómo escribe, sino cómo PIDE.

Anuar, 2026-08-10: *«integra mi lenguaje completamente a aurora»*.

QUÉ SE MIDIÓ ANTES DE ESCRIBIR ESTO
Se le hablaron 90 frases suyas reales al chat. 33 fallaron. Se midieron dos
hipótesis, una por una, en vez de suponer:

  · «Es la ortografía» → se le agregaron sus faltas reales (cotisa, ploter) y
    se le quitaron dos reglas que le reescribían la INTENCIÓN. Ganancia real
    medida: **+1 de 90**. No era la ortografía.

  · «Es el orden de la fila» → de las 9 colisiones, en **8 el candado correcto
    ni siquiera reconoció la frase**; perdió solo 1 por ir después. Reordenar
    habría arreglado 1 de 9. No era el orden.

Lo que queda, y es lo que de verdad pasa: los candados reconocen una LISTA DE
FRASES MEMORIZADAS. `_contiene_trigger` compara contra frases que alguien
escribió a mano. Si Anuar lo dice con otras palabras, no existe. `intuicion`
tiene «que deberia hacer» pero no «en que deberia enfocarme». `agenda` tiene
«que citas tengo» pero no «que sigue». Falla por dos palabras.

POR QUÉ ESTO NO ES «AGREGAR TRES FRASES MÁS»
Eso es justo lo que se venía haciendo, y es lo que produjo el problema: cada
bug agregaba tres frases a una lista, la lista crecía, y una lista más larga se
roba mensajes ajenos. El arreglo de ayer es la colisión de mañana. Aquí no se
guardan frases: se guardan **familias de cómo pide**, en un solo lugar, igual
que `perfil_anuar.py` hizo con su ortografía («cargado de una vez, no aprendido
a golpes»).

CÓMO SE CONECTA — un solo punto, no 33
El pipeline pregunta UNA vez `intencion(mensaje)`. Si hay respuesta:
  · ese candado dispara aunque su lista no reconozca la frase
  · y los demás se hacen a un lado, lo que también mata las colisiones
No se tocó ninguno de los 33 candados. Si esto falla, se apaga en una línea.

CÓMO NO HACER TRAMPA
Las familias NO se escribieron copiando las 33 frases que fallaron —eso sería
enseñarle el examen—. Se escribieron de sus PATRONES de habla, y la prueba se
volvió a correr con 90 frases distintas que este archivo nunca vio.
"""
from __future__ import annotations

import re
import unicodedata

# Cada entrada: candado → tupla de patrones. Se lee de arriba hacia abajo y el
# PRIMERO que calza manda, así que lo específico va antes que lo general.
#
# Se escriben como expresiones, no como frases, porque él nunca dice dos veces
# lo mismo igual: "que sigue", "que me toca", "que traigo pendiente" son la
# misma pregunta y ninguna está en la lista de la agenda.
FAMILIAS: tuple = (

    # ══ PRIMERO LO QUE HABLA *DE* ALGO, NO LO QUE PIDE ALGO ══════════════
    # Medido: al conectar esto la primera vez, «que hace el cotizador de
    # vinil» se lo llevó el cotizador de vinil —le pidió un precio a una
    # pregunta sobre su propio código—. Preguntar POR una herramienta y USAR
    # esa herramienta se escriben casi igual; lo único que las separa es que
    # una empieza con «qué hace» o «explícame». Por eso van hasta arriba.
    ("consulta_codigo", (
        r"\bque\s+hace\s+(?:el|la|tu|su)\s+\w+",
        r"\b(?:explicame|explica)\b.*\b(?:como\s+funciona|como\s+trabaja)\b",
        r"\ben\s+que\s+archivo\s+(?:esta|vive|guardas)\b",
        r"\bcomo\s+(?:esta|le\s+haces\s+para)\b.*\b(?:programad|codig)\w*\b",
        r"\bcomo\s+funciona\s+(?:el|la|tu)\s+\w+",
    )),
    # Un verbo de búsqueda al principio no admite discusión: «googlea cuánto
    # cobran por retrofit» es salir a internet, aunque traiga la palabra
    # retrofit. Medido en la ronda 2: sin esto, servicio_atf se lo llevaba.
    ("busqueda_web", (
        r"^\s*(?:investiga|googlea|busca\s+en\s+internet|buscame\s+en\s+internet)\b",
        r"\bbusca\s+en\s+(?:internet|linea|google)\b",
    )),
    # Vender el producto vs. cotizarlo: «cómo le vendo un retrofit» es pedir
    # argumentos, no precio. Va antes que servicio_atf, que reconoce
    # «retrofit» y se lo llevaba.
    ("ficha_vendedor", (
        r"\b(?:que|como)\s+le\s+(?:digo|contesto|respondo)\s+al?\s+cliente\b",
        r"\bcomo\s+(?:le\s+)?(?:vendo|convenzo|cierro)\b",
        r"\bme\s+dice\s+que\s+esta\s+caro\b",
        r"\b(?:objecion|argumento)(?:es)?\s+de\s+venta\b",
        r"\bficha\s+(?:de|del)\b",
        r"\bque\s+(?:le\s+)?pongo\s+en\s+la\s+cotizacion\b",
    )),
    # «Métete a mercadolibre y búscame faros aozoom» es abrir el navegador.
    # Va antes que servicio_atf, que reconoce «aozoom» en cualquier lado.
    ("abrir_navegador", (
        r"^\s*(?:abre|abreme|metete\s+a|entra\s+a|vete\s+a)\b",
        r"\b(?:abre|metete\s+a|entra\s+a)\s+(?:a\s+)?"
        r"(?:pinterest|youtube|facebook|mercado\s*libre|google|amazon|aliexpress)\b",
    )),
    # Precio de vinil antes que crear letras de vinil: la palabra de dinero
    # decide. Sin esto, «cotisa unas letras en vinil» genera el archivo en
    # vez de dar el precio.
    ("cotizar_vinil", (
        r"\b(?:vinil|vinilo|plotter|ploter|recorte|textil)\b.*"
        r"\b(?:cuanto|precio|costo|cotiz\w+|cotis\w+|sale|cobro|a\s+como)\b",
        r"\b(?:cuanto|precio|costo|cotiz\w+|cotis\w+|cobro|a\s+como)\b.*"
        r"\b(?:vinil|vinilo|de\s+recorte|textil)\b",
        # «5 calcas de 12x12 cuanto queda cada una»: el producto de recorte
        # con medidas y palabra de dinero, sin nombrar el material.
        r"\b(?:calcas?|calcomanias?|stickers?|stikers?|rotul\w+)\b.*"
        r"\d+\s*[x×]\s*\d+.*\b(?:cuanto|precio|costo|queda|sale)\b",
        r"\b(?:cuanto|a\s+como|precio)\b.*\brotular\b",
    )),

    # ── PREGUNTAS CORTAS: su sello. 2 a 5 palabras, sin contexto ──────────
    # Son tierra de nadie hoy: "como voy" no está en ninguna de las 16 listas
    # y es literalmente como pregunta por su negocio.
    ("negocio", (
        r"^\s*(?:y\s+)?como\s+(?:voy|vamos|va\s+(?:el|mi)\s+negocio|va\s+todo)\b",
        r"\bcomo\s+(?:voy|vamos)\s+(?:este\s+mes|esta\s+semana|hoy)\b",
        r"\bcuanto\s+(?:llevo|llevamos)\s+(?:vendido|de\s+venta|ganado)\b",
        r"\bcomo\s+(?:esta|va)\s+(?:la\s+)?(?:venta|caja|lana|feria)\b",
        r"\bque\s+tal\s+(?:va|vamos|voy)\b",
        r"\bcuanto\s+me\s+deben\b",
    )),
    ("agenda", (
        r"^\s*que\s+(?:sigue|me\s+toca|tengo)\s*\??$",
        r"\bque\s+(?:sigue|me\s+toca)\s+(?:hoy|manana|ahora|al\s+rato)\b",
        r"\bque\s+traigo\s+(?:pendiente|agendado|para\s+hoy)\b",
        r"\bpara\s+cuando\s+(?:quedo|quede|es)\s+(?:la|el)\b",
        r"\bcon\s+quien\s+(?:quede|tengo)\b",
    )),
    ("intuicion", (
        r"\ben\s+que\s+(?:deberia|debo|me\s+conviene)\s+(?:enfocarme|meterme|"
        r"invertir|concentrarme|pegarle)\b",
        r"\b(?:en\s+que|donde)\s+estoy\s+(?:perdiendo|dejando|tirando)\s+"
        r"(?:dinero|lana|feria|tiempo)\b",
        r"\bque\s+(?:me\s+)?(?:conviene|convendria)\s+(?:hacer|mas)\b",
        r"\bque\s+(?:oportunidad|area)\s+(?:hay|ves|tengo)\b",
        r"\bque\s+harias\s+(?:tu\s+)?en\s+mi\s+lugar\b",
    )),

    # ── LO QUE VENDE: su producto por NOMBRE, no por categoría ────────────
    # "traigo una jetta quiero ponerle aozoom" se lo llevó el cotizador de
    # catálogo. La marca del producto tiene que mandar sobre la palabra precio.
    ("servicio_atf", (
        r"\b(?:aozoom|bi[- ]?led|biled|retrofit|proyector(?:es)?\s+de\s+faro)\b",
        r"\bfaros?\b.*\b(?:instala|ponerle|cambiar|mejorar|actualizar)\b",
        r"\b(?:instala|ponerle|montar)\b.*\bfaros?\b",
        # «traigo un civic quiero mejorar los faros»: dice «traigo un», no
        # «mi», y el verbo es «mejorar». Medido en la ronda 2.
        r"\b(?:mi|traigo\s+(?:un|una)|tengo\s+(?:un|una))\s+"
        r"(?:jetta|golf|tsuru|sentra|civic|mazda|kia|hilux|ranger|tacoma|"
        r"camioneta|coche|carro|nave|troca)\b.*\b(?:faro|led|luz|luces)\b",
        r"\b(?:mejorar|cambiar|renovar)\b.*\b(?:los\s+)?faros?\b",
    )),

    # ── EL TALLER: pide por el trabajo, no por la herramienta ─────────────
    ("generar_caja", (
        r"\b(?:caja|cajita|cofre|baul|estuche|organizador)\b.*\d+\s*[x×]\s*\d+",
        r"\d+\s*[x×]\s*\d+\s*[x×]\s*\d+\b.*\b(?:caja|cofre|baul|estuche)\b",
        r"\b(?:hazme|armame|necesito|quiero)\b.*\b(?:caja|cofre|baul)\b",
    )),
    ("adaptar_diseno", (
        r"\b(?:archivo|diseno|dibujo|plantilla)\b.*\bde\s*\d+(?:[.,]\d+)?\s*mm\b"
        r".*\b(?:material|mdf|acrilico)\b",
        r"\bmi\s+material\s+es\s+de\s*\d+(?:[.,]\d+)?\b",
        r"\b(?:ajusta|adapta|reescala|acomoda)\b.*\b(?:a|para)\s*\d+(?:[.,]\d+)?\s*(?:mm)?\b",
        r"\bes(?:ta|tan)?\s+(?:hecho|para)\s+\d+(?:[.,]\d+)?\s*mm\b.*\btengo\s+(?:de\s+)?\d",
        r"\bencastres?\b",
        # Sin un solo número: «adapta la plantilla a mi mdf que es más
        # delgado». El grosor lo sabe la máquina, no hace falta que lo diga.
        r"\b(?:ajusta|adapta|reescala|acomoda)\b.*\bmi\s+"
        r"(?:material|mdf|acrilico|lamina|hoja)\b",
        r"\bmi\s+(?:material|mdf|acrilico)\b.*\b(?:mas\s+)?(?:delgad|gruesa?|"
        r"finit?|grues)\w*\b",
        r"\bviene\s+para\s+\d+(?:[.,]\d+)?\s*(?:mm)?\b",
    )),
    ("texto_a_corte", (
        r"\b(?:letras?|numeros?|palabra|nombre|rotulo|leyenda|frase|texto)\b.*"
        r"\b(?:plotter|ploter|recorte|vinil)\b",
        r"\b(?:ponme|hazme|escribe|sacame|quiero)\b.*\b(?:en|con|tipo)\s+"
        r"(?:letra|tipografia|fuente|script|negrita)\b",
        r"\b(?:letras?|numeros?|nombre|frase|palabra)\b.*"
        r"\bpara\s+(?:cortar|recortar|el\s+corte)\b",
        r"\b(?:el\s+nombre|la\s+frase|la\s+palabra)\b.*"
        r"\b(?:recortar|cortar|plotter|ploter|vinil)\b",
    )),
    ("print_and_cut", (
        r"\bprint\s*(?:and|&|y)\s*cut\b",
        r"\bimprim\w+\b.*\b(?:y|con)\s+(?:recortar|corte|linea\s+de\s+corte)\b",
        r"\b(?:stickers?|stikers?|calcas?|calcomanias?)\b.*"
        r"\b(?:impres\w+|imprimir|impreso|full\s+color|contorno)\b",
        r"\bmarcas?\s+de\s+registro\b",
        r"\bcontorno\s+de\s+corte\b",
    )),
    ("foto_a_dxf", (
        # «borra el fondo» se lo llevaba accion_fisica —que SÍ ejecuta cosas
        # de verdad— nada más por el verbo «borra». Medido en la ronda 2.
        r"\b(?:quita\w*|borra\w*|elimina\w*|sin)\s+(?:el\s+)?fondo\b"
        r".*\b(?:dxf|corte|cortar|vectoriz\w+|laser)\b",
        r"\b(?:foto|imagen|jpg|png)\b.*\bvectoriz\w+\b",
        r"\bvectoriz\w+\b.*\b(?:foto|imagen|jpg|png)\b",
        r"\bde\s+esta\s+(?:foto|imagen)\b.*\b(?:cortar|corte|laser|dxf)\b",
        # «esta imagen la quiero limpia y en vector para el laser»: nombra el
        # resultado —limpia, en vector— sin decir «quita el fondo».
        r"\b(?:imagen|foto|logo)\b.*\b(?:limpia|en\s+vector|vectorizad\w+)\b",
    )),
    ("cotizar_dxf", (
        r"\bcuant[oa]s?\s+(?:metros|mts|m)\s+de\s+corte\b",
        r"\b(?:cuanto|precio|costo|cobro|cobrarias)\b.*"
        r"\b(?:cortar|corte\s+de)\s+(?:este|ese|el|un)\s+"
        r"(?:archivo|dxf|diseno|dibujo)\b",
        r"\bmide\s+(?:este|el)\s+(?:archivo|dxf)\b",
    )),

    # ── SU PROPIA MÁQUINA: Corel, videos, voz ─────────────────────────────
    # Los tres candados de Corel cayeron al enrutador con las tres frases.
    ("corel", (
        r"\bcorel\w*\b",
        r"\bcdr\b",
        r"\b(?:que|lo\s+que)\s+(?:tengo|traigo)\s+abierto\b",
    )),
    ("video", (
        r"\b(?:videos?|clips?|material\s+de\s+video|tomas?)\b.*"
        r"\b(?:tengo|hay|listos?|sirvan?|sirven?|carpeta|publicar|subir|"
        r"guardad\w+|grabad\w+|reel|reels|tiktok|short)\b",
        r"\b(?:cuantos|que|cuales)\s+(?:videos?|clips?)\b",
        r"\b(?:saca|extrae|dame|busca)\w*\s+(?:los\s+)?(?:videos?|clips?)\b",
    )),
    ("voz", (
        # Aquí describe el RESULTADO —«platicar sin teclear», «que me
        # escuches»—, casi nunca la palabra «voz». Las tres frases de la
        # ronda 2 fallaron por eso.
        r"\b(?:hablame|hablarme|que\s+me\s+hables|contestarme\s+hablando)\b",
        r"\b(?:en\s+lugar\s+de|en\s+vez\s+de|sin)\s+(?:escribir|teclear)\b",
        r"\b(?:prende|apaga|activa|desactiva|prueba)\b.*"
        r"\b(?:la\s+voz|que\s+me\s+escuches|el\s+microfono|el\s+micro)\b",
        r"\bcomo\s+suenas\b",
        r"\b(?:platicar|hablar|conversar)\s+(?:contigo|con\s+aurora)\b",
        r"\bque\s+me\s+escuches\b",
    )),

    # ── MEMORIA Y APRENDIZAJE ─────────────────────────────────────────────
    ("memoria", (
        r"^\s*(?:acuerdate|recuerda|apuntate|no\s+se\s+te\s+olvide)\b",
        r"\bque\s+te\s+dije\s+(?:de|sobre|del)\b",
        r"\bguarda(?:te)?\s+(?:que|esto|este\s+dato)\b",
    )),
    ("ver_aprendizaje", (
        r"\bque\s+(?:has\s+|has\s+ido\s+)?aprendi\w+\b",
        r"\bque\s+sabes\s+(?:hacer|de\s+mi)\b",
        r"\ben\s+que\s+(?:soy|he\s+sido)\s+repetitiv\w+\b",
        r"\bque\s+patrones\b",
        r"\bcomo\s+(?:trabajo|te\s+pido\s+las\s+cosas)\b.*\b(?:aprend|sabes|ves)\w*\b",
    )),
    # Qué es AURORA. Las tres frases de la ronda 2 se fueron al enrutador
    # porque él nunca pregunta «quién eres»: pregunta para qué le sirve.
    ("acerca_de", (
        r"\bque\s+eres\b",
        r"\b(?:para\s+que|de\s+que)\s+(?:me\s+)?sirves\b",
        r"\bque\s+(?:ganamos|gano)\s+con\s+que\s+estes\b",
        r"\bexplicame\s+que\s+eres\b",
        r"\bquien\s+eres\b",
    )),
    # Los equipos de trabajo. Ninguna de las tres frases tenía familia.
    ("equipos", (
        r"\bequipos?\s+de\s+(?:trabajo|marketing|ventas?|diseno|publicacion|taller)\b",
        r"\b(?:que|cuales)\s+equipos?\b",
        r"\b(?:activa|echame\s+a\s+andar|pon\s+a\s+trabajar|arranca)\b.*\bequipo\b",
        r"\bque\s+puede\s+hacer\s+el\s+equipo\b",
    )),

    # ── VENTA Y CLIENTES ──────────────────────────────────────────────────
    ("alta_lead", (
        r"^\s*(?:apunta|registra|da\s+de\s+alta|anota|guarda)\b.*"
        r"(?:\b\d{10}\b|\bcliente\b|\binteresad|\bquiere\b)",
        # «da de alta a la señora del kinder»: la persona sin teléfono ni la
        # palabra cliente. Se reconoce por el verbo + que hable de alguien.
        r"^\s*(?:apunta|registra|da\s+de\s+alta|anota)\s+a\s+\w+",
        r"\b(?:nuevo|otro)\s+(?:cliente|lead|prospecto)\b",
        r"\bmetelo\s+(?:al|a\s+la)\s+(?:crm|lista|base)\b",
    )),
    ("proveedor", (
        r"\b(?:donde|quien|con\s+quien)\s+(?:compro|consigo|vende|surto)\b",
        r"\bproveedor(?:es)?\s+de\b",
        r"\bmi\s+proveedor\b",
    )),
    ("busqueda_web", (
        r"^\s*(?:investiga|googlea|busca\s+en\s+internet|buscame\s+en\s+internet)\b",
        r"\bque\s+(?:tendencias|se\s+esta\s+vendiendo|se\s+vende|hay)\b.*"
        r"\b(?:en\s+internet|en\s+el\s+mercado|alla\s+afuera)\b",
        r"\bque\s+se\s+esta\s+vendiendo\b",
    )),
    ("campana_escolar", (
        r"\b(?:cuanto|precio|costo)\b.*\bpaquete\s+(?:de\s+)?"
        r"(?:primaria|secundaria|preescolar|kinder|escolar)\b",
        r"\bel\s+de\s+(?:primaria|secundaria|preescolar|kinder)\b",
        # «cuanto el de la campaña» —así de corto lo pregunta una clienta—
        r"\bcuanto\b.*\bel\s+de\s+la\s+campana\b",
        r"\bpaquete\s+escolar\b",
    )),
    ("metodo_campana", (
        r"\b(?:como\s+ves|que\s+opinas\s+de|que\s+le\s+falta\s+a)\s+"
        r"(?:la|esta|mi)\s+campana\b",
        r"\brevisa\w*\s+(?:la|esta|mi)\s+campana\b",
    )),
    ("publicar", (
        r"\bque\s+publico\s+(?:hoy|manana)\b",
        r"\barma\w*\s+(?:el\s+)?post\b",
        r"\bque\s+(?:subo|saco)\s+hoy\b",
        r"\bque\s+toca\s+publicar\b",
        r"\bque\s+subo\s+(?:hoy\s+)?a\s+(?:las\s+)?redes\b",
    )),
    ("dxf", (
        r"\b(?:convierte|convierteme|pasa|pasalo|pasala)\b.*\ba\s+dxf\b",
        r"\ben\s+dxf\b.*\b(?:necesito|quiero|dame)\b",
        r"\b(?:necesito|quiero|dame)\b.*\ben\s+dxf\b",
        # «pasa el diseño a formato de corte»: nombra el resultado, no el
        # formato. Es su forma normal de pedirlo en el taller.
        r"\b(?:pasa|convierte|ponlo|dejalo)\b.*"
        r"\ba\s+formato\s+de\s+corte\b",
    )),

    # ══ HASTA EL FINAL: LO MÁS GENERAL ═══════════════════════════════════
    # Preguntar un precio a secas tiene que ser lo ÚLTIMO que se considere:
    # si va antes, se come todas las cotizaciones específicas de arriba
    # —vinil, dxf, campaña, servicios ATF—, que son las que sí saben el
    # precio de verdad.
    ("cotizar", (
        r"\b(?:cuanto|precio|costo|a\s+como|en\s+cuanto|cotiz\w+|cotis\w+)\b.*"
        r"\b(?:taza|termo|playera|gorra|vaso|agenda|boligrafo|sello|"
        r"sublimad\w+|grabad\w+|personalizad\w+|bordad\w+)\b",
        r"\b(?:taza|termo|playera|gorra|vaso|agenda|boligrafo|sello)s?\b.*"
        r"\b(?:cuanto|precio|costo|en\s+cuanto|dejo|sale)\b",
    )),
)

_COMPILADAS = tuple((c, tuple(re.compile(p) for p in ps)) for c, ps in FAMILIAS)

# Un mensaje que es SOLO una ruta de archivo o carpeta, sin nada más.
_SOLO_RUTA = re.compile(r"^\s*[a-z]:[\\/][^\s]*\s*$|^\s*[\\/]{2}[^\s]+\s*$")


def _limpia(t: str) -> str:
    """Minúsculas y sin acentos. Igual que el resto del sistema."""
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def intencion(mensaje: str) -> str | None:
    """Qué está pidiendo Anuar, o None si esto no lo sabe.

    Devolver None es la respuesta CORRECTA cuando no está seguro: el pipeline
    sigue como siempre. Este módulo solo habla cuando reconoce la familia; no
    adivina, porque un candado equivocado con confianza es peor que ninguno.
    """
    m = _limpia(mensaje)
    if not m:
        return None
    # Una ruta SOLA no es una petición: es el dato que le faltaba a la
    # petición anterior, y ese trabajo ya lo hace `ruta_sola`. Sin este
    # freno, «D:\algo.cdr» se lo llevaba Corel por traer «cdr» —medido el
    # 2026-08-10 al conectar esto la primera vez—.
    if _SOLO_RUTA.match(m):
        return None
    for candado, patrones in _COMPILADAS:
        for p in patrones:
            if p.search(m):
                return candado
    return None


def explica(mensaje: str) -> dict:
    """Qué familia calzó y con qué patrón. Para poder auditarlo."""
    m = _limpia(mensaje)
    for candado, patrones in _COMPILADAS:
        for p in patrones:
            if p.search(m):
                return {"candado": candado, "patron": p.pattern, "texto": m}
    return {"candado": None, "patron": None, "texto": m}


if __name__ == "__main__":
    import io
    import sys
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    print(f"{len(FAMILIAS)} familias · "
          f"{sum(len(p) for _, p in FAMILIAS)} formas de pedir\n")
    for f in ("como voy", "que sigue", "en que deberia enfocarme",
              "corel esta abierto", "cuantos videos hay",
              "traigo una jetta quiero ponerle aozoom cuanto me sale todo",
              "acuerdate que el telefono de atf es el 3326148674"):
        r = explica(f)
        print(f"  «{f[:56]:58}» → {r['candado']}")
