# -*- coding: utf-8 -*-
"""AURORA · LA LISTA MAESTRA: todo lo que el taller puede hacer, en un solo lado.

Anuar la pidió el 2026-08-09 con una idea que vale más que un catálogo:

    *«así me entero de todo lo que no estoy creando con el taller, qué sí hago
    y qué no»*

Por eso la lista es LARGA A PROPÓSITO. No es el inventario de lo que vende hoy
—eso ya lo tenía—, es el mapa de lo que su máquina puede hacer. Los renglones
vacíos no son huecos: son las ventas que todavía no existen.

DOS COLUMNAS, COMO LAS PIDIÓ:
    compra  → lo que le cuesta. Toda su lista de materiales es precio de compra
              (él lo confirmó el 2026-08-09), así que a estos les toca el +20%.
    venta   → lo que cobra. Sale de su catálogo real donde exista.

LA REGLA QUE NO SE ROMPE: los NOMBRES los propone AURORA; los PRECIOS jamás.
Un renglón sin precio se queda vacío y se ve vacío. Un precio inventado en una
lista de 300 renglones es imposible de cachar después, y termina cotizado.

NO PISA LO QUE ÉL CAPTURE: al correr de nuevo solo agrega los renglones que
falten. Un precio ya guardado no se toca nunca.

Correr:
    python TALLER/catalogo_maestro.py            # crea o actualiza la lista
    python TALLER/catalogo_maestro.py --resumen  # qué hay y qué falta
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "CONFIG" / "catalogo_maestro.json"
CONFIG = RAIZ / "CONFIG"

# ── LO QUE CORTA EL LÁSER ────────────────────────────────────────────────
# Los espesores que Anuar confirmó tener el 2026-08-09 van marcados con
# tengo=True. El resto son los que su 1390 de 100W SÍ puede cortar y hoy no
# maneja: ahí está el mapa de lo que le falta explorar.
LASER_CORTE = [
    # (nombre, unidad, medida, tengo)
    ("MDF 2.7mm", "hoja", "122x244 cm", True),
    ("MDF 3mm", "hoja", "122x244 cm", True),
    ("MDF 5.5mm", "hoja", "122x244 cm", True),
    ("MDF 6mm", "hoja", "122x244 cm", True),
    ("MDF 9mm", "hoja", "122x244 cm", True),
    ("MDF 12mm", "hoja", "122x244 cm", False),
    ("Trovicel 3mm", "hoja", "122x244 cm", True),
    ("Trovicel 5mm", "hoja", "122x244 cm", True),
    ("Trovicel 1mm", "hoja", "122x244 cm", False),
    ("Trovicel 2mm", "hoja", "122x244 cm", False),
    ("Trovicel 8mm", "hoja", "122x244 cm", False),
    ("Acrílico 2mm", "hoja", "120x180 cm", True),
    ("Acrílico 3mm Color", "hoja", "120x180 cm", True),
    ("Acrílico 3mm Transparente", "hoja", "120x180 cm", True),
    ("Acrílico 6mm", "hoja", "120x180 cm", True),
    ("Acrílico 4mm", "hoja", "120x180 cm", False),
    ("Acrílico 5mm", "hoja", "120x180 cm", False),
    ("Acrílico espejo 3mm", "hoja", "120x180 cm", False),
    ("Acrílico fluorescente 3mm", "hoja", "120x180 cm", False),
    ("Multiplay 4mm", "hoja", "122x244 cm", True),
    ("Multiplay 6mm", "hoja", "122x244 cm", False),
    ("Triplay 3mm", "hoja", "122x244 cm", False),
    ("Madera natural (pino)", "tabla", None, False),
    ("Madera balsa 3mm", "hoja", None, False),
    ("Chapa de madera (veneer)", "hoja", None, False),
    ("Cartón corrugado", "pliego", None, False),
    ("Cartulina / opalina", "pliego", None, False),
    ("Foamboard / cartón pluma 5mm", "hoja", None, False),
    ("Fieltro", "metro", None, False),
    ("Cuero natural", "pieza", None, False),
    ("Vinipiel / cuero sintético", "metro", None, False),
    ("Corcho 2mm", "hoja", None, False),
    ("EVA / foamy", "pliego", None, False),
    ("Goma para sellos (laser rubber)", "hoja", None, True),
    ("Tela algodón", "metro", None, False),
    ("Mezclilla", "metro", None, False),
    ("Polipropileno 1mm", "hoja", None, False),
    ("PETG 1mm", "hoja", None, False),
    ("Papel / papel calca", "pliego", None, False),
]

# ⚠️ ESTOS NO SE CORTAN. No es una lista de precios: es una lista que protege
# la máquina. El PVC suelta cloro al quemarse —corroe la óptica, los rieles y
# los pulmones—. Vale más aquí que en la memoria de alguien.
NO_CORTAR = [
    ("PVC / vinil rígido", "suelta cloro: corroe la máquina y es tóxico"),
    ("Policarbonato / Lexan", "no corta, se quema y amarillea"),
    ("ABS", "se derrite y suelta cianuro"),
    ("Fibra de vidrio", "suelta partículas de vidrio y resina tóxica"),
    ("Teflón (PTFE)", "suelta gas fluorado, muy tóxico"),
    ("Vinil de recorte", "es PVC: va en la plotter, nunca en el láser"),
    ("Espuma de poliestireno (unicel)", "se enciende"),
]

# ── LO QUE GRABA EL LÁSER ────────────────────────────────────────────────
# Graba todo lo que corta, y además estos que NO corta.
LASER_GRABADO = [
    ("Vidrio (copa, tarro, botella)", "pieza", None, True),
    ("Cristal", "pieza", None, True),
    ("Espejo", "pieza", None, False),
    ("Cerámica / azulejo", "pieza", None, True),
    ("Piedra / mármol", "pieza", None, False),
    ("Pizarra", "pieza", None, False),
    ("Acero inoxidable (con spray marcador)", "pieza", None, True),
    ("Spray marcador para metal (CerMark/Thermark)", "bote", None, False),
    ("Aluminio anodizado", "pieza", None, False),
    ("Placa laminada de dos capas", "hoja", None, False),
    ("Termo de acero", "pieza", None, True),
    ("Cuero / vinipiel", "pieza", None, True),
    ("Coco / hueso / concha", "pieza", None, False),
    ("Corcho", "pieza", None, False),
    ("Mezclilla (efecto desgastado)", "prenda", None, False),
]

# ── ARTÍCULOS SUBLIMABLES ────────────────────────────────────────────────
SUBLIMABLES = [
    # tazas
    ("Taza blanca 11oz", "pieza", True),
    ("Taza blanca 15oz", "pieza", False),
    ("Taza interior de color 11oz", "pieza", False),
    ("Taza mágica 11oz", "pieza", True),
    ("Taza mágica 15oz", "pieza", True),
    ("Taza cónica / latte", "pieza", False),
    ("Taza de peltre", "pieza", False),
    ("Tarro cervecero sublimable", "pieza", False),
    # termos y vasos
    ("Termo skinny 20oz", "pieza", True),
    ("Termo 30oz", "pieza", False),
    ("Termo 40oz", "pieza", False),
    ("Botella deportiva sublimable", "pieza", False),
    ("Vaso frappé con popote", "pieza", False),
    ("Cilindro sublimable", "pieza", False),
    # textil
    ("Playera poliéster blanca", "pieza", True),
    ("Playera poliéster cuello V", "pieza", False),
    ("Playera poliéster niño", "pieza", False),
    ("Jersey deportivo", "pieza", False),
    ("Sudadera sublimable", "pieza", False),
    ("Gorra sublimable", "pieza", True),
    ("Calcetines sublimables", "par", False),
    ("Cubrebocas sublimable", "pieza", False),
    ("Bandana / pañoleta", "pieza", False),
    ("Mandil sublimable", "pieza", False),
    ("Boxer poliéster", "pieza", True),
    ("Pijama sublimable", "juego", False),
    # hogar
    ("Mousepad", "pieza", True),
    ("Mousepad XL / gamer", "pieza", False),
    ("Funda de cojín", "pieza", False),
    ("Rompecabezas A4", "pieza", True),
    ("Rompecabezas A3", "pieza", False),
    ("Rompecabezas corazón", "pieza", False),
    ("Azulejo 10x10", "pieza", True),
    ("Azulejo 15x15", "pieza", False),
    ("Azulejo 20x20", "pieza", False),
    ("Portarretrato de vidrio", "pieza", True),
    ("Plato sublimable", "pieza", False),
    ("Reloj de pared sublimable", "pieza", False),
    ("Imán de refrigerador", "pieza", False),
    ("Posavasos sublimable", "pieza", False),
    ("Tabla de picar sublimable", "pieza", False),
    # accesorios
    ("Llavero de acero sublimable", "pieza", True),
    ("Llavero MDF sublimable", "pieza", False),
    ("Llavero acrílico sublimable", "pieza", False),
    ("Medalla sublimable", "pieza", False),
    ("Placa de reconocimiento", "pieza", False),
    ("Pluma sublimable", "pieza", False),
    ("Funda de celular sublimable", "pieza", False),
    ("Tote bag sublimable", "pieza", False),
    ("Mochila sublimable", "pieza", False),
    ("Cartuchera / estuche", "pieza", False),
    ("Monedero sublimable", "pieza", False),
    ("Espejo de bolsillo", "pieza", False),
    ("Destapador sublimable", "pieza", False),
    # papelería
    ("Libreta sublimable", "pieza", False),
    ("Agenda sublimable", "pieza", False),
    ("Carpeta sublimable", "pieza", False),
    # insumos de sublimación
    ("Lámina de aluminio sublimable", "hoja", False),
    ("MDF sublimable", "hoja", False),
    ("Tela sublimable", "metro", False),
    ("Papel de sublimación", "hoja", False),
    ("Tinta de sublimación", "juego", False),
]

# ── IMPRESIÓN LÁSER (la impresora, no la cortadora) ──────────────────────
# Anuar: *«impresión láser no hay nada»*. Aquí empieza de cero.
IMPRESION_MATERIAL = [
    ("Opalina carta", "paquete", True),
    ("Opalina tabloide (maquilada)", "hoja", True),
    ("Tabloide (maquilado)", "hoja", True),
    ("Vinil inkjet (maquilado)", "hoja", True),
    ("Papel adhesivo carta", "paquete", False),
    ("Papel adhesivo tabloide", "hoja", False),
    ("Papel bond carta", "paquete", False),
    ("Papel couché", "paquete", False),
    ("Papel fotográfico", "paquete", False),
    ("Cartulina", "pliego", False),
    ("Acetato / transparencia", "hoja", False),
    ("Transfer láser para tela clara", "hoja", False),
    ("Transfer láser para tela oscura", "hoja", False),
    ("Etiquetas troqueladas", "hoja", False),
    ("Tóner (juego CMYK)", "juego", True),
]

IMPRESION_ARTICULO = [
    ("Tarjetas de presentación", "millar", False),
    ("Volantes", "millar", False),
    ("Stickers en hoja", "hoja", False),
    ("Etiquetas para producto", "hoja", False),
    ("Menú impreso", "pieza", False),
    ("Invitaciones", "pieza", False),
    ("Calcomanías", "hoja", False),
    ("Separadores de libro", "pieza", False),
    ("Tarjetas de lealtad", "millar", False),
    ("Kit escolar (paquete)", "juego", True),
    ("Portada / cuadernillo", "pieza", False),
]

# ── VINIL ────────────────────────────────────────────────────────────────
# Anuar el 2026-08-09: *«el vinil textil cuesta de 180 a 235, siendo el
# metalizado el más caro, y los tornasoles; por eso no se podría un solo
# precio»*. Por eso van separados por tipo: un promedio le cobraría de menos
# el metalizado y de más el blanco.
VINIL = [
    ("Vinil textil blanco", "metro", True),
    ("Vinil textil negro", "metro", True),
    ("Vinil textil de color", "metro", True),
    ("Vinil textil metálico dorado", "metro", True),
    ("Vinil textil metálico plata", "metro", False),
    ("Vinil textil tornasol", "metro", True),
    ("Vinil textil sublimable", "metro", True),
    ("Vinil textil tipo bordado (flock)", "metro", True),
    ("Vinil textil reflejante", "metro", False),
    ("Vinil textil glitter", "metro", False),
    ("Vinil de recorte adhesivo (color)", "metro", True),
    ("Vinil de recorte transparente", "metro", False),
    ("Vinil de recorte esmerilado", "metro", False),
    ("Vinil de recorte reflejante", "metro", False),
    ("Vinil bifaz", "metro", True),
    ("DTF", "metro", True),
    ("DTF UV", "metro", True),
]

# ── PRENDAS (para personalizar) ──────────────────────────────────────────
PRENDAS = [
    ("Playera cuello redondo", "pieza", True),
    ("Playera polo manga corta", "pieza", True),
    ("Playera cuello V", "pieza", False),
    ("Playera manga larga", "pieza", False),
    ("Playera de niño", "pieza", False),
    ("Sudadera con gorro", "pieza", False),
    ("Sudadera sin gorro", "pieza", False),
    ("Chamarra", "pieza", False),
    ("Camisa", "pieza", False),
    ("Chaleco", "pieza", False),
    ("Bata", "pieza", False),
    ("Mandil", "pieza", False),
    ("Gorra", "pieza", True),
    ("Pants", "pieza", False),
    ("Short", "pieza", False),
    ("Uniforme (juego)", "juego", False),
    ("Boxer", "pieza", True),
    ("Tote bag de manta", "pieza", False),
    ("Mochila", "pieza", False),
    ("Toalla", "pieza", False),
]


# LO ÚNICO QUE VENDE COMO MATERIAL. Anuar, 2026-08-09: *«no vendo materiales,
# solo DTF UV y DTF textil por metro»*. Los demás no son productos: son insumos
# que entran a un trabajo. Que su columna de venta esté vacía es CORRECTO, no
# un pendiente —sin esta lista, 176 renglones se verían como precios faltantes.
MATERIAL_QUE_SI_VENDE = {"dtf", "dtf_uv"}


def _slug(texto: str) -> str:
    fuera = "áéíóúüñÁÉÍÓÚÜÑ"
    dentro = "aeiouunAEIOUUN"
    t = texto.lower()
    for a, b in zip(fuera, dentro):
        t = t.replace(a, b.lower())
    return "".join(c if c.isalnum() else "_" for c in t).strip("_")


def _precios_que_ya_tiene() -> tuple:
    """Saca los precios REALES de los archivos de Anuar. Nada se inventa."""
    compra, venta = {}, {}

    p = CONFIG / "precios_base.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        # materiales del láser: son precio de COMPRA (él lo confirmó)
        for m in (d.get("laser", {}).get("materiales") or []):
            nom = m["nombre"].replace(" (Hoja)", "").strip()
            compra[_slug(nom)] = float(m["precio_hoja"])
        for k, v in (d.get("insumos_textil") or {}).items():
            compra[_slug(k.replace("_metro", "").replace("_", " "))] = float(v)

    p = CONFIG / "catalogo_servicios.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for it in (d.get("productos") or []):
            pr = it.get("precio") or (it.get("escalas") or [{}])[0].get("precio")
            if pr is not None:
                venta[_slug(it["nombre"])] = float(pr)
        for it in (d.get("prendas") or []):
            if it.get("precio") is not None:
                venta[_slug(it["nombre"])] = float(it["precio"])
        dtf = d.get("dtf") or {}
        if dtf.get("venta_metro"):
            venta["dtf"] = float(dtf["venta_metro"])

    return compra, venta


def construir() -> dict:
    """Arma la lista completa. Si ya existe, respeta lo capturado."""
    compra_previa, venta_previa = _precios_que_ya_tiene()

    anterior = {}
    if DESTINO.exists():
        viejo = json.loads(DESTINO.read_text(encoding="utf-8"))
        anterior = {r["id"]: r for r in viejo.get("renglones", [])}

    renglones = []
    vistos = set()

    def agregar(categoria, tipo, nombre, unidad, medida=None, tengo=None):
        ident = f"{categoria}__{_slug(nombre)}"
        if ident in vistos:
            return
        vistos.add(ident)
        previo = anterior.get(ident, {})
        # un material NO se vende, se transforma. Su columna de venta queda
        # vacía a propósito y así se marca, para que no parezca un pendiente.
        se_vende = (tipo != "material") or (_slug(nombre) in MATERIAL_QUE_SI_VENDE)
        r = {
            "id": ident,
            "categoria": categoria,
            "tipo": tipo,
            "nombre": nombre,
            "unidad": unidad,
            "medida": medida,
            # se respeta SIEMPRE lo que él haya capturado
            "compra": previo.get("compra", compra_previa.get(_slug(nombre))),
            "venta": previo.get("venta", venta_previa.get(_slug(nombre))),
            "se_vende_asi": previo.get("se_vende_asi", se_vende),
            "lo_manejo": previo.get("lo_manejo", tengo),
            "nota": previo.get("nota"),
        }
        if not r["se_vende_asi"]:
            r["venta"] = None       # no se vende: no hay precio de venta
        renglones.append(r)

    for nom, uni, med, tengo in LASER_CORTE:
        agregar("laser_corte", "material", nom, uni, med, tengo)
    for nom, uni, med, tengo in LASER_GRABADO:
        agregar("laser_grabado", "material", nom, uni, med, tengo)
    for nom, uni, tengo in SUBLIMABLES:
        agregar("sublimacion", "articulo", nom, uni, None, tengo)
    for nom, uni, tengo in IMPRESION_MATERIAL:
        agregar("impresion_laser", "material", nom, uni, None, tengo)
    for nom, uni, tengo in IMPRESION_ARTICULO:
        agregar("impresion_laser", "articulo", nom, uni, None, tengo)
    for nom, uni, tengo in VINIL:
        agregar("vinil", "material", nom, uni, None, tengo)
    for nom, uni, tengo in PRENDAS:
        agregar("prendas", "articulo", nom, uni, None, tengo)

    # los 65 productos que ya vende: entran con su precio de venta real
    p = CONFIG / "catalogo_servicios.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for it in (d.get("productos") or []):
            if "nimo" in it.get("nombre", ""):
                continue          # los mínimos no son artículos
            agregar("ya_lo_vendo", "articulo", it["nombre"], "pieza", None, True)

    # lo que él haya agregado a mano y no esté en las listas: no se pierde
    for ident, r in anterior.items():
        if ident not in vistos:
            renglones.append(r)

    return {
        "_nota": ("LA LISTA MAESTRA del taller. Anuar la pidió larga a propósito: "
                  "«así me entero de todo lo que no estoy creando con el taller». "
                  "Un renglón vacío no es un hueco: es una venta que no existe."),
        "_regla": ("Los NOMBRES los propone AURORA. Los PRECIOS jamás: solo los "
                   "reales de Anuar. Lo que está vacío se ve vacío."),
        "_columnas": {
            "compra": "lo que le cuesta (toda su lista de materiales es de compra)",
            "venta": "lo que cobra; sale de su catálogo real donde exista",
            "lo_manejo": "true = ya lo trabaja · false = su máquina puede y no lo hace",
        },
        "_no_cortar": [{"material": m, "por_que": p} for m, p in NO_CORTAR],
        "renglones": renglones,
    }


def resumen(d: dict) -> str:
    """Separa lo que DE VERDAD falta de lo que está vacío con razón.

    Un material sin precio de venta no es un pendiente: Anuar no vende
    materiales. Contarlo como hueco haría que el 73% de la lista se viera
    incompleta y nadie volvería a mirarla.
    """
    from collections import Counter
    rs_todos = d["renglones"]
    cats = Counter(r["categoria"] for r in rs_todos)
    t = ["LISTA MAESTRA — %d renglones\n" % len(rs_todos)]
    t.append("%-18s %6s %8s %9s %9s" %
             ("categoría", "total", "manejo", "s/compra", "s/venta"))
    for c in sorted(cats):
        rs = [r for r in rs_todos if r["categoria"] == c]
        t.append("%-18s %6d %8d %9d %9d" % (
            c, len(rs),
            sum(1 for r in rs if r.get("lo_manejo")),
            sum(1 for r in rs if r.get("lo_manejo") and r.get("compra") is None),
            sum(1 for r in rs if r.get("se_vende_asi") and r.get("venta") is None)))

    faltan_c = [r for r in rs_todos if r.get("lo_manejo") and r.get("compra") is None]
    faltan_v = [r for r in rs_todos if r.get("se_vende_asi") and r.get("venta") is None]
    t.append("\nLO QUE DE VERDAD FALTA (solo de lo que YA manejas):")
    t.append("  %3d sin precio de compra" % len(faltan_c))
    t.append("  %3d sin precio de venta" % len(faltan_v))
    t.append("\nY %d renglones que tu máquina puede hacer y hoy NO haces."
             % sum(1 for r in rs_todos if r.get("lo_manejo") is False))
    t.append("(los materiales sin precio de venta NO cuentan: no los vendes)")
    return "\n".join(t)


if __name__ == "__main__":
    d = construir()
    if "--resumen" not in sys.argv:
        DESTINO.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print("guardada en", DESTINO)
    print()
    print(resumen(d))
