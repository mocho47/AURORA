# -*- coding: utf-8 -*-
"""AURORA · Apartar los archivos duplicados en una carpeta, para revisarlos

Anuar lo pidió el 2026-08-04: "genera 1 carpeta con todo lo duplicado, no
respaldo, solo lo duplicado, así reviso y borro".

Los duplicados se detectan por HASH del contenido, nunca por nombre: así agarra
los "ABox (1)", "ABox (2)" que son el mismo archivo renombrado, y NO confunde
dos archivos distintos que se llaman igual.

De cada grupo de idénticos se CONSERVA UNO en su lugar (el de la ruta más
corta y limpia, que suele ser el original) y los demás se MUEVEN a
Descargas\\_DUPLICADOS\\.

Todo movimiento queda anotado en un reporte con su origen exacto, así que es
REVERSIBLE. Nada se borra: eso lo decide Anuar viendo la carpeta.

Correr:
    python SISTEMA/apartar_duplicados.py --ver          solo mira y reporta
    python SISTEMA/apartar_duplicados.py --mover        aparta de verdad
    python SISTEMA/apartar_duplicados.py --deshacer     los regresa a su lugar
"""
from __future__ import annotations
import hashlib
import io
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y truena con acentos y emojis.

    Se llama SOLO al correr el script directo. Hacerlo al importar le rompía la
    salida a quien lo importara — incluida AURORA (2026-08-05).
    """
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CUARENTENA = Path.home() / "Downloads" / "_DUPLICADOS"
REPORTE = CUARENTENA / "_de_donde_salieron.json"

# Tipos que vale la pena revisar. Se dejan fuera los del sistema a propósito.
EXTENSIONES = ("dxf", "pdf", "jpg", "jpeg", "png", "svg", "ai", "eps", "cdr",
               "zip", "rar", "7z", "mp4", "docx", "xlsx", "txt")

_EXCLUIR = ("nexus", "aion", "enterprice", "enterprise", "aurora.worktrees",
            "evolucion", "chatbot_saas", "inmobiliaria_saas", "simplex", "forja",
            "windows", "program files", "programdata", "appdata", "$recycle",
            "node_modules", "site-packages", "__pycache__", ".git", ".venv",
            "_obsoletos", "_archive", "_rescate", "_backup", "system volume",
            "_duplicados")

TAMANO_MINIMO = 1024      # menos de 1 KB no vale la pena mover


def _excluida(p) -> bool:
    return any(x in str(p).lower() for x in _EXCLUIR)


def _huella(p: Path) -> str:
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _cual_conservar(rutas: list) -> Path:
    """El original suele ser el de ruta más corta y sin '(1)' en el nombre."""
    def puntaje(p: Path):
        n = p.name.lower()
        feo = sum(x in n for x in ("(1)", "(2)", "(3)", "copia", "copy", " - copia"))
        return (feo, len(str(p)), str(p))
    return sorted(rutas, key=puntaje)[0]


def buscar_duplicados() -> dict:
    raices = [Path.home()]
    for letra in "DEFGHIJ":
        u = Path(f"{letra}:/")
        try:
            if u.exists() and any(u.iterdir()):
                raices.append(u)
        except (OSError, PermissionError):
            pass

    por_tamano = defaultdict(list)
    for raiz in raices:
        for ext in EXTENSIONES:
            try:
                for p in raiz.rglob(f"*.{ext}"):
                    if _excluida(p):
                        continue
                    try:
                        t = p.stat().st_size
                    except OSError:
                        continue
                    if t >= TAMANO_MINIMO:
                        por_tamano[t].append(p)
            except (OSError, PermissionError):
                continue

    # Solo se calcula el hash de los que comparten tamaño: leer todo sería lentísimo.
    grupos = defaultdict(list)
    for t, rutas in por_tamano.items():
        if len(rutas) < 2:
            continue
        for p in rutas:
            h = _huella(p)
            if h:
                grupos[h].append(p)
    return {h: rutas for h, rutas in grupos.items() if len(rutas) > 1}


def main() -> int:
    if "--deshacer" in sys.argv:
        if not REPORTE.exists():
            print("No hay reporte: no hay nada que deshacer.")
            return 1
        datos = json.loads(REPORTE.read_text(encoding="utf-8"))
        vueltos = 0
        for item in datos.get("movidos", []):
            origen, actual = Path(item["origen"]), Path(item["ahora_en"])
            if actual.exists() and not origen.exists():
                try:
                    origen.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(actual), str(origen))
                    vueltos += 1
                except OSError:
                    pass
        print(f"Regresados a su lugar: {vueltos}")
        return 0

    mover = "--mover" in sys.argv
    print("Buscando duplicados por CONTENIDO (no por nombre)...")
    print("Excluyendo: NEXUS, AION, ENTERPRICE, AURORA, Windows y Program Files")
    print("=" * 74)

    grupos = buscar_duplicados()
    total_dup = sum(len(v) - 1 for v in grupos.values())
    bytes_dup = 0
    for rutas in grupos.values():
        try:
            bytes_dup += rutas[0].stat().st_size * (len(rutas) - 1)
        except OSError:
            pass

    print(f"  Grupos de archivos repetidos : {len(grupos)}")
    print(f"  Copias de más                : {total_dup}")
    print(f"  Espacio desperdiciado        : {bytes_dup/1e9:.2f} GB")
    print("=" * 74)

    if not grupos:
        print("  No hay duplicados. Nada que hacer.")
        return 0

    print("\n  LOS 12 QUE MÁS ESPACIO DESPERDICIAN:")
    orden = sorted(grupos.items(),
                   key=lambda kv: -(kv[1][0].stat().st_size * (len(kv[1]) - 1)
                                    if kv[1][0].exists() else 0))
    for _h, rutas in orden[:12]:
        try:
            mb = rutas[0].stat().st_size / 1e6
        except OSError:
            continue
        print(f"    {rutas[0].name[:44]:46} {len(rutas)} copias × {mb:.1f} MB")

    if not mover:
        print("\n  Esto fue SOLO MIRAR. Para apartarlos de verdad:")
        print("     python SISTEMA/apartar_duplicados.py --mover")
        return 0

    CUARENTENA.mkdir(parents=True, exist_ok=True)
    movidos, fallidos = [], 0
    for _h, rutas in grupos.items():
        queda = _cual_conservar(rutas)
        for p in rutas:
            if p == queda:
                continue
            destino = CUARENTENA / p.name
            n = 2
            while destino.exists():
                destino = CUARENTENA / f"{p.stem}__{n}{p.suffix}"
                n += 1
            try:
                shutil.move(str(p), str(destino))
                movidos.append({"origen": str(p), "ahora_en": str(destino),
                                "se_conservo": str(queda)})
            except (OSError, PermissionError):
                fallidos += 1

    REPORTE.write_text(json.dumps({
        "nota": ("De aquí salió cada duplicado. Para regresarlos todos: "
                 "python SISTEMA/apartar_duplicados.py --deshacer"),
        "total": len(movidos), "movidos": movidos,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  APARTADOS  : {len(movidos)}")
    print(f"  No se pudo : {fallidos}")
    print(f"  Están en   : {CUARENTENA}")
    print(f"  Reporte    : {REPORTE.name}  (dice de dónde salió cada uno)")
    print()
    print("  Revísalos y borra la carpeta cuando estés seguro.")
    print("  Si algo se movió mal:  python SISTEMA/apartar_duplicados.py --deshacer")
    return 0


if __name__ == "__main__":
    _consola_utf8()
    raise SystemExit(main())
