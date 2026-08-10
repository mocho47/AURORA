# -*- coding: utf-8 -*-
"""AURORA cobra el vinil con la lista de Anuar, no con un número inventado.

EL 2026-08-08 PASÓ ESTO, en el chat, con un cliente esperando:

    Anuar → «dame el costo del vinil textil de recorte y el corte e
             instalación de las palabras Coca-Cola OSVALDO en un área
             de 30 x 20 cm»
    AURORA → «podría costar entre $500 a $1,500 MXN»

Inventado. Su lista de precios llevaba meses guardada en
CONFIG/catalogo_servicios.json y decía otra cosa: $148. Él lo cobró en $150.
Sus palabras: *"aurora no supo cobrar"*, y después: *"comienza a desesperarme,
creeme que estoy muy cerca de borrarla"*.

Estas pruebas cierran las dos mitades de esa falla: que la pregunta llegue al
cotizador de vinil, y que el número salga de su lista.
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

_v = _ilu.spec_from_file_location("cotizador_vinil",
                                  RAIZ / "TALLER" / "cotizador_vinil.py")
cv = _ilu.module_from_spec(_v)
_v.loader.exec_module(cv)


# ── QUE LA PREGUNTA LLEGUE A DONDE DEBE ─────────────────────────────────
SUS_FRASES = (
    # las dos literales del día que falló
    "dame el costo de el vinil textil de recorte y el costo de el corte e "
    "instalacion de las palabras Coca-Cola OSVALDO EN UN AREA DE 30 X 20 CM",
    "la palabra coca cola y debajo osvaldo en un area de 30cm de largo x 20 cm "
    "de alto que costo tendria",
    "cuanto cuesta un vinil de recorte de 20x20",
    "cuanto sale un vinil textil de 15x10 planchado",
)


def _a_donde_llega(frase: str) -> str:
    for nombre, trigger, _m, _mo in cc._CANDADOS:
        try:
            if trigger(frase):
                return nombre
        except TypeError:
            continue
    return "ninguno"


def test_preguntar_el_precio_del_vinil_llega_al_cotizador_de_vinil():
    for f in SUS_FRASES:
        assert _a_donde_llega(f) == "cotizar_vinil", (
            f"«{f[:50]}...» cayó en {_a_donde_llega(f)}; ahí es donde un motor "
            "suelto le inventó «entre $500 y $1,500»")


def test_no_le_roba_el_trabajo_al_cotizador_laser():
    """Un trabajo de MDF es de láser, aunque pregunte un precio."""
    for f in ("cuanto cuesta cortar una caja de mdf de 30x20",
              "cotiza este acrilico de 40x60",
              "cuanto sale grabar una tabla de madera de 30x20"):
        assert _a_donde_llega(f) != "cotizar_vinil", f


def test_pedir_el_archivo_no_es_pedir_el_precio():
    """«hazme la palabra X» genera el corte; no cotiza."""
    assert _a_donde_llega('hazme "Oswaldo" en vinil de recorte de 30x20') \
        == "texto_a_corte"


# ── QUE EL NÚMERO SALGA DE SU LISTA ─────────────────────────────────────
def test_el_precio_sale_de_su_escalera_real():
    """30×20 con colocación = $148. Él lo cobró en $150."""
    r = cv.precio_de_lista(30, 20, colocar=True)
    assert r["status"] == "OK"
    assert 140 <= r["precio"] <= 155, r
    # y dice de dónde salió, para que él pueda discutirlo
    assert r["apoyado_en"]


def test_nunca_baja_de_su_minimo():
    r = cv.precio_de_lista(2, 2)
    assert r["precio"] >= r["minimo"] > 0


def test_varias_piezas_suman_areas_y_no_precios():
    """SU EJEMPLO REAL GUARDADO: letras 10×28 + números 15×10 = $95.

    Sumando el precio de cada pieza daría $131 —un 38% de más— y esa
    cotización se pierde. La escalera ya trae la economía de escala adentro.
    """
    junto = cv.precio_de_trabajo([(10, 28), (15, 10)])
    aparte = (cv.precio_de_lista(10, 28)["precio"]
              + cv.precio_de_lista(15, 10)["precio"])
    assert junto["precio"] < aparte
    assert 85 <= junto["precio"] <= 105, (junto, "su trabajo real fue $95")


def test_sin_precios_capturados_no_inventa():
    """Lo que no esté capturado se pide por su nombre; no se adivina."""
    c = cv.config("textil")
    for pedido in c["faltan"].values():
        assert "?" in pedido, "un dato faltante se pide preguntando"


def test_la_regla_vive_en_un_solo_lugar():
    """El panel NO debe volver a calcular la regla por su cuenta.

    Se descubrió el 2026-08-09: la suma de áreas estaba escrita dos veces —en
    `precio_de_trabajo` y otra vez en el JavaScript del panel—. Dos copias de
    la misma regla se despegan en cuanto se toca una sola, y el panel se
    quedaría cobrando con la regla vieja sin avisar.
    """
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    panel = (raiz / "TEMPLATES" / "panel-completo.html").read_text(
        encoding="utf-8", errors="ignore")
    ini = panel.index("async function pvCotizar()")
    cuerpo = panel[ini:panel.index("async function pvGuardarConfig()")]
    assert "/taller/vinil/trabajo" in cuerpo, "debe pedirle el precio al motor"
    assert "Math.sqrt" not in cuerpo, (
        "el panel volvió a calcular la regla en JavaScript")


def _consciencia():
    import importlib.util as ilu
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    s = ilu.spec_from_file_location("consc", raiz / "CEREBRO" / "consciencia.py")
    m = ilu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_el_chat_lee_TODAS_las_piezas_del_mensaje():
    """Falla real del 2026-08-09 en el chat en vivo.

    «unas letras de 10x28 y unos números de 15x10» → cotizó $74 (solo las
    letras) en vez de $95, y encima pidió «dímelas todas» después de
    ignorarlas. Leer la primera medida y pedir el resto que ya te dieron.
    """
    c = _consciencia()
    obj = c.Consciencia.__new__(c.Consciencia)
    piezas = obj._todas_las_medidas_cm(
        "cuanto cobro por unas letras de vinil de 10x28 y unos numeros de 15x10")
    assert piezas == [(10.0, 28.0), (15.0, 10.0)], piezas
    assert 85 <= cv.precio_de_trabajo(piezas)["precio"] <= 105


def test_una_sola_pieza_sigue_leyendose_igual():
    """No se rompe el caso normal por arreglar el de varias piezas."""
    c = _consciencia()
    obj = c.Consciencia.__new__(c.Consciencia)
    assert obj._todas_las_medidas_cm("un vinil de recorte de 30x20 cm") == [
        (30.0, 20.0)]
    assert obj._todas_las_medidas_cm("no dije medidas") == []
