# 🖥️ Mover Ollama a la Gateway
### Plan corto · pendiente del conector del cargador (Anuar lo genera 2026-08-04)

---

## Por qué, en una frase

La PC de Anuar tiene **8 GB soldados** (no se pueden ampliar) y trabaja al **99 %
de memoria**. El modelo local se come 724 MB y aun así tarda **111 segundos** en
responder. En otra máquina, dedicado solo a eso, sirve de verdad.

## Por qué Ollama y NO AURORA

Es la decisión que evita perder lo más usado:

> **Corel solo se controla desde la PC donde está instalado.**
> Si AURORA se mueve a la Gateway, se pierden todos los comandos de Corel.

| Máquina | Qué corre |
|---|---|
| **PC de Anuar** | AURORA + Corel, como hoy — pero sin Ollama comiéndole RAM |
| **Gateway** | Solo Ollama, sirviendo el modelo por WiFi |

AURORA le pega por red. Se gana en los dos lados: la PC recupera memoria, y el
respaldo local por fin responde rápido porque la Gateway no hace nada más.

---

## Los pasos

**1. Ver qué aguanta la Gateway** (en la propia Gateway):
```
systeminfo | findstr /C:"Memoria física total"
```
- **8 GB o más** → `llama3.2:3b` (el bueno para conversar)
- **4 GB** → `qwen2.5-coder:1.5b` (el chico, alcanza para respaldo)
- **Menos de 4 GB** → no vale la pena; mejor dejar AURORA sin respaldo local y
  que responda honesto cuando Groq no tenga cuota

**2. Instalar Ollama ahí** — `ollama.com/download`, y bajar el modelo:
```
ollama pull llama3.2:3b
```

**3. Que escuche en la red** (por defecto solo se oye a sí mismo).
En la Gateway, variable de entorno del sistema:
```
OLLAMA_HOST = 0.0.0.0:11434
```
Y reiniciar Ollama.

**4. Fijarle la IP en el router** (ZTE F689 de IZZI, `192.168.1.1`, user/user)
→ reserva DHCP. **Sin esto, la IP cambia y AURORA deja de encontrarla** — es
justo lo que ya pasa con el Google Home de la oficina.

**5. Apuntar AURORA allá.** En `CEREBRO/respaldo_local.py`:
```python
OLLAMA_URL = "http://192.168.1.XX:11434"     # la IP fija de la Gateway
SEGUNDOS_MAX_LOCAL = 60.0                    # ya puede esperar más: no compite por RAM
```

**6. Comprobar de verdad** desde la PC de Anuar:
```powershell
Invoke-WebRequest "http://192.168.1.XX:11434/api/tags" -UseBasicParsing
```
Si contesta con la lista de modelos, está listo.

**7. Desinstalar Ollama de la PC de Anuar** — o al menos dejarlo fuera del
arranque, que ya está hecho (su acceso está en `_ARRANQUE_DESACTIVADO`).

---

## Cómo se sabe si sirvió

Medir lo mismo que se midió hoy: pedirle algo simple al modelo y cronometrar.

| | |
|---|---|
| Hoy, en la PC de Anuar | **111.6 s** (modelo más chico, 0.8 GB libres) |
| Objetivo en la Gateway | **menos de 15 s** |

Si en la Gateway también pasa de 30 s, esa máquina tampoco alcanza y es mejor
saberlo que forzarlo.

---

## Lo que NO hay que hacer

- **No mover AURORA a la Gateway.** Pierde Corel, que es de lo que más se usa.
- **No dejar la IP en automático.** Cambia sola y el respaldo deja de funcionar.
- **No instalar modelos de 7B en una máquina de 8 GB.** El de 3B basta para
  respaldo; el de 7B la deja igual de trabada que la PC de ahora.

---

## Nota sobre la Chromebook

También se preguntó si AURORA cabe ahí. **No**: depende de CorelDRAW y de
`pywin32`, que son de Windows. Pero **no hace falta migrarla** — desde la
Chromebook se entra a AURORA por el navegador (`http://192.168.1.38:5000`),
igual que hace Rocío. La Chromebook es la pantalla; la PC hace el trabajo.
