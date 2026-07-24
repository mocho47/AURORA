"""
AURORA — AUDITORIA COMPLETA PRE-LANZAMIENTO
Escanea todo el proyecto, detecta problemas y genera reporte.
"""
import os, sys, importlib.util, sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

CARPETAS_SISTEMA = {
    'CORE', 'CEREBRO', 'MEMORIA', 'MOTORES', 'INTEGRACIONES',
    'ORACLE', 'VENDEDOR', 'MARKETING', 'PUBLICADOR', 'VOZ',
    'CONFIG', 'SHARED', 'SDKS', 'TEMPLATES', 'DASHBOARDS',
    'AUTH', 'MODULOS', 'SUBLIMACION', 'TALLER', 'EDITOR',
    'SYNC', 'ORACLE', 'REPARADOR', 'REPORTES', 'PROGRAMADOR',
    'COMANDOS', 'PROMPTS_MAESTROS', 'VENDEDOR', 'ACCESOS',
    'SUPER_MARKETING_SYSTEM', 'CONTENIDO', 'AUDITORIAS',
    'AURORA', 'MOTORES',
}

IGNORAR = {
    '_ARCHIVE', '.git', '__pycache__', 'SETUP', 'apps', 'TOOLS',
    'annotated_types','anyio','certifi','cffi','cryptography','dateutil',
    'gotrue','h11','h2','hpack','httpcore','httpx','hyperframe','idna',
    'jwt','multidict','packaging','postgrest','propcache','pycparser',
    'pydantic','pydantic_core','realtime','sniffio','storage3','strenum',
    'supabase','websockets','yarl','platform-tools',
}

resultados = {
    'estructura': {},
    'duplicados': [],
    'simulados': [],
    'rotos': [],
    'obsoletos': [],
    'dbs': [],
    'raiz_suelta': [],
}

# ── 1. ESCANEAR ESTRUCTURA ──────────────────────────────────────────
print("=" * 70)
print("AURORA — AUDITORÍA COMPLETA PRE-LANZAMIENTO")
print("=" * 70)
print()

print("── 1. ESTRUCTURA DE CARPETAS ──────────────────────────────────")
for item in sorted(ROOT.iterdir()):
    if item.name in IGNORAR or item.name.startswith('.'):
        continue
    if item.is_dir():
        pyfiles = [f for f in item.rglob('*.py') if '__pycache__' not in str(f)]
        resultados['estructura'][item.name] = [str(f.relative_to(item)) for f in pyfiles]
        print(f"  {item.name}/  → {len(pyfiles)} archivos .py")
    elif item.is_file() and item.suffix == '.py':
        resultados['raiz_suelta'].append(item.name)

print()
print("── 2. ARCHIVOS .PY EN RAÍZ (potencialmente obsoletos) ─────────")
raiz_py = list(ROOT.glob('*.py'))
for f in sorted(raiz_py):
    size = f.stat().st_size
    print(f"  {f.name}  ({size:,}b)")

print()
print("── 3. ARCHIVOS .BAT / .PS1 en RAÍZ ────────────────────────────")
raiz_scripts = list(ROOT.glob('*.bat')) + list(ROOT.glob('*.ps1'))
for f in sorted(raiz_scripts):
    print(f"  {f.name}")

print()
print("── 4. ARCHIVOS EXTRAÑOS EN RAÍZ ────────────────────────────────")
for f in sorted(ROOT.iterdir()):
    if f.is_file() and f.suffix not in {'.py','.bat','.ps1','.md','.txt','.json',
                                          '.gitignore','.example','.tar','.gz','.zip',
                                          '.db','.db-wal','.db-shm'}:
        print(f"  EXTRAÑO: {f.name}")
    # nombres con espacios o chars raros
    if f.is_file() and any(c in f.name for c in ['@', ' ', '[', ']']):
        print(f"  NOMBRE RARO: {f.name!r}")

print()
print("── 5. MOTORES: REAL vs SIMULADO ────────────────────────────────")
SIMULADO_TRIGGERS = ['SIMULADO', 'PENDIENTE = True', 'Template response',
                     'def solution():\n    pass', '$XXX', 'PLACEHOLDER']
REAL_TRIGGERS = ['AsyncGroq', 'groq.chat.completions.create']

for f in sorted((ROOT / 'MOTORES').glob('motor_*.py')):
    src = open(f, encoding='utf-8').read()
    simulado = any(t in src for t in SIMULADO_TRIGGERS)
    real = any(t in src for t in REAL_TRIGGERS)
    singleton = 'motor = Motor' in src
    estado = 'REAL' if (real and not simulado and singleton) else 'REVISAR'
    print(f"  {estado}  {f.name}")
    if estado != 'REAL':
        resultados['simulados'].append(f.name)

print()
print("── 6. IMPORTS CRÍTICOS: CEREBRO ────────────────────────────────")
cerebro_archivos = ['bus_neuronal.py','consciencia.py','registrador_bus.py',
                    'orquestador_aurora.py','auto_conocimiento.py','pc_access.py']
for nombre in cerebro_archivos:
    ruta = ROOT / 'CEREBRO' / nombre
    if not ruta.exists():
        print(f"  FALTA   {nombre}")
        resultados['rotos'].append(f'CEREBRO/{nombre} - NO EXISTE')
        continue
    src = open(ruta, encoding='utf-8').read()
    try:
        compile(src, str(ruta), 'exec')
        print(f"  OK      {nombre}")
    except SyntaxError as e:
        print(f"  SYNTAX  {nombre}  linea {e.lineno}: {e.msg}")
        resultados['rotos'].append(f'CEREBRO/{nombre} - SYNTAX ERROR linea {e.lineno}')

print()
print("── 7. IMPORTS CRÍTICOS: MEMORIA ────────────────────────────────")
for nombre in ['sistema_memoria.py','contexto_usuario.py','motor_sueno.py',
               'perfil_habilidades.py','analitica_marketing.py']:
    ruta = ROOT / 'MEMORIA' / nombre
    if not ruta.exists():
        print(f"  FALTA   {nombre}")
        resultados['rotos'].append(f'MEMORIA/{nombre}')
        continue
    src = open(ruta, encoding='utf-8').read()
    try:
        compile(src, str(ruta), 'exec')
        print(f"  OK      {nombre}")
    except SyntaxError as e:
        print(f"  SYNTAX  {nombre}  linea {e.lineno}: {e.msg}")
        resultados['rotos'].append(f'MEMORIA/{nombre} linea {e.lineno}')

print()
print("── 8. CORE: ARCHIVOS DUPLICADOS / REDUNDANTES ──────────────────")
core_archivos = list((ROOT / 'CORE').glob('*.py'))
# Buscar servidores duplicados
servidores = [f for f in core_archivos if 'servidor' in f.name or 'server' in f.name]
print(f"  Servidores en CORE: {[f.name for f in servidores]}")
cerebro_servidores = list((ROOT / 'CEREBRO').glob('*server*.py'))
print(f"  Servidores en CEREBRO: {[f.name for f in cerebro_servidores]}")
cerebros = list((ROOT / 'CEREBRO').glob('aurora_cerebro*.py'))
print(f"  Versiones cerebro: {[f.name for f in cerebros]}")

print()
print("── 9. BASES DE DATOS ───────────────────────────────────────────")
for db in sorted(ROOT.rglob('*.db')):
    if '__pycache__' not in str(db) and '_ARCHIVE' not in str(db):
        size = db.stat().st_size
        tablas = []
        try:
            conn = sqlite3.connect(str(db))
            tablas = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            conn.close()
        except: pass
        print(f"  {db.relative_to(ROOT)}  ({size:,}b)  tablas={tablas}")
        resultados['dbs'].append({'path': str(db.relative_to(ROOT)), 'size': size, 'tablas': tablas})

print()
print("── 10. ARCHIVOS CON NOMBRES PROBLEMÁTICOS EN RAÍZ ─────────────")
for f in sorted(ROOT.iterdir()):
    if f.is_file():
        nombre = f.name
        if nombre.startswith('@') or nombre.startswith('bool') or nombre.startswith('Dict[') or ' ' in nombre:
            print(f"  BASURA: {nombre!r}")
            resultados['obsoletos'].append(nombre)

print()
print("── 11. RESUMEN FINAL ───────────────────────────────────────────")
print(f"  Carpetas activas:      {len(resultados['estructura'])}")
print(f"  .py en raiz:           {len(raiz_py)}")
print(f"  .bat/.ps1 en raiz:     {len(raiz_scripts)}")
print(f"  Motores simulados:     {len(resultados['simulados'])}")
print(f"  Archivos rotos:        {len(resultados['rotos'])}")
print(f"  Nombres problemáticos: {len(resultados['obsoletos'])}")
print(f"  Bases de datos:        {len(resultados['dbs'])}")
if resultados['rotos']:
    print(f"\n  ROTOS: {resultados['rotos']}")
print()
print("FIN AUDITORÍA")
