# -*- coding: utf-8 -*-
"""AURORA · El ojo del panel — lo que Anuar hace con el ratón, no con el chat.

Anuar lo autorizó el 2026-08-10 después de que saliera el hueco: el panel
—donde de verdad trabaja— **no registraba absolutamente nada**. Un año de
clics en Órdenes, Cotizar, Contabilidad y Publicar sin dejar un solo rastro.
El observador de procesos nacía tuerto: solo veía el chat, que es la mitad
chica de su día.

POR QUÉ UN MIDDLEWARE Y NO 202 PARCHES
La regla de la casa, otra vez: una línea en el punto único por donde pasa
todo, no doscientas repartidas. Si mañana se agrega un endpoint nuevo, el ojo
lo ve sin que nadie se acuerde de avisarle.

QUÉ SE GUARDA Y QUÉ NO — esto importa
Se guarda: la hora, el método, la ruta y cuánto tardó.
NO se guarda el cuerpo de la petición. Por ahí pasan nombres de clientes,
teléfonos y precios, y para descubrir que «cotizar va seguido de orden» no
hace falta saber de quién era la orden. Lo que no se guarda no se puede
filtrar después.

EL RUIDO ERA EL RIESGO REAL
El panel se pregunta solo cada 60 s por alertas y cada 3 min por el taller.
Sin filtrar, 9 de cada 10 renglones serían el panel hablando consigo mismo y
el observador «descubriría» que Anuar consulta alertas 1,400 veces al día.
Por eso hay una lista de rutas que se ignoran: no es pereza, es que el
sondeo automático no es una decisión suya.
"""
from __future__ import annotations

import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import List

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "MEMORIA" / "aurora_memoria.db"

# Lo que el panel se pregunta SOLO, sin que Anuar toque nada.
_SONDEO = re.compile(
    r"^/(health|$)|/alertas|/taller/alertas|/estado$|/whatsapp/estado|"
    r"/consola/motores$|/bus/estado|/sistema/salud", re.I)
# Lo que no es una acción del negocio: el panel en sí, archivos, documentación.
_NO_ES_ACCION = re.compile(
    r"^/(panel|docs|openapi\.json|redoc|favicon\.ico|static/|manuales/)", re.I)

_listo = False


def _preparar() -> None:
    global _listo
    if _listo:
        return
    con = sqlite3.connect(str(DB))
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""
            CREATE TABLE IF NOT EXISTS acciones_panel (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metodo    TEXT NOT NULL,
                ruta      TEXT NOT NULL,
                http      INTEGER,
                ms        INTEGER
            )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_panel_ts "
                    "ON acciones_panel(timestamp DESC)")
        con.commit()
    finally:
        con.close()
    _listo = True


def vale_la_pena(metodo: str, ruta: str) -> bool:
    """¿Esto lo decidió Anuar, o se lo preguntó el panel a sí mismo?"""
    if _NO_ES_ACCION.match(ruta) or _SONDEO.match(ruta):
        return False
    # El chat ya se registra en interacciones_detalle con mucho más detalle;
    # anotarlo aquí también sería contar dos veces el mismo paso y el
    # observador vería cadenas que no existen.
    if ruta.startswith("/chat"):
        return False
    return True


def anotar(metodo: str, ruta: str, http: int, ms: int) -> None:
    """Nunca revienta: si el ojo falla, el panel tiene que seguir sirviendo."""
    try:
        if not vale_la_pena(metodo, ruta):
            return
        _preparar()
        con = sqlite3.connect(str(DB), timeout=3)
        try:
            con.execute(
                "INSERT INTO acciones_panel (timestamp, metodo, ruta, http, ms)"
                " VALUES (?,?,?,?,?)",
                (datetime.utcnow().isoformat(), metodo, ruta, http, ms))
            con.commit()
        finally:
            con.close()
    except Exception:
        pass


def acciones(desde: str = "", limite: int = 5000) -> List[dict]:
    """Lo que hizo en el panel, en orden. Lo lee el observador de procesos."""
    if not DB.exists():
        return []
    _preparar()
    con = sqlite3.connect(str(DB))
    try:
        q = "SELECT timestamp, metodo, ruta, http, ms FROM acciones_panel"
        if desde:
            q += f" WHERE timestamp >= '{desde}'"
        filas = list(con.execute(q + f" ORDER BY timestamp LIMIT {int(limite)}"))
    finally:
        con.close()
    return [{"ts": t, "metodo": m, "ruta": r, "http": h, "ms": s}
            for t, m, r, h, s in filas]


def resumen() -> dict:
    """Cuánto lleva visto. Sirve para saber si ya hay material que observar."""
    a = acciones()
    from collections import Counter
    c = Counter(x["ruta"] for x in a)
    return {"acciones": len(a),
            "desde": a[0]["ts"][:16] if a else None,
            "mas_usadas": c.most_common(12)}


if __name__ == "__main__":
    import io
    import sys
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    r = resumen()
    print(f"El ojo lleva {r['acciones']} acciones registradas"
          + (f", desde {r['desde']}" if r["desde"] else " (todavía ninguna)"))
    for ruta, n in r["mas_usadas"]:
        print(f"   {n:5d}x  {ruta}")
