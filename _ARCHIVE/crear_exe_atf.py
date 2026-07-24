#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║              🏗️ CONSTRUCTOR DE EXE - ATF RETROFIT APP 🏗️                  ║
║                                                                             ║
║  Convierte el código Python en ejecutable .EXE instalable                  ║
║  Usa PyInstaller para crear aplicación de escritorio profesional          ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import os
import subprocess
import sys
from pathlib import Path

def crear_aplicacion_exe():
    """Crea ejecutable .EXE para ATF usando PyInstaller"""

    print("\n" + "="*80)
    print("🏗️  CONSTRUCTOR DE APLICACIÓN EXE - ATF RETROFIT")
    print("="*80 + "\n")

    # Verificar PyInstaller
    print("📦 Verificando PyInstaller...")
    try:
        import PyInstaller
        print(f"✅ PyInstaller encontrado: {PyInstaller.__version__}\n")
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("   Instalando: pip install pyinstaller...\n")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Crear archivo de entrada único
    print("📝 Creando aplicación ATF...\n")

    app_atf_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATF RETROFIT - Aplicación Profesional
Sistema de Marketing Digital para ATF Retrofit
"""

import sys
import os
from pathlib import Path

# Agregar ruta de módulos
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from servidor_profesional_integrado import iniciar_servidor
from CORE.publicador_atf_profesional import PublicadorATFProfesional
from CORE.buscador_web_profesional import BuscadorWebProfesional
from CORE.chatbot_wa_profesional import ChatbotWAProfesional

def main():
    """Punto de entrada de la aplicación"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    🚗 ATF RETROFIT - APLICACIÓN PROFESIONAL 🚗             ║
║                                                                            ║
║              Sistema de Marketing Digital Automático para ATF              ║
║                                                                            ║
║  • Publicador Multi-Red (TikTok, Instagram, YouTube, Facebook)           ║
║  • Buscador Web Real con Comparativa de Precios                           ║
║  • ChatBot WhatsApp Inteligente                                           ║
║  • Dashboard Analytics en Tiempo Real                                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print("\\n🔧 Inicializando ATF Retrofit App...")
    print("   Abriendo: http://localhost:8000\\n")

    # Iniciar servidor
    iniciar_servidor(puerto=8000)

if __name__ == "__main__":
    main()
'''

    # Escribir archivo ATF
    with open("app_atf.py", "w", encoding="utf-8") as f:
        f.write(app_atf_content)

    print("✅ Archivo app_atf.py creado\n")

    # Crear especificación PyInstaller
    print("⚙️  Generando especificación PyInstaller...\n")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app_atf.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('CORE', 'CORE'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'aiohttp',
        'httpx',
        'beautifulsoup4',
        'lxml',
        'sqlite3',
        'json',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ATF_Retrofit_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open("app_atf.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)

    print("✅ Especificación creada\n")

    # Compilar con PyInstaller
    print("🔨 Compilando ejecutable (esto toma ~1-2 minutos)...\n")

    try:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "app_atf.spec",
            "--onefile",
            "--windowed",
            "--icon=icono_atf.ico" if Path("icono_atf.ico").exists() else None,
            "--distpath=dist_atf",
            "--buildpath=build_atf",
            "--specpath=.",
        ], check=True)

        print("\n✅ Compilación exitosa!\n")

        # Mostrar resultado
        exe_path = Path("dist_atf/ATF_Retrofit_App.exe")

        if exe_path.exists():
            tamanio_mb = exe_path.stat().st_size / (1024 * 1024)

            print("="*80)
            print("✅ APLICACIÓN EXE CREADA EXITOSAMENTE")
            print("="*80)
            print(f"\n📦 Ejecutable: {exe_path}")
            print(f"💾 Tamaño: {tamanio_mb:.1f} MB")
            print(f"\n🚀 Para usar:")
            print(f"   1. Hacer doble clic en: {exe_path}")
            print(f"   2. Se abrirá automáticamente en http://localhost:8000")
            print(f"   3. Sistema completamente autónomo\n")

            return True
        else:
            print("❌ Error: ejecutable no encontrado")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error en compilación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    exito = crear_aplicacion_exe()
    sys.exit(0 if exito else 1)
