# -*- coding: utf-8 -*-
"""
AURORA · ORGANIZADOR DE ARCHIVOS (escanear todo el PC + agrupar por tipo)
Seguro por diseño (regla de Anuar: sin romper nada, NO tocar la carpeta de AURORA):

- escanear(): SOLO LECTURA. Cataloga archivos por extensión en todo el árbol elegido.
  No mueve ni borra nada. Ideal para "ver qué hay" agrupado (zip/rar/dxf/pdf/…).
- agrupar(): mueve archivos SUELTOS a subcarpetas por tipo (_ZIP, _DXF, …) SOLO dentro
  de UNA carpeta segura que Anuar elija. Por defecto es SIMULACRO (mover=False): dice qué
  haría sin tocar nada. Con mover=True lo hace y deja un MANIFIESTO reversible.

BLINDAJE: nunca entra ni toca AURORA, Windows, Program Files, ProgramData ni AppData.
"""
from __future__ import annotations
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

AURORA_ROOT = Path(__file__).resolve().parent.parent          # C:\AURORA.worktrees
HOME = Path(os.path.expanduser("~"))

# Rutas que NUNCA se tocan ni se escanean (blindaje duro)
PROHIBIDAS = [
    AURORA_ROOT,
    Path(r"C:\Windows"),
    Path(r"C:\Program Files"),
    Path(r"C:\Program Files (x86)"),
    Path(r"C:\ProgramData"),
    HOME / "AppData",
]
# Carpetas seguras donde SÍ se permite mover/agrupar
SEGURAS = [HOME / "Desktop", HOME / "Downloads", HOME / "Documents",
           HOME / "Escritorio", HOME / "Descargas", HOME / "Documentos"]

# Agrupación por tipo → nombre de subcarpeta destino
GRUPOS_EXT = {
    "_COMPRIMIDOS": {".zip", ".rar", ".7z", ".gz", ".tar"},
    "_CORTE_DXF":   {".dxf", ".dwg", ".plt"},
    "_VECTORES":    {".svg", ".ai", ".eps", ".cdr"},
    "_PDF":         {".pdf"},
    "_IMAGENES":    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"},
    "_VIDEOS":      {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"},
    "_DOCUMENTOS":  {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"},
    "_INSTALADORES":{".exe", ".msi"},
    "_DISENO_3D":   {".stl", ".obj", ".3mf", ".f3d"},
}
_EXT2GRUPO = {e: g for g, exts in GRUPOS_EXT.items() for e in exts}
_GRUPO_NOMBRES = set(GRUPOS_EXT.keys())


def _prohibida(p: Path) -> bool:
    """True si la ruta cae dentro de una zona blindada."""
    try:
        rp = p.resolve()
    except Exception:
        return True
    for d in PROHIBIDAS:
        try:
            rp.relative_to(d.resolve())
            return True
        except Exception:
            continue
    return False


def _segura(carpeta: Path) -> bool:
    """True solo si la carpeta está dentro de una raíz segura y no es zona blindada."""
    if _prohibida(carpeta):
        return False
    rc = carpeta.resolve()
    for s in SEGURAS:
        try:
            rc.relative_to(s.resolve())
            return True
        except Exception:
            continue
    return rc in {s.resolve() for s in SEGURAS}


def escanear(raiz: str = "", extensiones: list | None = None, max_ejemplos: int = 5) -> dict:
    """
    SOLO LECTURA. Cataloga archivos por tipo bajo 'raiz' (por defecto el perfil del usuario),
    saltando zonas blindadas. No mueve ni borra nada.
    """
    base = Path(raiz) if raiz else HOME
    if not base.exists():
        return {"status": "error", "detalle": f"No existe: {base}"}
    filtro = {e.lower() if e.startswith(".") else "." + e.lower() for e in (extensiones or [])}
    grupos: dict = {}
    total = 0
    tam = 0
    for dirpath, dirnames, filenames in os.walk(base):
        d = Path(dirpath)
        if _prohibida(d):
            dirnames[:] = []          # no desciende a zonas blindadas
            continue
        # no re-cataloga lo ya agrupado
        dirnames[:] = [x for x in dirnames if x not in _GRUPO_NOMBRES]
        for fn in filenames:
            ext = Path(fn).suffix.lower() or "(sin_ext)"
            if filtro and ext not in filtro:
                continue
            fp = d / fn
            try:
                sz = fp.stat().st_size
            except Exception:
                continue
            g = grupos.setdefault(ext, {"archivos": 0, "mb": 0.0, "ejemplos": []})
            g["archivos"] += 1
            g["mb"] = round(g["mb"] + sz / 1048576, 1)
            if len(g["ejemplos"]) < max_ejemplos:
                g["ejemplos"].append(str(fp))
            total += 1
            tam += sz
    grupos_ord = dict(sorted(grupos.items(), key=lambda kv: kv[1]["archivos"], reverse=True))
    return {"status": "ok", "raiz": str(base), "total_archivos": total,
            "gb_total": round(tam / 1073741824, 2), "tipos": len(grupos_ord),
            "por_tipo": grupos_ord}


def agrupar(carpeta: str, mover: bool = False) -> dict:
    """
    Agrupa archivos SUELTOS de UNA carpeta segura en subcarpetas por tipo (_PDF, _DXF, …).
    mover=False (default) = SIMULACRO (no toca nada). mover=True = ejecuta + manifiesto reversible.
    Nunca entra a subcarpetas ni toca zonas blindadas.
    """
    c = Path(carpeta)
    if not c.exists() or not c.is_dir():
        return {"status": "error", "detalle": f"No es una carpeta válida: {carpeta}"}
    if not _segura(c):
        return {"status": "bloqueado",
                "detalle": "Por seguridad solo agrupo dentro de Escritorio/Descargas/Documentos. "
                           "AURORA, Windows y Archivos de programa NUNCA se tocan.",
                "carpetas_permitidas": [str(s) for s in SEGURAS if s.exists()]}
    plan: dict = {}
    movimientos = []
    for item in c.iterdir():
        if not item.is_file():
            continue                        # solo archivos sueltos (no subcarpetas)
        ext = item.suffix.lower()
        grupo = _EXT2GRUPO.get(ext)
        if not grupo:
            continue                        # tipo sin grupo definido: se deja igual
        plan.setdefault(grupo, []).append(item.name)
        movimientos.append((item, c / grupo / item.name))

    if not mover:
        return {"status": "simulacro", "carpeta": str(c),
                "resumen": {g: len(v) for g, v in plan.items()},
                "total_a_mover": len(movimientos),
                "nota": "Nada movido aún. Vuelve a llamar con mover=true para ejecutar."}

    # EJECUCIÓN real + manifiesto
    hechos = []
    for origen, destino in movimientos:
        try:
            destino.parent.mkdir(exist_ok=True)
            final = destino
            n = 1
            while final.exists():           # no sobrescribe: renombra si choca
                final = destino.with_stem(f"{destino.stem} ({n})"); n += 1
            shutil.move(str(origen), str(final))
            hechos.append({"de": str(origen), "a": str(final)})
        except Exception as e:
            hechos.append({"de": str(origen), "error": str(e)[:150]})
    manifiesto = c / "_organizado_manifiesto.json"
    data = {"fecha": datetime.now().isoformat(timespec="seconds"), "movimientos": hechos}
    try:
        prev = json.loads(manifiesto.read_text(encoding="utf-8")) if manifiesto.exists() else []
        if not isinstance(prev, list):
            prev = [prev]
    except Exception:
        prev = []
    prev.append(data)
    manifiesto.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for h in hechos if "error" not in h)
    return {"status": "ok", "carpeta": str(c), "movidos": ok, "con_error": len(hechos) - ok,
            "manifiesto": str(manifiesto), "resumen": {g: len(v) for g, v in plan.items()}}


def carpetas_seguras() -> dict:
    """Carpetas donde SÍ se permite agrupar (para el panel)."""
    return {"status": "ok",
            "seguras": [str(s) for s in SEGURAS if s.exists()],
            "blindadas": [str(p) for p in PROHIBIDAS]}
