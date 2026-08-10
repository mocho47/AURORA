# -*- coding: utf-8 -*-
"""AURORA · La lista maestra, en papel.

Anuar la pidió para imprimir el 2026-08-09. Va pensada para llenarse A MANO
en el taller —con el material enfrente, que es donde de verdad se acuerda uno
de lo que cuesta— y luego capturarla.

Por eso:
  · fondo blanco y tinta negra (el panel es oscuro; imprimirlo así se come
    un cartucho y no se lee)
  · renglón alto, para escribir encima con pluma
  · lo que YA tiene, impreso; lo que falta, una raya para llenar
  · cada categoría empieza en hoja nueva, para repartir las hojas por área
  · el encabezado se repite en cada página: sin eso, a la tercera hoja ya no
    se sabe qué columna es cuál

Correr:
    python TALLER/catalogo_imprimir.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "CONFIG" / "catalogo_maestro.json"
SALIDA = Path.home() / "Downloads" / "LISTA_MAESTRA_MILENS.html"

TITULOS = {
    "laser_corte": ("Materiales que CORTA el láser", "compra"),
    "laser_grabado": ("Materiales que GRABA el láser", "compra"),
    "vinil": ("Vinil y transfer", "ambas"),
    "sublimacion": ("Artículos sublimables", "ambas"),
    "impresion_laser": ("Impresión láser", "ambas"),
    "prendas": ("Prendas para personalizar", "ambas"),
    "ya_lo_vendo": ("Lo que YA vendes — falta saber qué te cuesta", "ambas"),
}

ORDEN = ["ya_lo_vendo", "laser_corte", "laser_grabado", "vinil",
         "sublimacion", "impresion_laser", "prendas"]

CSS = """
@page { size: letter; margin: 12mm 10mm; }
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; color: #000; background: #fff;
       margin: 0; font-size: 10pt; }
h1 { font-size: 16pt; margin: 0 0 2mm; }
h2 { font-size: 12pt; margin: 0 0 1mm; padding: 2mm 0 1mm;
     border-bottom: 2px solid #000; }
.sub { font-size: 8.5pt; color: #444; margin: 0 0 3mm; }
.cat { page-break-before: always; }
.cat:first-of-type { page-break-before: avoid; }
table { width: 100%; border-collapse: collapse; }
thead { display: table-header-group; }          /* se repite en cada hoja */
tr { page-break-inside: avoid; }
th { font-size: 8pt; text-transform: uppercase; letter-spacing: .4px;
     text-align: left; border-bottom: 1.5px solid #000; padding: 1.5mm 1mm; }
td { padding: 2.2mm 1mm; border-bottom: .4pt solid #bbb; vertical-align: middle; }
tr:nth-child(even) td { background: #f4f4f4; }
.num { text-align: right; white-space: nowrap; width: 22mm; }
.uni { color: #555; font-size: 8.5pt; width: 20mm; }
.chk { width: 10mm; text-align: center; }
.caja { display: inline-block; width: 4mm; height: 4mm; border: 1pt solid #000; }
.caja.on { background: #000; }
.raya { display: inline-block; width: 19mm; border-bottom: .6pt solid #666; }
.tiene { font-weight: bold; }
.nov { color: #888; font-size: 8pt; }
.aviso { border: 1.5pt solid #000; padding: 3mm; margin: 4mm 0; font-size: 9pt; }
.aviso b { display: block; margin-bottom: 1.5mm; }
.pie { margin-top: 3mm; font-size: 8pt; color: #555; }
@media print { .noimp { display: none; } }
"""


def _fila(r: dict) -> str:
    def celda(v):
        return (f'<span class="tiene">${v:,.2f}</span>' if v is not None
                else '<span class="raya"></span>')
    venta = ('<span class="nov">no se vende</span>'
             if not r.get("se_vende_asi") else celda(r.get("venta")))
    med = f' <span class="uni">{r["medida"]}</span>' if r.get("medida") else ""
    chk = "on" if r.get("lo_manejo") else ""
    return (f'<tr><td class="chk"><span class="caja {chk}"></span></td>'
            f'<td>{r["nombre"]}{med}</td>'
            f'<td class="uni">{r.get("unidad") or ""}</td>'
            f'<td class="num">{celda(r.get("compra"))}</td>'
            f'<td class="num">{venta}</td></tr>')


def generar() -> Path:
    d = json.loads(ORIGEN.read_text(encoding="utf-8"))
    rs = d["renglones"]

    p = [f'<style>{CSS}</style>',
         '<h1>Lista maestra · Creaciones Milens</h1>',
         '<p class="sub">Marca la casilla de lo que manejas. Escribe el precio '
         'donde haya raya. Lo que ya está impreso es lo que AURORA tiene '
         'guardado — si está mal, táchalo y corrígelo.</p>']

    faltan_c = sum(1 for r in rs if r.get("lo_manejo") and r.get("compra") is None)
    hoy_no = sum(1 for r in rs if r.get("lo_manejo") is False)
    p.append(f'<div class="aviso"><b>{len(rs)} renglones · '
             f'{faltan_c} sin precio de compra · '
             f'{hoy_no} cosas que tu máquina puede hacer y hoy no haces</b>'
             'Los materiales no llevan precio de venta: no los vendes, los '
             'transformas. Las únicas excepciones son DTF y DTF UV, que sí '
             'vendes por metro.</div>')

    for cat in ORDEN:
        filas = [r for r in rs if r["categoria"] == cat]
        if not filas:
            continue
        titulo, _ = TITULOS.get(cat, (cat, "ambas"))
        marcados = sum(1 for r in filas if r.get("lo_manejo"))
        p.append(f'<div class="cat"><h2>{titulo}</h2>'
                 f'<p class="sub">{len(filas)} renglones · '
                 f'{marcados} los manejas hoy</p>'
                 '<table><thead><tr>'
                 '<th class="chk">¿Lo<br>hago?</th><th>Nombre</th>'
                 '<th>Unidad</th><th class="num">Compra $</th>'
                 '<th class="num">Venta $</th></tr></thead><tbody>')
        for r in sorted(filas, key=lambda x: (not x.get("lo_manejo"), x["nombre"])):
            p.append(_fila(r))
        p.append('</tbody></table></div>')

    # la lista que protege la máquina va hasta el final, en su propia hoja
    p.append('<div class="cat"><h2>NUNCA meter esto al láser</h2>'
             '<p class="sub">No es una lista de precios: protege la máquina '
             'y a quien la opera.</p><table><thead><tr>'
             '<th>Material</th><th>Por qué</th></tr></thead><tbody>')
    for it in d.get("_no_cortar", []):
        p.append(f'<tr><td><b>{it["material"]}</b></td>'
                 f'<td>{it["por_que"]}</td></tr>')
    p.append('</tbody></table></div>')

    p.append('<p class="pie">AURORA · generado el 2026-08-09 · '
             'los nombres los propuso AURORA, los precios son de Anuar</p>')

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(p), encoding="utf-8")
    return SALIDA


if __name__ == "__main__":
    ruta = generar()
    kb = ruta.stat().st_size / 1024
    print("Lista para imprimir:")
    print("   %s   (%.0f KB)" % (ruta, kb))
    print()
    print("Abrela y dale Ctrl+P. Sale en blanco y negro, renglon alto para")
    print("escribir con pluma, y cada categoria en su propia hoja.")
