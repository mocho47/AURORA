# PENDIENTES DE PROGRAMADOR — cierre del 2026-08-26

Esta hoja se escribió al cerrar la sesión del 26 de agosto. Sirve para dos
cosas: que Anuar sepa qué falta, y que la siguiente sesión arranque sin volver
a averiguar lo ya averiguado.

**Regla al leerla:** nada de aquí se da por hecho hasta correrlo. Lo que dice
VERIFICADO se probó en vivo ese día; lo que dice SIN VERIFICAR, no.

---

## LO QUE QUEDÓ FUNCIONANDO (verificado en vivo el 26-ago)

| Qué | Prueba real que se corrió |
|---|---|
| **574 frases verificadas · 36 candados** (eran 176 y 30) | `python CEREBRO/generar_comandos_verificados.py` — las 574 pasan por el enrutador real |
| **Piñatas de Alicia, proceso completo** | `pinata_alicia.jpg` a 89.5 cm → PDF 67.12×89.5 + silueta 703 KB (33 m, 27.5 min) + despiece de 22 piezas |
| **Corel → PDF** | Documento de prueba → PDF real de 385 KB en disco. Va a `Descargas\PDF` |
| **`cuando te diga X es Y`** | «sacame la piñata» no llegaba a nada → ahora llega a `calcular_pieza_grande` |
| **`aurora aprende`** | 4 datos y 1 regla extraídos de un texto pegado; nombra los módulos que sí aplican cada número |
| **Los 12 motores importan** | Los 11 de `MOTORES/` + `publicador_core`, cero rotos |

Commits: `ce87aa2` (verificado) y `4c95ac6` (sin verificar). Subidos a
`mocho47/AURORA`.

---

## PENDIENTES, POR LO QUE CUESTAN

### 1. La pregunta que dejó abierta el agente de motores — **lo más urgente**
Murió escribiendo: *"ahora la verificación crítica: ¿la cotización de ATF sigue
sumando 120% encima del precio de catálogo?"*. Iba tras un bug real y no
alcanzó a decir si lo encontró.

**Por qué es lo primero:** un precio inflado dicho enfrente de un cliente es el
bug más caro que ha tenido este proyecto (el cotizador llegó a decir $8,000 por
un X1 que cuesta $3,149).

**Qué hacer:** cotizar un X1 y comparar contra `CONFIG/catalogo_atf.json`. El
commit `4c95ac6` se revierte entero de un movimiento si salió mal.

### 2. Correr las pruebas completas contra `4c95ac6`
358 líneas nuevas y 196 borradas en 12 archivos, sin una sola prueba corrida.
`python -m pytest tests/ -q`. El 26-ago pasaban 486.

### 3. Instagram — el bloqueo tiene solución escrita, falta probarla
El código de publicación **siempre estuvo completo** (`PUBLICADOR/publicador_core.py`
líneas ~87-105: `POST /{ig_id}/media` y luego `/media_publish`). El único
bloqueo real: **Instagram exige una `image_url` pública y no acepta bytes**.

- Supabase **está muerto**: el host de `SUPABASE_URL` no resuelve. No perder
  tiempo ahí.
- El camino que sí tiene futuro: subir la foto a su **página de Facebook**
  (`FB_PAGE_TOKEN` sirve, publica de verdad a diario) y reusar la URL del CDN.
- El agente alcanzó a escribir `PUBLICADOR/hospedaje_imagen.py` y
  `PUBLICADOR/marca_agua.py`. **Ninguno se probó.**
- Cuenta viva y confirmada: `rauna_892`, id `17841477357180920`. Es su cuenta
  personal, no la de ATF; él ya lo sabe y lo aceptó: *"por el momento es lo que hay"*.

### 4. La prueba en rojo (1 de 487)
`PRUEBAS_VIVAS/auditoria_mentiras.py` líneas 101-103 tiene tres números
escritos a mano que se pusieron viejos: dice *635 herramientas* y *33 candados*
cuando hoy son **713 y 38**. El validador tiene razón; la prueba es la que está
mal.

**Arreglo de raíz:** derivarlos del conteo real, no corregir el número a mano —
o se vuelve a poner viejo el mes que entra. Es la misma enfermedad que este
proyecto lleva meses curando.

### 5. Las 713 herramientas del enrutador, sin una sola frase
Los 36 candados ya están cubiertos, pero el **enrutador universal** tiene 713
herramientas y **ninguna tiene frase probada**. Anuar no sabe que existen.

El agente que iba a eso murió en el minuto uno. Dejó dicho que llevaba *"dos
hallazgos estructurales"* y que iba a revisar *"qué se traga el candado
`negocio`"* — ese es el hilo por donde retomar.

### 6. Los módulos huérfanos
Hay módulos que funcionan y que **el chat no puede alcanzar**: existen, corren,
y no hay puerta. El agente que iba a inventariarlos no alcanzó a escribir nada.

Método que traía: para cada `.py` de `TALLER/ EDITOR/ MARKETING/ PUBLICADOR/
MOTORES/ CORE/`, ver si `consciencia.py` o `registro_herramientas.py` llegan; y
para cada huérfano útil, entregar el paquete de cableado (trigger + ejecutor +
posición en `_CANDADOS` + frases).

### 7. El canal de aprendizaje, sin prueba de regresión
`CEREBRO/aprende_del_usuario.py` **sí funciona** — hay evidencia real: el
26-ago a las 4:20 AM aprendió solo, de Anuar, que «genera 5esta piñata para
alocia a 89.5cm» significa lo mismo que «cotiza esa piñata para alicia».

Pero **no hay una prueba que falle si se rompe**. Falta
`tests/test_aprendizaje_vivo.py` probando el ciclo completo, no que el archivo
exista.

---

## LO QUE NO ES DE PROGRAMADOR (es de Anuar)

- **RAM: 0.68 GB libres de 7.2.** Ésa es la causa medida de que se traben
  Corel, Aspire, RDWorks y Silhouette — Windows usa el disco como memoria.
  Dell Inspiron 15 3535, 2 ranuras ocupadas con 2×4 GB DDR5-5500, aguanta 64.
  Un kit **2×8 GB DDR5-5600 SODIMM** (~$1,000–1,500) lo acaba. Gratis mientras
  tanto: cerrar Chrome antes de cortar (son 1.1 GB, más que Corel).
- **El plugin de RDWorks para Corel no se puede modificar** (DLLs compiladas,
  no macros `.gms`). **Y no hace falta:** RDWorks lee DXF nativo
  (`Dxf2Grp.dll`). El camino corto es AURORA → DXF → RDWorks, sin Corel de por
  medio ni los dos programas abiertos comiéndose la RAM.
- **Borrar `Descargas\pin aurora.txt`** cuando se lo sepa de memoria.
- **La purga del historial de git** sigue sin decidir. `CONFIG/identidad.json`,
  `usuarios.json` y `contactos.json` ya no se rastrean, pero **siguen en el
  historial**. `git filter-repo` es irreversible: no se corre sin su permiso.
- **El extractor de `aurora aprende` está listo para estrenarse** pegándole la
  lista de precios de un proveedor.

---

## IDEAS SUYAS ANOTADAS, SIN EMPEZAR

1. **Que aprenda de imágenes y PDFs** — *"incluso diagramas de carro, lo que
   sea"*. Hoy `aurora aprende` solo lee texto.
2. **`intuicion` + los números de Meta.** Su idea era que *"aprenda a empatizar
   con el algoritmo"*; lo que sí es real es que lo **mida**: la misma API con
   la que ya publica devuelve alcance, interacción y horarios. Con el histórico,
   el candado `intuicion` puede decir *"tus reels vienen cayendo 3 semanas, el
   formato se está quemando"*. Eso es anticipar de verdad, y sale de sus datos.
   Su frase: *"con la intuición que irá adquiriendo debería incluso anticipar
   al algoritmo"*.
3. **Nivel 4 — que cree la capacidad desde la descripción.** Es la Fábrica
   (`crear_capacidad`), que ya existe. Por regla suya, **la Fábrica no se usa
   sin su autorización expresa.**

---

## LOS DOCE PROCESOS COMPLETOS DE SU NEGOCIO

Estado al 26-ago. Es el mapa de lo que falta ensamblar.

| # | Proceso | Estado |
|---|---|---|
| 1 | Piñata: imagen + 1 medida → PDF + silueta + despiece | ✅ probado |
| 2 | Foto → sin fondo → vectoriza → DXF ligero → cotiza | piezas ✅, sin ensamblar |
| 3 | Cotizar → orden de trabajo → anticipo/saldo → alerta 12h | piezas ✅ |
| 4 | Adaptar diseño a otro material (encastres) | ✅ |
| 5 | Caja/cofre por medidas → DXF + cotización | ✅ |
| 6 | Print & Cut | piezas ✅ |
| 7 | Vinil de recorte por escalera | ✅ |
| 8 | Lona por metros → PDF al DPI correcto | piezas ✅ |
| 9 | Cotizar prendas/sublimación | ✅ |
| 10 | Corel → PDF a `Descargas\PDF` | ✅ probado |
| 11 | Campaña → publicar FB + IG con marca de agua | ❌ IG bloqueado |
| 12 | Lead → ficha vendedor → seguimiento | piezas ✅ |
