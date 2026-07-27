# -*- coding: utf-8 -*-
"""
Adaptadores de módulos existentes al bus neuronal de AURORA.
Convierte módulos function-based en motores compatibles con la Consciencia.
"""
import asyncio, sys, logging
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
logger = logging.getLogger("aurora.adaptadores")

# ── ORACLE — CRM real ─────────────────────────────────────────────

PROMPT_ORACLE = """Eres el sistema CRM ORACLE de AURORA. Gestinas leads y órdenes reales de ATF Retrofit y MILENS.
Tienes acceso a la base de datos SQLite con todos los leads, órdenes y resúmenes del negocio.
Siempre reporta números reales, nunca estimados. Si un lead no existe, dilo directamente."""

class MotorOracle:
    motor_id = "motor_oracle"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "ORACLE"))
        try:
            import oracle_core as _o
            _o.init_db()
            self._o = _o
        except Exception as e:
            self._o = None
            logger.warning(f"ORACLE: {e}")

    async def listar_leads(self, estado: str = None) -> Dict:
        if not self._o: return {"error": "ORACLE no disponible"}
        return await asyncio.to_thread(self._o.listar_leads, estado)

    async def crear_lead(self, nombre: str, telefono: str = "", negocio: str = "ATF") -> Dict:
        if not self._o: return {"error": "ORACLE no disponible"}
        return await asyncio.to_thread(self._o.crear_lead, nombre, telefono, negocio)

    async def resumen(self, negocio: str = None) -> Dict:
        if not self._o: return {"error": "ORACLE no disponible"}
        return await asyncio.to_thread(self._o.resumen, negocio)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._o is not None}


# ── VENDEDOR — fichas técnicas y técnicas de venta ────────────────

PROMPT_VENDEDOR = """Eres el especialista en ventas técnicas de ATF Retrofit y MILENS.
Tienes acceso a todas las fichas técnicas de productos, técnicas de venta probadas y catálogos.
Usa datos reales de las fichas. Margen ATF: 120%. Precio: $1,500–$8,000 MXN instalado."""

class MotorFichas:
    motor_id = "motor_fichas"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "VENDEDOR"))
        try:
            import vendedor_core as _v
            self._v = _v
        except Exception as e:
            self._v = None
            logger.warning(f"VENDEDOR: {e}")

    async def ficha(self, producto: str) -> Dict:
        if not self._v: return {"error": "Vendedor no disponible"}
        return await asyncio.to_thread(self._v.ficha, producto)

    async def listar_fichas(self) -> Dict:
        if not self._v: return {"error": "Vendedor no disponible"}
        return await asyncio.to_thread(self._v.listar_fichas)

    async def tecnicas(self, nombre: str = None) -> Dict:
        if not self._v: return {"error": "Vendedor no disponible"}
        return await asyncio.to_thread(self._v.tecnicas, nombre)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._v is not None}


# ── TALLER — DXF, vectorizado, láser ─────────────────────────────

PROMPT_TALLER = """Eres el motor de taller digital de AURORA para MILENS. 
Conviertes imágenes a DXF, vectorizas diseños y preparas archivos para grabado láser.
Siempre verificas disponibilidad de Inkscape antes de operar."""

class MotorTaller:
    motor_id = "motor_taller"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "TALLER"))
        try:
            import taller_core as _t
            self._t = _t
        except Exception as e:
            self._t = None

    async def convertir_dxf(self, ruta: str) -> Dict:
        if not self._t: return {"error": "Taller no disponible"}
        return await asyncio.to_thread(self._t.convertir_a_dxf, ruta)

    async def vectorizar(self, ruta: str) -> Dict:
        if not self._t: return {"error": "Taller no disponible"}
        return await asyncio.to_thread(self._t.vectorizar, ruta)

    async def catalogo(self) -> Dict:
        if not self._t: return {"error": "Taller no disponible"}
        return await asyncio.to_thread(self._t.catalogo)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._t is not None,
                "inkscape": self._t.disponible() if self._t else False}


# ── SUBLIMACION — lienzos, frames de video ────────────────────────

PROMPT_SUBLIMACION = """Eres el motor de sublimación y edición multimedia de AURORA.
Preparas lienzos para impresión, extraes frames de video y montas imágenes en plantillas.
Trabajas con archivos reales en disco. Siempre validas que el archivo exista."""

class MotorSublimacion:
    motor_id = "motor_sublimacion"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "SUBLIMACION"))
        try:
            import sublimacion_core as _s
            self._s = _s
        except Exception as e:
            self._s = None

    async def frames_de_video(self, ruta: str, fps: int = 1) -> Dict:
        if not self._s: return {"error": "Sublimación no disponible"}
        return await asyncio.to_thread(self._s.de_video, ruta, fps)

    async def lienzo_blanco(self, ancho_cm: float = 21, alto_cm: float = 29.7) -> Dict:
        if not self._s: return {"error": "Sublimación no disponible"}
        return await asyncio.to_thread(self._s.lienzo_blanco, ancho_cm, alto_cm)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._s is not None}


# ── PUBLICADOR — FB, Instagram, WA ───────────────────────────────

PROMPT_PUBLICADOR = """Eres el motor de publicación real de AURORA en redes sociales.
Publicas en Facebook, Instagram y WhatsApp usando APIs reales.
Nunca simulas publicaciones. Si no hay token válido, lo dices directamente."""

class MotorPublicador:
    motor_id = "motor_publicador"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "PUBLICADOR"))
        try:
            import publicador_core as _p
            self._p = _p
        except Exception as e:
            self._p = None

    async def publicar(self, plataforma: str, texto: str, imagen: str = "") -> Dict:
        if not self._p: return {"error": "Publicador no disponible"}
        return await asyncio.to_thread(self._p.publicar, plataforma, texto, imagen)

    async def estado_redes(self) -> Dict:
        if not self._p: return {"error": "Publicador no disponible"}
        return await asyncio.to_thread(self._p.estado_redes)

    async def enviar_whatsapp(self, telefono: str, mensaje: str) -> Dict:
        if not self._p: return {"error": "Publicador no disponible"}
        return await asyncio.to_thread(self._p.enviar_whatsapp, telefono, mensaje)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._p is not None}


# ── VOZ — TTS Google ──────────────────────────────────────────────

PROMPT_VOZ = """Eres el motor de voz de AURORA. Conviertes texto a voz usando Google TTS.
Hablas con la voz de AURORA en el dispositivo de audio del usuario."""

class MotorVoz:
    motor_id = "motor_voz"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "VOZ"))
        try:
            import voz_google as _v
            self._v = _v
        except Exception as e:
            self._v = None

    async def hablar(self, texto: str, dispositivo: str = "oficina") -> Dict:
        if not self._v: return {"error": "Voz no disponible"}
        try:
            await asyncio.to_thread(self._v.hablar_google, texto, dispositivo)
            return {"status": "OK", "texto": texto[:100]}
        except Exception as e:
            return {"error": str(e)[:200]}

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._v is not None}


# ── ASESOR MARKETING ──────────────────────────────────────────────

PROMPT_ASESOR = """Eres el asesor de marketing estratégico de AURORA para ATF y MILENS.
Analizas métricas reales, propones estrategias de contenido y campañas accionables.
Siempre orientado a conversión real, no métricas de vanidad."""

class MotorAsesor:
    motor_id = "motor_asesor"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "MARKETING"))
        try:
            import asesor_core as _a
            self._a = _a
        except Exception as e:
            self._a = None

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._a is not None}


# ── EDITOR IMÁGENES ───────────────────────────────────────────────

PROMPT_EDITOR = """Eres el editor de imágenes de AURORA: quitas fondos, preparas para láser,
recolorizas, redimensionas y generas trazados B&N para grabado. Trabajas con archivos reales."""

class MotorEditor:
    motor_id = "motor_editor"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "EDITOR"))
        try:
            import conversiones as _e
            self._e = _e
        except Exception as e:
            self._e = None

    async def quitar_fondo(self, ruta: str) -> Dict:
        if not self._e: return {"error": "Editor no disponible"}
        return await asyncio.to_thread(self._e.quitar_fondo, ruta)

    async def preparar_laser(self, ruta: str) -> Dict:
        if not self._e: return {"error": "Editor no disponible"}
        return await asyncio.to_thread(self._e.a_bw_puro, ruta)

    async def linea_byn(self, ruta: str) -> Dict:
        if not self._e: return {"error": "Editor no disponible"}
        return await asyncio.to_thread(self._e.a_linea, ruta)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._e is not None}


# ── BUSCADOR WEB ──────────────────────────────────────────────────

PROMPT_BUSCADOR = """Eres el motor de búsqueda web real de AURORA.
Buscas precios de competencia, tendencias del mercado, información de productos y noticias relevantes.
Solo reportas información real encontrada en la web."""

class MotorBuscador:
    motor_id = "motor_buscador"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "CORE"))
        try:
            from buscador_web_profesional import BuscadorWebProfesional
            self._b = BuscadorWebProfesional()
        except Exception as e:
            self._b = None

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._b is not None}


# ── PROGRAMADOR / AGENDADOR ───────────────────────────────────────

PROMPT_PROGRAMADOR = """Eres el motor de programación y agendamiento de AURORA.
Agenda tareas, recordatorios y acciones automáticas en el sistema."""

class MotorProgramador:
    motor_id = "motor_programador"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "AGENDA"))
        try:
            import agenda as _ag
            self._ag = _ag
        except Exception as e:
            self._ag = None

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._ag is not None}


# ── COREL — control real de CorelDRAW por COM ─────────────────────

PROMPT_COREL = """Eres el motor de control de CorelDRAW de AURORA. Operas el CorelDRAW real
abierto en la PC (por COM): lees el documento activo, exportas a PDF y cambias tamaño de página.
Nunca simulas un resultado — si Corel no está abierto o algo falla, lo dices directamente."""

class MotorCorel:
    motor_id = "motor_corel"
    def __init__(self):
        sys.path.insert(0, str(ROOT / "EDITOR"))
        try:
            import corel_core as _c
            self._c = _c
        except Exception as e:
            self._c = None
            logger.warning(f"COREL: {e}")

    async def info_documento(self) -> Dict:
        if not self._c: return {"error": "Corel no disponible"}
        return await asyncio.to_thread(self._c.info_documento)

    async def exportar_pdf(self, ruta_salida: str) -> Dict:
        if not self._c: return {"error": "Corel no disponible"}
        return await asyncio.to_thread(self._c.exportar_pdf, ruta_salida)

    async def escalar_pagina(self, ancho_cm: float, alto_cm: float, en_documento_nuevo: bool = False) -> Dict:
        if not self._c: return {"error": "Corel no disponible"}
        return await asyncio.to_thread(self._c.escalar_pagina, ancho_cm, alto_cm, en_documento_nuevo)

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "disponible": self._c.disponible() if self._c else False}


# ── CATÁLOGO DE ADAPTADORES ───────────────────────────────────────
# Mapa: motor_id → clase adaptadora
ADAPTADORES_CATALOGO = {
    "motor_oracle":       MotorOracle,
    "motor_fichas":       MotorFichas,
    "motor_taller":       MotorTaller,
    "motor_sublimacion":  MotorSublimacion,
    "motor_publicador":   MotorPublicador,
    "motor_voz":          MotorVoz,
    "motor_asesor":       MotorAsesor,
    "motor_editor":       MotorEditor,
    "motor_buscador":     MotorBuscador,
    "motor_programador":  MotorProgramador,
    "motor_corel":        MotorCorel,
}
