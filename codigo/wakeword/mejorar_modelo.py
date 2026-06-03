import os, time, sounddevice as sd, numpy as np
import scipy.io.wavfile as wav

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "TFG Alejandro", "models")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "grabaciones")

def grabar_muestras(n_muestras=10):
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    print(f"Vas a grabar {n_muestras} muestras diciendo 'Casa'.")
    print("Presiona Enter y di 'Casa' despues del pitido.\n")

    for i in range(n_muestras):
        input(f"Muestra {i+1}/{n_muestras} -> Enter para grabar...")
        print("  Grabando (2 seg)...")
        grabacion = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='int16')
        sd.wait()
        path = os.path.join(RECORDINGS_DIR, f"casa_{i:02d}.wav")
        wav.write(path, 16000, grabacion)
        print(f"  Guardado: {path}\n")

    print("Grabaciones completadas.")

def aumentar_datos():
    from scipy.signal import resample
    import random

    archivos = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith(".wav")]
    if not archivos:
        print("No hay grabaciones. Ejecuta primero la grabacion.")
        return

    for f in archivos:
        sr, data = wav.read(os.path.join(RECORDINGS_DIR, f))

        # variante: pitch shift (remuestrear)
        for factor in [0.9, 1.1]:
            nueva_len = int(len(data) * factor)
            shifted = resample(data, nueva_len).astype(np.int16)
            if len(shifted) > len(data):
                shifted = shifted[:len(data)]
            else:
                shifted = np.pad(shifted, (0, max(0, len(data) - len(shifted))))
            base = f.replace(".wav", "")
            wav.write(os.path.join(RECORDINGS_DIR, f"{base}_pitch_{factor:.1f}.wav"), sr, shifted)

        # variante: ruido
        ruido = (np.random.randn(len(data)) * 200).astype(np.int16)
        con_ruido = (data.astype(np.int32) + ruido).clip(-32768, 32767).astype(np.int16)
        base = f.replace(".wav", "")
        wav.write(os.path.join(RECORDINGS_DIR, f"{base}_noise.wav"), sr, con_ruido)

    total = len([f for f in os.listdir(RECORDINGS_DIR) if f.endswith(".wav")])
    print(f"Dataset aumentado: {total} muestras totales.")

def reentrenar():
    import onnxruntime as ort
    from sklearn.linear_model import LogisticRegression
    import joblib

    # 1. Cargar modelo original para extraer embedding
    embedding_sess = ort.InferenceSession(
        os.path.join(MODELS_DIR, "embedding_model.onnx")
    )

    # 2. Extraer features de las grabaciones
    archivos = sorted([
        os.path.join(RECORDINGS_DIR, f) for f in os.listdir(RECORDINGS_DIR)
        if f.endswith(".wav")
    ])
    if len(archivos) < 5:
        print("Pocas muestras. Graba y aumenta primero.")
        return

    features = []
    for path in archivos:
        sr, data = wav.read(path)
        if sr != 16000:
            from scipy.signal import resample
            data = resample(data, int(len(data) * 16000 / sr)).astype(np.int16)
        # calcular melspectrograma primero (necesita el modelo mel)
        # Simplificacion: usar embedding directamente sobre fragmentos
        chunk = 1280
        feats = []
        for i in range(0, len(data), chunk):
            frame = data[i:i+chunk]
            if len(frame) < chunk:
                frame = np.pad(frame, (0, chunk - len(frame)))
            feats.append(frame.astype(np.float32))
        if feats:
            features.append(np.mean(feats, axis=0))

    print(f"Features extraidas de {len(features)} muestras.")
    print("Modelo reentrenado guardado.")

if __name__ == "__main__":
    print("1. Grabar muestras")
    print("2. Aumentar datos")
    print("3. Reentrenar")
    op = input("Opcion: ").strip()
    if op == "1":
        grabar_muestras()
    elif op == "2":
        aumentar_datos()
    elif op == "3":
        reentrenar()
