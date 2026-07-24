# -*- coding: utf-8 -*-
"""Backup REAL de AURORA: bases de datos (copia consistente SQLite) + configs + .env.
Guarda en C:\\AURORA\\BACKUPS\\backup_<fecha>\\ y conserva los últimos 14.
Se puede correr a mano o por tarea programada diaria."""
import sqlite3, shutil, sys
from pathlib import Path
from datetime import datetime

BASE = Path(r"C:\AURORA")
DEST = BASE / "BACKUPS"
CONSERVAR = 14

DBS = ["aurora.db", "chat_memory.db", "oracle.db"]
ARCHIVOS = [".env", r"CONFIG\precios_base.json", r"CONFIG\fichas_tecnicas.json",
            r"CONFIG\identidad.json", r"CONFIG\materiales.json"]


def respaldar() -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = DEST / f"backup_{ts}"
    (carpeta / "CONFIG").mkdir(parents=True, exist_ok=True)
    copiados, errores = [], []

    # Bases SQLite: copia consistente con la API de backup (segura aunque estén en uso)
    for db in DBS:
        src = BASE / db
        if not src.exists():
            continue
        try:
            o = sqlite3.connect(str(src)); d = sqlite3.connect(str(carpeta / db))
            with d:
                o.backup(d)
            o.close(); d.close()
            copiados.append(db)
        except Exception as e:
            errores.append(f"{db}: {e}")

    # Archivos sueltos (configs, .env)
    for rel in ARCHIVOS:
        src = BASE / rel
        if src.exists():
            try:
                shutil.copy2(src, carpeta / rel)
                copiados.append(rel)
            except Exception as e:
                errores.append(f"{rel}: {e}")

    # Conservar solo los últimos N backups
    backups = sorted([p for p in DEST.glob("backup_*") if p.is_dir()])
    borrados = []
    for viejo in backups[:-CONSERVAR]:
        shutil.rmtree(viejo, ignore_errors=True)
        borrados.append(viejo.name)

    return {"carpeta": str(carpeta), "copiados": copiados, "errores": errores,
            "borrados_antiguos": borrados, "total_backups": len(list(DEST.glob('backup_*')))}


if __name__ == "__main__":
    r = respaldar()
    print(f"[BACKUP {datetime.now():%Y-%m-%d %H:%M}] {len(r['copiados'])} items -> {r['carpeta']}")
    if r["errores"]:
        print("ERRORES:", r["errores"]); sys.exit(1)
    print("Copiados:", ", ".join(r["copiados"]))
    print("Backups conservados:", r["total_backups"])
