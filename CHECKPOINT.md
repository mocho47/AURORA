# 📌 CHECKPOINT AURORA — retomar aquí (2026-07-11)

## ▶️ ARRANQUE / CONEXIÓN
- Prender: acceso escritorio, o `python run_aurora.py` en `C:\AURORA.worktrees`. Levanta en ~70–110s.
- En la MISMA PC: **http://127.0.0.1:5000/panel** (funciona en cualquier red).
- Desde otro aparato en la WiFi del taller: **http://192.168.1.38:5000/panel** (firewall 5000 ya abierto).
- Desde OTRA red (casa): falta **Tailscale** (acceso remoto) — pendiente.
- ⚠️ La PC del taller debe quedar PRENDIDA con AURORA corriendo. (Se apagó hoy por un reinicio cancelado — ya la reprendí.)

## ✅ CONSTRUIDO Y PROBADO ESTA SESIÓN
- **Fábrica de Motores** (`CEREBRO/fabrica_motores.py`): crea motores desde descripción, con doctrina de creación + arsenal (ezdxf/cv2/rembg/PIL/fitz/vtracer/ddgs/psutil/sqlite/Groq) + auto-crítica en fases + ligada a autoconocimiento (`CONFIG/motores_creados.json`). EXCLUSIVA dueño (endpoints /motor/fabricar|custom/* exigen PIN). Panel 🏭. Probada (Medidor DXF, MXN→USD).
- **Razonador Profundo** (`CEREBRO/razonador.py`): 70B (Groq) + autocrítica; **delegación automática en el chat** (consciencia `_es_pregunta_profunda`). Panel 🧠 + /razonar. Probado en vivo (motores_usados=['razonador_profundo']).
- **Cerebro LOCAL offline** (Ollama `llama3.2:3b` YA descargado): razonador y chat (_ejecutar/_fallback en consciencia) caen a local sin internet. LENTO (~2.5min en 8GB) pero funciona. ⚠️ El daemon Ollama debe estar corriendo (`ollama serve`).
- **Biblioteca semántica** (`BIBLIOTECA/biblioteca.py`): embeddings locales (Ollama nomic-embed-text) híbrido con FTS5. Código en su lugar; **falta**: `ollama pull nomic-embed-text` + correr `reindexar_semantica()` (no se completó por corte de sesión).
- **Cotizadores**: láser con desperdicio (bug de arcos corregido) + **Cotizar Prendas** (catálogo real 47+ productos con escalas 1/docena/mayoreo, unidades pieza/par/millar, +4% tarjeta). Cotización→Orden con costo/utilidad. Contabilidad mensual.
- **Álbum de catálogo** (`TALLER/album_catalogo.py` + /taller/album + /catalogo/album.html): 10/15 imágenes.
- **Espiral DXF +30% encastres 2.5mm**: `Descargas/dxf/espiral_fix_+30_encastre2.5.dxf`.
- Precios reales corregidos (fichas vendedor ya no elevadas).

## ⚠️ PARCIAL (agentes cortados por límite de sesión, code compila OK)
- **Vendedor IA (pitch)**: el agente iba a agregar endpoint `/vendedor/pitch` + panel — VERIFICAR si quedó (compila, pero no probado en vivo).
- **Biblioteca semántica**: código sí, reindexado NO.
- **Docs** (MANUAL/SIGUIENTE_SESION): no se actualizaron.

## 🔲 PENDIENTE PRÓXIMA SESIÓN (multiagente, tras reset)
1. **AUDITORÍA final con checklist**: duplicados (endpoints/JS), sueltos, sim (ya salió LIMPIO en sims). Correr sobre código estable.
2. **UI moderna / rediseño del panel** (estético, gráficos).
3. **VERSIÓN GENÉRICA** ("estructura libre de mis necesidades"): despersonalizar (ver plan del agente: vaciar `.env`, `CONFIG/*.json`, `*.db`; externalizar identidad ATF/Milens a `CONFIG/negocio.json`; excluir fábrica+MOTORES_CUSTOM de la genérica). Base en `C:\NEXUS` (patrón config) + pitch `AURORA_GENERICO.html`.
4. **WhatsApp que cotice solo** (con Anuar, no autónomo).
5. Cablear respaldo offline a la **Fábrica** (hoy solo online).
6. Datos de Anuar: colocación/planchado DTF, provisión de luz, costo Porta llavero.

## 🔒 SEGURIDAD / TRANSPARENCIA
- Activado por Claude (autorizado): firewall 5000, bind 0.0.0.0, Ollama daemon+modelo, doctrina/arsenal fábrica, delegación razonador.
- APAGADO a propósito: auto-postear redes, auto-WhatsApp a clientes, exposición a internet público. Fábrica exige PIN. Nada oculto.
- Se declinó (a propósito): construir IA "sin límites/sin seguridad".

## 🧠 NOTA
Idea acordada: heredar a AURORA la **lógica de creación** (Claude) + la **visión/oficio** (Anuar). Fábrica = donde se unen. Herramienta al servicio del humano, con código de honor.
