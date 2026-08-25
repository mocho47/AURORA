# -*- coding: utf-8 -*-
"""AURORA · Los endpoints del taller, golpeados por HTTP de verdad.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

Segunda pieza de la red de seguridad (Fase 1 del plan de reparación de raíz).

Las 425 pruebas que había verificaban funciones sueltas. Ninguna comprobaba
que esas funciones siguieran alcanzables **desde el panel**. Un endpoint puede
romperse por algo que no tiene nada que ver con la lógica —un modelo de
entrada cambiado, un `_ordenes()` que ya no importa, una ruta renombrada— y
todas seguirían verdes mientras el taller deja de cotizar.

QUÉ CUBRE Y QUÉ NO — dicho claro, para que nadie lea de más:
  · SÍ: las rutas reales, la validación real de entrada, y los manejadores
    reales de `CORE/aurora_server.py`, invocados por HTTP.
  · NO: uvicorn, el puerto 5000, ni el arranque de los subsistemas de
    `run_aurora.py` (WhatsApp, motor de sueño, tareas programadas). Eso se
    comprueba a mano al reiniciar, como manda la regla de "reiniciar antes de
    dar por hecho".

REGLA DE ESTA PRUEBA: **no escribe nada**. No crea órdenes, no cambia
estados, no toca precios. El taller es el negocio real de Anuar y una prueba
no tiene por qué dejar basura en la base de trabajo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@pytest.fixture(scope="module")
def cliente():
    """La app REAL de AURORA, servida por HTTP dentro de la prueba."""
    from fastapi.testclient import TestClient
    from CORE.aurora_server import app
    with TestClient(app) as c:
        yield c


# ═════════════════════════════════════════════════════════════════════════
# 1. Que el servidor esté vivo y se presente.
# ═════════════════════════════════════════════════════════════════════════

def test_health_responde_sano(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


# ═════════════════════════════════════════════════════════════════════════
# 2. El catálogo real. 135 productos con precios dictados por Anuar.
# ═════════════════════════════════════════════════════════════════════════

def test_el_catalogo_trae_productos_reales(cliente):
    """Si esto se vacía, el buscador del panel queda mudo y AURORA cotiza al
    aire — que es exactamente el bug que ya costó dinero una vez."""
    r = cliente.get("/taller/catalogo")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0, "El catálogo salió vacío"
    p = d["productos"][0]
    for campo in ("nombre", "precio", "negocio"):
        assert campo in p, f"A los productos les falta '{campo}'"


def test_cada_producto_del_catalogo_tiene_precio_utilizable(cliente):
    """Un producto con precio 0, None o texto es un producto que no se puede
    vender. Se revisa el catálogo COMPLETO, no una muestra."""
    productos = cliente.get("/taller/catalogo").json()["productos"]
    malos = [p["nombre"] for p in productos
             if not isinstance(p.get("precio"), (int, float)) or p["precio"] <= 0]
    assert not malos, f"{len(malos)} producto(s) sin precio usable: {malos[:5]}"


# ═════════════════════════════════════════════════════════════════════════
# 3. Cotizar: el endpoint del que sale el dinero.
# ═════════════════════════════════════════════════════════════════════════

def test_cotizar_un_producto_real_da_el_precio_del_catalogo(cliente):
    """No se compara contra un número escrito a mano aquí —eso sería copiar
    el precio otra vez, la causa raíz de todo esto—. Se compara contra lo que
    el propio catálogo dice."""
    productos = cliente.get("/taller/catalogo").json()["productos"]
    esperado = productos[0]

    r = cliente.post("/taller/cotizar",
                     json={"producto": esperado["nombre"], "cantidad": 1})
    assert r.status_code == 200, r.text
    d = r.json()

    numeros = [v for v in d.values() if isinstance(v, (int, float)) and v > 0]
    assert numeros, f"La cotización no trajo ningún importe: {d}"
    assert esperado["precio"] in numeros, (
        f"'{esperado['nombre']}' vale {esperado['precio']} en el catálogo, "
        f"pero cotizó {numeros}")


def test_cotizar_multiplica_por_la_cantidad(cliente):
    """Dos piezas no pueden costar lo mismo que una."""
    productos = cliente.get("/taller/catalogo").json()["productos"]
    nombre = productos[0]["nombre"]

    def total(cantidad):
        d = cliente.post("/taller/cotizar",
                         json={"producto": nombre, "cantidad": cantidad}).json()
        return max([v for v in d.values() if isinstance(v, (int, float))], default=0)

    uno, tres = total(1), total(3)
    assert tres > uno, f"3 piezas ({tres}) no cuesta más que 1 ({uno})"


def test_cotizar_algo_que_no_existe_no_inventa_un_precio(cliente):
    """El candado de honestidad, visto desde el panel: ante un producto que no
    está en el catálogo, AURORA tiene que decir que no lo tiene — nunca
    devolver una cifra inventada."""
    r = cliente.post("/taller/cotizar",
                     json={"producto": "zzz_producto_que_no_existe_999", "cantidad": 1})
    assert r.status_code in (200, 404), r.text
    if r.status_code == 200:
        d = r.json()
        importes = [v for v in d.values() if isinstance(v, (int, float)) and v > 0]
        assert not importes, f"Inventó un precio para algo inexistente: {d}"


def test_cotizar_sin_producto_se_rechaza(cliente):
    """La validación de entrada tiene que seguir puesta."""
    assert cliente.post("/taller/cotizar", json={"cantidad": 1}).status_code == 422


# ═════════════════════════════════════════════════════════════════════════
# 4. Los tableros que el panel consulta a cada rato.
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ruta", [
    "/taller/precios",
    "/taller/vinilos",
    "/taller/ordenes",
    "/taller/alertas",
])
def test_los_tableros_del_taller_contestan(cliente, ruta):
    """Cada uno alimenta una pestaña del panel. Si uno truena, esa pestaña
    aparece vacía y parece que no hay trabajo — no que se rompió."""
    r = cliente.get(ruta)
    assert r.status_code == 200, f"{ruta} devolvió {r.status_code}: {r.text[:200]}"
    assert r.json() is not None


def test_los_vinilos_listados_se_pueden_cobrar(cliente):
    """El endpoint promete, en su propia documentación, que solo saca los
    vinilos que traen precio Y ancho de rollo — porque sin ancho no se sabe
    cuánto material gasta una pieza, y un menú con opciones que no cotizan es
    peor que no tenerlas (decisión del 14-ago). Esto comprueba esa promesa.
    """
    d = cliente.get("/taller/vinilos").json()
    lista = d if isinstance(d, list) else (d.get("vinilos") or [])
    assert lista, "No salió ningún vinil: el menú de vinil quedaría vacío"

    incompletos = [
        v.get("nombre", v) for v in lista
        if not (isinstance(v.get("precio_metro"), (int, float)) and v["precio_metro"] > 0
                and isinstance(v.get("ancho_rollo_cm"), (int, float)) and v["ancho_rollo_cm"] > 0)
    ]
    assert not incompletos, (
        f"Vinilos listados que no se pueden cotizar: {incompletos[:5]}")
