import urllib.request, json, time, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass
BASE="http://127.0.0.1:8000"
def post(p,b):
    req=urllib.request.Request(BASE+p,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req,timeout=180).read().decode())
fichas=json.load(urllib.request.urlopen(BASE+"/api/vendedor/fichas",timeout=20))["equipos"]
# ATF primero (prioridad), luego MILENS; solo lo no COMPLETA
orden=[f for f in fichas if f["negocio"]=="ATF" and f["estado"]!="COMPLETA"] + \
      [f for f in fichas if f["negocio"]=="MILENS" and f["estado"]!="COMPLETA"]
rep=[]
for f in orden:
    try:
        r=post("/api/vendedor/investigar",{"producto":f["nombre"]})
        est=(r.get("ficha") or {}).get("estado_ficha") or r.get("status")
        rep.append(f"{f['negocio']:6} {f['nombre'][:32]:34} -> {est}")
    except Exception as e:
        rep.append(f"{f['negocio']:6} {f['nombre'][:32]:34} -> ERROR {str(e)[:40]}")
    open(r"C:\AURORA\REPORTES\reinvestigacion.txt","w",encoding="utf-8").write("\n".join(rep))
    time.sleep(2)
print("REINVESTIGACION COMPLETA:",len(rep),"fichas")
