#!/usr/bin/env python3
"""
ATF Retrofit - Excelencia Profesional
Admin completo para gestión inteligente de marketing
- Publicación automática 2-3 videos/día
- Editor de videos integrado
- Sugerencias inteligentes de IA
- Monitor en vivo de todas las plataformas
- Dashboard profesional
"""

import subprocess
import sys
import os
import time

def main():
    """Launch ATF admin server with all features"""

    # Verificar que existan los módulos necesarios
    required_files = [
        "C:\\AURORA\\publicador_inteligente_atf.py",
        "C:\\AURORA\\servidor_admin_atf.py"
    ]

    for f in required_files:
        if not os.path.exists(f):
            print(f"❌ Error: {f} no encontrado")
            sys.exit(1)

    print("=" * 60)
    print("🚀 ATF RETROFIT - EXCELENCIA PROFESIONAL")
    print("=" * 60)
    print()
    print("INICIANDO SISTEMA INTELIGENTE:")
    print("  ✓ Publicador automático (2-3 posts/día)")
    print("  ✓ Editor de videos integrado")
    print("  ✓ Intelligence engine con sugerencias IA")
    print("  ✓ Monitor en vivo de todas las plataformas")
    print("  ✓ Dashboard admin profesional")
    print()
    print("Abriendo en: http://localhost:8000")
    print()

    # Cambiar a directorio AURORA
    os.chdir("C:\\AURORA")

    # Importar y ejecutar
    try:
        from servidor_admin_atf import main as start_server
        start_server()
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("\nIntentando instalar dependencias...")
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp", "beautifulsoup4"],
                      capture_output=True)
        print("Reintentando...")
        time.sleep(2)
        from servidor_admin_atf import main as start_server
        start_server()

if __name__ == "__main__":
    main()
