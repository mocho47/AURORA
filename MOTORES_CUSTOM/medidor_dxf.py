import os
import ezdxf
import requests
import json
import sqlite3
import psutil
import fitz
import vtracer
import ddgs
import rembg
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
from groq import Groq

META = {"id": "medidor_dxf", "nombre": "Medidor DXF", "descripcion": "Medidor de ancho y alto de archivos DXF", "categoria": "Medición"}

import ezdxf.bbox

# Fase 3 (2026-07-28), encontrado en vivo con un DXF real (rectangulo 10x5):
# .query('INSERT', punto, punto) NO es la API real de ezdxf — query() solo filtra
# por tipo de entidad, no acepta coordenadas de bounding box, y ademas solo
# buscaba entidades tipo INSERT (bloques), ignorando lineas/polilineas/circulos
# reales. Siempre fallaba y el except generico lo escondia como "error_desconocido".
# Arreglado con la API real de medicion de ezdxf (ezdxf.bbox.extents), que mide
# TODA la geometria del dibujo, no solo bloques.

def ejecutar(accion: str = "", datos: dict = None) -> dict:
    if accion == "":
        accion = "medir"

    if accion == "medir":
        if not datos or "ruta" not in datos or not datos["ruta"]:
            return {"status": "error", "mensaje": "ruta_vacia"}

        ruta = datos["ruta"]
        if not os.path.exists(ruta):
            return {"status": "error", "mensaje": "ruta_no_encontrada"}

        try:
            doc = ezdxf.readfile(ruta)
            caja = ezdxf.bbox.extents(doc.modelspace())
            if not caja.has_data:
                return {"status": "error", "mensaje": "dxf_sin_geometria (el archivo abre pero no tiene nada dibujado)"}
            ancho = caja.extmax.x - caja.extmin.x
            alto = caja.extmax.y - caja.extmin.y
            return {"status": "ok", "ancho": round(ancho, 3), "alto": round(alto, 3)}
        except ezdxf.DXFError as e:
            return {"status": "error", "mensaje": f"error_leer_archivo: {str(e)[:150]}"}
        except Exception as e:
            return {"status": "error", "mensaje": f"error_desconocido: {str(e)[:150]}"}

    elif accion == "ayuda":
        return {"status": "ok", "mensaje": "Para medir un archivo DXF, proporciona la ruta del archivo en la clave 'ruta' en el cuerpo de la solicitud."}

    else:
        return {"status": "error", "mensaje": "acción_no_soportada"}

def obtener_bbox(doc):
    try:
        return ezdxf.bbox.extents(doc.modelspace())
    except Exception:
        return None

def calcular_ancho_alto(bbox):
    if bbox is not None and bbox.has_data:
        ancho = bbox.extmax.x - bbox.extmin.x
        alto = bbox.extmax.y - bbox.extmin.y
        return round(ancho, 3), round(alto, 3)
    else:
        return None, None

def obtener_estado_sistema():
    try:
        estado = psutil.virtual_memory()
        return {"status": "ok", "mensaje": f"Memoria disponible: {estado.available / (1024 * 1024)} MB"}
    except Exception as e:
        return {"status": "error", "mensaje": "error_obtener_estado_sistema"}

if __name__ == '__main__':
    datos = {"ruta": "ruta_del_archivo_dxf.dxf"}
    resultado = ejecutar("medir", datos)
    print(resultado)
    
    resultado_estado_sistema = obtener_estado_sistema()
    print(resultado_estado_sistema)