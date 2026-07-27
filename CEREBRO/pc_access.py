# -*- coding: utf-8 -*-
"""
💻 AURORA — ACCESO REAL AL PC
Ejecuta comandos, lee/escribe archivos, monitorea el sistema.
Registra todo en memoria episódica. Respeta candados de seguridad.
Ruta: C:/AURORA/CEREBRO/pc_access.py
"""
import asyncio
import logging
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("aurora.pc_access")

ROOT = Path(__file__).parent.parent  # C:\AURORA

# ── Seguridad: rutas permitidas para escritura ────────────────────
RUTAS_ESCRITURA_PERMITIDAS = [
    ROOT,
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.home() / "Documents",
]

# ── Comandos/palabras bloqueadas ──────────────────────────────────
COMANDOS_BLOQUEADOS = [
    "format", "rmdir /s", "del /f /s", "rd /s", "deltree",
    "shutdown", "restart", "taskkill /f", "reg delete",
    "bcdedit", "diskpart", "cipher /w", "sfc /scannow",
    "netsh firewall", "net user /delete", "wmic process delete",
]


def _es_comando_seguro(cmd: str) -> Tuple[bool, str]:
    cmd_lower = cmd.lower()
    for bloqueado in COMANDOS_BLOQUEADOS:
        if bloqueado in cmd_lower:
            return False, f"Comando bloqueado por seguridad: '{bloqueado}'"
    return True, ""


def _es_ruta_escritura_permitida(path: Path) -> bool:
    path_resuelto = path.resolve()
    return any(
        str(path_resuelto).startswith(str(p.resolve()))
        for p in RUTAS_ESCRITURA_PERMITIDAS
    )


_EXT_BINARIAS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico",
    ".mp4", ".mp3", ".wav", ".avi", ".mov", ".mkv",
    ".zip", ".rar", ".7z", ".exe", ".msi", ".dll",
    ".docx", ".xlsx", ".pptx", ".cdr", ".ai", ".psd",
}


_CARPETAS_CONOCIDAS = {
    "descargas": Path.home() / "Downloads", "downloads": Path.home() / "Downloads",
    "escritorio": Path.home() / "Desktop", "desktop": Path.home() / "Desktop",
    "documentos": Path.home() / "Documents", "documents": Path.home() / "Documents",
}


def _resolver_archivo_real(ruta: str) -> Tuple[Optional[Path], Optional[Dict]]:
    """Resuelve una ruta como la escribiría un humano (carpeta conocida +
    nombre aproximado) y, si el nombre exacto no existe, busca la coincidencia
    real más cercana en esa carpeta — nunca deja pasar un nombre inventado.
    Regresa (ruta_real, None) si se resolvió, o (None, dict_de_error) si no."""
    import difflib
    p = Path(ruta)
    if not p.is_absolute():
        partes = Path(ruta.replace("\\", "/")).parts
        base = _CARPETAS_CONOCIDAS.get(partes[0].lower()) if partes else None
        p = (base / Path(*partes[1:])) if base and len(partes) > 1 else \
            (base if base else Path.home() / ruta)
    if not p.exists() and p.parent.exists():
        candidatos = [f.name for f in p.parent.iterdir() if f.is_file()]
        # Si se pidió una extensión específica, SOLO se consideran candidatos del
        # mismo tipo de archivo. Encontrado en vivo 2026-07-27: pedir "el pdf" con
        # nombre "argan" abrió "argan.gsp" (un archivo de corte de 5KB, no el PDF)
        # porque el nombre se parecía más, ignorando que el tipo pedido era otro.
        ext_pedida = p.suffix.lower()
        mismo_tipo = [c for c in candidatos if Path(c).suffix.lower() == ext_pedida] if ext_pedida else candidatos
        pool = mismo_tipo if mismo_tipo else candidatos
        match = difflib.get_close_matches(p.name, pool, n=3, cutoff=0.35)
        if len(match) == 1:
            p = p.parent / match[0]
        elif len(match) > 1:
            return None, {"status": "ambiguo",
                          "mensaje": f"'{ruta}' no existe exacto y hay varios parecidos en {p.parent}: "
                                     + ", ".join(match) + ". Dime cuál exacto (no invento cuál quisiste)."}
        else:
            return None, {"status": "no_encontrado",
                          "mensaje": f"No encontré '{ruta}' en {p.parent}. Archivos ahí: "
                                     + ", ".join(candidatos[:15]) + (" ..." if len(candidatos) > 15 else "")}
    return p, None


# ── Ops síncronas ─────────────────────────────────────────────────

def _ejecutar_powershell_sync(cmd: str, timeout: int = 30) -> Dict:
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout,
        cwd=str(ROOT), encoding="utf-8", errors="replace"
    )
    return {
        "stdout": resultado.stdout.strip(),
        "stderr": resultado.stderr.strip(),
        "returncode": resultado.returncode,
    }


def _estado_sistema_sync() -> Dict:
    import psutil
    cpu    = psutil.cpu_percent(interval=1)
    mem    = psutil.virtual_memory()
    disco  = psutil.disk_usage(str(ROOT))
    procs  = len(psutil.pids())
    return {
        "cpu_pct":      cpu,
        "ram_pct":      mem.percent,
        "ram_gb_libre": round(mem.available / 1024**3, 2),
        "disco_pct":    disco.percent,
        "disco_gb_libre": round(disco.free / 1024**3, 2),
        "procesos":     procs,
        "timestamp":    datetime.utcnow().isoformat(),
    }


class PcAccess:
    """
    Acceso real al PC de Anuar.
    AURORA puede leer, escribir, ejecutar y monitorear — con candados de seguridad.
    Todo queda registrado en la memoria episódica.
    """

    _instancia: Optional["PcAccess"] = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    async def _registrar(self, accion: str, detalle: Dict, importancia: float = 0.6) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen="pc_access",
                tipo_evento=accion,
                contenido=detalle,
                importancia=importancia,
            )
        except Exception:
            pass

    # ── EJECUCIÓN DE COMANDOS ─────────────────────────────────────

    async def ejecutar(self, cmd: str, timeout: int = 30) -> Dict:
        """Ejecuta un comando PowerShell real. Bloqueados los destructivos."""
        seguro, razon = _es_comando_seguro(cmd)
        if not seguro:
            await self._registrar("comando_bloqueado", {"cmd": cmd[:200], "razon": razon}, 0.9)
            return {"status": "BLOQUEADO", "razon": razon}

        try:
            resultado = await asyncio.to_thread(
                _ejecutar_powershell_sync, cmd, timeout
            )
            resultado["status"] = "OK" if resultado["returncode"] == 0 else "ERROR"
            resultado["cmd"] = cmd[:200]
            await self._registrar("comando_ejecutado", {
                "cmd": cmd[:200],
                "exitcode": resultado["returncode"],
                "output_preview": resultado["stdout"][:300],
            }, 0.5)
            return resultado
        except subprocess.TimeoutExpired:
            return {"status": "TIMEOUT", "cmd": cmd[:200]}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def ejecutar_python(self, codigo: str) -> Dict:
        """Ejecuta código Python en el contexto del proyecto."""
        try:
            resultado = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-c", codigo],
                capture_output=True, text=True, timeout=20,
                cwd=str(ROOT), encoding="utf-8", errors="replace"
            )
            await self._registrar("python_ejecutado", {"preview": codigo[:150]}, 0.5)
            return {
                "status": "OK" if resultado.returncode == 0 else "ERROR",
                "stdout": resultado.stdout.strip(),
                "stderr": resultado.stderr.strip(),
            }
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    # ── FILESYSTEM ────────────────────────────────────────────────

    async def leer_archivo(self, ruta: str) -> Dict:
        """Lee cualquier archivo de TEXTO del PC (código, .txt, .json, .csv...).
        Resuelve carpetas conocidas y busca la coincidencia real más cercana si
        el nombre exacto no existe. Para PDF/imágenes/video/binarios no lee el
        contenido como texto (saldría basura) — usa abrir_archivo en su lugar."""
        path, err = _resolver_archivo_real(ruta)
        if err:
            return err
        if not path.exists():
            return {"status": "NO_EXISTE", "ruta": str(path)}
        if path.suffix.lower() in _EXT_BINARIAS:
            return {"status": "es_binario", "ruta": str(path),
                    "mensaje": f"'{path.name}' es un archivo binario ({path.suffix}), no se puede "
                               "leer como texto. Usa abrir_archivo para abrirlo con su programa."}
        try:
            contenido = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
            await self._registrar("archivo_leido", {"ruta": str(path), "bytes": len(contenido)}, 0.4)
            return {"status": "OK", "ruta": str(path), "contenido": contenido, "lineas": contenido.count("\n")}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def escribir_archivo(self, ruta: str, contenido: str) -> Dict:
        """Escribe un archivo. Solo en rutas permitidas."""
        path = Path(ruta).resolve()
        if not _es_ruta_escritura_permitida(path):
            return {"status": "DENEGADO", "ruta": str(path), "razon": "Ruta fuera de zonas permitidas"}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(path.write_text, contenido, encoding="utf-8")
            await self._registrar("archivo_escrito", {"ruta": str(path), "bytes": len(contenido)}, 0.7)
            return {"status": "OK", "ruta": str(path), "bytes": len(contenido)}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def listar_directorio(self, ruta: str = ".", profundidad: int = 1) -> Dict:
        """Lista el contenido de un directorio."""
        path = Path(ruta).resolve()
        try:
            if not path.exists():
                return {"status": "NO_EXISTE"}
            items = []
            for item in sorted(path.iterdir()):
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue
                items.append({
                    "nombre": item.name,
                    "tipo": "dir" if item.is_dir() else "archivo",
                    "tamaño_kb": round(item.stat().st_size / 1024, 1) if item.is_file() else None,
                })
            return {"status": "OK", "ruta": str(path), "items": items, "total": len(items)}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def buscar_archivos(self, patron: str, directorio: str = None) -> List[str]:
        """Busca archivos por patrón glob."""
        base = Path(directorio).resolve() if directorio else ROOT
        resultados = [str(p) for p in base.rglob(patron)
                      if "__pycache__" not in str(p) and ".git" not in str(p)]
        return resultados[:50]

    # ── MONITOREO DEL SISTEMA ─────────────────────────────────────

    async def estado_sistema(self) -> Dict:
        """Estado en tiempo real: CPU, RAM, disco, procesos."""
        try:
            estado = await asyncio.to_thread(_estado_sistema_sync)
            return {"status": "OK", **estado}
        except ImportError:
            # psutil no instalado — usar PowerShell
            r = await self.ejecutar(
                "Get-ComputerInfo | Select-Object CsProcessors,OsTotalVisibleMemorySize,OsFreePhysicalMemory | ConvertTo-Json"
            )
            return {"status": "OK_FALLBACK", "raw": r.get("stdout", "")[:500]}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def procesos_activos(self, top: int = 15) -> Dict:
        """Lista los procesos con más uso de CPU/RAM."""
        r = await self.ejecutar(
            f"Get-Process | Sort-Object CPU -Descending | Select-Object -First {top} Name,CPU,WorkingSet | ConvertTo-Json"
        )
        return {"status": r["status"], "procesos": r.get("stdout", "")[:1000]}

    async def espacio_disco(self) -> Dict:
        r = await self.ejecutar("Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free | ConvertTo-Json")
        return {"status": r["status"], "discos": r.get("stdout", "")[:800]}

    # ── CLIPBOARD / PORTAPAPELES ──────────────────────────────────

    async def leer_portapapeles(self) -> str:
        """Lee el contenido actual del portapapeles."""
        r = await self.ejecutar("Get-Clipboard")
        return r.get("stdout", "")

    async def escribir_portapapeles(self, texto: str) -> Dict:
        """Escribe texto al portapapeles."""
        cmd = f'Set-Clipboard -Value "{texto[:2000].replace(chr(34), chr(39))}"'
        return await self.ejecutar(cmd)

    # ── APPS Y VENTANAS ───────────────────────────────────────────

    async def abrir_archivo(self, ruta: str) -> Dict:
        """Abre un archivo con su aplicación predeterminada. Resuelve carpetas
        conocidas (Descargas/Escritorio/Documentos) igual que las escribe un
        humano, y si el nombre exacto no existe busca la coincidencia real más
        cercana en esa carpeta — nunca intenta abrir un nombre inventado."""
        p, err = _resolver_archivo_real(ruta)
        if err:
            return err
        return await self.ejecutar(f'Start-Process "{p}"')

    async def abrir_url(self, url: str) -> Dict:
        """Abre una URL real en el navegador default (Start-Process). NO es un
        archivo: no pasa por resolución de carpetas ni búsqueda difusa, solo
        valida que tenga forma de URL y le agrega https:// si falta el esquema."""
        import re
        url = (url or "").strip()
        if not url:
            return {"status": "error", "mensaje": "Dame la URL o el dominio de la página a abrir."}
        if not re.match(r"^https?://", url, re.I):
            url = "https://" + url
        return await self.ejecutar(f'Start-Process "{url}"')

    async def apps_instaladas(self) -> Dict:
        r = await self.ejecutar(
            "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* "
            "| Select-Object DisplayName,DisplayVersion | Where-Object {$_.DisplayName} "
            "| Sort-Object DisplayName | Select-Object -First 40 | ConvertTo-Json"
        )
        return {"status": r["status"], "apps": r.get("stdout", "")[:2000]}


# Instancia global
pc_access = PcAccess()
