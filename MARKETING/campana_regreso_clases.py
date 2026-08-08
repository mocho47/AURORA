# -*- coding: utf-8 -*-
"""AURORA · CAMPAÑA REGRESO A CLASES 2026 — Milens

Clientas REALES que compraron en julio 2026 y quedaron satisfechas. No es una
lista comprada ni contactos fríos: son personas que ya conocen el taller.

Productos (precios dictados por Anuar el 2026-08-04):
  • Etiquetas para útiles — tabloide suajado en adhesivo de papel: $95
  • Lápices personalizados con láser: $7 c/u
  • Personalización de uniformes: $15 por prenda

NO ENVÍA NADA POR SÍ SOLO. Genera los mensajes para que Anuar los revise; el
envío real es una decisión suya, mensaje por mensaje o en tanda aprobada.

Correr:  python MARKETING/campana_regreso_clases.py           (solo muestra)
         python MARKETING/campana_regreso_clases.py --enviar  (envía de verdad)
"""
from __future__ import annotations
import io
import sqlite3
import sys
import time
from pathlib import Path

# La consola de Windows es cp1252 y truena con los emojis del mensaje. A
# WhatsApp llegan bien: el problema es solo mostrarlos aquí.
def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y truena con acentos y emojis.

    Se llama SOLO al correr el script directo. Hacerlo al importar le rompía la
    salida a quien lo importara — incluida AURORA (2026-08-05).
    """
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# El respaldo de antes de dejar AURORA virgen: ahí viven las órdenes reales.
BD = RAIZ / "_BACKUP_DB_pre_virgen_20260723_235128" / "taller.db"

# Entre envíos. WhatsApp marca como spam las ráfagas: mandar despacio no es
# lentitud, es lo que evita que tumben el número del negocio.
SEGUNDOS_ENTRE_ENVIOS = 45


def _plantilla(nombre: str) -> str:
    """Corto, de persona a persona. Nada de publicidad gritada."""
    # En algunas órdenes se capturó el PRODUCTO donde va el nombre
    # ("servilleteros"). Saludar así delata que es un envío masivo, que es justo
    # lo contrario de lo que se busca: se saluda sin nombre y ya.
    _NO_ES_NOMBRE = ("servillet", "taza", "playera", "vaso", "termo", "orden",
                     "pedido", "cliente", "sin nombre")
    crudo = (nombre or "").strip()
    primer = crudo.split(" ")[0].capitalize()
    if not primer or any(p in crudo.lower() for p in _NO_ES_NOMBRE):
        saludo = "Hola 👋 le saluda *Creaciones Milen's*"
    else:
        saludo = f"Hola {primer} 👋 le saluda *Creaciones Milen's*"
    return (
        f"{saludo}\n"
        # Va ARRIBA y no al final a propósito. Estas 21 no son desconocidas:
        # ya le compraron a Milen's. Agradecérselo en la primera línea es lo
        # que separa este mensaje de la publicidad — ella sabe de inmediato
        # que le escribe alguien a quien ya le compró, no un número cualquiera.
        # Idea de Anuar, 2026-08-06.
        "¡Gracias por su preferencia! 🙏\n\n"
        # EL HOOK NO ES EL CALENDARIO, ES EL DOLOR.
        # La primera versión decía "ya viene el regreso a clases", que es
        # información, no gancho: ella ya sabe que viene. Lo que de verdad le
        # pesa es estar marcando lápices con plumón a medianoche, y que aun
        # así todo se pierda. Se nombra eso, se le pone la escena, y hasta
        # entonces se ofrece.
        # OJO CON CÓMO SE DICE ESTO. La primera versión decía "nosotros se los
        # damos listos" justo después de hablar de los lápices, y se entendía
        # que Milen's entrega los útiles ya etiquetados. NO: se venden las
        # ETIQUETAS, ella las pega en sus propios útiles. Lo cachó Anuar el
        # 2026-08-06 antes de que saliera. Una clienta que llega esperando
        # lápices y recibe calcomanías es un pleito en la entrega y una
        # clienta menos.
        "¿Ya se vio marcando 40 lápices con plumón a las 11 de la noche? 😅\n\n"
        "Este año no. Le entregamos *las etiquetas ya impresas y cortadas con "
        "el nombre de su niño* — usted nomás las pega, y listo. Y lo que lleva "
        "nombre, no se pierde.\n\n"
        # LOS CUATRO PAQUETES SON DE ROCÍO, y su estructura es mejor que la de
        # un paquete parejo: una mamá de preescolar no necesita tablas de
        # multiplicar y una de primaria necesita el doble de etiquetas. Ella
        # conoce a la clienta (2026-08-06).
        #
        # Lo único que se emparejó: los 6 nombres para ropa valían $50 en
        # preescolar y $60 en primaria, siendo el mismo producto. Anuar lo
        # zanjó: **$55 en los dos**. Por eso #1 = #2 + $55, siempre.
        "🧸 *PREESCOLAR*\n"
        "  *$100* — 30 etiquetas para colores y lápices · 10 para libros y "
        "cuadernos\n"
        "  *$155* — todo lo anterior *+ 6 nombres para la ropa*\n\n"
        "🎒 *PRIMARIA*\n"
        "  *$150* — 45 etiquetas para colores y lápices · 30 para cuadernos y "
        "libros · *tabla de multiplicar enmicada*\n"
        "  *$205* — todo lo anterior *+ 6 nombres para la ropa*\n\n"
        "👕 *Los nombres para la ropa* van en vinil, listos para que usted los "
        "planche donde quiera. No son parches, no se sienten duros y aguantan "
        "lavada tras lavada.\n"
        "     _Colores: dorado, blanco, negro, rosa, verde y rojo_\n\n"
        # LAS DE 5×5 VAN DE PILÓN, no en la lista. Anuar lo definió el
        # 2026-08-06: son regalo para la clienta, aunque su costo ya esté
        # repartido dentro del precio del paquete. Metidas en la lista se leen
        # como relleno; dichas como pilón se sienten un detalle — y es lo que
        # hace que ella cuente el paquete como generoso.
        "🎁 *Y de pilón le van las grandotas de 5×5* — 6 en preescolar y 8 en "
        "primaria — para la lonchera, el termo y la mochila. Esas se ven de "
        "lejos y no hay forma de que se le pierdan.\n\n"
        # PERSONAJES CON NOMBRE, NO CATEGORÍAS. Anuar lo corrigió el
        # 2026-08-06: "carritos" es una categoría, *Goku* es una obsesión. La
        # mamá lee un nombre concreto y ve la cara de su hijo — y de paso se
        # entiende que aquí le hacen lo que el niño pida, no una lista fija.
        "📛 *Todas las etiquetas van ya cortadas*, solo se pegan. Y se las "
        "hacemos *con el personaje favorito de su niño*: Goku, Yu-Gi-Oh, "
        "Bluey, dinosaurios, unicornios, princesas, su equipo de futbol... "
        "el que él le diga 🐉⚽\n\n"
        "⚡ *Se lo entregamos al día siguiente* — mándelo hoy y mañana lo "
        "tiene.\n\n"
        "También personalizamos mochilas, loncheras, termos y cajas de "
        "colores ✨\n\n"
        # El cierre pide lo MÍNIMO: un nombre. No pide que decida, no pide que
        # pague, no pide que escoja paquete. Y la muestra hace el resto: ver
        # el nombre de su hijo con dinosaurios vende más que cualquier lista.
        "Solo mándeme el *nombre de su niño* y le paso una muestra de cómo "
        "quedaría 🙏 Sin compromiso.\n\n"
        "_Las clases ya casi empiezan y los pedidos se van juntando — entre "
        "antes me diga, mejor le acomodo la fecha._\n"
        # EL NÚMERO TIENE QUE SER EL MISMO QUE MANDA EL MENSAJE.
        # Salió desde el 3326148674 y en el texto decía "contácteme al
        # 3332386943": la señora recibe de un número y le dan otro, y eso en
        # una promoción se lee a spam. Anuar lo corrigió el 2026-08-06: va el
        # suyo, que además es donde AURORA está escuchando.
        "📲 3326148674"
    )


# En las órdenes a veces quedó apuntado el PRODUCTO en el lugar del nombre.
# Escribirle "Hola servilleteros" a una clienta real es peor que no saludarla
# por su nombre. Encontrado el 2026-08-06 revisando la lista antes de enviar.
_NO_SON_NOMBRES = ("servilleteros", "servilletero", "cliente", "varios",
                   "publico", "público", "mostrador", "sin nombre", "s/n")

# Nombres que quedaron mal escritos al capturar la orden. Es lo PRIMERO que
# lee la clienta: arrancar con su nombre mal puesto tira el mensaje entero.
_MAL_ESCRITOS = {"fernnanda": "Fernanda", "yesica": "Jessica",
                 "vannesa": "Vanessa", "jhoana": "Joana"}


def _nombre_de_persona(nombre: str):
    """El nombre listo para saludar, o None si eso no es una persona."""
    n = nombre.strip()
    if not n:
        return ""
    if n.lower() in _NO_SON_NOMBRES:
        return None
    primero = n.split()[0]
    corregido = _MAL_ESCRITOS.get(primero.lower())
    if corregido:
        return corregido
    # LAS MAYÚSCULAS SE ARREGLAN: en la base hay "ANA BELEN" y "CLAUDIA",
    # que gritados se ven a factura, no a mensaje de una persona.
    return n.title() if n.isupper() else n


def clientas() -> list:
    """Las que tienen teléfono. Sin teléfono no hay a quién escribirle."""
    if not BD.exists():
        return []
    con = sqlite3.connect(f"file:{BD}?mode=ro", uri=True)
    cols = [r[1] for r in con.execute("PRAGMA table_info(ordenes)")]
    c_nom = next((c for c in cols if "cliente" in c.lower()), None)
    c_tel = next((c for c in cols if "tel" in c.lower()), None)
    if not (c_nom and c_tel):
        con.close()
        return []
    vistos, salida = set(), []
    for nom, tel in con.execute(f"SELECT [{c_nom}], [{c_tel}] FROM ordenes"):
        t = "".join(ch for ch in str(tel or "") if ch.isdigit())
        if len(t) < 10 or t in vistos:
            continue
        # Nombres de prueba fuera: no se le escribe a "PruebaFlujo".
        if any(p in str(nom or "").lower() for p in ("prueba", "test", "demo")):
            continue
        vistos.add(t)
        limpio = _nombre_de_persona(str(nom or ""))
        # Si en la orden quedó apuntado el producto en vez de la clienta
        # —"servilleteros"— es mejor saludar sin nombre que llamarle así.
        if limpio is None:
            continue
        salida.append({"nombre": limpio, "telefono": t[-10:]})
    con.close()
    return salida


def enviar(tel10: str, texto: str) -> dict:
    """Envío REAL por Green API, el mismo que ya usa AURORA."""
    import os
    import requests
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    idi = os.getenv("GREEN_API_ID_INSTANCE") or os.getenv("GREEN_API_INSTANCE") or ""
    tok = os.getenv("GREEN_API_TOKEN") or os.getenv("GREEN_API_API_TOKEN") or ""
    pre = os.getenv("GREEN_API_SERVER") or "7107"
    if not (idi and tok):
        return {"status": "SIN_CREDENCIALES"}
    url = f"https://{pre}.api.greenapi.com/waInstance{idi}/sendMessage/{tok}"
    try:
        r = requests.post(url, json={"chatId": f"521{tel10}@c.us", "message": texto},
                          timeout=30)
        return {"status": "OK" if r.ok else "ERROR", "detalle": r.text[:150]}
    except Exception as e:
        return {"status": "ERROR", "detalle": f"{type(e).__name__}: {e}"}


def main() -> int:
    lista = clientas()
    de_verdad = "--enviar" in sys.argv

    print(f"Clientas con teléfono: {len(lista)}")
    print(f"Modo: {'ENVÍO REAL' if de_verdad else 'solo vista previa (no manda nada)'}")
    print("=" * 66)

    if not de_verdad:
        print("\nASÍ LES LLEGARÍA (ejemplo con la primera):\n")
        if lista:
            print(_plantilla(lista[0]["nombre"]))
        print("\n" + "=" * 66)
        print("A QUIÉNES:\n")
        for i, c in enumerate(lista, 1):
            print(f"  {i:2}. {c['nombre'][:28]:30} {c['telefono']}")
        print(f"\nPara enviar de verdad:  python {Path(__file__).name} --enviar")
        return 0

    ok = 0
    for i, c in enumerate(lista, 1):
        r = enviar(c["telefono"], _plantilla(c["nombre"]))
        marca = "OK " if r["status"] == "OK" else "FALLO"
        print(f"  [{i}/{len(lista)}] {marca} {c['nombre'][:24]:26} {c['telefono']}")
        if r["status"] == "OK":
            ok += 1
        if i < len(lista):
            time.sleep(SEGUNDOS_ENTRE_ENVIOS)
    print(f"\nEnviados: {ok} de {len(lista)}")
    return 0


if __name__ == "__main__":
    _consola_utf8()
    raise SystemExit(main())
