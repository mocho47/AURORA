# -*- coding: utf-8 -*-
"""AURORA · Una familia tiene que nombrar LA COSA, no nada más el verbo.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

`_FAMILIAS_ANUAR` describe CÓMO PIDE ANUAR cada cosa. Cuando una familia
reconoce un mensaje, su candado se atiende PRIMERO y dispara aunque su propia
lista no lo reconozca. Ese poder es necesario —resuelve colisiones reales como
"traigo una jetta quiero ponerle aozoom cuanto me sale"— y por eso mismo es
peligroso si una familia reclama de más.

El bug 2.1 de la auditoría del 24-ago fue exactamente eso: la familia
`abrir_navegador` empezaba con

    ^(abre|abreme|metete a|entra a|vete a)\\b

un verbo suelto, sin nombrar ninguna cosa. Se llevaba "abre mi agenda de hoy",
"abre el código", y lo que cayera. La agenda nunca era consultada.

ESTA PRUEBA NO CORRIGE ESE PATRÓN. Corrige la clase entera de error: recorre
TODAS las familias —las de hoy y las que se agreguen mañana— y falla si alguna
puede quedarse con una frase que no nombra nada. Así el arreglo no depende de
que alguien se acuerde de la regla.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from CEREBRO import consciencia as C  # noqa: E402


# Frases de puro verbo. Ninguna nombra una cosa: ni un sitio, ni un archivo,
# ni un material, ni un cliente. Ninguna familia debe reclamarlas — para eso
# está la fila normal de candados, que sí sabe mirar el mensaje completo.
FRASES_SIN_SUSTANCIA = [
    "abre", "abre eso", "abreme eso", "abre esto", "abrelo",
    "entra ahi", "vete alla", "metete ahi",
    "hazlo", "hazme eso", "haz esto",
    "dame eso", "damelo", "mandalo", "mandamelo",
    "checa esto", "revisa eso", "ponlo", "sacalo", "quitalo",
]

# Frases reales de Anuar que pertenecen a OTRO candado y que empiezan con un
# verbo que alguna familia podría querer acaparar. Cada una nombra su cosa.
FRASES_DE_OTRO_DUENIO = [
    ("abre mi agenda de hoy", "abrir_navegador"),
    ("abre mi agenda", "abrir_navegador"),
    ("abreme la agenda", "abrir_navegador"),
]


def _familias():
    """Las familias tal como las usa AURORA, ya compiladas."""
    return C._FAMILIAS_ANUAR_COMPILADAS


def test_hay_familias_que_revisar():
    """Si esto se queda en cero, el resto del archivo no prueba nada y estaría
    pasando en verde sin mirar nada. Ha pasado."""
    assert len(_familias()) > 0, "No se pudo leer ninguna familia"


@pytest.mark.parametrize("frase", FRASES_SIN_SUSTANCIA)
def test_ninguna_familia_reclama_una_frase_que_no_nombra_nada(frase):
    """Una familia que se queda con "abre eso" es una red de arrastre."""
    candado = C._candado_por_familia(frase)
    assert candado is None, (
        f"La familia '{candado}' reclama «{frase}», que no nombra ninguna cosa. "
        f"Una familia describe cómo se pide ALGO concreto; un verbo suelto se "
        f"lleva mensajes de otros candados. Métele la cosa al patrón o quítalo: "
        f"el disparador propio del candado sigue funcionando igual.")


@pytest.mark.parametrize("frase,ladron", FRASES_DE_OTRO_DUENIO)
def test_una_familia_no_se_queda_con_lo_que_es_de_otro(frase, ladron):
    """Los casos reales que provocaron esta regla (auditoría 2026-08-24)."""
    assert C._candado_por_familia(frase) != ladron, (
        f"«{frase}» se la sigue llevando la familia '{ladron}'")


def test_cada_patron_de_familia_exige_algo_ademas_del_verbo():
    """Revisión estructural del patrón, no solo de frases de ejemplo.

    Una lista de frases siempre se queda corta: al día siguiente alguien
    escribe una que no está. Esto mira el patrón en sí — si consiste solo en
    verbos, con nada obligatorio detrás, no es una familia.
    """
    import re

    VERBOS = ("abre", "abreme", "abrelo", "metete", "entra", "vete", "haz",
              "hazme", "hazlo", "dame", "damelo", "manda", "mandalo", "checa",
              "revisa", "pon", "ponlo", "saca", "sacalo", "quita", "quitalo")

    culpables = []
    for candado, patrones in _familias():
        for p in patrones:
            # Se prueba el patrón contra el verbo solo y contra el verbo con un
            # pronombre vacío. Si calza, no exige nada más que el verbo.
            for v in VERBOS:
                for frase in (v, f"{v} eso", f"{v} esto"):
                    if p.search(frase):
                        culpables.append((candado, v, p.pattern[:70]))
                        break
                else:
                    continue
                break

    assert not culpables, (
        "Estas familias calzan con un verbo solo:\n" +
        "\n".join(f"  · {c}: «{v}» → {pat}" for c, v, pat in culpables) +
        "\n\nUna familia tiene que nombrar la cosa que se pide.")
