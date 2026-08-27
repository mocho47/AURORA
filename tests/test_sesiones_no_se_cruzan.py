# -*- coding: utf-8 -*-
"""Lo de cada quien es de cada quien: dos personas a la vez sin cruzarse.

POR QUÉ EXISTE ESTE ARCHIVO
El 2026-08-27 encontré un bug que yo mismo había metido dos días antes: el
estado de la conversación —el último archivo subido y «estoy esperando tu
lección»— vivía en UNA casilla global del módulo. Rocío entra desde
192.168.1.38 al mismo tiempo que Anuar desde la misma máquina, así que:

  * el «aurora aprende» de uno podía tragarse el mensaje siguiente del otro;
  * el «vectorízalo» de uno podía agarrar la foto que subió el otro — y esa
    foto se va a la cortadora.

No lo reportó nadie. Justamente por eso va la prueba: un bug que nadie ve es
el que se queda años. Se arregló con un ContextVar (por tarea de asyncio) en
vez de pasarle session_id a las 38 pruebas de candado.

QUÉ PRUEBA, EN CONCRETO
Que dos sesiones simultáneas de verdad —corriendo en paralelo con asyncio,
no una tras otra— no se ven el archivo ni la lección. Y que el usuario solo
(el caso de siempre, sin sesión) sigue funcionando igual que antes.
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from CEREBRO import consciencia as c  # noqa: E402



async def _gather(*tareas):
    """Corre varias sesiones DE VERDAD en paralelo. Sin esto la prueba seria
    una tras otra, y una tras otra el bug ni siquiera aparece."""
    return await asyncio.gather(*tareas)


def _limpiar() -> None:
    c._ULTIMO_ARCHIVO.clear()
    c._ESPERANDO_LECCION.clear()


@pytest.fixture(autouse=True)
def _sin_residuos():
    _limpiar()
    yield
    _limpiar()


def _archivo(nombre: str) -> str:
    """Un archivo que existe de verdad: `_archivo_reciente` comprueba el disco
    antes de devolver una ruta, y con razón — nunca manda a cortar un archivo
    que ya no está."""
    p = RAIZ / "ENTRADAS_CHAT" / nombre
    p.parent.mkdir(exist_ok=True)
    p.write_bytes(b"0")
    return str(p)


# ── El archivo de uno no le llega al otro ────────────────────────────────

def test_el_archivo_de_rocio_no_le_llega_a_anuar():
    ruta_anuar = _archivo("prueba_anuar.dxf")
    ruta_rocio = _archivo("prueba_rocio.dxf")
    visto: dict = {}

    async def sesion(quien: str, ruta: str, espera: float):
        c._SESION_ACTUAL.set(quien)
        c.recordar_archivo(ruta, quien)
        # Se cruzan a propósito: mientras uno duerme, el otro escribe.
        await asyncio.sleep(espera)
        visto[quien] = c._archivo_reciente("dxf")

    asyncio.run(_gather(
        sesion("anuar", ruta_anuar, 0.05),
        sesion("rocio", ruta_rocio, 0.01),
    ))

    assert visto["anuar"] == ruta_anuar, "Anuar acabó con el archivo de Rocío"
    assert visto["rocio"] == ruta_rocio, "Rocío acabó con el archivo de Anuar"


def test_una_sesion_no_ve_el_archivo_de_la_otra_si_ella_no_subio_nada():
    """La de al lado no tiene archivo propio: debe quedarse SIN archivo, no
    heredar el ajeno. Es el caso que manda una pieza equivocada a cortar."""
    ruta = _archivo("prueba_solo_anuar.dxf")

    async def anuar():
        c._SESION_ACTUAL.set("anuar")
        c.recordar_archivo(ruta, "anuar")

    async def rocio():
        c._SESION_ACTUAL.set("rocio")
        await asyncio.sleep(0.02)
        return c._archivo_reciente("dxf")

    _, de_rocio = asyncio.run(_gather(anuar(), rocio()))
    assert de_rocio == "", f"Rocío heredó un archivo que no subió: {de_rocio}"


def test_el_usuario_solo_sigue_funcionando_igual():
    """Lo de siempre: se sube sin sesión (el navegador todavía no la manda) y
    el chat lo encuentra. Si esto se rompe, se rompió la piñata de Anuar."""
    ruta = _archivo("prueba_sin_sesion.dxf")
    c.recordar_archivo(ruta)                      # sin session_id, como hoy
    assert c._archivo_reciente("dxf") == ruta


# ── La lección de uno no captura el mensaje del otro ─────────────────────

def test_aurora_aprende_de_uno_no_se_traga_el_mensaje_del_otro():
    resultado: dict = {}

    async def anuar_dicta():
        c._SESION_ACTUAL.set("anuar")
        c._ESPERANDO_LECCION["anuar"] = time.time()   # dijo «aurora aprende»
        await asyncio.sleep(0.03)
        # Su siguiente mensaje SÍ es la lección, aunque no traiga disparador.
        resultado["anuar"] = c._es_aprende_conocimiento("el tabloide mide 33x48")

    async def rocio_cotiza():
        c._SESION_ACTUAL.set("rocio")
        await asyncio.sleep(0.01)
        # Ella no dijo nada de aprender: esto es una cotización, no una lección.
        resultado["rocio"] = c._es_aprende_conocimiento("cotiza 20 llaveros")

    asyncio.run(_gather(anuar_dicta(), rocio_cotiza()))

    assert resultado["anuar"] is True, "Se perdió la lección de quien sí la dictó"
    assert resultado["rocio"] is False, "La lección de Anuar se tragó el mensaje de Rocío"


def test_la_espera_se_cierra_solo_para_quien_la_abrio():
    c._SESION_ACTUAL.set("anuar")
    c._ESPERANDO_LECCION["anuar"] = time.time()
    c._ESPERANDO_LECCION["rocio"] = time.time()

    c._ESPERANDO_LECCION.pop(c._sesion(), None)      # llegó la lección de Anuar

    assert "anuar" not in c._ESPERANDO_LECCION
    assert "rocio" in c._ESPERANDO_LECCION, "Se le cerró la espera a quien no era"


def test_la_leccion_caduca_sola():
    """A los 10 minutos deja de esperar: si no, un «aurora aprende» olvidado
    convierte en lección la siguiente cotización del día."""
    c._SESION_ACTUAL.set("anuar")
    c._ESPERANDO_LECCION["anuar"] = time.time() - (c._VIGENCIA_LECCION_S + 5)
    assert c._es_aprende_conocimiento("cotiza 20 llaveros de mdf") is False
