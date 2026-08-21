# -*- coding: utf-8 -*-
"""El panel y el servidor tienen que hablar el mismo idioma.

El 2026-08-09 la pantalla nueva de cotizar láser mandaba `ruta` y `merma` por
FormData; el servidor esperaba `archivo` y `velocidad_mm_s` por JSON. Resultado:
422 en cada clic. Se cachó CORRIÉNDOLO —leyendo el código se veía bien— y por
eso no se entrega una pantalla sin haberla llamado de verdad.

Estas pruebas no levantan el servidor: leen los nombres de los campos de los
dos lados y los comparan. Es lo que habría bastado para atraparlo.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PANEL = RAIZ / "TEMPLATES" / "panel-completo.html"
SERVIDOR = RAIZ / "CORE" / "aurora_server.py"


@pytest.fixture(scope="module")
def panel():
    return PANEL.read_text(encoding="utf-8", errors="ignore")


@pytest.fixture(scope="module")
def servidor():
    return SERVIDOR.read_text(encoding="utf-8", errors="ignore")


def _cuerpo(panel, funcion, con_comentarios=True):
    ini = panel.index("async function " + funcion)
    fin = panel.index("\n}", ini)
    txt = panel[ini:fin]
    if not con_comentarios:
        # los comentarios explican los bugs viejos y nombran lo que YA no se
        # usa; leerlos aquí haría fallar la prueba por documentar bien.
        txt = "\n".join(l for l in txt.splitlines()
                        if not l.lstrip().startswith("//"))
    return txt


def test_cotizar_laser_manda_los_campos_que_el_servidor_espera(panel, servidor):
    """Los que pide CotizarCorteReq, ni más ni menos en los obligatorios."""
    m = re.search(r"class CotizarCorteReq\(BaseModel\):(.*?)\n\n", servidor, re.S)
    assert m, "se movió CotizarCorteReq; hay que actualizar esta prueba"
    espera = set(re.findall(r"^\s{4}(\w+)\s*:", m.group(1), re.M))
    cuerpo = _cuerpo(panel, "clCotizar")

    obligatorios = {c for c in espera if "=" not in
                    re.search(rf"{c}\s*:[^\n]*", m.group(1)).group(0)}
    faltan = {c for c in obligatorios if f"{c}:" not in cuerpo}
    assert not faltan, f"el panel no manda: {sorted(faltan)}"

    # y que no invente campos que el servidor no conoce
    enviados = set(re.findall(r"(\w+):\s*(?:ruta|parseFloat|document)", cuerpo))
    sobran = enviados - espera
    assert not sobran, f"el panel manda campos que el servidor ignora: {sorted(sobran)}"


def test_cotizar_laser_manda_json_no_formdata(panel):
    """El endpoint recibe un BaseModel: con FormData contesta 422."""
    cuerpo = _cuerpo(panel, "clCotizar", con_comentarios=False)
    assert "application/json" in cuerpo
    assert "FormData" not in cuerpo, "FormData contra un BaseModel = 422"


def test_no_se_pinta_un_campo_que_nadie_lee(panel):
    """Un input en pantalla que ninguna función lee es una mentira visual.

    Había un «Merma %» que el usuario podía cambiar y no hacía nada: el
    endpoint no recibe merma (el recuadro ya incluye el desperdicio).
    """
    seccion = panel[panel.index('id="cot-laser"'):panel.index('id="cot-caja"')]
    for ident in re.findall(r'id="(cl-[a-z]+)"', seccion):
        assert ident in panel[panel.index("async function clCotizar"):], (
            f"«{ident}» se pinta en pantalla pero clCotizar() nunca lo lee")


def test_activar_equipo_no_tira_el_trabajo_a_la_basura(panel, servidor):
    """Un botón que trabaja y no enseña nada se reporta como «no hace nada».

    `activar_equipo` devuelve `resultado` con el trabajo real —Marketing manda
    ~13 KB: algoritmo por red, estudio de mercado y el plan de posts de hoy— y
    el panel pintaba solo «trabajó». Anuar lo reportó el 2026-08-10 creyendo
    que el botón estaba muerto.
    """
    cuerpo = _cuerpo(panel, "cbrActivar")
    assert "r.resultado" in cuerpo, (
        "cbrActivar ignora `resultado`: el equipo trabaja y no se ve nada")
    assert "sin_accion_central" in cuerpo, (
        "taller y diseño no tienen acción central; sin esta rama parecen rotos")
    # y que el nombre del campo siga siendo el que manda equipos.py
    eq = (RAIZ / "CEREBRO" / "equipos.py").read_text(encoding="utf-8",
                                                     errors="ignore")
    assert '"resultado": resultado' in eq, (
        "cambió el nombre del campo en equipos.py; el panel dejaría de pintarlo")


def test_el_resultado_usa_los_campos_que_el_servidor_devuelve(panel):
    """Lo que se pinta tiene que existir en la respuesta real, medida en vivo.

    Los campos se sacan del DICCIONARIO QUE DEVUELVE el cotizador, no de una
    lista escrita aquí. La lista a mano se desincronizó en cuanto el cotizador
    empezó a devolver `precio` y `avisos` (2026-08-14): la prueba se ponía roja
    por campos que sí existían. Leerlos del código real es lo que la mantiene
    honesta sin mantenimiento.
    """
    import importlib.util as _ilu
    _sp = _ilu.spec_from_file_location("cotizador_corte",
                                       RAIZ / "EDITOR" / "cotizador_corte.py")
    _cc = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(_cc)
    fuente = (RAIZ / "EDITOR" / "cotizador_corte.py").read_text(encoding="utf-8",
                                                               errors="ignore")
    # las claves del `return {...}` de cotizar_corte, tal como están escritas
    reales = set(re.findall(r'^\s{8}"(\w+)":', fuente, re.M))
    assert "total" in reales, "no se pudieron leer las claves del cotizador"

    cuerpo = _cuerpo(panel, "clCotizar")
    usados = set(re.findall(r"\br\.(\w+)", cuerpo))
    inventados = usados - reales - {"error", "detalle"}
    assert not inventados, (
        f"el panel pinta campos que el servidor no manda: {sorted(inventados)}")
