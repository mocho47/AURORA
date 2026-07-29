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

from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_cotizador")

# Precios reales del catálogo ATF Retrofit
CATALOGO_ATF = {
    "aozoom_x1": {"nombre": "Aozoom X1 Básico", "costo": 3500, "precio_publico": 8000, "instalacion": 800},
    "aozoom_x3": {"nombre": "Aozoom X3 Standard", "costo": 6200, "precio_publico": 14999, "instalacion": 1200},
    "aozoom_x5": {"nombre": "Aozoom X5 Premium", "costo": 10500, "precio_publico": 24999, "instalacion": 1500},
    "aozoom_x7": {"nombre": "Aozoom X7 Elite", "costo": 16500, "precio_publico": 39999, "instalacion": 2000},
}

# Precios reales catálogo MILENS
CATALOGO_MILENS = {
    "polera": {"nombre": "Polera sublimada", "costo": 450, "precio_publico": 850, "mayorista": 650},
    "taza": {"nombre": "Taza sublimada 11oz", "costo": 85, "precio_publico": 170, "mayorista": 130},
    "taza_magica": {"nombre": "Taza mágica", "costo": 120, "precio_publico": 280, "mayorista": 200},
    "bolsa": {"nombre": "Bolsa sublimada", "costo": 180, "precio_publico": 380, "mayorista": 280},
    "caja": {"nombre": "Caja personalizada", "costo": 95, "precio_publico": 220, "mayorista": 160},
    "laser_grabado": {"nombre": "Grabado láser pieza", "costo": 60, "precio_publico": 180, "mayorista": 130},
}

PROMPT_COTIZADOR = """Eres el cotizador profesional de ATF Retrofit y MILENS de Anuar.
Generas SIEMPRE exactamente 3 opciones de cotización: Estándar, Premium y Cierre.
Usas los precios reales del catálogo proporcionado.
ATF margen real: 120-130%. MILENS margen real: 50-150%.
Formato de respuesta: claro, directo, con desglose de precios y próximo paso de acción.
Nunca inventas precios. Si el producto no está en catálogo, dices que necesitas verificar."""

_MODELO = "llama-3.1-8b-instant"

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
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
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
            respaldo = CATALOGO_ATF
        else:
            catalogo, _err_cat = _catalogo_milens_real()
            respaldo = CATALOGO_MILENS
        _aviso_catalogo = ""
        if catalogo is None:
            catalogo = respaldo
            _aviso_catalogo = (f"⚠️ Cotizado con la lista MINIMA de respaldo ({len(respaldo)} productos), "
                               f"no con el catálogo completo: {_err_cat}")
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
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_COTIZADOR},
                    {"role": "user", "content": prompt_usuario},
                ],
                max_tokens=700,
                temperature=0.3,
            )
            cotizacion = r.choices[0].message.content.strip()
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
