# -*- coding: utf-8 -*-
"""
✅ TESTS PARA EL CRM DE LEADS Y VENTAS
"""
import unittest
import os
import sys
import sqlite3
from unittest.mock import patch, MagicMock

# Asegurarse de que el directorio raíz del proyecto esté en el sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SUPER_MARKETING_SYSTEM.crm_leads_ventas import CRMLeadsVentas, Lead, EstadoLead
from config import settings

class TestCRM(unittest.TestCase):
    """Tests para el sistema CRM"""

    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Usar una base de datos en memoria para los tests
        cls.test_db_path = ":memory:"
        settings.db_path = cls.test_db_path
        
        # Mockear el logger para evitar escrituras en consola/archivos
        cls.mock_logger = MagicMock()
        
        # Aplicar patches
        cls.logger_patcher = patch('SUPER_MARKETING_SYSTEM.crm_leads_ventas.logger', cls.mock_logger)
        
        cls.logger_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Limpieza final después de todos los tests"""
        cls.logger_patcher.stop()

    def setUp(self):
        """Configuración antes de cada test"""
        # Usar una base de datos en memoria para cada test
        self.crm = CRMLeadsVentas(db_path=":memory:")
        self.mock_logger.reset_mock()

    def tearDown(self):
        """Limpieza después de cada test"""
        self.crm.conn.close()

    def test_01_inicializacion_db(self):
        """Verifica que la base de datos y las tablas se creen correctamente"""
        # La inicialización ocurre en setUp
        self.mock_logger.info.assert_called_with("✅ Base de datos CRM inicializada")
        
        c = self.crm.conn.cursor()
        
        # Verificar existencia de tablas
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertIsNotNone(c.fetchone(), "La tabla 'leads' no fue creada.")
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interacciones'")
        self.assertIsNotNone(c.fetchone(), "La tabla 'interacciones' no fue creada.")
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
        self.assertIsNotNone(c.fetchone(), "La tabla 'ventas' no fue creada.")

    def test_02_crear_lead_exitoso(self):
        """Prueba la creación exitosa de un nuevo lead"""
        lead_data = Lead(
            nombre="Juan Test",
            email="juan.test@example.com",
            whatsapp="1234567890",
            producto_interes="Test Product",
            origen="test"
        )
        lead_id = self.crm.crear_lead(lead_data)
        
        self.assertIsInstance(lead_id, int)
        self.assertGreater(lead_id, 0)
        self.mock_logger.info.assert_called_with(f"✅ Lead creado: {lead_data.nombre} (ID: {lead_id})")

    def test_03_crear_lead_duplicado(self):
        """Prueba que no se pueda crear un lead con email o whatsapp duplicado"""
        lead_data = Lead(
            nombre="Jane Doe",
            email="jane.doe@example.com",
            whatsapp="0987654321",
            producto_interes="Test Product",
            origen="test"
        )
        self.crm.crear_lead(lead_data)
        
        # Intentar crear de nuevo con el mismo email
        lead_data_duplicado_email = Lead(
            nombre="Jane Doe Email",
            email="jane.doe@example.com",
            whatsapp="1111111111",
            producto_interes="Test Product",
            origen="test"
        )
        lead_id_duplicado = self.crm.crear_lead(lead_data_duplicado_email)
        
        self.assertEqual(lead_id_duplicado, -1)
        self.mock_logger.error.assert_called_with("❌ Error: Lead duplicado - UNIQUE constraint failed: leads.email")

        # Intentar crear de nuevo con el mismo whatsapp
        lead_data_duplicado_whatsapp = Lead(
            nombre="Jane Doe Whatsapp",
            email="jane.doe.ws@example.com",
            whatsapp="0987654321",
            producto_interes="Test Product",
            origen="test"
        )
        lead_id_duplicado_ws = self.crm.crear_lead(lead_data_duplicado_whatsapp)
        self.assertEqual(lead_id_duplicado_ws, -1)
        self.mock_logger.error.assert_called_with("❌ Error: Lead duplicado - UNIQUE constraint failed: leads.whatsapp")

    def test_04_obtener_lead(self):
        """Prueba que se pueda obtener un lead por su ID"""
        lead_data = Lead(nombre="Obtener Lead", email="obtener@example.com", whatsapp="1122334455", producto_interes="P1", origen="o1")
        lead_id = self.crm.crear_lead(lead_data)
        
        lead_obtenido = self.crm.obtener_lead(lead_id)
        
        self.assertIsNotNone(lead_obtenido, "El lead obtenido no debería ser None")
        self.assertEqual(lead_obtenido['id'], lead_id)
        self.assertEqual(lead_obtenido['nombre'], "Obtener Lead")
        self.assertEqual(lead_obtenido['producto_interes'], "P1")

    def test_05_actualizar_estado_lead(self):
        """Prueba la actualización del estado de un lead"""
        lead_data = Lead(nombre="Actualizar Lead", email="actualizar@example.com", whatsapp="5544332211", producto_interes="P2", origen="o2")
        lead_id = self.crm.crear_lead(lead_data)
        
        nuevo_estado = EstadoLead.CONTACTADO.value
        actualizacion_exitosa = self.crm.actualizar_estado_lead(lead_id, nuevo_estado)
        
        self.assertTrue(actualizacion_exitosa)
        
        lead_actualizado = self.crm.obtener_lead(lead_id)
        self.assertIsNotNone(lead_actualizado, "El lead actualizado no debería ser None")
        self.assertEqual(lead_actualizado['estado'], nuevo_estado)
        self.mock_logger.info.assert_called_with(f"✅ Lead {lead_id} actualizado a: {nuevo_estado}")

    def test_06_registrar_interaccion(self):
        """Prueba el registro de una interacción con un lead"""
        lead_data = Lead(nombre="Interaccion Lead", email="interaccion@example.com", whatsapp="6677889900", producto_interes="P3", origen="o3")
        lead_id = self.crm.crear_lead(lead_data)
        
        registro_exitoso = self.crm.registrar_interaccion(lead_id, "llamada", "Se presentó el producto", "interesado")
        
        self.assertTrue(registro_exitoso)
        self.mock_logger.info.assert_called_with(f"✅ Interacción registrada para lead {lead_id}")

    def test_07_registrar_venta(self):
        """Prueba el registro de una venta y la actualización del estado del lead"""
        lead_data = Lead(nombre="Venta Lead", email="venta@example.com", whatsapp="1020304050", producto_interes="P4", origen="o4")
        lead_id = self.crm.crear_lead(lead_data)
        
        monto_venta = 1500.0
        producto_venta = "Producto Vendido"
        
        venta_exitosa = self.crm.registrar_venta(lead_id, monto_venta, producto_venta)
        
        self.assertTrue(venta_exitosa)
        
        lead_actualizado = self.crm.obtener_lead(lead_id)
        self.assertEqual(
            
            ['estado'], EstadoLead.GANADO.value)
        
        self.mock_logger.info.assert_called_with(f"✅ Venta registrada: Lead {lead_id}, Monto: ${monto_venta}")

    def test_08_obtener_resumen_crm(self):
        """Prueba que el resumen del CRM devuelva datos correctos"""
        # Limpiar la base de datos para un resumen predecible
        self.setUp()

        # Crear datos de prueba
        self.crm.crear_lead(Lead(nombre="L1", email="l1@e.com", whatsapp="1", producto_interes="P", origen="o"))
        lead_id_2 = self.crm.crear_lead(Lead(nombre="L2", email="l2@e.com", whatsapp="2", producto_interes="P", origen="o"))
        self.crm.crear_lead(Lead(nombre="L3", email="l3@e.com", whatsapp="3", producto_interes="P", origen="o", estado=EstadoLead.CONTACTADO.value))
        
        self.crm.registrar_venta(lead_id_2, 100.0, "Producto Vendido")

        resumen = self.crm.obtener_resumen_crm()

        self.assertIsInstance(resumen, dict)
        self.assertEqual(resumen['total_leads'], 3)
        self.assertEqual(resumen['leads_por_estado']['nuevo'], 1)
        self.assertEqual(resumen['leads_por_estado']['contactado'], 1)
        self.assertEqual(resumen['leads_por_estado']['ganado'], 1)
        self.assertEqual(resumen['total_ventas'], "$100.00")
        self.assertEqual(resumen['conversiones'], 1)
        self.assertEqual(resumen['tasa_conversion'], "33.33%")

if __name__ == '__main__':
    # Configurar el runner de tests para que muestre más detalles
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
