import os, openwakeword, sounddevice as sd
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "TFG Alejandro", "models")

print("=== TEST WAKE WORD: Alexa ===\n")

oww = openwakeword.Model(
    wakeword_models=[os.path.join(MODELS_DIR, "alexa_v0.1.onnx")],
    inference_framework="onnx",
    melspec_model_path=os.path.join(MODELS_DIR, "melspectrogram.onnx"),
    embedding_model_path=os.path.join(MODELS_DIR, "embedding_model.onnx")
)

print("Di 'Alexa' para probar. Ctrl+C para salir.\n")
CHUNK = 1280
UMBRAL = 0.6
cooldown = 0

with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
    while True:
        try:
            audio_chunk, _ = stream.read(CHUNK)
        except:
            continue

        try:
            oww.predict(audio_chunk.flatten())
        except:
            continue

        score = oww.prediction_buffer['alexa_v0.1'][-1]

        if cooldown > 0:
            cooldown -= 1
            continue

        if score > UMBRAL:
            print(f"\n[OK]  DETECTADO 'Alexa'! (score={score:.3f})")
            cooldown = 50
            print("  Esperando...")
        elif score > 0.3:
            print(f"  Score: {score:.3f}", end="\r")
