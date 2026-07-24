# -*- coding: utf-8 -*-
"""AURORA · CARTUCHO de DIAGNÓSTICO DE RED e IoT (Google Cast / Nest / Home Mini).

Descubre dispositivos Cast en la LAN, lee su señal Wi-Fi REAL (RSSI) desde el
propio dispositivo (endpoint eureka_info:8008), mide pérdida de paquetes y
diagnostica desconexiones con conocimiento real:
- Señal fuerte + cortes  → band-steering (2.4/5GHz same SSID) o DHCP sin reserva o IGMP snooping.
- Señal débil            → alcance/interferencia (reubicar / extensor 2.4GHz).

Cero invento: todo sale de mediciones reales del equipo y la red.
"""
from __future__ import annotations
import socket, subprocess, re
import concurrent.futures as cf
import requests

CAST_PORT = 8009   # Google Cast (control)
INFO_PORT = 8008   # eureka_info (nombre, RSSI, MAC, SSID)


def _ip_local() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except Exception:
        return "192.168.1.38"
    finally:
        s.close()


def _subred(ip: str) -> list:
    base = ip.rsplit(".", 1)[0]
    return [f"{base}.{i}" for i in range(1, 255)]


def _abierto(ip: str, port: int, t: float = 0.35) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=t):
            return True
    except Exception:
        return False


def _eureka(ip: str) -> dict:
    try:
        r = requests.get(f"http://{ip}:{INFO_PORT}/setup/eureka_info?options=detail", timeout=4)
        return r.json()
    except Exception:
        return {}


def escanear_cast() -> dict:
    """Encuentra dispositivos Google Cast/Nest/Home en la red local (puerto 8009)."""
    ip = _ip_local()
    ips = _subred(ip)
    with cf.ThreadPoolExecutor(max_workers=64) as ex:
        futs = {ex.submit(_abierto, x, CAST_PORT): x for x in ips}
        cast_ips = [futs[f] for f in cf.as_completed(futs) if f.result()]
    disp = []
    for cip in sorted(cast_ips, key=lambda s: int(s.rsplit(".", 1)[1])):
        info = _eureka(cip)
        disp.append({
            "ip": cip,
            "nombre": info.get("name", "(sin nombre)"),
            "ssid": info.get("ssid", ""),
            "mac": info.get("mac_address", ""),
            "rssi": info.get("signal_level"),
            "noise": info.get("noise_level"),
        })
    return {"status": "OK", "mi_ip": ip, "total": len(disp), "dispositivos": disp}


def ping_perdida(ip: str, n: int = 12) -> dict:
    """Mide pérdida de paquetes y latencia real hacia un dispositivo."""
    try:
        out = subprocess.run(["ping", "-n", str(n), "-w", "1000", ip],
                             capture_output=True, text=True, timeout=n * 1.5 + 12).stdout
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}
    perd = re.search(r"\((\d+)%", out)
    prom = re.search(r"(?:Media|Average)\s*=\s*(\d+)\s*ms", out)
    return {"status": "OK", "ip": ip,
            "perdida_pct": int(perd.group(1)) if perd else None,
            "latencia_ms": int(prom.group(1)) if prom else None}


def diagnosticar(ip: str) -> dict:
    """Diagnóstico REAL de un dispositivo Cast + recomendación según su estado."""
    info = _eureka(ip)
    if not info:
        return {"status": "OFFLINE", "ip": ip,
                "diagnostico": "No responde en 8008 — apagado o fuera de la Wi-Fi.",
                "acciones_recomendadas": ["Verifica que esté encendido",
                                          "Revisa que siga en la Wi-Fi correcta"]}
    rssi = info.get("signal_level")
    ping = ping_perdida(ip, 12)
    perd = ping.get("perdida_pct")
    lat = ping.get("latencia_ms")
    tiene_rssi = isinstance(rssi, (int, float))
    hay_perdida = isinstance(perd, (int, float)) and perd > 0
    causas, acciones = [], []

    # 1) Estado por pérdida/latencia (esto SÍ se mide siempre)
    if perd == 0 and isinstance(lat, (int, float)) and lat < 30:
        causas.append(f"Conexión ESTABLE ahora mismo: 0% pérdida, {lat} ms de latencia. "
                      "Si aun así se corta, es intermitente (típico: band-steering o DHCP sin reserva), no alcance.")
    elif hay_perdida:
        causas.append(f"PÉRDIDA de paquetes {perd}% (latencia {lat} ms): la Wi-Fi está fallando de verdad hacia este equipo.")

    # 2) Señal: fuerte / débil / no legible (NO asumir débil si es None)
    culpables_red = [
        "Separar bandas: SSID distinto para 2.4GHz y 5GHz; conectar el dispositivo SOLO a 2.4GHz (apagar 'Band Steering').",
        f"Reservar IP por DHCP: fijar {ip} a la MAC {info.get('mac_address', '?')}.",
        "Desactivar 'IGMP Snooping' si existe (rompe el descubrimiento Cast).",
        "Reiniciar el dispositivo (desenchufar 10 s).",
    ]
    if tiene_rssi and rssi > -70:
        causas.append(f"Señal FUERTE ({rssi} dBm): NO es alcance. Con buena señal + cortes, "
                      "el culpable típico en routers IZZI/ZTE es band-steering, DHCP sin reserva o IGMP snooping.")
        acciones += culpables_red
    elif tiene_rssi:
        causas.append(f"Señal DÉBIL ({rssi} dBm): alcance/interferencia.")
        acciones += ["Reubicar el dispositivo más cerca del router",
                     "Poner un extensor/repetidor en 2.4GHz"]
    else:
        causas.append("Señal (RSSI) no legible: este dispositivo no la expone. Me guío por pérdida/latencia.")
        if hay_perdida:
            acciones += culpables_red + ["Si persiste, reubicar más cerca del router o extensor 2.4GHz."]
        else:
            acciones += ["Sin problema medible ahora (0% pérdida). Si se corta a ciertas horas, "
                         "ataca band-steering y reserva de IP por DHCP (causas intermitentes)."]
    return {"status": "OK", "ip": ip, "nombre": info.get("name", ""),
            "ssid": info.get("ssid", ""), "mac": info.get("mac_address", ""),
            "rssi": rssi, "noise": info.get("noise_level"),
            "perdida_pct": ping.get("perdida_pct"), "latencia_ms": ping.get("latencia_ms"),
            "causas_probables": causas, "acciones_recomendadas": acciones}


if __name__ == "__main__":
    import json
    print(json.dumps(escanear_cast(), ensure_ascii=False, indent=2))
