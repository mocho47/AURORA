#!/usr/bin/env python3
"""AURORA NEXUS v3 - Service Wrapper con auto-recuperacion"""

import subprocess
import sys
import time
import logging
from pathlib import Path

log_path = Path("C:\\AURORA\\LOGS\\servicio.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AuroraService")

def _esperar_puerto_libre(port=8000, timeout=90):
    """Espera a que el puerto quede libre (evita el atasco por TIME_WAIT al reiniciar)."""
    import socket
    fin = time.time() + timeout
    while time.time() < fin:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1)
        ocupado = (s.connect_ex(("127.0.0.1", port)) == 0); s.close()
        if not ocupado:
            return True
        time.sleep(2)
    return False


def main():
    logger.info("="*80)
    logger.info("AURORA NEXUS v3 - SERVICIO INICIADO (reinicio infinito / auto-recuperacion)")
    logger.info("="*80)

    backoff = 5
    while True:   # NUNCA se rinde: servidor 24/7
        try:
            _esperar_puerto_libre(8000, 90)   # libera TIME_WAIT antes de arrancar
            inicio = time.time()
            logger.info("Iniciando AURORA...")
            # NO PIPE sin lector (se cuelga). Redirigir a log evita ese crash.
            _logout = open("C:\\AURORA\\LOGS\\aurora_stdout.log", "a", encoding="utf-8", errors="replace")
            proceso = subprocess.Popen(
                [sys.executable, "C:\\AURORA\\aurora_unified_main.py"],
                stdout=_logout, stderr=subprocess.STDOUT, cwd="C:\\AURORA")
            logger.info(f"[OK] AURORA iniciado (PID: {proceso.pid}) en http://127.0.0.1:8000/")

            proceso.wait()
            dur = time.time() - inicio
            logger.warning(f"[ALERTA] AURORA se detuvo tras {int(dur)}s")
            if dur > 90:
                backoff = 5            # corrio sano -> resetea el backoff
            else:
                backoff = min(backoff * 2, 30)   # fallo rapido -> espera mas (cap 30s)
            logger.info(f"[REINTENTO] esperando {backoff}s (reinicio infinito)...")
            time.sleep(backoff)

        except KeyboardInterrupt:
            logger.info("[OK] Servicio detenido manualmente")
            break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
            time.sleep(min(backoff * 2, 30))

if __name__ == "__main__":
    main()
