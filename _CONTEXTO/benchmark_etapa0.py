"""
Etapa 0 — Línea base de tiempos (PLAN_UN_SOLO_ENRUTADOR.md)
Mide los 10 mensajes: 6 casos fallidos reales + 4 normales.
Guarda resultados en _CONTEXTO/LINEA_BASE_ETAPA0.txt
"""
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

URL = "http://localhost:5000/chat"
USER = "anuar"

MENSAJES = [
    # Los 6 casos de la tabla de fallos
    ("F1 - vectorizar",        "coreldrau vectorizar"),
    ("F2 - ruta sola",         r"C:\Users\Administrador\Desktop\alon.jpg"),
    ("F3 - plugin",            "tiene instalado el plugin"),
    ("F4 - diagnostica",       "diagnostica"),
    ("F5 - edita tu archivo",  "edita tu archivo"),
    ("F6 - coachéame",         "coachéame"),
    # 4 mensajes normales representativos
    ("N1 - saludo",            "hola"),
    ("N2 - cotización",        "cotiza unas lámparas H4"),
    ("N3 - agenda hoy",        "¿cuáles son mis citas de hoy?"),
    ("N4 - capacidades",       "¿qué puedes hacer?"),
]

def medir(etiqueta, mensaje):
    payload = json.dumps({
        "mensaje": mensaje,
        "user_id": USER,
        "session_id": "benchmark_etapa0"
    }).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - t0
        respuesta = body.get("respuesta", "")[:80]
        motores   = body.get("motores_usados", [])
        return elapsed, respuesta, motores, None
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return elapsed, "", [], str(e)


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"  AURORA — ETAPA 0: LÍNEA BASE DE TIEMPOS")
    print(f"  {ts}")
    print(f"{'='*60}\n")

    resultados = []
    for etiqueta, mensaje in MENSAJES:
        print(f"  Enviando: {etiqueta!r}...")
        elapsed, respuesta, motores, error = medir(etiqueta, mensaje)
        resultados.append((etiqueta, mensaje, elapsed, respuesta, motores, error))
        estado = "ERROR" if error else "OK"
        print(f"    [{estado}] {elapsed:.2f}s  →  {respuesta!r}")
        if motores:
            print(f"           motores: {motores}")
        if error:
            print(f"           error: {error}")
        print()

    # Resumen
    tiempos = [r[2] for r in resultados]
    print(f"{'='*60}")
    print(f"  RESUMEN")
    print(f"  Min : {min(tiempos):.2f}s")
    print(f"  Max : {max(tiempos):.2f}s")
    print(f"  Prom: {sum(tiempos)/len(tiempos):.2f}s")
    print(f"  Total: {sum(tiempos):.2f}s")
    print(f"{'='*60}\n")

    # Guardar resultado
    outpath = r"C:\AURORA.worktrees\_CONTEXTO\LINEA_BASE_ETAPA0.txt"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(f"AURORA — ETAPA 0: LÍNEA BASE DE TIEMPOS\n")
        f.write(f"Fecha: {ts}\n")
        f.write(f"{'='*60}\n\n")
        for etiqueta, mensaje, elapsed, respuesta, motores, error in resultados:
            f.write(f"[{etiqueta}]\n")
            f.write(f"  mensaje : {mensaje!r}\n")
            f.write(f"  tiempo  : {elapsed:.3f}s\n")
            f.write(f"  motores : {motores}\n")
            f.write(f"  respuesta: {respuesta!r}\n")
            if error:
                f.write(f"  ERROR   : {error}\n")
            f.write("\n")
        f.write(f"{'='*60}\n")
        f.write(f"Min : {min(tiempos):.3f}s\n")
        f.write(f"Max : {max(tiempos):.3f}s\n")
        f.write(f"Prom: {sum(tiempos)/len(tiempos):.3f}s\n")
        f.write(f"Total: {sum(tiempos):.3f}s\n")

    print(f"  Guardado en: {outpath}")


if __name__ == "__main__":
    main()
