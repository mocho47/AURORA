# -*- coding: utf-8 -*-
"""AURORA · La cadena foto→DXF, corrida completa con una imagen de verdad.

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ EXISTE ESTE ARCHIVO                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

Tercera pieza de la red de seguridad (Fase 1 del plan de reparación de raíz).

Cuando Anuar pega una foto en el chat y pide cortarla, esto es lo que corre:
`EDITOR/imagen_a_dxf.py`, lanzado como subproceso aparte desde
`CEREBRO/consciencia.py`. De ahí sale el archivo que se manda a la máquina.

Es la cadena que más caro sale cuando falla en silencio: un DXF vacío pesa
unos 0.2 KB, **existe**, y sin abrirlo parece que todo salió bien. Ya pasó: se
reportaba éxito de algo que no servía para cortar. El código tiene desde
entonces un candado que revisa entidades y avisa; esta prueba comprueba que
ese candado sigue puesto y funcionando.

QUÉ SE COMPRUEBA — comportamiento, no texto:
  1. Con una imagen real sale un DXF con geometría de verdad y con tamaño.
  2. Con una imagen en blanco NO inventa un archivo: dice que salió vacío.
  3. Con una ruta que no existe avisa, no truena.

TARDA. Trazar es CPU real (bilateral + Canny + vtracer + ezdxf). Es el precio
de probar la cadena en serio en vez de fingir que se probó.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "EDITOR" / "imagen_a_dxf.py"
IMAGEN = RAIZ / "ENTRADAS_CHAT" / "image_LINEA.png"

TIEMPO_LIMITE = 600   # segundos: trazar una imagen real es lento de verdad


def _convertir(ruta, modo="lineal", timeout=TIEMPO_LIMITE) -> dict:
    """Llama a la cadena EXACTAMENTE como la llama AURORA: subproceso + --json."""
    p = subprocess.run([sys.executable, str(SCRIPT), str(ruta), modo, "--json"],
                       capture_output=True, text=True, timeout=timeout, cwd=str(RAIZ))
    salida = (p.stdout or "").strip()
    assert salida, f"La cadena no devolvió nada. stderr: {(p.stderr or '')[-400:]}"
    try:
        return json.loads(salida)
    except json.JSONDecodeError:
        pytest.fail(f"La salida no era JSON —AURORA la lee con json.loads y "
                    f"tronaría igual—: {salida[:300]}")


def _entidades_del_dxf(ruta: Path) -> int:
    """Cuenta lo dibujable de verdad dentro del DXF."""
    import ezdxf
    doc = ezdxf.readfile(str(ruta))
    return sum(1 for _ in doc.modelspace())


# ═════════════════════════════════════════════════════════════════════════
# 1. El camino bueno, con una imagen real del taller.
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not IMAGEN.exists(), reason=f"Falta la imagen de prueba: {IMAGEN}")
def test_una_foto_real_produce_un_dxf_que_si_se_puede_cortar():
    r = _convertir(IMAGEN)
    assert r.get("status") == "OK", f"La cadena no terminó bien: {r}"

    dxf = Path(r["archivo"])
    assert dxf.exists(), f"Dijo OK pero el archivo no está: {dxf}"
    assert dxf.suffix.lower() == ".dxf"

    # Un DXF vacío pesa ~0.2 KB y "existe". El tamaño solo no basta.
    n = _entidades_del_dxf(dxf)
    assert n > 0, (f"El DXF salió sin una sola entidad: no sirve para cortar "
                   f"y aun así reportó OK ({dxf})")
    assert r.get("trazos", 0) > 0, f"Reportó 0 trazos pero dijo OK: {r}"


@pytest.mark.skipif(not IMAGEN.exists(), reason="Falta la imagen de prueba")
def test_el_dibujo_tiene_medidas_de_verdad():
    """Un dibujo sin tamaño no se puede escalar ni cotizar: el cotizador láser
    cobra por el recuadro, y sin recuadro no hay precio."""
    r = _convertir(IMAGEN)
    assert r.get("status") == "OK", r

    import ezdxf
    doc = ezdxf.readfile(r["archivo"])
    puntos = []
    for e in doc.modelspace():
        try:
            puntos.extend([(p[0], p[1]) for p in e.get_points()])
        except Exception:
            continue
    assert puntos, "No se pudo leer ni un punto del DXF"
    ancho = max(p[0] for p in puntos) - min(p[0] for p in puntos)
    alto = max(p[1] for p in puntos) - min(p[1] for p in puntos)
    assert ancho > 0 and alto > 0, f"El dibujo no tiene tamaño: {ancho} x {alto}"


@pytest.mark.skipif(not IMAGEN.exists(), reason="Falta la imagen de prueba")
def test_dice_cuanto_va_a_corte_y_cuanto_a_grabado():
    """El panel muestra estos dos números y de ellos sale el tiempo de máquina,
    que a $8 el minuto es dinero. Hubo un bug real que reportaba 'GRABADO 0
    trazos' aunque sí los hubiera (05-ago)."""
    r = _convertir(IMAGEN)
    assert r.get("status") == "OK", r
    assert "corte" in r and "grabado" in r, f"Faltan los conteos por capa: {r}"
    assert r["corte"] + r["grabado"] == r["trazos"], (
        f"Las capas no suman el total: corte={r['corte']} grabado={r['grabado']} "
        f"total={r['trazos']}")


# ═════════════════════════════════════════════════════════════════════════
# 2. El candado de honestidad dentro de la cadena.
# ═════════════════════════════════════════════════════════════════════════

def test_una_imagen_en_blanco_no_produce_un_dxf_falso(tmp_path):
    """De una hoja en blanco no puede salir nada que cortar. Lo que NO puede
    pasar es que diga OK y entregue un archivo vacío: eso es exactamente el
    fallo silencioso que costó una plancha de material."""
    from PIL import Image
    blanca = tmp_path / "en_blanco.png"
    Image.new("RGB", (600, 600), "white").save(blanca)

    r = _convertir(blanca)
    if r.get("status") == "OK":
        n = _entidades_del_dxf(Path(r["archivo"]))
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
