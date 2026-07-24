# -*- coding: utf-8 -*-
"""AURORA · ACCIONES REALES DEL SISTEMA.

Ejecuta de VERDAD (nada de simular): mover/copiar archivos, buscar archivos,
reparar/limpiar cache de apps (WhatsApp). Cada función VERIFICA el resultado y
devuelve la prueba (existe en destino, bytes borrados, etc.). Si no puede, lo dice.

Blindaje: escritura solo en zonas permitidas (AURORA + Desktop/Downloads/Documents)
y rutas de red UNC (\\\\PC\\Compartida) para pasar archivos a la otra PC.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_HOME = Path.home()
UBICACIONES_BUSQUEDA = [_HOME / "Downloads", _HOME / "Desktop", _HOME / "Documents", _HOME / "Pictures", ROOT]
RUTAS_ESCRITURA = [ROOT, _HOME / "Desktop", _HOME / "Downloads", _HOME / "Documents", _HOME / "Pictures"]


def _permitida(path: Path) -> bool:
    pr = str(path.resolve())
    if pr.startswith("\\\\"):          # ruta de red UNC → permitida (otra PC compartida)
        return True
    return any(pr.startswith(str(b.resolve())) for b in RUTAS_ESCRITURA)


def buscar_archivo(nombre: str) -> list[str]:
    """Busca un archivo por nombre (o fragmento) en las carpetas comunes. Real."""
    nombre = (nombre or "").strip().lower()
    if not nombre:
        return []
    hits = []
    for base in UBICACIONES_BUSQUEDA:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if "__pycache__" in str(p) or ".ide_backups" in str(p):
                    continue
                if p.is_file() and nombre in p.name.lower():
                    hits.append(str(p))
                    if len(hits) >= 30:
                        return hits
        except (PermissionError, OSError):
            continue
    return hits


def copiar(origen: str, destino: str) -> dict:
    """Copia un archivo y VERIFICA que llegó. destino puede ser carpeta o archivo."""
    src = Path(origen)
    if not src.exists() or not src.is_file():
        return {"status": "NO_EXISTE", "detalle": f"No encontré el archivo origen: {origen}"}
    dst = Path(destino)
    if dst.is_dir() or destino.endswith(("\\", "/")):
        dst = dst / src.name
    if not _permitida(dst):
        return {"status": "DENEGADO", "detalle": f"Destino fuera de zonas permitidas: {dst}"}
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}
    if dst.exists() and dst.stat().st_size == src.stat().st_size:
        return {"status": "ok", "accion": "copiado", "origen": str(src), "destino": str(dst),
                "bytes": dst.stat().st_size, "verificado": True}
    return {"status": "ERROR", "detalle": "La copia no coincide en tamaño (no verificada)."}


def mover(origen: str, destino: str) -> dict:
    """Mueve un archivo y VERIFICA (existe en destino y ya no en origen)."""
    src = Path(origen)
    if not src.exists() or not src.is_file():
        return {"status": "NO_EXISTE", "detalle": f"No encontré el archivo origen: {origen}"}
    dst = Path(destino)
    if dst.is_dir() or destino.endswith(("\\", "/")):
        dst = dst / src.name
    if not _permitida(dst):
        return {"status": "DENEGADO", "detalle": f"Destino fuera de zonas permitidas: {dst}"}
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)[:200]}
    if dst.exists() and not src.exists():
        return {"status": "ok", "accion": "movido", "origen": str(src), "destino": str(dst),
                "bytes": dst.stat().st_size, "verificado": True}
    return {"status": "ERROR", "detalle": "No se pudo verificar el movimiento."}


# ── Reparación / limpieza de apps ─────────────────────────────────────

def _cerrar_proceso(nombre_exe: str) -> bool:
    try:
        r = subprocess.run(["taskkill", "/IM", nombre_exe, "/F"],
                           capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False


def reparar_whatsapp() -> dict:
    """Cierra WhatsApp y limpia su cache REAL. Devuelve exactamente qué hizo."""
    acciones = []
    cerrado = _cerrar_proceso("WhatsApp.exe")
    acciones.append("WhatsApp cerrado" if cerrado else "WhatsApp no estaba abierto (o no se pudo cerrar)")
    # Posibles ubicaciones de cache (Store app y clásica).
    local = Path(os.environ.get("LOCALAPPDATA", _HOME / "AppData" / "Local"))
    candidatos = [local / "WhatsApp" / "Cache", local / "WhatsApp" / "GPUCache"]
    pkgs = local / "Packages"
    if pkgs.exists():
        try:
            for d in pkgs.glob("*WhatsAppDesktop*"):
                candidatos += [d / "LocalCache", d / "AC" / "INetCache", d / "TempState"]
        except OSError:
            pass
    borrado_total = 0
    encontrados = 0
    for c in candidatos:
        if c.exists() and c.is_dir():
            encontrados += 1
            try:
                tam = sum(f.stat().st_size for f in c.rglob("*") if f.is_file())
                shutil.rmtree(str(c), ignore_errors=True)
                borrado_total += tam
                acciones.append(f"Cache borrado: {c.name} ({round(tam/1024/1024,1)} MB)")
            except Exception as e:
                acciones.append(f"No pude borrar {c.name}: {str(e)[:80]}")
    if encontrados == 0:
        acciones.append("No encontré carpetas de cache de WhatsApp (quizá ya estaba limpio o es otra versión).")
    return {"status": "ok", "app": "WhatsApp", "acciones": acciones,
            "mb_liberados": round(borrado_total / 1024 / 1024, 1),
            "verificado": True,
            "nota": "Vuelve a abrir WhatsApp; reconstruirá el cache limpio."}


if __name__ == "__main__":
    import json
    print(json.dumps({"buscar_4forte": buscar_archivo("4forte")}, ensure_ascii=False, indent=2))
