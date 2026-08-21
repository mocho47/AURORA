# -*- coding: utf-8 -*-
"""
AURORA · VALIDADOR DE HONESTIDAD (candado estructural anti-simulación)
======================================================================

POR QUÉ EXISTE
--------------
Durante el 29 y 30 de julio de 2026, AURORA inventó cosas SIETE veces, todas
por la misma causa de fondo: cuando la frase del usuario no calzaba con un
candado exacto, el mensaje caía a un modelo de IA que NO tiene acceso al
sistema — pero respondía igual, como si lo tuviera. Casos reales:

  · Dijo "CorelDRAW: PDF cargado correctamente... Vectorización finalizada...
    resultado: vectorizado_con_coreldraw.pdf". Ese archivo nunca existió.
  · Generó un "MANUAL MAESTRO DE COMANDOS" con 6 de 8 comandos INVENTADOS
    (AGENDA/agrega_usuario, CORE/evalua_expresion... ninguno existe).
  · Generó un "kit de configuración crítica" que mandaba ejecutar
    REINICIAR_NGROK.bat, OPTIMIZAR_PC.bat y NEXUS.bat — los tres inexistentes.
  · Inventó capacidades suyas (diseño de interiores, ciencia) al describirse.

Agregar frases al enrutador una por una es infinito: siempre habrá una forma
de decir las cosas que nadie anticipó. La corrección de RAÍZ no es adivinar
mejor las frases — es hacer **estructuralmente imposible que AURORA afirme
algo que no puede comprobar**. Aunque no entienda la orden, lo peor que puede
pasar es un "no te entendí", nunca una mentira.

CÓMO FUNCIONA
-------------
Esto es CÓDIGO, no una instrucción de prompt. Un modelo chico ignora las
reglas del prompt (pasó de verdad, varias veces); este candado no se puede
ignorar porque corre después, sobre el texto ya escrito, antes de que salga.

Tres comprobaciones, todas contra la realidad:
  1. ¿Afirma haber EJECUTADO algo, sin que se haya ejecutado nada real?
  2. ¿Menciona comandos/herramientas que no están en el registro real?
  3. ¿Menciona archivos que no existen en el disco?

Nunca borra la respuesta: le agrega una corrección visible y honesta, para
que Anuar vea qué se dijo y por qué no es confiable.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# ── 1. Afirmaciones de acción CUMPLIDA ───────────────────────────────────
# Solo pasado/consumado. "voy a", "puedo", "te lo hago" son promesas, no
# afirmaciones falsas — esas no se tocan.
_AFIRMA_ACCION = (
    r"\bya (?:lo |la |los |las )?(?:hice|abrí|abri|guardé|guarde|envié|envie|"
    r"convertí|converti|creé|cree|moví|movi|copié|copie|publiqué|publique|"
    r"exporté|exporte|instalé|instale|borré|borre|eliminé|elimine)\b",
    r"\b(?:he|hemos) (?:creado|generado|guardado|enviado|convertido|abierto|"
    r"exportado|publicado|movido|copiado|instalado|borrado|eliminado)\b",
    r"\b(?:archivo|documento|pdf|dxf|svg|imagen|reporte|catálogo|catalogo) "
    r"(?:ya )?(?:fue |ha sido |se ha |está |esta )?(?:generado|creado|guardado|"
    r"exportado|convertido)\b",
    r"\b(?:conversión|conversion|vectorización|vectorizacion|exportación|exportacion|"
    r"publicación|publicacion|instalación|instalacion) (?:finalizada|completada|"
    r"terminada|exitosa|lista)\b",
    r"\bse (?:ha |han )?(?:guardado|generado|creado|enviado|exportado|publicado)\b",
    r"\b(?:listo|hecho)[:,]\s*(?:el |la |tu )?(?:archivo|pdf|dxf|documento)\b",
    r"\bcargado correctamente\b",
    r"\bresultado:\s*\S+\.(?:pdf|dxf|svg|png|jpg|cdr|xlsx|docx|zip|bat|exe)\b",
)

# ── 2. Nombres de comandos/herramientas ──────────────────────────────────
# Formato real del registro: CARPETA/modulo:funcion  (ej. AGENDA/agenda:crear_cita)
# También se captura CARPETA/algo por si inventa la forma corta.
_RE_COMANDO = re.compile(r"\b([A-Z][A-Z_]{2,20})/([a-zA-Z_][\w]*)(?::([a-zA-Z_][\w.]*))?")

# ── 3. Archivos mencionados como si existieran ───────────────────────────
# El lookahead final NO es cosmético. Sin él, un nombre con punto en medio
# —como los de las cajas, que llevan el grosor: "ClosedBox_20x15_2.7mm.svg"—
# cortaba la ruta en el "2.7mm" y juzgaba un archivo que nunca existió, mientras
# el verdadero estaba ahí con sus 75 KB. Como TODAS las cajas llevan el grosor
# en el nombre, el aviso falso salía siempre. (Anuar lo pegó el 2026-08-05; el
# origen apareció al escribirle la prueba de regresión.)
_RE_RUTA = re.compile(r"[A-Za-z]:\\[^\r\n\"'<>|]+?\.[A-Za-z0-9]{2,5}(?![\w.])")
# Rutas que vienen dentro de un JSON con las barras escapadas se parten a la
# mitad y quedan como "C:\\AURORA.workt" — un fragmento que obviamente no existe.
# Encontrado en el barrido del 2026-08-02: le puso "⚠️ este archivo no existe"
# a una respuesta que era verdadera. Un candado que marca lo bueno como falso
# es peor que no tenerlo: se vuelve ruido y se ignora.
_RE_RUTA_PARTIDA = re.compile(r"\\\\|\.\w{1,5}$")
# Sin espacios a proposito: con [\w\-. ] el regex se comia las palabras de antes
# y reportaba "Si el sistema se congela ejecuta REINICIAR_NGROK.bat" como si ese
# fuera el nombre del archivo. Detectaba bien, pero el aviso quedaba ilegible.
_RE_ARCHIVO_SUELTO = re.compile(r"\b([\w\-.]{2,60}\.(?:bat|exe|ps1|py|dxf|svg|cdr))\b", re.I)

# Motores que SOLO escriben texto: no tienen manos, no ejecutan nada.
# Si la respuesta viene solo de estos, cualquier afirmación de acción es falsa.
_MOTORES_SIN_MANOS = {
    "motor_analisis", "conversacional", "razonador", "motor_reasoning",
    "motor_coaching", "motor_negocios", "chat", "llm", "groq",
}


def _hubo_ejecucion_real(motores_usados) -> bool:
    """True si la respuesta vino de algo que SÍ puede ejecutar (un candado
    directo o el router universal ejecutando una herramienta)."""
    if not motores_usados:
        return False
    usados = {str(m).strip().lower() for m in motores_usados}
    return bool(usados - _MOTORES_SIN_MANOS)


def _comandos_inventados(texto: str, registro_claves) -> List[str]:
    """Comandos con formato de herramienta que NO están en el registro real."""
    if not registro_claves:
        return []
    # Solo se juzgan carpetas que EXISTEN de verdad en el registro. Sin esto el
    # regex marcaba "PDF/CDR" y "PNG/JPG" como comandos inventados (encontrado en
    # vivo 2026-07-31): son formatos de archivo, no comandos. Un candado que da
    # avisos falsos se vuelve ruido, se ignora, y deja de servir para lo que existe.
    carpetas_reales = {k.split("/", 1)[0] for k in registro_claves if "/" in k}
    if not carpetas_reales:
        return []

    inventados, vistos = [], set()
    for m in _RE_COMANDO.finditer(texto):
        carpeta, modulo, funcion = m.group(1), m.group(2), m.group(3)
        mencion = m.group(0)
        if mencion in vistos or carpeta not in carpetas_reales:
            continue
        vistos.add(mencion)
        # Se acepta si existe tal cual, o si algo del registro empieza igual
        # (para no marcar como falso un "MARKETING/plan_monetizacion" válido
        # citado sin la función).
        prefijo = f"{carpeta}/{modulo}"
        if any(k == mencion or k.startswith(prefijo) for k in registro_claves):
            continue
        inventados.append(mencion)
    return inventados


def _archivos_inexistentes(texto: str, pregunta: str = "") -> List[str]:
    """Archivos que la respuesta menciona pero que no están en el disco.

    `pregunta` es lo que escribió el usuario. Se usa para no acusar de
    inventado un archivo que ÉL acaba de dar con su ruta completa.
    """
    faltantes, vistos = [], set()
    # CUARTO FALSO POSITIVO DEL MISMO TIPO (2026-08-14): Anuar pidió cotizar
    # `C:\...\Downloads\DXF\happybirth.dxf`. El cotizador contestó con el
    # nombre corto —`happybirth.dxf`, que es lo correcto— y la regla de
    # "archivo suelto" lo buscó SOLO dentro de la carpeta de AURORA. Como sus
    # diseños viven en Descargas, salía "este archivo no existe" pegado a una
    # cotización correcta. Los tres arreglos anteriores miraban solo la
    # respuesta; el dato que faltaba estaba en la pregunta.
    de_la_pregunta = set()
    for r in _RE_RUTA.findall(pregunta or ""):
        r = r.strip().rstrip(".,;:)\"'")
        try:
            if Path(r).exists():
                de_la_pregunta.add(Path(r).name.lower())
        except OSError:
            continue

    # Y los EJEMPLOS que la propia AURORA escribe para enseñar a pedir las
    # cosas: «así te lo entiendo: ajusta C:\ruta\casa.dxf al 50%». Esa ruta no
    # existe porque NO ES UNA PROMESA, es un molde. El aviso salía pegado a la
    # explicación y la contradecía (visto en vivo 2026-08-14).
    _EJEMPLO = re.compile(
        r"(?:^|\n)\s*_?(?:as[íi] te lo entiendo|d[íi]melo as[íi]|"
        r"ejemplo|por ejemplo|as[íi] me lo pides|cont[ée]stame)\b[^\n]*",
        re.I)
    for linea in _EJEMPLO.findall(texto):
        for r in _RE_RUTA.findall(linea):
            vistos.add(r.strip().rstrip(".,;:)\"'"))
        for n in _RE_ARCHIVO_SUELTO.findall(linea):
            vistos.add(n.strip())
    # Los nombres de archivo que YA se comprobaron en disco. Sirve para no
    # juzgar dos veces la misma cosa por caminos distintos.
    confirmadas = []
    for ruta in _RE_RUTA.findall(texto):
        ruta = ruta.strip().rstrip(".,;:)")
        if ruta in vistos:
            continue
        vistos.add(ruta)
        # Si la ruta trae barras dobles, viene de un JSON escapado y está
        # partida: no se juzga un fragmento como si fuera un archivo real.
        if "\\\\" in ruta or len(Path(ruta).name) < 5:
            continue
        try:
            if not Path(ruta).exists():
                faltantes.append(ruta)
            else:
                # FALSO POSITIVO ENCONTRADO POR ANUAR (2026-08-05): generó una
                # caja, el SVG quedó bien escrito FUERA del proyecto (Descargas),
                # y abajo la regla de "archivo suelto" volvía a agarrar el mismo
                # nombre —ya sin su ruta— y como no estaba dentro de AURORA lo
                # marcaba "no existe". El archivo sí existía, con 75 KB.
                # Se apunta el nombre como ya resuelto para que no se juzgue dos
                # veces la misma cosa con distinta vara.
                vistos.add(Path(ruta).name)
                confirmadas.append(Path(ruta).name.lower())
        except OSError:
            faltantes.append(ruta)
    # Archivos sueltos tipo "REINICIAR_NGROK.bat": se buscan en la raíz del proyecto.
    for nombre in _RE_ARCHIVO_SUELTO.findall(texto):
        nombre = nombre.strip()
        if nombre in vistos or "\\" in nombre or "/" in nombre:
            continue
        vistos.add(nombre)
        # ¿Es solo un pedazo de un archivo que ya se comprobó que existe?
        # Los archivos de Anuar traen espacios en el nombre —"crustacio
        # cascarudo __2.5mm.dxf"— y este regex, que no acepta espacios, agarra
        # nada más el último trozo: "__2.5mm.dxf". Ese trozo no existe como
        # archivo, claro, y salía el aviso de "no existe" sobre un archivo que
        # sí estaba, recién escrito. Encontrado en vivo el 2026-08-06, y es la
        # tercera variante del mismo falso positivo.
        if any(c.endswith(nombre.lower()) for c in confirmadas):
            continue
        # ¿Es el archivo que el propio Anuar acaba de pasar con su ruta?
        if nombre.lower() in de_la_pregunta:
            continue
        if _es_libreria(nombre):
            continue
        try:
            if not (RAIZ / nombre).exists() and not list(RAIZ.glob(f"**/{nombre}"))[:1]:
                faltantes.append(nombre)
        except OSError:
            pass
    return faltantes


def _es_libreria(nombre: str) -> bool:
    """¿Es el nombre de una librería instalada, no un archivo prometido?

    El otro falso positivo del mismo caso: la respuesta decía "boxes.py exporta
    SVG" —hablando de la LIBRERÍA— y el validador la buscó como archivo. Como
    boxes es un paquete (boxes/__init__.py) y no un boxes.py suelto, la marcó
    como inventada. Mencionar una librería no es prometer un archivo.
    """
    if not nombre.lower().endswith(".py"):
        return False
    try:
        import importlib.util
        return importlib.util.find_spec(nombre[:-3]) is not None
    except (ImportError, ValueError, ModuleNotFoundError, AttributeError):
        return False


# Formas de dar por hecho lo que se estaba PREGUNTANDO. La trampa es que suenan
# naturales y útiles: "con el plugin instalado, podemos...". Nadie dijo que
# estuviera instalado.
_DA_POR_HECHO = (
    r"\bcon (?:el|la|los|las) [\w\s]{2,30} (?:instalad|activad|configurad|conectad|habilitad)",
    r"\bya que (?:tienes|cuentas con|dispones de)\b",
    r"\bcomo (?:tienes|ya tienes|cuentas con)\b",
    r"\bpuesto que (?:tienes|esta|está)\b",
    r"\baprovechando que (?:tienes|esta|está)\b",
    r"\b(?:excelente|perfecto|genial|muy bien)[,.]? (?:dato|entonces|ya que|con)\b",
)

# ═════════════════════════════════════════════════════════════════════════
# LAS CINCO CLASES QUE FALTABAN (2026-08-10)
#
# Anuar le preguntó a AURORA «qué comandos entiendes realmente y sin humo» y
# le inventó tres listas seguidas. Su reclamo fue exacto: «no entiendo por qué
# sigue apareciendo si lo has corregido cien veces».
#
# La causa medida (PRUEBAS_VIVAS/auditoria_mentiras.py, 5 de 18 detectadas):
# todo lo de arriba vigila el PASADO —«ya lo hice», «se ha guardado»— porque
# eso fue lo que falló en julio. Ninguna regla miraba el presente ni el futuro.
# No falló el candado: nunca hubo candado ahí. Y como los 241 `return` del
# pipeline salen por `consciencia.procesar()`, cerrar esto aquí lo cierra para
# los 33 candados, el enrutador y el LLM crudo de un solo golpe.
#
# El filtro que evita el ruido en las cinco: solo se juzgan cuando NO hubo
# ejecución real. Un candado que de verdad corrió algo puede afirmar lo que
# hizo; el modelo de texto hablando de sí mismo está adivinando siempre.
# ═════════════════════════════════════════════════════════════════════════

# ── 1. CAPACIDAD: afirma que sabe/puede, sin haber consultado el registro.
# NO se marca «puedo ayudarte» ni «puedo explicarte» a propósito: eso sí lo
# puede hacer un modelo de texto y marcarlo volvería el candado ruido.
# Se marca únicamente cuando dice poseer COMANDOS, FUNCIONES o SABERES.
_VERBOS_DE_OFICIO = (
    r"(?:hacer|generar|emitir|timbrar|calcular|gestionar|administrar|"
    r"publicar|facturar|cobrar|agendar|imprimir|cortar|grabar|bordar|"
    r"sublimar|vectorizar|cotizar)\b")
_AFIRMA_CAPACIDAD = (
    r"\b(?:entiendo|reconozco|manejo|soporto|acepto) (?:el |los |estos )?comandos?\b",
    r"\bcomandos? que (?:entiendo|reconozco|manejo|soporto|acepto)\b",
    r"\b(?:estos|los|mis) comandos?\b[^.]{0,60}\b(?:integrad|disponible|"
    r"en mi arquitectura|los ejecuto|puedo ejecutar)",
    r"\bpuedo ejecutar(?:los|las)?\b(?:\s+con éxito|\s+sin problema)?",
    # Los dos se escriben con la MISMA lista de verbos a propósito. La primera
    # versión los tenía separados y «soy capaz de cotizar» se coló entre los
    # dos: el verbo estaba en una lista y la forma de decirlo en la otra.
    r"\b(?:puedo|sé|se|soy capaz de|tengo la capacidad de)\s+" + _VERBOS_DE_OFICIO,
)

# ── 2. APROPIACIÓN: los comandos de OTRO programa dichos como propios.
# Es la más peligrosa de las cinco porque cada dato es cierto y solo es falso
# de quién es. Pasó tal cual: AURORA leyó los manuales de la BIBLIOTECA que se
# le meten al prompt (consciencia.py, «--- BIBLIOTECA (manuales reales) ---»)
# y devolvió «Toolpaths», «Carve» y «Seleccionar cortador» como comandos suyos.
_PROGRAMAS_AJENOS = (
    r"corel\s*draw|coreldraw|vectric|aspire|inkscape|silhouette|rdworks|"
    r"libre\s*office|photoshop|illustrator|autocad|fusion\s*360|lightburn")
_SE_LOS_APROPIA = (
    r"\bmis comandos? (?:en|de|para)\b",
    r"\b(?:comandos?|funciones|herramientas) (?:que )?(?:entiendo|manejo|tengo)"
    r"\b[^.]{0,40}\b(?:en|de)\b",
    r"\ben \w+[,:]?\s*(?:puedo|sé|se)\b",
)

# ── 3. PROMESA: se compromete a algo futuro que nadie va a cumplir.
# En la misma sesión del 2026-08-10 le dijo «ese error se está corrigiendo»
# — y nadie estaba corrigiendo nada en ese momento. Suena a servicio y es
# humo: AURORA no tiene trabajos en segundo plano que respalden eso.
_PROMESA = (
    r"\bse est[áa] (?:corrigiendo|arreglando|solucionando|actualizando|"
    r"resolviendo|revisando|implementando)\b",
    r"\b(?:estoy|estamos) (?:trabajando en|corrigiendo|arreglando|"
    r"implementando|desarrollando)\b",
    r"\bvoy a (?:estar pendiente|avisarte|monitorear|revisarlo|checarlo)\b",
    r"\bte (?:aviso|informo|notifico) (?:cuando|en cuanto|apenas)\b",
    r"\ben (?:un momento|unos minutos|breve) (?:queda|estará|lo tengo|te lo)",
    r"\b(?:pr[óo]ximamente|muy pronto|en la pr[óo]xima versi[óo]n)\b",
)

# ── 4. CONEXIÓN: dice estar conectada a un servicio.
# Esta sí se puede comprobar de verdad: las integraciones reales salen de
# variables de entorno (CEREBRO/auto_conocimiento.py:156-163). Si el servicio
# no está en el mapa, AURORA no lo tiene — punto. Y si está pero le falta su
# llave, tampoco. Nada de esto es opinión.
_SERVICIOS_REALES = {
    "groq": "GROQ_API_KEY",
    "whatsapp": "GREEN_API_TOKEN",
    "green api": "GREEN_API_TOKEN",
    "facebook": "FB_PAGE_TOKEN",
    "instagram": "INSTAGRAM_ACCESS_TOKEN",
    "supabase": "SUPABASE_KEY",
}
_RE_DICE_CONECTADA = re.compile(
    r"\b(?:estoy|ya estoy|me encuentro) conectad[ao] (?:a|con|al)\s+"
    r"(?:tu |su |la |el |mi )?([\w\s]{3,25})|"
    r"\btengo (?:acceso|conexi[óo]n) (?:a|con|al)\s+"
    r"(?:tu |su |la |el |mi )?([\w\s]{3,25})", re.I)

# ── 5. NÚMEROS PROPIOS: cifras sobre sí misma.
# El peor de los cinco para lo que Anuar necesita, porque una demo se sostiene
# en estos números y si están inflados queda mal ÉL, no AURORA. Y este también
# se comprueba exacto: el registro sabe cuántas herramientas hay de verdad.
_RE_NUM_PROPIO = re.compile(
    r"\b(?:tengo|manejo|cuento con|dispongo de|son)\s+"
    r"(?:m[áa]s de\s+|cerca de\s+|unas?\s+|unos?\s+)?"
    r"([\d][\d,\.]{0,8})\s*"
    r"(herramientas?|comandos?|funciones?|candados?|motores?|m[óo]dulos?)", re.I)
# Cuánto se le tolera antes de marcarlo. «Unas 600 herramientas» siendo 635 es
# hablar en redondo, no mentir; 2,400 siendo 635 sí es inventar.
_TOLERANCIA_NUM = 0.15


# ── EL GUARDIÁN DE LOS CINCO: la negación ────────────────────────────────
# Sin esto el candado castiga «NO puedo publicar en TikTok, no tengo la llave»
# — que es AURORA siendo honesta— exactamente igual que a una mentira. Salió
# en la primera contraprueba del 2026-08-10 y es el peor error posible aquí:
# enseñarle a no reconocer sus límites es lo contrario de lo que se busca.
_NIEGA = re.compile(
    r"\b(?:no|nunca|jam[áa]s|tampoco|ni)\b|\b(?:a[úu]n|todav[íi]a)\s+no\b|"
    r"\bsin\s+(?:poder|saber)\b", re.I)


def _va_negado(texto: str, inicio: int) -> bool:
    """¿La afirmación viene negada? Se mira solo su propia frase.

    Se corta por signos de puntuación a propósito: en «Sí puedo cotizar. No
    tengo TikTok», el «No» de la segunda frase no debe absolver a la primera,
    ni al revés.
    """
    trozo = re.split(r"[.;:!?\n]", texto[:inicio])[-1]
    return bool(_NIEGA.search(trozo))


def _conteos_reales(registro_claves) -> Dict[str, int]:
    """Lo que AURORA es de verdad, contado del sistema y no de un texto fijo.

    Se cuenta en vivo a propósito: una constante escrita a mano aquí se
    desincroniza el día que alguien agregue un candado, y el candado que
    vigila mentiras acabaría diciendo una.
    """
    reales: Dict[str, int] = {}
    if registro_claves:
        reales["herramientas"] = len(registro_claves)
        reales["m[óo]dulos"] = len({k.split("/", 1)[0]
                                    for k in registro_claves if "/" in k})
    try:
        # Import perezoso: consciencia importa este módulo dentro de una
        # función, así que aquí no se cierra ningún ciclo.
        from CEREBRO.consciencia import _CANDADOS
        reales["candados"] = len(_CANDADOS)
    except Exception:
        pass
    return reales


def revisar(respuesta: str, motores_usados=None, registro_claves=None,
            pregunta: str = "") -> Tuple[str, Dict]:
    """Revisa una respuesta ANTES de que salga y le agrega la corrección honesta.

    Devuelve (respuesta_final, informe). El informe dice qué se detectó — sirve
    para registrar y para las pruebas.

    NUNCA borra la respuesta: agrega la corrección al final, visible, para que
    Anuar vea qué se dijo y por qué no es confiable.
    """
    informe = {"afirmo_accion_sin_hacerla": False, "dio_por_hecho": False,
               "comandos_inventados": [],
               "archivos_inexistentes": [], "corregida": False,
               # Las cinco clases que se agregaron el 2026-08-10.
               "afirmo_capacidad": False, "se_apropio": False,
               "prometio": False, "conexiones_falsas": [],
               "numeros_inflados": []}
    if not respuesta or not respuesta.strip():
        return respuesta, informe

    avisos: List[str] = []
    ejecuto = _hubo_ejecucion_real(motores_usados)

    # 0) ¿Da por hecho un dato que nadie le dio?
    # Encontrado en vivo 2026-08-02. Anuar preguntó "corel tiene instalado el
    # plugin laser" — o sea, PREGUNTÓ si lo tiene. AURORA respondió "Con el
    # plugin Laser instalado en CorelDRAW, podemos aprovechar...". Nadie le dijo
    # que estuviera instalado: lo dio por cierto para poder seguir hablando.
    # Es más sutil que inventar un archivo, pero es la misma falla: afirmar sin
    # comprobar. Y frente a un cliente es igual de caro.
    if not ejecuto and pregunta:
        _p = pregunta.lower()
        if re.search(r"\b(?:tiene[s]?|hay|existe|esta|está|cuenta con|dispone de)\b", _p) \
                and re.search(r"\?|\bsi\b|\bcual\b|\bcuál\b|\bque\b|\bqué\b", _p):
            for patron in _DA_POR_HECHO:
                if re.search(patron, respuesta.lower()):
                    informe["dio_por_hecho"] = True
                    avisos.append(
                        "⚠️ Me preguntaste si eso existe y respondí como si ya supiera que sí. "
                        "**No lo comprobé** — no tengo forma de revisarlo desde aquí. "
                        "Tómalo como suposición, no como dato.")
                    break

    # 1) ¿Dice que hizo algo, sin haber ejecutado nada?
    if not ejecuto:
        bajo = respuesta.lower()
        for patron in _AFIRMA_ACCION:
            if re.search(patron, bajo):
                informe["afirmo_accion_sin_hacerla"] = True
                avisos.append(
                    "⚠️ Arriba dije que ya había hecho algo, pero **no ejecuté nada**: "
                    "esa parte de la respuesta la escribió el modelo de texto, que no "
                    "tiene manos. Pídemelo directo con la ruta completa y lo hago de verdad.")
                break

    # 2) ¿Cita comandos que no existen?
    inventados = _comandos_inventados(respuesta, registro_claves)
    if inventados:
        informe["comandos_inventados"] = inventados
        lista = ", ".join(f"`{c}`" for c in inventados[:6])
        avisos.append(
            f"⚠️ Mencioné {'un comando que no existe' if len(inventados) == 1 else 'comandos que no existen'}: "
            f"{lista}. No los uses — pídeme la lista real y la saco del registro del sistema.")

    # 3) ¿Menciona archivos que no están?
    faltantes = _archivos_inexistentes(respuesta, pregunta or "")
    if faltantes:
        informe["archivos_inexistentes"] = faltantes
        lista = ", ".join(f"`{a}`" for a in faltantes[:5])
        avisos.append(
            f"⚠️ {'Este archivo no existe' if len(faltantes) == 1 else 'Estos archivos no existen'} "
            f"en el disco: {lista}. Si dije que lo generé, no es cierto.")

    # ── 4) ¿Dice que SABE o PUEDE, sin haberlo consultado? ────────────────
    # El eje que faltaba entero. Solo aplica cuando no hubo ejecución real:
    # ahí quien habla es el modelo de texto, que no tiene forma de saber qué
    # hay en el registro y lo rellena con lo que suena razonable.
    bajo = respuesta.lower()
    if not ejecuto:
        for patron in _AFIRMA_CAPACIDAD:
            _m = re.search(patron, bajo)
            if _m and not _va_negado(bajo, _m.start()):
                informe["afirmo_capacidad"] = True
                avisos.append(
                    "⚠️ Dije lo que sé hacer **sin consultar mi registro** — esa parte "
                    "la escribió el modelo de texto y puede estar inventada. "
                    "Pregúntame **«qué sabes hacer»** y te doy la lista real, "
                    "sacada del sistema.")
                break

        # ── 5) ¿Se está apropiando de comandos de otro programa? ──────────
        if re.search(_PROGRAMAS_AJENOS, bajo):
            for patron in _SE_LOS_APROPIA:
                _m = re.search(patron, bajo)
                if _m and not _va_negado(bajo, _m.start()):
                    informe["se_apropio"] = True
                    avisos.append(
                        "⚠️ Arriba mezclé **funciones de otros programas** (Corel, "
                        "Aspire, Inkscape…) con las mías. Las leí de tus manuales; "
                        "no son comandos que yo ejecute. Lo que yo hago con esos "
                        "programas es otra cosa y es más corto.")
                    break

        # ── 6) ¿Prometió algo que nadie va a cumplir? ─────────────────────
        for patron in _PROMESA:
            _m = re.search(patron, bajo)
            if _m and not _va_negado(bajo, _m.start()):
                informe["prometio"] = True
                avisos.append(
                    "⚠️ Prometí algo a futuro (que se está corrigiendo, que te aviso). "
                    "**No tengo forma de cumplirlo solo**: no hay nadie trabajando en "
                    "eso ahora mismo ni me quedo pendiente después de responderte.")
                break

    # ── 7) ¿Dice estar conectada a algo que no? ───────────────────────────
    # Este se comprueba de verdad contra las variables de entorno, así que
    # aplica siempre — hasta un candado que ejecutó puede decirlo mal.
    import os
    # SI NO PUEDO COMPROBAR, ME CALLO. Si no hay NINGUNA llave en el entorno,
    # no es que AURORA esté desconectada de todo: es que este proceso no cargó
    # el .env. Salió en la contraprueba del 2026-08-10, acusando de mentira un
    # «estoy conectada a WhatsApp» que era cierto. «No lo puedo verificar» y
    # «es falso» no son lo mismo, y confundirlos es la misma falla que se está
    # persiguiendo, solo que del otro lado.
    _hay_entorno = any(os.getenv(v) for v in set(_SERVICIOS_REALES.values()))
    for m in (_RE_DICE_CONECTADA.finditer(respuesta) if _hay_entorno else ()):
        servicio = (m.group(1) or m.group(2) or "").strip().lower()
        servicio = re.sub(r"\s+", " ", servicio).strip(" .,;:")
        if not servicio:
            continue
        env = next((v for k, v in _SERVICIOS_REALES.items() if k in servicio), None)
        if env and os.getenv(env):
            continue                        # conectada de verdad, sin aviso
        if servicio not in informe["conexiones_falsas"]:
            informe["conexiones_falsas"].append(servicio)
    if informe["conexiones_falsas"]:
        lista = ", ".join(f"**{s}**" for s in informe["conexiones_falsas"][:4])
        avisos.append(
            f"⚠️ Dije estar conectada a {lista} y **no lo estoy**. Mis conexiones "
            f"reales son las que tienen su llave puesta: WhatsApp, Facebook, "
            f"Instagram, Groq y Supabase. Lo demás no está enlazado.")

    # ── 8) ¿Infló los números sobre sí misma? ─────────────────────────────
    # El más caro para una demo: Anuar va a repetir esa cifra enfrente de un
    # cliente. Se compara contra el conteo real del sistema, no contra un
    # número escrito a mano que se desincroniza.
    reales = _conteos_reales(registro_claves)
    if reales:
        for m in _RE_NUM_PROPIO.finditer(respuesta):
            try:
                dicho = int(m.group(1).replace(",", "").replace(".", ""))
            except ValueError:
                continue
            cosa = m.group(2).lower()
            real = next((v for k, v in reales.items() if re.match(k, cosa)), None)
            if real is None or real == 0:
                continue
            if abs(dicho - real) / real > _TOLERANCIA_NUM:
                informe["numeros_inflados"].append(
                    {"dijo": dicho, "real": real, "de": cosa})
    if informe["numeros_inflados"]:
        det = "; ".join(f"dije {x['dijo']:,} {x['de']} y son {x['real']:,}"
                        for x in informe["numeros_inflados"][:3])
        avisos.append(
            f"⚠️ Di un número mío que no cuadra: {det}. **No repitas esa cifra** — "
            f"los conteos buenos los saco del registro cuando me los pidas.")

    if not avisos:
        return respuesta, informe

    informe["corregida"] = True
    return (respuesta.rstrip() + "\n\n---\n" + "\n".join(avisos)), informe
