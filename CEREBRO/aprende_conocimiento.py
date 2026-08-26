# -*- coding: utf-8 -*-
"""
AURORA · «AURORA APRENDE» — que Anuar le enseñe DATOS y REGLAS, no solo frases
=============================================================================

POR QUÉ EXISTE
--------------
Idea de Anuar, 2026-08-26, textual:

    *"estaría suuuuper chingón que tenga un comando de aprendizaje. Ejemplo:
    «aurora aprende», ella contesta «sí claro, dime», y le digo: «aurora, un
    tabloide mide 33x48, aprende que debes dejar un margen de 5mm siempre en
    todas las tareas»... ella dice «comprendo» cuando REALMENTE aprendió"*

Y remató con la mejor parte:

    *"si lo logras copio su manual y le digo aurora aprende y le pego su
    propio manual"*

Ahí está el valor de verdad: no es el manual, es que le pueda **pegar
cualquier cosa** —la lista de precios de un proveedor, la ficha técnica de un
material, sus propios apuntes— y ella saque los datos y las reglas de ahí.

QUÉ LO SEPARA DE LO QUE YA HABÍA
--------------------------------
Ya existían dos formas de aprender, y ésta es la tercera:

1. `aprende_del_usuario.py` — aprende SOLA cómo habla él. Pasiva: hay que
   fallar primero para aprender.
2. El candado `ensenar` — él le enseña un sinónimo: «cuando te diga X es Y».
   Enlaza una frase con un comando que ya existe.
3. **Esto** — él le enseña un DATO («un tabloide mide 33x48») o una REGLA
   («deja siempre 5 mm de margen»). No es una forma de hablar: es algo que
   ella tiene que SABER y aplicar.

EL «COMPRENDO» NO PUEDE SER MENTIRA
-----------------------------------
Él mismo puso el dedo en la llaga: *"ella dice comprendo cuando realmente
aprendió"*. Este proyecto ya tiene un candado estructural contra fingir
(`CEREBRO/validador_honestidad.py`, 4 bugs de invención cerrados en julio), y
esto no lo va a romper.

Por eso hay DOS destinos distintos, y ella contesta distinto según cuál:

* **Dato con número** → se guarda en `CONFIG/catalogo_servicios.json`, dentro
  de `aprendido_de_anuar`. Ésa es la puerta única de sus cifras
  (`TALLER/formula_precios.numero`), así que **todo módulo que ya pregunta lo
  respeta al instante**. `donde_aplica()` sale a buscar al disco quién lo
  pregunta de verdad, y ella nombra esos módulos. Ese "comprendo" es cierto.

* **Regla de conducta** → se guarda en `CONFIG/conocimiento_anuar.json` y se
  le mete en su contexto para que la tome en cuenta al contestar. Pero
  **ningún módulo la aplica solo**, y eso se le dice en la cara. Aquí ella NO
  dice "comprendo" a secas: dice "me lo guardé y lo tomo en cuenta al hablar
  contigo, pero todavía no hay módulo que lo aplique solo".

La diferencia entre las dos respuestas es la diferencia entre una herramienta
en la que se puede confiar y una que le va a fallar el día que más la
necesite.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "CONFIG" / "catalogo_servicios.json"
CONOCIMIENTO = RAIZ / "CONFIG" / "conocimiento_anuar.json"

# Dónde se busca quién pregunta por un número. Son las carpetas con código que
# de verdad corre; no tiene caso barrer pruebas ni archivos congelados.
CARPETAS_VIVAS = ("TALLER", "MOTORES", "CEREBRO", "EDITOR", "CORE",
                  "MARKETING", "PUBLICADOR")

# Cuánto texto se acepta de una pegada. Su manual entero son ~12 KB; el margen
# es de sobra y evita que un pegado accidental de medio proyecto la atore.
MAX_TEXTO = 200_000


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", str(t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip()


def _clave_desde(texto: str) -> str:
    """Un nombre de clave estable a partir de lo que él dijo.

    «un tabloide mide 33x48» → `tabloide`. Se queda con los sustantivos que
    importan y tira las palabras de relleno, para que si mañana lo vuelve a
    dictar de otra forma caiga en la MISMA clave en vez de crear una gemela.
    """
    relleno = {"un", "una", "el", "la", "los", "las", "de", "del", "que", "es",
               "son", "mide", "miden", "y", "a", "en", "por", "para", "con",
               "siempre", "todas", "todos", "aprende", "aurora", "debes",
               "deves", "dejar", "deja", "mi", "mis", "su", "sus", "cada",
               "tiene", "tienen", "lleva", "llevan", "se", "lo", "le"}
    # Fuera cualquier pedazo que traiga un número. Si la clave llevara la cifra
    # dentro («tabloide_33x48_ancho»), el día que él dicte «el tabloide mide
    # 34x49» nacería una clave GEMELA en vez de corregir la vieja, y se
    # quedaría con las dos medidas al mismo tiempo sin enterarse.
    palabras = [p for p in re.findall(r"[a-z0-9]+", _norm(texto))
                if p not in relleno and not re.search(r"\d", p)]
    return "_".join(palabras[:3]) or "dato"


def _clave_existente(propuesta: str, textual: str) -> str:
    """Si ya hay una clave suya que significa lo mismo, se usa ÉSA.

    La falla que esto cierra, encontrada en la primera prueba: «el minuto de
    corte lo cobro a 8 pesos» generaba `minuto_corte_cobro`, gemela de su
    `minuto_corte` de verdad. Anuar habría creído que cambió el precio del
    minuto y no habría cambiado nada, porque los módulos preguntan por la
    clave vieja. Un gemelo silencioso es el bug más caro de este proyecto.
    """
    try:
        from TALLER import formula_precios as fp
        existentes = set(fp.numeros())
    except Exception:
        return propuesta
    if propuesta in existentes:
        return propuesta

    # Todo lo que él dijo, en piezas: palabras sueltas y también los números
    # partidos («2.7» cuenta como «2.7», «2_7», «2» y «7»), porque sus claves
    # llevan el número con guion bajo: `hoja_mdf_2_7`.
    n = _norm(textual)
    piezas = set(re.findall(r"[a-z]+|\d+", n))
    for num in re.findall(r"\d+[.,]\d+", n):
        piezas.add(num.replace(",", "."))
        piezas.add(num.replace(",", "_").replace(".", "_"))
    piezas |= set(propuesta.split("_"))

    # REGLA ESTRICTA, y es la que evita el desastre: una clave suya solo se
    # reusa si **todas** sus piezas aparecen en lo que él acaba de decir.
    #
    # El intento anterior contaba coincidencias parciales y hacía algo peor
    # que crear un gemelo: pisaba el valor equivocado en silencio. «el minuto
    # de corte lo cobro a 8» caía en `minuto_corte_alicia` y le movía el trato
    # de Alicia; «la hoja de mdf de 2.7» caía en `hoja_mdf_5_5`, otro grosor.
    # Justo los números y el nombre propio —lo que distingue una clave de
    # otra— eran lo que se estaba ignorando.
    #
    # Con esto, `minuto_corte_alicia` queda descartada si él no dijo «alicia»,
    # y `hoja_mdf_5_5` si él dijo «2.7». En la duda se crea una clave nueva:
    # una clave de más se ve y se corrige; un precio pisado, no.
    mejor, largo_mejor = propuesta, 0
    for clave in existentes:
        pc = [p for p in clave.split("_") if p]
        if not pc or not all(p in piezas for p in pc):
            continue
        if len(pc) > largo_mejor:          # gana la más específica que sí calza
            mejor, largo_mejor = clave, len(pc)
    return mejor


# Un dato con número que sí se puede guardar como cifra. Cubre las formas en
# que él dicta de verdad: «mide 33x48», «margen de 5mm», «a 20 mm/s», «$110».
_RE_MEDIDA = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:x|×|por)\s*(\d+(?:[.,]\d+)?)\s*"
    r"(mm|cm|m|milimetros?|centimetros?|metros?|pulgadas?)?", re.I)
_RE_CIFRA = re.compile(
    r"(?:\$\s*)?(\d+(?:[.,]\d+)?)\s*"
    r"(mm|cm|m|kg|gr|g|dpi|mm/s|pesos?|mxn|%|min|minutos?|seg|segundos?)?", re.I)


def _numero(s: str) -> float:
    return float(str(s).replace(",", "."))


# Palabras con las que Anuar dice que algo CUESTA. Cuando aparece una de éstas,
# el número que importa es el del dinero, no cualquier otro de la línea.
_DINERO = ("cuesta", "cuestan", "vale", "valen", "cobro", "cobra", "cobran",
           "precio", "sale en", "me sale", "pesos", "mxn", "$")


def _cifra_de(t: str):
    """La cifra que importa de una línea, y su unidad.

    Falla real de la primera prueba, y de las caras: de «la hoja de mdf de 2.7
    me cuesta 110» sacaba **2.7** —el grosor— y lo guardaba como si fuera el
    precio. Un precio equivocado guardado en silencio es exactamente el bug
    que ya costó dinero en este proyecto (el cotizador que decía $8,000 por un
    X1 de $3,149).

    Cuando la línea habla de dinero, se toma el número que va DESPUÉS de la
    palabra de dinero, o el que trae `$`. Si no habla de dinero, el primero.
    """
    n = _norm(t)
    if any(p in n for p in _DINERO):
        # Un número pegado a $ gana siempre.
        m = re.search(r"\$\s*(\d+(?:[.,]\d+)?)", t)
        if m:
            return _numero(m.group(1)), "pesos"
        # Si no, el primero que venga después de la palabra de dinero.
        for palabra in _DINERO:
            i = n.find(palabra)
            if i < 0:
                continue
            m = re.search(r"(\d+(?:[.,]\d+)?)", n[i:])
            if m:
                return _numero(m.group(1)), "pesos"
        # Habla de dinero pero el número va antes («110 la hoja»): el último.
        todos = re.findall(r"(\d+(?:[.,]\d+)?)", t)
        if todos:
            return _numero(todos[-1]), "pesos"
        return None

    c = _RE_CIFRA.search(t)
    if not c or not re.search(r"\d", t):
        return None
    return _numero(c.group(1)), (c.group(2) or "").lower()


def extraer(texto: str) -> Dict[str, Any]:
    """Saca DATOS y REGLAS de un texto pegado. Renglón por renglón.

    No usa IA a propósito: tiene que dar exactamente lo mismo cada vez que se
    le pegue el mismo texto. Un extractor que cambia de humor no se puede
    auditar, y él tiene que poder mirar qué aprendió y quitárselo.
    """
    texto = str(texto or "")[:MAX_TEXTO]
    datos: List[Dict[str, Any]] = []
    reglas: List[str] = []
    vistos = set()

    # Se parte por renglones y también por «y», que es como él encadena
    # («un tabloide mide 33x48 y deja 5mm de margen»).
    trozos: List[str] = []
    for linea in texto.splitlines():
        linea = linea.strip(" \t-•*·#>|")
        if not linea:
            continue
        trozos.extend(t.strip() for t in re.split(r"\s+y\s+(?=\w)", linea) if t.strip())

    for t in trozos:
        if len(t) < 4:
            continue
        n = _norm(t)
        if n in vistos:
            continue
        vistos.add(n)

        # ¿Es una medida de dos lados? («un tabloide mide 33x48»)
        m = _RE_MEDIDA.search(t)
        if m:
            base = _clave_desde(t)
            unidad = (m.group(3) or "cm").lower()
            datos.append({"clave": _clave_existente(f"{base}_ancho", t),
                          "valor": _numero(m.group(1)),
                          "unidad": unidad, "textual": t,
                          "clave_cruda": f"{base}_ancho"})
            datos.append({"clave": _clave_existente(f"{base}_alto", t),
                          "valor": _numero(m.group(2)),
                          "unidad": unidad, "textual": t,
                          "clave_cruda": f"{base}_alto"})
            continue

        # ¿Es una cifra sola? («deja 5mm de margen», «el minuto a $8»)
        c = _cifra_de(t)
        if c:
            base = _clave_desde(t)
            datos.append({"clave": _clave_existente(base, t), "valor": c[0],
                          "unidad": c[1], "textual": t, "clave_cruda": base})
            continue

        # Sin número: es una regla de conducta.
        reglas.append(t)

    return {"status": "OK", "datos": datos, "reglas": reglas,
            "trozos": len(trozos)}


def donde_aplica(clave: str) -> List[str]:
    """Qué módulos preguntan de verdad por este número, buscándolos en el disco.

    Es el corazón de la honestidad de todo esto: no se le dice a Anuar «lo
    voy a aplicar en todos lados» sino los archivos que SÍ lo preguntan. Si
    no lo pregunta nadie, la lista sale vacía y él tiene que enterarse.
    """
    patron = re.compile(r"_?numero\(\s*[\"']" + re.escape(str(clave)) + r"[\"']")
    usan: List[str] = []
    for carpeta in CARPETAS_VIVAS:
        d = RAIZ / carpeta
        if not d.is_dir():
            continue
        for py in d.rglob("*.py"):
            try:
                if patron.search(py.read_text(encoding="utf-8", errors="ignore")):
                    usan.append(f"{carpeta}/{py.name}")
            except Exception:
                continue
    return sorted(set(usan))


def guardar_datos(datos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Los números, a la puerta única de las cifras de Anuar."""
    if not datos:
        return {"status": "OK", "guardados": 0, "detalle": []}
    try:
        d = json.loads(CATALOGO.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "ERROR", "detalle": f"No pude leer el catálogo: {e}"}

    seccion = d.setdefault("aprendido_de_anuar", {})
    seccion["_nota"] = ("Dictado por Anuar directamente a AURORA con «aurora "
                        "aprende». Manda sobre el resto del catálogo.")
    detalle = []
    for item in datos:
        clave, valor = item["clave"], item["valor"]
        antes = seccion.get(clave)
        seccion[clave] = valor
        seccion[f"_{clave}"] = {
            "dijo": item.get("textual", ""),
            "unidad": item.get("unidad", ""),
            "cuando": time.strftime("%Y-%m-%d %H:%M"),
        }
        detalle.append({"clave": clave, "valor": valor,
                        "unidad": item.get("unidad", ""),
                        "cambio": antes is not None and antes != valor,
                        "antes": antes,
                        "aplica_en": donde_aplica(clave)})

    # Se escribe a un lado y se reemplaza de golpe: si truena a media escritura,
    # su catálogo de precios no se queda partido.
    tmp = CATALOGO.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATALOGO)
    return {"status": "OK", "guardados": len(datos), "detalle": detalle}


def guardar_reglas(reglas: List[str]) -> Dict[str, Any]:
    """Las reglas de conducta, a su propio archivo."""
    if not reglas:
        return {"status": "OK", "guardadas": 0, "nuevas": []}
    try:
        d = json.loads(CONOCIMIENTO.read_text(encoding="utf-8"))
    except Exception:
        d = {"_nota": "Reglas que Anuar le dictó a AURORA con «aurora aprende». "
                      "Se le meten en el contexto para que las tome en cuenta.",
             "reglas": []}

    ya = {_norm(r.get("texto", "")) for r in d.get("reglas", [])}
    nuevas = []
    for texto in reglas:
        if _norm(texto) in ya:
            continue
        d["reglas"].append({"texto": texto,
                            "cuando": time.strftime("%Y-%m-%d %H:%M")})
        ya.add(_norm(texto))
        nuevas.append(texto)

    CONOCIMIENTO.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONOCIMIENTO.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONOCIMIENTO)
    return {"status": "OK", "guardadas": len(d["reglas"]), "nuevas": nuevas}


def listar_reglas() -> List[str]:
    """Lo que él le dictó, para metérselo en el contexto al contestar."""
    try:
        d = json.loads(CONOCIMIENTO.read_text(encoding="utf-8"))
        return [r["texto"] for r in d.get("reglas", []) if r.get("texto")]
    except Exception:
        return []


def olvidar_regla(fragmento: str) -> Dict[str, Any]:
    """Él manda: lo que le enseñó, se lo puede quitar."""
    f = _norm(fragmento)
    if not f:
        return {"status": "FALTA", "detalle": "Dime qué regla olvido."}
    try:
        d = json.loads(CONOCIMIENTO.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "OK", "borradas": 0, "quedan": 0}
    antes = len(d.get("reglas", []))
    d["reglas"] = [r for r in d.get("reglas", []) if f not in _norm(r.get("texto", ""))]
    tmp = CONOCIMIENTO.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONOCIMIENTO)
    return {"status": "OK", "borradas": antes - len(d["reglas"]),
            "quedan": len(d["reglas"])}


def aprender(texto: str) -> Dict[str, Any]:
    """Lo que él pegó, entendido y guardado. La puerta de entrada."""
    e = extraer(texto)
    if not e["datos"] and not e["reglas"]:
        return {"status": "NADA",
                "detalle": "No saqué ningún dato ni regla de eso."}
    rd = guardar_datos(e["datos"])
    if rd.get("status") != "OK":
        return {"status": "ERROR", "detalle": rd.get("detalle")}
    rr = guardar_reglas(e["reglas"])
    return {"status": "OK",
            "datos": rd["detalle"],
            "reglas_nuevas": rr["nuevas"],
            "reglas_total": rr["guardadas"],
            "trozos": e["trozos"]}
