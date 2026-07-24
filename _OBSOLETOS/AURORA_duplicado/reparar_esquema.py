# -*- coding: utf-8 -*-
"""
⚙️ REPARADOR DE NÚCLEO PYDANTIC - ECOSISTEMA FASTAPI
Ruta: C:\AURORA\reparar_esquema.py
"""
import subprocess
import sys
import shutil
from pathlib import Path

target_dir = Path(r"C:\AURORA\SUPER_MARKETING_SYSTEM")

print("🧹 Limpiando carpetas de pydantic en conflicto en la subcarpeta...")
# Eliminar carpetas rotas de la subcarpeta para evitar que Python se confunda
for folder in ["pydantic", "pydantic_core", "annotated_types"]:
    f_path = target_dir / folder
    if f_path.exists():
        shutil.rmtree(str(f_path))

print("⚙️ Inyectando suite nivelada y compatible de Pydantic v2...")
# Instalar de forma limpia la versión exacta requerida por FastAPI en el subdirectorio
subprocess.run([
    sys.executable, "-m", "pip", "install", 
    "pydantic==2.7.4", "pydantic-core==2.18.4", "annotated-types==0.7.0",
    "--target", str(target_dir), "--upgrade"
], check=True)

print("✅ Entorno de esquemas nivelado y reparado al 100%.")
