# -*- coding: utf-8 -*-
"""ASESOR DE MARKETING DIGITAL de AURORA.

Comprensión REAL de los algoritmos de las redes + lógica profesional de
viralización, ventas y monetización. NO hackea: entiende las señales públicas que
cada plataforma premia y aplica buena práctica.

REGLA: el conocimiento (algoritmos, playbook) es de dominio real/público.
El ANÁLISIS de resultados SIEMPRE exige métricas reales; si no hay datos,
lo dice honesto y entrega el playbook base. Nunca inventa números.
"""
from __future__ import annotations
from typing import Optional, Dict, List

# ───────────────────────── CONOCIMIENTO REAL DE ALGORITMOS ─────────────────────────
# Señales públicas que cada plataforma premia (guías oficiales para creadores).
ALGORITMOS: Dict[str, dict] = {
    "tiktok": {
        "objetivo": "Maximizar el tiempo que el usuario pasa en la app.",
        "señales_premia": [
            "Retención: % del video que se ve (lo más importante)",
            "Re-watch (que lo vean otra vez / en bucle)",
            "Watch time total y velocidad de interacción en la 1ª hora",
            "Shares, comentarios y guardados",
        ],
        "premia_formato": ["Vertical 9:16 nativo", "Gancho en 1-3 s", "Audio en tendencia",
                           "Texto en pantalla", "Videos cortos vistos completos", "Series repetibles"],
        "castiga": ["Marcas de agua de otras apps", "Links que sacan de la app",
                    "Baja retención (caída en los primeros segundos)", "Reposteo sin valor"],
    },
    "instagram": {
        "objetivo": "Tiempo de uso + interacción significativa (Reels = alcance nuevo).",
        "señales_premia": [
            "Guardados y compartidos a DM (los que más alcance dan en Reels)",
            "Watch time / re-views",
            "Comentarios y respuestas",
        ],
        "premia_formato": ["Reels 9:16 nativo", "Audio del propio IG", "Stickers/encuestas en stories",
                           "Gancho fuerte inicial", "CTA a guardar/compartir"],
        "castiga": ["Marca de agua de TikTok", "Baja retención", "Contenido que no se comparte"],
    },
    "facebook": {
        "objetivo": "Interacciones significativas entre personas.",
        "señales_premia": ["Comentarios y conversación", "Compartidos", "Retención de video",
                           "Video NATIVO (no link de YouTube)"],
        "premia_formato": ["Video nativo", "Contenido que genera debate/pregunta", "Grupos/comunidad"],
        "castiga": ["Links externos (bajan alcance)", "Clickbait engañoso", "Engagement-bait obvio"],
    },
    "youtube": {
        "objetivo": "Maximizar tiempo de sesión y satisfacción del espectador.",
        "señales_premia": ["CTR (miniatura + título)", "Duración promedio de visualización",
                           "Retención", "Tiempo de sesión", "Shorts: % visto y re-watch"],
        "premia_formato": ["Miniatura + título fuertes", "Buen gancho", "Capítulos", "Series"],
        "castiga": ["Títulos engañosos", "Caídas tempranas de retención"],
    },
}

# Cada red "acepta más fácil" su formato NATIVO (truco real de distribución).
FORMATOS_NATIVOS = {
    "tiktok": "Subida nativa 9:16 + audio en tendencia + texto en pantalla. Sin marca de agua externa.",
    "instagram": "Reel 9:16 con audio de IG + CTA a guardar/compartir. Sin marca de agua de TikTok.",
    "facebook": "Video nativo subido directo + pregunta para comentarios. Evitar links externos.",
    "youtube": "Short 9:16 o video con miniatura/título fuertes + capítulos.",
}

# ───────────────────────── PLAYBOOK PROFESIONAL (3 FLANCOS) ─────────────────────────
PLAYBOOK: Dict[str, dict] = {
    "viralizacion": {
        "principios": [
            "Gancho en 1-3 s: lo que decide si te ven o te saltan.",
            "Formato nativo 9:16 de cada red (no recicles con marca de agua de otra app).",
            "Audio en tendencia + texto en pantalla.",
            "1ª hora: responder comentarios rápido = empuje de alcance.",
            "Volumen + consistencia: muchos intentos, no buscar el viral perfecto.",
            "Reciclaje: 1 video → varias versiones por red (AURORA reedita a 9:16).",
            "CTA suave a comentar/guardar (no a salir de la app).",
        ],
    },
    "ventas": {
        "principios": [
            "El embudo real: contenido → lead → orden (todo se registra en ORACLE).",
            "CTA claro a un canal propio (WhatsApp/DM), no genérico.",
            "Prueba social: antes/después, testimonios reales, trabajos terminados.",
            "Responder en <5 min: ningún lead se enfría (orden permanente).",
            "Seguimiento: 2-3 toques sin ser invasivo; cotización con precio real.",
            "Oferta con urgencia HONESTA (cupos/tiempo reales, no inventados).",
        ],
    },
    "monetizacion": {
        "principios": [
            "Precio ancla con tu catálogo real + paquetes (retrofit + instalación).",
            "Upsell/cross-sell: sumar servicios complementarios.",
            "Retargeting a interesados que no cerraron.",
            "Medir ROI por red y reinvertir donde más deja (no donde hay más likes).",
            "Convertir alcance en dinero: cada pieza de contenido con objetivo claro.",
        ],
    },
}

# Lo que QUEMA la cuenta (penaliza el algoritmo). NO hacer.
EVITAR: List[str] = [
    "Comprar vistas/seguidores o usar bots",
    "Engagement pods / follow-unfollow",
    "Marcas de agua de otras apps",
    "Links que sacan al usuario fuera de la red",
    "Clickbait engañoso / títulos falsos",
    "Reposteo de contenido ajeno sin valor agregado",
]


def conocimiento(red: Optional[str] = None) -> dict:
    """Devuelve el conocimiento real del algoritmo de una red (o todas)."""
    if red:
        r = red.lower().strip()
        if r in ALGORITMOS:
            return {"status": "OK", "red": r, "algoritmo": ALGORITMOS[r],
                    "formato_nativo": FORMATOS_NATIVOS.get(r), "evitar": EVITAR}
        return {"status": "NO_ENCONTRADO", "detalle": f"No tengo '{red}'. Redes: {list(ALGORITMOS)}"}
    return {"status": "OK", "algoritmos": ALGORITMOS, "formatos_nativos": FORMATOS_NATIVOS, "evitar": EVITAR}


def playbook(flanco: Optional[str] = None) -> dict:
    """Buenas prácticas por flanco: viralizacion | ventas | monetizacion (o todos)."""
    if flanco:
        f = flanco.lower().strip()
        if f in PLAYBOOK:
            return {"status": "OK", "flanco": f, **PLAYBOOK[f]}
        return {"status": "NO_ENCONTRADO", "detalle": f"Flancos: {list(PLAYBOOK)}"}
    return {"status": "OK", "playbook": PLAYBOOK, "evitar": EVITAR}


def mejores_horarios(actividad_por_hora: Optional[Dict[int, float]] = None) -> dict:
    """Calcula las mejores horas para publicar a partir de datos REALES de actividad
    (seguidores activos por hora, de los insights). Sin datos → lo dice honesto."""
    if not actividad_por_hora:
        return {"status": "SIN_DATOS",
                "detalle": "Necesito tus insights reales (seguidores activos por hora). "
                           "Conecta Meta para traerlos; no invento horarios."}
    ordenado = sorted(actividad_por_hora.items(), key=lambda kv: kv[1], reverse=True)
    top = [{"hora": int(h), "actividad": round(float(v), 2)} for h, v in ordenado[:3]]
    return {"status": "OK", "mejores_horas": top,
            "nota": "Basado en TU actividad real de audiencia."}


# Reglas de diagnóstico: umbrales de buena práctica sobre métricas REALES.
def diagnostico(metricas: Optional[Dict[str, dict]] = None) -> dict:
    """Diagnostica sobre métricas REALES por red y sugiere acciones concretas.
    metricas = {"tiktok": {"retencion_pct":35,"shares":4,"comentarios":2,"vistas":1200}, ...}
    Sin métricas → entrega el playbook base y pide conectar datos (no inventa)."""
    if not metricas:
        return {"status": "SIN_DATOS",
                "detalle": "Aún no tengo tus métricas reales. Conecta Meta/redes para analizar. "
                           "Mientras, aplica el playbook base.",
                "playbook": PLAYBOOK}
    hallazgos: List[dict] = []
    for red, m in metricas.items():
        recs: List[str] = []
        ret = m.get("retencion_pct")
        vistas = m.get("vistas") or 0
        shares = m.get("shares") or 0
        com = m.get("comentarios") or 0
        if ret is not None and ret < 50:
            recs.append("Retención baja (<50%): refuerza el gancho en los primeros 1-3 s y acorta el video.")
        if vistas and (shares / vistas) < 0.01:
            recs.append("Pocos compartidos (<1%): añade un remate compartible o un dato útil al final.")
        if vistas and (com / vistas) < 0.01:
            recs.append("Pocos comentarios: cierra con una pregunta directa para disparar conversación.")
        if not recs:
            recs.append("Buenas señales: replica este formato/horario y sube el volumen.")
        hallazgos.append({"red": red, "metricas": m, "recomendaciones": recs})
    return {"status": "OK", "analisis": hallazgos,
            "nota": "Diagnóstico sobre TUS números reales, no simulado."}


def construir_brief_para_cerebro(negocio: str, metricas: Optional[dict], objetivo: str = "") -> str:
    """Arma el contexto (conocimiento + datos reales) para que el cerebro genere el plan.
    Si no hay métricas reales, lo deja explícito para que el cerebro NO invente."""
    partes = [
        f"Eres el Asesor de Marketing Digital de AURORA para el negocio {negocio.upper()}.",
        "Conocimiento real de algoritmos (señales que premia cada red):",
    ]
    for red, a in ALGORITMOS.items():
        partes.append(f"- {red}: premia {', '.join(a['señales_premia'][:3])}.")
    partes.append("Playbook: " + "; ".join(
        f"{f}: {d['principios'][0]}" for f, d in PLAYBOOK.items()))
    partes.append("NUNCA recomiendes: " + ", ".join(EVITAR[:4]) + ".")
    if metricas:
        partes.append(f"MÉTRICAS REALES del negocio: {metricas}")
        partes.append("Analiza ESTOS números reales y da un plan concreto (qué/cuándo/cómo) por los 3 flancos: viralización, ventas, monetización.")
    else:
        partes.append("NO hay métricas reales conectadas todavía. NO inventes números ni resultados. "
                      "Entrega el plan base accionable y aclara qué se debe conectar (Meta) para personalizarlo.")
    if objetivo:
        partes.append(f"Objetivo del usuario: {objetivo}")
    return "\n".join(partes)
