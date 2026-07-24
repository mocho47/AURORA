# -*- coding: utf-8 -*-
"""
AURORA · CATÁLOGO COMPARTIBLE  (material de venta listo para mandar)

Arma un PDF profesional de Creaciones Milens con los productos y precios REALES
del catálogo (CONFIG/catalogo_servicios.json vía el cotizador de servicios),
agrupados por familia. Pensado para compartir por WhatsApp / Facebook / imprimir.

Sin simulación: lee los precios reales; si un producto no está, no aparece.
Usa PyMuPDF (fitz), ya instalado. Cero dependencias nuevas.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import importlib.util
import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
NEGOCIO = "Creaciones Milens"
WHATSAPP = "33 3238 6943"

# Paleta (marca)
AZUL = (0.0, 0.525, 0.945)      # #0086f1
VERDE = (0.13, 0.77, 0.37)      # #22c55e (precio)
OSCURO = (0.10, 0.12, 0.16)
GRIS = (0.45, 0.48, 0.53)
BLANCO = (1, 1, 1)

# Familias por palabra clave (orden = orden en el catálogo)
FAMILIAS = [
    ("Prendas y textil", ("playera", "polo", "boxer", "gorra", "dtf", "vinil textil")),
    ("Tazas y termos", ("taza", "termo")),
    ("Cajas y artículos MDF", ("caja", "mdf", "servilletero", "posavas", "porta menú",
                               "porta menu", "señalét", "senalet", "tabla")),
    ("Cristal grabado", ("copa", "caballito", "cenicero", "tarro", "set copa")),
    ("Sublimación", ("sublimad", "sublimable", "lámina", "lamina", "mouse pad",
                     "azulejo", "rompecabezas", "vidrio")),
    ("Grabados y personalización", ("grabado", "llavero", "sticker", "bolígrafo",
                                    "boligrafo", "sello", "agenda", "módulo", "modulo")),
    ("Vinil y recorte", ("vinil recorte", "mínimo cualquier trabajo de vinil", "vinil")),
]


def _cot():
    spec = importlib.util.spec_from_file_location(
        "cotizador_servicios", ROOT / "TALLER" / "cotizador_servicios.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _norm(s: str) -> str:
    import unicodedata as ud
    return "".join(c for c in ud.normalize("NFD", (s or "").lower()) if ud.category(c) != "Mn")


def _precio_txt(it: dict) -> tuple[str, str]:
    """Devuelve (precio_principal, nota_mayoreo)."""
    esc = it.get("escalas")
    if esc:
        uni = esc[0]["precio"]
        may = esc[-1]["precio"]
        nota = f"mayoreo desde ${may:g}" if len(esc) > 1 and may != uni else ""
        return f"${uni:g}", nota
    p = it.get("precio")
    return (f"${p:g}" if p is not None else "cotizar"), ""


def _agrupar(items: list) -> list:
    """Agrupa los items en familias por palabra clave (respeta el orden de FAMILIAS)."""
    usados = set()
    grupos = []
    for titulo, claves in FAMILIAS:
        bucket = []
        for i, it in enumerate(items):
            if i in usados:
                continue
            n = _norm(it.get("nombre", ""))
            if any(_norm(k) in n for k in claves):
                bucket.append(it); usados.add(i)
        if bucket:
            grupos.append((titulo, bucket))
    # lo que no cayó en ninguna familia
    resto = [it for i, it in enumerate(items) if i not in usados]
    if resto:
        grupos.append(("Otros productos", resto))
    return grupos


def generar_catalogo_pdf(salida: str = "") -> dict:
    """Genera el PDF del catálogo y devuelve la ruta + conteos."""
    items = _cot().catalogo_plano().get("items", [])
    if not items:
        return {"status": "error", "mensaje": "El catálogo está vacío."}
    grupos = _agrupar(items)

    doc = fitz.open()
    W, H = 595, 842               # A4 vertical (pt)
    MX, MY = 45, 55               # márgenes
    fecha = datetime.now().strftime("%d/%m/%Y")

    # ── PORTADA ──
    pg = doc.new_page(width=W, height=H)
    pg.draw_rect(fitz.Rect(0, 0, W, 300), color=None, fill=AZUL)
    pg.insert_text((MX, 140), NEGOCIO, fontsize=40, fontname="hebo", color=BLANCO)
    pg.insert_text((MX, 180), "Catálogo de productos y precios", fontsize=17,
                   fontname="helv", color=BLANCO)
    pg.insert_text((MX, 245), "Corte láser · Sublimación · Personalización",
                   fontsize=13, fontname="helv", color=BLANCO)
    pg.insert_text((MX, 400), "Pedidos y cotizaciones por WhatsApp:",
                   fontsize=14, fontname="helv", color=OSCURO)
    pg.insert_text((MX, 440), WHATSAPP, fontsize=30, fontname="hebo", color=VERDE)
    pg.insert_text((MX, 500), "Precios de venta en pesos (MXN). Sujetos a cambio.",
                   fontsize=10, fontname="helv", color=GRIS)
    pg.insert_text((MX, H - 50), f"Actualizado: {fecha}", fontsize=10,
                   fontname="helv", color=GRIS)

    # ── PÁGINAS DE CONTENIDO ──
    pg = doc.new_page(width=W, height=H)
    y = MY

    def _nueva_pagina():
        nonlocal pg, y
        pg = doc.new_page(width=W, height=H)
        y = MY

    for titulo, bucket in grupos:
        # ¿cabe el encabezado + al menos una fila?
        if y > H - 120:
            _nueva_pagina()
        # encabezado de familia
        pg.draw_rect(fitz.Rect(MX, y, W - MX, y + 26), color=None, fill=AZUL)
        pg.insert_text((MX + 10, y + 18), titulo, fontsize=13, fontname="hebo", color=BLANCO)
        y += 40
        for it in bucket:
            if y > H - 55:
                _nueva_pagina()
            nombre = it.get("nombre", "")
            precio, nota = _precio_txt(it)
            # nombre (recorta si muy largo)
            nom = nombre if len(nombre) <= 62 else nombre[:60] + "…"
            pg.insert_text((MX + 4, y), nom, fontsize=10.5, fontname="helv", color=OSCURO)
            # precio alineado a la derecha
            pw = fitz.get_text_length(precio, fontname="hebo", fontsize=12)
            pg.insert_text((W - MX - pw, y), precio, fontsize=12, fontname="hebo", color=VERDE)
            # nota de mayoreo debajo, en gris
            if nota:
                pg.insert_text((MX + 4, y + 12), nota, fontsize=8, fontname="helv", color=GRIS)
                y += 12
            y += 20
            pg.draw_line(fitz.Point(MX, y - 6), fitz.Point(W - MX, y - 6),
                         color=(0.9, 0.91, 0.93), width=0.5)
        y += 14

    # pie de página en todas
    total_pag = doc.page_count
    for i in range(1, total_pag):
        p = doc[i]
        p.insert_text((MX, H - 30), f"{NEGOCIO} · WhatsApp {WHATSAPP}",
                      fontsize=9, fontname="helv", color=GRIS)
        pw = fitz.get_text_length(f"Pág. {i}/{total_pag-1}", fontname="helv", fontsize=9)
        p.insert_text((W - MX - pw, H - 30), f"Pág. {i}/{total_pag-1}",
                      fontsize=9, fontname="helv", color=GRIS)

    if not salida:
        salida = str(ROOT / "UPLOADS" / "editor_out" / f"catalogo_milens_{datetime.now():%Y%m%d}.pdf")
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    doc.save(salida); doc.close()
    return {"status": "ok", "salida": salida, "productos": len(items),
            "familias": len(grupos), "paginas": total_pag}


if __name__ == "__main__":
    import json
    print(json.dumps(generar_catalogo_pdf(), ensure_ascii=False, indent=2))
