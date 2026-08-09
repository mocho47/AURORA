# -*- coding: utf-8 -*-
"""Las correcciones del perfil de Anuar no pueden pelearse entre ellas.

EL 2026-08-08, al portar el normalizador de voz que él había escrito hace
meses, se metió esta pareja sin darse cuenta:

    "mercado libre" -> "mercadolibre"      (la nueva, de voz)
    "mercadolibre"  -> "mercado libre"     (la que AURORA ya tenía)

Cada una deshace a la otra. El texto sale igual, o distinto según el orden en
que Python recorra el diccionario. Es un bug que no se cae, no da error y se
busca durante horas.

Estas dos pruebas lo hacen imposible de repetir.
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import importlib.util as _ilu                                      # noqa: E402

_s = _ilu.spec_from_file_location("perfil_anuar", RAIZ / "CEREBRO" / "perfil_anuar.py")
pa = _ilu.module_from_spec(_s)
_s.loader.exec_module(pa)


def test_ninguna_regla_deshace_a_otra():
    """Si A se corrige a B, B no puede corregirse de vuelta a A."""
    reglas = {k.lower(): v.lower() for k, v in pa.ERRORES_REALES.items()}
    for malo, bueno in reglas.items():
        vuelta = reglas.get(bueno)
        assert vuelta != malo, (
            f"«{malo}» → «{bueno}» y «{bueno}» → «{malo}» se anulan entre sí. "
            "Hay que decidir cuál de las dos formas es la buena.")


def test_corregir_dos_veces_da_lo_mismo():
    """Pasar el texto por el normalizador otra vez no debe cambiarlo más.

    Si cambia, es que dos reglas se están empujando y el resultado depende de
    cuántas veces se aplique — que es justo lo que no puede pasar en el punto
    por donde entra CADA mensaje.
    """
    frases = (
        "busca el precio en mercado libre",
        "publica en fase book y en tik tok",
        "mandale por guatsap a la clienta",
        "sube el video a yutuf con has tag",
        "cuantas hojas de mdf ocupo para 20 cajas",
        "cotiza el corte laser de esta caja",
    )
    for f in frases:
        una = pa.normaliza(f)
        dos = pa.normaliza(una)
        assert una == dos, f"«{f}» cambia al normalizar dos veces: {una!r} → {dos!r}"


def test_no_se_tocan_las_palabras_del_taller():
    """«hojas» son las de MDF, «agenda» es un motor y «nota» es palabra común.

    El normalizador de voz traía `hojas → sheets`, `agenda → calendar` y
    `nota → notepad`, del vocabulario interno de NEXUS. Aquí romperían el
    cotizador y el motor de agenda, así que NO se portaron.
    """
    for palabra in ("hojas", "agenda", "nota", "documento", "correo"):
        salida = pa.normaliza(f"revisa {palabra} por favor").lower()
        assert palabra in salida, f"«{palabra}» se transformó: {salida!r}"
