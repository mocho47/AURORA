# -*- coding: utf-8 -*-
"""Radiografía REAL de Facebook (ATF) vía Graph API. Sin inventar:
trae página, publicaciones recientes con su interacción, e infiere mejor hora
a partir de TUS datos reales. Lo que la API no deje ver, lo dice honesto."""
import sys, json, urllib.request, urllib.parse
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def _env():
    e = {}
    for ln in Path(r"C:\AURORA\.env").read_text(encoding="utf-8").splitlines():
        if "=" in ln and not ln.strip().startswith("#"):
            k, _, v = ln.partition("="); e[k.strip()] = v.strip().strip('"')
    return e

def _g(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as ex:
        return {"error": str(ex)}

def radiografia():
    e = _env(); tok = e.get("FB_PAGE_TOKEN", ""); pid = e.get("FB_PAGE_ID", "")
    base = "https://graph.facebook.com/v18.0/"
    rep = {"generado": datetime.now().isoformat(timespec="seconds")}
    pg = _g(f"{base}{pid}?fields=name,fan_count,followers_count&access_token={tok}")
    rep["pagina"] = pg
    # publicaciones recientes con interacción real
    campos = "created_time,message,permalink_url,shares,likes.summary(true),comments.summary(true)"
    posts = _g(f"{base}{pid}/posts?fields={urllib.parse.quote(campos)}&limit=25&access_token={tok}")
    items, por_hora = [], defaultdict(lambda: {"posts": 0, "eng": 0})
    for p in posts.get("data", []):
        likes = (p.get("likes", {}).get("summary", {}) or {}).get("total_count", 0)
        coms = (p.get("comments", {}).get("summary", {}) or {}).get("total_count", 0)
        shares = (p.get("shares", {}) or {}).get("count", 0)
        eng = likes + coms + shares
        hora = None
        if p.get("created_time"):
            try:
                hora = datetime.fromisoformat(p["created_time"].replace("Z", "+00:00")).hour
                por_hora[hora]["posts"] += 1; por_hora[hora]["eng"] += eng
            except Exception:
                pass
        items.append({"fecha": p.get("created_time", "")[:16], "hora": hora, "likes": likes,
                      "comentarios": coms, "compartidos": shares, "interaccion": eng,
                      "texto": (p.get("message", "") or "")[:60], "url": p.get("permalink_url", "")})
    rep["total_publicaciones_analizadas"] = len(items)
    if items:
        rep["interaccion_total"] = sum(i["interaccion"] for i in items)
        rep["interaccion_promedio"] = round(rep["interaccion_total"] / len(items), 1)
        rep["top_publicacion"] = max(items, key=lambda i: i["interaccion"])
        mh = sorted(((h, d["eng"] / max(d["posts"], 1)) for h, d in por_hora.items()),
                    key=lambda x: x[1], reverse=True)[:3]
        rep["mejores_horas"] = [{"hora_utc": h, "interaccion_prom": round(v, 1)} for h, v in mh]
    # insights (puede requerir permiso adicional; si falla, honesto)
    ins = _g(f"{base}{pid}/insights?metric=page_impressions,page_post_engagements&period=days_28&access_token={tok}")
    rep["insights"] = ({d["name"]: (d.get("values", [{}])[-1].get("value")) for d in ins["data"]}
                       if ins.get("data") else {"nota": "Insights no disponibles con este permiso: " + str(ins.get('error', ''))[:120]})
    return rep

if __name__ == "__main__":
    r = radiografia()
    out = Path(r"C:\AURORA\REPORTES"); out.mkdir(exist_ok=True)
    f = out / f"radiografia_fb_{datetime.now():%Y%m%d_%H%M}.json"
    f.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    pg = r.get("pagina", {})
    print(f"PAGINA: {pg.get('name')} | seguidores: {pg.get('fan_count')}")
    print(f"Publicaciones analizadas: {r.get('total_publicaciones_analizadas')}")
    if r.get("total_publicaciones_analizadas"):
        print(f"Interaccion promedio: {r.get('interaccion_promedio')} | total: {r.get('interaccion_total')}")
        print(f"Mejores horas (UTC): {r.get('mejores_horas')}")
        tp = r.get("top_publicacion", {})
        print(f"TOP post ({tp.get('interaccion')} int): {tp.get('texto')}")
    print(f"Insights: {r.get('insights')}")
    print(f"Reporte: {f}")
