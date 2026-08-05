# 📊 Cobertura real de AURORA
### Medido el 2026-08-04 12:24 · muestra por carpeta

> Cada línea de aquí se mandó al chat **de verdad** y se miró a dónde
> llegó. No es una estimación.

## El número

| | |
|---|---|
| Herramientas en el registro | **537** |
| Probadas en este barrido | 81 |
| Llegan a su herramienta | **18** |
| Las atiende otro candado | 59 |
| **Se pierden** | **4** |
| Fallaron | 0 |
| **Cobertura** | **95.1%** |

*«Las atiende otro candado» no siempre es un error: pedir la
contabilidad y que responda el candado de negocio está bien.*

---

## ❌ Las 4 que se pierden

Son las que hay que conectar: la capacidad existe y no hay forma
de pedirla hablando.

| Herramienta | Se pidió así | Contestó |
|---|---|---|
| `AGENDA/agenda:actualizar_estado` | actualizar estado | No encontré cómo hacer eso todavía. Esto sí lo puedo hacer de verdad:  |
| `AUTH/identidad_core:estado` | quiero estado de usuarios | No puedo mostrar el estado de usuarios por ahora. Dime qué necesitas s |
| `MOTORES/adaptadores:MotorOracle.resumen` | quiero resumen | **Resumen del perfil del cliente actualizado**  **Intereses**: El clie |
| `ORACLE/oracle_core:crear_lead` | quiero crear lead de leads | No encontré cómo hacer eso todavía. Esto sí lo puedo hacer de verdad:  |

---

## ⏱️ Las 15 más lentas

| Segundos | Herramienta | Motor |
|---|---|---|
| 41.8 | `CEREBRO/acciones_sistema:copiar` | accion_sistema |
| 16.0 | `AUTH/identidad_core:estado` | motor_analisis |
| 15.5 | `CEREBRO/acciones_sistema:mover` | accion_sistema |
| 10.8 | `AGENDA/agenda:crear_cita` | agenda |
| 6.7 | `MOTORES/adaptadores:MotorOracle.resumen` | motor_analisis |
| 5.1 | `MOTORES_CUSTOM/medidor_dxf:obtener_estado_si` | router_universal |
| 4.2 | `INTEGRACIONES/email_integration:EmailIntegra` | router_universal |
| 3.8 | `SISTEMA/organizador_archivos:escanear` | router_universal |
| 3.7 | `SUBLIMACION/sublimacion_core:montar` | router_universal |
| 3.7 | `VENDEDOR/seguimiento_ventas:pendientes` | router_universal |
| 3.7 | `VENDEDOR/seguimiento_ventas:mensaje_sugerido` | router_universal |
| 3.7 | `WEB/web_real:contexto_para_llm` | router_universal |
| 3.5 | `MANUALES/aprendizaje:aprender` | web_search |
| 3.1 | `REDES/red_diagnostico:ping_perdida` | router_universal |
| 3.1 | `SISTEMA/optimizador:optimizar` | router_universal |

---

## Cómo se repite

```
python SETUP/barrido_cobertura.py            # muestra rápida
python SETUP/barrido_cobertura.py --todas    # las 535
python SETUP/barrido_cobertura.py --carpeta TALLER
```

Si la cobertura baja de una medición a otra, algo se rompió.
