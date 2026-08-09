import os
import sys
import time
import asyncio
import threading
import logging
import wave
from typing import Optional, Callable, Union

import speech_recognition as sr
from normalizador_comandos import normalizar_comando
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import whisper as _whisper

try:
    import whisper
except Exception:
    whisper = None

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


class VoiceController:
    def __init__(
        self,
        command_callback: Optional[Callable[[str], Union[None, asyncio.Future]]] = None,
        wake_words: Optional[list] = None,
        model_name: str = "tiny",
        language: str = "es",
        phrase_time_limit: float = 4.0,
        timeout: float = 4.0,
        mic_index: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ):
        self.base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.temp_dir = os.path.join(self.base_dir, "temp")
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self.log = logging.getLogger("voice")
        if not self.log.handlers:
            self.log.setLevel(logging.INFO)
            fh = logging.FileHandler(os.path.join(self.logs_dir, "voice.log"), encoding="utf-8")
            fmt = logging.Formatter("%(asctime)s [DIAG] %(levelname)s %(message)s")
            fh.setFormatter(fmt)
            self.log.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            self.log.addHandler(ch)

        self.command_callback = command_callback
        self.wake_words = wake_words or ["nexus", "nexus escucha", "ion", "ion nexus"]
        self.model_name = os.getenv("WHISPER_MODEL", model_name)
        self.language = language
        self.phrase_time_limit = phrase_time_limit
        self.timeout = timeout
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._recognizer = sr.Recognizer()
        self._mic_index = self._auto_detect_mic_index(mic_index)
        self._wake_mode = False
        self._wake_until = 0.0
        self._active = False
        self._model = None
        self._model_attempted = False
        self._metrics = {
            "wake_detected": 0,
            "wake_responses": 0,
            "commands_received": 0,
            "commands_executed": 0,
            "command_errors": 0,
            "stt_calls": 0,
            "stt_success": 0,
            "stt_empty": 0,
            "short_phrases": 0,
            "normalized_changed": 0,
        }

    def _candidate_mics(self) -> list:
        try:
            names = sr.Microphone.list_microphone_names() or []
        except Exception:
            names = []
        cands = []
        for i, n in enumerate(names):
            ln = (n or "").lower()
            score = 0
            if "este micro" in ln:
                score += 4
            if "micro" in ln:
                score += 3
            if "realtek" in ln:
                score += 2
            if "digital" in ln:
                score += 1
            if "mapper" in ln or "asignador" in ln:
                score -= 3
            cands.append((score, i))
        cands.sort(key=lambda x: (-x[0], x[1]))
        return [i for _, i in cands]

    def _narrate(self, text: str):
        if not text or pyttsx3 is None:
            return
        def run():
            try:
                e = pyttsx3.init()
                e.setProperty('rate', 170)
                try:
                    voices = e.getProperty('voices') or []
                    target = None
                    for v in voices:
                        nid = getattr(v, 'id', '') or ''
                        name = getattr(v, 'name', '') or ''
                        lang = ','.join(getattr(v, 'languages', []) or [])
                        if ('es' in nid.lower()) or ('es' in name.lower()) or ('es' in lang.lower()) or ('spanish' in name.lower()):
                            target = v.id
                            break
                    if target:
                        e.setProperty('voice', target)
                except Exception:
                    pass
                e.say(text)
                e.runAndWait()
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    def _verify_microphone(self, mic_id: Optional[int]) -> bool:
        try:
            if sd is None:
                return True
            if mic_id is None:
                return True
            devices = sd.query_devices()
            if mic_id < 0 or mic_id >= len(devices):
                self.log.info("Error al verificar micrófono: ID fuera de rango")
                return False
            name = devices[mic_id].get("name") or ""
            self.log.info(f"Micrófono detectado: {name} (ID {mic_id})")
            return True
        except Exception as e:
            self.log.info(f"Error al verificar micrófono: {e}")
            return False

    def _pick_source_params(self) -> Optional[tuple]:
        indices = []
        if self._mic_index is not None:
            indices.append(self._mic_index)
        for i in self._candidate_mics():
            if i not in indices:
                indices.append(i)
        indices.append(None)
        rates = [self.sample_rate, None, 16000, 44100, 48000]
        for idx in indices:
            for rate in rates:
                try:
                    if rate is None:
                        with sr.Microphone(device_index=idx, chunk_size=self.chunk_size) as s:
                            pass
                    else:
                        with sr.Microphone(device_index=idx, sample_rate=rate, chunk_size=self.chunk_size) as s:
                            pass
                    if rate:
                        self.sample_rate = rate
                    return (idx, rate)
                except Exception:
                    continue
        return None

    def _auto_detect_mic_index(self, override: Optional[int]) -> Optional[int]:
        if override is not None:
            self.log.info(f"Mic index forzado: {override}")
            return override
        env_idx = os.getenv("ION_MIC_INDEX")
        if env_idx:
            try:
                idx = int(env_idx)
                self.log.info(f"Mic por env: {idx}")
                return idx
            except Exception:
                self.log.info("ION_MIC_INDEX inválido")
        try:
            names = sr.Microphone.list_microphone_names() or []
        except Exception as e:
            self.log.info(f"Lista mic fallida: {e}")
            names = []
        self.log.info(f"Mic detectados: {names}")
        for i, n in enumerate(names):
            if n and ("realtek" in n.lower() or "usb" in n.lower() or "micro" in n.lower()):
                self.log.info(f"Mic auto: {i} {n}")
                return i
        self.log.info("Mic por defecto")
        return None

    def _ensure_model(self):
        if self._model is not None:
            return
        if whisper is None or self._model_attempted:
            self.log.info("Whisper no disponible")
            return
        try:
            self._model = whisper.load_model(self.model_name, device="cpu")
            self.log.info(f"Modelo Whisper: {self.model_name}")
        except Exception as e:
            self.log.info(f"Carga modelo fallida: {e}")
            self._model = None
            self._model_attempted = True

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._listen_loop, name="listen_loop", daemon=True)
        self._thread.start()

    async def astart(self):
        self.start()

    def stop(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def diagnostics(self) -> dict:
        try:
            names = sr.Microphone.list_microphone_names() or []
        except Exception:
            names = []
        return {
            "mic_names": names,
            "mic_index": self._mic_index,
            "thread_alive": bool(self._thread and self._thread.is_alive()),
            "active": self._active,
            "wake_mode": self._wake_mode,
            "wake_until": self._wake_until,
            "model": self.model_name,
            "temp_dir": self.temp_dir,
        }

    def _audio_to_wav_path(self, audio: sr.AudioData) -> str:
        data = audio.get_wav_data()
        ts = int(time.time() * 1000)
        path = os.path.join(self.temp_dir, f"chunk_{ts}.wav")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def transcribe_audio(self, audio: sr.AudioData) -> str:
        try:
            try:
                self._metrics["stt_calls"] += 1
            except Exception:
                pass
            if hasattr(self._recognizer, "recognize_vosk"):
                t = self._recognizer.recognize_vosk(audio)
                t = (t or "").strip()
                if t:
                    try:
                        self._metrics["stt_success"] += 1
                    except Exception:
                        pass
                    return t
        except Exception as e:
            self.log.info(f"Transcripción Vosk fallida: {e}")
        self._ensure_model()
        if self._model is not None:
            try:
                wav_path = self._audio_to_wav_path(audio)
                self.log.info(f"WAV generado: {wav_path}")
                result = self._model.transcribe(wav_path, language=self.language, fp16=False, verbose=False)
                text = (result.get("text") or "").strip()
                try:
                    if text:
                        self._metrics["stt_success"] += 1
                    else:
                        self._metrics["stt_empty"] += 1
                except Exception:
                    pass
                return text
            except Exception as e:
                self.log.info(f"Transcripción fallida: {e}")
        try:
            text = self._recognizer.recognize_google(audio, language="es-ES", show_all=False)
            text = (text or "").strip()
            try:
                if text:
                    self._metrics["stt_success"] += 1
                else:
                    self._metrics["stt_empty"] += 1
            except Exception:
                pass
            return text
        except Exception as e:
            self.log.info(f"Transcripción fallback fallida: {e}")
            try:
                self._metrics["stt_empty"] += 1
            except Exception:
                pass
            return ""

    def _in_wake(self) -> bool:
        return self._wake_mode and time.time() <= self._wake_until

    def _set_wake(self):
        self._wake_mode = True
        self._wake_until = time.time() + 8.0
        self.log.info("Wake activado")
        self._narrate("Dime, te escucho")
        try:
            self._metrics["wake_responses"] += 1
        except Exception:



            pass

    def process_text(self, text: str):
        orig = (text or "").lower().strip()
        lt = normalizar_comando(orig)
        if not lt:
            return
        wake_detected = False
        custom_wakes = ["nexus escucha", "ion escucha", "ion master escucha", "ion nexus escucha", "nexux escucha"]
        for w in (self.wake_words + custom_wakes):
            if w and w in lt:
                wake_detected = True
                lt = lt.replace(w, "").strip()
        if wake_detected:
            try:
                self._metrics["wake_detected"] += 1
            except Exception:
                pass
            self._set_wake()
            return
        if not self._in_wake():
            return
        if len(lt.split()) < 1:
            try:
                self._metrics["short_phrases"] += 1
            except Exception:
                pass
            self._narrate("No te entendí, ¿puedes repetirlo?")
            return
        try:
            if lt != orig:
                self._metrics["normalized_changed"] += 1
        except Exception:
            pass
        self._wake_mode = False
        self._wake_until = 0.0
        self.log.info(f"Comando: {lt}")
        self._narrate("Comando recibido. Ejecutando…")
        try:
            import os
            base = os.path.dirname(__file__)
            d = os.path.join(base, 'temp')
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, 'panel_cmd.txt')
            with open(p, 'w', encoding='utf-8') as f:
                f.write(lt)
        except Exception:
            pass
        try:
            try:
                self._metrics["commands_received"] += 1
            except Exception:
                pass
            if asyncio.iscoroutinefunction(self.command_callback):
                asyncio.run(self.command_callback(lt))
            elif self.command_callback:
                self.command_callback(lt)
            try:
                self._metrics["commands_executed"] += 1
            except Exception:
                pass
        except Exception as e:
            self.log.info(f"Callback error: {e}")
            try:
                self._metrics["command_errors"] += 1
            except Exception:
                pass

    def get_metrics(self) -> dict:
        try:
            return dict(self._metrics)
        except Exception:
            return {}

    def reset_metrics(self):
        try:
            for k in list(self._metrics.keys()):
                self._metrics[k] = 0
        except Exception:
            pass

    def export_metrics(self, path: Optional[str] = None) -> str:
        try:
            base = os.path.dirname(__file__)
            d = os.path.join(base, 'logs')
            os.makedirs(d, exist_ok=True)
            p = path or os.path.join(d, f"voice_metrics_{int(time.time())}.txt")
            m = self.get_metrics()
            lines = [f"{k}: {v}" for k, v in sorted(m.items())]
            with open(p, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            return p
        except Exception:
            return ""


class WhisperVoiceController:
    def __init__(self, command_callback: Optional[Callable[[str], Union[None, asyncio.Future]]] = None, wake_words: Optional[list] = None, model_name: str = "tiny"):
        self.command_callback = command_callback
        self.wake_words = wake_words or ["nexus", "ion", "nexus escucha", "ey nexus"]
        self.sample_rate = 16000
        self.running = False
        self._wake_until = 0.0
        self.buffer = None
        self.log = logging.getLogger("voice")
        if not self.log.handlers:
            self.log.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter("%(asctime)s [DIAG] %(levelname)s %(message)s"))
            self.log.addHandler(ch)
        try:
            self.model = whisper.load_model(model_name) if whisper else None
        except Exception:
            self.model = None
        try:
            import pyttsx3 as _py
            self._tts = _py.init()
        except Exception:
            self._tts = None

    def _in_wake(self):
        return time.time() < self._wake_until

    def _set_wake(self):
        self._wake_until = time.time() + 10.0
        self._narrate("Sí, te escucho")

    def _narrate(self, text: str):
        if not text:
            return
        try:
            if self._tts:
                try:
                    self._tts.setProperty("rate", 175)
                except Exception:
                    pass
                try:
                    voices = self._tts.getProperty("voices") or []
                    target = None
                    for v in voices:
                        nid = getattr(v, "id", "") or ""
                        name = getattr(v, "name", "") or ""
                        lang = ",".join(getattr(v, "languages", []) or [])
                        if ("es" in nid.lower()) or ("es" in name.lower()) or ("es" in lang.lower()) or ("spanish" in name.lower()):
                            target = v.id
                            break
                    if target:
                        self._tts.setProperty("voice", target)
                except Exception:
                    pass
                self._tts.say(text)
                self._tts.runAndWait()
        except Exception:
            pass

    def process_text(self, text: str):
        t = normalizar_comando((text or "").lower())
        wake = False
        for w in self.wake_words:
            if w and w in t:
                wake = True
                t = t.replace(w, "").strip()
        if wake:
            self._set_wake()
            return
        if (not self._in_wake()) or (not t.strip()):
            return
        self._wake_until = 0.0
        self.log.info(f"COMANDO → {t}")
        self._narrate("Ejecutando")
        try:
            if self.command_callback:
                threading.Thread(target=self.command_callback, args=(t,), daemon=True).start()
        except Exception:
            pass

    async def astart(self):
        self.running = True
        self.buffer = None

        def listener():
            if sd is None or whisper is None or self.model is None:
                try:
                    with sr.Microphone(sample_rate=self.sample_rate) as source:
                        r = sr.Recognizer()
                        try:
                            r.adjust_for_ambient_noise(source)
                        except Exception:
                            pass
                        while self.running:
                            try:
                                audio = r.listen(source, timeout=3.0, phrase_time_limit=3.0)
                                try:
                                    txt = r.recognize_google(audio, language="es-ES")
                                except Exception:
                                    txt = ""
                                if txt:
                                    self.log.info(f"Oído: {txt}")
                                    self.process_text(txt)
                            except Exception:
                                pass
                except Exception:
                    return
                return
            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=1024) as stream:
                    buf = []
                    while self.running:
                        try:
                            data, _ = stream.read(1024)
                            buf.append(data.copy())
                            if len(buf) * 1024 >= self.sample_rate * 3:
                                import numpy as _np
                                arr = _np.concatenate(buf, axis=0)
                                buf = []
                                try:
                                    res = self.model.transcribe(arr, language="es", fp16=False)
                                    txt = (res.get("text") or "").strip()
                                except Exception:
                                    txt = ""
                                if txt:
                                    self.log.info(f"Oído: {txt}")
                                    self.process_text(txt)
                        except Exception:
                            pass
            except Exception:
                pass

        threading.Thread(target=listener, daemon=True).start()
        self.log.info("Escuchando... di 'nexus' para activar")

    def _listen_loop(self):
        self.log.info("Escucha iniciando")
        self._active = True
        self._narrate("Aqui Nexus te escucho")
        while not self._stop_evt.is_set():
            if not self._verify_microphone(self._mic_index):
                time.sleep(0.5)
                continue
            params = self._pick_source_params()
            if not params:
                self.log.info("Sin fuente de microfono disponible")
                time.sleep(1.0)
                continue
            idx, rate = params
            self._mic_index = idx if idx is not None else self._mic_index
            try:
                if rate is None:
                    with sr.Microphone(device_index=idx, chunk_size=self.chunk_size) as stream:
                        try:
                            self._recognizer.adjust_for_ambient_noise(stream, duration=1.0)
                        except Exception:
                            pass
                        try:
                            audio = self._recognizer.listen(stream, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                        except Exception as e:
                            self.log.info(f"Captura vacía: {e}")
                            continue
                        text = self.transcribe_audio(audio)
                        self.log.info(f"Texto: {text}")
                        self.process_text(text)
                else:
                    with sr.Microphone(device_index=idx, sample_rate=rate, chunk_size=self.chunk_size) as stream:
                        try:
                            self._recognizer.adjust_for_ambient_noise(stream, duration=1.0)
                        except Exception:
                            pass
                        try:
                            audio = self._recognizer.listen(stream, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                        except Exception as e:
                            self.log.info(f"Captura vacía: {e}")
                            continue
                        text = self.transcribe_audio(audio)
                        self.log.info(f"Texto: {text}")
                        self.process_text(text)
            except Exception as e:
                self.log.info(f"Mic ocupado: {e}")
                time.sleep(0.5)
        self._active = False
        self.log.info("Escucha detenida")


async def run_voice_diagnostics(vc: VoiceController) -> dict:
    return vc.diagnostics()

def _mic_stream(idx: int, rate: Optional[int], chunk: int):
    if rate is None:
        return sr.Microphone(device_index=idx, chunk_size=chunk)
    return sr.Microphone(device_index=idx, sample_rate=rate, chunk_size=chunk)

class VoiceController(VoiceController):
    def listen_once(self) -> str:
        if not self._verify_microphone(self._mic_index):
            return ""
        params = self._pick_source_params()
        if not params:
            self.log.info("Sin fuente de microfono disponible")
            return ""
        idx, rate = params
        self._mic_index = idx if idx is not None else self._mic_index
        try:
            with _mic_stream(idx, rate, self.chunk_size) as stream:
                try:
                    self._recognizer.adjust_for_ambient_noise(stream, duration=1.0)
                except Exception:
                    pass
                try:
                    audio = self._recognizer.listen(stream, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                except Exception as e:
                    self.log.info(f"Captura vacía: {e}")
                    return ""
                text = self.transcribe_audio(audio)
                self.log.info(f"Texto: {text}")
                if text:
                    self.process_text(text)
                return text or ""
        except Exception as e:
            self.log.info(f"Mic ocupado: {e}")
            return ""

    def run_voice_diagnostics(self) -> dict:
        return self.diagnostics()

    def mic_quick_test(self) -> bool:
        return self._verify_microphone(self._mic_index)

    def adjust_for_noise(self) -> bool:
        params = self._pick_source_params()
        if not params:
            return False
        idx, rate = params
        try:
            with _mic_stream(idx, rate, self.chunk_size) as stream:
                try:
                    self._recognizer.adjust_for_ambient_noise(stream, duration=1.0)
                except Exception:
                    pass
            return True
        except Exception:
            return False
