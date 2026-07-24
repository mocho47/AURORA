"""
PUBLICADOR - Estado y publicacion en redes. 100% HONESTO:
- Publica REAL via API oficial cuando hay token.
- Si falta el token, lo DICE (status FALTA_TOKEN). NUNCA simula un exito.
Lee credenciales de login del vault real de NEXUS v3 (solo para reportar estado).
"""

import os
import json
from pathlib import Path
from datetime import datetime

VAULT_DIR = Path(r"C:\NEXUS-original\CONFIG")

# Token de API oficial por plataforma (publicacion REAL)
TOKENS_API = {
    "tiktok": "TIKTOK_ACCESS_TOKEN",
    "instagram": "INSTAGRAM_ACCESS_TOKEN",
    "facebook": "FB_PAGE_TOKEN",
    "youtube": "YOUTUBE_ACCESS_TOKEN",
}


def _leer_vault() -> dict:
    """Apps con credenciales de login guardadas en el vault. {app: True/False}. Sin exponer secretos."""
    try:
        from cryptography.fernet import Fernet
        key = (VAULT_DIR / "secret.key").read_bytes()
        data = Fernet(key).decrypt((VAULT_DIR / "vault.enc").read_bytes())
        db = json.loads(data.decode())
        return {app: bool(c.get("user") and c.get("pass")) for app, c in db.items()}
    except Exception:
        return {}


def estado_redes() -> dict:
    vault = _leer_vault()
    redes = []
    for plat, env_var in TOKENS_API.items():
        token = bool(os.getenv(env_var))
        login = vault.get(plat, False)
        if token:
            estado = "LISTA"
            detalle = "Token de API presente — publica por API oficial."
        elif login:
            estado = "FALTA_TOKEN"
            detalle = "Hay credencial de login en el vault, pero NO token de API. Falta token para publicar."
        else:
            estado = "FALTA"
            detalle = "Sin token de API ni credencial."
        redes.append({
            "plataforma": plat,
            "estado": estado,
            "token_api": token,
            "login_vault": login,
            "detalle": detalle,
            "env_var": env_var,
        })
    return {"redes": redes, "timestamp": datetime.now().isoformat(timespec="seconds")}


def publicar(plataforma: str, texto: str = "", media_url: str = "") -> dict:
    plataforma = (plataforma or "").lower()
    if plataforma not in TOKENS_API:
        return {"status": "ERROR", "detalle": f"Plataforma '{plataforma}' no soportada"}
    token = os.getenv(TOKENS_API[plataforma])
    if not token:
        return {"status": "FALTA_TOKEN", "plataforma": plataforma,
                "detalle": f"No se publica: falta {TOKENS_API[plataforma]}. No se simula."}
    return _publicar_api(plataforma, token, texto, media_url)


def _publicar_api(plataforma: str, token: str, texto: str, media_url: str) -> dict:
    """Publicacion REAL via API oficial. Solo se ejecuta si hay token."""
    try:
        import requests
        if plataforma == "facebook":
            page_id = os.getenv("FB_PAGE_ID", "")
            if not page_id:
                return {"status": "FALTA_TOKEN", "plataforma": "facebook", "detalle": "Falta FB_PAGE_ID"}
            r = requests.post(
                f"https://graph.facebook.com/v23.0/{page_id}/feed",
                data={"message": texto, "access_token": token}, timeout=20)
            if r.ok:
                return {"status": "PUBLICADO", "plataforma": "facebook", "id": r.json().get("id")}
            return {"status": "ERROR", "plataforma": "facebook", "detalle": r.text[:300]}
        if plataforma == "instagram":
            ig_id = os.getenv("INSTAGRAM_USER_ID", "")
            if not ig_id:
                return {"status": "FALTA_TOKEN", "plataforma": "instagram", "detalle": "Falta INSTAGRAM_USER_ID"}
            if not media_url:
                return {"status": "FALTA_MEDIA", "plataforma": "instagram",
                        "detalle": "Instagram requiere una imagen en URL público (media_url). Enciende ngrok o sube la imagen."}
            # 1. crear contenedor de media
            cr = requests.post(f"https://graph.facebook.com/v23.0/{ig_id}/media",
                               data={"image_url": media_url, "caption": texto, "access_token": token}, timeout=30)
            if not cr.ok:
                return {"status": "ERROR", "plataforma": "instagram", "detalle": cr.text[:300]}
            cid = cr.json().get("id")
            # 2. publicar el contenedor
            pub = requests.post(f"https://graph.facebook.com/v23.0/{ig_id}/media_publish",
                                data={"creation_id": cid, "access_token": token}, timeout=30)
            if pub.ok:
                return {"status": "PUBLICADO", "plataforma": "instagram", "id": pub.json().get("id")}
            return {"status": "ERROR", "plataforma": "instagram", "detalle": pub.text[:300]}
        # TikTok / YouTube: subida de video real. Requiere token + flujo de media.
        return {"status": "FALTA_IMPL", "plataforma": plataforma,
                "detalle": "Token presente; falta cablear el flujo de subida de esta plataforma."}
    except Exception as e:
        return {"status": "ERROR", "plataforma": plataforma, "detalle": str(e)[:300]}


def comentarios_pagina(limite: int = 10) -> dict:
    """Lee comentarios REALES de las publicaciones recientes de la página FB."""
    token = os.getenv("FB_PAGE_TOKEN", ""); page = os.getenv("FB_PAGE_ID", "")
    if not token or not page:
        return {"status": "FALTA_TOKEN", "detalle": "Falta FB_PAGE_TOKEN o FB_PAGE_ID."}
    try:
        import requests
        rp = requests.get(f"https://graph.facebook.com/v23.0/{page}/posts",
                          params={"fields": "id,message", "limit": 10, "access_token": token}, timeout=20)
        posts = rp.json().get("data", [])
        out = []
        for p in posts:
            rc = requests.get(f"https://graph.facebook.com/v23.0/{p['id']}/comments",
                              params={"fields": "id,from,message,created_time", "limit": 25,
                                      "access_token": token}, timeout=20)
            for cm in rc.json().get("data", []):
                out.append({"comment_id": cm["id"], "de": cm.get("from", {}).get("name", "?"),
                            "texto": cm.get("message", ""), "post": (p.get("message", "") or "")[:40],
                            "fecha": cm.get("created_time", "")})
            if len(out) >= limite:
                break
        return {"status": "OK", "total": len(out), "comentarios": out[:limite]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def responder_comentario(comment_id: str, texto: str) -> dict:
    """Responde un comentario REAL en Facebook (acción pública: requiere autorización de Anuar)."""
    token = os.getenv("FB_PAGE_TOKEN", "")
    if not token:
        return {"status": "FALTA_TOKEN"}
    try:
        import requests
        r = requests.post(f"https://graph.facebook.com/v23.0/{comment_id}/comments",
                          data={"message": texto, "access_token": token}, timeout=20)
        j = r.json()
        return ({"status": "PUBLICADO", "id": j["id"]} if j.get("id")
                else {"status": "ERROR", "detalle": str(j)[:200]})
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def publicar_video_fb(ruta: str, descripcion: str = "") -> dict:
    """Sube un VIDEO local a la página de Facebook (Graph API /videos). Publicación REAL."""
    token = os.getenv("FB_PAGE_TOKEN", "")
    page = os.getenv("FB_PAGE_ID", "")
    if not token or not page:
        return {"status": "FALTA_TOKEN", "detalle": "Falta FB_PAGE_TOKEN o FB_PAGE_ID."}
    if not os.path.isfile(ruta):
        return {"status": "ERROR", "detalle": f"No existe el video: {ruta}"}
    try:
        import requests
        with open(ruta, "rb") as f:
            r = requests.post(
                f"https://graph-video.facebook.com/v23.0/{page}/videos",
                data={"description": descripcion, "access_token": token},
                files={"source": f}, timeout=600)
        j = r.json()
        if r.ok and j.get("id"):
            return {"status": "PUBLICADO", "plataforma": "facebook", "post_id": j["id"]}
        return {"status": "ERROR", "plataforma": "facebook", "detalle": str(j)[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def configurar_meta(user_token: str, app_id: str, app_secret: str) -> dict:
    """AUTOMATIZA la config de Meta: con el token de usuario corto + app_id + secret,
    obtiene token largo, page_id, page_token e instagram_id, y los escribe en .env."""
    try:
        import requests
        base = "https://graph.facebook.com/v23.0"
        # 1. Token de usuario de larga duración (60 días)
        r = requests.get(f"{base}/oauth/access_token", params={
            "grant_type": "fb_exchange_token", "client_id": app_id,
            "client_secret": app_secret, "fb_exchange_token": user_token}, timeout=20)
        if not r.ok:
            return {"status": "ERROR", "paso": "token_largo", "detalle": r.text[:300]}
        long_token = r.json().get("access_token")
        # 2. Página + page token (derivado del token largo = no expira)
        r = requests.get(f"{base}/me/accounts", params={"access_token": long_token}, timeout=20)
        if not r.ok or not r.json().get("data"):
            return {"status": "ERROR", "paso": "paginas", "detalle": r.text[:300]}
        page = r.json()["data"][0]
        page_id, page_token = page["id"], page["access_token"]
        # 3. Instagram business account vinculado a la página
        r = requests.get(f"{base}/{page_id}", params={
            "fields": "instagram_business_account", "access_token": page_token}, timeout=20)
        ig_id = (r.json().get("instagram_business_account") or {}).get("id", "") if r.ok else ""
        # 4. Escribir en .env (sin duplicar). IG solo si REALMENTE hay cuenta vinculada.
        valores = {"FB_PAGE_ID": page_id, "FB_PAGE_TOKEN": page_token}
        if ig_id:
            valores["INSTAGRAM_USER_ID"] = ig_id
            valores["INSTAGRAM_ACCESS_TOKEN"] = page_token
        _escribir_env(valores)
        for k, v in valores.items():
            os.environ[k] = v
        return {"status": "OK", "page_id": page_id, "instagram_id": ig_id or "(no vinculado)",
                "page_name": page.get("name", ""), "detalle": "FB+IG configurados y guardados en .env"}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def _escribir_env(valores: dict):
    from pathlib import Path
    envp = Path(r"C:\AURORA\.env")
    lineas = envp.read_text(encoding="utf-8").splitlines() if envp.exists() else []
    claves = set(valores)
    nuevas = [l for l in lineas if "=" not in l or l.split("=", 1)[0].strip() not in claves]
    for k, v in valores.items():
        nuevas.append(f"{k}={v}")
    envp.write_text("\n".join(nuevas) + "\n", encoding="utf-8")


def estado_whatsapp() -> dict:
    inst = os.getenv("GREEN_API_INSTANCE"); tok = os.getenv("GREEN_API_TOKEN"); srv = os.getenv("GREEN_API_SERVER", "")
    if not (inst and tok):
        return {"status": "FALTA_TOKEN"}
    host = f"https://{srv}.api.greenapi.com" if srv else "https://api.green-api.com"
    try:
        import requests
        r = requests.get(f"{host}/waInstance{inst}/getStateInstance/{tok}", timeout=12)
        return {"status": "OK", "estado": r.json().get("stateInstance")}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}


def enviar_whatsapp(telefono: str, mensaje: str) -> dict:
    """Envía un WhatsApp REAL vía Green API. Honesto: si no está autorizado, lo dice."""
    inst = os.getenv("GREEN_API_INSTANCE"); tok = os.getenv("GREEN_API_TOKEN"); srv = os.getenv("GREEN_API_SERVER", "")
    if not (inst and tok):
        return {"status": "FALTA_TOKEN", "detalle": "Falta GREEN_API_INSTANCE/TOKEN"}
    digitos = "".join(c for c in (telefono or "") if c.isdigit())
    if len(digitos) == 10:
        digitos = "521" + digitos
    if not digitos:
        return {"status": "ERROR", "detalle": "Lead sin teléfono válido"}
    host = f"https://{srv}.api.greenapi.com" if srv else "https://api.green-api.com"
    try:
        import requests
        r = requests.post(f"{host}/waInstance{inst}/sendMessage/{tok}",
                          json={"chatId": f"{digitos}@c.us", "message": mensaje}, timeout=20)
        if r.ok:
            return {"status": "ENVIADO", "telefono": digitos, "id": r.json().get("idMessage")}
        return {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}
