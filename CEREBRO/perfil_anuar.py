# -*- coding: utf-8 -*-
"""AURORA · Cómo habla Anuar — cargado de una vez, no aprendido a golpes

Anuar lo dijo el 2026-08-05: *"¿por qué no has enseñado a AURORA a entenderme,
si tú puedes mostrarle cómo lo haría yo?"*. Tenía razón: yo venía agregando sus
frases de tres en tres cada vez que un bug las delataba, cuando podía volcar su
forma de hablar completa de una vez.

Esto NO son frases inventadas. Se extrajeron **72 peticiones reales suyas** del
historial de conversaciones, y de ahí salieron los patrones de abajo.

Lo que se ve en sus mensajes reales:
  • Escribe rápido y sin corregir: "imprecion", "watsapp", "coreldrau",
    "adesivo", "cotiz", "dijitalizar", "creeo", "ovio", "combiene"
  • Dobla letras al teclear: "pprecione", "impprecion", "hechoo", "celullar"
  • Pregunta el precio con "a cuánto" / "cuánto sale" / "cuánto costaría",
    casi nunca con "cuál es el precio"
  • Da las medidas primero y el producto después:
    "10 nombres de vinil de 25x6 cm", "una caja de 40x40 con 1 division"
  • Usa "provemos", "hagamos", "saca", "dale", "va" para arrancar algo
  • Cierra con "listo", "ok", "va", "dale"

Este módulo NO enruta: solo NORMALIZA el texto antes de que los candados lo
vean. Así una falta de dedo deja de romper el reconocimiento.
"""
from __future__ import annotations
import re

# Cómo escribe Anuar → cómo lo esperan los candados. Cada línea salió de un
# mensaje REAL suyo, no de suponer cómo escribiría.
ERRORES_REALES = {
    # Programas y herramientas
    "coreldrau": "corel", "coreldraw": "corel", "corell": "corel",
    "watsapp": "whatsapp", "watsap": "whatsapp", "wats": "whatsapp",
    "whats": "whatsapp", "wasap": "whatsapp",
    "chrimeboock": "chromebook", "chrome boock": "chromebook",
    "asppire": "aspire", "drw": "rdworks", "meracdo": "mercado",
    # Sitios que escribe rápido. "facebok" con una K le tumbó la búsqueda
    # entera el 2026-08-05.
    "facebok": "facebook", "feisbuk": "facebook", "fb": "facebook",
    "pinterets": "pinterest", "pintrest": "pinterest", "pinteres": "pinterest",
    "yotube": "youtube", "yutub": "youtube", "youtub": "youtube",
    "mercadolibre": "mercado libre", "meli": "mercado libre",
    "instagran": "instagram", "insta": "instagram",
    "3 axis": "3axis", "tresaxis": "3axis", "3axis co": "3axis",
    # "dxf download" en DOS palabras se lo llevaba el conversor de DXF, porque
    # la frase trae "dxf" (2026-08-05). Se junta antes de que nadie la vea.
    "dxf download": "dxfdownloads", "dxf downloads": "dxfdownloads",
    "dxfdownload": "dxfdownloads", "dxf-downloads": "dxfdownloads",
    "dxf for cnc": "dxfforcnc", "dxfforcnc com": "dxfforcnc",
    # Del taller
    "imprecion": "impresion", "impprecion": "impresion",
    "imprecione": "impresion", "impreciones": "impresiones",
    "adesivo": "adhesivo", "adesivos": "adhesivos",
    "laminadoora": "laminadora", "divicion": "division",
    "diviciones": "divisiones", "entrepaños": "entrepanos",
    "suaje": "suajado", "vinill": "vinil",
    "estikers": "stickers", "stikers": "stickers",
    "planillas": "planilla", "tabloyde": "tabloide",
    # Palabras de todos los días
    "creeo": "creo", "ovio": "obvio", "combiene": "conviene",
    "hechoo": "hecho", "celullar": "celular", "provemos": "probemos",
    "requero": "requiero", "requiro": "requiero",
    "dijitalizar": "digitalizar", "dijital": "digital",
    "aser": "hacer", "acemos": "hacemos", "haser": "hacer",
    "porfa": "por favor", "porfavor": "por favor",
    "pprecione": "presione", "precione": "presione",
    "livertad": "libertad", "exprecion": "expresion",
    "cotisar": "cotizar", "cotiza r": "cotizar",
    "invercion": "inversion", "invertion": "inversion",
    "comitea": "commit", "comitealo": "commit",
    "reinicia": "reiniciar", "cerar": "cerrar",
}

# Cómo pide las cosas Anuar → la forma que los candados sí reconocen.
# Se aplica sobre la frase completa, no palabra por palabra.
# EL ORDEN IMPORTA: las frases COMPLETAS van primero. Si no, dos reglas se
# pisan y cambian el sentido — "sácale el dibujo lineal" salía como "extrae el
# vectorizar", que ya no es español ni es lo que se pidió (2026-08-05).
MODISMOS = (
    # ── Frases completas del taller: se traducen enteras ──────────────
    (r"\bsaca(?:le|me)?\s+el\s+dibujo\s+lineal\b", "vectoriza"),
    (r"\bdibujo\s+lineal\b", "vectoriza"),
    (r"\bpasa(?:lo|la)?\s+a\s+corte\b", "convierte a dxf"),
    (r"\bpasar\s+a\s+corte\b", "convertir a dxf"),
    (r"\bdeja(?:lo|la)?\s+listo\s+para\s+(?:la\s+)?laser\b", "convierte a dxf"),
    (r"\bcorte\s+de\s+caja\b", "contabilidad"),
    (r"\bcuanto\s+cayo\b", "cuanto vendi"),
    (r"\bmapa\s+de\s+bits\b", "bitmap"),

    # ── Precio: casi siempre pregunta con "a cuánto" o "cuánto sale" ──
    (r"\ba cuanto (?:me )?(?:sale|queda|lo dan|cobro|cuesta)\b", "cuanto cuesta"),
    (r"\bcuanto (?:me )?(?:saldria|costaria|quedaria)\b", "cuanto cuesta"),
    (r"\bcual seria mi costo\b", "cuanto cuesta"),
    (r"\ben cuanto (?:sale|queda)\b", "cuanto cuesta"),

    # ── Verbo con el pronombre PEGADO: así escribe Anuar ──────────────
    # "ábreme", "guárdalo", "conviértelo". Los candados esperan el verbo solo,
    # así que "abreme coreldrau porfa" no calzaba con "abre" (2026-08-05).
    # Se arregla aquí y no en cada candado: el patrón es de TODOS.
    (r"\babre(?:me|lo|la|los|las)\b", "abre"),
    (r"\bcierra(?:lo|la|los|las)\b", "cierra"),
    (r"\bguarda(?:me|lo|la|los|las)\b", "guarda"),
    (r"\bconvierte(?:lo|la|los|las)\b", "convierte"),
    (r"\bexporta(?:lo|la|los|las)\b", "exporta"),
    (r"\bvectoriza(?:lo|la|los|las)\b", "vectoriza"),
    (r"\bimprime(?:lo|la|los|las)\b", "imprime"),
    (r"\bpublica(?:lo|la|los|las)\b", "publica"),
    (r"\bcotiza(?:me|lo|la)\b", "cotiza"),
    (r"\bbusca(?:me|lo|la)\b", "busca"),

    # ── Verbos sueltos: van AL FINAL, para no pisar las frases de arriba ──
    (r"\b(?:sacame|sacale|sacalo)\b", "extrae"),
    (r"\b(?:chekame|checame|chekalo|checalo|checa)\b", "revisa"),
    (r"\b(?:hagamos|hagamoos|provemos|probemos)\b", "haz"),
    (r"\b(?:mandale|mandalo|mandala)\b", "envia"),
    (r"\b(?:ensename|muestrame)\b", "dame"),
)


def normaliza(mensaje: str) -> str:
    """Deja el mensaje como los candados lo esperan, sin cambiar la intención.

    NO adivina ni completa: solo corrige lo que ya se sabe que Anuar escribe
    distinto. Si no reconoce nada, devuelve el mensaje tal cual.
    """
    if not mensaje:
        return mensaje
    t = mensaje

    # 1) Errores de dedo, palabra completa (para no romper otras palabras)
    for malo, bueno in ERRORES_REALES.items():
        t = re.sub(rf"\b{re.escape(malo)}\b", bueno, t, flags=re.IGNORECASE)

    # 2) Letras dobladas al teclear rápido: "pprecione", "hechoo", "aurora"
    #    Solo al inicio de palabra y solo consonantes: "llamar" y "carro" no se tocan.
    t = re.sub(r"\b([bcdfgjkmpqtvxyz])\1+", r"\1", t, flags=re.IGNORECASE)

    # 3) Su forma de pedir las cosas
    for patron, estandar in MODISMOS:
        t = re.sub(patron, estandar, t, flags=re.IGNORECASE)

    return " ".join(t.split())


def explica(mensaje: str) -> dict:
    """Qué se le cambió y por qué. Para poder revisar que no invente."""
    limpio = normaliza(mensaje)
    return {"original": mensaje, "normalizado": limpio,
            "cambio": limpio.lower() != (mensaje or "").lower()}


if __name__ == "__main__":
    import io
    import sys
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    # Frases REALES suyas, sacadas del historial.
    for f in ("aurora en corel abreme el diseno",
              "motor corel pregunte corel tiene instalado el plugin laser",
              "a cuanto tienes el costo del vinil textil",
              "10 nombrembres de vinil de 25x6 cm cual seria mi costo",
              "chekame el diseno abierto",
              "sacale el dibujo lineal",
              "pasalo a corte",
              "mandale un wats al cliente",
              "combiene mas maquilar en tabloide que hechoo en casa ?",
              "que decia imprecion inkjet y laser la publicasion",
              "hagamoos watsapp"):
        r = explica(f)
        marca = "→" if r["cambio"] else " ="
        print(f"  «{f[:52]:54}» {marca} «{r['normalizado'][:52]}»")
