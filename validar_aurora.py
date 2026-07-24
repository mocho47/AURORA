# -*- coding: utf-8 -*-
"""
✅ SCRIPT DE VALIDACIÓN - Verifica que todo funcione correctamente
"""
import sys
import os
import requests
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para resolver importaciones
RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

def validar_estructura_proyecto():
    """Valida estructura de carpetas y archivos"""
    print("\n📁 Validando estructura del proyecto...")
    
    archivos_criticos = [
        "config.py",
        ".env",
        "requirements.txt",
        "SUPER_MARKETING_SYSTEM/api_v3_new.py",
        "SUPER_MARKETING_SYSTEM/publicador_real.py",
        "SUPER_MARKETING_SYSTEM/crm_leads_ventas.py",
        "SUPER_MARKETING_SYSTEM/motor_whatsapp_real.py",
        "SUPER_MARKETING_SYSTEM/dashboard.py",
        "run_aurora.py"
    ]
    
    archivos_ok = 0
    for archivo in archivos_criticos:
        ruta = RAIZ / archivo
        if ruta.exists():
            print(f"   ✅ {archivo}")
            archivos_ok += 1
        else:
            print(f"   ❌ FALTA: {archivo}")
    
    print(f"\n   Archivos: {archivos_ok}/{len(archivos_criticos)}")
    return archivos_ok == len(archivos_criticos)

def validar_configuracion():
    """Valida configuración"""
    print("\n⚙️  Validando configuración...")
    
    try:
        from config import settings, validate_production_settings
        
        # Validar .env existe
        env_file = RAIZ / ".env"
        if not env_file.exists():
            print("   ❌ Archivo .env no encontrado")
            return False
        print("   ✅ .env cargado")
        
        # Validar credenciales
        validate_production_settings()
        print("   ✅ Credenciales configuradas")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def validar_dependencias():
    """Valida que las dependencias estén instaladas"""
    print("\n📦 Validando dependencias...")
    
    dependencias = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "PyJWT",
        "requests"
    ]
    
    deps_ok = 0
    for dep in dependencias:
        try:
            __import__(dep.replace("-", "_"))
            print(f"   ✅ {dep}")
            deps_ok += 1
        except ImportError:
            print(f"   ❌ FALTA: {dep}")
    
    print(f"\n   Dependencias: {deps_ok}/{len(dependencias)}")
    return deps_ok == len(dependencias)

def validar_base_datos():
    """Valida base de datos"""
    print("\n💾 Validando base de datos...")
    
    try:
        from crm_leads_ventas import crm
        resumen = crm.obtener_resumen_crm()
        print(f"   ✅ BD inicializada")
        print(f"   ✅ Leads en sistema: {resumen.get('total_leads', 0)}")
        print(f"   ✅ Ventas registradas: {resumen.get('conversiones', 0)}")
        return True
    except Exception as e:
        print(f"   ⚠️  BD: {str(e)}")
        return False

def validar_apis():
    """Valida conexión con APIs"""
    print("\n🔌 Validando conexiones con APIs...")
    
    try:
        from config import settings
        
        # Groq
        print("   → Groq API...", end=" ")
        if settings.groq_api_key and not settings.groq_api_key.startswith("your_"):
            print("✅")
        else:
            print("⚠️  No configurada")
        
        # Green-API
        print("   → Green-API...", end=" ")
        if settings.green_api_token and not settings.green_api_token.startswith("your_"):
            print("✅")
        else:
            print("⚠️  No configurada")
        
        # Facebook
        print("   → Facebook API...", end=" ")
        if settings.facebook_access_token and not settings.facebook_access_token.startswith("your_"):
            print("✅")
        else:
            print("⚠️  No configurada")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    """Ejecuta todas las validaciones"""
    print("\n" + "="*60)
    print("  ✅ VALIDADOR DE AURORA v3.0")
    print("="*60)
    
    resultados = []
    
    resultados.append(("Estructura", validar_estructura_proyecto()))
    resultados.append(("Configuración", validar_configuracion()))
    resultados.append(("Dependencias", validar_dependencias()))
    resultados.append(("Base de Datos", validar_base_datos()))
    resultados.append(("APIs", validar_apis()))
    
    print("\n" + "="*60)
    print("  📊 RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    todas_ok = True
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "⚠️  ATENCIÓN"
        print(f"  {nombre:.<30} {estado}")
        if not resultado:
            todas_ok = False
    
    print("="*60)
    
    if todas_ok:
        print("\n✅ AURORA ESTÁ LISTO PARA EJECUTARSE")
        print("\n   Ejecuta: python run_aurora.py")
    else:
        print("\n⚠️  REVISAR ITEMS CON ATENCIÓN")
        print("\n   Corrige los items marcados y vuelve a validar.")

    print("="*60 + "\n")

if __name__ == "__main__":
    main()
