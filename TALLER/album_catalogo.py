# -*- coding: utf-8 -*-
"""
album_catalogo.py  —  Generador de ÁLBUM DE CATÁLOGO para AURORA (Taller)

Lee CONFIG/catalogo_servicios.json, toma los artículos de sublimación,
busca UNA imagen de producto EN BLANCO por artículo (ddgs), la descarga a
UPLOADS/catalogo/ y genera un álbum HTML profesional (album.html) con
tarjetas: imagen + overlay "TU LOGO AQUÍ" + nombre + precio (1 pza).

Función principal: generar_album() -> dict
  { status, ruta_html, imagenes_ok, total_productos }

NOTA legal/honestidad: las imágenes son de referencia web (buscador). El
álbum incluye una nota al pie recordando usar fotos propias/autorizadas
para uso comercial. NO se afirma que sean libres de derechos.
"""

import os
import re
import json
import time
import html
import traceback

import requests

# ---------------------------------------------------------------------------
# Rutas (absolutas, Windows)
# ---------------------------------------------------------------------------
BASE = r"C:\AURORA.worktrees"
CONFIG_JSON = os.path.join(BASE, "CONFIG", "catalogo_servicios.json")
OUT_DIR = os.path.join(BASE, "UPLOADS", "catalogo")
IMG_DIR = os.path.join(OUT_DIR, "img")
HTML_OUT = os.path.join(OUT_DIR, "album.html")

MAX_PRODUCTOS = 15          # límite para no tardar demasiado
BUSQUEDA_RESULTADOS = 3     # imágenes candidatas por producto
HTTP_TIMEOUT = 15           # seg por descarga
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/122.0.0.0 Safari/537.36")

# Palabras clave que identifican artículos de SUBLIMACIÓN / promocionales
# (dentro de la lista "productos" del JSON). Se filtran por nombre.
CLAVES_SUBLIMACION = (
    "taza", "termo", "gorra", "mousepad", "playera", "cojin", "cojín",
    "vaso", "llavero", "boxer", "pluma", "tarro", "copa", "caballito",
    "rompecabezas", "pantufla", "azulejo", "libreta", "agenda",
    "lámina", "lamina", "aluminio", "mandil", "bote", "vidrio",
    "porta llavero", "skinny",
)

# Traducciones ES->EN para armar la query de imagen "en blanco"
TRADUCCIONES = {
    "taza": "mug",
    "taza mágica": "color changing magic mug",
    "taza magica": "color changing magic mug",
    "termo": "tumbler",
    "termo tipo yeti": "yeti style stainless steel tumbler",
    "termo skinny": "skinny tumbler",
    "termo dorado": "gold stainless steel tumbler",
    "gorra": "cap hat",
    "mousepad": "mouse pad",
    "playera": "t-shirt",
    "cojin": "pillow cushion",
    "cojín": "pillow cushion",
    "vaso": "cup",
    "vaso plástico": "plastic cup",
    "vaso plastico": "plastic cup",
    "llavero": "keychain",
    "boxer": "boxer shorts underwear",
    "pluma": "pen",
    "tarro": "beer mug jar",
    "tarro cervecero": "frosted beer mug",
    "copa": "wine glass",
    "caballito": "shot glass",
    "rompecabezas": "puzzle",
    "pantufla": "slippers",
    "azulejo": "ceramic tile",
    "libreta": "notebook",
    "agenda": "planner notebook",
    "lámina": "metal photo panel",
    "lamina": "metal photo panel",
    "aluminio": "aluminum photo panel",
    "mandil": "apron",
    "bote": "bottle",
    "bote chupón": "baby sippy bottle",
    "vidrio": "glass panel",
    "porta llavero": "keychain holder",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _precio_unitario(prod):
    """Precio de 1 pza: escalas[0].precio o 'precio'. Puede ser None."""
    escalas = prod.get("escalas")
    if isinstance(escalas, list) and escalas:
        p = escalas[0].get("precio")
        if p is not None:
            return p
    if prod.get("precio") is not None:
        return prod.get("precio")
    # productos por m2 / millar u otras variantes
    for k in ("precio_m2", "precio_millar"):
        if prod.get(k) is not None:
            return prod.get(k)
    return None


def _es_sublimacion(nombre):
    n = (nombre or "").lower()
    return any(clave in n for clave in CLAVES_SUBLIMACION)


def _query_ingles(nombre):
    """Construye la frase base en inglés para la búsqueda de imagen."""
    n = (nombre or "").lower()
    # busca la traducción más específica (frase más larga que aparezca)
    mejor = None
    for es, en in sorted(TRADUCCIONES.items(), key=lambda kv: -len(kv[0])):
        if es in n:
            mejor = en
            break
    if mejor is None:
        # fallback: usa el propio nombre limpio
        mejor = re.sub(r"[^a-záéíóúñ ]", " ", n).strip()
    return mejor


def _slug(nombre):
    s = (nombre or "producto").lower()
    s = re.sub(r"[áàä]", "a", s)
    s = re.sub(r"[éèë]", "e", s)
    s = re.sub(r"[íìï]", "i", s)
    s = re.sub(r"[óòö]", "o", s)
    s = re.sub(r"[úùü]", "u", s)
    s = re.sub(r"ñ", "n", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40] or "producto"


def _validar_imagen(ruta):
    """Verifica que el archivo bajado sea una imagen real y no diminuta."""
    try:
        from PIL import Image
        with Image.open(ruta) as im:
            im.verify()
        # tamaño mínimo razonable
        if os.path.getsize(ruta) < 3000:
            return False
        return True
    except Exception:
        return False


def _descargar_imagen(url, destino, session):
    try:
        r = session.get(url, timeout=HTTP_TIMEOUT, stream=True)
        if r.status_code != 200:
            return False
        ctype = r.headers.get("Content-Type", "")
        if "image" not in ctype and not url.lower().split("?")[0].endswith(
                (".jpg", ".jpeg", ".png", ".webp")):
            # a veces el content-type falta; intentamos igual pero validamos luego
            pass
        with open(destino, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        if _validar_imagen(destino):
            return True
        # limpia si no sirvió
        try:
            os.remove(destino)
        except OSError:
            pass
        return False
    except Exception:
        try:
            if os.path.exists(destino):
                os.remove(destino)
        except OSError:
            pass
        return False


def _buscar_y_bajar(prod, session):
    """Busca imágenes del producto en blanco y baja la primera que sirva.
    Devuelve la ruta relativa (img/xxx.ext) o None."""
    from ddgs import DDGS

    base_en = _query_ingles(prod["nombre"])
    query = f"{base_en} blank white sublimation mockup"
    slug = _slug(prod["nombre"])

    # Reutiliza imagen ya bajada en corridas previas (DDG throttlea seguido;
    # así las corridas acumulan cobertura en vez de perder aciertos).
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        previa = os.path.join(IMG_DIR, f"{slug}{ext}")
        if os.path.exists(previa) and _validar_imagen(previa):
            print(f"    [cache] {prod['nombre']} -> img/{slug}{ext}")
            return f"img/{slug}{ext}"

    # DuckDuckGo throttlea peticiones rápidas: reintenta con backoff.
    resultados = None
    ultimo_err = None
    for intento in range(1, 5):
        try:
            with DDGS() as ddgs:
                resultados = ddgs.images(query, max_results=BUSQUEDA_RESULTADOS)
            if resultados:
                break
            ultimo_err = "No results found."
        except Exception as e:
            ultimo_err = str(e)
        # backoff: 3, 6, 12 s
        espera = 3 * (2 ** (intento - 1))
        print(f"    [reintento {intento}] {prod['nombre']}: {ultimo_err} "
              f"— espero {espera}s")
        time.sleep(espera)

    if not resultados:
        print(f"    [sin-resultados] {prod['nombre']} :: '{query}' ({ultimo_err})")
        return None

    for i, res in enumerate(resultados):
        url = res.get("image") or res.get("thumbnail")
        if not url:
            continue
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"
        nombre_arch = f"{slug}{ext}"
        destino = os.path.join(IMG_DIR, nombre_arch)
        if _descargar_imagen(url, destino, session):
            print(f"    [ok] {prod['nombre']} -> img/{nombre_arch}")
            return f"img/{nombre_arch}"
        else:
            print(f"    [salta] candidata {i+1} falló: {url[:70]}")
    print(f"    [falla-total] {prod['nombre']}: ninguna candidata sirvió")
    return None


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def _fmt_precio(p):
    if p is None:
        return "Precio a cotizar"
    try:
        return f"${int(p)}" if float(p) == int(p) else f"${float(p):.2f}"
    except (ValueError, TypeError):
        return f"${p}"


def _tarjeta_html(prod, ruta_img):
    nombre = html.escape(prod["nombre"])
    precio = _fmt_precio(_precio_unitario(prod))
    if ruta_img:
        img_block = (
            f'<div class="foto">'
            f'<img src="{html.escape(ruta_img)}" alt="{nombre}" loading="lazy">'
            f'<span class="logo-overlay">TU LOGO AQUÍ</span>'
            f'</div>'
        )
    else:
        img_block = (
            f'<div class="foto sin-foto">'
            f'<span class="logo-overlay">TU LOGO AQUÍ</span>'
            f'<span class="ph">Sin imagen</span>'
            f'</div>'
        )
    return (
        '<article class="card">'
        f'{img_block}'
        f'<h2 class="nombre">{nombre}</h2>'
        f'<div class="precio">{precio} <small>/ 1 pza</small></div>'
        '</article>'
    )


def _construir_html(tarjetas, total, con_img):
    fecha = time.strftime("%d/%m/%Y")
    cards = "\n".join(tarjetas)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catálogo de Productos — Milens / Taller</title>
<style>
  :root {{
    --tinta:#1a1a2e; --acento:#e94560; --suave:#f6f6f9; --linea:#e3e3ec;
    --oro:#c9a24b;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; font-family:"Segoe UI",system-ui,Arial,sans-serif;
    color:var(--tinta); background:var(--suave); -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }}
  header.hero {{
    text-align:center; padding:34px 20px 22px;
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
    color:#fff;
  }}
  header.hero h1 {{ margin:0 0 6px; font-size:30px; letter-spacing:.5px; }}
  header.hero p {{ margin:0; opacity:.85; font-size:14px; }}
  .barra {{ height:5px; background:linear-gradient(90deg,var(--acento),var(--oro)); }}
  main {{ max-width:1180px; margin:0 auto; padding:26px 18px 10px; }}
  .grid {{
    display:grid; gap:20px;
    grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
  }}
  .card {{
    background:#fff; border:1px solid var(--linea); border-radius:14px;
    overflow:hidden; box-shadow:0 3px 10px rgba(20,20,50,.06);
    display:flex; flex-direction:column;
  }}
  .foto {{
    position:relative; aspect-ratio:1/1; background:#fafafd;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
  }}
  .foto img {{ width:100%; height:100%; object-fit:contain; padding:10px; }}
  .foto.sin-foto {{ background:repeating-linear-gradient(45deg,#f0f0f5,#f0f0f5 12px,#e8e8f0 12px,#e8e8f0 24px); }}
  .foto .ph {{ position:absolute; bottom:10px; color:#9a9ab0; font-size:12px; }}
  .logo-overlay {{
    position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) rotate(-8deg);
    font-weight:800; font-size:17px; letter-spacing:1px; text-transform:uppercase;
    color:#fff; background:rgba(233,69,96,.82); padding:7px 14px; border-radius:8px;
    border:2px dashed rgba(255,255,255,.9); box-shadow:0 2px 8px rgba(0,0,0,.25);
    text-align:center; pointer-events:none; white-space:nowrap;
  }}
  .nombre {{
    margin:12px 12px 4px; font-size:15px; line-height:1.25; font-weight:600;
    min-height:38px;
  }}
  .precio {{
    margin:auto 12px 14px; font-size:22px; font-weight:800; color:var(--acento);
  }}
  .precio small {{ font-size:12px; font-weight:500; color:#8a8aa0; }}
  footer {{
    max-width:1180px; margin:16px auto 40px; padding:16px 18px;
    font-size:12px; color:#6a6a80; border-top:1px solid var(--linea);
  }}
  footer .legal {{ color:#a33; }}
  @media print {{
    body {{ background:#fff; }}
    .card {{ box-shadow:none; break-inside:avoid; }}
    header.hero {{ padding:20px; }}
  }}
</style>
</head>
<body>
<header class="hero">
  <h1>Catálogo de Productos</h1>
  <p>Sublimación · Personalización · Milens / Taller — {fecha}</p>
</header>
<div class="barra"></div>
<main>
  <div class="grid">
{cards}
  </div>
</main>
<footer>
  <p><strong>{con_img}/{total} productos con imagen.</strong>
     El texto "TU LOGO AQUÍ" indica dónde se personaliza cada artículo.</p>
  <p class="legal">Imágenes de referencia web; para catálogo comercial usar
     fotos propias o autorizadas.</p>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
def generar_album():
    """Genera el álbum de catálogo. Devuelve dict con status y métricas."""
    try:
        os.makedirs(IMG_DIR, exist_ok=True)

        if not os.path.exists(CONFIG_JSON):
            return {"status": "error",
                    "error": f"No existe {CONFIG_JSON}",
                    "ruta_html": None, "imagenes_ok": 0, "total_productos": 0}

        with open(CONFIG_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        productos = data.get("productos", []) or []
        # filtra sublimación y limita
        sublim = [p for p in productos
                  if p.get("nombre") and _es_sublimacion(p["nombre"])]
        seleccion = sublim[:MAX_PRODUCTOS]

        if not seleccion:
            return {"status": "error",
                    "error": "No se encontraron productos de sublimación en el catálogo",
                    "ruta_html": None, "imagenes_ok": 0, "total_productos": 0}

        session = requests.Session()
        session.headers.update({"User-Agent": UA})

        tarjetas = []
        imagenes_ok = 0
        print(f"Procesando {len(seleccion)} productos de sublimación...")
        for idx, prod in enumerate(seleccion, 1):
            print(f"  {idx}/{len(seleccion)} {prod['nombre']}")
            ruta_img = _buscar_y_bajar(prod, session)
            if ruta_img:
                imagenes_ok += 1
            tarjetas.append(_tarjeta_html(prod, ruta_img))
            time.sleep(2.5)  # cortesía con el buscador (evita rate-limit DDG)

        html_doc = _construir_html(tarjetas, len(seleccion), imagenes_ok)
        with open(HTML_OUT, "w", encoding="utf-8") as f:
            f.write(html_doc)

        return {
            "status": "ok",
            "ruta_html": HTML_OUT,
            "imagenes_ok": imagenes_ok,
            "total_productos": len(seleccion),
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "error": str(e),
                "ruta_html": None, "imagenes_ok": 0, "total_productos": 0}


if __name__ == "__main__":
    print("=" * 60)
    print("GENERADOR DE ÁLBUM DE CATÁLOGO — AURORA / Taller")
    print("=" * 60)
    resultado = generar_album()
    print("-" * 60)
    print("RESULTADO:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if resultado["status"] == "ok":
        print(f"\nAbrir en navegador: {resultado['ruta_html']}")
