# -*- coding: utf-8 -*-
"""AURORA · LIBRERÍA DE EQUIPOS DE TRABAJO (declarativa).

Idea de Anuar: en vez de motores sueltos, EQUIPOS que trabajan juntos hacia una meta.
Aprovecha los GRUPOS que ya existen en la Consola de Motores (Taller, Ventas,
Marketing, Diseño...). Un "equipo" es una RECETA (datos, no código):
  - qué motores lo integran
  - cuál es su meta
  - qué acción real dispara (una función ya existente y probada)

NO es un "creador de equipos" abstracto: es una librería declarativa. Se amplía
agregando entradas al diccionario EQUIPOS, sin programar lógica nueva. El cerebro
puede pedir "equipo marketing → prepara la publicación de hoy" y se coordina.

REGLA: cada equipo apunta a funciones REALES ya conectadas y probadas. Nada de humo:
si un equipo no tiene su acción lista, se marca 'en_construccion' y se dice honesto.
"""
from __future__ import annotations
import importlib.util as _ilu
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _mod(nombre: str, ruta: str):
    spec = _ilu.spec_from_file_location(nombre, ROOT / ruta)
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


# ── LIBRERÍA DE EQUIPOS ─────────────────────────────────────────────
# grupo_consola = el grupo que ya existe en CORE/consola_motores.py (se reutiliza).
EQUIPOS = {
    "marketing": {
        "nombre": "Equipo de Marketing",
        "icono": "📣",
        "grupo_consola": "Marketing",
        "meta": "Crecer seguidores, viralizar y publicar con criterio de algoritmo.",
        "motores": ["asesor_marketing", "motor_marketing", "analitica_marketing", "publicador_core", "plan_monetizacion"],
        "accion": ("MARKETING/publicacion_inteligente.py", "estrategia_ingresos"),
        "estado": "listo",
    },
    "publicacion": {
        "nombre": "Equipo de Publicación",
        "icono": "📅",
        "grupo_consola": "Marketing",
        "meta": "Preparar y sacar el contenido del día en cada red (nativo + hora clave).",
        "motores": ["plan_monetizacion", "asesor_marketing", "publicador_core"],
        "accion": ("MARKETING/publicacion_inteligente.py", "preparar_publicacion"),
        "estado": "listo",
    },
    "ventas": {
        "nombre": "Equipo de Ventas",
        "icono": "💼",
        "grupo_consola": "Ventas",
        "meta": "Captar leads, mover el embudo y convertir en órdenes reales.",
        "motores": ["oracle_core", "vendedor_core", "seguimiento_ventas", "whatsapp"],
        "accion": ("ORACLE/oracle_core.py", "pronostico_embudo"),
        "estado": "listo",
    },
    "diseno": {
        "nombre": "Equipo de Diseño",
        "icono": "✎",
        "grupo_consola": "Diseño",
        "meta": "Convertir/preparar archivos para corte láser y sublimación.",
        "motores": ["taller_core", "conversiones", "plantillas_taza", "escalas_planillas"],
        "accion": None,  # se coordina por chat (convertir DXF, planillas); sin una sola acción central
        "estado": "listo",
    },
    "taller": {
        "nombre": "Equipo de Taller",
        "icono": "◧",
        "grupo_consola": "Taller",
        "meta": "Órdenes, cotización, inventario y contabilidad del taller.",
        "motores": ["ordenes_taller", "cotizador_servicios", "inventario", "administracion"],
        "accion": None,  # ya tienen paneles propios; el chat consulta datos reales
        "estado": "listo",
    },
}


def listar_equipos() -> dict:
    """Catálogo de equipos con sus motores, meta y si su acción está lista."""
    out = []
    for eid, e in EQUIPOS.items():
        out.append({
            "id": eid, "nombre": e["nombre"], "icono": e["icono"],
            "grupo_consola": e["grupo_consola"], "meta": e["meta"],
            "motores": e["motores"], "n_motores": len(e["motores"]),
            "tiene_accion": bool(e["accion"]), "estado": e["estado"],
        })
    return {"status": "ok", "total": len(out), "equipos": out}


def activar_equipo(equipo_id: str, **kw) -> dict:
    """Pone a trabajar un equipo: ejecuta su acción REAL. Si no tiene una acción
    central (taller/diseño), devuelve su meta y motores para coordinar por chat."""
    e = EQUIPOS.get((equipo_id or "").lower().strip())
    if not e:
        return {"status": "no_existe", "detalle": f"Equipos: {list(EQUIPOS)}"}
    if not e["accion"]:
        return {"status": "sin_accion_central", "equipo": e["nombre"], "meta": e["meta"],
                "motores": e["motores"],
                "detalle": "Este equipo trabaja por sus paneles/chat (no tiene una sola acción). "
                           "Pídele al chat una tarea concreta (ej. 'convierte X a DXF', '¿qué órdenes tengo?')."}
    ruta, funcion = e["accion"]
    try:
        mod = _mod(equipo_id + "_accion", ruta)
        fn = getattr(mod, funcion)
    except Exception as ex:
        return {"status": "error", "detalle": f"No pude cargar la acción del equipo: {str(ex)[:120]}"}
    # El reintento sin kwargs solo tiene sentido si SÍ había kwargs que pudieran sobrar
    # (función que no los acepta). Si kw ya estaba vacío, reintentar es un duplicado
    # inútil que puede re-ejecutar un efecto secundario real que ya corrió antes de fallar.
    try:
        resultado = fn(**kw) if kw else fn()
    except TypeError:
        if not kw:
            raise
        resultado = fn()
    return {"status": "ok", "equipo": e["nombre"], "meta": e["meta"], "resultado": resultado}


if __name__ == "__main__":
    import json
    print(json.dumps(listar_equipos(), ensure_ascii=False, indent=2))
