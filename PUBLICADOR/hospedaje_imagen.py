# -*- coding: utf-8 -*-
"""
AURORA · HOSPEDAJE PÚBLICO DE IMÁGENES — el bloqueo de Instagram, resuelto
=============================================================================
EL PROBLEMA, QUE LLEVABA MESES
---------------------------------------------------------------------------
Instagram no acepta que le mandes los bytes de una foto. Su API EXIGE una
`image_url` pública, que Meta va a descargar desde sus propios servidores:

    POST /{ig_id}/media   con  image_url=https://...   →  creation_id
    POST /{ig_id}/media_publish  con creation_id       →  publicado

`publicador_core.py` ya tenía ese flujo completo y correcto. Lo único que
faltaba era la URL, y por eso devolvía `FALTA_MEDIA` y AURORA nunca publicó
nada en Instagram. El camino viejo era Supabase, y ya no existe: el host de
`SUPABASE_URL` ni siquiera resuelve.

LA SOLUCIÓN: LA PROPIA PÁGINA DE FACEBOOK DE ANUAR
---------------------------------------------------------------------------
No hace falta contratar ni encender nada. AURORA ya publica de verdad en la
página de Facebook de ATF todos los días a las 19:00 con `FB_PAGE_TOKEN`, o
sea que ese token sirve y tiene permiso de subir fotos. Entonces:

  1. Se sube la foto a la página con `published=false`. Ojo: NO aparece en el
     muro, no la ve nadie. Queda como una foto "no publicada" de la página.
  2. Se le pide a Graph el campo `images`, que devuelve las URLs del CDN de
     Facebook (`scontent...fbcdn.net`). Esas URLs son públicas: cualquiera
     con el enlace las abre, sin token.
  3. Esa URL se le pasa a Instagram como `image_url`.

Y hay una razón de fondo por la que esto es lo correcto y no un truco: la
cuenta de Instagram del .env (`17841477357180920`) está vinculada como
`instagram_business_account` DE ESA MISMA PÁGINA. Comprobado contra Graph el
2026-08-26. O sea Instagram está descargando la imagen de la casa de al lado,
no de un servidor extraño.

POR QUÉ NO LAS OTRAS VÍAS
---------------------------------------------------------------------------
  · Supabase — muerto, el dominio no resuelve.
  · ngrok — hay que encender un túnel a mano cada vez y la URL cambia. Anuar
    necesita que esto corra solo a las 19:00, sin él.
  · Un hosting de imágenes de terceros — otra cuenta, otra llave, otra cosa
    que se cae sin avisar.
La página de Facebook ya está, ya funciona a diario y el token no expira
(comprobado: `expires_at = 0`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

GRAPH = "https://graph.facebook.com/v23.0"
RAIZ = Path(__file__).resolve().parent.parent
NEGOCIOS = RAIZ / "CONFIG" / "negocios.json"


def _llaves(negocio: str = "atf") -> tuple:
    """Token y página del negocio. Los NOMBRES de las variables viven en
    CONFIG/negocios.json; los valores solo en el .env — nunca en el código
    ni en un log."""
    try:
        d = json.loads(NEGOCIOS.read_text(encoding="utf-8"))
        n = (d.get("negocios") or {}).get((negocio or "atf").lower()) or {}
        env_tok = n.get("env_fb_token", "FB_PAGE_TOKEN")
        env_page = n.get("env_fb_page_id", "FB_PAGE_ID")
    except Exception:
        env_tok, env_page = "FB_PAGE_TOKEN", "FB_PAGE_ID"
    return os.getenv(env_tok, ""), os.getenv(env_page, ""), env_tok, env_page


def hospedar(ruta_local: str, negocio: str = "atf") -> dict:
    """Sube una imagen del disco a la página de Facebook SIN publicarla y
    devuelve su URL pública del CDN, lista para dársela a Instagram.

    Devuelve {status: OK, url, photo_id}. El `photo_id` sirve para borrarla
    después con `borrar(photo_id)` si se quiere no dejar rastro.
    """
    ruta = Path(ruta_local)
    if not ruta.is_file():
        return {"status": "ERROR", "detalle": f"No existe la imagen: {ruta_local}"}

    token, page_id, env_tok, env_page = _llaves(negocio)
    if not token or not page_id:
        return {"status": "FALTA_TOKEN",
                "detalle": f"Falta {env_tok} o {env_page} en el .env para el negocio "
                           f"'{negocio}'. No se publica y no se simula."}
    try:
        import requests
        # 1. Subir SIN publicar. published=false = no aparece en el muro.
        with open(ruta, "rb") as f:
            r = requests.post(f"{GRAPH}/{page_id}/photos",
                              data={"published": "false", "access_token": token},
                              files={"source": f}, timeout=180)
        if not r.ok:
            return {"status": "ERROR", "paso": "subida_fb", "detalle": r.text[:300]}
        photo_id = r.json().get("id")
        if not photo_id:
            return {"status": "ERROR", "paso": "subida_fb",
                    "detalle": f"Facebook no devolvió id: {r.text[:200]}"}

        # 2. Pedir las URLs del CDN. `images` viene ordenado de mayor a menor;
        # se toma la más grande para que Instagram reciba la mejor calidad.
        r2 = requests.get(f"{GRAPH}/{photo_id}",
                          params={"fields": "images,width,height",
                                  "access_token": token}, timeout=60)
        if not r2.ok:
            return {"status": "ERROR", "paso": "url_cdn", "detalle": r2.text[:300],
                    "photo_id": photo_id}
        imgs = r2.json().get("images") or []
        if not imgs:
            return {"status": "ERROR", "paso": "url_cdn", "photo_id": photo_id,
                    "detalle": "Facebook subió la foto pero no devolvió ninguna URL."}
        mejor = max(imgs, key=lambda i: (i.get("width") or 0) * (i.get("height") or 0))
        return {"status": "OK", "url": mejor["source"], "photo_id": photo_id,
                "medidas": f"{mejor.get('width')}x{mejor.get('height')}",
                "detalle": "Subida a la página como NO publicada (no aparece en el muro)."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}


def borrar(photo_id: str, negocio: str = "atf") -> dict:
    """Borra de Facebook la foto que solo se subió para hospedarla.

    OJO: si Instagram ya publicó usando esa URL, NO la borres — Instagram
    guarda su propia copia, pero solo después de que el post queda publicado.
    Se borra si algo falló a medio camino y quedó basura en la página.
    """
    token, _, env_tok, _ = _llaves(negocio)
    if not token:
        return {"status": "FALTA_TOKEN", "detalle": f"Falta {env_tok} en el .env"}
    try:
        import requests
        r = requests.delete(f"{GRAPH}/{photo_id}",
                            params={"access_token": token}, timeout=60)
        return ({"status": "BORRADA", "photo_id": photo_id} if r.ok
                else {"status": "ERROR", "detalle": r.text[:300]})
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:300]}
