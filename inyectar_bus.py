# -*- coding: utf-8 -*-
import sys
import os
import asyncio

sys.path.append(os.path.abspath('C:\\AURORA.worktrees'))

print('🚀 [NEXUS -> AURORA] Transmitiendo Mensaje al Bus Neuronal...')

try:
    # Cargamos el bus y la clase Mensaje/TipoMensaje nativa para armar el paquete exacto
    from CEREBRO.bus_neuronal import bus, Mensaje, TipoMensaje
    print('✅ Entidades del Bus cargadas con éxito.')
except ImportError:
    # Si TipoMensaje o Mensaje se manejan como diccionarios, usaremos fallback
    from CEREBRO.bus_neuronal import bus
    Mensaje = None
    print('✅ Instancia de Bus cargada (modo diccionario).')

async def enviar_lead_adaptado():
    # Estructura de contenido base
    datos_taller = {
        'texto': 'Registrar cliente Carlos Mendoza, telefono 5511223344, interesado en un servicio de Kit Retrofit por un valor de 5000 pesos.',
        'origen': 'mic_taller'
    }

    try:
        fn_publicar = getattr(bus, 'publicar')
        
        # INTENTO A: Si el sistema exige la clase Mensaje formal del Bus
        if Mensaje is not None:
            print('🧠 [Intento A] Construyendo objeto de clase Mensaje...')
            try:
                # Instanciamos el Mensaje pasando el contenido según firmas estándar
                msg_objeto = Mensaje(tipo="EVENTO_TALLER", contenido=datos_taller)
            except TypeError:
                try:
                    # Alternativa por si los campos se llaman diferente (ej. texto/origen)
                    msg_objeto = Mensaje(texto=datos_taller['texto'], origen=datos_taller['origen'])
                except Exception:
                    msg_objeto = None
            
            if msg_objeto is not None:
                if asyncio.iscoroutinefunction(fn_publicar):
                    await fn_publicar(msg_objeto)
                else:
                    fn_publicar(msg_objeto)
                print('✅ [Intento A] Mensaje estructurado inyectado con éxito.')
                return

        # INTENTO B: Enviar un diccionario único con el tipo embebido (Fallback universal)
        print('🧠 [Intento B] Enviando diccionario empaquetado único...')
        payload_unico = {
            'tipo': 'EVENTO_TALLER',
            'texto': datos_taller['texto'],
            'origen': datos_taller['origen']
        }
        
        if asyncio.iscoroutinefunction(fn_publicar):
            await fn_publicar(payload_unico)
        else:
            fn_publicar(payload_unico)
        print('✅ [Intento B] Diccionario inyectado con éxito.')

    except Exception as e:
        print(f'❌ Fallo en la transmisión adaptada: {e}')

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enviar_lead_adaptado())
