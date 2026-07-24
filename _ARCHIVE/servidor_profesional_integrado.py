#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║  🌐 SERVIDOR HTTP PROFESIONAL INTEGRADO - CÓDIGO DE PRODUCCIÓN 🌐         ║
║                                                                             ║
║  API REST que integra:                                                     ║
║  • Publicador ATF profesional                                              ║
║  • Buscador web profesional                                                ║
║  • ChatBot WhatsApp profesional                                            ║
║  • Webhook para WhatsApp                                                   ║
║  • Base de datos SQLite                                                    ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import threading
from datetime import datetime

# Importar módulos profesionales
from CORE.publicador_atf_profesional import PublicadorATFProfesional, ConfiguracionPublicacion, RedSocial, CredencialesRed
from CORE.buscador_web_profesional import BuscadorWebProfesional
from CORE.chatbot_wa_profesional import ChatbotWAProfesional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('servidor_profesional.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServidorProfesionalHandler(BaseHTTPRequestHandler):
    """Handler HTTP para API REST profesional"""

    # Variables de clase compartidas entre requests
    publicador = None
    buscador = None
    chatbot = None

    def log_message(self, format, *args):
        """Custom logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        """Maneja GET requests"""
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        logger.info(f"GET {path}")

        try:
            if path == "/":
                self._responder_html_panel()

            elif path == "/api/health":
                self._responder_json({
                    "status": "ok",
                    "timestamp": datetime.now().isoformat(),
                    "sistema": "Servidor Profesional Integrado"
                })

            elif path == "/api/estadisticas/chatbot":
                if self.chatbot:
                    self._responder_json(self.chatbot.obtener_estadisticas())
                else:
                    self._responder_error("ChatBot no inicializado", 503)

            elif path == "/api/publicaciones":
                if self.publicador:
                    self._responder_json(self.publicador.obtener_estadisticas())
                else:
                    self._responder_error("Publicador no inicializado", 503)

            else:
                self._responder_404()

        except Exception as e:
            logger.error(f"❌ Error en GET {path}: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    def do_POST(self):
        """Maneja POST requests"""
        path = urlparse(self.path).path

        logger.info(f"POST {path}")

        try:
            # Leer body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            if path == "/api/publicar":
                self._manejar_publicar(body)

            elif path == "/api/buscar":
                asyncio.run(self._manejar_buscar(body))

            elif path == "/api/chatbot/mensaje":
                asyncio.run(self._manejar_mensaje_chatbot(body))

            elif path == "/webhook/whatsapp":
                self._manejar_webhook_whatsapp(body)

            else:
                self._responder_404()

        except Exception as e:
            logger.error(f"❌ Error en POST {path}: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    def _manejar_publicar(self, body: bytes):
        """Maneja publicación multi-red"""

        try:
            datos = json.loads(body.decode('utf-8'))

            if not self.publicador:
                self._responder_error("Publicador no inicializado", 503)
                return

            # Validar datos
            if not datos.get('titulo') or not datos.get('archivo_video_path'):
                self._responder_error("Faltan parámetros requeridos", 400)
                return

            # Crear configuración
            config = ConfiguracionPublicacion(
                titulo=datos['titulo'],
                descripcion=datos.get('descripcion', ''),
                archivo_video_path=datos['archivo_video_path'],
                redes=[RedSocial[r] for r in datos.get('redes', ['TIKTOK', 'INSTAGRAM'])]
            )

            # Validar
            valida, mensaje = config.validar()
            if not valida:
                self._responder_error(mensaje, 400)
                return

            # Ejecutar publicación en thread async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            resultados = loop.run_until_complete(
                self.publicador.publicar_multi_red(config)
            )

            loop.close()

            # Responder
            respuesta = {
                "status": "success",
                "titulo": config.titulo,
                "redes_procesadas": len(resultados),
                "resultados": {
                    red.value['nombre']: {
                        "exitoso": resultado.exitoso,
                        "id_post": resultado.id_post,
                        "url": resultado.url_post,
                        "error": resultado.error
                    }
                    for red, resultado in resultados.items()
                }
            }

            self._responder_json(respuesta)

        except json.JSONDecodeError:
            self._responder_error("JSON inválido", 400)
        except Exception as e:
            logger.error(f"❌ Error en publicación: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    async def _manejar_buscar(self, body: bytes):
        """Maneja búsqueda de productos"""

        try:
            datos = json.loads(body.decode('utf-8'))

            if not self.buscador:
                self._responder_error("Buscador no inicializado", 503)
                return

            query = datos.get('query')
            if not query:
                self._responder_error("Falta parámetro 'query'", 400)
                return

            # Realizar búsqueda
            resultado = await self.buscador.buscar(
                query,
                incluir_google=datos.get('incluir_google', False),
                incluir_mercadolibre=datos.get('incluir_mercadolibre', True),
                incluir_scraping=datos.get('incluir_scraping', False)
            )

            mejor_opcion = resultado.obtener_mejor_opcion()

            respuesta = {
                "status": "success",
                "query": query,
                "opciones_encontradas": len(resultado.productos),
                "tiempo_busqueda_segundos": resultado.tiempo_busqueda_segundos,
                "mejor_opcion": {
                    "titulo": mejor_opcion.titulo,
                    "precio": mejor_opcion.precio,
                    "moneda": mejor_opcion.moneda,
                    "vendedor": mejor_opcion.vendedor,
                    "url": mejor_opcion.url,
                    "rating": mejor_opcion.rating,
                    "opiniones": mejor_opcion.numero_opiniones
                } if mejor_opcion else None,
                "analisis": resultado.obtener_analisis()
            }

            self._responder_json(respuesta)

        except json.JSONDecodeError:
            self._responder_error("JSON inválido", 400)
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    async def _manejar_mensaje_chatbot(self, body: bytes):
        """Maneja mensaje para chatbot"""

        try:
            datos = json.loads(body.decode('utf-8'))

            if not self.chatbot:
                self._responder_error("ChatBot no inicializado", 503)
                return

            whatsapp = datos.get('whatsapp')
            mensaje = datos.get('mensaje')

            if not whatsapp or not mensaje:
                self._responder_error("Faltan parámetros: whatsapp, mensaje", 400)
                return

            # Procesar mensaje
            respuesta_bot = await self.chatbot.procesar_mensaje(whatsapp, mensaje)

            # Enviar respuesta automáticamente si está configurado
            enviado = await self.chatbot.enviar_mensaje(whatsapp, respuesta_bot)

            respuesta = {
                "status": "success",
                "whatsapp": whatsapp,
                "respuesta": respuesta_bot,
                "enviado": enviado,
                "timestamp": datetime.now().isoformat()
            }

            self._responder_json(respuesta)

        except json.JSONDecodeError:
            self._responder_error("JSON inválido", 400)
        except Exception as e:
            logger.error(f"❌ Error en chatbot: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    def _manejar_webhook_whatsapp(self, body: bytes):
        """Maneja webhook de WhatsApp (Green API / Meta)"""

        try:
            # Verificar token
            verify_token = self.headers.get('X-Hub-Signature', '')

            if self.chatbot and not self.chatbot.validar_firma_webhook(body.decode(), verify_token):
                self._responder_error("Firma inválida", 403)
                return

            datos = json.loads(body.decode('utf-8'))

            # Procesar diferentes tipos de webhooks
            entry = datos.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])

            respuestas = []

            for msg in messages:
                whatsapp_sender = msg.get('from')
                texto = msg.get('text', {}).get('body', '')

                if whatsapp_sender and texto and self.chatbot:
                    # Procesar en thread async
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    respuesta_bot = loop.run_until_complete(
                        self.chatbot.procesar_mensaje(whatsapp_sender, texto)
                    )

                    loop.close()

                    respuestas.append({
                        "whatsapp": whatsapp_sender,
                        "respuesta": respuesta_bot,
                        "procesado": True
                    })

            self._responder_json({
                "status": "success",
                "mensajes_procesados": len(respuestas),
                "respuestas": respuestas
            })

        except json.JSONDecodeError:
            self._responder_error("JSON inválido", 400)
        except Exception as e:
            logger.error(f"❌ Error en webhook: {e}", exc_info=True)
            self._responder_error(str(e), 500)

    def _responder_json(self, datos: dict, codigo: int = 200):
        """Envía respuesta JSON"""
        respuesta = json.dumps(datos, ensure_ascii=False, indent=2)

        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(respuesta.encode('utf-8'))

    def _responder_error(self, mensaje: str, codigo: int = 400):
        """Envía respuesta de error"""
        self._responder_json({
            "status": "error",
            "error": mensaje,
            "timestamp": datetime.now().isoformat()
        }, codigo)

    def _responder_404(self):
        """Responde 404"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def _responder_html_panel(self):
        """Sirve panel HTML"""
        html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servidor Profesional Integrado</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; background: #0f0f1e; color: #fff; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #00ff00; margin-bottom: 20px; }
        .section { background: #1a1a2e; padding: 15px; margin-bottom: 15px; border-left: 3px solid #00ff00; }
        .endpoint { background: #262642; padding: 10px; margin: 5px 0; font-size: 0.9em; }
        code { color: #00ff00; background: #000; padding: 2px 5px; border-radius: 3px; }
        button { background: #00ff00; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; margin: 5px; }
        button:hover { background: #00dd00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 SERVIDOR PROFESIONAL INTEGRADO</h1>

        <div class="section">
            <h2>📊 API REST Endpoints</h2>
            <div class="endpoint">GET <code>/</code> - Este panel</div>
            <div class="endpoint">GET <code>/api/health</code> - Estado del servidor</div>
            <div class="endpoint">GET <code>/api/estadisticas/chatbot</code> - Estadísticas de ChatBot</div>
            <div class="endpoint">GET <code>/api/publicaciones</code> - Historial de publicaciones</div>
            <div class="endpoint">POST <code>/api/publicar</code> - Publicar en redes</div>
            <div class="endpoint">POST <code>/api/buscar</code> - Buscar productos</div>
            <div class="endpoint">POST <code>/api/chatbot/mensaje</code> - Enviar mensaje a chatbot</div>
            <div class="endpoint">POST <code>/webhook/whatsapp</code> - Webhook de WhatsApp</div>
        </div>

        <div class="section">
            <h2>🧪 Tests Rápidos</h2>
            <button onclick="testHealth()">Test Health</button>
            <button onclick="testBuscar()">Test Búsqueda</button>
            <button onclick="testChatbot()">Test ChatBot</button>
        </div>

        <div id="resultado" style="background: #000; padding: 10px; margin-top: 10px; max-height: 300px; overflow: auto; display: none;"></div>
    </div>

    <script>
        function mostrar(data) {
            const elem = document.getElementById('resultado');
            elem.textContent = JSON.stringify(data, null, 2);
            elem.style.display = 'block';
        }

        async function testHealth() {
            const response = await fetch('/api/health');
            const data = await response.json();
            mostrar(data);
        }

        async function testBuscar() {
            const response = await fetch('/api/buscar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: 'Bumper deportivo Ford Mustang',
                    incluir_mercadolibre: true
                })
            });
            const data = await response.json();
            mostrar(data);
        }

        async function testChatbot() {
            const response = await fetch('/api/chatbot/mensaje', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    whatsapp: '+5215551234567',
                    mensaje: 'Hola, me interesa un bumper deportivo'
                })
            });
            const data = await response.json();
            mostrar(data);
        }
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


def inicializar_servicios():
    """Inicializa los servicios profesionales"""

    logger.info("🔧 Inicializando servicios...")

    # Cargar credenciales
    credenciales_redes = {}

    # TikTok
    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if tiktok_token:
        credenciales_redes[RedSocial.TIKTOK] = CredencialesRed(
            red=RedSocial.TIKTOK,
            access_token=tiktok_token,
            user_id=os.getenv("TIKTOK_USER_ID", ""),
            username=os.getenv("TIKTOK_USERNAME", "")
        )
        logger.info("✅ TikTok configurado")

    # Instagram
    instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if instagram_token:
        credenciales_redes[RedSocial.INSTAGRAM] = CredencialesRed(
            red=RedSocial.INSTAGRAM,
            access_token=instagram_token,
            user_id=os.getenv("INSTAGRAM_USER_ID", ""),
            username=os.getenv("INSTAGRAM_USERNAME", "")
        )
        logger.info("✅ Instagram configurado")

    # Inicializar publicador
    ServidorProfesionalHandler.publicador = PublicadorATFProfesional(credenciales_redes)
    logger.info("✅ Publicador inicializado")

    # Inicializar buscador
    ServidorProfesionalHandler.buscador = BuscadorWebProfesional()
    logger.info("✅ Buscador inicializado")

    # Inicializar chatbot
    ServidorProfesionalHandler.chatbot = ChatbotWAProfesional()
    logger.info("✅ ChatBot WhatsApp inicializado")

    logger.info("✅ Todos los servicios listos")


def iniciar_servidor(puerto: int = 8000):
    """Inicia el servidor HTTP"""

    inicializar_servicios()

    servidor = HTTPServer(('0.0.0.0', puerto), ServidorProfesionalHandler)

    logger.info(f"\n{'='*80}")
    logger.info(f"🌐 SERVIDOR PROFESIONAL INTEGRADO")
    logger.info(f"{'='*80}")
    logger.info(f"✅ Puerto: {puerto}")
    logger.info(f"✅ URL: http://localhost:{puerto}")
    logger.info(f"✅ API Docs: http://localhost:{puerto}")
    logger.info(f"{'='*80}\n")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 Servidor detenido")
        servidor.shutdown()


if __name__ == "__main__":
    iniciar_servidor(8000)
