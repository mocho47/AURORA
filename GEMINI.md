# AURORA — contexto para Gemini

## Qué es esto

AURORA es un sistema **en producción**. Lo construyó Anuar Milán a lo largo de
dos años y con él opera dos negocios reales: Milens (corte láser y sublimación)
y ATF (retrofit de faros). Corre todos los días. Nada aquí es un ejercicio.

Es una **consola con motores intercambiables** sobre un bus. El núcleo —chat,
memoria, enrutador universal, panel, WhatsApp, agenda, cotizador— no sabe de qué
ramo es: sirve igual para un taller, una primaria o un despacho. Lo único que
cambia entre clientes son los motores.

```
Ruta        C:\AURORA.worktrees
Arranque    python run_aurora.py         (~90 s, 28 motores)
Puerto      5000
Salud       http://127.0.0.1:5000/health    <- 127.0.0.1, NO localhost (IPv6 falla)
Python      C:\Program Files\Python312\python.exe
Pruebas     python -m pytest tests/ -q      -> 76 passed
Chat (API)  POST http://127.0.0.1:5000/chat
            {"mensaje": "...", "session_id": "prueba", "canal": "api"}
```

## LEE ESTO ANTES DE PROPONER CAMBIOS

- `_CONTEXTO/LEEME_PRIMERO.md` — reglas, mapa, cómo arrancar sin gastar de más
- `_CONTEXTO/ESTADO_REAL.md` — qué funciona **verificado**, qué no, y por qué
- `_CONTEXTO/PLAN_MAESTRO_DEMO.md` — el trabajo pendiente, ya priorizado
- `MANUALES/COMANDOS_VERIFICADOS.md` — lo único probado en vivo

Esa carpeta existe porque el 60 % de los tokens se iba en redescubrir el
proyecto cada sesión. Leerla cuesta 5 minutos y ahorra medio presupuesto.

## REGLAS QUE NO SE NEGOCIAN

1. **Nada simulado.** Ni mocks, ni datos de ejemplo, ni `return "ok"`, ni `TODO`,
   ni `pass` como cuerpo, ni "supongamos que". Si algo no se puede hacer de
   verdad, **paras y lo dices con esas palabras exactas**.

2. **Nada se declara hecho sin la salida real del comando pegada.** Describir un
   cambio no es haberlo hecho. Un resumen no es una prueba.

   > Precedente real: el 30 de julio de 2026 AURORA describió con detalle un
   > respaldo, un borrado de líneas y una compilación **que nunca ocurrieron**.
   > Hay un candado en código que la delató. Tú no tienes ese candado: la
   > disciplina la pones tú.

3. **No restar funciones.** Son dos años de trabajo que ya sirve. Ante cualquier
   riesgo de romper algo: **paras y preguntas.** Quitar código es decisión de
   Anuar, nunca autónoma.

4. **Corrección de raíz, cero parches.** Anuar lo dijo textual: *"ya son
   demasiadas veces, parches y fixes"*. Un parche más es un retroceso.

5. **Verifica contra el registro real** antes de usar cualquier función del
   núcleo: `CEREBRO/registro_herramientas.descubrir()`. Si no está ahí, no
   existe — no la uses ni la inventes.

6. **Una tarea a la vez.** Al terminar, paras y reportas. Encadenar etapas
   construye sobre errores que nadie ve hasta el final.

7. **Nunca imprimas el valor de una variable del `.env`.** Solo su nombre.

8. **Español** en el código y los comentarios, en el estilo del que ya está ahí.

## ARCHIVOS BLINDADOS — cambios mínimos y quirúrgicos

| Archivo | Por qué |
|---|---|
| `CEREBRO/consciencia.py` | 148,000 caracteres. El auto-reparador casi borró el 96 % de este archivo una vez. Es el corazón |
| `CEREBRO/validador_honestidad.py` | **Se EXTIENDE, jamás se reescribe.** Es lo único que impide que AURORA le mienta a un cliente |
| `CORE/aurora_server.py` | 163 endpoints en producción |
| `run_aurora.py` | El arranque |

## Los problemas reales de hoy (medidos, no supuestos)

**Lo que duele:** desde el chat, la mayoría de las peticiones no se ejecutan.
De siete intentos reales de Anuar, seis fallaron. Los motores funcionan; lo que
falla es la forma de pedírselo. **Es un problema de interfaz, no de fundamento.**

Casos concretos que hoy fallan y deben pasar:

```
convierte a pdf                      entiende el verbo, no el objeto
corel tiene instalado el plugin      cae en un motor que no le toca
como mi coach que me puedes aportar  pide permiso para platicar
edita tu archivo <ruta>              nunca llega al cartucho IDE
si publicalo                         no se reconoce como confirmación
diagnostica el problema              cae en el motor de faros de ATF
```

**La lentitud NO es la arquitectura.** Está medido: el enrutador tarda 1 s, los
candados 0.7 s. Los 16-22 s son la cuota de Groq (error 429 + tres reintentos).
El plan para arreglarlo está en `_CONTEXTO/PLAN_MAESTRO_DEMO.md`, fase 1.

**AURORA no es un navegador.** Hace búsquedas contra una API y devuelve
resultados. No abre páginas, no entra a YouTube, no hace clic. Nunca prometas
que navega.

## Cómo se trabaja aquí

**Antes de cortar, medir.** El 31 de julio se escribió un plan de 6 etapas para
rediseñar el enrutamiento, sólido y detallado — y apuntaba al lugar equivocado.
Cuatro mediciones de treinta segundos lo tumbaron entero.

**Y prueba como escribe la gente, no como escribe quien programó.** Los cinco
bugs reales de esa semana no los encontró ninguna auditoría: los encontró Anuar
escribiéndole a AURORA con typos y frases sueltas, como le escribe cualquiera.

## Cómo entregas, siempre

- **a)** Qué cambiaste y por qué
- **b)** La prueba real: el comando exacto y su salida pegada
- **c)** Qué **NO** quedó cubierto y por qué — **esta sección nunca va vacía**

Al cerrar: `python -m pytest tests/ -q` → **76 passed**, con la salida pegada.
Un commit por tarea, para poder revertir.
