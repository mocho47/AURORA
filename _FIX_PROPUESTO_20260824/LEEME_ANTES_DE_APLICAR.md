# FIX PROPUESTO — NO ESTÁ APLICADO

Esta carpeta contiene el fix de raíz **escrito pero NO integrado**, a petición
de Anuar (2026-08-24): *"el fix definitivo solo lo escribas sin integrarlo para
checarlo a detalle antes de aplicarlo a AURORA"*.

**AURORA hoy sigue corriendo exactamente igual que antes.** Nada de esta
carpeta está conectado, importado ni ejecutándose. Ningún archivo de AURORA fue
modificado para crear esto.

## Qué hay aquí

| Archivo | Reemplaza a | Qué causa de raíz cierra |
|---|---|---|
| `backup_aurora.py` | `SETUP/backup_aurora.py` | **E** — durabilidad de datos |
| `identidad_core_endurecido.py` | `AUTH/identidad_core.py` | **D** — frontera de seguridad |
| `consciencia_despacho.py` | *(solo el bloque de despacho de `CEREBRO/consciencia.py`)* | **B** — el candado que se secuestra |
| `gitignore_agregar.txt` | *(líneas a añadir a `.gitignore`)* | **D** |

## Cómo revisarlo

Cada archivo abre con un bloque `POR QUÉ ESTE ARCHIVO` que explica qué estaba
mal, qué cambia, y **qué decisión tuya falta** si aplica. Los tres son
independientes: se puede aplicar uno sin los otros.

## Lo que NO está escrito todavía

Las fases 1, 3, 4 y 5 del plan (`_CONTEXTO/PLAN_REPARACION_RAIZ_20260824.md`)
están **especificadas pero no escritas**. No se escribieron porque cada una
necesita una confirmación previa que no se puede asumir:

- **Fase 1 (números)**: hay que confirmar si `TALLER/generar_caja.py` está
  muerto de verdad antes de borrarlo.
- **Fase 4 (motores)**: hay que decidir si el chat ejecuta las clases de los
  motores o si los motores son solo prompts. Es una decisión de arquitectura,
  no una corrección.
- **Fase 5 (voz)**: hay que decidir cuál de los dos sistemas de voz es el
  bueno.

Decirlo así es parte del trabajo. Escribir código para las tres asumiendo la
respuesta sería exactamente el error que este plan existe para no repetir.
