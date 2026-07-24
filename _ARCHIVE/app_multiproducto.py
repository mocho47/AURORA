#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║              🎯 APP MULTI-PRODUCTO - VERSIÓN PARA VENTA 🎯                ║
║                                                                             ║
║  Aplicación genérica configurable para CUALQUIER negocio                   ║
║  • Marketing Digital 24/7 Autónomo                                         ║
║  • Publicador Multi-Red                                                    ║
║  • Búsqueda Web Real                                                       ║
║  • ChatBot WhatsApp                                                        ║
║  • Dashboard Analytics                                                     ║
║                                                                             ║
║  CONFIGURABLE PARA:                                                        ║
║  • ATF Retrofit                                                            ║
║  • MILENS                                                                  ║
║  • Cualquier otro negocio (e-commerce, servicios, etc)                    ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Agregar ruta de módulos
sys.path.insert(0, str(Path(__file__).parent))

from servidor_profesional_integrado import iniciar_servidor


class ConfiguracionNegocio:
    """Configuración del negocio/producto"""

    def __init__(self, archivo_config=None):
        self.archivo_config = archivo_config or "config_negocio.json"
        self.datos = self._cargar_configuracion()

    def _cargar_configuracion(self):
        """Carga configuración desde archivo"""
        if Path(self.archivo_config).exists():
            with open(self.archivo_config, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Configuración por defecto
        return {
            "nombre_negocio": "Mi Negocio",
            "descripcion": "Sistema de Marketing Digital",
            "puerto": 8000,
            "color_primario": "#00ff00",
            "redes_soportadas": ["TIKTOK", "INSTAGRAM", "YOUTUBE", "FACEBOOK"],
            "whatsapp_enabled": True,
            "buscador_enabled": True,
            "analytics_enabled": True
        }

    def guardar(self):
        """Guarda configuración en archivo"""
        with open(self.archivo_config, 'w', encoding='utf-8') as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    def obtener(self, clave, default=None):
        """Obtiene un valor de configuración"""
        return self.datos.get(clave, default)


def mostrar_menu_inicial():
    """Muestra menú inicial de configuración"""

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              🎯 APP MULTI-PRODUCTO - MARKETING DIGITAL 24/7                ║
║                                                                            ║
║  Selecciona cómo deseas usar esta aplicación:                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print("1️⃣  PARA VENDER (Versión genérica - sin personalización)")
    print("2️⃣  PARA ATF (Versión adaptada para ATF Retrofit)")
    print("3️⃣  PARA MILENS (Versión adaptada para MILENS)")
    print("4️⃣  PERSONALIZAR (Configura para tu propio negocio)")
    print("5️⃣  CONTINUAR (Usar configuración existente)")
    print("")

    opcion = input("Selecciona una opción (1-5): ").strip()
    return opcion


def configurar_para_venta():
    """Configura versión genérica para venta"""
    config = ConfiguracionNegocio()

    config.datos = {
        "nombre_negocio": "Marketing Digital Pro",
        "descripcion": "Sistema de Marketing Digital Automático",
        "tipo": "GENERICO_PARA_VENTA",
        "puerto": 8000,
        "version": "Pro",
        "redes_soportadas": ["TIKTOK", "INSTAGRAM", "YOUTUBE", "FACEBOOK"],
        "whatsapp_enabled": True,
        "buscador_enabled": True,
        "analytics_enabled": True,
        "fecha_configuracion": datetime.now().isoformat()
    }

    config.guardar()

    print("\n✅ Configurado para VENTA (versión genérica)")
    print("   Puerto: 8000")
    print("   Características completas habilitadas")

    return config.datos["puerto"]


def configurar_para_atf():
    """Configura versión para ATF"""
    config = ConfiguracionNegocio()

    config.datos = {
        "nombre_negocio": "ATF Retrofit",
        "descripcion": "Sistema de Marketing Digital para ATF Retrofit",
        "tipo": "ATF",
        "puerto": 8000,
        "version": "ATF v1.0",
        "logo": "🚗",
        "redes_soportadas": ["TIKTOK", "INSTAGRAM", "YOUTUBE", "FACEBOOK"],
        "whatsapp_enabled": True,
        "buscador_enabled": True,
        "analytics_enabled": True,
        "nicho": "Accesorios Retrofit para Autos",
        "productos": ["Bumper", "Spoiler", "Rines", "Suspension", "Escape"],
        "fecha_configuracion": datetime.now().isoformat()
    }

    config.guardar()

    print("\n✅ Configurado para ATF RETROFIT")
    print("   Puerto: 8000")
    print("   Productos: Bumper, Spoiler, Rines, Suspension, Escape")

    return config.datos["puerto"]


def configurar_para_milens():
    """Configura versión para MILENS"""
    config = ConfiguracionNegocio()

    config.datos = {
        "nombre_negocio": "MILENS",
        "descripcion": "Sistema de Marketing Digital para MILENS",
        "tipo": "MILENS",
        "puerto": 8001,
        "version": "MILENS v1.0",
        "logo": "💼",
        "redes_soportadas": ["TIKTOK", "INSTAGRAM", "YOUTUBE", "FACEBOOK"],
        "whatsapp_enabled": True,
        "buscador_enabled": True,
        "analytics_enabled": True,
        "nicho": "Servicios y Productos MILENS",
        "productos": ["Producto 1", "Producto 2", "Producto 3"],
        "fecha_configuracion": datetime.now().isoformat()
    }

    config.guardar()

    print("\n✅ Configurado para MILENS")
    print("   Puerto: 8001")
    print("   Características completas habilitadas")

    return config.datos["puerto"]


def configurar_personalizado():
    """Permite configuración personalizada"""
    config = ConfiguracionNegocio()

    print("\n🔧 CONFIGURACIÓN PERSONALIZADA")
    print("━" * 80)

    nombre = input("\n¿Nombre de tu negocio? (default: Mi Negocio): ").strip() or "Mi Negocio"
    descripcion = input("¿Descripción? (default: Sistema Marketing Digital): ").strip() or "Sistema Marketing Digital"
    puerto = input("¿Puerto? (default: 8000): ").strip() or "8000"

    config.datos = {
        "nombre_negocio": nombre,
        "descripcion": descripcion,
        "tipo": "PERSONALIZADO",
        "puerto": int(puerto),
        "version": "v1.0",
        "redes_soportadas": ["TIKTOK", "INSTAGRAM", "YOUTUBE", "FACEBOOK"],
        "whatsapp_enabled": True,
        "buscador_enabled": True,
        "analytics_enabled": True,
        "fecha_configuracion": datetime.now().isoformat()
    }

    config.guardar()

    print(f"\n✅ Configurado para {nombre}")
    print(f"   Puerto: {puerto}")

    return int(puerto)


def main():
    """Punto de entrada de la aplicación"""

    # Mostrar menú
    opcion = mostrar_menu_inicial()

    puerto = 8000

    if opcion == "1":
        puerto = configurar_para_venta()
    elif opcion == "2":
        puerto = configurar_para_atf()
    elif opcion == "3":
        puerto = configurar_para_milens()
    elif opcion == "4":
        puerto = configurar_personalizado()
    elif opcion == "5":
        config = ConfiguracionNegocio()
        puerto = config.obtener("puerto", 8000)
        print(f"\n✅ Usando configuración: {config.obtener('nombre_negocio')}")
    else:
        print("❌ Opción no válida. Usando configuración por defecto.")
        puerto = 8000

    # Mostrar inicio
    config = ConfiguracionNegocio()
    nombre = config.obtener("nombre_negocio", "Mi Negocio")

    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                   ✅ {nombre.center(66)} ✅
║                                                                            ║
║                    Sistema de Marketing Digital 24/7                       ║
║                                                                            ║
║  🔗 Publicador Multi-Red   |   🔍 Búsqueda Web Real                       ║
║  💬 ChatBot WhatsApp       |   📊 Analytics en Vivo                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print(f"🚀 Iniciando aplicación...")
    print(f"   Puerto: http://localhost:{puerto}")
    print(f"   Abriendo navegador automáticamente...\n")

    # Iniciar servidor
    iniciar_servidor(puerto=puerto)


if __name__ == "__main__":
    main()
