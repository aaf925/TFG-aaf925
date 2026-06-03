"""
WHISPER FINE-TUNING PARA VOCABULARIO DOMÓTICO
==============================================
1. Sube la carpeta dataset/ al panel de archivos de Colab
2. Copia y pega TODO este archivo en una celda de Colab
3. Ejecuta con entorno de ejecución -> T4 GPU
4. Esperar ~10-15 minutos
5. El modelo se descargará automáticamente como whisper-finetuned-domotica.zip
"""

# === INSTALACIONES (descomenta en Colab) ===
# !pip install -q transformers datasets evaluate accelerate jiwer soundfile librosa

import json, os, torch, shutil, zipfile
from datasets import Dataset, Audio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
)
from evaluate import load as load_metric

# --- CONFIG ---
MODEL_BASE = "openai/whisper-tiny"
OUTPUT_DIR = "./whisper-finetuned-domotica"
TRAIN_JSON = "dataset/train.json"
VAL_JSON = "dataset/val.json"

# --- CARGAR DATOS ---
def cargar_json(path):
    data = json.load(open(path, encoding="utf-8"))
    for item in data:
        if "audio" in item:
            item["audio"] = item["audio"].replace("\\", "/")
    return data

def preparar_dataset(data_list, processor):
    dataset = Dataset.from_list(data_list)
    dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))
    def preparar(batch):
        audio = batch["audio"]["array"]
        batch["input_features"] = processor.feature_extractor(audio, sampling_rate=16000).input_features[0]
        batch["labels"] = processor.tokenizer(batch["text"]).input_ids
        return batch
    dataset = dataset.map(preparar, remove_columns=["audio", "text"])
    return dataset

# --- MAIN ---
def main():
    print(f"Cargando modelo base: {MODEL_BASE}")
    processor = WhisperProcessor.from_pretrained(MODEL_BASE, language="es", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_BASE)

    for param in model.model.encoder.parameters():
        param.requires_grad = False

    model.generation_config.forced_decoder_ids = None
    model.generation_config.suppress_tokens = []

    print("Preparando datasets...")
    train_data = cargar_json(TRAIN_JSON)
    val_data = cargar_json(VAL_JSON)

    train_dataset = preparar_dataset(train_data, processor)
    val_dataset = preparar_dataset(val_data, processor)

    args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=1,
        learning_rate=1e-5,
        warmup_steps=50,
        num_train_epochs=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        predict_with_generate=True,
        generation_max_length=128,
        logging_steps=10,
        report_to=["tensorboard"],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        push_to_hub=False,
    )

    wer_metric = load_metric("wer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": round(wer, 4)}

    def collator(features):
        input_features = torch.stack([torch.tensor(f.pop("input_features")) for f in features])
        labels = [torch.tensor(f.pop("labels")) for f in features]
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100)
        return {"input_features": input_features, "labels": labels}

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=processor.feature_extractor,
        data_collator=collator,
        compute_metrics=compute_metrics,
    )

    print("Iniciando entrenamiento...")
    trainer.train()
    print("Entrenamiento completado.")

    print(f"Guardando modelo en {OUTPUT_DIR}")
    trainer.save_model(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)

    metrics = trainer.evaluate()
    print(f"WER final en validacion: {metrics['eval_wer']:.4f}")

    # === COMPRIMIR Y DESCARGAR ===
    zip_path = "whisper-finetuned-domotica.zip"
    print(f"Comprimiendo modelo en {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for fn in files:
                fp = os.path.join(root, fn)
                zf.write(fp, arcname=os.path.relpath(fp, OUTPUT_DIR))
    print(f"Modelo comprimido: {zip_path} ({os.path.getsize(zip_path)/1024/1024:.1f} MB)")

    print("Descargando...")
    try:
        from google.colab import files
        files.download(zip_path)
    except ImportError:
        print("No estas en Colab. Descarga manual desde el panel de archivos.")

if __name__ == "__main__":
    main()
