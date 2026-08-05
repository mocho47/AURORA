# -*- coding: utf-8 -*-
"""AURORA · Índice de los programas de la PC — sin copiar nada

Anuar lo aclaró el 2026-08-04: "no es un respaldo, es lo que tenemos indexado".
Tiene razón: copiar ejecutables no sirve (un .exe instalado no funciona fuera de
su carpeta) y duplicar gigas de programas es puro desperdicio de disco.

Esto solo MIRA y ANOTA. Registra en un catálogo:
  • Programas instalados (leídos del registro de Windows, como los ve el sistema)
  • Instaladores guardados (los que sirven de verdad si hay que reinstalar)
  • Carpetas de programas portables (los que corren sin instalar)

Cero copias, cero movimientos, cero borrados. Solo saber qué hay.

Excluye los proyectos de código: NEXUS, AION, ENTERPRICE, AURORA y demás.

Correr:   python SISTEMA/indexar_programas.py
Buscar:   python SISTEMA/indexar_programas.py --buscar corel
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y truena con acentos y emojis.

    Se llama SOLO al correr el script directo. Hacerlo al importar le rompía la
    salida a quien lo importara — incluida AURORA (2026-08-05).
    """
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CATALOGO = RAIZ / "CONFIG" / "catalogo_programas.json"

# Proyectos de código: no son programas del sistema, son trabajo de Anuar.
_EXCLUIR = ("nexus", "aion", "enterprice", "enterprise", "aurora.worktrees",
            "evolucion", "chatbot_saas", "inmobiliaria_saas", "simplex", "forja",
            "node_modules", "site-packages", "__pycache__", ".git", ".venv")

# Un instalador de verdad: nombre delator, y pesa lo que pesa un instalador.
_PISTAS_INSTALADOR = ("setup", "install", "instalador", "installer", "_x64",
                      "-x64", "_win", "webinstall", "offline")
_MB_MINIMO_INSTALADOR = 3.0


def _excluida(p) -> bool:
    return any(x in str(p).lower() for x in _EXCLUIR)


def instalados() -> list:
    """Lo que Windows tiene registrado como instalado. Es la lista de verdad:
    la misma que ve 'Agregar o quitar programas'."""
    salida = []
    try:
        import winreg
    except ImportError:
        return salida
    claves = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    vistos = set()
    for raiz, ruta in claves:
        try:
            with winreg.OpenKey(raiz, ruta) as k:
                for i in range(winreg.QueryInfoKey(k)[0]):
                    try:
                        with winreg.OpenKey(k, winreg.EnumKey(k, i)) as sub:
                            def leer(nombre):
                                try:
                                    return winreg.QueryValueEx(sub, nombre)[0]
                                except OSError:
                                    return ""
                            nombre = str(leer("DisplayName") or "").strip()
                            if not nombre or nombre.lower() in vistos:
                                continue
                            vistos.add(nombre.lower())
                            salida.append({
                                "nombre": nombre,
                                "version": str(leer("DisplayVersion") or ""),
                                "editor": str(leer("Publisher") or ""),
                                "carpeta": str(leer("InstallLocation") or ""),
                                "mb": round(float(leer("EstimatedSize") or 0) / 1024, 1),
                            })
                    except OSError:
                        continue
        except OSError:
            continue
    return sorted(salida, key=lambda x: -x["mb"])


def instaladores() -> list:
    """Los .exe que SÍ sirven si hay que reinstalar: los autocontenidos."""
    salida = []
    for carpeta in (Path.home() / "Downloads", Path.home() / "Desktop",
                    Path.home() / "Documents"):
        if not carpeta.exists():
            continue
        try:
            for p in carpeta.rglob("*.exe"):
                if _excluida(p):
                    continue
                try:
                    mb = p.stat().st_size / 1e6
                except OSError:
                    continue
                n = p.name.lower()
                if any(x in n for x in _PISTAS_INSTALADOR) or mb >= _MB_MINIMO_INSTALADOR:
                    salida.append({"nombre": p.name, "ruta": str(p), "mb": round(mb, 1)})
        except (OSError, PermissionError):
            continue
    return sorted(salida, key=lambda x: -x["mb"])


def portables() -> list:
    """Carpetas que traen un .exe y corren sin instalarse."""
    salida = []
    for base in (Path.home() / "Downloads", Path.home() / "Desktop",
                 Path("C:/"), Path("D:/")):
        if not base.exists():
            continue
        try:
            for d in base.iterdir():
                if not d.is_dir() or _excluida(d):
                    continue
                try:
                    exes = [x for x in d.glob("*.exe")][:3]
                except (OSError, PermissionError):
                    continue
                if exes:
                    try:
                        mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                    except (OSError, PermissionError):
                        mb = 0
                    salida.append({"nombre": d.name, "ruta": str(d),
                                   "ejecutables": [x.name for x in exes],
                                   "mb": round(mb, 1)})
        except (OSError, PermissionError):
            continue
    return sorted(salida, key=lambda x: -x["mb"])


def main() -> int:
    if "--buscar" in sys.argv:
        i = sys.argv.index("--buscar")
        q = " ".join(sys.argv[i + 1:]).lower()
        if not CATALOGO.exists():
            print("No hay catálogo. Corre: python SISTEMA/indexar_programas.py")
            return 1
        d = json.loads(CATALOGO.read_text(encoding="utf-8"))
        for seccion in ("instalados", "instaladores", "portables"):
            hits = [x for x in d.get(seccion, [])
                    if q in json.dumps(x, ensure_ascii=False).lower()]
            if hits:
                print(f"\n=== {seccion.upper()} ({len(hits)})")
                for x in hits[:12]:
                    print(f"  {x.get('nombre','')[:52]:54} {x.get('mb',0):8.1f} MB")
                    if x.get("ruta"):
                        print(f"     {x['ruta']}")
                    elif x.get("carpeta"):
                        print(f"     {x['carpeta']}")
        return 0

    print("Indexando los programas de la PC. NO se copia ni se mueve nada.")
    print("Excluyendo: NEXUS, AION, ENTERPRICE, AURORA y demás proyectos.")
    print("=" * 74)

    ins = instalados()
    print(f"  Instalados (registro de Windows) : {len(ins)}")
    inst = instaladores()
    print(f"  Instaladores guardados           : {len(inst)}")
    port = portables()
    print(f"  Carpetas portables               : {len(port)}")

    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_text(json.dumps({
        "nota": ("Índice de los programas de esta PC. NO es un respaldo: nada se "
                 "copió. Regenerar con python SISTEMA/indexar_programas.py"),
        "instalados": ins, "instaladores": inst, "portables": port,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 74)
    print(f"  Guardado en: {CATALOGO}")
    print()
    print("  LOS 10 QUE MÁS DISCO OCUPAN:")
    for x in ins[:10]:
        print(f"    {x['nombre'][:48]:50} {x['mb']:9.1f} MB")
    if inst:
        print()
        print("  INSTALADORES MÁS PESADOS (los que sirven si reinstalas):")
        for x in inst[:6]:
            print(f"    {x['nombre'][:48]:50} {x['mb']:9.1f} MB")
    print()
    print("  Buscar:  python SISTEMA/indexar_programas.py --buscar corel")
    return 0


if __name__ == "__main__":
    _consola_utf8()
    raise SystemExit(main())
