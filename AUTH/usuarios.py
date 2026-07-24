# -*- coding: utf-8 -*-
"""
AURORA · MULTI-USUARIO (Anuar + Rocío)
Cada usuario tiene un ROL, y el rol define QUÉ CARTUCHOS ve (se apoya en la Consola de Motores).
- PIN por usuario, hasheado con salt (nunca en claro).
- Separación por rol a nivel panel (qué pestañas ve). El control de PC sigue además blindado
  por el PIN de dueño (AUTH/identidad_core). Es seguridad de taller/hogar compartido, honesta:
  no es enterprise, pero es real (PIN hasheado + roles).
Estado en CONFIG/usuarios.json.
"""
from __future__ import annotations
import hashlib
import json
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "CONFIG" / "usuarios.json"

# Roles → cartuchos permitidos (ids de la Consola de Motores). "*" = todos.
ROLES = {
    "dueño": {"nombre": "Dueño (acceso total)", "cartuchos": "*"},
    "esposa": {"nombre": "Esposa / socia",
               "cartuchos": ["dash", "chat", "taller", "tprecios", "contabilidad",
                             "crm", "vendedor", "marketing", "monetiza", "redes",
                             "biblioteca", "editor", "web"]},
    "colaborador": {"nombre": "Colaborador",
                    "cartuchos": ["dash", "chat", "taller", "tprecios", "vendedor", "biblioteca"]},
}

# Usuarios que se siembran la primera vez (sin PIN: se define en el primer login).
# Anuar y Rocío = ambos acceso TOTAL (co-dueños). Los roles esposa/colaborador quedan
# disponibles por si luego se agrega a Samm o un empleado con acceso limitado.
SEED = [
    {"id": "anuar", "nombre": "Anuar", "rol": "dueño"},
    {"id": "rocio", "nombre": "Rocío", "rol": "dueño"},
]


def _hash(salt: str, valor: str) -> str:
    return hashlib.sha256((salt + "::" + valor).encode("utf-8")).hexdigest()


def _load() -> dict:
    if STATE.exists():
        try:
            d = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            d = {}
    else:
        d = {}
    d.setdefault("usuarios", [])
    if not d["usuarios"]:
        d["usuarios"] = [{**u, "pin_salt": "", "pin_hash": ""} for u in SEED]
        _save(d)
    return d


def _save(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _cartuchos_de(rol: str) -> str | list:
    return ROLES.get(rol, {}).get("cartuchos", [])


def listar_usuarios() -> dict:
    """Para la pantalla de login: nombres, rol y si ya tienen PIN. Sin secretos."""
    d = _load()
    us = [{"id": u["id"], "nombre": u["nombre"], "rol": u["rol"],
           "rol_nombre": ROLES.get(u["rol"], {}).get("nombre", u["rol"]),
           "tiene_pin": bool(u.get("pin_hash"))} for u in d["usuarios"]]
    return {"status": "ok", "usuarios": us, "roles": {k: v["nombre"] for k, v in ROLES.items()}}


def _find(d: dict, uid: str):
    return next((u for u in d["usuarios"] if u["id"] == uid), None)


def configurar_pin(uid: str, pin_nuevo: str, pin_actual: str = "") -> dict:
    """Define o cambia el PIN de un usuario. Si ya tiene, exige el actual."""
    if not pin_nuevo or len(pin_nuevo) < 4:
        return {"status": "error", "detalle": "El PIN debe tener al menos 4 dígitos."}
    d = _load()
    u = _find(d, uid)
    if not u:
        return {"status": "no_encontrado", "detalle": f"Usuario '{uid}' no existe."}
    if u.get("pin_hash") and _hash(u["pin_salt"], pin_actual) != u["pin_hash"]:
        return {"status": "error", "detalle": "PIN actual incorrecto."}
    salt = secrets.token_hex(16)
    u["pin_salt"] = salt
    u["pin_hash"] = _hash(salt, pin_nuevo)
    _save(d)
    return {"status": "ok", "detalle": f"PIN de {u['nombre']} configurado."}


def login(uid: str, pin: str) -> dict:
    """Verifica el PIN y devuelve rol + cartuchos permitidos + una llave de sesión."""
    d = _load()
    u = _find(d, uid)
    if not u:
        return {"status": "no_encontrado"}
    if not u.get("pin_hash"):
        return {"status": "sin_pin", "detalle": f"{u['nombre']} aún no tiene PIN. Créalo para entrar.",
                "id": u["id"], "nombre": u["nombre"]}
    if _hash(u["pin_salt"], pin or "") != u["pin_hash"]:
        return {"status": "denegado", "detalle": "PIN incorrecto."}
    return {"status": "ok", "id": u["id"], "nombre": u["nombre"], "rol": u["rol"],
            "rol_nombre": ROLES.get(u["rol"], {}).get("nombre", u["rol"]),
            "cartuchos": _cartuchos_de(u["rol"]),
            "token": secrets.token_urlsafe(24)}


def crear_usuario(nombre: str, rol: str, uid: str = "") -> dict:
    """Agrega un usuario nuevo (rol válido). El PIN lo pone él en su primer login."""
    if rol not in ROLES:
        return {"status": "error", "detalle": f"Rol inválido. Válidos: {list(ROLES)}"}
    nombre = (nombre or "").strip()
    if not nombre:
        return {"status": "error", "detalle": "Ponle nombre al usuario."}
    d = _load()
    uid = (uid or "".join(c for c in nombre.lower() if c.isalnum())) or secrets.token_hex(3)
    if _find(d, uid):
        return {"status": "existe", "detalle": f"Ya existe '{uid}'."}
    d["usuarios"].append({"id": uid, "nombre": nombre, "rol": rol, "pin_salt": "", "pin_hash": ""})
    _save(d)
    return {"status": "ok", "id": uid, "nombre": nombre, "rol": rol}


def eliminar_usuario(uid: str) -> dict:
    d = _load()
    u = _find(d, uid)
    if not u:
        return {"status": "no_encontrado"}
    if u["rol"] == "dueño" and sum(1 for x in d["usuarios"] if x["rol"] == "dueño") <= 1:
        return {"status": "error", "detalle": "No puedes borrar al único dueño."}
    d["usuarios"] = [x for x in d["usuarios"] if x["id"] != uid]
    _save(d)
    return {"status": "ok", "eliminado": uid}
