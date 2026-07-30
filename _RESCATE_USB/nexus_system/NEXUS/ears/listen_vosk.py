from vosk import Model, KaldiRecognizer
import pyaudio

model = Model(r"D:\NEXUS_SYSTEM\NEXUS\ears\model_es")
rec = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Habla...")
while True:
    data = stream.read(4000, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        print(rec.Result())
        break

stream.stop_stream()
stream.close()
p.terminate()