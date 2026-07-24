# -*- coding: utf-8 -*-
"""
SCRIPT DE ARRANQUE AURORA - Inicializa todo el sistema
"""
import asyncio
import logging
import sys
import io
from pathlib import Path

# Forzar UTF-8 en la consola de Windows para evitar errores con emojis y caracteres especiales
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AURORA_STARTUP")

def verificar_puerto_libre(host: str, port: int) -> bool:
    """Verifica si el puerto está libre. Si no, avisa y sale."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((host, port)) == 0:
            logger.error(f"❌ Puerto {port} ya en uso. AURORA ya esta corriendo.")
            logger.error(f"   Abre http://localhost:{port}/api/docs en el navegador.")
            logger.error(f"   Para reiniciar, cierra la instancia anterior primero.")
            sys.exit(0)

# Agregar rutas
RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "SUPER_MARKETING_SYSTEM"))

async def validar_configuracion():
    """Valida que la configuración sea correcta"""
    logger.info("🔍 Validando configuración...")
    
    try:
        from config import validate_production_settings
        settings = validate_production_settings()
        logger.info("✅ Configuración validada")
        return True
    except Exception as e:
        logger.error(f"❌ Error en configuración: {str(e)}")
        return False

async def inicializar_base_datos():
    """Inicializa base de datos"""
    logger.info("💾 Inicializando base de datos...")
    
    try:
        from crm_leads_ventas import crm
        logger.info("✅ Base de datos CRM inicializada")
        return True
    except Exception as e:
        logger.error(f"❌ Error en BD: {str(e)}")
        return False

async def validar_apis():
    """Valida conexión con APIs externas"""
    logger.info("🔌 Validando conexiones con APIs...")
    
    try:
        import requests
        from config import settings
        
        # Validar Groq
        logger.info("   → Validando Groq API...")
        if settings.groq_api_key.startswith("your_"):
            logger.error("   ❌ Groq API key no configurada")
            return False
        logger.info("   ✅ Groq API: OK")
        
        # Validar Green-API
        logger.info("   → Validando Green-API (WhatsApp)...")
        if settings.green_api_token.startswith("your_"):
            logger.error("   ❌ Green-API token no configurada")
            return False
        logger.info("   ✅ Green-API: OK")
        
        # Validar Facebook (opcional - no bloquea el arranque si no está configurada)
        logger.info("   → Validando Facebook API...")
        if not settings.facebook_access_token or settings.facebook_access_token.startswith("your_"):
            logger.warning("   ⚠️  Facebook token no configurada (publicación manual deshabilitada)")
        else:
            logger.info("   ✅ Facebook API: OK")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error validando APIs: {str(e)}")
        return False

async def iniciar_servicios():
    """Inicia servicios en background"""
    logger.info("🔄 Iniciando servicios...")
    
    try:
        # Importar módulos
        from SUPER_MARKETING_SYSTEM.motor_whatsapp_real import motor_whatsapp
        from SUPER_MARKETING_SYSTEM.publicador_real import publicador
        
        # Iniciar WhatsApp listener en background
        logger.info("   → Iniciando WhatsApp listener...")
        asyncio.create_task(motor_whatsapp.escuchar_mensajes())
        logger.info("   ✅ WhatsApp listener activo")
        
        logger.info("✅ Todos los servicios iniciados")
        return True
    except Exception as e:
        logger.error(f"❌ Error iniciando servicios: {str(e)}")
        return False

async def iniciar_api():
    """Inicia API FastAPI"""
    logger.info("🌐 Iniciando API FastAPI...")
    
    try:
        import uvicorn
        from config import settings
        
        logger.info(f"   → Puerto: {settings.fastapi_port}")
        logger.info(f"   → Host: {settings.fastapi_host}")
        logger.info(f"   → Documentación: http://{settings.fastapi_host}:{settings.fastapi_port}/api/docs")
        
        # Uvicorn se ejecutará en main
        return True
    except Exception as e:
        logger.error(f"❌ Error en API: {str(e)}")
        return False

async def print_banner():
    """Imprime banner de bienvenida"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                   🚀 AURORA v3.0 - INICIANDO...                          ║
║                                                                           ║
║  Sistema Integral de Marketing IA para Redes Sociales y WhatsApp        ║
║  • Publicador Multi-Red (Facebook, Instagram, TikTok)                   ║
║  • CRM de Leads y Ventas                                                ║
║  • WhatsApp Business Automático                                         ║
║  • Dashboard de Control en Tiempo Real                                  ║
║  • IA Generativa (Groq)                                                 ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Función principal de arranque"""
    from config import settings as cfg
    verificar_puerto_libre(cfg.fastapi_host, cfg.fastapi_port)
    await print_banner()
    
    # Paso 1: Validar configuración
    if not await validar_configuracion():
        logger.error("❌ Aurora no pudo iniciarse - Validación fallida")
        return False
    
    # Paso 2: Inicializar BD
    if not await inicializar_base_datos():
        logger.error("❌ Aurora no pudo iniciarse - BD falló")
        return False
    
    # Paso 3: Validar APIs
    if not await validar_apis():
        logger.error("❌ Aurora no pudo iniciarse - APIs no conectadas")
        return False
    
    # Paso 4: Iniciar servicios
    if not await iniciar_servicios():
        logger.error("❌ Aurora no pudo iniciarse - Servicios fallaron")
        return False
    
    # Paso 5: API lista
    if not await iniciar_api():
        logger.error("❌ Aurora no pudo iniciarse - API falló")
        return False
    
    logger.info("")
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║  ✅ AURORA COMPLETAMENTE OPERATIVO                     ║")
    logger.info("║  🌐 Accede a: http://localhost:5000                   ║")
    logger.info("║  📚 Docs: http://localhost:5000/api/docs              ║")
    logger.info("║  💬 WhatsApp: ESCUCHANDO                              ║")
    logger.info("║  📤 Publicador: LISTO                                 ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    logger.info("")
    
    return True

async def run_uvicorn():
    """Inicia Uvicorn"""
    import uvicorn
    from config import settings
    
    config = uvicorn.Config(
        app="SUPER_MARKETING_SYSTEM.api_v3_new:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        log_level=getattr(settings, 'fastapi_log_level', 'info'),
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()

async def run_all():
    """Ejecuta todo junto"""
    startup_ok = await main()
    
    if startup_ok:
        # Iniciar Uvicorn
        await run_uvicorn()

if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("\n🛑 Aurora detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        sys.exit(1)
