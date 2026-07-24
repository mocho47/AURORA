# -*- coding: utf-8 -*-
"""AGENDADOR de AURORA — pipeline de CARPETAS + rotación de redes (supervisado).

Flujo de Anuar:
  0_ORIGINAL (su material) -> AURORA copia candidato + caption a 1_REVISION
  -> Anuar MUEVE lo bueno a 2_APROBADOS -> AURORA publica en su red/horario
  -> 3_PUBLICADOS ; el video ROTA a otra red el siguiente turno (FB -> TikTok -> IG)
Nada se publica sin que Anuar lo apruebe (moviéndolo a 2_APROBADOS).
Solo Facebook publica por API hoy; TikTok/IG quedan listos para subir manual o cuando
se conecten sus APIs (honesto, sin simular).
"""
from __future__ import annotations
import json, shutil
from pathlib import Path
from datetime import datetime

BASE = Path(r"C:\AURORA\CONTENIDO")
REVISION = BASE / "1_REVISION"
APROBADOS = BASE / "2_APROBADOS"
PUBLICADOS = BASE / "3_PUBLICADOS"
REGISTRO = Path(r"C:\AURORA\CONFIG\contenido_registro.json")

VIDEOS_SRC = Path(r"C:\Users\Administrador\Videos")
EXCLUIR = ("familiar", "familliar", "captures", "almacenamiento de google", "\\publicados\\")
REDES_ROTACION = ["facebook", "tiktok", "instagram"]   # orden de rotación

HOOKS = [
    "🔦 ¿Manejas de noche con faros opacos? Mira este antes y después. Cotiza por WhatsApp.",
    "Faros como nuevos en una sola sesión. ¿Tu auto lo necesita? Escríbenos.",
    "La diferencia se nota desde 200 metros. Retrofit de iluminación ATF.",
    "Deja de manejar a ciegas de noche. Te dejamos los faros perfectos.",
    "De amarillo opaco a blanco intenso. Pregúntanos precio por WhatsApp.",
]

for _d in (REVISION, APROBADOS, PUBLICADOS):
    _d.mkdir(parents=True, exist_ok=True)


def _reg() -> dict:
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_reg(r: dict) -> None:
    REGISTRO.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


def _fuente() -> list:
    vids = []
    for p in VIDEOS_SRC.rglob("*.mp4"):
        low = str(p).lower()
        if p.stem.strip() and not any(x in low for x in EXCLUIR):
            vids.append(p)
    return sorted(vids, key=lambda p: str(p))


def _uname(src: Path) -> str:
    """Nombre único por carpeta para evitar colisiones (mismos nombres en distintas carpetas)."""
    carpeta = src.parent.name.replace(" ", "_")
    return f"{carpeta}__{src.name}"


def _siguiente_red(redes_usadas: list):
    for r in REDES_ROTACION:
        if r not in redes_usadas:
            return r
    return None  # ya rotó por todas


def preparar_revision(cantidad: int = 10) -> dict:
    """Copia candidatos de ORIGINAL a 1_REVISION con caption + red objetivo (rotación)."""
    reg = _reg()
    en_rev = {p.name for p in REVISION.glob("*.mp4")} | {p.name for p in APROBADOS.glob("*.mp4")}
    preparados = []
    i = 0
    for src in _fuente():
        if len(preparados) >= cantidad:
            break
        name = _uname(src)
        if name in en_rev:
            continue
        info = reg.get(name, {"origen": str(src), "redes": []})
        target = _siguiente_red(info.get("redes", []))
        if not target:
            continue  # ya pasó por todas las redes
        dst = REVISION / name
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            continue
        cap = HOOKS[i % len(HOOKS)]; i += 1
        (REVISION / (dst.stem + ".txt")).write_text(f"[RED: {target}]\n{cap}", encoding="utf-8")
        info.update({"origen": str(src), "estado": "en_revision", "target": target,
                     "caption": cap, "preparado": datetime.now().isoformat(timespec="minutes")})
        reg[name] = info
        preparados.append({"video": name, "red_objetivo": target, "caption": cap})
    _save_reg(reg)
    return {"status": "OK", "preparados": len(preparados), "items": preparados,
            "nota": "Revisa en 1_REVISION; mueve los buenos a 2_APROBADOS."}


def estado_pipeline() -> dict:
    def cuenta(d): return len(list(d.glob("*.mp4")))
    reg = _reg()
    rotacion = {}
    for v in reg.values():
        k = len(v.get("redes", []))
        rotacion[k] = rotacion.get(k, 0) + 1
    return {"status": "OK",
            "en_revision": cuenta(REVISION), "aprobados": cuenta(APROBADOS),
            "publicados": cuenta(PUBLICADOS), "fuente_total": len(_fuente()),
            "registrados": len(reg)}


def publicar_aprobados(publicar_fn, max_por_corrida: int = 1) -> dict:
    """Publica lo que Anuar movió a 2_APROBADOS. Solo Facebook por API; otras -> manual.
    Mueve a 3_PUBLICADOS y registra la red (para la rotación)."""
    reg = _reg(); hechos, pendientes_manual, errores = [], [], []
    for vid in sorted(APROBADOS.glob("*.mp4")):
        if len(hechos) + len(pendientes_manual) >= max_por_corrida:
            break
        name = vid.name
        info = reg.get(name, {"redes": []})
        # caption + red del sidecar si existe
        side = APROBADOS / (vid.stem + ".txt")
        target = info.get("target", "facebook")
        caption = info.get("caption", HOOKS[0])
        if side.exists():
            txt = side.read_text(encoding="utf-8")
            if txt.startswith("[RED:"):
                target = txt.split("]")[0].replace("[RED:", "").strip() or target
                caption = txt.split("]", 1)[1].strip() or caption
        if target == "facebook":
            r = publicar_fn(str(vid), caption)
            if r.get("status") == "PUBLICADO":
                info.setdefault("redes", []).append("facebook")
                info["estado"] = "publicado"; info["post_id"] = r.get("post_id", "")
                _mover(vid, side); hechos.append({"video": name, "red": "facebook", "post_id": info["post_id"]})
            else:
                errores.append({"video": name, "error": r.get("detalle", "")[:160]})
        else:
            # TikTok/IG: sin API -> queda registrado como pendiente manual, NO se simula
            info.setdefault("redes", []).append(target)
            info["estado"] = f"pendiente_manual_{target}"
            _mover(vid, side); pendientes_manual.append({"video": name, "red": target})
        reg[name] = info
    _save_reg(reg)
    return {"status": "OK", "publicados_fb": hechos, "pendientes_manual": pendientes_manual,
            "errores": errores,
            "nota": "FB se publicó real. TikTok/IG quedaron en 3_PUBLICADOS para subir manual (sin API aún)."}


def _mover(vid: Path, side: Path):
    try:
        shutil.move(str(vid), str(PUBLICADOS / vid.name))
        if side.exists():
            shutil.move(str(side), str(PUBLICADOS / side.name))
    except Exception:
        pass
