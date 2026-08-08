# -*- coding: utf-8 -*-
"""AURORA · Los paquetes escolares que se le mandaron a las clientas

Esto existe por un riesgo real que Anuar señaló el 2026-08-06, cuando la
campaña ya estaba saliendo: **AURORA contesta sola el WhatsApp**. Si una
clienta acaba de leer «primaria $150» y le pregunta el precio, AURORA no puede
contestarle otra cosa — eso tumba la venta y la deja como mentirosa.

Los paquetes son de Rocío. Su estructura —separar preescolar de primaria— es
mejor que un paquete parejo: una mamá de preescolar no necesita tablas de
multiplicar y una de primaria necesita el doble de etiquetas.

Lo único que se emparejó fue el precio de los nombres para ropa: valían $50 en
preescolar y $60 en primaria siendo el mismo producto. Anuar lo dejó en **$55
para los dos**, y por eso cada paquete #1 vale su #2 más 55.
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

NOMBRES_ROPA = 55          # el mismo precio en los dos niveles

PAQUETES = {
    "preescolar_2": {
        "nombre": "Preescolar",
        "precio": 100,
        "lleva": ["30 etiquetas para colores y lápices",
                  "10 etiquetas para libros y cuadernos"],
    },
    "preescolar_1": {
        "nombre": "Preescolar con nombres para ropa",
        "precio": 155,
        "lleva": ["30 etiquetas para colores y lápices",
                  "10 etiquetas para libros y cuadernos",
                  "6 nombres para la ropa"],
    },
    "primaria_2": {
        "nombre": "Primaria",
        "precio": 150,
        "lleva": ["45 etiquetas para colores y lápices",
                  "30 etiquetas para cuadernos y libros",
                  "tabla de multiplicar enmicada"],
    },
    "primaria_1": {
        "nombre": "Primaria con nombres para ropa",
        "precio": 205,
        "lleva": ["45 etiquetas para colores y lápices",
                  "30 etiquetas para cuadernos y libros",
                  "tabla de multiplicar enmicada",
                  "6 nombres para la ropa"],
    },
}

# Van INCLUIDAS y se dicen como regalo. Su costo ya está repartido en el
# precio, pero para la clienta son un detalle, no un renglón de la lista.
PILON = {"preescolar": 6, "primaria": 8}

ENTREGA = "al día siguiente"


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def responder(pregunta: str = "") -> str:
    """Lo que AURORA le contesta a una clienta que pregunta por los paquetes.

    Se responde con los CUATRO precios aunque pregunte por uno: la mamá que
    pregunta por preescolar muchas veces tiene también uno en primaria, y
    decírselo de una vez ahorra un mensaje y sube el pedido.
    """
    p = (pregunta or "").lower()

    lineas = ["Con mucho gusto 🙏 Estos son los paquetes de regreso a clases:\n"]
    for clave in ("preescolar_2", "preescolar_1", "primaria_2", "primaria_1"):
        q = PAQUETES[clave]
        lineas.append(f"*${q['precio']}* — {q['nombre']}")
        lineas.append("   " + " · ".join(q["lleva"]))
    lineas.append(f"\n🎁 Y de pilón las grandotas de 5×5 — "
                  f"{PILON['preescolar']} en preescolar y {PILON['primaria']} "
                  f"en primaria — para la lonchera, el termo y la mochila.")
    lineas.append(f"\n⚡ Se lo entregamos {ENTREGA}.")
    lineas.append("\nTodas van ya cortadas, solo se pegan, y se las hacemos "
                  "con el personaje favorito de su niño.")
    lineas.append("\n¿Me dice el *nombre de su niño* y de qué grado va? "
                  "Le paso una muestra de cómo quedaría.")
    return "\n".join(lineas)


def main() -> int:
    _consola_utf8()
    print(responder(" ".join(sys.argv[1:])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
