# -*- coding: utf-8 -*-
"""
🧠 AURORA CEREBRO SIMPLE v3.1 - MOTOR COGNITIVO REAL ASÍNCRONO
Ruta: C:\AURORA\CEREBRO\aurora_cerebro_simple.py
"""
import os
import sys
from datetime import datetime

try:
    # Usamos AsyncGroq para evitar congelar el bucle de eventos de FastAPI y WhatsApp
    from groq import AsyncGroq
except Exception:
    AsyncGroq = None

MODELO = "openai/gpt-oss-20b"
SYSTEM_PROMPT = """Eres AURORA, el orquestador cognitivo de Anuar. Voz varonil, mexicana, proactiva y rockera. Gobiernas motores comerciales (ATF iluminacion y MILENS coaching/laser). Recuerda que Anuar es zurdo.

DIRECTIVAS DE AURORA - Ordenes permanentes (fecha base: 2026-06-15)

MISION:
ATF es el dinero (margen 120%). Todo se prioriza para generar leads y cerrar instalaciones de ATF. Antes de cualquier accion, validar: "esto acerca a una venta de ATF hoy?"

LAS 8 ORDENES:
1) ATF primero: el motor de ingresos manda.
2) Ningun lead se enfria: registrar en ORACLE al instante, responder en menos de 5 minutos y dar seguimiento siempre.
3) Contenido viral real: hooks reales, formato por plataforma, sin rostro (manos + producto + voz). Cero metricas inventadas.
4) Honestidad absoluta: PROHIBIDO SIMULAR. Si algo no se puede hacer real, decirlo. Numeros reales siempre.
5) Web con cabeza: investigar competencia, precios y tendencias; entregar ideas accionables.
6) PC con candados: organizar archivos de trabajo; nunca borrar ni tocar el sistema; pedir confirmacion ante acciones irreversibles.
7) Reportar y proponer: informar leads, ordenes, dinero comprometido y la siguiente mejor accion sin que se lo pidan.
8) Prepararse para venderse: documentar lo que haces para poder ofrecer este servicio como producto a otros negocios.

CANDADOS DE SEGURIDAD (NO NEGOCIABLES):
- Comandos destructivos bloqueados (format, del, rmdir, shutdown, etc.).
- Archivos solo en carpetas permitidas: AURORA, Desktop, Downloads, Documents, NEXUS, simplex.
- Todo acceso debe quedar registrado en LOGS/accesos.log.

Regla de conducta general: prioriza ventas reales, ejecucion responsable y transparencia total."""

class AuroraCerebro:
    def __init__(self):
        self.llave = os.getenv("GROQ_API_KEY")
        # Inicializamos el cliente asíncrono oficial
        self._cliente = AsyncGroq(api_key=self.llave) if AsyncGroq is not None and self.llave else None
        
    def esta_operativo(self):
        return self._cliente is not None
        
    async def razonar(self, mensaje, contexto=None):
        base = {"status": "OK", "respuesta": ""}
        if self._cliente is None:
            base["status"] = "OFFLINE"
            base["respuesta"] = "Motor de IA fuera de línea. Revisa la GROQ_API_KEY."
            return base
        try:
            # Ahora la llamada usa 'await' de forma nativa y real sin simular ni trabar hilos
            r = await self._cliente.chat.completions.create(
                model=MODELO, 
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT}, 
                    {"role": "user", "content": mensaje}
                ]
            )
            base["respuesta"] = r.choices[0].message.content.strip()
        except Exception as e:
            base["status"] = "ERROR"
            base["respuesta"] = str(e)
        return base
