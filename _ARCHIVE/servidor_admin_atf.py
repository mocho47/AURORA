#!/usr/bin/env python3
"""
ServidorAdminATF - Dashboard profesional para gestión completa
- Panel admin con control 100% de publicaciones
- Monitor en vivo de todas las plataformas
- Sugerencias inteligentes automáticas
- Editor de videos integrado
- Analytics y métricas detalladas
"""

import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from publicador_inteligente_atf import PublicadorInteligenteATF

class AdminATFHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ATF admin panel"""

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/" or path == "/admin":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._get_dashboard_html().encode('utf-8'))

        elif path == "/api/dashboard":
            asyncio.run(self._handle_dashboard_api())

        elif path == "/api/videos":
            asyncio.run(self._handle_videos_list())

        elif path == "/api/publicaciones":
            asyncio.run(self._handle_publicaciones_list())

        elif path == "/api/monitor":
            asyncio.run(self._handle_monitor())

        elif path == "/api/sugerencias":
            asyncio.run(self._handle_sugerencias())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/programar-publicaciones":
            asyncio.run(self._handle_programar_publicaciones(data))

        elif path == "/api/crear-variaciones":
            asyncio.run(self._handle_crear_variaciones(data))

        elif path == "/api/ejecutar-ahora":
            asyncio.run(self._handle_ejecutar_ahora(data))

        elif path == "/api/escanear-videos":
            asyncio.run(self._handle_escanear_videos())

        else:
            self.send_response(404)
            self.end_headers()

    async def _handle_dashboard_api(self):
        """GET /api/dashboard - Main dashboard metrics"""
        publicador = PublicadorInteligenteATF()
        monitor_data = await publicador.get_monitor_en_vivo()

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(monitor_data).encode('utf-8'))

    async def _handle_videos_list(self):
        """GET /api/videos - List all videos in library"""
        publicador = PublicadorInteligenteATF()

        try:
            import sqlite3
            conn = sqlite3.connect("C:\\AURORA\\atf_inteligente.db")
            c = conn.cursor()
            c.execute("SELECT id, filename, duration, plays, last_published FROM videos LIMIT 50")
            videos = [
                {
                    "id": row[0],
                    "filename": row[1],
                    "duration": row[2],
                    "plays": row[3],
                    "last_published": row[4]
                }
                for row in c.fetchall()
            ]
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"videos": videos}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_publicaciones_list(self):
        """GET /api/publicaciones - List all scheduled publications"""
        try:
            import sqlite3
            conn = sqlite3.connect("C:\\AURORA\\atf_inteligente.db")
            c = conn.cursor()
            c.execute("""
                SELECT id, video_id, plataforma, grupo_url, hora_publicar, estado, fecha_creacion
                FROM publicaciones
                ORDER BY fecha_creacion DESC
                LIMIT 100
            """)
            publicaciones = [
                {
                    "id": row[0],
                    "video_id": row[1],
                    "plataforma": row[2],
                    "grupo_url": row[3],
                    "hora_publicar": row[4],
                    "estado": row[5],
                    "fecha_creacion": row[6]
                }
                for row in c.fetchall()
            ]
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"publicaciones": publicaciones}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_monitor(self):
        """GET /api/monitor - Live monitoring data"""
        publicador = PublicadorInteligenteATF()
        monitor = await publicador.get_monitor_en_vivo()

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(monitor).encode('utf-8'))

    async def _handle_sugerencias(self):
        """GET /api/sugerencias - AI suggestions for next publications"""
        try:
            import sqlite3
            conn = sqlite3.connect("C:\\AURORA\\atf_inteligente.db")
            c = conn.cursor()
            c.execute("""
                SELECT video_id, plataforma, grupo_url, score, razon
                FROM sugerencias
                ORDER BY score DESC
                LIMIT 20
            """)
            sugerencias = [
                {
                    "video_id": row[0],
                    "plataforma": row[1],
                    "grupo_url": row[2],
                    "score": row[3],
                    "razon": row[4]
                }
                for row in c.fetchall()
            ]
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"sugerencias": sugerencias}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_programar_publicaciones(self, data):
        """POST /api/programar-publicaciones - Schedule publications"""
        try:
            publicador = PublicadorInteligenteATF()
            dias = data.get("dias", 7)

            resultado = await publicador.programar_publicaciones(dias)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resultado).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_crear_variaciones(self, data):
        """POST /api/crear-variaciones - Create video variations"""
        try:
            video_id = data.get("video_id")
            publicador = PublicadorInteligenteATF()

            variaciones = await publicador.crear_variaciones_video(video_id)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "video_id": video_id,
                "variaciones": variaciones
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_ejecutar_ahora(self, data):
        """POST /api/ejecutar-ahora - Execute pending publications immediately"""
        try:
            publicador = PublicadorInteligenteATF()
            resultados = await publicador.ejecutar_publicaciones_pendientes()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "publicaciones_ejecutadas": len(resultados),
                "resultados": resultados
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    async def _handle_escanear_videos(self):
        """POST /api/escanear-videos - Scan videos directory"""
        try:
            publicador = PublicadorInteligenteATF()
            videos = await publicador.scan_videos_library()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "videos_encontrados": len(videos),
                "videos": [
                    {
                        "id": v.id,
                        "filename": v.filename,
                        "duration": v.duration,
                        "size": v.size
                    }
                    for v in videos
                ]
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def _get_dashboard_html(self) -> str:
        """Return beautiful admin dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATF - Admin Profesional</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .container { max-width: 1400px; margin: 0 auto; }

        header {
            background: rgba(0,0,0,0.3);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #ff6b6b;
        }

        header h1 { font-size: 2.5em; margin-bottom: 5px; }
        header p { opacity: 0.8; }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }

        .card h3 {
            color: #ff6b6b;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }

        .card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #fff;
        }

        .card .subtitle {
            opacity: 0.7;
            margin-top: 5px;
            font-size: 0.85em;
        }

        .actions {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }

        button {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }

        button:hover {
            background: #ff5252;
            transform: translateY(-2px);
        }

        button.secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }

        button.secondary:hover {
            background: rgba(255,255,255,0.2);
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .tab {
            padding: 15px 20px;
            background: none;
            border: none;
            color: #fff;
            cursor: pointer;
            opacity: 0.6;
            border-bottom: 2px solid transparent;
        }

        .tab.active {
            opacity: 1;
            border-bottom-color: #ff6b6b;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        table th {
            background: rgba(255,255,255,0.05);
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        table td {
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        table tr:hover {
            background: rgba(255,255,255,0.02);
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }

        .badge.pending {
            background: #ff9100;
            color: white;
        }

        .badge.published {
            background: #4caf50;
            color: white;
        }

        .badge.error {
            background: #f44336;
            color: white;
        }

        .loading {
            text-align: center;
            padding: 20px;
            opacity: 0.7;
        }

        .error {
            background: rgba(244, 67, 54, 0.2);
            border-left: 4px solid #f44336;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }

        .success {
            background: rgba(76, 175, 80, 0.2);
            border-left: 4px solid #4caf50;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <header>
            <h1>🎬 ATF - Admin Profesional</h1>
            <p>Gestión inteligente de 200+ videos • Publicación automática 2-3 posts/día</p>
        </header>

        <!-- KPIs -->
        <div class="grid">
            <div class="card">
                <h3>Publicaciones Hoy</h3>
                <div class="number" id="pub-hoy">-</div>
                <div class="subtitle">Videos publicados</div>
            </div>
            <div class="card">
                <h3>Pendientes</h3>
                <div class="number" id="pendientes">-</div>
                <div class="subtitle">Próximas publicaciones</div>
            </div>
            <div class="card">
                <h3>Videos en Library</h3>
                <div class="number" id="total-videos">-</div>
                <div class="subtitle">Catalogados y listos</div>
            </div>
            <div class="card">
                <h3>Engagement</h3>
                <div class="number" id="engagement">-</div>
                <div class="subtitle">Promedio de interacción</div>
            </div>
        </div>

        <!-- ACTIONS -->
        <div class="actions">
            <button onclick="escanearVideos()">📁 Escanear Videos</button>
            <button onclick="programarPublicaciones()">📅 Programar 7 días</button>
            <button onclick="ejecutarAhora()">🚀 Ejecutar Ahora</button>
            <button class="secondary" onclick="actualizarDashboard()">🔄 Actualizar</button>
        </div>

        <!-- TABS -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('publicaciones')">Publicaciones</button>
            <button class="tab" onclick="switchTab('videos')">Videos</button>
            <button class="tab" onclick="switchTab('sugerencias')">Sugerencias IA</button>
            <button class="tab" onclick="switchTab('plataformas')">Plataformas</button>
        </div>

        <!-- PUBLICACIONES TAB -->
        <div id="publicaciones" class="tab-content active">
            <div class="card">
                <h3>Próximas Publicaciones</h3>
                <div id="pub-lista" class="loading">Cargando...</div>
            </div>
        </div>

        <!-- VIDEOS TAB -->
        <div id="videos" class="tab-content">
            <div class="card">
                <h3>Videos Catalogados</h3>
                <div id="video-lista" class="loading">Cargando...</div>
            </div>
        </div>

        <!-- SUGERENCIAS TAB -->
        <div id="sugerencias" class="tab-content">
            <div class="card">
                <h3>Sugerencias de IA para Publicar</h3>
                <div id="sugerencias-lista" class="loading">Cargando...</div>
            </div>
        </div>

        <!-- PLATAFORMAS TAB -->
        <div id="plataformas" class="tab-content">
            <div class="card">
                <h3>Desempeño por Plataforma</h3>
                <div id="plataformas-lista" class="loading">Cargando...</div>
            </div>
        </div>
    </div>

    <script>
        async function actualizarDashboard() {
            try {
                const dash = await fetch('/api/dashboard').then(r => r.json());
                document.getElementById('pub-hoy').textContent = dash.publicaciones_hoy || '0';
                document.getElementById('pendientes').textContent = dash.pendientes || '0';
                document.getElementById('engagement').textContent = (dash.engagement_promedio || 0).toFixed(1) + '%';

                const videos = await fetch('/api/videos').then(r => r.json());
                document.getElementById('total-videos').textContent = videos.videos.length;

                cargarPublicaciones();
                cargarVideos();
                cargarSugerencias();
            } catch (e) {
                console.error(e);
            }
        }

        async function cargarPublicaciones() {
            try {
                const data = await fetch('/api/publicaciones').then(r => r.json());
                let html = '<table><tr><th>Video</th><th>Plataforma</th><th>Hora</th><th>Estado</th></tr>';
                data.publicaciones.slice(0, 20).forEach(p => {
                    const estadoClass = p.estado === 'publicado' ? 'published' : p.estado === 'error' ? 'error' : 'pending';
                    html += `<tr><td>${p.video_id}</td><td>${p.plataforma}</td><td>${p.hora_publicar}</td><td><span class="badge ${estadoClass}">${p.estado}</span></td></tr>`;
                });
                html += '</table>';
                document.getElementById('pub-lista').innerHTML = html;
            } catch (e) {
                document.getElementById('pub-lista').innerHTML = `<div class="error">Error: ${e.message}</div>`;
            }
        }

        async function cargarVideos() {
            try {
                const data = await fetch('/api/videos').then(r => r.json());
                let html = '<table><tr><th>Archivo</th><th>Duración</th><th>Reproducciones</th></tr>';
                data.videos.slice(0, 20).forEach(v => {
                    html += `<tr><td>${v.filename}</td><td>${v.duration}s</td><td>${v.plays || 0}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('video-lista').innerHTML = html;
            } catch (e) {
                document.getElementById('video-lista').innerHTML = `<div class="error">Error: ${e.message}</div>`;
            }
        }

        async function cargarSugerencias() {
            try {
                const data = await fetch('/api/sugerencias').then(r => r.json());
                let html = '<table><tr><th>Video</th><th>Plataforma</th><th>Score</th><th>Razón</th></tr>';
                data.sugerencias.slice(0, 15).forEach(s => {
                    html += `<tr><td>${s.video_id}</td><td>${s.plataforma}</td><td>${(s.score * 100).toFixed(0)}%</td><td>${s.razon}</td></tr>`;
                });
                html += '</table>';
                document.getElementById('sugerencias-lista').innerHTML = html;
            } catch (e) {
                document.getElementById('sugerencias-lista').innerHTML = `<div class="error">Error: ${e.message}</div>`;
            }
        }

        async function programarPublicaciones() {
            try {
                const result = await fetch('/api/programar-publicaciones', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({dias: 7})
                }).then(r => r.json());

                alert(`✅ ${result.publicaciones_programadas} publicaciones programadas para 7 días`);
                actualizarDashboard();
            } catch (e) {
                alert(`Error: ${e.message}`);
            }
        }

        async function ejecutarAhora() {
            try {
                const result = await fetch('/api/ejecutar-ahora', {
                    method: 'POST',
                    body: '{}'
                }).then(r => r.json());

                alert(`✅ ${result.publicaciones_ejecutadas} videos publicados`);
                actualizarDashboard();
            } catch (e) {
                alert(`Error: ${e.message}`);
            }
        }

        async function escanearVideos() {
            try {
                const result = await fetch('/api/escanear-videos', {
                    method: 'POST',
                    body: '{}'
                }).then(r => r.json());

                alert(`✅ ${result.videos_encontrados} videos catalogados`);
                actualizarDashboard();
            } catch (e) {
                alert(`Error: ${e.message}`);
            }
        }

        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        // Cargar al abrir
        actualizarDashboard();
        setInterval(actualizarDashboard, 10000); // Auto-refresh cada 10 segundos
    </script>
</body>
</html>
        '''

def main():
    """Start ATF admin server"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, AdminATFHandler)
    print("🚀 ATF Admin Profesional corriendo en http://localhost:8000")
    print("   - Panel completo de publicaciones")
    print("   - Programación automática 2-3 posts/día")
    print("   - Editor de videos integrado")
    print("   - Sugerencias inteligentes de IA")
    print("\nPresiona Ctrl+C para detener...")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
