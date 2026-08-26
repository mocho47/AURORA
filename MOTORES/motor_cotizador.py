# -*- coding: utf-8 -*-
"""
AURORA — MOTOR COTIZADOR INTELIGENTE
Genera cotizaciones reales con 3 opciones para ATF y MILENS.
Precios reales del catálogo. Usa Groq. Sin simulaciones.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from MOTORES import _llamada_modelo as _lm
except ImportError:
    import _llamada_modelo as _lm

logger = logging.getLogger("aurora.motor_cotizador")

# ── NO HAY PRECIOS EN ESTE ARCHIVO. A PROPOSITO. ───────────────────────────
# Aqui vivian dos listas de precios escritas a mano (4 productos ATF, 6 de
# MILENS) que se usaban de "respaldo" cuando no se podia leer el catalogo real.
# Dos problemas, los dos reales y encontrados el 2026-08-26:
#   1. Estaban VIEJAS. El Aozoom X1 decia $8,000; el catalogo real de Anuar
#      (CONFIG/catalogo_atf.json) dice $3,149. Dos veces y media de mas.
#   2. El aviso que supuestamente advertia "cotizado con lista de respaldo" se
#      calculaba en una variable y NUNCA se metia en la respuesta. O sea el
#      cliente recibia un precio inventado sin una sola señal de que lo era.
# Regla de Anuar: nunca se inventa un precio. Un precio equivocado cuesta mas
# que no dar precio. Si no se puede leer el catalogo real, se DICE y no se
# cotiza. Los precios se cambian en CONFIG/catalogo_atf.json y en el catalogo
# de servicios — en un solo lugar, y llegan aqui solos.

# ── EL MARGEN NO SE VUELVE A APLICAR AQUI (arreglo 2026-08-26) ─────────────
# Encontrado corriendo el motor de verdad: se le pidio cotizar faros para un
# Jetta y devolvio esto —
#     "Faro LED Plus (Doble) - Precio público $550.00"
#     Estándar  120% -> $1,320    Premium 125% -> $1,375    Cierre 130% -> $1,430
# O sea agarro el precio del catalogo, que YA ES el precio de venta al publico,
# y encima le multiplico el margen. El cliente recibia $1,320 por algo que
# cuesta $550. La culpa era de una sola linea de este prompt: "ATF margen real:
# 120-130%. MILENS margen real: 50-150%.".
# Dos cosas mas que salieron mal de la misma linea:
#   · La opcion de "Cierre agresivo" salia MAS CARA que la estandar ($1,430 vs
#     $1,320). Un cierre que sube el precio no es un cierre.
#   · El margen es informacion INTERNA de Anuar. No tiene por que viajar en un
#     prompt que arma lo que ve el cliente.
# La regla de Anuar es la de siempre: el precio del catalogo es el precio. Si
# hay que sumarle algo (corte, diseño, instalacion) sale de su formula, no de
# un porcentaje inventado por el modelo.

PROMPT_COTIZADOR = """Eres el cotizador profesional de ATF Retrofit y MILENS de Anuar.
Generas SIEMPRE exactamente 3 opciones de cotización: Estándar, Premium y Cierre.

⛔ LA REGLA QUE MANDA SOBRE TODO — EL PRECIO DEL CATÁLOGO ES EL PRECIO.
El número que viene en el catálogo YA ES el precio de venta al público de Anuar.
· NO le apliques margen, ni porcentaje, ni recargo, ni "120%", ni redondeos.
· NO inventes un precio que no esté en el catálogo que te pasaron.
· NO calcules precios "estimados", "aproximados" ni "desde".
Las 3 opciones se diferencian por lo que INCLUYEN (cantidad, modelo, servicios,
tiempo de entrega), NUNCA por un margen que tú le sumes al mismo producto.
La opción de Cierre es la MÁS BARATA de las tres, no la más cara: es la que se
usa para cerrar la venta.

Si el producto que pide el cliente no está en el catálogo, dilo claramente y di
que hay que verificar el precio. Vale mil veces más un "déjame confirmarte" que
un número inventado: un precio equivocado ya le costó dinero real a Anuar.

Formato: claro, directo, con desglose y próximo paso accionable. En español."""

_MODELO = "openai/gpt-oss-20b"

# Deteccion del negocio por lo que el cliente REALMENTE pide (arreglo 2026-07-29).
# Bug encontrado en vivo: negocio se tomaba SIEMPRE como "atf" por default y nunca
# se miraba el texto — cotizar "50 tazas ceramica sublimadas" (trabajo de MILENS)
# usaba el catalogo de FAROS de ATF, o sea precios del negocio equivocado en la
# mitad de las cotizaciones. Ahora se deduce del pedido; el contexto explicito
# sigue mandando por encima de la deteccion.
_PALABRAS_MILENS = (
    "taza", "termo", "playera", "polo", "gorra", "sublima", "sublimad", "vaso",
    "laser", "láser", "grabado", "grabar", "mdf", "acrilico", "acrílico", "madera",
    "sello", "llavero", "bolsa", "caja", "posavaso", "servilletero", "dtf", "vinil",
    "copa", "caballito", "tarro", "agenda", "boligrafo", "bolígrafo", "mousepad",
    "rompecabezas", "azulejo", "peluche", "planilla", "sticker",
)
_PALABRAS_ATF = (
    "faro", "faros", "led h", "h4", "h7", "h11", "h13", "9005", "9006",
    "retrofit", "proyector", "bi-led", "biled", "aozoom", "ojo de angel",
    "ojos de angel", "ojo demonio", "ojos demonio", "demonio", "cuartos",
    "calavera", "stop", "direccional", "canbus", "balastro", "xenon", "xenón",
    "fibra optica", "fibra óptica", "tira secuencial", "tiras secuenciales",
)


# ── CATALOGOS REALES, UNA SOLA FUENTE DE VERDAD (arreglo 2026-07-29) ────────
# Problema real encontrado: este archivo tenia su PROPIA copia hardcodeada de
# los catalogos (4 productos de ATF y 6 de MILENS) mientras los catalogos de
# verdad, ya mantenidos, viven aparte:
#   · CONFIG/catalogo_atf.json  -> 106 productos reales (clonado del PDF del proveedor)
#   · CONFIG/catalogo_servicios.json -> servicios MILENS (73 items via catalogo_plano())
# O sea el cotizador cotizaba con una lista minima y vieja, y cualquier precio
# que Anuar actualizara en los archivos NO llegaba aqui. Ahora se leen de la
# fuente real en cada cotizacion; si no se pueden leer, se cae a las listas de
# abajo y se DICE en la respuesta (nunca se finge tener el catalogo completo).
_RAIZ = Path(__file__).resolve().parent.parent


def _catalogo_atf_real():
    """106 productos reales del catalogo ATF. (None, motivo) si no se pudo leer."""
    try:
        d = json.loads((_RAIZ / "CONFIG" / "catalogo_atf.json").read_text(encoding="utf-8"))
        prods = d.get("productos") or []
        if not prods:
            return None, "catalogo_atf.json no tiene productos"
        return {p.get("sku") or p.get("nombre"): {
                    "nombre": p.get("nombre", ""), "precio_publico": p.get("precio", 0),
                    "categoria": p.get("categoria", ""), "sku": p.get("sku", ""),
                } for p in prods}, None
    except Exception as e:
        return None, f"no pude leer catalogo_atf.json: {str(e)[:120]}"


def _catalogo_milens_real():
    """Servicios reales de MILENS via el cotizador de servicios ya existente."""
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("cotizador_servicios",
                                            _RAIZ / "TALLER" / "cotizador_servicios.py")
        cs = _ilu.module_from_spec(spec); spec.loader.exec_module(cs)
        r = cs.catalogo_plano()
        items = r.get("items") or []
        if not items:
            return None, "catalogo_servicios no devolvio items"
        return {it.get("nombre", f"item{i}"): {
                    "nombre": it.get("nombre", ""), "precio_publico": it.get("precio", 0),
                    "categoria": it.get("categoria", ""), "unidad": it.get("unidad", ""),
                    "incluye": it.get("incluye", ""),
                } for i, it in enumerate(items)}, None
    except Exception as e:
        return None, f"no pude leer el catalogo de servicios MILENS: {str(e)[:120]}"


def _filtrar_catalogo(catalogo: dict, pedido: str, maximo: int = 25) -> dict:
    """Devuelve solo los productos del catalogo que se parecen a lo que pidio el
    cliente (por palabras compartidas en nombre/categoria/sku). Si ninguno calza,
    devuelve una muestra — para que el modelo pueda decir 'hay que verificar' en
    vez de inventar un precio."""
    import unicodedata as _ud

    def norm(s):
        return "".join(c for c in _ud.normalize("NFD", str(s or "").lower())
                       if _ud.category(c) != "Mn")

    p = norm(pedido)
    # Plural/singular: el cliente pide "50 TAZAS" y el producto se llama "TAZA
    # blanca 11oz". Buscar la palabra tal cual no calza (bug real encontrado al
    # probarlo: pedir tazas devolvia playeras). Se prueba tambien la raiz sin la
    # 's'/'es' final, en ambos sentidos.
    palabras = set()
    for w in p.replace(",", " ").replace("/", " ").split():
        if len(w) < 4:
            continue
        palabras.add(w)
        if w.endswith("es") and len(w) > 5:
            palabras.add(w[:-2])
        elif w.endswith("s") and len(w) > 4:
            palabras.add(w[:-1])
    if not palabras:
        return dict(list(catalogo.items())[:maximo])
    calzan = {}
    for clave, val in catalogo.items():
        texto = norm(f"{clave} {val.get('nombre','')} {val.get('categoria','')} {val.get('sku','')}")
        if any(w in texto for w in palabras):
            calzan[clave] = val
            if len(calzan) >= maximo:
                break
    return calzan or dict(list(catalogo.items())[:maximo])


def _detectar_negocio(texto: str) -> str:
    """Deduce si el pedido es de MILENS (sublimacion/laser) o ATF (faros) por sus
    palabras reales. Empate o sin señales -> 'atf' (comportamiento anterior)."""
    import unicodedata as _ud
    t = "".join(c for c in _ud.normalize("NFD", (texto or "").lower())
                if _ud.category(c) != "Mn")
    n_milens = sum(1 for p in _PALABRAS_MILENS if p in t)
    n_atf = sum(1 for p in _PALABRAS_ATF if p in t)
    return "milens" if n_milens > n_atf else "atf"


class MotorCotizador:
    def __init__(self):
        self.motor_id = "motor_cotizador"
        self._groq = _lm.cliente()
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def cotizar(self, requerimiento: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        # El contexto explicito manda; si no viene, se deduce del pedido real
        # (antes se asumia "atf" a ciegas — ver nota en _detectar_negocio).
        negocio = (contexto.get("negocio") or _detectar_negocio(requerimiento)).lower()
        # Catalogo REAL desde su fuente (ver nota arriba). Si falla, se usa la
        # lista minima de respaldo y se avisa honesto en la respuesta.
        if negocio == "atf":
            catalogo, _err_cat = _catalogo_atf_real()
            _fuente = "CONFIG/catalogo_atf.json"
        else:
            catalogo, _err_cat = _catalogo_milens_real()
            _fuente = "el catálogo de servicios de MILENS"
        if not catalogo:
            # Sin precios de verdad NO se cotiza. Antes aqui se caia a una lista
            # vieja escrita a mano y se entregaba el precio equivocado como si
            # fuera bueno. Vale mas decir la verdad y arreglar la fuente.
            return {"status": "ERROR", "motor": self.motor_id,
                    "detalle": f"No pude leer {_fuente}, así que no tengo tus precios reales. "
                               f"No te voy a inventar una cotización. Motivo: {_err_cat}"}
        folio = f"COT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # Con el catalogo real (106 productos ATF / 73 servicios MILENS) mandarlo
        # completo no cabe bien en el prompt y diluye la atencion del modelo. Se
        # filtran los productos que de verdad se parecen a lo que pidio el
        # cliente; si nada calza, se manda una muestra para que el modelo pueda
        # decir honestamente que hay que verificar (nunca inventar un precio).
        catalogo_prompt = _filtrar_catalogo(catalogo, requerimiento)
        prompt_usuario = (
            f"Folio: {folio}\n"
            f"Negocio: {negocio.upper()}\n"
            f"Requerimiento del cliente: {requerimiento}\n"
            f"Catálogo disponible ({len(catalogo)} productos en total, "
            f"estos son los que calzan con el pedido): {catalogo_prompt}\n"
            f"Contexto: {contexto}\n\n"
            f"Genera exactamente 3 opciones de cotización (Estándar / Premium / Cierre agresivo). "
            f"Incluye desglose, total y próximo paso accionable."
        )
        try:
            cotizacion = await _lm.responder(
                self._groq, PROMPT_COTIZADOR, prompt_usuario,
                max_tokens=900, temperature=0.3, modelo=_MODELO)
            self.stats["exitosos"] += 1
            await self._registrar("cotizacion_generada", {
                "folio": folio, "negocio": negocio,
                "requerimiento": requerimiento[:100], "preview": cotizacion[:200]
            })
            return {
                "status": "OK",
                "motor": self.motor_id,
                "folio": folio,
                "negocio": negocio,
                "cotizacion": cotizacion,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_cotizador: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.8,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorCotizador()
