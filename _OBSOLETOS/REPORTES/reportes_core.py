from CORE.db_connector import get_supabase_client
from datetime import datetime, timedelta

def generar_reporte_ventas(fecha_inicio: str, fecha_fin: str):
    """
    Obtiene un resumen de las ventas dentro de un rango de fechas.
    Las fechas deben estar en formato YYYY-MM-DD.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "ERROR", "detalle": "Sin conexión a la base de datos."}

    try:
        # Asegurarse de que el rango de fechas sea inclusivo para todo el día final
        fecha_fin_dt = datetime.fromisoformat(fecha_fin) + timedelta(days=1)
        fecha_fin_iso = fecha_fin_dt.isoformat()

        response = supabase.table('ventas').select(
            'id, monto_total, metodo_pago, estado_pedido, fecha_venta, vendedor_id, clientes(nombre, telefono)'
        ).gte(
            'fecha_venta', fecha_inicio
        ).lt(
            'fecha_venta', fecha_fin_iso
        ).order(
            'fecha_venta', desc=True
        ).execute()

        if response.data:
            total_ingresos = sum(item['monto_total'] for item in response.data)
            return {
                "status": "OK",
                "periodo": f"{fecha_inicio} al {fecha_fin}",
                "numero_ventas": len(response.data),
                "ingresos_totales": total_ingresos,
                "ventas": response.data
            }
        return {"status": "OK", "periodo": f"{fecha_inicio} al {fecha_fin}", "detalle": "No se encontraron ventas en este período."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}

def obtener_detalles_venta(venta_id: str):
    """
    Obtiene los productos específicos (detalles) de una venta por su ID.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "ERROR", "detalle": "Sin conexión a la base de datos."}
        
    try:
        response = supabase.table('detalles_venta').select(
            'cantidad, precio_unitario, productos(nombre, sku)'
        ).eq(
            'venta_id', venta_id
        ).execute()

        if response.data:
            return {"status": "OK", "venta_id": venta_id, "detalles": response.data}
        return {"status": "NO_ENCONTRADO", "detalle": f"No se encontraron detalles para la venta con ID '{venta_id}'."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}
