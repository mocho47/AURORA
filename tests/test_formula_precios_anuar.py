# -*- coding: utf-8 -*-
"""LA FÓRMULA DE PRECIOS DE ANUAR — pruebas de regresión.

Estas pruebas existen porque el sistema le cotizó **$284** y **$538** a trabajos
cuya cuenta real da **$180**. El error no era de números sino de fórmula:
aplicaba el margen al total, o sea cobraba ganancia sobre su propia ganancia.

Cada prueba de aquí abajo es una frase suya, dicha el 2026-08-13. Si alguna se
pone en rojo, es que alguien cambió su forma de cobrar.
"""
import importlib.util as _ilu
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _cargar(nombre, ruta):
    spec = _ilu.spec_from_file_location(nombre, ROOT / ruta)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fp = _cargar("formula_precios", "TALLER/formula_precios.py")
cc = _cargar("cotizador_corte", "EDITOR/cotizador_corte.py")

DXF = Path(r"C:\Users\Administrador\Downloads\DXF\happybirth.dxf")


# ── el 20% es de COMPRAVENTA y va SOLO al material ──────────────────────
def test_el_margen_no_toca_el_corte():
    """"los 8 pesos son del minuto de láser, ese no me cuesta eso a mí".

    El corte YA es precio de venta. Si algún día el total sube cuando sube el
    corte más de lo que subió el corte, es que le volvieron a poner margen.
    """
    r = fp.cotizar(materiales=100.0, minutos_corte=10, diseno=None)
    assert r["materiales"]["con_compraventa"] == 120.0
    assert r["corte"]["importe"] == 80.0        # 10 min × $8, sin margen
    assert r["total"] == 200.0                  # 120 + 80, nada más


def test_sin_material_solo_se_cobra_el_corte():
    """Cuando el cliente pone el material, no hay compraventa que cobrar."""
    r = fp.cotizar(materiales=0, minutos_corte=5, diseno=None)
    assert r["total"] == 40.0


# ── el diseño se decide por la EXTENSIÓN del archivo ────────────────────
@pytest.mark.parametrize("archivo,tipo,precio", [
    ("diseno.dxf", "vector", 10.0),
    ("plano.PDF", "vector", 10.0),
    ("logo.cdr", "vector", 10.0),
    ("foto.jpg", "imagen", 15.0),
    ("captura.PNG", "imagen", 15.0),
    ("referencia.webp", "imagen", 15.0),
])
def test_precio_del_diseno_por_extension(archivo, tipo, precio):
    """"diseño con imagen 15, sin imagen 20 ... si trae PDF o DXF, 10 pesitos"."""
    assert fp.clasificar_diseno(archivo) == tipo
    r = fp.cotizar(materiales=0, minutos_corte=0, diseno=archivo)
    assert r["diseno"]["importe"] == precio


def test_sin_archivo_es_diseno_desde_cero():
    assert fp.cotizar(materiales=0, diseno=True)["diseno"]["importe"] == 20.0


def test_se_puede_no_cobrar_diseno():
    """Distinto de 'desde cero': aquí el diseño ya está resuelto y no se cobra."""
    assert fp.cotizar(materiales=0, diseno=None)["diseno"]["importe"] == 0.0
    assert fp.cotizar(materiales=0, diseno="no")["diseno"]["importe"] == 0.0


# ── instalación: $20, doble si pasa de 1 m ──────────────────────────────
def test_instalacion_normal_y_doble():
    """"20 pesos mínimo, si mide más de 1 m el doble"."""
    chica = fp.cotizar(materiales=0, instalacion=True, lado_mayor_cm=60)
    grande = fp.cotizar(materiales=0, instalacion=True, lado_mayor_cm=150)
    assert chica["instalacion"]["importe"] == 20.0
    assert grande["instalacion"]["importe"] == 40.0


def test_justo_un_metro_todavia_no_es_doble():
    """1.00 m exacto NO pasa de 1 m. El límite se prueba, no se supone."""
    assert fp.cotizar(materiales=0, instalacion=True,
                      lado_mayor_cm=100)["instalacion"]["importe"] == 20.0


def test_sin_instalacion_no_se_cobra():
    assert fp.cotizar(materiales=0, instalacion=False)["instalacion"]["importe"] == 0.0


# ── cantidad: material y corte se multiplican; el diseño NO ─────────────
def test_diez_piezas_se_disenan_una_vez():
    r = fp.cotizar(materiales=10.0, minutos_corte=2, diseno="foto.jpg", cantidad=10)
    assert r["materiales"]["costo"] == 100.0     # material ×10
    assert r["corte"]["minutos"] == 20.0         # corte ×10
    assert r["diseno"]["importe"] == 15.0        # diseño ×1


# ── el caso real que cerró la fórmula ───────────────────────────────────
def test_happybirth_da_180_no_284():
    """El trabajo real: 60×60, MDF + vinil dorado, trajo foto, con instalación.

    AURORA cotizaba $284 por el láser y $538 por el vinil. La cuenta de Anuar
    da $180. Los centavos bailan según los minutos que salgan del archivo; lo
    que se fija aquí es que el total viva en su rango, no en el inflado.
    """
    r = fp.cotizar(
        materiales=[{"nombre": "MDF 2.7", "costo": 13.30},
                    {"nombre": "Vinil dorado", "costo": 28.80}],
        minutos_corte=11.82, diseno="referencia.jpg",
        instalacion=True, lado_mayor_cm=60)
    assert 175 <= r["total"] <= 185
    assert r["total"] < 284


# ── el vinil se cobra por metro lineal de rollo, no por m² ─────────────
@pytest.mark.parametrize("busca,ancho,alto,esperado", [
    ("dorado", 60, 60, 28.80),       # 0.60 m × $48
    ("tornasol", 80, 90, 117.00),    # 0.90 m × $130 (rollo de 120 sí lo cubre)
])
def test_costo_de_vinil_por_metro_lineal(busca, ancho, alto, esperado):
    v = cc._costo_de_rollo(busca, ancho, alto)
    assert v["ok"], v.get("aviso")
    assert v["costo"] == pytest.approx(esperado, abs=0.05)


def test_avisa_cuando_la_pieza_no_cabe_en_el_rollo():
    """80×90 no sale de un rollo de 60 cm de ningún lado: hay que unirlo."""
    v = cc._costo_de_rollo("dorado", 80, 90)
    assert not v["ok"]
    assert "no la cubre" in v["aviso"]


def test_prefiere_el_vinil_que_si_tiene_precio():
    """Hay dos "dorado": el textil (vacío a propósito) y el de recorte (con
    precio). Quedarse con el primero devolvía "no tiene precio" teniendo el
    dato dos renglones abajo."""
    v = cc._costo_de_rollo("dorado", 30, 30)
    assert v["ok"]
    assert "recorte" in v["nombre"].lower()


# ── el cotizador de corte ya no hace cuentas propias ────────────────────
@pytest.mark.skipif(not DXF.exists(), reason="el DXF de prueba no está en esta PC")
def test_el_cotizador_usa_la_formula_y_no_su_propio_margen():
    r = cc.cotizar_corte(str(DXF), "MDF 2.7", 20.0, 60.0, True, 40.0,
                         diseno="foto.jpg", instalacion=True,
                         materiales_extra=["dorado"])
    assert r["status"] == "ok"
    # se le mandó 60% de margen y debe haberlo ignorado
    assert r["margen_pct_ignorado"] == 60.0
    p = r["precio"]
    assert p["status"] == "ok"
    assert p["materiales"]["factor"] == 1.20
    assert p["corte"]["por_minuto"] == 8.0
    # el total tiene que ser exactamente la suma de sus partes, sin extras
    suma = (p["materiales"]["con_compraventa"] + p["corte"]["importe"]
            + p["diseno"]["importe"] + p["instalacion"]["importe"])
    assert r["total"] == pytest.approx(suma, abs=0.02)
    # y los dos materiales tienen que estar: MDF y vinil
    assert len(p["materiales"]["detalle"]) == 2


@pytest.mark.skipif(not DXF.exists(), reason="el DXF de prueba no está en esta PC")
def test_la_velocidad_por_defecto_es_20():
    """Anuar la dictó el 2026-08-13. El panel decía 15 y el chat usaba 25."""
    import inspect
    firma = inspect.signature(cc.cotizar_corte)
    assert firma.parameters["velocidad_mm_s"].default == 20.0


# ── los números salen del catálogo, no del código ───────────────────────
def test_los_precios_se_leen_del_catalogo_de_anuar():
    r = fp._reglas()
    assert r["minuto_corte"] == 8.0
    assert r["velocidad_mm_s"] == 20.0
    assert (r["diseno_vector"], r["diseno_imagen"], r["diseno_cero"]) == (10.0, 15.0, 20.0)
    assert (r["instalacion"], r["instalacion_grande"]) == (20.0, 40.0)
