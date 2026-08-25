# -*- coding: utf-8 -*-
"""AURORA · RESPALDO REAL — reemplazo de SETUP/backup_aurora.py

╔══════════════════════════════════════════════════════════════════════════╗
║ POR QUÉ ESTE ARCHIVO                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

El respaldo anterior llevaba fallando en silencio desde el 23-jul-2026. La
tarea programada corría cada noche a las 3:00, fallaba con ERROR_FILE_NOT_FOUND,
y en el Programador de Tareas se veía "Ready" — parecía sano. Cero copias reales
en un mes.

Tres cosas estaban mal, no una:

1. `BASE = Path(r"C:\\AURORA")` — esa carpeta ya no existe. El proyecto vive en
   `C:\\AURORA.worktrees`.
2. La lista de bases era `["aurora.db", "chat_memory.db", "oracle.db"]`. De
   esas, **dos no existen** y faltaban **13 más** que sí existen — incluida
   `MEMORIA/aurora_memoria.db`, que es la memoria y el aprendizaje de AURORA.
3. Respaldaba `CONFIG/materiales.json`, que tampoco existe.

CORRECCIÓN DE RAÍZ, no parche:
El error de fondo no fue "la ruta estaba mal". Fue que **el respaldo tenía una
lista escrita a mano**, y una lista escrita a mano se desactualiza sola — como
pasó. Este respaldo **descubre** qué hay que respaldar en vez de que se lo
digan: busca las bases de datos y las configuraciones donde estén. Si mañana
nace una base nueva, entra sola. No puede volver a quedarse viejo.

Y no se da por bueno solo porque no truene: al terminar **verifica** cada copia
(integridad SQLite real) y si algo salió mal, **falla ruidoso** con código de
salida distinto de cero, para que la tarea programada lo reporte como error de
verdad en vez de decir "Ready".

DECISIÓN PENDIENTE DE ANUAR: ninguna. Este archivo se puede aplicar tal cual.
Después de aplicarlo hay que corregir la ruta de la tarea programada de Windows,
que también apunta a C:\\AURORA (el comando exacto está al final de este archivo).
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# La raíz se deduce de dónde vive este archivo. Así el respaldo sigue al
# proyecto si se vuelve a mover, en vez de quedarse apuntando a una ruta
# muerta como pasó con C:\AURORA.
BASE = Path(__file__).resolve().parent.parent
DEST = BASE / "BACKUPS"
CONSERVAR = 14

# Carpetas que NO se recorren buscando bases: son copias históricas, respaldos
# viejos y librerías. Respaldar un respaldo no aporta nada y multiplica el peso.
IGNORAR = {"_OBSOLETOS", "_ARCHIVE", "_RESCATE_USB", "BACKUPS", ".git",
           "__pycache__", ".venv", "venv", "node_modules", "MODELOS",
           ".pytest_cache"}


def _relevante(p: Path) -> bool:
    """¿Este archivo está en una carpeta que sí queremos respaldar?"""
    return not any(parte in IGNORAR or parte.startswith("_BACKUP_DB_")
                   for parte in p.relative_to(BASE).parts)


def _descubrir_bases() -> list[Path]:
    """Todas las bases SQLite vivas del proyecto, estén donde estén.

    Descubrir en vez de listar es el punto de este archivo: la lista escrita a
    mano del respaldo anterior mencionaba 3 bases (2 inexistentes) cuando hay 14.
    """
    return sorted(p for p in BASE.rglob("*.db") if _relevante(p))


def _descubrir_configs() -> list[Path]:
    """Configuración y credenciales: todo CONFIG/*.json más el .env."""
    encontrados = sorted(p for p in (BASE / "CONFIG").glob("*.json")
                         if not p.name.startswith("catalogo_maestro.bak-")
                         and not p.name.startswith("catalogo_servicios.bak-")
                         and not p.name.startswith("precios_base.bak-"))
    env = BASE / ".env"
    if env.exists():
        encontrados.append(env)
    return encontrados


def _copiar_base(src: Path, destino: Path) -> None:
    """Copia consistente de una base SQLite, segura aunque esté en uso.

    Usa la API de backup de SQLite (no shutil.copy), que es la única forma
    correcta de copiar una base abierta: una copia cruda de un archivo en modo
    WAL puede quedar corrupta o a medias.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Conexión normal, NO `file:...?mode=ro`: en Windows las rutas traen
    # backslashes y letra de unidad, que como URI fallan o se malinterpretan.
    # Además, abrir en solo-lectura una base en modo WAL puede fallar si
    # necesita recuperar el journal. La API de backup no escribe en el origen.
    origen = sqlite3.connect(str(src))
    copia = sqlite3.connect(str(destino))
    try:
        with copia:
            origen.backup(copia)
    finally:
        origen.close()
        copia.close()


def _verificar_base(ruta: Path) -> str:
    """Abre la copia recién hecha y confirma que SQLite la da por íntegra.

    Sin esto, un respaldo corrupto se ve idéntico a uno bueno hasta el día que
    lo necesitas — que es el peor día para descubrirlo.
    """
    con = sqlite3.connect(str(ruta))
    try:
        resultado = con.execute("PRAGMA integrity_check").fetchone()
        return (resultado[0] if resultado else "sin respuesta")
    finally:
        con.close()


def respaldar() -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = DEST / f"backup_{ts}"
    carpeta.mkdir(parents=True, exist_ok=True)

    copiados: list[str] = []
    verificados: list[str] = []
    errores: list[str] = []

    for src in _descubrir_bases():
        rel = src.relative_to(BASE)
        destino = carpeta / rel
        try:
            _copiar_base(src, destino)
            copiados.append(str(rel))
            estado = _verificar_base(destino)
            if estado == "ok":
                verificados.append(str(rel))
            else:
                errores.append(f"{rel}: la copia NO pasó integrity_check ({estado})")
        except Exception as e:
            errores.append(f"{rel}: {e}")

    for src in _descubrir_configs():
        rel = src.relative_to(BASE)
        destino = carpeta / rel
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, destino)
            copiados.append(str(rel))
        except Exception as e:
            errores.append(f"{rel}: {e}")

    # El modelo de voz no puede ir a git (pesa demasiado) pero SÍ tiene que
    # estar aquí: si se restaura AURORA en otra PC sin él, la voz queda muda
    # sin avisar. Se copia solo si existe, y no es error que falte.
    modelo_voz = BASE / "VOZ" / "modelo-vosk-es"
    if modelo_voz.is_dir():
        try:
            shutil.copytree(modelo_voz, carpeta / "VOZ" / "modelo-vosk-es")
            copiados.append("VOZ/modelo-vosk-es (modelo de voz)")
        except Exception as e:
            errores.append(f"VOZ/modelo-vosk-es: {e}")

    # Conservar solo los últimos N respaldos.
    previos = sorted(p for p in DEST.glob("backup_*") if p.is_dir())
    borrados = []
    for viejo in previos[:-CONSERVAR]:
        shutil.rmtree(viejo, ignore_errors=True)
        borrados.append(viejo.name)

    return {"carpeta": str(carpeta),
            "copiados": copiados,
            "verificados": verificados,
            "errores": errores,
            "borrados_antiguos": borrados,
            "total_backups": len([p for p in DEST.glob("backup_*") if p.is_dir()])}


if __name__ == "__main__":
    r = respaldar()
    print(f"[RESPALDO {datetime.now():%Y-%m-%d %H:%M}] "
          f"{len(r['copiados'])} elementos -> {r['carpeta']}")
    print(f"Bases verificadas íntegras: {len(r['verificados'])}")

    if r["errores"]:
        print("\nERRORES (el respaldo NO está completo):")
        for e in r["errores"]:
            print(f"  - {e}")
        # Salir con error de verdad, para que la tarea programada de Windows
        # lo marque como fallo en vez de mostrarse "Ready" como hasta ahora.
        sys.exit(1)

    print(f"Respaldos conservados: {r['total_backups']}")
    print("Respaldo completo y verificado.")


# ─────────────────────────────────────────────────────────────────────────────
# DESPUÉS DE APLICAR ESTE ARCHIVO, corregir la tarea programada de Windows,
# que hoy todavía apunta a la ruta muerta C:\AURORA. En PowerShell como
# administrador:
#
#   $a = New-ScheduledTaskAction `
#          -Execute "C:\Program Files\Python312\pythonw.exe" `
#          -Argument "C:\AURORA.worktrees\SETUP\backup_aurora.py"
#   Set-ScheduledTask -TaskName "AURORA-Backup-Diario" -Action $a
#
# Y comprobar que de verdad corrió (no que "diga Ready"):
#
#   Get-ScheduledTaskInfo -TaskName "AURORA-Backup-Diario" |
#       Select LastRunTime, LastTaskResult      # LastTaskResult debe ser 0
# ─────────────────────────────────────────────────────────────────────────────
