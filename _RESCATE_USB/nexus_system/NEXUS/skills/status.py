import os
import sys
from datetime import datetime

def run():
    print("=== NEXUS STATUS ===")
    print(f"Ruta actual      : {os.getcwd()}")
    print(f"Archivo ejecutado: {__file__}")
    print(f"Python versión   : {sys.version.split()[0]}")
    print(f"Fecha y hora     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("====================")

if __name__ == "__main__":
    run()
