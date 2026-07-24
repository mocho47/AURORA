# -*- coding: utf-8 -*-
"""
AURORA · OPTIMIZADOR DE PC (mantenimiento real, con mi lógica)
Diagnostica de verdad (RAM/procesos/disco), limpia temporales SEGURO,
y da recomendaciones honestas. NO usa "optimizadores mágicos". Cero simulación.
"""
from __future__ import annotations
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil


def diagnostico() -> dict:
    vm = psutil.virtual_memory()
    procs = []
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            procs.append((p.info["name"], p.info["memory_info"].rss))
        except Exception:
            pass
    # agrupar por nombre (varias pestañas del mismo navegador suman)
    por_nombre = {}
    for n, rss in procs:
        por_nombre[n] = por_nombre.get(n, 0) + rss
    top = sorted(por_nombre.items(), key=lambda x: -x[1])[:8]
    disco = psutil.disk_usage("C:\\")
    return {
        "ram_total_gb": round(vm.total / 1073741824, 1),
        "ram_libre_gb": round(vm.available / 1073741824, 2),
        "ram_uso_pct": vm.percent,
        "top_procesos": [{"nombre": n, "ram_mb": round(r / 1048576)} for n, r in top],
        "disco_libre_gb": round(disco.free / 1073741824),
        "disco_total_gb": round(disco.total / 1073741824),
    }


def limpiar_temporales(horas_antiguedad: float = 2) -> dict:
    """Borra temporales más viejos que N horas (seguro: no toca archivos en uso reciente)."""
    rutas = [os.environ.get("TEMP", ""), r"C:\Windows\Temp"]
    corte = datetime.now() - timedelta(hours=horas_antiguedad)
    liberado = 0
    borrados = 0
    for r in rutas:
        if not r or not os.path.isdir(r):
            continue
        for root, _dirs, files in os.walk(r):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    st = os.stat(fp)
                    if datetime.fromtimestamp(st.st_mtime) < corte:
                        sz = st.st_size
                        os.remove(fp)
                        liberado += sz
                        borrados += 1
                except Exception:
                    pass
    return {"mb_liberados": round(liberado / 1048576), "archivos": borrados}


def _recomendaciones(d: dict) -> list:
    recs = []
    if d["ram_uso_pct"] >= 85:
        recs.append(f"RAM al {d['ram_uso_pct']}% — cierra apps que no uses (navegadores/pestañas de más).")
    if d["ram_total_gb"] <= 8:
        recs.append(f"Solo {d['ram_total_gb']} GB de RAM: subir a 16 GB es el arreglo real y más barato.")
    navs = [p for p in d["top_procesos"] if p["nombre"] in ("msedge.exe", "chrome.exe", "msedgewebview2.exe")]
    if len(navs) >= 2:
        recs.append("Tienes varios navegadores/webviews abiertos — deja solo el que uses.")
    if d["disco_libre_gb"] < 20:
        recs.append("Disco casi lleno — libera espacio.")
    if not recs:
        recs.append("Todo en orden por ahora.")
    return recs


def optimizar() -> dict:
    antes = diagnostico()
    limpieza = limpiar_temporales()
    time.sleep(0.5)
    despues = diagnostico()
    return {
        "status": "ok",
        "antes": {"ram_libre_gb": antes["ram_libre_gb"], "ram_uso_pct": antes["ram_uso_pct"]},
        "limpieza": limpieza,
        "despues": {"ram_libre_gb": despues["ram_libre_gb"], "ram_uso_pct": despues["ram_uso_pct"]},
        "top_procesos": despues["top_procesos"],
        "recomendaciones": _recomendaciones(despues),
    }


if __name__ == "__main__":
    import json, sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "optimizar"
    fn = {"diagnostico": diagnostico, "limpiar": limpiar_temporales, "optimizar": optimizar}.get(cmd, optimizar)
    print(json.dumps(fn(), ensure_ascii=False, indent=2))
