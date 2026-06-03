import os, time, tempfile, threading
from pathlib import Path

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models", "piper_tts")
VOICE_ES = "es_ES-davefx-medium"
AUDIO_OUTPUT = os.path.join(tempfile.gettempdir(), "respuesta_piper.wav")

class PiperTTS:
    def __init__(self, voice=VOICE_ES):
        self.voice = voice
        self.piper = None
        self.disponible = False
        self._iniciar()

    def _iniciar(self):
        modelo_onnx = os.path.join(MODELS_DIR, f"{self.voice}.onnx")
        modelo_json = os.path.join(MODELS_DIR, f"{self.voice}.onnx.json")
        if not (os.path.exists(modelo_onnx) and os.path.exists(modelo_json)):
            print(f"  Modelo Piper no encontrado en {MODELS_DIR}")
            return
        try:
            import piper
            self.piper = piper.PiperVoice.load(modelo_onnx, config_path=modelo_json, use_cuda=False)
            self.disponible = True
        except ImportError:
            pass
        except Exception as e:
            print(f"  Error iniciando Piper: {e}")

    def decir(self, texto):
        if not self.disponible or not self.piper:
            return None
        try:
            import wave
            audio_stream = self.piper.synthesize(texto)
            audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_stream)
            with wave.open(AUDIO_OUTPUT, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(audio_bytes)
            return AUDIO_OUTPUT
        except Exception as e:
            print(f"  Error Piper: {e}")
            return None

class TTSManager:
    def __init__(self):
        self.piper = PiperTTS()
        self._pytts3_engine = None

    def _get_pyttsx3(self):
        if self._pytts3_engine is None:
            try:
                import pyttsx3
                self._pytts3_engine = pyttsx3.init()
            except:
                pass
        return self._pytts3_engine

    def decir(self, texto):
        print(f" Asistente: {texto}")

        archivo = self.piper.decir(texto)
        if archivo:
            try:
                import sounddevice as sd
                import soundfile as sf
                data, sr = sf.read(archivo)
                sd.play(data, sr)
                sd.wait()
                return
            except:
                pass
            try:
                import subprocess
                subprocess.Popen(["start", archivo], shell=True)
                return
            except:
                pass

        engine = self._get_pyttsx3()
        if engine:
            try:
                engine.say(texto)
                engine.runAndWait()
                return
            except:
                pass

        try:
            from gtts import gTTS
            import requests
            tts = gTTS(text=texto, lang='es')
            archivo_mp3 = os.path.join(tempfile.gettempdir(), "respuesta_gtts.mp3")
            tts.save(archivo_mp3)
            try:
                import sounddevice as sd
                import soundfile as sf
                data, sr = sf.read(archivo_mp3)
                sd.play(data, sr)
                sd.wait()
            except:
                pass
        except:
            pass
