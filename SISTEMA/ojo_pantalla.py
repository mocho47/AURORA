# -*- coding: utf-8 -*-
"""AURORA · El ojo de pantalla — qué programa tiene Anuar enfrente.

Anuar lo autorizó el 2026-08-10, después de que yo le recomendara NO hacerlo
esa madrugada y él lo pidiera igual. Queda escrito de quién fue la decisión.

POR QUÉ EXISTE
El ojo del panel ve lo que pasa DENTRO de AURORA. Pero el día real de Anuar es
CorelDRAW → Silhouette Studio → AURORA → WhatsApp, y de esos cuatro AURORA solo
se veía a sí misma. Sin esto, el observador de procesos descubre las rutinas de
un cuarto de su trabajo y cree que son todas.

QUÉ GUARDA — y qué NO, que importa más
Guarda: el nombre del programa, el título de la ventana, cuándo entró y
cuántos segundos estuvo.
NO guarda: nada de lo que hay dentro. Ni teclas, ni pantalla, ni portapapeles,
ni contenido de archivos. No es que esté apagado: no hay código que lo lea.

LOS TRES CANDADOS, PORQUE ESTO MIRA SU TRABAJO
  1. INTERRUPTOR SUYO — `CONFIG/ojo_pantalla.json` con `activo`. Arranca
     APAGADO. Nadie lo prende por él.
  2. NO SE PUEDE ESPIAR EN SILENCIO — mientras corre, `esta_mirando()` dice
     que sí. La barra flotante lo pinta en rojo y no hay forma de dejarlo
     corriendo sin que se vea.
  3. LO PRIVADO NI SE ESCRIBE — hay una lista de programas que jamás se
     anotan (banca, gestores de contraseñas, ventanas de incógnito). No se
     anota y se descarta antes de tocar el disco.

TODO SE QUEDA AQUÍ
Escribe en su propio SQLite de esta PC. No hay red, no hay nube, no hay envío
a ningún lado. Se puede borrar completo con `olvidar_todo()`.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "MEMORIA" / "aurora_memoria.db"
CONFIG = RAIZ / "CONFIG" / "ojo_pantalla.json"

# Cada cuánto se asoma. 3 s es suficiente para saber en qué anda y no gasta
# nada; menos sería mirar más seguido de lo necesario.
CADA_SEG = 3
# Menos de esto no fue trabajo, fue pasar de largo (alt-tab, un clic perdido).
MINIMO_SEG = 5

# Ni se escriben. Se descartan ANTES de tocar el disco: lo que no se guarda no
# se puede filtrar después.
NUNCA = re.compile(
    r"banco|bbva|banorte|santander|hsbc|citibanamex|banamex|nu\b|nubank|"
    r"paypal|mercado\s*pago|clip|billetera|wallet|"
    r"keepass|bitwarden|1password|lastpass|contrasen|password|"
    r"incognito|inprivate|privada|"
    r"\.env\b|token|api.?key|secreto", re.I)


def _config() -> Dict:
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Arranca APAGADO a propósito. Que Anuar lo autorizara no significa que
    # deba estar mirando desde el segundo cero sin que él lo prenda.
    return {"activo": False, "desde": None}


def _guardar_config(d: Dict) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                      encoding="utf-8")


def _preparar() -> None:
    con = sqlite3.connect(str(DB))
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""
            CREATE TABLE IF NOT EXISTS uso_pantalla (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                inicio    TEXT NOT NULL,
                segundos  INTEGER NOT NULL,
                programa  TEXT NOT NULL,
                titulo    TEXT
            )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_uso_ini "
                    "ON uso_pantalla(inicio DESC)")
        con.commit()
    finally:
        con.close()


def _ventana_al_frente() -> Optional[tuple]:
    """(programa, titulo) de lo que está enfrente. None si no se puede saber."""
    try:
        import win32gui
        import win32process
        import psutil
        h = win32gui.GetForegroundWindow()
        if not h:
            return None
        titulo = win32gui.GetWindowText(h) or ""
        _, pid = win32process.GetWindowThreadProcessId(h)
        try:
            prog = psutil.Process(pid).name()
        except Exception:
            prog = "?"
        return prog, titulo
    except Exception:
        return None


def _anotar(programa: str, titulo: str, inicio: float, segundos: int) -> None:
    if segundos < MINIMO_SEG:
        return
    if NUNCA.search(programa) or NUNCA.search(titulo):
        return                                   # ni se escribe
    try:
        _preparar()
        con = sqlite3.connect(str(DB), timeout=3)
        try:
            con.execute(
                "INSERT INTO uso_pantalla (inicio, segundos, programa, titulo)"
                " VALUES (?,?,?,?)",
                (datetime.fromtimestamp(inicio).isoformat(), segundos,
                 programa, titulo[:200]))
            con.commit()
        finally:
            con.close()
    except Exception:
        pass


# ── el hilo que mira ─────────────────────────────────────────────────────
_hilo: Optional[threading.Thread] = None
_parar = threading.Event()


def _bucle() -> None:
    actual, desde = None, time.time()
    while not _parar.is_set():
        v = _ventana_al_frente()
        if v and v != actual:
            if actual:
                _anotar(actual[0], actual[1], desde, int(time.time() - desde))
            actual, desde = v, time.time()
        _parar.wait(CADA_SEG)
    if actual:
        _anotar(actual[0], actual[1], desde, int(time.time() - desde))


def prender() -> Dict:
    """Solo Anuar. Nada dentro de AURORA llama a esto por su cuenta."""
    global _hilo
    if _hilo and _hilo.is_alive():
        return {"status": "ya_estaba", "mirando": True}
    _parar.clear()
    _hilo = threading.Thread(target=_bucle, daemon=True, name="ojo_pantalla")
    _hilo.start()
    _guardar_config({"activo": True, "desde": datetime.utcnow().isoformat()})
    return {"status": "ok", "mirando": True,
            "detalle": "Mirando qué programa tienes enfrente. Solo el nombre "
                       "y el título — nada de lo que hay dentro."}


def apagar() -> Dict:
    _parar.set()
    _guardar_config({"activo": False, "desde": None})
    return {"status": "ok", "mirando": False}


def esta_mirando() -> bool:
    """La verdad del hilo, no lo que diga el archivo de configuración.

    Se lee del hilo vivo a propósito: si alguien editara el JSON para que
    dijera «apagado» mientras el hilo sigue corriendo, esto seguiría diciendo
    la verdad y la barra lo seguiría pintando en rojo.
    """
    return bool(_hilo and _hilo.is_alive() and not _parar.is_set())


# ── lo que ve, para el observador ────────────────────────────────────────

def uso(desde: str = "", limite: int = 5000) -> List[Dict]:
    if not DB.exists():
        return []
    _preparar()
    con = sqlite3.connect(str(DB))
    try:
        q = "SELECT inicio, segundos, programa, titulo FROM uso_pantalla"
        if desde:
            q += f" WHERE inicio >= '{desde}'"
        filas = list(con.execute(q + f" ORDER BY inicio LIMIT {int(limite)}"))
    finally:
        con.close()
    return [{"inicio": i, "segundos": s, "programa": p, "titulo": t}
            for i, s, p, t in filas]


def resumen() -> Dict:
    from collections import Counter
    u = uso()
    minutos = Counter()
    for x in u:
        minutos[x["programa"]] += x["segundos"]
    return {
        "mirando": esta_mirando(),
        "registros": len(u),
        "desde": u[0]["inicio"][:16] if u else None,
        "programas": [(p, round(s / 60)) for p, s in minutos.most_common(10)],
    }


def olvidar_todo() -> Dict:
    """Borra TODO lo que vio. Sin preguntar dos veces: es su información."""
    _preparar()
    con = sqlite3.connect(str(DB))
    try:
        n = con.execute("SELECT count(*) FROM uso_pantalla").fetchone()[0]
        con.execute("DELETE FROM uso_pantalla")
        con.commit()
    finally:
        con.close()
    return {"status": "ok", "borrados": n}


if __name__ == "__main__":
    import io
    import sys
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    r = resumen()
    print(f"Mirando ahora: {'SÍ' if r['mirando'] else 'no'} · "
          f"{r['registros']} registros"
          + (f" desde {r['desde']}" if r["desde"] else ""))
    for p, m in r["programas"]:
        print(f"   {m:5d} min   {p}")
    if not r["registros"]:
        print("\nTodavía no ha mirado nada. Arranca apagado a propósito: "
              "se prende desde la barra.")
