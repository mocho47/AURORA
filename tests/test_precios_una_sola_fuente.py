# -*- coding: utf-8 -*-
"""AURORA · Los números de Anuar viven en UN solo lugar. Esta prueba lo vigila.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

Fase 3 del plan de reparación de raíz. El bug no era un precio equivocado: era
que los precios estaban COPIADOS en varios archivos. Anuar corregía uno y los
otros seguían mintiendo, sin que nada avisara. Lo que se encontró de verdad:

  · `TALLER/produccion_piezas_grandes.py`, `indexar_dxf.py`, `cajas_boxes.py`
    y `generar_caja.py` traían `VELOCIDAD_MM_S = 25.0`. Él ya había dictado
    **20 mm/s** el 2026-08-13. Cada cotización de esos módulos salía con el
    tiempo de máquina mal, y a $8 el minuto eso es dinero.
  · `MOTORES/motor_cotizador.py` tenía su propia lista de precios: el Aozoom
    X1 en **$8,000** cuando el catálogo real dice **$3,149**.
  · `MOTORES/motor_ventas.py` le decía al vendedor que los faros van de
    "$8k a $40k instalado". El rango real de los proyectores es $1,599–$3,149.

Arreglar los archivos no cierra la fase: mañana alguien vuelve a escribir un
número a mano y nadie se entera. Esta prueba es el candado. Recorre TODO el
proyecto y truena si aparece un precio o una velocidad escritos a mano fuera
de su fuente.

Si esta prueba te falla: no le agregues una excepción. Mueve el número a
`TALLER/formula_precios.py` (o al catálogo que corresponda) y pídelo con
`formula_precios.numero("...")`. Eso es exactamente lo que la prueba cuida.
"""
from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Carpetas que no son el proyecto vivo: historia, respaldos, cachés.
CARPETAS_FUERA = {
    "_OBSOLETOS", "BACKUPS", "__pycache__", ".git", "tests", "node_modules",
    "venv", ".venv", "AUDITORIAS", "ARCHIVO", "build", "dist", ".pytest_cache",
    # FORJA es un proyecto APARTE (NEXUS_v3), declarado fuera del alcance de
    # AURORA. Tiene su propio código y sus propios datos; no se le manda.
    "FORJA",
    # El generador de la versión DEMO escribe datos falsos A PROPÓSITO, para
    # enseñar el sistema sin enseñar los números reales de Anuar.
    "EMPAQUETADO",
}

# LA fuente. Es el único archivo con derecho a tener los números escritos.
FUENTE = RAIZ / "TALLER" / "formula_precios.py"

# Nombres que hablan de dinero o de la máquina.
PALABRAS = ("precio", "costo", "velocidad", "tarifa", "minuto_corte")

# Un nombre que termina en _MM o _CM es una medida física (un margen de 3 mm en
# la hoja), no una tarifa. Se distinguen por el sufijo, no por una lista a mano.
SUFIJOS_GEOMETRIA = ("_MM", "_CM", "_PX", "_DPI", "_MM_S_MIN")


def _archivos():
    for f in RAIZ.rglob("*.py"):
        if any(p in CARPETAS_FUERA for p in f.parts):
            continue
        if f.resolve() == FUENTE.resolve():
            continue
        yield f


def _es_geometria(nombre: str) -> bool:
    return nombre.upper().endswith(SUFIJOS_GEOMETRIA)


def test_ningun_precio_ni_velocidad_escrito_a_mano():
    """Ninguna constante de módulo con nombre de dinero o de velocidad puede
    tener el número escrito en el archivo. Tiene que pedirlo a la fuente."""
    culpables = []
    for f in _archivos():
        try:
            arbol = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for nodo in arbol.body:                      # solo el nivel del módulo
            if not isinstance(nodo, (ast.Assign, ast.AnnAssign)):
                continue
            objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for t in objetivos:
                if not isinstance(t, ast.Name):
                    continue
                if not any(w in t.id.lower() for w in PALABRAS):
                    continue
                if _es_geometria(t.id):
                    continue
                v = nodo.value
                if isinstance(v, ast.Constant) and isinstance(v.value, (int, float)):
                    culpables.append(f"{f.relative_to(RAIZ)}:{nodo.lineno}  "
                                     f"{t.id} = {v.value}")
                elif isinstance(v, ast.Dict) and any(
                        isinstance(x, ast.Constant) and isinstance(x.value, (int, float))
                        for x in v.values):
                    culpables.append(f"{f.relative_to(RAIZ)}:{nodo.lineno}  "
                                     f"{t.id} = {{...{len(v.keys)} números...}}")

    assert not culpables, (
        "Hay números de Anuar escritos a mano fuera de su fuente:\n  "
        + "\n  ".join(culpables)
        + "\n\nMuévelos a TALLER/formula_precios.py y pídelos con "
          "formula_precios.numero('clave'). Un número copiado se queda viejo "
          "sin que nadie lo note — eso es justo lo que pasó con los 25 mm/s.")


def test_los_motores_y_el_cerebro_no_traen_ni_un_precio():
    """Ni MOTORES/ ni CEREBRO/ pueden tener un precio escrito.

    No es una regla de estilo: es la capa que le CONTESTA al cliente. Un precio
    ahí es una copia que nadie ve y que se queda vieja — fue exactamente lo que
    pasó con `motor_cotizador`, que traía el Aozoom X1 en $8,000 mientras el
    catálogo real de Anuar decía $3,149, y con `motor_ventas`, que ofrecía
    "$8k a $40k instalado" cuando los proyectores van de $1,599 a $3,149.

    Estas dos carpetas piden los números; no los guardan. Los guardan
    CONFIG/*.json y TALLER/formula_precios.py, que es lo que Anuar edita.

    Otras carpetas SÍ pueden tener cifras propias cuando son el registro
    original de algo (lo que le cuesta un material a Anuar en
    `TALLER/proveedores.py`, con su fecha; los paquetes de la campaña escolar
    que armó Rocío). Eso no es una copia: es la fuente.
    """
    llaves = {"precio", "precio_publico", "precio_venta", "costo", "mayorista"}
    culpables = []
    for carpeta in ("MOTORES", "CEREBRO"):
        for f in (RAIZ / carpeta).rglob("*.py"):
            if any(p in CARPETAS_FUERA for p in f.parts):
                continue
            try:
                arbol = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for nodo in ast.walk(arbol):
                if not isinstance(nodo, ast.Dict):
                    continue
                for k, v in zip(nodo.keys, nodo.values):
                    if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                            and k.value.lower() in llaves
                            and isinstance(v, ast.Constant)
                            and isinstance(v.value, (int, float))
                            and v.value != 0):
                        culpables.append(f"{f.relative_to(RAIZ)}:{nodo.lineno}  "
                                         f"'{k.value}': {v.value}")
    assert not culpables, (
        "Hay precios escritos dentro de los motores o del cerebro:\n  "
        + "\n  ".join(sorted(set(culpables)))
        + "\n\nEsa capa le contesta al cliente: tiene que LEER el catálogo "
          "(CONFIG/catalogo_atf.json o el de servicios), nunca traer su propia "
          "copia. Una copia se queda vieja y nadie se entera.")


def test_ningun_producto_del_catalogo_tiene_su_precio_repetido_en_codigo():
    """El gemelo de verdad: un producto que YA está en el catálogo de Anuar y
    además tiene su precio escrito en algún .py. Ese es el que se desincroniza.

    La lista de productos NO se escribe aquí: se lee del catálogo real, así que
    el día que Anuar agregue uno queda vigilado solo.
    """
    import json
    cat = json.loads((RAIZ / "CONFIG" / "catalogo_atf.json").read_text(encoding="utf-8"))
    precios_reales = {}
    for p in cat.get("productos", []):
        if p.get("precio"):
            precios_reales.setdefault(float(p["precio"]), []).append(p.get("nombre", ""))
    assert precios_reales, "El catálogo de ATF no trae ni un precio: revísalo"

    llaves = {"precio", "precio_publico", "precio_venta"}
    culpables = []
    for f in _archivos():
        try:
            arbol = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Dict):
                continue
            for k, v in zip(nodo.keys, nodo.values):
                if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                        and k.value.lower() in llaves
                        and isinstance(v, ast.Constant)
                        and isinstance(v.value, (int, float))
                        and float(v.value) in precios_reales):
                    culpables.append(
                        f"{f.relative_to(RAIZ)}:{nodo.lineno}  {v.value} "
                        f"(en el catálogo es: {precios_reales[float(v.value)][0]})")
    assert not culpables, (
        "Estos precios ya viven en CONFIG/catalogo_atf.json y están repetidos "
        "en código:\n  " + "\n  ".join(sorted(set(culpables)))
        + "\n\nBórralos del .py y léelos del catálogo.")


def test_la_fuente_si_tiene_los_numeros_y_los_entrega():
    """El reverso: la fuente tiene que existir y contestar de verdad. Si esta
    prueba pasara con la fuente vacía, las dos de arriba serían decorativas."""
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("formula_precios", FUENTE)
    fp = ilu.module_from_spec(spec)
    spec.loader.exec_module(fp)

    assert fp.numero("velocidad_mm_s") == 20.0, (
        "La velocidad que Anuar dictó el 2026-08-13 es 20 mm/s")
    assert fp.numero("minuto_corte") == 8.0, "Su corte es $8.00 el minuto"
    assert fp.numero("compraventa") == 1.20, "Su margen de material es 1.20"

    # Y que truene con una clave inventada, en vez de devolver 0 calladito.
    import pytest
    with pytest.raises(KeyError):
        fp.numero("precio_que_no_existe")


def test_los_modulos_del_taller_traen_la_velocidad_de_la_fuente():
    """Los cuatro que estaban en 25 mm/s. Se comprueba el valor que de verdad
    queda cargado en cada módulo, no que el archivo mencione la palabra."""
    import importlib.util as ilu
    for rel in ("TALLER/produccion_piezas_grandes.py", "TALLER/indexar_dxf.py",
                "TALLER/cajas_boxes.py", "TALLER/generar_caja.py"):
        spec = ilu.spec_from_file_location(Path(rel).stem, RAIZ / rel)
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        if hasattr(m, "VELOCIDAD_MM_S"):
            assert m.VELOCIDAD_MM_S == 20.0, f"{rel} corre a {m.VELOCIDAD_MM_S} mm/s"
        if hasattr(m, "COSTO_MINUTO"):
            assert m.COSTO_MINUTO == 8.0, f"{rel} cobra {m.COSTO_MINUTO} el minuto"
