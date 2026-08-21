# -*- coding: utf-8 -*-
"""AURORA · BUSCADOR DE CLIENTES REALES (por zona y por nicho)

Anuar lo pidió el 2026-08-16, estando en números rojos: *"buscador de posibles
clientes reales por área y multinicho, así podré incursionar en ventas"*, y
después *"se le puede integrar un perfilador de clientes… al tipo de perfil
que tenga cada empresa basado en lo que este tenga en la web"*.

**De dónde salen los clientes.** Del **DENUE del INEGI**: el censo oficial de
todos los negocios de México. Se midió el 2026-08-16 — Jalisco trae **401,813
negocios**, y **164,203 con teléfono**. Descarga libre, sin token, sin
depender de que ninguna plataforma nos deje entrar. Es el dato más duro que
existe para vender aquí, y es gratis.

Se probaron antes, y se descartaron por medición, no por corazonada:
  · OpenStreetMap → 400 negocios en Guadalajara, **4 con teléfono**.
  · Mercado Libre / Amazon → bloquean el raspado.
  · Google Maps → sin API de paga no entrega datos.

**El perfilador.** Un negocio no se atiende igual si es un changarro de 3
personas que si es una empresa de 60. El DENUE ya trae **el tamaño** (personal
ocupado), **el giro** exacto y **la ubicación**; con eso solo ya se perfila
sin tocar internet. Y si el negocio tiene página o Facebook, se lee y se
afina: eso es lo que dijo Anuar de *"lo que este tenga en la web"*.

**Lo que lo hace vendible y no una lista más:** a cada negocio se le dice
**qué venderle**. Un salón de belleza necesita batas y espejo grabado; un
taller, uniformes y señalética; una taquería, mandiles y letrero. Eso sale de
una tabla de giro → producto, con lo que Milens y ATF de verdad hacen.

Correr:
    python MERCADO/buscador_clientes.py --preparar
    python MERCADO/buscador_clientes.py --nichos
    python MERCADO/buscador_clientes.py --buscar "salon de belleza" --zona Zapopan
    python MERCADO/buscador_clientes.py --oportunidad "taller mecanico"
"""
from __future__ import annotations
import csv
import io
import json
import sqlite3
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "DATOS" / "denue"
BD = DATOS / "negocios.db"
URL = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_{}_csv.zip"

# Las claves del INEGI por estado. Anuar trabaja en Jalisco (14), pero el día
# que quiera vender en otro lado solo cambia el número.
ESTADOS = {
    "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
    "04": "Campeche", "05": "Coahuila", "06": "Colima", "07": "Chiapas",
    "08": "Chihuahua", "09": "Ciudad de México", "10": "Durango",
    "11": "Guanajuato", "12": "Guerrero", "13": "Hidalgo", "14": "Jalisco",
    "15": "Estado de México", "16": "Michoacán", "17": "Morelos",
    "18": "Nayarit", "19": "Nuevo León", "20": "Oaxaca", "21": "Puebla",
    "22": "Querétaro", "23": "Quintana Roo", "24": "San Luis Potosí",
    "25": "Sinaloa", "26": "Sonora", "27": "Tabasco", "28": "Tamaulipas",
    "29": "Tlaxcala", "30": "Veracruz", "31": "Yucatán", "32": "Zacatecas",
}

# ── QUÉ LE VENDO A CADA GIRO ────────────────────────────────────────────
# Esta tabla es la que convierte una lista de nombres en una lista de ventas.
#
# **Vive en `CONFIG/ofertas_por_giro.json`, no aquí.** Anuar lo pidió el
# 2026-08-17: *"al ser multinicho puedes dejar la versión para usar en
# cualquier ramo sin nada que ver conmigo; mi versión queda personalizada"*.
# Tiene razón, y es lo que vuelve vendible la herramienta: el buscador y el
# perfilador son iguales para todos; lo único que cambia de un negocio a otro
# es QUÉ vendes. Sacarlo a un archivo hace que un despacho contable, una
# imprenta o una constructora usen esto tal cual, sin tocar código.
#
# Lo de abajo es solo el respaldo, por si el archivo no está o viene roto.
OFERTAS_BASE = [
    ("Salones de belleza y barberías",
     ("salon", "belleza", "peluquer", "estetica", "barber", "spa", "uñas", "unas"),
     ["Batas y capas personalizadas", "Espejo o letrero grabado en acrílico",
      "Tarjetas de cita en MDF grabado", "Vinil para el aparador"],
     "Batas con su nombre bordado o sublimado: se ven en cada foto que suben.",
     900),
    ("Talleres y servicio automotriz",
     ("taller", "mecanic", "automotriz", "hojalater", "llantera", "refaccion",
      "autopart", "faros", "electrico automotriz"),
     ["Uniformes y camisolas con logo", "Señalética de seguridad en el taller",
      "Lona de fachada", "Llaveros y placas grabadas para entrega",
      "Retrofit de faros (ATF)"],
     "Uniformes con logo: cambia por completo cómo lo ve el cliente que deja "
     "su coche.",
     1500),
    ("Restaurantes, taquerías y cafés",
     ("restaurant", "taco", "antojito", "cafeter", "fonda", "cocina economica",
      "pizzer", "marisc", "bar,", "cantina", "never", "refresquer", "juguer"),
     ["Mandiles con logo", "Menú grabado en madera o acrílico",
      "Portacuentas grabado", "Señalética de mesas y baños",
      "Lona de fachada", "Termos y vasos personalizados"],
     "Mandiles con logo y el menú grabado: es lo que sube el ticket sin "
     "cambiar la comida.",
     1200),
    ("Escuelas y colegios",
     ("escuela", "primaria", "secundaria", "preescolar", "kinder", "colegio",
      "bachiller", "universidad", "educacion"),
     ["Uniformes y playeras de generación", "Reconocimientos grabados en MDF",
      "Señalética de salones", "Paquetes escolares (Milens)",
      "Porta gafetes y credenciales"],
     "Playeras de generación y reconocimientos: se piden cada ciclo, es "
     "cliente que vuelve.",
     3000),
    ("Gimnasios y deportivos",
     ("gimnasio", "deportivo", "fitness", "crossfit", "yoga", "box", "futbol"),
     ["Jerseys y playeras deportivas sublimadas", "Termos personalizados",
      "Lona y señalética", "Medallas y trofeos en MDF grabado"],
     "Jerseys sublimados por equipo: se venden por docenas, no por pieza.",
     2500),
    ("Veterinarias y mascotas",
     ("veterinar", "mascota", "pet", "estetica canina"),
     ["Placas grabadas para collar", "Batas y mandiles",
      "Señalética y letrero", "Termos y tazas del negocio"],
     "Placas grabadas para collar: se venden todos los días y dejan buen "
     "margen por pieza.",
     600),
    ("Papelerías e imprentas",
     ("papeler", "imprenta", "copias", "regalo", "novedad", "libros"),
     ["Artículos personalizados para revender", "Letrero y vinil de aparador",
      "Corte láser por maquila para sus pedidos"],
     "Maquila de corte: en vez de competirle, se le vende a él y revende.",
     1000),
    ("Abarrotes y tiendas de barrio",
     ("abarrote", "tienda", "miscelanea", "minisuper", "carnicer", "tortiller",
      "frutas y verduras", "pollo"),
     ["Lona de precios y fachada", "Letrero de horario y promociones",
      "Vinil para vitrina"],
     "Una lona de fachada bien hecha, de $400 a $900. Es la venta más rápida "
     "y la que abre la puerta a las demás.",
     700),
    ("Hoteles y hospedaje",
     ("hotel", "moteles", "hospedaje", "posada", "cabañ"),
     ["Señalética de habitaciones", "Amenidades grabadas",
      "Uniformes de personal", "Placas de numeración en MDF o acrílico"],
     "Numeración y señalética de cuartos: se cotiza por juego completo.",
     4000),
    ("Consultorios y salud",
     ("consultorio", "medic", "dental", "dentista", "clinica", "laboratorio",
      "farmacia", "optic"),
     ["Placas de consultorio grabadas", "Batas personalizadas",
      "Señalética y directorio", "Porta recetas grabado"],
     "La placa del consultorio: cuesta poco, se ve mucho, y abre la puerta a "
     "la señalética de todo el edificio.",
     800),
    ("Construcción, herrería y carpintería",
     ("inmobiliar", "bienes raices", "construc", "arquitect", "ingenier",
      "herrer", "carpinter", "vidrio", "aluminio"),
     ["Letreros de obra y lonas", "Maquetas y cortes en MDF",
      "Placas de entrega de obra", "Señalética de seguridad"],
     "Letreros de obra: cada obra nueva es un pedido nuevo del mismo cliente.",
     1800),
    ("Eventos y fiestas",
     ("evento", "fiesta", "banquete", "salon de fiesta", "jardin", "foto",
      "boda"),
     ["Recuerdos y souvenirs en MDF o acrílico", "Letras gigantes",
      "Centros de mesa cortados", "Invitaciones grabadas"],
     "Recuerdos por evento: se piden de 50 a 300 piezas de un jalón.",
     2500),
]
GENERICA_BASE = ("Otros negocios",
                 ["Lona de fachada", "Letrero o placa grabada",
                  "Playeras o uniformes con logo", "Artículos promocionales"],
                 "Empieza por la lona o el letrero: es lo que todo negocio "
                 "necesita y lo que más rápido se cierra.",
                 700)
OFERTAS_JSON = RAIZ / "CONFIG" / "ofertas_por_giro.json"


def _cargar_ofertas():
    """Lee el catálogo de ofertas del archivo. Si falla, usa el de respaldo.

    Nunca truena por un archivo mal escrito: quien lo edita es el dueño del
    negocio, no un programador, y una coma de más no puede dejarlo sin
    herramienta a media jornada.
    """
    try:
        if OFERTAS_JSON.exists():
            d = json.loads(OFERTAS_JSON.read_text(encoding="utf-8"))
            grupos = [(g["grupo"], tuple(g["giros"]), list(g["ofrecer"]),
                       g.get("gancho", ""), int(g.get("ticket", 0)))
                      for g in d.get("grupos", []) if g.get("giros")]
            gen = d.get("generica") or {}
            generica = (gen.get("grupo", "Otros negocios"),
                        list(gen.get("ofrecer", [])), gen.get("gancho", ""),
                        int(gen.get("ticket", 0)))
            if grupos:
                return grupos, generica
    except Exception:
        pass
    return OFERTAS_BASE, GENERICA_BASE


OFERTAS, GENERICA = _cargar_ofertas()


# ── CÓMO SE DICE EN LA CALLE vs. CÓMO LO LLAMA EL INEGI ─────────────────
# El censo no dice «taller mecánico», dice «Reparación mecánica en general de
# automóviles y camiones». Ni «gimnasio», dice «Instalaciones deportivas».
# Sin esta tabla, buscar como habla la gente devolvía CERO — y parecía que no
# había clientes cuando había miles. Se midió el 2026-08-16.
SINONIMOS = {
    "taller mecanico": "reparacion mecanica",
    "taller": "reparacion",
    "mecanico": "mecanica",
    "gimnasio": "deportiv",
    "gym": "deportiv",
    "evento": "organizadores",
    "eventos": "organizadores",
    "fiesta": "organizadores",
    "salon de fiestas": "organizadores",
    "hojalateria": "hojalater",
    "estetica": "belleza",
    "peluqueria": "peluquer",
    "barberia": "peluquer",
    "guarderia": "guarder",
    "dentista": "dental",
    "doctor": "consultorio",
    "medico": "consultorio",
    "tienda": "abarrotes",
    "changarro": "abarrotes",
    "cocina economica": "preparacion de alimentos",
    "taqueria": "tacos",
    "loncheria": "antojitos",
    "ferreteria": "ferreter",
    "carniceria": "carnicer",
    "panaderia": "panificacion",
    "floreria": "flores",
    "funeraria": "funerar",
    "lavanderia": "lavander",
    "tintoreria": "lavander",
    "zapateria": "calzado",
    "mueblería": "muebles",
    "muebleria": "muebles",
    "vulcanizadora": "llantas",
    "llantera": "llantas",
    "refaccionaria": "refacciones",
    "autolavado": "lavado",
    "car wash": "lavado",
    "spa": "belleza",
    "guarderias": "guarder",
    "iglesia": "religios",
    "despacho": "juridic",
    "abogado": "juridic",
    "contador": "contabilidad",
    "notaria": "notari",
}


def _traducir(giro: str) -> str:
    """Pasa lo que uno diría a como lo escribe el INEGI."""
    g = _limpio(giro).strip()
    if not g:
        return g
    if g in SINONIMOS:
        return SINONIMOS[g]
    # Si la frase completa no está, se traduce palabra por palabra: así
    # «taller mecanico de motos» sigue encontrando algo.
    return " ".join(SINONIMOS.get(p, p) for p in g.split())


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _limpio(t) -> str:
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# ─────────────────────────── preparar la base ────────────────────────────
def preparar(estado: str = "14", forzar: bool = False, avisar=None) -> dict:
    """Baja el censo del estado y lo deja en una base rápida de consultar.

    Se hace UNA vez (unos minutos y ~38 MB). Después las búsquedas son
    instantáneas y **sin internet** — que es lo que hace que esto sirva un
    martes a las 11 de la noche cuando se cae la red.
    """
    def _di(t):
        if avisar:
            avisar(t)
    estado = str(estado).zfill(2)
    if estado not in ESTADOS:
        return {"status": "ESTADO_RARO",
                "detalle": f"No conozco el estado «{estado}». Jalisco es 14."}
    DATOS.mkdir(parents=True, exist_ok=True)
    z = DATOS / f"denue_{estado}.zip"
    if forzar or not z.exists() or z.stat().st_size < 1_000_000:
        _di(f"Bajando el censo de {ESTADOS[estado]}…")
        try:
            r = urllib.request.Request(URL.format(estado),
                                       headers={"User-Agent": "Mozilla/5.0"})
            z.write_bytes(urllib.request.urlopen(r, timeout=600).read())
        except Exception as e:
            return {"status": "NO_BAJO", "detalle": str(e)[:300]}
    _di("Guardando en la base…")

    cx = sqlite3.connect(BD, timeout=30)
    cx.execute("PRAGMA journal_mode=WAL")
    cx.execute("""CREATE TABLE IF NOT EXISTS negocios (
        id INTEGER PRIMARY KEY, estado TEXT, nombre TEXT, razon TEXT,
        giro TEXT, giro_b TEXT, tamano TEXT, empleados INTEGER,
        municipio TEXT, colonia TEXT, calle TEXT, numero TEXT, cp TEXT,
        telefono TEXT, correo TEXT, web TEXT, lat REAL, lon REAL,
        alta TEXT)""")
    cx.execute("DELETE FROM negocios WHERE estado=?", (estado,))

    tam_n = {"0 a 5 personas": 3, "6 a 10 personas": 8,
             "11 a 30 personas": 20, "31 a 50 personas": 40,
             "51 a 100 personas": 75, "101 a 250 personas": 175,
             "251 y más personas": 400}
    csv.field_size_limit(10 ** 7)
    n = 0
    with zipfile.ZipFile(z) as Z:
        nom = next(x for x in Z.namelist()
                   if x.lower().endswith(".csv") and "conjunto" in x.lower())
        with Z.open(nom) as f:
            rd = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"))
            lote = []
            for r in rd:
                giro = (r.get("nombre_act") or "").strip()
                lote.append((
                    int(r.get("id") or 0), estado,
                    (r.get("nom_estab") or "").strip(),
                    (r.get("raz_social") or "").strip(),
                    giro, _limpio(giro),
                    (r.get("per_ocu") or "").strip(),
                    tam_n.get((r.get("per_ocu") or "").strip(), 0),
                    (r.get("municipio") or "").strip(),
                    (r.get("nomb_asent") or "").strip(),
                    ((r.get("tipo_vial") or "") + " "
                     + (r.get("nom_vial") or "")).strip(),
                    (r.get("numero_ext") or "").strip(),
                    (r.get("cod_postal") or "").strip(),
                    (r.get("telefono") or "").strip(),
                    (r.get("correoelec") or "").strip(),
                    (r.get("www") or "").strip(),
                    float(r.get("latitud") or 0) or None,
                    float(r.get("longitud") or 0) or None,
                    (r.get("fecha_alta") or "").strip()))
                n += 1
                if len(lote) >= 5000:
                    cx.executemany("INSERT OR REPLACE INTO negocios VALUES ("
                                   + ",".join("?" * 19) + ")", lote)
                    lote = []
                    if n % 50000 == 0:
                        _di(f"  {n:,} negocios…")
            if lote:
                cx.executemany("INSERT OR REPLACE INTO negocios VALUES ("
                               + ",".join("?" * 19) + ")", lote)
    _di("Indexando…")
    for s in ("CREATE INDEX IF NOT EXISTS ix_giro ON negocios(giro_b)",
              "CREATE INDEX IF NOT EXISTS ix_mun ON negocios(municipio)",
              "CREATE INDEX IF NOT EXISTS ix_tam ON negocios(empleados)"):
        cx.execute(s)
    cx.commit()
    con_tel = cx.execute("SELECT COUNT(*) FROM negocios WHERE estado=? AND "
                         "telefono<>''", (estado,)).fetchone()[0]
    cx.close()
    return {"status": "OK", "estado": ESTADOS[estado], "negocios": n,
            "con_telefono": con_tel, "base": str(BD)}


def _cx():
    if not BD.exists():
        return None
    cx = sqlite3.connect(f"file:{BD}?mode=ro", uri=True, timeout=15)
    cx.row_factory = sqlite3.Row
    return cx


def listo() -> bool:
    cx = _cx()
    if not cx:
        return False
    try:
        n = cx.execute("SELECT COUNT(*) FROM negocios").fetchone()[0]
        return n > 0
    except sqlite3.Error:
        return False
    finally:
        cx.close()


# ───────────────────────────── buscar clientes ───────────────────────────
def nichos(zona: str = "", limite: int = 40) -> dict:
    """Qué giros hay y cuántos negocios de cada uno. Para escoger a quién ir.

    Es la vista que le faltaba: no *cuántos clientes tengo*, sino **cuántos
    hay allá afuera** de cada tipo, en la zona que uno alcanza.
    """
    cx = _cx()
    if not cx:
        return {"status": "SIN_BASE",
                "detalle": "Todavía no bajo el censo. Corre --preparar."}
    q = ("SELECT giro, COUNT(*) n, SUM(telefono<>'') tel FROM negocios "
         "WHERE 1=1")
    p = []
    if zona:
        q += " AND municipio LIKE ?"
        p.append(f"%{zona}%")
    q += " GROUP BY giro ORDER BY n DESC LIMIT ?"
    p.append(limite)
    filas = [dict(f) for f in cx.execute(q, p).fetchall()]
    cx.close()
    return {"status": "OK", "zona": zona or "todo el estado",
            "giros": filas}


def buscar(giro: str = "", zona: str = "", colonia: str = "",
           minimo_empleados: int = 0, con_telefono: bool = True,
           limite: int = 60) -> dict:
    """Negocios reales que cumplen lo que pides. Sin internet, al instante."""
    cx = _cx()
    if not cx:
        return {"status": "SIN_BASE",
                "detalle": "Todavía no bajo el censo. Corre --preparar."}
    q = ("SELECT nombre, giro, tamano, empleados, municipio, colonia, calle, "
         "numero, cp, telefono, correo, web, lat, lon FROM negocios WHERE 1=1")
    p = []
    if giro:
        # Cada palabra del giro tiene que aparecer: «taller mecanico» no debe
        # traer todos los talleres de costura.
        for pal in _traducir(giro).split():
            q += " AND giro_b LIKE ?"
            p.append(f"%{pal}%")
    if zona:
        q += " AND municipio LIKE ?"
        p.append(f"%{zona}%")
    if colonia:
        q += " AND colonia LIKE ?"
        p.append(f"%{colonia}%")
    if minimo_empleados:
        q += " AND empleados >= ?"
        p.append(int(minimo_empleados))
    if con_telefono:
        q += " AND telefono <> ''"
    # Primero los más grandes: pagan mejor y deciden más rápido.
    q += " ORDER BY empleados DESC, nombre LIMIT ?"
    p.append(int(limite))
    filas = [dict(f) for f in cx.execute(q, p).fetchall()]
    total = cx.execute("SELECT COUNT(*) FROM negocios").fetchone()[0]
    cx.close()
    for f in filas:
        f["perfil"] = perfilar(f)
    return {"status": "OK", "cuantos": len(filas), "de_un_total": total,
            "giro": giro, "zona": zona or "todo el estado",
            "negocios": filas}


def cerca_de(lat: float, lon: float, km: float = 3.0, giro: str = "",
             limite: int = 60) -> dict:
    """Los negocios a la redonda. Para armar ruta de visita, no para llamar.

    Anuar vende local: tocar puerta con muestra en mano cierra mucho más que
    una llamada en frío. Esto le arma el recorrido.
    """
    cx = _cx()
    if not cx:
        return {"status": "SIN_BASE", "detalle": "Corre --preparar primero."}
    # Un grado de latitud son ~111 km; el de longitud se encoge con el coseno
    # de la latitud. A 3 km de distancia esa aproximación se equivoca en
    # metros — de sobra para armar una ruta a pie.
    import math
    dlat = km / 111.0
    dlon = km / (111.0 * max(0.2, math.cos(math.radians(lat))))
    q = ("SELECT nombre, giro, tamano, empleados, municipio, colonia, calle, "
         "numero, telefono, correo, web, lat, lon FROM negocios "
         "WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?")
    p = [lat - dlat, lat + dlat, lon - dlon, lon + dlon]
    if giro:
        for pal in _traducir(giro).split():
            q += " AND giro_b LIKE ?"
            p.append(f"%{pal}%")
    filas = [dict(f) for f in cx.execute(q, p).fetchall()]
    cx.close()
    for f in filas:
        f["km"] = round(math.hypot((f["lat"] - lat) * 111.0,
                                   (f["lon"] - lon) * 111.0
                                   * math.cos(math.radians(lat))), 2)
        f["perfil"] = perfilar(f)
    filas.sort(key=lambda x: x["km"])
    return {"status": "OK", "cuantos": len(filas[:limite]),
            "centro": (lat, lon), "radio_km": km, "negocios": filas[:limite]}


# ──────────────────────────── el perfilador ──────────────────────────────
def _oferta(giro: str):
    g = _limpio(giro)
    for grupo, palabras, productos, gancho, ticket in OFERTAS:
        if any(p in g for p in palabras):
            return grupo, productos, gancho, ticket
    return GENERICA


def perfilar(negocio: dict) -> dict:
    """El perfil del cliente y qué venderle. Sin internet.

    Se arma con lo que el censo ya trae: **giro** (qué necesita), **tamaño**
    (cuánto puede gastar y quién decide) y **presencia** (si tiene correo o
    página, o si ni eso). Eso solo ya dice cómo entrarle.
    """
    emp = int(negocio.get("empleados") or 0)
    giro = negocio.get("giro", "")
    grupo, productos, gancho, ticket = _oferta(giro)

    if emp <= 5:
        clase, quien, como = ("Changarro", "El dueño, en el mostrador",
                              "Se decide en el momento y se paga en efectivo. "
                              "Hay que llegar con la muestra en la mano y un "
                              "precio cerrado, no con una cotización.")
        factor = 1.0
    elif emp <= 10:
        clase, quien, como = ("Negocio chico", "El dueño o el encargado",
                              "Ya tiene con qué pagar y le importa verse "
                              "formal. Cotización por WhatsApp, con foto de "
                              "trabajos anteriores.")
        factor = 1.6
    elif emp <= 30:
        clase, quien, como = ("Negocio establecido",
                              "Gerente o encargado de compras",
                              "Compra por volumen y repite. Vale la pena "
                              "dejarle una carpeta y darle seguimiento a los "
                              "15 días.")
        factor = 3.0
    else:
        clase, quien, como = ("Empresa", "Compras o Recursos Humanos",
                              "Pide factura y varias cotizaciones. Es el que "
                              "deja los pedidos grandes, pero tarda: hay que "
                              "entrar por uniformes o señalética.")
        factor = 8.0

    presencia, senal = [], 0
    if (negocio.get("web") or "").strip():
        presencia.append("tiene página")
        senal += 2
    if (negocio.get("correo") or "").strip():
        presencia.append("tiene correo")
        senal += 1
    if (negocio.get("telefono") or "").strip():
        presencia.append("tiene teléfono")
        senal += 1

    if senal >= 3:
        lectura = ("Cuida su imagen y ya invierte en ella. Entra con lo de "
                   "más valor: uniformes, señalética completa, no la lona "
                   "suelta.")
    elif senal == 0:
        lectura = ("Sin presencia. Ese es el argumento: no lo van a encontrar "
                   "ni saben qué vende. Entra con lo básico y barato.")
    else:
        lectura = ("Presencia a medias. La lona o el letrero es lo que más "
                   "rápido le cambia el negocio, y es lo que más rápido "
                   "cierra.")

    return {"grupo": grupo, "clase": clase, "empleados": emp, "con_quien_hablar": quien,
            "como_entrarle": como, "presencia": presencia or ["sin datos"],
            "lectura": lectura, "que_venderle": productos, "gancho": gancho,
            "ticket_base": int(ticket),
            "ticket_estimado": int(ticket * factor)}


def perfil_web(nombre: str, municipio: str = "", leer: bool = True) -> dict:
    """El perfil por lo que el negocio tenga en la web. Esto sí usa internet.

    Anuar lo pidió así: *"no me refiero a redes solamente, más bien al tipo de
    perfil que tenga cada empresa basado a lo que este tenga en la web"*.

    Se busca el negocio, se mira qué aparece (página propia, Facebook,
    directorio, o nada) y **eso mismo es el perfil**: un negocio sin nada en
    internet se atiende distinto a uno con página y catálogo.
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
    except ImportError:
        return {"status": "FALTA_LIBRERIA",
                "detalle": "Falta `ddgs`: pip install ddgs"}
    consulta = f"{nombre} {municipio}".strip()
    try:
        with DDGS() as d:
            res = list(d.text(consulta, region="mx-es", max_results=8))
    except Exception as e:
        return {"status": "SIN_INTERNET", "detalle": str(e)[:200]}

    sitios, redes, directorios = [], [], []
    for x in res:
        u = (x.get("href") or "").lower()
        if not u:
            continue
        if any(k in u for k in ("facebook.com", "instagram.com", "tiktok.com",
                                "linkedin.com", "youtube.com")):
            redes.append(x.get("href"))
        elif any(k in u for k in ("paginasamarillas", "cylex", "infoisinfo",
                                  "yelp", "foursquare", "denue", "inegi",
                                  "google.com/maps", "waze")):
            directorios.append(x.get("href"))
        else:
            sitios.append(x.get("href"))

    if sitios:
        nivel, lectura = ("Con página propia",
                          "Ya invierte en su imagen: aquí no se compite por "
                          "precio, se compite por acabado. Ofrécele lo bueno.")
    elif redes:
        nivel, lectura = ("Solo redes",
                          "Se mueve por Facebook o Instagram. Todo lo que le "
                          "vendas tiene que verse bien EN FOTO: ese es el "
                          "argumento de venta con él.")
    elif directorios:
        nivel, lectura = ("Solo en directorios",
                          "Existe, pero no se promociona. Es tu cliente más "
                          "fácil: cualquier cosa que le hagas es más de lo "
                          "que tiene hoy.")
    else:
        nivel, lectura = ("Invisible",
                          "No aparece en internet. Entra por la puerta, no "
                          "por el teléfono — y llévale la muestra.")

    return {"status": "OK", "busque": consulta, "nivel": nivel,
            "lectura": lectura, "pagina": sitios[:2], "redes": redes[:3],
            "directorios": directorios[:2]}


def oportunidad(giro: str) -> dict:
    """Qué venderle a un giro, con qué entrar y cuánto pedir."""
    grupo, productos, gancho, ticket = _oferta(giro)
    cx = _cx()
    cuantos = con_tel = 0
    if cx:
        q = "SELECT COUNT(*), SUM(telefono<>'') FROM negocios WHERE 1=1"
        p = []
        for pal in _traducir(giro).split():
            q += " AND giro_b LIKE ?"
            p.append(f"%{pal}%")
        cuantos, con_tel = cx.execute(q, p).fetchone()
        cx.close()
    return {"status": "OK", "giro": giro, "grupo": grupo,
            "que_venderle": productos,
            "gancho": gancho, "ticket_base": ticket,
            "negocios_en_el_estado": cuantos or 0,
            "con_telefono": con_tel or 0,
            "mercado_estimado": int((cuantos or 0) * ticket * 0.02),
            "nota": ("El mercado estimado es a un 2% de conversión, que ya es "
                     "optimista tocando en frío. Sirve para comparar giros "
                     "entre sí, no para hacer cuentas alegres.")}


def agrupar(zona: str = "", colonia: str = "", minimo_empleados: int = 0,
            por_grupo: int = 400) -> dict:
    """Los clientes de una zona, ordenados por grupo y por si se pueden contactar.

    Anuar lo pidió así el 2026-08-17: *"agrupar y separar los que sí tengan
    dirección y número de teléfono, así como la propuesta a ofrecer por
    grupo"*.

    Van **tres bolsas, no dos**, y la razón es cómo vende él de verdad:

      · **Para visitar** — trae teléfono Y calle con número. Es la mejor:
        llegas, enseñas la muestra y cierras el mismo día.
      · **Solo teléfono** — se le marca o se le manda WhatsApp con fotos.
      · **Solo dirección** — no tiene teléfono, pero se sabe dónde está. Para
        vender a pie eso vale igual: se toca la puerta.

    Y cada grupo trae **su propuesta**: qué venderle, con qué entrar y cuánto
    pedir. Una lista sin eso es una lista de nombres; con eso es un plan.
    """
    cx = _cx()
    if not cx:
        return {"status": "SIN_BASE",
                "detalle": "Todavía no bajo el censo. Corre --preparar."}
    q = ("SELECT nombre, giro, tamano, empleados, municipio, colonia, calle, "
         "numero, cp, telefono, correo, web, lat, lon FROM negocios WHERE 1=1")
    p = []
    if zona:
        q += " AND municipio LIKE ?"
        p.append(f"%{zona}%")
    if colonia:
        q += " AND colonia LIKE ?"
        p.append(f"%{colonia}%")
    if minimo_empleados:
        q += " AND empleados >= ?"
        p.append(int(minimo_empleados))
    q += " ORDER BY empleados DESC, nombre"
    filas = [dict(f) for f in cx.execute(q, p).fetchall()]
    cx.close()

    grupos = {}
    for n in filas:
        pf = perfilar(n)
        n["perfil"] = pf
        g = grupos.setdefault(pf["grupo"], {
            "grupo": pf["grupo"], "que_venderle": pf["que_venderle"],
            "gancho": pf["gancho"], "ticket": pf["ticket_base"],
            "para_visitar": [], "solo_telefono": [], "solo_direccion": [],
            "sin_datos": 0})
        tel = bool((n.get("telefono") or "").strip())
        # Dirección útil = calle CON número. Una calle sin número no sirve
        # para llegar, y por eso no cuenta como visitable.
        dire = bool((n.get("calle") or "").strip()
                    and (n.get("numero") or "").strip())
        if tel and dire:
            g["para_visitar"].append(n)
        elif tel:
            g["solo_telefono"].append(n)
        elif dire:
            g["solo_direccion"].append(n)
        else:
            g["sin_datos"] += 1

    salida = []
    for g in grupos.values():
        for k in ("para_visitar", "solo_telefono", "solo_direccion"):
            g[f"n_{k}"] = len(g[k])
            g[k] = g[k][:por_grupo]
        g["total"] = (g["n_para_visitar"] + g["n_solo_telefono"]
                      + g["n_solo_direccion"] + g["sin_datos"])
        # El ticket del grupo es el de un negocio chico, que es la mayoría;
        # así el número que se ve no viene inflado por dos empresas grandes.
        salida.append(g)
    salida.sort(key=lambda x: -x["n_para_visitar"])
    return {"status": "OK", "zona": zona or "todo el estado",
            "colonia": colonia, "revisados": len(filas),
            "grupos": salida}


def exportar_grupos(r: dict, carpeta: str = "") -> dict:
    """Un CSV por grupo y por bolsa, más un resumen. Para abrirlos del celular.

    Se parten en archivos y no en uno solo a propósito: en el celular no se
    filtra una hoja de 3,000 renglones. Un archivo por grupo se abre, se lee
    y se va tachando.
    """
    if r.get("status") != "OK":
        return r
    base = Path(carpeta) if carpeta else (
        Path.home() / "Downloads" / "clientes_por_grupo")
    base.mkdir(parents=True, exist_ok=True)
    escritos, total = [], 0
    encabezado = ["Negocio", "Giro", "Tamaño", "Perfil", "Teléfono",
                  "Dirección", "Colonia", "Municipio", "Correo",
                  "Qué ofrecerle", "Con qué entrar", "Ticket", "Visitado"]

    def _fila(n):
        p = n["perfil"]
        return [n.get("nombre", ""), n.get("giro", "")[:60],
                n.get("tamano", ""), p["clase"], n.get("telefono", ""),
                (n.get("calle", "") + " " + n.get("numero", "")).strip(),
                n.get("colonia", ""), n.get("municipio", ""),
                n.get("correo", ""), " · ".join(p["que_venderle"][:3]),
                p["gancho"], p["ticket_estimado"], ""]

    for g in r["grupos"]:
        limpio = "".join(c if c.isalnum() or c in " -" else ""
                         for c in g["grupo"])[:40].strip().replace(" ", "_")
        for bolsa, etiqueta in (("para_visitar", "1_PARA_VISITAR"),
                                ("solo_telefono", "2_SOLO_TELEFONO"),
                                ("solo_direccion", "3_SOLO_DIRECCION")):
            if not g[bolsa]:
                continue
            f = base / f"{limpio}__{etiqueta}.csv"
            with open(f, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh)
                w.writerow([f"{g['grupo']} — {etiqueta.split('_', 1)[1]}"])
                w.writerow([f"Ofrécele: {' · '.join(g['que_venderle'])}"])
                w.writerow([f"Con qué entrar: {g['gancho']}"])
                w.writerow([f"Ticket estimado: ${g['ticket']:,}"])
                w.writerow([])
                w.writerow(encabezado)
                for n in g[bolsa]:
                    w.writerow(_fila(n))
            escritos.append(str(f))
            total += len(g[bolsa])

    resumen = base / "0_RESUMEN.csv"
    with open(resumen, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["Grupo", "Para visitar", "Solo teléfono",
                    "Solo dirección", "Sin datos", "Total", "Ticket",
                    "Qué ofrecerle", "Con qué entrar"])
        for g in r["grupos"]:
            w.writerow([g["grupo"], g["n_para_visitar"], g["n_solo_telefono"],
                        g["n_solo_direccion"], g["sin_datos"], g["total"],
                        g["ticket"], " · ".join(g["que_venderle"]),
                        g["gancho"]])
    return {"status": "OK", "carpeta": str(base), "archivos": len(escritos) + 1,
            "renglones": total, "resumen": str(resumen)}


def exportar(negocios: list, archivo: str = "") -> dict:
    """Deja la lista en CSV, para abrirla en Excel o cargarla al celular."""
    destino = Path(archivo) if archivo else (
        Path.home() / "Downloads" / "clientes_posibles.csv")
    destino.parent.mkdir(parents=True, exist_ok=True)
    k = 2
    while destino.exists():
        destino = destino.with_name(f"{destino.stem}__{k}.csv")
        k += 1
    campos = ["nombre", "giro", "tamano", "municipio", "colonia", "calle",
              "numero", "telefono", "correo", "clase", "que_venderle",
              "gancho", "ticket_estimado"]
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Negocio", "Giro", "Tamaño", "Municipio", "Colonia",
                    "Calle", "Número", "Teléfono", "Correo", "Perfil",
                    "Qué venderle", "Con qué entrar", "Ticket estimado"])
        for n in negocios:
            p = n.get("perfil", {})
            w.writerow([n.get("nombre", ""), n.get("giro", ""),
                        n.get("tamano", ""), n.get("municipio", ""),
                        n.get("colonia", ""), n.get("calle", ""),
                        n.get("numero", ""), n.get("telefono", ""),
                        n.get("correo", ""), p.get("clase", ""),
                        " · ".join(p.get("que_venderle", [])),
                        p.get("gancho", ""), p.get("ticket_estimado", "")])
    return {"status": "OK", "archivo": str(destino), "cuantos": len(negocios)}


# ─────────────────────────────── textos ──────────────────────────────────
def _t_buscar(r: dict) -> str:
    if r.get("status") != "OK":
        return f"⚠️ {r.get('detalle', r.get('status'))}"
    t = (f"🎯 **{r['cuantos']} clientes posibles** — {r.get('giro') or 'todos'}"
         f" en {r['zona']}\n")
    for n in r["negocios"][:25]:
        p = n["perfil"]
        t += (f"\n• **{n['nombre'] or '(sin nombre)'}** · {p['clase']}"
              f" ({n['tamano']})\n"
              f"  📞 {n['telefono'] or '—'}   📍 {n['calle']} {n['numero']}, "
              f"{n['colonia']}, {n['municipio']}\n"
              f"  💡 {p['gancho']}\n"
              f"  💰 ~${p['ticket_estimado']:,} · véndele: "
              f"{', '.join(p['que_venderle'][:3])}\n")
    if r["cuantos"] > 25:
        t += f"\n… y {r['cuantos'] - 25} más. Exporta a CSV para verlos todos."
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

    if "--preparar" in a:
        r = preparar(_op("estado", "14"), "--forzar" in a, print)
        if r["status"] != "OK":
            print("⚠️", r["detalle"])
            return 1
        print(f"\n✅ {r['negocios']:,} negocios de {r['estado']} · "
              f"{r['con_telefono']:,} con teléfono\n   {r['base']}")
        return 0
    if "--nichos" in a:
        r = nichos(_op("zona", ""), int(_op("limite", 30)))
        if r["status"] != "OK":
            print("⚠️", r["detalle"])
            return 1
        print(f"📚 **Giros en {r['zona']}**\n")
        for g in r["giros"]:
            print(f"  {g['n']:>7,}  ({g['tel'] or 0:>6,} con tel)  {g['giro'][:60]}")
        return 0
    if _op("oportunidad"):
        r = oportunidad(_op("oportunidad"))
        print(f"💼 **{r['giro']}** — {r['negocios_en_el_estado']:,} negocios, "
              f"{r['con_telefono']:,} con teléfono")
        print(f"   Véndele: {', '.join(r['que_venderle'])}")
        print(f"   Con qué entrar: {r['gancho']}")
        print(f"   Ticket base ~${r['ticket_base']:,}")
        print(f"   Mercado estimado ${r['mercado_estimado']:,}\n   ⚠️ {r['nota']}")
        return 0
    if _op("perfil"):
        r = perfil_web(_op("perfil"), _op("zona", ""))
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if "--grupos" in a:
        r = agrupar(_op("zona", ""), _op("colonia", ""),
                    int(_op("empleados", 0)))
        if r["status"] != "OK":
            print("⚠️", r["detalle"])
            return 1
        print(f"👥 **Clientes por grupo** — {r['zona']}"
              + (f" · colonia {r['colonia']}" if r["colonia"] else "")
              + f"  ({r['revisados']:,} negocios revisados)\n")
        print(f"{'GRUPO':<38}{'VISITAR':>9}{'SOLO TEL':>10}"
              f"{'SOLO DIR':>10}{'TICKET':>9}")
        for g in r["grupos"]:
            print(f"{g['grupo'][:37]:<38}{g['n_para_visitar']:>9,}"
                  f"{g['n_solo_telefono']:>10,}{g['n_solo_direccion']:>10,}"
                  f"{g['ticket']:>9,}")
        print("\nLa propuesta de cada grupo:")
        for g in r["grupos"]:
            if not (g["n_para_visitar"] or g["n_solo_telefono"]):
                continue
            print(f"\n• **{g['grupo']}** — ~${g['ticket']:,}\n"
                  f"  ofrécele: {' · '.join(g['que_venderle'])}\n"
                  f"  con qué entrar: {g['gancho']}")
        if "--csv" in a:
            e = exportar_grupos(r, _op("carpeta", ""))
            print(f"\n📁 {e['archivos']} archivos con {e['renglones']:,} "
                  f"negocios en:\n   {e['carpeta']}")
        return 0
    if "--buscar" in a:
        r = buscar(_op("buscar", ""), _op("zona", ""), _op("colonia", ""),
                   int(_op("empleados", 0)), "--sin-telefono" not in a,
                   int(_op("limite", 60)))
        print(_t_buscar(r))
        if r.get("status") == "OK" and "--csv" in a:
            e = exportar(r["negocios"])
            print(f"\n📁 {e['archivo']}")
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
