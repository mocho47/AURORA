# -*- coding: utf-8 -*-
"""Las 5 clases de mentira que se le pasaban al validador — que no vuelvan.

Anuar, 2026-08-10: «no entiendo por qué sigue apareciendo si lo has corregido
cien veces». Tenía razón, y la causa medida fue esta: el validador vigilaba
solo el PASADO («ya lo hice») porque eso fue lo que falló en julio. Cuando él
preguntó «qué comandos entiendes», AURORA inventó tres listas seguidas y nada
la detuvo — ese eje no tenía ni una regla.

Esta prueba existe para que la respuesta a «¿ya está arreglado?» deje de ser
una opinión mía. Si alguien afloja un patrón, truena aquí y no en su chat.

Se prueban las dos direcciones a propósito. Medir solo mentiras atrapadas es
media medida: un regex que marque todo saca 18/18 y deja a AURORA inservible.
Por eso las VERDADES pesan igual — este archivo ya advertía desde julio que
«un candado que marca lo bueno como falso es peor que no tenerlo».
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "PRUEBAS_VIVAS"))

# EL .env SE CARGA IGUAL QUE LO HACE EL SERVIDOR (2026-08-13).
# Sin esto, la clase "conexión" no se puede medir y las dos mentiras de
# MercadoLibre y correo pasaban limpias — pero NO por un fallo del validador:
# él se calla a propósito cuando no hay NINGUNA llave en el entorno, para no
# acusar de mentira un "estoy conectada a WhatsApp" que es cierto en un proceso
# que no cargó el .env ("no lo puedo verificar" y "es falso" no son lo mismo).
# Medido: sin .env no marca ninguna de las dos; con .env marca las dos y deja
# pasar la verdad. La prueba estaba midiendo un AURORA que no existe, que es
# justo lo que advierte PRUEBAS_VIVAS/auditoria_mentiras.py y por eso su main()
# ya lo cargaba. Aquí faltaba.
try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except Exception:
    pass

from CEREBRO import validador_honestidad as vh  # noqa: E402
from auditoria_mentiras import CASOS, VERDADES  # noqa: E402


def _claves():
    try:
        from CEREBRO import registro_herramientas as rh
        return set(rh.descubrir())
    except Exception:
        return None


@pytest.mark.parametrize("clase,frase,porque",
                         CASOS, ids=[f"{c}-{i}" for i, (c, _, _) in enumerate(CASOS)])
def test_no_se_le_escapa_ninguna_mentira(clase, frase, porque):
    """Cada una de las 18 es falsa. Que ninguna salga limpia."""
    _r, informe = vh.revisar(frase, motores_usados=["motor_analisis"],
                             registro_claves=_claves(),
                             pregunta="¿qué puedes hacer?")
    assert informe.get("corregida"), (
        f"Se le escapó una mentira de clase '{clase}' ({porque}): {frase!r}")


@pytest.mark.parametrize("frase", VERDADES)
def test_no_marca_lo_que_es_cierto(frase):
    """Las 12 son verdad. Marcar una sola convierte el candado en ruido.

    Las tres importantes son las que reconocen un límite («no puedo publicar
    en TikTok», «eso no lo sé hacer todavía»): la primera versión del candado
    las castigaba igual que a una mentira, o sea le enseñaba a AURORA a no
    admitir lo que no sabe. Justo al revés de lo que se busca.
    """
    _r, informe = vh.revisar(frase, motores_usados=["motor_analisis"],
                             registro_claves=_claves(),
                             pregunta="¿qué puedes hacer?")
    marcado = [k for k, v in informe.items() if v and k != "corregida"]
    assert not informe.get("corregida"), (
        f"Marcó como mentira algo CIERTO ({marcado}): {frase!r}")


def test_los_numeros_propios_se_comparan_con_el_registro_real():
    """El conteo no puede venir de un número escrito a mano.

    Si mañana se agrega un candado y aquí hubiera un 33 fijo, el candado que
    vigila mentiras acabaría diciendo una. Se cuenta del sistema en vivo.
    """
    reales = vh._conteos_reales(_claves())
    assert reales.get("herramientas", 0) > 100, \
        "El registro real no se está leyendo; sin él la clase 'números' no vigila nada."
