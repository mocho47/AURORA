# -*- coding: utf-8 -*-
"""FLUJO MARKETING MILENS — generación y publicación REAL de contenido.

REGLA SAGRADA: nada simulado. Cada paso llama a un motor REAL de AURORA:
  - generar_idea / generar_script / generar_caption → Groq REAL (llama-3.3-70b)
    con el contexto profesional del Asesor (MARKETING/asesor_core.py: conocimiento,
    playbook, construir_brief_para_cerebro).
  - generar_imagen → HONESTO: no hay generador de imágenes conectado; se dice claro
    y se apunta a la videoteca / plantillas existentes. No se inventa ninguna URL.
  - publicar_redes → MARKETING/publicacion_inteligente.py. confirmar=False → dry-run
    real (preparar_publicacion, NO publica). confirmar=True → publicar_hoy(aprobar=True)
    (publicación REAL). Nada se publica sin confirmar=True.
  - monitorear_engagement → métricas REALES vía PUBLICADOR/publicador_core.py
    (comentarios_pagina). Si faltan tokens/datos, lo dice honesto; no inventa números.

Los errores de los motores reales se propagan honestos; no se tapan con datos falsos.
"""
import asyncio
import importlib.util as _ilu
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# ── Rutas: este archivo vive en <ROOT>/AUTH/AUTOMATIONS/ ──
ROOT = Path(__file__).resolve().parent.parent.parent


def _mod(nombre: str, ruta: Path):
    """Carga un módulo real de AURORA por ruta (mismo patrón que publicacion_inteligente)."""
    spec = _ilu.spec_from_file_location(nombre, ruta)
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _cargar_env() -> None:
    """Carga el .env real de AURORA (para GROQ_API_KEY, FB_PAGE_TOKEN, etc.)."""
    env_path = ROOT / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except Exception:
        pass
    # Fallback sin python-dotenv: parsea el .env a mano.
    try:
        import io
        with io.open(env_path, encoding="utf-8") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


def _asesor():
    return _mod("asesor_core", ROOT / "MARKETING" / "asesor_core.py")


def _publicacion():
    return _mod("publicacion_inteligente", ROOT / "MARKETING" / "publicacion_inteligente.py")


def _publicador():
    return _mod("publicador_core", ROOT / "PUBLICADOR" / "publicador_core.py")


def _groq(system_prompt: str, mensaje: str, max_tokens: int = 500,
          temperature: float = 0.8) -> str:
    """Llamada REAL a Groq. Sin API key o sin librería → lanza excepción honesta
    (el flujo la propaga; NO se inventa texto de reemplazo)."""
    _cargar_env()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY ausente en .env: no puedo generar texto real con Groq.")
    from groq import Groq
    client = Groq(api_key=api_key, timeout=30.0)
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": mensaje},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (completion.choices[0].message.content or "").strip()


class FlujoMarketingMilens:
    def __init__(self, negocio: str = "milens"):
        self.nombre = "flujo_marketing_milens"
        self.negocio = negocio
        self.contenido_actual: Dict[str, Any] = {}

    def _brief(self, objetivo: str = "") -> str:
        """Contexto profesional REAL del Asesor (conocimiento de algoritmos + playbook)."""
        ase = _asesor()
        # Sin métricas conectadas → el brief le ordena a Groq NO inventar números.
        return ase.construir_brief_para_cerebro(self.negocio, metricas=None, objetivo=objetivo)

    async def generar_idea(self, tema: str = "bienestar") -> Dict[str, Any]:
        """Paso 1: idea REAL de contenido generada por Groq con el contexto del Asesor."""
        brief = self._brief(objetivo=f"Idea de contenido corto (Reel/TikTok) sobre: {tema}")
        mensaje = (
            f"Genera UNA sola idea concreta y original de video corto vertical (9:16) "
            f"para el negocio {self.negocio.upper()} sobre el tema '{tema}'. "
            f"Responde en 1-2 frases, sin numerar, lista para producir. Español de México."
        )
        idea = _groq(brief, mensaje, max_tokens=180, temperature=0.9)
        self.contenido_actual["idea"] = idea
        self.contenido_actual["tema"] = tema
        return {
            "paso": 1, "accion": "generar_idea", "motor": "Groq (llama-3.3-70b) + asesor_core",
            "tema": tema, "idea": idea, "fuente": "REAL",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def generar_script(self) -> Dict[str, Any]:
        """Paso 2: script REAL de video (Groq) a partir de la idea real."""
        idea = self.contenido_actual.get("idea")
        if not idea:
            raise RuntimeError("No hay idea generada. Ejecuta generar_idea primero.")
        brief = self._brief(objetivo="Guion de video corto con gancho fuerte en 1-3s")
        mensaje = (
            f"Escribe el guion de un video corto vertical (~30s) para {self.negocio.upper()} "
            f"basado en esta idea: \"{idea}\". "
            f"Estructura: GANCHO (1-3s), DESARROLLO, CTA. Marca los tiempos. "
            f"Gancho potente en los primeros segundos. Español de México."
        )
        script = _groq(brief, mensaje, max_tokens=500, temperature=0.8)
        self.contenido_actual["script"] = script
        return {
            "paso": 2, "accion": "generar_script", "motor": "Groq (llama-3.3-70b) + asesor_core",
            "script": script, "caracteres": len(script), "fuente": "REAL",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def generar_imagen(self) -> Dict[str, Any]:
        """Paso 3: HONESTO. No hay generador de imágenes conectado en AURORA.
        No se inventa ninguna URL; se apunta a la videoteca / plantillas reales."""
        return {
            "paso": 3, "accion": "generar_imagen", "fuente": "NO_CONECTADO",
            "status": "SIN_MOTOR",
            "detalle": ("Generación de imagen no conectada en AURORA. Usa contenido existente "
                        "de la videoteca (C:\\Users\\Administrador\\Videos) o plantillas del "
                        "Editor. No se genera ni inventa ninguna imagen/URL."),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def generar_caption(self) -> Dict[str, Any]:
        """Paso 4: caption + hashtags REALES generados por Groq."""
        idea = self.contenido_actual.get("idea", "")
        brief = self._brief(objetivo="Caption viral con CTA y hashtags")
        mensaje = (
            f"Escribe el caption para redes de este video de {self.negocio.upper()} "
            f"(idea: \"{idea}\"). Incluye un gancho, un CTA claro y 4-6 hashtags relevantes. "
            f"Máximo 300 caracteres. Español de México."
        )
        caption = _groq(brief, mensaje, max_tokens=220, temperature=0.85)
        self.contenido_actual["caption"] = caption
        hashtags = [w for w in caption.split() if w.startswith("#")]
        return {
            "paso": 4, "accion": "generar_caption", "motor": "Groq (llama-3.3-70b) + asesor_core",
            "caption": caption, "caracteres": len(caption), "hashtags": len(hashtags),
            "fuente": "REAL", "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def publicar_redes(self, red: str = "facebook", confirmar: bool = False) -> Dict[str, Any]:
        """Paso 5: publicación REAL con salvaguarda.
        confirmar=False → preparar_publicacion (dry-run real, NO publica).
        confirmar=True  → publicar_hoy(aprobar=True) (publica de verdad).
        Nada se publica sin confirmar=True. Errores reales se propagan honestos."""
        pub = _publicacion()
        caption = self.contenido_actual.get("caption", "")
        if not confirmar:
            preparado = pub.preparar_publicacion(self.negocio)
            return {
                "paso": 5, "accion": "publicar_redes", "modo": "DRY_RUN",
                "motor": "publicacion_inteligente.preparar_publicacion",
                "publico": False, "fuente": "REAL",
                "preparado": preparado,
                "nota": "No se publicó nada. Para publicar de verdad: confirmar=True.",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        # ── Publicación REAL ──
        resultado = pub.publicar_hoy(red=red, descripcion=caption, aprobar=True)
        return {
            "paso": 5, "accion": "publicar_redes", "modo": "PUBLICACION_REAL",
            "motor": "publicacion_inteligente.publicar_hoy(aprobar=True)",
            "publico": resultado.get("status") == "PUBLICADO", "red": red,
            "resultado": resultado, "fuente": "REAL",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def monitorear_engagement(self, limite: int = 10) -> Dict[str, Any]:
        """Paso 6: métricas REALES (comentarios de la página FB). Sin tokens/datos,
        lo dice honesto; NO inventa views/likes."""
        pub = _publicador()
        datos = pub.comentarios_pagina(limite=limite)
        return {
            "paso": 6, "accion": "monitorear_engagement",
            "motor": "publicador_core.comentarios_pagina",
            "fuente": "REAL", "datos": datos,
            "nota": ("Métricas reales de Facebook. Views/likes por publicación requieren "
                     "insights de Meta (aún no cableados); no se inventan."),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    async def ejecutar_flujo_completo(self, tema: str = "bienestar",
                                      confirmar: bool = False,
                                      red: str = "facebook") -> Dict[str, Any]:
        """Ciclo completo REAL. Por defecto confirmar=False → NO publica."""
        results: List[Dict[str, Any]] = []
        results.append(await self.generar_idea(tema))
        results.append(await self.generar_script())
        results.append(await self.generar_imagen())
        results.append(await self.generar_caption())
        results.append(await self.publicar_redes(red=red, confirmar=confirmar))
        results.append(await self.monitorear_engagement())
        return {
            "flujo": "marketing_milens", "negocio": self.negocio, "tema": tema,
            "publico_real": confirmar, "pasos": results,
            "timestamp_inicio": datetime.now().isoformat(timespec="seconds"),
            "nota": "Todo generado por motores REALES. Nada simulado.",
        }


if __name__ == "__main__":
    flujo = FlujoMarketingMilens(negocio="milens")
    # Por seguridad: confirmar=False (NO publica).
    resultado = asyncio.run(flujo.ejecutar_flujo_completo("bienestar", confirmar=False))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
