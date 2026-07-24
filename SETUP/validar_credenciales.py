# -*- coding: utf-8 -*-
"""
VALIDADOR REAL DE CREDENCIALES — AURORA v3
Prueba cada credencial CONTRA SU SERVICIO EN VIVO. No simula.
Nunca imprime secretos: solo PASS/FAIL + motivo real.
"""
import io
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

RAIZ = Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"


def cargar_env() -> dict:
    d = {}
    if not ENV.exists():
        return d
    for linea in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def ok(n):    print(f"   ✅ {n}")
def fail(n):  print(f"   ❌ {n}")
def warn(n):  print(f"   ⚠️  {n}")


def probar_groq(e):
    tok = e.get("GROQ_API_KEY", "")
    if not tok:
        fail("GROQ: sin clave"); return False
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {tok}"}, timeout=12)
        if r.status_code == 200:
            n = len(r.json().get("data", []))
            ok(f"GROQ (cerebro): VÁLIDA — {n} modelos disponibles"); return True
        fail(f"GROQ: rechazada (HTTP {r.status_code}: {r.text[:80]})"); return False
    except Exception as ex:
        fail(f"GROQ: error de red ({ex})"); return False


def probar_facebook(e):
    pid, tok = e.get("FB_PAGE_ID", ""), e.get("FB_PAGE_TOKEN", "")
    if not (pid and tok):
        fail("Facebook: falta page id o token"); return False
    try:
        r = requests.get(f"https://graph.facebook.com/v19.0/{pid}",
                         params={"fields": "name,fan_count", "access_token": tok}, timeout=12)
        j = r.json()
        if r.status_code == 200 and "name" in j:
            ok(f"Facebook: VÁLIDA — página '{j['name']}' ({j.get('fan_count','?')} seguidores)"); return True
        msg = j.get("error", {}).get("message", r.text[:80])
        fail(f"Facebook: rechazada ({msg})"); return False
    except Exception as ex:
        fail(f"Facebook: error de red ({ex})"); return False


def probar_instagram(e):
    uid, tok = e.get("INSTAGRAM_USER_ID", ""), e.get("INSTAGRAM_ACCESS_TOKEN", "")
    if not (uid and tok):
        fail("Instagram: falta user id o token"); return False
    try:
        r = requests.get(f"https://graph.facebook.com/v19.0/{uid}",
                         params={"fields": "username,followers_count", "access_token": tok}, timeout=12)
        j = r.json()
        if r.status_code == 200 and "username" in j:
            ok(f"Instagram: VÁLIDA — @{j['username']} ({j.get('followers_count','?')} seguidores)"); return True
        msg = j.get("error", {}).get("message", r.text[:80])
        fail(f"Instagram: rechazada ({msg})"); return False
    except Exception as ex:
        fail(f"Instagram: error de red ({ex})"); return False


def probar_whatsapp(e):
    tok = e.get("GREEN_API_TOKEN", "")
    inst = e.get("GREEN_API_INSTANCE_ID", "") or "7107622171"
    server = e.get("GREEN_API_SERVER", "").strip().rstrip("/")
    if not server.startswith("http"):
        warn(f"WhatsApp: GREEN_API_SERVER inválido en .env ('{server}') → usando https://api.green-api.com")
        server = "https://api.green-api.com"
    if not tok:
        fail("WhatsApp: sin token"); return False
    try:
        url = f"{server}/waInstance{inst}/getStateInstance/{tok}"
        r = requests.get(url, timeout=12)
        if r.status_code == 200:
            estado = r.json().get("stateInstance", "?")
            if estado == "authorized":
                ok(f"WhatsApp (Green API): VÁLIDA — instancia {inst} AUTORIZADA"); return True
            warn(f"WhatsApp: conecta pero estado='{estado}' (no autorizada / QR pendiente)"); return False
        fail(f"WhatsApp: rechazada (HTTP {r.status_code}: {r.text[:80]})"); return False
    except Exception as ex:
        fail(f"WhatsApp: error de red ({ex})"); return False


def probar_supabase(e):
    url, key = e.get("SUPABASE_URL", ""), e.get("SUPABASE_KEY", "")
    if not (url and key):
        fail("Supabase: falta url o key"); return False
    try:
        r = requests.get(f"{url.rstrip('/')}/rest/v1/",
                         headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=12)
        if r.status_code in (200, 404):
            ok("Supabase: VÁLIDA — responde y autentica"); return True
        fail(f"Supabase: rechazada (HTTP {r.status_code}: {r.text[:80]})"); return False
    except Exception as ex:
        fail(f"Supabase: error de red ({ex})"); return False


def probar_locales(e):
    for k, nombre in [("JWT_SECRET_KEY", "JWT secret"), ("ADMIN_PASSWORD", "Admin password")]:
        v = e.get(k, "")
        (ok if len(v) >= 8 else fail)(f"{nombre}: {'presente' if len(v)>=8 else 'FALTA o muy corto'}")


def main():
    print("=" * 62)
    print("   VALIDADOR REAL DE CREDENCIALES — AURORA v3")
    print("   (prueba en vivo, no simula)")
    print("=" * 62)
    e = cargar_env()
    if not e:
        print("\n[ERROR] No se pudo leer .env en", ENV); sys.exit(1)

    print("\n\U0001f9e0 IA / Cerebro:")
    r_groq = probar_groq(e)
    print("\n\U0001f4f1 Redes sociales:")
    r_fb = probar_facebook(e)
    r_ig = probar_instagram(e)
    print("\n\U0001f4ac Mensajería:")
    r_wa = probar_whatsapp(e)
    print("\n\U0001f5c4️  Base de datos:")
    r_sb = probar_supabase(e)
    print("\n\U0001f512 Locales (solo presencia):")
    probar_locales(e)

    validas = sum([r_groq, r_fb, r_ig, r_wa, r_sb])
    print("\n" + "=" * 62)
    print(f"   RESULTADO: {validas}/5 credenciales de servicio FUNCIONAN en vivo")
    print("=" * 62)


if __name__ == "__main__":
    main()
