# `escribir_motores_reales.py` — archivado el 2026-08-26

Era el script que **creó** los 9 motores de AURORA la primera vez. Guarda una
copia congelada del código de cada uno tal como estaba ese día.

**Por qué se saca de `SETUP/`:** correrlo hoy no "repara" los motores — los
**sobrescribe** con la versión vieja y borra de un golpe cada arreglo hecho
desde entonces. Entre otras cosas devolvería los precios equivocados que se
quitaron hoy del cotizador (Aozoom X1 en $8,000 cuando el catálogo real dice
$3,149) y la tabla de precios de ATF copiada dentro de `motor_ventas` y
`motor_negocios`.

Nadie lo llama: se buscó en todo el proyecto (.py, .bat, .ps1, .md, .json) y no
aparece una sola referencia. Se conserva aquí por historia, no para usarse.

Los motores de verdad viven en `MOTORES/`. Los precios de verdad viven en
`CONFIG/catalogo_atf.json` y en el catálogo de servicios — en un solo lugar.
