# PLAN DE CIERRE DEL PROYECTO AURORA

**Fecha:** 27 de Junio de 2026
**Autor:** GitHub Copilot (Modelo: Gemini 2.5 Pro)
**Propósito:** Este documento sirve como una guía de traspaso completa para finalizar la integración del sistema AURORA con una base de datos en la nube (Supabase). Contiene el estado actual, los pasos restantes y el código necesario para que cualquier IA de programación avanzada o desarrollador pueda completar el proyecto.

---

### 1. Objetivo Final del Proyecto

Transformar AURORA de un sistema basado en archivos locales a una aplicación multiusuario profesional con una base de datos centralizada en la nube. Esto permitirá que múltiples usuarios (ej. el usuario principal y su esposa) puedan registrar y consultar datos de ventas y clientes en tiempo real desde diferentes ordenadores.

---

### 2. Arquitectura y Estado Actual

- **Backend:** `aurora_unified_main.py` (FastAPI) actúa como el servidor central.
- **Base de Datos:** Se ha elegido **Supabase** como proveedor de base de datos en la nube (PostgreSQL).
- **Módulos:** La lógica de negocio está encapsulada en directorios (`VENDEDOR`, `REPORTES`, etc.).
- **Credenciales:** La URL y la clave `anon` de Supabase ya han sido añadidas al archivo `.env`.
- **Conexión a BD:** Se ha creado el archivo `CORE/db_connector.py`, que gestiona la conexión a Supabase.
- **Estructura de BD:** El usuario ha ejecutado el script SQL para crear las tablas `clientes`, `productos`, `ventas` y `detalles_venta` en Supabase.
- **Dependencias:** La librería `supabase-py` ha sido instalada en el entorno virtual.

**El sistema está listo para la refactorización del código.**

---

### 3. Pasos Restantes para la Finalización

La tarea principal es modificar los módulos que actualmente leen/escriben en archivos locales para que, en su lugar, interactúen con la base de datos de Supabase.

#### **Paso 3.1: Refactorizar el Módulo `VENDEDOR/vendedor_core.py`**

**Análisis:**
El archivo `VENDEDOR/vendedor_core.py` actualmente gestiona un catálogo de productos leyendo y escribiendo en un archivo local: `C:\AURORA\CONFIG\fichas_tecnicas.json`. Las funciones clave son `_cargar`, `listar_fichas`, `ficha` y `guardar_ficha`.

**Acción Requerida:**
Modificar estas funciones para que realicen operaciones `CRUD` (Crear, Leer, Actualizar, Borrar) en la tabla `productos` de Supabase.

**Instrucciones y Código de Ejemplo:**

1.  **Importar el conector de la base de datos:**
    Añadir al principio de `VENDEDOR/vendedor_core.py`:
    ```python
    from CORE.db_connector import get_supabase_client
    supabase = get_supabase_client()
    ```

2.  **Reemplazar `listar_fichas`:**
    La nueva función debe consultar la tabla `productos`.

    *Código de Reemplazo:*
    ```python
    def listar_fichas_db():
        """Lista los productos desde la base de datos Supabase."""
        try:
            response = supabase.table('productos').select('sku', 'nombre', 'precio').execute()
            if response.data:
                return {"status": "OK", "total": len(response.data), "equipos": response.data}
            return {"status": "OK", "total": 0, "equipos": []}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)}
    ```

3.  **Reemplazar `ficha`:**
    La nueva función debe buscar un producto por `sku` o `nombre`.

    *Código de Reemplazo:*
    ```python
    def ficha_db(producto_sku: str):
        """Devuelve la ficha de un producto desde la base de datos."""
        try:
            # Buscar por SKU (idealmente)
            response = supabase.table('productos').select('*').eq('sku', producto_sku).execute()
            if response.data:
                return {"status": "OK", "ficha": response.data[0]}
            return {"status": "NO_ENCONTRADO", "detalle": f"No se encontró el producto con SKU '{producto_sku}'."}
        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)}
    ```

4.  **Reemplazar `guardar_ficha` con `registrar_venta`:**
    Esta es la función más crítica. Debe registrar una nueva venta, sus detalles y el cliente en la base de datos.

    *Código de Reemplazo (Nueva Función):*
    ```python
    def registrar_venta_db(datos_venta: dict):
        """
        Registra una venta completa en la base de datos.
        'datos_venta' debe contener:
        {
            "cliente": {"nombre": "John Doe", "telefono": "555-1234"},
            "productos": [{"producto_id": "UUID_DEL_PRODUCTO", "cantidad": 1, "precio_unitario": 150.00}],
            "monto_total": 150.00,
            "metodo_pago": "Tarjeta",
            "vendedor_id": "nombre_vendedor"
        }
        """
        try:
            # 1. Crear o encontrar al cliente
            cliente_data = datos_venta['cliente']
            cliente, error = supabase.table('clientes').upsert(cliente_data, on_conflict='telefono').execute()
            if error:
                raise Exception(f"Error al guardar cliente: {error}")
            
            cliente_id = cliente.data[0]['id']

            # 2. Crear la venta
            venta_info = {
                "cliente_id": cliente_id,
                "monto_total": datos_venta['monto_total'],
                "metodo_pago": datos_venta['metodo_pago'],
                "vendedor_id": datos_venta.get('vendedor_id', 'No especificado')
            }
            venta, error = supabase.table('ventas').insert(venta_info).execute()
            if error:
                raise Exception(f"Error al crear venta: {error}")

            venta_id = venta.data[0]['id']

            # 3. Registrar los detalles de la venta
            detalles_para_insertar = []
            for item in datos_venta['productos']:
                detalles_para_insertar.append({
                    "venta_id": venta_id,
                    "producto_id": item['producto_id'],
                    "cantidad": item['cantidad'],
                    "precio_unitario": item['precio_unitario']
                })
            
            detalles, error = supabase.table('detalles_venta').insert(detalles_para_insertar).execute()
            if error:
                raise Exception(f"Error al guardar detalles: {error}")

            return {"status": "OK", "venta_id": venta_id, "detalle": "Venta registrada exitosamente."}

        except Exception as e:
            return {"status": "ERROR", "detalle": str(e)}
    ```

#### **Paso 3.2: Crear el Módulo `REPORTES/reportes_core.py`**

**Análisis:**
La carpeta `REPORTES` no tiene un `_core.py`, por lo que debemos crearlo. Este módulo contendrá funciones para generar informes consultando la base de datos.

**Acción Requerida:**
Crear el archivo `REPORTES/reportes_core.py` e implementar funciones de consulta.

**Instrucciones y Código de Ejemplo:**

*Contenido para `REPORTES/reportes_core.py`:*
```python
from CORE.db_connector import get_supabase_client

supabase = get_supabase_client()

def generar_reporte_ventas_diario():
    """Obtiene un resumen de las ventas del día actual."""
    try:
        # Supabase usa funciones de PostgreSQL, 'now()' y 'interval'
        response = supabase.table('ventas').select('id', 'monto_total', 'fecha_venta').gte('fecha_venta', 'now()::date').execute()
        
        if response.data:
            total_ventas = sum(item['monto_total'] for item in response.data)
            return {
                "status": "OK",
                "fecha_reporte": "hoy",
                "numero_ventas": len(response.data),
                "ingresos_totales": total_ventas,
                "ventas": response.data
            }
        return {"status": "OK", "detalle": "No se encontraron ventas para el día de hoy."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}

def reporte_por_vendedor(vendedor_id: str):
    """Obtiene las ventas realizadas por un vendedor específico."""
    try:
        response = supabase.table('ventas').select('*').eq('vendedor_id', vendedor_id).execute()
        if response.data:
            return {"status": "OK", "vendedor": vendedor_id, "ventas": response.data}
        return {"status": "NO_ENCONTRADO", "detalle": f"No se encontraron ventas para '{vendedor_id}'."}
    except Exception as e:
        return {"status": "ERROR", "detalle": str(e)}
```

#### **Paso 3.3: Integrar en `aurora_unified_main.py`**

**Acción Requerida:**
Añadir los nuevos endpoints para las funciones de base de datos en el archivo principal.

*Ejemplo de nuevos endpoints:*
```python
# En aurora_unified_main.py

# ... (importaciones existentes)
from VENDEDOR.vendedor_core import registrar_venta_db
from REPORTES.reportes_core import generar_reporte_ventas_diario

# ... (app = FastAPI())

@app.post("/ventas/registrar", tags=["Ventas DB"])
async def api_registrar_venta(datos_venta: dict):
    return registrar_venta_db(datos_venta)

@app.get("/reportes/ventas_hoy", tags=["Reportes DB"])
async def api_reporte_hoy():
    return generar_reporte_ventas_diario()
```

---

### 4. Compilación e Instalación Final

Una vez que el código ha sido refactorizado y probado:

1.  **Generar el Ejecutable Final:**
    Ejecutar el mismo comando de `pyinstaller` usado anteriormente para crear el nuevo `aurora_unified_main.exe`.
    ```bash
    pyinstaller --name aurora_unified_main --onefile --console --add-data "PROMPTS_MAESTROS;PROMPTS_MAESTROS" --hidden-import "PIL._tkinter_finder" aurora_unified_main.py
    ```

2.  **Ejecutar el Instalador:**
    Ejecutar el script `instalar_aurora_produccion.ps1`. Este copiará el nuevo ejecutable y configurará los accesos directos en el escritorio.
    ```powershell
    powershell.exe -ExecutionPolicy Bypass -File "C:\AURORA\instalar_aurora_produccion.ps1"
    ```

3.  **Distribuir:**
    Copiar la carpeta `C:\AURORA_PRODUCCION` al ordenador del otro usuario. El sistema funcionará de inmediato, ya que se conecta a la misma base de datos central.

---
**Fin del Documento de Traspaso.**
Con esta guía, el proyecto puede ser completado de manera exitosa.