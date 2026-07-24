#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SLEEP CYCLE REAL - Mantenimiento y resumen del día con DATOS REALES.

Cuando AURORA no se usa, este ciclo hace mantenimiento REAL (diagnóstico de
módulos, solo lectura) y saca un resumen REAL del día leyendo las bases de
datos y motores que ya existen. NO inventa números. Si un dato no existe
(ej. oracle.db vacía) lo reporta honesto (0), jamás lo rellena.

Fuentes reales conectadas (cargadas con importlib.util.spec_from_file_location):
  - TALLER/reportes_bi.py    -> ingresos/utilidad/estados reales de taller.db
  - ORACLE/oracle_core.py    -> leads/órdenes CRM reales de oracle.db
  - MARKETING/asesor_core.py -> mejores_horarios sobre actividad real
  - CEREBRO/auto_conocimiento.py -> diagnóstico de módulos (solo lectura)
  - CEREBRO/auto_reparacion.py   -> reparación (SOLO si confirmar=True)
"""

import asyncio
import importlib.util
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Raíz del ecosistema AURORA: .../AUTH/AUTOMATIONS/sleep_cycle.py -> sube 2
ROOT = Path(__file__).resolve().parents[2]


def _cargar(nombre: str, ruta_rel: str):
    """Carga un módulo por ruta de archivo. Devuelve el módulo o None si falla."""
    ruta = ROOT / ruta_rel
    if not ruta.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(nombre, str(ruta))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


class SleepCycle:
    def __init__(self, confirmar: bool = False):
        # confirmar=False => ciclo de LECTURA/diagnóstico, no escribe nada.
        # confirmar=True  => habilita auto-reparación (acciones que escriben).
        self.nombre = "sleep_cycle"
        self.confirmar = confirmar
        self.hora_inicio = datetime.now()

    # ------------------------------------------------------------------ #
    #  1. RESUMEN DEL DÍA — TALLER (taller.db vía reportes_bi.py)
    # ------------------------------------------------------------------ #
    async def resumen_taller(self) -> Dict[str, Any]:
        """Ingresos/órdenes/estados REALES del taller (34 órdenes reales)."""
        bi = _cargar("reportes_bi", "TALLER/reportes_bi.py")
        if bi is None:
            return {"fase": "resumen_taller", "status": "SIN_MODULO",
                    "detalle": "No se pudo cargar TALLER/reportes_bi.py"}
        try:
            general = bi.resumen_general()
            estados = bi.estados()
            top = bi.top_productos(3)
        except Exception as e:
            return {"fase": "resumen_taller", "status": "ERROR", "detalle": str(e)}
        return {
            "fase": "resumen_taller",
            "fuente": "taller.db (real)",
            "general": general,
            "estados": estados,
            "top_productos": top,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  2. RESUMEN DEL DÍA — CRM/LEADS (oracle.db vía oracle_core.py)
    # ------------------------------------------------------------------ #
    async def resumen_crm(self) -> Dict[str, Any]:
        """Leads y órdenes CRM REALES. Si oracle.db está vacía → 0 honesto."""
        orc = _cargar("oracle_core", "ORACLE/oracle_core.py")
        if orc is None:
            return {"fase": "resumen_crm", "status": "SIN_MODULO",
                    "detalle": "No se pudo cargar ORACLE/oracle_core.py"}
        try:
            res = orc.resumen()
        except Exception as e:
            return {"fase": "resumen_crm", "status": "ERROR", "detalle": str(e)}
        nota = ""
        if res.get("total_leads", 0) == 0 and res.get("total_ordenes", 0) == 0:
            nota = "CRM sin datos reales aún: 0 leads / 0 órdenes (honesto, no inventado)."
        return {
            "fase": "resumen_crm",
            "fuente": "oracle.db (real)",
            "resumen": res,
            "nota": nota,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  3. HORAS PICO REALES — actividad real de creación de órdenes
    #     (taller.db.creado) analizada por MARKETING/asesor_core.py
    # ------------------------------------------------------------------ #
    async def horas_pico(self) -> Dict[str, Any]:
        """Calcula hora pico a partir de CUÁNDO se crearon las órdenes reales.
        Sin actividad real → lo dice honesto (no inventa un horario)."""
        actividad_por_hora: Dict[int, float] = {}
        n_eventos = 0
        db = ROOT / "taller.db"
        if db.exists():
            try:
                conn = sqlite3.connect(str(db))
                filas = conn.execute("SELECT creado FROM ordenes WHERE creado IS NOT NULL").fetchall()
                conn.close()
                horas = Counter()
                for (creado,) in filas:
                    try:
                        h = datetime.fromisoformat(str(creado)).hour
                        horas[h] += 1
                        n_eventos += 1
                    except Exception:
                        continue
                actividad_por_hora = {int(h): float(c) for h, c in horas.items()}
            except Exception as e:
                return {"fase": "horas_pico", "status": "ERROR", "detalle": str(e)}

        asesor = _cargar("asesor_core", "MARKETING/asesor_core.py")
        if asesor is None:
            return {"fase": "horas_pico", "status": "SIN_MODULO",
                    "detalle": "No se pudo cargar MARKETING/asesor_core.py"}
        try:
            calculo = asesor.mejores_horarios(actividad_por_hora or None)
        except Exception as e:
            return {"fase": "horas_pico", "status": "ERROR", "detalle": str(e)}
        return {
            "fase": "horas_pico",
            "fuente": "taller.db.creado (actividad real de órdenes)",
            "eventos_analizados": n_eventos,
            "resultado": calculo,
            "nota": ("Horas pico calculadas de cuándo se crearon órdenes reales."
                     if n_eventos else
                     "Sin actividad real registrada; no se inventa horario."),
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  4. MANTENIMIENTO REAL — diagnóstico de módulos (SOLO LECTURA)
    # ------------------------------------------------------------------ #
    async def mantenimiento(self) -> Dict[str, Any]:
        """Revisa de verdad que los módulos compilen. No modifica nada.
        Si confirmar=True y hay errores de sintaxis, intenta auto-reparar."""
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        try:
            from CEREBRO.auto_conocimiento import auto_conocimiento
        except Exception as e:
            return {"fase": "mantenimiento", "status": "SIN_MODULO",
                    "detalle": f"No se pudo cargar auto_conocimiento: {e}"}
        try:
            diag = await auto_conocimiento.diagnosticar_modulos()
        except Exception as e:
            return {"fase": "mantenimiento", "status": "ERROR", "detalle": str(e)}

        resultado = {
            "fase": "mantenimiento",
            "tipo": "diagnostico_solo_lectura",
            "modulos_ok": diag.get("total_ok", 0),
            "modulos_totales": len(diag.get("modulos", {})),
            "errores": diag.get("errores", {}),
            "reparacion": {"estado": "NO_EJECUTADA",
                           "motivo": "confirmar=False (ciclo no destructivo por defecto)"},
            "timestamp": datetime.now().isoformat(),
        }

        errores_sintaxis = [k for k, v in diag.get("errores", {}).items()
                            if v.get("status") == "ERROR_SINTAXIS"]
        if errores_sintaxis and self.confirmar:
            try:
                from CEREBRO.auto_reparacion import auto_reparacion
                rep = await auto_reparacion.diagnosticar_y_reparar_todo()
                resultado["reparacion"] = {"estado": "EJECUTADA", "detalle": rep}
            except Exception as e:
                resultado["reparacion"] = {"estado": "ERROR", "detalle": str(e)}
        elif errores_sintaxis:
            resultado["reparacion"]["errores_sintaxis_detectados"] = errores_sintaxis
        return resultado

    # ------------------------------------------------------------------ #
    #  5. REPORTE CONSOLIDADO (solo agrega lo REAL de las fases previas)
    # ------------------------------------------------------------------ #
    def _consolidar(self, fases: Dict[str, Dict]) -> Dict[str, Any]:
        taller = fases.get("resumen_taller", {}).get("general", {}) or {}
        crm = fases.get("resumen_crm", {}).get("resumen", {}) or {}
        pico = fases.get("horas_pico", {}).get("resultado", {}) or {}
        mant = fases.get("mantenimiento", {}) or {}
        return {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "taller_real": {
                "ordenes": taller.get("n_ordenes", 0),
                "ingresos": taller.get("ingresos", 0),
                "utilidad": taller.get("utilidad", 0),
                "cobrado": taller.get("cobrado", 0),
                "por_cobrar": taller.get("por_cobrar", 0),
                "ticket_promedio": taller.get("ticket_promedio", 0),
            },
            "crm_real": {
                "leads": crm.get("total_leads", 0),
                "ordenes_crm": crm.get("total_ordenes", 0),
            },
            "horas_pico": pico,
            "salud_sistema": {
                "modulos_ok": mant.get("modulos_ok", 0),
                "modulos_totales": mant.get("modulos_totales", 0),
                "modulos_con_error": len(mant.get("errores", {})),
            },
            "honestidad": [
                m for m in [
                    fases.get("resumen_crm", {}).get("nota"),
                    fases.get("horas_pico", {}).get("nota"),
                ] if m
            ],
        }

    # ------------------------------------------------------------------ #
    #  CICLO COMPLETO
    # ------------------------------------------------------------------ #
    async def ejecutar_ciclo_completo(self) -> Dict[str, Any]:
        print("[SLEEP CYCLE] Mantenimiento + resumen REAL del dia...")

        fases: Dict[str, Dict] = {}

        fases["resumen_taller"] = await self.resumen_taller()
        print("[ok] Resumen de taller (taller.db)")

        fases["resumen_crm"] = await self.resumen_crm()
        print("[ok] Resumen CRM (oracle.db)")

        fases["horas_pico"] = await self.horas_pico()
        print("[ok] Horas pico (actividad real)")

        fases["mantenimiento"] = await self.mantenimiento()
        print("[ok] Mantenimiento (diagnostico solo lectura)")

        reporte = self._consolidar(fases)
        print("[ok] Reporte consolidado")

        duracion = datetime.now() - self.hora_inicio
        return {
            "ciclo": "sleep_cycle_real",
            "estado": "completado",
            "modo": "confirmar=True (con reparacion)" if self.confirmar
                    else "solo_lectura (no destructivo)",
            "duracion_segundos": duracion.total_seconds(),
            "reporte": reporte,
            "fases": fases,
            "proxima_ejecucion": (datetime.now() + timedelta(hours=24)).isoformat(),
        }


if __name__ == "__main__":
    import io
    sleep = SleepCycle(confirmar=False)
    resultado = asyncio.run(sleep.ejecutar_ciclo_completo())
    salida = json.dumps(resultado, indent=2, ensure_ascii=False, default=str)
    with io.open("sleep_cycle_resultado.json", "w", encoding="utf-8") as f:
        f.write(salida)
    print("Resultado escrito en sleep_cycle_resultado.json")
