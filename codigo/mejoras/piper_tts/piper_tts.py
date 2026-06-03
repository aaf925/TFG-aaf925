import os, time, tempfile, subprocess, threading, json
from pathlib import Path

# --- CONFIGURACION ---
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
VOICE_ES = "es_ES-davefx-medium"  # voz en español, calidad media

AUDIO_OUTPUT = os.path.join(tempfile.gettempdir(), "respuesta_piper.wav")

def descargar_modelo(voice=VOICE_ES):
    modelo_onnx = os.path.join(MODELS_DIR, f"{voice}.onnx")
    modelo_json = os.path.join(MODELS_DIR, f"{voice}.onnx.json")
    if os.path.exists(modelo_onnx) and os.path.exists(modelo_json):
        return modelo_onnx, modelo_json

    print(f"Descargando modelo Piper: {voice}...")
    os.makedirs(MODELS_DIR, exist_ok=True)

    # voice = "es_ES-davefx-medium"  -> locale=es_ES, name=davefx, quality=medium
    # HF dir: es/{locale}/{name}/{quality}/{voice}.onnx
    parts = voice.split("-")
    locale = parts[0]  # es_ES
    name = parts[1]    # davefx
    quality = parts[2]  # medium
    base_hf = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{locale[:2]}/{locale}/{name}/{quality}/{voice}"
    urls = {
        modelo_onnx: f"{base_hf}.onnx",
        modelo_json: f"{base_hf}.onnx.json",
    }

    import urllib.request
    for dest, url in urls.items():
        if not os.path.exists(dest):
            urllib.request.urlretrieve(url, dest)
            print(f"  Descargado: {os.path.basename(dest)}")

    return modelo_onnx, modelo_json

class PiperTTS:
    def __init__(self, voice=VOICE_ES):
        self.voice = voice
        self.modelo_onnx = None
        self.modelo_json = None
        self.disponible = False
        self._iniciar()

    def _iniciar(self):
        try:
            modelo_onnx, modelo_json = descargar_modelo(self.voice)
            import piper
            self.piper = piper.PiperVoice.load(modelo_onnx, config_path=modelo_json, use_cuda=False)
            self.disponible = True
            print(f"Piper TTS listo: {self.voice}")
        except ImportError:
            print("piper-tts no instalado. Ejecuta: pip install piper-tts")
        except Exception as e:
            print(f"Error iniciando Piper: {e}")

    def decir(self, texto):
        if not self.disponible:
            return None
        try:
            t0 = time.time()
            import wave
            import numpy as np
            audio_stream = self.piper.synthesize(texto)
            audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_stream)
            with wave.open(AUDIO_OUTPUT, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(audio_bytes)
            t_total = time.time() - t0
            return {"archivo": AUDIO_OUTPUT, "duracion": round(t_total, 3), "texto": texto}
        except Exception as e:
            print(f"Error Piper: {e}")
            return None

    def reproducir(self, texto):
        res = self.decir(texto)
        if not res:
            return False
        try:
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(res["archivo"])
            sd.play(data, sr)
            sd.wait()
            return True
        except ImportError:
            subprocess.Popen(["start", res["archivo"]], shell=True)
            return True

    def detener(self):
        import sounddevice as sd
        sd.stop()

    @property
    def requiere_internet(self):
        return False

# --- COMPARATIVA CON OTRAS OPCIONES TTS ---

class GttsWrapper:
    def __init__(self):
        self.disponible = True

    def decir(self, texto):
        try:
            from gtts import gTTS
            import tempfile
            t0 = time.time()
            tts = gTTS(text=texto, lang="es")
            path = os.path.join(tempfile.gettempdir(), "respuesta_gtts.mp3")
            tts.save(path)
            t_total = time.time() - t0
            return {"archivo": path, "duracion": round(t_total, 3), "texto": texto}
        except Exception as e:
            print(f"Error gTTS: {e}")
            return None

    @property
    def requiere_internet(self):
        return True

class Pyttsx3Wrapper:
    def __init__(self):
        self.disponible = True

    def decir(self, texto):
        try:
            import pyttsx3
            import tempfile
            t0 = time.time()
            engine = pyttsx3.init()
            path = os.path.join(tempfile.gettempdir(), "respuesta_pyttsx3.wav")
            engine.save_to_file(texto, path)
            engine.runAndWait()
            t_total = time.time() - t0
            return {"archivo": path, "duracion": round(t_total, 3), "texto": texto}
        except Exception as e:
            print(f"Error pyttsx3: {e}")
            return None

    @property
    def requiere_internet(self):
        return False

def comparativa():
    textos = [
        "Hecho.",
        "Enciendo la luz del salon.",
        "La temperatura actual es de veintidos grados.",
        "Buenos dias, bienvenido a casa.",
    ]

    motores = {
        "Piper (local)": PiperTTS(),
        "gTTS (cloud)": GttsWrapper(),
        "pyttsx3 (local)": Pyttsx3Wrapper(),
    }

    print(f"{'Motor':<20} {'Texto':<40} {'Tiempo':<10} {'Internet':<10}")
    print("-" * 80)

    resultados = []
    for nombre, motor in motores.items():
        for texto in textos:
            res = motor.decir(texto)
            if res:
                print(f"{nombre:<20} {res['texto'][:38]:<40} {res['duracion']:<10}s {str(not motor.requiere_internet):<10}")
                resultados.append({
                    "motor": nombre,
                    "texto": texto,
                    "tiempo": res["duracion"],
                    "local": not motor.requiere_internet,
                })
            else:
                print(f"{nombre:<20} {texto[:38]:<40} {'ERROR':<10}")

    with open("resultados_comparativa_tts.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en resultados_comparativa_tts.json")
    return resultados

if __name__ == "__main__":
    import sys
    if "--comparativa" in sys.argv:
        comparativa()
    else:
        print("=== MODO DEMO: Piper TTS ===")
        tts = PiperTTS()
        if not tts.disponible:
            print("Piper no disponible. Prueba: pip install piper-tts")
            sys.exit(1)
        while True:
            texto = input("Texto a decir (o 'salir'): ").strip()
            if texto in ("salir", "exit"):
                break
            if not texto:
                continue
            res = tts.decir(texto)
            if res:
                print(f"Generado en {res['duracion']}s: {res['archivo']}")
                r = input("Reproducir? [S/n]: ").strip().lower()
                if r != "n":
                    tts.reproducir(texto)
