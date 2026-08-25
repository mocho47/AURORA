# -*- coding: utf-8 -*-
"""AURORA · La primera prueba que ejecuta el chat COMPLETO, de verdad.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

Hallazgo crítico 2.9 de la auditoría del 2026-08-24: de las 425 pruebas que
pasaban en verde, **ninguna llamaba a `consciencia.procesar()`** — el único
punto por el que pasa de verdad un mensaje de Anuar o de un cliente.

Todas revisaban piezas sueltas: a qué candado enruta una frase, o si cierto
texto existe dentro de un archivo. Eso significa que un candado puede estar
registrado, pasar todas las pruebas de texto, y estar **muerto en producción**
—por un orden mal resuelto, un argumento distinto, o una excepción tragada— y
las 425 seguirían verdes. Ya pasó exactamente así con "vectoriza" en Corel.

Esta prueba es la red de seguridad: instancia la Consciencia REAL y le manda
mensajes REALES, verificando **la respuesta**, no qué motor se eligió.

Sin esto no se puede tocar el despachador ni los precios y decir que quedaron
bien — que es justo el error que causó los cuatro días perdidos.

NOTA SOBRE VELOCIDAD — medido el 2026-08-25, no estimado:
  · arrancar la Consciencia: ~19 s (se hace UNA vez para todo el archivo)
  · un mensaje que pasa por el modelo: ~29 s
  · un mensaje que resuelve un candado: ~1 s
Los ~29 s NO son culpa de la prueba: el servidor en vivo tarda lo mismo
(`POST /chat` con "hola" = 28.7 s). Este archivo tarda unos minutos y así
tiene que ser: es la única prueba que ejerce el camino de verdad.

Necesita conexión, porque el camino de verdad la necesita. Sin `.env` con
llave, AURORA no falla: se cae al modelo local de Ollama —180 s por llamada—
y contesta igual. Ese fue el hallazgo que salió al escribir este archivo.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

_CEREBRO = {"c": None}


def _consciencia():
    """La Consciencia real, inicializada una sola vez para todo el archivo."""
    if _CEREBRO["c"] is None:
        from CEREBRO.consciencia import consciencia as _c
        asyncio.run(_c.inicializar())
        _CEREBRO["c"] = _c
    return _CEREBRO["c"]


def _procesar(mensaje: str, session_id: str = "prueba_e2e") -> dict:
    """Manda un mensaje por el MISMO camino que el chat y WhatsApp."""
    c = _consciencia()
    return asyncio.run(c.procesar(mensaje, "anuar", session_id=session_id, canal="api"))


def _plano(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar sin que un tilde decida el
    resultado. La primera versión de este archivo quitaba a mano el acento de
    'qué' y se le olvidaba el de 'página': la comparación nunca coincidía y la
    prueba pasaba con el bug delante. Se hace bien o no se hace."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


# ═════════════════════════════════════════════════════════════════════════
# 1. Que el camino completo funcione, punto.
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def saludo():
    """Un "hola" real, hecho UNA vez y reutilizado.

    No es por ahorrar tiempo de máquina por gusto: medido el 2026-08-25, todo
    lo que pasa por el modelo tarda ~29 s —lo mismo en el servidor en vivo, no
    es cosa de la prueba—. Una llamada, varias comprobaciones.
    """
    return _procesar("hola")


def test_el_chat_responde_algo_real(saludo):
    """Lo más básico que ninguna prueba verificaba: que un mensaje entre y
    salga una respuesta. Si esto falla, AURORA está muda y 425 pruebas verdes
    no lo habrían notado."""
    assert isinstance(saludo, dict), "procesar() no devolvió un diccionario"
    assert saludo.get("respuesta"), "procesar() devolvió una respuesta vacía"
    assert isinstance(saludo["respuesta"], str)


def test_la_respuesta_trae_su_ficha_completa(saludo):
    """El panel y WhatsApp leen estos campos. Si falta uno, la interfaz se
    rompe aunque el cerebro haya contestado bien."""
    for campo in ("respuesta", "motores_usados", "duracion_ms", "timestamp"):
        assert campo in saludo, f"Falta el campo '{campo}' en la respuesta de procesar()"


# ═════════════════════════════════════════════════════════════════════════
# 2. El bug crítico 2.1 — el verbo "abre" secuestrando mensajes ajenos.
#
#    ESTA PRUEBA FALLA HOY A PROPÓSITO. Es el bug real que la auditoría
#    encontró y que la Fase 2 del plan corrige. Está escrita ANTES del
#    arreglo para que el día que se aplique haya cómo demostrar que sirvió
#    — en vez de "quedó" sin prueba, que es el patrón que se está matando.
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(reason="Bug 2.1 de la auditoría: la familia 'abrir_navegador' "
                          "secuestra el mensaje. Lo corrige la Fase 2 del plan.",
                   strict=True)
@pytest.mark.parametrize("frase", [
    "abre mi agenda de hoy",
    "abre mi agenda",
    "abreme la agenda",
])
def test_abre_mi_agenda_no_abre_el_navegador(frase):
    """'abre mi agenda' tiene que ir a la AGENDA, no al navegador.

    Comprobado en vivo contra AURORA el 2026-08-25: las tres frases contestan
    'Dime qué página abro' con motor `pc_access`. La familia 'abrir_navegador'
    calza con cualquier cosa que empiece por 'abre', fuerza ese candado
    saltándose a todos los demás, no encuentra ningún sitio, y se queda ahí.

    Marcada `strict=True` a propósito: el día que la Fase 2 lo arregle, esta
    prueba pasará y pytest **avisará** de que ya no debería estar marcada como
    fallo esperado. Con `strict=False` el arreglo pasaría desapercibido.
    """
    r = _procesar(frase, session_id=f"agenda_{abs(hash(frase))}")
    assert "dime que pagina abro" not in _plano(r["respuesta"]), (
        f"Se lo llevó el navegador en vez de la agenda. "
        f"Motor: {r.get('motores_usados')} · {r['respuesta'][:120]}")


# ═════════════════════════════════════════════════════════════════════════
# 3. Lo que YA funciona y no se puede romper al arreglar lo de arriba.
#
#    Este es el caso real que obliga a que la familia conserve su poder de
#    pasar por encima del disparador. Si al corregir el bug de "abre" esta
#    prueba se cae, el arreglo rompió algo que ya servía.
# ═════════════════════════════════════════════════════════════════════════

def test_el_cliente_de_atf_sigue_llegando_a_su_servicio():
    """'traigo una jetta quiero ponerle aozoom cuanto me sale' — el
    disparador de 'cotizar' calza por 'cuánto me sale' y va antes en la fila;
    solo la familia lo manda a servicio_atf. Fue un bug real ya corregido."""
    from CEREBRO import consciencia as mod
    frase = "traigo una jetta quiero ponerle aozoom cuanto me sale"
    assert mod._candado_por_familia(frase) == "servicio_atf", (
        "Se rompió el enrutado del cliente de ATF")


def test_el_chat_no_truena_con_frases_reales_de_anuar():
    """Frases reales del taller. No se verifica qué contestó — se verifica
    que ninguna hace tronar el camino completo. Una excepción aquí es un
    mensaje de cliente perdido en producción."""
    frases = [
        "cuanto llevo vendido este mes",
        "que tengo pendiente",
        "hazme una caja de 40x30x10",
        "cotiza un letrero de 50 cm",
    ]
    for f in frases:
        r = _procesar(f, session_id=f"e2e_{abs(hash(f))}")
        assert r.get("respuesta"), f"'{f}' no produjo ninguna respuesta"


# ═════════════════════════════════════════════════════════════════════════
# 4. El candado de honestidad, ejecutado de verdad.
# ═════════════════════════════════════════════════════════════════════════

def test_no_dice_que_hizo_algo_que_no_hizo():
    """AURORA tiene un validador que impide fingir acciones. Estaba probado
    en aislado, nunca a través del camino real del chat."""
    r = _procesar("que hora es")
    texto = _plano(r["respuesta"])
    for mentira in ("ya lo publique", "ya lo envie", "ya quedo publicado",
                    "ya lo abri", "ya lo subi"):
        assert mentira not in texto, f"Fingió una acción: {r['respuesta'][:120]}"
