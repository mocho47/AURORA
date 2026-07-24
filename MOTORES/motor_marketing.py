# -*- coding: utf-8 -*-
"""
🚀 AURORA — MOTOR MARKETING COGNITIVO
Genera contenido viral real para ATF usando memoria acumulada.
Lee qué funcionó → genera mejor contenido → aprende del resultado.
Ruta: C:/AURORA/MOTORES/motor_marketing.py
"""
import asyncio, json, logging, os
from datetime import datetime
from typing import Dict, List, Optional
from groq import AsyncGroq

logger = logging.getLogger("aurora.motor_marketing")

PROMPT_MARKETING = """Eres el estratega de marketing viral de ATF Retrofit — iluminación automotriz México.
Especialidad: contenido que VENDE. Hooks que detienen el scroll. Captions que convierten.
Formato siempre real por plataforma: TikTok (hook 3s + trend), Instagram (visual + CTA), YouTube (thumbnail + title SEO), Facebook (comunidad + FOMO).
Producto: retrofit LED de faros, iluminación automotriz premium. Margen 120%. Precio $1,500–$8,000 MXN instalado.
Buyer persona: hombre 20-40 años, le gusta su carro, quiere diferenciarse, poder adquisitivo medio-alto.
NUNCA inventes métricas. SIEMPRE propone contenido accionable y grabable HOY."""

_MODELO = "llama-3.1-8b-instant"

PLATAFORMAS = {
    "tiktok":     {"duracion": "15-60s", "formato": "vertical 9:16", "hook": "primeros 3s"},
    "instagram":  {"duracion": "reels 15-90s", "formato": "vertical + cuadrado", "hook": "caption+visual"},
    "youtube":    {"duracion": "3-15min o shorts <60s", "formato": "horizontal 16:9", "hook": "thumbnail+título"},
    "facebook":   {"duracion": "cualquiera", "formato": "cuadrado o horizontal", "hook": "historia+FOMO"},
    "whatsapp":   {"duracion": "stories o mensaje", "formato": "vertical", "hook": "texto directo"},
}


class MotorMarketing:
    """Motor marketing con retroalimentación de memoria semántica."""

    def __init__(self):
        self.motor_id = "motor_marketing"
        self._groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None
        self.stats = {"requests": 0, "exitosos": 0}

    async def generar_contenido(
        self,
        tipo: str = "hook",
        plataforma: str = "tiktok",
        producto: str = "ATF Retrofit LED",
        contexto_extra: str = "",
    ) -> Dict:
        """
        Genera contenido viral real para la plataforma indicada.
        Lee la memoria semántica para basar el contenido en lo que funcionó.
        tipo: hook | caption | estrategia | guion | hashtags
        """
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}

        # Leer qué funcionó en memoria semántica
        patrones_exitosos = await self._leer_memoria_marketing(plataforma)

        info_plataforma = PLATAFORMAS.get(plataforma, PLATAFORMAS["tiktok"])
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        prompt_usuario = (
            f"Genera un {tipo} para {plataforma.upper()}.\n"
            f"Producto: {producto}\n"
            f"Specs plataforma: {json.dumps(info_plataforma)}\n"
            f"Contexto adicional: {contexto_extra or 'ninguno'}\n"
            f"Lo que ha funcionado antes (memoria AURORA): {patrones_exitosos}\n"
            f"Fecha/hora: {fecha}\n\n"
            f"Entrega el {tipo} listo para usar, sin explicaciones."
        )

        try:
            r = await self._groq.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": PROMPT_MARKETING},
                    {"role": "user",   "content": prompt_usuario},
                ],
                max_tokens=600, temperature=0.8,
            )
            contenido = r.choices[0].message.content.strip()
            self.stats["exitosos"] += 1

            # Registrar generación en episódica
            await self._registrar_generacion(tipo, plataforma, contenido)

            return {
                "status": "OK",
                "motor": self.motor_id,
                "tipo": tipo,
                "plataforma": plataforma,
                "contenido": contenido,
                "basado_en_memoria": bool(patrones_exitosos),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error generando {tipo}: {e}")
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def estrategia_semanal(self, objetivo: str = "leads ATF") -> Dict:
        """Genera un plan de contenido para 7 días basado en memoria + tendencias."""
        if not self._groq:
            return {"status": "ERROR"}
        patrones = await self._leer_memoria_marketing("todas")
        r = await self._groq.chat.completions.create(
            model=_MODELO,
            messages=[
                {"role": "system", "content": PROMPT_MARKETING},
                {"role": "user", "content": (
                    f"Crea un calendario de contenido para 7 días. Objetivo: {objetivo}.\n"
                    f"Plataformas: TikTok, Instagram, Facebook, YouTube.\n"
                    f"Patrones exitosos de memoria AURORA: {patrones}\n"
                    "Formato: día → plataforma → tipo → descripción breve del contenido."
                )},
            ],
            max_tokens=900, temperature=0.7,
        )
        plan = r.choices[0].message.content.strip()
        await self._registrar_generacion("estrategia_semanal", "todas", plan)
        return {"status": "OK", "plan": plan, "objetivo": objetivo}

    async def analizar_competencia(self, nicho: str = "iluminación automotriz México") -> Dict:
        """Analiza tendencias del nicho usando web search + LLM."""
        if not self._groq:
            return {"status": "ERROR"}
        try:
            import sys
            sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "SUPER_MARKETING_SYSTEM" / "MODULES"))
            from motor_busqueda_web_real import MotorBusquedaWebReal
            buscador = MotorBusquedaWebReal()
            resultados_web = await buscador.buscar_competencia(nicho)
        except Exception:
            resultados_web = "Búsqueda web no disponible — usando conocimiento LLM."

        r = await self._groq.chat.completions.create(
            model=_MODELO,
            messages=[
                {"role": "system", "content": PROMPT_MARKETING},
                {"role": "user", "content": (
                    f"Analiza la competencia en: {nicho}\n"
                    f"Datos web: {str(resultados_web)[:1000]}\n"
                    "Responde: 1) Qué hace la competencia 2) Oportunidades para ATF 3) Diferenciación táctica."
                )},
            ],
            max_tokens=600,
        )
        analisis = r.choices[0].message.content.strip()
        # Guardar insight en semántica
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.aprender(
                tema="marketing",
                patron=f"competencia_{nicho[:30]}",
                conocimiento=analisis[:400],
                confianza=0.6,
            )
        except Exception:
            pass
        return {"status": "OK", "nicho": nicho, "analisis": analisis}

    async def _leer_memoria_marketing(self, plataforma: str) -> str:
        """Lee patrones de marketing exitosos de la memoria semántica."""
        try:
            from MEMORIA.sistema_memoria import memoria
            conocimientos = await memoria.recordar(tema="marketing", limite=5)
            if not conocimientos:
                return "Sin patrones previos — primera generación."
            return " | ".join([
                f"{k['patron']}: {k['conocimiento'][:100]}"
                for k in conocimientos[:3]
            ])
        except Exception:
            return ""

    async def _registrar_generacion(self, tipo: str, plataforma: str, contenido: str) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen="motor_marketing",
                tipo_evento="contenido_generado",
                contenido={"tipo": tipo, "plataforma": plataforma, "preview": contenido[:200]},
                importancia=0.6,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {
            "motor_id": self.motor_id,
            "groq_activo": self._groq is not None,
            "stats": self.stats,
        }


motor = MotorMarketing()
