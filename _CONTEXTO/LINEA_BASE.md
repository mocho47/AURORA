# 📈 LINEA BASE — ETAPA 1 (llamadas Groq por mensaje)
Fecha: 2026-07-31  
Sesión medida: `auditoria-vivo`  
Método: POST reales a `http://127.0.0.1:5000/chat` + trazas `[ETAPA1_GROQ]` en `consciencia.py`

## Resultado por mensaje (medido en vivo)

| # | Mensaje | Tiempo endpoint | Llamadas Groq en `consciencia.py` | Rutas registradas | 429/retry |
|---|---|---:|---:|---|---|
| 1 | `busca fabricantes de mdf en guadalajara jalisco` | 28.3 s | 3 | `routing_llm` + `router_universal` + `ejecutar_motor(motor_analisis)` | No (en esas 3) |
| 2 | `ya abriste el archivo ...NO_EXISTE_12345.pdf en corel?` | 1.0 s | 2 | `routing_llm` + `router_universal` | No |
| 3 | `abre en corel el archivo ...README.md` | 0.5 s | 1 | `routing_llm` | No |
| 4 | `coreldrau vektoriza este archivo porfa` | 35.9 s | 3 | `routing_llm` + `router_universal` + `ejecutar_motor(motor_analisis)` | **Sí** (2 retries) |
| 5 | `oye podrias meter esto al corel porfa ...README.md` | 35.4 s | 3 | `routing_llm` + `router_universal` + `ejecutar_motor(motor_analisis)` | **Sí** (1 retry largo) |
| 6 | `tiene instalado el plugin laser?` | 0.5 s | 1 | `router_universal` | No |

## Hallazgo principal

- Sí hay mensajes que disparan **3 llamadas Groq** en el mismo turno.
- La latencia extrema coincide con retries por cuota en Groq:
  - `HTTP/1.1 429 Too Many Requests`
  - `Retrying request ... in 20s / 7s / 24s`

## Instrumentación usada (sugerencia incluida)

Se registró por llamada:
- `session_id`
- `ruta`
- `motor`
- `duracion_ms`
- `status` (200 / 429 / ERR)

Formato de log:
- `inicio`: `[ETAPA1_GROQ] inicio ...`
- `fin`: `[ETAPA1_GROQ] fin ...`

## Nota importante

Durante la misma ventana aparecieron algunas líneas `httpx ... 200 OK` sin prefijo `[ETAPA1_GROQ]`, lo que sugiere llamadas Groq fuera de los puntos instrumentados de `consciencia.py` (u otros módulos/clientes).
