# -*- coding: utf-8 -*-
"""AURORA · Cambiar tu PIN, de verdad y en los dos lugares donde vive.

╔══════════════════════════════════════════════════════════════════════════╗
║ PARA QUÉ SIRVE                                                           ║
╚══════════════════════════════════════════════════════════════════════════╝

AURORA guarda PINes en DOS lugares distintos, y es fácil cambiar uno y dejar
el otro viejo:

  1. CONFIG/usuarios.json   → el PIN con el que entras al PANEL (Anuar, Rocío)
  2. CONFIG/identidad.json  → el PIN de DUEÑO, el que da control de la PC

Este programa los cambia juntos y COMPRUEBA que el nuevo PIN de verdad abre
antes de darse por bueno. Si algo sale mal, deja todo como estaba: escribe
primero una copia de respaldo de los dos archivos.

CÓMO SE USA
    Doble clic en SETUP\\CAMBIAR_PIN.bat
    (o:  python SETUP\\cambiar_pin.py)

Lo que escribas NO se ve en pantalla y NO se guarda en ningún registro.
"""
from __future__ import annotations

import getpass
import importlib.util

import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MINIMO = 6


def _ok(respuesta: dict) -> bool:
    """¿La operación salió bien?

    Ojo: los dos módulos de PIN de AURORA NO contestan igual. usuarios.py
    devuelve "ok" en minúscula y identidad_core.py devuelve "OK". Comparar
    contra una sola forma hacía que esta herramienta diera por fallado un
    cambio que sí funcionó, y lo revirtiera. Se comparan sin distinguir
    mayúsculas hasta que ambos módulos hablen igual (Fase 4 del plan raíz).
    """
    return str(respuesta.get("status", "")).lower() == "ok"


def _cargar(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


def _respaldar(archivos: list[Path]) -> Path:
    """Copia de seguridad antes de tocar nada. Si el cambio falla, se restaura."""
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = RAIZ / "BACKUPS" / f"pin_{sello}"
    carpeta.mkdir(parents=True, exist_ok=True)
    for a in archivos:
        if a.exists():
            shutil.copy2(a, carpeta / a.name)
    return carpeta


def _restaurar(carpeta: Path, archivos: list[Path]) -> None:
    for a in archivos:
        copia = carpeta / a.name
        if copia.exists():
            shutil.copy2(copia, a)


def _pedir_pin_nuevo() -> str:
    """Pide el PIN nuevo dos veces y revisa que no sea uno regalado."""
    obvios = {"123456", "1234567", "12345678", "000000", "0000000", "00000000",
              "111111", "654321", "abcdef", "password", "aurora", "aurora1"}
    while True:
        nuevo = getpass.getpass("PIN NUEVO (no se ve al escribir): ").strip()
        if len(nuevo) < MINIMO:
            print(f"   Muy corto. Mínimo {MINIMO} caracteres.\n")
            continue
        if nuevo.lower() in obvios:
            print("   Ese lo adivina cualquiera. Pon otro.\n")
            continue
        if len(set(nuevo)) == 1:
            print("   Todos los caracteres iguales. Pon otro.\n")
            continue
        otra = getpass.getpass("Escríbelo otra vez para confirmar: ").strip()
        if nuevo != otra:
            print("   No coinciden. Empezamos de nuevo.\n")
            continue
        return nuevo


def main() -> int:
    print("=" * 68)
    print("  AURORA · CAMBIO DE PIN")
    print("=" * 68)
    print("Cambia el PIN del PANEL y el de DUEÑO al mismo tiempo.")
    print("Nada de lo que escribas se muestra ni se guarda en ningún log.\n")

    usuarios_json = RAIZ / "CONFIG" / "usuarios.json"
    identidad_json = RAIZ / "CONFIG" / "identidad.json"
    archivos = [usuarios_json, identidad_json]

    usu = _cargar("usuarios", RAIZ / "AUTH" / "usuarios.py")
    ide = _cargar("identidad_core", RAIZ / "AUTH" / "identidad_core.py")

    cuentas = usu.listar_usuarios().get("usuarios", [])
    if not cuentas:
        print("No hay usuarios dados de alta. Nada que cambiar.")
        return 1

    print("Usuarios del panel:")
    for i, u in enumerate(cuentas, 1):
        print(f"   {i}) {u['nombre']}  ({u['rol']})")
    while True:
        sel = input(f"\n¿A cuál le cambias el PIN? [1-{len(cuentas)}]: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(cuentas):
            cuenta = cuentas[int(sel) - 1]
            break
        print("   Escribe solo el número.")

    print(f"\nCambiando el PIN de {cuenta['nombre']}.\n")
    actual = getpass.getpass("PIN ACTUAL (no se ve al escribir): ").strip()

    # Se comprueba ANTES de tocar nada: si el PIN actual no abre, no seguimos.
    abre_panel = _ok(usu.login(cuenta["id"], actual))
    abre_dueno = _ok(ide.login(actual))
    if not abre_panel and not abre_dueno:
        print("\nEse PIN no abre ninguno de los dos sistemas. No se cambió nada.")
        return 1
    print(f"   PIN actual → panel: {'sí' if abre_panel else 'no'} · "
          f"dueño: {'sí' if abre_dueno else 'no'}\n")

    nuevo = _pedir_pin_nuevo()
    if nuevo == actual:
        print("\nEl PIN nuevo es igual al de antes. No se cambió nada.")
        return 1

    copia = _respaldar(archivos)
    print(f"\nRespaldo de seguridad: {copia}")

    hechos, fallos = [], []

    if abre_panel:
        r = usu.configurar_pin(cuenta["id"], nuevo, actual)
        (hechos if _ok(r) else fallos).append(
            ("panel", r.get("detalle", r.get("status"))))
    if abre_dueno:
        r = ide.configurar_pin(nuevo, actual)
        (hechos if _ok(r) else fallos).append(
            ("dueño", r.get("detalle", r.get("status"))))

    # Comprobación REAL: se vuelve a entrar con el PIN nuevo. Sin esto, el
    # cambio es una promesa, no un hecho.
    ok_panel = (not abre_panel) or _ok(usu.login(cuenta["id"], nuevo))
    ok_dueno = (not abre_dueno) or _ok(ide.login(nuevo))

    if fallos or not (ok_panel and ok_dueno):
        print("\nALGO FALLÓ. Se está restaurando todo como estaba:")
        for donde, det in fallos:
            print(f"   - {donde}: {det}")
        if not ok_panel:
            print("   - el PIN nuevo NO abrió el panel al comprobarlo")
        if not ok_dueno:
            print("   - el PIN nuevo NO abrió dueño al comprobarlo")
        _restaurar(copia, archivos)
        print("Restaurado. Tu PIN de antes sigue funcionando.")
        return 1

    print("\n" + "=" * 68)
    print("  LISTO — y comprobado entrando con el PIN nuevo:")
    for donde, _ in hechos:
        print(f"   · {donde}: cambiado y verificado")
    print("=" * 68)

    if abre_dueno:
        rev = ide.revocar_todos()
        print(f"\nLlaves de dispositivos revocadas ({rev.get('status')}): "
              "en cada equipo hay que volver a entrar con el PIN nuevo.")

    print("\nSi habías escrito el PIN en un archivo o en un chat, bórralo ahora:")
    print("un PIN escrito en texto plano ya no es secreto.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelado. No se cambió nada.")
        sys.exit(1)
