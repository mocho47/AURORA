# -*- coding: utf-8 -*-
"""
💼 CRM DE LEADS Y VENTAS - Sistema completo de gestión de clientes
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from config import settings

logger = logging.getLogger("CRM")

class EstadoLead(Enum):
    NUEVO = "nuevo"
    CONTACTADO = "contactado"
    INTERESADO = "interesado"
    PROPUESTA_ENVIADA = "propuesta_enviada"
    NEGOCIANDO = "negociando"
    GANADO = "ganado"
    PERDIDO = "perdido"

@dataclass
class Lead:
    nombre: str
    email: str
    whatsapp: str
    producto_interes: str
    origen: str
    estado: str = EstadoLead.NUEVO.value
    valor_potencial: float = 0.0
    notas: str = ""

class CRMLeadsVentas:
    """Sistema CRM de gestión de leads y ventas"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or settings.db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._inicializar_db()
    
    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def _inicializar_db(self):
        """Inicializa tablas de CRM"""
        try:
            c = self.conn.cursor()
            
            # Tabla de leads
            c.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT UNIQUE,
                    whatsapp TEXT UNIQUE,
                    producto_interes TEXT,
                    origen TEXT,
                    estado TEXT DEFAULT 'nuevo',
                    valor_potencial REAL DEFAULT 0.0,
                    notas TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_conversion TIMESTAMP
                )
            ''')
            
            # Tabla de interacciones
            c.execute('''
                CREATE TABLE IF NOT EXISTS interacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    tipo TEXT,
                    descripcion TEXT,
                    resultado TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            ''')
            
            # Tabla de ventas
            c.execute('''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    monto REAL,
                    producto TEXT,
                    estado_pago TEXT,
                    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_pago TIMESTAMP,
                    notas TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            ''')
            
            self.conn.commit()
            logger.info("✅ Base de datos CRM inicializada")
        except Exception as e:
            logger.error(f"❌ Error inicializando la base de datos CRM: {str(e)}")

    def crear_lead(self, lead: Lead) -> int:
        """Crea un nuevo lead"""
        try:
            c = self.conn.cursor()
            
            c.execute('''
                INSERT INTO leads (nombre, email, whatsapp, producto_interes, origen, estado, valor_potencial, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (lead.nombre, lead.email, lead.whatsapp, lead.producto_interes, 
                  lead.origen, lead.estado, lead.valor_potencial, lead.notas))
            
            self.conn.commit()
            lead_id = c.lastrowid
            
            logger.info(f"✅ Lead creado: {lead.nombre} (ID: {lead_id})")
            return lead_id
        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Error: Lead duplicado - {str(e)}")
            return -1
        except Exception as e:
            logger.error(f"❌ Error creando lead: {str(e)}")
            return -1
    
    def obtener_lead(self, lead_id: int) -> Optional[Dict]:
        """Obtiene detalles de un lead"""
        try:
            c = self.conn.cursor()
            c.row_factory = sqlite3.Row
            
            c.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
            resultado = c.fetchone()
            
            if resultado:
                return dict(resultado)
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo lead: {str(e)}")
            return None
    
    def actualizar_estado_lead(self, lead_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un lead"""
        try:
            c = self.conn.cursor()
            
            c.execute('''
                UPDATE leads SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (nuevo_estado, lead_id))
            
            self.conn.commit()
            
            logger.info(f"✅ Lead {lead_id} actualizado a: {nuevo_estado}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando lead: {str(e)}")
            return False
    
    def registrar_interaccion(self, lead_id: int, tipo: str, descripcion: str, resultado: str) -> bool:
        """Registra una interacción con el lead"""
        try:
            c = self.conn.cursor()
            
            c.execute('''
                INSERT INTO interacciones (lead_id, tipo, descripcion, resultado)
                VALUES (?, ?, ?, ?)
            ''', (lead_id, tipo, descripcion, resultado))
            
            self.conn.commit()
            
            logger.info(f"✅ Interacción registrada para lead {lead_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error registrando interacción: {str(e)}")
            return False
    
    def registrar_venta(self, lead_id: int, monto: float, producto: str) -> bool:
        """Registra una venta"""
        try:
            c = self.conn.cursor()
            
            # Crear venta
            c.execute('''
                INSERT INTO ventas (lead_id, monto, producto, estado_pago)
                VALUES (?, ?, ?, 'pendiente')
            ''', (lead_id, monto, producto))
            
            # Actualizar estado del lead
            c.execute('''
                UPDATE leads SET estado = ?, fecha_conversion = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (EstadoLead.GANADO.value, lead_id))
            
            self.conn.commit()
            
            logger.info(f"✅ Venta registrada: Lead {lead_id}, Monto: ${monto}")
            return True
        except Exception as e:
            logger.error(f"❌ Error registrando venta: {str(e)}")
            return False
    
    def obtener_resumen_crm(self) -> Dict:
        """Obtiene resumen del CRM"""
        try:
            c = self.conn.cursor()
            
            # Total de leads
            c.execute('SELECT COUNT(*) FROM leads')
            total_leads = c.fetchone()[0]
            
            # Leads por estado
            c.execute('''
                SELECT estado, COUNT(*) FROM leads GROUP BY estado
            ''')
            leads_por_estado = {row[0]: row[1] for row in c.fetchall()}
            
            # Ventas totales
            c.execute('SELECT SUM(monto) FROM ventas')
            ventas_totales = c.fetchone()[0] or 0.0
            
            # Conversiones
            c.execute('SELECT COUNT(*) FROM ventas')
            total_conversiones = c.fetchone()[0]
            
            tasa_conversion = (total_conversiones / total_leads * 100) if total_leads > 0 else 0
            
            return {
                "total_leads": total_leads,
                "leads_por_estado": leads_por_estado,
                "total_ventas": f"${ventas_totales:.2f}",
                "conversiones": total_conversiones,
                "tasa_conversion": f"{tasa_conversion:.2f}%",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen: {str(e)}")
            return {}

crm = CRMLeadsVentas()
