# -*- coding: utf-8 -*-
"""AURORA · Contrato electrónico del generador de sitios + redes.

Anuar, 2026-08-23: *"generar un contrato electrónico para que al enviar la
primer propuesta el cliente lo firme vía electrónica... describir todo como
debe ser y deslindar responsabilidades para ambas partes"*.

OJO — esto NO sustituye una revisión de un abogado real. Es un borrador
completo y honesto para operar YA con algo mejor que nada (su situación real
no permite pagar asesoría legal hoy), pero si el volumen de contratos crece,
vale la pena que un abogado lo revise una vez.

La "firma electrónica" aquí es la real y honesta para un negocio chico: el
cliente escribe su nombre completo, marca que aceptó, y el SERVIDOR (no el
navegador del cliente, que se puede falsear) sella fecha/hora e IP. Es
consentimiento documentado, no una firma con certificado — se lo dice claro
al cliente en el propio documento, sin fingir ser algo que no es.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jinja2 import Template
except ImportError as e:
    raise ImportError("Falta jinja2 (ya estaba instalado, 3.1.5).") from e

ROOT = Path(__file__).parent.parent
_LEDGER = ROOT / "CONFIG" / "contratos_firmados.json"


_CONTRATO_TEXTO = Template("""\
CONTRATO DE PRESTACIÓN DE SERVICIOS
Creación de sitio web y presencia en redes sociales

Entre {{ prestador_nombre }} (en adelante "el Prestador") y
{{ cliente_nombre }}, representante de {{ negocio_nombre }}
(en adelante "el Cliente"), se celebra el presente contrato bajo las
siguientes cláusulas:

────────────────────────────────────────────────────────────────
1. OBJETO DEL CONTRATO
────────────────────────────────────────────────────────────────
El Prestador se obliga a crear para el Cliente un sitio web y presencia
en redes sociales, nivel de servicio **{{ nivel }}**, que incluye:

{% for item in incluye %}  · {{ item }}
{% endfor %}
{% if extras %}
Extras contratados adicionalmente:
{% for e in extras %}  · {{ e.nombre }} — ${{ '%.2f'|format(e.precio) }} MXN
{% endfor %}
{% endif %}

────────────────────────────────────────────────────────────────
2. PRECIO Y FORMA DE PAGO
────────────────────────────────────────────────────────────────
Precio total: ${{ '%.2f'|format(precio_total) }} MXN.
Forma de pago: {{ anticipo_pct }}% de anticipo (${{ '%.2f'|format(precio_total * anticipo_pct / 100) }} MXN)
para iniciar el trabajo, y el saldo (${{ '%.2f'|format(precio_total * (100-anticipo_pct) / 100) }} MXN)
contra entrega del sitio funcionando.
El anticipo cubre el trabajo ya realizado y NO es reembolsable si el
Cliente cancela después de iniciado el proyecto.

────────────────────────────────────────────────────────────────
3. DOMINIO (si aplica)
────────────────────────────────────────────────────────────────
{% if incluye_dominio %}
El Cliente autoriza al Prestador a adquirir el dominio a nombre del
Prestador, cuyo costo real más un cargo del 20% por gestión corre por
cuenta del Cliente. El Prestador administra el dominio mientras dure la
relación de servicio. Si el Cliente solicita en cualquier momento la
titularidad o transferencia del dominio, el Prestador la realizará sin
costo adicional más allá de los cargos que el propio registrador cobre.
{% else %}
Este proyecto no incluye la gestión de un dominio propio.
{% endif %}

────────────────────────────────────────────────────────────────
4. CONTENIDO E INSUMOS QUE PROPORCIONA EL CLIENTE
────────────────────────────────────────────────────────────────
El Cliente es el único responsable de que la información, fotografías,
logotipos, precios y textos que entregue sean verídicos y de que tenga
los derechos necesarios para usarlos. El Prestador NO investiga ni
verifica la veracidad de esa información, y no se hace responsable por
reclamos de terceros derivados de contenido proporcionado por el Cliente
(por ejemplo, fotografías sin derechos de uso, o información comercial
falsa).

────────────────────────────────────────────────────────────────
5. ENTREGA Y GARANTÍA
────────────────────────────────────────────────────────────────
El Prestador entregará el sitio con un usuario y contraseña de acceso.
El Cliente debe cambiar la contraseña por default al tomar posesión; el
Prestador no se hace responsable por accesos no autorizados ocurridos
DESPUÉS de la entrega si el Cliente no cambió esa contraseña.

Garantía de 30 días naturales a partir de la entrega: cualquier error o
falla del sitio TAL COMO FUE ENTREGADO se corrige sin costo. La garantía
NO cubre: cambios de contenido, funciones no contratadas, ni fallas
originadas por cambios que el Cliente o un tercero hayan hecho al sitio
después de la entrega.

────────────────────────────────────────────────────────────────
6. SOPORTE POSTERIOR A LA GARANTÍA
────────────────────────────────────────────────────────────────
Pasados los 30 días de garantía, cualquier cambio de contenido o ajuste
(fotos, precios, textos, horario) se cobra a razón de ${{ costo_sesion }} MXN
por sesión de hasta 30 minutos. Cambios grandes (rediseño, nuevas
secciones o funciones no incluidas en el nivel contratado) se cotizan
aparte.

────────────────────────────────────────────────────────────────
7. LO QUE EL PRESTADOR NO GARANTIZA
────────────────────────────────────────────────────────────────
El Prestador no garantiza resultados comerciales (ventas, tráfico,
seguidores): el servicio es la creación y correcto funcionamiento del
sitio y las redes, no el éxito del negocio del Cliente. El Prestador no
es responsable de caídas, cambios de política o suspensión de servicios
de terceros que el sitio utilice (Meta/Facebook/Instagram, WhatsApp,
TikTok, el proveedor de hosting o el registrador de dominio), al ser
plataformas fuera de su control.
{% if nivel == 'Premium' %}
Para la tienda con pagos del nivel Premium: el Cliente debe tener su
PROPIA cuenta de procesador de pagos (Stripe, PayPal u otro). El
Prestador NO recibe, retiene ni es responsable de los fondos de las
ventas del Cliente a sus propios consumidores.
{% endif %}

────────────────────────────────────────────────────────────────
8. PROPIEDAD DEL TRABAJO ENTREGADO
────────────────────────────────────────────────────────────────
Una vez pagado el precio total, el sitio web y su contenido son
propiedad del Cliente. El código queda documentado y es exportable, de
forma que el propio Cliente o un tercero de sistemas que el Cliente
designe pueda administrarlo en el futuro sin depender exclusivamente del
Prestador.

────────────────────────────────────────────────────────────────
9. CONFIDENCIALIDAD
────────────────────────────────────────────────────────────────
Ambas partes se comprometen a no divulgar información comercial
confidencial del otro (precios internos, datos de clientes, credenciales)
obtenida con motivo de este contrato.

────────────────────────────────────────────────────────────────
10. ACEPTACIÓN Y FIRMA ELECTRÓNICA
────────────────────────────────────────────────────────────────
Este documento se acepta de forma electrónica: al escribir su nombre
completo y confirmar, el Cliente declara haber leído y estar de acuerdo
con todas las cláusulas anteriores. El sistema registra el nombre
escrito, la fecha y hora del servidor, y la dirección IP desde la que se
confirmó, como constancia de la aceptación. Esto es un registro de
consentimiento documentado, no una firma con certificado digital.

Contrato generado: {{ fecha_generado }}
Folio: {{ contrato_id }}
""")


_PAGINA_FIRMA = Template("""\
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Contrato — {{ negocio_nombre }}</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; max-width: 760px;
         margin: 0 auto; padding: 2rem 1.2rem; line-height: 1.6; color: #222; }
  pre { white-space: pre-wrap; font-family: inherit; background: #f7f7f7;
        padding: 1.5rem; border-radius: 8px; font-size: .92rem; }
  .firma { margin-top: 2rem; padding: 1.5rem; background: #fff8e6; border-radius: 8px;
           border: 1px solid #e6d59a; }
  input[type=text] { width: 100%; padding: .7rem; font-size: 1rem; margin: .5rem 0 1rem;
                      box-sizing: border-box; }
  button { background: #2c3e50; color: #fff; padding: .8rem 1.6rem; border: none;
           border-radius: 6px; font-size: 1rem; cursor: pointer; }
  .aviso { font-size: .85rem; color: #666; margin-top: .6rem; }
  #resultado { margin-top: 1rem; font-weight: 600; }
</style>
</head>
<body>
<pre>{{ texto_contrato }}</pre>

<div class="firma" id="bloque-firma">
  <h3>Firmar y aceptar</h3>
  <label>Nombre completo de quien firma:</label>
  <input type="text" id="nombre_firmante" placeholder="Escribe tu nombre completo">
  <label><input type="checkbox" id="acepto"> He leído y acepto todas las cláusulas de este contrato.</label>
  <br><br>
  <button onclick="firmar()">Firmar y aceptar</button>
  <div id="resultado"></div>
  <p class="aviso">Al firmar, el servidor registra tu nombre, la fecha/hora y tu
  dirección IP como constancia de aceptación (no es una firma con certificado
  digital).</p>
</div>

<script>
async function firmar() {
  const nombre = document.getElementById('nombre_firmante').value.trim();
  const acepto = document.getElementById('acepto').checked;
  const res = document.getElementById('resultado');
  if (!nombre) { res.textContent = 'Escribe tu nombre completo.'; return; }
  if (!acepto) { res.textContent = 'Debes marcar que aceptas las cláusulas.'; return; }
  try {
    const r = await fetch(window.location.pathname + '/firmar', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({nombre_completo: nombre})
    });
    const data = await r.json();
    if (data.status === 'ok') {
      res.style.color = '#1a7f37';
      res.textContent = 'Firmado correctamente el ' + data.fecha + '. Gracias.';
      document.getElementById('bloque-firma').querySelectorAll('input,button').forEach(
        el => el.disabled = true);
    } else {
      res.style.color = '#c0392b';
      res.textContent = data.mensaje || 'No se pudo registrar la firma.';
    }
  } catch (e) {
    res.style.color = '#c0392b';
    res.textContent = 'Error de conexión, intenta de nuevo.';
  }
}
</script>
</body>
</html>
""")


NIVELES_INCLUYE = {
    "Básico": [
        "Sitio web de una página, responsivo, diseño a la medida",
        "Gráficos profesionales de marca",
        "3 redes sociales sincronizadas visualmente (Facebook, Instagram, TikTok)",
        "Publicación inicial real en Facebook e Instagram",
        "Garantía de 30 días por errores del sitio entregado",
    ],
    "Plus": [
        "Todo lo incluido en el nivel Básico",
    ],
    "Premium": [
        "Todo lo incluido en el nivel Plus",
    ],
}


def _leer_ledger() -> Dict[str, Any]:
    if _LEDGER.exists():
        try:
            return json.loads(_LEDGER.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _guardar_ledger(datos: Dict[str, Any]) -> None:
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def generar_contrato(contrato_id: str, datos: Dict[str, Any],
                      carpeta_salida: str, fecha_generado: str) -> Dict[str, Any]:
    """Genera el HTML del contrato con el formulario de firma real.

    datos: cliente_nombre, negocio_nombre, prestador_nombre, nivel
           (Básico/Plus/Premium), extras (lista de {"nombre","precio"}),
           precio_total, anticipo_pct (default 50), incluye_dominio (bool),
           costo_sesion (default 300).
    fecha_generado: pasada por quien llama (este módulo no puede usar
           datetime.now() de forma determinista en algunos entornos; se
           pide explícita para que el folio sea siempre real y trazable).
    """
    faltan = [k for k in ("cliente_nombre", "negocio_nombre", "precio_total")
              if not datos.get(k)]
    if faltan:
        return {"status": "error",
                "mensaje": f"Faltan datos obligatorios: {', '.join(faltan)}"}

    nivel = datos.get("nivel", "Básico")
    texto = _CONTRATO_TEXTO.render(
        prestador_nombre=datos.get("prestador_nombre", "El Prestador (definir nombre comercial)"),
        cliente_nombre=datos["cliente_nombre"],
        negocio_nombre=datos["negocio_nombre"],
        nivel=nivel,
        incluye=NIVELES_INCLUYE.get(nivel, NIVELES_INCLUYE["Básico"]),
        extras=datos.get("extras") or [],
        precio_total=float(datos["precio_total"]),
        anticipo_pct=datos.get("anticipo_pct", 50),
        incluye_dominio=datos.get("incluye_dominio", False),
        costo_sesion=datos.get("costo_sesion", 300),
        fecha_generado=fecha_generado,
        contrato_id=contrato_id,
    )

    html = _PAGINA_FIRMA.render(
        negocio_nombre=datos["negocio_nombre"],
        texto_contrato=texto,
    )

    salida = Path(carpeta_salida)
    salida.mkdir(parents=True, exist_ok=True)
    ruta_html = salida / f"contrato_{contrato_id}.html"
    ruta_html.write_text(html, encoding="utf-8")

    ledger = _leer_ledger()
    ledger[contrato_id] = {
        "status": "pendiente_firma",
        "datos": datos,
        "texto_contrato": texto,
        "fecha_generado": fecha_generado,
        "ruta_html": str(ruta_html),
    }
    _guardar_ledger(ledger)

    return {"status": "ok", "contrato_id": contrato_id, "ruta_html": str(ruta_html)}


def registrar_firma(contrato_id: str, nombre_completo: str, ip: str,
                     fecha_firma: str) -> Dict[str, Any]:
    """Registra la aceptación real. fecha_firma la pone quien llama (el
    servidor, con su reloj real) — nunca el navegador del cliente, que se
    puede falsear.
    """
    ledger = _leer_ledger()
    registro = ledger.get(contrato_id)
    if not registro:
        return {"status": "error", "mensaje": "Ese contrato no existe."}
    if registro["status"] == "firmado":
        return {"status": "error",
                "mensaje": f"Ya fue firmado el {registro.get('fecha_firma')} "
                           f"por {registro.get('nombre_firmante')}."}
    if not nombre_completo or not nombre_completo.strip():
        return {"status": "error", "mensaje": "Falta el nombre completo."}

    registro["status"] = "firmado"
    registro["nombre_firmante"] = nombre_completo.strip()
    registro["fecha_firma"] = fecha_firma
    registro["ip_firma"] = ip
    ledger[contrato_id] = registro
    _guardar_ledger(ledger)

    return {"status": "ok", "fecha": fecha_firma}


def consultar_contrato(contrato_id: str) -> Dict[str, Any]:
    ledger = _leer_ledger()
    registro = ledger.get(contrato_id)
    if not registro:
        return {"status": "error", "mensaje": "Ese contrato no existe."}
    return {"status": "ok", **registro}
