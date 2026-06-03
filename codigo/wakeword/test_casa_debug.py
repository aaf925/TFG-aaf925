import os, sys, traceback
os.environ['PYTHONWARNINGS'] = 'ignore'

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "TFG Alejandro", "models")

print("=== TEST WAKE WORD: Casa (DEBUG) ===\n", flush=True)

print("Paso 1: Importando librerias...", flush=True)
import openwakeword
import sounddevice as sd
import numpy as np
print("  OK", flush=True)

print(f"Paso 2: Cargando modelo {os.path.join(MODELS_DIR, 'casa.onnx')}...", flush=True)
try:
    oww = openwakeword.Model(
        wakeword_models=[os.path.join(MODELS_DIR, "casa.onnx")],
        inference_framework="onnx",
        melspec_model_path=os.path.join(MODELS_DIR, "melspectrogram.onnx"),
        embedding_model_path=os.path.join(MODELS_DIR, "embedding_model.onnx")
    )
    print("  OK", flush=True)
except Exception as e:
    print(f"  ERROR cargando modelo: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print(f"Paso 3: Abriendo stream de audio...", flush=True)
CHUNK = 1280
UMBRAL = 0.6
cooldown = 0
predicted = False

try:
    stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16')
    stream.start()
    print("  Stream abierto. Escuchando...\n", flush=True)
    print("Di 'Casa' para probar. Ctrl+C para salir.\n", flush=True)

    while True:
        try:
            audio_chunk, _ = stream.read(CHUNK)
        except Exception as e:
            print(f"  Error leyendo audio: {e}", flush=True)
            continue

        if not predicted:
            try:
                oww.predict(audio_chunk.flatten())
                print(f"  Buffers disponibles: {list(oww.prediction_buffer.keys())}", flush=True)
                predicted = True
            except Exception as e:
                print(f"  Error en predict: {e}", flush=True)
                continue

        try:
            oww.predict(audio_chunk.flatten())
        except Exception as e:
            continue

        score = oww.prediction_buffer['casa'][-1]

        if cooldown > 0:
            cooldown -= 1
            continue

        if score > UMBRAL:
            print(f"\n  DETECTADO 'Casa'! (score={score:.3f})", flush=True)
            cooldown = 50
            print("  Esperando...", flush=True)
        elif score > 0.3:
            print(f"  Score: {score:.3f}", end="\r", flush=True)

except KeyboardInterrupt:
    print("\n\nSaliendo...", flush=True)
except Exception as e:
    print(f"\nError general: {e}", flush=True)
    traceback.print_exc()
finally:
    try:
        stream.stop()
        stream.close()
    except:
        pass
    print("Stream cerrado.", flush=True)
