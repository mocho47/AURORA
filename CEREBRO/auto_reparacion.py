# -*- coding: utf-8 -*-
"""
🔧 AURORA — AUTO-REPARACIÓN REAL
Detecta errores en su propio código, genera fix con LLM, valida y aplica con backup.
Ruta: C:/AURORA/CEREBRO/auto_reparacion.py
"""
import asyncio, json, logging, os, py_compile, shutil, tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from groq import AsyncGroq

sys_path_guard = __import__("sys")
sys_path_guard.path.insert(0, str(Path(__file__).parent.parent))
from CEREBRO.auto_conocimiento import auto_conocimiento, ROOT

logger = logging.getLogger("aurora.auto_reparacion")

PROMPT_REPARACION = """Eres un experto Python en el proyecto AURORA.
Se te da un archivo con un error. Devuelve SOLO el código Python corregido y completo.
Sin explicaciones, sin markdown, sin comentarios extra.
Si no es posible corregir, responde exactamente: IRREPARABLE: [motivo]"""

# ── BLINDAJE (agregado 2026-07-29 tras encontrar un bug catastrofico real) ──
# El bug: se le mandaban al LLM solo los primeros 6000 caracteres del archivo,
# pero su respuesta REEMPLAZABA EL ARCHIVO COMPLETO. En consciencia.py (148,330
# caracteres) el LLM veia el 4% del archivo y su salida habria borrado el otro
# 96% — el cerebro entero de AURORA. Y py_compile lo aprobaba, porque un archivo
# truncado compila perfecto: la "validacion" daba falsa confianza. Peor:
# diagnosticar_y_reparar_todo() corre esto AUTOMATICAMENTE sobre cada modulo con
# error, incluido consciencia.py. Choca de frente con la regla permanente de
# Anuar: "NO restar funciones (2 años de trabajo limpio que YA funciona)".
#
# Tres candados, cada uno suficiente por si solo:
# Mejora 2026-07-29: se pasa del modelo chico (openai/gpt-oss-20b) al grande
# (openai/gpt-oss-120b, verificado disponible con la llave real de Anuar).
# Reescribir codigo es justo la tarea donde el modelo chico se equivoca; y su
# contexto de 128k permite subir el limite de tamaño de 6,000 a 40,000
# caracteres SIN romper la garantia de "el archivo cabe completo": eso pasa la
# cobertura de 80 a mas de 170 de los 195 archivos propios de AURORA.
MODELO_REPARACION = "openai/gpt-oss-120b"
CHARS_AL_LLM = 40000         # lo que el LLM alcanza a ver de verdad
# 1) Archivos del nucleo: NUNCA se auto-reparan sin Anuar (son el corazon).
ARCHIVOS_NUCLEO = {
    "cerebro/consciencia.py", "core/aurora_server.py", "run_aurora.py",
    "cerebro/auto_reparacion.py", "cerebro/registro_herramientas.py",
}
# 2) Si el archivo no cabe completo en lo que ve el LLM, se rechaza: reescribir
#    a ciegas lo que no viste es garantia de perdida de codigo.
# 3) Aunque quepa, si el resultado pierde mas de este % de lineas, se revierte.
PERDIDA_LINEAS_MAX_PCT = 25.0


def _puede_importarse(path: Path):
    """Intenta importar el archivo en un proceso APARTE (para no contaminar el
    actual ni dejar el modulo a medias cargado). Devuelve (True, "") si importa,
    o (False, error_real) si no. Es la prueba que compilar NO da: un archivo
    puede compilar perfecto y aun asi estar roto por dentro."""
    import subprocess as _sp
    codigo = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('_verif_fix', r'''{path}''')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "print('IMPORT_OK')\n"
    )
    try:
        r = _sp.run([sys_path_guard.executable, "-c", codigo], capture_output=True,
                    text=True, timeout=60, cwd=str(ROOT))
        if "IMPORT_OK" in (r.stdout or ""):
            return True, ""
        return False, ((r.stderr or r.stdout or "").strip() or "no importó, sin detalle")
    except Exception as e:
        # Si no se pudo ni hacer la verificacion, se es honesto: no se afirma que
        # esta bien. Se trata como fallo para que se revierta (lado seguro).
        return False, f"no se pudo verificar el import: {str(e)[:150]}"


def _limpiar_respuesta_llm(texto: str) -> str:
    """Quita el envoltorio markdown que el modelo pone aunque se le pida que no.

    Encontrado probandolo en vivo 2026-07-29: el auto-reparador NUNCA habia
    reparado nada. El modelo devuelve el codigo dentro de ```python ... ``` y
    eso jamas compila, asi que TODOS los intentos morian en FIX_INVALIDO. El
    prompt ya pedia "sin markdown" pero el modelo (openai/gpt-oss-20b) lo
    ignora — pedirlo no basta, hay que limpiarlo.
    """
    t = (texto or "").strip()
    if not t.startswith("```"):
        return t
    lineas = t.splitlines()
    # Primera linea es la apertura (```python, ```py, ``` ...): se descarta.
    if lineas and lineas[0].lstrip().startswith("```"):
        lineas = lineas[1:]
    # Ultima linea de cierre, si esta.
    while lineas and lineas[-1].strip() in ("```", ""):
        lineas.pop()
    return "\n".join(lineas).strip()


class AutoReparacion:
    _instancia: Optional["AutoReparacion"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self):
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY","")) if os.getenv("GROQ_API_KEY") else None

    async def reparar(self, descripcion_error: str, archivo_relativo: str) -> Dict:
        """Repara un archivo. Backup → LLM fix → validar → aplicar o rollback."""
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}

        path = (ROOT / archivo_relativo).resolve()
        if not str(path).startswith(str(ROOT.resolve())):
            return {"status": "DENEGADO", "detalle": "Fuera del ecosistema"}
        if not path.exists():
            return {"status": "ERROR", "detalle": f"No existe: {archivo_relativo}"}

        # CANDADO 1: archivos del núcleo jamás se auto-reparan solos.
        _rel_norm = archivo_relativo.replace("\\", "/").lstrip("./").lower()
        if _rel_norm in ARCHIVOS_NUCLEO:
            return {"status": "DENEGADO_NUCLEO",
                    "detalle": f"'{archivo_relativo}' es del núcleo de AURORA. No se auto-repara "
                               "sin que Anuar lo revise — un error aquí tumba todo el sistema."}

        # 1. Leer código actual
        codigo_actual = path.read_text(encoding="utf-8")

        # CANDADO 2: si el archivo NO cabe completo en lo que el LLM alcanza a
        # ver, no se toca. Reescribir a ciegas lo que no viste borra código real.
        if len(codigo_actual) > CHARS_AL_LLM:
            return {"status": "DEMASIADO_GRANDE",
                    "detalle": (f"'{archivo_relativo}' tiene {len(codigo_actual):,} caracteres y el "
                                f"modelo solo alcanza a ver {CHARS_AL_LLM:,}. Repararlo así borraría "
                                f"el {100 - (CHARS_AL_LLM * 100 // len(codigo_actual))}% del archivo. "
                                "No lo toco: hay que arreglarlo a mano o por partes."),
                    "caracteres": len(codigo_actual), "limite": CHARS_AL_LLM}
        _lineas_antes = len(codigo_actual.splitlines())

        # 2. LLM genera fix
        try:
            resp = await self._groq.chat.completions.create(
                model=MODELO_REPARACION,
                messages=[
                    {"role": "system", "content": PROMPT_REPARACION},
                    # Ya no se recorta: el CANDADO 2 garantiza que el archivo
                    # completo cabe. Antes el [:6000] mutilaba la entrada mientras
                    # la salida reemplazaba el archivo entero (bug catastrofico).
                    {"role": "user", "content": f"ERROR: {descripcion_error}\n\nARCHIVO ({archivo_relativo}):\n{codigo_actual}"}
                ],
                max_tokens=4096, temperature=0.1
            )
            codigo_nuevo = _limpiar_respuesta_llm(resp.choices[0].message.content)
        except Exception as e:
            return {"status": "ERROR_LLM", "detalle": str(e)}

        if codigo_nuevo.startswith("IRREPARABLE:"):
            return {"status": "IRREPARABLE", "detalle": codigo_nuevo}

        # 3. Backup
        backup_path = path.with_suffix(f".bak_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(path, backup_path)

        # 4. Escribir en temp y validar sintaxis
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(codigo_nuevo)
            tmp_path = tmp.name

        try:
            py_compile.compile(tmp_path, doraise=True)
        except py_compile.PyCompileError as e:
            Path(tmp_path).unlink(missing_ok=True)
            backup_path.unlink(missing_ok=True)
            return {"status": "FIX_INVALIDO", "detalle": str(e), "codigo_propuesto": codigo_nuevo[:500]}

        # CANDADO 3: compilar NO prueba que no se perdio codigo — un archivo
        # truncado compila perfecto. Si el "fix" borro una parte grande del
        # archivo, se rechaza y no se aplica (el original queda intacto).
        _lineas_despues = len(codigo_nuevo.splitlines())
        if _lineas_antes > 0:
            _perdida_pct = (_lineas_antes - _lineas_despues) * 100.0 / _lineas_antes
            if _perdida_pct > PERDIDA_LINEAS_MAX_PCT:
                Path(tmp_path).unlink(missing_ok=True)
                backup_path.unlink(missing_ok=True)
                return {"status": "FIX_RECHAZADO_PERDIDA",
                        "detalle": (f"El fix propuesto pasa de {_lineas_antes} a {_lineas_despues} líneas "
                                    f"({_perdida_pct:.0f}% menos). Compila, pero perdió código real — "
                                    "no se aplica. El archivo original quedó intacto."),
                        "lineas_antes": _lineas_antes, "lineas_propuestas": _lineas_despues}

        # 5. Aplicar
        shutil.copy2(tmp_path, path)
        Path(tmp_path).unlink(missing_ok=True)

        # CANDADO 4 (mejora 2026-07-29): compilar solo prueba que la SINTAXIS
        # esta bien; un archivo puede compilar y estar roto por dentro (un
        # import que ya no existe, una constante borrada, indentacion que
        # cambio el significado). Aqui se intenta IMPORTAR de verdad el modulo
        # ya aplicado, en un proceso aparte para no contaminar este. Si no
        # importa, se restaura el respaldo automaticamente: el archivo original
        # NUNCA se queda roto por un fix malo.
        _import_ok, _import_err = _puede_importarse(path)
        if not _import_ok:
            shutil.copy2(backup_path, path)      # rollback real inmediato
            return {"status": "FIX_REVERTIDO_NO_IMPORTA",
                    "detalle": (f"El fix compilaba pero el módulo ya no se puede importar, "
                                f"así que se restauró el original automáticamente. "
                                f"Error real: {_import_err[:200]}"),
                    "archivo": archivo_relativo, "revertido": True}

        # 6. Registrar en memoria episódica
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen="auto_reparacion",
                tipo_evento="fix_aplicado",
                contenido={"archivo": archivo_relativo, "error": descripcion_error[:200], "backup": str(backup_path)},
                importancia=0.95
            )
        except Exception:
            pass

        logger.info(f"✅ Fix aplicado: {archivo_relativo} | Backup: {backup_path.name}")
        return {
            "status": "OK",
            "archivo": archivo_relativo,
            "backup": str(backup_path),
            "lineas_nuevas": len(codigo_nuevo.splitlines())
        }

    async def diagnosticar_y_reparar_todo(self) -> Dict:
        """Escanea todos los módulos, detecta errores de sintaxis y los repara."""
        diagnostico = await auto_conocimiento.diagnosticar_modulos()
        errores = diagnostico.get("errores", {})
        reparaciones = {}

        for modulo_path, info in errores.items():
            if info["status"] != "ERROR_SINTAXIS":
                continue
            archivo_rel = info.get("archivo", "").replace(str(ROOT) + "\\", "").replace(str(ROOT) + "/", "")
            if not archivo_rel:
                continue
            resultado = await self.reparar(info["detalle"], archivo_rel)
            reparaciones[archivo_rel] = resultado

        return {
            "errores_encontrados": len(errores),
            "reparaciones_aplicadas": sum(1 for r in reparaciones.values() if r.get("status") == "OK"),
            "detalle": reparaciones
        }

    async def revertir(self, archivo_relativo: str) -> Dict:
        """Restaura el backup más reciente de un archivo."""
        path = (ROOT / archivo_relativo).resolve()
        carpeta = path.parent
        nombre_base = path.stem

        backups = sorted(carpeta.glob(f"{nombre_base}.bak_*"), reverse=True)
        if not backups:
            return {"status": "SIN_BACKUP"}

        ultimo_backup = backups[0]
        shutil.copy2(ultimo_backup, path)
        logger.info(f"↩️  Revertido: {archivo_relativo} desde {ultimo_backup.name}")
        return {"status": "OK", "restaurado_desde": ultimo_backup.name}


auto_reparacion = AutoReparacion()
