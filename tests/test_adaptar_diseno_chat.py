# -*- coding: utf-8 -*-
"""AURORA entiende cuando Anuar le pide adaptar un diseño a otro material.

El flujo que él describió el 2026-08-06: *"yo elijo el material y la escala
del tamaño; al poner el espesor del material, este genera los ajustes en
automático, ranuras y largo de dientes"*. Dos perillas y nada más, y con el
número que él quiera.

Las frases de aquí abajo son suyas o calcadas de cómo habla. La primera es
literal, y es la que falló en la primera versión del candado: dice «la casa de
bob», no una ruta — pedirle que escriba rutas sería hacerle trabajo a él para
ahorrárselo al código.
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import importlib.util as _ilu                                      # noqa: E402

_s = _ilu.spec_from_file_location("consciencia", RAIZ / "CEREBRO" / "consciencia.py")
cc = _ilu.module_from_spec(_s)
_s.loader.exec_module(cc)


SI_ENTIENDE = (
    "ajusta la casa de bob al 50% para material de 2.5",     # su frase literal
    "ajusta el crustaceo al 50 % para mdf de 2.5",
    "adapta el archivo dxf a material de 5mm",
    "reduce el diseno al 50% y deja los encastres para 3",
    "pon las hembras del dxf para mdf de 6",
    "deja los encastres de calamardo para 2.5",
    "ajusta el dxf al 120% para material de 9",              # también agranda
)

NO_ES_ESTO = (
    "crea una caja tipo cofre de 20x15x7",           # eso lo hace el generador
    "escala la pagina a 20x30 cm",                   # eso es Corel
    "que tal suena el corte laser en mdf a 60/25",   # es una consulta
    "cuanto cuesta el mdf de 3mm",                   # es un precio
)


def test_entiende_como_lo_pide_anuar():
    for frase in SI_ENTIENDE:
        assert cc._es_adaptar_diseno(frase), f"no entendió: {frase}"


def test_no_se_roba_lo_que_es_de_otro_candado():
    for frase in NO_ES_ESTO:
        assert not cc._es_adaptar_diseno(frase), f"se robó: {frase}"


def test_sin_numeros_no_es_una_orden_de_trabajo():
    """«ajusta el material» sin medidas es plática, no un encargo."""
    assert not cc._es_adaptar_diseno("ajusta el material de los encastres")


def test_escalar_a_secas_no_alcanza():
    """Escalar sin decir el material dejaría los encastres inservibles: ese es
    justo el error que esto existe para evitar."""
    assert not cc._es_adaptar_diseno("reduce el archivo al 50%")


def test_va_antes_que_el_generador_de_cajas():
    """«ajusta ... al 50% para material de 2.5» trae medidas y podría caer en
    el generador de cajas, que le inventaría una caja de 50 cm."""
    orden = [c[0] for c in cc._CANDADOS]
    assert orden.index("adaptar_diseno") < orden.index("generar_caja")
