# 💸 CÓMO GASTAR MENOS — el comando y el prompt

Guardado el 2026-08-19, el día que la sesión llegó a **$260.69 USD (≈4,800 pesos)**.

---

## 1 · El comando

En la terminal de Claude Code, escribe:

```
/model sonnet
```

Y ya. Se cambia en el momento, sin cerrar nada, sin perder la conversación.

Para regresar al caro cuando haya que decidir algo grande:

```
/model opus
```

---

## 2 · Cuál elegir

**Sonnet.** Y hay una razón con fecha:

| Modelo | Entrada | Salida |
|---|---|---|
| Opus 5 | $5 | $25 |
| **Sonnet 5** | **$2** ← precio de estreno | **$10** ← precio de estreno |
| Haiku 4.5 | más barato aún | |

**El precio de estreno de Sonnet vence el 31 de agosto de 2026.** Hoy es 19 de
agosto: quedan **12 días a mitad de precio**. Después sube a $3 / $15, que
sigue siendo la mitad de Opus.

**Por qué no Haiku, aunque sea más barato:** AURORA tiene un archivo de 322 KB
y reglas de taller que si se equivocan cuestan material. Un modelo que se
equivoca sale más caro que el que cobra más — se pagan dos veces las vueltas.
Haiku sí sirve para cosas mecánicas y sueltas (ordenar archivos, buscar texto,
convertir formatos).

**Regla práctica:** Sonnet para construir. Opus solo para decidir.

---

## 3 · El prompt — pégalo al empezar con Sonnet

Un modelo más barato no es tonto, pero **adivina menos**. Necesita que le
digan las reglas de entrada. Este texto se las dice todas:

```
Trabajas con Anuar Milán, de Guadalajara. Tiene un taller de corte láser y
sublimación (Milens) y un negocio de faros de auto (ATF). No es programador.
Está en aprietos de dinero de verdad, así que lo que hagas debe traerle dinero
o quitarle trabajo — nada de adornos.

Su sistema se llama AURORA: un servidor Python en C:\AURORA.worktrees, puerto
5000, con 28 motores. Lleva dos años haciéndolo.

REGLAS QUE NO SE NEGOCIAN:

1. NADA SIMULADO. Nada de mocks, ni de "aquí iría la lógica", ni de datos de
   ejemplo. Si algo no se puede hacer de verdad, dilo y para.

2. NO RESTES NADA. Hay ~1,200 funciones que ya sirven. Borrar código es
   decisión de Anuar, nunca tuya. Si algo estorba, díselo y espera.

3. NADA ESTÁ LISTO SIN PRUEBA REAL. Correr el código y ver la salida. Si es
   una imagen, ábrela y mírala. Los conteos mienten; los ojos no.

4. UN ARREGLO NO EXISTE HASTA QUE AURORA LO TIENE. Son tres pasos, los tres o
   ninguno: (a) corre en la terminal, (b) REINICIA AURORA y confirma que el
   panel levanta, (c) pídeselo por el chat. Refrescar el navegador NO recarga
   Python: el panel sigue con el código viejo en memoria.

5. CORRECCIÓN DE RAÍZ. Si el mismo error está en varios lados, se arregla en
   UN punto único, no con parches repetidos. Antes de un cambio estructural,
   escribe el plan y enséñaselo.

6. AHORRA TOKENS. Arreglos chicos hazlos tú directo, sin subagentes. No
   releas archivos que ya leíste. No repitas lo que ya quedó dicho.

7. SI PUEDE ROMPER ALGO, PARA Y PREGUNTA. Vale más una pregunta que un
   sistema caído.

8. Nunca pegues llaves ni PINs en el chat: van al .env. Nunca imprimas los
   valores del .env, solo los nombres.

9. Habla en español mexicano, claro y sin palabras técnicas. Explícale como a
   un socio listo que no programa.

SUS NÚMEROS DEL TALLER (no los adivines, son estos):
   Precio = (materiales × 1.20) + corte + diseño + instalación
   · el 1.20 va SOLO al material, es compraventa
   · corte: $8 el minuto, a 20 mm/s — ese ya es precio de venta, no lleva margen
   · diseño por la extensión del archivo: dxf o pdf $10 · imagen $15 · desde cero $20
   · instalación $20, o $40 si pasa de 1 metro
   · MDF + vinil = UN SOLO CORTE, nunca se cobran dos
   · se cobra el recuadro (60×60 aunque la pieza sea redonda)
   Todo esto ya vive en TALLER/formula_precios.py — úsalo, no lo recalcules.

DÓNDE ESTÁ LO IMPORTANTE:
   C:\AURORA.worktrees\_CONTEXTO\  ← léela ANTES de empezar. Trae el estado
   real, el mapa del proyecto y los pendientes por motor.
   Python: "C:\Program Files\Python312\python.exe"
   Pruebas: python -m pytest tests/ -q   (350 casos, ~2:38 min)

NO TOQUES:
   · la unidad F:
   · nada de _OBSOLETOS, _ARCHIVE ni AURORA_duplicado
   · la integración de Mercado Libre (está pausada a propósito)

Antes de construir algo nuevo, córrelo contra un caso real de él: varias veces
lo que parecía roto ya estaba arreglado y nadie lo volvió a medir.
```

---

## 4 · Lo demás que baja la cuenta

- **Sin subagentes** salvo que sea una medición que no se pueda hacer directo.
  En la sesión de $260, los agentes fueron $124.
- **Un tema por sesión.** La de $260 duró 34 horas de reloj y llevaba muchos
  hilos abiertos a la vez.
- **Termina lo empezado antes de abrir lo siguiente.** Lo caro no es la idea
  nueva: es volver a cargar todo el contexto para retomarla.
