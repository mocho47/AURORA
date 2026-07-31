# 🔀 PLAN — Un solo enrutador
### Escrito 2026-07-31 · NO ejecutado · requiere presupuesto sano

> **Regla que obliga este documento:** cambios estructurales llevan plan escrito
> ANTES de tocar código. Esto es cirugía en `consciencia.py`, el corazón del
> sistema. Hacerlo a medias es peor que no hacerlo.

---

## 1. El problema, dicho en una frase

**Hay tres enrutadores haciendo el trabajo de uno**, y se pisan entre ellos.

Lo detectó Anuar el 2026-07-31 después de seis fallas seguidas: *"no se trata
de un solo comando, es global el asunto"*. Tenía razón — yo estaba arreglando
síntomas de uno en uno.

### Lo que pasa hoy con cada mensaje

```
mensaje
  ↓
1. _routing_rapido      heurístico por palabras           (rápido, sin IA)
  ↓ si no decide
2. _routing_llm         ← LLAMADA A IA #1                 (~1-3 s)
  ↓
3. ~18 candados         cada uno con frases a mano        (rápido)
  ↓ si ninguno calzó
4. _router_universal    ← LLAMADA A IA #2 + buscar en registro  (~2-5 s)
  ↓ si no aplicó
5. motor elegido        ← LLAMADA A IA #3 para redactar    (~10-25 s)
```

**Hasta tres llamadas a IA en serie para contestar una pregunta.** Medido en
vivo: 16.1 s y 33.8 s en preguntas normales.

### Las seis fallas son UN problema saliendo por seis lados

Todas del 30-31 de julio, todas encontradas por Anuar usando AURORA normal:

| Lo que escribió | Qué pasó | Capa culpable |
|---|---|---|
| "coreldrau vectorizar" | fue al enrutador y propuso `preparar_para_lona` | 3 → 4 |
| solo una ruta de archivo | negó falsamente poder abrirla | 3 |
| "tiene instalado el plugin" | 33.8 s y una vaguedad de `motor_negocios` | 1/2 |
| "diagnostica" | cayó en el candado de servicios de faros | 3 |
| "edita tu archivo" | nunca llegó al cartucho IDE | 3 |
| "coachéame" | pidió permiso para *platicar* | 4 |

**No son seis bugs. Es que tres capas deciden cosas distintas sobre el mismo
mensaje.** Agregar frases una por una es infinito: siempre habrá una forma de
decir las cosas que nadie anticipó.

---

## 2. El diseño destino

**Un solo punto de decisión.**

```
mensaje
  ↓
1. CANDADOS DETERMINISTAS   solo lo crítico. Sin IA. Instantáneos.
  ↓ si ninguno calzó
2. ENRUTADOR UNIVERSAL      UNA llamada. Elige y ejecuta del registro real.
  ↓ si no aplica ninguna herramienta
3. RESPUESTA CONVERSACIONAL una llamada para redactar.
```

**Máximo dos llamadas a IA, nunca tres.**

### Qué se conserva
- Los candados de **acción real y crítica**: Corel, DXF, WhatsApp, publicar,
  agenda, acción física, ruta_sola. Son deterministas, instantáneos y probados.
- `_router_universal` completo (517 herramientas) — es la pieza buena.
- `validador_honestidad` en el punto único de salida. **Intocable.**
- Las 76 pruebas de regresión. **Deben seguir pasando todas.**

### Qué se elimina
- **`_routing_llm`** — la capa redundante que más cuesta y menos aporta. El
  enrutador universal ya elige mejor, con datos reales del registro.
- Los candados **de tema, no de acción** (los que solo eligen "de qué habla"):
  esos son justo los que se roban mensajes ajenos, como el de servicios de ATF
  con la palabra "diagnostica".

### Qué se corrige de paso
- **Charla no pide confirmación.** Solo se confirma lo que toca algo real
  (escribir, borrar, enviar, publicar). Coaching, consultas y análisis, jamás.
- **`motor_negocios` deja de ser cajón de sastre.** Si la pregunta no es de
  negocio, pasa de largo en vez de contestar vaguedades.
- **Nunca quedarse muda.** Si nada aplica, decir qué sí puede hacer.

---

## 3. Orden de ejecución

Cada etapa cierra con las 76 pruebas en verde. Si una no cierra, no se sigue.

| # | Etapa | Cómo se comprueba |
|---|---|---|
| **0** | **Medir antes.** Cronometrar 10 mensajes reales (los 6 de la tabla + 4 normales). Guardar los tiempos. | Sin la línea base no se puede saber si mejoró |
| **1** | Separar los candados en dos listas: ACCIÓN (se quedan) y TEMA (se van). No borrar nada todavía, solo clasificar. | Las 76 pruebas siguen verdes |
| **2** | Eliminar `_routing_llm`. Cuando el heurístico no decida, pasar directo a los candados de acción. | Cronometrar de nuevo: debe bajar 1-3 s por mensaje |
| **3** | Quitar los candados de TEMA. El enrutador universal los cubre. | Los 6 casos de la tabla deben mejorar, no empeorar |
| **4** | Marcar qué herramientas necesitan confirmación de verdad (solo escritura/envío/borrado). Charla, nunca. | "coachéame" debe responder directo, sin pedir permiso |
| **5** | Red de honestidad final: si nada aplicó, responder qué SÍ puede hacer. Nunca silencio. | Ninguno de los 10 mensajes puede quedar sin respuesta útil |
| **6** | Medir después y comparar contra la etapa 0. | Objetivo: **de 16-34 s a 3-5 s** |

### Criterio de terminado
- Las **76 pruebas** pasan.
- Los **6 casos reales** de la tabla se comportan bien, verificados en vivo.
- El tiempo bajó de forma medible contra la línea base de la etapa 0.
- **Ninguna función se perdió.** Regla #1 de Anuar.

### Si algo sale mal
`git revert` del commit de la etapa. Por eso **una etapa = un commit**, nunca
todo junto.

---

## 4. ¿Puede hacerlo Copilot con estas instrucciones?

Pregunta real de Anuar. Respuesta honesta, por partes:

**Lo que Copilot sí hace bien:** completar código, escribir funciones sueltas,
refactors mecánicos dentro de un archivo abierto. Para eso es excelente y es
más barato.

**Por qué este trabajo en particular NO es para Copilot:**

1. **No puede ejecutar ni verificar.** Este plan es 80% verificación: correr las
   76 pruebas, cronometrar antes y después, probar los 6 casos en vivo contra el
   servidor. Copilot sugiere código; no reinicia AURORA, no corre pytest, no mide
   tiempos, no lee la respuesta real de `/chat`. Y la regla de este proyecto es
   *nada se declara listo sin prueba real ejecutada*.
2. **`consciencia.py` no cabe.** Son ~148,000 caracteres. Este cambio toca el
   pipeline completo, no una función. Copilot trabaja bien en la ventana
   alrededor del cursor, no sobre la arquitectura de un archivo así.
3. **Requiere juicio, no autocompletado.** Decidir qué candado es de ACCIÓN y
   cuál de TEMA es una decisión de diseño con consecuencias reales — si se
   equivoca, se pierde una función que hoy sirve. Ese es exactamente el tipo de
   decisión donde no se puede aceptar una sugerencia a ciegas.
4. **El riesgo no es simétrico.** Si Copilot acierta, ahorras dinero. Si falla en
   este archivo, rompes lo que da de comer. Ya pasó una vez: el auto-reparador
   casi borra el 96% de este mismo archivo.

**Dónde SÍ conviene usarlo, y ahorra de verdad:** los motores nuevos y los
cartuchos, que son archivos chicos y aislados con su propia prueba. Ahí Copilot
rinde y el riesgo es cero — si sale mal, se borra el archivo y ya.

**Veredicto:** el corazón se toca con algo que pueda ejecutar y verificar.
Todo lo demás, con lo más barato que sirva. No es lealtad a una herramienta;
es dónde duele si se equivoca.

---

## 5. Lo que NO entra en este plan
- No se toca `validador_honestidad`.
- No se agregan funciones nuevas. Esto es simplificar, no crecer.
- No se toca ningún motor. Solo el enrutamiento.
- No se cambia el panel ni los endpoints.
