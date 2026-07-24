import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from servidor_profesional_integrado import iniciar_servidor

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    MILENS - APLICACION PROFESIONAL                         ║
║                                                                            ║
║              Sistema de Marketing Digital para MILENS                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    print("\nIniciando MILENS...")
    iniciar_servidor(puerto=8001)

if __name__ == "__main__":
    main()
