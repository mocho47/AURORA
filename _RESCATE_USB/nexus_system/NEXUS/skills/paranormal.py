import time, random, pyttsx3

target_name = None
running = True

def speak(t):
    e = pyttsx3.init()
    e.setProperty('rate', 150)
    e.say(t)
    e.runAndWait()

def main(nombre=None):
    global target_name, running
    target_name = nombre.capitalize() if nombre else None
    running = True

    if target_name:
        speak(f"Detectando actividad paranormal alrededor de {target_name}...")
        print(f"=== PARANORMAL MODE ACTIVADO PARA {target_name} ===")
    else:
        speak("Detectando actividad paranormal...")
        print("=== PARANORMAL MODE ACTIVADO ===")

    try:
        while running:
            eventos_generales = [
                "Se escuchan pasos en el pasillo...",
                "Una sombra cruza la habitación...",
                "El aire se enfría repentinamente...",
                "Un susurro dice tu nombre...",
                "Luces parpadean sin explicación..."
            ]

            eventos_personalizados = [
                f"Siento una presencia detrás de {target_name}...",
                f"Una voz susurra: {target_name}...",
                f"Las sombras parecen seguir a {target_name}...",
                f"El ambiente se torna pesado cerca de {target_name}...",
                f"Algo observa fijamente a {target_name}..."
            ] if target_name else []

            if target_name and random.random() > 0.5:
                evento = random.choice(eventos_personalizados)
            else:
                evento = random.choice(eventos_generales)

            print(evento)
            speak(evento)
            time.sleep(random.randint(10, 25))

    except KeyboardInterrupt:
        speak("Actividad paranormal cancelada.")
        print("=== PARANORMAL MODE OFF ===")

def stop():
    global running
    running = False
    speak("Actividad paranormal cancelada.")
    print("=== PARANORMAL MODE OFF ===")