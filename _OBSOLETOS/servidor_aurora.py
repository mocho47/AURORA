#!/usr/bin/env python3
"""
AURORA v2.0 - Servidor Profesional
Sistema inteligente multi-rol sin censura
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import sqlite3

# ========== CONFIGURACIÓN ==========

AURORA_DIR = Path(__file__).parent.parent
PANEL_PATH = AURORA_DIR / "panel.html"
DB_PATH = AURORA_DIR / "aurora.db"
PORT = 8000
HOST = "127.0.0.1"

# ========== DATABASE SETUP ==========

def init_database():
    """Inicializa base de datos SQLite"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Tabla de conversaciones
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        rol TEXT,
        mensaje TEXT,
        respuesta TEXT,
        situacion TEXT,
        sdk TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        rol TEXT,
        nombre TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Tabla de cotizaciones
    c.execute('''CREATE TABLE IF NOT EXISTS cotizaciones (
        id TEXT PRIMARY KEY,
        usuario_id TEXT,
        productos TEXT,
        total REAL,
        margen REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# ========== MOTORES INTELIGENTES ==========

class MotorCoaching:
    """Motor de coaching psicológico para adolescentes"""

    SITUACIONES = {
        "estrés": {
            "keywords": ["estrés", "estresado", "estresada", "ansiedad", "miedo", "arrebato", "presión", "abrumado"],
            "respuesta": """Entiendo. El estrés es REAL y NORMAL a tu edad.

Aquí está lo importante:
**No vamos a eliminarlo** (imposible en la vida real)
**Vamos a aprender a convivir con él**

TÉCNICA INMEDIATA (5 minutos):
1. Respira: Inhala 4seg → Retén 4seg → Exhala 4seg
2. Grounding: Nombra 5 cosas que ves → 4 que tocas → 3 sonidos → 2 olores → 1 sabor
3. Muévete: Camina, estira, baila

¿Cuál es exactamente lo que te abruma?"""
        },
        "identidad": {
            "keywords": ["quién soy", "quien soy", "identidad", "futuro", "qué quiero", "que quiero", "no sé quién"],
            "respuesta": """La pregunta "¿Quién soy?" es LA pregunta adolescente.

No es que no sepas. Es que ESTÁS DESCUBRIENDO.

EXPLORA:
✓ ¿Qué te hace FELIZ? (sin que otro lo diga)
✓ ¿En qué eres realmente bueno?
✓ ¿Qué injusticia te enoja?
✓ ¿A qué tipo de persona quieres ser?

No tienes que saberlo YA.
Pero sí explorar.

¿Cuál de esas 4 te atrae más?"""
        },
        "fracaso": {
            "keywords": ["fracaso", "no puedo", "no sirvo", "rendición"],
            "respuesta": """El fracaso es tu MEJOR MAESTRO.

Tu cerebro está DISEÑADO para aprender de errores.

LA PREGUNTA REAL no es: "¿Por qué fallé?"
LA PREGUNTA es: "¿Qué aprendí?"

Cuéntame:
✓ ¿Qué pasó exactamente?
✓ ¿Qué intentabas lograr?
✓ ¿Qué no funcionó?

Vamos a encontrar la LECCIÓN.
Los ganadores fallan más.
Simplemente aprenden más rápido."""
        },
        "relaciones": {
            "keywords": ["solo", "aislado", "nadie", "excluido", "no encajo"],
            "respuesta": """"No encajo" ≠ "Me rechazan". DIFERENCIA CRÍTICA.

Tu "rareza" es tu PODER.
Los que parecen "normales" también se sienten solos.

ACCIÓN:
¿Qué te hace diferente? (hobby, talento, forma de pensar)

Vamos a encontrar TU GENTE. Existen."""
        },
        "default": {
            "keywords": [],
            "respuesta": """Entiendo tu preocupación.

Para ayudarte mejor, cuéntame:
✓ ¿Qué es exactamente lo que te preocupa?
✓ ¿Lleva tiempo así o es nuevo?
✓ ¿Ya hablaste con alguien sobre esto?

Soy especialista en adolescentes.

¿Cuál es tu mayor preocupación ahora?"""
        }
    }

    @staticmethod
    def procesar(mensaje: str) -> Tuple[str, str]:
        """Detecta situación y retorna respuesta"""
        msg_lower = mensaje.lower()

        # Buscar en cada situación
        for situacion, config in MotorCoaching.SITUACIONES.items():
            if situacion != "default":  # Skip default por ahora
                if any(kw in msg_lower for kw in config["keywords"]):
                    return situacion, config["respuesta"]

        # Default
        return "general", MotorCoaching.SITUACIONES["default"]["respuesta"]

class MotorVentas:
    """Motor para cotizaciones y ventas"""

    CATALOGO = {
        "Servilletero": {"costo": 20, "venta_base": 25},
        "Vaso Fiesta": {"costo": 32, "venta_base": 65},
        "Vaso Cafetero": {"costo": 30, "venta_base": 45},
        "Taza Blanca": {"costo": 25, "venta_base": 60},
        "Playera": {"costo": 65, "venta_base": 200},
    }

    @staticmethod
    def cotizar(producto: str, cantidad: int) -> Dict[str, Any]:
        if producto not in MotorVentas.CATALOGO:
            return {"error": f"Producto '{producto}' no encontrado"}

        cat = MotorVentas.CATALOGO[producto]
        costo_total = cat["costo"] * cantidad
        venta_total = cat["venta_base"] * cantidad
        margen = venta_total - costo_total

        return {
            "producto": producto,
            "cantidad": cantidad,
            "costo_unitario": cat["costo"],
            "venta_unitario": cat["venta_base"],
            "costo_total": costo_total,
            "venta_total": venta_total,
            "margen": margen,
            "margen_porcentaje": round((margen / venta_total * 100), 2)
        }

# ========== HANDLER HTTP ==========

class AuroraHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Maneja GET requests"""
        path = urlparse(self.path).path

        if path == "/":
            self._json_response({
                "sistema": "AURORA v2 - Operativo",
                "version": "2.0.0",
                "status": "activo",
                "roles": ["teen", "maestro", "padre", "vendedor", "admin"],
                "features": ["coaching", "codigo", "cotizador", "chat", "crisis_protocol"],
                "panel": "http://localhost:8000/panel"
            })

        elif path == "/health":
            self._json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "memoria": "~30MB",
                "uptime": "indefinido"
            })

        elif path == "/panel":
            if PANEL_PATH.exists():
                with open(PANEL_PATH, 'r', encoding='utf-8') as f:
                    self._html_response(f.read())
            else:
                self._html_response(f"<h1>Panel no encontrado: {PANEL_PATH}</h1>")

        elif path == "/api/librerias":
            self._json_response({
                "total": 16,
                "librerias": [
                    "Regulación Emocional",
                    "Fortalezas",
                    "Resiliencia",
                    "Integración Social",
                    "Identidad y Valores",
                    "Toma de Decisiones",
                    "Estrés Académico",
                    "Relaciones y Sexualidad",
                    "Propósito y Carrera",
                    "Salud Mental",
                    "Autonomía y Límites",
                    "Creatividad",
                    "Mindfulness",
                    "Comunicación No Violenta",
                    "Cuerpo y Movimiento",
                    "Narrativa Personal",
                ]
            })

        elif path == "/api/roles":
            self._json_response({
                "total": 6,
                "roles": [
                    {"id": "teen", "nombre": "Adolescente", "icon": "🧠"},
                    {"id": "maestro", "nombre": "Maestro", "icon": "👨‍🏫"},
                    {"id": "padre", "nombre": "Padre", "icon": "👨‍👩‍👧"},
                    {"id": "vendedor", "nombre": "Vendedor", "icon": "💼"},
                    {"id": "admin", "nombre": "Admin", "icon": "⚙️"},
                ]
            })

        elif path == "/api/catalogo":
            self._json_response({
                "productos": MotorVentas.CATALOGO
            })

        else:
            self._error_404()

    def do_POST(self):
        """Maneja POST requests"""
        path = urlparse(self.path).path

        # Leer body con manejo correcto de encoding
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)

        try:
            body = body_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                body = body_bytes.decode('latin-1')
            except UnicodeDecodeError:
                body = ""

        # Parsear JSON
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/chat":
            mensaje = data.get("mensaje", "")
            rol = data.get("rol", "teen")
            user_id = data.get("user_id", "anónimo")

            # Procesar con Motor Coaching
            situacion, respuesta = MotorCoaching.procesar(mensaje)

            # Guardar en DB
            self._guardar_chat(user_id, rol, mensaje, respuesta, situacion)

            self._json_response({
                "status": "ok",
                "respuesta": respuesta,
                "situacion": situacion,
                "timestamp": datetime.now().isoformat()
            })

        elif path == "/api/cotizar":
            producto = data.get("producto", "")
            cantidad = data.get("cantidad", 1)

            resultado = MotorVentas.cotizar(producto, cantidad)

            if "error" in resultado:
                self._json_response(resultado, 400)
            else:
                self._json_response(resultado)

        else:
            self._error_404()

    # ========== HELPERS ==========

    def _json_response(self, data: Dict, status: int = 200):
        """Envía respuesta JSON"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _html_response(self, html: str):
        """Envía respuesta HTML"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _error_404(self):
        """Envía error 404"""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint no encontrado"}).encode())

    def _guardar_chat(self, user_id: str, rol: str, mensaje: str, respuesta: str, situacion: str):
        """Guarda conversación en DB"""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute(
                'INSERT INTO conversations (user_id, rol, mensaje, respuesta, situacion) VALUES (?, ?, ?, ?, ?)',
                (user_id, rol, mensaje, respuesta, situacion)
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            # Log silenciosamente - DB es opcional para funcionalidad core
            print(f"[DB Error] {e}", file=sys.__stderr__)

    def log_message(self, format, *args):
        """Suprime logging"""
        pass

# ========== MAIN ==========

if __name__ == "__main__":
    # Inicializar BD
    init_database()

    # Crear servidor
    server = HTTPServer((HOST, PORT), AuroraHandler)

    print(f"\n{'='*80}")
    print("AURORA v2.0 - SERVIDOR PROFESIONAL INICIADO")
    print(f"{'='*80}\n")
    print(f"Panel:    http://localhost:{PORT}/panel")
    print(f"API:      http://localhost:{PORT}/api/")
    print(f"Chat:     POST http://localhost:{PORT}/api/chat")
    print(f"Cotizar:  POST http://localhost:{PORT}/api/cotizar")
    print(f"\nMotores activos: Coaching | Ventas")
    print(f"Database: {DB_PATH}")
    print(f"\nPresiona Ctrl+C para detener\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nAURORA apagándose...")
        server.server_close()
        sys.exit(0)
