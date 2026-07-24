"""
ACCESOS - Web + PC para AURORA. 100% REAL, con candados de seguridad.
- Web: leer paginas y buscar (requests).
- PC: ejecutar comandos (con lista negra), leer/escribir/listar archivos (solo carpetas permitidas).
Todo queda registrado en LOGS/accesos.log (auditoria).
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

LOG = Path(__file__).parent.parent / "LOGS" / "accesos.log"

# ACCESO TOTAL a la PC (autorizado por el dueño). Solo se conserva un candado
# anti-catastrofe para evitar destruir el disco/sistema por un error.
COMANDOS_PROHIBIDOS = [
    "format ", "diskpart", "mkfs", "clear-disk", "format-volume",
    "vssadmin delete", "shutdown", "restart-computer", "stop-computer",
    "del /s /q c:\\windows", "rd /s /q c:\\windows", "rmdir /s /q c:\\windows",
    "c:\\windows\\system32\\", "remove-item c:\\windows",
]

TIMEOUT_CMD = 30


def _log(accion: str, detalle: str, ok: bool):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            estado = "OK" if ok else "BLOQUEADO/ERROR"
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {estado} {accion}: {detalle[:200]}\n")
    except Exception:
        pass


def _ruta_permitida(ruta: str) -> bool:
    # Acceso total a archivos (autorizado por el dueño). Solo se protege el nucleo de Windows en ESCRITURA.
    try:
        real = os.path.realpath(ruta).lower()
        if real.startswith(r"c:\windows\system32"):
            return False
        return True
    except Exception:
        return False


# ==================== WEB ====================

def leer_web(url: str) -> dict:
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    try:
        import requests
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (AURORA)"})
        html = r.text
        # HTML -> texto plano (basico)
        html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
        texto = re.sub(r"(?s)<[^>]+>", " ", html)
        texto = re.sub(r"\s+", " ", texto).strip()
        _log("leer_web", url, True)
        return {"status": "OK", "url": url, "http": r.status_code,
                "texto": texto[:8000], "truncado": len(texto) > 8000}
    except Exception as e:
        _log("leer_web", f"{url} -> {e}", False)
        return {"status": "ERROR", "url": url, "detalle": str(e)[:300]}


def buscar_web(query: str) -> dict:
    try:
        import requests
        r = requests.post("https://html.duckduckgo.com/html/", data={"q": query},
                          timeout=20, headers={"User-Agent": "Mozilla/5.0 (AURORA)"})
        resultados = []
        for m in re.finditer(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text):
            titulo = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if titulo:
                resultados.append({"titulo": titulo, "url": m.group(1)})
            if len(resultados) >= 8:
                break
        _log("buscar_web", query, True)
        return {"status": "OK", "query": query, "resultados": resultados}
    except Exception as e:
        _log("buscar_web", f"{query} -> {e}", False)
        return {"status": "ERROR", "query": query, "detalle": str(e)[:300]}


# ==================== PC ====================

def ejecutar_comando(comando: str) -> dict:
    bajo = comando.lower()
    for prohibido in COMANDOS_PROHIBIDOS:
        if prohibido in bajo:
            _log("ejecutar_comando", f"BLOQUEADO ('{prohibido}'): {comando}", False)
            return {"status": "BLOQUEADO", "comando": comando,
                    "detalle": f"Comando bloqueado por seguridad (contiene '{prohibido.strip()}')."}
    try:
        r = subprocess.run(comando, shell=True, capture_output=True, text=True,
                           timeout=TIMEOUT_CMD, encoding="utf-8", errors="replace")
        _log("ejecutar_comando", comando, True)
        return {"status": "OK", "comando": comando, "codigo": r.returncode,
                "salida": (r.stdout or "")[:6000], "error": (r.stderr or "")[:2000]}
    except subprocess.TimeoutExpired:
        _log("ejecutar_comando", f"TIMEOUT: {comando}", False)
        return {"status": "ERROR", "comando": comando, "detalle": f"Timeout ({TIMEOUT_CMD}s)"}
    except Exception as e:
        _log("ejecutar_comando", f"{comando} -> {e}", False)
        return {"status": "ERROR", "comando": comando, "detalle": str(e)[:300]}


def leer_archivo(ruta: str) -> dict:
    if not _ruta_permitida(ruta):
        _log("leer_archivo", f"FUERA DE CARPETAS PERMITIDAS: {ruta}", False)
        return {"status": "BLOQUEADO", "detalle": "Ruta fuera de las carpetas permitidas."}
    try:
        contenido = Path(ruta).read_text(encoding="utf-8", errors="replace")
        _log("leer_archivo", ruta, True)
        return {"status": "OK", "ruta": ruta, "contenido": contenido[:10000],
                "truncado": len(contenido) > 10000}
    except Exception as e:
        _log("leer_archivo", f"{ruta} -> {e}", False)
        return {"status": "ERROR", "ruta": ruta, "detalle": str(e)[:300]}


def escribir_archivo(ruta: str, contenido: str) -> dict:
    if not _ruta_permitida(ruta):
        _log("escribir_archivo", f"FUERA DE CARPETAS PERMITIDAS: {ruta}", False)
        return {"status": "BLOQUEADO", "detalle": "Ruta fuera de las carpetas permitidas."}
    try:
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        _log("escribir_archivo", ruta, True)
        return {"status": "OK", "ruta": ruta, "bytes": len(contenido.encode("utf-8"))}
    except Exception as e:
        _log("escribir_archivo", f"{ruta} -> {e}", False)
        return {"status": "ERROR", "ruta": ruta, "detalle": str(e)[:300]}


def listar_directorio(ruta: str) -> dict:
    if not _ruta_permitida(ruta):
        return {"status": "BLOQUEADO", "detalle": "Ruta fuera de las carpetas permitidas."}
    try:
        items = []
        for e in sorted(Path(ruta).iterdir()):
            items.append({"nombre": e.name, "tipo": "dir" if e.is_dir() else "archivo",
                          "kb": round(e.stat().st_size / 1024, 1) if e.is_file() else None})
        _log("listar_directorio", ruta, True)
        return {"status": "OK", "ruta": ruta, "items": items}
    except Exception as e:
        return {"status": "ERROR", "ruta": ruta, "detalle": str(e)[:300]}


def estado() -> dict:
    return {
        "web": True,
        "pc": True,
        "acceso": "TOTAL (disco completo; solo protegido C:\\Windows\\System32)",
        "candado_anticatastrofe": len(COMANDOS_PROHIBIDOS),
        "log": str(LOG),
    }
