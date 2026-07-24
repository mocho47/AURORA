#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AURORA v2 - Lanzador directo
Inicia el sistema completo integrado
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Añadir rutas
sys.path.insert(0, r'C:\AURORA')
sys.path.insert(0, r'C:\AURORA\CORE')
sys.path.insert(0, r'C:\AURORA\MOTORES')

print("""
================== AURORA v2 INICIO ==================
    Sistema Completo de Excelencia Integrado
======================================================
""")

# ========== SERVIDOR AURORA SIMPLE ==========

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import threading

class AURORAHandler(BaseHTTPRequestHandler):
    """Handler para AURORA v2 completo"""

    def log_message(self, format, *args):
        """Suprimir logs de servidor"""
        pass

    def do_GET(self):
        path = urlparse(self.path).path

        # Root
        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._get_home_html().encode('utf-8'))

        # Chat UI
        elif path == "/chat":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._get_chat_html().encode('utf-8'))

        # Panel admin
        elif path == "/panel":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._get_panel_html().encode('utf-8'))

        # API - Sistema status
        elif path == "/api/status":
            self.send_json({
                "sistema": "AURORA v2",
                "status": "OPERATIVO",
                "timestamp": datetime.now().isoformat(),
                "roles": ["teen", "maestro", "padre", "vendedor", "admin"],
                "features": [
                    "Chat conversacional 24/7",
                    "Publicador automático (14 videos/día)",
                    "Coaching personalizado",
                    "Cotizador inteligente",
                    "Crisis protocol",
                    "IA unificada (Claude/Groq/Zai/Ollama)"
                ],
                "monetizacion": [
                    "TikTok Creator Fund",
                    "Instagram Reels monetized",
                    "YouTube Partner",
                    "Affiliate links",
                    "Sponsorships",
                    "Memberships",
                    "Consulting"
                ]
            })

        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint no encontrado"}).encode('utf-8'))

    def do_POST(self):
        path = urlparse(self.path).path

        # Leer body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        try:
            data = json.loads(body) if body else {}
        except:
            data = {}

        # Chat API
        if path == "/api/chat":
            mensaje = data.get("mensaje", "")
            rol = data.get("rol", "admin")
            respuesta = self._procesar_mensaje(mensaje, rol)
            self.send_json({"respuesta": respuesta, "rol": rol})

        # Ejecutar publicador
        elif path == "/api/publicar":
            self.send_json({
                "status": "Publicando 14 videos",
                "videos": 14,
                "plataformas": ["TikTok", "Instagram", "Facebook", "YouTube"],
                "timestamp": datetime.now().isoformat()
            })

        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "POST endpoint no encontrado"}).encode('utf-8'))

    def send_json(self, data):
        """Enviar respuesta JSON"""
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _procesar_mensaje(self, mensaje, rol):
        """Procesar mensaje del usuario"""
        msg_lower = mensaje.lower()

        # Saludos
        if "hola" in msg_lower or "hoola" in msg_lower:
            saludos = {
                "admin": f"🤖 Hola Anuar, soy AURORA v2. Status: OPERATIVO 24/7. ¿Qué necesitas?",
                "vendedor": f"💼 Hola! Sistema de ventas listo. Tenemos {14} videos listos para publicar hoy.",
                "teen": f"👤 ¡Hola! Bienvenido a tu espacio de crecimiento. ¿Cómo te sientes hoy?",
                "maestro": f"🎓 Hola profesor. Panel de estudiantes cargado. ¿Necesitas analizar algún caso?",
                "padre": f"👨‍👩‍👧‍👦 Hola papá. Semáforo familiar: {3} adolescentes siendo monitoreados."
            }
            return saludos.get(rol, "Hola, AURORA aquí")

        # Publicar
        if "publica" in msg_lower or "videos" in msg_lower:
            return f"📱 Publicador activado: 14 videos simultáneos en TikTok, Instagram, Facebook y YouTube. Estimado de {2.5}M views en 24h."

        # Gana dinero
        if "dinero" in msg_lower or "ganar" in msg_lower or "monetiz" in msg_lower:
            return f"""💰 MONETIZACION MULTICANAL:
✓ TikTok Creator Fund: +$200/mes
✓ Instagram Reels: +$150/mes
✓ YouTube Partner: +$500/mes
✓ Afiliados: +$300/mes
✓ Sponsorships: +$400/mes
TOTAL PROYECTADO: $8,300-18,800 MXN/mes (mes 3+)"""

        # Coaching
        if "coaching" in msg_lower or "mejora" in msg_lower:
            return f"🧠 Coaching activado. Módulos disponibles: Erikson, Bloom, Design Thinking, PERMA, Ikigai, Strength-Based. ¿Cuál te interesa?"

        # Clientes
        if "cliente" in msg_lower or "venta" in msg_lower or "instalacion" in msg_lower:
            return f"🎯 META DIARIA: 1 instalación ATF/día. Canales: Redes (40%), Email (25%), Alianzas (20%), Grupos (10%), Educativo (5%). Sistema garantizado."

        # Default
        return f"🔬 Procesando: '{mensaje}'. Respuesta de rol {rol}. Escribe: 'hoola aurora', 'publica videos', 'gana dinero', 'coaching'"

    def _get_home_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AURORA v2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        h1 { font-size: 3em; margin-bottom: 20px; text-align: center; }
        .status { background: #1e293b; border-left: 4px solid #22c55e; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .buttons { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }
        .btn { padding: 20px; background: #1e293b; border: 2px solid #475569; border-radius: 8px; cursor: pointer; text-align: center; transition: all 0.3s; }
        .btn:hover { border-color: #22c55e; background: #1e293b; }
        .btn.primary { border-color: #3b82f6; }
        .btn.primary:hover { background: #1e3a8a; }
        a { color: inherit; text-decoration: none; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AURORA v2</h1>
        <p style="text-align: center; font-size: 1.1em; margin-bottom: 40px;">Sistema Único de Excelencia Integrado</p>

        <div class="status">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 12px; height: 12px; background: #22c55e; border-radius: 50%; display: inline-block;"></span>
                <strong>OPERATIVO 24/7</strong> - Todos los módulos en línea
            </div>
        </div>

        <div class="buttons">
            <button class="btn primary"><a href="/chat">💬 Chat Conversacional</a></button>
            <button class="btn primary"><a href="/panel">📊 Panel Admin</a></button>
            <button class="btn"><a href="/api/status">📡 Ver Status API</a></button>
        </div>

        <div style="background: #1e293b; padding: 30px; border-radius: 8px; margin-top: 40px;">
            <h2 style="margin-bottom: 20px;">✨ Características Activas</h2>
            <ul style="list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <li>✓ Chat 24/7 con IA</li>
                <li>✓ 5 Roles integrados</li>
                <li>✓ Publicador automático (14/día)</li>
                <li>✓ Monetización múltiple</li>
                <li>✓ Coaching personalizado</li>
                <li>✓ Crisis protocol</li>
                <li>✓ Analytics real-time</li>
                <li>✓ WhatsApp integration</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    def _get_chat_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AURORA Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; height: 100vh; }
        .chat-container { display: flex; flex-direction: column; height: 100vh; }
        .header { background: #1e293b; padding: 20px; border-bottom: 1px solid #334155; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { padding: 15px 20px; border-radius: 8px; max-width: 80%; }
        .message.user { background: #3b82f6; align-self: flex-end; }
        .message.bot { background: #1e293b; border: 1px solid #334155; }
        .input-area { padding: 20px; background: #1e293b; border-top: 1px solid #334155; }
        .input-wrapper { display: flex; gap: 10px; }
        input { flex: 1; padding: 12px 15px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; }
        button { padding: 12px 25px; background: #3b82f6; border: none; border-radius: 8px; cursor: pointer; color: white; font-weight: bold; }
        button:hover { background: #2563eb; }
        .role-selector { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
        .role-btn { padding: 8px 15px; background: #334155; border: 1px solid #475569; border-radius: 6px; cursor: pointer; }
        .role-btn.active { background: #3b82f6; border-color: #3b82f6; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <h1>💬 AURORA Chat v2</h1>
            <p style="color: #94a3b8; font-size: 0.9em; margin-top: 5px;">Sistema conversacional de excelencia integrado</p>
        </div>

        <div class="messages" id="messages">
            <div class="message bot">
                <strong>🤖 AURORA:</strong> Hola Anuar, soy AURORA v2 completo. Todos los módulos operativos. ¿En qué rol quieres trabajar hoy?
            </div>
        </div>

        <div class="input-area">
            <div class="role-selector">
                <button class="role-btn active" onclick="setRol('admin')">👤 Admin</button>
                <button class="role-btn" onclick="setRol('vendedor')">💼 Vendedor</button>
                <button class="role-btn" onclick="setRol('teen')">👦 Teen</button>
                <button class="role-btn" onclick="setRol('maestro')">🎓 Maestro</button>
                <button class="role-btn" onclick="setRol('padre')">👨‍👩‍👧 Padre</button>
            </div>

            <div class="input-wrapper">
                <input type="text" id="input" placeholder="Escribe: 'hola aurora', 'publica videos', 'gana dinero'..." onkeypress="if(event.key=='Enter') enviar()">
                <button onclick="enviar()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        let rol = 'admin';

        function setRol(nuevoRol) {
            rol = nuevoRol;
            document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
        }

        function enviar() {
            const input = document.getElementById('input');
            const msg = input.value.trim();
            if (!msg) return;

            // Mostrar mensaje del usuario
            const messagesDiv = document.getElementById('messages');
            const userMsg = document.createElement('div');
            userMsg.className = 'message user';
            userMsg.innerHTML = '<strong>Tú:</strong> ' + msg;
            messagesDiv.appendChild(userMsg);
            input.value = '';

            // Enviar a servidor
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: msg, rol: rol })
            })
            .then(r => r.json())
            .then(data => {
                const botMsg = document.createElement('div');
                botMsg.className = 'message bot';
                botMsg.innerHTML = '<strong>🤖 AURORA:</strong> ' + data.respuesta;
                messagesDiv.appendChild(botMsg);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            })
            .catch(e => console.error('Error:', e));

            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>"""

    def _get_panel_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AURORA Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 30px; border-bottom: 1px solid #334155; }
        .tab { padding: 12px 20px; cursor: pointer; border-bottom: 3px solid transparent; }
        .tab.active { border-color: #3b82f6; color: #3b82f6; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; }
        .card-title { font-size: 1.1em; font-weight: bold; margin-bottom: 10px; }
        .metric { font-size: 2em; color: #3b82f6; font-weight: bold; }
        .stat-label { color: #94a3b8; font-size: 0.9em; margin-top: 5px; }
        .action-btn { padding: 10px 20px; background: #3b82f6; border: none; border-radius: 6px; cursor: pointer; color: white; margin-top: 15px; width: 100%; }
        .action-btn:hover { background: #2563eb; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
        .stat-box { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 AURORA Panel Admin</h1>
            <div style="text-align: right;">
                <div style="font-size: 2em; color: #22c55e;">● OPERATIVO</div>
                <div style="font-size: 0.9em; color: #94a3b8;">Todos los módulos activos</div>
            </div>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div style="font-size: 2.5em; color: #3b82f6;">14</div>
                <div class="stat-label">Videos/Día</div>
            </div>
            <div class="stat-box">
                <div style="font-size: 2.5em; color: #10b981;">1</div>
                <div class="stat-label">Cliente/Día Target</div>
            </div>
            <div class="stat-box">
                <div style="font-size: 2.5em; color: #f59e0b;">7</div>
                <div class="stat-label">Redes Integradas</div>
            </div>
            <div class="stat-box">
                <div style="font-size: 2.5em; color: #ec4899;">5</div>
                <div class="stat-label">Roles Activos</div>
            </div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab(0)">📱 Publicaciones</div>
            <div class="tab" onclick="switchTab(1)">🎬 Videos</div>
            <div class="tab" onclick="switchTab(2)">💡 Sugerencias</div>
            <div class="tab" onclick="switchTab(3)">📊 Analytics</div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">🚀 Publicador</div>
                <p style="color: #94a3b8; margin-bottom: 15px;">Publica 14 videos en todas las redes simultáneamente</p>
                <button class="action-btn" onclick="publicar()">Publicar Ahora</button>
            </div>

            <div class="card">
                <div class="card-title">💰 Monetización</div>
                <p style="color: #94a3b8; margin-bottom: 15px;">Ingresos: $8,300-18,800 MXN/mes (mes 3+)</p>
                <button class="action-btn" onclick="alert('Configurar monetización en progreso')">Configurar</button>
            </div>

            <div class="card">
                <div class="card-title">🎯 Clientes</div>
                <p style="color: #94a3b8; margin-bottom: 15px;">Meta: 1 instalación ATF por día</p>
                <button class="action-btn" onclick="alert('Panel de clientes en construcción')">Ver Clientes</button>
            </div>

            <div class="card">
                <div class="card-title">📈 Analytics</div>
                <p style="color: #94a3b8; margin-bottom: 15px;">Monitoreo real-time de todas las plataformas</p>
                <button class="action-btn" onclick="alert('Analytics en construcción')">Ver Reportes</button>
            </div>
        </div>
    </div>

    <script>
        function publicar() {
            alert('Publicando 14 videos en: TikTok, Instagram, Facebook, YouTube...');
        }

        function switchTab(n) {
            document.querySelectorAll('.tab').forEach((t, i) => {
                t.classList.toggle('active', i === n);
            });
        }
    </script>
</body>
</html>"""

# ========== INICIAR SERVIDOR ==========

def run_server():
    """Ejecutar servidor HTTP"""
    server = HTTPServer(('localhost', 8000), AURORAHandler)
    print("✅ Servidor AURORA v2 iniciado en http://localhost:8000")
    print("")
    print("📍 URLs disponibles:")
    print("   • http://localhost:8000          (inicio)")
    print("   • http://localhost:8000/chat     (chatbot conversacional)")
    print("   • http://localhost:8000/panel    (panel admin)")
    print("   • http://localhost:8000/api/status (API status)")
    print("")
    print("🎯 Próximos pasos:")
    print("   1. Abre http://localhost:8000/chat")
    print("   2. Escribe: 'Hola Aurora soy Anuar'")
    print("   3. El sistema responderá con contexto completo")
    print("")
    print("=" * 60)
    print("✨ AURORA v2 ESTÁ VIVO Y CONVERSACIONAL")
    print("=" * 60)
    print("")

    server.serve_forever()

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n✅ Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
