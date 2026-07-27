# -*- coding: utf-8 -*-
"""
Corrige el telefono en los reels/videos YA publicados de ATF.
- Reemplaza numeros viejos (3329879109, 3323530146) por el correcto 3326148674.
- A los que no tienen telefono, les agrega una linea de contacto.
Guarda RESPALDO del texto original de cada reel editado (para revertir).
Modo:  python corregir_telefono_atf.py test   -> edita solo 1 (prueba)
        python corregir_telefono_atf.py full   -> edita todos
"""
import json, os, re, sys, time, urllib.request, urllib.parse
from pathlib import Path

TOKEN = ""
PAGE = ""
for ln in open(r"C:\AURORA.worktrees\.env", encoding="utf-8", errors="ignore"):
    if ln.startswith("FB_PAGE_TOKEN="):
        TOKEN = ln.split("=", 1)[1].strip()
    elif ln.startswith("FB_PAGE_ID="):
        PAGE = ln.split("=", 1)[1].strip()
CORRECTO = "3326148674"
VIEJOS = ["3329879109", "3323530146"]
LINEA_TEL = f"\n\n\U0001F4F2 WhatsApp / Llamadas: {CORRECTO}\n#ActualizaTusFaros #Faros #Retrofit #GDL"
SC = Path(r"C:\AURORA.worktrees\LOGS")
SC.mkdir(exist_ok=True)
RESPALDO = SC / "respaldo_descripciones_atf.jsonl"


def _sin(s):
    return re.sub(r"[ \-]", "", s or "")


def traer_videos():
    url = (f"https://graph.facebook.com/v23.0/{PAGE}/videos?"
           f"fields=id,created_time,description&limit=200&access_token={urllib.parse.quote(TOKEN)}")
    return json.load(urllib.request.urlopen(url, timeout=60)).get("data", [])


def nueva_desc(desc):
    """Devuelve (nuevo_texto, motivo) o (None, None) si no hay que tocar."""
    d = desc or ""
    limpio = _sin(d)
    for viejo in VIEJOS:
        if viejo in limpio:
            # reemplaza el viejo (con o sin espacios/guiones) por el correcto
            patron = re.compile(re.escape(viejo[:2]) + r"[ \-]?" + re.escape(viejo[2:6]) +
                                r"[ \-]?" + re.escape(viejo[6:]))
            nuevo = patron.sub(CORRECTO, d)
            if _sin(nuevo).find(viejo) >= 0:      # por si el formato no calzo, anexa
                nuevo = d + f"\n\U0001F4F2 Tel correcto: {CORRECTO}"
            return nuevo, f"reemplazo {viejo}"
    if CORRECTO not in limpio:
        return (d.rstrip() + LINEA_TEL), "agrega telefono"
    return None, None


def editar(vid, texto):
    data = urllib.parse.urlencode({"description": texto, "access_token": TOKEN}).encode()
    req = urllib.request.Request(f"https://graph.facebook.com/v23.0/{vid}",
                                 data=data, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=60))


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "test"
    vids = traer_videos()
    pendientes = []
    for v in vids:
        nuevo, motivo = nueva_desc(v.get("description"))
        if nuevo is not None:
            pendientes.append((v["id"], v.get("description") or "", nuevo, motivo))
    print(f"Reels que necesitan cambio: {len(pendientes)}")
    if modo == "test":
        pendientes = [next((p for p in pendientes if "reemplazo" in p[3]), pendientes[0])]
        print("MODO PRUEBA: edito solo 1 ->", pendientes[0][0], "|", pendientes[0][3])

    ok = err = 0
    with open(RESPALDO, "a", encoding="utf-8") as bkp:
        for vid, viejo, nuevo, motivo in pendientes:
            try:
                r = editar(vid, nuevo)
                if r.get("success") or r.get("id"):
                    bkp.write(json.dumps({"id": vid, "original": viejo}, ensure_ascii=False) + "\n")
                    ok += 1
                    print(f"  OK  {vid}  ({motivo})")
                else:
                    err += 1
                    print(f"  ERR {vid}  -> {json.dumps(r)[:120]}")
            except Exception as e:
                err += 1
                print(f"  ERR {vid}  -> {str(e)[:120]}")
            time.sleep(0.4)
    print(f"\nEditados OK: {ok} | Errores: {err} | Respaldo: {RESPALDO}")


if __name__ == "__main__":
    main()
