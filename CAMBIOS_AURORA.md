# Registro de cambios de AURORA

Registro en español simple, para que Anuar pueda saber qué cambió y por qué sin tener que leer código. Cada entrada tiene fecha, qué se hizo, y por qué — el código real queda en los commits de git (mensajes claros, uno por pieza).

---

## 2026-07-26/27 — Corrección de raíz del enrutador (consciencia.py + registro_herramientas.py)

**Por qué**: Anuar encontró esta noche que AURORA negaba capacidades reales, entraba en respuestas circulares, y no seguía sus propias reglas. Se investigó a fondo (3 auditorías reales en paralelo, código leído línea por línea, nada especulado) antes de tocar nada, y se corrigió todo junto — no parche por parche.

**Qué se encontró y se arregló:**

1. **El enrutador tenía 17 reglas apiladas con el tiempo**, sin orden real (una quedó numerada "2.535" pero insertada físicamente después de otra llamada "2.61"). Se convirtió en una lista ordenada por especificidad — agregar algo nuevo mañana es una línea, no cirugía.

2. **"Núcleo blindado" no protegía nada** — el archivo se escribía en disco ANTES de checar si era del núcleo (consciencia.py mismo, el propio cerebro). Ahora pide confirmación real ANTES de tocar un archivo del núcleo, no un aviso después del hecho.

3. **Palabras cortas se confundían con otras** — "hazme un **borra**dor" se interceptaba como orden de borrar archivos; "eso me con**mueve**" como orden de mover archivos; "la **instala**ción cuesta" como orden de instalar algo. Arreglado con coincidencia de palabra completa, no de fragmento.

4. **Mismo bug de Corel, pero en 329 funciones más**: el sistema que ejecuta herramientas reales fallaba al llamar cualquier función que fuera "async" desde un hilo de fondo — el error real quedaba disfrazado de "fallo genérico". Es el mismo tipo de bug que ya se había arreglado hoy en Corel, solo que aquí afectaba potencialmente a todo el catálogo.

5. **Una función que sí modifica archivos** (`diagnosticar_y_reparar_todo`) estaba clasificada como "solo lectura" — se hubiera ejecutado sin pedir confirmación. Corregido.

6. **WhatsApp real mandaba siempre un saludo genérico**, ignorando lo que Anuar pedía escribir — aunque el sistema SÍ decía "enviado de verdad" (el envío era real, el contenido no era el pedido). Corregido para usar el texto real.

7. **El "candado único de verdad"**: ahora CUALQUIER respuesta de AURORA, antes de llegar al chat, se revisa contra el catálogo real de herramientas. Si dice "no puedo hacer X" y sí existe una herramienta real para X, se corrige automáticamente — sin importar qué modelo de IA generó la respuesta ni si el modelo decidió ignorar las instrucciones.

8. **El "razonador profundo"** (para preguntas largas/complejas) antes corría primero y sin saber nada de lo que AURORA puede hacer — por eso mensajes largos se iban directo a una respuesta genérica. Ahora es el último recurso de verdad (después de intentar todo lo real) y recibe el contexto completo, incluida la Biblioteca de manuales.

9. Varios bugs menores de un pitch de venta que mostraba texto interno crudo en vez del pitch real, una búsqueda de memoria que no encontraba el tema real de la pregunta, y coincidencias de palabras que no calzaban entre lo que el candado reconocía y lo que buscaba adentro.

**Probado en vivo, no solo en teoría**: se reprodujeron los 3 mensajes exactos que fallaron esta noche y las 3 colisiones de palabras encontradas — los 6 casos ahora responden correctamente. Los comandos de Corel de hoy (gotero, planilla, exportar, etc.) siguen funcionando igual, sin romper nada.

**Archivos que cambiaron**: `CEREBRO/consciencia.py`, `CEREBRO/registro_herramientas.py`, `CEREBRO/equipos.py`.

**Explícitamente NO se hizo en esta corrección** (para no prometer de más): no se fusionaron los candados de dominio dentro del enrutador universal (son más confiables por separado, es un cambio de riesgo real para otra sesión); no se construyó ninguna capacidad nueva (eso es trabajo aparte, con su propia prueba real).
