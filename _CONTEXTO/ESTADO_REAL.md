# 📊 ESTADO REAL DE AURORA
### Última actualización: 2026-07-30

> **Regla de este archivo:** aquí solo entra lo **verificado**, con evidencia.
> Nada de "debería funcionar". Si algo no se probó, va en la sección de
> no-verificado. **No re-verifiques lo que aquí ya dice verificado** — ese es
> exactamente el gasto que esta carpeta existe para evitar.

---

## ✅ Verificado y funcionando

| Qué | Evidencia |
|---|---|
| **63 pruebas de regresión** | `python -m pytest tests/ -q` → 63 passed en 46 s. Una prueba por bug real que de verdad ocurrió |
| **Candado anti-invención** | `CEREBRO/validador_honestidad.py` — 4/4 en vivo contra los inventos reales |
| **Fase 3 completa** | Las 20 carpetas del enrutador (~517 herramientas) revisadas comando por comando |
| **Navegación web natural** | 4/4 frases naturales con resultados reales (Amazon, proveedores de Guadalajara) |
| **Respaldo en GitHub** | `mocho47/AURORA` privado, al día, nada suelto |
| **Corel** | 8 comandos reales probados con Corel abierto (importar, extraer texto, escalar, exportar PDF 376 KB real, guardar copia 12.8 KB real, reparar conexión) |
| **Agenda** | Citas de hoy/mañana/próximas y creación real. No inventa cuando le faltan datos |
| **Cotizador** | Detecta el negocio solo: Milens (73 servicios) vs ATF (98 productos) |
| **Contactos** | Distingue familia de clientes; la intención de compra gana al tono (14/14) |
| **WhatsApp** | Green API instancia 7107622171, autorizada, envío real |
| **Multi-usuario** | Anuar y Rocío, ambos rol dueño, cada quien su PIN |
| **Panel** | 30 pestañas en 6 grupos, 163 endpoints, 0 crashes |
| **Offline** | Ollama local (llama3.2:3b) + SQLite. Aguanta sin WiFi; solo degradan web y publicar |

**Los dos manuales están al día:**
- `MANUALES/manual_comandos_aurora.md` — 679 líneas, **generado del código**
  (17 candados + 517 herramientas). Regenerar: `python CEREBRO/generar_manual.py`
- `MANUALES/COMANDOS_VERIFICADOS.md` — 147 líneas, **solo lo probado en vivo**

---

## ❌ No funciona (confirmado, con causa conocida)

| Qué | Por qué | Salida |
|---|---|---|
| **Exportar PNG/JPG desde Corel** | Incompatibilidad de pywin32, no del Corel de Anuar (el ejemplo oficial VBA sí corre dentro de Corel). 4 caminos intentados, los 4 fallaron | Usar PDF (funciona 100 %) o exportar a mano |
| **Caché `gen_py` de win32com corrupta** | Problema de entorno | Borrar `%TEMP%\gen_py` para que se regenere |
| **TikTok y YouTube** | Sin tokens propios | Pendiente de darlos de alta |
| **Marketplace de Facebook** | No tiene API pública | Usar Tienda/Catálogo |
| **Meta de Milens** | Faltan 4 variables en `.env` | Requiere un clic de Rocío en su PC |
| **Tareas de fondo largas** | Se cuelgan en `asyncio.to_thread` | Sin diagnosticar |

---

## ⚠️ Sabido pero sin arreglar

1. `vectoriza` / `vectorizar` no ejecuta directo como el resto de frases de su
   candado: pasa por el enrutador y pide confirmación aparte.
2. El enrutador prefiere `leer_archivo` sobre `abrir_archivo` cuando el usuario
   dice "ábrelo". Ya no es inseguro, pero sigue siendo la herramienta equivocada.
3. `generar_manual.py` no detecta candados con lógica compuesta (dos categorías
   de disparador a la vez, como `negocio` o `corel`). Hoy se avisa con nota a mano.
4. **5 módulos muertos en CORE** que el enrutador cree disponibles. Quitarlos es
   decisión de Anuar (regla: no restar funciones sin su visto bueno).
5. Fichas del vendedor: solo 4 de 29 están completas. La del LED H4 tiene una
   incoherencia real (el texto menciona H7).
6. Videoteca: 296 archivos = ~127 únicos (169 duplicados sin depurar).

---

## 🚫 Documentos que AURORA generó y son FALSOS

**No usarlos. Se conservan solo como evidencia de por qué existe el candado.**

- **"MANUAL MAESTRO DE COMANDOS"** — 6 de 8 comandos inventados
  (`AGENDA/agrega_usuario`, `CORE/evalua_expresion`… ninguno existe)
- **"Kit de configuración crítica"** — manda ejecutar `REINICIAR_NGROK.bat`,
  `OPTIMIZAR_PC.bat` y `NEXUS.bat`. Los tres inexistentes.

Los manuales buenos son los dos de `MANUALES/` listados arriba.

---

## 🧭 Decisiones tomadas (no volver a discutirlas)

| Decisión | Fecha |
|---|---|
| AURORA es una **consola agnóstica de dominio**. El producto vendible es la consola + un **paquete de dominio**, no verticales separados | 30 jul |
| La Fábrica **se copia, no se corta**. AURORA sigue intacta; Aurorita XP es una copia con otro nombre, solo para generar motores | 30 jul |
| El cuello de botella de la motorteca es la **verificación**, no el disco. Mil motores ≈ 50 MB | 30 jul |
| FORJA es un proyecto **independiente e inconcluso**. Fuera del alcance de AURORA | 29 jul |
| Evolución se separa a su propia carpeta junto con NEXUS Teens | pendiente de ejecutar |
| MercadoLibre **pausado a propósito**. No reactivar | — |

---

## 📌 Pendientes por orden de valor

1. **Demo de AURORA con comandos normalizados** — es lo único que puede traer dinero esta semana
2. **Contrato del motor** (`motor.json`) — sin él, separar la Fábrica es cosmético
3. Precios de los 7 servicios de mano de obra de ATF — **los dicta Anuar**
4. Asistente de configuración inicial por voz — la pieza que vuelve vendible a AURORA
5. Unificar Evolución v1 y v2, separarla a su carpeta
6. Decidir qué se hace con `Marketing_Digital_Pro` (nunca se lanzó; el código se
   puede recuperar del .exe empacado con PyInstaller)
7. Distribución: instalador local + actualización automática

---

## 🖥️ Datos técnicos que siempre se preguntan

```
Ruta       C:\AURORA.worktrees
Arranque   python run_aurora.py   (~90 s, 28 motores en bus)
Puerto     5000
Salud      http://127.0.0.1:5000/health   ← 127.0.0.1, NO localhost (IPv6 falla)
Rocío      http://192.168.1.38:5000       (firewall abierto)
Python     C:\Program Files\Python312\python.exe
Pruebas    python -m pytest tests/ -q
Manual     python CEREBRO/generar_manual.py
GitHub     mocho47/AURORA (privado)
Reinicio   scratchpad/reiniciar.ps1  (evita falsos positivos del sandbox)
```

**Teléfono oficial de ATF: 3326148674.** Los viejos (3329879109, 3323530146)
están erradicados de todo el sistema; si aparece alguno, es un error.
