# -*- coding: utf-8 -*-
"""
AURORA · ¿LAS LLAVES DE VERDAD FUNCIONAN?
=========================================

No basta con que estén escritas en el `.env`: una llave mal copiada, vencida o
sin permisos se ve idéntica a una buena hasta que falla frente a un cliente.

Esto las **prueba de verdad** contra cada servicio y dice cuál sirve.
NUNCA imprime el valor de una llave — solo su nombre y si funcionó.

Uso:  python SETUP/probar_credenciales.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_env() -> None:
    """Lee el .env como lo hace AURORA al arrancar."""
    env = RAIZ / ".env"
    if not env.exists():
        return
    for linea in env.read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, _, v = linea.partition("=")
        v = v.strip().strip('"').strip("'")
        if v:
            os.environ.setdefault(k.strip(), v)


def _pedir(url: str, timeout: int = 20) -> tuple[bool, str]:
    # El User-Agent no es opcional: varios servicios detrás de Cloudflare
    # rechazan con 403 cualquier petición sin él, y eso marcaba llaves buenas
    # como rotas (visto con Groq, error 1010).
    peticion = urllib.request.Request(url, headers={
        "User-Agent": "AURORA/1.0 (verificador de credenciales)",
        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:
            return r.status == 200, r.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:250]}"
    except Exception as e:
        return False, str(e)[:250]


# ── Una prueba por servicio ──────────────────────────────────────────────────
def _var(*nombres: str) -> str:
    """La primera variable que exista, sin importar mayúsculas ni el alias usado.

    Anuar escribió `google_search_api_key` en minúsculas y el código pedía
    `GOOGLE_API_KEY`: la llave estaba bien puesta y nadie la usaba, en silencio.
    """
    entorno = {k.upper(): v for k, v in os.environ.items()}
    for n in nombres:
        v = entorno.get(n.upper(), "")
        if v and v.strip():
            return v.strip()
    return ""


def probar_google() -> tuple[str, str]:
    llave = _var("GOOGLE_API_KEY", "GOOGLE_SEARCH_API_KEY", "GOOGLE_CSE_KEY")
    motor = _var("GOOGLE_SEARCH_ENGINE_ID", "GOOGLE_CSE_ID", "GOOGLE_CX", "SEARCH_ENGINE_ID")
    if llave and not motor:
        return "FALTA", ("tienes la llave pero falta el ID del buscador "
                         "(GOOGLE_SEARCH_ENGINE_ID) — se saca en programmablesearchengine.google.com")
    if not llave or not motor:
        falta = " y ".join(n for n, v in (("GOOGLE_API_KEY", llave),
                                          ("GOOGLE_SEARCH_ENGINE_ID", motor)) if not v)
        return "FALTA", f"no está {falta} en el .env"
    url = ("https://www.googleapis.com/customsearch/v1?"
           + urllib.parse.urlencode({"key": llave, "cx": motor, "q": "faros led h4", "num": 1}))
    ok, cuerpo = _pedir(url)
    if ok:
        try:
            n = json.loads(cuerpo).get("searchInformation", {}).get("totalResults", "?")
            return "OK", f"búsqueda real, {n} resultados"
        except Exception:
            return "OK", "respondió correctamente"
    if "API key not valid" in cuerpo:
        return "MAL", "la llave no es válida (revísala en console.cloud.google.com)"
    if "Custom Search API has not been used" in cuerpo or "accessNotConfigured" in cuerpo:
        return "MAL", "falta habilitar Custom Search API en el proyecto de Google Cloud"
    if "Invalid Value" in cuerpo or "invalid" in cuerpo.lower():
        return "MAL", "el ID del buscador (cx) no es correcto"
    return "MAL", cuerpo[:180]


def probar_groq() -> tuple[str, str]:
    llave = os.environ.get("GROQ_API_KEY", "")
    if not llave:
        return "FALTA", "no está GROQ_API_KEY"
    # Se prueba con una respuesta real, no listando modelos: /models devolvía 403
    # aunque la llave sirviera, y marcaba como rota una llave buena. Una prueba
    # que da falsos negativos es peor que no tenerla.
    cuerpo = json.dumps({
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": "di ok"}],
        "max_tokens": 5,
    }).encode()
    # Con User-Agent a fuerza: sin él, Cloudflare devuelve 403 error 1010 y la
    # prueba marcaba como rota una llave que sí funciona. El SDK de Groq que usa
    # AURORA sí manda estas cabeceras — por eso allá nunca falló.
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=cuerpo,
        headers={"Authorization": f"Bearer {llave}",
                 "Content-Type": "application/json",
                 "User-Agent": "AURORA/1.0 (verificador de credenciales)",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            json.loads(r.read().decode())
        return "OK", "responde de verdad"
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:150]
        if e.code == 429:
            return "OK", "la llave sirve, pero hoy ya no hay cuota (429)"
        if e.code == 401:
            return "MAL", "la llave no es válida"
        return "MAL", f"HTTP {e.code}: {detalle}"
    except Exception as e:
        return "MAL", str(e)[:180]


def probar_telegram() -> tuple[str, str]:
    tok = os.environ.get("TELEGRAM_TOKEN", "")
    if not tok:
        return "FALTA", "no está TELEGRAM_TOKEN (se saca en 3 min con @BotFather)"
    ok, cuerpo = _pedir(f"https://api.telegram.org/bot{tok}/getMe")
    if ok:
        try:
            u = json.loads(cuerpo).get("result", {}).get("username", "?")
            chat = os.environ.get("TELEGRAM_CHAT_ID", "")
            extra = "" if chat else "  (falta TELEGRAM_CHAT_ID para poder avisarte)"
            return "OK", f"bot @{u}{extra}"
        except Exception:
            return "OK", "el bot responde"
    return "MAL", "el token no sirve"


def probar_whatsapp() -> tuple[str, str]:
    inst = os.environ.get("GREEN_API_INSTANCE", "")
    tok = os.environ.get("GREEN_API_TOKEN", "")
    if not inst or not tok:
        return "FALTA", "no están GREEN_API_INSTANCE / GREEN_API_TOKEN"
    # Green API no usa una URL fija: el subdominio es un PREFIJO numérico.
    #   https://{prefijo}.api.greenapi.com/waInstance{instancia}/{accion}/{token}
    # La primera versión de esta prueba asumió que GREEN_API_SERVER era una URL
    # completa y armó una dirección rota — el .env estaba bien, la prueba no.
    srv = os.environ.get("GREEN_API_SERVER", "").strip().rstrip("/")
    if srv.startswith("http"):
        base = srv
    else:
        prefijo = srv or inst
        base = f"https://{prefijo}.api.greenapi.com"
    ok, cuerpo = _pedir(f"{base}/waInstance{inst}/getStateInstance/{tok}")
    if ok:
        try:
            estado = json.loads(cuerpo).get("stateInstance", "?")
            return ("OK", "autorizado y listo para enviar") if estado == "authorized" \
                else ("MAL", f"la instancia está '{estado}' — hay que reconectar el celular")
        except Exception:
            return "OK", "respondió"
    return "MAL", cuerpo[:180]


def probar_facebook() -> tuple[str, str]:
    tok = os.environ.get("FB_PAGE_TOKEN", "")
    pid = os.environ.get("FB_PAGE_ID", "")
    if not tok or not pid:
        return "FALTA", "no están FB_PAGE_TOKEN / FB_PAGE_ID"
    ok, cuerpo = _pedir(f"https://graph.facebook.com/v21.0/{pid}?fields=name&access_token={tok}")
    if ok:
        try:
            return "OK", f"página «{json.loads(cuerpo).get('name', '?')}»"
        except Exception:
            return "OK", "respondió"
    if "expired" in cuerpo.lower() or "Session has expired" in cuerpo:
        return "MAL", "el token VENCIÓ — hay que generarlo de nuevo"
    return "MAL", cuerpo[:180]


def probar_instagram() -> tuple[str, str]:
    tok = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
    uid = os.environ.get("INSTAGRAM_USER_ID", "")
    if not tok or not uid:
        return "FALTA", "no están INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ID"
    ok, cuerpo = _pedir(f"https://graph.facebook.com/v21.0/{uid}?fields=username&access_token={tok}")
    if ok:
        try:
            return "OK", f"cuenta @{json.loads(cuerpo).get('username', '?')}"
        except Exception:
            return "OK", "respondió"
    return "MAL", cuerpo[:180]


def probar_gemini() -> tuple[str, str]:
    llave = os.environ.get("GEMINI_API_KEY", "")
    if not llave:
        return "FALTA", "no está GEMINI_API_KEY"
    ok, cuerpo = _pedir(f"https://generativelanguage.googleapis.com/v1beta/models?key={llave}")
    if ok:
        try:
            return "OK", f"{len(json.loads(cuerpo).get('models', []))} modelos"
        except Exception:
            return "OK", "respondió"
    return "MAL", cuerpo[:180]


def probar_ollama() -> tuple[str, str]:
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ok, cuerpo = _pedir(f"{url}/api/tags", timeout=5)
    if ok:
        try:
            return "OK", f"{len(json.loads(cuerpo).get('models', []))} modelos locales"
        except Exception:
            return "OK", "respondió"
    return "MAL", "Ollama no responde (¿está apagado?)"


PRUEBAS = [
    ("Groq (el cerebro y la voz)", probar_groq),
    ("WhatsApp (Green API)", probar_whatsapp),
    ("Facebook ATF", probar_facebook),
    ("Instagram ATF", probar_instagram),
    ("Google Custom Search", probar_google),
    ("Gemini", probar_gemini),
    ("Telegram", probar_telegram),
    ("Ollama local", probar_ollama),
]


def main() -> int:
    _cargar_env()
    print("Probando las llaves de verdad contra cada servicio...\n")
    malas = 0
    for nombre, fn in PRUEBAS:
        try:
            estado, detalle = fn()
        except Exception as e:
            estado, detalle = "MAL", str(e)[:150]
        marca = {"OK": "  OK   ", "MAL": "  MAL  ", "FALTA": "  falta "}[estado]
        print(f"{marca} {nombre:28s} {detalle}")
        if estado == "MAL":
            malas += 1
    print()
    if malas:
        print(f"{malas} llave(s) están puestas pero NO funcionan. Eso es lo peligroso:")
        print("se ven bien en el .env y fallan frente a un cliente.")
    else:
        print("Todas las que están puestas funcionan de verdad.")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
