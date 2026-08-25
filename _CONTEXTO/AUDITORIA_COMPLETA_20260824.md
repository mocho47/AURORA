# Auditoría Completa de AURORA — Reporte Final
**Para: Anuar Milán | Fecha: 2026-08-24 | Repo: C:\AURORA.worktrees**
**Método: 7 auditores en paralelo (lenguaje, motores, seguridad, riesgo de datos, cotizadores, pruebas, documentación) + verificación adversarial de cada hallazgo contra el código real antes de reportarlo.**

---

## 1. Resumen Ejecutivo

Se confirmaron **38 hallazgos** tras verificación adversarial (cada uno leído contra el código real, no solo sospechado): **9 críticos, 8 altos, 12 medios, 7 bajos** (más 2 verificaciones positivas de bugs viejos que siguen arreglados). **Sí hay riesgo real hoy**, no es alarmismo: una API key de Groq y el hash del PIN de dueño están expuestos en texto plano dentro del repo; el backup diario lleva semanas fallando en silencio (0 copias reales de la memoria de AURORA); y dos motores activos de negocio (ATF) cotizan a clientes reales con precios inventados 4-6 veces por encima del catálogo verdadero. Ninguno de estos 9 críticos es teórico — todos tienen ruta de ejecución confirmada hacia un cliente real, un backup real, o una credencial real. La buena noticia: nada está roto de forma visible hoy (AURORA sigue funcionando), así que hay margen para arreglarlo en orden sin parar el negocio — pero el riesgo de perder dinero, perder la memoria del sistema, o filtrar credenciales es real y activo, no hipotético.

---

## 2. CRÍTICOS (9)

### 2.1 — `CEREBRO/consciencia.py:2010` — El verbo "abre" secuestra mensajes que no tienen nada que ver con abrir una página
Cualquier mensaje que empiece con "abre/ábreme/métete a/entra a/vete a" (sin mencionar Corel ni traer una ruta tipo `C:\`) se enruta a la fuerza al candado "abrir_navegador", saltándose TODOS los demás candados — incluida la agenda. Un mensaje real como "abre mi agenda de hoy" dispara el navegador en vez de la agenda, y AURORA responde algo absurdo tipo "Dime qué página abro". **Por qué cuesta**: es exactamente el tipo de respuesta que rompe la confianza en el sistema cuando lo usas a diario mezclando taller, código y agenda. **Recomendación**: hacer que el candado de familia "abrir_navegador" respete su propio disparador real (que sí exige un dominio o sitio conocido) antes de bloquear a los demás candados.

### 2.2 — `MOTORES/motor_negocios.py:22` y `MOTORES/motor_ventas.py:19` — Precios de ATF inventados y 4-6 veces inflados, activos en el chat con clientes
El prompt que AURORA usa para hablar de negocio con un cliente real dice "Aozoom X1 ($8k), X3 ($15k), X5 ($25k), X7 ($40k)". El catálogo real dice X1=$3,149, X3=$3,149, X5=$1,599, X7=$2,099 — y además el orden está invertido. Este mismo bug ya se corrigió en `motor_cotizador.py` el mes pasado, pero nunca se tocó en estos dos gemelos. **Recomendación**: borrar la tabla hardcodeada de ambos archivos y hacer que lean del mismo `CONFIG/catalogo_atf.json`.

### 2.3 — `_OBSOLETOS/AURORA_duplicado/.gitignore:95` — La API key de Groq sigue expuesta en texto plano en el repo, HOY
La misma llave ya revocada sigue viva y completa dentro de una carpeta duplicada que sigue rastreada por git en el commit actual. **Recomendación**: borrar `_OBSOLETOS/AURORA_duplicado/` completo del repo, y purgar el historial de git (BFG / git-filter-repo) — borrar el archivo en un commit nuevo no basta, la key sigue recuperable en commits viejos.

### 2.4 — `CONFIG/identidad.json:2` — El hash+salt de tu PIN de dueño está en el repo, y el algoritmo es débil
El PIN mínimo es de 4 caracteres, el hash es SHA-256 simple sin protección contra fuerza bruta, y el archivo está versionado en git. **Recomendación**: agregarlo a `.gitignore`, purgarlo del historial, cambiar el PIN a mínimo 8 caracteres, migrar el hash a PBKDF2/bcrypt.

### 2.5 — `SETUP/backup_aurora.py:9` — El backup diario lleva fallando en silencio desde que se creó
Apunta a `C:\AURORA`, que ya no existe (`C:\AURORA.worktrees` es la ruta real). Falla cada noche con ERROR_FILE_NOT_FOUND pero se ve "Ready" en el Programador de Tareas. **Recomendación**: corregir la ruta Y actualizar la lista de archivos a respaldar (falta `MEMORIA/aurora_memoria.db`, sobra `CONFIG/materiales.json` que ya no existe).

### 2.6 — `TALLER/indexar_dxf.py:41` — Los 665 diseños del catálogo se cotizan con la fórmula vieja ya rechazada
25 mm/s en vez de 20, precio ×3 sin material/diseño/instalación. Vivo en el chat cuando se cotiza por nombre sin dar ruta. **Recomendación**: usar `TALLER/formula_precios.py` también en esta rama.

### 2.7 — `CEREBRO/consciencia.py:4520` — El candado que evita negarle un servicio a un cliente de ATF no tiene ninguna prueba real
### 2.8 — `CEREBRO/consciencia.py:4040` — La cadena foto→DXF (bandera del negocio de láser) nunca se prueba con una conversión real
### 2.9 — `CEREBRO/consciencia.py:2432` — Ninguna de las 425 pruebas ejecuta el flujo real de un mensaje de chat/WhatsApp de punta a punta

---

## 3. ALTOS (8)

3.1 `consciencia.py:1993` — la fusión del 23-ago perdió los patrones de "búsqueda de tendencias" pese a decir que copió todo completo.
3.2 `consciencia.py:3128` — el chat solo usa el texto del prompt de cada motor, nunca su lógica real; `motor_pedidos` está registrado pero el archivo no existe.
3.3 `AUTH/identidad_core.py:42` — PIN de 4 dígitos, sin límite de intentos (rate limiting definido en config pero nunca conectado).
3.4 `auto_reparacion.py:44` — `bus_neuronal.py` no está en la lista de archivos núcleo protegidos.
3.5 `MEMORIA/aurora_memoria.db` — 1.4 MB de memoria real sin ningún backup funcionando (mismo origen que 2.5).
3.6 `produccion_piezas_grandes.py:35` — piñatas/piezas grandes cotizadas a 25 mm/s, escrito 8 días DESPUÉS de la corrección a 20.
3.7 `tests/` — ningún test levanta el servidor real ni prueba los 204 endpoints con una petición HTTP real.
3.8 `GEMINI.md:20` — documento de arranque desactualizado desde el 2-ago, dice "76 pruebas" cuando hay 425.

---

## 4. MEDIOS (12)

4.1 Cotizar láser sin medidas fuerza el candado equivocado · 4.2 Normalización de texto duplicada fuera de `_norm_txt` · 4.3 Búsqueda web fallida se trata como dato real en marketing (hoy desconectado) · 4.4 Filtro de comandos peligrosos es lista de palabras, evadible con cmdlets equivalentes · 4.5 `/motor/{id}/ejecutar` no exige PIN a diferencia de otros endpoints sensibles · 4.6 `generar_caja.py` es un gemelo muerto con fórmula incorrecta, sin usar pero presente · 4.7 Pruebas "de conexión" que solo buscan texto, no ejecutan el candado real (repetido ~33 veces) · 4.8 Prueba acepta "OK" para medidas absurdas (99999cm, 0cm) · 4.9 Pruebas de precio dependen de archivos personales fuera del repo, se saltan en silencio · 4.10 `CONFIG/operaciones.json` con velocidad vieja (15 mm/s), sin uso hoy · 4.11 Catálogo de material no se actualiza tras el primer copiado · 4.12 `_CONTEXTO/COBERTURA.md` desactualizado, marca como roto algo ya arreglado.

---

## 5. BAJOS (7) + verificaciones positivas

- Esta auditoría cubrió solo `MOTORES/`; faltan ORACLE, VENDEDOR, TALLER, SUBLIMACION, MEMORIA, VOZ, MARKETING, PUBLICADOR, INTEGRACIONES, LICENCIA, MERCADO, EDITOR.
- `CONFIG/contactos.json` invita a pegar teléfonos reales en un JSON rastreado por git (hoy solo datos de ejemplo).
- `fabrica_agentes.py` borra sin respaldo previo, a diferencia del resto del sistema (hoy desconectada).
- `cajas_boxes.py:56` tiene la constante vieja (25 mm/s) declarada pero sin uso.
- `motor_cotizador.py:34` usa un precio fijo de respaldo en vez de calcular con la fórmula.
- Puntero roto en `LEEME_PRIMERO.md` + un reporte de pruebas duplicado byte a byte.

**Verificaciones positivas**: el bug catastrófico viejo de auto-reparación (el LLM veía un pedazo del archivo pero su respuesta reemplazaba el archivo completo) sigue arreglado y con sus 4 candados activos, tanto en `auto_reparacion.py` como en el sistema gemelo de edición por chat.

---

## 6. Qué hacer primero

Si solo hay tiempo para lo mínimo: **rotar la API key de Groq** (ya revocada, falta purgar del repo) y **cambiar el PIN de dueño** — son los dos que exponen acceso real a alguien externo ahora mismo. Después, **arreglar el backup** porque cada día sin él es un día de riesgo de perder la memoria de AURORA sin remedio. Luego, **los precios de ATF** porque cada cotización real que salga con ese número inflado es dinero que se puede estar perdiendo hoy mismo con un cliente. El resto puede esperar sin que nada se caiga, pero no se debe olvidar — especialmente el hueco de pruebas, porque sin ellas cualquier arreglo futuro puede romper algo más sin que nadie se entere.
