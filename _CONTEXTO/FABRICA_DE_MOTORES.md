# 🏭 AURORITA XP · Fábrica de Motores
### Plano de construcción — 2026-07-30

> **Qué es esto:** la especificación con la que se construye. No es un resumen
> de ideas. Cualquier IA que lea este archivo debe poder ejecutarlo sin volver
> a preguntar el contexto.
>
> **Decisión de origen (Anuar):** **no se corta nada de AURORA. Se copia.**
> AURORA sigue funcionando intacta; Aurorita XP es una copia con otro nombre,
> potenciada **exclusivamente** para generar motores. AURORA queda virgen: una
> consola donde solo se agrega o se quita un motor.

---

## 0. El problema que resuelve

AURORA es agnóstica de dominio. Lo único que cambia entre un cliente y otro son
**los motores**. Por lo tanto:

> **El producto no es AURORA. El producto es la capacidad de producir motores.**

Hoy la Fábrica de Agentes genera esqueletos que corren. No alcanza. Un motor
terminado llega con manifiesto, pruebas verdes, conocimiento de dominio
verificado y su commit. Si no, cada motor es trabajo manual y la motorteca se
vuelve un basurero.

**Lo que hace posible una motorteca grande no es generar rápido — es verificar
sin excepciones.** El 29-30 de julio AURORA inventó siete veces. Mil motores sin
probar son mil formas nuevas de mentirle a un cliente. Por eso el Juez no es
opcional.

---

## 1. Anatomía — los once órganos

Si falta uno, la fábrica produce basura convincente.

### 🦴 ESQUELETO — El Contrato del Motor
**Se construye primero. Sin esto, nada encaja.**

```
motor_<nombre>/
├── motor.json          ← manifiesto (identidad + contrato)
├── motor_<nombre>.py   ← el código
├── pruebas/test_<nombre>.py
├── datos/              ← catálogos, plantillas (opcional)
└── LEEME.md            ← qué hace, en lenguaje simple
```

`motor.json` declara:

| Campo | Para qué |
|---|---|
| `nombre`, `version`, `dominio` | identidad y ramo |
| `descripcion` | una línea en lenguaje humano |
| `expone` | funciones públicas: nombre, parámetros, qué devuelve |
| `necesita_del_nucleo` | servicios que usa — **lista cerrada** |
| `dependencias` | paquetes pip con versión |
| `pruebas` | ruta al archivo de pruebas |
| `requiere_llaves` | variables de entorno **por nombre**, nunca el valor |
| `peligroso` | si ejecuta algo irreversible → pide confirmación |
| `generado_por`, `verificado_el`, `commit` | trazabilidad |

**Regla de oro:** un motor solo toca el núcleo por lo que declaró en
`necesita_del_nucleo`. Si necesita algo no declarado, no pasa el Juez. Esto es
lo que hace que "agregar motor" sea copiar una carpeta.

---

### 🧠 CEREBRO — El Arquitecto
**No escribe código. Escribe la especificación.**

Recibe una necesidad humana ("un motor de boletas para primaria") y produce:
funciones exactas, entradas y salidas, casos límite, qué debe **rechazar**, qué
NO le toca, criterios de aceptación.

*Por qué existe:* hoy los motores salen incompletos porque nadie define
"completo" antes de escribir.  · *Modelo:* fuerte.

---

### 👁️ OJOS — El Investigador de Dominio
**Evita que el motor alucine el negocio.**

Un motor de boletas necesita saber de boletas: promedios, escalas, reglamentos.
AURORA no lo sabe y si lo intenta, lo inventa. El Investigador busca en web,
manuales y PDFs y entrega **hechos con fuente citada**. Lo que no encontró lo
marca como hueco.

*Regla:* un hueco es una pregunta para el humano, nunca una suposición.
· *Modelo:* rápido + `WEB/web_real` (ya existe).

---

### ✋ MANOS — El Constructor
Toma la spec + los hechos y escribe código, manifiesto, pruebas y LEEME.

*Regla dura:* **nunca inventa APIs del núcleo.** Consulta
`CEREBRO/registro_herramientas.descubrir()` antes de usar cualquier cosa. Si no
está ahí, no existe.  · *Modelo:* hiperfast (Groq) — es el paso que más se repite.

---

### 🛡️ SISTEMA INMUNE — El Verificador
**Prueba que CORRE, en aislamiento real.**

1. Directorio temporal + `venv` limpio
2. Instala solo lo declarado *(si falta algo, el manifiesto miente)*
3. Importa el motor *(si truena aquí, se acabó)*
4. Corre pytest
5. Verifica que no escribió fuera de su carpeta
6. Verifica que no llamó a producción (WhatsApp real, Facebook real, DBs reales)

Devuelve verde o rojo **con la salida pegada**, nunca un resumen.

> ⚠️ **VS Code no aísla nada** — es un editor. Lo que aísla es `venv` +
> temporal + pytest. VS Code sirve para lanzarlo cómodo, y para eso es
> excelente. Pero si se le confía el aislamiento, un motor mal generado toca
> archivos reales.

---

### ⚖️ CONCIENCIA — El Auditor Adversario
**Distinto del Verificador.** Aquel prueba que corre; este intenta **romperlo**:

- ¿Simula? (`return "ok"`, datos hardcodeados, `TODO`, `pass`)
- ¿El docstring dice algo distinto de lo que hace el código?
- ¿Maneja vacío, nulo, negativo, archivo inexistente?
- ¿Hardcodea rutas, teléfonos o llaves?
- ¿Reinventa algo que **ya existe** en el núcleo?
- ¿Las pruebas prueban de verdad, o solo que la función existe?

**Tres auditores independientes con lentes distintos** (corrección / seguridad /
¿de verdad hace lo que dice?). Mayoría manda. Mismo patrón que ya funcionó con
el validador de honestidad.  · *Modelo:* fuerte. Aquí no se ahorra.

---

### 👨‍⚖️ JUEZ — El Aprobador
**La única puerta. Reglas duras, no opinión:**

- [ ] Pruebas 100 % verdes en aislamiento
- [ ] Manifiesto honesto (todo lo que usa está declarado)
- [ ] Cero bloqueantes del Auditor
- [ ] Cero simulación detectada
- [ ] No duplica un motor del catálogo
- [ ] LEEME entendible por alguien que no programa

Si falla → **regresa al Constructor con el motivo exacto**, no con "mejóralo".
Máximo **3 reintentos**; al cuarto para y pregunta. Un bucle infinito quemando
tokens es un fracaso, no una fábrica.

---

### 🧬 MEMORIA — El Catálogo (la motorteca)
Índice de lo publicado: nombre, dominio, versión, qué expone, pruebas, commit.

*Para qué sirve de verdad:* **evitar duplicados.** El Arquitecto lo consulta
antes de construir; si ya existe algo parecido, se **extiende** en vez de crear
el motor 47 que hace lo del 12. Eso hace que la motorteca sea *completa* y no
solo *grande*.

> El disco no es el límite: un motor pesa 20–80 KB. **Mil motores ≈ 50 MB.**
> Donde sí hacen falta terabytes es en la **biblioteca de conocimiento**
> (manuales, PDFs, embeddings, históricos). El instinto del disco de 1 TB es
> correcto; su destino es la memoria, no los motores.

---

### 🦵 PIERNAS — El Commiteador
**Solo se mueve si el Juez aprobó. Nunca commitea rojo.**
Rama por motor → commit con la evidencia pegada → push → alta en el catálogo →
aviso a Anuar en lenguaje simple.

---

### ❤️ CORAZÓN — El Orquestador

```
necesidad
   ↓
Arquitecto   → spec
   ↓
Investigador → hechos de dominio (con fuente)
   ↓
Constructor  → código + manifiesto + pruebas
   ↓
Verificador  → ¿corre aislado?        ──rojo──┐
   ↓ verde                                    │
Auditor ×3   → ¿es real o simula?     ──rojo──┤
   ↓ verde                                    │
Juez         → las 6 reglas           ──rojo──┤
   ↓ verde                                    │
Commiteador  → rama, commit, catálogo         │
                                              │
      ←──── reintento con el motivo exacto ───┘
                 (máximo 3, luego pregunta)
```

---

### 🩸 NERVIOS — La Bitácora
Cada paso con su evidencia: qué modelo, qué prompt, qué devolvió, cuánto costó,
qué falló. Sin bitácora no se sabe **por qué** salió mal, y la fábrica no mejora.

---

## 2. Reparto de modelos

| Pieza | Modelo | Por qué |
|---|---|---|
| Constructor | **hiperfast** (Groq) | mecánico, se repite mucho |
| Investigador | rápido + web real | busca y cita, no razona hondo |
| Verificador | **ninguno, es código** | pytest no necesita IA |
| Commiteador | **ninguno, es código** | git no necesita IA |
| Arquitecto | fuerte | define "completo"; fallar aquí cuesta todo |
| Auditor ×3 | fuerte | detectar simulación es lo más difícil |
| Juez | código + fuerte | las 6 reglas son código; el veredicto razona |

**Lo que no lleva IA, no lleva IA.** Ahorra dinero y no puede alucinar.

---

## 3. Guardarraíles — lo que la fábrica NUNCA hace

1. **Nunca toca AURORA de producción.** Otra carpeta, otro puerto, otro `.env`.
2. **Nunca tiene llaves de publicar.** Sin `FB_PAGE_TOKEN` ni Green API válidos.
   Si los tuviera, un motor mal generado publica de verdad en la página de ATF.
3. **Nunca hereda las tareas de Windows** (`AURORA_Publicar_ATF`,
   `AURORA_Arranque`). Si las hereda, se publica dos veces.
4. **Nunca escribe fuera de su carpeta** durante la verificación.
5. **Nunca commitea en rojo.**
6. **Nunca reintenta más de 3 veces.**
7. **Nunca instala un motor en AURORA sola.** La fábrica *produce*; instalar lo
   decide Anuar. *(Su regla de oro, vuelta estructural en vez de disciplina.)*

---

## 4. El techo real — lo que NO puede garantizar

**El Verificador prueba que el motor CORRE. No que sea CORRECTO para el
negocio.** Un motor de boletas puede correr impecable y calcular mal el
promedio, porque el reglamento de esa escuela dice otra cosa.

Lo que sí se puede: el Investigador cita fuentes y marca huecos, y todo motor de
un dominio nuevo se marca `validacion_humana: pendiente` hasta que alguien del
ramo lo confirme **una vez**. Después el dominio queda aprendido y los
siguientes motores heredan las reglas confirmadas.

> **Automatizar la producción es real. Automatizar el juicio de negocio, no.**
> Mejor saberlo aquí que frente a un cliente.

---

## 5. PLAN DE CONSTRUCCIÓN

Cada etapa termina con algo que **corre y está probado**. Si una etapa no cierra,
no se pasa a la siguiente — así nunca hay medio proyecto.

| # | Etapa | Entregable que corre | Por qué en este orden |
|---|---|---|---|
| **1** | Contrato del motor | `motor.json` de ejemplo sobre un motor **real ya existente**, y un validador de manifiestos que corre | Sin contrato, todo lo demás es cosmético. Probarlo contra un motor que ya funciona demuestra que el contrato sirve |
| **2** | Copia aislada | Aurorita XP arranca en puerto 5001, sin llaves de publicar, sin tareas de Windows, `/health` responde | Antes de potenciar, probar que no se pisa con AURORA |
| **3** | Verificador | Corre un motor existente en venv temporal y devuelve verde con la salida real | Probar sin aislar es mentirse. Va antes que el generador |
| **4** | Constructor + Arquitecto | Generan un motor simple **de un dominio que Anuar domina** y pasa el Verificador | Ya hay contra qué verificar |
| **5** | Auditor ×3 | Detecta un motor simulado **plantado a propósito** | Se prueba con una trampa, no con buena fe |
| **6** | Juez + Catálogo | Rechaza el motor malo, aprueba el bueno, detecta un duplicado | La puerta y el antiduplicados |
| **7** | Commiteador | Commit real con la evidencia pegada, alta en el catálogo | Al final: solo commitea lo aprobado |
| **8** | Investigador de dominio | Trae hechos con fuente de un ramo nuevo (primaria) | Lo que abre los ramos nuevos |

**Ya existe y solo se muda** (no se construye): Fábrica de Agentes, cartucho IDE,
`registro_herramientas`, las 63 pruebas, `validador_honestidad`, el bus, el panel.
**Esto es una mudanza con refuerzos, no una obra desde cero.**

**Criterio de avance:** una etapa está cerrada cuando corre en la máquina, tiene
su prueba de regresión, y otra persona entendería qué hace leyendo el LEEME.
Si falta una de las tres, no está cerrada — y decirla cerrada es el peor error.

---

## 6. PROMPT MAESTRO

> Para pegarle a cualquier IA (Claude, VS Code, otra sesión) y que arranque sin
> volver a explicar nada. **Una etapa a la vez** — quien intente las ocho de un
> jalón entrega ocho cosas a medias.

```
Eres un ingeniero senior construyendo AURORITA XP, una fábrica que produce
motores para AURORA de forma automática, terminados y verificados.

CONTEXTO OBLIGATORIO
Lee estos dos archivos completos antes de escribir una sola línea:
  C:\AURORA.worktrees\_CONTEXTO\LEEME_PRIMERO.md
  C:\AURORA.worktrees\_CONTEXTO\FABRICA_DE_MOTORES.md
Ahí están la anatomía, el contrato del motor, el plan y los guardarraíles.
AURORA (C:\AURORA.worktrees, puerto 5000) es PRODUCCIÓN y NO se toca. Aurorita
XP es una copia con otro nombre, otro puerto y sin llaves de publicar.

TU TAREA
Construir ÚNICAMENTE la etapa: <NÚMERO Y NOMBRE DE LA ETAPA>
No adelantes otras etapas. No dejes ganchos "para después".

REGLAS QUE NO SE NEGOCIAN
1. Nada simulado. Ni mocks, ni datos de ejemplo, ni `return "ok"`, ni TODO, ni
   `pass` como cuerpo. Si algo no se puede hacer de verdad, PARAS y lo dices con
   esa palabra: "esto no se puede hacer de verdad, y esta es la razón".
2. Nada se declara listo sin prueba real ejecutada. Pegas la salida completa del
   comando, no un resumen ni una promesa.
3. No restes funciones. Si algo ya funciona, se conserva. Ante riesgo de romper
   algo: PARAS y preguntas.
4. Antes de usar cualquier función del núcleo, verifícala contra
   CEREBRO/registro_herramientas.descubrir(). Si no está ahí, no existe: no la
   uses ni la inventes.
5. Cero parches, cero código huérfano. Corrección de raíz o nada.
6. Código y comentarios en español, en el estilo del código que ya está ahí.
7. Si te falta algo para hacerlo bien, pregunta ANTES de construir. Una pregunta
   cuesta menos que un motor mal hecho.

CÓMO ENTREGAS
a) Qué construiste y por qué así (breve).
b) El código completo, sin recortes ni "...".
c) La prueba real: el comando que corriste y su salida pegada.
d) Qué NO quedó cubierto y por qué. Esta sección nunca va vacía.
e) Qué etapa sigue.

CRITERIO DE TERMINADO
La etapa está terminada cuando corre de verdad en esta máquina, tiene su prueba
de regresión que la protege, y otra persona entendería qué hace leyendo solo el
código y su LEEME. Si falta cualquiera de las tres, no está terminada, y
decirla terminada es el peor error posible.
```

---

## 7. Prompt para producir UN motor (la fábrica en operación)

```
Necesito un motor para AURORA que: <NECESIDAD EN LENGUAJE HUMANO>
Dominio: <taller | primaria | despacho | ...>

Sigue el ciclo completo de FABRICA_DE_MOTORES.md en orden, sin saltarte pasos:

1. ARQUITECTO — spec antes que código: funciones, entradas, salidas, casos
   límite, qué debe RECHAZAR, qué NO le toca. Consulta el catálogo primero: si
   ya existe algo parecido, extiéndelo en vez de duplicarlo.
2. INVESTIGADOR — hechos reales del dominio, CON FUENTE. Lo que no encuentres,
   márcalo como hueco y pregúntamelo. No lo rellenes suponiendo.
3. CONSTRUCTOR — código + motor.json + pruebas + LEEME.
4. VERIFICADOR — venv y directorio temporal, instalar solo lo declarado,
   importar, correr pytest. Pega la salida real.
5. AUDITOR ×3 — lentes distintos (corrección / seguridad / ¿de verdad hace lo
   que dice?). Cada uno intenta ROMPERLO. Mayoría manda.
6. JUEZ — las 6 reglas. Si falla, regresa al Constructor con el motivo EXACTO.
   Máximo 3 reintentos; al cuarto para y pregúntame.
7. COMMITEADOR — solo si el Juez aprobó: rama, commit con evidencia, alta en el
   catálogo.

NO instales el motor en AURORA. La fábrica produce; instalar lo decido yo.
Si el motor toca un dominio nuevo, márcalo validacion_humana: pendiente.
```

---

## 8. Lo que falta decidir (Anuar)

1. **Nombre y ruta definitivos.** Propuesto: `C:\AURORITA_XP`, puerto 5001.
2. **Qué llaves lleva.** Propuesto: solo las de razonar (Groq / Ollama local).
   Ninguna de publicar. Confirmar.
3. **Primer motor de prueba.** Recomendado: uno de **taller**, un dominio que
   Anuar domina, para poder juzgar si de verdad quedó bien. Un motor de primaria
   como primer intento no se puede evaluar sin la escuela enfrente.
4. **Dónde vive la biblioteca de conocimiento** (el disco de 1 TB).
