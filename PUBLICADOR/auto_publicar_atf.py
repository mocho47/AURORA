# -*- coding: utf-8 -*-
"""
AUTO-PUBLICADOR ATF — piloto automático diario.
Cada corrida: agarra el video de HOY (rotado, sin repetir), le pone un copy que
varia por dia, y lo publica REAL en la pagina de Facebook de ATF. Registra todo.
Lo dispara una tarea de Windows (AURORA_Publicar_ATF) a las 19:00 diario.
Publicar es accion real: este script SOLO se ejecuta porque Anuar lo autorizo
para ATF (contenido propio, cuenta propia).
"""
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

BASE = "http://127.0.0.1:5000"
LOG = Path(__file__).resolve().parent.parent / "LOGS" / "auto_publicaciones_atf.log"

# Copys profesionales que ROTAN por dia (mismo tono que los posts reales de ATF).
COPYS = [
    "Mejora tu visibilidad nocturna con nuestros kits de retrofit para faros. Manejar de noche vuelve a ser seguro. 🚗💡 Escríbenos por mensaje.",
    "Faros opacos o amarillentos? Los dejamos como nuevos. Más luz, más seguridad al volante. ✨ Pregunta por tu modelo.",
    "La iluminación correcta cambia todo: ves mejor, te ven mejor. Actualiza tus faros con nosotros. 🔦",
    "Instalación profesional de proyectores y LED de alta gama. Calidad que se nota en cada camino de noche. 🌙",
    "Tu seguridad empieza por ver bien. Retrofit de faros con garantía y trabajo limpio. 💪 Cotiza sin compromiso.",
    "Convierte tus faros en los de una unidad de agencia. Luz blanca, potente y bien enfocada. 🚘",
    "Maneja con confianza de noche. Kits de faros de alto rendimiento, instalados por expertos. ⭐",
    "Dale una nueva vida a tu auto: faros restaurados y mejorados que iluminan de verdad. 🔧",
    "Menos deslumbramiento, más visibilidad. Hacemos el retrofit correcto para tu modelo. 👀",
    "La diferencia entre ver el camino y adivinarlo son unos buenos faros. Actualízalos hoy. 🛣️",
    "Trabajo garantizado y atención personalizada. Actualiza Tus Faros: expertos en iluminación automotriz. ✅",
    "Cada noche cuenta. Invierte en faros que te cuidan a ti y a los tuyos. 🌟 Escríbenos.",
]

# Telefono oficial de ATF. Se anexa a CADA publicacion automatica.
TELEFONO_ATF = "3326148674"
CTA = f"\n\n📲 WhatsApp / Llamadas: {TELEFONO_ATF}\n#ActualizaTusFaros #Faros #Retrofit #GDL"


def _post(ruta, body, timeout=650):
    req = urllib.request.Request(
        BASE + ruta, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def _log(linea):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linea.rstrip() + "\n")


def _mover_a_publicados(ruta_video):
    """Mueve el video ya publicado a la carpeta PUBLICADOS (así se va vaciando la pila
    hasta agotar todos, como lo quiere Anuar). Reversible: mueve, no borra."""
    try:
        if not ruta_video:
            return "(sin ruta de video)"
        origen = Path(ruta_video)
        if not origen.is_file():
            return "(video ya no estaba en su sitio)"
        destino_dir = origen.parents[0] if origen.parent.name == "PUBLICADOS" else \
            (Path(r"C:\Users\Administrador\Videos") / "PUBLICADOS")
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / origen.name
        if destino.exists():
            destino = destino_dir / f"{origen.stem}_{origen.stat().st_mtime_ns}{origen.suffix}"
        origen.replace(destino)
        return f"| movido a PUBLICADOS: {destino.name}"
    except Exception as e:
        return f"| NO se pudo mover (no lo simulo): {str(e)[:120]}"


def main():
    hoy = date.today()
    copy = COPYS[hoy.toordinal() % len(COPYS)] + CTA  # rota por dia + telefono oficial
    marca = f"[{hoy.isoformat()}]"
    try:
        r = _post("/publicador/publicar-hoy",
                  {"red": "facebook", "descripcion": copy, "aprobar": True})
    except Exception as e:
        _log(f"{marca} ERROR de conexion: {e}")
        print("ERROR", e)
        return 1

    estado = r.get("status")
    if estado == "PUBLICADO":
        movido = _mover_a_publicados(r.get("video"))
        _log(f"{marca} PUBLICADO post_id={r.get('post_id')} video={r.get('video')} {movido}")
        print("PUBLICADO", r.get("post_id"))
        return 0
    if estado == "ya_publicado":
        _log(f"{marca} ya estaba publicado hoy, no repito.")
        print("YA_PUBLICADO")
        return 0
    _log(f"{marca} NO se publico: {json.dumps(r, ensure_ascii=False)[:300]}")
    print("NO_PUBLICADO", estado)
    return 1


if __name__ == "__main__":
    sys.exit(main())
