# archivo: conversor_mxn_a_usd.py

META = {"id": "conversor_mxn_a_usd", "nombre": "Conversor MXN a USD", "descripcion": "Convierte una cantidad de pesos MXN a dólares USD", "categoria": "Finanzas"}

def ejecutar(accion: str = "", datos: dict = None) -> dict:
    if accion != "convertir":
        return {"status": "error", "mensaje": "Accion no soportada"}
    
    if datos is None:
        datos = {}
    
    if "tc" not in datos or "monto" not in datos:
        return {"status": "error", "mensaje": "Faltan datos necesarios"}
    
    try:
        tc = float(datos["tc"])
        monto = float(datos["monto"])
        resultado = monto / tc
        return {"status": "ok", "resultado": resultado}
    except ValueError:
        return {"status": "error", "mensaje": "Error de conversión de datos"}

if __name__ == '__main__':
    datos = {"tc": 20.5, "monto": 1000}
    print(ejecutar("convertir", datos))