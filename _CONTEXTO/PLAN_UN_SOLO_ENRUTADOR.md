# 🔀 PLAN — Un solo enrutador
### Escrito 2026-07-31 · NO ejecutado · requiere presupuesto sano

> **Regla que obliga este documento:** cambios estructurales llevan plan escrito
> ANTES de tocar código. Esto es cirugía en `consciencia.py`, el corazón del
> sistema. Hacerlo a medias es peor que no hacerlo.

> ## ⚠️ ESTE PLAN REEMPLAZA UNA VERSIÓN ANTERIOR QUE ESTABA EQUIVOCADA
>
> La versión previa decía que había "tres enrutadores peleándose" y proponía
> rediseñar el corazón de `consciencia.py` en 6 etapas. **Era un diagnóstico
> equivocado.** Se midió antes de cortar y los datos lo tumbaron.
>
> Si alguien encuentra una copia del plan viejo: **no lo ejecute.** Habría
> gastado una sesión entera rediseñando algo que no está roto.

---

## 1. La causa real, medida

**AURORA no es lenta. Groq está rechazando las peticiones por límite de cuota y
el cliente reintenta tres veces con espera.**

Evidencia directa del log del servidor (2026-07-31):

```
HTTP/1.1 429 Too Many Requests
groq._base_client: Retrying request in 3.000000 seconds
HTTP/1.1 429 Too Many Requests
groq._base_client: Retrying request in 4.000000 seconds
HTTP/1.1 429 Too Many Requests
groq._base_client: Retrying request in 3.000000 seconds
```

Tiempos medidos en vivo contra `/chat`:

| Tiempo | Motor | Qué hace |
|---|---|---|
| **0.7 s** | `negocio_real` | candado directo, **sin llamar a Groq** |
| **1.0 s** | `router_universal` | el enrutador universal, **una llamada que sí pasó** |
| **16.0 s** | `agenda` | candado que llama a Groq → reintentos |
| **22.5 s** | `motor_negocios` | motor que llama a Groq → reintentos |

**Todo lo que no toca Groq responde en menos de un segundo.** El enrutador
universal —que el plan viejo señalaba como el culpable lento— tarda **1 segundo**
y es de lo más rápido que hay.

El modelo en uso es `llama-3.1-8b-instant` (`_MODELO`, línea 682), que responde
en 1-2 s cuando la petición pasa. La lentitud **no es del modelo**: son las tres
esperas de los reintentos.

Esto también explica algo que nadie entendía: por qué a veces contesta rápido y
a veces no. No depende del mensaje — depende de si en ese momento hay cuota.

---

## 2. Qué hacer (3 etapas, ninguna toca la arquitectura)

Cada etapa cierra con las 76 pruebas en verde y su propio commit.

### ETAPA 1 — Ver cuántas llamadas hace AURORA por mensaje
**Lo primero, porque puede ser la causa del 429.**

Si un solo mensaje del usuario dispara 3-4 llamadas a Groq, la cuota se agota
sola. Contar antes de cambiar nada.

- Instrumentar con `logger.warning` cada llamada a `self._groq.chat.completions.create`
  en `CEREBRO/consciencia.py` (hay ~10 puntos, buscar `model=_MODELO`).
- Mandar 5 mensajes normales y contar cuántas llamadas genera cada uno.
- Escribir el resultado en `_CONTEXTO/LINEA_BASE.md`.
- **Si un mensaje genera más de 2 llamadas, ahí está el desperdicio** y hay que
  reportarlo antes de seguir.
- Quitar los logs temporales al terminar.

**Entregable:** cuántas llamadas por mensaje, medidas de verdad.

### ETAPA 2 — Bajar los reintentos de 3 a 1
**La más simple y la que más alivio da de inmediato.**

En `CEREBRO/consciencia.py` línea ~725:

```python
self._groq = AsyncGroq(api_key=api_key) if api_key else None
```

pasa a:

```python
# max_retries=1: con el default (2 reintentos + el original) un 429 costaba
# 16-22 s de espera antes de responder. Medido el 2026-07-31. Si Groq dice que
# no, es mejor caer rápido a Ollama que esperar tres veces por lo mismo.
self._groq = AsyncGroq(api_key=api_key, max_retries=1) if api_key else None
```

**Verificar:** volver a cronometrar los 4 mensajes de la tabla de arriba. El
caso lento debe bajar de ~16-22 s a ~6-8 s. **Si no baja, parar y reportar** —
significa que la espera viene de otro lado.

### ETAPA 3 — Caer a Ollama cuando Groq diga 429
**La que de verdad lo resuelve.**

AURORA ya tiene Ollama local funcionando (`llama3.2:3b`, se usa en modo offline).
Hoy, cuando Groq responde 429, AURORA espera y a veces falla. Debería usar el
modelo local, que responde en ~3 s y siempre está disponible.

- Localizar dónde se manejan los errores de las llamadas a Groq.
- Al recibir un 429 (o cualquier fallo de Groq), reintentar **una vez con Ollama**
  antes de rendirse.
- La respuesta debe decir honestamente que se usó el modelo local si aplica —
  **regla del proyecto: nunca simular ni ocultar de dónde salió una respuesta.**
- Si Ollama tampoco está, responder honesto: "no pude conectarme al modelo".
  **Nunca inventar la respuesta.**

**Verificar:** apagar temporalmente la llave de Groq en el entorno (NO borrarla
del `.env`) y comprobar que AURORA sigue respondiendo con Ollama, en segundos.

---

## 3. Lo que NO hay que hacer

- **No rediseñar el enrutamiento.** Tarda 1 segundo. No está roto.
- **No eliminar `_routing_llm`** por lentitud. No es la causa. *(Si algún día se
  quita, que sea por simplificar, no por velocidad, y con su propia medición.)*
- **No quitar candados.** Los rápidos (0.7 s) son justamente los que no llaman
  a Groq: son la parte buena del diseño.
- **No cambiar de modelo.** `llama-3.1-8b-instant` responde en 1-2 s cuando pasa.
- **No tocar `validador_honestidad`.** Intocable.

---

## 4. Prompt para Copilot (modo agente)

Una etapa a la vez. Cambiar el número en cada corrida.

```
Trabajas sobre AURORA en C:\AURORA.worktrees. Es PRODUCCIÓN: dos años de
trabajo operando dos negocios reales. Nada aquí es un ejercicio.

Lee COMPLETOS antes de escribir una línea:
  _CONTEXTO\LEEME_PRIMERO.md
  _CONTEXTO\ESTADO_REAL.md
  _CONTEXTO\PLAN_UN_SOLO_ENRUTADOR.md

TAREA: ejecuta ÚNICAMENTE la ETAPA <N> de ese plan.
No adelantes otras etapas. No aproveches para arreglar nada más.

CÓMO ARRANCAR AURORA
  python run_aurora.py          (tarda ~90 segundos)
  Verifica: http://127.0.0.1:5000/health
  Usa 127.0.0.1, NO localhost — con localhost falla por IPv6.

CÓMO PROBAR
  POST http://127.0.0.1:5000/chat
  {"mensaje": "...", "session_id": "prueba", "canal": "api"}

REGLAS QUE NO SE NEGOCIAN
- Nada simulado. Si algo no se puede hacer de verdad, PARAS y lo dices con
  esas palabras exactas.
- Nada se declara hecho sin la salida real del comando pegada. Un resumen no
  es prueba.
- NO restar funciones. Lo que funciona hoy se conserva.
- consciencia.py está BLINDADO por una razón real: el auto-reparador casi borró
  el 96% de ese archivo una vez. Cambios mínimos y quirúrgicos únicamente.
- Ante cualquier riesgo de romper algo: PARAS y preguntas.
- Español en el código y los comentarios, en el estilo del que ya está ahí.
- NUNCA imprimas el valor de una variable del .env. Solo su nombre.

AL CERRAR LA ETAPA
  python -m pytest tests/ -q     → deben ser 76 passed. Pega la salida completa.
  Un solo commit para esta etapa (para poder revertir si algo sale mal).

ENTREGAS
a) Qué cambiaste y por qué
b) La prueba real: el comando y su salida pegada
c) Los tiempos medidos antes y después (en las etapas 2 y 3)
d) Qué NO quedó cubierto y por qué. Esta sección nunca va vacía.
```

**Orden:** 1 → 2 → 3.

La etapa 1 va primero porque puede cambiar todo: si resulta que un mensaje
dispara 4 llamadas a Groq, el problema es el desperdicio, no los reintentos.

---

## 5. Lo que Anuar hace, y no se delega

1. **Correr él mismo** `python -m pytest tests/ -q` al cerrar cada etapa.
   Deben ser **76 passed**. Si no, `git revert` de ese commit.
2. **Cronometrar él mismo.** Si Copilot dice que bajó de 20 s a 5 s, comprobarlo
   escribiéndole a AURORA y contando.
3. **No creerle un "ya está" sin salida de comando pegada.** Ya pasó: el 30 de
   julio AURORA describió un respaldo, un borrado y una compilación que nunca
   ocurrieron. El candado de honestidad la delató. Copilot no tiene ese candado.

---

## 6. La lección que costó esta sesión

El plan anterior era sólido, detallado, con etapas y criterios de verificación
— **y apuntaba al lugar equivocado**, porque se escribió razonando sobre el
código en vez de midiendo el sistema corriendo.

Cuatro mediciones de treinta segundos lo tumbaron entero.

**Antes de cortar, medir. Siempre.** Sobre todo cuando el plan suena convincente.
