# -*- coding: utf-8 -*-
"""AURORA · LICENCIAS DE LAS APPS

Anuar lo pidió el 2026-08-17: *"a esta versión podrías ponerle 3 meses de
licencia administrada por AURORA, además de que ambas tengan el plugin"*.

Es lo que convierte una herramienta en un producto: puede entregarla, cobrarla
y saber a quién le vendió qué y cuándo se le vence.

**Cómo funciona, y por qué así:**

· **La clave se valida sin internet.** Trae adentro el cliente, el producto y
  la fecha de vencimiento, firmados. El cliente de un taller puede quedarse
  sin internet un martes y la herramienta sigue abriendo — que es lo mínimo
  que se le pide a algo por lo que pagó.
· **La firma es HMAC-SHA256** con un secreto que vive en el `.env`, nunca en
  el código. Sin ese secreto no se puede fabricar una clave válida.
· **AURORA lleva el registro** en `DATOS/licencias.db`: a quién, qué, desde
  cuándo, hasta cuándo, y si ya se renovó.
· **Avisa antes de vencer**, no el día que vence. Un cliente al que se le
  apaga la herramienta sin avisar no renueva: se enoja.

**Lo que esto NO es, dicho de frente:** una licencia que se valida en la
misma computadora del cliente siempre se puede romper por alguien que se lo
proponga en serio. Esto sirve para lo que de verdad pasa — que se venza y se
renueve, y que no se pase de mano en mano sin control. Para blindarlo de
verdad haría falta un servidor que valide, y eso cuesta y se cae. No vale la
pena todavía.

Correr:
    python LICENCIA/licencias.py --generar "Taller El Güero" --app buscador_clientes --meses 3
    python LICENCIA/licencias.py --revisar CLAVE
    python LICENCIA/licencias.py --lista
    python LICENCIA/licencias.py --por-vencer
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import io
import json
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BD = RAIZ / "DATOS" / "licencias.db"
VAR_SECRETO = "LICENCIA_SECRETO"
AVISAR_DIAS = 15          # cuántos días antes se empieza a avisar


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _secreto() -> bytes:
    """El secreto que firma las claves. Del `.env`, jamás del código.

    Si no está, se crea uno y se deja escrito en el `.env` — pero se avisa,
    porque a partir de ese momento las claves viejas dejan de valer.
    """
    v = os.environ.get(VAR_SECRETO)
    if not v:
        env = RAIZ / ".env"
        if env.exists():
            for l in env.read_text(encoding="utf-8", errors="replace").splitlines():
                if l.strip().startswith(f"{VAR_SECRETO}="):
                    v = l.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not v:
        import secrets
        v = secrets.token_urlsafe(32)
        env = RAIZ / ".env"
        with open(env, "a", encoding="utf-8") as f:
            f.write(f"\n{VAR_SECRETO}={v}\n")
        print(f"⚠️  No había secreto de licencias. Se creó uno y se guardó en "
              f"{env} como {VAR_SECRETO}.\n"
              f"   Guárdalo bien: si se pierde, todas las claves que hayas "
              f"dado dejan de servir.")
    return v.encode()


def _firma(carga: bytes) -> str:
    return base64.urlsafe_b64encode(
        hmac.new(_secreto(), carga, hashlib.sha256).digest()[:9]
    ).decode().rstrip("=")


def _bonita(s: str) -> str:
    """La clave partida en bloques de 5. Se dicta por teléfono sin errores."""
    s = s.replace("-", "")
    return "-".join(s[i:i + 5] for i in range(0, len(s), 5))


def generar(cliente: str, app: str = "buscador_clientes", meses: int = 3,
            notas: str = "", desde: str = "") -> dict:
    """Fabrica una clave y la deja anotada en el registro de AURORA."""
    if not cliente.strip():
        return {"status": "SIN_CLIENTE",
                "detalle": "Dime a nombre de quién va la licencia."}
    ini = (datetime.strptime(desde, "%Y-%m-%d").date() if desde
           else date.today())
    # Tres meses son 3 × 30 días redondos, a propósito: es lo que la gente
    # entiende por «tres meses» y no depende de si el mes tuvo 28 o 31.
    fin = ini + timedelta(days=int(meses) * 30)
    carga = json.dumps({"c": cliente.strip()[:40], "a": app,
                        "f": fin.isoformat()},
                       separators=(",", ":"), ensure_ascii=False).encode()
    cuerpo = base64.urlsafe_b64encode(carga).decode().rstrip("=")
    clave = _bonita(f"{cuerpo}.{_firma(carga)}".replace(".", "Z9"))

    cx = _bd()
    cx.execute("""INSERT INTO licencias
                  (clave, cliente, app, desde, hasta, meses, notas, creada)
                  VALUES (?,?,?,?,?,?,?,?)""",
               (clave, cliente.strip(), app, ini.isoformat(), fin.isoformat(),
                int(meses), notas,
                datetime.now().strftime("%Y-%m-%d %H:%M")))
    cx.commit()
    cx.close()
    return {"status": "OK", "clave": clave, "cliente": cliente.strip(),
            "app": app, "desde": ini.isoformat(), "hasta": fin.isoformat(),
            "dias": (fin - ini).days}


def revisar(clave: str, app: str = "") -> dict:
    """¿Sirve esta clave? Se responde sin internet y sin base de datos.

    Es lo que corre en la máquina del cliente. Por eso no consulta nada:
    la clave se valida sola.
    """
    try:
        crudo = str(clave or "").replace("-", "").replace(" ", "")
        if "Z9" not in crudo:
            return {"status": "CLAVE_RARA",
                    "detalle": "Esa clave no tiene la forma correcta. "
                               "Revisa que esté completa."}
        cuerpo, firma = crudo.rsplit("Z9", 1)
        carga = base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4))
        if not hmac.compare_digest(_firma(carga), firma):
            return {"status": "NO_ES_VALIDA",
                    "detalle": "Esa clave no la generé yo, o viene alterada."}
        d = json.loads(carga)
    except Exception:
        return {"status": "CLAVE_RARA",
                "detalle": "No pude leer esa clave. Cópiala completa, con "
                           "todo y guiones."}

    fin = date.fromisoformat(d["f"])
    faltan = (fin - date.today()).days
    if app and d.get("a") != app:
        return {"status": "OTRA_APP",
                "detalle": f"Esa licencia es de «{d.get('a')}», no de "
                           f"«{app}».", "cliente": d.get("c")}
    r = {"cliente": d.get("c"), "app": d.get("a"), "hasta": d["f"],
         "dias": faltan}
    if faltan < 0:
        r["status"] = "VENCIDA"
        r["detalle"] = (f"La licencia venció hace {abs(faltan)} días "
                        f"({fin.strftime('%d/%m/%Y')}).")
    elif faltan <= AVISAR_DIAS:
        r["status"] = "POR_VENCER"
        r["detalle"] = (f"Quedan {faltan} días: vence el "
                        f"{fin.strftime('%d/%m/%Y')}.")
    else:
        r["status"] = "OK"
        r["detalle"] = (f"Activa hasta el {fin.strftime('%d/%m/%Y')} "
                        f"({faltan} días).")
    return r


def _bd():
    BD.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(BD, timeout=10)
    cx.execute("PRAGMA journal_mode=WAL")
    cx.execute("""CREATE TABLE IF NOT EXISTS licencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, clave TEXT UNIQUE,
        cliente TEXT NOT NULL, app TEXT, desde TEXT, hasta TEXT,
        meses INTEGER, notas TEXT, creada TEXT, renovada_de TEXT)""")
    cx.commit()
    return cx


def lista(app: str = "", incluir_vencidas: bool = True) -> dict:
    """Todo lo que has entregado. Es tu cartera, no un log."""
    cx = _bd()
    q = "SELECT * FROM licencias WHERE 1=1"
    p = []
    if app:
        q += " AND app=?"
        p.append(app)
    q += " ORDER BY hasta"
    cx.row_factory = sqlite3.Row
    filas = [dict(f) for f in cx.execute(q, p).fetchall()]
    cx.close()
    hoy = date.today()
    fuera = []
    for f in filas:
        f["dias"] = (date.fromisoformat(f["hasta"]) - hoy).days
        f["estado"] = ("vencida" if f["dias"] < 0 else
                       "por vencer" if f["dias"] <= AVISAR_DIAS else "activa")
        if f["estado"] == "vencida" and not incluir_vencidas:
            continue
        fuera.append(f)
    activas = sum(1 for f in fuera if f["estado"] == "activa")
    return {"status": "OK", "cuantas": len(fuera), "activas": activas,
            "por_vencer": sum(1 for f in fuera if f["estado"] == "por vencer"),
            "vencidas": sum(1 for f in fuera if f["estado"] == "vencida"),
            "licencias": fuera}


def por_vencer(dias: int = AVISAR_DIAS) -> dict:
    """A quién hay que llamarle esta semana. Renovar cuesta menos que vender.

    Esto es lo que AURORA revisa sola: un cliente al que se le venció sin
    aviso ya no vuelve, y uno al que le avisas con tiempo casi siempre paga.
    """
    r = lista()
    urgentes = [f for f in r["licencias"] if -30 <= f["dias"] <= dias]
    urgentes.sort(key=lambda x: x["dias"])
    return {"status": "OK", "cuantas": len(urgentes), "licencias": urgentes,
            "dinero_en_juego": len(urgentes)}


def renovar(clave_vieja: str, meses: int = 3) -> dict:
    """Renueva desde donde se quedó, no desde hoy: no se le regalan días."""
    v = revisar(clave_vieja)
    if v["status"] in ("CLAVE_RARA", "NO_ES_VALIDA"):
        return v
    cx = _bd()
    cx.row_factory = sqlite3.Row
    f = cx.execute("SELECT * FROM licencias WHERE clave=?",
                   (clave_vieja.strip(),)).fetchone()
    cx.close()
    cliente = (f["cliente"] if f else v.get("cliente", "")) or ""
    app = (f["app"] if f else v.get("app", "")) or ""
    # Si todavía no vence, la nueva arranca el día que terminaba la vieja.
    arranque = (v["hasta"] if v["dias"] > 0 else date.today().isoformat())
    r = generar(cliente, app, meses, notas="renovación", desde=arranque)
    if r.get("status") == "OK":
        cx = _bd()
        cx.execute("UPDATE licencias SET renovada_de=? WHERE clave=?",
                   (clave_vieja.strip(), r["clave"]))
        cx.commit()
        cx.close()
        r["renovada_de"] = clave_vieja.strip()
    return r


# ── CANDADOS CONTRA COPIAR LA LICENCIA ──────────────────────────────────
# Anuar lo pidió el 2026-08-17: *"pon candados de seguridad anti clonaje o
# réplica"*. Sin esto, una clave se pasa por WhatsApp y se vende una vez para
# veinte talleres.
#
# Van tres candados, y cada uno tapa una forma distinta de hacer trampa:
#
#  1. **Atada al equipo.** La primera vez que se pega la clave, se toma la
#     huella de ESA computadora y queda amarrada. En otra máquina no abre.
#  2. **El archivo de activación va firmado.** Si alguien lo edita para
#     cambiar la fecha o la huella, la firma deja de cuadrar y no abre.
#  3. **El reloj no se puede echar para atrás.** Se guarda la última fecha
#     vista; si la computadora amanece en el año pasado, se cacha.
#
# **Lo que NO tapa, dicho de frente:** alguien que sepa programar puede abrir
# el archivo .py y quitar la revisión. Contra eso solo sirve entregar el
# programa compilado, y aun así se rompe si alguien se lo propone. Esto está
# hecho para el 99% de los casos reales — que se pase la clave a un conocido,
# o que se copie la carpeta a otra computadora — no para un pirata dedicado.

def huella_equipo() -> dict:
    """La huella de esta computadora. Varias piezas, para que aguante cambios.

    Se toman tres cosas y basta con que **dos** coincidan. Así un cliente que
    cambia un disco duro o le formatean no pierde su licencia — pero copiar
    la carpeta a otra máquina sí se cacha, porque ahí no coincide ninguna.
    """
    import platform
    piezas = {}
    try:
        piezas["equipo"] = platform.node()[:40]
    except Exception:
        pass
    if os.name == "nt":
        # **Nada de `wmic`.** Se probó el 2026-08-17 y en Windows 11 ya no
        # existe: devolvía vacío y la huella se quedaba con una sola pieza,
        # el nombre del equipo — que cualquiera cambia en dos clics. Estas
        # dos se leen del registro y del sistema de archivos, son rápidas y
        # no dependen de ningún programa externo.
        try:
            import winreg
            with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography", 0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                # MachineGuid es único por instalación de Windows. Sobrevive
                # cambios de nombre y de hardware; solo cambia si reinstalan.
                piezas["windows"] = winreg.QueryValueEx(k, "MachineGuid")[0]
        except Exception:
            pass
        try:
            import ctypes
            serie = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p("C:\\"), None, 0,
                    ctypes.byref(serie), None, None, None, 0):
                # El número de serie del volumen C: cambia si formatean, y
                # por eso NO va solo — va junto con los otros dos.
                piezas["disco"] = f"{serie.value:08X}"
        except Exception:
            pass
    else:
        for nombre, ruta in (("placa", "/etc/machine-id"),
                             ("disco", "/var/lib/dbus/machine-id")):
            try:
                piezas[nombre] = Path(ruta).read_text().strip()[:60]
            except Exception:
                continue
    corta = {k: hashlib.sha256((v + "aurora").encode()).hexdigest()[:12]
             for k, v in piezas.items()}
    return {"piezas": corta,
            "resumen": hashlib.sha256(
                "|".join(f"{k}={v}" for k, v in sorted(corta.items())).encode()
            ).hexdigest()[:16]}


def _mismo_equipo(guardada: dict, ahora: dict) -> tuple:
    """¿Es la misma computadora? Con 2 de 3 piezas basta."""
    g, a = guardada.get("piezas", {}), ahora.get("piezas", {})
    iguales = [k for k in g if k in a and g[k] == a[k]]
    # Si solo se pudo leer una pieza (una máquina que no deja consultar el
    # hardware), se acepta esa una: es preferible a dejar sin herramienta a
    # un cliente que sí pagó.
    minimo = 1 if min(len(g), len(a)) < 2 else 2
    return len(iguales) >= minimo, iguales


def _archivo(app: str, carpeta: str = "") -> Path:
    d = Path(carpeta) if carpeta else Path.home() / ".aurora"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"licencia_{app}.json"


def _sellar(d: dict) -> dict:
    """Le pone firma al archivo de activación para que no se pueda editar."""
    crudo = json.dumps({k: v for k, v in d.items() if k != "sello"},
                       sort_keys=True, ensure_ascii=False).encode()
    d["sello"] = hmac.new(_secreto(), crudo, hashlib.sha256).hexdigest()[:24]
    return d


def _sello_bueno(d: dict) -> bool:
    if "sello" not in d:
        return False
    crudo = json.dumps({k: v for k, v in d.items() if k != "sello"},
                       sort_keys=True, ensure_ascii=False).encode()
    return hmac.compare_digest(
        hmac.new(_secreto(), crudo, hashlib.sha256).hexdigest()[:24], d["sello"])


def activar(clave: str, app: str, carpeta: str = "") -> dict:
    """Amarra la clave a ESTA computadora. Se hace una sola vez."""
    r = revisar(clave, app)
    if r["status"] in ("CLAVE_RARA", "NO_ES_VALIDA", "OTRA_APP"):
        return {**r, "puede_usarse": False}
    if r["status"] == "VENCIDA":
        return {**r, "puede_usarse": False,
                "mensaje": f"⛔ {r['detalle']} Pide tu renovación."}
    f = _archivo(app, carpeta)
    if f.exists():
        try:
            viejo = json.loads(f.read_text(encoding="utf-8"))
            if (viejo.get("clave") == clave.strip() and _sello_bueno(viejo)):
                ok, _ = _mismo_equipo(viejo.get("huella", {}), huella_equipo())
                if not ok:
                    return {"status": "OTRO_EQUIPO", "puede_usarse": False,
                            "mensaje": ("Esta licencia ya está activada en "
                                        "otra computadora. Cada licencia es "
                                        "para un equipo.")}
        except Exception:
            pass
    d = _sellar({"clave": clave.strip(), "app": app,
                 "cliente": r.get("cliente", ""),
                 "hasta": r.get("hasta", ""),
                 "huella": huella_equipo(),
                 "activada": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "visto": date.today().isoformat()})
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**r, "puede_usarse": True, "archivo": str(f),
            "mensaje": f"✅ Licencia activada en este equipo. {r['detalle']}"}


def guardar_local(clave: str, app: str, carpeta: str = "") -> dict:
    """Guarda y activa. Es lo que llama la app cuando pegan la clave."""
    return activar(clave, app, carpeta)


def leer_local(app: str, carpeta: str = "") -> str:
    f = _archivo(app, carpeta)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8")).get("clave", "")
        except Exception:
            return ""
    # Compatibilidad con las primeras copias, que guardaban un .txt pelón.
    viejo = f.with_suffix(".txt")
    return viejo.read_text(encoding="utf-8").strip() if viejo.exists() else ""


def al_abrir(app: str, carpeta: str = "") -> dict:
    """Lo que la app pregunta al arrancar. Una llamada, una respuesta clara.

    Devuelve `puede_usarse` para que la app no tenga que interpretar nada, y
    un `mensaje` ya escrito para enseñárselo al usuario tal cual.
    """
    f = _archivo(app, carpeta)
    clave = leer_local(app, carpeta)
    if not clave:
        return {"status": "SIN_LICENCIA", "puede_usarse": False,
                "mensaje": ("Esta copia todavía no tiene licencia. Pídesela a "
                            "quien te entregó el programa y pégala aquí.")}

    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        # CANDADO 2 — el archivo va firmado.
        if d and not _sello_bueno(d):
            return {"status": "MANIPULADA", "puede_usarse": False,
                    "mensaje": ("El archivo de licencia fue modificado. "
                                "Vuelve a pegar tu clave original.")}
        # CANDADO 1 — el equipo tiene que ser el mismo.
        if d.get("huella"):
            ok, iguales = _mismo_equipo(d["huella"], huella_equipo())
            if not ok:
                return {"status": "OTRO_EQUIPO", "puede_usarse": False,
                        "mensaje": ("Esta licencia está activada en otra "
                                    "computadora. Si cambiaste de equipo, "
                                    "pide que te la reactiven.")}
        # CANDADO 3 — el reloj no se echa para atrás.
        visto = d.get("visto")
        if visto:
            try:
                if date.today() < date.fromisoformat(visto) - timedelta(days=2):
                    return {"status": "RELOJ", "puede_usarse": False,
                            "mensaje": ("La fecha de esta computadora está "
                                        "atrasada. Ponla en la fecha correcta "
                                        "y vuelve a abrir.")}
            except ValueError:
                pass
        try:
            d["visto"] = max(str(d.get("visto") or ""),
                             date.today().isoformat())
            f.write_text(json.dumps(_sellar(d), ensure_ascii=False, indent=2),
                         encoding="utf-8")
        except Exception:
            pass

    r = revisar(clave, app)
    r["puede_usarse"] = r["status"] in ("OK", "POR_VENCER")
    if r["status"] == "OK":
        r["mensaje"] = f"Licencia de {r['cliente']} · {r['detalle']}"
    elif r["status"] == "POR_VENCER":
        r["mensaje"] = (f"⚠️ {r['detalle']} Pide tu renovación para que no se "
                        f"te corte a media chamba.")
    elif r["status"] == "VENCIDA":
        r["mensaje"] = (f"⛔ {r['detalle']} Pide tu renovación y la "
                        f"herramienta vuelve a abrir de inmediato.")
    else:
        r["mensaje"] = r.get("detalle", "La licencia no es válida.")
    return r


def _texto_lista(r: dict) -> str:
    if not r["cuantas"]:
        return "Todavía no has entregado ninguna licencia."
    t = (f"🔑 **{r['cuantas']} licencias** · {r['activas']} activas · "
         f"{r['por_vencer']} por vencer · {r['vencidas']} vencidas\n")
    for f in r["licencias"]:
        ico = {"activa": "🟢", "por vencer": "🟡", "vencida": "🔴"}[f["estado"]]
        t += (f"\n{ico} **{f['cliente']}** · {f['app']}\n"
              f"   vence {f['hasta']} "
              + (f"(faltan {f['dias']} días)" if f["dias"] >= 0
                 else f"(hace {abs(f['dias'])} días)") + "\n"
              f"   `{f['clave']}`")
        if f.get("notas"):
            t += f"   — {f['notas']}"
    return t


def main() -> int:
    _consola_utf8()
    a = sys.argv[1:]

    def _op(n, d=None):
        if f"--{n}" in a:
            i = a.index(f"--{n}")
            if i + 1 < len(a):
                return a[i + 1]
        return d

    if _op("generar"):
        r = generar(_op("generar"), _op("app", "buscador_clientes"),
                    int(_op("meses", 3)), _op("notas", ""))
        if r["status"] != "OK":
            print("⚠️", r["detalle"])
            return 1
        print(f"🔑 Licencia para **{r['cliente']}**\n"
              f"   app: {r['app']}\n"
              f"   del {r['desde']} al {r['hasta']} ({r['dias']} días)\n\n"
              f"   {r['clave']}\n\n"
              f"   Pásasela así, con guiones. Se pega una vez y ya.")
        return 0
    if _op("revisar"):
        r = revisar(_op("revisar"), _op("app", ""))
        ico = {"OK": "🟢", "POR_VENCER": "🟡", "VENCIDA": "🔴"}.get(r["status"], "⚠️")
        print(f"{ico} {r.get('cliente', '')} — {r['detalle']}")
        return 0 if r["status"] in ("OK", "POR_VENCER") else 1
    if _op("renovar"):
        r = renovar(_op("renovar"), int(_op("meses", 3)))
        if r.get("status") != "OK":
            print("⚠️", r.get("detalle", r.get("status")))
            return 1
        print(f"🔁 Renovada **{r['cliente']}** hasta {r['hasta']}\n\n"
              f"   {r['clave']}")
        return 0
    if "--por-vencer" in a:
        r = por_vencer(int(_op("dias", AVISAR_DIAS)))
        if not r["cuantas"]:
            print("✅ Nadie está por vencer. Nada que cobrar hoy.")
            return 0
        print(f"📞 **{r['cuantas']} por renovar** — llámales antes de que se "
              f"les corte:\n")
        for f in r["licencias"]:
            print(f"  {'⛔' if f['dias'] < 0 else '🟡'} {f['cliente']:<28} "
                  f"{f['app']:<22} "
                  + (f"vence en {f['dias']} días" if f["dias"] >= 0
                     else f"venció hace {abs(f['dias'])} días"))
        return 0
    if "--lista" in a:
        print(_texto_lista(lista(_op("app", ""))))
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
