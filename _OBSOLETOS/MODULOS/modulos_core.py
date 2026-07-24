# -*- coding: utf-8 -*-
"""MODULOS de AURORA: FORJA, EVOLUCION, CANBUSFIX integrados en modo PAUSADO.
Quedan registrados y administrables; se activan cuando se elija (ATF es prioridad)."""
import os, json, subprocess, webbrowser
from pathlib import Path
from datetime import datetime

ESTADO_FILE = Path(r"C:\AURORA\MODULOS\estado.json")

MODULOS = {
    "forja": {
        "nombre": "FORJA", "desc": "Sistema de órdenes / gestión de pedidos centralizada",
        "tipo": "modulo", "ruta": r"C:\NEXUS-CONTENEDOR\MODULES\FORJA\module.py", "puerto": None,
    },
    "evolucion": {
        "nombre": "EVOLUCIÓN", "desc": "Coaching familiar (teens, padres, maestros)",
        "tipo": "python_server", "ruta": r"C:\evolucion\evolucion_server.py", "puerto": 8080,
    },
    "canbusfix": {
        "nombre": "CANBUSFIX", "desc": "Sitio web del servicio CanbusFix",
        "tipo": "html", "ruta": r"C:\NEXUS\WEB_CANBUSFIX\index.html", "puerto": None,
    },
}

_proc = {}  # procesos activos en memoria

def _estados():
    if ESTADO_FILE.exists():
        try: return json.loads(ESTADO_FILE.read_text(encoding="utf-8"))
        except: pass
    return {k: "pausado" for k in MODULOS}

def _guardar(est):
    ESTADO_FILE.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")

def listar():
    est = _estados()
    out = []
    for k, m in MODULOS.items():
        out.append({"id": k, "nombre": m["nombre"], "desc": m["desc"], "tipo": m["tipo"],
                    "puerto": m["puerto"], "existe": os.path.exists(m["ruta"]),
                    "estado": est.get(k, "pausado")})
    return {"modulos": out, "timestamp": datetime.now().isoformat(timespec="seconds")}

def activar(mid: str):
    m = MODULOS.get(mid)
    if not m: return {"status": "ERROR", "detalle": "Módulo no existe"}
    if not os.path.exists(m["ruta"]): return {"status": "ERROR", "detalle": f"No se encontró {m['ruta']}"}
    try:
        if m["tipo"] == "python_server":
            p = subprocess.Popen(["pythonw", m["ruta"]], cwd=str(Path(m["ruta"]).parent))
            _proc[mid] = p.pid
        elif m["tipo"] == "html":
            webbrowser.open(m["ruta"])
        # forja (modulo): solo se marca activo (es submódulo del core)
        est = _estados(); est[mid] = "activo"; _guardar(est)
        return {"status": "OK", "modulo": mid, "estado": "activo", "puerto": m["puerto"]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}

def pausar(mid: str):
    m = MODULOS.get(mid)
    if not m: return {"status": "ERROR", "detalle": "Módulo no existe"}
    pid = _proc.pop(mid, None)
    if pid:
        try: subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        except: pass
    est = _estados(); est[mid] = "pausado"; _guardar(est)
    return {"status": "OK", "modulo": mid, "estado": "pausado"}
