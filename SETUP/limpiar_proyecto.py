"""
AURORA — LIMPIEZA Y REORGANIZACION FINAL
Mueve obsoletos a _OBSOLETOS/. Deja solo lo esencial para funcionar.
"""
import os, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DESTINO = ROOT / "_OBSOLETOS"
DESTINO.mkdir(exist_ok=True)

movidos = []
errores = []

def mover(src: Path, razon: str):
    dst = DESTINO / src.name
    # Si ya existe en destino, agregar sufijo
    if dst.exists():
        dst = DESTINO / f"{src.stem}_dup_{src.suffix}"
    try:
        shutil.move(str(src), str(dst))
        movidos.append(f"{src.relative_to(ROOT)}  →  _OBSOLETOS/  [{razon}]")
        print(f"MOVIDO  {src.name}  [{razon}]")
    except Exception as e:
        errores.append(f"ERROR {src.name}: {e}")
        print(f"ERROR   {src.name}: {e}")

print("=" * 65)
print("AURORA — LIMPIEZA FINAL")
print("=" * 65)
print()

# ── 1. ARCHIVOS BASURA EN RAÍZ (nombres inválidos / fragmentos) ──
basura_raiz = [
    "bool",
    "Dict[str",
    "AUTO_POST_PAUSADO",
    "0.24.0",
    "_a3.txt",
    "_audit.txt",
    "_invest_atf.txt",
    "__init__.py",   # raiz - no es un paquete real
]
print("── 1. Basura en raíz ──────────────────────────────────────────")
for nombre in basura_raiz:
    f = ROOT / nombre
    if f.exists():
        mover(f, "basura/fragmento")

# @echo of... (nombre con @ inválido)
for f in ROOT.glob("@*"):
    if f.is_file():
        mover(f, "nombre inválido con @")

# ── 2. SCRIPTS .BAT y .PS1 OBSOLETOS EN RAÍZ ────────────────────
# Solo se conserva: run_aurora.py
# Los .bat/.ps1 son todos scripts de arranque duplicados o de fix
print()
print("── 2. Scripts .bat/.ps1 obsoletos ────────────────────────────")
bat_conservar = set()  # ninguno es necesario — run_aurora.py los reemplaza
for f in ROOT.glob("*.bat"):
    mover(f, "script arranque obsoleto")
for f in ROOT.glob("*.ps1"):
    mover(f, "script arranque obsoleto")

# ── 3. SCRIPTS .PY EN RAÍZ OBSOLETOS ────────────────────────────
# CONSERVAR: run_aurora.py, config.py, requirements.txt, .env.example
# MOVER: aplicar_*, fix_*, reparar_*, validar_*, main_unified, aurora_unified_main,
#        production_hub_launcher, generar_token_jwt
print()
print("── 3. Scripts .py raíz obsoletos ──────────────────────────────")
py_raiz_obsoletos = [
    "aplicar_despliegue_total.py",
    "aplicar_fix.py",
    "aplicar_fix_maestro.py",
    "aplicar_fix_whatsapp_v4.py",
    "aurora_unified_main.py",
    "generar_token_jwt.py",
    "main_unified.py",
    "production_hub_launcher.py",
    "reparar_esquema.py",
    "reparar_httpx.py",
    "validar_aurora.py",
]
for nombre in py_raiz_obsoletos:
    f = ROOT / nombre
    if f.exists():
        mover(f, "script fix/arranque obsoleto")

# ── 4. CORE: SERVIDORES DUPLICADOS ──────────────────────────────
# CONSERVAR: aurora_server.py (el principal con /chat)
# MOVER: servidor_aurora.py, servidor_aurora_completo.py, servidor_simple.py
print()
print("── 4. CORE: servidores duplicados ─────────────────────────────")
core_obsoletos = [
    "CORE/servidor_aurora.py",
    "CORE/servidor_aurora_completo.py",
    "CORE/servidor_simple.py",
]
for ruta_rel in core_obsoletos:
    f = ROOT / ruta_rel
    if f.exists():
        mover(f, "servidor duplicado en CORE")

# ── 5. CEREBRO: VERSIONES ANTIGUAS DEL CEREBRO ──────────────────
# CONSERVAR: consciencia.py, bus_neuronal.py, registrador_bus.py,
#            auto_conocimiento.py, pc_access.py, auto_reparacion.py, aurora_sync.py
# MOVER: aurora_cerebro.py (v1), aurora_cerebro_v4.py (versión anterior),
#        aurora_server.py (duplicado del server), orquestador_aurora.py (roto)
print()
print("── 5. CEREBRO: versiones antiguas ─────────────────────────────")
cerebro_obsoletos = [
    "CEREBRO/aurora_cerebro.py",        # v1 - reemplazado por consciencia.py
    "CEREBRO/aurora_cerebro_v4.py",     # v4 - reemplazado por consciencia.py
    "CEREBRO/aurora_server.py",         # duplicado del server en CORE
    "CEREBRO/orquestador_aurora.py",    # imports rotos a SUPER_MARKETING_SYSTEM
]
for ruta_rel in cerebro_obsoletos:
    f = ROOT / ruta_rel
    if f.exists():
        mover(f, "version antigua / duplicado CEREBRO")

# CONSERVAR aurora_cerebro_simple.py — es el cerebro usado por WhatsApp sync
# No se mueve.

# ── 6. CARPETAS VACIAS O SIN USO REAL ───────────────────────────
print()
print("── 6. Archivos sueltos sin uso real ───────────────────────────")
sueltos = [
    "AURORA/auditar_aurora_B.bat",  # dentro de carpeta AURORA/ (es copia de raíz)
]
for ruta_rel in sueltos:
    f = ROOT / ruta_rel
    if f.exists():
        mover(f, "archivo suelto sin uso")

# ── 7. .db-wal y .db-shm VACÍOS ─────────────────────────────────
print()
print("── 7. DB auxiliares vacíos ─────────────────────────────────────")
for f in ROOT.rglob("*.db-wal"):
    if f.stat().st_size == 0 and '_ARCHIVE' not in str(f) and '_OBSOLETOS' not in str(f):
        mover(f, "db-wal vacío")
for f in ROOT.rglob("*.db-shm"):
    if '_ARCHIVE' not in str(f) and '_OBSOLETOS' not in str(f):
        if f.exists():
            mover(f, "db-shm auxiliar")

# ── RESUMEN ──────────────────────────────────────────────────────
print()
print("=" * 65)
print(f"MOVIDOS:  {len(movidos)}")
print(f"ERRORES:  {len(errores)}")
print()
print("Archivos movidos a _OBSOLETOS/:")
for m in movidos:
    print(f"  {m}")
if errores:
    print()
    print("Errores:")
    for e in errores:
        print(f"  {e}")

print()
print("ARCHIVOS RAÍZ QUE QUEDAN (esenciales):")
for f in sorted(ROOT.iterdir()):
    if f.is_file() and '_OBSOLETOS' not in str(f):
        print(f"  {f.name}")
