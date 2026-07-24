"""
METRICOOL - Conector REAL a la API de Metricool (redes ya conectadas ahi por Anuar:
Facebook, TikTok, Pinterest). 100% HONESTO: si faltan credenciales, lo DICE
(status FALTA_TOKEN). NUNCA simula un exito.
Credenciales: cuenta > Configuracion > API (userToken + userId). blogId = marca.
"""

import os
from datetime import datetime

BASE_URL = "https://app.metricool.com/api"


def _creds():
    return (os.getenv("METRICOOL_USER_TOKEN", ""),
            os.getenv("METRICOOL_USER_ID", ""),
            os.getenv("METRICOOL_BLOG_ID", ""))


def _headers(token: str) -> dict:
    return {"Content-Type": "application/json", "X-Mc-Auth": token}


def _auth_params(user_id: str, blog_id: str = "") -> dict:
    p = {"userId": user_id}
    if blog_id:
        p["blogId"] = blog_id
    return p


def estado_metricool() -> dict:
    token, user_id, blog_id = _creds()
    if not (token and user_id):
        return {"status": "FALTA_TOKEN",
                "detalle": "Falta METRICOOL_USER_TOKEN o METRICOOL_USER_ID en .env "
                           "(Metricool > Configuracion > API)."}
    return listar_marcas()


def listar_marcas() -> dict:
    """Marcas/brands conectadas a la cuenta de Metricool (cada una con su blogId)."""
    token, user_id, _ = _creds()
    if not (token and user_id):
        return {"status": "FALTA_TOKEN"}
    try:
        import requests
        r = requests.get(f"{BASE_URL}/admin/simpleProfiles",
                          headers=_headers(token), params=_auth_params(user_id), timeout=20)
        if r.ok:
            return {"status": "OK", "marcas": r.json()}
        return {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def publicar_metricool(texto: str, redes: list, media: list = None,
                        fecha: str = "", borrador: bool = False, blog_id: str = "") -> dict:
    """Publica/agenda REAL via Metricool a una o varias redes (facebook, tiktok, pinterest, instagram...).
    fecha: ISO 'YYYY-MM-DDTHH:MM:SS' (vacio = ahora). borrador=True para NO auto-publicar."""
    token, user_id, blog_default = _creds()
    blog_id = blog_id or blog_default
    if not (token and user_id and blog_id):
        return {"status": "FALTA_TOKEN",
                "detalle": "Falta METRICOOL_USER_TOKEN/USER_ID/BLOG_ID."}
    if not redes:
        return {"status": "ERROR", "detalle": "Falta al menos una red en 'redes'."}
    fecha_dt = fecha or datetime.now().isoformat(timespec="seconds")
    post = {
        "text": texto or "",
        "providers": [{"network": r} for r in redes],
        "publicationDate": {"dateTime": fecha_dt, "timezone": "America/Mexico_City"},
        "draft": borrador,
        "autoPublish": not borrador,
        "media": media or [],
    }
    try:
        import requests
        r = requests.post(f"{BASE_URL}/v2/scheduler/posts",
                           headers=_headers(token),
                           params=_auth_params(user_id, blog_id),
                           json=post, timeout=30)
        if r.ok:
            j = r.json()
            return {"status": "PROGRAMADO" if borrador else "PUBLICADO",
                     "id": j.get("id"), "redes": redes}
        return {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def listar_publicaciones(desde: str = "", hasta: str = "", blog_id: str = "") -> dict:
    """Publicaciones programadas/publicadas en Metricool en un rango de fechas ISO."""
    token, user_id, blog_default = _creds()
    blog_id = blog_id or blog_default
    if not (token and user_id and blog_id):
        return {"status": "FALTA_TOKEN"}
    try:
        import requests
        params = _auth_params(user_id, blog_id)
        if desde:
            params["start"] = desde
        if hasta:
            params["end"] = hasta
        r = requests.get(f"{BASE_URL}/v2/scheduler/posts",
                          headers=_headers(token), params=params, timeout=20)
        if r.ok:
            return {"status": "OK", "publicaciones": r.json()}
        return {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def eliminar_publicacion(post_id: str, blog_id: str = "") -> dict:
    token, user_id, blog_default = _creds()
    blog_id = blog_id or blog_default
    if not (token and user_id and blog_id):
        return {"status": "FALTA_TOKEN"}
    try:
        import requests
        r = requests.delete(f"{BASE_URL}/v2/scheduler/posts/{post_id}",
                             headers=_headers(token), params=_auth_params(user_id, blog_id), timeout=20)
        return {"status": "ELIMINADO"} if r.ok else {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def mejor_hora_publicar(blog_id: str = "") -> dict:
    """Mejor horario sugerido por Metricool para publicar (segun tu audiencia real)."""
    token, user_id, blog_default = _creds()
    blog_id = blog_id or blog_default
    if not (token and user_id and blog_id):
        return {"status": "FALTA_TOKEN"}
    try:
        import requests
        r = requests.get(f"{BASE_URL}/planner/best-time-to-publish",
                          headers=_headers(token), params=_auth_params(user_id, blog_id), timeout=20)
        if r.ok:
            return {"status": "OK", "sugerencia": r.json()}
        return {"status": "ERROR", "detalle": r.text[:300]}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}
