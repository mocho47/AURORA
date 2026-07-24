"""
AURORA v2 - Configuración Integrada
Lee API Keys existentes + Repositorio GitHub + Sincronización
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional

# ==================== PATHS ====================
BASE_DIR = Path(__file__).parent.parent
CORE_DIR = BASE_DIR / "CORE"
CEREBRO_DIR = BASE_DIR / "CEREBRO"
DATA_DIR = BASE_DIR / "DATA"
MEMORIA_DIR = BASE_DIR / "MEMORIA"
SYNC_DIR = BASE_DIR / "SYNC"

# ==================== API KEYS (LEE DEL AMBIENTE) ====================
class APIKeys:
    """Carga API Keys desde variables de entorno (ya configuradas)"""

    @staticmethod
    def obtener():
        """Obtiene todas las API Keys configuradas"""
        return {
            "CLAUDE": os.getenv("CLAUDE_API_KEY", ""),
            "GROQ": os.getenv("GROQ_API_KEY", ""),
            "ZAI": os.getenv("ZAI_API_KEY", ""),
            "OLLAMA_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "GREEN_API_ID": os.getenv("GREEN_API_INSTANCE", ""),
            "GREEN_API_TOKEN": os.getenv("GREEN_API_TOKEN", ""),
        }

    @staticmethod
    def validar():
        """Valida qué APIs están disponibles"""
        keys = APIKeys.obtener()
        disponibles = {
            "claude": bool(keys["CLAUDE"]),
            "groq": bool(keys["GROQ"]),
            "zai": bool(keys["ZAI"]),
            "ollama": True,  # Siempre disponible (local)
            "green_api": bool(keys["GREEN_API_ID"] and keys["GREEN_API_TOKEN"]),
        }
        return disponibles

    @staticmethod
    def reportar():
        """Reporta qué APIs están configuradas (sin mostrar keys)"""
        disponibles = APIKeys.validar()
        print("\n[CONFIG] APIs Disponibles:")
        for api, disponible in disponibles.items():
            estado = "✓ Configurada" if disponible else "✗ No configurada"
            print(f"  {api.upper()}: {estado}")
        print()

# ==================== REPOSITORIO GITHUB ====================
class RepositorioGitHub:
    """Lee configuración del repositorio GitHub existente"""

    @staticmethod
    def obtener_config():
        """Lee config de GitHub si existe"""
        github_config_paths = [
            Path.home() / ".github_config.json",
            BASE_DIR / "GITHUB_CONFIG.json",
            CORE_DIR / ".github_config.json",
        ]

        for path in github_config_paths:
            if path.exists():
                with open(path) as f:
                    return json.load(f)

        # Config por defecto
        return {
            "repositorio": "mocho47/aurora-v2",
            "rama": "main",
            "url": "https://github.com/mocho47/aurora-v2.git",
            "pull_request": False,
            "auto_sync": True
        }

    @staticmethod
    def get_repo_url():
        """Obtiene URL del repositorio"""
        config = RepositorioGitHub.obtener_config()
        return config.get("url", "https://github.com/mocho47/aurora-v2.git")

    @staticmethod
    def get_repo_nombre():
        """Obtiene nombre del repositorio"""
        config = RepositorioGitHub.obtener_config()
        return config.get("repositorio", "mocho47/aurora-v2")

# ==================== SINCRONIZACIÓN ====================
class ConfigSync:
    """Configuración de sincronización entre PCs"""

    @staticmethod
    def cargar():
        """Carga configuración de sincronización"""
        sync_config_path = SYNC_DIR / "sync_config.json"

        if sync_config_path.exists():
            with open(sync_config_path) as f:
                return json.load(f)

        # Config por defecto
        return {
            "tu_pc": {
                "nombre": "Tu PC",
                "ip": os.getenv("SYNC_TU_PC_IP", "192.168.1.100"),
                "puerto": 8000,
            },
            "pc_esposa": {
                "nombre": "PC Esposa",
                "ip": os.getenv("SYNC_PC_ESPOSA_IP", "192.168.1.101"),
                "puerto": 8000,
            },
            "intervalo_sync": 5,
            "modo": "bidireccional",
        }

# ==================== SDKS ====================
class SDKConfig:
    """Configuración de SDKs con prioridades"""

    # Orden de preferencia (por capacidad + velocidad + costo)
    PRIORIDAD_SDK = {
        "razonamiento_profundo": ["claude", "groq", "zai", "ollama"],
        "velocidad": ["groq", "zai", "claude", "ollama"],
        "economia": ["groq", "zai", "ollama", "claude"],
        "offline": ["ollama"],
        "default": ["groq", "claude", "zai", "ollama"],
    }

    @staticmethod
    def obtener_sdk_optimo(tipo: str = "default"):
        """Obtiene SDK óptimo según tipo de tarea"""
        disponibles = APIKeys.validar()
        preferidos = SDKConfig.PRIORIDAD_SDK.get(tipo, SDKConfig.PRIORIDAD_SDK["default"])

        for sdk in preferidos:
            if disponibles.get(sdk):
                return sdk

        # Fallback a Ollama (siempre disponible)
        return "ollama"

    @staticmethod
    def get_timeouts():
        """Timeouts por SDK"""
        return {
            "claude": 15.0,
            "groq": 12.0,
            "zai": 8.0,
            "ollama": 90.0,
        }

    @staticmethod
    def get_max_tokens():
        """Máx tokens por SDK"""
        return {
            "claude": 4096,
            "groq": 500,
            "zai": 400,
            "ollama": 512,
        }

# ==================== MOTORES ====================
class MotoresConfig:
    """Configuración de los 17 motores"""

    MOTORES = {
        "m01_conversor": {
            "nombre": "Conversor Universal",
            "descripcion": "Archivos → formato correcto",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m02_cotiz_sub": {
            "nombre": "Cotizador Sublimación",
            "descripcion": "Producto + cantidad → precio",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m03_preparador": {
            "nombre": "Preparador Archivo",
            "descripcion": "DPI, color, sangrado",
            "sdk_preferido": "ollama",
            "activo": True,
        },
        "m04_cotiz_laser": {
            "nombre": "Cotizador Láser",
            "descripcion": "Material + dimensiones → precio",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m05_cajas_dxf": {
            "nombre": "Generador Cajas DXF",
            "descripcion": "Medidas → archivo DXF",
            "sdk_preferido": "ollama",
            "activo": True,
        },
        "m06_vectorizador": {
            "nombre": "Vectorizador",
            "descripcion": "Raster → vectorial",
            "sdk_preferido": "ollama",
            "activo": True,
        },
        "m07_cotiz_atf": {
            "nombre": "Cotizador ATF",
            "descripcion": "Aozoom X1-X7 → precio",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m08_agenda_atf": {
            "nombre": "Agenda ATF",
            "descripcion": "Citas, instaladores",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m09_material_atf": {
            "nombre": "Material ATF",
            "descripcion": "Tarjetas, llaveros, portadas",
            "sdk_preferido": "claude",
            "activo": True,
        },
        "m10_directorio": {
            "nombre": "Directorio Instaladores",
            "descripcion": "Quién instala dónde",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m11_catalogo": {
            "nombre": "Catálogo Servicios",
            "descripcion": "Precios y disponibilidad",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m12_pedidos_clientes": {
            "nombre": "Pedidos + Clientes",
            "descripcion": "CRM + órdenes",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m13_detector": {
            "nombre": "Detector Oportunidades",
            "descripcion": "Clientes inactivos, leads fríos",
            "sdk_preferido": "groq",
            "activo": True,
        },
        "m14_mensajes_wa": {
            "nombre": "Generador Mensajes WA",
            "descripcion": "Cliente + producto → mensaje",
            "sdk_preferido": "claude",
            "activo": True,
        },
        "m15_redes": {
            "nombre": "Publicaciones Redes",
            "descripcion": "Instagram, TikTok, Facebook",
            "sdk_preferido": "claude",
            "activo": True,
        },
        "m16_pipeline": {
            "nombre": "Pipeline Ventas",
            "descripcion": "Lead → venta → entrega",
            "sdk_preferido": "groq",
            "activo": True,
        },
    }

    @staticmethod
    def obtener_motores_activos():
        """Retorna solo motores activos"""
        return {k: v for k, v in MotoresConfig.MOTORES.items() if v["activo"]}

# ==================== NEGOCIOS ====================
class NegociosConfig:
    """Configuración integrada de los 4 negocios"""

    NEGOCIOS = {
        "ATF": {
            "nombre": "Retrofit Faros",
            "descripcion": "Instalación bi-LED Aozoom",
            "modulos": ["m07_cotiz_atf", "m08_agenda_atf", "m09_material_atf"],
            "prioridad": 1,  # Principal
            "motores_relacionados": ["m14_mensajes_wa", "m15_redes", "m16_pipeline"],
        },
        "MILENS": {
            "nombre": "Sublimación + Láser",
            "descripcion": "Productos personalizados",
            "modulos": ["m01_conversor", "m02_cotiz_sub", "m03_preparador", "m04_cotiz_laser", "m05_cajas_dxf", "m06_vectorizador"],
            "prioridad": 1,  # Principal
            "motores_relacionados": ["m14_mensajes_wa", "m15_redes", "m16_pipeline"],
        },
        "FORJA": {
            "nombre": "Sistema de Órdenes",
            "descripcion": "Gestión de pedidos centralizada",
            "modulos": ["m12_pedidos_clientes"],
            "prioridad": 2,  # Secundario
            "motores_relacionados": ["m12_pedidos_clientes", "m16_pipeline"],
        },
        "TEENS": {
            "nombre": "Coaching Familiar",
            "descripcion": "Panel padres + adolescentes",
            "modulos": [],
            "prioridad": 2,  # Secundario
            "motores_relacionados": ["m14_mensajes_wa"],
            "nota": "Lead generation para ATF (parents → customers)"
        },
    }

    @staticmethod
    def obtener_negocios_principales():
        """Retorna negocios con prioridad 1 (ATF + MILENS)"""
        return {k: v for k, v in NegociosConfig.NEGOCIOS.items() if v["prioridad"] == 1}

# ==================== INICIALIZACIÓN ====================
def inicializar_config():
    """Inicializa toda la configuración"""

    print("\n" + "="*70)
    print("AURORA v2 - CONFIGURACIÓN INTEGRADA")
    print("="*70)

    # 1. Verificar API Keys
    print("\n[1/4] Verificando API Keys...")
    APIKeys.reportar()

    # 2. Repositorio GitHub
    print("[2/4] Configuración de repositorio GitHub:")
    repo = RepositorioGitHub.obtener_config()
    print(f"  Repositorio: {RepositorioGitHub.get_repo_nombre()}")
    print(f"  URL: {RepositorioGitHub.get_repo_url()}")
    print(f"  Rama: {repo.get('rama', 'main')}")

    # 3. Sincronización
    print("\n[3/4] Configuración de sincronización:")
    sync = ConfigSync.cargar()
    print(f"  Tu PC: {sync['tu_pc']['nombre']} ({sync['tu_pc']['ip']})")
    print(f"  PC Esposa: {sync['pc_esposa']['nombre']} ({sync['pc_esposa']['ip']})")
    print(f"  Intervalo sync: {sync['intervalo_sync']}s")

    # 4. Motores
    print("\n[4/4] Motores configurados:")
    motores = MotoresConfig.obtener_motores_activos()
    print(f"  Total activos: {len(motores)}/17")
    print(f"  Negocios principales: {len(NegociosConfig.obtener_negocios_principales())}")

    print("\n" + "="*70)
    print("✓ AURORA v2 LISTO PARA OPERACIÓN")
    print("="*70 + "\n")

    return {
        "api_keys": APIKeys.obtener(),
        "github": repo,
        "sync": sync,
        "motores": motores,
        "negocios": NegociosConfig.NEGOCIOS,
    }

# Inicializar al importar
if __name__ == "__main__":
    config = inicializar_config()
