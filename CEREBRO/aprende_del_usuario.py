# -*- coding: utf-8 -*-
"""
AURORA · APRENDE CÓMO HABLA SU DUEÑO
====================================

POR QUÉ EXISTE
--------------
Idea de Anuar, 2026-08-02: *"también podría ser que aprendiera del usuario cómo
es que se expresa, tal cual tú lo haces; así no tendrías que inventar el fix,
solo copiarlo"*.

Tenía razón, y es la corrección de raíz que faltaba. Durante dos días el arreglo
fue siempre el mismo: Anuar escribía algo, no lo entendía, y yo agregaba su
frase a una lista a mano. `coreldrau`, `combierte`, `si publicalo`, `corte de
caja`... Eso no se acaba nunca: siempre habrá una forma de decirlo que nadie
anticipó.

Esto lo automatiza. La señal ya está en la conversación y es clarísima:

    "abreme coreldrau porfa"   → no ejecutó nada
    "abre corel"               → ejecutó de verdad
        → aprende: la primera forma también significa eso

CÓMO NO SE ECHA A PERDER
------------------------
Un sistema que aprende solo puede aprender mal y empeorar sin que nadie se
entere. Tres candados para que eso no pase:

1. **Solo aprende de ejecuciones REALES.** Si la segunda forma tampoco hizo
   nada, no se aprende. Una respuesta bonita no cuenta como éxito.
2. **Solo dentro de la misma conversación y con poco tiempo entre medias.** Dos
   mensajes seguidos son una reformulación; dos mensajes con media hora de
   diferencia son dos temas distintos.
3. **Anuar manda.** Puede ver todo lo aprendido y borrar lo que no le guste:
   "qué has aprendido de mí" y "olvida X". Nada es permanente a sus espaldas.

Y algo que vale más de lo que parece: **cada cliente habla distinto**. Un
despacho no dice "chécame el corte de caja". Esto hace que el paquete de dominio
se afine solo en la primera semana de uso, en vez de necesitar a alguien
escribiendo listas de frases para cada negocio.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "CONFIG" / "aprendido_del_usuario.json"

# Una reformulación llega enseguida. Más de esto y son dos temas distintos.
SEGUNDOS_MAX_ENTRE_INTENTOS = 180

# Cuántas veces tiene que confirmarse antes de usarse para enrutar. Con una sola
# vez podría ser casualidad; con dos ya es cómo habla.
VECES_PARA_CONFIAR = 1

# Palabras que no distinguen nada: si el parecido se apoya solo en estas, no vale.
_VACIAS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "a", "en", "con", "por", "para", "que", "y", "o", "me", "te", "se", "lo",
    "mi", "tu", "su", "es", "esta", "este", "esto", "ya", "porfa", "porfavor",
    "please", "ahi", "aqui", "eso", "esa", "ese", "hay",
}


def _norm(texto: str) -> str:
    """Igual criterio que el resto de AURORA: sin acentos, minúsculas, sin ruido."""
    t = "".join(c for c in unicodedata.normalize("NFD", (texto or "").lower())
                if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def _palabras_utiles(texto: str) -> set:
    return {p for p in _norm(texto).split() if len(p) > 2 and p not in _VACIAS}


def _leer() -> Dict:
    if not ARCHIVO.exists():
        return {"aprendido": [], "nota": "Lo que AURORA aprendió de cómo habla su dueño."}
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return {"aprendido": []}


def _guardar(datos: Dict) -> None:
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Memoria de trabajo: qué falló hace un momento, por sesión ────────────────
_FALLOS_RECIENTES: Dict[str, Dict] = {}


def registrar_fallo(session_id: str, mensaje: str, ahora: float) -> None:
    """Este mensaje no ejecutó nada. Se guarda por si el siguiente sí lo hace."""
    if not session_id or not mensaje:
        return
    if not _palabras_utiles(mensaje):
        return
    _FALLOS_RECIENTES[session_id] = {"mensaje": mensaje.strip(), "cuando": ahora}


def registrar_exito(session_id: str, mensaje: str, herramienta: str, ahora: float) -> Optional[Dict]:
    """Este mensaje SÍ ejecutó. Si el anterior falló, se aprende la equivalencia.

    Devuelve lo aprendido, o None si no había nada que aprender.
    """
    if not session_id or not herramienta:
        return None
    previo = _FALLOS_RECIENTES.pop(session_id, None)
    if not previo:
        return None
    if ahora - previo["cuando"] > SEGUNDOS_MAX_ENTRE_INTENTOS:
        return None

    frase_mala = previo["mensaje"]
    a, b = _palabras_utiles(frase_mala), _palabras_utiles(mensaje)
    if not a or not b or a == b:
        return None

    # NO se exige que las dos frases compartan palabras. La primera versión sí lo
    # hacía y por eso no aprendía nunca (probado el 2026-08-02): una reformulación
    # de verdad casi nunca repite las palabras — precisamente por eso es una
    # reformulación.
    #     "echale un ojo a las cuentas del changarro"  vs  "como va la contabilidad"
    #     "abreme coreldrau porfa"                     vs  "abre corel"
    #     "hazme un corte de caja"                     vs  "contabilidad"
    # Ninguna comparte nada, y las tres son el mismo pedido dicho de otro modo.
    #
    # Lo que las relaciona no son las palabras: es que Anuar las escribió una
    # detrás de otra, en menos de tres minutos, y la segunda SÍ ejecutó algo real.
    # Esa secuencia es la señal, y ya está comprobada arriba.

    datos = _leer()
    lista = datos.setdefault("aprendido", [])
    clave = _norm(frase_mala)
    for item in lista:
        if item.get("clave") == clave:
            item["veces"] = int(item.get("veces", 1)) + 1
            item["ultima_vez"] = ahora
            item["herramienta"] = herramienta      # la más reciente manda
            _guardar(datos)
            return item

    nuevo = {
        "clave": clave,
        "como_lo_dijo": frase_mala,
        "que_si_funciono": mensaje.strip(),
        "herramienta": herramienta,
        "veces": 1,
        "aprendido": ahora,
        "ultima_vez": ahora,
    }
    lista.append(nuevo)
    _guardar(datos)
    return nuevo


def buscar(mensaje: str) -> Optional[Dict]:
    """¿Ya aprendimos que Anuar dice las cosas así? Devuelve lo aprendido o None."""
    if not mensaje:
        return None
    palabras = _palabras_utiles(mensaje)
    if not palabras:
        return None

    mejor, mejor_puntaje = None, 0.0
    for item in _leer().get("aprendido", []):
        if int(item.get("veces", 0)) < VECES_PARA_CONFIAR:
            continue
        suyas = _palabras_utiles(item.get("como_lo_dijo", ""))
        if not suyas:
            continue
        # Parecido de Jaccard: cuánto comparten sobre todo lo que hay entre las dos.
        comunes = palabras & suyas
        puntaje = len(comunes) / len(palabras | suyas)
        # Se exige mucho parecido a propósito: enrutar mal por un alias flojo es
        # peor que no tener alias.
        if puntaje >= 0.6 and puntaje > mejor_puntaje:
            mejor, mejor_puntaje = item, puntaje
    if mejor:
        mejor = dict(mejor)
        mejor["parecido"] = round(mejor_puntaje, 2)
    return mejor


def listar() -> List[Dict]:
    """Todo lo aprendido, de lo más usado a lo menos. Para que Anuar lo revise."""
    lista = _leer().get("aprendido", [])
    return sorted(lista, key=lambda x: (-int(x.get("veces", 0)), x.get("clave", "")))


def olvidar(texto: str) -> Dict:
    """Borra lo aprendido que coincida con ese texto. Anuar siempre puede deshacer."""
    if not texto or not texto.strip():
        return {"status": "error", "mensaje": "Dime qué quieres que olvide."}
    datos = _leer()
    antes = datos.get("aprendido", [])
    busca = _norm(texto)
    quedan = [i for i in antes if busca not in i.get("clave", "")
              and busca not in _norm(i.get("como_lo_dijo", ""))]
    borrados = len(antes) - len(quedan)
    if borrados:
        datos["aprendido"] = quedan
        _guardar(datos)
    return {"status": "OK", "borrados": borrados, "quedan": len(quedan)}


def olvidar_todo() -> Dict:
    datos = _leer()
    n = len(datos.get("aprendido", []))
    datos["aprendido"] = []
    _guardar(datos)
    return {"status": "OK", "borrados": n}
