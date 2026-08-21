# Paquete de Marca — plan comercial y técnico para Milens
### 2026-08-20 · Escrito para decidir, no para ejecutar todavía

---

## Resumen ejecutivo (léelo primero)

Hay DOS caminos, y no son el mismo tamaño de esfuerzo:

**El camino rápido — dinero esta semana.** Tu clienta del salón ya está en
la puerta. La lámpara y el letrero luminoso **ya se pueden cotizar y cortar
HOY** con lo que AURORA tiene ahorita mismo (nada nuevo que construir). Las
tarjetas son diseño puro, lo sabes hacer. Esto no espera al plan grande.

**El camino grande — el cuestionario único que arma todo.** Es real, es
construible, y el hueco de mercado que tú mismo detectaste (en GDL solo dan
tarjetas o cosas básicas) lo confirma. Pero es varias piezas nuevas: un
módulo de sitios web, uno que llame a Nano Banana para las 3 variantes, y la
ficha nueva que junte todo. No es una tarde de trabajo.

**Mi recomendación:** cobra la lámpara y el letrero de tu clienta esta
semana con lo que ya existe. De esa cotización real sale la receta. El
cuestionario grande se arma después, sobre un caso que sí cobraste — no en
abstracto. Así el camino rápido financia el camino grande, en vez de que el
camino grande te quite tiempo del camino rápido.

No investigué software de código abierto para la lámpara ni las tarjetas —
esas piezas ya las resuelve AURORA sola. La investigación de código abierto
(más abajo) es solo para la pieza que SÍ falta: sitio web + logo con IA.

---

## 1. Plan comercial para Milens

### El hueco de mercado (tu propia observación, validada)
En Guadalajara, quien da servicio publicitario normalmente da UNA pieza:
tarjetas, o un logo, o nada más el letrero. Nadie arma las 4 piezas juntas
(sitio, redes, tarjetas, letrero físico) desde un solo lugar, con el mismo
diseño repetido en todas. Ese es el hueco: no "hacer publicidad", sino
**la consistencia entre lo digital y lo físico**, que es justo lo que
Milens ya sabe hacer del lado físico (láser, sublimado) y lo que a ti te
sobra del lado de negocio (ya trabajaste el camino conmigo).

### Los niveles de servicio (segmentado, como tú lo pediste)
Cada pieza es un SÍ/NO independiente en el cuestionario inicial:

| Pieza | Quién la resuelve hoy | Nueva o ya existe |
|---|---|---|
| Letrero luminoso con logo | AURORA (texto_a_corte + láser) | Ya existe |
| Lámpara / mobiliario de exhibición | AURORA (cajas_boxes.py, 42 diseños) | Ya existe |
| Tarjetas de presentación | AURORA (mismo motor de etiquetas.py, PDF vectorial) | Ya existe, se adapta |
| Logo / identidad (3 variantes) | AURORA + Nano Banana | Nueva — pieza chica |
| Sitio web (3 variantes) | AURORA + plantilla | Nueva — pieza mediana |
| Redes sociales (cuenta real) | Anuar / esposa / hija, presenciales | Humano, no AURORA |
| Contenido y calendario de redes | AURORA (ya existe: estratega_shorts, asesor_marketing) | Ya existe |

### Precio: la fórmula real + la mano de obra humana
La fórmula que ya usa Milens no cambia:

```
PRECIO = (materiales × 1.20) + corte $8/min (20 mm/s) + diseño + instalación
```

Para las piezas digitales (sitio, redes, logo) no hay "material" ni "corte"
— se cobra como **diseño desde cero** ($20 base, tu propio número) más una
**cuota de mano de obra humana** cuando se elige que Anuar/esposa/hija
abran cuentas o hagan movimientos con el cliente presente. Esa cuota es
tuya por dictar (no la inventé): tiene que cubrir el tiempo real de la
visita, no solo el trabajo de AURORA.

### Ejemplo cerrado — tu clienta del salón (números reales del catálogo, lámpara aún sin medir)

Con MDF 2.7mm a $110/hoja (122×244cm) y vinil color a $28/m (60cm), del
catálogo real de Milens:

**Letrero luminoso con logo (ejemplo: 30×15 cm, MDF + vinil recortado)**
```
materiales (MDF ~$8 + vinil ~$12) × 1.20    $ 24.00
corte (~6 min × $8)                          $ 48.00
diseño (logo, trae imagen)                   $ 15.00
instalación                                  $ 20.00
                                    TOTAL    $107.00
```
*(Cifra estimada con la fórmula real — se confirma exacta en cuanto se
genere el DXF real del letrero con sus medidas finales, antes de cobrarla.)*

**Lámpara (ejemplo: TriangleLamp, MDF, sin medir todavía)** — se cotiza
igual que cualquier caja de `cajas_boxes.py`: se genera el DXF real primero
(ya probado hoy en vivo), se miden los minutos de corte reales del archivo,
y se aplica la misma fórmula. No se inventa un número sin el DXF.

**Tarjetas (100 piezas, mismo motor que etiquetas.py)** — usando
`cuanto_cobrar()` ya existente: con hoja carta, costo de hoja ~$3.50 y
diseño de $15, salen en el mismo rango que las etiquetas de hoy
(~$1.80-2.00 por pieza impresa).

Total aproximado del paquete físico para esta clienta: **entre $250 y $350**,
sin contar la parte digital si la pide.

---

## 2. Investigación real de código abierto — solo para la pieza que falta

Busqué software ya hecho para dos cosas: generar logos/kits de marca con IA,
y generar sitios web completos desde un cuestionario. Esto es lo que
encontré, evaluado con la misma vara que usa AURORA (licencia, mantenimiento,
qué tan fácil se integra a un sistema 100% Python).

### Logos / identidad de marca

**`SamurAIGPT/ai-logo-studio`** (GitHub) — MIT. Genera logo + kit de marca
con Nano Banana Pro, con Stripe y créditos ya armados.
- **Punto a favor real:** usa el MISMO modelo que ya tienes pagado
  (Nano Banana Pro).
- **Punto en contra real, no menor:** no llama a Gemini directo — llama a
  un intermediario de paga llamado "MuAPI", así que necesitarías OTRA
  llave de pago, no la que ya tienes. Además es Next.js + PostgreSQL +
  Prisma + NextAuth — un stack de JavaScript entero, mientras que AURORA es
  100% Python. Traerlo significaría mantener dos lenguajes y una base de
  datos nueva solo para esto.
- **Mi recomendación:** no lo integres. Sirve como referencia de qué se ve
  bien en pantalla, pero técnicamente cuesta más traerlo que escribir un
  módulo Python chico que llame a tu Gemini directo — que es exactamente
  el patrón que ya usaste hoy con `respaldo_nube.py`.

**`Nutlope/logocreator`** — proyecto similar, usa FLUX en vez de Gemini
(otro proveedor de pago distinto). Mismo problema: no aprovecha la llave
que ya pagaste. Descartado por la misma razón.

### Sitios web desde cuestionario

Encontré varios (`VoxelSite`, `OpenThorn`, `loupe`, `Devonz`,
`Ai-Website-Builder`), y ninguno vale la pena traer:
- La mayoría tiene **menos de 200 estrellas** en GitHub — proyectos chicos,
  de una persona, sin garantía de que sigan vivos el próximo año.
- `VoxelSite`/`VoxelSwarm` son **AGPL** — más restrictivo que GPL. Si algún
  día vendes AURORA como producto, AGPL obliga a abrir TODO el código que
  lo toque, incluso si solo lo llamas por red. Nunca traer AGPL a algo que
  piensas vender.
- Todos son stacks de JavaScript/TypeScript, ninguno Python.

**Mi recomendación honesta: no hay un "asistente completo" de código
abierto que valga la pena importar entero.** Lo que sí vale la pena, y es
real, maduro y de las licencias buenas (MIT/Apache), es usar un
**generador de sitios estáticos** ya probado por millones de sitios
—como Astro o 11ty— **solo como el motor que arma las páginas**, y que
AURORA (con Gemini) llene el contenido y las imágenes. Eso es componer
piezas maduras, no importar un proyecto experimental de un solo
desarrollador. Es más trabajo de integración que "bajar un repo y ya",
pero es el camino que no te deja con una dependencia frágil.

**Para tarjetas: no busqué nada externo.** El motor de `etiquetas.py`
(ReportLab, PDF vectorial con medida real) ya hace exactamente esto. Una
tarjeta es una etiqueta con otro tamaño. No hay que traer nada de fuera.

---

## 3. Estructura técnica del asistente (cuando se construya)

Sigue el mismo patrón que ya está probado hoy en `PLUGINS/etiquetas.json` —
no es arquitectura nueva:

```
PLUGINS/paquete_de_marca.json
  app: "paquete_de_marca"
  frases: ["hazme el paquete completo", "necesito marca desde cero",
           "quiero sitio y redes", "paquete de identidad"...]
  acciones:
    cuestionario   -> arma las preguntas segmentadas (qué piezas sí/no)
    logo           -> llama a Nano Banana, 3 variantes
    sitio          -> arma el sitio con la plantilla + el contenido de Gemini
    tarjetas       -> reusa TALLER/etiquetas.py con medida de tarjeta
    letrero        -> reusa EDITOR/texto_a_corte.py + TALLER/cajas_boxes.py
    cotizar        -> TALLER/formula_precios.py + la cuota de mano de obra
```

**Módulo nuevo real, uno solo:** `MARKETING/paquete_marca.py` (o
`TALLER/`, donde tú decidas que viva) — junta lo que ya existe, no
reinventa nada:
- `CEREBRO/respaldo_nube.py` ya sabe hablarle a Gemini — se extiende para
  pedir imagen en vez de solo texto (Nano Banana ya está en tu llave).
- `TALLER/cajas_boxes.py` para la lámpara.
- `EDITOR/texto_a_corte.py` para el letrero.
- `TALLER/etiquetas.py` (o una copia adaptada) para las tarjetas.
- `TALLER/formula_precios.py` para cada pieza física, más la cuota de mano
  de obra para las piezas humanas.
- El sitio web es la única pieza sin dueño hoy — necesita el módulo nuevo
  que compone la plantilla (Astro/11ty) con el contenido de Gemini.

**Reusa el sistema de licencias si algún día se vende a otros talleres:**
`LICENCIA/licencias.py` ya genera claves de 3 meses — serviría tal cual si
este paquete se ofreciera como suscripción a otros negocios de Guadalajara,
no solo a los clientes de Milens.

---

## 4. Plan de trabajo, por dependencia real (sin fechas inventadas)

**Ahora, con la clienta real:**
1. Generar el DXF real de la lámpara elegida (`cajas_boxes.py`, ya probado).
2. Generar el DXF real del letrero (`texto_a_corte.py`, ya probado).
3. Cotizar ambos con `formula_precios.py` — números reales, no estimados.
4. Cotizar las tarjetas adaptando `etiquetas.py`.
5. Cerrar la venta física. Esto no depende de nada nuevo.

**Fase 2 — cuando decidas generalizar (depende de que la Fase 1 ya haya
cobrado al menos una vez):**
1. Extender `respaldo_nube.py` para pedir imágenes a Nano Banana (cierra
   también el pendiente viejo de "generar imágenes con IA" — sirve para
   más cosas que este paquete).
2. Escribir la ficha `PLUGINS/paquete_de_marca.json` con el cuestionario
   segmentado, siguiendo el patrón de `etiquetas.json`.
3. Definir tú la cuota de mano de obra humana (cuánto cobra una visita de
   apertura de cuentas con el cliente presente).

**Fase 3 — el sitio web (depende de que la Fase 2 ya esté probada en un
cliente real, es la pieza más grande):**
1. Elegir el generador estático (Astro o 11ty — decisión tuya, ninguna es
   mejor objetivamente, ambas MIT).
2. Escribir el módulo que compone plantilla + contenido de Gemini +
   imágenes de Nano Banana.
3. Definir dónde se hospeda el sitio del cliente (esto también tiene un
   costo mensual real que hay que cobrarle a él, no absorberlo).

---

## 5. Lo que NO se construye hoy, y por qué

- **No se crea la cuenta de redes del cliente automáticamente.** Facebook e
  Instagram exigen que el dueño del negocio la abra con su propio teléfono
  y verificación — no es un límite de AURORA, es una regla de la
  plataforma. Por eso esa parte la hacen ustedes en persona.
- **No se importa ningún "asistente completo" de código abierto.** Ya
  quedó explicado arriba: ninguno de los que encontré vale más que
  componer lo que AURORA ya tiene.
- **No se construye el cuestionario genérico todavía.** Se construye
  DESPUÉS de cobrar el caso real de tu clienta — la receta sale de ahí,
  no al revés.
- **No se decide hoy la cuota de mano de obra humana ni dónde se hospeda
  el sitio web.** Son números y decisiones tuyas, no mías.
