# -*- coding: utf-8 -*-
"""AURORA · ESTRATEGA DE YOUTUBE SHORTS

Anuar pidió el 2026-08-18 convertir en app un prompt que circula como *"haz
dinero en YouTube Shorts"*: analizar su perfil, sacar los 5 mejores nichos por
CPM, decir cuál conviene con cero inversión, y armar el plan de 30 días.

**La verdad que esta herramienta dice y el prompt original no.** Shorts NO
paga por CPM como los videos largos. Paga por un fondo repartido entre todos
los creadores, y el RPM real anda en **centavos de dólar por cada mil
vistas** — no en dólares. Con audiencia mexicana son de 1 a 3 centavos por
mil. Eso significa que **un millón de vistas puede pagar 20 dólares**.

Por eso esta app calcula **dos ingresos, no uno**:

  1. **AdSense** — lo que YouTube te deposita. Casi siempre decepciona, y es
     mejor verlo antes de dejar el taller por grabar.
  2. **Clientes captados** — lo que de verdad deja un canal cuando ya tienes
     un oficio: la gente te ve trabajando y te busca. Un solo cliente de
     retrofit deja más que un mes de AdSense.

Los números de CPM y RPM viven en `CONFIG/nichos_shorts.json`, **con la fecha
en que se capturaron**, porque cambian. El archivo manda sobre el código.

Correr:
    python MARKETING/estratega_shorts.py --nichos
    python MARKETING/estratega_shorts.py --perfil --edad 45 --temas "corte laser, autos" --horas 5 --inversion 0
    python MARKETING/estratega_shorts.py --cuanto --vistas 1000000 --nicho automotriz
    python MARKETING/estratega_shorts.py --plan automotriz --horas 5
"""
from __future__ import annotations
import io
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NICHOS_JSON = RAIZ / "CONFIG" / "nichos_shorts.json"
DOLAR = 18.5          # pesos por dólar; se puede cambiar en el JSON

# ── REQUISITOS REALES PARA MONETIZAR (capturado 2026-08-18) ─────────────
# Son la puerta de entrada y casi nadie los lee antes de empezar. Si no se
# cumplen los dos en la misma ventana de 90 días, no hay pago.
REQUISITOS = {
    "shorts": {"suscriptores": 1000, "vistas_90_dias": 10_000_000,
               "que_es": "10 millones de vistas VÁLIDAS de Shorts en 90 días"},
    "largos": {"suscriptores": 1000, "horas_12_meses": 4000,
               "que_es": "4,000 horas de reproducción en videos largos en 12 meses"},
    "basico": {"suscriptores": 500, "vistas_90_dias": 3_000_000,
               "que_es": "nivel básico: 500 subs + 3M vistas de Shorts en 90 "
                         "días — da propinas y membresías, NO anuncios"},
}

# ── NICHOS ──────────────────────────────────────────────────────────────
# `rpm_mx` y `rpm_us` son **dólares por cada MIL vistas de Shorts**, no CPM de
# video largo. Son rangos observados, no una promesa: dependen del país de
# quien te ve, de la época del año y de la duración.
#
# `saturacion` 1 a 5: 5 es un nicho donde ya hay miles de canales iguales.
# `barrera`: qué necesitas de verdad para hacerlo bien.
NICHOS_BASE = [
    {"nicho": "Finanzas personales e inversión", "rpm_mx": [0.03, 0.09],
     "rpm_us": [0.12, 0.40], "saturacion": 5,
     "barrera": "Hay que saber de verdad o se nota. Y YouTube castiga el "
                "consejo financiero irresponsable.",
     "necesitas": ["conocimiento real", "guion cuidado"],
     "temas": ["finanzas", "inversion", "dinero", "ahorro", "credito",
               "negocio", "emprendimiento", "bolsa", "cripto"]},
    {"nicho": "Tecnología, software y herramientas de IA",
     "rpm_mx": [0.02, 0.07], "rpm_us": [0.10, 0.30], "saturacion": 5,
     "barrera": "Se renueva cada semana; si no publicas seguido, te apagas.",
     "necesitas": ["computadora", "grabar pantalla"],
     "temas": ["tecnologia", "software", "ia", "inteligencia artificial",
               "computacion", "apps", "programacion", "gadgets"]},
    {"nicho": "Automotriz y modificación de autos", "rpm_mx": [0.02, 0.06],
     "rpm_us": [0.08, 0.25], "saturacion": 3,
     "barrera": "Necesitas taller y autos de verdad. Esa es justo la razón "
                "por la que está menos saturado que los demás.",
     "necesitas": ["taller", "autos", "oficio"],
     "temas": ["autos", "carros", "automotriz", "faros", "retrofit",
               "mecanica", "tuning", "vehiculos", "iluminacion"]},
    {"nicho": "Oficios y trabajos manuales (satisfying)",
     "rpm_mx": [0.01, 0.04], "rpm_us": [0.05, 0.18], "saturacion": 2,
     "barrera": "Necesitas el taller y la máquina. Poca gente lo tiene, y por "
                "eso es de los menos saturados que existen.",
     "necesitas": ["taller", "maquinaria", "oficio"],
     "temas": ["laser", "corte", "carpinteria", "herreria", "manualidades",
               "artesania", "taller", "grabado", "sublimacion", "cnc",
               "oficio", "hazlo tu mismo", "diy"]},
    {"nicho": "Salud, fitness y bienestar", "rpm_mx": [0.02, 0.06],
     "rpm_us": [0.08, 0.22], "saturacion": 5,
     "barrera": "YouTube exige mucho con los consejos de salud; sin "
                "credencial te limita el alcance.",
     "necesitas": ["cuerpo o credencial"],
     "temas": ["salud", "fitness", "ejercicio", "gym", "nutricion", "dieta",
               "bienestar"]},
    {"nicho": "Bienes raíces y construcción", "rpm_mx": [0.03, 0.08],
     "rpm_us": [0.10, 0.32], "saturacion": 3,
     "barrera": "Necesitas acceso a propiedades u obra real.",
     "necesitas": ["propiedades", "obra"],
     "temas": ["bienes raices", "casas", "construccion", "arquitectura",
               "inmobiliaria", "remodelacion"]},
    {"nicho": "Cocina y recetas rápidas", "rpm_mx": [0.01, 0.03],
     "rpm_us": [0.04, 0.12], "saturacion": 5,
     "barrera": "Ninguna, y por eso está lleno. Compites contra millones.",
     "necesitas": ["cocina"],
     "temas": ["cocina", "recetas", "comida", "postres", "reposteria"]},
    {"nicho": "Comedia y entretenimiento", "rpm_mx": [0.005, 0.02],
     "rpm_us": [0.03, 0.10], "saturacion": 5,
     "barrera": "El RPM más bajo que hay. Se necesita volumen enorme para "
                "que pague algo.",
     "necesitas": ["gracia"],
     "temas": ["comedia", "humor", "entretenimiento", "memes", "bromas"]},
    {"nicho": "Educación y tutoriales", "rpm_mx": [0.02, 0.05],
     "rpm_us": [0.08, 0.20], "saturacion": 4,
     "barrera": "Hay que dominar el tema y explicarlo claro en 40 segundos.",
     "necesitas": ["dominio del tema"],
     "temas": ["educacion", "tutorial", "aprender", "escuela", "clases",
               "matematicas", "idiomas", "ingles"]},
    {"nicho": "Mascotas y animales", "rpm_mx": [0.01, 0.03],
     "rpm_us": [0.04, 0.14], "saturacion": 5,
     "barrera": "Ninguna. Es el más fácil de empezar y el que menos paga.",
     "necesitas": ["mascota"],
     "temas": ["mascotas", "perros", "gatos", "animales", "veterinaria"]},
]


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _limpio(t) -> str:
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def nichos() -> list:
    """Los nichos con sus números. El JSON gana; si no hay, la tabla base."""
    try:
        if NICHOS_JSON.exists():
            d = json.loads(NICHOS_JSON.read_text(encoding="utf-8"))
            if d.get("nichos"):
                return d["nichos"]
    except Exception:
        pass
    return NICHOS_BASE


def guardar_nichos(lista=None) -> Path:
    """Deja la tabla en disco para que se pueda corregir sin tocar código."""
    NICHOS_JSON.parent.mkdir(parents=True, exist_ok=True)
    NICHOS_JSON.write_text(json.dumps({
        "capturado": date.today().isoformat(),
        "dolar": DOLAR,
        "aviso": ("rpm_mx y rpm_us son DÓLARES POR CADA MIL VISTAS de Shorts, "
                  "no CPM de video largo. Cambian por temporada y por el país "
                  "de quien te ve. Ajusta con lo que veas en tu propio "
                  "YouTube Studio: ese es el único dato que no miente."),
        "nichos": lista or NICHOS_BASE},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return NICHOS_JSON


# ── CUÁNTO PAGA DE VERDAD ───────────────────────────────────────────────
def cuanto_paga(vistas: int, nicho: str = "", pct_extranjero: float = 10.0,
                dolar: float = DOLAR) -> dict:
    """Lo que deja AdSense por esas vistas. Es la cifra que despierta a la gente.

    `pct_extranjero` es qué tanto de tu público está en Estados Unidos o
    Europa. Importa muchísimo: la misma vista vale de 5 a 10 veces más si
    viene de allá. Con contenido en español, lo normal es 5% a 15%.
    """
    n = _buscar_nicho(nicho) or nichos()[3]
    mx = sum(n["rpm_mx"]) / 2
    us = sum(n["rpm_us"]) / 2
    p = max(0.0, min(100.0, float(pct_extranjero))) / 100
    rpm = mx * (1 - p) + us * p
    usd = vistas / 1000 * rpm
    return {"status": "OK", "nicho": n["nicho"], "vistas": int(vistas),
            "rpm_usado": round(rpm, 4), "rpm_mx": mx, "rpm_us": us,
            "pct_extranjero": pct_extranjero,
            "usd": round(usd, 2), "pesos": round(usd * dolar, 2),
            "bajo": round(vistas / 1000 * (n["rpm_mx"][0] * (1 - p)
                                           + n["rpm_us"][0] * p) * dolar, 2),
            "alto": round(vistas / 1000 * (n["rpm_mx"][1] * (1 - p)
                                           + n["rpm_us"][1] * p) * dolar, 2)}


def _buscar_nicho(nombre: str):
    if not nombre:
        return None
    t = _limpio(nombre)
    for n in nichos():
        if t in _limpio(n["nicho"]) or _limpio(n["nicho"]) in t:
            return n
        if any(t == _limpio(x) or t in _limpio(x) for x in n.get("temas", [])):
            return n
    return None


def cuanto_falta(subs: int = 0, vistas_90: int = 0) -> dict:
    """Qué tan lejos estás de que YouTube te pague. Sin adornos."""
    r = {"status": "OK", "subs": int(subs), "vistas_90": int(vistas_90),
         "puertas": []}
    for clave, req in REQUISITOS.items():
        falta_s = max(0, req["suscriptores"] - int(subs))
        meta_v = req.get("vistas_90_dias")
        falta_v = max(0, meta_v - int(vistas_90)) if meta_v else None
        r["puertas"].append({
            "cual": clave, "que_es": req["que_es"],
            "faltan_subs": falta_s, "faltan_vistas": falta_v,
            "abierta": falta_s == 0 and (falta_v == 0 if meta_v else False)})
    return r


# ── EL ANÁLISIS DEL PERFIL ──────────────────────────────────────────────
def analizar(edad=None, temas="", horas_semana: float = 0,
             inversion: float = 0, subs: int = 0, vistas_90: int = 0,
             pct_extranjero: float = 10.0, videos_ya_grabados: int = 0,
             tiene_oficio: str = "") -> dict:
    """El análisis completo: qué nicho te toca y qué esperar de verdad.

    Lo que lo separa de una respuesta genérica es que **cruza tus temas con
    lo que de verdad puedes producir**. De nada sirve que finanzas pague más
    si no sabes de finanzas: el canal muere en tres semanas.
    """
    mis = [_limpio(t) for t in str(temas).replace(",", " ").split() if t]
    horas = float(horas_semana or 0)

    puntuados = []
    for n in nichos():
        # Compatibilidad: cuántos de tus temas caen en ese nicho.
        toques = sum(1 for t in mis
                     for x in n.get("temas", []) if t and t in _limpio(x))
        compat = min(100, toques * 28)
        mx = sum(n["rpm_mx"]) / 2
        us = sum(n["rpm_us"]) / 2
        p = max(0.0, min(100.0, pct_extranjero)) / 100
        rpm = mx * (1 - p) + us * p
        # Menos saturación es mejor: en un nicho lleno, un canal nuevo no se
        # ve por bueno que sea.
        aire = (6 - n["saturacion"]) * 20
        # El puntaje pesa MÁS la compatibilidad que el dinero, a propósito:
        # el nicho que mejor paga no sirve si no lo puedes sostener.
        puntos = compat * 0.45 + min(100, rpm * 400) * 0.30 + aire * 0.25
        puntuados.append({**n, "compatibilidad": compat, "rpm": round(rpm, 4),
                          "aire": aire, "puntos": round(puntos, 1),
                          "con_10k_subs_pesos": round(
                              cuanto_paga(300_000, n["nicho"],
                                          pct_extranjero)["pesos"], 0)})
    puntuados.sort(key=lambda x: -x["puntos"])
    top = puntuados[:5]

    # ¿Le queda el traje a alguno?
    mejor = top[0] if top else None
    hay_compatible = any(n["compatibilidad"] >= 28 for n in top)

    avisos = []
    if horas and horas < 3:
        avisos.append(
            f"Con {horas:g} horas a la semana no alcanza. Un canal de Shorts "
            f"que crece publica de 1 a 2 diarios; eso son 5 a 8 horas "
            f"semanales mínimo, contando grabar, cortar y subir.")
    if not hay_compatible:
        avisos.append(
            "Ninguno de tus temas cae claro en un nicho de los que pagan "
            "bien. Antes de arrancar, define de qué vas a hablar 200 veces "
            "seguidas: esa es la prueba de si aguantas el nicho.")
    if videos_ya_grabados >= 50:
        avisos.append(
            f"Ya tienes {videos_ya_grabados} videos grabados. Eso te ahorra "
            f"meses: la razón #1 por la que mueren los canales es quedarse "
            f"sin material, y tú arrancas con banco.")

    falta = cuanto_falta(subs, vistas_90)
    return {"status": "OK", "edad": edad, "horas_semana": horas,
            "inversion": inversion, "temas": temas,
            "top": top, "mejor": mejor, "hay_compatible": hay_compatible,
            "avisos": avisos, "requisitos": falta,
            "por_que_mueren": POR_QUE_MUEREN}


# Las tres razones técnicas, y ninguna es «no fui constante». Esa es la
# consecuencia, no la causa.
POR_QUE_MUEREN = [
    {"razon": "El primer segundo no retiene",
     "detalle": "Shorts decide en los primeros 1 a 2 segundos si te sigue "
                "mostrando. Un video que empieza con logo, saludo o "
                "«qué onda, bienvenidos» ya perdió. La retención de los "
                "primeros 3 segundos es la métrica que más pesa.",
     "como_evitarla": "Arranca con el resultado o con el momento más fuerte. "
                      "Nada de intro. El saludo va después del gancho, si "
                      "acaso."},
    {"razon": "El canal habla de todo",
     "detalle": "El algoritmo necesita saber a quién enseñarte. Si un día "
                "subes autos y otro recetas, no encuentra público y deja de "
                "repartir. Un canal revuelto se apaga aunque cada video esté "
                "bueno.",
     "como_evitarla": "Un solo tema durante los primeros 100 videos. "
                      "Aburre a ti, no al algoritmo."},
    {"razon": "Se persiguen las vistas y no la puerta de monetización",
     "detalle": "Se necesitan 1,000 suscriptores **y** 10 millones de vistas "
                "de Shorts en 90 días, en la misma ventana. Un video viral "
                "suelto no sirve: si las vistas llegan repartidas en dos "
                "años, nunca se juntan los 90 días.",
     "como_evitarla": "Publica diario y sostenido. Vale más 90 días parejos "
                      "que un viral aislado."},
]


def plan_30_dias(nicho: str = "", horas_semana: float = 5,
                 videos_ya: int = 0) -> dict:
    """El plan mínimo viable del primer mes. Concreto, no motivacional."""
    n = _buscar_nicho(nicho) or nichos()[3]
    # A 20 minutos por Short ya editado, que es lo real cuando ya tienes el
    # material grabado. Desde cero son 45 a 60 minutos.
    minutos = 20 if videos_ya >= 30 else 45
    al_dia = max(1, int(float(horas_semana) * 60 / 7 / minutos))
    return {"status": "OK", "nicho": n["nicho"],
            "shorts_al_dia": al_dia, "shorts_al_mes": al_dia * 30,
            "minutos_por_short": minutos,
            "duracion": "de 20 a 35 segundos — abajo de 40 el porcentaje de "
                        "video visto sube, y ese porcentaje es lo que hace "
                        "que te sigan repartiendo",
            "estructura": [
                "0–2 s · el gancho: el resultado final, el corte más limpio, "
                "el antes y después. Sin logo, sin saludo.",
                "2–8 s · el problema o la pregunta que hace quedarse.",
                "8–25 s · el proceso, cortado rápido, sin tiempos muertos.",
                "25–35 s · el remate, y un motivo para volver a verlo "
                "(un detalle que se escapó a la primera).",
                "Texto en pantalla SIEMPRE: mucha gente lo ve sin sonido."],
            "publicacion": f"{al_dia} al día, todos los días, a la misma hora. "
                           f"La constancia pesa más que la calidad de "
                           f"cualquier video suelto.",
            "primeros_pasos": [
                "Define el tema único del canal y no lo muevas en 100 videos.",
                "Graba en vertical 9:16 desde el principio: recortar "
                "horizontal se ve mal y baja la retención.",
                "Los primeros 10 Shorts son de práctica. Súbelos igual, pero "
                "no midas nada con ellos.",
                "Revisa a los 30 días **la retención de los primeros 3 "
                "segundos**, no las vistas. Esa métrica es la que te dice si "
                "vas o no vas."]}


def como_negocio(vistas_mes: int, nicho: str = "", pct_extranjero: float = 10.0,
                 clientes_por_millon: float = 3.0, ticket: float = 2500.0,
                 dolar: float = DOLAR) -> dict:
    """Los dos ingresos, lado a lado. Es la comparación que cambia decisiones.

    `clientes_por_millon` — cuántos clientes te llegan por cada millón de
    vistas. Con público local y un oficio que se ve en cámara, de 2 a 5 es
    realista; con público disperso, menos de 1.
    """
    ads = cuanto_paga(vistas_mes, nicho, pct_extranjero, dolar)
    clientes = vistas_mes / 1_000_000 * float(clientes_por_millon)
    por_clientes = clientes * float(ticket)
    r = {"status": "OK", "vistas_mes": int(vistas_mes),
         "adsense_pesos": ads["pesos"], "rpm_usado": ads["rpm_usado"],
         "clientes_estimados": round(clientes, 1),
         "ticket": ticket, "por_clientes_pesos": round(por_clientes, 2),
         "total": round(ads["pesos"] + por_clientes, 2)}
    if por_clientes > ads["pesos"] * 3:
        r["veredicto"] = "EL CANAL ES PARA VENDER, NO PARA COBRAR ANUNCIOS"
        r["explicacion"] = (
            f"Con {vistas_mes:,} vistas al mes, YouTube te paga "
            f"${ads['pesos']:,.0f} y los clientes que llegan te dejan "
            f"${por_clientes:,.0f} — **{por_clientes / max(1, ads['pesos']):.0f} "
            f"veces más**. Deja de perseguir la monetización: persigue que te "
            f"vean los que te pueden comprar.")
    elif ads["pesos"] > por_clientes:
        r["veredicto"] = "ADSENSE MANDA"
        r["explicacion"] = ("En este caso el anuncio deja más que los "
                            "clientes. Ojo: eso normalmente significa que "
                            "estás calculando pocos clientes por vista.")
    else:
        r["veredicto"] = "VAN PAREJOS"
        r["explicacion"] = ("Los dos aportan parecido. Sube el ticket o "
                            "afina a quién le hablas y los clientes ganan.")
    return r


# ── TEXTOS ──────────────────────────────────────────────────────────────
def _t_analisis(r: dict) -> str:
    t = "🎬 **Los 5 nichos que te tocan**\n\n"
    t += (f"{'NICHO':<40}{'COMPAT':>7}{'RPM USD':>9}{'SAT':>5}"
          f"{'300K VISTAS':>13}\n")
    for n in r["top"]:
        t += (f"{n['nicho'][:39]:<40}{n['compatibilidad']:>6}%"
              f"{n['rpm']:>9.4f}{n['saturacion']:>5}"
              f"{'$' + format(int(n['con_10k_subs_pesos']), ','):>13}\n")
    if r["mejor"]:
        m = r["mejor"]
        t += (f"\n👉 **El que te conviene hoy: {m['nicho']}**\n"
              f"   Compatibilidad {m['compatibilidad']}% · saturación "
              f"{m['saturacion']} de 5 · RPM ${m['rpm']:.4f} por mil vistas\n"
              f"   Barrera real: {m['barrera']}\n")
    for a in r["avisos"]:
        t += f"\n⚠️ {a}\n"
    t += "\n🚪 **Para que YouTube te pague:**\n"
    for p in r["requisitos"]["puertas"]:
        t += f"   · {p['que_es']}\n"
        if p["faltan_subs"] or p["faltan_vistas"]:
            t += (f"     te faltan {p['faltan_subs']:,} subs"
                  + (f" y {p['faltan_vistas']:,} vistas"
                     if p["faltan_vistas"] else "") + "\n")
    t += "\n💀 **Por qué mueren el 90% de los canales nuevos:**\n"
    for i, m in enumerate(r["por_que_mueren"], 1):
        t += (f"\n   {i}. **{m['razon']}**\n      {m['detalle']}\n"
              f"      → {m['como_evitarla']}\n")
    return t


def _t_plan(p: dict) -> str:
    t = (f"📅 **Plan de 30 días — {p['nicho']}**\n\n"
         f"   {p['shorts_al_dia']} Shorts al día = {p['shorts_al_mes']} al mes "
         f"(≈{p['minutos_por_short']} min cada uno)\n"
         f"   Duración: {p['duracion']}\n\n"
         f"   **La estructura que el algoritmo premia:**\n")
    for e in p["estructura"]:
        t += f"      · {e}\n"
    t += f"\n   **Publicación:** {p['publicacion']}\n\n   **Primeros pasos:**\n"
    for e in p["primeros_pasos"]:
        t += f"      · {e}\n"
    return t


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
        try:
            return float(str(_op(n, d)).replace(",", ""))
        except (TypeError, ValueError):
            return d

    if "--nichos" in a:
        print(f"{'NICHO':<40}{'RPM MX':>16}{'RPM US':>16}{'SAT':>5}")
        for n in nichos():
            print(f"{n['nicho'][:39]:<40}"
                  f"{n['rpm_mx'][0]:>7.3f}-{n['rpm_mx'][1]:<8.3f}"
                  f"{n['rpm_us'][0]:>7.3f}-{n['rpm_us'][1]:<8.3f}"
                  f"{n['saturacion']:>5}")
        print("\nRPM = dólares por cada MIL vistas de Shorts. No es CPM de "
              "video largo.")
        return 0
    if "--cuanto" in a:
        r = cuanto_paga(int(_f("vistas", 1_000_000)), _op("nicho", ""),
                        _f("extranjero", 10))
        print(f"💵 {r['vistas']:,} vistas en «{r['nicho']}»\n"
              f"   RPM usado: ${r['rpm_usado']:.4f} USD por mil vistas "
              f"({r['pct_extranjero']:g}% público extranjero)\n"
              f"   **${r['pesos']:,.2f} pesos**  (rango real: "
              f"${r['bajo']:,.0f} a ${r['alto']:,.0f})")
        return 0
    if "--negocio" in a:
        r = como_negocio(int(_f("vistas", 500_000)), _op("nicho", ""),
                         _f("extranjero", 10), _f("clientes", 3),
                         _f("ticket", 2500))
        print(f"📊 Con {r['vistas_mes']:,} vistas al mes:\n"
              f"   AdSense:            ${r['adsense_pesos']:>12,.2f}\n"
              f"   Clientes ({r['clientes_estimados']:g}):    "
              f"${r['por_clientes_pesos']:>12,.2f}\n"
              f"   ─────────────────────────────────\n"
              f"   Total:              ${r['total']:>12,.2f}\n\n"
              f"   **{r['veredicto']}**\n   {r['explicacion']}")
        return 0
    if _op("plan"):
        print(_t_plan(plan_30_dias(_op("plan"), _f("horas", 5),
                                   int(_f("videos", 0)))))
        return 0
    if "--perfil" in a:
        print(_t_analisis(analizar(
            _op("edad"), _op("temas", ""), _f("horas", 0), _f("inversion", 0),
            int(_f("subs", 0)), int(_f("vistas90", 0)), _f("extranjero", 10),
            int(_f("videos", 0)))))
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
