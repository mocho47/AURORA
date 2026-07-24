import requests
import json

API_URL = "http://127.0.0.1:5000"

def probar_sistema_completo():
    print("🚀 Iniciando prueba de inyección en Raíz Única (C:\\AURORA.worktrees)...")
    credenciales = {"usuario_id": "admin", "password": "admin"}
    try:
        r_auth = requests.post(f"{API_URL}/api/auth/login", json=credenciales, timeout=5)
        if r_auth.status_code == 404:
            r_auth = requests.post(f"{API_URL}/auth/login", json=credenciales, timeout=5)

        if r_auth.status_code != 200:
            print(f"❌ Error en login ({r_auth.status_code}): {r_auth.text}")
            return
        
        token = r_auth.json().get("token") if isinstance(r_auth.json(), dict) else r_auth.text.strip()
        print("✅ Token JWT obtenido con éxito.")
        
        headers = {"Authorization": f"Bearer {token}"}
        dictado_voz = {
            "texto": "Registrar cliente Carlos Mendoza, teléfono 5511223344, interesado en un servicio de Kit Retrofit por un valor de 5000 pesos, llegó por WhatsApp",
            "usuario_id": "admin",
            "chat_id": "nexus_taller_test"
        }
        
        url_msg = f"{API_URL}/api/mensaje"
        r_msg = requests.post(url_msg, json=dictado_voz, headers=headers, timeout=10)
        if r_msg.status_code == 404:
            url_msg = f"{API_URL}/mensaje"
            r_msg = requests.post(url_msg, json=dictado_voz, headers=headers, timeout=10)

        if r_msg.status_code == 200:
            print(f"🤖 Respuesta de Aurora (Groq): {r_msg.json().get('respuesta')}")
        else:
            print(f"❌ Error en mensaje ({r_msg.status_code}): {r_msg.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    probar_sistema_completo()
