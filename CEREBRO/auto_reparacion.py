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

        # 1. Leer código actual
        codigo_actual = path.read_text(encoding="utf-8")

        # 2. LLM genera fix
        try:
            resp = await self._groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": PROMPT_REPARACION},
                    {"role": "user", "content": f"ERROR: {descripcion_error}\n\nARCHIVO ({archivo_relativo}):\n{codigo_actual[:6000]}"}
                ],
                max_tokens=4096, temperature=0.1
            )
            codigo_nuevo = resp.choices[0].message.content.strip()
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

        # 5. Aplicar
        shutil.copy2(tmp_path, path)
        Path(tmp_path).unlink(missing_ok=True)

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
