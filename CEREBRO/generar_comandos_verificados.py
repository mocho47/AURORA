# -*- coding: utf-8 -*-
"""Genera MANUALES/COMANDOS_VERIFICADOS.md probando CADA frase de verdad.

Por qué existe: el manual anterior se escribió a mano el 2026-08-05 y decía "26
candados" cuando ya había 36. Un manual que se escribe a mano se queda viejo la
primera vez que alguien toca un trigger, y entonces le enseña a Anuar comandos
que ya no existen — peor que no tener manual.

Aquí no se escribe ninguna frase: se toman las frases REALES de Anuar de
`PRUEBAS_VIVAS/frases_anuar*.py`, se pasan por el enrutador REAL de la
Consciencia, y **solo entran al manual las que llegan a donde deben**. Si una
deja de funcionar, desaparece del manual sola en la siguiente corrida.

Uso:  python CEREBRO/generar_comandos_verificados.py
"""
from __future__ import annotations

import importlib.util as ilu
import io
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
SALIDA = RAIZ / "MANUALES" / "COMANDOS_VERIFICADOS.md"

# Qué es cada capacidad, en las palabras del taller. Lo único escrito a mano
# aquí, y a propósito: el nombre del candado no dice para qué sirve, y Anuar
# necesita leer "para qué" antes que "cómo".
QUE_HACE = {
    "abrir_navegador": ("Abre una página en el navegador", "Diseño"),
    "acerca_de": ("Te explica qué es y qué puede hacer", "Cerebro"),
    "accion_fisica": ("Mueve, copia o borra archivos y manda WhatsApps de verdad", "Cerebro"),
    "adaptar_diseno": ("Adapta un diseño a OTRO grosor de material (ajusta las ranuras)", "Taller"),
    "agenda": ("Tus citas y pendientes", "Taller"),
    "alta_lead": ("Da de alta un cliente nuevo en el CRM", "Ventas"),
    "busqueda_web": ("Busca en internet de verdad", "Conocimiento"),
    "calcular_pieza_grande": ("Piñatas y piezas grandes: escala, tabloides, MDF y corte de un jalón", "Taller"),
    "campana_escolar": ("Los precios de los paquetes escolares de Rocío", "Ventas"),
    "consulta_codigo": ("Te dice cómo funciona ella misma por dentro", "Cerebro"),
    "corel": ("Habla con CorelDRAW: qué tienes abierto, exportar", "Diseño"),
    "cotizar": ("Cotiza cualquier producto del catálogo", "Taller"),
    "cotizar_dxf": ("Mide un DXF y te dice el corte real", "Taller"),
    "cotizar_laser_medidas": ("Cotiza láser + material dándole tú las medidas, sin DXF", "Taller"),
    "cotizar_vinil": ("Cotiza vinil de recorte por área", "Taller"),
    "crear_capacidad": ("Le pides una capacidad nueva (hoy eso lo fabrica AURORITA XP)", "Cerebro"),
    "delineado": ("Saca la silueta para recortar, o el dibujo lineal para estarcir", "Diseño"),
    "dxf": ("Convierte cualquier archivo a DXF", "Diseño"),
    "editar_codigo": ("Le pides que corrija un archivo de su propio código", "Cerebro"),
    "equipos": ("Pone a trabajar a un equipo de agentes", "Cerebro"),
    "ficha_vendedor": ("Argumentos de venta y manejo de objeciones", "Ventas"),
    "foto_a_dxf": ("Foto → sin fondo → vectorizada → DXF, de un jalón", "Diseño"),
    "generar_caja": ("Crea una caja con encastres dando solo las medidas", "Taller"),
    "intuicion": ("Te dice dónde estás perdiendo dinero", "Cerebro"),
    "memoria": ("Recuerda lo que le dices y te lo devuelve", "Cerebro"),
    "metodo_campana": ("Revisa una campaña antes de que la mandes", "Marketing"),
    "negocio": ("Cuánto vendiste, cuánto te deben", "Ventas"),
    "print_and_cut": ("Imprimir y recortar: contorno y marcas de registro", "Taller"),
    "proveedor": ("Dónde comprar y a qué precio", "Taller"),
    "publicar": ("Arma el post del día (no lo sube sin tu OK)", "Marketing"),
    "ruta_sola": ("Le pegas una ruta sola y te dice qué puede hacer con eso", "Diseño"),
    "servicio_atf": ("Atiende al cliente de faros/retrofit", "Ventas"),
    "texto_a_corte": ("Convierte texto en letras listas para el plóter", "Diseño"),
    "aprende_conocimiento": ("Le dictas un dato o le pegas un documento y se lo aprende", "Cerebro"),
    "ensenar": ("Le enseñas tú una forma nueva de pedirle algo", "Cerebro"),
    "ver_aprendizaje": ("Qué ha aprendido de cómo trabajas", "Cerebro"),
    "video": ("Qué videos tienes listos para publicar", "Marketing"),
    "voz": ("Hablarle en vez de escribirle", "Cerebro"),
}

ORDEN_GRUPOS = ["Taller", "Ventas", "Diseño", "Marketing", "Conocimiento", "Cerebro"]


def _frases_reales() -> dict:
    """Las frases de Anuar, de sus tres rondas, sin repetir."""
    todo = {}
    for n in ("frases_anuar", "frases_anuar_ronda2", "frases_anuar_ronda3"):
        ruta = RAIZ / "PRUEBAS_VIVAS" / f"{n}.py"
        if not ruta.exists():
            continue
        spec = ilu.spec_from_file_location(n, ruta)
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        for candado, dato in getattr(m, "FRASES", {}).items():
            lista = dato[0] if isinstance(dato, tuple) and dato and isinstance(dato[0], list) else dato
            for f in (lista if isinstance(lista, (list, tuple)) else [lista]):
                if isinstance(f, str) and f not in todo.setdefault(candado, []):
                    todo[candado].append(f)
    return todo


def _destino(C, frase: str):
    """A qué candado llega REALMENTE esa frase, por el camino de verdad."""
    d = C._candado_por_familia(frase)
    if d:
        return d
    for nombre, disparador, _m, _i in C._CANDADOS:
        try:
            if disparador(frase):
                return nombre
        except Exception:
            continue
    # Lo que AURORA APRENDIÓ también cuenta: el chat de verdad lo consulta
    # cuando ningún candado calza, así que un manual que no lo mire estaría
    # reportando como perdidas frases que en vivo sí llegan.
    # Agregado el 2026-08-26, cuando se le enseñaron las frases de estudio de
    # mercado («qué se está vendiendo en corte láser») y el manual las seguía
    # dando por muertas.
    try:
        from CEREBRO import aprende_del_usuario as _apr
        ap = _apr.buscar(frase)
        if ap and ap.get("herramienta"):
            return ap["herramienta"]
    except Exception:
        pass
    return None



def _escribir_txt(ok: dict, fallan: list, hoy: str, n_ok: int, n_cand: int) -> Path:
    """La misma lista, en texto plano para el Bloc de notas y para imprimir.

    Anuar la quiere en papel al lado del teclado. Markdown en el Bloc de notas
    se ve como basura (## y backticks), asi que aqui se escribe plano, con
    saltos de linea de Windows y sin acentos raros: se imprime tal cual.
    """
    A = []
    A += ["=" * 74,
          "        COMANDOS DE AURORA  -  probados uno por uno",
          "=" * 74,
          "",
          f"  {n_ok} frases verificadas   ·   {len(ok)} capacidades   ·   {hoy}",
          "",
          "  Cada frase de esta hoja se paso por AURORA de verdad y llego a",
          "  donde debia. No te la tienes que aprender: basta con que le digas",
          "  la idea. Si algo no lo entiende y se lo dices de otra forma que si",
          "  funciona, se queda con las dos.",
          "",
          "  Se escribe igual que hablas: sin acentos, como te salga.",
          "",
          "=" * 74,
          ""]

    por_grupo = {}
    for candado in ok:
        _q, grupo = QUE_HACE.get(candado, ("", "Cerebro"))
        por_grupo.setdefault(grupo, []).append(candado)

    for grupo in ORDEN_GRUPOS:
        if grupo not in por_grupo:
            continue
        A += ["", "-" * 74, f"  {grupo.upper()}", "-" * 74, ""]
        for candado in sorted(por_grupo[grupo]):
            que, _g = QUE_HACE.get(candado, ("", ""))
            A.append(f"  {que}")
            for f in ok[candado]:
                A.append(f"      > {f}")
            A.append("")

    if fallan:
        A += ["", "=" * 74,
              "  ESTAS CONTESTAN, PERO LAS AGARRA OTRA FUNCION (por arreglar)",
              "=" * 74, ""]
        for c, f, d in fallan:
            A.append(f"      > {f}")
            A.append(f"        deberia ir a {c} - hoy la atiende {d}")
        A.append("")

    A += ["", "=" * 74,
          "  Esta hoja NO se escribe a mano: la genera AURORA sola con",
          "  python CEREBRO/generar_comandos_verificados.py",
          "  Si un comando deja de servir, desaparece de aqui en la siguiente",
          "  corrida. Nunca te va a ensenar algo que ya no existe.",
          "=" * 74]

    txt = "\r\n".join(A)
    destino = SALIDA.with_suffix(".txt")
    destino.write_text(txt, encoding="utf-8-sig", newline="")
    return destino


def generar() -> dict:
    from CEREBRO import consciencia as C

    todo = _frases_reales()
    ok, fallan = {}, []
    for candado, frases in todo.items():
        for f in frases:
            if _destino(C, f) == candado:
                ok.setdefault(candado, []).append(f)
            else:
                fallan.append((candado, f, _destino(C, f)))

    n_ok = sum(len(v) for v in ok.values())
    hoy = date.today().isoformat()
    L = [
        "# Comandos de AURORA — probados uno por uno",
        "",
        "**Cada frase de esta lista se pasó por el enrutador real de AURORA y llegó**",
        "**a donde debía.** Si una dejara de funcionar, desaparecería de aquí sola:",
        "este archivo no se escribe, se genera (`CEREBRO/generar_comandos_verificados.py`).",
        "",
        "Están escritas **como escribe Anuar**, sin acentos y con sus modismos, porque",
        "así se van a usar de verdad.",
        "",
        f"Generado: {hoy} · **{n_ok} frases verificadas** en **{len(ok)} capacidades**"
        f" · {len(C._CANDADOS)} candados en total",
        "",
        "> **No te lo tienes que aprender.** Basta con que le digas la idea. Si algo no",
        "> lo entiende y se lo dices de otra forma que sí funciona, se queda con las dos.",
        "",
        "---",
        "",
    ]

    por_grupo = {}
    for candado in ok:
        _q, grupo = QUE_HACE.get(candado, ("", "Cerebro"))
        por_grupo.setdefault(grupo, []).append(candado)

    for grupo in ORDEN_GRUPOS:
        if grupo not in por_grupo:
            continue
        L += [f"## {grupo}", ""]
        for candado in sorted(por_grupo[grupo]):
            que, _g = QUE_HACE.get(candado, ("", ""))
            L += [f"### {que}", ""]
            for f in ok[candado]:
                L.append(f"- `{f}`")
            L.append("")
        L.append("---")
        L.append("")

    if fallan:
        L += ["## Frases que hoy atiende otro candado", "",
              "No fallan: contestan igual, pero las agarra un gemelo. Se anotan para",
              "arreglarlas, no para que Anuar las evite.", ""]
        for c, f, d in fallan:
            L.append(f"- `{f}` — esperado **{c}**, lo atiende **{d}**")
        L.append("")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(L), encoding="utf-8")
    txt = _escribir_txt(ok, fallan, hoy, n_ok, len(C._CANDADOS))
    return {"verificadas": n_ok, "capacidades": len(ok),
            "fallan": len(fallan), "archivo": str(SALIDA), "txt": str(txt)}


if __name__ == "__main__":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    r = generar()
    print(f"{r['archivo']}\n{r['txt']}\n  {r['verificadas']} frases verificadas · "
          f"{r['capacidades']} capacidades · {r['fallan']} las atiende un gemelo")
