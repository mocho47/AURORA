# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║           🔭 AURORA — AUTO-CONOCIMIENTO                              ║
║   AURORA lee su propia estructura, capacidades y estado real.         ║
║   Sin simulaciones — introspección directa del sistema de archivos.  ║
╚══════════════════════════════════════════════════════════════════════╝
Ruta: C:/AURORA/CEREBRO/auto_conocimiento.py
"""
import asyncio
import importlib
import importlib.util
import json
import logging
import py_compile
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aurora.auto_conocimiento")

ROOT = Path(__file__).parent.parent  # C:\AURORA

# Módulos que AURORA conoce de sí misma
CARPETAS_PROPIAS = [
    "CEREBRO", "MEMORIA", "MOTORES", "CORE",
    "INTEGRACIONES", "EDITOR", "ORACLE",
    "VENDEDOR", "ACCESOS", "COMANDOS", "TOOLS",
]

# ─────────────────────────────────────────────────────────────────────


class AutoConocimiento:
    """
    AURORA se conoce a sí misma.

    Capacidades:
    · Escanea su estructura real de archivos y módulos
    · Lee el contenido de sus propios archivos
    · Detecta errores de importación en sus módulos
    · Conoce sus capacidades activas vs pendientes
    · Genera un mapa de inteligencia del ecosistema
    · Detecta qué integraciones están operativas
    """

    _instancia: Optional["AutoConocimiento"] = None

    def __new__(cls) -> "AutoConocimiento":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._cache_estructura: Optional[Dict] = None
            cls._instancia._cache_ts: Optional[datetime] = None
        return cls._instancia

    # ── ESTRUCTURA Y CAPACIDADES ──────────────────────────────────

    async def escanear_estructura(self, forzar: bool = False) -> Dict:
        """
        Escanea los archivos Python de AURORA y devuelve un mapa completo.
        Cachea el resultado 5 minutos para no re-escanear en cada consulta.
        """
        ahora = datetime.utcnow()
        if (
            not forzar
            and self._cache_estructura
            and self._cache_ts
            and (ahora - self._cache_ts).total_seconds() < 300
        ):
            return self._cache_estructura

        estructura = {}
        for carpeta in CARPETAS_PROPIAS:
            ruta = ROOT / carpeta
            if ruta.exists():
                archivos = sorted(ruta.glob("*.py"))
                estructura[carpeta] = [
                    f.stem for f in archivos if not f.stem.startswith("__")
                ]
            else:
                estructura[carpeta] = []

        self._cache_estructura = estructura
        self._cache_ts = ahora
        return estructura

    async def leer_archivo(self, ruta_relativa: str) -> str:
        """
        Lee el contenido de un archivo propio de AURORA.
        Solo permite rutas dentro de C:/AURORA.
        """
        path = (ROOT / ruta_relativa).resolve()
        if not str(path).startswith(str(ROOT.resolve())):
            raise PermissionError(f"Ruta fuera del ecosistema AURORA: {ruta_relativa}")
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        return await asyncio.to_thread(path.read_text, encoding="utf-8")

    async def diagnosticar_modulos(self) -> Dict[str, Dict]:
        """
        Intenta importar cada módulo de MOTORES y CEREBRO.
        Reporta cuáles cargan bien y cuáles tienen errores.
        """
        resultados: Dict[str, Dict] = {}

        estructura = await self.escanear_estructura()
        modulos_a_probar = (
            [f"MOTORES.{m}" for m in estructura.get("MOTORES", [])] +
            [f"CEREBRO.{m}" for m in estructura.get("CEREBRO", [])] +
            [f"MEMORIA.{m}" for m in estructura.get("MEMORIA", [])]
        )

        for nombre_modulo in modulos_a_probar:
            try:
                spec = importlib.util.find_spec(nombre_modulo)
                if spec is None:
                    resultados[nombre_modulo] = {"status": "NO_ENCONTRADO"}
                    continue
                # Compilar sin ejecutar
                archivo = spec.origin
                py_compile.compile(archivo, doraise=True)
                resultados[nombre_modulo] = {"status": "OK", "archivo": archivo}
            except py_compile.PyCompileError as e:
                resultados[nombre_modulo] = {"status": "ERROR_SINTAXIS", "detalle": str(e)}
            except Exception as e:
                resultados[nombre_modulo] = {"status": "ERROR", "detalle": str(e)[:200]}

        ok = sum(1 for v in resultados.values() if v["status"] == "OK")
        errores = {k: v for k, v in resultados.items() if v["status"] != "OK"}
        logger.info(f"🔭 Diagnóstico: {ok}/{len(resultados)} módulos OK | Errores: {len(errores)}")
        return {"modulos": resultados, "total_ok": ok, "errores": errores}

    async def obtener_capacidades(self) -> Dict:
        """
        Retorna un mapa de todas las capacidades activas de AURORA.
        Detecta cuáles tienen API keys configuradas y cuáles no.
        """
        import os

        capacidades = {
            "motores_ia": [],
            "integraciones": {},
            "memoria": {},
            "web": {},
            "editor": {},
        }

        # Motores
        estructura = await self.escanear_estructura()
        capacidades["motores_ia"] = estructura.get("MOTORES", [])

        # Integraciones reales
        capacidades["integraciones"] = {
            "groq_llm":        bool(os.getenv("GROQ_API_KEY")),
            "whatsapp_green":  bool(os.getenv("GREEN_API_TOKEN")),
            "facebook":        bool(os.getenv("FB_PAGE_TOKEN")),
            "instagram":       bool(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
            "supabase":        bool(os.getenv("SUPABASE_KEY")),
            "jwt_auth":        bool(os.getenv("JWT_SECRET_KEY")),
        }

        # Estado de la memoria
        try:
            from MEMORIA.sistema_memoria import DB_PATH
            conn = sqlite3.connect(str(DB_PATH))
            ep = conn.execute("SELECT COUNT(*) FROM episodica").fetchone()[0]
            sem = conn.execute("SELECT COUNT(*) FROM semantica").fetchone()[0]
            conn.close()
            capacidades["memoria"] = {
                "db_path": str(DB_PATH),
                "episodios": ep,
                "conocimientos_semanticos": sem,
                "estado": "OPERATIVA",
            }
        except Exception as e:
            capacidades["memoria"] = {"estado": "ERROR", "detalle": str(e)[:100]}

        # Web search
        capacidades["web"] = {
            "google_search": bool(os.getenv("GOOGLE_API_KEY")),
            "scraping_httpx": True,
        }

        # Editor
        capacidades["editor"] = {
            "editor_imagenes": True,
            "editor_codigo": True,  # auto_reparacion
        }

        return capacidades

    async def estado_sistema_completo(self) -> Dict:
        """
        Fotografía completa del sistema en este momento.
        Estructura + Capacidades + Diagnóstico de módulos.
        """
        estructura = await self.escanear_estructura()
        capacidades = await self.obtener_capacidades()
        diagnostico = await self.diagnosticar_modulos()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "root": str(ROOT),
            "estructura": estructura,
            "capacidades": capacidades,
            "salud_modulos": {
                "total_ok": diagnostico["total_ok"],
                "errores_detectados": list(diagnostico["errores"].keys()),
            },
        }

    # ── BÚSQUEDA EN CÓDIGO PROPIO ─────────────────────────────────

    async def buscar_en_codigo(self, patron: str) -> List[Dict]:
        """
        Busca un patrón de texto en todos los archivos Python de AURORA.
        Útil para que AURORA entienda dónde está definida una función.
        """
        resultados = []
        estructura = await self.escanear_estructura()

        for carpeta, modulos in estructura.items():
            for modulo in modulos:
                ruta = ROOT / carpeta / f"{modulo}.py"
                if not ruta.exists():
                    continue
                try:
                    contenido = await asyncio.to_thread(
                        ruta.read_text, encoding="utf-8"
                    )
                    lineas_match = [
                        {"linea": i + 1, "contenido": l.strip()}
                        for i, l in enumerate(contenido.splitlines())
                        if patron.lower() in l.lower()
                    ]
                    if lineas_match:
                        resultados.append({
                            "archivo": str(ruta.relative_to(ROOT)),
                            "coincidencias": lineas_match[:5],
                        })
                except Exception:
                    continue

        return resultados


# Instancia global (singleton)
auto_conocimiento = AutoConocimiento()
