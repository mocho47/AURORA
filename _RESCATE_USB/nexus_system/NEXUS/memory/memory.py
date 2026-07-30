# memory/memory.py

import datetime

def read_memory():
    """
    Simula la lectura de memoria del sistema.
    """
    return "Memoria cargada correctamente."

def write_state(state: str):
    """
    Guarda un estado en memoria.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] Estado guardado: {state}"

def log_event(event: str):
    """
    Registra un evento en consola.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] EVENTO: {event}")