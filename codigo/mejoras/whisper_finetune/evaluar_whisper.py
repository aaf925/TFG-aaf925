import json, os, sys, time, warnings, numpy as np
warnings.filterwarnings("ignore")

TEST_COMMANDS = [
    "enciende la luz del salon",
    "apaga la persiana de la cocina",
    "sube el estor del dormitorio",
    "que temperatura hace",
    "regula la luz al cincuenta",
    "baja todas las persianas",
    "enciende todas las luces del salon",
    "dime la temperatura exterior",
    "sube la persiana del bano",
    "apaga la luz de la entrada",
    "cierra los estores del aula",
    "consulta el sensor de temperatura",
    "pon la calefaccion a veintidos grados",
    "abre las persianas de la cocina",
    "modo bienvenida",
    "apaga todo al salir",
]

def transcribir(archivo, pipe):
    import scipy.io.wavfile
    rate, data = scipy.io.wavfile.read(archivo)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / 32768.0
    result = pipe(data, generate_kwargs={"language": "es", "task": "transcribe"})
    return result["text"].strip().lower()

def evaluar():
    print("=== Evaluacion Whisper: Base vs Fine-tuned ===\n")

    # Cargar pipelines
    print("Cargando Whisper tiny (base)...")
    from transformers import pipeline
    base_pipe = pipeline("automatic-speech-recognition",
                         model="openai/whisper-tiny",
                         device=-1)  # CPU

    finetuned_dir = os.path.join(os.path.dirname(__file__), "whisper-finetuned-domotica")
    finetune_pipe = None
    if os.path.exists(finetuned_dir):
        print(f"Cargando fine-tuned desde {finetuned_dir}...")
        try:
            finetune_pipe = pipeline("automatic-speech-recognition",
                                     model=finetuned_dir,
                                     device=-1)
        except Exception as e:
            print(f"  Error cargando modelo fine-tuned: {e}")
    else:
        print(f"  No se encontro {finetuned_dir}. Solo se evaluara el modelo base.")

    # Generar audio con Piper
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "piper_tts"))
    from piper_tts import PiperTTS
    tts = PiperTTS()
    if not tts.disponible:
        print("Piper no disponible. Prueba con modo solo texto.")

    resultados = []

    for i, texto in enumerate(TEST_COMMANDS):
        print(f"\n[{i+1}/{len(TEST_COMMANDS)}] '{texto}'")

        # generar audio
        if not tts.disponible:
            print("  ERROR: Piper no disponible")
            continue
        res = tts.decir(texto)
        if not res or not os.path.exists(res["archivo"]):
            print("  ERROR: no se pudo generar audio")
            continue
        archivo = res["archivo"]

        # transcribir con base
        t0 = time.time()
        trans_base = transcribir(archivo, base_pipe)
        t_base = time.time() - t0

        # transcribir con fine-tuned
        trans_ft = None
        t_ft = None
        if finetune_pipe:
            t0 = time.time()
            trans_ft = transcribir(archivo, finetune_pipe)
            t_ft = time.time() - t0

        # word error rate simple
        def wer(hyp, ref):
            h = hyp.split()
            r = ref.split()
            if not r:
                return 0.0
            correct = sum(1 for hw, rw in zip(h, r) if hw == rw)
            return 1.0 - correct / max(len(r), 1)

        wer_base = wer(trans_base, texto)
        wer_ft = wer(trans_ft, texto) if trans_ft else None

        resultados.append({
            "texto": texto,
            "trans_base": trans_base,
            "wer_base": round(wer_base, 3),
            "tiempo_base": round(t_base, 3),
            "trans_finetune": trans_ft,
            "wer_finetune": round(wer_ft, 3) if wer_ft is not None else None,
            "tiempo_finetune": round(t_ft, 3) if t_ft else None,
        })

        print(f"  Base:      '{trans_base}' (WER={wer_base:.2f}, {t_base:.2f}s)")
        if trans_ft:
            print(f"  Finetuned: '{trans_ft}' (WER={wer_ft:.2f}, {t_ft:.2f}s)")

    # resumen
    print("\n=== RESUMEN ===")
    wer_base_total = sum(r["wer_base"] for r in resultados) / len(resultados)
    print(f"WER medio base: {wer_base_total:.3f}")
    if resultados[0]["wer_finetune"] is not None:
        wer_ft_total = sum(r["wer_finetune"] for r in resultados) / len(resultados)
        mejora = (wer_base_total - wer_ft_total) / wer_base_total * 100 if wer_base_total > 0 else 0
        print(f"WER medio finetuned: {wer_ft_total:.3f}")
        print(f"Mejora relativa: {mejora:.1f}%")

    with open(os.path.join(os.path.dirname(__file__), "resultados_evaluacion_whisper.json"),
              "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nResultados guardados en resultados_evaluacion_whisper.json")

if __name__ == "__main__":
    evaluar()
