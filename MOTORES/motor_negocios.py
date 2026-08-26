# -*- coding: utf-8 -*-
"""
AURORA — MOTOR NEGOCIOS (ATF + MILENS)
Gestión operativa real de los negocios de Anuar.
Usa Groq + datos reales de CONFIG. Sin simulaciones.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from MOTORES import _llamada_modelo as _lm
except ImportError:
    import _llamada_modelo as _lm

logger = logging.getLogger("aurora.motor_negocios")

# ── AQUI VIVIA LA PEOR LISTA DE PRECIOS INVENTADOS DEL PROYECTO ────────────
# Arreglo 2026-08-26. Este prompt le decia al motor, y por lo tanto al cliente:
#   · ATF: "kits Aozoom X1 ($8k), X3 ($15k), X5 ($25k), X7 ($40k) MXN instalado"
#   · MILENS: "poleras ($850), tazas ($170), grabado láser ($180 por pieza)"
#   · "Margen: 120% sobre costo"
# NINGUNO de esos numeros sale de una fuente de Anuar. El catalogo real
# (CONFIG/catalogo_atf.json, 106 productos) dice que los proyectores van de
# $1,599 a $3,149: el "X7 a $40k" era TRECE VECES el precio de verdad. Y los de
# MILENS ni siquiera coinciden con CONFIG/catalogo_servicios.json.
#
# Por que la prueba `tests/test_precios_una_sola_fuente.py` no lo agarro: esa
# prueba lee el AST y busca constantes y diccionarios con numeros. Estos precios
# estaban DENTRO DE UN STRING de prompt, que para el AST es texto y ya. El
# candado cuidaba la puerta y los precios entraban por la ventana.
#
# Ahora el motor no trae ni un numero: los lee del catalogo cuando arranca, como
# ya lo hacia motor_ventas.

_RAIZ = Path(__file__).resolve().parent.parent


def _catalogos_reales() -> str:
    """Los productos de Anuar leidos de su catalogo. Si no se puede leer, se le
    dice al motor que NO de precios — nunca se rellena con una lista vieja."""
    lineas = []
    try:
        d = json.loads((_RAIZ / "CONFIG" / "catalogo_atf.json").read_text(encoding="utf-8"))
        pr = [float(p["precio"]) for p in d.get("productos", []) if p.get("precio")]
        if pr:
            lineas.append(
                f"ATF Retrofit — iluminación automotriz LED. Catálogo real: "
                f"{len(pr)} productos, de ${min(pr):,.0f} a ${max(pr):,.0f} MXN. "
                f"Los precios EXACTOS están en CONFIG/catalogo_atf.json.")
    except Exception as e:
        lineas.append(f"ATF Retrofit: NO pude leer el catálogo ({str(e)[:60]}). "
                      f"No des ningún precio de ATF.")
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("cotizador_servicios",
                                            _RAIZ / "TALLER" / "cotizador_servicios.py")
        cs = _ilu.module_from_spec(spec); spec.loader.exec_module(cs)
        items = (cs.catalogo_plano() or {}).get("items") or []
        pr = [float(i["precio"]) for i in items if i.get("precio")]
        if pr:
            lineas.append(
                f"MILENS — sublimación y láser. Catálogo real: {len(items)} "
                f"servicios, de ${min(pr):,.0f} a ${max(pr):,.0f} MXN. "
                f"Los precios EXACTOS están en el catálogo de servicios.")
    except Exception as e:
        lineas.append(f"MILENS: NO pude leer el catálogo de servicios "
                      f"({str(e)[:60]}). No des ningún precio de MILENS.")
    return "\n".join(lineas)


PROMPT_NEGOCIOS = """Eres el gestor operativo de los negocios de Anuar: ATF Retrofit y MILENS.

""" + _catalogos_reales() + """

⛔ PRECIOS: tú NO cotizas y NO das cifras de memoria. Ni precios, ni márgenes,
ni rangos "aproximados". Aquí antes decía que el kit X7 costaba $40,000 cuando
el producto más caro del catálogo real vale $3,900 — trece veces más, dicho con
toda seguridad. Si te preguntan un precio: di que lo cotice el cotizador, que sí
lee el catálogo. El margen de Anuar es información interna: nunca lo menciones.

ATF: canales TikTok, Instagram, YouTube, WhatsApp directo. Prioridad #1 generar
leads y cerrar instalaciones HOY. Respuesta a un lead: < 5 minutos.
MILENS: clientes empresas, eventos y regalos personalizados. Fortaleza: calidad
y entrega rápida.

Tu rol: reportar estado real, proponer acciones, detectar oportunidades.
Regla fundamental: NUNCA inventes métricas. Si no tienes datos reales, dilo y
propone cómo obtenerlos.
Contesta SIEMPRE en español de México.
Siempre termina con "PRÓXIMA ACCIÓN RECOMENDADA:" + acción concreta."""

_MODELO = "openai/gpt-oss-20b"


class MotorNegocios:
    def __init__(self):
        self.motor_id = "motor_negocios"
        self._groq = _lm.cliente()
        self.stats = {"requests": 0, "exitosos": 0, "errores": 0}

    async def consultar(self, consulta: str, contexto: dict = None) -> Dict:
        self.stats["requests"] += 1
        if not self._groq:
            return {"status": "ERROR", "detalle": "Sin GROQ_API_KEY"}
        contexto = contexto or {}
        negocio = contexto.get("negocio", "ambos")
        resumen_oracle = await self._resumen_oracle(negocio)
        prompt_usuario = (
            f"Consulta operativa: {consulta}\n"
            f"Negocio: {negocio}\n"
            f"Resumen actual desde ORACLE: {resumen_oracle}\n"
            f"Contexto adicional: {contexto}"
        )
        try:
            respuesta = await _lm.responder(
                self._groq, PROMPT_NEGOCIOS, prompt_usuario,
                max_tokens=600, temperature=0.4, modelo=_MODELO)
            self.stats["exitosos"] += 1
            await self._registrar("consulta_negocio", {"negocio": negocio, "preview": respuesta[:150]})
            return {
                "status": "OK",
                "motor": self.motor_id,
                "negocio": negocio,
                "respuesta": respuesta,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error motor_negocios: {e}")
            self.stats["errores"] += 1
            return {"status": "ERROR", "detalle": str(e)[:200]}

    async def _resumen_oracle(self, negocio: str) -> str:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "ORACLE"))
            import oracle_core as oracle
            oracle.init_db()
            r = oracle.resumen(negocio if negocio != "ambos" else None)
            return str(r)
        except Exception as e:
            return f"ORACLE no disponible: {e}"

    async def _registrar(self, tipo: str, contenido: dict) -> None:
        try:
            from MEMORIA.sistema_memoria import memoria
            await memoria.registrar(
                motor_origen=self.motor_id, tipo_evento=tipo,
                contenido=contenido, importancia=0.7,
            )
        except Exception:
            pass

    def get_status(self) -> Dict:
        return {"motor_id": self.motor_id, "groq_activo": self._groq is not None, "stats": self.stats}


motor = MotorNegocios()
