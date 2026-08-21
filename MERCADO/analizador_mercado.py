# -*- coding: utf-8 -*-
"""AURORA · ANALIZADOR DE MERCADO Y COMERCIO

Anuar lo pidió el 2026-08-16, estando en números rojos: *"poder hacer
dropshipping en Amazon o comprar por mi cuenta con el analizador de mercado o
de negocios… análisis de compraventa de mercado y comercio por estado o
ciudad, sugerencias de la misma app"*.

**Lo primero, la verdad de las fuentes** — se midió, no se supuso (2026-08-16):
  · `api.mercadolibre.com` búsqueda pública → **HTTP 403**, ya exige token.
  · `listado.mercadolibre.com.mx` por script → **suspicious-traffic**, bloquea.
  · Lo mismo con navegador real headless (Playwright) → **0 productos**.
  · Buscador web (ddgs) → sí responde, pero los resúmenes **no traen precios**.

Por eso esta herramienta NO se cuelga de un raspador que se rompe cada mes.
Se apoya en lo que de verdad decide si ganas o pierdes, y eso **no depende de
que ninguna plataforma te deje entrar**:

  1. **La cuenta real.** Qué te queda en la mano después de comisión, envío,
     empaque, pasarela e IVA. Es la razón por la que se puede vender mucho y
     seguir perdiendo.
  2. **El piso.** El precio mínimo al que NO pierdes, y el precio para ganar
     el margen que tú decidas.
  3. **La competencia, medida.** Pegas los precios que ves en pantalla — que
     es lo que ya haces con los ojos — y te dice el rango real, la mediana y
     en qué parte del mercado caes.
  4. **Comprar para revender vs. hacerlo en tu taller**, con tu fórmula real:
     (materiales × 1.20) + corte $8/min + diseño + instalación.
  5. **Por estado y por ciudad**, con TUS ventas reales, las que ya están en
     las bases de AURORA. No con números de nadie más.
  6. **Historial**: cada análisis se guarda, para ver si un producto sube o
     baja con el tiempo. Ahí es donde se vuelve escalable.

Las comisiones viven en `CONFIG/canales_venta.json`, con **la fecha en que se
capturaron y dónde confirmarlas**. Cambian; el que manda es tu estado de
cuenta, no este archivo.

Correr:
    python MERCADO/analizador_mercado.py --canales
    python MERCADO/analizador_mercado.py --cuenta 450 --costo 180 --canal ml_clasica
    python MERCADO/analizador_mercado.py --piso 180 --margen 40 --canal amazon
    python MERCADO/analizador_mercado.py --competencia "350 420 399 380 450" --costo 180
    python MERCADO/analizador_mercado.py --geo
"""
from __future__ import annotations
import io
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CANALES_JSON = RAIZ / "CONFIG" / "canales_venta.json"
BD = RAIZ / "DATOS" / "mercado.db"
IVA = 0.16

# Comisiones capturadas el 2026-08-16. Son el punto de partida, NO la verdad
# revelada: cada quien tiene su categoría, su reputación y sus promociones.
# El JSON manda sobre esto en cuanto exista.
CANALES_BASE = {
    "ml_clasica": {
        "nombre": "Mercado Libre · publicación Clásica",
        "comision_pct": 14.5,
        "cargo_fijo": [[149, 25.0], [299, 30.0], [None, 0.0]],
        "envio_gratis_desde": 299.0,
        "comision_lleva_iva": True,
        "nota": "La Clásica no aparece en cuotas sin interés. De $299 en "
                "adelante el envío gratis lo pagas tú y pesa fuerte.",
        "confirmar_en": "Mercado Libre › Tarifas por vender",
    },
    "ml_premium": {
        "nombre": "Mercado Libre · publicación Premium",
        "comision_pct": 18.5,
        "cargo_fijo": [[149, 25.0], [299, 30.0], [None, 0.0]],
        "envio_gratis_desde": 299.0,
        "comision_lleva_iva": True,
        "nota": "Premium da meses sin intereses. Se usa cuando el producto se "
                "vende por financiamiento, no por precio.",
        "confirmar_en": "Mercado Libre › Tarifas por vender",
    },
    "amazon": {
        "nombre": "Amazon México",
        "comision_pct": 15.0,
        "cargo_fijo": [[None, 0.0]],
        "cuota_mensual": 600.0,
        "comision_lleva_iva": True,
        "nota": "La comisión cambia por categoría (8% a 15%). El plan "
                "Profesional cuesta ~$600 al mes: si vendes poco, el "
                "Individual sale mejor aunque cobre por artículo.",
        "confirmar_en": "Amazon Seller Central › Tarifas de venta",
    },
    "marketplace": {
        "nombre": "Facebook Marketplace (entrega local)",
        "comision_pct": 0.0,
        "cargo_fijo": [[None, 0.0]],
        "comision_lleva_iva": False,
        "nota": "Entrega en persona no cobra comisión. Es tu canal más "
                "barato y el que ya usas — el costo real es tu tiempo.",
        "confirmar_en": "Facebook › Políticas de Marketplace",
    },
    "tienda_propia": {
        "nombre": "Venta directa / tienda propia",
        "comision_pct": 0.0,
        "cargo_fijo": [[None, 0.0]],
        "pasarela_pct": 3.5,
        "comision_lleva_iva": True,
        "nota": "Sin comisión de plataforma. Si cobras con terminal o link "
                "de pago, ahí sí entra la pasarela (~3.5% + IVA).",
        "confirmar_en": "Tu terminal o Mercado Pago › Costos",
    },
}

ESTADOS_LADA = {
    "33": "Jalisco", "55": "Ciudad de México", "81": "Nuevo León",
    "222": "Puebla", "442": "Querétaro", "477": "Guanajuato",
    "444": "San Luis Potosí", "998": "Quintana Roo", "999": "Yucatán",
    "664": "Baja California", "656": "Chihuahua", "844": "Coahuila",
    "618": "Durango", "662": "Sonora", "667": "Sinaloa", "312": "Colima",
    "443": "Michoacán", "228": "Veracruz", "961": "Chiapas",
    "951": "Oaxaca", "744": "Guerrero", "777": "Morelos", "449": "Aguascalientes",
    "492": "Zacatecas", "246": "Tlaxcala", "722": "Estado de México",
    "993": "Tabasco", "981": "Campeche", "834": "Tamaulipas", "612": "BCS",
    "311": "Nayarit", "871": "Durango/Coahuila (Laguna)",
}


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


# ─────────────────────────── canales y comisiones ────────────────────────────
def canales() -> dict:
    """Los canales con sus comisiones. El JSON gana; si no hay, la base."""
    datos = dict(CANALES_BASE)
    try:
        if CANALES_JSON.exists():
            guardado = json.loads(CANALES_JSON.read_text(encoding="utf-8"))
            for k, v in (guardado.get("canales") or {}).items():
                datos[k] = {**datos.get(k, {}), **v}
    except Exception:
        pass
    return datos


def guardar_canales(datos: dict) -> Path:
    """Deja las comisiones editadas en disco, con la fecha del cambio."""
    CANALES_JSON.parent.mkdir(parents=True, exist_ok=True)
    CANALES_JSON.write_text(json.dumps(
        {"capturado": datetime.now().strftime("%Y-%m-%d"),
         "aviso": "Confirma cada porcentaje en tu propia cuenta: cambian por "
                  "categoría y por promociones. Manda tu estado de cuenta.",
         "canales": datos}, ensure_ascii=False, indent=2), encoding="utf-8")
    return CANALES_JSON


def _fijo(canal: dict, precio: float) -> float:
    for tope, monto in canal.get("cargo_fijo", [[None, 0.0]]):
        if tope is None or precio < tope:
            return float(monto)
    return 0.0


# ──────────────────────────── la cuenta que decide ───────────────────────────
def cuenta(precio_venta: float, costo: float, canal: str = "ml_clasica",
           envio: float = 0.0, empaque: float = 0.0, otros: float = 0.0,
           yo_pago_envio: bool | None = None, piezas: int = 1) -> dict:
    """Qué te queda en la mano. Es el corazón de todo el analizador.

    `costo` es lo que TE cuesta la pieza: lo que pagas al proveedor si
    revendes, o lo que te sale producirla si la haces tú.
    `yo_pago_envio` — si no se dice, se usa la regla del canal (en Mercado
    Libre, de $299 para arriba el envío gratis lo absorbe el vendedor).
    """
    cs = canales()
    c = cs.get(canal)
    if not c:
        return {"status": "CANAL_RARO",
                "detalle": f"No conozco «{canal}». Tengo: " + ", ".join(cs)}
    if precio_venta <= 0:
        return {"status": "PRECIO_INVALIDO",
                "detalle": "El precio de venta tiene que ser mayor que cero."}

    pct = float(c.get("comision_pct", 0)) / 100.0
    comision = precio_venta * pct
    if c.get("comision_lleva_iva"):
        comision *= (1 + IVA)
    fijo = _fijo(c, precio_venta)
    pasarela = precio_venta * float(c.get("pasarela_pct", 0)) / 100.0
    if pasarela and c.get("comision_lleva_iva"):
        pasarela *= (1 + IVA)

    if yo_pago_envio is None:
        desde = c.get("envio_gratis_desde")
        yo_pago_envio = bool(desde and precio_venta >= float(desde))
    envio_real = float(envio) if yo_pago_envio else 0.0

    gastos = comision + fijo + pasarela + envio_real + float(empaque) + float(otros)
    ganancia = precio_venta - float(costo) - gastos
    margen = ganancia / precio_venta * 100 if precio_venta else 0.0
    sobre_costo = ganancia / float(costo) * 100 if costo else 0.0

    r = {"status": "OK", "canal": c["nombre"], "clave": canal,
         "precio_venta": round(precio_venta, 2), "costo": round(float(costo), 2),
         "comision": round(comision, 2), "cargo_fijo": round(fijo, 2),
         "pasarela": round(pasarela, 2), "envio": round(envio_real, 2),
         "empaque": round(float(empaque), 2), "otros": round(float(otros), 2),
         "gastos": round(gastos, 2), "ganancia": round(ganancia, 2),
         "margen_pct": round(margen, 1), "sobre_costo_pct": round(sobre_costo, 1),
         "yo_pago_envio": yo_pago_envio, "piezas": int(piezas),
         "ganancia_total": round(ganancia * int(piezas), 2),
         "nota_canal": c.get("nota", "")}

    # El veredicto, dicho como se dice en el taller.
    if ganancia < 0:
        r["veredicto"] = "PIERDES"
        r["explicacion"] = (f"Cada pieza te deja **${abs(ganancia):,.2f} de "
                            f"pérdida**. Vender más solo te hunde más rápido.")
    elif margen < 15:
        r["veredicto"] = "APENAS"
        r["explicacion"] = (f"Te quedan ${ganancia:,.2f} ({margen:.1f}%). Con "
                            f"una devolución o un cliente enojado se te va la "
                            f"ganancia de varias piezas.")
    elif margen < 30:
        r["veredicto"] = "SE PUEDE"
        r["explicacion"] = (f"Te quedan ${ganancia:,.2f} ({margen:.1f}%). "
                            f"Aguanta, pero no deja para invertir.")
    else:
        r["veredicto"] = "BUENO"
        r["explicacion"] = (f"Te quedan ${ganancia:,.2f} ({margen:.1f}%). "
                            f"Este sí deja para reponer material y crecer.")
    if c.get("cuota_mensual"):
        piso = c["cuota_mensual"] / ganancia if ganancia > 0 else None
        r["cuota_mensual"] = c["cuota_mensual"]
        r["piezas_para_la_cuota"] = (int(piso) + 1 if piso else None)
    return r


def piso(costo: float, canal: str = "ml_clasica", margen_pct: float = 30.0,
         envio: float = 0.0, empaque: float = 0.0, otros: float = 0.0) -> dict:
    """El precio mínimo para no perder, y el precio para ganar lo que quieres.

    Se resuelve buscando: la comisión depende del precio y el cargo fijo da
    brincos por tramos, así que despejar a mano se equivoca justo en las
    orillas. Buscar centavo a centavo tarda milésimas y no falla.
    """
    def _g(p, m):
        r = cuenta(p, costo, canal, envio, empaque, otros)
        return r.get("margen_pct", -999) if m else r.get("ganancia", -999)

    def _buscar(objetivo, por_margen):
        lo, hi = 0.01, max(float(costo) * 20 + 5000, 10000.0)
        for _ in range(60):
            mid = (lo + hi) / 2
            if _g(mid, por_margen) < objetivo:
                lo = mid
            else:
                hi = mid
        return round(hi, 2)

    equilibrio = _buscar(0.0, False)
    objetivo = _buscar(float(margen_pct), True)
    return {"status": "OK", "costo": round(float(costo), 2),
            "canal": canales().get(canal, {}).get("nombre", canal),
            "clave": canal,
            "precio_equilibrio": equilibrio,
            "precio_objetivo": objetivo, "margen_pedido": float(margen_pct),
            "detalle_objetivo": cuenta(objetivo, costo, canal, envio,
                                       empaque, otros)}


# ──────────────────────────── medir la competencia ───────────────────────────
def _numeros(texto) -> list:
    """Saca los precios de un pegote de texto: '350, $420 c/u  399.00' → […]."""
    import re
    if isinstance(texto, (list, tuple)):
        crudos = []
        for t in texto:
            crudos += _numeros(t) if isinstance(t, str) else [float(t)]
        return crudos
    limpio = str(texto).replace("$", " ").replace(",", "")
    vals = []
    for m in re.findall(r"\d+(?:\.\d+)?", limpio):
        v = float(m)
        if 1 <= v <= 1_000_000:
            vals.append(v)
    return vals


def competencia(precios, mi_precio: float = 0.0, costo: float = 0.0,
                canal: str = "ml_clasica") -> dict:
    """Dónde caes tú entre los precios que ves en pantalla.

    Anuar ya hace esto con los ojos. Aquí se vuelve número: el rango real, la
    mediana (que resiste mejor al vendedor loco que pone el triple), y qué
    margen te queda si te pones en cada punto del mercado.
    """
    vals = sorted(_numeros(precios))
    if len(vals) < 2:
        return {"status": "POCOS_PRECIOS",
                "detalle": "Necesito al menos 2 precios para comparar. Copia "
                           "los que ves en la búsqueda y pégalos aquí."}

    def _cuartil(q):
        i = (len(vals) - 1) * q
        b, t = int(i), min(int(i) + 1, len(vals) - 1)
        return vals[b] + (vals[t] - vals[b]) * (i - b)

    med = _cuartil(0.5)
    r = {"status": "OK", "cuantos": len(vals), "minimo": round(vals[0], 2),
         "q1": round(_cuartil(0.25), 2), "mediana": round(med, 2),
         "q3": round(_cuartil(0.75), 2), "maximo": round(vals[-1], 2),
         "promedio": round(sum(vals) / len(vals), 2)}
    r["hueco_pct"] = round((vals[-1] - vals[0]) / vals[0] * 100, 1)

    if mi_precio:
        abajo = sum(1 for v in vals if v < mi_precio)
        r["mi_precio"] = round(float(mi_precio), 2)
        r["mas_baratos_que_yo"] = abajo
        r["posicion_pct"] = round(abajo / len(vals) * 100, 1)
        if mi_precio <= r["q1"]:
            r["donde_caigo"] = ("Estás entre los MÁS BARATOS. Vendes por "
                                "precio: revisa que de verdad te quede algo.")
        elif mi_precio >= r["q3"]:
            r["donde_caigo"] = ("Estás entre los MÁS CAROS. Solo funciona si "
                                "tu foto, tu entrega o tu acabado se ven "
                                "mejor que los demás.")
        else:
            r["donde_caigo"] = "Estás en el medio del mercado, que es lo sano."

    if costo:
        puntos = {"al más barato": vals[0], "al cuartil bajo": r["q1"],
                  "a la mediana": med, "al cuartil alto": r["q3"]}
        if mi_precio:
            puntos["a mi precio"] = float(mi_precio)
        r["si_vendo"] = {}
        for etiqueta, p in puntos.items():
            c = cuenta(p, costo, canal)
            r["si_vendo"][etiqueta] = {
                "precio": round(p, 2), "ganancia": c.get("ganancia"),
                "margen_pct": c.get("margen_pct"),
                "veredicto": c.get("veredicto")}
        vivos = [e for e, d in r["si_vendo"].items()
                 if (d["ganancia"] or 0) > 0]
        r["consejo"] = (
            "Ni al precio del más caro te queda: este producto no es para ti "
            "en este canal." if not vivos else
            f"Te deja ganancia vendiendo {', '.join(vivos)}.")
    return r


# ─────────────────── comprar para revender vs. hacerlo tú ────────────────────
def comprar_o_producir(precio_venta: float, costo_proveedor: float,
                       materiales: float = 0.0, minutos_corte: float = 0.0,
                       diseno: float = 0.0, instalacion: float = 0.0,
                       canal: str = "ml_clasica", envio_proveedor: float = 0.0,
                       piezas: int = 1) -> dict:
    """Las dos rutas, con la fórmula real de Anuar para la de su taller.

    Su fórmula, dictada por él: (materiales × 1.20) + corte $8/min + diseño +
    instalación. El corte a $8 el minuto ya trae adentro luz, desgaste y su
    trabajo — por eso no se le suma nada aparte.
    """
    costo_taller = (float(materiales) * 1.20 + float(minutos_corte) * 8.0
                    + float(diseno) + float(instalacion))
    revender = cuenta(precio_venta, float(costo_proveedor) + float(envio_proveedor),
                      canal, piezas=piezas)
    producir = cuenta(precio_venta, costo_taller, canal, piezas=piezas)
    if revender.get("status") != "OK":
        return revender

    g_r = revender["ganancia"]
    g_p = producir["ganancia"]
    r = {"status": "OK", "precio_venta": round(precio_venta, 2),
         "revender": revender, "producir": producir,
         "costo_taller": round(costo_taller, 2),
         "costo_proveedor": round(float(costo_proveedor) + float(envio_proveedor), 2),
         "desglose_taller": {
             "materiales_con_20": round(float(materiales) * 1.20, 2),
             "corte": round(float(minutos_corte) * 8.0, 2),
             "diseno": round(float(diseno), 2),
             "instalacion": round(float(instalacion), 2)},
         "diferencia": round(abs(g_p - g_r), 2)}

    if g_p > g_r:
        r["conviene"] = "PRODUCIR"
        r["por_que"] = (f"Hacerlo tú deja ${g_p:,.2f} contra ${g_r:,.2f} de "
                        f"revender: **${g_p - g_r:,.2f} más por pieza**. "
                        f"Pero ocupa {minutos_corte:g} min de máquina — si "
                        f"tienes trabajo encimado, ese tiempo también vale.")
    elif g_r > g_p:
        r["conviene"] = "REVENDER"
        r["por_que"] = (f"Revender deja ${g_r:,.2f} contra ${g_p:,.2f} de "
                        f"producirlo: **${g_r - g_p:,.2f} más por pieza**, y "
                        f"sin ocupar la máquina ni tu tiempo.")
    else:
        r["conviene"] = "IGUAL"
        r["por_que"] = "Dejan lo mismo. Decide por tiempo de máquina."
    if piezas > 1:
        r["por_que"] += (f"\nPor {piezas} piezas la diferencia es "
                         f"**${abs(g_p - g_r) * piezas:,.2f}**.")
    if g_r < 0 and g_p < 0:
        r["conviene"] = "NINGUNA"
        r["por_que"] = ("A ese precio pierdes por las dos rutas. O subes el "
                        "precio, o este producto no es negocio hoy.")
    return r


# ───────────────────────── por estado y por ciudad ───────────────────────────
def _bases() -> list:
    return sorted(set(list(RAIZ.rglob("*.db")) + list(RAIZ.rglob("*.sqlite"))))


def geografia(limite: int = 15) -> dict:
    """Dónde están tus clientes de verdad, sacado de tus propias bases.

    No son números de mercado de nadie más: son TUS ventas. El estado sale de
    la lada del teléfono, que es el único dato geográfico que de verdad
    tienes capturado.
    """
    import re
    vistos, por_estado = set(), {}
    revisadas, con_datos = 0, []
    for f in _bases():
        try:
            cx = sqlite3.connect(f"file:{f}?mode=ro", uri=True, timeout=4)
            cur = cx.cursor()
            tablas = [t[0] for t in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            revisadas += 1
            for t in tablas:
                try:
                    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")')]
                except sqlite3.Error:
                    continue
                tel = [c for c in cols
                       if any(k in c.lower() for k in
                              ("tel", "phone", "celular", "whats", "numero"))]
                if not tel:
                    continue
                for col in tel:
                    try:
                        filas = cur.execute(
                            f'SELECT "{col}" FROM "{t}" WHERE "{col}" IS NOT NULL'
                        ).fetchall()
                    except sqlite3.Error:
                        continue
                    for (v,) in filas:
                        d = re.sub(r"\D", "", str(v))
                        if len(d) < 10:
                            continue
                        d = d[-10:]
                        if d in vistos:
                            continue
                        vistos.add(d)
                        est = None
                        for n in (3, 2):
                            if d[:n] in ESTADOS_LADA:
                                est = ESTADOS_LADA[d[:n]]
                                break
                        est = est or f"lada {d[:3]} (sin identificar)"
                        por_estado[est] = por_estado.get(est, 0) + 1
                    if filas:
                        con_datos.append(f"{f.name} › {t}.{col}")
            cx.close()
        except Exception:
            continue

    orden = sorted(por_estado.items(), key=lambda x: -x[1])
    total = sum(por_estado.values())
    r = {"status": "OK", "bases_revisadas": revisadas, "clientes": total,
         "por_estado": orden[:limite], "tablas": sorted(set(con_datos))[:12]}
    if total:
        top = orden[0]
        r["lectura"] = (
            f"De {total} clientes con teléfono, **{top[1]} son de {top[0]}** "
            f"({top[1] / total * 100:.0f}%). "
            + ("Tu mercado es local: la entrega en persona por Marketplace no "
               "te cuesta comisión y es tu canal más rentable."
               if top[1] / total > 0.6 else
               "Tienes clientes repartidos: ahí sí vale la pena el envío y "
               "publicar en plataformas."))
    else:
        r["lectura"] = ("No encontré teléfonos capturados. En cuanto factures "
                        "con teléfono, esto se llena solo.")
    return r


# ───────────────────────── descubrir qué se está vendiendo ───────────────────
def explorar(termino: str, cuantos: int = 8) -> dict:
    """Qué hay allá afuera con ese término. Sirve para descubrir, no para precios.

    Se midió el 2026-08-16: los buscadores devuelven títulos y resúmenes, pero
    NO los precios de las plataformas. Así que esto es una lupa para encontrar
    ideas y competidores — los precios los capturas con `competencia()`.
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
    except ImportError:
        return {"status": "FALTA_LIBRERIA",
                "detalle": "Falta `ddgs`. Instálala con: pip install ddgs"}
    try:
        with DDGS() as d:
            res = list(d.text(f"{termino} precio méxico", region="mx-es",
                              max_results=int(cuantos)))
    except Exception as e:
        return {"status": "SIN_INTERNET", "detalle": str(e)[:200]}
    hallazgos = [{"titulo": x.get("title", "")[:110],
                  "resumen": x.get("body", "")[:200],
                  "link": x.get("href", "")} for x in res]
    return {"status": "OK", "termino": termino, "cuantos": len(hallazgos),
            "hallazgos": hallazgos,
            "aviso": ("Los buscadores no entregan los precios de Mercado Libre "
                      "ni de Amazon. Abre 2 o 3 de estos, copia los precios "
                      "que veas y pégalos en «Competencia»: ahí sí sale el "
                      "análisis con números.")}


# ─────────────────────────────── historial ───────────────────────────────────
def _bd():
    BD.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(BD, timeout=10)
    cx.execute("PRAGMA journal_mode=WAL")
    cx.execute("""CREATE TABLE IF NOT EXISTS analisis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuando TEXT NOT NULL, producto TEXT NOT NULL, canal TEXT,
        precio_venta REAL, costo REAL, ganancia REAL, margen REAL,
        mediana_mercado REAL, cuantos_competidores INTEGER, nota TEXT)""")
    cx.commit()
    return cx


def anotar(producto: str, resultado: dict, mercado: dict = None,
           nota: str = "") -> dict:
    """Guarda el análisis para poder ver, con el tiempo, si mejora o empeora."""
    cx = _bd()
    cx.execute("""INSERT INTO analisis (cuando, producto, canal, precio_venta,
                  costo, ganancia, margen, mediana_mercado,
                  cuantos_competidores, nota) VALUES (?,?,?,?,?,?,?,?,?,?)""",
               (datetime.now().strftime("%Y-%m-%d %H:%M"), producto.strip(),
                resultado.get("clave", ""), resultado.get("precio_venta"),
                resultado.get("costo"), resultado.get("ganancia"),
                resultado.get("margen_pct"),
                (mercado or {}).get("mediana"),
                (mercado or {}).get("cuantos"), nota))
    cx.commit()
    n = cx.execute("SELECT COUNT(*) FROM analisis WHERE producto=?",
                   (producto.strip(),)).fetchone()[0]
    cx.close()
    return {"status": "OK", "producto": producto.strip(), "veces": n,
            "archivo": str(BD)}


def historial(producto: str = "", limite: int = 30) -> dict:
    cx = _bd()
    if producto:
        filas = cx.execute(
            """SELECT cuando, producto, canal, precio_venta, costo, ganancia,
               margen, mediana_mercado FROM analisis WHERE producto LIKE ?
               ORDER BY id DESC LIMIT ?""",
            (f"%{producto}%", limite)).fetchall()
    else:
        filas = cx.execute(
            """SELECT cuando, producto, canal, precio_venta, costo, ganancia,
               margen, mediana_mercado FROM analisis
               ORDER BY id DESC LIMIT ?""", (limite,)).fetchall()
    cx.close()
    campos = ("cuando", "producto", "canal", "precio_venta", "costo",
              "ganancia", "margen", "mediana_mercado")
    filas = [dict(zip(campos, f)) for f in filas]
    r = {"status": "OK", "cuantos": len(filas), "filas": filas}
    if producto and len(filas) >= 2:
        nuevo, viejo = filas[0], filas[-1]
        if nuevo["margen"] is not None and viejo["margen"] is not None:
            d = nuevo["margen"] - viejo["margen"]
            r["tendencia"] = (
                f"El margen de «{producto}» pasó de {viejo['margen']:.1f}% a "
                f"{nuevo['margen']:.1f}% ({'+' if d >= 0 else ''}{d:.1f} "
                f"puntos) entre {viejo['cuando']} y {nuevo['cuando']}.")
    return r


# ───────────────────────── sugerencias de la propia app ──────────────────────
def sugerencias(producto: str = "", costo: float = 0.0,
                precios_competencia=None, canal: str = "ml_clasica",
                minutos_corte: float = 0.0) -> dict:
    """Lo que la app opina, con lo que tiene enfrente. Sin adivinar.

    Él lo pidió con esas palabras: *"sugerencias de la misma app"*. Cada
    sugerencia sale de un número, y se dice de dónde salió.
    """
    dice = []
    cs = canales()

    if costo and precios_competencia:
        merc = competencia(precios_competencia, costo=costo, canal=canal)
        if merc.get("status") == "OK":
            med = merc["mediana"]
            c = cuenta(med, costo, canal)
            if c["ganancia"] <= 0:
                dice.append(
                    f"⛔ A la mediana del mercado (${med:,.2f}) **pierdes "
                    f"${abs(c['ganancia']):,.2f} por pieza** en "
                    f"{cs[canal]['nombre']}. Tu costo de ${costo:,.2f} es muy "
                    f"alto para este producto: o consigues mejor proveedor, o "
                    f"lo dejas.")
            else:
                dice.append(
                    f"✅ A la mediana (${med:,.2f}) te quedan "
                    f"${c['ganancia']:,.2f} ({c['margen_pct']:.1f}%).")
            if merc["hueco_pct"] > 80:
                dice.append(
                    f"🔎 El mercado va de ${merc['minimo']:,.2f} a "
                    f"${merc['maximo']:,.2f} — {merc['hueco_pct']:.0f}% de "
                    f"diferencia. Cuando el rango es así de ancho, no se está "
                    f"vendiendo el mismo producto: hay calidades distintas y "
                    f"ahí es donde cabe uno bien presentado.")

    if costo:
        # ¿Qué canal deja más, al mismo precio? Se calcula, no se opina.
        base = (competencia(precios_competencia, costo=costo).get("mediana")
                if precios_competencia else costo * 2.5)
        tabla = []
        for k in cs:
            c = cuenta(base, costo, k)
            if c.get("status") == "OK":
                tabla.append((k, cs[k]["nombre"], c["ganancia"], c["margen_pct"]))
        tabla.sort(key=lambda x: -x[2])
        if tabla:
            mejor, peor = tabla[0], tabla[-1]
            dice.append(
                f"🏆 Vendiendo a ${base:,.2f}, el canal que más deja es "
                f"**{mejor[1]}** con ${mejor[2]:,.2f} ({mejor[3]:.1f}%); el "
                f"que menos, {peor[1]} con ${peor[2]:,.2f}. La diferencia por "
                f"pieza es **${mejor[2] - peor[2]:,.2f}** — solo por dónde la "
                f"publicas.")
        p = piso(costo, canal, 30.0)
        dice.append(
            f"📉 En {cs[canal]['nombre']} tu punto de equilibrio es "
            f"**${p['precio_equilibrio']:,.2f}** (abajo de ahí, pierdes) y "
            f"para ganar 30% tendrías que vender en "
            f"**${p['precio_objetivo']:,.2f}**.")

    if minutos_corte:
        dice.append(
            f"⏱️ Ese producto ocupa {minutos_corte:g} min de láser = "
            f"${minutos_corte * 8:,.2f} de tu tarifa. Si te llega trabajo de "
            f"taller ese mismo día, ese tiempo ya está vendido: revisa "
            f"«Comprar o producir» antes de comprometer la máquina.")

    g = geografia()
    if g.get("clientes"):
        dice.append("📍 " + g["lectura"])

    if not dice:
        dice.append("Dame al menos el costo de la pieza y te digo el precio "
                    "mínimo, el mejor canal y qué te queda.")
    return {"status": "OK", "producto": producto, "sugerencias": dice}


# ──────────────────────────────── textos ─────────────────────────────────────
def _t_cuenta(r: dict) -> str:
    if r.get("status") != "OK":
        return f"⚠️ {r.get('detalle', r.get('status'))}"
    ico = {"PIERDES": "⛔", "APENAS": "⚠️", "SE PUEDE": "🟡", "BUENO": "✅"}
    t = (f"{ico.get(r['veredicto'], '•')} **{r['veredicto']}** · {r['canal']}\n"
         f"   Vendes en ${r['precio_venta']:,.2f} · te cuesta "
         f"${r['costo']:,.2f}\n"
         f"   ─ comisión ${r['comision']:,.2f}")
    if r["cargo_fijo"]:
        t += f" · cargo fijo ${r['cargo_fijo']:,.2f}"
    if r["pasarela"]:
        t += f" · pasarela ${r['pasarela']:,.2f}"
    if r["envio"]:
        t += f" · envío ${r['envio']:,.2f}"
    if r["empaque"]:
        t += f" · empaque ${r['empaque']:,.2f}"
    t += (f"\n   ─ gastos totales ${r['gastos']:,.2f}\n"
          f"   **Te queda ${r['ganancia']:,.2f} por pieza "
          f"({r['margen_pct']:.1f}% del precio, {r['sobre_costo_pct']:.0f}% "
          f"sobre lo que te costó)**\n   {r['explicacion']}")
    if r.get("piezas", 1) > 1:
        t += f"\n   Por {r['piezas']} piezas: **${r['ganancia_total']:,.2f}**"
    if r.get("piezas_para_la_cuota"):
        t += (f"\n   ⚠️ Ese canal cobra ${r['cuota_mensual']:,.0f} al mes: "
              f"necesitas vender {r['piezas_para_la_cuota']} piezas solo para "
              f"pagar la cuota.")
    if r.get("nota_canal"):
        t += f"\n   💡 {r['nota_canal']}"
    return t


def _t_competencia(r: dict) -> str:
    if r.get("status") != "OK":
        return f"⚠️ {r.get('detalle', r.get('status'))}"
    t = (f"📊 **{r['cuantos']} precios de la competencia**\n"
         f"   más barato ${r['minimo']:,.2f} · 1 de cada 4 abajo de "
         f"${r['q1']:,.2f} · **mediana ${r['mediana']:,.2f}** · 1 de cada 4 "
         f"arriba de ${r['q3']:,.2f} · más caro ${r['maximo']:,.2f}\n"
         f"   El más caro cuesta {r['hueco_pct']:.0f}% más que el más barato.")
    if r.get("mi_precio"):
        t += (f"\n   Tu precio ${r['mi_precio']:,.2f}: "
              f"{r['mas_baratos_que_yo']} de {r['cuantos']} están más baratos "
              f"({r['posicion_pct']:.0f}% del mercado).\n   {r['donde_caigo']}")
    if r.get("si_vendo"):
        t += "\n\n   Qué te queda según dónde te pongas:"
        for et, d in r["si_vendo"].items():
            t += (f"\n   · {et:<18} ${d['precio']:>9,.2f} → "
                  f"${d['ganancia']:>9,.2f}  ({d['margen_pct']:>5.1f}%)  "
                  f"{d['veredicto']}")
        t += f"\n   👉 {r['consejo']}"
    return t


def _t_geo(r: dict) -> str:
    t = (f"📍 **Tus clientes por estado** — {r['clientes']} con teléfono, de "
         f"{r['bases_revisadas']} bases\n")
    for est, n in r["por_estado"]:
        barra = "█" * max(1, int(n / max(1, r["por_estado"][0][1]) * 24))
        t += f"   {est:<26} {n:>4}  {barra}\n"
    return t + f"\n   {r['lectura']}"


def main() -> int:
    _consola_utf8()
    a = sys.argv[1:]

    def _op(n, d=None):
        if f"--{n}" in a:
            i = a.index(f"--{n}")
            if i + 1 < len(a):
                return a[i + 1]
        return d

    def _f(n, d=0.0):
        v = _op(n)
        try:
            return float(str(v).replace(",", ".")) if v is not None else d
        except ValueError:
            return d

    canal = _op("canal", "ml_clasica")
    if "--canales" in a:
        for k, c in canales().items():
            print(f"\n• {k}\n  {c['nombre']} — comisión {c['comision_pct']}%"
                  + (" + IVA" if c.get("comision_lleva_iva") else ""))
            if c.get("cuota_mensual"):
                print(f"  cuota mensual ${c['cuota_mensual']:,.0f}")
            print(f"  {c.get('nota', '')}\n  confirmar en: "
                  f"{c.get('confirmar_en', '—')}")
        return 0
    if "--geo" in a:
        print(_t_geo(geografia()))
        return 0
    if _op("explorar"):
        r = explorar(_op("explorar"))
        if r["status"] != "OK":
            print("⚠️", r["detalle"])
            return 1
        for h in r["hallazgos"]:
            print(f"• {h['titulo']}\n  {h['resumen'][:120]}\n  {h['link']}")
        print("\n💡", r["aviso"])
        return 0
    # Sugerir va ANTES que competencia: `--sugerir` casi siempre viene
    # acompañado de `--competencia`, y si se revisa al revés nunca se alcanza.
    if "--sugerir" in a:
        s = sugerencias(_op("sugerir", ""), _f("costo"),
                        _op("competencia"), canal, _f("minutos"))
        print(f"🧠 **Sugerencias** — {s['producto']}\n")
        for d in s["sugerencias"]:
            print("  " + d + "\n")
        return 0
    if _op("competencia"):
        print(_t_competencia(competencia(_op("competencia"), _f("mi_precio"),
                                         _f("costo"), canal)))
        return 0
    if "--piso" in a:
        p = piso(_f("piso"), canal, _f("margen", 30.0))
        print(f"📉 Costo ${p['costo']:,.2f} en {p['canal']}\n"
              f"   Punto de equilibrio: **${p['precio_equilibrio']:,.2f}**\n"
              f"   Para ganar {p['margen_pedido']:.0f}%: "
              f"**${p['precio_objetivo']:,.2f}**\n")
        print(_t_cuenta(p["detalle_objetivo"]))
        return 0
    if "--cuenta" in a:
        r = cuenta(_f("cuenta"), _f("costo"), canal, _f("envio"),
                   _f("empaque"), _f("otros"), piezas=int(_f("piezas", 1)))
        print(_t_cuenta(r))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
