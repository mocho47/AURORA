# -*- coding: utf-8 -*-
"""AURORA · Generador de la versión DEMO (virgen, con licencia)

Pedido real de Anuar (2026-08-21): *"si o si requiero la version virgen sin
informacion mia el demo con licencia"* — una copia de AURORA que se pueda
entregar/distribuir sin ningún dato real de su negocio (clientes, precios,
catálogos, identidad), y que pida licencia para abrir.

Qué hace, en orden real:
  1. Copia todo el proyecto a una carpeta destino, EXCLUYENDO lo que nunca
     debe salir de aquí: base de datos, backups con fecha, artefactos de
     Git/Python, y — el punto central — los archivos de CONFIG que sí traen
     su información real (ver _CONFIG_PERSONAL abajo).
  2. Esos archivos de CONFIG no se copian vacíos y ya: se reemplazan por una
     versión de EJEMPLO real y funcional (mismo formato, datos de mentira
     obvios) para que la demo abra y funcione sin tronar por archivo
     faltante — sin arrastrar ni un dato suyo.
  3. Le mete el candado de licencia a la copia del arranque
     (`run_aurora.py`): sin clave válida, no levanta el servidor. Esto NO
     toca el run_aurora.py real de Anuar — solo el de la copia.
  4. Genera una licencia de prueba real (`LICENCIA/licencias.py`) para que
     la demo ya tenga con qué abrir desde el primer momento.

Lo que esto NO hace (dicho de frente, para no prometer de más):
  - No compila un instalador ni un .exe — deja una carpeta Python lista para
    correr con `python run_aurora.py`, igual que la real.
  - No es una versión para Android. Ver el aviso que imprime al final.

Correr:  python EMPAQUETADO/generar_version_demo.py [carpeta_destino]
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Carpetas/archivos que JAMÁS se copian a la demo — ni siquiera de ejemplo.
_EXCLUIR_SIEMPRE = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv",
    "DATOS", "LOGS", "logs", "_OBSOLETOS", "EMPAQUETADO",
    ".env", ".env.local",
}
_EXCLUIR_SUFIJOS = (".pyc", ".db", ".sqlite3", ".log")
_EXCLUIR_PATRON_BAK = "bak-"  # catalogo_maestro.bak-20260813-...json

# CONFIG/*.json que traen información REAL de Anuar — su negocio, sus
# clientes, sus precios, su identidad. Se reemplazan por un ejemplo.
_CONFIG_PERSONAL = {
    "aprendido_del_usuario.json": {},
    "catalogo_atf.json": {"productos": [
        {"nombre": "Ejemplo: Kit LED Demo", "precio": 999.0}]},
    "catalogo_maestro.json": {"productos": [
        {"nombre": "Ejemplo: Producto Demo", "categoria": "demo",
         "precio": 100.0}]},
    "catalogo_servicios.json": {"servicios": [
        {"nombre": "Ejemplo: Servicio Demo", "precio": 100.0}]},
    "contactos.json": {},
    "contenido_registro.json": [],
    "fichas_tecnicas.json": {"Ejemplo Demo": {
        "estado": "COMPLETA", "descripcion": "Ficha de ejemplo.",
        "precio": 100.0}},
    "identidad.json": {"negocio": "AURORA DEMO",
                       "descripcion": "Consola de negocio con lenguaje natural."},
    "maquinas.json": {"laser_demo": {"tipo": "láser CO2 (ejemplo)",
                                     "area_mm": [600, 400]}},
    "negocios.json": {"demo": {"nombre": "Negocio de Ejemplo"}},
    "operaciones.json": [],
    "precios_base.json": {"laser": {"materiales": [
        {"nombre": "MDF 2.7mm (Hoja) [EJEMPLO]", "precio_hoja": 100.0,
         "ancho": 122, "alto": 244}]}},
    "precios_vinil.json": {"vinil_textil": [
        {"desde_cm2": 0, "precio_cm2": 1.0}]},
    "procesos_observados.json": [],
    "proveedores.json": [],
    "servicios_atf.json": {},
    "usuarios.json": {"demo": {"rol": "dueño", "pin": "0000"}},
}


def _debe_excluir(rel: Path) -> bool:
    partes = rel.parts
    if partes and partes[0] in _EXCLUIR_SIEMPRE:
        return True
    nombre = rel.name
    if any(nombre.endswith(s) for s in _EXCLUIR_SUFIJOS):
        return True
    if _EXCLUIR_PATRON_BAK in nombre:
        return True
    return False


def _copiar_arbol(destino: Path) -> int:
    copiados = 0
    for origen in RAIZ.rglob("*"):
        if origen.is_dir():
            continue
        rel = origen.relative_to(RAIZ)
        if _debe_excluir(rel):
            continue
        # Los CONFIG/*.json de la lista personal se sustituyen aparte, no se
        # copian tal cual — se saltan aquí a propósito.
        if rel.parts[:1] == ("CONFIG",) and rel.name in _CONFIG_PERSONAL:
            continue
        dst = destino / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, dst)
        copiados += 1
    return copiados


def _escribir_config_ejemplo(destino: Path) -> None:
    carpeta = destino / "CONFIG"
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, contenido in _CONFIG_PERSONAL.items():
        (carpeta / nombre).write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2),
            encoding="utf-8")


def _meter_candado_licencia(destino: Path) -> None:
    """Le agrega la revisión de licencia al run_aurora.py de LA COPIA.
    El run_aurora.py real de Anuar no se toca — este archivo vive solo en
    destino/."""
    ruta = destino / "run_aurora.py"
    txt = ruta.read_text(encoding="utf-8")
    candado = '''def main() -> None:
    import uvicorn

    # ── CANDADO DE LICENCIA (solo en la versión demo/distribuible) ──
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from LICENCIA import licencias
    _lic = licencias.al_abrir("aurora_demo")
    if not _lic.get("puede_usarse") and _lic.get("status") == "SIN_LICENCIA":
        print("\\n" + _lic.get("mensaje", ""))
        _clave = input("Pega aquí tu clave de licencia y presiona Enter: ").strip()
        if _clave:
            _lic = licencias.guardar_local(_clave, "aurora_demo")
    if not _lic.get("puede_usarse"):
        print("\\n⛔ " + _lic.get("mensaje", "Esta copia necesita una licencia."))
        print("   Pide tu clave a quien te entregó AURORA.\\n")
        raise SystemExit(1)
    print("✅ " + _lic.get("mensaje", "Licencia activa."))
    # ── fin candado ──────────────────────────────────────────────────

    # Importar la app FastAPI (que ahora usa consciencia como router)
    from CORE.aurora_server import app'''
    original = '''def main() -> None:
    import uvicorn

    # Importar la app FastAPI (que ahora usa consciencia como router)
    from CORE.aurora_server import app'''
    if original not in txt:
        raise RuntimeError("run_aurora.py cambió de forma — no pude meter el candado "
                           "sin arriesgar romperlo. Revísalo a mano.")
    txt = txt.replace(original, candado)
    if "from pathlib import Path" not in txt:
        txt = "from pathlib import Path\n" + txt
    ruta.write_text(txt, encoding="utf-8")


def generar(destino: str = "") -> dict:
    dst = Path(destino) if destino else Path(r"C:\AURORA_DEMO")
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    n = _copiar_arbol(dst)
    _escribir_config_ejemplo(dst)
    _meter_candado_licencia(dst)

    from LICENCIA import licencias
    lic = licencias.generar("DEMO", "aurora_demo", meses=3,
                            notas="clave de prueba generada al empaquetar")
    # La clave se valida con HMAC contra LICENCIA_SECRETO — si la demo no
    # se lleva ESE mismo secreto, no puede validar ni esta clave ni ninguna
    # otra que se le entregue después. Se copia SOLO esa línea del .env
    # real, nunca las demás (esas sí son claves de negocio de Anuar).
    env_real = RAIZ / ".env"
    if env_real.exists():
        for linea in env_real.read_text(encoding="utf-8", errors="replace").splitlines():
            if linea.strip().startswith("LICENCIA_SECRETO="):
                (dst / ".env").write_text(linea.strip() + "\n", encoding="utf-8")
                break

    return {"status": "OK", "destino": str(dst), "archivos_copiados": n,
            "config_reemplazados": len(_CONFIG_PERSONAL),
            "licencia_demo": lic.get("clave"), "vence": lic.get("hasta")}


if __name__ == "__main__":
    r = generar(sys.argv[1] if len(sys.argv) > 1 else "")
    print(f"Demo lista en: {r['destino']}")
    print(f"Archivos copiados: {r['archivos_copiados']}")
    print(f"CONFIG reemplazados por ejemplo: {r['config_reemplazados']}")
    print(f"\nClave de licencia de prueba: {r['licencia_demo']}")
    print(f"Vence: {r['vence']}")
    print(f"\nPara correrla: cd {r['destino']} && python run_aurora.py")
