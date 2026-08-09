import os
import asyncio
import time
import webbrowser
import subprocess
from typing import Optional

from voice import VoiceController, WhisperVoiceController
from trae_executor import ejecutar_comando_trae
import threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time, os, sqlite3


BASE = os.path.dirname(os.path.abspath(__file__))


def handle_voice_command(cmd: str):
    c = (cmd or "").lower().strip()
    if not c:
        return
    try:
        ejecutar_comando_trae(c)
    except Exception:
        pass

class _CmdHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path != '/status':
                self.send_response(404); self.end_headers(); return
            s = {
                'uptime': int(time.time()),
                'base': os.path.dirname(os.path.abspath(__file__)),
                'items': 0,
                'reminders': 0,
            }
            try:
                db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marketing.db')
                con = sqlite3.connect(db)
                cur = con.cursor()
                cur.execute('SELECT COUNT(*) FROM items')
                s['items'] = int(cur.fetchone()[0])
                cur.execute('SELECT COUNT(*) FROM reminders WHERE done=0')
                s['reminders'] = int(cur.fetchone()[0])
                con.close()
            except Exception:
                pass
            b = json.dumps(s).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        except Exception:
            try:
                self.send_response(500); self.end_headers()
            except Exception:
                pass
    def do_POST(self):
        try:
            if self.path != '/comando':
                self.send_response(404); self.end_headers(); return
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length).decode('utf-8') if length>0 else '{}'
            data = json.loads(body or '{}')
            texto = str(data.get('texto', '')).strip()
            if texto:
                try:
                    ejecutar_comando_trae(texto)
                except Exception:
                    pass
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception:
            try:
                self.send_response(500); self.end_headers()
            except Exception:
                pass

def _start_http_server():
    try:
        srv = HTTPServer(('127.0.0.1', 8765), _CmdHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except Exception:
        pass


async def main():
    try:
        vc = WhisperVoiceController(command_callback=handle_voice_command, wake_words=["nexus", "ion", "nexus escucha", "ey nexus"], model_name=os.getenv("WHISPER_MODEL", "tiny"))
    except Exception:
        vc = VoiceController(command_callback=handle_voice_command, wake_words=["nexus", "nexus escucha", "ion", "ion nexus"], model_name=os.getenv("WHISPER_MODEL", "tiny"), language="es", phrase_time_limit=60.0, timeout=60.0, mic_index=int(os.getenv("ION_MIC_INDEX", "1")), sample_rate=16000, chunk_size=2048)
    _start_http_server()
    await vc.astart()
    try:
        while True:
            await asyncio.sleep(0.2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())