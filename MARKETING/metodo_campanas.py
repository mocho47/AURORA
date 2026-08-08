# -*- coding: utf-8 -*-
"""AURORA · CÓMO SE HACE UNA CAMPAÑA (no una campaña: el método)

Anuar lo pidió el 2026-08-06, y es la petición correcta: *"importantísimo es
que AURORA entienda cómo realizaste la campaña, pues tú ya no estarás y lo
requiero"*.

Aquí no vive la campaña escolar. Aquí vive **lo que se aprendió armándola**,
para que AURORA arme la siguiente sola — la de ATF, la de Navidad, la que
sea — y para que REVISE la que alguien escriba y le diga qué está mal.

Todo lo de este archivo salió de errores reales de una sola tarde. Los cuatro
graves los encontró Anuar leyendo, no la máquina.

Correr:
    python MARKETING/metodo_campanas.py --revisar "texto de la campaña"
    python MARKETING/metodo_campanas.py --anatomia
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


# ── LAS SIETE REGLAS, CADA UNA DE UN ERROR REAL ─────────────────────────
ANATOMIA = (
    ("Gancho de DOLOR, no de calendario",
     "«Ya viene el regreso a clases» es información: ella ya lo sabe. "
     "«¿Ya se vio marcando 40 lápices con plumón a las 11 de la noche?» es "
     "un gancho: le pone la escena. Primero el dolor, luego la oferta."),

    ("NUNCA prometer lo que no se entrega",
     "El borrador decía «nosotros se los damos listos» justo después de "
     "hablar de lápices: se entendía que Milen's entrega los útiles. Se "
     "venden las ETIQUETAS. Una clienta que llega esperando lápices y recibe "
     "calcomanías es un pleito y una clienta menos. Lo cachó Anuar."),

    ("Nada que hoy no se pueda cumplir",
     "Si falta el material, sale de la lista. Se ofreció una tabla enmicada "
     "creyendo que no había con qué laminarla. Prometer y no llegar cuesta "
     "más que los pesos que se dejan de vender."),

    ("Personajes con nombre, no categorías",
     "«Carritos» es una categoría. «Goku» es una obsesión. La mamá lee un "
     "nombre concreto y ve la cara de su hijo. Corrección de Anuar."),

    ("El teléfono del texto = el que manda el mensaje",
     "Salió desde un número y en el texto decía otro. La señora recibe de "
     "uno y le dan otro: eso en una promoción se lee a spam."),

    ("Un solo producto, un solo precio",
     "Los nombres para ropa valían $50 en un paquete y $60 en otro siendo lo "
     "mismo. Quien compara los dos lo nota y desconfía de todo."),

    ("Pedir el MÍNIMO al cerrar",
     "No pedir que decida, ni que escoja paquete, ni que pague. Pedir un "
     "dato: «mándeme el nombre de su niño y le paso una muestra». La muestra "
     "hace el resto del trabajo."),
)

# Lo que hace que un mensaje NO parezca envío masivo.
PERSONALIZACION = (
    "Saludarla por su nombre, bien escrito (revisar la base: había "
    "«Fernnanda» con dos enes, y es la primera palabra que lee).",
    "Si en la orden quedó apuntado el producto en vez del nombre "
    "—«servilleteros»— se saluda sin nombre. Nunca con el producto.",
    "Las MAYÚSCULAS de la base se arreglan: «ANA BELEN» gritado se ve a "
    "factura, no a mensaje de una persona.",
    "Si ya te compró, agradecerlo en la PRIMERA línea. Eso separa el "
    "mensaje de la publicidad.",
)

# El orden de trabajo. Saltarse un paso es lo que hace que salga mal.
PASOS = (
    "1. SACAR la lista de clientes REALES de la base, no inventarla.",
    "2. LIMPIAR nombres: erratas, mayúsculas, los que no son personas.",
    "3. ESCRIBIR con las siete reglas de arriba.",
    "4. COSTEAR: cuánto cuesta cada paquete y qué margen deja. Sin esto no "
    "se sabe si la campaña gana o pierde.",
    "5. VISTA PREVIA SIEMPRE. Se le enseña al dueño el texto exacto y la "
    "lista exacta antes de mandar un solo mensaje.",
    "6. ESPERAR SU OK con todas sus letras. Nunca enviar por iniciativa.",
    "7. ENVIAR con pausa entre mensajes (45 s) para no verse a robot.",
    "8. REPORTAR con NÚMEROS: cuántos salieron, cuántos fallaron y POR QUÉ.",
)


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def revisar(texto: str, telefono_remitente: str = "") -> dict:
    """Revisa un borrador de campaña contra las reglas y dice qué está mal.

    Esto es lo que de verdad hay que heredar: no la campaña escolar, sino la
    capacidad de mirar un borrador y ver los errores ANTES de que salga a 21
    personas. Cada aviso de aquí es un error que ya ocurrió.
    """
    t = (texto or "")
    b = t.lower()
    problemas, bien = [], []

    # 1. ¿Promete entregar el producto del cliente?
    promesas = ("se los damos", "se los entregamos listos", "le damos listos",
                "nosotros se los")
    if any(p in b for p in promesas):
        problemas.append(
            "PROMESA AMBIGUA: dice «se los damos» cerca del producto del "
            "cliente. Se puede entender que ustedes entregan los útiles. "
            "Aclarar QUÉ se entrega exactamente.")

    # 2. ¿El gancho es calendario en vez de dolor?
    if re.search(r"^[^\n]{0,120}(ya viene|se acerca|est[aá] por llegar)", b):
        problemas.append(
            "GANCHO DE CALENDARIO: abre informando una fecha que el cliente "
            "ya sabe. Abrir con el dolor concreto.")

    # 3. ¿El teléfono del texto es el que manda?
    tels = re.findall(r"\b(\d{10})\b", t)
    if telefono_remitente and tels:
        limpio = "".join(c for c in telefono_remitente if c.isdigit())[-10:]
        if limpio not in tels:
            problemas.append(
                f"TELÉFONO CRUZADO: el texto dice {tels[0]} pero el mensaje "
                f"sale desde {limpio}. Se lee a spam.")

    # 4. ¿El mismo concepto con dos precios?
    precios = re.findall(r"\$\s?(\d{2,5})", t)
    if len(precios) != len(set(precios)) and len(precios) > 2:
        bien.append("Hay precios repetidos: verificar que no sea el mismo "
                    "producto con dos valores distintos.")

    # 5. ¿Cierra pidiendo algo mínimo?
    if not re.search(r"m[aá]ndeme|d[ií]game|escr[ií]bame|mande el", b):
        problemas.append(
            "SIN CIERRE: no pide nada concreto. Pedir UN dato fácil "
            "(un nombre), no una decisión.")

    # 6. ¿Saluda por su nombre?
    if "hola" in b[:40] and not re.search(r"hola\s+[a-záéíóúñ]{3,}", b[:60]):
        problemas.append("SIN NOMBRE: saluda genérico. Se nota el envío masivo.")
    else:
        bien.append("Saluda por su nombre.")

    # 7. ¿Da una razón para actuar hoy?
    if re.search(r"al d[ií]a siguiente|hoy mismo|entrega|ma[ñn]ana", b):
        bien.append("Dice cuándo lo entrega: eso vende más que un descuento.")
    else:
        problemas.append("SIN TIEMPO DE ENTREGA: decir cuándo lo tiene.")

    return {"status": "OK" if not problemas else "REVISAR",
            "problemas": problemas, "bien": bien}


def _texto(r: dict) -> str:
    if r["status"] == "OK":
        s = "✅ La campaña pasa las revisiones.\n"
    else:
        s = f"⚠️ **{len(r['problemas'])} cosa(s) que corregir antes de mandar:**\n"
    for p in r["problemas"]:
        s += f"\n   • {p}"
    if r["bien"]:
        s += "\n\n_Lo que ya está bien:_"
        for b in r["bien"]:
            s += f"\n   ✓ {b}"
    return s


def anatomia() -> str:
    s = ["📐 **CÓMO SE ARMA UNA CAMPAÑA QUE VENDE**\n",
         "Cada regla salió de un error real, no de un manual.\n"]
    for n, (regla, porque) in enumerate(ANATOMIA, 1):
        s.append(f"**{n}. {regla}**")
        s.append(f"   _{porque}_\n")
    s.append("\n🙋 **Para que no parezca envío masivo:**")
    for p in PERSONALIZACION:
        s.append(f"   • {p}")
    s.append("\n📋 **El orden de trabajo:**")
    for p in PASOS:
        s.append(f"   {p}")
    return "\n".join(s)


def main() -> int:
    _consola_utf8()
    if "--anatomia" in sys.argv:
        print(anatomia())
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    print(_texto(revisar(args[0], args[1] if len(args) > 1 else "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
