# 🎯 PLAN MAESTRO — AURORA lista para el demo de 4Forte
### 2026-07-31 · Fusión del plan de Copilot + hallazgos medidos · NO ejecutado

> **Reemplaza a `PLAN_UN_SOLO_ENRUTADOR.md`.** Ese apuntaba al enrutamiento; se
> midió y el enrutamiento no era el problema. Lo que sobrevive de él está aquí.
>
> **Este plan tiene un solo norte:** que AURORA aguante un demo en vivo frente a
> un cliente real sin fallar ni mentir. Todo lo que no sirva para eso es después.

---

## 0. El norte: el demo de 4Forte

No se trata de que las 517 herramientas funcionen. **Se trata de que 10 funcionen
impecables frente a alguien que puede pagar.**

Un demo se cae por tres cosas, en este orden:
1. **Tarda** — 20 segundos de silencio frente a un cliente es eterno
2. **Miente** — dice que hizo algo y no lo hizo
3. **No entiende** — le hablan normal y no responde

El plan ataca las tres, en ese orden, porque ese es el orden en que duelen.

---

## 1. Lo que YA está resuelto (no rehacer)

Verificado en vivo el 30-31 de julio. **No tocar, solo conservar:**

| Qué | Evidencia |
|---|---|
| `CEREBRO/validador_honestidad.py` | Impide afirmar acciones falsas. 4/4 en vivo |
| El enrutador universal | **1.0 s** — es la parte rápida del sistema |
| Candados sin IA | **0.7 s** — la parte buena del diseño |
| 76 pruebas de regresión | Una por bug real que de verdad ocurrió |
| Corel, agenda, cotizador, web, WhatsApp | Probados uno por uno |

> ⛔ **`validador_honestidad.py` se EXTIENDE, nunca se reescribe.** Es lo único
> que impide que AURORA le mienta a un cliente. Si se rehace, se pierde.

---

## 2. La causa medida de la lentitud

**No es la arquitectura. Es la cuota de Groq.** Log real:

```
HTTP/1.1 429 Too Many Requests
groq._base_client: Retrying request in 3.000000 seconds   ← ×3
```

| Tiempo | Ruta | Llama a Groq |
|---|---|---|
| 0.7 s | candado `negocio_real` | no |
| 1.0 s | `router_universal` | sí, y pasó |
| 16.0 s | candado `agenda` | sí → 3 reintentos |
| 22.5 s | `motor_negocios` | sí → 3 reintentos |

**Todo lo que no toca Groq responde en menos de un segundo.**

---

## 3. Las fases, en orden de valor contra costo

Cada fase **cierra con las 76 pruebas en verde y su propio commit**. Copilot
**para y reporta** al terminar cada una. Nunca encadena fases sin revisión.

---

### FASE 1 — Quitarle el dolor (≈1 hora)
*Lo más barato y lo que más se nota. Va primero.*

**1.1 — Bajar los reintentos de 3 a 1**

`CEREBRO/consciencia.py`, línea ~725:

```python
# max_retries=1: con el default, un 429 costaba 16-22 s de espera antes de
# responder (medido 2026-07-31). Si Groq dice que no, es mejor caer rápido a
# Ollama que esperar tres veces por lo mismo.
self._groq = AsyncGroq(api_key=api_key, max_retries=1) if api_key else None
```

*Cierre:* los casos lentos bajan de ~16-22 s a ~6-8 s, cronometrado.
**Si no bajan, PARAR y reportar** — la espera vendría de otro lado.

**1.2 — Caer a Ollama cuando Groq falle**

Ollama local (`llama3.2:3b`) ya funciona en modo offline. Cuando Groq devuelva
429 o falle, usarlo **una vez** antes de rendirse.

- La respuesta debe **decir** que se usó el modelo local. Nunca ocultarlo.
- Si Ollama tampoco responde: *"no pude conectarme al modelo"*. **Jamás inventar.**

*Cierre:* apagar la llave de Groq **en el entorno** (NO borrarla del `.env`) y
comprobar que AURORA sigue respondiendo en segundos.

**1.3 — Techo de llamadas por turno** *(idea de Copilot, buena)*

Un mensaje del usuario no debe disparar más de **2** llamadas al modelo. Contar
primero cuántas dispara hoy; si son más de 2, ahí está el desperdicio que agota
la cuota.

*Cierre:* tabla real de llamadas por mensaje en `_CONTEXTO/LINEA_BASE.md`.

---

### FASE 2 — Que no se pierdan datos (≈2 horas)
*Copilot encontró esto en los logs y es lo más grave del sistema.*

Errores reales de SQLite: `UNIQUE constraint` y `database is locked`.

Un `database is locked` en el taller puede perder una orden de trabajo. **Eso es
peor que cualquier lentitud** y hay que arreglarlo antes de enseñarle nada a un
cliente.

- Localizar en qué rutas ocurren (los logs los tienen).
- Serializar las escrituras que chocan.
- Idempotencia donde aplique: repetir una operación no debe duplicar el registro.

*Cierre:* prueba de concurrencia real —dos operaciones simultáneas sobre la misma
tabla— sin errores. Logs limpios.

---

### FASE 3 — Que el chat sirva de verdad (≈1 día)
*El problema de fondo: hay capacidades sin puerta de entrada.*

**3.1 — Mapa de capacidad conversacional** *(idea de Copilot, es la correcta)*

En vez de agregar frases cuando algo falla —que fue el error de toda la
sesión—, garantizar que **cada herramienta crítica tenga al menos una frase
natural que llegue a ella**.

Producir `_CONTEXTO/MAPA_CAPACIDADES.md`: `capacidad → frase natural → herramienta`.

Empezar por las que van en el demo, no por las 517.

**3.2 — Nunca quedarse muda**

Si ningún motor aplica, decir qué **sí** puede hacer. El silencio es peor que un
"no puedo": el usuario no sabe si falló o lo ignoraron.

Casos reales que hoy fallan y deben pasar:

```
corel tiene instalado el plugin laser
como mi coach que me puedes aportar
usa coreldrau para vectorizar el archivo que tengo abierto
edita tu archivo CORE/buscador_web_profesional.py
si publicalo                      ← confirmación que hoy NO se reconoce
diagnostica el problema           ← hoy cae en el motor de faros de ATF
```

**3.3 — Charla no pide permiso**

Solo se confirma lo que toca algo real: escribir, borrar, enviar, publicar.
Coaching, consultas y análisis **jamás** deben pedir confirmación. Hoy sí lo
hacen, y el usuario cree que no le respondió.

*Cierre:* los 6 casos de arriba resueltos, verificados en vivo.

---

### FASE 4 — EL DEMO (≈1 día) ⭐
*Esta es la fase que importa. Todo lo anterior existe para que esta salga bien.*

**4.1 — El guion**

Diez comandos, ni uno más, elegidos porque cuentan una historia de negocio:

| # | Qué muestra | Por qué impresiona |
|---|---|---|
| 1 | Saluda por nombre a quien escribe | "sabe quién soy" |
| 2 | Cotiza con catálogo real | precios de verdad, no inventados |
| 3 | Agenda una cita | y avisa antes |
| 4 | Consulta ventas del mes | dato real de su operación |
| 5 | Busca en internet | proveedores reales, con fuente |
| 6 | Abre un archivo en Corel | **acción física en la PC** |
| 7 | Convierte a DXF | listo para cortar |
| 8 | Manda un WhatsApp real | al celular del cliente, en vivo |
| 9 | Distingue familia de cliente | no le vende a la hija |
| 10 | **Se niega a inventar** | el candado, en vivo |

**El número 10 es el más importante.** Pedirle algo que no puede hacer y que
diga *"no ejecuté nada"*. Ningún competidor puede enseñar eso, y es lo que
convierte "otra IA" en "una que no me va a quemar con mi cliente".

**4.2 — Cada uno probado 3 veces seguidas**

No una. **Tres.** Si uno falla una de tres, no entra al guion. En un demo no hay
segunda oportunidad.

**4.3 — Documentar en `_COMERCIAL/4FORTE/GUION_DEMO.md`**

Frase exacta, respuesta esperada, y **qué hacer si falla en vivo**.

**4.4 — Plan B sin internet**

Si en 4Forte no hay WiFi o Groq no responde, el demo debe seguir con Ollama
local. Probarlo **con el WiFi apagado de verdad**, no en teoría.

*Cierre:* los 10 comandos, 3 de 3, con el guion escrito y el plan B probado.

---

### FASE 5 — Observabilidad (≈medio día)
*Al final, no al principio: hace baratas todas las sesiones futuras.*

Trazabilidad por turno: ruta, herramienta, latencia, estado. Configurable
(debug on/off), no logs temporales invisibles.

*Cierre:* diagnosticar cualquier fallo en menos de 10 minutos leyendo el log.

---

## 4. Lo que NO se hace

- **No rediseñar el enrutamiento.** Tarda 1 segundo. Está bien.
- **No eliminar `_routing_llm`** por velocidad. No es la causa.
- **No quitar candados.** Los rápidos son la parte buena.
- **No cambiar de modelo.** `llama-3.1-8b-instant` responde en 1-2 s cuando pasa.
- **No reescribir `validador_honestidad.py`.** Se extiende.
- **No restar funciones.** Dos años que ya sirven.
- **No perseguir las 517 herramientas.** El demo son 10.

---

## 5. Prompt para Copilot (modo agente)

**Una fase a la vez.** Cambiar el número en cada corrida.

```
Trabajas sobre AURORA en C:\AURORA.worktrees. Es PRODUCCIÓN: dos años de trabajo
operando dos negocios reales. Nada aquí es un ejercicio.

Lee COMPLETOS antes de escribir una línea:
  _CONTEXTO\LEEME_PRIMERO.md
  _CONTEXTO\ESTADO_REAL.md
  _CONTEXTO\PLAN_MAESTRO_DEMO.md

TAREA: ejecuta ÚNICAMENTE la FASE <N>. Al terminarla, PARAS y reportas.
NO encadenes fases. NO "aproveches para" arreglar nada más.
Si crees que otra fase es más urgente, dilo y espera respuesta — no la hagas.

CÓMO ARRANCAR AURORA
  python run_aurora.py            (tarda ~90 segundos)
  Verifica: http://127.0.0.1:5000/health
  Usa 127.0.0.1, NO localhost — con localhost falla por IPv6.

CÓMO PROBAR
  POST http://127.0.0.1:5000/chat
  {"mensaje": "...", "session_id": "prueba", "canal": "api"}

REGLAS QUE NO SE NEGOCIAN
- Nada simulado. Ni mocks, ni datos de ejemplo, ni "supongamos". Si algo no se
  puede hacer de verdad, PARAS y lo dices con esas palabras exactas.
- Nada se declara hecho sin la salida real del comando pegada. Un resumen no es
  una prueba. Describir un cambio no es haberlo hecho.
- NO restar funciones. Lo que funciona hoy se conserva.
- validador_honestidad.py se EXTIENDE, jamás se reescribe. Es lo único que
  impide que AURORA le mienta a un cliente.
- consciencia.py está BLINDADO por una razón real: el auto-reparador casi borró
  el 96% de ese archivo una vez. Cambios mínimos y quirúrgicos.
- NUNCA imprimas el valor de una variable del .env. Solo su nombre.
- Ante cualquier riesgo de romper algo: PARAS y preguntas.
- Español en el código y los comentarios, en el estilo del que ya está ahí.

AL CERRAR LA FASE
  python -m pytest tests/ -q    → deben ser 76 passed. Pega la salida COMPLETA.
  Un solo commit para esta fase, para poder revertir.

ENTREGAS
a) Qué cambiaste y por qué
b) La prueba real: el comando exacto y su salida pegada
c) Los tiempos medidos antes y después, donde aplique
d) Qué NO quedó cubierto y por qué. Esta sección NUNCA va vacía.
```

---

## 6. Lo que hace Anuar, y no se delega

1. **Correr él** `python -m pytest tests/ -q` al cerrar cada fase → **76 passed**.
   Si no, `git revert` de ese commit.
2. **Cronometrar él.** Si dice que bajó de 20 s a 5 s, comprobarlo escribiéndole
   a AURORA y contando.
3. **No creer un "ya está" sin salida de comando pegada.**
   Precedente real: el 30 de julio AURORA describió con detalle un respaldo, un
   borrado de líneas y una compilación **que nunca ocurrieron**. El candado de
   honestidad la delató. **Copilot no tiene ese candado.**
4. **No dejar que corra varias fases seguidas.** Si se equivoca en la fase 2, las
   siguientes se construyen sobre el error y nadie se entera hasta el final.

---

## 7. La lección que costó esta sesión

Se escribió un plan de 6 etapas, sólido y detallado, para rediseñar el corazón
del sistema. **Apuntaba al lugar equivocado.** Cuatro mediciones de treinta
segundos lo tumbaron entero: el enrutamiento tarda 1 segundo, y los 22 segundos
eran la cuota de Groq.

Y los cinco bugs de esa madrugada no los encontró ninguna auditoría: los
encontró Anuar escribiéndole a AURORA como le escribe cualquiera, con typos y
frases sueltas.

**Antes de cortar, medir. Y probar como escribe la gente, no como escribe quien
programó.**
