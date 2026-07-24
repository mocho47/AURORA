"""
AURORA v1 - Test Suite
Valida que todos los componentes estén conectados correctamente
"""
import asyncio
import sys
from pathlib import Path

# Add parent dirs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Test 1: Verificar que todos los módulos se importan correctamente"""
    print("\n[TEST 1] Importando modulos...")
    try:
        from config import DEFAULT_MOTOR, SDK_TIMEOUTS, SDK_MAX_TOKENS
        print("  [OK] config.py")

        from aurora_selector import get_selector, AuroraSelector
        print("  [OK] aurora_selector.py")

        from aurora_sdk_manager import call_sdk, call_with_fallback
        print("  [OK] aurora_sdk_manager.py")

        from aurora_registry import get_registry, MotorRegistry
        print("  [OK] aurora_registry.py")

        from aurora import get_aurora, AURORA
        print("  [OK] aurora.py")

        print("\n[PASS] Todos los modulos importados correctamente\n")
        return True
    except Exception as e:
        print(f"\n[FAIL] Error de importacion: {e}\n")
        return False


async def test_selector_initialization():
    """Test 2: Verificar que selector se inicializa correctamente"""
    print("[TEST 2] Inicializando selector...")
    try:
        from aurora_selector import get_selector
        selector = get_selector()
        print(f"  [+] Selector inicializado")
        print(f"  - Motores cargados: {len(selector.motores)}")
        print(f"  - Fallback chain: {selector.sdk_fallback_chain}")
        print("[PASS] Selector listo\n")
        return True
    except Exception as e:
        print(f"[FAIL] Error en selector: {e}\n")
        return False


async def test_registry_discovery():
    """Test 3: Verificar que registry descubre motores"""
    print("[TEST 3] Descubriendo motores...")
    try:
        from aurora_registry import get_registry
        registry = get_registry()
        status = registry.get_status()
        print(f"  [+] Registry inicializado")
        print(f"  - Total motores: {status['total_motors']}")
        print(f"  - Motores activos: {status['active_motors']}")
        print(f"  - Módulos cargados: {status['loaded_modules']}")

        motors = registry.list_motors()
        if motors:
            print(f"  - Motores encontrados:")
            for m in motors:
                status_icon = "[+]" if m["activo"] else "[-]"
                print(f"    {status_icon} {m['id']} ({m['sdk_preferido']})")

        print("[PASS] Discovery completado\n")
        return len(motors) > 0
    except Exception as e:
        print(f"[FAIL] Error en discovery: {e}\n")
        return False


async def test_aurora_initialization():
    """Test 4: Verificar que AURORA se inicializa correctamente"""
    print("[TEST 4] Inicializando AURORA...")
    try:
        from aurora import get_aurora
        aurora = get_aurora()
        print(f"  [+] AURORA inicializado")
        print(f"  - Selector: {aurora.selector.__class__.__name__}")
        print(f"  - Registry: {aurora.registry.__class__.__name__}")
        print(f"  - Historial dir: {aurora.historial_dir}")
        print("[PASS] AURORA listo\n")
        return True
    except Exception as e:
        print(f"[FAIL] Error en AURORA init: {e}\n")
        return False


async def test_simple_message():
    """Test 5: Procesar un mensaje simple"""
    print("[TEST 5] Procesando mensaje simple...")
    try:
        from aurora import get_aurora
        aurora = get_aurora()

        # Mensaje simple
        mensaje = "Hola, ¿cómo estás?"
        print(f"  Mensaje: '{mensaje}'")

        # Procesar (esto intentará llamar a SDK, que podría fallar sin keys)
        # Solo validamos que la función existe y puede ser llamada
        if hasattr(aurora, "procesar_mensaje"):
            print("  [+] Método procesar_mensaje existe")
            print("  [WARN]  Nota: SDK call requiere API keys configuradas")
        else:
            return False

        print("[PASS] Estructura de mensaje validada\n")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}\n")
        return False


async def test_env_vars():
    """Test 6: Verificar variables de entorno"""
    print("[TEST 6] Verificando configuración...")
    try:
        import os
        vars_check = {
            "CLAUDE_API_KEY": "Claude",
            "GROQ_API_KEY": "Groq",
            "ZAI_API_KEY": "Zai",
            "OLLAMA_BASE_URL": "Ollama",
        }

        configured = 0
        for var, name in vars_check.items():
            value = os.getenv(var)
            if value:
                print(f"  [+] {name}: configurado")
                configured += 1
            else:
                print(f"  [-] {name}: NO configurado")

        print(f"\n  Configurados: {configured}/{len(vars_check)}")
        if configured == 0:
            print("  [WARN]  Sin API keys: solo Ollama estará disponible")

        print("[PASS] Verificación completada\n")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}\n")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("  AURORA v1 - Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Selector Init", test_selector_initialization),
        ("Motor Discovery", test_registry_discovery),
        ("AURORA Init", test_aurora_initialization),
        ("Message Processing", test_simple_message),
        ("Environment Vars", test_env_vars),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] Test '{name}' crashed: {e}\n")
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        icon = "[PASS]" if result else "[FAIL]"
        print(f"{icon} {name}")

    print(f"\nResultado: {passed}/{total} tests pasados")

    if passed == total:
        print("\n[SUCCESS] AURORA está listo para usar!\n")
        return 0
    else:
        print("\n[WARN]  Algunos tests fallaron. Revisa los errores arriba.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
