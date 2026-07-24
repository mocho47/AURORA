# -*- coding: utf-8 -*-
"""AURORA · PUBLICACIÓN INTELIGENTE (el conector que faltaba).

Une las piezas que YA existían pero vivían sueltas:
  - plan_monetizacion  → qué video toca hoy (rotación sin repetir, 296 videos reales)
  - asesor_core        → conocimiento REAL del algoritmo + playbook de viralización
  - publicador_core    → subida REAL a Facebook (token permanente de ATF)

Objetivo (visión de Anuar): "video diferente diario, en horario clave, con criterio
de viralización, y que registre lo publicado". Sin simular: si algo no se puede,
lo dice; si publica, es de verdad y devuelve el post_id.

REGLA: publicar es acción pública real. Esta capa PREPARA todo (video + copy nativo
por red + hora sugerida) y solo DISPARA la subida cuando se le pide explícitamente
(aprobar=True), respetando la regla del publicador (Anuar aprueba).
"""
from __future__ import annotations
import importlib.util as _ilu
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent


def _mod(nombre: str, ruta: Path):
    spec = _ilu.spec_from_file_location(nombre, ruta)
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _monetizacion():
    return _mod("plan_monetizacion", ROOT / "MARKETING" / "plan_monetizacion.py")


def _asesor():
    return _mod("asesor_core", ROOT / "MARKETING" / "asesor_core.py")


def _publicador():
    return _mod("publicador_core", ROOT / "PUBLICADOR" / "publicador_core.py")


def _mercado():
    return _mod("analizador_mercado", ROOT / "MARKETING" / "analizador_mercado.py")


def estrategia_ingresos(negocio: str = "atf", tema: str = "") -> dict:
    """EQUIPO INTERACTIVO en una llamada: une conocimiento de algoritmo (asesor) +
    estudio de mercado (analizador) + plan de contenido (monetización) para una
    estrategia de crecimiento e ingresos. Honesto: el análisis de mercado con datos
    reales usa web; si falla, lo dice y entrega el playbook base sin inventar."""
    ase = _asesor()
    salida = {
        "status": "ok", "negocio": negocio,
        "algoritmos": ase.conocimiento(),                    # cómo premia cada red
        "playbook_viralizacion": ase.playbook("viralizacion"),
        "playbook_ventas": ase.playbook("ventas"),
        "playbook_monetizacion": ase.playbook("monetizacion"),
    }
    # Estudio de mercado (qué atrae) — real vía web; si no, honesto.
    try:
        mer = _mercado()
        consulta = tema or ("retrofit faros LED automotriz" if negocio == "atf"
                            else "sublimación láser personalizados")
        salida["mercado"] = mer.analizar(consulta)
    except Exception as e:
        salida["mercado"] = {"status": "SIN_DATOS", "detalle": f"Estudio de mercado no disponible ahora: {str(e)[:100]}"}
    # Qué video/plan toca
    try:
        salida["plan_hoy"] = preparar_publicacion(negocio)
    except Exception as e:
        salida["plan_hoy"] = {"status": "error", "detalle": str(e)[:100]}
    salida["nota"] = ("Este es el equipo interactivo: algoritmo + mercado + plan. "
                      "Publicar sigue siendo acción real que se dispara con aprobar=True.")
    return salida


# Horarios base por red (arranque; se afinan con insights reales vía asesor.mejores_horarios).
HORARIOS_BASE = {
    "facebook":  "13:00 y 19:00 (comida y noche — mayor interacción)",
    "instagram": "12:00 y 20:00 (Reels: mediodía y noche)",
    "tiktok":    "18:00-22:00 (prime time de scroll)",
    "youtube":   "15:00-17:00 y 20:00 (tarde/noche)",
}


def preparar_publicacion(negocio: str = "atf") -> dict:
    """Arma TODO para el post de hoy SIN publicar: qué video, copy nativo por red con
    criterio de viralización, hora sugerida y el gancho recomendado. Cero simulación:
    usa el video real del plan y el playbook real del asesor."""
    mon = _monetizacion()
    hoy = mon.post_de_hoy()
    if hoy.get("status") != "ok":
        return hoy

    ase = _asesor()
    playbook = ase.playbook("viralizacion")
    principios = playbook.get("principios", []) if isinstance(playbook, dict) else []

    preparados = []
    for p in hoy.get("posts", []):
        red = (p.get("plataforma") or p.get("red") or "").lower()
        algo = ase.conocimiento(red)
        formato = (algo.get("formato_nativo") if isinstance(algo, dict) else "") or ""
        preparados.append({
            "id": p.get("id"),
            "red": red,
            "video": p.get("video"),
            "estado": p.get("estado"),
            "formato_nativo": formato,
            "hora_plan": p.get("hora") or "",
            "hora_sugerida": HORARIOS_BASE.get(red, "horario de mayor actividad"),
            "gancho_recordatorio": "Gancho fuerte en los primeros 1-3 segundos (decide si te ven o te saltan).",
        })
    return {"status": "ok", "fecha": hoy["fecha"], "negocio": negocio,
            "ruta_videos": hoy.get("ruta_videos"),
            "posts_preparados": preparados,
            "principios_viralizacion": principios,
            "nota": "Preparado. Para publicar de verdad usa publicar_hoy(red=..., aprobar=True)."}


def publicar_hoy(red: str = "facebook", descripcion: str = "", aprobar: bool = False) -> dict:
    """DISPARA la publicación REAL del video de hoy en la red indicada.
    aprobar=False → solo devuelve qué se publicaría (dry-run, no sube nada).
    aprobar=True  → sube de verdad (hoy: Facebook por API oficial con token permanente).
    """
    red = (red or "facebook").lower().strip()
    mon = _monetizacion()
    hoy = mon.post_de_hoy()
    if hoy.get("status") != "ok":
        return hoy

    post = next((p for p in hoy.get("posts", [])
                 if (p.get("plataforma") or p.get("red") or "").lower() == red), None)
    if not post:
        return {"status": "sin_post", "detalle": f"No hay post de {red} para hoy."}
    if post.get("estado") == "publicado":
        return {"status": "ya_publicado", "red": red, "detalle": "Ese post ya se publicó hoy."}

    vids_dir = Path(hoy.get("ruta_videos", ""))
    ruta_video = str(vids_dir / post["video"]) if post.get("video") else ""
    if not ruta_video or not Path(ruta_video).is_file():
        return {"status": "sin_video", "detalle": f"No encontré el video: {ruta_video}"}

    if not aprobar:
        return {"status": "listo_para_aprobar", "red": red, "video": ruta_video,
                "descripcion": descripcion or "(se usará el copy que le pases)",
                "detalle": "DRY-RUN: no publiqué nada. Llama con aprobar=True para subirlo de verdad."}

    # ── Publicación REAL ──
    if red != "facebook":
        return {"status": "no_soportado_aun", "red": red,
                "detalle": f"Hoy solo publico automático en Facebook (token oficial). "
                           f"{red.title()} necesita su propia API/token."}
    pub = _publicador()
    r = pub.publicar_video_fb(ruta_video, descripcion)
    if isinstance(r, dict) and r.get("status") == "PUBLICADO":
        try:
            mon.marcar_publicado(post["id"])
        except Exception:
            pass
        return {"status": "PUBLICADO", "red": "facebook", "video": ruta_video,
                "post_id": r.get("post_id"), "cuando": datetime.now().isoformat(timespec="seconds")}
    return {"status": "ERROR", "red": red, "detalle": (r or {}).get("detalle", str(r))}


if __name__ == "__main__":
    import json
    print(json.dumps(preparar_publicacion(), ensure_ascii=False, indent=2)[:1500])
