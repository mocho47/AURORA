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
            bbox = doc.modelspace().query('INSERT', (-float('inf'), -float('inf')), (float('inf'), float('inf')))
            if bbox:
                ancho = bbox[0].x - bbox[1].x
                alto = bbox[0].y - bbox[1].y
                return {"status": "ok", "ancho": ancho, "alto": alto}
            else:
                return {"status": "error", "mensaje": "no_se_encuentra_bbox"}
        except ezdxf.DXFError as e:
            return {"status": "error", "mensaje": "error_leer_archivo"}
        except Exception as e:
            return {"status": "error", "mensaje": "error_desconocido"}
    
    elif accion == "ayuda":
        return {"status": "ok", "mensaje": "Para medir un archivo DXF, proporciona la ruta del archivo en la clave 'ruta' en el cuerpo de la solicitud."}
    
    else:
        return {"status": "error", "mensaje": "acción_no_soportada"}

def obtener_bbox(doc):
    try:
        bbox = doc.modelspace().query('INSERT', (-float('inf'), -float('inf')), (float('inf'), float('inf')))
        return bbox
    except ezdxf.DXFError as e:
        return None

def calcular_ancho_alto(bbox):
    if bbox:
        ancho = bbox[0].x - bbox[1].x
        alto = bbox[0].y - bbox[1].y
        return ancho, alto
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