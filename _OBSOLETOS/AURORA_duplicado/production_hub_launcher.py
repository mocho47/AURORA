# -*- coding: utf-8 -*-
"""
� AURORA PRODUCTION HUB LAUNCHER
Arranca el sistema AURORA completo en modo producción.
"""
import sys
import io
import subprocess
from pathlib import Path

# Forzar UTF-8 en consola Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

RAIZ = Path(__file__).parent

def main():
    print("=" * 60)
    print("   AURORA PRODUCTION HUB - Iniciando sistema...")
    print("=" * 60)

    script = RAIZ / "run_aurora.py"
    if not script.exists():
        print(f"[ERROR] No se encontró run_aurora.py en {RAIZ}")
        sys.exit(1)

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(RAIZ),
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n[INFO] Aurora detenido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fallo al arrancar Aurora: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
