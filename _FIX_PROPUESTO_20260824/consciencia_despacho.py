# -*- coding: utf-8 -*-
"""AURORA · FIX DE DESPACHO — bloque propuesto para CEREBRO/consciencia.py

╔══════════════════════════════════════════════════════════════════════════╗
║ ESTE ARCHIVO NO SE EJECUTA. Es el bloque de código propuesto, escrito     ║
║ aparte para revisarlo antes de tocar consciencia.py.                      ║
╚══════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════
EL PROBLEMA (hallazgo crítico 2.1 de la auditoría)
═══════════════════════════════════════════════════════════════════════════

Hoy, cuando una familia reconoce un mensaje, hace DOS cosas a la vez
(consciencia.py:2644 y 2665):

    1. EXCLUYE a todos los demás candados          (línea 2644: `continue`)
    2. OBLIGA al suyo a ejecutarse aunque su propio
       disparador diga que no aplica                (línea 2665: `_por_familia`)

El resultado real: la familia `abrir_navegador` matchea con CUALQUIER mensaje
que empiece con "abre / ábreme / métete a / entra a / vete a" (solo se excluye
si menciona Corel o trae una ruta `C:\\`). Entonces:

    "abre mi agenda de hoy"  →  abrir_navegador  →  "Dime qué página abro"

...aunque `_es_agenda()` reconoce perfectamente "mi agenda". El candado de
agenda nunca llega a ser consultado.

═══════════════════════════════════════════════════════════════════════════
POR QUÉ EL ARREGLO OBVIO ESTÁ MAL — esto es lo importante
═══════════════════════════════════════════════════════════════════════════

El arreglo que sale solo es: "que la familia respete el disparador del
candado". **Eso rompe algo que hoy sí funciona.**

Caso real que la familia existe para resolver:

    "traigo una jetta quiero ponerle aozoom cuanto me sale"

El disparador propio de `servicio_atf` NO reconoce esa frase. El de `cotizar`
sí (por "cuánto me sale"), y `cotizar` va antes en la fila. Sin el poder de la
familia para pasar por encima del disparador, esa frase se la lleva el
cotizador de catálogo y contesta cualquier cosa. Ese fue un bug real, ya
corregido, y **no se puede reintroducir**.

O sea: la familia SÍ necesita poder mandar sobre un disparador. El problema no
es el mecanismo — es que hay una familia mal escrita que reclama de más.

═══════════════════════════════════════════════════════════════════════════
EL ARREGLO DE RAÍZ — dos partes, ninguna es un parche a "abre"
═══════════════════════════════════════════════════════════════════════════

PARTE 1 · Una regla estructural sobre qué puede ser una familia.

    Una familia describe CÓMO PIDE ANUAR una cosa. Entonces el patrón tiene
    que contener LA COSA, no nada más el verbo.

    `^(abre|abreme|metete a|entra a|vete a)\\b` no nombra ninguna cosa: es un
    verbo suelto. Por eso se lleva la agenda, el código, y lo que caiga. No es
    una familia válida; es una red de arrastre.

    Esto NO se arregla corrigiendo ese patrón a mano (eso sería el parche que
    la directiva prohíbe). Se arregla con una PRUEBA que recorre las 31
    familias y falla si alguna puede matchear una frase de puro verbo. Así
    esta familia se corrige, y ninguna futura puede nacer con el mismo
    defecto.

PARTE 2 · Que una familia equivocada deje de ser fatal.

    Hoy, si la familia se equivoca, el mensaje muere ahí: el candado
    equivocado contesta su respuesta genérica y ya. Nadie más lo ve.

    Se agrega un contrato explícito: un candado puede decir "esto no era mío"
    devolviendo `no_aplica: True`. Cuando eso pasa, el despachador **sigue
    con los demás candados** en vez de devolver la respuesta inútil.

    No es adivinar leyendo el texto de la respuesta — es que el candado lo
    declare. `_abrir_navegador_real` ya tiene el punto exacto donde sabe que
    no aplica: la rama donde no encontró ni dominio ni sitio conocido.

    Con esto, aunque una familia se equivoque, el sistema se recupera solo.

═══════════════════════════════════════════════════════════════════════════
"""

# ═════════════════════════════════════════════════════════════════════════
# CAMBIO 1 · consciencia.py — el bucle de despacho
# ═════════════════════════════════════════════════════════════════════════
#
# ANTES (líneas 2635-2666, resumido a lo que cambia):
#
#     for _nombre_candado, _trigger, _metodo, _motor_id in _CANDADOS:
#         ...
#         if _candado_de_familia and _nombre_candado != _candado_de_familia:
#             continue                      # ← excluye a todos los demás
#         ...
#         if not _trigger(mensaje) and not _por_aprendizaje and not _por_familia:
#             continue
#         ...
#         real = await getattr(self, _metodo)(mensaje)
#         # ← lo que devuelva se acepta, aunque no haya sabido qué hacer
#
# DESPUÉS: dos vueltas. La familia conserva su poder, pero si su candado
# declara que no aplica, la segunda vuelta atiende al resto.

_PSEUDO_DESPUES = r'''
        _candado_de_familia = _candado_por_familia(mensaje)

        # Dos vueltas. En la primera solo compite el candado que nombró la
        # familia (conserva su poder de pasar por encima del disparador, que
        # es lo que resuelve "traigo una jetta ... aozoom ... cuanto me sale").
        # Si ese candado declara que no era suyo, la segunda vuelta corre la
        # fila completa con las reglas normales, en vez de morir ahí.
        _vueltas = ([_candado_de_familia, None] if _candado_de_familia else [None])

        for _solo_este in _vueltas:
            for _nombre_candado, _trigger, _metodo_candado, _motor_id_candado in _CANDADOS:
                if _solo_memoria and _nombre_candado not in ("memoria", "ver_aprendizaje"):
                    continue

                if _solo_este is not None:
                    # Primera vuelta: únicamente el candado de la familia.
                    if _nombre_candado != _solo_este:
                        continue
                    _por_familia = True
                else:
                    # Segunda vuelta: la fila normal. El candado de la familia
                    # ya tuvo su turno y dijo que no era suyo, así que aquí no
                    # se le vuelve a dar trato preferente.
                    _por_familia = False
                    if _candado_de_familia and _nombre_candado == _candado_de_familia:
                        continue

                if _nombre_candado == "accion_fisica" and (set(motor_ids) & _MOTORES_EJECUTORES):
                    continue
                if _tema_sistema and _nombre_candado in _CANDADOS_DE_VENTA:
                    continue

                _por_aprendizaje = (_aprendido is not None
                                    and _aprendido.get("herramienta") == _motor_id_candado)

                if _nombre_candado == "crear_capacidad" and not FABRICA_HABILITADA:
                    if _trigger(mensaje):
                        self._agregar_sesion(session_id, mensaje, _MSG_FABRICA_FUERA)
                        ms = round((datetime.utcnow() - inicio).total_seconds() * 1000)
                        return {"respuesta": _MSG_FABRICA_FUERA,
                                "motores_usados": ["fabrica_fuera"],
                                "temperatura_lead": "frio", "duracion_ms": ms,
                                "timestamp": inicio.isoformat()}
                    continue

                if not _trigger(mensaje) and not _por_aprendizaje and not _por_familia:
                    continue

                if _por_familia and not _trigger(mensaje):
                    logger.info(f"[LENGUA] '{mensaje[:40]}' → {_nombre_candado} "
                                f"(su lista no la reconoció; la familia sí)")
                if _por_aprendizaje and not _trigger(mensaje):
                    logger.info(f"[APRENDIDO] '{mensaje[:40]}' → {_nombre_candado} "
                                f"(parecido {_aprendido.get('parecido')})")

                # ... (el bloque de ejecución de cada candado queda IGUAL) ...
                real = await getattr(self, _metodo_candado)(mensaje)

                # NUEVO: el candado puede declarar que el mensaje no era suyo.
                # Solo se le hace caso en la primera vuelta y solo si llegó ahí
                # por la familia — si su propio disparador dijo que sí, su
                # respuesta se respeta aunque sea un fallback.
                if real.get("no_aplica") and _por_familia and not _trigger(mensaje):
                    logger.info(f"[LENGUA] {_nombre_candado} declaró que "
                                f"'{mensaje[:40]}' no era suyo; sigo con los demás")
                    break        # corta la primera vuelta, pasa a la fila normal

                self._agregar_sesion(session_id, mensaje, real["respuesta"])
                # ... (resto del cuerpo original, sin cambios) ...
'''


# ═════════════════════════════════════════════════════════════════════════
# CAMBIO 2 · consciencia.py — `_abrir_navegador_real` declara cuándo no aplica
# ═════════════════════════════════════════════════════════════════════════
#
# ANTES (~línea 3238):
#     if not destino:
#         return {"respuesta": "Dime qué página abro (ej. youtube, facebook...)"}
#
# DESPUÉS: la misma respuesta, pero marcada. Si el usuario de verdad quería
# abrir algo, la sigue viendo igual. Si llegó aquí por error de la familia,
# el despachador ahora puede seguir buscando.

_PSEUDO_NO_APLICA = r'''
        if not destino:
            return {"respuesta": "Dime qué página abro (ej. youtube, facebook, mercadolibre).",
                    # No encontré ni dominio ni sitio conocido: si me trajo la
                    # familia y no mi propio disparador, esto no era mío.
                    "no_aplica": True}
'''


# ═════════════════════════════════════════════════════════════════════════
# CAMBIO 3 · tests/ — la regla estructural que impide que vuelva a pasar
# ═════════════════════════════════════════════════════════════════════════
#
# Esta es la parte que hace que sea una corrección de raíz y no un parche:
# no corrige el patrón de `abrir_navegador`, obliga a que TODAS las familias
# —las 31 de hoy y las que se agreguen— nombren la cosa que piden.

_PRUEBA_PROPUESTA = r'''
# tests/test_familias_no_son_red_de_arrastre.py

"""Una familia describe CÓMO PIDE ANUAR una cosa concreta.

Si su patrón matchea una frase de puro verbo ("abre algo", "hazme eso"),
no es una familia: es una red de arrastre que se lleva mensajes de otros
candados. Esta prueba nació del bug real donde "abre mi agenda de hoy"
abría el navegador (auditoría 2026-08-24, hallazgo 2.1).
"""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _consciencia():
    ruta = RAIZ / "CEREBRO" / "consciencia.py"
    spec = importlib.util.spec_from_file_location("consciencia", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Frases de puro verbo: no nombran NADA. Ninguna familia debe reclamarlas.
FRASES_VACIAS = [
    "abre", "abreme eso", "abre esto", "entra ahi", "vete alla",
    "hazlo", "hazme eso", "dame eso", "checa esto", "revisa eso",
    "metete ahi", "ponlo", "mandalo", "sacalo",
]


def test_ninguna_familia_reclama_una_frase_sin_sustancia():
    c = _consciencia()
    culpables = []
    for frase in FRASES_VACIAS:
        candado = c._candado_por_familia(frase)
        if candado:
            culpables.append(f"{frase!r} → {candado}")
    assert not culpables, (
        "Estas familias matchean frases que no nombran nada, así que van a "
        "secuestrar mensajes de otros candados:\n  " + "\n  ".join(culpables))


def test_abre_mi_agenda_va_a_la_agenda_no_al_navegador():
    """El bug exacto de la auditoría (hallazgo 2.1)."""
    c = _consciencia()
    assert c._candado_por_familia("abre mi agenda de hoy") != "abrir_navegador"


def test_el_caso_de_atf_sigue_funcionando():
    """La familia NO pierde su poder: este caso real depende de que la familia
    mande sobre el disparador de `cotizar`. Si esta prueba se cae, el arreglo
    del navegador rompió algo que ya servía."""
    c = _consciencia()
    frase = "traigo una jetta quiero ponerle aozoom cuanto me sale"
    assert c._candado_por_familia(frase) == "servicio_atf"
'''


# ═════════════════════════════════════════════════════════════════════════
# ANTES DE APLICAR — qué falta y qué hay que comprobar
# ═════════════════════════════════════════════════════════════════════════
#
# 1. El patrón de la familia `abrir_navegador` (consciencia.py:2010) tiene que
#    reescribirse para exigir sustancia (un dominio, "pagina", "internet", un
#    sitio conocido). NO se escribió aquí a propósito: primero hay que correr
#    la prueba del CAMBIO 3 contra las 31 familias, porque es muy probable que
#    `abrir_navegador` no sea la única red de arrastre. Corregir solo esa sin
#    mirar las otras 30 sería repetir el error que causó todo esto.
#
# 2. Las 174 frases reales de PRUEBAS_VIVAS/ tienen que resolver al MISMO
#    candado antes y después del cambio. Es la única forma de saber que no se
#    rompió nada — y por eso la Fase 1 del plan (poner la red) va antes que
#    esta.
#
# 3. Este cambio toca el corazón del lenguaje. Va en su propia rama de git,
#    con las 425 pruebas corriendo antes y después.
