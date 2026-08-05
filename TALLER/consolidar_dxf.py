# -*- coding: utf-8 -*-
"""AURORA · Juntar TODOS los DXF en una sola carpeta, sin duplicados

Anuar lo pidió el 2026-08-04: tiene 665 DXF regados por el disco y las USB, y
cuando un cliente le pide algo no encuentra nada. Sin el DXF no hay metros de
corte, y sin metros no hay precio — así vendió una casa de muñecas en $280 que
costaba ~$200 producir.

Esto COPIA (no mueve, no borra) todos los .dxf a una sola carpeta, saltando los
duplicados reales. Los duplicados se detectan por HASH del contenido, no por
nombre: así agarra los "ABox (1).dxf", "ABox (2).dxf" que son el mismo archivo
con nombre distinto.

Los originales se quedan donde están. Borrarlos es decisión de Anuar, después
de ver el resultado.

Correr:  python TALLER/consolidar_dxf.py
"""
from __future__ import annotations
import hashlib
import io
import shutil
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

DESTINO = Path.home() / "Downloads" / "dxf"

# Dónde buscar: el perfil del usuario y cualquier unidad extraíble.
_IGNORAR = ("_OBSOLETOS", "_ARCHIVE", "_RESCATE", "node_modules", "site-packages",
            "__pycache__", ".git", "AppData", "_BACKUP", "Windows", "Program Files")


def _unidades() -> list:
    """El disco del usuario más las USB conectadas."""
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
    """Hash del contenido. Dos archivos con el mismo hash son el MISMO archivo,
    aunque se llamen distinto."""
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _nombre_libre(destino: Path, nombre: str) -> Path:
    """Si ya existe uno con ese nombre pero DISTINTO contenido, no se pisa."""
    p = destino / nombre
    if not p.exists():
        return p
    tallo, ext = p.stem, p.suffix
    for n in range(2, 999):
        q = destino / f"{tallo}__{n}{ext}"
        if not q.exists():
            return q
    return destino / f"{tallo}__x{ext}"


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    print(f"Destino: {DESTINO}")
    print("Buscando .dxf en el disco y las USB conectadas...")

    encontrados = []
    for raiz in _unidades():
        try:
            for p in raiz.rglob("*.dxf"):
                if any(x in str(p) for x in _IGNORAR):
                    continue
                if DESTINO in p.parents:
                    continue          # lo ya consolidado no se vuelve a leer
                encontrados.append(p)
        except (OSError, PermissionError):
            continue

    print(f"Encontrados: {len(encontrados)}")
    print("=" * 74)

    # Lo que YA está en el destino cuenta como visto, para poder correrlo otra vez.
    vistos = {}
    for p in DESTINO.glob("*.dxf"):
        h = _huella(p)
        if h:
            vistos[h] = p

    copiados, duplicados, fallidos = 0, 0, 0
    bytes_ahorrados = 0
    for i, p in enumerate(encontrados, 1):
        h = _huella(p)
        if not h:
            fallidos += 1
            continue
        if h in vistos:
            duplicados += 1
            try:
                bytes_ahorrados += p.stat().st_size
            except OSError:
                pass
            continue
        try:
            shutil.copy2(p, _nombre_libre(DESTINO, p.name))
            vistos[h] = p
            copiados += 1
        except (OSError, PermissionError):
            fallidos += 1
        if i % 100 == 0:
            print(f"   [{i}/{len(encontrados)}]  {copiados} únicos, {duplicados} duplicados")

    print("=" * 74)
    print(f"  ÚNICOS copiados     : {copiados}")
    print(f"  Duplicados saltados : {duplicados}   ({bytes_ahorrados/1e6:.1f} MB que no se repitieron)")
    print(f"  No se pudieron leer : {fallidos}")
    print(f"  TOTAL en la carpeta : {len(list(DESTINO.glob('*.dxf')))}")
    print()
    print(f"  Todo en: {DESTINO}")
    print("  Los originales NO se tocaron. Si quieres borrarlos, dilo y")
    print("  te preparo la lista exacta de lo que se borraría.")
    print()
    print("  Siguiente paso — catalogarlos con su precio:")
    print("     python TALLER/indexar_dxf.py")
    return 0


if __name__ == "__main__":
    _consola_utf8()
    raise SystemExit(main())
