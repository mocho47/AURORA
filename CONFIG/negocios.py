# -*- coding: utf-8 -*-
"""AURORA · IDENTIDAD DE NEGOCIOS (una sola fuente de verdad).

Lee CONFIG/negocios.json. Existe porque los telefonos estaban hardcodeados en
3 archivos distintos y esa dispersion ya costo caro (175 reels publicados con
un numero viejo). Ahora: se cambia en el JSON y ya.

Las LLAVES no viven aqui ni en el JSON (texto plano que va a git): el JSON solo
dice COMO SE LLAMA la variable de entorno de cada negocio, y el token real se
lee del .env. Si falta, se dice honesto — nunca se publica con la cuenta
equivocada por usar un token de otro negocio como respaldo.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

_ARCHIVO = Path(__file__).resolve().parent / "negocios.json"
_DEFECTO = "atf"


def _datos() -> dict:
    try:
        return json.loads(_ARCHIVO.read_text(encoding="utf-8")).get("negocios", {})
    except Exception:
        return {}


def listar() -> list:
    """Ids de los negocios configurados (ej. ['atf', 'milens'])."""
    return sorted(_datos().keys())


def negocio(nombre: str = "") -> dict:
    """Datos de un negocio. Si no existe, devuelve los del negocio por defecto."""
    d = _datos()
    n = (nombre or _DEFECTO).strip().lower()
    return d.get(n) or d.get(_DEFECTO) or {}


def telefono(nombre: str = "") -> str:
    """Telefono REAL del negocio, sin adivinar. Cadena vacia si no esta configurado."""
    return str(negocio(nombre).get("telefono") or "")


def telefono_bonito(nombre: str = "") -> str:
    """Telefono formateado para mostrar a un cliente: '33 3238 6943'."""
    t = telefono(nombre)
    return f"{t[:2]} {t[2:6]} {t[6:]}" if len(t) == 10 else t


def credenciales(nombre: str = "") -> dict:
    """Tokens reales del negocio, leidos del .env segun los nombres del JSON.

    Devuelve {'fb_token','fb_page_id','ig_token','ig_user_id','completo','faltan'}.
    'completo' es False si falta cualquiera de Facebook — asi quien publique puede
    avisar honesto en vez de usar el token de otro negocio.
    """
    n = negocio(nombre)
    vals, faltan = {}, []
    for clave, env_key in (("fb_token", "env_fb_token"), ("fb_page_id", "env_fb_page_id"),
                           ("ig_token", "env_ig_token"), ("ig_user_id", "env_ig_user_id")):
        var = n.get(env_key, "")
        v = os.getenv(var, "") if var else ""
        vals[clave] = v
        if not v:
            faltan.append(var or clave)
    vals["completo"] = bool(vals["fb_token"] and vals["fb_page_id"])
    vals["faltan"] = faltan
    return vals


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    for n in listar():
        c = credenciales(n)
        print(f"{n:8s} tel={telefono_bonito(n):15s} facebook_listo={c['completo']}"
              f"{'  falta: ' + ', '.join(c['faltan']) if c['faltan'] else ''}")
