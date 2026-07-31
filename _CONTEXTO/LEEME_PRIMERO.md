# 🚦 LEEME PRIMERO — Contexto de AURORA
### Para cualquier IA o persona que llegue a este proyecto. Léelo completo antes de tocar nada.

> **Por qué existe esta carpeta:** más del 60 % de los tokens gastados en este
> proyecto se fueron en que cada sesión nueva redescubriera lo mismo. Esta
> carpeta es el mapa. Leerla cuesta 5 minutos y ahorra medio presupuesto.
> Debió existir hace medio año. Ahora existe: **manténla actualizada.**

---

## 1. Qué es AURORA (en dos párrafos)

AURORA es una **consola** con motores intercambiables (cartuchos) sobre un bus
neuronal. Vive en `C:\AURORA.worktrees`, corre en el **puerto 5000** con
`run_aurora.py`, tarda ~90 s en arrancar y la construyó **Anuar Milán** a lo
largo de dos años para operar sus negocios reales.

**Lo más importante de entender:** la estructura **no sabe de qué ramo es**. El
núcleo (chat, memoria, bus, enrutador universal, registro de herramientas,
panel, multi-usuario, WhatsApp, agenda, CRM, cotizador) sirve igual para un
taller, una primaria o un despacho. Lo único específico son los catálogos y
algunos motores. **AURORA es agnóstica de dominio por diseño** — ese es su
activo más valioso, y se descubrió apenas el 2026-07-30.

---

## 2. Las reglas que NO se negocian

Están primero porque romper una cuesta más que cualquier función que agregues.

1. **Nada simulado.** Ni mocks, ni datos de ejemplo, ni `return "ok"`, ni TODO,
   ni `pass` como cuerpo. Si algo no se puede hacer de verdad: **paras y lo
   dices con esa palabra.**
2. **Nada se declara listo sin prueba real ejecutada.** Se pega la salida del
   comando, no un resumen ni una promesa.
3. **No restar funciones.** Son dos años de trabajo que YA funciona. Ante riesgo
   de romper algo: **paras y preguntas.**
4. **Corrección de raíz, cero parches.** Anuar lo dijo textual: *"ya es
   demasiadas veces y parches y fixes"*. Un parche más es un retroceso.
5. **Verificar contra el registro real** antes de usar cualquier función del
   núcleo: `CEREBRO/registro_herramientas.descubrir()`. Si no está ahí, no
   existe — no la uses ni la inventes.
6. **Protocolo de ideas:** Anuar da la idea → tú analizas y devuelves las
   mejoras **realmente posibles** ANTES de construir → él decide. Y le anotas
   cada idea al instante diciéndole "anotada" (tiene TDAH; cargar 5-6 hilos
   simultáneos le pesa de verdad).
7. **Cambios estructurales llevan plan escrito antes de tocar código.**
8. **Eficiencia de tokens permanente.** Arreglos chicos: directo, sin agentes.
9. **Nunca** pegar llaves, PINs ni tokens en el chat. Van directo al `.env`.
   Nunca imprimir valores del `.env`, solo nombres de variable.
10. **AURORA tiene Fábrica de Agentes pero NUNCA la usa sin autorización de
    Anuar.** Capacidad ≠ autonomía. Es su regla de oro.

---

## 3. Mapa de la carpeta

| Archivo | Qué contiene |
|---|---|
| `LEEME_PRIMERO.md` | esto |
| `ESTADO_REAL.md` | qué funciona **verificado**, qué no, y qué está pendiente |
| `FABRICA_DE_MOTORES.md` | plano de Aurorita XP, la fábrica que produce motores |
| `PROPUESTA_4FORTE.md` | la propuesta comercial, versión simplificada |

**Fuera de esta carpeta, lo que de verdad importa:**

| Ruta | Qué es |
|---|---|
| `MANUALES/manual_comandos_aurora.md` | **generado del código real** — 17 candados + 517 herramientas. No se escribe a mano; se regenera con `python CEREBRO/generar_manual.py` |
| `MANUALES/COMANDOS_VERIFICADOS.md` | solo lo probado **en vivo**, más lo que honestamente no funciona |
| `tests/test_regresion_bugs_reales.py` | 63 pruebas, una por bug real que de verdad ocurrió |
| `CEREBRO/consciencia.py` | el corazón: los candados y el punto único de salida |
| `CEREBRO/validador_honestidad.py` | el candado anti-simulación (ver abajo) |
| `CEREBRO/registro_herramientas.py` | descubre las herramientas reales del sistema |

---

## 4. Lo único que hay que entender del código

**`CEREBRO/consciencia.py` — el flujo de un mensaje:**

```
mensaje del usuario
   ↓
_CANDADOS  ← lista ordenada de (nombre, disparador, método, motor)
   ↓        si una frase calza → ejecuta ese motor directo (determinista)
   ↓        si ninguna calza  → cae al enrutador universal (IA con tool-calling)
   ↓
procesar() ← PUNTO ÚNICO DE SALIDA. Todas las respuestas pasan por aquí.
   ├── _verificar_capacidad_real   (atrapa NEGACIONES falsas: "no puedo" cuando sí puede)
   └── validador_honestidad.revisar (atrapa AFIRMACIONES falsas: "ya lo hice" sin hacerlo)
   ↓
respuesta
```

**Si vas a agregar un candado o una protección, va en el punto único de salida,
no en cada función.** Ese es el error que se cometió durante meses.

---

## 5. La historia que no debe repetirse

El 29 y 30 de julio de 2026, AURORA **inventó cosas siete veces**: fingió que
CorelDRAW había vectorizado un PDF (archivo que nunca existió), generó un
"manual maestro" con 6 de 8 comandos inventados, y un "kit de configuración"
con tres `.bat` inexistentes.

**Causa única de las siete:** cuando la frase no calzaba con un candado exacto,
caía a un modelo de texto sin acceso al sistema — que respondía igual, como si
tuviera manos.

**No se arregló agregando frases** (eso es infinito). Se arregló con
`CEREBRO/validador_honestidad.py`: **código**, no una regla de prompt, corriendo
en el punto único de salida. Revisa tres cosas contra la realidad:

1. ¿Afirma haber ejecutado algo, sin que se ejecutara nada?
2. ¿Cita comandos que no están en el registro real?
3. ¿Menciona archivos que no existen en el disco?

Nunca borra la respuesta: le agrega la corrección honesta y visible. Verificado
en vivo contra los 4 inventos reales: **4/4 sin mentir**.

> **La lección, que aplica a todo lo que sigue:** una regla en el prompt la
> ignora un modelo chico. Un candado en código, no.

---

## 6. Cómo arrancar una sesión sin quemar el presupuesto

1. Lee esta carpeta completa (5 min).
2. Lee `MEMORY.md` si tienes acceso a la memoria del proyecto.
3. **No re-verifiques lo que `ESTADO_REAL.md` ya da por verificado.** Si dice
   "63/63 pruebas pasan", pasan. Correrlas otra vez cuesta 46 s y no aporta.
4. Pregunta a Anuar **una sola cosa**: qué quiere hoy. Luego trabaja.
5. Al terminar, **actualiza `ESTADO_REAL.md`**. Si no lo actualizas, la próxima
   sesión vuelve a pagar el descubrimiento y esta carpeta no sirvió de nada.
