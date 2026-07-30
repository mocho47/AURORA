import os, sys, threading, queue, json, time, winsound, pyttsx3, subprocess, re
import tkinter as tk
from tkinter import ttk

try:
    import pyaudio
    from vosk import Model, KaldiRecognizer
    VOSK_OK = True
except Exception:
    VOSK_OK = False
try:
    import requests
except Exception:
    requests = None

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")

BASE = r"C:\anuar"
LICENCIA = os.path.join(BASE, ".envasador_key")
SEGMENTO_FILE = os.path.join(BASE, "nexus_segment.txt")
LINK_FILE = os.path.join(BASE, "nexus_link.txt")
REDES_FILE = os.path.join(BASE, "nexus_redes.txt")
SOPORTE_FILE = os.path.join(BASE, "nexus_soporte.txt")
CATALOG_FILE = os.path.join(BASE, "nexus_catalog.json")
FINANZAS_FILE = os.path.join(BASE, "nexus_finanzas.csv")
OUTBOX_DIR = os.path.join(BASE, "nexus_outbox")
WHATSAPP_TOKEN_FILE = os.path.join(BASE, "nexus_whatsapp_token.txt")
WHATSAPP_PHONE_ID_FILE = os.path.join(BASE, "nexus_whatsapp_phone_id.txt")
WHATSAPP_RECIPIENT_FILE = os.path.join(BASE, "nexus_whatsapp_recipient.txt")
FFMPEG_EXE = os.path.join(BASE, "nexus", "bin", "ffmpeg.exe")
LOG_FILE = os.path.join(BASE, "nexus_log.txt")
LOGO_PATH_FILE = os.path.join(BASE, "nexus_logo.txt")
BGM_PATH_FILE = os.path.join(BASE, "nexus_bgm.txt")
os.makedirs(OUTBOX_DIR, exist_ok=True)
REDES_FILE = os.path.join(BASE, "nexus_redes.txt")
SOPORTE_FILE = os.path.join(BASE, "nexus_soporte.txt")
SUBLIMINALES = os.path.join(BASE, "subliminales")
os.makedirs(SUBLIMINALES, exist_ok=True)

if os.path.exists(LICENCIA) and open(LICENCIA).read().strip() == "ENVASADOR_2025":
    MODO = "ENVASADOR"
else:
    MODO = "PLUS"
SEGMENTO = "DEMO"
try:
    if os.path.exists(SEGMENTO_FILE):
        val = open(SEGMENTO_FILE).read().strip().upper()
        if val in ("DEMO", "PLUS"):
            SEGMENTO = val
except Exception:
    pass

subliminal_queue = queue.Queue()

def subliminal_worker():
    while True:
        sound = subliminal_queue.get()
        if sound is None:
            break
        try:
            if os.path.exists(sound):
                winsound.PlaySound(sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass
        subliminal_queue.task_done()
        time.sleep(0.12)

threading.Thread(target=subliminal_worker, daemon=True).start()

def play_subliminales():
    while True:
        if SUBLIMINAL_ENABLED:
            subliminal_queue.put(os.path.join(SUBLIMINALES, "compra_plus_ya.wav"))
            subliminal_queue.put(os.path.join(SUBLIMINALES, "recomienda_gorila.wav"))
        time.sleep(3.0)

SUBLIMINAL_ENABLED = True
threading.Thread(target=play_subliminales, daemon=True).start()

def get_link():
    try:
        if os.path.exists(LINK_FILE):
            v = open(LINK_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    return "https://mpago.la/tu_link"

URL_COMPRA = get_link()
def get_redes():
    try:
        if os.path.exists(REDES_FILE):
            v = open(REDES_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    return "ENLACE REDES"

def get_soporte():
    try:
        if os.path.exists(SOPORTE_FILE):
            v = open(SOPORTE_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    return "ENLACE SOPORTE"

URL_REDES = get_redes()
URL_SOPORTE = get_soporte()
def get_redes():
    try:
        if os.path.exists(REDES_FILE):
            v = open(REDES_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    return "ENLACE REDES"

def get_soporte():
    try:
        if os.path.exists(SOPORTE_FILE):
            v = open(SOPORTE_FILE).read().strip()
            if v:
                return v
    except Exception:
        pass
    return "ENLACE SOPORTE"

URL_REDES = get_redes()
URL_SOPORTE = get_soporte()

root = tk.Tk()
root.title("NEXUS by Simplex")
root.geometry("1280x800")
root.configure(bg="#000000")

tk.Label(root, text="NEXUS", font=("Impact", 90, "bold"), fg="#FFD700", bg="#000000").pack(pady=60)
mode_label = tk.Label(root, text=f"MODO: {MODO} | SEGMENTO: {SEGMENTO}", font=("Courier", 28, "bold"), fg="#00FFFF", bg="#000000")
mode_label.pack(pady=20)
status = tk.Label(root, text="INICIANDO...", font=("Courier", 24, "bold"), fg="#FFD700", bg="#000000")
status.pack(pady=50)

log = tk.Text(root, height=10, bg="#000000", fg="#00FFFF", insertbackground="#00FFFF", font=("Courier", 16, "bold"))
log.pack(fill="x", padx=40)

def append_log(msg):
    try:
        open(LOG_FILE, "a", encoding="utf-8").write(msg + "\n")
    except Exception:
        pass
    root.after(0, lambda: (log.insert("end", msg + "\n"), log.see("end")))

style = ttk.Style()
style.configure("G.TButton", font=("Impact", 22, "bold"), padding=20)

def voz(texto):
    def _say():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_RATE)
            engine.setProperty("volume", TTS_VOLUME)
            engine.say(texto.upper() + ", JEFE")
            engine.runAndWait()
        except Exception:
            pass
    threading.Thread(target=_say, daemon=True).start()

TTS_RATE = 130
TTS_VOLUME = 1.0
voz("NEXUS ONLINE. MODO " + MODO)
append_log("Sistema: NEXUS ONLINE")

stream = None
p = None
model = None
rec = None

def safe_status(text):
    root.after(0, lambda: status.config(text=text))

def restart_recognition():
    global p, stream, model, rec
    try:
        if stream:
            stream.stop_stream()
            stream.close()
    except Exception:
        pass
    try:
        if p:
            p.terminate()
    except Exception:
        pass
    try:
        if VOSK_OK:
            if model is None:
                model = Model(MODEL_PATH)
            rec = KaldiRecognizer(model, 16000)
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            safe_status("ESCUCHANDO ÓRDENES 24/7")
            voz("REINICIO DE VOZ COMPLETO")
        else:
            safe_status("VOZ OFFLINE - USA BOTONES")
    except Exception:
        safe_status("VOZ OFFLINE - USA BOTONES")

if VOSK_OK:
    try:
        model = Model(MODEL_PATH)
        rec = KaldiRecognizer(model, 16000)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        safe_status("ESCUCHANDO ÓRDENES 24/7")

        def refresh_mode_segment():
            try:
                m = "ENVASADOR" if os.path.exists(LICENCIA) and open(LICENCIA).read().strip() == "ENVASADOR_2025" else "PLUS"
            except Exception:
                m = MODO
            s = SEGMENTO
            try:
                if os.path.exists(SEGMENTO_FILE):
                    val = open(SEGMENTO_FILE).read().strip().upper()
                    if val in ("DEMO", "PLUS"):
                        s = val
            except Exception:
                pass
            root.after(0, lambda: mode_label.config(text=f"MODO: {m} | SEGMENTO: {s}"))

        def show_local_action(title, body):
            try:
                win = tk.Toplevel(root)
                win.title(title)
                win.configure(bg="#000000")
                tk.Label(win, text=title, font=("Impact", 32, "bold"), fg="#FFD700", bg="#000000").pack(pady=10)
                tk.Label(win, text=body, font=("Courier", 18, "bold"), fg="#00FFFF", bg="#000000").pack(pady=10)
                def copy():
                    try:
                        win.clipboard_clear()
                        win.clipboard_append(body)
                        voz("COPIADO")
                    except Exception:
                        pass
                ttk.Button(win, text="COPIAR", style="G.TButton", command=copy).pack(pady=10)
            except Exception:
                pass

        def ffmpeg_available():
            try:
                return os.path.exists(FFMPEG_EXE)
            except Exception:
                return False

        def run_ffmpeg(args, out_path):
            try:
                if not ffmpeg_available():
                    return False
                cmd = [FFMPEG_EXE] + args + [out_path]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return True
            except Exception:
                return False

        def find_font():
            try:
                fp = r"C:\Windows\Fonts\arial.ttf"
                return fp if os.path.exists(fp) else ""
            except Exception:
                return ""

        def get_logo_path():
            try:
                if os.path.exists(LOGO_PATH_FILE):
                    v = open(LOGO_PATH_FILE).read().strip()
                    if v:
                        return v
            except Exception:
                pass
            return ""

        def get_bgm_path():
            try:
                if os.path.exists(BGM_PATH_FILE):
                    v = open(BGM_PATH_FILE).read().strip()
                    if v:
                        return v
            except Exception:
                pass
            fallback = os.path.join(SUBLIMINALES, "recomienda_gorila.wav")
            return fallback if os.path.exists(fallback) else ""

        def edit_template_video(seconds, title, subtitle, audio_path=None):
            try:
                sec = max(1, int(seconds))
            except Exception:
                sec = 5
            out_path = os.path.join(OUTBOX_DIR, f"plantilla_{sec}s.mp4")
            font = find_font()
            args = ["-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={sec}"]
            if font:
                filt = f"drawtext=fontfile='{font}':text='{title}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h/2-120),drawtext=fontfile='{font}':text='{subtitle}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h/2+10)"
                args += ["-vf", filt]
            args += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
            if audio_path and os.path.exists(audio_path):
                args += ["-i", audio_path, "-shortest", "-c:a", "aac"]
            ok = run_ffmpeg(args, out_path)
            if ok:
                voz("VIDEO PLANTILLA LISTO")
                append_log(f"Video: {out_path}")
            else:
                voz("ERROR EDITAR VIDEO")

        def edit_brand_video(seconds, title, subtitle, logo_path=None, bgm_path=None):
            try:
                sec = max(1, int(seconds))
            except Exception:
                sec = 10
            out_path = os.path.join(OUTBOX_DIR, f"brand_{sec}s.mp4")
            font = find_font()
            base = ["-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={sec}"]
            inputs = list(base)
            filter_complex = None
            if logo_path and os.path.exists(logo_path):
                inputs += ["-loop", "1", "-i", logo_path]
                txt = ""
                if font:
                    txt = f",drawtext=fontfile='{font}':text='{title}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h/2-120),drawtext=fontfile='{font}':text='{subtitle}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h/2+10)"
                filter_complex = f"[0:v][1:v]overlay=10:10{txt}"
                inputs += ["-filter_complex", filter_complex]
            else:
                if font:
                    filt = f"drawtext=fontfile='{font}':text='{title}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h/2-120),drawtext=fontfile='{font}':text='{subtitle}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h/2+10)"
                    inputs += ["-vf", filt]
            inputs += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
            if bgm_path and os.path.exists(bgm_path):
                inputs += ["-i", bgm_path, "-shortest", "-c:a", "aac"]
            ok = run_ffmpeg(inputs, out_path)
            if ok:
                voz("VIDEO BRAND LISTO")
                append_log(f"Video: {out_path}")
            else:
                voz("ERROR EDITAR VIDEO")

        def run_campaign(nombre):
            it = find_item(nombre)
            if it:
                edit_template_video(10, "NEXUS", it.get("nombre", ""), os.path.join(SUBLIMINALES, "compra_plus_ya.wav"))
                send_whatsapp(f"Campana {it.get('nombre')} activa: {URL_COMPRA}")
                voz("CAMPANA LISTA")
            else:
                voz("NO ENCONTRADO")

        def run_campaign_full(nombre, cantidad):
            it, total = cotizar_item(nombre, cantidad)
            if it:
                logo = get_logo_path()
                bgm = get_bgm_path()
                edit_brand_video(12, "NEXUS", f"{it.get('nombre')} x {cantidad} = ${total}", logo, bgm)
                send_whatsapp(f"Campaña completa {it.get('nombre')} x {cantidad} = ${total}. Link: {URL_COMPRA}")
                voz("CAMPANA COMPLETA LISTA")
            else:
                voz("NO ENCONTRADO")

        def edit_demo_video(seconds, title=None):
            try:
                sec = max(1, int(seconds))
            except Exception:
                sec = 5
            out_path = os.path.join(OUTBOX_DIR, f"demo_{sec}s.mp4")
            audio1 = os.path.join(SUBLIMINALES, "compra_plus_ya.wav")
            audio2 = os.path.join(SUBLIMINALES, "recomienda_gorila.wav")
            args = ["-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={sec}", "-c:v", "libx264", "-pix_fmt", "yuv420p"]
            if os.path.exists(audio1):
                args += ["-i", audio1, "-shortest", "-c:a", "aac"]
            ok = run_ffmpeg(args, out_path)
            if ok:
                voz("VIDEO DEMO EDITADO")
                append_log(f"Video: {out_path}")
            else:
                voz("ERROR EDITAR VIDEO")

        def load_catalog():
            try:
                return json.loads(open(CATALOG_FILE, "r", encoding="utf-8").read())
            except Exception:
                return []

        def find_item(q):
            try:
                ql = q.lower()
                for it in load_catalog():
                    if ql in str(it.get("nombre", "")).lower():
                        return it
            except Exception:
                pass
            return None

        def cotizar_item(nombre, cantidad):
            it = find_item(nombre)
            if it:
                try:
                    qty = max(1, int(cantidad))
                except Exception:
                    qty = 1
                total = float(it.get("precio", 0)) * qty
                return it, total
            return None, 0.0

        def log_finanza(tipo, concepto, monto):
            try:
                newfile = not os.path.exists(FINANZAS_FILE)
                f = open(FINANZAS_FILE, "a", encoding="utf-8")
                if newfile:
                    f.write("fecha,tipo,concepto,monto\n")
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{tipo},{concepto},{monto}\n")
                f.close()
            except Exception:
                pass

        def send_whatsapp(texto):
            try:
                token = open(WHATSAPP_TOKEN_FILE).read().strip() if os.path.exists(WHATSAPP_TOKEN_FILE) else ""
                phone_id = open(WHATSAPP_PHONE_ID_FILE).read().strip() if os.path.exists(WHATSAPP_PHONE_ID_FILE) else ""
                recipient = open(WHATSAPP_RECIPIENT_FILE).read().strip() if os.path.exists(WHATSAPP_RECIPIENT_FILE) else ""
                if requests and token and phone_id and recipient:
                    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    data = {"messaging_product": "whatsapp", "to": recipient, "text": {"body": texto}}
                    try:
                        requests.post(url, headers=headers, json=data, timeout=10)
                        voz("WHATSAPP ENVIADO")
                        append_log("WhatsApp: enviado")
                        return
                    except Exception:
                        pass
                out = os.path.join(OUTBOX_DIR, "whatsapp.txt")
                open(out, "a", encoding="utf-8").write(texto + "\n")
                voz("WHATSAPP GUARDADO")
                append_log("WhatsApp: guardado en outbox")
            except Exception:
                pass

        def handle_cmd(txt):
            if txt:
                append_log("Usuario: " + txt)
            if "vender" in txt:
                voz("VENDIENDO COMO BESTIA")
            elif "viral" in txt or "virales" in txt:
                voz("GENERANDO MILLONES")
            elif "comprar" in txt or "licencia" in txt or "plus" in txt:
                show_local_action("Licencia PLUS", URL_COMPRA)
                voz("LICENCIA PLUS DISPONIBLE")
            elif "envasador" in txt:
                try:
                    open(LICENCIA, "w").write("ENVASADOR_2025")
                    voz("MODO ENVASADOR ACTIVADO")
                    safe_status("ENVASADOR ACTIVO")
                    refresh_mode_segment()
                except Exception:
                    pass
            elif "demo" in txt:
                try:
                    open(SEGMENTO_FILE, "w").write("DEMO")
                    voz("SEGMENTO DEMO ACTIVADO")
                    refresh_mode_segment()
                except Exception:
                    pass
            elif "plus" in txt:
                try:
                    open(SEGMENTO_FILE, "w").write("PLUS")
                    voz("SEGMENTO PLUS ACTIVADO")
                    refresh_mode_segment()
                except Exception:
                    pass
            elif "abrir" in txt or "abre" in txt:
                show_local_action("Abrir", URL_COMPRA)
                voz("ABRIENDO LOCAL")
            elif "reiniciar voz" in txt or "reiniciar" in txt or "reset voz" in txt:
                restart_recognition()
            elif "diagnostico" in txt or "diagnóstico" in txt:
                try:
                    s1 = "Voz OK" if VOSK_OK else "Voz OFF"
                    s2 = "Modelo OK" if os.path.exists(MODEL_PATH) else "Modelo FALTANTE"
                    s3 = "Mic OK" if (p is not None and stream is not None) else "Mic OFF"
                    s4 = "FFmpeg OK" if os.path.exists(FFMPEG_EXE) else "FFmpeg FALTANTE"
                    show_local_action("Diagnóstico", f"{s1}\n{s2}\n{s3}\n{s4}")
                    voz("DIAGNOSTICO MOSTRADO")
                except Exception:
                    pass
            elif "modo" in txt:
                try:
                    m = "ENVASADOR" if os.path.exists(LICENCIA) and open(LICENCIA).read().strip() == "ENVASADOR_2025" else MODO
                    s = open(SEGMENTO_FILE).read().strip() if os.path.exists(SEGMENTO_FILE) else SEGMENTO
                    show_local_action("Modo", f"{m} | {s}")
                    voz("MODO MOSTRADO")
                except Exception:
                    pass
            elif txt.startswith("editar demo"):
                nums = re.findall(r"(\d+)", txt)
                sec = int(nums[0]) if nums else 5
                edit_demo_video(sec)
            elif txt.startswith("editar plantilla"):
                nums = re.findall(r"(\d+)", txt)
                sec = int(nums[0]) if nums else 5
                rest = txt.split(str(nums[0]))[1].strip() if nums else "NEXUS"
                title = rest if rest else "NEXUS"
                edit_template_video(sec, title, "Simplex", os.path.join(SUBLIMINALES, "recomienda_gorila.wav"))
            elif txt.startswith("campaña "):
                nombre = txt.split("campaña ", 1)[1].strip()
                run_campaign(nombre)
            elif txt.startswith("campaña completa "):
                rest = txt.split("campaña completa ", 1)[1]
                partes = rest.split("cantidad")
                nombre = partes[0].strip()
                cantidad = partes[1].strip() if len(partes) > 1 else "1"
                run_campaign_full(nombre, cantidad)
            elif txt.startswith("buscar "):
                q = txt.split("buscar ", 1)[1].strip()
                it = find_item(q)
                if it:
                    show_local_action("Resultado", f"{it.get('nombre')} ${it.get('precio')}")
                    voz("BUSQUEDA MOSTRADA")
                else:
                    voz("NO ENCONTRADO")
            elif txt.startswith("cotizar "):
                rest = txt.split("cotizar ", 1)[1]
                partes = rest.split("cantidad")
                nombre = partes[0].strip()
                cantidad = partes[1].strip() if len(partes) > 1 else "1"
                it, total = cotizar_item(nombre, cantidad)
                if it:
                    show_local_action("Cotización", f"{it.get('nombre')} x {cantidad} = ${total}")
                    voz("COTIZACION LISTA")
                else:
                    voz("NO ENCONTRADO")
            elif txt.startswith("ingreso "):
                rest = txt.split("ingreso ", 1)[1]
                try:
                    parts = rest.rsplit(" ", 1)
                    concepto = parts[0]
                    monto = float(parts[1])
                except Exception:
                    concepto = rest
                    monto = 0.0
                log_finanza("ingreso", concepto, monto)
                voz("INGRESO REGISTRADO")
            elif txt.startswith("egreso "):
                rest = txt.split("egreso ", 1)[1]
                try:
                    parts = rest.rsplit(" ", 1)
                    concepto = parts[0]
                    monto = float(parts[1])
                except Exception:
                    concepto = rest
                    monto = 0.0
                log_finanza("egreso", concepto, monto)
                voz("EGRESO REGISTRADO")
            elif txt.startswith("whatsapp "):
                msg = txt.split("whatsapp ", 1)[1].strip()
                if msg:
                    send_whatsapp(msg)
            elif txt.startswith("personalidad "):
                val = txt.split("personalidad ", 1)[1].strip()
                if "agresiva" in val:
                    globals()["PERSONALIDAD"] = "agresiva"
                    globals()["TTS_RATE"] = 170
                    globals()["TTS_VOLUME"] = 1.0
                    voz("PERSONALIDAD AGRESIVA")
                elif "amable" in val:
                    globals()["PERSONALIDAD"] = "amable"
                    globals()["TTS_RATE"] = 120
                    globals()["TTS_VOLUME"] = 0.8
                    voz("PERSONALIDAD AMABLE")
                else:
                    globals()["PERSONALIDAD"] = "pro"
                    globals()["TTS_RATE"] = 130
                    globals()["TTS_VOLUME"] = 1.0
                    voz("PERSONALIDAD PROFESIONAL")
            elif "redes" in txt:
                show_local_action("Redes", URL_REDES)
                voz("REDES DISPONIBLES")
            elif "soporte" in txt:
                show_local_action("Soporte", URL_SOPORTE)
                voz("SOPORTE DISPONIBLE")
            elif "estado" in txt or "estatus" in txt or "status" in txt:
                try:
                    append_log(f"Estado: Modo={open(LICENCIA).read().strip() if os.path.exists(LICENCIA) else MODO}, Segmento={open(SEGMENTO_FILE).read().strip() if os.path.exists(SEGMENTO_FILE) else SEGMENTO}, VozRate={TTS_RATE}, Volumen={TTS_VOLUME}")
                    voz("ESTADO MOSTRADO")
                except Exception:
                    pass
            elif "ayuda" in txt or "comandos" in txt:
                show_local_action("Comandos", "vender, virales, comprar/licencia/plus, envasador, demo, plus, abrir/abre, redes, soporte, estado, ayuda, limpiar, salir, activar subliminales, desactivar subliminales, volumen alto/medio/bajo, velocidad lenta/normal/rapida")
                voz("AYUDA MOSTRADA")
            elif "limpiar" in txt:
                try:
                    log.delete("1.0", "end")
                    voz("LIMPIADO")
                except Exception:
                    pass
            elif "salir" in txt or "cerrar" in txt:
                try:
                    voz("CERRANDO")
                    root.after(200, root.destroy)
                except Exception:
                    pass
            elif "activar subliminales" in txt or "subliminales activar" in txt or "sonido activar" in txt:
                try:
                    globals()["SUBLIMINAL_ENABLED"] = True
                    voz("SUBLIMINALES ACTIVADOS")
                except Exception:
                    pass
            elif "desactivar subliminales" in txt or "subliminales desactivar" in txt or "silenciar" in txt:
                try:
                    globals()["SUBLIMINAL_ENABLED"] = False
                    voz("SUBLIMINALES DESACTIVADOS")
                except Exception:
                    pass
            elif "volumen alto" in txt:
                globals()["TTS_VOLUME"] = 1.0
                voz("VOLUMEN ALTO")
            elif "volumen medio" in txt:
                globals()["TTS_VOLUME"] = 0.6
                voz("VOLUMEN MEDIO")
            elif "volumen bajo" in txt:
                globals()["TTS_VOLUME"] = 0.3
                voz("VOLUMEN BAJO")
            elif "velocidad lenta" in txt:
                globals()["TTS_RATE"] = 90
                voz("VELOCIDAD LENTA")
            elif "velocidad normal" in txt:
                globals()["TTS_RATE"] = 130
                voz("VELOCIDAD NORMAL")
            elif "velocidad rapida" in txt or "velocidad rápida" in txt:
                globals()["TTS_RATE"] = 170
                voz("VELOCIDAD RÁPIDA")

        def escuchar():
            while True:
                try:
                    data = stream.read(4000, exception_on_overflow=False)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        txt = result.get("text", "").lower()
                        handle_cmd(txt)
                except Exception:
                    time.sleep(0.1)
        threading.Thread(target=escuchar, daemon=True).start()
    except Exception:
        safe_status("VOZ OFFLINE - USA BOTONES")
else:
    safe_status("VOZ OFFLINE - USA BOTONES")

def on_close():
    if stream:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
    if p:
        try:
            p.terminate()
        except Exception:
            pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

ttk.Button(root, text="VENDER TODO", style="G.TButton", command=lambda: voz("VENDIENDO COMO BESTIA")).pack(pady=15)
ttk.Button(root, text="VIRALES + SUBLIMINALES", style="G.TButton", command=lambda: voz("GENERANDO MILLONES")).pack(pady=15)
ttk.Button(root, text="COMPRAR LICENCIA PLUS", style="G.TButton", command=lambda: show_local_action("Licencia PLUS", URL_COMPRA)).pack(pady=15)
ttk.Button(root, text="ACTIVAR ENVASADOR", style="G.TButton", command=lambda: (open(LICENCIA, "w").write("ENVASADOR_2025"), voz("MODO ENVASADOR ACTIVADO"))).pack(pady=15)
ttk.Button(root, text="SEGMENTO DEMO", style="G.TButton", command=lambda: (open(SEGMENTO_FILE, "w").write("DEMO"), voz("SEGMENTO DEMO ACTIVADO"))).pack(pady=15)
ttk.Button(root, text="SEGMENTO PLUS", style="G.TButton", command=lambda: (open(SEGMENTO_FILE, "w").write("PLUS"), voz("SEGMENTO PLUS ACTIVADO"))).pack(pady=15)

def test_watcher():
    path = os.path.join(BASE, "nexus_test_commands.txt")
    processed = False
    while True:
        try:
            if os.path.exists(path):
                data = open(path, "r", encoding="utf-8", errors="ignore").read().strip()
                if data:
                    for line in data.splitlines():
                        handle_cmd(line.strip().lower())
                    open(path, "w").write("")
                    processed = True
        except Exception:
            pass
        time.sleep(1.0)

threading.Thread(target=test_watcher, daemon=True).start()

root.mainloop()