# -*- coding: utf-8 -*-
"""AURORA · Cargar el `.env` desde donde se necesita, no desde quien llama.

╔══════════════════════════════════════════════════════════════════════════╗
║ EL PROBLEMA QUE RESUELVE (encontrado el 2026-08-25)                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Hasta hoy, el único que cargaba el `.env` era `run_aurora.py`. `consciencia.py`
—que es quien de verdad necesita `GROQ_API_KEY`— daba por hecho que alguien
más lo había cargado antes.

Consecuencia real, medida: cualquier otra forma de arrancar la Consciencia
(una prueba, `PRUEBAS_VIVAS/arnes.py`, un script suelto) levanta una AURORA
**sin llaves y sin decirlo**. No falla: se cae calladita al modelo local de
Ollama, con 180 segundos de espera por llamada. Un "hola" tardó más de diez
minutos y contestó igual. Nadie se entera de que está contestando el modelo
chico en vez del bueno.

Es la misma causa de fondo de todo el plan de reparación: **una lista que
alguien tiene que acordarse de mantener** —aquí, "acuérdate de cargar el
entorno antes de importar"— siempre termina olvidada. La configuración se
carga donde se usa.

Llamar a `cargar()` muchas veces no cuesta nada ni pisa variables que ya
estén puestas en el sistema: `load_dotenv` no sobrescribe lo que ya existe.
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / ".env"

_cargado = False


def cargar() -> bool:
    """Carga el `.env` de AURORA. Devuelve si el archivo existe.

    Segura de llamar tantas veces como haga falta: solo lee el archivo la
    primera vez, y nunca pisa una variable que ya venga del sistema.
    """
    global _cargado
    if _cargado:
        return ARCHIVO.exists()
    _cargado = True
    try:
        from dotenv import load_dotenv
        load_dotenv(ARCHIVO)
    except ImportError:
        # Sin python-dotenv, el sistema sigue: las variables pueden venir del
        # entorno de Windows. No es motivo para tumbar AURORA.
        pass
    return ARCHIVO.exists()


def falta(*nombres: str) -> list[str]:
    """Cuáles de estas variables NO están puestas.

    Sirve para avisar en voz alta en vez de degradarse en silencio. Devuelve
    NOMBRES, nunca valores: un secreto no se imprime ni en un log.
    """
    cargar()
    return [n for n in nombres if not os.getenv(n)]
