# 🛟 Rescate de la USB F: — 2026-08-08

Lo que se salvó de una memoria de 30 GB que iba a formatearse, después de que
un chkdsk la dejara con 6,264 pedazos sueltos.

**De 26 GB ocupados, esto es todo lo que valía.** El resto eran builds,
librerías públicas, logs, ejecutables viejos y 2.85 GB de fragmentos rotos.

---

## 🥇 `comandos/normalizador_comandos.py` — lo más valioso

**138 entradas** de cómo el reconocimiento de voz oye mal el español de Anuar,
más normalización de verbos.

```
"fase book", "fasebuk"   → facebook
"yutuf"                  → youtube
"guatsap", "guasap"      → whatsapp
"has tag", "hash tag"    → hashtag
"abrir/abri/abree/abré"  → abre
```

**Esto no se inventa desde un escritorio.** Solo sale de hablarle a la máquina
muchas veces y anotar cada vez que entendió mal. Trae además su vocabulario de
negocio: corte láser, sublimación, iluminación automotriz.

Es el pendiente **#55 (demo con comandos normalizados)**, ya resuelto por él
mismo hace meses. Cuando AURORA tenga voz, esto va en `_norm_txt()` de
`CEREBRO/consciencia.py`, que es el punto por donde pasa todo mensaje.

---

## 🔧 `instalacion/` — las dos piezas que faltaban para vender

| archivo | qué resuelve |
|---|---|
| `shortcut.py` | crea el acceso directo en el Escritorio con `winshell` + COM. 600 bytes que funcionan. |
| `configure_nexus.py` | asistente de configuración inicial |

Son los pendientes **#47** (asistente de configuración) y **#51**
(distribución: instalador en vez de instalar a mano por cliente).

El manual de NEXUS prometía un `install.ps1` que NO estaba en el respaldo —
pero `shortcut.py` es la parte que de verdad importaba.

---

## 🎙️ `voz/` — implementaciones reales, no maquetas

`voz_segura.py` (24.8 KB) y `voice.py` (24.1 KB) usan pyttsx3 y ffmpeg de
verdad. `nexus.py` es el esqueleto VOSK + sounddevice + pyttsx3.

El **modelo de voz** (57.5 MB) NO está aquí: pesa demasiado para un repositorio
de código. Está en `C:\AURORA.worktrees\MODELOS\vosk-es\` y está en
`.gitignore`. Es `vosk-model-small-es-0.42`, español, funciona sin internet.

---

## 🎬 `video/` — ffmpeg real

`subtitle_generator.py`, `video_processor.py` y `audio_manager.py` de
`ion_master_nexus`. Comprobado que llaman ffmpeg de verdad.

Subtítulos para los 296 videos que ya tiene: es de lo poco que sube el alcance
sin costar dinero.

---

## ⚠️ LO QUE NO SE RESCATÓ, Y POR QUÉ IMPORTA SABERLO

**Los cuatro publicadores de `ion_master_nexus/platforms/` son FALSOS.**
`facebook.py`, `instagram.py`, `tiktok.py`, `youtube.py` hacen esto:

```python
await asyncio.sleep(0.05)                        # duerme
post_id = hashlib.md5(...).hexdigest()[:16]      # inventa un ID
url = f"https://tiktok.com/@ionmaster/video/{post_id}"
return PostResult(success=True, metrics={"views": 0, "likes": 0})
```

Ninguno importa `requests`. Ninguno toca la red. **Duermen 50 ms, inventan una
URL y reportan éxito.** Las métricas están escritas a mano en cero.

Esto explica y confirma lo que ya estaba anotado: las funciones de
TikTok/YouTube/IG de Marketing_Digital_Pro **nunca funcionaron**. Es la misma
enfermedad en otra carpeta.

**Si algún día se toma código de ahí, se toma el pipeline de video — nunca los
publicadores.**

---

## 🪤 Dos trampas encontradas, para no repetirlas

1. **`skills/time.py`** se llamaba igual que un módulo de Python. Cualquier
   `import time` en esa carpeta agarraba ese archivo en vez del real. Rompe
   programas en silencio.
2. **`status.py` definía `run()`** mientras todas las demás skills definían
   `main()`. El despachador solo llamaba una de las dos.

Y la razón de fondo por la que ese NEXUS ya no arranca: su `.venv` apunta a
`C:\Users\anuar\...` —la cuenta que se perdió— y a `D:\`, que ya no existe.
**Un `.venv` no es portátil.** Para que AURORA se instale sola en la máquina de
un cliente hay que empaquetar un Python embebido, no copiar un entorno.
