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
