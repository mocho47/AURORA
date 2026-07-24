import os, sys
from pathlib import Path
from collections import defaultdict
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

CATS = {
 "videos": (".mp4",".mov",".avi",".mkv",".wmv"),
 "fotos": (".jpg",".jpeg",".png",".heic",".webp",".bmp"),
 "dxf": (".dxf",), "pdf": (".pdf",), "zip": (".zip",".rar",".7z"),
 "programas": (".exe",".msi"), "corel": (".cdr",), "svg": (".svg",),
 "office": (".docx",".xlsx",".pptx",".doc",".xls"),
}
SKIP = ("\windows","\program files","\programdata","\appdata","$recycle","\node_modules",
        "\.git","\python3","\steamlibrary","\windows.old","\$winreagent")
roots = []
for letra in "CDEFG":
    r = f"{letra}:\\"
    if os.path.isdir(r): roots.append(r)

conteo = defaultdict(lambda: {"n":0,"mb":0.0,"dirs":defaultdict(int)})
for root in roots:
    for dp, dns, fns in os.walk(root):
        low = dp.lower()
        if any(s in low for s in SKIP):
            dns[:] = []; continue
        for fn in fns:
            ext = os.path.splitext(fn)[1].lower()
            for cat, exts in CATS.items():
                if ext in exts:
                    try: mb = os.path.getsize(os.path.join(dp,fn))/1048576
                    except: mb = 0
                    conteo[cat]["n"] += 1; conteo[cat]["mb"] += mb
                    conteo[cat]["dirs"][dp] += 1
                    break

out = ["INVENTARIO DE ARCHIVOS (discos: %s)" % ", ".join(roots), "="*50]
for cat in CATS:
    c = conteo[cat]
    out.append(f"\n[{cat.upper()}] {c['n']} archivos · {c['mb']/1024:.1f} GB")
    top = sorted(c["dirs"].items(), key=lambda x:x[1], reverse=True)[:6]
    for d,n in top: out.append(f"   {n:4d}  {d}")
Path(r"C:\AURORA\REPORTES").mkdir(exist_ok=True)
Path(r"C:\AURORA\REPORTES\inventario.txt").write_text("\n".join(out), encoding="utf-8")
print("INVENTARIO LISTO -> C:\AURORA\REPORTES\inventario.txt")
print("\n".join(out)[:1500])
