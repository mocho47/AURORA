# -*- coding: utf-8 -*-
"""
AURORA · VOZ — te escucha y te contesta hablando
================================================

DE DÓNDE SALE
-------------
No se inventó: se **portó** del sistema de voz de NEXUS que Anuar construyó y
quedó en el respaldo del USB Kingston (`voice_service.py` + `nexus_core.py`).
Estaba mejor pensado de lo que parecía y ya traía resuelto lo difícil.

Lo que se conservó tal cual, porque ya estaba bien:

* **Dos oídos, uno barato y uno bueno.** VOSK local vigila el nombre todo el día
  (gratis, sin internet, sin gastar cuota). Cuando lo oye, el comando completo lo
  transcribe **Whisper de Groq**, que entiende mucho mejor el español mexicano.
  Es el mismo patrón de Alexa y Siri.
* **Los alias del ruido.** Anuar ya había apuntado lo que el micrófono entiende
  mal con el compresor y el láser encendidos: *nesco, nescoilo, lexus, flexos*.
  Eso es oro de campo, no se tira.
* **Muting lógico.** Mientras habla, no escucha. Si no, se responde a sí misma.
* **Monitor de RAM.** Él ya lo tenía: si la memoria pasa del 90 %, avisa
  hablando. Justo el problema que tiene su PC hoy.

LO QUE SE AGREGÓ, Y POR QUÉ
---------------------------
1. **El nombre es configurable.** Antes estaba fijo en "nexus". Cada cliente va
   a querer el suyo, y el asistente de configuración inicial lo va a preguntar.
2. **Todo pasa por el mismo cerebro y el mismo candado.** La voz no habla con el
   modelo por su cuenta: manda el texto a `/chat`, igual que si lo escribieras.
   Así hereda el validador de honestidad. **Si no, AURORA podría mentir por voz,
   y por voz es peor: no queda por escrito.**
3. **Lo irreversible se confirma hablando.** Publicar, enviar o borrar te
   pregunta y espera un "sí" dicho en voz alta. Con las manos ocupadas no ves la
   pantalla — que es justo cuando usas la voz.

POR QUÉ IMPORTA
---------------
Anuar trabaja con las manos ocupadas: el láser, la prensa, montando un faro. El
chat lo obliga a soltar todo e ir a la PC. La voz no. Es muy probable que esta
sea su interfaz de verdad, y el chat la de la oficina.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("aurora.voz")

RAIZ = Path(__file__).resolve().parent.parent
MODELO_VOSK = RAIZ / "VOZ" / "modelo-vosk-es"
CONFIG_VOZ = RAIZ / "CONFIG" / "voz.json"

# ── Cómo se llama y qué contesta ─────────────────────────────────────────────
CONFIG_POR_DEFECTO = {
    "nombre": "aurora",
    # Lo que el micrófono entiende mal cuando hay ruido de taller. La lista de
    # "nexus" es de Anuar, de uso real; la de "aurora" es su equivalente.
    "alias": ["aurora", "aurorita", "ahora", "aurola", "aurora la", "au rora",
              "orora", "aurra", "arora"],
    "voz": "es-MX-JorgeNeural",      # hombre, mexicano
    "velocidad": "+10%",
    "confirmar_hablando": True,
    "avisar_ram": True,
}


def config() -> dict:
    """Lee la configuración de voz; si no hay, usa la de fábrica."""
    c = dict(CONFIG_POR_DEFECTO)
    try:
        if CONFIG_VOZ.exists():
            c.update(json.loads(CONFIG_VOZ.read_text(encoding="utf-8")))
    except Exception as e:
        logger.warning(f"No pude leer {CONFIG_VOZ.name}, uso la de fábrica: {e}")
    return c


# ── BOCA ─────────────────────────────────────────────────────────────────────
def hablar(texto: str, esperar: bool = True) -> bool:
    """Dice el texto en voz alta. Edge TTS primero (voz mexicana de verdad),
    y la voz de Windows si no hay internet."""
    if not texto or not texto.strip():
        return False
    c = config()
    limpio = _para_leer(texto)

    try:
        import asyncio
        import edge_tts
        import pygame

        salida = Path(tempfile.gettempdir()) / f"aurora_voz_{int(time.time()*1000)}.mp3"

        async def _generar():
            com = edge_tts.Communicate(limpio, c["voz"], rate=c.get("velocidad", "+0%"))
            await com.save(str(salida))

        asyncio.run(_generar())
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(salida))
        pygame.mixer.music.play()
        if esperar:
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            try:
                salida.unlink()
            except OSError:
                pass
        return True
    except Exception as e:
        logger.warning(f"Edge TTS no pudo ({str(e)[:70]}), uso la voz de Windows")

    try:
        import pyttsx3
        m = pyttsx3.init()
        m.setProperty("rate", 175)
        for v in m.getProperty("voices"):
            if "spanish" in v.name.lower() or "español" in v.name.lower() or "-MX" in v.id:
                m.setProperty("voice", v.id)
                break
        m.say(limpio)
        m.runAndWait()
        return True
    except Exception as e:
        logger.error(f"No pude hablar de ninguna forma: {e}")
        return False


def _para_leer(texto: str) -> str:
    """Quita lo que se ve bien escrito pero se oye horrible.

    Anuar, 2026-07-31: "regresa con la lectura de lo que ejecutará, puntos,
    comas, símbolos — eso no me interesa, además de escucharse tedioso y largo".
    """
    import re
    t = texto
    t = re.sub(r"```.*?```", " ", t, flags=re.S)          # bloques de código
    t = re.sub(r"[*_`#>|]+", " ", t)                       # markdown
    t = re.sub(r"[A-Za-z]:\\[^\s]+", "el archivo", t)      # rutas completas
    t = re.sub(r"\b[A-Z][A-Z_]{2,}/[\w.:]+", "esa herramienta", t)   # CARPETA/modulo
    t = re.sub(r"[•▪·]", ". ", t)
    t = re.sub(r"\s{2,}", " ", t)
    # Por voz, largo es insoportable. Se lee lo importante y se avisa.
    if len(t) > 700:
        t = t[:700].rsplit(".", 1)[0] + ". Te dejé el resto escrito en la pantalla."
    return t.strip()


# ── OÍDOS ────────────────────────────────────────────────────────────────────
def _oir_comando_whisper(segundos: int = 25) -> Optional[str]:
    """El comando completo, con Whisper de Groq: entiende el español mexicano
    mucho mejor que cualquier alternativa gratuita."""
    llave = os.environ.get("GROQ_API_KEY")
    if not llave:
        return _oir_comando_google(segundos)
    try:
        import speech_recognition as sr
        from groq import Groq

        r = sr.Recognizer()
        r.pause_threshold = 1.2      # deja respirar sin cortar la frase
        with sr.Microphone() as fuente:
            r.adjust_for_ambient_noise(fuente, duration=0.5)
            audio = r.listen(fuente, timeout=8, phrase_time_limit=segundos)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio.get_wav_data())
            ruta = tmp.name
        try:
            with open(ruta, "rb") as f:
                t = Groq(api_key=llave).audio.transcriptions.create(
                    file=(ruta, f.read()), model="whisper-large-v3",
                    language="es", temperature=0.0)
            return (t.text or "").strip()
        finally:
            try:
                os.remove(ruta)
            except OSError:
                pass
    except Exception as e:
        logger.warning(f"Whisper no pudo ({str(e)[:70]}), pruebo con Google")
        return _oir_comando_google(segundos)


def _oir_comando_google(segundos: int = 25) -> Optional[str]:
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.pause_threshold = 1.2
        with sr.Microphone() as fuente:
            r.adjust_for_ambient_noise(fuente, duration=0.5)
            audio = r.listen(fuente, timeout=8, phrase_time_limit=segundos)
        return r.recognize_google(audio, language="es-MX").strip()
    except Exception:
        return None


class ServicioVoz:
    """Escucha el nombre todo el día y, cuando lo oye, atiende.

    El nombre lo vigila VOSK en local: gratis, sin internet y sin gastar cuota.
    El comando lo transcribe Whisper, que es el bueno. Así se puede tener el
    micrófono encendido todo el día sin costo.
    """

    def __init__(self, al_recibir_comando: Callable[[str], str]):
        self.responder = al_recibir_comando      # función que procesa y devuelve texto
        self.corriendo = False
        self.hablando = False                    # muting lógico
        self._hilo: Optional[threading.Thread] = None
        self.cfg = config()
        self._ultimo_aviso_ram = 0.0

    # ── ¿es mi nombre? ──
    def _me_llaman(self, texto: str) -> bool:
        t = (texto or "").lower()
        return any(a in t for a in self.cfg["alias"])

    def _quitar_nombre(self, texto: str) -> str:
        t = (texto or "").lower()
        for a in sorted(self.cfg["alias"], key=len, reverse=True):
            if a in t:
                t = t.replace(a, " ", 1)
                break
        return t.strip(" ,.")

    def decir(self, texto: str) -> None:
        """Habla sin escucharse a sí misma."""
        self.hablando = True
        try:
            hablar(texto)
        finally:
            time.sleep(0.4)          # evita el eco del final
            self.hablando = False

    def _revisar_ram(self) -> None:
        """Aviso hablado si la PC se está ahogando. La idea es de Anuar y hoy es
        más útil que nunca: su PC tiene 8 GB soldados y trabaja al 99 %."""
        if not self.cfg.get("avisar_ram"):
            return
        if time.time() - self._ultimo_aviso_ram < 900:      # máximo cada 15 min
            return
        try:
            import psutil
            uso = psutil.virtual_memory().percent
            if uso > 92:
                self._ultimo_aviso_ram = time.time()
                self.decir(f"Oye, la memoria de la PC va al {int(uso)} por ciento. "
                           "Cierra algo o me voy a poner lenta.")
        except Exception:
            pass

    def _bucle(self) -> None:
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model
        except Exception as e:
            logger.error(f"No puedo escuchar, falta una librería: {e}")
            return
        if not MODELO_VOSK.exists():
            logger.error(f"No está el modelo de voz en {MODELO_VOSK}")
            return

        modelo = Model(str(MODELO_VOSK))
        rec = KaldiRecognizer(modelo, 16000)
        cola: "queue.Queue[bytes]" = queue.Queue()

        def entrada(datos, marcos, tiempo, estado):
            cola.put(bytes(datos))

        logger.info(f"Escuchando. Dime «{self.cfg['nombre']}» para empezar.")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                               channels=1, callback=entrada):
            while self.corriendo:
                try:
                    datos = cola.get(timeout=0.5)
                except queue.Empty:
                    self._revisar_ram()
                    continue

                # Mientras habla, no escucha: si no, se contesta sola.
                if self.hablando:
                    continue

                if not rec.AcceptWaveform(datos):
                    continue
                texto = (json.loads(rec.Result()).get("text") or "").strip()
                if not texto or not self._me_llaman(texto):
                    continue

                logger.info(f"Me llamaron: '{texto}'")
                resto = self._quitar_nombre(texto)

                # Si dijo el nombre y el comando de corrido, se atiende directo.
                comando = resto if len(resto.split()) >= 2 else None
                if not comando:
                    self.decir("Mande.")
                    comando = _oir_comando_whisper()

                if not comando:
                    self.decir("No te escuché bien, repítemelo.")
                    continue

                logger.info(f"Comando: '{comando}'")
                try:
                    # Va al MISMO cerebro que el chat: así hereda el candado de
                    # honestidad. La voz nunca habla con el modelo por su cuenta.
                    respuesta = self.responder(comando)
                except Exception as e:
                    logger.error(f"Falló al procesar: {e}")
                    respuesta = "Algo falló al procesarlo. No te invento el resultado."
                self.decir(respuesta or "Listo.")

    def arrancar(self) -> None:
        if self.corriendo:
            return
        self.corriendo = True
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self.corriendo = False
