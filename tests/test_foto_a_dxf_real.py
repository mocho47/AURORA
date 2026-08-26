# -*- coding: utf-8 -*-
"""AURORA · La cadena foto→DXF, corrida completa y de verdad.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

Tercera pieza de la red de seguridad (Fase 1 del plan de reparación de raíz).

Cuando Anuar pega una foto en el chat y pide cortarla, esto es lo que corre:
`EDITOR/imagen_a_dxf.py`, lanzado como subproceso aparte desde
`CEREBRO/consciencia.py` con modo "lineal". De ahí sale el archivo que va a la
máquina.

Es la cadena que más caro sale cuando falla en silencio: un DXF vacío pesa
unos 0.2 KB, **existe**, y sin abrirlo parece que todo salió bien. Ya pasó: se
reportaba éxito de algo que no servía para cortar. El código tiene desde
entonces un candado que cuenta entidades y avisa; esta prueba comprueba que
ese candado sigue puesto.

POR QUÉ LA IMAGEN SE GENERA AQUÍ Y NO SE TOMA DE `ENTRADAS_CHAT/`:
esa carpeta está en `.gitignore` —son archivos de clientes, no del proyecto—
así que una prueba que dependa de lo que haya ahí pasa en esta PC y no existe
en ninguna otra. La figura se dibuja al vuelo: misma entrada siempre, mismo
resultado siempre, y corre en cualquier equipo.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "EDITOR" / "imagen_a_dxf.py"

# El mismo modo que usa AURORA en el chat (consciencia.py:3982 y 6073).
MODO = "lineal"

# AURORA le da 150 s como máximo en el chat. Aquí se deja más margen porque la
# prueba puede correr con la máquina ocupada, pero no infinito: si se pasa de
# esto, el problema es real y hay que verlo, no esperarlo.
LIMITE = 420


def _convertir(ruta, modo=MODO, timeout=LIMITE) -> dict:
    """Llama a la cadena EXACTAMENTE como la llama AURORA: subproceso + --json."""
    p = subprocess.run([sys.executable, str(SCRIPT), str(ruta), modo, "--json"],
                       capture_output=True, text=True, timeout=timeout, cwd=str(RAIZ))
    salida = (p.stdout or "").strip()
    assert salida, f"La cadena no devolvió nada. stderr: {(p.stderr or '')[-400:]}"
    try:
        return json.loads(salida)
    except json.JSONDecodeError:
        pytest.fail("La salida no era JSON. AURORA la lee con json.loads y se "
                    f"quedaría sin respuesta: {salida[:300]}")


def _entidades(ruta: Path) -> int:
    """Cuenta lo dibujable de verdad dentro del DXF."""
    import ezdxf
    return sum(1 for _ in ezdxf.readfile(str(ruta)).modelspace())


@pytest.fixture(scope="module")
def figura(tmp_path_factory):
    """Una figura negra sobre blanco, del estilo de lo que se manda a cortar.

    Chica a propósito: lo que se prueba es que la cadena entera funcione, no
    cuánto aguanta el trazador. El tamaño real se mide aparte."""
    from PIL import Image, ImageDraw
    ruta = tmp_path_factory.mktemp("dxf") / "figura.png"
    img = Image.new("RGB", (400, 400), "white")
    d = ImageDraw.Draw(img)
    d.ellipse([60, 60, 340, 340], outline="black", width=8)
    d.rectangle([150, 150, 250, 250], outline="black", width=8)
    img.save(ruta)
    return ruta


@pytest.fixture(scope="module")
def resultado(figura):
    """La cadena corrida UNA vez; varias comprobaciones sobre lo mismo."""
    return _convertir(figura)


# ═════════════════════════════════════════════════════════════════════════
# 1. El camino bueno.
# ═════════════════════════════════════════════════════════════════════════

def test_una_figura_produce_un_dxf_que_si_se_puede_cortar(resultado):
    assert resultado.get("status") == "OK", f"La cadena no terminó bien: {resultado}"

    dxf = Path(resultado["archivo"])
    assert dxf.exists(), f"Dijo OK pero el archivo no está: {dxf}"
    assert dxf.suffix.lower() == ".dxf"

    # Un DXF vacío pesa ~0.2 KB y "existe". El tamaño solo no basta.
    n = _entidades(dxf)
    assert n > 0, (f"El DXF salió sin una sola entidad: no sirve para cortar y "
                   f"aun así reportó OK ({dxf})")
    assert resultado.get("trazos", 0) > 0, f"Reportó 0 trazos pero dijo OK: {resultado}"


def test_el_dibujo_tiene_medidas_de_verdad(resultado):
    """Un dibujo sin tamaño no se puede escalar ni cotizar: el cotizador láser
    cobra por el recuadro, y sin recuadro no hay precio."""
    import ezdxf
    puntos = []
    for e in ezdxf.readfile(resultado["archivo"]).modelspace():
        try:
            puntos.extend([(p[0], p[1]) for p in e.get_points()])
        except Exception:
            continue
    assert puntos, "No se pudo leer ni un punto del DXF"
    ancho = max(p[0] for p in puntos) - min(p[0] for p in puntos)
    alto = max(p[1] for p in puntos) - min(p[1] for p in puntos)
    assert ancho > 0 and alto > 0, f"El dibujo no tiene tamaño: {ancho} x {alto}"


def test_dice_cuanto_va_a_corte_y_cuanto_a_grabado(resultado):
    """El panel muestra estos dos números y de ellos sale el tiempo de máquina,
    que a $8 el minuto es dinero. Hubo un bug real que reportaba 'GRABADO 0
    trazos' aunque sí los hubiera (05-ago)."""
    assert "corte" in resultado and "grabado" in resultado, (
        f"Faltan los conteos por capa: {resultado}")
    assert resultado["corte"] + resultado["grabado"] == resultado["trazos"], (
        f"Las capas no suman el total: corte={resultado['corte']} "
        f"grabado={resultado['grabado']} total={resultado['trazos']}")


# ═════════════════════════════════════════════════════════════════════════
# 2. El candado de honestidad dentro de la cadena.
# ═════════════════════════════════════════════════════════════════════════

def test_una_imagen_en_blanco_no_produce_un_dxf_falso(tmp_path):
    """De una hoja en blanco no puede salir nada que cortar. Lo que NO puede
    pasar es que diga OK y entregue un archivo vacío: ese es exactamente el
    fallo silencioso que costó una plancha de material."""
    from PIL import Image
    blanca = tmp_path / "en_blanco.png"
    Image.new("RGB", (400, 400), "white").save(blanca)

    r = _convertir(blanca)
    if r.get("status") == "OK":
        n = _entidades(Path(r["archivo"]))
        pytest.fail(f"Dijo OK con una imagen en blanco y entregó un DXF de "
                    f"{n} entidades. Tiene que avisar, no entregar. {r}")
    assert r.get("status") in ("VACIO", "ERROR"), (
        f"Ante una imagen en blanco contestó algo inesperado: {r}")


def test_una_ruta_que_no_existe_avisa_en_vez_de_tronar():
    """AURORA lee esta salida con json.loads. Si el script muere con una
    excepción, el chat se queda sin respuesta y el cliente sin contestación."""
    r = _convertir(RAIZ / "no_existe_esta_imagen_999.png", timeout=90)
    assert r.get("status") == "NO_EXISTE", f"Debería avisar NO_EXISTE: {r}"
    assert r.get("detalle"), "Avisa que no existe pero no dice cuál"
