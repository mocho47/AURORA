# -*- coding: utf-8 -*-
"""VENDEDOR de AURORA.

Dos caras:
- Interno (para Anuar): asesor técnico/auto-eléctrico real.
- Cliente: súper-vendedor con técnicas reales + datos reales del catálogo.

HONESTIDAD: las fichas técnicas vienen de CONFIG/fichas_tecnicas.json (datos reales
de Anuar). Si un campo está en PENDIENTE, el vendedor NO inventa: lo dice y ofrece
confirmarlo. Las técnicas de venta son frameworks reales y probados.
"""
from __future__ import annotations
import json
import re
import sqlite3
import unicodedata as _ud
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

FICHAS_PATH = Path(__file__).resolve().parent.parent / "CONFIG" / "fichas_tecnicas.json"


def _norm(s: str) -> str:
    """minúsculas sin acentos (el usuario escribe sin tildes)."""
    return "".join(c for c in _ud.normalize("NFD", (s or "").lower()) if _ud.category(c) != "Mn")


def _coincide(consulta: str, f: dict) -> bool:
    """Empareja consulta con una ficha sin importar acentos/plurales/palabras extra."""
    pn = _norm(consulta); nn = _norm(f.get("nombre", ""))
    if not pn:
        return False
    if pn == nn or pn in nn or nn in pn or pn == _norm(f.get("id", "")):
        return True
    nt = [w for w in nn.split() if len(w) > 2]          # tokens del nombre dentro de la consulta
    if nt and all(w in pn for w in nt):
        return True
    pt = [w for w in pn.split() if len(w) > 2]          # tokens de la consulta dentro del nombre
    return bool(pt) and all(w in nn or (w.endswith("s") and w[:-1] in nn) for w in pt)


_RE_CODIGO = re.compile(r"\bh\d+\b")  # códigos de foco reales: h1, h3, h4, h7, h8, h11, h13...


def _busca_ficha(producto: str, fichas: list) -> Optional[dict]:
    """Si la consulta trae un código de foco real (h4, h7...), ese código EXACTO
    gana sobre cualquier match genérico por palabra suelta. Encontrado en vivo
    2026-07-27: pedir 'ficha del led h7' regresaba la ficha de H4, porque _coincide()
    descarta tokens de 2 caracteres ('h7') y solo quedaba 'led', que empata con
    cualquier ficha LED — la primera del JSON ganaba sin importar cuál pidió el
    usuario. Datos reales pero del producto equivocado."""
    pn = _norm(producto)
    codigos_consulta = set(_RE_CODIGO.findall(pn))
    if codigos_consulta:
        exactas = [x for x in fichas
                   if codigos_consulta & set(_RE_CODIGO.findall(_norm(x.get("nombre", ""))))]
        if exactas:
            return exactas[0]
    return next((x for x in fichas if _coincide(producto, x)), None)

# ───────────────────────── LIBRERÍA REAL DE TÉCNICAS DE VENTA ─────────────────────────
TECNICAS_VENTA: Dict[str, dict] = {
    "descubrimiento_SPIN": {
        "que_es": "Preguntar antes de vender: Situación, Problema, Implicación, Necesidad.",
        "uso": ["¿Qué auto tienes y qué buscas lograr?", "¿Qué te molesta de tu iluminación actual?",
                "¿Te ha pasado no ver bien de noche / que se vea opaco?", "Si lo resolvemos, ¿qué ganarías?"],
    },
    "estructura_AIDA": {
        "que_es": "Atención → Interés → Deseo → Acción. Esqueleto de todo pitch/contenido.",
        "uso": ["Gancho que para el scroll", "Beneficio claro", "Mostrar el resultado deseado", "CTA concreto"],
    },
    "valor_no_precio": {
        "que_es": "Vender el resultado/identidad, no las características. Traducir specs a beneficios.",
        "uso": ["No 'X lúmenes' → 'ves el doble de carretera de noche'",
                "No 'RGB BT' → 'tu auto único, lo controlas desde el cel'"],
    },
    "persuasion_cialdini": {
        "que_es": "6 principios éticos: reciprocidad, escasez HONESTA, autoridad, prueba social, compromiso, simpatía.",
        "uso": ["Dar valor antes de pedir (tip gratis)", "Cupos/tiempos reales (no falsos)",
                "Mostrar tu experiencia/trabajos", "Antes-después y testimonios reales",
                "Pequeños sí que llevan al sí grande", "Trato cercano y humano"],
    },
    "manejo_objeciones": {
        "que_es": "Validar → preguntar → reencuadrar con valor. Nunca discutir.",
        "uso": {
            "esta_caro": "Entiendo. ¿Caro comparado con qué? Mira lo que incluye e dura años…",
            "lo_pienso": "Claro. ¿Qué es lo que te haría decidir, el precio o cómo queda?",
            "lo_hago_yo": "Se puede; el detalle es el sellado/CANbus: si falla, sale más caro. Te lo dejo garantizado.",
        },
    },
    "cierre": {
        "que_es": "Cerrar con opción, no con sí/no. Bajar fricción al siguiente paso.",
        "uso": ["¿Te lo agendo este sábado o entre semana?", "¿Lo quieres premium o estándar?",
                "Aparto tu lugar con anticipo y te confirmo hora."],
    },
}

EVITAR_VENTA = ["Mentir sobre specs/compatibilidad", "Prometer lo que no se puede cumplir",
                "Presionar con escasez falsa", "Hablar mal de la competencia"]


def _cargar() -> dict:
    try:
        return json.loads(FICHAS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e), "fichas": []}


def listar_fichas() -> dict:
    """Lista los equipos del catálogo y si su ficha técnica está COMPLETA o PENDIENTE."""
    d = _cargar()
    if d.get("_error"):
        # Antes esto se ignoraba y respondía "OK, 0 fichas" — un catálogo corrupto
        # se veía igual que un catálogo vacío, sin ningún aviso del error real.
        return {"status": "ERROR", "detalle": f"No pude leer el catálogo real: {d['_error']}"}
    items = [{"id": f["id"], "nombre": f["nombre"], "precio": f.get("precio"),
              "negocio": f.get("negocio", ""), "estado": f.get("estado_ficha", "PENDIENTE")}
             for f in d.get("fichas", [])]
    completas = sum(1 for i in items if i["estado"] == "COMPLETA")
    return {"status": "OK", "total": len(items), "completas": completas,
            "pendientes": len(items) - completas, "equipos": items}


def ficha(producto: str) -> dict:
    """Devuelve la ficha técnica REAL de un equipo. Si hay campos PENDIENTE, lo dice honesto."""
    d = _cargar()
    if d.get("_error"):
        return {"status": "ERROR", "detalle": f"No pude leer el catálogo real: {d['_error']}"}
    f = _busca_ficha(producto, d.get("fichas", []))
    if not f:
        disp = [x["nombre"] for x in d.get("fichas", [])]
        return {"status": "NO_ENCONTRADO", "detalle": f"No tengo '{producto}'.", "disponibles": disp}
    faltan = [c for c in ("que_es", "compatibilidad", "diferencias", "specs", "instalacion", "recomendado_para")
              if not f.get(c)]
    return {"status": "OK", "ficha": f,
            "completa": f.get("estado_ficha") == "COMPLETA",
            "faltan_datos": faltan,
            "aviso": None if not faltan else
            f"Faltan datos reales ({', '.join(faltan)}). El vendedor los confirmará contigo, no los inventa."}


def tecnicas(nombre: Optional[str] = None) -> dict:
    """Librería real de técnicas de venta (una o todas)."""
    if nombre:
        n = nombre.lower().strip()
        hit = next((k for k in TECNICAS_VENTA if n in k.lower()), None)
        if hit:
            return {"status": "OK", "tecnica": hit, **TECNICAS_VENTA[hit]}
        return {"status": "NO_ENCONTRADO", "disponibles": list(TECNICAS_VENTA)}
    return {"status": "OK", "tecnicas": TECNICAS_VENTA, "evitar": EVITAR_VENTA}


def prompt_extraccion(producto: str, texto_web: str) -> str:
    """Prompt para que el cerebro extraiga la ficha SOLO del texto real de la web. Sin inventar."""
    return (
        f"Eres técnico de iluminación automotriz. Del SIGUIENTE texto real de la web sobre "
        f"'{producto}', extrae SOLO lo que esté explícito. Devuelve EXCLUSIVAMENTE un JSON con claves: "
        "que_es (1-2 frases), specs (objeto clave:valor), compatibilidad (lista de autos/sockets), "
        "diferencias (texto breve), instalacion (objeto: dificultad, requiere [lista], pasos [lista]), "
        "recomendado_para (texto), argumentos_venta (lista 2-3). "
        "Si un dato NO aparece en el texto, déjalo vacío (\"\" o []). NO inventes NADA. "
        "Para cableado/instalación, solo lo que el texto diga textual. Responde SOLO el JSON.\n\n"
        "=== TEXTO REAL DE LA WEB ===\n" + (texto_web or "")[:6000]
    )


def guardar_ficha(producto: str, datos: dict, fuentes: list) -> dict:
    """Guarda en fichas_tecnicas.json SOLO los campos con dato real + las fuentes (URLs)."""
    d = _cargar()
    for f in d.get("fichas", []):
        if _coincide(producto, f):
            for k in ("que_es", "compatibilidad", "diferencias", "specs", "instalacion",
                      "recomendado_para", "argumentos_venta"):
                v = datos.get(k)
                if v:
                    f[k] = v
            f["fuentes"] = fuentes
            faltan = [c for c in ("que_es", "compatibilidad", "diferencias", "specs", "recomendado_para")
                      if not f.get(c)]
            # COMPLETA solo con calidad real: descripción sustancial + specs o compatibilidad
            que_ok = isinstance(f.get("que_es"), str) and len(f.get("que_es", "").strip()) >= 25
            rico = bool(f.get("specs")) or bool(f.get("compatibilidad"))
            if que_ok and rico and not faltan:
                f["estado_ficha"] = "COMPLETA"
            elif f.get("que_es") or f.get("specs"):
                f["estado_ficha"] = "PARCIAL"
            else:
                f["estado_ficha"] = "PENDIENTE"
            FICHAS_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"status": "OK", "ficha": f, "faltan": faltan, "estado": f["estado_ficha"],
                    "nota": "Datos reales de la web (con fuentes). Lo que falta sigue pendiente; no se inventó."}
    return {"status": "NO_ENCONTRADO", "detalle": f"No existe '{producto}' en el catálogo."}


def editar_ficha(fid: str, datos: dict, fuentes: Optional[list] = None) -> dict:
    """
    Editor del PANEL: actualiza una ficha por su ID EXACTO. A diferencia de guardar_ficha,
    permite CORREGIR datos malos (sobrescribe con lo que mande el panel, aunque ya hubiera algo).
    Recalcula el estado con el mismo criterio de calidad real.
    """
    d = _cargar()
    for f in d.get("fichas", []):
        if f.get("id") == fid:
            for k in ("nombre", "precio", "que_es", "compatibilidad", "diferencias",
                      "specs", "instalacion", "recomendado_para", "argumentos_venta"):
                if k in datos:
                    f[k] = datos[k]
            if fuentes is not None:
                f["fuentes"] = fuentes
            faltan = [c for c in ("que_es", "compatibilidad", "diferencias", "specs", "recomendado_para")
                      if not f.get(c)]
            que_ok = isinstance(f.get("que_es"), str) and len(f.get("que_es", "").strip()) >= 25
            rico = bool(f.get("specs")) or bool(f.get("compatibilidad"))
            if que_ok and rico and not faltan:
                f["estado_ficha"] = "COMPLETA"
            elif f.get("que_es") or f.get("specs"):
                f["estado_ficha"] = "PARCIAL"
            else:
                f["estado_ficha"] = "PENDIENTE"
            FICHAS_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"status": "OK", "estado": f["estado_ficha"], "faltan": faltan, "ficha": f,
                    "nota": "Ficha actualizada desde el panel. Lo que quede vacío sigue pendiente."}
    return {"status": "NO_ENCONTRADO", "detalle": f"No existe la ficha con id '{fid}'."}


def construir_brief(modo: str, producto: str = "", objetivo: str = "", negocio: str = "") -> str:
    """Arma el contexto para el cerebro. modo: 'cliente' (vender) o 'interno' (asesor técnico de Anuar).
    negocio: ATF o MILENS (mismas reglas para ambos). Solo datos reales; lo PENDIENTE se marca,
    el cerebro NO inventa."""
    partes = []
    fz = ficha(producto) if producto else None
    if fz and fz.get("status") == "OK":
        negocio = negocio or fz["ficha"].get("negocio", "ATF")
    negocio = (negocio or "ATF").upper()
    experto = ("auto-eléctrico / retrofit de iluminación automotriz" if negocio == "ATF"
               else "personalización: sublimación, corte y grabado láser, DTF/vinil")
    if modo == "interno":
        partes.append(f"Eres el asesor técnico de AURORA para {negocio}, experto en {experto}, SOLO para Anuar "
                      "(dueño). Sé técnico, directo y honesto. Si un dato no está en la ficha, dilo y sugiere "
                      "buscar/confirmar el diagrama, manual o ficha real del fabricante.")
    else:
        partes.append(f"Eres el VENDEDOR de {negocio} ante un cliente, experto en {experto}. "
                      "PERSONALIDAD: atractivo, seguro y dinámico — con carisma y energía que dan confianza, "
                      "pero SIEMPRE real (esa seguridad nace de saber, no de exagerar). Frases cortas, entusiastas, "
                      "que enganchan. Usa técnicas reales (descubrir, valor>precio, prueba social, cierre con opción). "
                      "NUNCA inventes specs/compatibilidad ni prometas de más. Captura el lead y, para cerrar, "
                      "deja que Anuar autorice.")
    if producto:
        if fz and fz.get("status") == "OK":
            partes.append(f"FICHA REAL del equipo: {json.dumps(fz['ficha'], ensure_ascii=False)}")
            if fz.get("faltan_datos"):
                partes.append(f"DATOS PENDIENTES (NO inventar, confirmar con Anuar): {fz['faltan_datos']}")
        else:
            partes.append(f"No hay ficha de '{producto}'. No inventes; ofrece confirmarlo.")
    partes.append("Técnicas disponibles: " + ", ".join(TECNICAS_VENTA.keys()))
    if objetivo:
        partes.append(f"Objetivo: {objetivo}")
    return "\n".join(partes)

# ─────────────────── BASE DE DATOS REAL (SQLite, local, sin nube) ───────────────────
# Persistencia de ventas/clientes/productos igual que el resto de AURORA (taller.db,
# biblioteca.db). Sin dependencia de nube: no se auto-pausa ni caduca. El catálogo de
# productos se siembra desde CONFIG/fichas_tecnicas.json (datos reales de Anuar).
DB_VENDEDOR = Path(__file__).resolve().parent.parent / "vendedor.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_VENDEDOR))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_vendedor_db() -> None:
    """Crea las tablas si no existen y siembra el catálogo desde las fichas reales."""
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT UNIQUE NOT NULL,
            email TEXT,
            creado TEXT
        )""")
    con.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL DEFAULT 0,
            stock INTEGER,
            categoria TEXT
        )""")
    con.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            monto_total REAL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'No especificado',
            estado_pedido TEXT DEFAULT 'Pendiente',
            vendedor_id TEXT DEFAULT 'AURORA',
            creado TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )""")
    con.execute("""
        CREATE TABLE IF NOT EXISTS detalles_venta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id TEXT,
            cantidad INTEGER DEFAULT 1,
            precio_unitario REAL DEFAULT 0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
        )""")
    con.commit()
    _sembrar_productos(con)
    con.close()


def _sembrar_productos(con: sqlite3.Connection) -> None:
    """Alinea la tabla productos con el catálogo real de fichas (upsert por SKU=id de ficha)."""
    d = _cargar()
    for f in d.get("fichas", []):
        sku = f.get("id")
        if not sku:
            continue
        con.execute("""
            INSERT INTO productos (sku, nombre, precio, stock, categoria)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                nombre=excluded.nombre, precio=excluded.precio, categoria=excluded.categoria
        """, (sku, f.get("nombre"), f.get("precio") or 0, f.get("stock"), f.get("categoria")))
    con.commit()


def registrar_venta_db(datos_venta: dict):
    """
    Registra una venta completa (cliente + venta + detalles) en vendedor.db (SQLite).
    'datos_venta' debe contener:
    {
        "cliente": {"nombre": "John Doe", "telefono": "555-1234", "email": "john@example.com"},
        "productos": [{"producto_id": "sku_o_id", "cantidad": 1, "precio_unitario": 150.00}],
        "monto_total": 150.00,
        "metodo_pago": "Tarjeta",
        "vendedor_id": "nombre_vendedor"
    }
    Transacción atómica: si algo falla, no queda nada a medias.
    """
    cliente_data = datos_venta.get("cliente") or {}
    if not cliente_data.get("telefono"):
        return {"status": "ERROR", "detalle": "Los datos del cliente y su teléfono son obligatorios."}

    init_vendedor_db()
    con = _conn()
    try:
        ahora = datetime.now().isoformat(timespec="seconds")
        # 1. Cliente (upsert por teléfono)
        con.execute("""
            INSERT INTO clientes (nombre, telefono, email, creado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telefono) DO UPDATE SET
                nombre=COALESCE(excluded.nombre, clientes.nombre),
                email=COALESCE(excluded.email, clientes.email)
        """, (cliente_data.get("nombre"), cliente_data["telefono"], cliente_data.get("email"), ahora))
        cliente_id = con.execute(
            "SELECT id FROM clientes WHERE telefono=?", (cliente_data["telefono"],)
        ).fetchone()["id"]

        # 2. Venta
        cur = con.execute("""
            INSERT INTO ventas (cliente_id, monto_total, metodo_pago, estado_pedido, vendedor_id, creado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cliente_id, datos_venta.get("monto_total", 0),
              datos_venta.get("metodo_pago", "No especificado"),
              datos_venta.get("estado_pedido", "Pendiente"),
              datos_venta.get("vendedor_id", "AURORA"), ahora))
        venta_id = cur.lastrowid

        # 3. Detalles
        for item in datos_venta.get("productos", []):
            con.execute("""
                INSERT INTO detalles_venta (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (venta_id, item.get("producto_id"), item.get("cantidad", 1),
                  item.get("precio_unitario", 0)))

        con.commit()
        return {"status": "OK", "venta_id": venta_id, "cliente_id": cliente_id,
                "detalle": "Venta registrada exitosamente en la base de datos."}
    except Exception as e:
        con.rollback()
        print(f"Error detallado en registrar_venta_db: {e}")
        return {"status": "ERROR", "detalle": str(e)}
    finally:
        con.close()


def listar_productos_db():
    """Lista todos los productos del catálogo (sembrado desde las fichas reales)."""
    init_vendedor_db()
    con = _conn()
    try:
        rows = con.execute(
            "SELECT id, sku, nombre, precio, stock FROM productos ORDER BY nombre"
        ).fetchall()
        productos = [dict(r) for r in rows]
        return {"status": "OK", "total": len(productos), "productos": productos}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}
    finally:
        con.close()


def obtener_producto_db(sku: str):
    """Obtiene la información de un producto específico por su SKU."""
    init_vendedor_db()
    con = _conn()
    try:
        row = con.execute("SELECT * FROM productos WHERE sku=? LIMIT 1", (sku,)).fetchone()
        if row:
            return {"status": "OK", "producto": dict(row)}
        return {"status": "NO_ENCONTRADO", "detalle": f"No se encontró producto con SKU '{sku}'."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}
    finally:
        con.close()
