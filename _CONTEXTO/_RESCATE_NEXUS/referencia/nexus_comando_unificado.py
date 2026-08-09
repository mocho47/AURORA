import os
import sys
import time
import threading
import speech_recognition as sr
import sounddevice as sd
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    import pygame
    HAS_PYGAME = True
except Exception:
    pygame = None
    HAS_PYGAME = False
import webbrowser
import subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE, 'logs', 'voice_log.txt')
MIC_ID = int(os.getenv('ION_MIC_INDEX', '1'))
USE_VOSK = True

persona_actual = 'ejecutivo'
modo_poseido = False
modo_actual = 'normal'
SUBLIMINALES_PATH = os.path.join(BASE, 'subliminales')
LIC_FILE = os.path.join(BASE, 'nexus_lic.json')

if HAS_PYGAME:
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
    except Exception:
        HAS_PYGAME = False

BIBLIOTECA = {
    'compra_ya': 'COMPRA_YA_18500hz.wav',
    'oferta_limitada': 'OFERTA_LIMITADA_19000hz.wav',
    'confia': 'CONFIA_EN_MI_17800hz.wav',
    'paga_rapido': 'PAGA_RAPIDO_19200hz.wav',
    'recomiendame': 'RECOMIENDAME_18000hz_binaural.wav',
    'mejor_opcion': 'SOY_TU_MEJOR_OPCION_17500hz.wav',
    'no_negocies': 'NO_NEGOCIES_PRECIO_18800hz.wav',
    'repite_compra': 'VUELVE_A_COMPRAR_17700hz.wav',
    'envio_gratis': 'ENVIO_GRATIS_YA_18600hz.wav',
    'ultimas_piezas': 'ULTIMAS_3_PIEZAS_19100hz.wav',
    'gana_comision': 'GANA_30_COMISION_18000hz.wav',
    'delta_compra': 'DELTA_3HZ_COMPRA.wav',
    'theta_confianza': 'THETA_6HZ_CONFIANZA.wav',
    'fomo_ya': 'FOMO_SE_ACABA_18900hz.wav',
    'acepta_precio': 'ACEPTA_EL_PRECIO_18700hz.wav'
}

class SubliminalNexus:
    def __init__(self):
        if HAS_PYGAME:
            try:
                self.canal = pygame.mixer.Channel(7)
            except Exception:
                self.canal = None
        else:
            self.canal = None
        self.en_uso = False

    def disparar(self, clave: str):
        if clave not in BIBLIOTECA:
            return False
        archivo = os.path.join(SUBLIMINALES_PATH, BIBLIOTECA[clave])
        if not os.path.exists(archivo):
            return False
        if self.en_uso:
            return True
        def _play():
            self.en_uso = True
            try:
                if HAS_PYGAME:
                    snd = pygame.mixer.Sound(archivo)
                    try:
                        snd.set_volume(0.12)
                    except Exception:
                        pass
                    if self.canal:
                        self.canal.play(snd)
                        while self.canal.get_busy():
                            time.sleep(0.1)
                    else:
                        pygame.mixer.Sound.play(snd)
                        time.sleep(2.0)
                else:
                    import winsound
                    try:
                        winsound.PlaySound(archivo, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    except Exception:
                        pass
                    time.sleep(2.0)
            except Exception:
                pass
            self.en_uso = False
        try:
            threading.Thread(target=_play, daemon=True).start()
            return True
        except Exception:
            return False

subliminal = SubliminalNexus()

def cargar_lic():
    try:
        if not os.path.exists(LIC_FILE):
            lic = {'tipo': 'demo', 'usos_demo': 0}
            with open(LIC_FILE, 'w', encoding='utf-8') as f:
                import json
                json.dump(lic, f, indent=4)
            return lic
        with open(LIC_FILE, 'r', encoding='utf-8') as f:
            import json
            return json.load(f)
    except Exception:
        return {'tipo': 'demo', 'usos_demo': 0}

def contar_subliminal():
    try:
        import json
        lic = cargar_lic()
        if lic.get('tipo') == 'demo' and lic.get('usos_demo', 0) >= 3:
            narrar('Solo 3 subliminales en demo. Plus da 15 al mes. Embassy ilimitados.')
            return False
        if lic.get('tipo') == 'demo':
            lic['usos_demo'] = int(lic.get('usos_demo', 0)) + 1
            with open(LIC_FILE, 'w', encoding='utf-8') as f:
                json.dump(lic, f, indent=4)
        return True
    except Exception:
        return True

def activar_subliminal(clave: str):
    try:
        if contar_subliminal():
            subliminal.disparar(clave)
    except Exception:
        pass

def log_event(msg: str):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[DIAG] {datetime.now()} - {msg}\n")
    except Exception:
        pass

def _panel_bridge_command(cmd: str):
    try:
        d = os.path.join(BASE, 'temp')
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, 'panel_cmd.txt')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(cmd)
    except Exception:
        pass

def narrar(texto: str):
    try:
        e = pyttsx3.init()
        rate = 170
        if persona_actual == 'fuego':
            rate = 190
        elif persona_actual == 'compañero':
            rate = 160
        else:
            rate = 170
        if modo_poseido:
            rate = 140
        e.setProperty('rate', rate)
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
        e.say(texto)
        e.runAndWait()
    except Exception:
        pass

def validar_microfono(index: int) -> bool:
    try:
        dispositivos = sd.query_devices()
        if index < 0 or index >= len(dispositivos):
            return False
        if not dispositivos[index].get('max_input_channels', 0) > 0:
            return False
        log_event(f"Micrófono detectado: {dispositivos[index].get('name','')} (ID {index})")
        return True
    except Exception as e:
        log_event(f"Error al verificar micrófono: {e}")
        return False

def ejecutar_comando(texto: str):
    global persona_actual, modo_poseido
    t = (texto or '').lower().strip()
    try:
        _panel_bridge_command(t)
    except Exception:
        pass
    if t.startswith('subliminal '):
        clave = t.replace('subliminal', '').strip()
        if clave:
            activar_subliminal(clave)
            narrar('Ejecutando subliminal')
            return
    if ('modo fuego' in t):
        persona_actual = 'fuego'
        narrar('Modo fuego activo')
        log_event('Persona: fuego')
        return
    if ('modo ejecutivo' in t):
        persona_actual = 'ejecutivo'
        narrar('Modo ejecutivo activo')
        log_event('Persona: ejecutivo')
        return
    if ('modo compañero' in t):
        persona_actual = 'compañero'
        narrar('Modo compañero activo')
        log_event('Persona: compañero')
        return
    if ('detecta actividad demoníaca' in t):
        modo_poseido = True
        narrar('Modo teatral activado')
        log_event('Modo poseído activado')
        return
    if ('abrir facebook' in t) or ('facebook' in t):
        try:
            webbrowser.open('https://www.facebook.com/', new=2)
            log_event('Acción: abrir facebook')
        except Exception as e:
            log_event(f'Error abrir facebook: {e}')
        return
    if ('abrir carpeta' in t) or ('carpeta' in t) or ('explorador' in t):
        try:
            subprocess.Popen(['explorer.exe', BASE])
            log_event('Acción: abrir carpeta')
        except Exception as e:
            log_event(f'Error abrir carpeta: {e}')
        return
    if ('abrir navegador' in t) or ('navegador' in t) or ('google' in t):
        try:
            webbrowser.open('https://www.google.com/', new=2)
            log_event('Acción: abrir navegador')
        except Exception as e:
            log_event(f'Error abrir navegador: {e}')
        return
    if ('abrir tiktok' in t):
        try:
            webbrowser.open('https://www.tiktok.com/', new=2)
            log_event('Acción: abrir tiktok')
        except Exception as e:
            log_event(f'Error abrir tiktok: {e}')
        return
    if ('tiktok studio' in t):
        try:
            webbrowser.open('https://www.tiktok.com/creator-center', new=2)
            log_event('Acción: tiktok studio')
        except Exception as e:
            log_event(f'Error tiktok studio: {e}')
        return
    if ('subir tiktok' in t) or ('publicar tiktok' in t) or ('programar tiktok' in t):
        try:
            webbrowser.open('https://www.tiktok.com/upload?lang=es', new=2)
            log_event('Acción: tiktok upload')
        except Exception as e:
            log_event(f'Error tiktok upload: {e}')
        return
    if ('abrir instagram' in t):
        try:
            webbrowser.open('https://www.instagram.com/', new=2)
            log_event('Acción: abrir instagram')
        except Exception as e:
            log_event(f'Error abrir instagram: {e}')
        return
    if ('instagram creator' in t) or ('publicar reels' in t) or ('programar reels' in t):
        try:
            webbrowser.open('https://business.facebook.com/creatorstudio/', new=2)
            log_event('Acción: instagram/reels')
        except Exception as e:
            log_event(f'Error instagram/reels: {e}')
        return
    if ('abrir youtube' in t):
        try:
            webbrowser.open('https://www.youtube.com/', new=2)
            log_event('Acción: abrir youtube')
        except Exception as e:
            log_event(f'Error abrir youtube: {e}')
        return
    if ('youtube studio' in t):
        try:
            webbrowser.open('https://studio.youtube.com/', new=2)
            log_event('Acción: youtube studio')
        except Exception as e:
            log_event(f'Error youtube studio: {e}')
        return
    if ('subir shorts' in t) or ('publicar shorts' in t) or ('programar shorts' in t):
        try:
            webbrowser.open('https://www.youtube.com/upload', new=2)
            log_event('Acción: youtube upload')
        except Exception as e:
            log_event(f'Error youtube upload: {e}')
        return
    if ('facebook creator studio' in t) or ('publicar facebook' in t) or ('programar facebook' in t):
        try:
            webbrowser.open('https://business.facebook.com/creatorstudio/', new=2)
            log_event('Acción: facebook creator studio')
        except Exception as e:
            log_event(f'Error facebook creator studio: {e}')
        return
    if ('abrir x' in t) or ('abrir twitter' in t):
        try:
            webbrowser.open('https://x.com/', new=2)
            log_event('Acción: abrir x/twitter')
        except Exception as e:
            log_event(f'Error abrir x/twitter: {e}')
        return
    if ('publicar tweet' in t) or ('programar tweet' in t):
        try:
            webbrowser.open('https://x.com/compose/tweet', new=2)
            log_event('Acción: publicar tweet')
        except Exception as e:
            log_event(f'Error publicar tweet: {e}')
        return
    if ('abrir linkedin' in t):
        try:
            webbrowser.open('https://www.linkedin.com/', new=2)
            log_event('Acción: abrir linkedin')
        except Exception as e:
            log_event(f'Error abrir linkedin: {e}')
        return
    if ('publicar linkedin' in t):
        try:
            webbrowser.open('https://www.linkedin.com/feed/', new=2)
            log_event('Acción: publicar linkedin')
        except Exception as e:
            log_event(f'Error publicar linkedin: {e}')
        return
    if ('abrir whatsapp web' in t):
        try:
            webbrowser.open('https://web.whatsapp.com/', new=2)
            log_event('Acción: abrir whatsapp web')
        except Exception as e:
            log_event(f'Error abrir whatsapp: {e}')
        return
    if ('abrir pinterest' in t):
        try:
            webbrowser.open('https://www.pinterest.com/', new=2)
            log_event('Acción: abrir pinterest')
        except Exception as e:
            log_event(f'Error abrir pinterest: {e}')
        return
    if ('publicar pin' in t):
        try:
            webbrowser.open('https://www.pinterest.com/pin-builder/', new=2)
            log_event('Acción: publicar pin')
        except Exception as e:
            log_event(f'Error publicar pin: {e}')
        return

def proceso_voz_continuo():
    try:
        if not validar_microfono(MIC_ID):
            narrar('Micrófono no disponible.')
            return
        with sr.Microphone(device_index=MIC_ID) as source:
            try:
                recognizer = sr.Recognizer()
                recognizer.adjust_for_ambient_noise(source)
            except Exception:
                pass
            narrar('Aquí Nexus, te escucho.')
            log_event('Escucha continua iniciada')
            while True:
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    try:
                        if USE_VOSK and hasattr(recognizer, 'recognize_vosk'):
                            texto = recognizer.recognize_vosk(audio)
                        else:
                            texto = recognizer.recognize_google(audio, language='es-ES')
                    except sr.UnknownValueError:
                        raise sr.UnknownValueError()
                    t = (texto or '').lower().strip()
                    log_event(f'Detectado: {t}')
                    if t.startswith('nexus escucha detecta actividad demoníaca'):
                        global modo_poseido
                        modo_poseido = True
                        narrar('Modo teatral activado')
                        log_event('Modo poseído activado')
                        continue
                    if t.startswith('nexus escucha'):
                        comando = t.replace('nexus escucha', '').strip()
                        if comando:
                            narrar('Comando recibido. Ejecutando…')
                            try:
                                _panel_bridge_command(comando)
                            except Exception:
                                pass
                            ejecutar_comando(comando)
                        else:
                            narrar('No te entendí, ¿puedes repetirlo?')
                            log_event('Frase activadora sin comando')
                    else:
                        pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    log_event(f'Error en escucha continua: {e}')
                    narrar('Error en la captura de voz.')
                    break
    except Exception as e:
        log_event(f'Error al iniciar escucha: {e}')
        narrar('Error al iniciar la escucha.')

if __name__ == '__main__':
    proceso_voz_continuo()