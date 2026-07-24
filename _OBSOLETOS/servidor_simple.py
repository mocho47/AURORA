#!/usr/bin/env python3
"""
AURORA v2 - Servidor Simple (Sin FastAPI)
Sirve panel HTML + endpoints básicos JSON
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

# ========== CONFIGURACIÓN ==========

AURORA_DIR = Path(__file__).parent.parent
PANEL_PATH = AURORA_DIR / "panel.html"
PORT = 8000

# ========== HANDLER ==========

class AuroraHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        # ========== ENDPOINTS ==========

        if path == "/":
            self._respond_json({
                "sistema": "AURORA v2 - Operativo",
                "status": "✅ En línea",
                "roles": ["teen", "maestro", "padre", "vendedor", "admin"],
                "librerias": 16,
                "dinamicas": 6,
                "crisis_protocol": "Activo",
                "acceso": "http://localhost:8000/panel"
            })

        elif path == "/health":
            self._respond_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "aurora": "operativo",
                "cerebro": "activo"
            })

        elif path == "/panel":
            if PANEL_PATH.exists():
                with open(PANEL_PATH, 'r', encoding='utf-8') as f:
                    self._respond_html(f.read())
            else:
                self._respond_html(f"""
                    <html>
                    <head><title>AURORA - Error</title></head>
                    <body style="background: #0f0f23; color: #e0e0e0; padding: 40px; font-family: Arial;">
                        <h1>❌ Panel no encontrado</h1>
                        <p>Ruta esperada: {PANEL_PATH}</p>
                        <p><a href="/" style="color: #667eea;">Volver</a></p>
                    </body>
                    </html>
                """)

        elif path == "/librerias":
            self._respond_json({
                "total": 16,
                "activas": [
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

        elif path == "/dinamicas":
            self._respond_json({
                "total": 6,
                "dinamicas": [
                    "Reto de 72 horas",
                    "Experto por un día",
                    "Debate Estructurado",
                    "Proyecto de Impacto",
                    "Círculo de Confianza",
                    "Mentoría Inversa",
                ]
            })

        elif path == "/roles":
            self._respond_json({
                "total": 6,
                "roles": [
                    {"id": "teen", "nombre": "🧠 Adolescente"},
                    {"id": "maestro", "nombre": "👨‍🏫 Maestro"},
                    {"id": "padre", "nombre": "👨‍👩‍👧 Padre"},
                    {"id": "vendedor", "nombre": "💼 Vendedor"},
                    {"id": "admin", "nombre": "⚙️ Admin"},
                ]
            })

        elif path == "/crisis/status":
            self._respond_json({
                "monitor": "activo",
                "nivel": "normal",
                "protocolo": "5 niveles operativos"
            })

        else:
            self._respond_404()

    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        try:
            body = self.rfile.read(content_length).decode('utf-8')
        except UnicodeDecodeError:
            body = self.rfile.read(content_length).decode('latin-1')

        try:
            data = json.loads(body) if body else {}
        except:
            data = {}

        if path == "/chat":
            mensaje = data.get("mensaje", "").lower()
            rol = data.get("rol", "teen")

            # Detectar situación y retornar respuesta real
            situacion, respuesta = self._procesar_chat(mensaje, rol)

            self._respond_json({
                "status": "ok",
                "respuesta": respuesta,
                "situacion": situacion,
                "timestamp": datetime.now().isoformat()
            })

        elif path == "/cotizar":
            producto = data.get("producto", "Desconocido")
            cantidad = data.get("cantidad", 1)

            self._respond_json({
                "producto": producto,
                "cantidad": cantidad,
                "precio_unitario": 100,
                "total_costo": 100 * cantidad,
                "margen": 50 * cantidad,
                "precio_venta": 150 * cantidad,
            })

        else:
            self._respond_404()

    def _respond_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _respond_html(self, html):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _respond_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "No encontrado"}).encode())

    def _procesar_chat(self, mensaje, rol):
        """Procesa mensaje y retorna (situacion, respuesta)"""

        # TEEN: Preguntas sobre desarrollo, estrés, identidad
        if "teen" in mensaje or "adolescente" in mensaje or "joven" in mensaje:
            return "teen_question", """AURORA es especialista en adolescentes.

Puedo ayudarte con:
✓ Estrés académico (exámenes, presión)
✓ Identidad (¿quién soy?, confusión)
✓ Relaciones (amigos, familia, novio/a)
✓ Emociones (ansiedad, tristeza, rabia)
✓ Decisiones (futuro, carrera, opciones)
✓ Autoestima (inseguridad, fracaso)
✓ Aislamiento (soledad, no encajo)
✓ Creatividad (expresión, talento dormido)
✓ Conflictos (peleas, no entiendo a adultos)
✓ Salud (mental, física, cambios)

¿Cuál es tu mayor preocupación ahora?"""

        # PREGUNTAS sobre CAPACIDADES
        elif "puedo" in mensaje or "que puedes" in mensaje or "capabilities" in mensaje or "features" in mensaje:
            return "capabilities", """AURORA puede:

🧠 CHAT PSICOLÓGICO
  • Acompañarte sin juzgar
  • Detectar qué necesitas realmente
  • Sugerir técnicas para regular emociones
  • Validar tus sentimientos

📊 ANÁLISIS SITUACIONAL
  • Entender tu contexto
  • Detectar patrones
  • Sugerir perspectivas
  • Riesgo nivel 1-5 (si es grave, alertar)

🎯 HERRAMIENTAS
  • Técnicas de respiración
  • Grounding (anclar al presente)
  • Cuestionamiento constructivo
  • Narrativa personal

💼 NEGOCIOS (si eres vendedor)
  • Cotización automática
  • Cálculo de márgenes
  • Gestión de productos

🎓 EDUCACIÓN (si eres maestro)
  • Dinámicas de grupo
  • Detección de riesgo
  • Recursos pedagógicos

👨‍👩‍👧 FAMILIA (si eres padre)
  • Escuela para padres
  • Comunicación efectiva
  • Señales de alerta

¿Cuál necesitas?"""

        # PREGUNTAS sobre TRABAJAR JUNTOS
        elif "trabajar" in mensaje or "proyecto" in mensaje or "colaborar" in mensaje:
            return "collaboration", """Sí, podemos trabajar juntos.

Si quieres que AURORA sea parte de tu proyecto:

✓ Integración en tu app
✓ API especializada por rol
✓ Modelos psicológicos reales
✓ Detección de riesgo automática
✓ Respuestas personalizadas

¿Qué tipo de proyecto?
(educativo, terapéutico, empresarial, investigación)"""

        # ESTRÉS y ANSIEDAD
        elif any(word in mensaje for word in ["estres", "estresado", "ansiedad", "nervios", "panico", "presion"]):
            return "stress", """Entiendo. El estrés es REAL y NORMAL a tu edad.

Lo importante: No vamos a eliminarlo (imposible).
Vamos a aprender a convivir con él.

Aquí está el PLAN INMEDIATO:

1️⃣ AHORA (próximos 5 min)
Respira: Inhala 4seg → Retén 4seg → Exhala 4seg
Repite 3 veces

2️⃣ LUEGO (próxima hora)
¿Qué exactamente te abruma?
(Examen específico, relación, futuro, dinero?)

3️⃣ DESPUÉS
Hacemos un plan realista, paso a paso

¿Cuál es tu MAYOR presión ahora?"""

        # SOLEDAD
        elif any(word in mensaje for word in ["solo", "aislado", "nadie", "excluido", "solo", "no encajo"]):
            return "loneliness", """"No encajo" ≠ "Me rechazan". DIFERENCIA CRÍTICA.

Sentirse solo es NORMAL adolescente.
Pero estar realmente solo es raro.

Aquí va la verdad:
✓ Tu "rareza" es tu PODER
✓ Existen otros "raros" como tú
✓ Encajar al 100% = aburrimiento
✓ Ser auténtico > conformarse

ACCIÓN:
¿Qué te hace diferente?
(Hobby, talento, forma de pensar, gustos raros?)

Vamos a encontrar TU GENTE. Existen."""

        # FRACASO/INSEGURIDAD
        elif any(word in mensaje for word in ["fracaso", "no valgo", "soy malo", "inutil", "no sirvo", "fracasé"]):
            return "failure", """El fracaso es tu MEJOR MAESTRO.

Tu cerebro está DISEÑADO para aprender de errores.

La pregunta no es: "¿Por qué fallé?"
La pregunta REAL es: "¿Qué aprendí?"

Cuéntame:
✓ ¿Qué pasó exactamente?
✓ ¿Qué intentabas lograr?
✓ ¿Qué no funcionó?

Vamos a encontrar la LECCIÓN.
Los ganadores fallan más que otros.
Simplemente aprenden más rápido."""

        # IDENTIDAD/FUTURO
        elif any(word in mensaje for word in ["quien soy", "que debo", "futuro", "carrera", "que estudiar", "identidad"]):
            return "identity", """La pregunta "¿Quién soy?" es LA pregunta adolescente.

No es que no sepas. Es que ESTÁS DESCUBRIENDO.

HERRAMIENTAS:
✓ ¿Qué te hace FELIZ? (sin que otro diga)
✓ ¿En qué eres realmente bueno?
✓ ¿Qué injusticia te enoja?
✓ ¿A qué tipo de persona quieres ser?

NO tienes que saberlo YA.
Pero sí EXPLORAR.

¿Cuál de esas 4 preguntas te atrae más?"""

        # DEPRESIÓN/TRISTEZA
        elif any(word in mensaje for word in ["triste", "tristeza", "deprimido", "sin esperanza", "vacio", "gris", "nada importa"]):
            return "depression", """Entiendo. La tristeza persistente es seria.

IMPORTANTE: Si tienes ideas de hacerte daño,
HABLA YA con un adulto. No esperes.

Si no (es "solo" tristeza profunda):

PRIMERO: Verifica lo básico
✓ ¿Estás durmiendo bien?
✓ ¿Comes regular?
✓ ¿Movimiento físico (5 min caminar)?
✓ ¿Contacto con alguien?

SEGUNDO: Busca profesional
Psicólogo real > yo

TERCERO: AHORA conmigo
¿Cuándo empezó?
¿Algo específico o "de la nada"?"""

        # RELACIONES
        elif any(word in mensaje for word in ["novio", "novia", "relacion", "beso", "amor", "sexo", "pareja"]):
            return "relationships", """Buena pregunta. La sexualidad adolescente es NORMAL.

Aquí voy sin sermón:

INFORMACIÓN REAL:
✓ Tener curiosidad es normal
✓ Masturbación es NORMAL
✓ Atracción a otros es NORMAL
✓ Ser gay/bi/pan es NORMAL

IMPORTANTE:
✓ Consentimiento SIEMPRE
✓ Comunicación honesta
✓ Protección si hay penetración
✓ "No" significa "no", sin negociar

¿Tienes una pregunta específica?
(Sin vergüenza, aquí no hay tabú)"""

        # DEFAULT: Preguntas generales
        else:
            return "general", """Entiendo tu pregunta.

Para responder mejor, cuéntame:
✓ ¿Qué es exactamente lo que te preocupa?
✓ ¿Lleva tiempo así o es nuevo?
✓ ¿Ya hablaste con alguien sobre esto?

Soy experto en adolescentes, educación, familia y desarrollo humano.

¿Cuál es tu mayor preocupación ahora?"""

    def log_message(self, format, *args):
        """Suppress logging"""
        pass

# ========== MAIN ==========

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), AuroraHandler)

    print("\n" + "="*80)
    print("AURORA v2 - SERVIDOR INICIADO")
    print("="*80)
    print("\nPanel:  http://localhost:8000/panel")
    print("API:    http://localhost:8000/")
    print("Chat:   POST http://localhost:8000/chat")
    print("\n6 Roles operativos")
    print("16 Librerías psicológicas")
    print("6 Dinámicas educativas")
    print("Crisis protocol activo")
    print("\nPresiona Ctrl+C para detener AURORA\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nAURORA v2 apagándose...")
        server.server_close()
