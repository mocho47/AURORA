import pyttsx3

_engine = None
_modo = 'seguro'

def _ensure():
    global _engine
    if _engine is not None:
        return
    try:
        e = pyttsx3.init()
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
        _engine = e
    except Exception:
        _engine = None

def establecer_modo_narracion(modo: str):
    global _modo
    m = (modo or '').lower().strip()
    if m in ('fluido', 'seguro', 'legado'):
        _modo = m

def narrar(texto: str):
    _ensure()
    if _engine is None:
        return
    rate = 180
    if _modo == 'fluido':
        rate = 210
    elif _modo == 'seguro':
        rate = 175
    elif _modo == 'legado':
        rate = 150
    try:
        _engine.setProperty('rate', rate)
    except Exception:
        pass
    try:
        _engine.say(texto)
        _engine.runAndWait()
    except Exception:
        pass