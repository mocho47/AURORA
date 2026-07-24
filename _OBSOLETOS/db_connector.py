import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN DE LA CONEXIÓN A SUPABASE ---
# Obtiene la URL y la clave de las variables de entorno para mayor seguridad.
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# --- INICIALIZACIÓN DEL CLIENTE ---
# Se crea una única instancia del cliente de Supabase que se reutilizará en toda la aplicación.
# Esto es más eficiente que crear una nueva conexión cada vez.
try:
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_KEY no definidas en .env")
    supabase: Client = create_client(url, key)
    print("[OK] Supabase conectado.")
except Exception as e:
    print(f"[WARN] Supabase no disponible: {str(e).encode('ascii', errors='replace').decode()}")
    supabase: Client = None

# --- FUNCIÓN DE ACCESO GLOBAL ---
def get_supabase_client() -> Client:
    """
    Devuelve la instancia única del cliente de Supabase.
    
    Esto asegura que todos los módulos de la aplicación usen la misma conexión.
    """
    return supabase

