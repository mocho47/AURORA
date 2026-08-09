# -*- coding: utf-8 -*-
"""AURORA · Cotizar corte de plotter: vinil de recorte y vinil textil

Anuar lo pidió el 2026-08-08, después de que AURORA le INVENTARA un precio en
el chat («entre $500 y $1,500 MXN»). Sus palabras: *"aurora cotiza láser, no
corte plotter"*. Tenía razón: el hueco era real, y en vez de decirlo se puso
a adivinar.

POR QUÉ NO SE PARECE AL COTIZADOR LÁSER: en láser el costo manda por MINUTO DE
MÁQUINA. En plotter la máquina es casi gratis —corta en un minuto lo que se
despica en veinte—. Aquí el costo es **material + manos**:

    material  →  el m² de vinil que se ocupa, con su desperdicio
    corte     →  minutos de plotter, los menos
    despicado →  sacar a mano el sobrante de cada hueco. ES EL COSTO REAL.
    planchado →  solo textil: una planchada por color, con su tack press
    instalación → pegar/posicionar en la superficie o la prenda

EL DESPICADO SE COBRA POR CONTORNOS, NO POR TAMAÑO. Una palabra de 30 cm en
letra gorda se despica en dos minutos; la misma palabra en cursiva delgada con
sesenta huequitos se lleva media hora. El área es la misma y el trabajo no.

Los precios REALES viven en CONFIG/precios_vinil.json y se editan desde el
panel. Lo que no esté capturado NO se inventa: se dice qué falta.

Correr:
    python TALLER/cotizador_vinil.py --area 30x20 --contornos 20 --textil
    python TALLER/cotizador_vinil.py --config
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

CONFIG = RAIZ / "CONFIG" / "precios_vinil.json"
PRECIOS_BASE = RAIZ / "CONFIG" / "precios_base.json"


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


# ── LO QUE FALTA POR CAPTURAR ───────────────────────────────────────────
# Cada uno de estos es un dato que solo Anuar sabe. En null, y el cotizador
# los pide por su nombre en vez de suponerlos: un precio inventado se vuelve
# una cotización perdida o un trabajo regalado.
DATOS_DE_ANUAR = {
    "ancho_rollo_textil_cm": "¿De cuántos cm de ancho es tu rollo de vinil "
                             "textil? (los comunes son 50 o 61)",
    "ancho_rollo_recorte_cm": "¿Y el de vinil de recorte adhesivo?",
    "precio_metro_recorte": "¿Cuánto te cuesta el metro lineal de vinil de "
                            "recorte adhesivo?",
    "precio_hora_mano_obra": "¿En cuánto pones tu hora de trabajo? De aquí "
                             "salen el despicado y la instalación.",
}

# Valores de arranque para lo que SÍ es parejo en cualquier taller. Se pueden
# corregir desde el panel; no son precios, son tiempos y parámetros de máquina.
ARRANQUE = {
    # material
    "desperdicio_pct": 20,          # recortes que quedan alrededor del diseño
    "precio_metro_transfer": 25.0,  # papel de transferencia, solo adhesivo

    # plotter
    "velocidad_corte_cm_min": 600.0,
    "minutos_montaje": 3.0,         # cargar el rollo, alinear, prueba de fuerza

    # despicado — lo que de verdad cuesta
    "segundos_por_contorno": 8.0,
    "segundos_por_dm2": 20.0,       # el área también pesa, pero mucho menos

    # planchado (textil)
    "segundos_por_planchada": 15.0,
    "segundos_tack_press": 3.0,     # entre capa y capa de color
    "minutos_preparar_prenda": 2.0,  # colocar, alinear, pre-planchar la humedad
    "temperatura_algodon_c": 160,
    "temperatura_poliester_c": 140,

    # instalación
    "minutos_instalar_base": 5.0,
    "minutos_instalar_por_dm2": 1.0,

    # negocio
    "margen_pct": 60,
}

# Parámetros de planchado por tipo. Son los del fabricante de vinil textil
# estándar; se corrigen con SU plancha, que es la que manda.
PLANCHADO = {
    "algodon": {"temp": 160, "seg": 15, "pelado": "en caliente"},
    "poliester": {"temp": 140, "seg": 20, "pelado": "en frío",
                  "ojo": "el color de la prenda puede migrar al vinil. Si es "
                         "playera de color oscuro, va vinil bloqueador."},
    "mezcla": {"temp": 150, "seg": 15, "pelado": "en caliente"},
}


def _cargar() -> dict:
    d = dict(ARRANQUE)
    for k in DATOS_DE_ANUAR:
        d[k] = None
    # el vinil textil ya tiene precio real capturado en el taller
    try:
        base = json.loads(PRECIOS_BASE.read_text(encoding="utf-8"))
        it = base.get("insumos_textil", {})
        d["precio_metro_textil"] = it.get("vinil_textil_metro")
        d["precio_metro_bifaz"] = it.get("bifaz_metro")
    except Exception:
        d["precio_metro_textil"] = None
        d["precio_metro_bifaz"] = None
    if CONFIG.exists():
        try:
            d.update(json.loads(CONFIG.read_text(encoding="utf-8")))
        except Exception:
            pass
    return d


def guardar(cambios: dict) -> dict:
    """Guarda los precios que capturó Anuar desde el panel."""
    actual = {}
    if CONFIG.exists():
        try:
            actual = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            actual = {}
    for k, v in (cambios or {}).items():
        if v in ("", None):
            continue
        try:
            actual[k] = float(v) if str(v).replace(".", "", 1).replace(
                "-", "", 1).isdigit() else v
        except Exception:
            actual[k] = v
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(actual, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    return {"status": "OK", "guardados": list(actual.keys())}


def config(tipo: str = "") -> dict:
    """Los precios de hoy y cuáles siguen sin capturar.

    Con `tipo` se piden SOLO los que hacen falta para esa cotización: no tiene
    sentido bloquear un trabajo de textil por no saber el precio del vinil
    adhesivo, que no se va a usar.
    """
    d = _cargar()
    necesarios = dict(DATOS_DE_ANUAR)
    necesarios["precio_metro_textil"] = ("¿Cuánto cuesta el metro de vinil "
                                         "textil?")
    if tipo == "textil":
        necesarios.pop("ancho_rollo_recorte_cm", None)
        necesarios.pop("precio_metro_recorte", None)
    elif tipo == "recorte":
        necesarios.pop("ancho_rollo_textil_cm", None)
        necesarios.pop("precio_metro_textil", None)
    faltan = {k: p for k, p in necesarios.items() if not d.get(k)}
    return {"valores": d, "faltan": faltan, "archivo": str(CONFIG)}


def _escalera() -> list:
    """SU escalera real de precios de vinil de recorte, por tamaño.

    Está capturada en CONFIG/catalogo_servicios.json y es la que usa de
    verdad frente al cliente. No se toca desde aquí: se lee.
    """
    try:
        cat = json.loads((RAIZ / "CONFIG" / "catalogo_servicios.json")
                         .read_text(encoding="utf-8"))
    except Exception:
        return []
    import re as _re
    peldanos = []
    for p in cat.get("productos", []):
        n = str(p.get("nombre", ""))
        if "vinil recorte" not in n.lower():
            continue
        m = _re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm", n, _re.I)
        if m:
            peldanos.append({"area": float(m.group(1)) * float(m.group(2)),
                             "precio": float(p["precio"]), "nombre": n})
    return sorted(peldanos, key=lambda x: x["area"])


def _minimo_y_colocacion() -> tuple:
    """El mínimo de cualquier trabajo y lo que cobra por colocar/planchar."""
    minimo, coloc = 0.0, 0.0
    try:
        cat = json.loads((RAIZ / "CONFIG" / "catalogo_servicios.json")
                         .read_text(encoding="utf-8"))
        for p in cat.get("productos", []):
            if "mínimo" in str(p.get("nombre", "")).lower():
                minimo = float(p["precio"])
        coloc = float(cat.get("dtf", {}).get("colocacion_planchado") or 0)
    except Exception:
        pass
    return minimo, coloc


def precio_de_lista(ancho_cm: float, alto_cm: float,
                    colocar: bool = False) -> dict:
    """Lo que ESE trabajo cuesta según su propia lista, no según un modelo.

    Entre dos peldaños se interpola por área —que es como lo hace él a ojo—
    y nunca se baja del mínimo. Se dice de qué peldaños salió el número, para
    que pueda discutirlo o corregirlo.
    """
    esc = _escalera()
    if not esc:
        return {"status": "SIN_LISTA"}
    area = ancho_cm * alto_cm
    minimo, coloc = _minimo_y_colocacion()

    if area <= esc[0]["area"]:
        base, apoyo = esc[0]["precio"], [esc[0]["nombre"]]
    elif area >= esc[-1]["area"]:
        # más grande que el peldaño más alto: se sigue la última pendiente
        a, b = esc[-2], esc[-1]
        pend = (b["precio"] - a["precio"]) / (b["area"] - a["area"])
        base = b["precio"] + (area - b["area"]) * pend
        apoyo = [a["nombre"], b["nombre"]]
    else:
        for a, b in zip(esc, esc[1:]):
            if a["area"] <= area <= b["area"]:
                k = (area - a["area"]) / (b["area"] - a["area"])
                base = a["precio"] + k * (b["precio"] - a["precio"])
                apoyo = [a["nombre"], b["nombre"]]
                break

    base = max(base, minimo)
    total = base + (coloc if colocar else 0.0)
    return {"status": "OK", "area_cm2": round(area, 1),
            "corte": round(base, 2), "colocacion": coloc if colocar else 0.0,
            "precio": round(total, 2), "minimo": minimo,
            "apoyado_en": apoyo}


def precio_de_trabajo(piezas: list, colocar: bool = False) -> dict:
    """Varias piezas en UN trabajo: se suman las ÁREAS, no los precios.

    SALIÓ DE SU PROPIO EJEMPLO GUARDADO, no de una teoría. En el catálogo está
    anotado un trabajo real: *«letras 10×28 cm + números 15×10 cm, solo
    recorte — $95»*.

        cobrando pieza por pieza:  $74 + $57  =  $131
        sumando las áreas:         430 cm²    =  $94.20   ← lo que cobró

    La escalera ya trae la economía de escala adentro; aplicarla dos veces
    sobrecobra un 38% y tumba la venta. `piezas` va como [(ancho, alto), ...]
    en centímetros.
    """
    if not piezas:
        return {"status": "SIN_PIEZAS"}
    area = sum(float(a) * float(b) for a, b in piezas)
    # se cotiza como un solo rectángulo de esa área
    lado = area ** 0.5
    r = precio_de_lista(lado, lado, colocar)
    if r.get("status") == "OK":
        r["piezas"] = [f"{a:g}×{b:g}" for a, b in piezas]
        r["regla"] = "áreas sumadas (su ejemplo real: 10×28 + 15×10 = $95)"
    return r


def cotizar(ancho_cm: float, alto_cm: float, contornos: int = 1,
            largo_corte_cm: float = 0.0, textil: bool = False,
            piezas: int = 1, colores: int = 1, tela: str = "algodon",
            instalacion: bool = True) -> dict:
    """Qué cuesta cortar (y planchar, y pegar) ese trabajo.

    ancho/alto en cm es el ÁREA QUE OCUPA EL DISEÑO, no la hoja: el vinil se
    cobra por lo que se consume del rollo.
    """
    d = _cargar()
    tipo = "textil" if textil else "recorte"
    c = config(tipo)
    if c["faltan"]:
        return {"status": "FALTAN_PRECIOS", "faltan": c["faltan"]}

    ancho_rollo = d[f"ancho_rollo_{tipo}_cm"]
    precio_metro = d[f"precio_metro_{tipo}"]
    hora = d["precio_hora_mano_obra"]
    minuto = hora / 60.0

    if ancho_cm > ancho_rollo and alto_cm > ancho_rollo:
        return {"status": "NO_CABE_EN_EL_ROLLO",
                "detalle": (f"{ancho_cm}×{alto_cm} cm no entra en un rollo de "
                            f"{ancho_rollo} cm. Hay que partir el diseño o "
                            f"conseguir rollo más ancho.")}
    # se acuesta el diseño si así consume menos rollo
    largo_rollo_cm = min(alto_cm, ancho_cm) if max(ancho_cm, alto_cm) <= \
        ancho_rollo else (alto_cm if ancho_cm <= ancho_rollo else ancho_cm)
    largo_rollo_cm *= (1 + d["desperdicio_pct"] / 100.0)

    dm2 = (ancho_cm * alto_cm) / 100.0

    # ── MATERIAL
    material = largo_rollo_cm / 100.0 * precio_metro * piezas * colores
    if not textil:
        material += largo_rollo_cm / 100.0 * d["precio_metro_transfer"] * piezas

    # ── CORTE (poco, pero se cuenta)
    if not largo_corte_cm:
        # sin el archivo se estima por el perímetro del área; es un piso, y
        # se avisa que lo es
        largo_corte_cm = 2 * (ancho_cm + alto_cm) * max(1, contornos) * 0.4
    min_corte = d["minutos_montaje"] + (
        largo_corte_cm / d["velocidad_corte_cm_min"]) * piezas * colores
    corte = min_corte * minuto

    # ── DESPICADO: el costo de verdad
    min_despique = ((contornos * d["segundos_por_contorno"]
                     + dm2 * d["segundos_por_dm2"]) / 60.0) * piezas * colores
    despique = min_despique * minuto

    # ── PLANCHADO (solo textil)
    min_plancha = 0.0
    if textil:
        p = PLANCHADO.get(tela, PLANCHADO["algodon"])
        seg = d["minutos_preparar_prenda"] * 60
        seg += p["seg"]                                  # la planchada final
        seg += d["segundos_tack_press"] * max(0, colores - 1)
        min_plancha = (seg / 60.0) * piezas
    plancha = min_plancha * minuto

    # ── INSTALACIÓN
    min_inst = 0.0
    if instalacion and not textil:
        min_inst = (d["minutos_instalar_base"]
                    + dm2 * d["minutos_instalar_por_dm2"]) * piezas
    inst = min_inst * minuto

    costo = material + corte + despique + plancha + inst
    precio = costo * (1 + d["margen_pct"] / 100.0)

    return {
        "status": "OK", "tipo": tipo, "piezas": piezas, "colores": colores,
        "area": f"{ancho_cm:g} × {alto_cm:g} cm", "contornos": contornos,
        "rollo_cm": round(largo_rollo_cm, 1), "ancho_rollo": ancho_rollo,
        "desglose": {
            "material": round(material, 2),
            "corte": round(corte, 2),
            "despicado": round(despique, 2),
            "planchado": round(plancha, 2),
            "instalacion": round(inst, 2),
        },
        "minutos": {
            "corte": round(min_corte, 1), "despicado": round(min_despique, 1),
            "planchado": round(min_plancha, 1), "instalacion": round(min_inst, 1),
        },
        "minutos_total": round(min_corte + min_despique + min_plancha
                               + min_inst, 1),
        "costo": round(costo, 2), "precio": round(precio, 2),
        "precio_pieza": round(precio / max(1, piezas), 2),
        "margen_pct": d["margen_pct"],
        "estimado_el_corte": largo_corte_cm and True,
        "planchado_receta": PLANCHADO.get(tela) if textil else None,
    }


def tarifa_implicita(precio_cobrado: float, ancho_cm: float, alto_cm: float,
                     contornos: int = 1, textil: bool = False,
                     piezas: int = 1, colores: int = 1,
                     tela: str = "algodon", instalacion: bool = True) -> dict:
    """De un trabajo YA COBRADO saca a cuánto le salió la hora.

    Es mejor que preguntarle su tarifa: él no la tiene en un número, la tiene
    en la mano. Le cobró $150 a un cliente por poner unas letras y de ahí sale
    lo que vale su hora de verdad, con su margen puesto. Así los trabajos que
    siguen se cotizan con SU precio, no con uno de manual.
    """
    d = _cargar()
    # se cotiza con una tarifa cualquiera para separar material de manos: el
    # material no depende de la hora, los minutos tampoco.
    guardado = d.get("precio_hora_mano_obra")
    try:
        _tmp = dict(guardado=guardado)
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        prev = json.loads(CONFIG.read_text(encoding="utf-8")) \
            if CONFIG.exists() else {}
        CONFIG.write_text(json.dumps({**prev, "precio_hora_mano_obra": 60.0},
                                     ensure_ascii=False, indent=1),
                          encoding="utf-8")
        r = cotizar(ancho_cm, alto_cm, contornos, 0.0, textil, piezas,
                    colores, tela, instalacion)
    finally:
        prev.pop("precio_hora_mano_obra", None)
        if guardado:
            prev["precio_hora_mano_obra"] = guardado
        CONFIG.write_text(json.dumps(prev, ensure_ascii=False, indent=1),
                          encoding="utf-8")

    if r.get("status") != "OK":
        return r
    margen = 1 + r["margen_pct"] / 100.0
    material = r["desglose"]["material"]
    minutos = r["minutos_total"]
    # precio = (material + minutos·tarifa/60) · margen
    mano = precio_cobrado / margen - material
    if minutos <= 0 or mano <= 0:
        return {"status": "NO_SALE", "detalle": (
            f"Con ${precio_cobrado:.2f} no alcanza ni el material "
            f"(${material:.2f} + margen). Ese trabajo se cobró por debajo.")}
    return {"status": "OK", "precio_cobrado": precio_cobrado,
            "material": round(material, 2), "minutos": minutos,
            "mano_de_obra": round(mano, 2),
            "por_minuto": round(mano / minutos, 2),
            "por_hora": round(mano / minutos * 60, 2),
            "margen_pct": r["margen_pct"], "detalle_minutos": r["minutos"]}


def _texto(r: dict) -> str:
    s = r.get("status")
    if s == "FALTAN_PRECIOS":
        t = ["No te doy un número inventado. Me faltan estos datos "
             "—captúralos una vez en el panel y ya queda:\n"]
        for k, p in r["faltan"].items():
            t.append(f"   • **{k}** — {p}")
        return "\n".join(t)
    if s != "OK":
        return f"No se pudo: {r.get('detalle', s)}"

    d, m = r["desglose"], r["minutos"]
    t = [f"✂️ **Corte de plotter · vinil {r['tipo']}** — {r['area']}",
         f"   {r['piezas']} pieza(s) · {r['colores']} color(es) · "
         f"{r['contornos']} contornos",
         f"   consume **{r['rollo_cm']} cm** de rollo de {r['ancho_rollo']} cm\n",
         "   ```",
         f"   material      $ {d['material']:>8.2f}",
         f"   corte         $ {d['corte']:>8.2f}   ({m['corte']} min)",
         f"   despicado     $ {d['despicado']:>8.2f}   ({m['despicado']} min)"]
    if d["planchado"]:
        t.append(f"   planchado     $ {d['planchado']:>8.2f}   "
                 f"({m['planchado']} min)")
    if d["instalacion"]:
        t.append(f"   instalación   $ {d['instalacion']:>8.2f}   "
                 f"({m['instalacion']} min)")
    t += [f"   {'─'*30}",
          f"   costo         $ {r['costo']:>8.2f}",
          f"   **PRECIO      $ {r['precio']:>8.2f}**  (margen {r['margen_pct']}%)",
          "   ```"]
    if r["piezas"] > 1:
        t.append(f"   ${r['precio_pieza']:.2f} por pieza")
    t.append(f"\n   ⏱️ {r['minutos_total']} minutos de trabajo en total")

    if r.get("planchado_receta"):
        p = r["planchado_receta"]
        t.append(f"\n🔥 **Planchado:** {p['temp']} °C · {p['seg']} s · "
                 f"pelado {p['pelado']}")
        if p.get("ojo"):
            t.append(f"   ⚠️ {p['ojo']}")
        if r["colores"] > 1:
            t.append(f"   Son {r['colores']} capas: cada una lleva un tack "
                     "press de 3 s, y solo la última va la planchada completa.")
    t.append("\n_El despicado es el que manda el precio, no el tamaño. "
             "Si el diseño trae mucho detalle fino, sube._")
    return "\n".join(t)


def main() -> int:
    _consola_utf8()
    a = sys.argv[1:]
    if "--config" in a:
        c = config()
        print(json.dumps(c, ensure_ascii=False, indent=1))
        return 0
    an, al, cont, largo = 30.0, 20.0, 1, 0.0
    piezas, colores, tela = 1, 1, "algodon"
    i = 0
    while i < len(a):
        if a[i] == "--area" and i + 1 < len(a):
            p = a[i + 1].lower().split("x"); an, al = float(p[0]), float(p[1]); i += 1
        elif a[i] == "--contornos" and i + 1 < len(a):
            cont = int(a[i + 1]); i += 1
        elif a[i] == "--largo" and i + 1 < len(a):
            largo = float(a[i + 1]); i += 1
        elif a[i] == "--piezas" and i + 1 < len(a):
            piezas = int(a[i + 1]); i += 1
        elif a[i] == "--colores" and i + 1 < len(a):
            colores = int(a[i + 1]); i += 1
        elif a[i] == "--tela" and i + 1 < len(a):
            tela = a[i + 1]; i += 1
        i += 1
    print(_texto(cotizar(an, al, cont, largo, "--textil" in a, piezas,
                         colores, tela)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
