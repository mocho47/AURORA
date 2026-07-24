# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

target_dir = r"C:\AURORA\SUPER_MARKETING_SYSTEM"

print("⚙️ Ajustando versiones compatibles del ecosistema HTTP...")
# Forzar una versión de httpx que sea compatible con Supabase y FastAPI a la vez
subprocess.run([
    sys.executable, "-m", "pip", "install", 
    "httpx==0.25.2", "httpcore==1.0.2",
    "--target", target_dir, "--upgrade"
], check=True)
print("✅ Sincronización de paquetes completada.")
