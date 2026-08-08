# -*- coding: utf-8 -*-
"""AURORA · PRINT & CUT completo: de la impresión al corte

Todo esto lo aprendió Anuar a mano el 2026-08-07, equivocándose paso por paso
con las calcomanías de Luisa. Sus palabras al terminar: *"tuve que hacer todo
manual para aprender, valió la pena el tiempo y dolor de cabeza"*.

Queda aquí para que nadie —ni él, ni Rocío, ni un cliente de AURORA— vuelva a
pagar ese aprendizaje. Cada advertencia de este archivo es un error que de
verdad ocurrió y costó una hoja, una impresión o una tarde.

Correr:  python TALLER/print_and_cut.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


# ── EL PROCESO, PASO POR PASO ───────────────────────────────────────────
PASOS = (
    ("1 · DISEÑO", (
        "Página **A4 real: 210 × 297**. Nada de sangrado.",
        "En Corel: *Diseño → Configuración de página → Sangrado = 0*.",
        "Al publicar el PDF, en **Preimpresión** apagar las tres: "
        "*Límite de sangrado*, *Marcas de recorte* y *Marcas de registro*.",
        "⚠️ Las marcas de Corel son de imprenta —cruces para alinear planchas "
        "de offset— y **la Cameo no las lee**. Se comprobó en la máquina: "
        "«no registraba». No hay tamaño de página que las haga coincidir.",
        "El dibujo va dentro del **área útil**: de X 23 a 172, de Y 23 a 259. "
        "Fuera de ahí lo tapan las marcas.",
    )),
    ("2 · MARCAS DE REGISTRO", (
        "Se ponen **en Silhouette Studio**, nunca en Corel.",
        "*Panel de Configuración de página → pestaña de marcas → Tipo 1*.",
        "Quedan a **15.6 mm de cada orilla**: cuadro relleno de 5.5 mm arriba "
        "a la izquierda, y dos escuadras en L de 20.2 mm (arriba-derecha y "
        "abajo-izquierda). La cuarta esquina va vacía **a propósito**: así la "
        "máquina sabe cómo está orientada la hoja.",
        "Ninguna figura puede invadir esas zonas ni pegarse a ellas.",
    )),
    ("3 · IMPRESIÓN", (
        "Imprimir **desde Silhouette Studio**, para que las marcas salgan "
        "exactamente donde la máquina las busca.",
        "⚠️ **AL 100%, SIN AJUSTAR A PÁGINA.** Es lo único que puede echarlo "
        "todo a perder: si la papelería escala, las marcas se recorren y ya no "
        "registra — con la impresión pagada.",
        "Decírselo así: *«al 100%, tamaño real, sin ajustar a página»*.",
        "**El seguro:** meter un cuadro de 10 × 10 cm en una esquina libre. "
        "Al recibir la hoja se mide: si da 10, imprimió bien. Si da 9.5, la "
        "escalaron y no vale la pena ni intentar cortar.",
        "El vinil de inyección **NO va en impresora láser**: el tóner no se "
        "agarra y se despinta, y el vinil se puede derretir en el fusor.",
    )),
    ("4 · TRAZAR EL CONTORNO", (
        "La imagen es un dibujo, no una línea de corte. Hay que trazarla.",
        "*Panel de Trazo* → seleccionar el área → subir el umbral hasta que la "
        "figura quede bien cubierta → **Trazar contorno exterior**.",
    )),
    ("5 · EL EXCEDENTE (lo que salva el trabajo)", (
        "El corte NO va justo en la orilla del dibujo: va un poco por fuera. "
        "Así un desfase de un milímetro no deja el filito blanco.",
        "*Panel de Desplazamiento* → **Desplazamiento** (hacia afuera, no "
        "interno) → **1.0 mm** → Aplicar.",
        "En *Esquina* poner **redondeada**: en punta deja picos raros.",
        "⚠️ **Borrar el trazo de adentro**, o corta dos veces cada pieza.",
        "Cuánto excedente cabe: la mitad del hueco entre piezas. Con 4.6 mm de "
        "separación, 1 mm por lado deja 2.6 mm entre corte y corte.",
    )),
    ("6 · CORTE", (
        "*Medios*: el tamaño real de la hoja impresa.",
        "Si la hoja trae sangrado de Corel: **242 × 333, sin tapete** — así lo "
        "ajustó Anuar y así coinciden.",
        "Hoja limpia sin sangrado: **210 × 297**.",
        "El vinil necesita **tapete**: no tiene respaldo rígido que la máquina "
        "jale sola. Pegarlo alineado a la **esquina superior izquierda**.",
        "Mandar a leer las marcas. **Si el sensor no las encuentra, la máquina "
        "NO corta** — se detiene y avisa. Probar es gratis.",
    )),
    ("7 · SIN REGISTRO (hojas ya impresas)", (
        "Cuando la hoja ya salió con marcas de Corel, se corta a mano.",
        "Se alinea la hoja pegada a la esquina del tapete y se colocan los "
        "contornos en coordenadas medidas del archivo.",
        "⚠️ **Cortar la primera en la hoja que peor haya salido.** Sin sensor "
        "la máquina no corrige nada: lo que salga en esa, sale en todas.",
    )),
)

# Lo que cuesta el registro, en material. Con marcas caben MENOS piezas, y
# ese dato cambia el precio: se costeó la campaña escolar a 30 etiquetas por
# hoja y con marcas caben 14. La etiqueta pasó de $0.26 a $0.56.
RENDIMIENTO = (
    ("etiquetas 2.7 × 6 cm", 28, 14),
    ("etiquetas 4 × 9 cm", 12, 7),
    ("etiquetas 5 × 5 cm", 20, 8),
)


def manual() -> str:
    s = ["🖨️✂️ **PRINT & CUT — de la impresión al corte**\n",
         "_Cada advertencia aquí es un error que ya ocurrió y costó material._\n"]
    for titulo, puntos in PASOS:
        s.append(f"\n**{titulo}**")
        for p in puntos:
            s.append(f"   • {p}")
    s.append("\n\n📉 **Lo que cuestan las marcas, en piezas por hoja:**\n")
    s.append(f"   {'':22} {'sin marcas':>11} {'con marcas':>11}")
    for nom, sin, con in RENDIMIENTO:
        s.append(f"   {nom:22} {sin:>11} {con:>11}")
    s.append("\n   _Costear sobre la hoja completa y luego descubrir que no "
             "cabe es perder la impresión. El registro se paga en material._")
    return "\n".join(s)


def main() -> int:
    _consola_utf8()
    print(manual())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
