# -*- coding: utf-8 -*-
"""AURORA · Cómo trabaja Anuar de verdad, sacado de su propia PC

Él lo pidió el 2026-08-05: *"obtén todo lo que puedas de cómo trabajo de mi PC,
rasca, escudriña... creo que mi PC tiene mucha más información de mí que yo
mismo"*.

Esto SOLO LEE. No copia, no mueve, no borra. Y mira únicamente lo que dice cómo
TRABAJA: archivos de diseño, productos, clientes, redes, herramientas. Lo
personal no se toca ni se reporta.

El objetivo es concreto: saber qué hace de verdad para que AURORA le quite
trabajo real, no el que uno se imagina.

Correr:  python SETUP/perfil_de_trabajo.py
"""
from __future__ import annotations
import collections
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SALIDA = RAIZ / "_CONTEXTO" / "PERFIL_DE_TRABAJO.md"

# Solo trabajo. Nada personal.
_NO_MIRAR = (
    "appdata", "windows", "program files", "programdata", "$recycle",
    "node_modules", "site-packages", "__pycache__", ".git", ".venv",
    "temp", "cache", "cookies", "historial personal",
)

_DISENO = ("dxf", "cdr", "svg", "ai", "eps", "plt", "nc", "gcode", "rd", "lbrn")
_IMAGEN = ("jpg", "jpeg", "png", "psd", "tif", "webp")
_DOC = ("pdf", "docx", "xlsx", "txt", "csv")
_VIDEO = ("mp4", "mov", "avi", "mkv")


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _saltar(p) -> bool:
    return any(x in str(p).lower() for x in _NO_MIRAR)


def donde_trabaja() -> dict:
    """Qué carpetas tienen su trabajo de verdad, y cuál está viva."""
    carpetas = collections.Counter()
    recientes = collections.Counter()
    hace_30 = datetime.now() - timedelta(days=30)
    total = 0
    for base in (Path.home() / "Downloads", Path.home() / "Documents",
                 Path.home() / "Desktop", Path.home() / "Pictures",
                 Path.home() / "Videos"):
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_file() or _saltar(p):
                    continue
                ext = p.suffix.lower().lstrip(".")
                if ext not in _DISENO + _IMAGEN + _DOC + _VIDEO:
                    continue
                total += 1
                carpetas[str(p.parent)] += 1
                try:
                    if datetime.fromtimestamp(p.stat().st_mtime) > hace_30:
                        recientes[str(p.parent)] += 1
                except OSError:
                    pass
        except (OSError, PermissionError):
            continue
    return {"total": total,
            "carpetas": carpetas.most_common(15),
            "vivas_30dias": recientes.most_common(10)}


def que_produce() -> dict:
    """Qué hace de verdad, leído de los NOMBRES de sus archivos."""
    palabras = collections.Counter()
    por_tipo = collections.Counter()
    _vacias = {"copia", "copy", "final", "nuevo", "new", "sin", "titulo",
               "documento", "imagen", "archivo", "descarga", "whatsapp",
               "image", "img", "screenshot", "captura", "www", "com", "http",
               "dxf", "cdr", "svg", "pdf", "jpg", "png", "mp4", "the", "and",
               "for", "with", "free", "download", "vector", "file", "files"}
    for base in (Path.home() / "Downloads", Path.home() / "Documents",
                 Path.home() / "Desktop", Path.home() / "Pictures"):
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_file() or _saltar(p):
                    continue
                ext = p.suffix.lower().lstrip(".")
                if ext not in _DISENO + _IMAGEN:
                    continue
                por_tipo[ext] += 1
                for w in re.findall(r"[a-záéíóúñü]{4,}", p.stem.lower()):
                    if w not in _vacias and not w.isdigit():
                        palabras[w] += 1
        except (OSError, PermissionError):
            continue
    return {"por_tipo": por_tipo.most_common(12),
            "temas": palabras.most_common(40)}


def sus_redes() -> dict:
    """Qué redes usa de verdad, de la configuración real de AURORA."""
    redes = {}
    env = RAIZ / ".env"
    if env.exists():
        try:
            txt = env.read_text(encoding="utf-8", errors="replace")
            # SOLO los NOMBRES de las variables: nunca los valores.
            for linea in txt.splitlines():
                if "=" not in linea or linea.strip().startswith("#"):
                    continue
                clave = linea.split("=", 1)[0].strip()
                valor = linea.split("=", 1)[1].strip()
                for red in ("FACEBOOK", "FB_", "INSTAGRAM", "IG_", "TIKTOK",
                            "YOUTUBE", "WHATSAPP", "GREEN_API", "TELEGRAM",
                            "META", "GOOGLE", "GROQ", "GEMINI", "MELI"):
                    if red in clave.upper():
                        redes[clave] = "configurada" if valor and len(valor) > 8 else "VACÍA"
        except Exception:
            pass
    return redes


def su_catalogo() -> dict:
    """Qué vende, de sus catálogos reales."""
    salida = {}
    for f in sorted((RAIZ / "CONFIG").glob("*.json")):
        if not any(k in f.name for k in ("catalogo", "precio", "servicio")):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            s = json.dumps(d, ensure_ascii=False)
            salida[f.name] = {"kb": round(f.stat().st_size / 1024, 1),
                              "productos": s.count('"nombre"') or s.count('"producto"')}
        except Exception:
            pass
    return salida


def cuando_trabaja() -> dict:
    """A qué horas y días crea archivos: su ritmo real."""
    horas = collections.Counter()
    dias = collections.Counter()
    _dias = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
    for base in (Path.home() / "Downloads", Path.home() / "Documents",
                 Path.home() / "Pictures"):
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_file() or _saltar(p):
                    continue
                if p.suffix.lower().lstrip(".") not in _DISENO + _IMAGEN:
                    continue
                try:
                    t = datetime.fromtimestamp(p.stat().st_mtime)
                    horas[t.hour] += 1
                    dias[_dias[t.weekday()]] += 1
                except (OSError, ValueError):
                    pass
        except (OSError, PermissionError):
            continue
    return {"horas": horas.most_common(8), "dias": dias.most_common(7)}


def main() -> int:
    _consola_utf8()
    print("Leyendo cómo trabajas de verdad. SOLO se lee, nada se toca.")
    print("=" * 74)

    d = donde_trabaja()
    print(f"\n=== ARCHIVOS DE TRABAJO: {d['total']}")
    print("  Donde está tu trabajo:")
    for c, n in d["carpetas"][:8]:
        print(f"   {n:6}  {c[:66]}")
    print("\n  Lo VIVO (últimos 30 días):")
    for c, n in d["vivas_30dias"][:6]:
        print(f"   {n:6}  {c[:66]}")

    q = que_produce()
    print("\n=== QUÉ PRODUCES")
    print("  Por tipo de archivo:")
    for e, n in q["por_tipo"]:
        print(f"   {n:6}  .{e}")
    print("\n  Los temas de tus diseños (de los nombres de archivo):")
    linea = []
    for w, n in q["temas"][:30]:
        linea.append(f"{w}({n})")
    print("   " + " · ".join(linea))

    r = sus_redes()
    print(f"\n=== TUS INTEGRACIONES ({len(r)})")
    for k, v in sorted(r.items()):
        marca = "OK " if v == "configurada" else "-- "
        print(f"   {marca} {k:32} {v}")

    c = su_catalogo()
    print("\n=== TUS CATÁLOGOS")
    for f, info in c.items():
        print(f"   {f:34} {info['productos']:4} productos  {info['kb']} KB")

    t = cuando_trabaja()
    print("\n=== TU RITMO")
    print("  Horas en que más produces:")
    for h, n in t["horas"]:
        print(f"   {h:02d}:00  {'█' * min(40, n // 12)} {n}")
    print("  Días:")
    for dia, n in t["dias"]:
        print(f"   {dia:11} {'█' * min(40, n // 12)} {n}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        "# Cómo trabaja Anuar — leído de su propia PC\n\n"
        f"Generado el {datetime.now():%Y-%m-%d %H:%M}. Solo lectura.\n\n"
        f"```json\n{json.dumps({'donde': d, 'produce': q, 'redes': r, 'catalogos': c, 'ritmo': t}, ensure_ascii=False, indent=2, default=str)[:20000]}\n```\n",
        encoding="utf-8")
    print(f"\nGuardado en: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
