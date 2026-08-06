# -*- coding: utf-8 -*-
"""
AURORA · MOTOR COREL
Control real de CorelDRAW 2025 por COM (win32com). Se conecta a la instancia
que ya está abierta (o la abre si no hay ninguna) y opera sobre el documento
real. Honesto: si Corel no está instalado o falla la conexión, lo dice;
nunca simula un resultado.
"""
from __future__ import annotations
import functools
from pathlib import Path
from typing import Dict

_PROGID = "CorelDRAW.Application.26"


def _con_com(fn):
    """
    Inicializa el apartamento COM en el hilo actual antes de tocar Corel y lo
    libera al salir. Necesario porque estas funciones se llaman desde hilos
    del pool de asyncio.to_thread, que no traen COM inicializado — sin esto
    la llamada se cuelga en vez de fallar o responder.
    """
    @functools.wraps(fn)
    def envoltura(*args, **kwargs):
        import pythoncom
        pythoncom.CoInitialize()
        try:
            return fn(*args, **kwargs)
        finally:
            pythoncom.CoUninitialize()
    return envoltura


def _app():
    import win32com.client
    try:
        return win32com.client.gencache.EnsureDispatch(_PROGID)
    except Exception as e:
        raise RuntimeError(f"No se pudo conectar a CorelDRAW: {e}")


@_con_com
def disponible() -> bool:
    """True si CorelDRAW responde por COM ahora mismo."""
    try:
        _app()
        return True
    except Exception:
        return False


@_con_com
def info_documento() -> Dict:
    """Estado real del documento activo en Corel (solo lectura)."""
    try:
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        pg = doc.ActivePage
        return {
            "status": "ok",
            "nombre": doc.Name,
            "paginas": doc.Pages.Count,
            "ancho": round(pg.SizeWidth, 3),
            "alto": round(pg.SizeHeight, 3),
            "unidad": doc.Unit,
        }
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


@_con_com
def extraer_texto_documento() -> Dict:
    """
    Lee TODO el texto real de las formas de texto del documento activo,
    recorriendo todas las páginas y capas (incluye texto dentro de grupos).
    También cuenta las formas que no son texto (los "adornos": imágenes,
    rectángulos, elipses, curvas/líneas, otros) para dar un resumen real
    de qué más trae el diseño, sin inventar nada que no esté ahí.
    """
    try:
        import win32com.client
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        c = win32com.client.constants
        textos = []
        conteo_formas: Dict[str, int] = {}

        def _recorrer(shapes):
            for shp in shapes:
                try:
                    if shp.Type == c.cdrTextShape:
                        contenido = shp.Text.Story.Text
                        if contenido and contenido.strip():
                            textos.append(contenido.strip())
                        conteo_formas["texto"] = conteo_formas.get("texto", 0) + 1
                    elif shp.Type == c.cdrGroupShape:
                        _recorrer(shp.Shapes)
                    else:
                        etiqueta = {
                            getattr(c, "cdrBitmapShape", object()): "imagen",
                            getattr(c, "cdrRectangleShape", object()): "rectangulo",
                            getattr(c, "cdrEllipseShape", object()): "elipse",
                            getattr(c, "cdrCurveShape", object()): "curva/linea",
                        }.get(shp.Type, "otro")
                        conteo_formas[etiqueta] = conteo_formas.get(etiqueta, 0) + 1
                except Exception:
                    continue

        for pg in doc.Pages:
            for lyr in pg.Layers:
                _recorrer(lyr.Shapes)

        return {
            "status": "ok",
            "textos": textos,
            "total_bloques_texto": len(textos),
            "formas_no_texto": conteo_formas,
        }
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def exportar_pdf(ruta_salida: str) -> Dict:
    """
    Publica el documento activo a PDF en ruta_salida.
    Genera un archivo NUEVO — no modifica el documento original.
    Usa el perfil de PDF configurado por última vez en Corel (Corel no expone
    el DPI como parámetro directo de PublishToPDF; para forzar DPI exacto
    usar exportar_bitmap con formato raster).
    """
    try:
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        destino = Path(ruta_salida).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        doc.PublishToPDF(str(destino))
        if not destino.exists():
            return {"status": "error", "detalle": "Corel no generó el archivo (verificado en disco)."}
        return {"status": "ok", "ruta": str(destino),
                "kb": round(destino.stat().st_size / 1024, 1)}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def cerrar_a_curvas_y_publicar(ruta_salida: str = "") -> Dict:
    """Convierte TODO el texto a curvas y publica el PDF listo para maquila.

    Es lo primero que le rechazan a Anuar: *"wey, tu lona no pasa, las letras
    ciérralas a curvas"*. Si el texto sigue vivo y la maquila no tiene esa
    tipografía, se la cambia por otra y la lona sale con letras distintas.

    Él fue claro el 2026-08-05: *"no quiero que me diga eso, quiero que lo
    corrija"*. Decirle "aprieta Ctrl+Q" es devolverle el problema. Esto lo
    hace: es la ÚNICA forma real, porque desde el PDF ya no se puede — ahí el
    texto ya dejó de ser texto.

    EL ORIGINAL NO SE TOCA: se trabaja sobre una copia del documento, así que
    su .cdr sigue con el texto editable por si hay que corregir una palabra.
    """
    try:
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento",
                    "detalle": "No hay documento abierto en Corel."}

        nombre = getattr(doc, "Name", "documento") or "documento"
        destino = Path(ruta_salida).resolve() if ruta_salida else \
            Path.home() / "Downloads" / "pdf" / f"{Path(nombre).stem}_CURVAS.pdf"
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Se trabaja sobre un duplicado para no destruir su texto editable.
        # Corel no tiene "duplicar documento", así que se guarda una copia
        # temporal, se abre, y se convierte ahí.
        temporal = destino.parent / f"~{Path(nombre).stem}_curvas_tmp.cdr"
        doc.SaveAs(str(temporal))
        copia = app.OpenDocument(str(temporal))

        antes = 0
        try:
            # Se cuenta el texto ANTES para poder decir cuántos se convirtieron
            # de verdad, en vez de afirmar "listo" sin haber tocado nada.
            for pagina in copia.Pages:
                for forma in pagina.Shapes:
                    if getattr(forma, "Type", 0) == 6:      # 6 = cdrTextShape
                        antes += 1
        except Exception:
            antes = -1

        copia.ClearSelection()
        for pagina in copia.Pages:
            pagina.Activate()
            pagina.Shapes.All().ConvertToCurves()

        copia.PublishToPDF(str(destino))
        copia.Close()
        try:
            temporal.unlink()
        except OSError:
            pass

        if not destino.exists():
            return {"status": "error",
                    "detalle": "Corel no generó el PDF (verificado en disco)."}
        return {"status": "ok", "ruta": str(destino),
                "textos_convertidos": antes,
                "kb": round(destino.stat().st_size / 1024, 1),
                "original_intacto": True}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def exportar_bitmap(ruta_salida: str, dpi: int = 300, formato: str = "png") -> Dict:
    """
    Exporta el documento activo a PNG/JPG con el DPI exacto indicado.
    Genera un archivo NUEVO — no modifica el documento original.
    LIMITACION REAL CONOCIDA (2026-07-28, no resuelta): incompatibilidad de pywin32
    con este metodo especifico de Corel 2025 — puede fallar aunque el documento y
    Corel esten bien. Si falla, usa exportar_pdf() o exporta manual desde Corel.
    """
    try:
        import win32com.client
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        c = win32com.client.constants
        filtros = {"png": getattr(c, "cdrPNG", None), "jpg": getattr(c, "cdrJPEG", None),
                   "jpeg": getattr(c, "cdrJPEG", None)}
        filtro = filtros.get(formato.lower())
        if filtro is None:
            return {"status": "error", "detalle": f"Formato '{formato}' no soportado (usa png o jpg)."}
        destino = Path(ruta_salida).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        # LIMITACION REAL CONOCIDA, NO RESUELTA (encontrada en vivo 2026-07-28, lote
        # "Corel al 100%"): PaletteOptions/ExportArea son parametros COM VT_DISPATCH.
        # Pasar 0/entero -> TypeError de Python antes de llegar a Corel (peor: no
        # honesto, parece bug de codigo). Omitirlos -> el wrapper generado los
        # rellena con su propio default (0) y falla igual. Pasar None SI llega hasta
        # Corel de verdad, pero Corel a veces responde con una excepcion generica
        # (E_FAIL sin detalle) o, con contenido real en el documento, no truena pero
        # tampoco escribe el archivo — el chequeo de abajo (destino.exists()) atrapa
        # ese caso y lo reporta honesto, nunca finge éxito. No se encontró la causa
        # raíz exacta dentro de Corel esta noche; exportar_pdf() es la ruta que SÍ
        # funciona 100% verificada — úsala si el PNG/JPG exacto no es indispensable.
        doc.ExportBitmap(str(destino), filtro, 1, 4, 0, 0, dpi, dpi,
                          1, False, False, True, False, 0, None, None)
        if not destino.exists():
            return {"status": "error",
                    "detalle": "Corel no generó el archivo PNG/JPG (verificado en disco). "
                               "Limitación real conocida de exportar_bitmap — usa PDF si es posible."}
        return {"status": "ok", "ruta": str(destino),
                "kb": round(destino.stat().st_size / 1024, 1), "dpi": dpi}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def escalar_pagina(ancho_cm: float, alto_cm: float, en_documento_nuevo: bool = False) -> Dict:
    """
    Cambia el tamaño de página (cm) del documento activo.
    Si en_documento_nuevo=True, opera sobre un documento nuevo en blanco
    (útil para pruebas sin tocar el trabajo real que esté abierto).
    """
    try:
        import win32com.client
        app = _app()
        # Encontrado en vivo 2026-07-28 (lote "Corel al 100%"): pedir "escala a 20x30"
        # sin nada abierto en Corel fallaba con "sin_documento" — mismo hueco que ya
        # se había cerrado para agregar_imagen_documento_activo. en_documento_nuevo=True
        # sigue forzando un documento nuevo aunque haya uno activo (uso real: pruebas).
        doc = app.CreateDocument() if en_documento_nuevo else (app.ActiveDocument or app.CreateDocument())
        c = win32com.client.constants
        doc.Unit = c.cdrCentimeter
        pg = doc.ActivePage
        pg.SizeWidth = ancho_cm
        pg.SizeHeight = alto_cm
        return {"status": "ok", "ancho_cm": ancho_cm, "alto_cm": alto_cm,
                "documento_nuevo": en_documento_nuevo, "nombre": doc.Name}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def preparar_para_lona(ancho_m: float, alto_m: float, ruta_salida: str, dpi: int = 120) -> Dict:
    """
    Prepara el mismo diseño del documento activo para impresión de lona/banner:
    escala la página al tamaño real en metros (se ve de lejos, no necesita
    300dpi) y exporta a PNG a dpi bajo-medio (120 por default) para que el
    archivo sea manejable. Usa exportar_pdf() en vez de esta si el taller
    de impresión pide PDF en lugar de imagen.
    """
    try:
        import win32com.client
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        c = win32com.client.constants
        doc.Unit = c.cdrCentimeter
        pg = doc.ActivePage
        pg.SizeWidth = ancho_m * 100
        pg.SizeHeight = alto_m * 100

        filtros = {"png": getattr(c, "cdrPNG", None), "jpg": getattr(c, "cdrJPEG", None)}
        formato = Path(ruta_salida).suffix.lstrip(".").lower()
        filtro = filtros.get(formato, filtros["png"])
        destino = Path(ruta_salida).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        # LIMITACION REAL CONOCIDA, NO RESUELTA (ver nota identica en exportar_bitmap,
        # encontrada en vivo 2026-07-28, lote "Corel al 100%"): PaletteOptions/
        # ExportArea son VT_DISPATCH — None es lo unico que no truena en Python al
        # marshalling, pero a veces Corel no escribe el archivo igual. El chequeo de
        # abajo (con espera, por si es de verdad solo lentitud) lo atrapa honesto.
        doc.ExportBitmap(str(destino), filtro, 1, 4, 0, 0, dpi, dpi,
                          1, False, False, True, False, 0, None, None)
        # Imagenes de lona son grandes (varios megapixeles): Corel puede seguir
        # escribiendo el archivo un momento despues de que la llamada regresa.
        import time as _time
        for _ in range(20):
            if destino.exists() and destino.stat().st_size > 0:
                break
            _time.sleep(1)
        if not destino.exists():
            return {"status": "error",
                    "detalle": "Corel no generó el archivo (verificado en disco). "
                               "Limitación real conocida de exportar a PNG/JPG — usa exportar_pdf() si es posible."}
        return {"status": "ok", "ruta": str(destino), "kb": round(destino.stat().st_size / 1024, 1),
                "ancho_m": ancho_m, "alto_m": alto_m, "dpi": dpi}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def cerrar_documento_sin_guardar(nombre: str) -> Dict:
    """Cierra un documento por nombre SIN guardar (para limpiar documentos de prueba)."""
    try:
        app = _app()
        for d in app.Documents:
            if d.Name == nombre:
                d.Close()
                return {"status": "ok", "cerrado": nombre}
        return {"status": "no_encontrado", "detalle": f"'{nombre}' no está abierto."}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


@_con_com
def abrir_documento(ruta: str) -> Dict:
    """Abre un archivo REAL (PDF, CDR, AI, etc.) dentro de CorelDRAW (OpenDocument),
    a diferencia de abrirlo con el visor por default de Windows. Verifica que el
    archivo exista antes de intentarlo — nunca finge abrir algo que no está ahí."""
    try:
        origen = Path(ruta)
        if not origen.exists():
            return {"status": "no_encontrado", "detalle": f"No existe el archivo: {ruta}"}
        # Una CARPETA también pasa exists(). Caso real 2026-08-03: se pidió abrir
        # "...\Bart_simpson\Bart_simpson", que al descomprimir el .rar quedó como
        # carpeta anidada. Corel no la abrió, pero se leyó el documento activo
        # ("Sin título-1.cdr") y se reportó "✅ Abierto real" — una mentira.
        if origen.is_dir():
            dentro = [f.name for f in sorted(origen.iterdir())[:10]] if any(origen.iterdir()) else []
            return {"status": "es_carpeta", "carpeta": str(origen), "contiene": dentro,
                    "detalle": (f"Eso es una carpeta, no un archivo. "
                                + (f"Adentro hay: {', '.join(dentro)}" if dentro
                                   else "Y está vacía."))}
        app = _app()
        doc = app.OpenDocument(str(origen))
        if not doc:
            return {"status": "error", "detalle": "Corel no regresó un documento abierto."}
        # Corel puede devolver el documento que YA estaba activo si la apertura
        # falló. Se compara el nombre contra lo pedido: si no coincide, NO se
        # canta éxito. Esta es la diferencia entre informar y adivinar.
        abierto = str(doc.Name or "")
        if abierto and origen.stem.lower() not in abierto.lower():
            return {"status": "no_abrio", "esperado": origen.name, "activo": abierto,
                    "detalle": (f"Corel no abrió '{origen.name}'. El documento activo "
                                f"sigue siendo '{abierto}', así que no cuento esto como hecho.")}
        return {"status": "ok", "nombre": abierto, "paginas": doc.Pages.Count}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def guardar_copia(ruta_salida: str) -> Dict:
    """
    Guarda una COPIA del documento activo en ruta_salida (.cdr) sin tocar
    ni renombrar el archivo original abierto (SaveAsCopy, no rompe el vínculo).
    """
    try:
        app = _app()
        doc = app.ActiveDocument
        if not doc:
            return {"status": "sin_documento", "detalle": "No hay documento abierto en Corel."}
        destino = Path(ruta_salida).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        doc.SaveAsCopy(str(destino), None)
        if not destino.exists():
            return {"status": "error", "detalle": "Corel no generó la copia (verificado en disco)."}
        return {"status": "ok", "ruta": str(destino), "kb": round(destino.stat().st_size / 1024, 1)}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def agregar_imagen_documento_activo(ruta_imagen: str, enviar_atras: bool = False) -> Dict:
    """
    Importa una imagen REAL al documento activo de Corel — si no hay ninguno
    abierto, crea uno nuevo primero (mismo patrón que crear_planilla/preparar_
    para_lona). Antes fallaba con "sin_documento" si Corel no tenía nada
    abierto — encontrado en vivo 2026-07-27: pedir "abre esta imagen en Corel"
    desde cero (sin documento previo) no funcionaba. Si enviar_atras=True, la
    manda al fondo de la pila de capas (para ponerla detrás del logo).
    """
    try:
        app = _app()
        doc = app.ActiveDocument or app.CreateDocument()
        if not Path(ruta_imagen).exists():
            return {"status": "error", "detalle": f"No existe la imagen: {ruta_imagen}"}
        lyr = doc.ActiveLayer
        lyr.Import(str(ruta_imagen), 0, None)
        shape = lyr.Shapes.Item(1)
        if enviar_atras:
            shape.OrderToBack()
        return {"status": "ok", "forma": shape.Name, "enviada_atras": enviar_atras}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


def quitar_fondo_y_agregar(ruta_imagen: str, enviar_atras: bool = True) -> Dict:
    """
    Flujo real del splash: quita el fondo de la imagen (IA real, rembg) y
    el resultado lo importa al documento activo de Corel, mandándolo atrás
    del logo por default (igual que el flujo manual de Anuar).
    """
    import importlib.util as _ilu
    try:
        spec = _ilu.spec_from_file_location("conversiones", Path(__file__).parent / "conversiones.py")
        conv = _ilu.module_from_spec(spec); spec.loader.exec_module(conv)
        r_fondo = conv.quitar_fondo(ruta_imagen)
        if r_fondo.get("status") != "ok":
            return {"status": "error", "detalle": f"No se pudo quitar el fondo: {r_fondo}"}
    except Exception as e:
        return {"status": "error", "detalle": f"quitar_fondo fallo: {str(e)[:200]}"}

    r_import = agregar_imagen_documento_activo.__wrapped__(r_fondo["salida"], enviar_atras)
    if r_import.get("status") == "ok":
        r_import["imagen_sin_fondo"] = r_fondo["salida"]
    return r_import


@_con_com
def crear_planilla(ruta_pieza: str, ancho_hoja_cm: float, alto_hoja_cm: float,
                    ancho_pieza_cm: float, alto_pieza_cm: float,
                    ruta_salida_pdf: str, espacio_entre_piezas_cm: float = 0.2,
                    margen_hoja_cm: float = 0.5) -> Dict:
    """
    Arma una planilla real: repite ruta_pieza tantas veces como quepan en
    una hoja de ancho_hoja_cm x alto_hoja_cm, cada pieza a su tamaño real
    (ancho_pieza_cm x alto_pieza_cm — el tamaño del suaje), con espacio
    entre piezas para que el corte no se traslape. Exporta a PDF.
    """
    try:
        import win32com.client
        app = _app()
        if not Path(ruta_pieza).exists():
            return {"status": "error", "detalle": f"No existe la pieza: {ruta_pieza}"}

        doc = app.CreateDocument()
        c = win32com.client.constants
        doc.Unit = c.cdrCentimeter
        pg = doc.ActivePage
        pg.SizeWidth = ancho_hoja_cm
        pg.SizeHeight = alto_hoja_cm
        lyr = doc.ActiveLayer

        paso_x = ancho_pieza_cm + espacio_entre_piezas_cm
        paso_y = alto_pieza_cm + espacio_entre_piezas_cm
        ancho_util = ancho_hoja_cm - 2 * margen_hoja_cm
        alto_util = alto_hoja_cm - 2 * margen_hoja_cm
        columnas = max(int(ancho_util // paso_x), 0)
        filas = max(int(alto_util // paso_y), 0)
        if columnas == 0 or filas == 0:
            doc.Close()
            return {"status": "error",
                    "detalle": f"La pieza ({ancho_pieza_cm}x{alto_pieza_cm}cm) no cabe en la hoja ({ancho_hoja_cm}x{alto_hoja_cm}cm)."}

        # Importamos la pieza UNA sola vez y duplicamos (mucho mas rapido que
        # reimportar el archivo en cada casilla — igual que lo haria un diseñador real).
        lyr.Import(str(ruta_pieza), 0, None)
        original = lyr.Shapes.Item(1)
        original.SetSize(ancho_pieza_cm, alto_pieza_cm)
        x0 = margen_hoja_cm
        y0 = alto_hoja_cm - margen_hoja_cm - alto_pieza_cm
        original.SetPosition(x0, y0)

        total = 0
        for fila in range(filas):
            for col in range(columnas):
                x = margen_hoja_cm + col * paso_x
                y = alto_hoja_cm - margen_hoja_cm - alto_pieza_cm - fila * paso_y
                if col == 0 and fila == 0:
                    total += 1
                    continue  # ya es la original, no se duplica a si misma
                original.Duplicate(x - x0, y - y0)
                total += 1

        destino = Path(ruta_salida_pdf).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        doc.PublishToPDF(str(destino))
        doc.Close()

        if not destino.exists():
            return {"status": "error", "detalle": "Corel no genero el PDF de la planilla (verificado en disco)."}
        return {"status": "ok", "ruta": str(destino), "kb": round(destino.stat().st_size / 1024, 1),
                "piezas": total, "columnas": columnas, "filas": filas}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


def extraer_color_pixel(ruta_imagen: str, x: int, y: int) -> Dict:
    """
    Gotero real: lee el color exacto del pixel (x,y) de una imagen de
    referencia (ej. foto del envase). No usa Corel, solo lee la imagen.
    """
    try:
        from PIL import Image
        ruta = Path(ruta_imagen)
        if not ruta.exists():
            return {"status": "error", "detalle": f"No existe la imagen: {ruta_imagen}"}
        img = Image.open(ruta).convert("RGB")
        if not (0 <= x < img.width and 0 <= y < img.height):
            return {"status": "error",
                    "detalle": f"Pixel ({x},{y}) fuera de la imagen ({img.width}x{img.height})."}
        r, g, b = img.getpixel((x, y))
        return {"status": "ok", "r": r, "g": g, "b": b, "hex": f"#{r:02X}{g:02X}{b:02X}"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:200]}


@_con_com
def aplicar_color_seleccion(r: int, g: int, b: int) -> Dict:
    """
    Aplica un color RGB real a la forma actualmente SELECCIONADA en Corel
    (el mismo gesto que tú: seleccionas las letras, aplicas el tono).
    """
    try:
        app = _app()
        shape = app.ActiveShape
        if not shape:
            return {"status": "sin_seleccion", "detalle": "No hay ninguna forma seleccionada en Corel."}
        color = app.CreateRGBColor(r, g, b)
        shape.Fill.ApplyUniformFill(color)
        return {"status": "ok", "r": r, "g": g, "b": b, "forma": shape.Name}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


@_con_com
def extraer_y_aplicar_color(ruta_imagen: str, x: int, y: int) -> Dict:
    """
    Gotero completo: muestra el pixel (x,y) de ruta_imagen y lo aplica de
    una vez a la forma seleccionada en Corel. Combina las dos funciones
    de arriba en un solo paso para el flujo real del sticker.
    """
    muestra = extraer_color_pixel(ruta_imagen, x, y)
    if muestra.get("status") != "ok":
        return muestra
    return aplicar_color_seleccion.__wrapped__(muestra["r"], muestra["g"], muestra["b"])


@_con_com
def integrar_logo_fondo(ruta_fondo: str, ruta_logo: str, ruta_salida_pdf: str) -> Dict:
    """
    Crea un documento NUEVO, importa la imagen de fondo (ajustada al tamaño
    de página) y el logo encima (centrado), y exporta el resultado a PDF.
    No toca ningún documento que ya esté abierto en Corel.
    """
    try:
        app = _app()
        if not Path(ruta_fondo).exists():
            return {"status": "error", "detalle": f"No existe el fondo: {ruta_fondo}"}
        if not Path(ruta_logo).exists():
            return {"status": "error", "detalle": f"No existe el logo: {ruta_logo}"}

        doc = app.CreateDocument()
        lyr = doc.ActiveLayer

        # Fondo: importar y ajustar a la página completa
        lyr.Import(str(ruta_fondo), 0, None)
        fondo = lyr.Shapes.Item(1)
        pg = doc.ActivePage
        fondo.SetSize(pg.SizeWidth, pg.SizeHeight)
        fondo.SetPosition(0, 0)

        # Logo: importar y centrar sobre el fondo
        lyr.Import(str(ruta_logo), 0, None)
        logo = lyr.Shapes.Item(1)  # el ultimo importado queda seleccionado/al frente
        logo.CenterX = pg.SizeWidth / 2
        logo.CenterY = pg.SizeHeight / 2

        destino = Path(ruta_salida_pdf).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        doc.PublishToPDF(str(destino))
        doc.Close()

        if not destino.exists():
            return {"status": "error", "detalle": "Corel no generó el PDF final (verificado en disco)."}
        return {"status": "ok", "ruta": str(destino), "kb": round(destino.stat().st_size / 1024, 1)}
    except Exception as e:
        return {"status": "error", "detalle": str(e)[:250]}


# ── ¿QUÉ MACROS/PLUGINS TIENE COREL? ─────────────────────────────────────────
# Agregado 2026-08-02 por un caso real: Anuar preguntó "corel tiene instalado el
# plugin laser" y AURORA, que no tenía forma de saberlo, contestó un ensayo sobre
# plugins dando por hecho que sí estaba instalado. No era capacidad de más: era
# capacidad de MENOS. Los plugins de Corel son archivos .gms en carpetas
# conocidas, así que se pueden leer del disco SIN que Corel esté abierto.
_CARPETAS_GMS = (
    r"%APPDATA%\Corel",                                   # los que instala el usuario
    r"C:\Program Files\Corel",                            # los que trae Corel
    r"C:\Program Files (x86)\Corel",
)


def listar_plugins() -> Dict:
    """Lista las macros y plugins (.gms) instalados en CorelDRAW, leyendo el disco.

    No necesita que Corel esté abierto. Devuelve lo que hay de verdad: si no
    encuentra nada, lo dice — nunca supone que un plugin está instalado.
    """
    import os
    encontrados, carpetas = [], []
    for base in _CARPETAS_GMS:
        raiz = Path(os.path.expandvars(base))
        if not raiz.exists():
            continue
        try:
            for gms in raiz.rglob("*.gms"):
                try:
                    kb = round(gms.stat().st_size / 1024, 1)
                except OSError:
                    kb = 0
                encontrados.append({
                    "nombre": gms.stem,
                    "archivo": gms.name,
                    "kb": kb,
                    "de_fabrica": "Program Files" in str(gms),
                    "ruta": str(gms),
                })
                if str(gms.parent) not in carpetas:
                    carpetas.append(str(gms.parent))
        except OSError:
            continue

    # No todo lo que se integra con Corel es una macro .gms. Encontrado en vivo
    # el 2026-08-03: Anuar preguntó si tenía el plugin de láser, se buscaron solo
    # macros y se le respondió que NO — cuando RDWorks estaba instalado DENTRO de
    # la carpeta de Corel (`Corel\RDWorksV8\RDWorksV8.exe`), que es justo como se
    # integra. La respuesta era cierta para .gms y engañosa para él.
    for base in _CARPETAS_GMS:
        raiz = Path(os.path.expandvars(base))
        if not raiz.exists():
            continue
        try:
            for exe in raiz.rglob("*.exe"):
                nombre = exe.stem.lower()
                if any(k in nombre for k in ("rdwork", "lasercut", "lightburn",
                                             "laserwork", "rdcam", "printcut")):
                    if any(p["ruta"] == str(exe) for p in encontrados):
                        continue
                    try:
                        kb = round(exe.stat().st_size / 1024, 1)
                    except OSError:
                        kb = 0
                    encontrados.append({
                        "nombre": exe.stem,
                        "archivo": exe.name,
                        "kb": kb,
                        "de_fabrica": False,        # esto lo instaló el usuario
                        "tipo": "programa integrado",
                        "ruta": str(exe),
                    })
        except OSError:
            continue

    propios = [p for p in encontrados if not p["de_fabrica"]]
    return {
        "status": "OK",
        "total": len(encontrados),
        "de_fabrica": len(encontrados) - len(propios),
        "instalados_por_ti": len(propios),
        "plugins": sorted(encontrados, key=lambda p: (p["de_fabrica"], p["nombre"])),
        "carpetas": carpetas,
        "nota": ("Leído del disco, no de Corel — no hace falta tenerlo abierto. "
                 "Un plugin puede estar en disco y aun así no cargado en Corel; "
                 "eso se ve en Herramientas → Macros → Administrador de macros."),
    }


def tiene_plugin(nombre: str) -> Dict:
    """¿Está instalado un plugin/macro que se llame así? Responde con la verdad.

    Busca por coincidencia parcial e insensible a mayúsculas, porque nadie
    recuerda el nombre exacto del archivo.
    """
    todos = listar_plugins()
    if todos.get("status") != "OK":
        return todos
    busca = (nombre or "").strip().lower()
    if not busca:
        return {"status": "ERROR", "mensaje": "Dime qué plugin busco."}

    # Anuar pregunta por "el plugin de láser", no por "RDWorksV8". Nadie llama a
    # los programas por el nombre de su ejecutable. Sin esto se le respondió que
    # NO tenía plugin de láser, teniendo RDWorks instalado dentro de Corel
    # (2026-08-03) — cierto para el nombre del archivo, engañoso para él.
    _SINONIMOS = {
        "laser": ("rdwork", "lasercut", "lightburn", "laserwork", "rdcam"),
        "corte": ("rdwork", "lasercut", "lightburn", "printcut"),
        "grabado": ("rdwork", "lasercut", "lightburn"),
        "sublima": ("filecon", "colorchart"),
        "calendario": ("calendar",),
        "color": ("colorchart",),
        "curvas": ("converttocurves", "convertall"),
    }
    palabras = [busca] + list(_SINONIMOS.get(busca, ()))

    coinciden = [p for p in todos["plugins"]
                 # El desinstalador no es un plugin: confunde el conteo.
                 if not p["nombre"].lower().endswith("uninstall")
                 and any(w in p["nombre"].lower() for w in palabras)]
    return {
        "status": "OK",
        "buscado": nombre,
        "instalado": bool(coinciden),
        "coincidencias": coinciden,
        "total_revisados": todos["total"],
    }
