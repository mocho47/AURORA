# -*- coding: utf-8 -*-
"""
AURORA · APRENDIZAJE / MANUALES
Busca, descarga e ingiere a la Biblioteca los manuales de usuario de las herramientas
de Anuar, para que AURORA sepa qué hace cada botón.

Honesto:
- Herramientas con manual PDF oficial (Silhouette, RDWorks, LibreOffice, Aspire): busca el
  PDF, lo descarga, valida que sea PDF REAL (magic bytes %PDF) y lo ingiere a biblioteca.db.
- Facebook / redes: NO existe un PDF de "qué hace cada botón". Devuelve los enlaces del
  centro de ayuda oficial para consultarlos en vivo (cartucho Web). No inventa un PDF.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESCARGAS = ROOT / "MANUALES" / "descargas"

HERRAMIENTAS = {
    "silhouette":  {"nombre": "Silhouette Studio", "tipo": "pdf",
                    "query": "Silhouette Studio user manual filetype:pdf"},
    "rdworks":     {"nombre": "RDWorks (láser)", "tipo": "pdf",
                    "query": "RDWorks V8 user manual filetype:pdf"},
    "libreoffice": {"nombre": "LibreOffice", "tipo": "pdf",
                    "query": "LibreOffice Getting Started Guide filetype:pdf"},
    "aspire":      {"nombre": "Vectric Aspire", "tipo": "pdf",
                    "query": "Vectric Aspire reference manual filetype:pdf"},
    "inkscape":    {"nombre": "Inkscape", "tipo": "pdf",
                    "query": "Inkscape manual filetype:pdf"},
    "coreldraw":   {"nombre": "CorelDRAW Graphics Suite 2025", "tipo": "pdf",
                    "query": "CorelDRAW Graphics Suite Quick Start Guide site:product.corel.com filetype:pdf"},
    "coreldraw_vba": {"nombre": "CorelDRAW VBA Programming Guide (automatizacion real)", "tipo": "pdf",
                    "query": "VBA Programming Guide for CorelDRAW filetype:pdf"},
    "facebook":    {"nombre": "Facebook", "tipo": "web",
                    "query": "Facebook centro de ayuda crear publicación página"},
    "instagram":   {"nombre": "Instagram", "tipo": "web",
                    "query": "Instagram centro de ayuda reels publicar"},
    "tiktok":      {"nombre": "TikTok", "tipo": "web",
                    "query": "TikTok centro de ayuda subir video creador"},
}


def _mod(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _web():
    return _mod("web_real", ROOT / "WEB" / "web_real.py")


def _bib():
    return _mod("biblioteca", ROOT / "BIBLIOTECA" / "biblioteca.py")


def catalogo() -> dict:
    """Herramientas que AURORA puede aprender (para el panel)."""
    return {"status": "ok",
            "herramientas": {k: {"nombre": v["nombre"], "tipo": v["tipo"]}
                             for k, v in HERRAMIENTAS.items()}}


def _candidatos_pdf(query: str, n: int = 8) -> list:
    r = _web().buscar(query, n)
    urls = []
    for item in r.get("resultados", []) if isinstance(r, dict) else []:
        u = item.get("url") or item.get("href") or ""
        if u:
            urls.append(u)
    # prioriza los que terminan en .pdf
    return sorted(set(urls), key=lambda u: (0 if u.lower().split("?")[0].endswith(".pdf") else 1))


def _descargar_pdf(url: str, destino: Path) -> dict:
    """Descarga y valida que sea un PDF REAL (magic bytes %PDF)."""
    import requests
    try:
        r = requests.get(url, timeout=45, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (AURORA manual fetch)"})
        if not r.ok:
            return {"ok": False, "detalle": f"HTTP {r.status_code}"}
        primero = next(r.iter_content(chunk_size=1024), b"")
        if not primero.startswith(b"%PDF"):
            return {"ok": False, "detalle": "No es un PDF (sin cabecera %PDF)."}
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, "wb") as f:
            f.write(primero)
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        kb = destino.stat().st_size / 1024
        if kb < 5:
            destino.unlink(missing_ok=True)
            return {"ok": False, "detalle": "PDF demasiado pequeño (sospechoso)."}
        return {"ok": True, "kb": round(kb, 1)}
    except Exception as e:
        return {"ok": False, "detalle": str(e)[:180]}


def aprender(herramienta: str) -> dict:
    """
    Busca el manual de 'herramienta', lo descarga (si es PDF) y lo ingiere a la Biblioteca.
    Para herramientas web, devuelve los enlaces de ayuda oficial (no hay PDF).
    """
    h = HERRAMIENTAS.get((herramienta or "").lower().strip())
    if not h:
        return {"status": "desconocida", "detalle": f"No conozco '{herramienta}'.",
                "disponibles": list(HERRAMIENTAS)}
    if h["tipo"] == "web":
        r = _web().buscar(h["query"], 6)
        enlaces = [{"titulo": it.get("titulo") or it.get("title", ""), "url": it.get("url") or it.get("href", "")}
                   for it in (r.get("resultados", []) if isinstance(r, dict) else [])]
        return {"status": "web", "herramienta": h["nombre"],
                "detalle": "Sin PDF de manual; su ayuda es web. AURORA la lee en vivo (cartucho Web).",
                "enlaces_ayuda": enlaces[:6]}

    # PDF real: probar candidatos hasta que uno descargue como PDF válido
    urls = _candidatos_pdf(h["query"])
    if not urls:
        return {"status": "sin_resultados", "herramienta": h["nombre"],
                "detalle": "La búsqueda no devolvió candidatos. Reintenta o pásame la URL."}
    intentos = []
    for u in urls[:5]:
        destino = DESCARGAS / (herramienta.lower() + ".pdf")
        d = _descargar_pdf(u, destino)
        intentos.append({"url": u, **d})
        if d.get("ok"):
            ing = _bib().ingerir_pdf(str(destino), f"Manual · {h['nombre']}")
            return {"status": "ok", "herramienta": h["nombre"], "url": u,
                    "kb": d["kb"], "ingerido": ing, "intentos": intentos}
    return {"status": "no_descargable", "herramienta": h["nombre"],
            "detalle": "Ningún candidato bajó como PDF válido. Pásame la URL del manual y lo ingiero.",
            "intentos": intentos}


def ingerir_url(herramienta_nombre: str, url: str) -> dict:
    """Ruta manual: Anuar pega la URL exacta del PDF y AURORA lo descarga+ingiere."""
    destino = DESCARGAS / (("".join(c for c in herramienta_nombre.lower() if c.isalnum()) or "manual") + ".pdf")
    d = _descargar_pdf(url, destino)
    if not d.get("ok"):
        return {"status": "error", "detalle": d.get("detalle"), "url": url}
    ing = _bib().ingerir_pdf(str(destino), f"Manual · {herramienta_nombre}")
    return {"status": "ok", "herramienta": herramienta_nombre, "kb": d["kb"], "ingerido": ing}
