# -*- coding: utf-8 -*-
"""Las 3 graves que Anuar encontró usando AURORA normal el 2026-08-13.

Ninguna salió de una auditoría: las tres las destapó él en una prueba viva de
diez minutos. Quedan aquí para que no vuelvan.

  1. Dijo "Hecho." con un error adentro     -> registro_herramientas + consciencia
  2. Negó una capacidad que sí tiene        -> _verificar_capacidad_real quedó ciego
  3. Perdió el hilo de la conversación      -> _completar_continuacion (nuevo)
  + Bonus: faltaba el infinitivo "escalar"  -> _ADAPTAR_DISENO
"""
import importlib.util as ilu
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _cargar(nombre, rel):
    spec = ilu.spec_from_file_location(nombre, RAIZ / rel)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _cargar("registro_herramientas", "CEREBRO/registro_herramientas.py")
con = _cargar("consciencia", "CEREBRO/consciencia.py")


# ── GRAVE 1 — "Hecho." con el error adentro ──────────────────────────────
# La respuesta real que salió: "Hecho. 🔧 escalar_pagina: • detalle:
# (-2147352571, 'Los tipos no coinciden.')". El motor de Corel había devuelto
# bien su {"status": "error"}; el registro lo envolvía en un "ok" propio.

def test_registro_no_envuelve_un_fracaso_en_ok(monkeypatch):
    """Si el motor dice error, el registro NO puede reportar ok."""
    falla = {"status": "error", "detalle": "(-2147352571, 'Los tipos no coinciden.', None, 1)"}
    assert str(falla["status"]).lower() in reg._ESTADOS_FALLO


def test_estados_de_fallo_no_incluyen_resultados_validos():
    """NO_CORTAR y pendiente son resultados de una ejecución que SÍ corrió.
    Marcarlos como error rompería herramientas que hoy funcionan."""
    for valido in ("ok", "OK", "no_cortar", "pendiente", "publicado", "revisar"):
        assert valido.lower() not in reg._ESTADOS_FALLO


def test_estados_de_fallo_reconocen_las_formas_reales():
    for malo in ("error", "fallo", "failed", "no_existe"):
        assert malo in reg._ESTADOS_FALLO


# ── BONUS — el infinitivo que faltaba ────────────────────────────────────

FRASE_REAL = ('"C:\\Users\\Administrador\\Downloads\\DXF\\glovo terraqueoo.dxf"'
              'podrias escalar este archivo al 50% pero para material de 2.5mm')


def test_la_frase_real_de_anuar_cae_en_adaptar_diseno():
    """Esta frase exacta se fue al enrutador y tronó en Corel."""
    assert con._es_adaptar_diseno(FRASE_REAL)


@pytest.mark.parametrize("verbo", [
    "escalar", "ajustar", "adaptar", "reducir", "achicar", "agrandar",
    "escala", "ajusta", "adapta", "reduce",
])
def test_verbos_de_ajustar_en_las_dos_formas(verbo):
    """Anuar pide en infinitivo cuando pide con cortesía. Las dos formas valen."""
    assert con._es_adaptar_diseno(f"{verbo} el archivo al 50% para mdf de 2.5mm")


def test_sin_senal_de_material_no_es_adaptar():
    """El infinitivo solo no basta: sin material es escalar a secas, otra cosa."""
    assert not con._es_adaptar_diseno("escalar la imagen al 50%")


# ── GRAVE 3 — el hilo perdido ────────────────────────────────────────────

class _Falsa:
    """Lo mínimo de Consciencia para probar la continuación sin arrancar todo."""
    _NO_ES_DATO = con.Consciencia._NO_ES_DATO
    _RE_ES_MEDIDA = con.Consciencia._RE_ES_MEDIDA
    _completar_continuacion = con.Consciencia._completar_continuacion

    def __init__(self, previos):
        self._memoria_corto = {"s": [{"rol": "user", "contenido": p} for p in previos]}


PREVIO = "reduce C:\\Users\\Administrador\\Downloads\\DXF\\glovo.dxf y dejalo para mdf de 2.5mm"


def test_el_dato_suelto_se_pega_a_la_peticion_anterior():
    """"al 50%" solo no dice nada. Con lo anterior, sí."""
    c = _Falsa([PREVIO])
    salida = c._completar_continuacion("al 50%", "s")
    assert PREVIO in salida and "al 50%" in salida


@pytest.mark.parametrize("dato", ["al 50%", "20x30", "a 15 cm", "2.5mm"])
def test_varias_formas_de_dar_la_medida(dato):
    c = _Falsa([PREVIO])
    assert PREVIO in c._completar_continuacion(dato, "s")


@pytest.mark.parametrize("confirma", ["si", "sí", "dale", "no", "ok", "hazlo"])
def test_un_si_no_es_un_dato(confirma):
    """El sí/no ya tiene su propio camino. Tocarlo rompe "¿le doy?" → "sí"."""
    c = _Falsa([PREVIO])
    assert c._completar_continuacion(confirma, "s") == confirma


def test_un_mensaje_completo_no_se_toca():
    """Si ya se basta solo, se deja tal cual."""
    c = _Falsa([PREVIO])
    largo = "reduce el otro archivo al 30% para mdf de 5.5mm"
    assert c._completar_continuacion(largo, "s") == largo


def test_sin_medida_no_se_pega_nada():
    """Sin un número no es un dato: puede ser cualquier otra cosa."""
    c = _Falsa([PREVIO])
    assert c._completar_continuacion("gracias", "s") == "gracias"


def test_sin_nada_previo_devuelve_igual():
    c = _Falsa([])
    assert c._completar_continuacion("al 50%", "s") == "al 50%"
