# -*- coding: utf-8 -*-
"""AURORA · Directorio de proveedores, indexado por artículo

Anuar lo pidió el 2026-08-04, y ese mismo día lo sufrió: no sabía a quién
cotizarle el papel adhesivo ni el vinil, y terminó pidiéndole a AURORA que
buscara en MercadoLibre porque no tenía dónde consultarlo.

La pregunta que resuelve es "¿quién me vende X y a cuánto?". Si el proveedor
está aquí, se contesta al instante con datos REALES. Si no está, se dice que no
se tiene y se ofrece buscarlo en internet — nunca se inventa un proveedor ni un
teléfono.

Cada precio trae la fecha en que se supo: un precio de hace un año no es un
precio, es una referencia vieja, y eso hay que decirlo.

Correr:  python TALLER/proveedores.py                 lista todo
         python TALLER/proveedores.py vinil           busca por artículo
"""
from __future__ import annotations
import io
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ARCHIVO = RAIZ / "CONFIG" / "proveedores.json"

# Arranque con lo VERIFICADO el 2026-08-04. Los teléfonos van vacíos a
# propósito: no se inventan. Anuar los llena conforme cotice.
_SEMILLA = {
    "nota": ("Proveedores reales de Anuar, indexados por artículo. Los precios "
             "traen la fecha en que se supieron. Sin teléfono = todavía no se "
             "ha confirmado; NO se inventan datos de contacto."),
    "proveedores": [
        {
            "nombre": "Lideart",
            "tipo": "tienda en línea",
            "web": "lideart.com.mx",
            "telefono": "",
            "zona": "envía a todo México",
            "articulos": ["vinil textil", "vinil", "forever", "laser-dark",
                          "multi-trans", "silhouette", "cameo", "tapete",
                          "papel transfer", "foil textil"],
            "precios": [
                {"articulo": "vinil textil 60 cm", "precio": 180.0,
                 "unidad": "metro", "fecha": "2026-08-04",
                 "nota": "precio real confirmado por Anuar"},
            ],
        },
        {
            "nombre": "MercadoLibre",
            "tipo": "marketplace",
            "web": "mercadolibre.com.mx",
            "telefono": "",
            "zona": "envío a domicilio",
            "articulos": ["papel adhesivo", "adhesivo", "etiquetas",
                          "papel", "micas", "insumos"],
            "precios": [
                {"articulo": "papel adhesivo carta láser/inkjet", "precio": 2.50,
                 "unidad": "hoja (paquete de 100 = $250)", "fecha": "2026-08-04",
                 "nota": "debe decir 'para láser'; el de solo inyección daña el fusor"},
            ],
        },
        {
            "nombre": "Maderería local",
            "tipo": "local",
            "web": "",
            "telefono": "",
            "zona": "Guadalajara",
            "articulos": ["mdf", "madera", "multiplay", "triplay"],
            "precios": [
                {"articulo": "MDF 2.7 mm (hoja 122x244)", "precio": 110.0,
                 "unidad": "hoja", "fecha": "2026-08-04"},
                {"articulo": "MDF 5.5 mm (hoja 122x244)", "precio": 280.0,
                 "unidad": "hoja", "fecha": "2026-08-04"},
                {"articulo": "Multiplay 4 mm (hoja 122x244)", "precio": 350.0,
                 "unidad": "hoja", "fecha": "2026-08-04"},
            ],
        },
        {
            "nombre": "Maquila de impresión",
            "tipo": "servicio",
            "web": "",
            "telefono": "",
            "zona": "Guadalajara",
            "articulos": ["impresion", "tabloide", "suaje", "suajado",
                          "impresion tabloide"],
            "precios": [
                {"articulo": "tabloide solo impreso", "precio": 10.0,
                 "unidad": "pieza", "fecha": "2026-08-04",
                 "nota": "Anuar suaja en su Cameo — es la opción que conviene"},
                {"articulo": "tabloide impreso y suajado", "precio": 45.0,
                 "unidad": "pieza", "fecha": "2026-08-04",
                 "nota": "los $35 de diferencia son mano de obra de corte"},
            ],
        },
    ],
}


def _leer() -> dict:
    if not ARCHIVO.exists():
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps(_SEMILLA, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        return dict(_SEMILLA)
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return dict(_SEMILLA)


def _guardar(d: dict) -> None:
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def buscar(articulo: str) -> dict:
    """¿Quién vende esto? Si no está, se DICE — no se inventa un proveedor."""
    q = (articulo or "").strip().lower()
    if not q:
        return {"status": "FALTA_DATO", "detalle": "Dime qué artículo buscas."}

    d = _leer()
    hallados = []
    for p in d.get("proveedores", []):
        calza_art = any(q in a.lower() or a.lower() in q for a in p.get("articulos", []))
        calza_precio = any(q in x.get("articulo", "").lower()
                           for x in p.get("precios", []))
        if calza_art or calza_precio:
            precios = [x for x in p.get("precios", [])
                       if q in x.get("articulo", "").lower()] or p.get("precios", [])
            hallados.append({**p, "precios": precios})

    if not hallados:
        return {"status": "NO_LO_TENGO", "buscado": articulo,
                "total_proveedores": len(d.get("proveedores", [])),
                "detalle": (f"No tengo ningún proveedor de '{articulo}' en el "
                            f"directorio (llevo {len(d.get('proveedores', []))}). "
                            "Puedo buscarlo en internet si quieres.")}
    return {"status": "OK", "buscado": articulo, "total": len(hallados),
            "proveedores": hallados}


def agregar(nombre: str, articulos: list, telefono: str = "", web: str = "",
            zona: str = "", tipo: str = "") -> dict:
    """Da de alta un proveedor. Los datos los pone Anuar, no se inventan."""
    if not nombre or not articulos:
        return {"status": "FALTA_DATO",
                "detalle": "Necesito al menos el nombre y qué vende."}
    d = _leer()
    for p in d.setdefault("proveedores", []):
        if p["nombre"].lower() == nombre.lower():
            p["articulos"] = sorted(set(p.get("articulos", []) + list(articulos)))
            p["telefono"] = telefono or p.get("telefono", "")
            p["web"] = web or p.get("web", "")
            _guardar(d)
            return {"status": "ACTUALIZADO", "proveedor": p}
    nuevo = {"nombre": nombre, "tipo": tipo or "proveedor", "web": web,
             "telefono": telefono, "zona": zona,
             "articulos": list(articulos), "precios": []}
    d["proveedores"].append(nuevo)
    _guardar(d)
    return {"status": "AGREGADO", "proveedor": nuevo}


def anotar_precio(proveedor: str, articulo: str, precio: float,
                  unidad: str = "pieza", nota: str = "") -> dict:
    """Registra un precio CON su fecha. Un precio sin fecha no sirve para decidir."""
    d = _leer()
    for p in d.get("proveedores", []):
        if p["nombre"].lower() == proveedor.lower():
            p.setdefault("precios", []).append({
                "articulo": articulo, "precio": float(precio), "unidad": unidad,
                "fecha": date.today().isoformat(), "nota": nota,
            })
            _guardar(d)
            return {"status": "OK", "proveedor": proveedor,
                    "detalle": f"{articulo}: ${precio} por {unidad}"}
    return {"status": "NO_ENCONTRADO",
            "detalle": f"No tengo a '{proveedor}'. Agrégalo primero."}


def listar() -> dict:
    d = _leer()
    return {"status": "OK", "total": len(d.get("proveedores", [])),
            "proveedores": d.get("proveedores", [])}


def _texto(r: dict) -> str:
    """La respuesta como la lee un humano, para el chat."""
    if r.get("status") == "NO_LO_TENGO":
        return r["detalle"]
    if r.get("status") != "OK":
        return r.get("detalle", "No pude consultar el directorio.")
    if "proveedores" not in r:
        return "Sin datos."
    partes = []
    for p in r["proveedores"]:
        linea = f"🏪 **{p['nombre']}**"
        datos = [x for x in (p.get("web"), p.get("telefono"), p.get("zona")) if x]
        if datos:
            linea += "  ·  " + " · ".join(datos)
        if not p.get("telefono"):
            linea += "\n   _(sin teléfono todavía — pásamelo cuando cotices)_"
        for x in p.get("precios", [])[:4]:
            linea += (f"\n   • {x['articulo']}: **${x['precio']:,.2f}** "
                      f"por {x['unidad']}  _(dato del {x['fecha']})_")
            if x.get("nota"):
                linea += f"\n     ↳ {x['nota']}"
        partes.append(linea)
    return "\n\n".join(partes)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(_texto(buscar(" ".join(sys.argv[1:]))))
    else:
        d = listar()
        print(f"{d['total']} proveedores en el directorio:\n")
        print(_texto({"status": "OK", "proveedores": d["proveedores"]}))
