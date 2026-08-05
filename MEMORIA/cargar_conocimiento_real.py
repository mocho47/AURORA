# -*- coding: utf-8 -*-
"""AURORA · Cargar a memoria lo aprendido trabajando con Anuar

Anuar lo pidió el 2026-08-04: "estaría excelente que aurora realmente aprendiera
de ti todo lo que hicimos hoy... si integras todo lo aprendido por ambas partes
en aurora, la voy a amar".

Esto vuelca a la memoria semántica de AURORA el conocimiento REAL del negocio:
parámetros probados en su máquina, precios que él dictó, criterios de costeo y
las decisiones que se tomaron con números medidos. Nada inventado — cada entrada
salió de una sesión de trabajo real y trae la fecha.

Lo que NO se carga: notas técnicas del desarrollo, rutas de archivos, historial
de bugs. Eso no le sirve a AURORA para operar el negocio.

Correr:  python MEMORIA/cargar_conocimiento_real.py
Ver:     en el chat, "qué recuerdas de láser" / "qué recuerdas de precios"
"""
from __future__ import annotations
import asyncio
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# (tema, patrón, conocimiento, confianza)
# La confianza es 1.0 solo cuando se probó en la máquina de Anuar o él lo dictó.
CONOCIMIENTO = [
    # ── LÁSER CO2 100W ────────────────────────────────────────────────────
    ("laser", "corte mdf 2.7mm",
     "MDF 2.7 mm en la CO2 100W: potencia 60%, velocidad 25 mm/s, un solo pase "
     "con aire. Probado por Anuar el 2026-07-20.", 1.0),
    ("laser", "galga de foco mdf",
     "La galga de foco para MDF 2.7 son DOS TROZOS del mismo MDF apilados = "
     "5.4 mm de separación cabezal/material. Con esa galga corta limpio a 60/25. "
     "Antes estaba anotado 8 mm y ESE era el error: con foco alto ya no pasaba a "
     "60/25 y había que bajar a 60/20, que castiga más el tubo. Nunca fue la "
     "potencia, era el foco (2026-08-03).", 1.0),
    ("laser", "formula energia por milimetro",
     "Energía por mm = potencia ÷ velocidad. Es cuánto se cocina cada milímetro. "
     "60/25 = 2.4 · 80/30 = 2.67 · 60/20 = 3.0. Para bajar potencia sin perder "
     "corte, baja la velocidad en la misma proporción. Regla de oro: la potencia "
     "MÍNIMA que corta de un pase = tubo longevo y borde limpio.", 1.0),
    ("laser", "orientacion de la lente",
     "La lente del cañón va con la cara CURVA (convexa) hacia ARRIBA, mirando al "
     "tubo, y la plana hacia abajo. Para checarla: ponla sobre un paño y presiona "
     "la orilla — si NO se levanta, la plana está abajo (correcto); si baila, está "
     "al revés. Los fabricantes chinos la ponían invertida de fábrica.", 1.0),
    ("laser", "diagnostico no corta a velocidad conocida",
     "Si deja de cortar a una velocidad que antes sí funcionaba, revisar EN ESTE "
     "ORDEN: 1) foco y galga, 2) lente limpia, 3) orientación de la lente, "
     "4) espejos. Los cuatro dan los MISMOS síntomas: no corta, más quemado, "
     "letra chica borrosa.", 1.0),
    ("laser", "materiales prohibidos",
     "NUNCA cortar unicel (poliestireno expandido) ni PVC en la CO2: emiten gases "
     "tóxicos y se incendian. El foam EVA sí se corta, con potencia baja "
     "(15-20%), velocidad alta y extracción al máximo.", 1.0),
    ("laser", "costo de reponer el tubo",
     "Reponer el tubo CO2 de 100W cuesta entre $2,000 y $4,000 MXN. Por eso "
     "conviene siempre la potencia mínima que corte de un pase.", 1.0),

    # ── PRECIOS DE TEMPORADA ESCOLAR (dictados por Anuar 2026-08-04) ───────
    ("precios escolares", "planilla de etiquetas",
     "Planilla de etiquetas para útiles: $50. Set de 35 piezas — 15 etiquetas de "
     "4x9 cm para libros y libretas, 20 de 2.7x6 cm para lápices y colores. De "
     "una hoja carta salen 15 de 4x9 o 30 de 2.7x6.", 1.0),
    ("precios escolares", "lapices personalizados",
     "Lápices con el nombre grabado a láser: $7 cada uno, o la docena a $5 cada "
     "uno ($60).", 1.0),
    ("precios escolares", "personalizacion de prendas",
     "Nombre en uniforme: $15 por prenda, medida 2.5x8 cm en vinil textil, listo "
     "para que la mamá lo planche donde quiera. NO son parches. Colores: dorado, "
     "blanco, negro, rosa, verde y rojo. Escudo escolar a color por impresión "
     "digital: $15. Con costo extra de $30: sublimable tipo bordado, sublimable "
     "liso o sublimable con glitter.", 1.0),
    ("precios escolares", "tabla de multiplicar",
     "Tabla de multiplicar enmicada de 15x10 cm con el nombre del niño. Costo real "
     "$10 (impresión + mica). En papelería las genéricas cuestan $12; las "
     "personalizadas se pueden vender en $25.", 1.0),
    ("precios escolares", "paquete completo",
     "PAQUETE ESCOLAR $115: set de 35 etiquetas + 6 nombres en vinil + tabla de "
     "multiplicar personalizada. Costo $51.10, utilidad $63.90. El vinil es donde "
     "está el dinero: $56 de utilidad contra $12 de las etiquetas.", 1.0),

    # ── CRITERIOS DE COSTEO (método de trabajo de Anuar) ──────────────────
    ("costeo", "material ya pagado",
     "Material ya pagado NO es material gratis. Aunque las micas o el vinil ya "
     "estén comprados, hay que cargarles su costo de reposición a cada pieza. Si "
     "no se cuenta, el día que se acaben el dinero no está. Criterio de Anuar, "
     "2026-08-04.", 1.0),
    ("costeo", "que cargarle a cada pieza",
     "A cada pieza hay que cargarle: material, tubo láser prorrateado entre sus "
     "horas de vida, tóner por hoja, micas y navajas por uso, luz y renta, y el "
     "TIEMPO de trabajo. Un plan que solo cuenta el material miente sobre el "
     "margen.", 1.0),
    ("costeo", "maquilar o hacerlo en casa",
     "La decisión no es por margen sino por punto de equilibrio e INVERSIÓN. "
     "Maquilar no requiere invertir: se paga al vender. Hacerlo en casa exige "
     "comprar material primero. Fórmula: inversión ÷ (lo que se ahorra por pieza) "
     "= piezas para empatar. Con las tarjetas apretadas conviene maquilar primero "
     "y comprar material con las ganancias, no con el último dinero.", 1.0),
    ("costeo", "maquila de tabloide",
     "El tabloide impreso Y suajado cuesta $45; solo impreso, $10. Esos $35 de "
     "diferencia son mano de obra de corte — se ahorran cortando en la Cameo, que "
     "trabaja sola. Un tabloide = 2 hojas carta exactas = 30 etiquetas de 4x9.", 1.0),

    # ── INSUMOS: precios reales verificados ───────────────────────────────
    ("insumos", "vinil textil",
     "Vinil textil de 60 cm: $180 el metro (precio real de Anuar, 2026-08-04). Un "
     "metro son 6,000 cm² y rinde 50 juegos de 6 nombres de 2.5x8. El juego sale "
     "en $3.60 y se vende en $60.", 1.0),
    ("insumos", "papel adhesivo",
     "Papel adhesivo tamaño carta: $2.50 por hoja comprando paquete de 100 ($250). "
     "Debe decir 'para impresora láser' o 'láser/inkjet' — el de solo inyección se "
     "derrite en el fusor y ensucia la impresora por dentro.", 1.0),
    ("insumos", "toner de la HP",
     "La HP M452dw imprime máximo tamaño LEGAL (21.6 x 35.6 cm). NO imprime "
     "tabloide. Un cartucho 410A rinde ~2,300 páginas, así que al 10% quedan ~230 "
     "hojas = unos 135 sets de etiquetas.", 1.0),

    # ── VENTA ─────────────────────────────────────────────────────────────
    ("venta", "como escribirle a un cliente",
     "El cierre debe pedir UNA sola cosa fácil (el nombre del niño), no "
     "'¿le interesa?' que se contesta con no. Vender el resultado, no el producto: "
     "'ya no se le pierde nada al niño' vende más que 'etiqueta de 4x9'. Y siempre "
     "'sin compromiso'.", 1.0),
    ("venta", "recompra",
     "Venderle a alguien que ya compró cuesta una fracción de conseguir un cliente "
     "nuevo. Mencionar la compra anterior ('gracias por confiar la vez pasada') es "
     "lo que hace que funcione.", 1.0),
    ("venta", "envios masivos de whatsapp",
     "Nunca mandar mensajes en ráfaga: WhatsApp tumba el número. Mínimo 45 "
     "segundos entre envíos. El número del negocio es el canal de ventas, "
     "perderlo cuesta más que esperar.", 1.0),
    ("venta", "publicidad honesta",
     "No mostrar una foto de algo más grande de lo que se entrega. Si se vende "
     "planilla carta, se fotografía la carta real y bien llena — se ve abundante "
     "sin prometer de más. Que la primera venta no cueste la segunda.", 1.0),

    # ── TICKETS DEL NEGOCIO ───────────────────────────────────────────────
    ("negocio", "ticket por linea",
     "ATF (retrofit de faros) tiene ticket de $1,550 a $3,149. Milens (láser y "
     "sublimación) promedia ~$270 por orden. Un retrofit de faros equivale a 10 "
     "velas o 6 paquetes escolares: cuando urge flujo, ATF paga más rápido.", 1.0),
    ("negocio", "activos de cada linea",
     "ATF tiene 307 videos de retrofit grabados pero pocos clientes en base. "
     "Milens tiene 22 clientas reales con teléfono (julio 2026) pero ningún video. "
     "Cada línea tiene lo que a la otra le falta.", 1.0),

    # ── CÓMO SE TRABAJA AQUÍ (reglas de Anuar) ────────────────────────────
    ("metodo de trabajo", "nada simulado",
     "Prohibido simular, usar mocks o entregar algo parcial. Nada se declara "
     "'listo' sin una prueba real. Ante el riesgo de romper algo que funciona: "
     "parar y preguntar, nunca seguir a ciegas. Regla permanente de Anuar.", 1.0),
    ("metodo de trabajo", "correccion de raiz",
     "Los errores se corrigen de RAÍZ, no con parches. Si un bug aparece en un "
     "comando, hay que preguntarse dónde más aparece el mismo patrón. Un arreglo "
     "que solo tapa el caso de hoy deja el hueco de mañana abierto.", 1.0),
    ("metodo de trabajo", "medir antes de cambiar",
     "Antes de un cambio grande hay que MEDIR, no razonar. Dos veces la medición "
     "mató la hipótesis: el enrutador parecía lento y tarda 1.0 s; se iba a "
     "invertir el orden de los candados y resultó que aciertan 95% con cero "
     "errores. Cambiar sin medir es apostar con lo que ya funciona.", 1.0),
    ("metodo de trabajo", "no restar funciones",
     "Nunca quitar funciones que ya sirven. Son dos años de trabajo. Quitar un "
     "motor no es borrarlo: es moverlo o desactivarlo, y siempre es decisión de "
     "Anuar, jamás automática.", 1.0),
    ("metodo de trabajo", "quien encuentra los bugs",
     "Los bugs reales los encuentra Anuar usando AURORA normalmente, no las "
     "auditorías. Ha pasado con todos: la lona inventada, el PDF marcado como "
     "comando falso, el 'abierto real' de una carpeta, el cotizador de $75,000. "
     "El uso real es el mejor detector que existe.", 1.0),

    # ── CÓMO ESTÁ HECHA AURORA ────────────────────────────────────────────
    ("arquitectura", "candados y enrutador",
     "El chat entiende por CANDADOS: listas de palabras que corren en orden y "
     "mandan al motor correcto. Si ninguno agarra, entra el ENRUTADOR UNIVERSAL, "
     "que usa IA, conoce las 537 herramientas y tarda ~1 segundo. Los candados "
     "son rápidos pero rígidos; el enrutador entiende pero es más lento.", 1.0),
    ("arquitectura", "por que a veces no entiende",
     "Cuando AURORA no entiende algo es casi siempre porque una lista de palabras "
     "no previó cómo se dijo. No es que no pueda hacerlo: es que no reconoció el "
     "pedido. Por eso existe el aprendizaje, que registra las frases de Anuar.", 1.0),
    ("arquitectura", "no puede mentir",
     "Hay un candado de honestidad en el punto único de salida: revisa cada "
     "respuesta antes de entregarla. Si va a afirmar que hizo algo, se verifica; "
     "si va a negar una capacidad que sí tiene, se corrige. Por eso cuando no "
     "puede hacer algo lo DICE en vez de inventar.", 1.0),
    ("arquitectura", "aprende de como habla anuar",
     "AURORA registra las frases de Anuar en CONFIG/aprendido_del_usuario.json. "
     "Antes solo aprendía cuando una frase fallaba y él la reformulaba — o sea, "
     "cada frase nueva costaba un fracaso. Desde el 2026-08-04 también aprende A "
     "LA PRIMERA: si el enrutador resuelve algo que ningún candado agarró, la "
     "frase queda registrada en el momento.", 1.0),
    ("arquitectura", "la fabrica esta cerrada",
     "AURORA TIENE fábrica de motores pero NUNCA la usa sin autorización de "
     "Anuar (FABRICA_HABILITADA = False). Capacidad no es lo mismo que autonomía.", 1.0),

    # ── DECISIONES TÉCNICAS TOMADAS, CON SU RAZÓN ─────────────────────────
    ("decisiones", "por que no hay ollama local",
     "El plan de mover Ollama a otra máquina se CERRÓ el 2026-08-04 con tres "
     "datos: la Gateway y la Chromebook tienen 2 GB (Windows solo usa 1.8), "
     "Gemini está sin cuota, y sobre todo Groq NUNCA ha fallado — cero registros "
     "en los logs. Se iba a montar un servidor para un problema que no ocurre.", 1.0),
    ("decisiones", "por que aurora no se mueve de maquina",
     "AURORA se queda en la laptop de Anuar porque Corel solo se controla desde "
     "la PC donde está instalado. Moverla significaría perder todos los comandos "
     "de Corel, que son de los más usados. Además se midió: AURORA consume 26 MB, "
     "no es ella la que satura la máquina — son los navegadores con 2 GB.", 1.0),
    ("decisiones", "exportar bitmap de corel esta roto",
     "corel_core.exportar_bitmap NO funciona por una limitación real de pywin32. "
     "A PDF sí exporta al 100%. No prometer PNG/JPG desde Corel: hay que sacar "
     "PDF y convertir después.", 1.0),

    # ── INFRA ─────────────────────────────────────────────────────────────
    ("infraestructura", "como se levanta aurora",
     "AURORA corre en el puerto 5000 con run_aurora.py, 28 motores en bus, y "
     "tarda ~90 segundos en arrancar. La salud se consulta por 127.0.0.1, NUNCA "
     "por localhost (resuelve a IPv6 y falla). La esposa entra por "
     "192.168.1.38:5000.", 1.0),
    ("infraestructura", "pruebas de regresion",
     "Hay 112 pruebas de regresión en tests/, una por cada bug real que ocurrió. "
     "Se corren con: python -m pytest tests/ -q. Si alguna se pone en rojo, algo "
     "que ya funcionaba se rompió.", 1.0),
]


async def main() -> int:
    from MEMORIA.sistema_memoria import SistemaMemoria

    mem = SistemaMemoria()
    await mem.inicializar()

    print(f"Cargando {len(CONOCIMIENTO)} conocimientos reales a la memoria de AURORA")
    print("=" * 72)
    por_tema: dict = {}
    for tema, patron, texto, conf in CONOCIMIENTO:
        await mem.aprender(tema=tema, patron=patron, conocimiento=texto, confianza=conf)
        por_tema.setdefault(tema, 0)
        por_tema[tema] += 1
        print(f"  [{tema:18}] {patron}")

    print("=" * 72)
    for tema, n in sorted(por_tema.items()):
        print(f"  {tema:20} {n}")
    print()
    print("Pruébalo en el chat:")
    for tema in sorted(por_tema):
        print(f"   «qué recuerdas de {tema}»")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
