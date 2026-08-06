# -*- coding: utf-8 -*-
"""El validador de honestidad no debe marcar como falso lo que SÍ es cierto.

Un candado que grita cuando no pasa nada es tan dañino como uno mudo: se
desconfía de todo el reporte y se deja de leer. Anuar encontró los dos casos de
aquí abajo el 2026-08-05 usando AURORA normal, no una auditoría.
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from CEREBRO.validador_honestidad import _archivos_inexistentes   # noqa: E402


def test_archivo_real_fuera_del_proyecto_no_se_marca(tmp_path):
    """El caso literal de Anuar: la caja se guardó en Descargas y el validador
    dijo que no existía. Existía, con 75 KB."""
    real = tmp_path / "ClosedBox_20x15_2.7mm.svg"
    real.write_text("<svg/>", encoding="utf-8")
    texto = f"Listo, quedó en `{real}` (75.0 KB)."
    assert _archivos_inexistentes(texto) == []


def test_nombre_suelto_no_se_rejuzga_tras_la_ruta_completa(tmp_path):
    """Aunque el nombre aparezca otra vez sin su ruta, es el mismo archivo."""
    real = tmp_path / "cofre_20x15x7.dxf"
    real.write_text("0\nSECTION\n", encoding="utf-8")
    texto = f"Guardé `{real}`.\nEl archivo cofre_20x15x7.dxf ya está listo."
    assert _archivos_inexistentes(texto) == []


def test_mencionar_una_libreria_no_es_prometer_un_archivo():
    """"boxes.py exporta SVG" habla de la librería, no de un archivo entregado."""
    assert _archivos_inexistentes("boxes.py exporta SVG, no DXF.") == []


def test_sigue_cachando_lo_que_de_verdad_no_existe():
    """Lo importante: el candado no se ablandó, sigue sirviendo."""
    faltan = _archivos_inexistentes(
        r"Corre C:\AURORA.worktrees\NO_EXISTE_ESTE_ARCHIVO.bat para reiniciar.")
    assert any("NO_EXISTE_ESTE_ARCHIVO" in f for f in faltan)
