# -*- coding: utf-8 -*-
"""
AURORA · VALIDADOR DE HONESTIDAD (candado estructural anti-simulación)
======================================================================

POR QUÉ EXISTE
--------------
Durante el 29 y 30 de julio de 2026, AURORA inventó cosas SIETE veces, todas
por la misma causa de fondo: cuando la frase del usuario no calzaba con un
candado exacto, el mensaje caía a un modelo de IA que NO tiene acceso al
sistema — pero respondía igual, como si lo tuviera. Casos reales:

  · Dijo "CorelDRAW: PDF cargado correctamente... Vectorización finalizada...
    resultado: vectorizado_con_coreldraw.pdf". Ese archivo nunca existió.
  · Generó un "MANUAL MAESTRO DE COMANDOS" con 6 de 8 comandos INVENTADOS
    (AGENDA/agrega_usuario, CORE/evalua_expresion... ninguno existe).
  · Generó un "kit de configuración crítica" que mandaba ejecutar
    REINICIAR_NGROK.bat, OPTIMIZAR_PC.bat y NEXUS.bat — los tres inexistentes.
  · Inventó capacidades suyas (diseño de interiores, ciencia) al describirse.

Agregar frases al enrutador una por una es infinito: siempre habrá una forma
de decir las cosas que nadie anticipó. La corrección de RAÍZ no es adivinar
mejor las frases — es hacer **estructuralmente imposible que AURORA afirme
algo que no puede comprobar**. Aunque no entienda la orden, lo peor que puede
pasar es un "no te entendí", nunca una mentira.

CÓMO FUNCIONA
-------------
Esto es CÓDIGO, no una instrucción de prompt. Un modelo chico ignora las
reglas del prompt (pasó de verdad, varias veces); este candado no se puede
ignorar porque corre después, sobre el texto ya escrito, antes de que salga.

Tres comprobaciones, todas contra la realidad:
  1. ¿Afirma haber EJECUTADO algo, sin que se haya ejecutado nada real?
  2. ¿Menciona comandos/herramientas que no están en el registro real?
  3. ¿Menciona archivos que no existen en el disco?

Nunca borra la respuesta: le agrega una corrección visible y honesta, para
que Anuar vea qué se dijo y por qué no es confiable.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# ── 1. Afirmaciones de acción CUMPLIDA ───────────────────────────────────
# Solo pasado/consumado. "voy a", "puedo", "te lo hago" son promesas, no
# afirmaciones falsas — esas no se tocan.
_AFIRMA_ACCION = (
    r"\bya (?:lo |la |los |las )?(?:hice|abrí|abri|guardé|guarde|envié|envie|"
    r"convertí|converti|creé|cree|moví|movi|copié|copie|publiqué|publique|"
    r"exporté|exporte|instalé|instale|borré|borre|eliminé|elimine)\b",
    r"\b(?:he|hemos) (?:creado|generado|guardado|enviado|convertido|abierto|"
    r"exportado|publicado|movido|copiado|instalado|borrado|eliminado)\b",
    r"\b(?:archivo|documento|pdf|dxf|svg|imagen|reporte|catálogo|catalogo) "
    r"(?:ya )?(?:fue |ha sido |se ha |está |esta )?(?:generado|creado|guardado|"
    r"exportado|convertido)\b",
    r"\b(?:conversión|conversion|vectorización|vectorizacion|exportación|exportacion|"
    r"publicación|publicacion|instalación|instalacion) (?:finalizada|completada|"
    r"terminada|exitosa|lista)\b",
    r"\bse (?:ha |han )?(?:guardado|generado|creado|enviado|exportado|publicado)\b",
    r"\b(?:listo|hecho)[:,]\s*(?:el |la |tu )?(?:archivo|pdf|dxf|documento)\b",
    r"\bcargado correctamente\b",
    r"\bresultado:\s*\S+\.(?:pdf|dxf|svg|png|jpg|cdr|xlsx|docx|zip|bat|exe)\b",
)

# ── 2. Nombres de comandos/herramientas ──────────────────────────────────
# Formato real del registro: CARPETA/modulo:funcion  (ej. AGENDA/agenda:crear_cita)
# También se captura CARPETA/algo por si inventa la forma corta.
_RE_COMANDO = re.compile(r"\b([A-Z][A-Z_]{2,20})/([a-zA-Z_][\w]*)(?::([a-zA-Z_][\w.]*))?")

# ── 3. Archivos mencionados como si existieran ───────────────────────────
_RE_RUTA = re.compile(r"[A-Za-z]:\\[^\r\n\"'<>|]+?\.[A-Za-z0-9]{2,5}")
# Sin espacios a proposito: con [\w\-. ] el regex se comia las palabras de antes
# y reportaba "Si el sistema se congela ejecuta REINICIAR_NGROK.bat" como si ese
# fuera el nombre del archivo. Detectaba bien, pero el aviso quedaba ilegible.
_RE_ARCHIVO_SUELTO = re.compile(r"\b([\w\-.]{2,60}\.(?:bat|exe|ps1|py|dxf|svg|cdr))\b", re.I)

# Motores que SOLO escriben texto: no tienen manos, no ejecutan nada.
# Si la respuesta viene solo de estos, cualquier afirmación de acción es falsa.
_MOTORES_SIN_MANOS = {
    "motor_analisis", "conversacional", "razonador", "motor_reasoning",
    "motor_coaching", "motor_negocios", "chat", "llm", "groq",
}


def _hubo_ejecucion_real(motores_usados) -> bool:
    """True si la respuesta vino de algo que SÍ puede ejecutar (un candado
    directo o el router universal ejecutando una herramienta)."""
    if not motores_usados:
        return False
    usados = {str(m).strip().lower() for m in motores_usados}
    return bool(usados - _MOTORES_SIN_MANOS)


def _comandos_inventados(texto: str, registro_claves) -> List[str]:
    """Comandos con formato de herramienta que NO están en el registro real."""
    if not registro_claves:
        return []
    # Solo se juzgan carpetas que EXISTEN de verdad en el registro. Sin esto el
    # regex marcaba "PDF/CDR" y "PNG/JPG" como comandos inventados (encontrado en
    # vivo 2026-07-31): son formatos de archivo, no comandos. Un candado que da
    # avisos falsos se vuelve ruido, se ignora, y deja de servir para lo que existe.
    carpetas_reales = {k.split("/", 1)[0] for k in registro_claves if "/" in k}
    if not carpetas_reales:
        return []

    inventados, vistos = [], set()
    for m in _RE_COMANDO.finditer(texto):
        carpeta, modulo, funcion = m.group(1), m.group(2), m.group(3)
        mencion = m.group(0)
        if mencion in vistos or carpeta not in carpetas_reales:
            continue
        vistos.add(mencion)
        # Se acepta si existe tal cual, o si algo del registro empieza igual
        # (para no marcar como falso un "MARKETING/plan_monetizacion" válido
        # citado sin la función).
        prefijo = f"{carpeta}/{modulo}"
        if any(k == mencion or k.startswith(prefijo) for k in registro_claves):
            continue
        inventados.append(mencion)
    return inventados


def _archivos_inexistentes(texto: str) -> List[str]:
    """Archivos que la respuesta menciona pero que no están en el disco."""
    faltantes, vistos = [], set()
    for ruta in _RE_RUTA.findall(texto):
        ruta = ruta.strip().rstrip(".,;:)")
        if ruta in vistos:
            continue
        vistos.add(ruta)
        try:
            if not Path(ruta).exists():
                faltantes.append(ruta)
        except OSError:
            faltantes.append(ruta)
    # Archivos sueltos tipo "REINICIAR_NGROK.bat": se buscan en la raíz del proyecto.
    for nombre in _RE_ARCHIVO_SUELTO.findall(texto):
        nombre = nombre.strip()
        if nombre in vistos or "\\" in nombre or "/" in nombre:
            continue
        vistos.add(nombre)
        try:
            if not (RAIZ / nombre).exists() and not list(RAIZ.glob(f"**/{nombre}"))[:1]:
                faltantes.append(nombre)
        except OSError:
            pass
    return faltantes


def revisar(respuesta: str, motores_usados=None, registro_claves=None) -> Tuple[str, Dict]:
    """Revisa una respuesta ANTES de que salga y le agrega la corrección honesta.

    Devuelve (respuesta_final, informe). El informe dice qué se detectó — sirve
    para registrar y para las pruebas.

    NUNCA borra la respuesta: agrega la corrección al final, visible, para que
    Anuar vea qué se dijo y por qué no es confiable.
    """
    informe = {"afirmo_accion_sin_hacerla": False, "comandos_inventados": [],
               "archivos_inexistentes": [], "corregida": False}
    if not respuesta or not respuesta.strip():
        return respuesta, informe

    avisos: List[str] = []
    ejecuto = _hubo_ejecucion_real(motores_usados)

    # 1) ¿Dice que hizo algo, sin haber ejecutado nada?
    if not ejecuto:
        bajo = respuesta.lower()
        for patron in _AFIRMA_ACCION:
            if re.search(patron, bajo):
                informe["afirmo_accion_sin_hacerla"] = True
                avisos.append(
                    "⚠️ Arriba dije que ya había hecho algo, pero **no ejecuté nada**: "
                    "esa parte de la respuesta la escribió el modelo de texto, que no "
                    "tiene manos. Pídemelo directo con la ruta completa y lo hago de verdad.")
                break

    # 2) ¿Cita comandos que no existen?
    inventados = _comandos_inventados(respuesta, registro_claves)
    if inventados:
        informe["comandos_inventados"] = inventados
        lista = ", ".join(f"`{c}`" for c in inventados[:6])
        avisos.append(
            f"⚠️ Mencioné {'un comando que no existe' if len(inventados) == 1 else 'comandos que no existen'}: "
            f"{lista}. No los uses — pídeme la lista real y la saco del registro del sistema.")

    # 3) ¿Menciona archivos que no están?
    faltantes = _archivos_inexistentes(respuesta)
    if faltantes:
        informe["archivos_inexistentes"] = faltantes
        lista = ", ".join(f"`{a}`" for a in faltantes[:5])
        avisos.append(
            f"⚠️ {'Este archivo no existe' if len(faltantes) == 1 else 'Estos archivos no existen'} "
            f"en el disco: {lista}. Si dije que lo generé, no es cierto.")

    if not avisos:
        return respuesta, informe

    informe["corregida"] = True
    return (respuesta.rstrip() + "\n\n---\n" + "\n".join(avisos)), informe
