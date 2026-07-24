# -*- coding: utf-8 -*-
"""
AURORA · PANELES CEREBRO
Expone el ESTADO REAL de tres motores del "cerebro" que YA existen en AURORA,
para mostrarlos en un panel. NO simula: lee introspección directa de los módulos.

Motores:
  · Autoconocimiento     → CEREBRO/auto_conocimiento.py  (inventario/capacidades reales)
  · Sueño + Auto-reparación → MEMORIA/motor_sueno.py + CEREBRO/auto_reparacion.py
  · Voz                  → VOZ/voz_google.py  (TTS por Google Home Mini, solo salida)

Diseño:
  · Self-contained. Cada función devuelve un dict con "status".
  · Si un motor no carga, devuelve {"status": "no_disponible", "detalle": ...} sin romper.
  · Reutiliza el patrón importlib de MANUALES/aprendizaje.py (_mod), pero prefiere la
    instancia YA cargada en el proceso (sys.modules) para leer el estado VIVO de los
    singletons (contadores de sueño, etc.) cuando corre dentro del servidor.
"""
from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # C:\AURORA.worktrees

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────

def _mod(dotted: str, ruta: Path):
    """
    Carga un módulo. Para singletons con estado vivo (motor_sueno, auto_reparacion)
    prefiere la instancia YA importada en el proceso (sys.modules) o el import por
    nombre de paquete, para no crear una copia fresca con contadores en cero.
    Cae a spec_from_file_location (patrón de aprendizaje.py) si el paquete no resuelve.
    """
    if dotted in sys.modules:
        return sys.modules[dotted]
    try:
        return importlib.import_module(dotted)
    except Exception:
        # Fallback: carga por ruta de archivo (para carpetas sin __init__.py, ej. VOZ)
        spec = importlib.util.spec_from_file_location(dotted.replace(".", "_"), ruta)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m


def _run_async(coro):
    """Ejecuta una corutina de forma segura, haya o no un event loop corriendo."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Ya hay un loop corriendo (endpoint async): ejecuta en un hilo aparte.
        out = {}

        def _worker():
            out["r"] = asyncio.run(coro)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join()
        return out.get("r")


# ─────────────────────────────────────────────────────────────────────
# 1) AUTOCONOCIMIENTO
# ─────────────────────────────────────────────────────────────────────

def autoconocimiento() -> dict:
    """
    Inventario/estado REAL del sistema, leído por AURORA sobre sí misma.
    Usa CEREBRO/auto_conocimiento.py (singleton auto_conocimiento):
      · escanear_estructura()  → módulos por carpeta
      · obtener_capacidades()  → integraciones con/ sin API key, estado de memoria
    """
    try:
        m = _mod("CEREBRO.auto_conocimiento", ROOT / "CEREBRO" / "auto_conocimiento.py")
        ac = m.auto_conocimiento

        async def _todo():
            estructura = await ac.escanear_estructura()
            capacidades = await ac.obtener_capacidades()
            return estructura, capacidades

        estructura, capacidades = _run_async(_todo())

        total_modulos = sum(len(v) for v in estructura.values())
        integraciones = capacidades.get("integraciones", {})
        return {
            "status": "ok",
            "motor": "auto_conocimiento",
            "raiz": str(m.ROOT),
            "total_modulos": total_modulos,
            "estructura": estructura,
            "capacidades": capacidades,
            "integraciones_activas": [k for k, v in integraciones.items() if v],
            "integraciones_inactivas": [k for k, v in integraciones.items() if not v],
            "memoria": capacidades.get("memoria", {}),
            "nota": "Para diagnóstico profundo de sintaxis usar auto_conocimiento.estado_sistema_completo() (compila todos los módulos, más lento).",
        }
    except Exception as e:
        return {"status": "no_disponible", "motor": "auto_conocimiento", "detalle": str(e)[:300]}


# ─────────────────────────────────────────────────────────────────────
# 2) SUEÑO + AUTO-REPARACIÓN
# ─────────────────────────────────────────────────────────────────────

def _estado_sueno() -> dict:
    try:
        m = _mod("MEMORIA.motor_sueno", ROOT / "MEMORIA" / "motor_sueno.py")
        est = m.motor_sueno.estado()  # método sync que ya expone el motor
        est["status"] = "ok"
        return est
    except Exception as e:
        return {"status": "no_disponible", "detalle": str(e)[:300]}


def _estado_memoria() -> dict:
    """Evidencia real de consolidación: contadores en la BD de memoria."""
    try:
        m = _mod("MEMORIA.sistema_memoria", ROOT / "MEMORIA" / "sistema_memoria.py")
        stats = m._estadisticas()  # lectura directa de la BD (episodica/semantica)
        stats["status"] = "ok"
        stats["db_path"] = str(m.DB_PATH)
        return stats
    except Exception as e:
        return {"status": "no_disponible", "detalle": str(e)[:300]}


def _estado_reparacion() -> dict:
    """
    auto_reparacion NO expone un método estado(); reportamos evidencia REAL:
      · groq_disponible (necesario para generar fixes)
      · backups .bak_* en disco (cada fix aplicado deja un backup)
      · episodios 'fix_aplicado' registrados en memoria episódica
    """
    detalle = {"status": "ok", "motor": "auto_reparacion"}
    # ¿Carga el módulo?
    try:
        _mod("CEREBRO.auto_reparacion", ROOT / "CEREBRO" / "auto_reparacion.py")
        detalle["modulo_carga"] = True
    except Exception as e:
        return {"status": "no_disponible", "motor": "auto_reparacion", "detalle": str(e)[:300]}

    detalle["groq_disponible"] = bool(os.getenv("GROQ_API_KEY"))

    # Backups en disco = reparaciones aplicadas (evidencia real)
    try:
        backups = sorted(ROOT.rglob("*.bak_*"))
        detalle["backups_reparacion"] = len(backups)
        detalle["ultimos_backups"] = [b.name for b in backups[-5:]]
    except Exception as e:
        detalle["backups_reparacion"] = "no_disponible"
        detalle["backups_detalle"] = str(e)[:120]

    # Historial de fixes en memoria episódica (tipo_evento='fix_aplicado')
    try:
        import sqlite3
        m = _mod("MEMORIA.sistema_memoria", ROOT / "MEMORIA" / "sistema_memoria.py")
        conn = sqlite3.connect(str(m.DB_PATH))
        n = conn.execute(
            "SELECT COUNT(*) FROM episodica WHERE tipo_evento='fix_aplicado'"
        ).fetchone()[0]
        conn.close()
        detalle["fixes_registrados_memoria"] = n
    except Exception as e:
        detalle["fixes_registrados_memoria"] = "no_disponible"
        detalle["fixes_detalle"] = str(e)[:120]

    return detalle


def sueno_reparacion() -> dict:
    """Estado combinado del motor de sueño + memoria + auto-reparación."""
    sueno = _estado_sueno()
    memoria = _estado_memoria()
    reparacion = _estado_reparacion()
    disponibles = [x["status"] == "ok" for x in (sueno, reparacion)]
    return {
        "status": "ok" if any(disponibles) else "no_disponible",
        "sueno": sueno,
        "memoria": memoria,
        "reparacion": reparacion,
    }


# ─────────────────────────────────────────────────────────────────────
# 3) VOZ
# ─────────────────────────────────────────────────────────────────────

def voz(escanear_red: bool = False) -> dict:
    """
    Estado REAL del subsistema de voz (VOZ/voz_google.py).
    Honesto: es SOLO salida (TTS casteado al Google Home Mini). No hay daemon;
    se invoca bajo demanda. En el chat la voz está SUSPENDIDA (texto es la interfaz).
    Por defecto NO escanea la red (es lento); pasar escanear_red=True para listar Minis.
    """
    try:
        m = _mod("voz_google", ROOT / "VOZ" / "voz_google.py")
        pychromecast_ok = importlib.util.find_spec("pychromecast") is not None
        funciones = [f for f in ("hablar_google", "dispositivos") if hasattr(m, f)]

        estado = {
            "status": "ok",
            "motor": "voz_google",
            "modo": "solo_salida_TTS",
            "activo_en_chat": False,
            "nota": "Voz suspendida en el chat (texto = interfaz). Salida por casting al Google Home Mini bajo demanda.",
            "motor_tts": "Google Translate TTS (translate_tts) casteado por pychromecast",
            "pychromecast_instalado": pychromecast_ok,
            "dispositivo_objetivo": "oficina 2 (Google Home Mini)",
            "alias": getattr(m, "ALIAS", {}),
            "funciones": funciones,
            "requiere_red_local": True,
        }
        if escanear_red and pychromecast_ok:
            try:
                estado["dispositivos_detectados"] = m.dispositivos(timeout=8)
            except Exception as e:
                estado["dispositivos_detectados"] = f"error_escaneo: {str(e)[:120]}"
        return estado
    except Exception as e:
        return {"status": "no_disponible", "motor": "voz_google", "detalle": str(e)[:300]}


# ─────────────────────────────────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────────────────────────────────

def resumen() -> dict:
    """Junta los tres motores del cerebro en un solo dict para el panel."""
    return {
        "status": "ok",
        "autoconocimiento": autoconocimiento(),
        "sueno_reparacion": sueno_reparacion(),
        "voz": voz(),
    }


# ─────────────────────────────────────────────────────────────────────
# PRUEBA STANDALONE
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    for nombre, fn in (
        ("AUTOCONOCIMIENTO", autoconocimiento),
        ("SUENO + REPARACION", sueno_reparacion),
        ("VOZ", voz),
    ):
        print(f"\n{'='*60}\n{nombre}\n{'='*60}")
        print(json.dumps(fn(), ensure_ascii=False, indent=2, default=str))
