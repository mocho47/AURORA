# -*- coding: utf-8 -*-
"""
AURORA · MOTOR DE VIDEO — convertir la videoteca en material que se publica
===========================================================================

POR QUÉ EXISTE
--------------
Anuar tiene **296 videos (9.92 GB)** de trabajos reales del taller, grabados a lo
largo de años. Están parados en el disco sin producir nada.

Medido con ffprobe el 2026-08-03 sobre una muestra real:

    duración mediana        24 segundos     ← perfecta para Reels/TikTok
    21 de 25                 ≤ 60 s          ← no hay que cortarlos
    16 de 25                 horizontales    ← ~190 videos no se pueden publicar
    ~150                     en carpetas de duplicados

**El problema no es el contenido: es el formato.** Hay casi doscientos videos
listos que no se publican solo porque están acostados.

Esto los pone en 9:16 y los deja listos para subir. El publicador automático ya
existe y funciona; lo que le faltaba era material.

CÓMO SE PASA DE HORIZONTAL A VERTICAL
-------------------------------------
Dos formas, y la elección importa:

* **recorte** — se queda el centro y se tiran los lados. Sirve cuando lo
  importante está en medio (un grabado, una pieza en la cama del láser).
* **fondo difuminado** — el video completo al centro, y arriba y abajo el mismo
  video borroso rellenando. No se pierde nada de la imagen y es como se ve el
  contenido profesional en Reels. **Es el que se usa por defecto.**

Todo con FFmpeg, que ya está instalado (8.0.1 con libx264, aac y vp9). FFmpeg se
invoca como programa externo, así que su licencia GPL no afecta a AURORA.
"""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("aurora.video")

RAIZ = Path(__file__).resolve().parent.parent
VIDEOTECA = Path.home() / "Videos"
SALIDA = VIDEOTECA / "_LISTOS_PARA_PUBLICAR"

EXTENSIONES = (".mp4", ".mov", ".avi", ".mkv", ".webm")

# 1080x1920 es lo que piden TikTok, Reels y Shorts.
ANCHO_VERTICAL, ALTO_VERTICAL = 1080, 1920


def _ffmpeg_existe() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


_CODIFICADOR: Optional[str] = None


def _codificador_disponible() -> str:
    """Qué acelerador por hardware tiene esta PC. Se averigua una sola vez.

    No basta con que FFmpeg lo liste: hay que probar que de verdad codifica.
    Un `h264_amf` listado pero sin driver falla a medio trabajo, y eso sería
    peor que ir lento — perdería el video a la mitad.
    """
    global _CODIFICADOR
    if _CODIFICADOR is not None:
        return _CODIFICADOR
    _CODIFICADOR = "cpu"
    try:
        listados = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                                  capture_output=True, text=True, timeout=20).stdout
        for cod in ("h264_amf", "h264_nvenc", "h264_qsv"):
            if cod not in listados:
                continue
            # Prueba real: dos segundos de video de color a la basura.
            prueba = subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30:duration=2",
                 "-c:v", cod, "-f", "null", "-"],
                capture_output=True, text=True, timeout=60)
            if prueba.returncode == 0:
                _CODIFICADOR = cod
                logger.info(f"Acelerador de video: {cod}")
                break
    except Exception as e:
        logger.debug(f"No pude detectar acelerador: {e}")
    return _CODIFICADOR


def info_video(ruta: str | Path) -> Dict:
    """Ancho, alto, duración y peso reales. Nada estimado."""
    p = Path(ruta)
    if not p.exists():
        return {"status": "error", "mensaje": f"No existe: {p}"}
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", str(p)],
            capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
        v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
        if not v:
            return {"status": "error", "mensaje": "No tiene pista de video"}
        ancho, alto = int(v.get("width", 0)), int(v.get("height", 0))
        dur = float(d.get("format", {}).get("duration", 0))
        forma = ("vertical" if alto and ancho / alto < 0.9
                 else "cuadrado" if alto and ancho / alto < 1.2 else "horizontal")
        return {
            "status": "OK", "ancho": ancho, "alto": alto, "forma": forma,
            "duracion": round(dur, 1),
            "mb": round(p.stat().st_size / 1024**2, 1),
            "sirve_para_reel": dur <= 90,
            "ruta": str(p),
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)[:160]}


def a_vertical(ruta: str | Path, salida: str = "", modo: str = "fondo",
               segundos_max: int = 0) -> Dict:
    """Deja el video en 9:16, listo para TikTok, Reels y Shorts.

    modo="fondo"   el video completo al centro y el mismo video borroso de
                   relleno arriba y abajo. No se pierde nada de la imagen.
    modo="recorte" se queda el centro. Sirve cuando lo importante está en medio.

    segundos_max   recorta desde el inicio si el video es más largo. 0 = completo.
    """
    if not _ffmpeg_existe():
        return {"status": "error", "mensaje": "No encuentro FFmpeg en el sistema."}
    p = Path(ruta)
    inf = info_video(p)
    if inf.get("status") != "OK":
        return inf

    SALIDA.mkdir(parents=True, exist_ok=True)
    dst = Path(salida) if salida else SALIDA / f"{p.stem}_9x16.mp4"

    if modo == "recorte":
        filtro = (f"crop='min(iw,ih*9/16)':ih,"
                  f"scale={ANCHO_VERTICAL}:{ALTO_VERTICAL}:force_original_aspect_ratio=increase,"
                  f"crop={ANCHO_VERTICAL}:{ALTO_VERTICAL}")
    else:
        # El fondo es el mismo video ampliado y desenfocado: se ve profesional y
        # conserva la imagen completa al centro.
        #
        # EL TRUCO QUE LO HACE VIABLE: el desenfoque se calcula sobre una versión
        # CHICA (135x240) y luego se amplía. Difuminar a tamaño completo costaba
        # 238 s por video — medido el 2026-08-03 — y con 190 videos eran 12 horas.
        # Sobre una imagen 64 veces más chica cuesta una fracción, y al ampliarla
        # el resultado se ve igual: total, está borroso a propósito.
        chico_w, chico_h = ANCHO_VERTICAL // 8, ALTO_VERTICAL // 8
        filtro = (
            f"[0:v]scale={chico_w}:{chico_h}:force_original_aspect_ratio=increase,"
            f"crop={chico_w}:{chico_h},boxblur=6:2,"
            f"scale={ANCHO_VERTICAL}:{ALTO_VERTICAL}[fondo];"
            f"[0:v]scale={ANCHO_VERTICAL}:{ALTO_VERTICAL}:force_original_aspect_ratio=decrease[frente];"
            f"[fondo][frente]overlay=(W-w)/2:(H-h)/2"
        )

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if segundos_max > 0:
        cmd += ["-t", str(segundos_max)]
    cmd += ["-i", str(p)]
    cmd += ["-filter_complex" if modo != "recorte" else "-vf", filtro]

    # Se usa la TARJETA DE VIDEO si la hay. Medido el 2026-08-03 en la PC de
    # Anuar: 238 s por video con el CPU solo — 190 videos serían 12 horas, y su
    # máquina ya va al 99 % de memoria. Con la GPU baja a una fracción, y de
    # paso deja el procesador libre para que él siga trabajando en Corel.
    codificador = _codificador_disponible()
    if codificador == "h264_amf":            # AMD, que es lo que tiene
        cmd += ["-c:v", "h264_amf", "-quality", "speed", "-rc", "cqp", "-qp_i", "26", "-qp_p", "28"]
    elif codificador == "h264_nvenc":        # NVIDIA
        cmd += ["-c:v", "h264_nvenc", "-preset", "p1", "-cq", "26"]
    elif codificador == "h264_qsv":          # Intel
        cmd += ["-c:v", "h264_qsv", "-global_quality", "26"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]

    cmd += ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"status": "error", "mensaje": "Tardó más de 15 minutos y se canceló."}

    if r.returncode != 0 or not dst.exists():
        return {"status": "error", "mensaje": (r.stderr or "FFmpeg falló")[:200]}

    return {
        "status": "OK",
        "salida": str(dst),
        "mb": round(dst.stat().st_size / 1024**2, 1),
        "de": f"{inf['ancho']}x{inf['alto']} ({inf['forma']})",
        "a": f"{ANCHO_VERTICAL}x{ALTO_VERTICAL} (9:16)",
        "modo": modo,
    }


def miniatura(ruta: str | Path, segundo: float = 0, salida: str = "") -> Dict:
    """Saca un fotograma para usar de portada del post."""
    if not _ffmpeg_existe():
        return {"status": "error", "mensaje": "No encuentro FFmpeg."}
    p = Path(ruta)
    if not p.exists():
        return {"status": "error", "mensaje": f"No existe: {p}"}
    if segundo <= 0:
        inf = info_video(p)
        # Al segundo 1 casi siempre hay negro o una mano tapando: se toma a un
        # tercio del video, donde ya se ve el trabajo.
        segundo = max(1.0, inf.get("duracion", 6) / 3) if inf.get("status") == "OK" else 2.0
    SALIDA.mkdir(parents=True, exist_ok=True)
    dst = Path(salida) if salida else SALIDA / f"{p.stem}_portada.jpg"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(segundo), "-i", str(p), "-frames:v", "1",
           "-q:v", "2", str(dst)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"status": "error", "mensaje": "Tardó demasiado."}
    if r.returncode != 0 or not dst.exists():
        return {"status": "error", "mensaje": (r.stderr or "FFmpeg falló")[:200]}
    return {"status": "OK", "salida": str(dst),
            "kb": round(dst.stat().st_size / 1024, 1), "segundo": round(segundo, 1)}


def _huella(p: Path, kb: int = 512) -> str:
    """Huella del contenido, no del nombre. Dos copias con nombres distintos
    tienen la misma huella; eso es lo que hace que se detecten de verdad."""
    h = hashlib.md5()
    h.update(str(p.stat().st_size).encode())
    with open(p, "rb") as f:
        h.update(f.read(kb * 1024))
    return h.hexdigest()


def buscar_duplicados(carpeta: str | Path = "") -> Dict:
    """Encuentra videos repetidos por su CONTENIDO. Solo reporta: no borra nada.

    Borrar es decisión de Anuar, nunca automática — regla del proyecto.
    """
    raiz = Path(carpeta) if carpeta else VIDEOTECA
    if not raiz.exists():
        return {"status": "error", "mensaje": f"No existe la carpeta: {raiz}"}

    por_huella: Dict[str, List[Path]] = {}
    revisados = 0
    for p in raiz.rglob("*"):
        if p.suffix.lower() not in EXTENSIONES or not p.is_file():
            continue
        try:
            por_huella.setdefault(_huella(p), []).append(p)
            revisados += 1
        except OSError:
            continue

    grupos = [v for v in por_huella.values() if len(v) > 1]
    desperdiciado = sum(sum(q.stat().st_size for q in g[1:]) for g in grupos)
    return {
        "status": "OK",
        "revisados": revisados,
        "grupos_repetidos": len(grupos),
        "copias_de_mas": sum(len(g) - 1 for g in grupos),
        "gb_desperdiciados": round(desperdiciado / 1024**3, 2),
        "grupos": [
            {"conservar": str(g[0]), "repetidos": [str(q) for q in g[1:]],
             "mb": round(g[0].stat().st_size / 1024**2, 1)}
            for g in sorted(grupos, key=lambda g: -g[0].stat().st_size)[:30]
        ],
        "nota": "Solo se reporta. Borrar lo decide Anuar.",
    }


def listos_para_publicar(carpeta: str | Path = "", limite: int = 0) -> Dict:
    """Revisa la videoteca y dice cuáles ya sirven y cuáles hay que voltear."""
    raiz = Path(carpeta) if carpeta else VIDEOTECA
    if not raiz.exists():
        return {"status": "error", "mensaje": f"No existe la carpeta: {raiz}"}

    ya, voltear, largos, fallos = [], [], [], 0
    n = 0
    for p in raiz.rglob("*"):
        if p.suffix.lower() not in EXTENSIONES or not p.is_file():
            continue
        if limite and n >= limite:
            break
        n += 1
        i = info_video(p)
        if i.get("status") != "OK":
            fallos += 1
            continue
        if i["duracion"] > 90:
            largos.append(str(p))
        elif i["forma"] == "vertical":
            ya.append(str(p))
        else:
            voltear.append(str(p))

    return {
        "status": "OK",
        "revisados": n,
        "ya_sirven": len(ya),
        "hay_que_voltear": len(voltear),
        "muy_largos": len(largos),
        "no_se_pudieron_leer": fallos,
        "listos": ya[:20],
        "para_voltear": voltear[:20],
    }


def preparar_lote(cuantos: int = 10, modo: str = "fondo") -> Dict:
    """Voltea de golpe los primeros N videos horizontales y les saca portada.

    Pensado para lo que de verdad hace falta: tener material que publicar HOY,
    no revisar 296 archivos a mano.
    """
    revision = listos_para_publicar()
    if revision.get("status") != "OK":
        return revision
    pendientes = revision.get("para_voltear", [])
    if not pendientes:
        return {"status": "OK", "mensaje": "No hay videos horizontales pendientes.",
                "hechos": []}

    hechos, fallidos = [], []
    for ruta in pendientes[:cuantos]:
        r = a_vertical(ruta, modo=modo)
        if r.get("status") == "OK":
            port = miniatura(r["salida"])
            hechos.append({"video": r["salida"], "mb": r["mb"],
                           "portada": port.get("salida", "")})
        else:
            fallidos.append({"archivo": ruta, "porque": r.get("mensaje", "")})

    return {
        "status": "OK",
        "convertidos": len(hechos),
        "fallidos": len(fallidos),
        "carpeta": str(SALIDA),
        "hechos": hechos,
        "errores": fallidos,
        "faltan": max(0, len(pendientes) - cuantos),
    }
