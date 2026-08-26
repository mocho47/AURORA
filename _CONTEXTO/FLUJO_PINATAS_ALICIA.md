# Flujo real de las piñatas para Alicia — dictado por Anuar 2026-08-26

> Anotado tal como lo pidió. Esto NO es un plan aprobado: es la especificación
> del servicio + el estado real del código, para decidir qué se construye.

## Lo que él quiere que AURORA haga con UN solo pedido

Ejemplo de pedido: «cotiza/genera esta piñata para alicia [imagen] de 895 mm de alto»
(895 mm = 89.5 cm; él usa las dos unidades indistintamente).

1. Saber que su área de trabajo mide **130 x 90 cm**.
2. Calcular **solo** cuántos tabloides hacen falta. A 89.5 cm de alto son 3
   tabloides horizontales; si el tamaño es mayor, ajusta a los que se necesiten
   (6, los que sean) sin que él lo diga.
3. Si pide **"tamaño tabloide"**, ajustar la imagen a 1 tabloide **sin
   deformarla**, y seguir las mismas reglas.
4. Entregar **2 PDF** con la impresión a tamaño real, listos para mandar a
   maquilar, **con el traslape** para el ensamble de los tabloides y
   **respetando colores**.
5. Entregar **2 DXF que coincidan con esos PDF**:
   · **DXF 1 — silueta ranurada**, con **pestañas** para que no se despedace.
   · **DXF 2 — despiece**.

## Su flujo de taller (por qué lo quiere así)

Pega el **segundo PDF** en tabloides y corta el despiece con **papel adhesivo**.
Por eso los PDF y los DXF tienen que coincidir milímetro a milímetro: uno es lo
que se imprime, el otro es por dónde corta la máquina.

## Estado REAL del código (verificado el 2026-08-26, no de memoria)

| Pieza | Estado | Dónde |
|---|---|---|
| Cama del láser 1300x900 mm | ✅ existe, **desconectada** del cálculo | `CONFIG/maquinas.json` |
| Cuántos tabloides según el tamaño | ✅ funciona | `TALLER/produccion_piezas_grandes.py` |
| Escalar sin deformar (por alto o ancho) | ✅ funciona | idem |
| Traslape entre hojas (5 mm) | ✅ existe, **sale en DXF, no en PDF** | `TALLER/dividir_en_hojas.py` |
| Pestañas en el contorno | ✅ existe, **desconectada** de este flujo | `EDITOR/contorno_de_corte.py --pestanas N` |
| PDF a tamaño real para maquila | ❌ **no existe** | — |
| Silueta **ranurada** (crear ranuras) | ❌ **no existe** | `TALLER/adaptar_grosor.py` solo ajusta ranuras que el archivo YA trae |
| Despiece automático | ❌ **no** — un DXF de personaje trae curvas sueltas sin capas por prenda (RUMO: 126 curvas). Hay que clasificar a mano UNA vez por personaje | `produccion_piezas_grandes.py` lo declara |
| Que los 2 PDF y los 2 DXF coincidan | ❌ salen de caminos separados | — |

**3 de 9 funcionan · 2 existen pero desconectadas · 4 no existen.**

## Orden propuesto (por lo que le trae dinero más rápido)

1. **PDF a tamaño real con traslape** — es lo que manda a maquilar y hoy lo arma a mano.
2. **Silueta con pestañas conectada a ese PDF** — la pieza ya existe, falta enchufarla.
3. **Ranurado** — se genera sobre la silueta; es geometría, se puede.
4. **Despiece** — al final, con el paso manual declarado y no disimulado.

Pendiente: que Anuar confirme el orden.
