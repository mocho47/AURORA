# -*- coding: utf-8 -*-
"""
🔑 GENERADOR DE TOKENS JWT - Para testing de API
"""
import jwt
from datetime import datetime, timedelta
from pathlib import Path
import sys

RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ))

from config import settings

def generar_token(usuario_id: str = "admin", duracion_horas: int = 24) -> str:
    """Genera JWT token"""
    expire = datetime.utcnow() + timedelta(hours=duracion_horas)
    payload = {
        "sub": usuario_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🔑 GENERADOR DE TOKENS JWT - AURORA")
    print("="*60)
    
    usuario = input("\n  Usuario (default: admin): ").strip() or "admin"
    
    token = generar_token(usuario)
    
    print(f"\n  ✅ Token generado para: {usuario}")
    print(f"\n  Token:")
    print(f"  {token}")
    print(f"\n  Uso en headers:")
    print(f"  Authorization: Bearer {token}")
    print("\n" + "="*60 + "\n")
