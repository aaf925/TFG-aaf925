# TTS local con Piper

## Qué hace
Sustituye gTTS (requiere internet) por Piper TTS, un motor de síntesis de voz neuronal que se ejecuta 100% en local sobre CPU.

## Ventajas
- **Sin dependencia cloud**: elimina la última pieza que requiere internet
- **Baja latencia**: genera audio en <1s en CPU moderna
- **Voces en español**: voces neuronales de calidad comparable a gTTS
- **Privacidad**: el texto nunca sale del equipo

## Archivos

| Archivo | Descripción |
|---|---|
| `piper_tts.py` | Clase `PiperTTS` (wrapper), más wrappers de `gTTS` y `pyttsx3` para comparativa. |
| `models/` | Modelos ONNX descargados automáticamente desde HuggingFace (~50MB). |

## Instalación
```bash
pip install piper-tts sounddevice soundfile
```

## Cómo usar

### Modo interactivo
```bash
cd mejoras/piper_tts
python piper_tts.py
```
Escribe texto y lo escuchas por los altavoces.

### Comparativa con otros motores
```bash
python piper_tts.py --comparativa
```
Genera una tabla con tiempos de Piper vs gTTS vs pyttsx3 para 4 textos de prueba.

### Integrar en el asistente
```python
from piper_tts import PiperTTS

tts = PiperTTS()

def decir(texto):
    res = tts.decir(texto)
    if res:
        tts.reproducir(texto)
```

## Voces disponibles
- `es_ES-davefx-medium` (por defecto, ~50MB, buena calidad)
- `es_ES-sharvard-medium` (alternativa)
- `es_ES-carlfm-x_low` (más ligera, ~20MB, menor calidad)

Se cambian al instanciar: `PiperTTS(voice="es_ES-sharvard-medium")`
