import json, os, sys, random, wave, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "piper_tts"))
from piper_tts import PiperTTS

DOMOTIC_SENTENCES = [
    # === LUCES ===
    "enciende la luz del salon",
    "apaga la luz de la cocina",
    "enciende la luz del bano",
    "apaga la luz del dormitorio",
    "enciende todas las luces del salon",
    "apaga las luces de la cocina",
    "enciende la luz del aula",
    "apaga la entrada",
    "regula la luz del salon al cincuenta por ciento",
    "baja la intensidad al treinta",
    "sube la luz al ochenta por ciento",
    "pon la luz al maximo",
    "dimeriza la luz del salon",
    "enciende las luces del distribuidor",

    # === PERSIANAS Y ESTORES ===
    "sube la persiana de la cocina",
    "baja la persiana del bano",
    "sube el estor del salon",
    "baja el estor del dormitorio",
    "sube todas las persianas",
    "baja todas las persianas de la casa",
    "cierra las persianas",
    "abre los estores del aula",
    "levanta la persiana del bano",
    "extiende los estores del salon",

    # === CONSULTAS ===
    "que temperatura hace en el salon",
    "cual es la temperatura exterior",
    "dime la temperatura actual",
    "consulta el sensor de temperatura",
    "cuanto marca el sensor de clima",
    "que humedad hay en el salon",
    "cual es el nivel de CO2",
    "dame la temperatura del aula",

    # === CLIMATIZACION ===
    "sube la calefaccion",
    "baja el aire acondicionado",
    "pon la climatizacion a veintidos grados",
    "activa la calefaccion del salon",

    # === ESCENAS ===
    "hola buenos dias",
    "apaga todo al salir",
    "modo bienvenida",
    "activa la escena de salida",
    "buenas noches apaga todo",
    "preparate para el cine",

    # === VARIANTES CON ERRORES TIPICOS ===
    "enciende la perciana de la cocina",
    "apaga la luz del salón",  # con tilde
    "sube la persiana del cuarto",
    "enciende las luces del baño",
    "regula la persiana al treinta",  # mezcla persiana con regular
    "termostato del salon a veinte",
]

AUGMENTATIONS = [
    "",  # sin ruido
    " con ruido de fondo",
    " desde la cocina",
    " por favor",
    " rapido",
]

def generar_dataset(output_dir="dataset", num_clones=3, seed=42):
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    tts = PiperTTS()
    if not tts.disponible:
        print("Piper no disponible. Ejecuta primero la instalacion.")
        return

    samples = []
    for i, sentence in enumerate(DOMOTIC_SENTENCES):
        # generar variantes con distintos niveles de ruido
        for clone in range(num_clones):
            texto = sentence.strip()
            # añadir coletilla aleatoria
            if random.random() < 0.3:
                texto += random.choice(AUGMENTATIONS)

            filename = f"sample_{i:04d}_v{clone}.wav"
            filepath = os.path.join(output_dir, filename)

            # generar audio con Piper
            res = tts.decir(texto)
            if res and os.path.exists(res["archivo"]):
                import shutil
                shutil.copy(res["archivo"], filepath)
                samples.append({
                    "audio": filepath,
                    "text": texto,
                    "original": i < len(DOMOTIC_SENTENCES),
                })

            if (i * num_clones + clone) % 20 == 0:
                print(f"Generados {i * num_clones + clone + 1} samples...")

    # guardar metadatos
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    # dividir train/val
    random.shuffle(samples)
    split = int(len(samples) * 0.8)
    with open(os.path.join(output_dir, "train.json"), "w", encoding="utf-8") as f:
        json.dump(samples[:split], f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "val.json"), "w", encoding="utf-8") as f:
        json.dump(samples[split:], f, indent=2, ensure_ascii=False)

    print(f"\nDataset generado en '{output_dir}/'")
    print(f"  Total: {len(samples)} samples")
    print(f"  Train: {split}")
    print(f"  Val:   {len(samples) - split}")

if __name__ == "__main__":
    generar_dataset()
