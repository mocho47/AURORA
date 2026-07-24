import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from servidor_profesional_integrado import iniciar_servidor

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    ATF RETROFIT - APLICACION PROFESIONAL                   ║
║                                                                            ║
║              Sistema de Marketing Digital para ATF Retrofit                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    print("\nIniciando ATF...")
    iniciar_servidor(puerto=8000)

if __name__ == "__main__":
    main()
