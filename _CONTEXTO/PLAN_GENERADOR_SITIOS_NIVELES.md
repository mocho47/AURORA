# Generador de sitios + redes — niveles de venta

Escrito por Claude, 2026-08-23, a petición de Anuar: *"realiza tu listado de
condiciones... desde tu perspectiva no la mía... 3 niveles de venta"*.
Es una PROPUESTA para que él decida — no está construido, solo es el
contexto/diseño (ver también `generador_sitios_contexto.md` en memoria).

Ancla real: ya cobró **$2,800 MXN** por sitio + 3 redes sincronizadas a un
cliente real (restaurant) — ese número YA está validado en el mercado, no
se inventa, se usa como base del nivel Básico.

## Cuestionario único (aplica a los 3 niveles)
Uno solo (`MARKETING/cuestionario_sitio_web.py`, ya existe, agregar estos
campos): nombre/giro/dirección/horario/teléfono/redes actuales, **colores
de marca y estilo visual** (moderno/clásico/minimalista/juguetón),
productos o platillos con precio, frase diferenciadora, promociones, fotos
o logo, nombre de dominio deseado, y qué nivel/extras quiere.

## NIVEL BÁSICO — $2,800 MXN
- Sitio de una página, responsivo, diseño a la medida del cuestionario.
- Gráficos profesionales — SIEMPRE incluido en cualquier nivel, es el piso
  de calidad, no un extra.
- 3 redes sincronizadas visualmente (mismo logo/colores/bio): Facebook,
  Instagram, TikTok. Publicación inicial real en FB/IG (infraestructura ya
  existe en AURORA). TikTok sin API real — se entrega la cuenta lista, la
  publicación ahí queda manual (no prometerlo automático).
- Dominio: lo paga el cliente (ver abajo).
- Entrega con usuario/contraseña por default **888888** — el cliente la
  cambia al tomar posesión.
- Garantía de **30 días**: cualquier error del sitio ENTREGADO se corrige
  sin costo.
- NO incluye actualizaciones de contenido después de entregar (fuera de
  bugs de garantía) — eso se cobra por sesión.

## NIVEL PLUS — $2,800 + extras que el cliente elija
Todo lo del Básico, más (el cliente elige cuáles, cada uno con costo
propio para ajustarse a su presupuesto):
- **Bot de WhatsApp de preguntas frecuentes** (+$1,500): contesta
  horario/menú/dirección/promos con el cerebro real de AURORA y los datos
  del cuestionario. Requiere que el cliente tenga o autorice su número de
  WhatsApp Business.
- **Panel de administración simple** (+$800): el cliente cambia fotos,
  precios y horario sin tocar código y sin pedirle nada a Anuar — reduce
  la fricción de "actualización" del lado de Anuar.
- **SEO básico** (+$500): metadatos, sitemap, mejor posición en buscadores.
- **Formulario de contacto real** (+$300): manda a su correo/WhatsApp.
- **Botón de reseñas** (+$200): enlaza a Google Reviews.
- **Bilingüe ES/EN** (+$600): relevante si el negocio recibe turistas
  (zona GDL con flujo turístico).
- **Sitio interactivo con sección de dinámicas para seguidores** (+$700):
  encuestas, sorteos o retos simples embebidos en el sitio, pensados para
  que el negocio del cliente enganche a sus seguidores de redes — pedido
  de Anuar 2026-08-23, "desde el plan Plus".

## NIVEL PREMIUM — Plus completo + extras premium
Todo lo del Plus, más:
- **Bot de WhatsApp con reservaciones/pedidos** (+$2,500, reemplaza al bot
  simple de Plus): agenda real conectada (Google Calendar o similar),
  confirma/cancela citas o pedidos automáticamente.
- **Catálogo/tienda con pagos** (+$2,000): el cliente debe tener SU PROPIA
  cuenta de Stripe/PayPal — Anuar no debe ser quien recibe el dinero de
  las ventas del cliente final (riesgo legal y fiscal real, explicarlo
  claro antes de vender esto).
- **Facturación electrónica** (costo real pass-through, ~$150-300/mes del
  proveedor + gestión): requiere RFC/certificados del PROPIO negocio del
  cliente. No es un extra de una sola vez, es un servicio recurrente de
  terceros — no absorberlo en el precio fijo.
- **Blog/noticias con publicación cruzada a redes** (+$1,200).
- **Reportes mensuales de tráfico** (+$400): Google Analytics conectado,
  resumen simple mensual.
- Traspaso administrable a terceros: código documentado y exportable para
  que un sistemas del cliente lo mantenga si algún día Anuar no está —
  viene incluido por CÓMO se construye (HTML/CSS simple, sin dependencias
  raras), no es un módulo aparte que se cobre.

## Dominio
- Costo real (~$300-500 MXN el primer año, .com o .mx) + **20% de
  trámite** recomendado (ejemplo: $400 real → $480 cobrado al cliente).
  Anuar lo compra y administra a su cuenta.
- Aclarar en la entrega qué pasa si algún día Anuar deja de dar soporte —
  el cliente no debe quedar sin poder renovar su propio dominio.

## Soporte después de entregado (cualquier nivel, después de los 30 días)
- **$300 MXN por sesión de hasta 30 minutos**: cambiar fotos, precios,
  texto, horario.
- Cambios grandes (rediseño, nueva sección) se cotizan aparte, no cuentan
  como "sesión".
- Opcional para Plus/Premium: mantenimiento mensual de **$350 MXN/mes**
  con hasta 2 sesiones incluidas — más conveniente para el cliente que
  varias sesiones sueltas, y es ingreso recurrente real para Anuar.

## Del lado de Anuar (la herramienta interna, para que sea "muy amigable")
- Un solo flujo: cuestionario contestado → Anuar pega/sube las respuestas
  en un panel simple dentro de AURORA → vista previa → un clic genera →
  un clic publica. Nada de tocar código.
- El generador avisa CLARO qué falta antes de poder entregar (ej. "falta
  el WhatsApp del negocio para activar el bot de Plus") — nunca inventa un
  dato que no llegó, mismo candado de honestidad que ya tiene AURORA.

## Estado: SOLO CONTEXTO — no construido
Confirmar con Anuar los precios y qué extras entran en cada nivel antes de
tocar código. Cuando dé luz verde, el orden natural es: 1) cuestionario
final con los campos de estilo, 2) panel simple del lado de Anuar, 3) el
extra que el primer cliente real (restaurant) realmente pida.
