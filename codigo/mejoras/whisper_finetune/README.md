# Fine-tune de Whisper para vocabulario domótico

## Qué hace
Whisper comete errores con palabras técnicas del ámbito domótico (persiana, dimerización, climatización, estor, etc.). Este fine-tune entrena Whisper tiny con ~150 muestras sintéticas en español para mejorar la precisión en este dominio específico.

## Proceso
1. **Generar dataset sintético** (`generar_dataset.py`): usa Piper TTS para crear audios de ~50 órdenes domóticas con 3 variantes cada una (~150 muestras total). Se guardan en `dataset/` con metadatos.
2. **Fine-tune** (`finetune_colab.py`): entrena Whisper tiny durante 10 épocas. El encoder se congela para ahorrar memoria. Solo se entrena el decoder.
3. **Evaluar** (`evaluar_whisper.py`): compara Whisper base vs fine-tuned sobre 16 órdenes de prueba, midiendo WER (Word Error Rate) y latencia.

## Archivos

| Archivo | Descripción |
|---|---|
| `generar_dataset.py` | Genera dataset sintético usando Piper TTS. |
| `finetune_colab.py` | Script para Google Colab que fine-tunea Whisper tiny. |
| `evaluar_whisper.py` | Evalúa y compara modelo base vs fine-tuned. |
| `dataset/` | Audios y metadatos generados (se crea al ejecutar `generar_dataset.py`). |

## Cómo usar

### 1. Generar dataset
```bash
cd mejoras/whisper_finetune
python generar_dataset.py
```
Crea ~150 samples en `dataset/` usando Piper TTS.

### 2. Fine-tune (en Google Colab)
Sube la carpeta `dataset/` a Colad y ejecuta `finetune_colab.py`, o en local si tienes GPU:
```bash
pip install -q transformers datasets evaluate accelerate jiwer
python finetune_colab.py
```
El modelo fine-tuneado se guarda en `whisper-finetuned-domotica/`.

### 3. Evaluar
```bash
python evaluar_whisper.py
```
Compara Whisper tiny base vs fine-tuned sobre 16 órdenes de prueba.
Genera `resultados_evaluacion_whisper.json` con WER y tiempos.

## Resultados esperados
- WER base en vocabulario domótico: ~15–30% (errores en palabras técnicas)
- WER fine-tuned: ~5–15% (mejora significativa en persiana, estor, etc.)
- Latencia: similar (~0.5-2s en CPU con tiny)
