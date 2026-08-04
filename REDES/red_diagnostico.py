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


# ── ESCANEO GENERAL DE LA RED ────────────────────────────────────────────────
# Este cartucho nació para el Google Home de la oficina, así que solo sabía
# buscar dispositivos Cast. El 2026-08-03 hizo falta encontrar la laptop Gateway
# en la red y no había con qué: se resolvió con un script suelto que se iba a
# tirar. Esto deja la capacidad DENTRO de AURORA, donde sirve otra vez — para la
# impresora, para un equipo que se pierde, para lo que sea que se conecte.

# Puerto -> qué significa, para no reportar números pelones.
_PUERTOS_UTILES = {
    9100: "impresora (RAW/JetDirect)",
    631:  "impresora (IPP)",
    515:  "impresora (LPD)",
    11434: "Ollama",
    5000: "AURORA",
    3389: "Escritorio remoto",
    5985: "administración remota (WinRM)",
    445:  "compartir archivos (SMB)",
    22:   "SSH",
    80:   "página web",
    443:  "página web segura",
    8009: "Google Cast",
    62078: "iPhone",
}

# Primeros 3 bytes de la MAC (OUI) de los fabricantes que de verdad aparecen en
# esta red. No pretende ser la lista completa: solo evita decir "desconocido"
# cuando sí se puede saber.
_FABRICANTES = {
    "74-26-ff": "ZTE (router IZZI)", "34-85-11": "Intel", "1c-3b-f3": "Intel",
    "fc-d7-49": "Intel", "34-de-1a": "Intel", "3c-95-09": "Intel",
    "00-1a-11": "Google", "f4-f5-d8": "Google", "d8-6c-63": "Google",
    "94-65-2d": "OnePlus", "b8-27-eb": "Raspberry Pi", "dc-a6-32": "Raspberry Pi",
    "00-1b-a9": "Brother", "3c-2a-f4": "Brother", "9c-93-4e": "Xerox",
    "00-15-99": "Samsung", "a4-5e-60": "Apple", "f0-18-98": "Apple",
    "d0-27-88": "HP", "b4-b6-86": "HP", "70-5a-0f": "HP", "3c-d9-2b": "HP",
    "e4-e7-49": "HP", "00-1e-8f": "Canon", "00-00-85": "Canon",
    "00-26-73": "Epson", "a4-ee-57": "Epson", "64-eb-8c": "Seiko Epson",
}


def _tabla_arp() -> dict:
    """IP -> MAC, leída de la tabla ARP real del sistema (no adivinada).

    Sirve para dos cosas: saber el fabricante, y detectar equipos que están
    conectados pero NO responden al ping (Windows lo bloquea por defecto
    cuando marca la red como Pública — fue justo el caso de la Gateway).
    """
    mapa = {}
    try:
        salida = subprocess.run(["arp", "-a"], capture_output=True, text=True,
                                timeout=20).stdout
    except Exception:
        return mapa
    for linea in salida.splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}(?:[-:][0-9a-fA-F]{2}){5})", linea)
        if m:
            mapa[m.group(1)] = m.group(2).lower().replace(":", "-")
    return mapa


def _fabricante(mac: str) -> str:
    return _FABRICANTES.get((mac or "")[:8], "")


def _nombre_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def _responde_ping(ip: str) -> bool:
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", "700", ip],
                           capture_output=True, text=True, timeout=8)
        return "TTL=" in r.stdout.upper()
    except Exception:
        return False


def escanear_red(puertos: list = None) -> dict:
    """Encuentra TODOS los equipos de la red local, no solo los Cast.

    De cada uno reporta lo que se puede COMPROBAR: si responde al ping, su MAC
    real (tabla ARP), el fabricante deducido de esa MAC, su nombre de red y qué
    puertos tiene abiertos traducidos a lenguaje normal ("impresora", "Ollama").

    Un equipo puede estar conectado y NO responder al ping: Windows lo bloquea
    cuando marca la red como Pública. Por eso se cruza con la tabla ARP, que sí
    lo registra — sin ese cruce, la laptop Gateway aparecía como ausente
    estando conectada (caso real 2026-08-03).
    """
    mia = _ip_local()
    arp = _tabla_arp()
    revisar = puertos or list(_PUERTOS_UTILES.keys())

    # Candidatos: toda la subred, más lo que ya está en ARP (por si el router
    # reparte en otro rango).
    candidatos = sorted(set(_subred(mia)) | set(arp.keys()),
                        key=lambda s: [int(x) for x in s.split(".")])
    candidatos = [c for c in candidatos if not c.endswith(".255")
                  and not c.startswith(("224.", "239."))]

    with cf.ThreadPoolExecutor(max_workers=64) as ex:
        vivos_ping = dict(zip(candidatos, ex.map(_responde_ping, candidatos)))

    # Está presente si contesta al ping O si el sistema ya le habló (ARP).
    presentes = [c for c in candidatos if vivos_ping.get(c) or c in arp]

    equipos = []
    for ip in presentes:
        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            abiertos = [p for p, ok in zip(revisar, ex.map(lambda p: _abierto(ip, p, 0.6), revisar)) if ok]
        mac = arp.get(ip, "")
        equipos.append({
            "ip": ip,
            "es_esta_pc": ip == mia,
            "nombre": _nombre_dns(ip),
            "mac": mac,
            "fabricante": _fabricante(mac),
            "responde_ping": bool(vivos_ping.get(ip)),
            "puertos": abiertos,
            "servicios": [_PUERTOS_UTILES.get(p, str(p)) for p in abiertos],
        })

    return {"status": "OK", "mi_ip": mia, "total": len(equipos), "equipos": equipos}


def buscar_equipo(que: str) -> dict:
    """Busca un equipo por nombre, fabricante o servicio ('impresora', 'ollama').

    Pensado para la pregunta real: "¿dónde quedó la Gateway?", "¿cuál es la IP
    de la impresora?". Si no lo encuentra lo dice — no devuelve el más parecido
    haciéndolo pasar por el bueno.
    """
    q = (que or "").strip().lower()
    if not q:
        return {"status": "FALTA_DATO", "detalle": "Dime qué equipo busco."}
    red = escanear_red()
    hallados = [e for e in red["equipos"]
                if q in (e["nombre"] or "").lower()
                or q in (e["fabricante"] or "").lower()
                or any(q in s.lower() for s in e["servicios"])
                or q in e["ip"]]
    if not hallados:
        return {"status": "NO_ENCONTRADO", "buscado": que,
                "revisados": red["total"], "mi_ip": red["mi_ip"],
                "detalle": (f"Revisé los {red['total']} equipos de la red y ninguno "
                            f"coincide con '{que}'. Puede estar apagado, en otra red, "
                            "o con el firewall bloqueando todo.")}
    return {"status": "OK", "buscado": que, "total": len(hallados), "equipos": hallados}


if __name__ == "__main__":
    import json
    print(json.dumps(escanear_red(), ensure_ascii=False, indent=2))
