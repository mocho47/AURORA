# -*- coding: utf-8 -*-
"""AURORA · CAMPAÑA REGRESO A CLASES 2026 — Milens

Clientas REALES que compraron en julio 2026 y quedaron satisfechas. No es una
lista comprada ni contactos fríos: son personas que ya conocen el taller.

Productos (precios dictados por Anuar el 2026-08-04):
  • Etiquetas para útiles — tabloide suajado en adhesivo de papel: $95
  • Lápices personalizados con láser: $7 c/u
  • Personalización de uniformes: $15 por prenda

NO ENVÍA NADA POR SÍ SOLO. Genera los mensajes para que Anuar los revise; el
envío real es una decisión suya, mensaje por mensaje o en tanda aprobada.

Correr:  python MARKETING/campana_regreso_clases.py           (solo muestra)
         python MARKETING/campana_regreso_clases.py --enviar  (envía de verdad)
"""
from __future__ import annotations
import io
import sqlite3
import sys
import time
from pathlib import Path

# La consola de Windows es cp1252 y truena con los emojis del mensaje. A
# WhatsApp llegan bien: el problema es solo mostrarlos aquí.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# El respaldo de antes de dejar AURORA virgen: ahí viven las órdenes reales.
BD = RAIZ / "_BACKUP_DB_pre_virgen_20260723_235128" / "taller.db"

# Entre envíos. WhatsApp marca como spam las ráfagas: mandar despacio no es
# lentitud, es lo que evita que tumben el número del negocio.
SEGUNDOS_ENTRE_ENVIOS = 45


def _plantilla(nombre: str) -> str:
    """Corto, de persona a persona. Nada de publicidad gritada."""
    # En algunas órdenes se capturó el PRODUCTO donde va el nombre
    # ("servilleteros"). Saludar así delata que es un envío masivo, que es justo
    # lo contrario de lo que se busca: se saluda sin nombre y ya.
    _NO_ES_NOMBRE = ("servillet", "taza", "playera", "vaso", "termo", "orden",
                     "pedido", "cliente", "sin nombre")
    crudo = (nombre or "").strip()
    primer = crudo.split(" ")[0].capitalize()
    if not primer or any(p in crudo.lower() for p in _NO_ES_NOMBRE):
        saludo = "Hola 👋 le saluda *Creaciones Milen's*"
    else:
        saludo = f"Hola {primer} 👋 le saluda *Creaciones Milen's*"
    return (
        f"{saludo}\n\n"
        # Hook: el dolor real de agosto es lo que cuesta el regreso a clases.
        "Ya viene el regreso a clases 🎒 y sabemos lo que se junta en estos "
        "días. Por eso armamos un *paquete de temporada, en apoyo a la "
        "economía del hogar*:\n\n"
        "🎒 *PAQUETE ESCOLAR — $115*\n\n"
        "👕 *6 nombres para las prendas* — en vinil, listos para que usted los "
        "planche donde quiera. No son parches, no se sienten duros y aguantan "
        "lavada tras lavada.\n"
        "     _Colores: dorado, blanco, negro, rosa, verde y rojo_\n\n"
        "📛 *35 etiquetas para todos sus útiles* — libretas, libros, "
        "cuadernos, lápices y colores. Ya cortadas, solo se pegan.\n"
        "     _Y se las hacemos del tema que le guste al niño: dinosaurios, "
        "unicornios, carritos, princesas, de su equipo... usted nos dice_ 🦕⚽\n\n"
        "✖️ *Tabla de multiplicar enmicada* — con el nombre de su hijo, para "
        "que no se le maltrate.\n\n"
        "También personalizamos mochilas, loncheras, termos y cajas de "
        "colores ✨\n\n"
        "Solo mándeme el *nombre del niño* y le paso cómo quedaría, sin "
        "compromiso 🙏\n"
        "📲 3332386943"
    )


def clientas() -> list:
    """Las que tienen teléfono. Sin teléfono no hay a quién escribirle."""
    if not BD.exists():
        return []
    con = sqlite3.connect(f"file:{BD}?mode=ro", uri=True)
    cols = [r[1] for r in con.execute("PRAGMA table_info(ordenes)")]
    c_nom = next((c for c in cols if "cliente" in c.lower()), None)
    c_tel = next((c for c in cols if "tel" in c.lower()), None)
    if not (c_nom and c_tel):
        con.close()
        return []
    vistos, salida = set(), []
    for nom, tel in con.execute(f"SELECT [{c_nom}], [{c_tel}] FROM ordenes"):
        t = "".join(ch for ch in str(tel or "") if ch.isdigit())
        if len(t) < 10 or t in vistos:
            continue
        # Nombres de prueba fuera: no se le escribe a "PruebaFlujo".
        if any(p in str(nom or "").lower() for p in ("prueba", "test", "demo")):
            continue
        vistos.add(t)
        salida.append({"nombre": str(nom or "").strip(), "telefono": t[-10:]})
    con.close()
    return salida


def enviar(tel10: str, texto: str) -> dict:
    """Envío REAL por Green API, el mismo que ya usa AURORA."""
    import os
    import requests
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    idi = os.getenv("GREEN_API_ID_INSTANCE") or os.getenv("GREEN_API_INSTANCE") or ""
    tok = os.getenv("GREEN_API_TOKEN") or os.getenv("GREEN_API_API_TOKEN") or ""
    pre = os.getenv("GREEN_API_SERVER") or "7107"
    if not (idi and tok):
        return {"status": "SIN_CREDENCIALES"}
    url = f"https://{pre}.api.greenapi.com/waInstance{idi}/sendMessage/{tok}"
    try:
        r = requests.post(url, json={"chatId": f"521{tel10}@c.us", "message": texto},
                          timeout=30)
        return {"status": "OK" if r.ok else "ERROR", "detalle": r.text[:150]}
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {e}"}


def main() -> int:
    lista = clientas()
    de_verdad = "--enviar" in sys.argv

    print(f"Clientas con teléfono: {len(lista)}")
    print(f"Modo: {'ENVÍO REAL' if de_verdad else 'solo vista previa (no manda nada)'}")
    print("=" * 66)

    if not de_verdad:
        print("\nASÍ LES LLEGARÍA (ejemplo con la primera):\n")
        if lista:
            print(_plantilla(lista[0]["nombre"]))
        print("\n" + "=" * 66)
        print("A QUIÉNES:\n")
        for i, c in enumerate(lista, 1):
            print(f"  {i:2}. {c['nombre'][:28]:30} {c['telefono']}")
        print(f"\nPara enviar de verdad:  python {Path(__file__).name} --enviar")
        return 0

    ok = 0
    for i, c in enumerate(lista, 1):
        r = enviar(c["telefono"], _plantilla(c["nombre"]))
        marca = "OK " if r["status"] == "OK" else "FALLO"
        print(f"  [{i}/{len(lista)}] {marca} {c['nombre'][:24]:26} {c['telefono']}")
        if r["status"] == "OK":
            ok += 1
        if i < len(lista):
            time.sleep(SEGUNDOS_ENTRE_ENVIOS)
    print(f"\nEnviados: {ok} de {len(lista)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
