# -*- coding: utf-8 -*-
"""AURORA · FÁBRICA DE MOTORES (cartucho generador).

Anuar describe en lenguaje natural QUÉ debe hacer un motor nuevo y AURORA lo
GENERA: escribe un archivo .py autónomo que cumple un CONTRATO UNIVERSAL, de
modo que sea portátil y compatible con la versión genérica (no depende de nada
interno de AURORA, solo stdlib + requests).

CONTRATO que cumple cada motor generado:
  - META = {"id": str, "nombre": str, "descripcion": str, "categoria": str}
  - def ejecutar(accion: str = "", datos: dict = None) -> dict  (siempre {"status": ...})
  - Solo librería estándar de Python + requests.

SEGURIDAD: todo lo generado se compila con py_compile ANTES de guardarse (no se
guarda código roto) y toda carga/ejecución de motores va con try/except para que
un motor defectuoso NUNCA tumbe el servidor.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import traceback
import unicodedata
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CUSTOM_DIR = ROOT / "MOTORES_CUSTOM"
ENV_FILE = ROOT / ".env"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


# ── utilidades ────────────────────────────────────────────────────────
def _slug(nombre: str) -> str:
    """Convierte un nombre a un identificador de archivo seguro (a-z0-9_)."""
    s = (nombre or "").lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or ("motor_" + uuid.uuid4().hex[:8])


def _groq_key() -> str:
    """Toma la GROQ_API_KEY del entorno o del .env de AURORA."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GROQ_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _limpia_fences(codigo: str) -> str:
    """Quita ```python ... ``` u otros fences de markdown si Groq los mete."""
    t = (codigo or "").strip()
    if t.startswith("```"):
        # elimina la primera línea de apertura (```python / ```)
        t = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", t)
        # elimina el fence de cierre
        t = re.sub(r"\n```\s*$", "", t).strip()
    # por si quedaron fences sueltos en medio
    t = t.replace("```python", "").replace("```", "").strip()
    return t


def _groq(messages: list, temperature: float = 0.2) -> str:
    """Llama a Groq y devuelve el texto de la respuesta (o lanza excepción)."""
    key = _groq_key()
    import time
    if key:
        for intento in range(4):
            try:
                r = requests.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": GROQ_MODEL, "messages": messages,
                          "temperature": temperature, "max_tokens": 2048},
                    timeout=60,
                )
            except Exception:
                break  # sin conexión → respaldo LOCAL
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            if r.status_code == 429 and intento < 3:   # rate limit: esperar y reintentar
                mm = re.search(r"try again in ([0-9.]+)s", r.text)
                time.sleep(min((float(mm.group(1)) + 1.0) if mm else 10.0, 30))
                continue
            break  # otro error → respaldo LOCAL
    # RESPALDO LOCAL sin internet (Ollama llama3.2:3b) — la Fábrica crea aunque no haya nube
    try:
        rr = requests.post("http://127.0.0.1:11434/api/chat",
                           json={"model": "llama3.2:3b", "messages": messages, "stream": False},
                           timeout=180)
        if rr.status_code == 200:
            return (rr.json().get("message", {}).get("content") or "").strip()
    except Exception:
        pass
    raise RuntimeError("No hay cerebro disponible (ni Groq nube ni Ollama local).")


# ── EL PULSO DE CREACIÓN heredado a AURORA ────────────────────────────
# La VISIÓN y el oficio los pone Anuar (dueño). Esta es la LÓGICA DE INGENIERÍA
# —la forma de construir un motor de primer nivel— heredada para servir esa visión.
_MANIFIESTO_CREACION = """Eres el CEREBRO DE CREACIÓN de AURORA: construyes motores nuevos de Python con el oficio de un ingeniero de software de primerísimo nivel, al servicio de la visión de Anuar, dueño de un taller (sublimación, corte láser, DTF, prendas, faros). Tu código es REAL, honesto e impecable. NUNCA simulas.

═══ FILOSOFÍA (inquebrantable) ═══
- NADA simulado, NADA de mocks, NADA de placeholders, NADA a medias. Datos reales o el motor lo DICE.
- Si falta un dato o algo falla, el motor devuelve status "error" con un mensaje claro y accionable; JAMÁS inventa un valor ni finge éxito.
- Primer nivel: escribe como si el negocio de una persona dependiera de que funcione — porque así es.

═══ CONTRATO UNIVERSAL (obligatorio, portátil) ═══
- META = {"id","nombre","descripcion","categoria"} a nivel de módulo.
- def ejecutar(accion: str = "", datos: dict = None) -> dict  → SIEMPRE devuelve dict con clave "status" ("ok"|"error").
- datos None se trata como {}. accion vacía = una acción por defecto razonable (documenta las que soporta).
- Puedes usar la librería estándar de Python + requests + el ARSENAL instalado (abajo). NO importes módulos internos de AURORA (usa las librerías directamente): así el motor queda limpio y autónomo.

═══ ARSENAL DISPONIBLE (librerías REALES ya instaladas — úsalas cuando aporten) ═══
- ezdxf → leer/crear/transformar DXF (corte y grabado láser): medidas, escalado, splines→polilíneas, bbox.
- cv2 (OpenCV) + numpy → procesamiento de imagen: filtros, Canny, XDoG, umbral, morfología, detección de caras (haarcascades).
- rembg → quitar fondo con IA (modelos u2net y u2net_human_seg para personas).
- PIL/Pillow → abrir/convertir/componer/guardar imágenes.
- fitz (PyMuPDF) → PDF: renderizar a 300 DPI, extraer texto e imágenes.
- vtracer → vectorizar raster a SVG.
- ddgs → búsqueda web, imágenes y noticias EN VIVO (from ddgs import DDGS).
- psutil → estado del sistema (CPU, RAM, disco, procesos).
- sqlite3 (stdlib) → persistencia local real (crea tu propia .db si el motor necesita guardar datos).
- Groq (LLM) → razonamiento/generación de texto: POST a https://api.groq.com/openai/v1/chat/completions, modelo "llama-3.1-8b-instant", con la GROQ_API_KEY del entorno (os.environ). Úsalo para motores que entiendan lenguaje, redacten, clasifiquen o decidan.
Elige del arsenal SOLO lo que el motor de verdad necesite; si con stdlib basta, no metas dependencias.

═══ DISEÑO ═══
- Piensa primero el problema del negocio. Define acciones claras y nómbralas bien.
- Cada acción: entradas explícitas (qué claves espera en datos y sus tipos), salida explícita, errores posibles.
- Funciones pequeñas, un solo propósito. Nombres en español que se expliquen solos.

═══ ROBUSTEZ Y ERRORES ═══
- Valida TODA entrada: presencia, tipo, rango. Convierte con cuidado (try/except en float/int).
- Envuelve toda operación que pueda fallar y tradúcela a {"status":"error","mensaje":...}. El caller NUNCA recibe una excepción cruda.
- requests: SIEMPRE con timeout; valida status_code; maneja sin conexión.
- Sin estado global frágil; determinista cuando aplique.

═══ SEGURIDAD ═══
- Nunca ejecutes comandos destructivos ni borres/sobrescribas sin validar la ruta. No expongas secretos. No confíes ciegamente en entradas externas.

═══ CALIDAD ═══
- Docstring de módulo (qué hace y qué acciones) y de funciones. Comentarios solo donde aportan.
- Bloque if __name__ == "__main__" con una PRUEBA REAL que ejercite la acción principal con datos de ejemplo.
- Código limpio, sin imports sin usar.

Respondes ÚNICAMENTE con el código Python COMPLETO del archivo. SIN explicaciones. SIN fences de markdown."""


_CONTRATO = (
    "Genera UN archivo .py completo de un 'motor' para AURORA que cumpla EXACTAMENTE "
    "este contrato universal (portátil, sin depender de nada interno de AURORA):\n"
    "1) Debe definir la variable global META = {\"id\": str, \"nombre\": str, "
    "\"descripcion\": str, \"categoria\": str}.\n"
    "2) Debe definir la función: def ejecutar(accion: str = \"\", datos: dict = None) -> dict\n"
    "   - datos puede ser None; trátalo como diccionario vacío si lo es.\n"
    "   - SIEMPRE debe devolver un dict que incluya la clave \"status\" con valor "
    "\"ok\" o \"error\".\n"
    "   - Ante cualquier fallo o dato faltante, devuelve {\"status\": \"error\", "
    "\"mensaje\": ...} en lugar de lanzar excepción.\n"
    "3) Puedes usar la librería estándar + requests + el ARSENAL instalado (ezdxf, cv2/numpy, "
    "rembg, PIL, fitz/PyMuPDF, vtracer, ddgs, psutil, sqlite3) y Groq (LLM) vía requests. "
    "Usa solo lo que el motor necesite. PROHIBIDO importar módulos internos de AURORA.\n"
    "4) Incluye un bloque if __name__ == '__main__' con una prueba mínima.\n"
    "REGLAS DE SALIDA: responde ÚNICAMENTE con el código Python del archivo. "
    "NADA de explicaciones. NADA de markdown ni ``` fences."
)


def _validar_compila(codigo: str) -> tuple[bool, str]:
    """Compila el código en un temporal con py_compile. (ok, error)."""
    import py_compile
    tmp = Path(tempfile.gettempdir()) / f"aurora_fabrica_{uuid.uuid4().hex}.py"
    try:
        tmp.write_text(codigo, encoding="utf-8")
        py_compile.compile(str(tmp), doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass


def _cargar_desde_ruta(ruta: Path):
    """Importa un módulo .py de forma aislada (devuelve el módulo o lanza)."""
    spec = importlib.util.spec_from_file_location(f"motor_custom_{ruta.stem}", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _leer_meta(ruta: Path) -> dict:
    """Intenta cargar el módulo y leer su META (con try/except)."""
    try:
        mod = _cargar_desde_ruta(ruta)
        meta = getattr(mod, "META", None)
        if isinstance(meta, dict):
            return meta
    except Exception:
        pass
    return {}


def _registrar_autoconocimiento(meta: dict, slug: str) -> None:
    """AURORA se AUTO-RECONOCE al crecer: registra la nueva habilidad en su
    autoconocimiento. La VISIÓN es de Anuar; la habilidad recién creada pasa a ser
    parte de lo que AURORA sabe que puede hacer. Best-effort — nunca rompe la creación."""
    from datetime import datetime
    reg = ROOT / "CONFIG" / "motores_creados.json"
    try:
        data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else []
    except Exception:
        data = []
    data = [m for m in data if m.get("slug") != slug]           # sin duplicados
    data.append({"slug": slug, "meta": meta,
                 "creado": datetime.now().isoformat(timespec="seconds")})
    try:
        reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    for cand in (ROOT / "CEREBRO" / "auto_conocimiento.py",
                 ROOT / "MOTORES" / "auto_conocimiento.py",
                 ROOT / "MOTORES" / "motor_auto_conocimiento.py"):
        try:
            if cand.exists():
                m = _cargar_desde_ruta(cand)
                for fn_name in ("registrar_habilidad", "registrar_motor",
                                "notificar_capacidad", "aprender"):
                    fn = getattr(m, fn_name, None)
                    if callable(fn):
                        try:
                            fn({"tipo": "motor_creado", "slug": slug, "meta": meta})
                        except Exception:
                            pass
                        return
                return
        except Exception:
            pass


# ── API PÚBLICA ───────────────────────────────────────────────────────
def crear_motor(nombre: str, descripcion: str) -> dict:
    """Genera con Groq un motor .py que cumple el contrato, lo valida con
    py_compile (1 reintento si falla) y lo guarda en MOTORES_CUSTOM/<slug>.py.

    Devuelve {"status":"ok","archivo":ruta,"meta":META} o
    {"status":"error","detalle":...} sin guardar código roto.
    """
    if not nombre or not nombre.strip():
        return {"status": "error", "detalle": "El nombre es obligatorio."}
    if not descripcion or not descripcion.strip():
        return {"status": "error", "detalle": "La descripción es obligatoria."}

    slug = _slug(nombre)

    # ── FASE 1 · DISEÑO (pensar el motor antes de escribirlo) ──
    diseno = ""
    try:
        diseno = _groq([
            {"role": "system", "content": _MANIFIESTO_CREACION},
            {"role": "user", "content": (
                f"Diseña (NO codifiques todavía) el motor '{nombre}'. Objetivo de Anuar:\n{descripcion}\n\n"
                "En 6-10 líneas define: acciones que soportará (con su nombre), qué claves espera en "
                "'datos' cada acción y sus tipos, qué devuelve, y qué errores debe manejar. Solo el diseño.")},
        ], temperature=0.2)
    except Exception:
        diseno = ""

    prompt_user = (
        f"{_CONTRATO}\n\n"
        f"El motor se llama: {nombre}\n"
        f"Su id (para META['id']) debe ser: {slug}\n"
        f"Lo que debe hacer (Anuar):\n{descripcion}\n"
    )
    if diseno:
        prompt_user += f"\nDISEÑO a respetar:\n{diseno}\n"
    messages = [
        {"role": "system", "content": _MANIFIESTO_CREACION},
        {"role": "user", "content": prompt_user},
    ]

    # ── FASE 2 · GENERAR ──
    try:
        codigo = _limpia_fences(_groq(messages))
    except Exception as e:
        return {"status": "error", "detalle": f"Groq falló: {e}"}

    ok, err = _validar_compila(codigo)
    if not ok:  # reintento por error de compilación
        try:
            codigo = _limpia_fences(_groq(messages + [
                {"role": "assistant", "content": codigo},
                {"role": "user", "content": (
                    "El código NO compila. Error exacto:\n" + err +
                    "\nCorrige y devuelve el .py COMPLETO. Solo código, sin fences.")},
            ]))
            ok, err = _validar_compila(codigo)
        except Exception as e:
            return {"status": "error", "detalle": f"Reintento Groq falló: {e}"}
    if not ok:
        return {"status": "error", "detalle": f"El código no compila: {err}"}

    # ── FASE 3 · AUTO-CRÍTICA (revisar el propio código contra la doctrina) ──
    try:
        mejor = _limpia_fences(_groq([
            {"role": "system", "content": _MANIFIESTO_CREACION},
            {"role": "user", "content": (
                "Revisa TU propio motor contra la doctrina y mejóralo: ¿valida todas las entradas? "
                "¿hay algún valor simulado/inventado? ¿algún fallo sin atrapar? ¿ejecutar SIEMPRE "
                "devuelve status? ¿requests con timeout? Devuelve el .py COMPLETO ya corregido "
                "(si ya estaba impecable, devuélvelo igual). Solo código, sin fences.\n\n=== CÓDIGO ===\n" + codigo)},
        ], temperature=0.1))
        ok2, _ = _validar_compila(mejor)
        if ok2 and len(mejor) > 60:
            codigo = mejor
    except Exception:
        pass

    # ── FASE 4 · GUARDAR (solo si compila) + AUTOCONOCIMIENTO ──
    try:
        CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
        ruta = CUSTOM_DIR / f"{slug}.py"
        ruta.write_text(codigo, encoding="utf-8")
    except Exception as e:
        return {"status": "error", "detalle": f"No se pudo guardar: {e}"}

    meta = _leer_meta(ruta)
    _registrar_autoconocimiento(meta, slug)
    return {"status": "ok", "archivo": str(ruta), "slug": slug, "meta": meta,
            "diseno": diseno[:800], "autoconocimiento": "registrado"}


def listar_motores_custom() -> dict:
    """Lista los .py de MOTORES_CUSTOM con su META (carga aislada, tolerante)."""
    motores = []
    if CUSTOM_DIR.exists():
        for ruta in sorted(CUSTOM_DIR.glob("*.py")):
            if ruta.name.startswith("_"):
                continue
            motores.append({
                "slug": ruta.stem,
                "archivo": str(ruta),
                "meta": _leer_meta(ruta),
            })
    return {"status": "ok", "total": len(motores), "motores": motores}


def probar_motor(slug: str, accion: str = "", datos: dict = None) -> dict:
    """Carga el motor <slug> con importlib y ejecuta ejecutar(accion, datos).

    Blindado con try/except: un motor roto NO revienta, devuelve error.
    """
    ruta = CUSTOM_DIR / f"{_slug(slug) if '/' not in slug else slug}.py"
    if not ruta.exists():
        ruta = CUSTOM_DIR / f"{slug}.py"
    if not ruta.exists():
        return {"status": "error", "mensaje": f"No existe el motor '{slug}'."}
    try:
        mod = _cargar_desde_ruta(ruta)
    except Exception as e:
        return {"status": "error", "mensaje": f"El motor no cargó: {e}",
                "traza": traceback.format_exc()[-800:]}
    fn = getattr(mod, "ejecutar", None)
    if not callable(fn):
        return {"status": "error", "mensaje": "El motor no expone ejecutar()."}
    try:
        res = fn(accion, datos or {})
    except Exception as e:
        return {"status": "error", "mensaje": f"ejecutar() lanzó: {e}",
                "traza": traceback.format_exc()[-800:]}
    if not isinstance(res, dict):
        return {"status": "error", "mensaje": "ejecutar() no devolvió un dict.",
                "resultado_crudo": str(res)[:400]}
    return {"status": "ok", "resultado": res, "meta": getattr(mod, "META", {})}


if __name__ == "__main__":
    print(">> Fábrica de motores — prueba end-to-end")
    r = crear_motor(
        "Conversor MXN a USD",
        "convierte una cantidad de pesos MXN a dólares USD usando un tipo de "
        "cambio dado en datos['tc']. El monto viene en datos['monto'].",
    )
    print("crear_motor:", json.dumps(r, ensure_ascii=False, indent=2))
    if r.get("status") == "ok":
        print("\nlistar_motores_custom:",
              json.dumps(listar_motores_custom(), ensure_ascii=False, indent=2))
        prueba = probar_motor(r["slug"], "", {"monto": 100, "tc": 17})
        print("\nprobar_motor:", json.dumps(prueba, ensure_ascii=False, indent=2))
