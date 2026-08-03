# -*- coding: utf-8 -*-
"""
Genera MANUALES/manual_comandos_aurora.md a partir del código REAL de
CEREBRO/consciencia.py (los 14 candados directos y sus funciones _es_X) y del
registro real de herramientas (~690 funciones, CEREBRO/registro_herramientas.py).

Nunca se escribe a mano: si un trigger cambia en el código, correr este script
de nuevo regenera el manual y queda al día — mismo problema que ya se vio 3 veces
esta noche con los candados de Corel (el manual a mano se desincroniza apenas
alguien toca un trigger).

Uso:  python CEREBRO/generar_manual.py
"""
from __future__ import annotations
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from CEREBRO import consciencia as _c  # noqa: E402
from CEREBRO import registro_herramientas as _rh  # noqa: E402

SALIDA = ROOT / "MANUALES" / "manual_comandos_aurora.md"

# Candado -> grupo de trabajo real del panel (mismos 6 .nav-group de
# TEMPLATES/panel-completo.html). Se mantiene a mano (solo 14 líneas, no 690)
# porque el nombre del candado no trae el grupo codificado en ningún lado.
_GRUPO = {
    "busqueda_web": "Conocimiento", "corel": "Diseño", "dxf": "Diseño",
    "negocio": "Taller", "publicar": "Marketing", "agenda": "Taller",
    "ficha_vendedor": "Ventas", "intuicion": "Cerebro y Sistema",
    "memoria": "Cerebro y Sistema", "equipos": "Cerebro y Sistema",
    "crear_capacidad": "Cerebro y Sistema", "consulta_codigo": "Cerebro y Sistema",
    "editar_codigo": "Cerebro y Sistema", "accion_fisica": "Cerebro y Sistema",
    "abrir_navegador": "Cerebro y Sistema",
}
_ORDEN_GRUPOS = ["Taller", "Ventas", "Marketing", "Diseño", "Conocimiento", "Cerebro y Sistema"]

_STR_RE = re.compile(r'''["']([^"']{2,60})["']''')
_NOMBRE_CONST_RE = re.compile(r"\b(_[A-Z][A-Z0-9_]*)\b")


def _extraer_triggers(fn) -> list:
    """Frases/triggers reales que reconoce una función _es_X: literales de texto
    en su propio código fuente + cualquier tupla de módulo que referencie
    (ej. _COREL_ACCIONES). No depende de un mapeo a mano por candado."""
    try:
        src = inspect.getsource(fn)
    except Exception:
        return []
    triggers = set()
    for m in _STR_RE.finditer(src):
        s = m.group(1).strip()
        if not s or s.startswith("_") or not any(c.isalpha() for c in s):
            continue
        if len(s.split()) <= 6:  # descarta prosa larga (docstrings, mensajes)
            triggers.add(s)
    for m in _NOMBRE_CONST_RE.finditer(src):
        val = getattr(_c, m.group(1), None)
        if isinstance(val, tuple):
            triggers.update(t for t in val if isinstance(t, str) and len(t.split()) <= 6)
    return sorted(_utiles(triggers))


# Palabras que salen del código pero NO son comandos. Encontrado leyendo el
# manual con Anuar el 2026-08-03: aparecían «hoy», «cdr», «cuales», «abre» y
# hasta un regex crudo como si fueran cosas que él podía escribir. Un ejemplo
# que no se puede teclear no es un ejemplo: es ruido que hace desconfiar del
# resto del manual.
_NO_SON_COMANDOS = {
    "hoy", "manana", "mañana", "cuales", "cuantas", "cuantos", "cuanto", "dime",
    "lista", "resumen", "cdr", "dxf", "pdf", "png", "svg", "jpg", "abre", "abrir",
    "cierra", "cerrar", "corel", "corell", "agenda", "agente", "archivo", "olvida",
    "que", "como", "cual", "donde", "ok", "si", "va", "dale", "sale", "vale",
    "coach", "voz", "plugin", "plugins", "macro", "macros", "web", "internet",
}


def _utiles(frases) -> list:
    """Deja solo lo que Anuar podría escribir tal cual y funcionaría."""
    limpias = []
    for f in frases:
        f = f.strip()
        # Un regex no es una frase: «\b(busca|buscame|investiga)\b» salía en el
        # manual como si fuera algo que se pudiera teclear.
        if any(c in f for c in ("\\", "|", "(", ")", "[", "]", "^", "$", "{", "}")):
            continue
        if f.lower() in _NO_SON_COMANDOS:
            continue
        if len(f) < 4:
            continue
        limpias.append(f)
    return limpias


# Cuando el código no explica un candado, el manual decía "(sin descripción en
# el código)". Anuar, leyéndolo el 2026-08-03: "muchos de los motores no saben
# qué hacer, pues así está descrito en el manual". Tenía razón — un manual que
# dice que no sabe para qué sirve algo es peor que no tenerlo.
# Estas descripciones son de lo que el candado HACE de verdad, verificado en vivo.
# Cada una dice lo que la función INVOCA DE VERDAD, leído de su código el
# 2026-08-03 — no lo que uno supondría por el nombre. Entre paréntesis va la
# llamada real, para que se pueda comprobar.
_QUE_HACE = {
    "agenda":
        "Tus citas de hoy, de mañana y las próximas 24 h, y agenda nuevas. Si le "
        "faltan la fecha, la hora o el cliente, los pide en vez de inventarlos "
        "(usa dia, proximas, resumen y crear_cita de la agenda real).",
    "ficha_vendedor":
        "Arma la ficha técnica y los argumentos de venta de un producto de tu "
        "catálogo, para que puedas cerrar sin buscar datos (ficha + construir_brief).",
    "negocio":
        "Las cifras reales de tus negocios: contabilidad del mes, órdenes del "
        "taller, inventario bajo mínimo, pronóstico del embudo y de qué fuente "
        "vienen tus leads (contabilidad_mensual, listar_ordenes, bajo_minimo, "
        "pronostico_embudo, fuentes_efectivas).",
    "corel":
        "Maneja CorelDRAW de verdad por COM: abre archivos, exporta a PDF, escala "
        "la página, extrae el texto del diseño, quita fondos, arma planillas, "
        "saca colores con gotero y te dice qué plugins tienes instalados.",
    "dxf":
        "Convierte tus archivos entre DXF, PDF, PNG, SVG y EPS, con el DPI y la "
        "página que le pidas, y vectoriza imágenes para la láser. Si le das solo "
        "el nombre, busca el archivo en tu disco (convertir, convertir_todo).",
    "busqueda_web":
        "Busca en internet de verdad y te devuelve resultados con su fuente. No "
        "responde de memoria: si no encuentra, lo dice.",
    "publicar":
        "Te enseña qué se publicaría hoy y lo sube a redes solo cuando confirmas. "
        "También te da la estrategia de ingresos del día (preparar_publicacion, "
        "estrategia_ingresos).",
    "servicio_atf":
        "Atiende a un cliente que pide un servicio de mano de obra de ATF "
        "—recolocar una lupa, instalar un retrofit— y **nunca niega uno que sí "
        "haces**. Existe porque una vez le negó el servicio a un cliente real.",
    "abrir_navegador":
        "Abre páginas en tu navegador de verdad. Entiende «abre youtube» sin que "
        "tengas que decir el punto-com; reconoce 24 sitios por su nombre (abrir_url).",
    "consulta_codigo":
        "Te lee y te explica el código de la propia AURORA, sin modificar nada.",
    "editar_codigo":
        "Edita archivos de código de verdad: hace respaldo antes, verifica que "
        "compile después y revierte solo si algo sale mal. El corazón del sistema "
        "está blindado y te pide confirmación explícita.",
    "accion_fisica":
        "Abre programas y archivos de tu PC de verdad (Corel, Silhouette, "
        "carpetas, documentos).",
    "intuicion":
        "Te propone el siguiente paso a partir de tu perfil real de trabajo: qué "
        "sueles hacer, qué está pendiente y qué conviene ahora. No adivina, lee "
        "tus datos (obtener_perfil + sugerencia_proactiva).",
    "memoria":
        "Busca en lo que ya se habló y se aprendió antes, para no repetir ni "
        "perder contexto entre sesiones.",
    "equipos":
        "Coordina varios motores a la vez cuando un trabajo necesita más de uno "
        "(por ejemplo cotizar + agendar + avisar al cliente).",
    "ruta_sola":
        "Si le mandas solo la ruta de un archivo, lo encuentra —aunque le falte "
        "la extensión— y te dice qué puede hacer con él. Si venías pidiendo algo, "
        "completa esa petición con ese archivo.",
    "ver_aprendizaje":
        "Te muestra las formas de hablar que te ha aprendido y te deja borrar las "
        "que estén mal, con «olvida <la frase>» (listar, olvidar, olvidar_todo).",
    "voz":
        "Prende o apaga la voz: te escucha por el micrófono y te contesta "
        "hablando, con voz mexicana. También te avisa si la PC se queda sin memoria.",
    "acerca_de":
        "Te dice qué puede hacer de verdad, con los números reales del sistema y "
        "sus límites — nunca inventa capacidades (obtener_capacidades + descubrir).",
    "crear_capacidad":
        "Crear motores nuevos ya no lo hace AURORA: es trabajo de AURORITA XP, la "
        "fábrica que vive aparte. Aquí solo se cargan motores ya probados.",
    "cotizar":
        "Cotiza con los precios reales de tu catálogo (98 productos de ATF, 73 "
        "servicios de Milens). Si no encuentra el producto lo dice: no inventa precios.",
}


def _descripcion_handler(metodo: str, nombre_candado: str = "") -> str:
    """Qué hace el candado, en lenguaje de Anuar.

    Primero la descripción escrita a mano (clara y para él); si no hay, el
    docstring del código, pero la PRIMERA FRASE COMPLETA — antes se cortaba en
    el primer salto de línea y salían cosas como "Lee datos REALES (órdenes,
    inventario, CRM," cortada a media frase.
    """
    if nombre_candado in _QUE_HACE:
        return _QUE_HACE[nombre_candado]

    fn = getattr(_c.Consciencia, metodo, None)
    doc = (inspect.getdoc(fn) or "").strip() if fn else ""
    if not doc:
        return "Sin descripción todavía — pregúntale «qué puedes hacer» y te lo dice."

    # Se une hasta el primer punto que cierre una frase de verdad, no hasta el
    # primer salto de línea.
    texto = " ".join(l.strip() for l in doc.split("\n") if l.strip())
    texto = re.sub(r"^CHAT\s*↔\s*[A-ZÁÉÍÓÚÑ ]+[:.]?\s*", "", texto)   # prefijo interno
    corte = re.search(r"\.(?:\s|$)", texto)
    frase = texto[:corte.end()].strip() if corte else texto
    return frase if len(frase) > 25 else texto[:180].strip()


def _seccion_candados_directos() -> dict:
    """Agrupa los 14 candados de consciencia.py por grupo de trabajo."""
    por_grupo: dict = {g: [] for g in _ORDEN_GRUPOS}
    for nombre, trigger_fn, metodo, motor_id in _c._CANDADOS:
        grupo = _GRUPO.get(nombre, "Cerebro y Sistema")
        triggers = _extraer_triggers(trigger_fn)
        desc = _descripcion_handler(metodo, nombre)
        por_grupo[grupo].append({
            "nombre": nombre, "motor_id": motor_id,
            "descripcion": desc, "triggers": triggers,
        })
    return por_grupo


def _seccion_herramientas_router() -> dict:
    """Agrupa las ~690 herramientas reales del router universal por carpeta
    (el propio 'clave' del registro ya trae el prefijo carpeta/modulo:funcion)."""
    catalogo = _rh.descubrir(refrescar=True)
    por_carpeta: dict = {}
    for clave, meta in catalogo.items():
        carpeta = clave.split("/")[0] if "/" in clave else clave.split(":")[0]
        por_carpeta.setdefault(carpeta, []).append({
            "clave": clave, "doc": (meta.get("doc") or "").split("\n")[0].strip(),
            "params": meta.get("params", []),
        })
    return dict(sorted(por_carpeta.items()))


def generar() -> Path:
    candados = _seccion_candados_directos()
    herramientas = _seccion_herramientas_router()

    partes = [
        "# Manual de comandos reales de AURORA",
        "",
        "Generado automáticamente del código real (no escrito a mano) — si algo cambia en el "
        "código, este manual se regenera corriendo `python CEREBRO/generar_manual.py` y queda "
        "al día. Cada frase de ejemplo listada aquí es una que AURORA reconoce de verdad hoy.",
        "",
        "**Aviso real** (encontrado probando en vivo, 2026-07-27): algunos candados combinan "
        "DOS categorías de frases a la vez (ej. `negocio` necesita una palabra de pregunta "
        "como \"cuánto\"/\"cómo va\" JUNTO CON una palabra de dominio como \"inventario\"/"
        "\"contabilidad\" en el MISMO mensaje; `corel` necesita \"corel\"/\"cdr\" JUNTO CON una "
        "acción como \"exporta\"). Una sola frase suelta de la lista puede no bastar por sí sola "
        "— este generador aún no distingue esa lógica compuesta, es una mejora pendiente.",
        "",
        "**Aviso real 2** (mismo día): dentro de `dxf`, la frase \"vectoriza\"/\"vectorizar\" no "
        "ejecuta directo como las demás (\"convierte a dxf\", \"pásalo a dxf\") — pasa por el "
        "enrutador de IA y pide confirmación aparte antes de correr. Mismo candado, comportamiento "
        "distinto según la frase exacta usada — verificado en vivo, no corregido todavía.",
        "",
        "## Índice por grupo de trabajo (comandos directos)",
        "",
    ]
    total_candados = 0
    for grupo in _ORDEN_GRUPOS:
        items = candados.get(grupo, [])
        if not items:
            continue
        partes.append(f"### {grupo}")
        partes.append("")
        for it in items:
            total_candados += 1
            partes.append(f"**{it['nombre']}** ({it['motor_id']})")
            partes.append(f"- Qué hace: {it['descripcion']}")
            if it["triggers"]:
                ejemplos = ", ".join(f"«{t}»" for t in it["triggers"][:12])
                partes.append(f"- Frases que reconoce: {ejemplos}")
            else:
                partes.append("- Frases que reconoce: (no se detectaron literales — revisar a mano)")
            partes.append("")
        partes.append("")

    partes.append("## Herramientas del enrutador universal (~%d funciones reales)" % sum(len(v) for v in herramientas.values()))
    partes.append("")
    partes.append(
        "Estas no se activan por una frase fija — el enrutador de IA elige la que mejor "
        "responda a lo que pidas, verificando que existan los datos necesarios antes de "
        "ejecutarla de verdad (nunca la adivina a ciegas)."
    )
    partes.append("")
    for carpeta, items in herramientas.items():
        partes.append(f"### {carpeta} ({len(items)})")
        partes.append("")
        for it in items:
            partes.append(f"- `{it['clave']}` — {it['doc'] or '(sin descripción)'}")
        partes.append("")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"Manual generado: {SALIDA} ({total_candados} candados directos, "
          f"{sum(len(v) for v in herramientas.values())} herramientas del router)")
    return SALIDA


if __name__ == "__main__":
    generar()
