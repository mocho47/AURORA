
import os
import threading
import subprocess
import webbrowser
import speech_recognition as sr
from normalizador_comandos import normalizar_comando
from narrador import narrar, establecer_modo_narracion

MIC_INDEX = int(os.getenv("ION_MIC_INDEX", "1") or "1")
MIC_ID = MIC_INDEX
PHRASE_LIMIT = 10
TIMEOUT = 4.0
USE_VOSK = False
np = None
sd = None

class _ResultadoVarStub:
    def set(self, _):
        try:
            pass
        except Exception:
            pass

resultado_var = _ResultadoVarStub()

def log_event(msg: str):
    try:
        print(msg)
    except Exception:
        pass

def _panel_bridge_command(cmd: str):
    try:
        base = os.path.dirname(__file__)
        d = os.path.join(base, 'temp')
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, 'panel_cmd.txt')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(cmd)
    except Exception:
        pass

def validar_microfono(index):
    try:
        names = sr.Microphone.list_microphone_names() or []
    except Exception:
        names = []
    return index in range(len(names))

def proceso_voz_continuo():
    try:
        if not validar_microfono(MIC_INDEX):
            narrar("Micrófono no disponible.")
            return
        recognizer = sr.Recognizer()
        with sr.Microphone(device_index=MIC_INDEX) as source:
            try:
                recognizer.adjust_for_ambient_noise(source)
            except Exception:
                pass
            narrar("Aqui Nexus te escucho")
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    texto = ""
                    if hasattr(recognizer, "recognize_vosk"):
                        try:
                            texto = recognizer.recognize_vosk(audio)
                        except Exception:
                            texto = recognizer.recognize_google(audio, language="es-ES")
                    else:
                        texto = recognizer.recognize_google(audio, language="es-ES")
                    texto = (texto or "").lower().strip()
                    if texto.startswith("nexus escucha"):
                        comando_raw = texto.replace("nexus escucha", "").strip()
                        comando = normalizar_comando(comando_raw)
                        if comando:
                            narrar("Comando recibido. Ejecutando…")
                            ejecutar_comando_trae(comando)
                        else:
                            narrar("No te entendí, ¿puedes repetirlo?")
                except sr.UnknownValueError:
                    pass
                except Exception:
                    narrar("Error en la captura de voz.")
                    break
    except Exception:
        narrar("Error al iniciar la escucha.")

def captura_un_minuto():
    try:
        sr_index = None
        try:
            sr_index = _sr_pick_index(MIC_INDEX)
        except Exception:
            sr_index = None
        if sr_index is None:
            sr_index = MIC_INDEX
        recognizer = sr.Recognizer()
        source_ctx = None
        try:
            source_ctx = sr.Microphone(device_index=sr_index)
        except Exception:
            try:
                source_ctx = sr.Microphone()
            except Exception:
                source_ctx = None
        if source_ctx is None:
            narrar("Micrófono no disponible.")
            return
        with source_ctx as source:
            try:
                recognizer.adjust_for_ambient_noise(source)
            except Exception:
                pass
            narrar("Tienes un minuto para hablar")
            try:
                audio = recognizer.record(source, duration=60)
            except Exception:
                narrar("Error al capturar audio.")
                return
            try:
                texto = ""
                if hasattr(recognizer, "recognize_vosk"):
                    try:
                        texto = recognizer.recognize_vosk(audio)
                    except Exception:
                        texto = recognizer.recognize_google(audio, language="es-ES")
                else:
                    texto = recognizer.recognize_google(audio, language="es-ES")
                t = normalizar_comando(texto)
                for w in ["nexus escucha", "ion escucha", "ion master escucha", "ion nexus escucha", "nexux escucha"]:
                    if w in t:
                        t = t.replace(w, "").strip()
                if t:
                    try:
                        print(f"[VOZ] Comando: {t}")
                    except Exception:
                        pass
                    try:
                        narrar(f"Comando recibido: {t}")
                    except Exception:
                        pass
                    narrar("Comando recibido. Ejecutando…")
                    try:
                        ejecutar_comando(t)
                    except Exception:
                        try:
                            ejecutar_comando_trae(t)
                        except Exception:

                            pass
                else:
                    narrar("No te entendí, ¿puedes repetirlo?")
            except sr.UnknownValueError:
                narrar("No entendí. ¿Puedes repetirlo?")
            except sr.RequestError:
                narrar("Servicio de reconocimiento no disponible.")
            except Exception:
                narrar("Error en la captura de voz.")
    except Exception:
        narrar("Error al iniciar la escucha.")

def iniciar_voz_segura():

    hilo = threading.Thread(target=proceso_voz_continuo, name="voz_segura", daemon=True)
    hilo.start()
    return hilo

if __name__ == "__main__":
    captura_un_minuto()
    input("Presiona Enter para detener...\n")

def _panel_ready() -> bool:
    try:
        base = os.path.dirname(__file__)
        d = os.path.join(base, 'temp')
        p = os.path.join(d, 'panel_ready.flag')
        return os.path.exists(p)
    except Exception:
        return False

def _sr_pick_index(prefer_index):
    try:
        names = sr.Microphone.list_microphone_names() or []
    except Exception:
        names = []
    if prefer_index is not None and 0 <= prefer_index < len(names):
        return prefer_index
    prefer_name = None
    for n in names:
        if "este micro" in n.lower() or "realtek" in n.lower():
            prefer_name = n
            break
    if prefer_name is not None:
        try:
            return names.index(prefer_name)
        except Exception:
            pass
    return None

def _open_mic(index):
    rates = [None, 48000, 44100, 16000]
    for r in rates:
        try:
            if r is None:
                with sr.Microphone(device_index=index) as s:
                    return (index, None)
            else:
                with sr.Microphone(device_index=index, sample_rate=r) as s:
                    return (index, r)
        except Exception as e:
            log_event(f"Intento fallido mic={index} rate={r}: {e}")
            continue
    return None

def _sd_capture_bytes(duration_sec: float, samplerate: int = 16000) -> bytes:
    try:
        if np is not None:
            frames = int(duration_sec * samplerate)
            data = sd.rec(frames, samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()
            return data.tobytes()
        else:
            with sd.RawInputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:
                total = int(duration_sec * samplerate)
                chunk = 1024
                buf = bytearray()
                remaining = total
                while remaining > 0:
                    to_read = min(chunk, remaining)
                    b, ov = stream.read(to_read)
                    buf.extend(b)
                    remaining -= to_read
                return bytes(buf)
    except Exception as e:
        log_event(f"Error al capturar con sounddevice: {e}")
        return b""

def escuchar_con_gui():
    sr_index = _sr_pick_index(MIC_ID)
    if sr_index is None:
        sr_index = MIC_ID
    recognizer = sr.Recognizer()

    def proceso_voz():
        try:
            picked = _open_mic(sr_index)
            if not picked:
                log_event("Sin fuente de micrófono disponible. Usando captura alternativa.")
                narrar("Micrófono no disponible. Intentando captura alternativa.")
                raw = _sd_capture_bytes(PHRASE_LIMIT, 16000)
                if not raw:
                    resultado_var.set("❌ Error de captura alternativa.")
                    return
                audio = sr.AudioData(raw, 16000, 2)
                try:
                    if hasattr(recognizer, "recognize_vosk"):
                        texto = recognizer.recognize_vosk(audio)
                    else:
                        texto = recognizer.recognize_google(audio, language="es-ES")
                    log_event(f"Comando: {texto}")
                    narrar(f"Comando recibido: {texto}")
                    resultado_var.set(f"🗣️ {texto}")
                except sr.UnknownValueError:
                    log_event("Sin reconocimiento en captura alternativa.")
                    narrar("No entendí. ¿Puedes repetirlo?")
                    resultado_var.set("⚠️ No se reconoció ningún comando.")
                return
            idx, rate = picked
            if rate is None:
                with sr.Microphone(device_index=idx) as source:
                    try:
                        recognizer.adjust_for_ambient_noise(source)
                    except Exception as e:
                        log_event(f"Ajuste de ruido falló: {e}")
                    log_event("Escucha iniciando")
                    narrar("Aqui Nexus te escucho.")
                    try:
                        audio = recognizer.listen(source, timeout=TIMEOUT, phrase_time_limit=PHRASE_LIMIT)
                    except sr.WaitTimeoutError:
                        log_event("Tiempo agotado sin inicio de frase.")
                        narrar("No se detectó voz. Intenta de nuevo.")
                        resultado_var.set("⏳ Tiempo agotado sin voz.")
                        return
                    try:
                        if USE_VOSK and hasattr(recognizer, "recognize_vosk"):
                            try:
                                texto = recognizer.recognize_vosk(audio)
                            except Exception:
                                texto = recognizer.recognize_google(audio, language="es-ES")
                        else:
                            texto = recognizer.recognize_google(audio, language="es-ES")
                        log_event(f"Comando: {texto}")
                        narrar(f"Comando recibido: {texto}")
                        resultado_var.set(f"🗣️ {texto}")
                        ejecutar_comando(texto)
                    except sr.UnknownValueError:
                        log_event("Sin reconocimiento. Verifique volumen y privacidad.")
                        narrar("No entendí. ¿Puedes repetirlo?")
                        resultado_var.set("⚠️ No se reconoció ningún comando.")
                    except sr.RequestError as e:
                        log_event(f"Error de red en reconocimiento: {e}")
                        narrar("Servicio de reconocimiento no disponible.")
                        resultado_var.set("⚠️ Servicio de reconocimiento no disponible.")
            else:
                with sr.Microphone(device_index=idx, sample_rate=rate) as source:
                    try:
                        recognizer.adjust_for_ambient_noise(source)
                    except Exception as e:
                        log_event(f"Ajuste de ruido falló: {e}")
                    log_event("Escucha iniciando")
                    narrar("Aqui Nexus te escucho.")
                    try:
                        audio = recognizer.listen(source, timeout=TIMEOUT, phrase_time_limit=PHRASE_LIMIT)
                    except sr.WaitTimeoutError:
                        log_event("Tiempo agotado sin inicio de frase.")
                        narrar("No se detectó voz. Intenta de nuevo.")
                        resultado_var.set("⏳ Tiempo agotado sin voz.")
                        return
                    try:
                        if USE_VOSK and hasattr(recognizer, "recognize_vosk"):
                            try:
                                texto = recognizer.recognize_vosk(audio)
                            except Exception:
                                texto = recognizer.recognize_google(audio, language="es-ES")
                        else:
                            texto = recognizer.recognize_google(audio, language="es-ES")
                        log_event(f"Comando: {texto}")
                        narrar(f"Comando recibido: {texto}")
                        resultado_var.set(f"🗣️ {texto}")
                        ejecutar_comando(texto)
                    except sr.UnknownValueError:
                        log_event("Sin reconocimiento. Verifique volumen y privacidad.")
                        narrar("No entendí. ¿Puedes repetirlo?")
                        resultado_var.set("⚠️ No se reconoció ningún comando.")
                    except sr.RequestError as e:
                        log_event(f"Error de red en reconocimiento: {e}")
                    narrar("Servicio de reconocimiento no disponible.")
                    resultado_var.set("⚠️ Servicio de reconocimiento no disponible.")

        except Exception as e:
            log_event(f"Captura vacía: {e}")
            narrar("Error al capturar audio.")
            resultado_var.set("❌ Error de captura.")

    Thread(target=proceso_voz).start()

def proceso_voz_continuo():
    try:
        sr_index = _sr_pick_index(MIC_ID)
        if sr_index is None:
            sr_index = MIC_ID
        recognizer = sr.Recognizer()
        mic_index = sr_index
        if not validar_microfono(mic_index):
            narrar("Micrófono no disponible.")
            resultado_var.set("❌ Micrófono inválido.")
            return

        try:
            source_ctx = sr.Microphone(device_index=mic_index)
        except Exception:
            source_ctx = None
        if source_ctx is None:
            try:
                narrar("Micrófono no disponible. Captura alternativa activa.")
            except Exception:
                pass
            log_event("Fallo Microphone. Fallback a sounddevice")
            while True:
                try:
                    raw = _sd_capture_bytes(10.0, 16000)
                    if not raw:
                        continue
                    audio = sr.AudioData(raw, 16000, 2)
                    texto = _transcribir(recognizer, audio)
                    texto = normalizar_comando(texto)
                    log_event(f"Detectado: {texto}")
                    if texto.startswith("nexus escucha"):
                        comando = texto.replace("nexus escucha", "").strip()
                        if comando:
                            narrar("Comando recibido. Ejecutando…")
                            resultado_var.set(f"🗣️ {comando}")
                            try:
                                _panel_bridge_command(comando)
                            except Exception:
                                pass
                            ejecutar_comando(comando)
                        else:
                            narrar("No te entendí, ¿puedes repetirlo?")
                            resultado_var.set("🤔 No te entendí, ¿puedes repetirlo?")
                            log_event("Frase activadora sin comando.")
                    else:
                        log_event("Frase ignorada (sin activación).")
                except sr.UnknownValueError:
                    log_event("Ruido o voz no reconocida. Silencio mantenido.")
                except Exception as e:
                    log_event(f"Error en escucha continua (fallback): {e}")
                    narrar("Error en la captura de voz.")
                    resultado_var.set("❌ Error en escucha.")
                    break
            return
        with source_ctx as source:
            try:
                recognizer.adjust_for_ambient_noise(source)
            except Exception:
                pass
            narrar("Aqui Nexus te escucho.")
            log_event("Escucha continua iniciada")

            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    texto = _transcribir(recognizer, audio)
                    texto = normalizar_comando(texto)
                    log_event(f"Detectado: {texto}")

                    if texto.startswith("nexus escucha"):
                        comando = texto.replace("nexus escucha", "").strip()
                        if comando:
                            narrar("Comando recibido. Ejecutando…")
                            resultado_var.set(f"🗣️ {comando}")
                            try:
                                _panel_bridge_command(comando)
                            except Exception:
                                pass
                            ejecutar_comando(comando)
                        else:
                            narrar("No te entendí, ¿puedes repetirlo?")
                            resultado_var.set("🤔 No te entendí, ¿puedes repetirlo?")
                            log_event("Frase activadora sin comando.")
                    else:
                        log_event("Frase ignorada (sin activación).")
                except sr.UnknownValueError:
                    log_event("Ruido o voz no reconocida. Silencio mantenido.")
                except Exception as e:
                    log_event(f"Error en escucha continua: {e}")
                    narrar("Error en la captura de voz.")
                    resultado_var.set("❌ Error en escucha.")
                    break
    except Exception as e:
        log_event(f"Error al iniciar escucha: {e}")
        narrar("Error al iniciar la escucha.")
        resultado_var.set("❌ Error al iniciar captura.")

def ejecutar_comando(texto: str):
    t = normalizar_comando(texto)
    try:
        _panel_bridge_command(t)
    except Exception:
        pass
    if ("activa modo fluido" in t):
        try:
            establecer_modo_narracion("fluido")
            narrar("Modo fluido activado")
        except Exception:
            pass
        return
    if ("activa modo seguro" in t):
        try:
            establecer_modo_narracion("seguro")
            narrar("Modo seguro activado")
        except Exception:
            pass
        return
    if ("activa modo legado" in t):
        try:
            establecer_modo_narracion("legado")
            narrar("Modo legado activado")
        except Exception:
            pass
        return
    if (t.startswith("abre ") and ("facebook" in t)) or ("abrir facebook" in t) or ("facebook" in t):
        try:
            webbrowser.open("https://www.facebook.com/", new=2)
            log_event("Acción: abrir facebook")
        except Exception as e:
            log_event(f"Error al abrir facebook: {e}")
        return
    if (t.startswith("abre ") and ("carpeta" in t or "explorador" in t)) or ("abrir carpeta" in t) or ("carpeta" in t) or ("explorador" in t):
        try:
            subprocess.Popen(["explorer.exe", os.getcwd()])
            log_event("Acción: abrir carpeta")
        except Exception as e:
            log_event(f"Error al abrir carpeta: {e}")
        return
    if (t.startswith("abre ") and ("navegador" in t or "google" in t)) or ("abrir navegador" in t) or ("navegador" in t) or ("google" in t):
        try:
            webbrowser.open("https://www.google.com/", new=2)
            log_event("Acción: abrir navegador")
        except Exception as e:
            log_event(f"Error al abrir navegador: {e}")
        return
    if (t.startswith("abre ") and ("tiktok" in t)) or ("abrir tiktok" in t):
        try:
            webbrowser.open("https://www.tiktok.com/", new=2)
            log_event("Acción: abrir tiktok")
        except Exception as e:
            log_event(f"Error al abrir tiktok: {e}")
        return
    if ("tiktok studio" in t):
        try:
            webbrowser.open("https://www.tiktok.com/creator-center", new=2)
            log_event("Acción: tiktok studio")
        except Exception as e:
            log_event(f"Error tiktok studio: {e}")
        return
    if ("sube tiktok" in t) or ("subir tiktok" in t) or ("publica tiktok" in t) or ("publicar tiktok" in t) or ("programa tiktok" in t) or ("programar tiktok" in t):
        try:
            webbrowser.open("https://www.tiktok.com/upload?lang=es", new=2)
            log_event("Acción: tiktok upload")
        except Exception as e:
            log_event(f"Error tiktok upload: {e}")
        return
    if (t.startswith("abre ") and ("instagram" in t)) or ("abrir instagram" in t):
        try:
            webbrowser.open("https://www.instagram.com/", new=2)
            log_event("Acción: abrir instagram")
        except Exception as e:
            log_event(f"Error abrir instagram: {e}")
            return
    if ("instagram creator" in t) or ("publicar reels" in t) or ("programar reels" in t):
        try:
            webbrowser.open("https://business.facebook.com/creatorstudio/", new=2)
            log_event("Acción: instagram/reels")
        except Exception as e:
            log_event(f"Error instagram/reels: {e}")
            return
    if (t.startswith("abre ") and ("youtube" in t)) or ("abrir youtube" in t):
        try:
            webbrowser.open("https://www.youtube.com/", new=2)
            log_event("Acción: abrir youtube")
        except Exception as e:
            log_event(f"Error abrir youtube: {e}")
            return
    if ("youtube studio" in t):
        try:
            webbrowser.open("https://studio.youtube.com/", new=2)
            log_event("Acción: youtube studio")
        except Exception as e:
            log_event(f"Error youtube studio: {e}")
            return
    if ("sube shorts" in t) or ("subir shorts" in t) or ("publica shorts" in t) or ("publicar shorts" in t) or ("programa shorts" in t) or ("programar shorts" in t):
        try:
            webbrowser.open("https://www.youtube.com/upload", new=2)
            log_event("Acción: youtube upload")
        except Exception as e:
            log_event(f"Error youtube upload: {e}")
            return
    if ("facebook creator studio" in t) or ("publica facebook" in t) or ("publicar facebook" in t) or ("programa facebook" in t) or ("programar facebook" in t):
        try:
            webbrowser.open("https://business.facebook.com/creatorstudio/", new=2)
            log_event("Acción: facebook creator studio")
        except Exception as e:
            log_event(f"Error facebook creator studio: {e}")
            return
    if (t.startswith("abre ") and ("x" in t or "twitter" in t)) or ("abrir x" in t) or ("abrir twitter" in t):
        try:
            webbrowser.open("https://x.com/", new=2)
            log_event("Acción: abrir x/twitter")
        except Exception as e:
            log_event(f"Error abrir x/twitter: {e}")
            return
    if ("publica tweet" in t) or ("publicar tweet" in t) or ("programa tweet" in t) or ("programar tweet" in t):
        try:
            webbrowser.open("https://x.com/compose/tweet", new=2)
            log_event("Acción: publicar tweet")
        except Exception as e:
            log_event(f"Error publicar tweet: {e}")
            return
    if (t.startswith("abre ") and ("linkedin" in t)) or ("abrir linkedin" in t):
        try:
            webbrowser.open("https://www.linkedin.com/", new=2)
            log_event("Acción: abrir linkedin")
        except Exception as e:
            log_event(f"Error abrir linkedin: {e}")
            return
    if ("publica linkedin" in t) or ("publicar linkedin" in t):
        try:
            webbrowser.open("https://www.linkedin.com/feed/", new=2)
            log_event("Acción: publicar linkedin")
        except Exception as e:
            log_event(f"Error publicar linkedin: {e}")
            return
    if (t.startswith("abre ") and ("whatsapp" in t)) or ("abrir whatsapp web" in t):
        try:
            webbrowser.open("https://web.whatsapp.com/", new=2)
            log_event("Acción: abrir whatsapp web")
        except Exception as e:
            log_event(f"Error abrir whatsapp: {e}")
            return
    if (t.startswith("abre ") and ("pinterest" in t)) or ("abrir pinterest" in t):
        try:
            webbrowser.open("https://www.pinterest.com/", new=2)
            log_event("Acción: abrir pinterest")
        except Exception as e:
            log_event(f"Error abrir pinterest: {e}")
            return
    if ("publica pin" in t) or ("publicar pin" in t):
        try:
            webbrowser.open("https://www.pinterest.com/pin-builder/", new=2)
            log_event("Acción: publicar pin")
        except Exception as e:
            log_event(f"Error publicar pin: {e}")
            return