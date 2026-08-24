# -*- coding: utf-8 -*-
"""AURORA · Generador real de sitio web de una página, a partir de las
respuestas reales del cuestionario (MARKETING/cuestionario_sitio_web.py).

Autorizado por Anuar 2026-08-23: "siguete con el generador de sitioos web
sin simular nada y sin preguntar". No inventa contenido: si un campo no
llega, esa sección se omite en vez de rellenarse con texto de relleno.
Las fotos son las FOTOS REALES que mande el cliente (rutas locales) — nunca
imágenes de stock.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Template
except ImportError as e:
    raise ImportError(
        "Falta jinja2 (ya estaba instalado, confirmado 3.1.5). "
        "pip install jinja2") from e


_PLANTILLA = Template("""\
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ nombre }}</title>
<style>
  :root {
    --color-primario: {{ color_primario }};
    --color-secundario: {{ color_secundario }};
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         color: #222; line-height: 1.5; }
  header { background: var(--color-primario); color: #fff; padding: 2.5rem 1.5rem;
           text-align: center; }
  header h1 { font-size: 2.2rem; margin-bottom: .4rem; }
  header p { font-size: 1.1rem; opacity: .95; }
  nav { display: flex; justify-content: center; gap: 1.2rem; flex-wrap: wrap;
        background: var(--color-secundario); padding: .8rem; }
  nav a { color: #fff; text-decoration: none; font-weight: 600; }
  section { max-width: 900px; margin: 0 auto; padding: 2.5rem 1.5rem; }
  section h2 { color: var(--color-primario); margin-bottom: 1rem;
               border-bottom: 3px solid var(--color-secundario); display: inline-block; }
  .fotos { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
           gap: .8rem; }
  .fotos img { width: 100%; height: 220px; object-fit: cover; border-radius: 8px; }
  .portada { width: 100%; max-height: 420px; object-fit: cover; display: block; }
  .foto-menu { width: 100%; max-width: 500px; border-radius: 8px; margin-top: 1rem;
               display: block; }
  .platillos { display: grid; gap: .6rem; }
  .platillo { display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc;
              padding: .5rem 0; }
  .platillo strong { color: var(--color-primario); }
  .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
               gap: 1rem; }
  .info-grid div { background: #f7f7f7; padding: 1rem; border-radius: 8px; }
  .redes { display: flex; gap: 1rem; flex-wrap: wrap; }
  .redes a { color: var(--color-primario); font-weight: 600; text-decoration: none; }
  .promo { background: var(--color-secundario); color: #fff; padding: 1rem 1.5rem;
           border-radius: 8px; text-align: center; font-weight: 600; }
  .atencion { background: var(--color-primario); color: #fff; border-radius: 8px;
              padding: 1.5rem; text-align: center; }
  .atencion a.boton { display: inline-block; margin-top: .8rem; background: #25D366;
        color: #fff; padding: .7rem 1.4rem; border-radius: 50px; text-decoration: none;
        font-weight: 700; }
  .whatsapp-flotante { position: fixed; bottom: 20px; right: 20px; background: #25D366;
        color: #fff; padding: .9rem 1.3rem; border-radius: 50px; text-decoration: none;
        font-weight: 700; box-shadow: 0 4px 10px rgba(0,0,0,.25); }
  footer { text-align: center; padding: 1.5rem; background: #222; color: #ccc;
           font-size: .85rem; }
</style>
</head>
<body>
<header>
  <h1>{{ nombre }}</h1>
  {% if frase %}<p>{{ frase }}</p>{% endif %}
</header>
{% if foto_portada %}<img class="portada" src="img/{{ foto_portada }}" alt="{{ nombre }}">{% endif %}
<nav>
  {% if platillos or foto_menu %}<a href="#menu">Menú</a>{% endif %}
  {% if telefono %}<a href="#atencion">Atención a Cliente</a>{% endif %}
  {% if horario or direccion %}<a href="#info">Información</a>{% endif %}
  {% if fotos %}<a href="#fotos">Fotos</a>{% endif %}
  {% if redes %}<a href="#redes">Redes</a>{% endif %}
</nav>

{% if promociones %}
<section>
  <div class="promo">{{ promociones }}</div>
</section>
{% endif %}

{% if platillos or foto_menu %}
<section id="menu">
  <h2>Menú</h2>
  {% if especialidad %}<p style="margin-bottom:1rem">{{ especialidad }}</p>{% endif %}
  {% if platillos %}
  <div class="platillos">
    {% for p in platillos %}
    <div class="platillo"><span>{{ p.nombre }}</span><strong>${{ p.precio }}</strong></div>
    {% endfor %}
  </div>
  {% endif %}
  {% if foto_menu %}<img class="foto-menu" src="img/{{ foto_menu }}" alt="Menú de {{ nombre }}">{% endif %}
</section>
{% endif %}

{% if telefono %}
<section id="atencion">
  <div class="atencion">
    <h2 style="color:#fff;border:none">¿Dudas? Contáctanos</h2>
    <p>Escríbenos directo y te respondemos.</p>
    <a class="boton" href="https://wa.me/{{ telefono_wa }}" target="_blank" rel="noopener">
      Escribir por WhatsApp
    </a>
  </div>
</section>
{% endif %}

{% if fotos %}
<section id="fotos">
  <h2>Fotos</h2>
  <div class="fotos">
    {% for f in fotos %}<img src="img/{{ f }}" alt="{{ nombre }}">{% endfor %}
  </div>
</section>
{% endif %}

{% if horario or direccion or servicio %}
<section id="info">
  <h2>Información</h2>
  <div class="info-grid">
    {% if direccion %}<div><strong>Dirección</strong><br>{{ direccion }}</div>{% endif %}
    {% if horario %}<div><strong>Horario</strong><br>{{ horario }}</div>{% endif %}
    {% if servicio %}<div><strong>Servicio</strong><br>{{ servicio }}</div>{% endif %}
    {% if telefono %}<div><strong>Teléfono</strong><br>{{ telefono }}</div>{% endif %}
  </div>
</section>
{% endif %}

{% if redes %}
<section id="redes">
  <h2>Síguenos</h2>
  <div class="redes">
    {% for nombre_red, url in redes.items() %}
    <a href="{{ url }}" target="_blank" rel="noopener">{{ nombre_red }}</a>
    {% endfor %}
  </div>
</section>
{% endif %}

<footer>{{ nombre }} {% if direccion %}· {{ direccion }}{% endif %}</footer>

{% if telefono %}
<a class="whatsapp-flotante"
   href="https://wa.me/{{ telefono_wa }}" target="_blank" rel="noopener">
   WhatsApp
</a>
{% endif %}
</body>
</html>
""")


def _telefono_wa(telefono: str) -> str:
    """Deja solo dígitos y antepone 52 si no trae lada de país."""
    digitos = "".join(c for c in (telefono or "") if c.isdigit())
    if digitos and not digitos.startswith("52") and len(digitos) == 10:
        digitos = "52" + digitos
    return digitos


def generar_sitio(datos: Dict[str, Any], carpeta_salida: str,
                   fotos_locales: Optional[List[str]] = None,
                   foto_portada: Optional[str] = None,
                   foto_menu: Optional[str] = None) -> Dict[str, Any]:
    """Genera el sitio real (index.html + carpeta img/) de las respuestas del
    cuestionario. No inventa nada: los campos que no lleguen simplemente no
    aparecen en el sitio.

    datos: dict con las llaves del cuestionario (nombre, direccion, horario,
           telefono, redes, especialidad, platillos, servicio, colores,
           frase, promociones, dominio_sugerido).
    fotos_locales: rutas REALES a fotos que mandó el cliente para la galería
           (se copian a carpeta_salida/img/, nunca se inventan ni se bajan
           de internet). Se recorta a 6 — pedido real de Anuar 2026-08-23
           ("1 foto de portada, foto del menú, unas 6 imágenes en total").
    foto_portada: ruta real a la foto de portada (se muestra grande, debajo
           del encabezado).
    foto_menu: ruta real a una foto del menú físico (se muestra dentro de
           la sección Menú, junto a los platillos si los hay).
    """
    if not datos.get("nombre"):
        return {"status": "error",
                "mensaje": "Falta el nombre del negocio — es el único dato "
                           "obligatorio, sin él no hay título ni footer."}

    salida = Path(carpeta_salida)
    salida.mkdir(parents=True, exist_ok=True)
    img_dir = salida / "img"

    def _copiar(ruta: str, nombre_base: str) -> str:
        origen = Path(ruta)
        if not origen.exists():
            return ""
        img_dir.mkdir(exist_ok=True)
        destino = img_dir / f"{nombre_base}{origen.suffix.lower()}"
        shutil.copy2(origen, destino)
        return destino.name

    nombre_portada = _copiar(foto_portada, "portada") if foto_portada else ""
    nombre_menu = _copiar(foto_menu, "menu") if foto_menu else ""

    fotos_copiadas = []
    for i, ruta in enumerate((fotos_locales or [])[:6]):
        origen = Path(ruta)
        if not origen.exists():
            continue
        img_dir.mkdir(exist_ok=True)
        destino = img_dir / f"foto_{i+1}{origen.suffix.lower()}"
        shutil.copy2(origen, destino)
        fotos_copiadas.append(destino.name)

    colores = datos.get("colores") or ["#c0392b", "#2c3e50"]
    color_primario = colores[0]
    color_secundario = colores[1] if len(colores) > 1 else colores[0]

    html = _PLANTILLA.render(
        nombre=datos.get("nombre", ""),
        frase=datos.get("frase", ""),
        direccion=datos.get("direccion", ""),
        horario=datos.get("horario", ""),
        telefono=datos.get("telefono", ""),
        telefono_wa=_telefono_wa(datos.get("telefono", "")),
        especialidad=datos.get("especialidad", ""),
        platillos=datos.get("platillos") or [],
        servicio=datos.get("servicio", ""),
        promociones=datos.get("promociones", ""),
        redes=datos.get("redes") or {},
        fotos=fotos_copiadas,
        foto_portada=nombre_portada,
        foto_menu=nombre_menu,
        color_primario=color_primario,
        color_secundario=color_secundario,
    )

    ruta_html = salida / "index.html"
    ruta_html.write_text(html, encoding="utf-8")

    bio = _generar_bios(datos)
    ruta_bio = salida / "redes_bio.txt"
    ruta_bio.write_text(bio, encoding="utf-8")

    return {"status": "ok",
            "index_html": str(ruta_html),
            "bios": str(ruta_bio),
            "fotos_copiadas": len(fotos_copiadas)}


def _generar_bios(datos: Dict[str, Any]) -> str:
    """Textos reales listos para pegar en bio de Instagram/Facebook/TikTok,
    armados SOLO con lo que el cliente dio — sin relleno inventado.
    """
    nombre = datos.get("nombre", "")
    frase = datos.get("frase", "")
    direccion = datos.get("direccion", "")
    telefono = datos.get("telefono", "")
    horario = datos.get("horario", "")

    partes_bio = [p for p in [nombre, frase] if p]
    linea1 = " · ".join(partes_bio)
    partes_datos = [p for p in [direccion, horario] if p]
    linea2 = " | ".join(partes_datos)
    linea3 = f"📱 {telefono}" if telefono else ""

    bio_corta = "\n".join(x for x in [linea1, linea2, linea3] if x)

    return (
        "=== BIO Instagram/Facebook (pegar tal cual) ===\n"
        f"{bio_corta}\n\n"
        "=== Primer post sugerido ===\n"
        f"¡Ya estamos en línea! {nombre}"
        f"{' — ' + frase if frase else ''}. "
        f"{('Escríbenos: ' + telefono) if telefono else ''}\n"
    )


if __name__ == "__main__":
    # Prueba de humo con datos de ejemplo — NO es el entregable del cliente
    # real, solo confirma que el generador corre de punta a punta antes de
    # tener las respuestas reales del cuestionario.
    import tempfile
    demo = {
        "nombre": "PRUEBA — no es el cliente real",
        "frase": "texto de prueba del generador",
        "direccion": "",
        "horario": "",
        "telefono": "3312345678",
        "especialidad": "",
        "platillos": [{"nombre": "Platillo de prueba", "precio": "99"}],
        "servicio": "",
        "colores": ["#c0392b", "#2c3e50"],
        "promociones": "",
        "redes": {"Facebook": "https://facebook.com/prueba"},
    }
    salida_demo = Path(tempfile.gettempdir()) / "aurora_sitio_demo"
    r = generar_sitio(demo, str(salida_demo))
    print(r)
