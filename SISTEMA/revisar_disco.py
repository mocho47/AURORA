# -*- coding: utf-8 -*-
"""AURORA · Revisa un disco o memoria antes de formatearla, y rescata los .CHK

Anuar lo pidió el 2026-08-08, con una USB de 30 GB que acababa de salir de un
chkdsk: *"a ver qué sirve para formatearla, chécala toda"*.

POR QUÉ ESTO ES RECURRENTE Y NO UN FAVOR DE UNA VEZ: sus memorias se corrompen
seguido, y siempre por lo mismo —FAT32 no lleva bitácora, y si se desconecta a
media escritura la tabla queda partida—. Ya está documentado que así se dañó el
disco de la oficina. Cada vez que pasa, la pregunta es la misma: *¿qué me
llevo antes de formatear?*

QUÉ HACE:
  • Inventario real: qué carpetas pesan, cuántos archivos y de qué tipo
  • Separa LO QUE VALE (diseños, documentos, fotos) de lo desechable
    (instaladores, temporales, cachés) — porque un instalador se vuelve a
    bajar y un DXF suyo no
  • Identifica los FILE####.CHK que deja chkdsk: cada formato tiene una firma
    en sus primeros bytes, así que se sabe cuál era DXF, PDF, JPG o ZIP de
    verdad, y cuál es basura

NO BORRA NADA, NO FORMATEA NADA. Solo lee y reporta. Lo que se tira lo decide
Anuar, siempre.

Correr:
    python SISTEMA/revisar_disco.py F:
    python SISTEMA/revisar_disco.py F: --rescatar     # copia los .CHK buenos
"""
from __future__ import annotations
import collections
import io
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Lo que de verdad duele perder: es su trabajo, no se vuelve a bajar.
VALE = {
    "diseño": (".dxf", ".cdr", ".ai", ".eps", ".svg", ".plt", ".stl", ".dwg",
               ".studio3", ".rld", ".nc", ".gcode"),
    "documento": (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                  ".txt", ".csv", ".odt"),
    "imagen": (".jpg", ".jpeg", ".png", ".psd", ".tif", ".tiff", ".webp",
               ".bmp", ".heic"),
    "video": (".mp4", ".mov", ".avi", ".mkv", ".webm"),
    "código": (".py", ".js", ".html", ".json", ".sql", ".php", ".bat", ".ps1"),
}
# Lo desechable: pesa mucho y se recupera bajándolo otra vez.
DESECHABLE = (".exe", ".msi", ".iso", ".cab", ".dll", ".tmp", ".log", ".bak",
              ".chk", ".dmp", ".crdownload", ".part")

# La firma de los primeros bytes. Es como se sabe qué era un .CHK sin nombre.
FIRMAS = (
    (b"%PDF", ".pdf"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF8", ".gif"),
    (b"PK\x03\x04", ".zip"),          # también docx/xlsx/studio3
    (b"Rar!\x1a\x07", ".rar"),
    (b"7z\xbc\xaf\x27\x1c", ".7z"),
    (b"\x1f\x8b", ".gz"),
    (b"RIFF", ".riff"),               # wav / avi / webp
    (b"\x00\x00\x00\x18ftyp", ".mp4"),
    (b"\x00\x00\x00\x20ftyp", ".mp4"),
    (b"ID3", ".mp3"),
    (b"\xd0\xcf\x11\xe0", ".doc"),    # Office viejo: doc/xls/ppt
    (b"SQLite format 3", ".db"),
    (b"MZ", ".exe"),
    (b"\x8aMNG", ".mng"),
    (b"II*\x00", ".tif"),
    (b"MM\x00*", ".tif"),
    (b"8BPS", ".psd"),
    (b"{\\rtf", ".rtf"),
    (b"CDR", ".cdr"),
)
# Los de texto no tienen firma binaria: se buscan por lo que dicen adentro.
TEXTO = (
    ("SECTION", "ENTITIES", ".dxf"),
    ("<svg", "", ".svg"),
    ("<?xml", "", ".xml"),
    ("<html", "", ".html"),
    ("%!PS", "", ".eps"),
)


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _mb(n: float) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024**3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024**2:.1f} MB"
    return f"{n / 1024:.0f} KB"


def _categoria(ext: str) -> str:
    for cat, exts in VALE.items():
        if ext in exts:
            return cat
    if ext in DESECHABLE:
        return "desechable"
    return "otro"


def _tipo_real(ruta: Path) -> str:
    """Qué es de verdad este archivo, leyendo sus primeros bytes."""
    try:
        with open(ruta, "rb") as f:
            cab = f.read(2048)
    except Exception:
        return ""
    if not cab:
        return ".vacio"
    for firma, ext in FIRMAS:
        if cab.startswith(firma):
            return ext
    try:
        txt = cab.decode("utf-8", errors="ignore")[:800]
    except Exception:
        txt = ""
    for a, b, ext in TEXTO:
        if a in txt and (not b or b in txt):
            return ext
    # ¿es texto legible aunque no se reconozca el formato?
    legibles = sum(1 for c in cab if 32 <= c < 127 or c in (9, 10, 13))
    if legibles > len(cab) * 0.9:
        return ".txt"
    return ""


def revisar(unidad: str) -> dict:
    """Camina el disco completo y devuelve qué hay, sin tocar nada."""
    base = Path(unidad)
    if not base.exists():
        return {"status": "NO_EXISTE", "detalle": str(base)}

    por_ext = collections.Counter()
    peso_ext = collections.Counter()
    por_cat = collections.Counter()
    peso_cat = collections.Counter()
    carpetas = collections.Counter()
    grandes = []
    chks = []
    errores = 0

    for dirpath, _dirnames, filenames in os.walk(base, onerror=lambda e: None):
        d = Path(dirpath)
        try:
            top = d.relative_to(base).parts[0] if d != base else "(raíz)"
        except Exception:
            top = "(raíz)"
        for nombre in filenames:
            p = d / nombre
            try:
                tam = p.stat().st_size
            except Exception:
                errores += 1
                continue
            ext = p.suffix.lower()
            cat = _categoria(ext)
            por_ext[ext] += 1
            peso_ext[ext] += tam
            por_cat[cat] += 1
            peso_cat[cat] += tam
            carpetas[top] += tam
            if tam > 50 * 1024 ** 2:
                grandes.append((tam, str(p)))
            if ext == ".chk":
                chks.append(p)

    grandes.sort(reverse=True)
    return {"status": "OK", "unidad": str(base), "por_ext": por_ext,
            "peso_ext": peso_ext, "por_cat": por_cat, "peso_cat": peso_cat,
            "carpetas": carpetas, "grandes": grandes[:25], "chks": chks,
            "errores": errores}


def identificar_chks(chks: list, limite: int = 0) -> dict:
    """Qué eran de verdad los FILE####.CHK que dejó chkdsk."""
    tipos = collections.Counter()
    peso = collections.Counter()
    ejemplos = collections.defaultdict(list)
    for i, p in enumerate(chks):
        if limite and i >= limite:
            break
        t = _tipo_real(p) or ".basura"
        try:
            tam = p.stat().st_size
        except Exception:
            tam = 0
        tipos[t] += 1
        peso[t] += tam
        if len(ejemplos[t]) < 3:
            ejemplos[t].append((str(p), tam))
    return {"tipos": tipos, "peso": peso, "ejemplos": dict(ejemplos)}


def rescatar_chks(chks: list, destino: Path,
                  solo: tuple = ()) -> dict:
    """Copia los .CHK que SÍ son algo, ya con su extensión correcta.

    Se COPIA, nunca se mueve: el original se queda donde está hasta que Anuar
    decida formatear.
    """
    import shutil
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    copiados = collections.Counter()
    for p in chks:
        t = _tipo_real(p)
        if not t or t in (".basura", ".vacio", ".exe"):
            continue
        if solo and t not in solo:
            continue
        carpeta = destino / t.lstrip(".")
        carpeta.mkdir(exist_ok=True)
        try:
            shutil.copy2(p, carpeta / (p.stem + t))
            copiados[t] += 1
        except Exception:
            continue
    return {"status": "OK", "destino": str(destino),
            "copiados": dict(copiados), "total": sum(copiados.values())}


VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp", ".m4v")


def _huella(ruta: Path, tam: int) -> str:
    """Identifica un archivo grande sin leerlo entero.

    Se toman el tamaño y tres mordidas —principio, medio y final—. Para dos
    videos, que sean idénticos en esos tres puntos Y en el tamaño exacto es
    prueba suficiente; leer 5 GB completos desde una memoria dañada tardaría
    una hora y no diría nada nuevo.
    """
    import hashlib
    h = hashlib.sha1(str(tam).encode())
    try:
        with open(ruta, "rb") as f:
            h.update(f.read(262144))
            if tam > 786432:
                f.seek(tam // 2)
                h.update(f.read(262144))
                f.seek(max(0, tam - 262144))
                h.update(f.read(262144))
    except Exception:
        return ""
    return h.hexdigest()


def inventario_videos(origen: str) -> dict:
    """Todos los videos de un disco: los sueltos y los que van dentro de zips.

    De los que están dentro de un zip se usa el CRC que el propio zip ya trae
    en su índice: no hay que descomprimir nada para saber si es el mismo.
    """
    import zipfile
    base = Path(origen)
    sueltos, en_zip, zips_rotos = [], [], []

    for dp, _dn, fn in os.walk(base, onerror=lambda e: None):
        if "FOUND.000" in dp:
            continue
        for n in fn:
            p = Path(dp) / n
            ext = p.suffix.lower()
            try:
                tam = p.stat().st_size
            except Exception:
                continue
            if ext in VIDEO_EXT:
                sueltos.append({"ruta": p, "nombre": n, "tam": tam})
            elif ext == ".zip":
                try:
                    z = zipfile.ZipFile(p)
                    for i in z.infolist():
                        if Path(i.filename).suffix.lower() in VIDEO_EXT:
                            en_zip.append({"zip": p, "interno": i.filename,
                                           "nombre": Path(i.filename).name,
                                           "tam": i.file_size, "crc": i.CRC})
                except Exception as e:
                    zips_rotos.append((str(p), type(e).__name__))
    return {"sueltos": sueltos, "en_zip": en_zip, "zips_rotos": zips_rotos}


def consolidar_videos(origen: str, destino: str,
                      solo_plan: bool = True,
                      comparar_contra: str = "") -> dict:
    """Copia a `destino` los videos que de verdad faltan, sin repetir ninguno.

    TRES FILTROS, EN ESTE ORDEN, DEL MÁS BARATO AL MÁS CARO:
      1. contra lo que ya hay en destino, por nombre y tamaño
      2. entre los del propio origen, por huella real de contenido
      3. los de dentro de los zips, por su CRC y tamaño

    Con `solo_plan=True` NO COPIA NADA: dice qué haría. Mover gigas sin haber
    visto la cuenta primero es como cortar la hoja sin medir.
    """
    import zipfile
    dest = Path(destino)
    inv = inventario_videos(origen)

    # 1 · lo que YA TIENE, para no traérselo dos veces.
    # OJO: se compara contra su videoteca completa, no contra la carpeta nueva
    # a la que se va a copiar —que está vacía y no descartaría nada—. Es el
    # error que casi le duplica 4.89 GB (2026-08-08).
    revisar_en = Path(comparar_contra) if comparar_contra else dest
    ya = {}
    for dp, _dn, fn in os.walk(revisar_en, onerror=lambda e: None):
        for n in fn:
            if Path(n).suffix.lower() not in VIDEO_EXT:
                continue
            p = Path(dp) / n
            try:
                ya[(n.lower(), p.stat().st_size)] = p
            except Exception:
                continue

    # 2 · los sueltos, por huella de contenido
    vistos, nuevos_sueltos, repetidos = {}, [], 0
    for v in inv["sueltos"]:
        if (v["nombre"].lower(), v["tam"]) in ya:
            repetidos += 1
            continue
        hh = _huella(v["ruta"], v["tam"])
        if not hh or hh in vistos:
            repetidos += 1
            continue
        vistos[hh] = v["ruta"]
        nuevos_sueltos.append(v)

    # 3 · los de dentro de los zips, por CRC + tamaño
    crc_vistos, nuevos_zip = set(), []
    tam_sueltos = {(v["nombre"].lower(), v["tam"]) for v in inv["sueltos"]}
    for v in inv["en_zip"]:
        clave = (v["crc"], v["tam"])
        if clave in crc_vistos:
            repetidos += 1
            continue
        if (v["nombre"].lower(), v["tam"]) in ya or \
           (v["nombre"].lower(), v["tam"]) in tam_sueltos:
            repetidos += 1
            continue
        crc_vistos.add(clave)
        nuevos_zip.append(v)

    peso = sum(v["tam"] for v in nuevos_sueltos) + \
        sum(v["tam"] for v in nuevos_zip)
    plan = {"status": "PLAN", "nuevos_sueltos": len(nuevos_sueltos),
            "nuevos_zip": len(nuevos_zip), "repetidos": repetidos,
            "peso": peso, "zips_rotos": inv["zips_rotos"],
            "total_origen": len(inv["sueltos"]) + len(inv["en_zip"]),
            "ya_tenia": len(ya), "destino": str(dest)}
    if solo_plan:
        return plan

    # ── copiar de verdad
    import shutil
    dest.mkdir(parents=True, exist_ok=True)
    copiados, fallos = 0, []
    for v in nuevos_sueltos:
        d = dest / v["nombre"]
        n = 2
        while d.exists():
            d = dest / f"{Path(v['nombre']).stem}__{n}{Path(v['nombre']).suffix}"
            n += 1
        try:
            shutil.copy2(v["ruta"], d)
            copiados += 1
        except Exception as e:
            fallos.append((str(v["ruta"]), type(e).__name__))
    for v in nuevos_zip:
        d = dest / v["nombre"]
        n = 2
        while d.exists():
            d = dest / f"{Path(v['nombre']).stem}__{n}{Path(v['nombre']).suffix}"
            n += 1
        try:
            with zipfile.ZipFile(v["zip"]) as z, z.open(v["interno"]) as f, \
                    open(d, "wb") as g:
                shutil.copyfileobj(f, g, 1024 * 1024)
            copiados += 1
        except Exception as e:
            fallos.append((f"{v['zip']}::{v['interno']}", type(e).__name__))
    plan.update({"status": "OK", "copiados": copiados, "fallos": fallos})
    return plan


def _texto_videos(r: dict) -> str:
    s = [f"🎬 **Videos** — {r['total_origen']} encontrados en el origen",
         f"   en el destino ya había **{r['ya_tenia']}**",
         f"   repetidos que NO se traen: **{r['repetidos']}**",
         f"   **nuevos: {r['nuevos_sueltos']} sueltos + {r['nuevos_zip']} "
         f"dentro de zips** = {_mb(r['peso'])}"]
    if r["zips_rotos"]:
        s.append("\n   ⚠️ Zips que no abren (su contenido se perdió):")
        for z, err in r["zips_rotos"]:
            s.append(f"      {z}  ({err})")
    if r.get("status") == "OK":
        s.append(f"\n✅ **{r['copiados']} copiados** a {r['destino']}")
        if r["fallos"]:
            s.append(f"   ⚠️ {len(r['fallos'])} no se pudieron leer:")
            for f, e in r["fallos"][:10]:
                s.append(f"      {f}  ({e})")
    else:
        s.append(f"\n   _Esto es el plan. Nada se ha copiado todavía._")
    return "\n".join(s)


def _texto(r: dict, chk: dict | None = None) -> str:
    if r.get("status") != "OK":
        return f"No se pudo leer {r.get('detalle')}"
    s = [f"💾 **{r['unidad']}** — inventario completo\n"]

    s.append("**Qué pesa, por carpeta:**")
    for nom, tam in r["carpetas"].most_common(15):
        s.append(f"   {_mb(tam):>10}  {nom}")

    s.append("\n**Qué vale la pena y qué no:**")
    orden = ["diseño", "documento", "imagen", "video", "código", "otro",
             "desechable"]
    for cat in orden:
        if not r["por_cat"].get(cat):
            continue
        marca = "🗑️" if cat == "desechable" else ("❓" if cat == "otro" else "✅")
        s.append(f"   {marca} {cat:11} {r['por_cat'][cat]:>6} archivos  "
                 f"{_mb(r['peso_cat'][cat]):>10}")

    s.append("\n**Los tipos más pesados:**")
    for ext, tam in r["peso_ext"].most_common(12):
        s.append(f"   {_mb(tam):>10}  {ext or '(sin extensión)':12} "
                 f"×{r['por_ext'][ext]}")

    if r["grandes"]:
        s.append("\n**Los archivos más grandes:**")
        for tam, ruta in r["grandes"][:10]:
            s.append(f"   {_mb(tam):>10}  {ruta}")

    if chk:
        s.append(f"\n🔍 **Los .CHK que dejó chkdsk** — qué eran de verdad:")
        for t, n in chk["tipos"].most_common(15):
            nom = "basura (irrecuperable)" if t == ".basura" else t
            s.append(f"   {n:>6} × {nom:24} {_mb(chk['peso'][t]):>10}")
        rescatables = sum(n for t, n in chk["tipos"].items()
                          if t not in (".basura", ".vacio"))
        s.append(f"\n   **{rescatables} se pueden rescatar** con su extensión "
                 "correcta. Corre con `--rescatar`.")

    if r["errores"]:
        s.append(f"\n⚠️ {r['errores']} archivos no se pudieron leer — "
                 "probablemente los que el chkdsk dejó dañados.")
    s.append("\n_Esto no borró ni formateó nada. Lo que se tira lo decides tú._")
    return "\n".join(s)


def main() -> int:
    _consola_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    unidad = args[0]
    r = revisar(unidad)
    if r.get("status") != "OK":
        print(_texto(r))
        return 1
    chk = identificar_chks(r["chks"]) if r["chks"] else None
    print(_texto(r, chk))

    if "--rescatar" in sys.argv and r["chks"]:
        destino = Path(args[1]) if len(args) > 1 else \
            Path.home() / "Downloads" / "RESCATE_CHK"
        print("\nRescatando...")
        res = rescatar_chks(r["chks"], destino)
        print(f"✅ {res['total']} archivos rescatados en {res['destino']}")
        for t, n in sorted(res["copiados"].items(), key=lambda x: -x[1]):
            print(f"   {n:>5} × {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
