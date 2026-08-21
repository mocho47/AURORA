# -*- coding: utf-8 -*-
"""AURORA · NÚCLEO — el contrato y el único camino de una petición.

Lo pidió Anuar el 2026-08-10, después de una noche de medir: «requiero un
archivo núcleo». Tenía razón en que no existía. `consciencia.py` son 5,380
líneas donde la clase empieza en la 1,844 — antes van 69 funciones sueltas,
casi todas detectores. Detección, ruteo, negocio y modelo, todo revuelto. No
se podía arreglar el núcleo porque no había un núcleo que arreglar.

════════════════════════════════════════════════════════════════════════════
LA REGLA, Y ES UNA SOLA
════════════════════════════════════════════════════════════════════════════
Un motor no se puede ofrecer si no trae CÓMO COMPROBAR QUE HIZO SU TRABAJO.

Todo lo que le falló a Anuar en dos años es la misma falla:

  · La plantilla de tazas dibujaba un recuadro con la palabra "FOTO" y no
    podía recibir una imagen. Corría sin tronar, así que contaba como buena.
  · El adaptador de encastres convirtió 65 de 173 y respondió «✅ adaptado».
    Si él corta esa lámina, tres de cada cuatro dientes no entran.
  · El barrido de las 860 marcó 649 OK. 386 de esos «OK» eran respuestas que
    decían «no sé hacer eso». Medía largo de texto. Lo escribí yo.

Ninguna es un error de cálculo. Las tres son lo mismo: **nadie volvió a mirar
el resultado.** Un número que devuelve la misma función que hizo el trabajo no
es una verificación — es la función felicitándose.

Por eso aquí `verificar` no es opcional ni es un campo más del diccionario:
sin él, `registrar()` levanta ValueError y el motor no entra. No se puede
prometer lo que no se puede comprobar.

════════════════════════════════════════════════════════════════════════════
QUÉ NO HACE ESTE ARCHIVO — dicho antes de que se note
════════════════════════════════════════════════════════════════════════════
No arregla las 444 capacidades. No las toca. Un motor que hoy funciona a
medias va a seguir funcionando a medias: la diferencia es que **lo va a
decir**, en vez de contestar «listo».

Tampoco reemplaza a `consciencia.py`. Vive al lado. Los motores se van
mudando de uno en uno, cuando cada uno tenga su verificador escrito — que es
justo el trabajo que nadie hizo en dos años y el que decide si esto sirve.

Es cimiento, no arreglo. Escrito así a propósito: prometer más sería repetir
exactamente lo que trajo a Anuar hasta aquí.
"""
from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger("aurora.nucleo")


# ══════════════════════════════════════════════════════════════════════════
# 1. LO QUE UN MOTOR DEVUELVE
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Resultado:
    """Lo que pasó de verdad. `hizo` lo pone el VERIFICADOR, no el motor.

    Ésta es toda la idea del archivo. Hoy el motor dice si le fue bien y
    nadie lo revisa. Aquí el motor entrega lo que produjo, y otro código
    —que no sabe nada de sus intenciones— decide si sirve.
    """
    hizo: bool                              # ¿se completó el trabajo?
    detalle: str = ""                       # qué decirle a Anuar, en su idioma
    evidencia: Dict[str, Any] = field(default_factory=dict)
    parcial: bool = False                   # hizo una parte y falta el resto
    salida: str = ""                        # archivo producido, si hubo
    segundos: float = 0.0
    motor: str = ""

    def __bool__(self) -> bool:
        return self.hizo and not self.parcial


# ══════════════════════════════════════════════════════════════════════════
# 2. EL CONTRATO
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Motor:
    """Lo que un motor DEBE declarar para que AURORA lo pueda ofrecer.

    `hace` va en una frase y en el idioma de Anuar porque es lo que se le
    muestra cuando pregunta qué sabe hacer. Hoy esa lista sale de los
    docstrings del código, y por eso una vez le ofreció como capacidad el
    comentario interno de una función mía: «La verdad del hilo, no lo que
    diga el archivo de configuración». Aquí eso no puede pasar: si nadie
    escribió `hace`, el motor no existe para el usuario.
    """
    clave: str
    hace: str
    ejecutar: Callable[..., Any]
    verificar: Callable[[Any, dict], Resultado]
    necesita: Tuple[str, ...] = ()
    peligrosa: bool = False
    probado_en_real: bool = False   # ¿Anuar ya lo usó en un trabajo cobrado?

    def __post_init__(self):
        if not callable(self.verificar):
            raise ValueError(
                f"El motor '{self.clave}' no trae verificador. "
                f"Sin forma de comprobar que hizo su trabajo, no se registra: "
                f"eso es exactamente lo que produjo dos años de '✅ listo' falsos."
            )
        if not (self.hace or "").strip():
            raise ValueError(
                f"El motor '{self.clave}' no dice qué hace en una frase. "
                f"Si no se puede explicar, no se puede ofrecer."
            )


_MOTORES: Dict[str, Motor] = {}


def registrar(motor: Motor) -> Motor:
    """Da de alta un motor. Es el ÚNICO camino para que AURORA lo ofrezca.

    A diferencia del registro viejo, aquí nada entra por existir. El registro
    anterior indexaba cualquier función llamable —incluidos 191 tornillos de
    infraestructura— y los presentaba como capacidades del negocio.
    """
    if motor.clave in _MOTORES:
        logger.warning("Motor '%s' re-registrado; se queda el último.", motor.clave)
    _MOTORES[motor.clave] = motor
    return motor


def catalogo(solo_probados: bool = False) -> Dict[str, str]:
    """Lo que AURORA puede decir que hace. La única fuente para esa respuesta.

    Cuando Anuar pregunta «¿qué comandos entiendes?», la contestación sale de
    aquí y de ningún otro lado. El 2026-08-10 se lo preguntó tres veces y le
    inventó tres listas distintas —una con comandos de Aspire y de Inkscape
    tomados de sus propios manuales— porque no había de dónde sacar la
    verdadera.
    """
    return {k: m.hace for k, m in sorted(_MOTORES.items())
            if m.probado_en_real or not solo_probados}


# ══════════════════════════════════════════════════════════════════════════
# 3. EL CAMINO ÚNICO
# ══════════════════════════════════════════════════════════════════════════

def atender(clave: str, datos: Optional[dict] = None,
            autorizado: bool = False) -> Resultado:
    """Ejecuta un motor y COMPRUEBA el resultado antes de devolverlo.

    Los cuatro pasos, y el tercero es el que no existía:
        1. ¿existe el motor?
        2. ¿están los datos que pide?
        3. ejecutar
        4. VERIFICAR contra la realidad
    """
    datos = dict(datos or {})
    t0 = time.perf_counter()

    motor = _MOTORES.get(clave)
    if motor is None:
        return Resultado(hizo=False, motor=clave,
                         detalle=f"No tengo '{clave}'. No lo intento ni lo simulo.")

    faltan = [c for c in motor.necesita if not datos.get(c)]
    if faltan:
        # Se pregunta ANTES de trabajar. Hacer media tarea y avisar después
        # cuesta material; preguntar cuesta un renglón.
        return Resultado(hizo=False, motor=clave,
                         detalle=f"Me falta {', '.join(faltan)} para hacerlo.",
                         evidencia={"faltan": faltan})

    if motor.peligrosa and not autorizado:
        return Resultado(hizo=False, motor=clave,
                         detalle=f"Esto {motor.hace.lower()} y no tiene vuelta atrás. "
                                 f"¿Le doy?",
                         evidencia={"requiere_autorizacion": True})

    try:
        crudo = motor.ejecutar(**datos)
    except Exception as e:
        logger.error("Motor '%s' tronó: %s\n%s", clave, e, traceback.format_exc())
        return Resultado(hizo=False, motor=clave,
                         segundos=time.perf_counter() - t0,
                         detalle=f"No pude completar {clave} (no lo invento): {e}",
                         evidencia={"excepcion": f"{type(e).__name__}: {e}"})

    # ── El paso que faltaba en todo AURORA ────────────────────────────────
    # El verificador NO recibe lo que el motor opina de sí mismo: recibe lo
    # que produjo, y va a ver el archivo, la base o el disco.
    try:
        r = motor.verificar(crudo, datos)
        if not isinstance(r, Resultado):
            raise TypeError(f"verificar() devolvió {type(r).__name__}, no Resultado")
    except Exception as e:
        # Si no se puede comprobar, NO se declara éxito. Antes, la duda se
        # resolvía a favor del sistema; ahora se resuelve a favor de Anuar,
        # porque el que paga el error con material es él.
        logger.error("Verificador de '%s' falló: %s", clave, e)
        return Resultado(hizo=False, motor=clave,
                         segundos=time.perf_counter() - t0,
                         detalle=f"Corrí {clave} pero no pude comprobar el resultado. "
                                 f"No te digo que quedó bien sin haberlo visto.",
                         evidencia={"fallo_verificador": str(e)})

    r.motor = clave
    r.segundos = time.perf_counter() - t0
    if r.parcial:
        logger.warning("[NÚCLEO] %s quedó PARCIAL: %s", clave, r.detalle)
    return r


def como_esta_todo() -> Dict[str, Any]:
    """Cuántos motores hay, y cuántos probados en un trabajo real.

    Se separan los dos números a propósito. «Registrado» solo quiere decir
    que alguien escribió su verificador. «Probado en real» quiere decir que
    Anuar lo usó y cobró — que es la única definición de terminado que no se
    puede fingir desde este lado de la pantalla.
    """
    return {
        "registrados": len(_MOTORES),
        "probados_en_real": sum(1 for m in _MOTORES.values() if m.probado_en_real),
        "pendientes_de_probar": sorted(k for k, m in _MOTORES.items()
                                       if not m.probado_en_real),
    }
