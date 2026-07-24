"""
AURORA Database Manager - SQLite WAL con índices
Maneja: Conversaciones, Usuarios, Cotizaciones, Historial
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class AuroraDB:
    """Gestor profesional de base de datos SQLite"""

    def __init__(self, db_path: str = "aurora.db"):
        self.db_path = Path(db_path)
        self.init()

    def init(self):
        """Inicializa base de datos con WAL y índices"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        # Enable WAL mode (mejor para concurrencia)
        c.execute("PRAGMA journal_mode=WAL")

        # Conversaciones
        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            rol TEXT,
            mensaje TEXT NOT NULL,
            respuesta TEXT,
            situacion TEXT,
            sdk TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Índices para conversaciones
        c.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_conversations_situacion ON conversations(situacion)')

        # Usuarios
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            rol TEXT,
            nombre TEXT,
            email TEXT,
            perfil_psicologico TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Índices para usuarios
        c.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol)')

        # Cotizaciones
        c.execute('''CREATE TABLE IF NOT EXISTS cotizaciones (
            id TEXT PRIMARY KEY,
            usuario_id TEXT,
            productos TEXT,
            total REAL,
            margen REAL,
            margen_porcentaje REAL,
            estado TEXT DEFAULT 'pendiente',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )''')

        # Índices para cotizaciones
        c.execute('CREATE INDEX IF NOT EXISTS idx_cotizaciones_usuario ON cotizaciones(usuario_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_cotizaciones_timestamp ON cotizaciones(timestamp)')

        # Alertas de riesgo (crisis protocol)
        c.execute('''CREATE TABLE IF NOT EXISTS alertas_riesgo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            nivel INTEGER,
            mensaje TEXT,
            accion_tomada TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Índices para alertas
        c.execute('CREATE INDEX IF NOT EXISTS idx_alertas_user ON alertas_riesgo(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_alertas_nivel ON alertas_riesgo(nivel)')

        conn.commit()
        conn.close()

    def guardar_chat(self, user_id: str, rol: str, mensaje: str, respuesta: str,
                     situacion: str, sdk: str = "local") -> int:
        """Guarda conversación en DB"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute('''INSERT INTO conversations
                   (user_id, rol, mensaje, respuesta, situacion, sdk)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, rol, mensaje, respuesta, situacion, sdk))

        conn.commit()
        chat_id = c.lastrowid
        conn.close()

        return chat_id

    def obtener_historial(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Obtiene historial de conversaciones del usuario"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute('''SELECT id, mensaje, respuesta, situacion, timestamp
                   FROM conversations
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?''', (user_id, limit))

        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "mensaje": row[1],
                "respuesta": row[2],
                "situacion": row[3],
                "timestamp": row[4]
            }
            for row in rows
        ]

    def crear_usuario(self, user_id: str, rol: str, nombre: str = "", email: str = "") -> bool:
        """Crea nuevo usuario"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()

            c.execute('''INSERT OR IGNORE INTO usuarios
                       (id, rol, nombre, email)
                       VALUES (?, ?, ?, ?)''',
                    (user_id, rol, nombre, email))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False

    def obtener_usuario(self, user_id: str) -> Optional[Dict]:
        """Obtiene datos del usuario"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute('''SELECT id, rol, nombre, email, created_at
                   FROM usuarios WHERE id = ?''', (user_id,))

        row = c.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "rol": row[1],
                "nombre": row[2],
                "email": row[3],
                "created_at": row[4]
            }

        return None

    def guardar_cotizacion(self, id: str, usuario_id: str, productos: str,
                          total: float, margen: float, margen_porcentaje: float) -> bool:
        """Guarda cotización"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()

            c.execute('''INSERT INTO cotizaciones
                       (id, usuario_id, productos, total, margen, margen_porcentaje)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (id, usuario_id, productos, total, margen, margen_porcentaje))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error guardando cotización: {e}")
            return False

    def obtener_cotizaciones(self, usuario_id: str) -> List[Dict]:
        """Obtiene cotizaciones del usuario"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute('''SELECT id, productos, total, margen, estado, timestamp
                   FROM cotizaciones
                   WHERE usuario_id = ?
                   ORDER BY timestamp DESC''', (usuario_id,))

        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "productos": row[1],
                "total": row[2],
                "margen": row[3],
                "estado": row[4],
                "timestamp": row[5]
            }
            for row in rows
        ]

    def guardar_alerta_riesgo(self, user_id: str, nivel: int, mensaje: str,
                             accion_tomada: str = "") -> bool:
        """Guarda alerta de riesgo (crisis protocol)"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()

            c.execute('''INSERT INTO alertas_riesgo
                       (user_id, nivel, mensaje, accion_tomada)
                       VALUES (?, ?, ?, ?)''',
                    (user_id, nivel, mensaje, accion_tomada))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error guardando alerta: {e}")
            return False

    def obtener_alertas(self, user_id: str) -> List[Dict]:
        """Obtiene alertas de riesgo del usuario"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute('''SELECT id, nivel, mensaje, accion_tomada, timestamp
                   FROM alertas_riesgo
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT 10''', (user_id,))

        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "nivel": row[1],
                "mensaje": row[2],
                "accion": row[3],
                "timestamp": row[4]
            }
            for row in rows
        ]

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        # Total conversaciones
        c.execute('SELECT COUNT(*) FROM conversations')
        total_chats = c.fetchone()[0]

        # Total usuarios
        c.execute('SELECT COUNT(*) FROM usuarios')
        total_usuarios = c.fetchone()[0]

        # Total cotizaciones
        c.execute('SELECT COUNT(*) FROM cotizaciones')
        total_cotizaciones = c.fetchone()[0]

        # Ingresos
        c.execute('SELECT SUM(margen) FROM cotizaciones')
        ingresos = c.fetchone()[0] or 0

        # Alertas activas
        c.execute('SELECT COUNT(*) FROM alertas_riesgo WHERE nivel >= 4')
        alertas_criticas = c.fetchone()[0]

        conn.close()

        return {
            "total_conversaciones": total_chats,
            "total_usuarios": total_usuarios,
            "total_cotizaciones": total_cotizaciones,
            "ingresos_totales": round(ingresos, 2),
            "alertas_criticas": alertas_criticas
        }

    def cleanup_old_data(self, dias: int = 90) -> int:
        """Limpia datos antiguos (para mantenimiento)"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()

        c.execute(f'''DELETE FROM conversations
                   WHERE timestamp < datetime('now', '-{dias} days')''')

        deleted = c.rowcount

        conn.commit()
        conn.close()

        return deleted
