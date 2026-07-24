# -*- coding: utf-8 -*-
"""IDENTIDAD de AURORA — reconoce al DUEÑO (Anuar) vs un CLIENTE.

Seguridad real (fuerte, local, honesta — no 'mágica'):
- PIN secreto que SOLO Anuar conoce (se guarda hasheado con salt, nunca en claro).
- Por cada dispositivo de confianza se emite una LLAVE única (token aleatorio
  criptográfico = irrepetible e imposible de adivinar); se guarda solo su hash.
- Todo queda LOCAL en el servidor; nada viaja a internet.
- Sin llave/PIN válido => rol 'cliente' (acceso limitado: vender/cotizar, SIN control de PC).
"""
from __future__ import annotations
import json, hashlib, secrets, hmac
from pathlib import Path
from datetime import datetime

CFG = Path(__file__).resolve().parent.parent / "CONFIG" / "identidad.json"


def _load() -> dict:
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {"pin_salt": "", "pin_hash": "", "tokens": []}


def _save(d: dict) -> None:
    CFG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _hash(salt: str, valor: str) -> str:
    return hashlib.sha256((salt + valor).encode("utf-8")).hexdigest()


def estado() -> dict:
    d = _load()
    return {"status": "OK", "configurado": bool(d.get("pin_hash")),
            "dispositivos_confiables": len(d.get("tokens", []))}


def configurar_pin(pin_nuevo: str, pin_actual: str = "") -> dict:
    """Define o cambia el PIN del dueño. Si ya existe, exige el PIN actual."""
    if not pin_nuevo or len(pin_nuevo) < 4:
        return {"status": "ERROR", "detalle": "El PIN debe tener al menos 4 caracteres."}
    d = _load()
    if d.get("pin_hash"):
        if _hash(d["pin_salt"], pin_actual) != d["pin_hash"]:
            return {"status": "ERROR", "detalle": "PIN actual incorrecto."}
    salt = secrets.token_hex(16)
    d["pin_salt"] = salt
    d["pin_hash"] = _hash(salt, pin_nuevo)
    d.setdefault("tokens", [])
    _save(d)
    return {"status": "OK", "detalle": "PIN del dueño configurado. Solo tú lo conoces."}


def login(pin: str) -> dict:
    """Verifica el PIN y, si es correcto, emite una LLAVE única para este dispositivo."""
    d = _load()
    if not d.get("pin_hash"):
        return {"status": "SIN_CONFIGURAR", "detalle": "Aún no defines tu PIN de dueño."}
    if _hash(d["pin_salt"], pin or "") != d["pin_hash"]:
        return {"status": "DENEGADO", "detalle": "PIN incorrecto."}
    token = secrets.token_urlsafe(32)          # llave irrepetible e impredecible
    tsalt = secrets.token_hex(8)
    d.setdefault("tokens", []).append(
        {"salt": tsalt, "hash": _hash(tsalt, token), "creado": datetime.now().isoformat(timespec="seconds")})
    _save(d)
    return {"status": "OK", "rol": "dueño", "token": token,
            "detalle": "Dispositivo de confianza registrado. Guarda esta llave (queda en tu equipo)."}


def rol(token: str) -> str:
    """Devuelve 'dueño' si la llave es válida; si no, 'cliente'."""
    if not token:
        return "cliente"
    d = _load()
    for t in d.get("tokens", []):
        if hmac.compare_digest(_hash(t["salt"], token), t["hash"]):
            return "dueño"
    return "cliente"


def revocar_todos() -> dict:
    """Cierra sesión en TODOS los dispositivos (si pierdes uno o sospechas)."""
    d = _load()
    d["tokens"] = []
    _save(d)
    return {"status": "OK", "detalle": "Todas las llaves revocadas. Vuelve a iniciar sesión con tu PIN."}
