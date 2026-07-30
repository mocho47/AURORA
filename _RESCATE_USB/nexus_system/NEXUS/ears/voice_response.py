import time, random, pyttsx3, sys, os
print("NEXUS arrancó correctamente, esperando entrada de voz...")
target_name = None
gender = "neutral"
name_mentions = 0
running = True

def speak(text, rate=150, volume=1.0):
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[random.randint(0, len(voices)-1)].id)
    engine.say(text)
    engine.runAndWait()

def detect_gender(nombre):
    if nombre.endswith("a"):
        return "femenino"
    elif nombre.endswith("o"):
        return "masculino"
    else:
        return "neutral"

def glitch_print(text):
    # Simula parpadeo/glitch en pantalla
    sys.stdout.write("\033[2J\033[H")  # limpia pantalla
    glitch = ''.join(random.choice([c, c.upper(), '#', '%', '¿']) for c in text)
    print(glitch)

def reverse_text(text):
    return text[::-1]

def broken_phrase(text):
    words = text.split()
    if words:
        idx = random.randint(0, len(words)-1)
        words[idx] = words[idx][:2] + "..." + words[idx]
    return " ".join(words)

def main(nombre=None):
    global target_name, gender, name_mentions, running
    target_name = nombre.capitalize() if nombre else None
    gender = detect_gender(target_name) if target_name else "neutral"
    name_mentions = 0
    running = True

    if target_name:
        speak(f"Detectando actividad paranormal alrededor de {target_name}...", rate=130)
        print(f"=== PARANORMAL MODE ACTIVADO PARA {target_name} ===")
    else:
        speak("Detectando actividad paranormal...", rate=130)
        print("=== PARANORMAL MODE ACTIVADO ===")

    try:
        while running:
            # Frases base
            generales = [
                "Se escuchan pasos en el pasillo...",
                "Una sombra cruza la habitación...",
                "El aire se enfría repentinamente...",
                "Un susurro dice tu nombre...",
                "Luces parpadean sin explicación..."
            ]

            if target_name:
                if name_mentions < 2:
                    personalizados = [
                        f"Una voz susurra: {target_name}...",
                        f"Siento una presencia detrás de {target_name}..."
                    ]
                    name_mentions += 1
                else:
                    if gender == "femenino":
                        personalizados = [
                            "Ella siente que alguien la observa...",
                            "Una sombra se acerca a ella...",
                            "El ambiente se torna pesado cerca de ella..."
                        ]
                    elif gender == "masculino":
                        personalizados = [
                            "Él siente que alguien lo observa...",
                            "Una sombra se acerca a él...",
                            "El ambiente se torna pesado cerca de él..."
                        ]
                    else:
                        personalizados = [
                            "Esa persona siente que alguien la observa...",
                            "Una sombra se acerca a esa persona...",
                            "El ambiente se torna pesado cerca de esa persona..."
                        ]
            else:
                personalizados = []

            # Selección aleatoria
            evento = random.choice(personalizados if target_name and random.random() > 0.5 else generales)

            # Efectos aleatorios
            efecto = random.choice(["normal", "reverse", "broken", "glitch", "scream", "laugh"])
            if efecto == "reverse":
                evento = reverse_text(evento)
                speak(evento, rate=120)
            elif efecto == "broken":
                evento = broken_phrase(evento)
                speak(evento, rate=100)
            elif efecto == "glitch":
                glitch_print(evento)
                speak(evento, rate=140)
            elif efecto == "scream" and target_name:
                evento = f"¡¡¡{target_name.upper()}!!!"
                speak(evento, rate=200, volume=1.0)
            elif efecto == "laugh":
                evento = "JAJAJAJAJAJAJA..."
                speak(evento, rate=180)
            else:
                speak(evento, rate=random.randint(100,180))

            print(evento)
            time.sleep(random.randint(8, 20))

    except KeyboardInterrupt:
        stop()

def stop():
    global running
    running = False
    speak("Actividad paranormal cancelada.", rate=130)
    print("=== PARANORMAL MODE OFF ===")