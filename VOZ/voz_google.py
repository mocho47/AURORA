# -*- coding: utf-8 -*-
"""Voz de AURORA por Google Home Mini (casting). Reusa el enfoque de NEXUS (nexus_cast):
castea TTS de Google al dispositivo. Solo SALIDA (hablar). El Mini en la misma red."""
import urllib.parse

ALIAS = {"oficina": "oficina 2", "mini": "oficina 2", "oficina2": "oficina 2"}


def _nombre(cc):
    return (getattr(cc, "cast_info", None) and cc.cast_info.friendly_name) or getattr(getattr(cc, "device", None), "friendly_name", "")


def dispositivos(timeout=8):
    import pychromecast
    ccs, browser = pychromecast.get_chromecasts(timeout=timeout)
    nombres = [_nombre(c) for c in ccs]
    try:
        pychromecast.discovery.stop_discovery(browser)
    except Exception:
        pass
    return nombres


def hablar_google(texto, device="oficina", lang="es"):
    import pychromecast
    if not texto:
        return {"status": "ERROR", "detalle": "Texto vacío"}
    name = ALIAS.get(device.lower().strip(), device.lower().strip())
    ccs, browser = pychromecast.get_chromecasts(timeout=10)
    target = next((c for c in ccs if name in _nombre(c).lower()), None)
    if not target:
        nombres = [_nombre(c) for c in ccs]
        try: pychromecast.discovery.stop_discovery(browser)
        except Exception: pass
        return {"status": "NO_DEVICE", "detalle": f"No encontré '{device}'.", "dispositivos": nombres}
    try:
        target.wait(timeout=12)
        url = ("https://translate.google.com/translate_tts?ie=UTF-8&q="
               + urllib.parse.quote(texto[:200]) + f"&tl={lang}&client=tw-ob")
        target.media_controller.play_media(url, "audio/mp3")
        target.media_controller.block_until_active(timeout=12)
        return {"status": "OK", "device": _nombre(target), "dijo": texto[:200]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}
    finally:
        try: pychromecast.discovery.stop_discovery(browser)
        except Exception: pass


if __name__ == "__main__":
    import sys
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    print("Escaneando dispositivos Google/Chromecast en la red...")
    print("Encontrados:", dispositivos())
