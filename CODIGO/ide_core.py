# -*- coding: utf-8 -*-
"""AURORA · IDE DEL SISTEMA (cartucho).

Editor de código real dentro del panel de AURORA. Permite ver y editar el código
de la propia AURORA (y del sistema) con red de seguridad:

  1. Árbol de archivos (oculta lo sensible: .env, secretos, meta/, .git, __pycache__).
  2. Abrir/guardar archivos.
  3. RESPALDO automático antes de cada sobrescritura (nada se pierde).
  4. Chequeo de compilación en .py: si tiene error de sintaxis, NO guarda y avisa.
  5. Blindaje de escritura: solo en AURORA + Desktop/Downloads/Documents.

Los endpoints que exponen esto exigen PIN de dueño (ver aurora_server).
"""
from __future__ import annotations
import ast
import hashlib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent           # C:\AURORA(.worktrees)
BACKUPS = ROOT / ".ide_backups"

# Escritura permitida (mismo criterio que pc_access): AURORA + carpetas del usuario.
RUTAS_ESCRITURA = [ROOT, Path.home() / "Desktop", Path.home() / "Downloads", Path.home() / "Documents"]

# Qué se oculta en el árbol y NO se puede abrir/editar (protección de secretos).
OCULTOS_NOMBRE = {".git", "__pycache__", ".ide_backups", "node_modules", ".venv", "venv", "meta"}
OCULTOS_ARCHIVO = {".env", ".env.local"}
BLOQUEADOS_SUFIJO = {".key", ".pem", ".pfx"}
MAX_BYTES = 2_000_000  # 2 MB — no abrir binarios/enormes en el editor

# Extensiones que se consideran texto editable.
TEXTO_EXT = {
    ".py", ".txt", ".md", ".json", ".js", ".ts", ".html", ".htm", ".css", ".bat",
    ".ps1", ".sh", ".yml", ".yaml", ".ini", ".cfg", ".toml", ".xml", ".csv", ".log",
    ".sql", ".env.example", ".gitignore",
}


def _permitida_escritura(path: Path) -> bool:
    pr = path.resolve()
    return any(str(pr).startswith(str(base.resolve())) for base in RUTAS_ESCRITURA)


def _es_oculto(item: Path) -> bool:
    n = item.name.lower()
    if n in OCULTOS_NOMBRE or n in OCULTOS_ARCHIVO:
        return True
    if item.suffix.lower() in BLOQUEADOS_SUFIJO:
        return True
    return False


def _es_texto(path: Path) -> bool:
    if path.suffix.lower() in TEXTO_EXT:
        return True
    return path.suffix == "" and path.name.lower() in {"dockerfile", "makefile", "procfile"}


def arbol(ruta: str | None = None) -> dict:
    """Lista un directorio (un nivel). Sin ruta => raíz de AURORA."""
    base = Path(ruta).resolve() if ruta else ROOT
    if not base.exists():
        return {"status": "NO_EXISTE", "ruta": str(base)}
    if not base.is_dir():
        return {"status": "NO_DIR", "ruta": str(base)}
    items = []
    try:
        for it in sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if _es_oculto(it):
                continue
            items.append({
                "nombre": it.name,
                "ruta": str(it.resolve()),
                "tipo": "dir" if it.is_dir() else "archivo",
                "editable": bool(it.is_file() and _es_texto(it)),
                "kb": round(it.stat().st_size / 1024, 1) if it.is_file() else None,
            })
    except PermissionError:
        return {"status": "SIN_PERMISO", "ruta": str(base)}
    padre = str(base.parent.resolve()) if base != base.parent else None
    return {"status": "ok", "ruta": str(base), "padre": padre,
            "raiz_aurora": str(ROOT), "items": items, "total": len(items)}


def leer(ruta: str) -> dict:
    path = Path(ruta).resolve()
    if not path.exists() or not path.is_file():
        return {"status": "NO_EXISTE", "ruta": str(path)}
    if _es_oculto(path):
        return {"status": "PROTEGIDO", "ruta": str(path),
                "razon": "Archivo protegido (secreto/oculto): no se abre en el editor."}
    if path.stat().st_size > MAX_BYTES:
        return {"status": "MUY_GRANDE", "ruta": str(path), "kb": round(path.stat().st_size / 1024, 1)}
    try:
        contenido = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}
    return {"status": "ok", "ruta": str(path), "nombre": path.name,
            "contenido": contenido, "lineas": contenido.count("\n") + 1,
            "editable": _permitida_escritura(path), "lenguaje": path.suffix.lower().lstrip(".")}


def _respaldar(path: Path) -> str | None:
    """Copia el archivo actual a .ide_backups con marca de tiempo. Devuelve la ruta del respaldo."""
    if not path.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = hashlib.md5(str(path.resolve()).encode()).hexdigest()[:8]
    BACKUPS.mkdir(parents=True, exist_ok=True)
    dest = BACKUPS / f"{path.name}.{tag}.{ts}.bak"
    dest.write_bytes(path.read_bytes())
    return str(dest)


def guardar(ruta: str, contenido: str) -> dict:
    """Guarda con red de seguridad: respaldo previo + chequeo de sintaxis en .py."""
    path = Path(ruta).resolve()
    if _es_oculto(path):
        return {"status": "PROTEGIDO", "razon": "Archivo protegido: no editable."}
    if not _permitida_escritura(path):
        return {"status": "DENEGADO", "ruta": str(path),
                "razon": "Fuera de zonas de escritura permitidas (AURORA, Desktop, Downloads, Documents)."}
    # Chequeo de compilación para Python — NO guarda si hay error de sintaxis.
    if path.suffix.lower() == ".py":
        try:
            ast.parse(contenido)
        except SyntaxError as e:
            return {"status": "ERROR_SINTAXIS", "ruta": str(path),
                    "linea": e.lineno, "columna": e.offset,
                    "detalle": f"Error de sintaxis en línea {e.lineno}: {e.msg}. NO se guardó (tu código sigue intacto)."}
    try:
        respaldo = _respaldar(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}
    return {"status": "ok", "ruta": str(path), "bytes": len(contenido.encode("utf-8")),
            "respaldo": respaldo, "nuevo": respaldo is None,
            "msg": ("Guardado (archivo nuevo)." if respaldo is None else "Guardado. Respaldo creado por si necesitas revertir.")}


def respaldos(ruta: str) -> dict:
    """Lista los respaldos disponibles de un archivo (más recientes primero)."""
    path = Path(ruta).resolve()
    tag = hashlib.md5(str(path).encode()).hexdigest()[:8]
    if not BACKUPS.exists():
        return {"status": "ok", "respaldos": []}
    encontrados = sorted(
        [p for p in BACKUPS.glob(f"{path.name}.{tag}.*.bak")],
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    return {"status": "ok", "ruta": str(path),
            "respaldos": [{"archivo": str(p), "cuando": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                           "kb": round(p.stat().st_size / 1024, 1)} for p in encontrados]}


def restaurar(respaldo: str, destino: str) -> dict:
    """Restaura un respaldo sobre el archivo destino (haciendo antes respaldo del estado actual)."""
    src = Path(respaldo).resolve()
    dst = Path(destino).resolve()
    if not src.exists() or src.parent != BACKUPS.resolve():
        return {"status": "ERROR", "razon": "Respaldo inválido."}
    if not _permitida_escritura(dst):
        return {"status": "DENEGADO", "razon": "Destino fuera de zonas permitidas."}
    _respaldar(dst)
    dst.write_bytes(src.read_bytes())
    return {"status": "ok", "ruta": str(dst), "msg": "Restaurado desde el respaldo."}


if __name__ == "__main__":
    import json
    print(json.dumps(arbol(), ensure_ascii=False, indent=2)[:1500])
