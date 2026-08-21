# -*- coding: utf-8 -*-
"""AURORA · La campaña, pero por WhatsApp Web (sin API, sin límite, gratis)

Anuar lo cachó el 2026-08-14: *"cómo lo mandas si Green API solo te deja
mandarlo a 3 personas, pues se acabó el plan gratis"*. Tenía razón — la API
gratuita solo entrega a los números autorizados, así que la campaña a 21
clientas por ahí no sale.

Esto lo resuelve por el otro lado: se arma una página con un botón por
clienta. El botón abre WhatsApp con el mensaje YA ESCRITO para ella; él nomás
aprieta enviar. No hay API, no hay costo, no hay tope de destinatarios, y
cada envío lo hace él — que es como debe ser.

La página marca en verde a las que ya mandó y se acuerda aunque cierre el
navegador, para que no le mande dos veces a la misma ni pierda el lugar.

Correr:
    python MARKETING/campana_por_whatsapp_web.py
"""
from __future__ import annotations
import html
import io
import sys
import urllib.parse
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _consola_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")


def _campana():
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        "campana_regreso_clases", RAIZ / "MARKETING" / "campana_regreso_clases.py")
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e8eaed;
     font:15px/1.5 system-ui,'Segoe UI',Roboto,sans-serif}
header{padding:22px 18px;background:#161a21;border-bottom:1px solid #262c36;
       position:sticky;top:0;z-index:5}
h1{margin:0 0 4px;font-size:19px}
.sub{color:#9aa3ae;font-size:13px}
.barra{height:6px;background:#262c36;border-radius:99px;margin-top:12px;overflow:hidden}
.barra>i{display:block;height:100%;background:#25d366;width:0;transition:width .25s}
main{padding:14px 12px 60px;max-width:760px;margin:0 auto}
.c{display:flex;align-items:center;gap:12px;padding:12px 14px;margin-bottom:9px;
   background:#161a21;border:1px solid #262c36;border-radius:12px}
.c.ok{border-color:#1f6b3d;background:#12261a}
.n{width:26px;text-align:right;color:#6b7480;font-size:13px}
.d{flex:1;min-width:0}
.nom{font-weight:600;text-transform:capitalize}
.tel{color:#9aa3ae;font-size:13px;font-variant-numeric:tabular-nums}
a.b{background:#25d366;color:#07210f;text-decoration:none;font-weight:700;
    padding:12px 18px;border-radius:9px;white-space:nowrap}
/* En el celular los dedos no aciertan botones chicos: todo más alto. */
@media(max-width:520px){
  .c{padding:14px 12px;gap:9px}
  .nom{font-size:16px}
  a.b{padding:14px 16px}
  button.m{padding:12px 12px}
  h1{font-size:17px}
}
.c.ok a.b{background:#2a3b31;color:#8fbfa2}
button.m{background:none;border:1px solid #39414d;color:#9aa3ae;border-radius:8px;
         padding:8px 10px;cursor:pointer;font-size:16px;line-height:1}
.pie{color:#6b7480;font-size:12px;text-align:center;padding:18px 10px}
.aviso{background:#1d1a10;border:1px solid #4a3d16;color:#e0cf9a;
       padding:11px 14px;border-radius:10px;margin-bottom:14px;font-size:13px}
"""

_JS = """
const K='milens_campana_regreso_2026';
const hechas=new Set(JSON.parse(localStorage.getItem(K)||'[]'));
function pinta(){
  document.querySelectorAll('.c').forEach(c=>{
    c.classList.toggle('ok',hechas.has(c.dataset.tel));
  });
  const t=document.querySelectorAll('.c').length;
  document.getElementById('cuenta').textContent=hechas.size+' de '+t+' enviados';
  document.querySelector('.barra>i').style.width=(hechas.size/t*100)+'%';
}
function marcar(tel){
  hechas.has(tel)?hechas.delete(tel):hechas.add(tel);
  localStorage.setItem(K,JSON.stringify([...hechas]));pinta();
}
document.querySelectorAll('a.b').forEach(a=>{
  a.addEventListener('click',()=>{hechas.add(a.dataset.tel);
    localStorage.setItem(K,JSON.stringify([...hechas]));setTimeout(pinta,300);});
});
document.querySelectorAll('button.m').forEach(b=>{
  b.addEventListener('click',()=>marcar(b.dataset.tel));
});
pinta();
"""


def generar(salida: str = "") -> dict:
    """Arma la página con un botón por clienta."""
    camp = _campana()
    lista = camp.clientas()
    if not lista:
        return {"status": "SIN_CLIENTAS",
                "detalle": "No encontré clientas con teléfono en la base."}

    filas = []
    for i, c in enumerate(lista, 1):
        nombre = (c.get("nombre") or "").strip()
        tel = "".join(ch for ch in str(c.get("telefono") or "") if ch.isdigit())
        if len(tel) != 10:
            continue
        # El mensaje decide solo si saluda por nombre; aquí solo se muestra a
        # quién le toca. Sin nombre NO se descarta: es un cliente igual.
        texto = camp._plantilla(nombre)
        visible = nombre or "sin nombre"
        url = ("https://wa.me/52" + tel + "?text="
               + urllib.parse.quote(texto, safe=""))
        filas.append(
            f'<div class="c" data-tel="{tel}">'
            f'<div class="n">{i}</div>'
            f'<div class="d"><div class="nom">{html.escape(visible)}</div>'
            f'<div class="tel">{tel}</div></div>'
            f'<button class="m" data-tel="{tel}" title="Marcar a mano">✓</button>'
            f'<a class="b" data-tel="{tel}" target="_blank" href="{url}">WhatsApp</a>'
            f'</div>')

    pagina = (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Campaña regreso a clases · Milen's</title>"
        f"<style>{_CSS}</style></head><body>"
        "<header><h1>🎒 Regreso a clases · Creaciones Milen's</h1>"
        f"<div class='sub' id='cuenta'>0 de {len(filas)} enviados</div>"
        "<div class='barra'><i></i></div></header><main>"
        "<div class='aviso'>Cada botón abre WhatsApp con el mensaje ya escrito "
        "para esa clienta. <b>Tú aprietas enviar.</b> Deja pasar un minuto "
        "entre una y otra: 21 mensajes seguidos en un ratito es lo que hace "
        "que WhatsApp marque la cuenta.</div>"
        + "".join(filas) +
        "<div class='pie'>Las verdes ya se mandaron. Se guarda en esta "
        "computadora, puedes cerrar y seguir después.</div>"
        f"</main><script>{_JS}</script></body></html>")

    destino = Path(salida) if salida else (Path.home() / "Downloads"
                                           / "CAMPANA_REGRESO_CLASES.html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    return {"status": "OK", "archivo": str(destino), "clientas": len(filas),
            "kb": round(destino.stat().st_size / 1024, 1)}


def _texto(r: dict) -> str:
    if r.get("status") != "OK":
        return f"No pude armarla: {r.get('detalle', r.get('status'))}"
    return (f"📲 **Campaña lista para mandar a mano** — {r['clientas']} clientas\n\n"
            f"📁 `{r['archivo']}`  ({r['kb']} KB)\n\n"
            "Se abre en el navegador. **Un clic por clienta**: WhatsApp se abre "
            "con el mensaje ya escrito y tú aprietas enviar. Las que ya mandaste "
            "se ponen en verde.\n\n"
            "_Sin API, sin costo y sin tope de 3 números._")


def main() -> int:
    _consola_utf8()
    r = generar()
    print(_texto(r))
    if r.get("status") == "OK" and "--abrir" in sys.argv:
        webbrowser.open(Path(r["archivo"]).as_uri())
    return 0 if r.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
