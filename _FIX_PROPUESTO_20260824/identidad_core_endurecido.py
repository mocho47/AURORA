# -*- coding: utf-8 -*-
"""AURORA · IDENTIDAD ENDURECIDA — reemplazo de AUTH/identidad_core.py

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ ESTE ARCHIVO                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

El PIN de dueño da control total: ejecutar PowerShell real en la PC, escribir
cualquier archivo del proyecto, mover cosas. La auditoría encontró tres
debilidades que se suman entre sí:

1. `CONFIG/identidad.json` (que guarda el salt y el hash del PIN) está
   versionado en git desde el primer commit. Nunca se protegió como sí se
   protegió el `.env`.
2. El hash es **un solo pase de SHA-256**. SHA-256 está diseñado para ser
   RÁPIDO, que es exactamente lo contrario de lo que quieres para una
   contraseña: un PIN de 4-6 dígitos se prueba entero en milisegundos.
3. El PIN mínimo son **4 caracteres** y `/auth/login` no tiene ningún límite
   de intentos (la bandera `enable_rate_limiting` existe en `config.py` pero
   nunca se conectó a nada).

Juntas significan: quien tenga una copia del repo puede romper el PIN sin
tocar el servidor, offline, en un instante.

QUÉ CAMBIA (corrección de raíz):

* **PBKDF2 con 240,000 iteraciones** en vez de SHA-256 pelón. Convierte un
  ataque de milisegundos en uno de años. Es el mismo cambio que hace la
  diferencia entre "hash" y "hash de contraseña".
* **Mínimo 8 caracteres** al definir un PIN nuevo.
* **Bloqueo por intentos**: 5 fallos seguidos y espera de 15 minutos.
* **Comparación en tiempo constante** en todos los caminos, no solo en uno.

COMPATIBILIDAD — esto importa, es lo que evita dejarte fuera de tu propio
sistema: tu PIN actual está guardado en el formato viejo. Este archivo **sigue
aceptando el formato viejo** para que entres normal, y en cuanto entras bien,
**vuelve a guardar tu PIN en el formato nuevo automáticamente**, sin que hagas
nada. No hay un momento en que quedes bloqueado.

El mínimo de 8 aplica **solo al definir un PIN nuevo**, nunca al entrar. Si tu
PIN actual es de 4, sigues entrando — pero el sistema te lo va a decir, porque
callarlo sería fingir que estás protegido.

DECISIONES PENDIENTES DE ANUAR (por eso esto no está aplicado):
  1. El PIN nuevo, de 8 o más. Este archivo no lo cambia solo.
  2. Sacar `CONFIG/identidad.json` de git y purgarlo del historial — es
     irreversible y no se hace sin tu confirmación (ver `gitignore_agregar.txt`).

Nota honesta sobre el límite de intentos: el contador vive en memoria, así que
reiniciar el servidor lo reinicia. Para reiniciar el servidor ya se necesita
acceso local a la PC, así que no debilita la defensa contra alguien en la red
— pero es correcto decirlo en vez de venderlo como más de lo que es.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime
from pathlib import Path

CFG = Path(__file__).resolve().parent.parent / "CONFIG" / "identidad.json"

# ── Parámetros de endurecimiento ─────────────────────────────────────────────
ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 240_000          # ~0.1 s por intento en esta PC: imperceptible
                               # para ti, inviable para fuerza bruta.
PIN_MINIMO = 8
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 15 * 60

# Contador de intentos fallidos. En memoria a propósito (ver nota del docstring).
_fallos: dict[str, list] = {}


def _load() -> dict:
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {"pin_salt": "", "pin_hash": "", "tokens": []}


def _save(d: dict) -> None:
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Hashing ──────────────────────────────────────────────────────────────────
def _hash_viejo(salt: str, valor: str) -> str:
    """El SHA-256 de un solo pase que se usaba antes.

    Se conserva SOLO para poder verificar credenciales ya guardadas y migrarlas.
    Nunca se usa para guardar algo nuevo.
    """
    return hashlib.sha256((salt + valor).encode("utf-8")).hexdigest()


def _hash_fuerte(salt: str, valor: str, iteraciones: int = ITERACIONES) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", valor.encode("utf-8"), salt.encode("utf-8"), iteraciones
    ).hex()


def _verificar(d: dict, pin: str) -> tuple[bool, bool]:
    """¿El PIN es correcto? Devuelve (es_correcto, hay_que_migrarlo).

    Entiende los dos formatos para que nadie quede fuera durante la migración.
    """
    guardado = d.get("pin_hash", "")
    salt = d.get("pin_salt", "")
    if not guardado or not salt:
        return (False, False)

    if d.get("pin_algoritmo") == ALGORITMO:
        calculado = _hash_fuerte(salt, pin or "", d.get("pin_iteraciones", ITERACIONES))
        return (hmac.compare_digest(calculado, guardado), False)

    # Formato viejo: si es correcto, se aprovecha para migrarlo en el acto.
    correcto = hmac.compare_digest(_hash_viejo(salt, pin or ""), guardado)
    return (correcto, correcto)


def _migrar(d: dict, pin: str) -> None:
    """Reescribe el PIN correcto en el formato fuerte. Se llama solo tras un
    login exitoso, que es el único momento en que se conoce el PIN en claro."""
    salt = secrets.token_hex(16)
    d["pin_salt"] = salt
    d["pin_hash"] = _hash_fuerte(salt, pin)
    d["pin_algoritmo"] = ALGORITMO
    d["pin_iteraciones"] = ITERACIONES
    d["pin_migrado"] = datetime.now().isoformat(timespec="seconds")
    _save(d)


# ── Bloqueo por intentos ─────────────────────────────────────────────────────
def _bloqueado(origen: str) -> int:
    """Segundos que faltan de castigo, o 0 si puede intentar."""
    intentos = _fallos.get(origen, [])
    recientes = [t for t in intentos if time.time() - t < BLOQUEO_SEGUNDOS]
    _fallos[origen] = recientes
    if len(recientes) < MAX_INTENTOS:
        return 0
    return int(BLOQUEO_SEGUNDOS - (time.time() - recientes[0]))


def _anotar_fallo(origen: str) -> None:
    _fallos.setdefault(origen, []).append(time.time())


def _limpiar_fallos(origen: str) -> None:
    _fallos.pop(origen, None)


# ── API pública (misma firma que el archivo original) ────────────────────────
def estado() -> dict:
    d = _load()
    return {"status": "OK",
            "configurado": bool(d.get("pin_hash")),
            "dispositivos_confiables": len(d.get("tokens", [])),
            "algoritmo": d.get("pin_algoritmo", "sha256_simple (débil, se migra al entrar)")}


def configurar_pin(pin_nuevo: str, pin_actual: str = "") -> dict:
    """Define o cambia el PIN del dueño. Si ya existe, exige el PIN actual."""
    if not pin_nuevo or len(pin_nuevo) < PIN_MINIMO:
        return {"status": "ERROR",
                "detalle": f"El PIN debe tener al menos {PIN_MINIMO} caracteres. "
                           "Con menos, alguien que tenga una copia del repositorio "
                           "puede adivinarlo sin tocar el servidor."}

    d = _load()
    if d.get("pin_hash"):
        correcto, _ = _verificar(d, pin_actual)
        if not correcto:
            return {"status": "ERROR", "detalle": "PIN actual incorrecto."}

    salt = secrets.token_hex(16)
    d["pin_salt"] = salt
    d["pin_hash"] = _hash_fuerte(salt, pin_nuevo)
    d["pin_algoritmo"] = ALGORITMO
    d["pin_iteraciones"] = ITERACIONES
    d.setdefault("tokens", [])
    _save(d)
    return {"status": "OK",
            "detalle": "PIN del dueño configurado y guardado en formato fuerte."}


def login(pin: str, origen: str = "local") -> dict:
    """Verifica el PIN y, si es correcto, emite una LLAVE para este dispositivo."""
    faltan = _bloqueado(origen)
    if faltan:
        return {"status": "BLOQUEADO",
                "detalle": f"Demasiados intentos fallidos. Espera {faltan // 60 + 1} "
                           "minutos antes de volver a intentar.",
                "segundos_restantes": faltan}

    d = _load()
    if not d.get("pin_hash"):
        return {"status": "SIN_CONFIGURAR", "detalle": "Aún no defines tu PIN de dueño."}

    correcto, hay_que_migrar = _verificar(d, pin or "")
    if not correcto:
        _anotar_fallo(origen)
        restantes = MAX_INTENTOS - len(_fallos.get(origen, []))
        return {"status": "DENEGADO",
                "detalle": ("PIN incorrecto." if restantes > 0 else
                            "PIN incorrecto. Siguiente intento queda bloqueado."),
                "intentos_restantes": max(0, restantes)}

    _limpiar_fallos(origen)

    aviso = None
    if hay_que_migrar:
        _migrar(d, pin)
        d = _load()
        aviso = "Tu PIN quedó guardado en el formato seguro nuevo."
    if len(pin) < PIN_MINIMO:
        aviso = ((aviso + " ") if aviso else "") + (
            f"Aviso: tu PIN tiene {len(pin)} caracteres. Se recomiendan "
            f"{PIN_MINIMO} o más — cámbialo cuando puedas.")

    token = secrets.token_urlsafe(32)
    tsalt = secrets.token_hex(16)
    d.setdefault("tokens", []).append({
        "salt": tsalt,
        "hash": _hash_fuerte(tsalt, token),
        "algoritmo": ALGORITMO,
        "iteraciones": ITERACIONES,
        "creado": datetime.now().isoformat(timespec="seconds"),
    })
    _save(d)

    r = {"status": "OK", "rol": "dueño", "token": token,
         "detalle": "Dispositivo de confianza registrado."}
    if aviso:
        r["aviso"] = aviso
    return r


def rol(token: str) -> str:
    """Devuelve 'dueño' si la llave es válida; si no, 'cliente'."""
    if not token:
        return "cliente"
    d = _load()
    for t in d.get("tokens", []):
        if t.get("algoritmo") == ALGORITMO:
            calculado = _hash_fuerte(t["salt"], token, t.get("iteraciones", ITERACIONES))
        else:
            calculado = _hash_viejo(t["salt"], token)
        if hmac.compare_digest(calculado, t["hash"]):
            return "dueño"
    return "cliente"


def revocar_todos() -> dict:
    """Cierra sesión en TODOS los dispositivos (si pierdes uno o sospechas)."""
    d = _load()
    d["tokens"] = []
    _save(d)
    _fallos.clear()
    return {"status": "OK",
            "detalle": "Todas las llaves revocadas. Vuelve a iniciar sesión con tu PIN."}
