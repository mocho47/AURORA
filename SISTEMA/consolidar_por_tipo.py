# -*- coding: utf-8 -*-
"""AURORA · Juntar los archivos por tipo en una carpeta cada uno, sin duplicados

Anuar lo pidió el 2026-08-04, después de que la consolidación de DXF resolviera
su problema real: tenía 665 diseños regados y no encontraba ninguno cuando un
cliente le pedía algo.

Misma mecánica para los demás tipos: COPIA (nunca mueve, nunca borra) a
Descargas\\<tipo>\\, saltando duplicados detectados por HASH del contenido — no
por nombre, así agarra los "archivo (1)", "archivo (2)" que son el mismo.

EXCLUYE los proyectos de código (NEXUS, AION, AION MASTER, ENTERPRICE...): esos
archivos pertenecen a su proyecto y sacarlos de ahí no sirve de nada.

Correr:
    python SISTEMA/consolidar_por_tipo.py pdf
    python SISTEMA/consolidar_por_tipo.py pdf txt zip rar
    python SISTEMA/consolidar_por_tipo.py --todos
"""
from __future__ import annotations
import hashlib
import io
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DESTINO = Path.home() / "Downloads"

# Tipos que valen la pena juntar. El .exe NO está aquí a propósito: un ejecutable
# casi nunca funciona fuera de su carpeta (le faltan sus DLLs), así que juntarlos
# da un montón de programas rotos. Se puede pedir explícitamente si se quiere.
TIPOS_SEGUROS = ("pdf", "txt", "zip", "rar", "7z", "svg", "ai", "eps",
                 "cdr", "psd", "xlsx", "docx")

# Carpetas de proyectos y del sistema que NO se tocan.
_EXCLUIR = (
    # Proyectos de código de Anuar — sus archivos pertenecen a su proyecto
    "nexus", "aion", "enterprice", "enterprise", "aurora.worktrees",
    "evolucion", "chatbot_saas", "inmobiliaria_saas", "simplex", "forja",
    # Sistema y basura técnica
    "windows", "program files", "programdata", "appdata", "$recycle",
    "node_modules", "site-packages", "__pycache__", ".git", ".venv", "venv",
    "_obsoletos", "_archive", "_rescate", "_backup", "system volume",
)


def _excluida(p: Path) -> bool:
    s = str(p).lower()
    return any(x in s for x in _EXCLUIR)


def _unidades() -> list:
    raices = [Path.home()]
    for letra in "DEFGHIJ":
        u = Path(f"{letra}:/")
        try:
            if u.exists() and any(u.iterdir()):
                raices.append(u)
        except (OSError, PermissionError):
            pass
    return raices


def _huella(p: Path) -> str:
    """Hash del contenido: dos archivos iguales lo son aunque cambien de nombre."""
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _nombre_libre(destino: Path, nombre: str) -> Path:
    p = destino / nombre
    if not p.exists():
        return p
    tallo, ext = p.stem, p.suffix
    for n in range(2, 999):
        q = destino / f"{tallo}__{n}{ext}"
        if not q.exists():
            return q
    return destino / f"{tallo}__x{ext}"


def consolidar(ext: str) -> dict:
    ext = ext.lower().lstrip(".")
    destino = BASE_DESTINO / ext
    destino.mkdir(parents=True, exist_ok=True)

    encontrados = []
    for raiz in _unidades():
        try:
            for p in raiz.rglob(f"*.{ext}"):
                if _excluida(p) or destino in p.parents:
                    continue
                encontrados.append(p)
        except (OSError, PermissionError):
            continue

    print(f"\n=== .{ext.upper()}  — encontrados {len(encontrados)}")
    if not encontrados:
        return {"ext": ext, "copiados": 0, "duplicados": 0}

    vistos = {}
    for p in destino.glob(f"*.{ext}"):
        h = _huella(p)
        if h:
            vistos[h] = p

    copiados, duplicados, fallidos, ahorro = 0, 0, 0, 0
    for i, p in enumerate(encontrados, 1):
        h = _huella(p)
        if not h:
            fallidos += 1
            continue
        if h in vistos:
            duplicados += 1
            try:
                ahorro += p.stat().st_size
            except OSError:
                pass
            continue
        try:
            shutil.copy2(p, _nombre_libre(destino, p.name))
            vistos[h] = p
            copiados += 1
        except (OSError, PermissionError):
            fallidos += 1
        if i % 200 == 0:
            print(f"     [{i}/{len(encontrados)}]")

    print(f"     únicos {copiados} · duplicados {duplicados} "
          f"({ahorro/1e6:.1f} MB) · ilegibles {fallidos}")
    print(f"     → {destino}")
    return {"ext": ext, "copiados": copiados, "duplicados": duplicados,
            "mb_ahorrados": round(ahorro / 1e6, 1)}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tipos = list(TIPOS_SEGUROS) if "--todos" in sys.argv else args
    if not tipos:
        print(__doc__)
        print(f"Tipos seguros: {', '.join(TIPOS_SEGUROS)}")
        return 1

    if "exe" in tipos:
        print("AVISO: los .exe casi nunca funcionan fuera de su carpeta (les")
        print("faltan sus DLLs). Sirve para instaladores sueltos, no para")
        print("programas ya instalados.\n")

    print(f"Consolidando: {', '.join(tipos)}")
    print(f"Excluyendo proyectos: NEXUS, AION, ENTERPRICE, AURORA y demás")
    print("Se COPIA. Nada se mueve ni se borra.")
    print("=" * 74)

    total_c, total_d, total_mb = 0, 0, 0.0
    for t in tipos:
        r = consolidar(t)
        total_c += r["copiados"]
        total_d += r["duplicados"]
        total_mb += r.get("mb_ahorrados", 0)

    print("\n" + "=" * 74)
    print(f"  TOTAL únicos copiados : {total_c}")
    print(f"  TOTAL duplicados      : {total_d}  ({total_mb:.1f} MB que no se repitieron)")
    print(f"  Todo bajo             : {BASE_DESTINO}")
    print("  Los originales NO se tocaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
