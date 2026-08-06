# -*- coding: utf-8 -*-
"""Rocío trabaja desde su PC: AURORA tiene que ENTREGARLE los archivos.

Antes generaba la caja y le contestaba con una ruta del disco de Anuar, que
desde su máquina no significa nada. Ahora hay un enlace para bajarla.

Y lo que este archivo cuida de verdad: que ese enlace NO se convierta en
"leer cualquier archivo de la PC por la red". Solo sale lo que AURORA generó.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _cargar_guardia():
    """Saca _es_entregable del servidor sin tener que levantarlo."""
    src = (RAIZ / "CORE" / "aurora_server.py").read_text(encoding="utf-8")
    trozo = re.search(r"_CARPETAS_ENTREGA = .*?return bool\(dentro\.parts\).*?\n",
                      src, re.S)
    assert trozo, "no encontré _es_entregable en aurora_server.py"
    ns = {"Path": Path}
    exec(trozo.group(0), ns)
    return ns["_es_entregable"]


_es_entregable = _cargar_guardia()


def test_entrega_lo_que_aurora_genero(tmp_path, monkeypatch):
    salida = Path.home() / "Downloads" / "dxf"
    salida.mkdir(parents=True, exist_ok=True)
    prueba = salida / "_prueba_entrega.dxf"
    prueba.write_text("0\nSECTION\n", encoding="utf-8")
    try:
        assert _es_entregable(prueba) is True
    finally:
        prueba.unlink(missing_ok=True)


def test_no_entrega_el_env():
    """El .env tiene las llaves. Jamás sale por la red."""
    assert _es_entregable(RAIZ / ".env") is False


def test_no_se_puede_salir_con_puntos():
    """El truco clásico: ../../ para llegar a donde no se debe."""
    trampa = Path.home() / "Downloads" / "dxf" / ".." / ".." / ".ssh" / "id_rsa"
    assert _es_entregable(trampa) is False


def test_no_entrega_programas_de_windows():
    assert _es_entregable(Path("C:/Windows/System32/cmd.exe")) is False


def test_no_entrega_una_carpeta():
    assert _es_entregable(Path.home() / "Downloads" / "dxf") is False
