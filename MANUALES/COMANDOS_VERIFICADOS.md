# Comandos de AURORA — probados en vivo

**Aquí solo hay comandos que se ejecutaron de verdad contra el sistema real y
respondieron bien.** No es una lista de lo que *debería* funcionar: cada línea se
mandó al chat y se comprobó el resultado — el archivo en el disco, la cifra en la
base, la página abierta.

Están escritos **como los escribe Anuar**, con sus faltas de dedo y sus
modismos, porque así es como se van a usar.

Actualizado: 2026-08-05 · 26 candados directos · 558 herramientas · 210 pruebas

> **No tienes que aprenderte esto.** AURORA aprende cómo hablas: si algo no lo
> entiende y se lo dices de otra forma que sí funciona, se queda con las dos.
> Esta lista es para saber qué se puede hacer, no cómo hay que decirlo.

---

## 🎨 Corel

| Escribe esto | Qué hace |
|---|---|
| `corel abre C:\ruta\foto.jpg` | Importa la imagen al documento abierto (crea uno si no hay) |
| `corel abre C:\ruta\archivo.pdf` | Abre PDF, CDR o AI dentro de Corel |
| `corel extrae el texto del documento` | Lee todo el texto real del diseño abierto |
| `corel escala la pagina a 20x30 cm` | Cambia el tamaño de página |
| `corel exporta a pdf` | Exporta a `Escritorio\PDFs a Impresion` |
| `corel guarda una copia en C:\ruta\copia.cdr` | Copia sin tocar el original |
| `corel cierra el documento` | Cierra sin guardar |
| `corel tiene instalado el plugin laser` | **Lee el disco de verdad** y te dice si lo tienes |
| `que macros tiene corel` | Lista las macros instaladas (funciona con Corel cerrado) |
| `arregla la conexion con corel` | Repara el caché corrupto y lo confirma reconectando |

**Escribe `coreldrau` o `corell`** y también funciona.

⚠️ **Exportar a PNG/JPG desde Corel no sirve** — limitación real de la librería,
no de tu Corel. Usa PDF, que funciona al 100 %.

---

## 🔄 Convertir archivos

| Escribe esto | Qué hace |
|---|---|
| `convierte a dxf C:\ruta\archivo.svg` | SVG, PDF, AI o EPS → DXF para la láser |
| `convierte a png C:\ruta\archivo.pdf` | PDF → PNG **(probado: 2 MB reales en disco)** |
| `convierte a pdf C:\ruta\archivo.svg` | A PDF |
| `convierte a svg C:\ruta\imagen.png` | A SVG |
| `combierte a dxf ...` | Con B también funciona |
| `vectoriza C:\ruta\imagen.png` | Traza la imagen y genera SVG + DXF |

**Con la calidad que necesitas:**

| Escribe esto | Qué hace |
|---|---|
| `convierte a png a 150 dpi C:\ruta\archivo.pdf` | El número que digas manda |
| `convierte a png para lona C:\ruta\archivo.pdf` | **150 DPI solo** — la lona se ve a metros |
| `convierte a png para imprenta C:\ruta\archivo.pdf` | 600 DPI |
| `convierte la pagina 2 a png C:\ruta\archivo.pdf` | Solo esa página |
| `convierte todas las paginas a png C:\ruta\archivo.pdf` | Una imagen por página |

Sin decir nada: **300 DPI**, que es tu estándar para sublimación y láser.

⚠️ Archivos grandes o PDFs de muchas páginas tardan **1-2 minutos**. No está
colgado: está rasterizando de verdad.

---

## 📅 Agenda

| Escribe esto | Qué hace |
|---|---|
| `que tengo agendado hoy` | Las citas de hoy |
| `que tengo agendado manana` | Las de mañana |
| `proximas citas` | Lo que viene en 24 h |
| `agenda una cita para Pedro Lopez el 2026-08-05 10:00 tipo instalacion, tel 3312345678` | La agenda de verdad |
| `agendame una cita` | Te pide lo que falta, **no inventa** |

Tipos: `instalacion`, `entrega`, `cita`, `cotizacion`.

---

## 💰 Dinero y órdenes

| Escribe esto | Qué hace |
|---|---|
| `cuanto llevo vendido este mes` | Cifras reales de tu contabilidad |
| `hazme un corte de caja` | Lo mismo — es el cuadre, **no** cortar una caja |
| `como va la contabilidad` | Ingresos, costos, utilidad, cobrado, por cobrar |
| `que ordenes tengo pendientes` | Órdenes reales del taller |
| `echale un ojo a las cuentas del changarro` | También lo entiende |

---

## 🏷️ Cotizar

| Escribe esto | Qué hace |
|---|---|
| `cuanto sale una taza sublimada` | Precio real del catálogo de Milens |
| `cotizame 20 playeras cuello redondo` | Con tus precios, no inventados |
| `cuanto cuesta el faro aozoom x5` | Catálogo de ATF |
| `precio de instalacion de lupas` | Servicio de mano de obra de ATF |
| `quiero lupas cuanto sale la instalacion` | Igual |

Detecta solo si es Milens o ATF por lo que pidas.

---

## 🌐 Internet

| Escribe esto | Qué hace |
|---|---|
| `buscame proveedores de acrilico en guadalajara` | Búsqueda real con resultados |
| `investiga el precio de faros led h4 en mexico` | Precios de mercado reales |
| `que dicen de los proyectores aozoom` | Opiniones reales |
| `compara precios de termos para sublimar` | Comparativa real |
| `checa en internet cuanto esta el dolar hoy` | Dato real del día |

**Y abrir páginas de verdad:**

| Escribe esto | Qué hace |
|---|---|
| `abre youtube` | La abre en el navegador **(probado)** |
| `abreme mercadolibre` | Igual |
| `abre facebook` · `instagram` · `gmail` · `drive` · `canva` | 24 sitios por su nombre |
| `abre ameede.com` | Cualquier dominio que escribas |

⚠️ **AURORA no navega dentro de las páginas.** Las abre y busca en internet;
no hace clic ni llena formularios.

---

## 🧠 Sobre sí misma

| Escribe esto | Qué hace |
|---|---|
| `que puedes hacer` | Sus datos **reales**: candados, herramientas, límites |
| `cuantas herramientas tienes` | El número de verdad, del registro |
| `que has aprendido de mi` | Las formas de hablar que te aprendió |
| `olvida <la frase>` | Borra lo que aprendió mal |

---

## 📁 Archivos

| Escribe esto | Qué hace |
|---|---|
| `C:\Users\Administrador\Downloads\archivo.jpg` | **Solo la ruta**: te dice qué puede hacer con él |
| Una ruta sin extensión | La encuentra igual y te dice el tamaño |
| `abre el archivo trailer hit y extrae el dibujo lineal` | Recorta el fondo y saca el trazo limpio B&N |
| `edita CEREBRO/validador_honestidad.py` | Edita con respaldo, verifica que compile y revierte si falla |

⚠️ Archivos de más de 14,000 caracteres **no los edita** — te avisa antes en vez
de devolverte medio archivo.

---

## 🚫 Lo que NO hace, y te lo dice

| Si le pides | Contesta |
|---|---|
| Crear un motor nuevo | *"Eso es trabajo de AURORITA XP"* — la fábrica vive aparte |
| Algo que no sabe hacer | Te ofrece lo que **sí** puede, sacado de sus herramientas reales |
| Algo físico (ir por un café) | Niega limpio, sin inventarte una alternativa falsa |

**Y desde el 30 de julio no puede afirmar que hizo algo que no hizo.** Hay un
candado en código que revisa cada respuesta antes de salir: las acciones que dice
haber hecho, los comandos que menciona (contra el registro real) y los archivos
que nombra (contra el disco). Si algo no cuadra, lo corrige a la vista.

---

## ⏱️ Cuánto tarda

| | |
|---|---|
| Contabilidad, agenda, servicios | **menos de 1 segundo** |
| Corel, convertir, buscar en web | **2-10 segundos** |
| Conversiones pesadas | **1-2 minutos** (está trabajando de verdad) |
| Cuando Groq limita la cuota | puede tardar; eso es del proveedor, no de AURORA |


---

## 🧠 Lo que AURORA sabe de tu taller *(nuevo 2026-08-04)*

Tiene guardados **40 conocimientos reales** — tus parámetros probados, tus
precios y tus criterios. Se los preguntas hablando normal, no con palabras raras.

| Escribe esto | Qué te contesta |
|---|---|
| `a cuanto corto mdf de 2.7` | tu 60% / 25 mm/s y la galga de 2 trozos (5.4 mm) |
| `que galga uso para el mdf` | los 5.4 mm, y por qué los 8 mm eran el error |
| `a que potencia grabo` | tus parámetros probados |
| `como va la lente del cañon` | curva arriba, cómo checarla con el paño |
| `que recuerdas de costeo` | material ya pagado NO es gratis, y qué cargarle a cada pieza |
| `que recuerdas de precios escolares` | planilla $50, lápices $7/$5, uniformes $15 |
| `que recuerdas de insumos` | vinil $180 el metro, papel $2.50 la hoja |
| `que recuerdas de venta` | cómo escribirle a un cliente, 45 s entre mensajes |
| `que recuerdas de arquitectura` | cómo está hecha ella misma |
| `que recuerdas de decisiones` | por qué se cerró Ollama, por qué no se mueve de máquina |

**Temas cargados:** láser · precios escolares · costeo · insumos · venta ·
negocio · método de trabajo · arquitectura · decisiones · infraestructura

Para recargarlos o agregar más: `python MEMORIA/cargar_conocimiento_real.py`

---

## 🔍 Buscar precios AFUERA *(corregido 2026-08-04)*

Antes, pedir el precio de algo en MercadoLibre te devolvía una cotización de tus
propios productos. Ya no: el cotizador es para **vender**, no para **comprar**.

| Escribe esto | Qué hace |
|---|---|
| `busca en mercado libre papel adhesivo para laser` | busca en internet de verdad |
| `donde compro vinil textil mas barato` | busca proveedores |
| `encuentra el mejor precio y dame el link` | busca y trae la publicación |
| `cuanto cuestan 100 playeras` | **cotiza con TUS precios** (esto no cambió) |

---

## 🎒 Campaña escolar *(lista, sin enviar)*

No es un comando del chat: es un script aparte, para que nada se mande solo.

```
python MARKETING/campana_regreso_clases.py            # ver el mensaje y a quién
python MARKETING/campana_regreso_clases.py --enviar   # mandarlo de verdad
```

22 clientas reales de julio. Va con 45 segundos entre mensaje y mensaje para que
WhatsApp no tumbe el número del negocio.


---

## 🏪 Proveedores — a quién le compras *(nuevo 2026-08-05)*

Antes de mandarte a internet, revisa TU directorio.

| Escribe esto | Qué hace |
|---|---|
| `quien me vende vinil textil` | Lideart, $180 el metro, con la fecha del dato |
| `proveedor de mdf` | maderería, MDF 2.7 a $110 y 5.5 a $280 |
| `que proveedores tengo` | los lista todos |

Si no lo tiene, **lo dice** y te ofrece buscarlo en internet. Nunca inventa un
teléfono. Los que faltan los agregas conforme cotices.

---

## 👤 Apuntar un cliente *(nuevo 2026-08-05)*

Antes esto no existía: un cliente que llamaba se anotaba en un papel o se perdía.

| Escribe esto | Qué hace |
|---|---|
| `apunta a Juan Perez 3312345678 interesado en faros` | lo guarda con folio, saca el teléfono y detecta que es de ATF |
| `anota este cliente Maria 3339876543` | lo mismo, sin interés |
| `nuevo cliente Roberto quiere lupas` | lo guarda en ATF por lo de las lupas |

Si no le pasas nombre, **no lo guarda** — un cliente sin nombre no sirve para
llamarle después.

---

## 📐 Diseños y cotización *(nuevo 2026-08-05)*

```
python TALLER/indexar_dxf.py --buscar casa
```

Te da el archivo, sus metros de corte, los minutos y el precio con tus números
($8/min, 25 mm/s, margen ×3). Eso es lo que faltó el día de la casa de muñecas.

| Escribe esto en el chat | Qué te contesta |
|---|---|
| `que recuerdas de cotizar` | la regla de bolsillo: metros × $50, y los mínimos |
| `que recuerdas de inventario` | cuántos DXF y programas tienes |
| `que recuerdas de proveedores` | cómo consultarlos |


---

## 📦 Cajas para láser — se las pides hablando *(nuevo 2026-08-05)*

**189 modelos** de boxes.py, y le hablas normal. Las medidas en cm.

| Escribe esto | Qué te da |
|---|---|
| `hazme una caja corazon de 45x7 con tapa de agujero` | el SVG listo para cortar |
| `quiero una caja con divisiones de 40x30x7` | bandeja con separadores |
| `hazme una caja con bisagras de 20x10` | con bisagras integradas |
| `una caja flex de 20x10` | pared curva (kerf bending) |
| `un cajon de 20x10` | cajón deslizante |
| **`que cajas puedes hacer`** | **la lista completa** |

**Tipos que entiende:** corazón · flex · bisagras · divisiones · divisor ·
cajón · redonda · hexagonal · dados · cartas · libro · castillo · pajarera ·
alcancía · bandeja · compartimentos · cerrada

**La tapa:** di *"con tapa de agujero"*, *"con tapa"* o *"cerrada"*.
**El grosor:** si no lo dices, 2.7 mm. Para otro: *"de 5.5 mm"*.

Sale en **SVG** — lo abre Corel y RDWorks directo. Para el precio, guárdalo como
DXF desde Corel y dile `cotiza <ruta>`.

---

## ✂️ Cotizar un corte *(nuevo 2026-08-05)*

| Escribe esto | Qué hace |
|---|---|
| `cotiza C:\Users\...\diseno.dxf` | mide los metros REALES y da el precio |
| `cuanto cuesta cortar este dxf` | lo mismo |
| `cuantos metros de corte tiene` | solo la medición |

Usa tus números: **$8 por minuto a 25 mm/s**, margen ×3. Es lo que faltó el día
de la casa de muñecas.

---

## 🗣️ AURORA ya entiende cómo escribes *(nuevo 2026-08-05)*

Se le cargó tu forma real de escribir, sacada de **72 peticiones tuyas**. Ya no
tienes que cuidar la ortografía ni pensar cómo pedirlo:

| Escribes | Entiende |
|---|---|
| `abreme coreldrau porfa` | abre Corel |
| `chekame el diseno abierto` | revisa el documento de Corel |
| `sacale el dibujo lineal` | vectoriza |
| `pasalo a corte` | convierte a DXF |
| `mandale un wats al cliente` | envía WhatsApp |
| `a cuanto me sale...` | cuánto cuesta |
| `imprecion`, `adesivo`, `watsapp`, `combiene` | los corrige solos |

Y los verbos con pronombre pegado —`ábreme`, `guárdalo`, `cotízame`— ya no la
confunden.
