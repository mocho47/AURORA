# -*- coding: utf-8 -*-
"""AURORA · QUIEN ESCRIBE (clasificacion de contactos de WhatsApp).

Existe por un riesgo real que señalo Anuar: el telefono y WhatsApp son el 90% de
su dialogo con TODOS — clientes, familia y amigos — y AURORA trataba a cualquiera
como cliente. Su hija escribiendo "papa ya sali de la escuela" quedaba registrada
como LEAD en el CRM (con ese texto como "interes") y recibia una respuesta
automatica de ventas.

Dos capas, en este orden:
  1. Numero conocido en CONFIG/contactos.json -> se usa su relacion real.
  2. Numero desconocido -> se leen las palabras del mensaje. Si suena personal
     (papa, hija, te quiero, pasas por mi...), NO se vende ni se responde como si
     fuera Anuar: se le avisa a el. Un desconocido con mensaje de negocio si
     recibe atencion normal — ahi esta el valor del vendedor 24/7.

Regla de oro: AURORA nunca se hace pasar por Anuar con su familia.
"""
from __future__ import annotations
import json
import unicodedata as _ud
from pathlib import Path

_ARCHIVO = Path(__file__).resolve().parent / "contactos.json"
_CACHE = None


def _cfg() -> dict:
    global _CACHE
    if _CACHE is None:
        try:
            _CACHE = json.loads(_ARCHIVO.read_text(encoding="utf-8"))
        except Exception:
            _CACHE = {}
    return _CACHE


def _norm(s: str) -> str:
    return "".join(c for c in _ud.normalize("NFD", str(s or "").lower())
                   if _ud.category(c) != "Mn")


def _solo_digitos(tel: str) -> str:
    return "".join(c for c in str(tel or "") if c.isdigit())


def suena_personal(texto: str) -> bool:
    """True si el mensaje suena a familia/amigo y NO a cliente."""
    t = _norm(texto)
    for p in _cfg().get("_palabras_personales", []):
        pn = _norm(p)
        # Palabra suelta (hasta 6 letras): se exige que vaya SOLA, para no
        # confundir "apa" dentro de otra palabra, "ami" dentro de "amigo del
        # taller", ni "gorda" dentro de "engordado". Las frases mas largas
        # ("ya sali de la escuela") si se buscan como subcadena.
        if len(pn) <= 6:
            palabras_msg = t.replace(",", " ").replace("?", " ").replace("!", " ").replace(".", " ").split()
            if pn in palabras_msg:
                return True
        elif pn in t:
            return True
    return False


def clasificar(telefono: str, texto: str = "") -> dict:
    """Quien escribe y que se debe hacer.

    Devuelve {'relacion','nombre','conocido','por_texto','vender','responder',
              'avisar_a_anuar','registrar_lead'}.
    """
    cfg = _cfg()
    pol = cfg.get("politica_por_relacion", {})
    tel = _solo_digitos(telefono)

    # 1) Numero conocido (se compara por los ultimos 10 digitos: los prefijos de
    #    pais/WhatsApp varian — 52, 521, +52 — y no deben provocar un fallo).
    #    Las claves que empiezan con "_EJEMPLO" son plantillas, no contactos.
    for num, datos in (cfg.get("contactos") or {}).items():
        if num.startswith("_"):
            continue
        n = _solo_digitos(num)
        if n and tel and (n[-10:] == tel[-10:]):
            rel = (datos.get("relacion") or "desconocido").lower()
            p = dict(pol.get(rel, pol.get("desconocido", {})))
            if datos.get("no_responder"):
                p["responder"] = False
                p["vender"] = False
            # La respuesta del CONTACTO manda sobre la de su relacion: asi la
            # esposa recibe su trato propio y no el generico de "familia".
            if "respuesta" in datos:
                p["respuesta"] = datos.get("respuesta") or ""
            return {"relacion": rel, "nombre": datos.get("nombre", ""),
                    "titulo": datos.get("titulo", ""), "conocido": True,
                    "por_texto": False, **p}

    # 2) Desconocido: decide por como suena el mensaje.
    if texto and suena_personal(texto):
        p = dict(pol.get("personal_probable", pol.get("familia", {})))
        return {"relacion": "personal_probable", "nombre": "",
                "titulo": "alguien cercano (por como escribe)", "conocido": False,
                "por_texto": True, **p}

    p = dict(pol.get("desconocido", {}))
    return {"relacion": "desconocido", "nombre": "", "titulo": "", "conocido": False,
            "por_texto": False, **p}


if __name__ == "__main__":
    pruebas = [
        ("5213311112222", "papa ya sali de la escuela, pasas por mi?"),
        ("5213311112222", "buenas tardes, cuanto cuesta instalar lupas en un jetta?"),
        ("5213326148674", "hola"),
        ("5213344445555", "te quiero mucho, bendicion"),
        ("5213344445555", "quiero cotizar 50 tazas sublimadas"),
    ]
    for tel, txt in pruebas:
        c = clasificar(tel, txt)
        print(f"{c['relacion']:18s} vender={str(c.get('vender')):5s} "
              f"responder={str(c.get('responder')):5s} avisar={str(c.get('avisar_a_anuar')):5s} "
              f"lead={str(c.get('registrar_lead')):5s} <- {txt[:45]}")
