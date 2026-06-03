"""
ENTRENAMIENTO DE WAKE WORD "CASA" CON VOZ ESPAÑOLA
===================================================
Usa Piper TTS directamente con voz española para generar muestras sintéticas,
luego entrena con openWakeWord.

INSTRUCCIONES:
1. Google Colab -> Nuevo notebook -> Entorno de ejecución -> T4 GPU
2. Sube este archivo al panel de archivos de Colab
3. En una celda:    %run colab_casa_espanol.py
4. Cuando pida grabaciones reales, súbelas
5. Esperar ~30-45 min
6. Se descargará casa.onnx automáticamente
"""

import os, sys, yaml, uuid, shutil, subprocess, wave, random, math, copy, gc
import numpy as np
from pathlib import Path
from tqdm import tqdm
import locale
locale.getpreferredencoding = lambda: "UTF-8"

def sh(cmd, check=False):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:2000])
    if result.stderr:
        print("[STDERR]", result.stderr[:2000])
    if result.returncode != 0:
        print(f"  [ERROR] Codigo de retorno: {result.returncode}")
        if check:
            raise RuntimeError(f"Comando fallo con codigo {result.returncode}")
    return result.returncode

# ============================================================
TARGET_WORD = "casa"
NUM_EXAMPLES = 5000
TRAIN_STEPS = 15000
FP_PENALTY = 1500

print(f"Palabra: {TARGET_WORD}")
print(f"Muestras sinteticas: {NUM_EXAMPLES}")
print(f"Pasos: {TRAIN_STEPS}")

# ============================================================
# 1. INSTALAR DEPENDENCIAS
# ============================================================
print("\n=== INSTALANDO DEPENDENCIAS ===")
sh("git clone https://github.com/dscripka/openwakeword")
# No usar pip install - editable install roto en Python 3.12 + Colab
# En su lugar, añadir ruta directa al sys.path al importar
sh("pip install piper-tts piper-phonemize-cross webrtcvad")
sh("pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu121")
sh("pip install mutagen==1.47.0 torchinfo==1.8.0 torchmetrics==1.2.0")
sh("pip install speechbrain==0.5.14 audiomentations==0.33.0 torch-audiomentations==0.11.0 acoustics==0.2.6")
sh("pip install onnxruntime==1.22.1 onnx==1.19.1 onnxsim")
sh("pip install pronouncing")

# generate_samples solo se importa (no se llama en --train_model), stub minimo
with open("generate_samples.py", "w") as f:
    f.write("""def generate_samples(text=None, max_samples=None, batch_size=None,
               noise_scales=None, noise_scale_ws=None, length_scales=None,
               output_dir=None, auto_reduce_batch_size=None, file_names=None):
    pass
""")

# Descargar modelos base openWakeWord
os.makedirs("./openwakeword/openwakeword/resources/models", exist_ok=True)
sh("wget -q https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx -O ./openwakeword/openwakeword/resources/models/embedding_model.onnx")
sh("wget -q https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.tflite -O ./openwakeword/openwakeword/resources/models/embedding_model.tflite")
sh("wget -q https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx -O ./openwakeword/openwakeword/resources/models/melspectrogram.onnx")
sh("wget -q https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.tflite -O ./openwakeword/openwakeword/resources/models/melspectrogram.tflite")

# ============================================================
# 2. VOZ ESPAÑOLA PIPER
# ============================================================
print("\n=== DESCARGANDO VOZ ESPAÑOLA: es_ES-sharvard-medium ===")
sh("wget -q 'https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx' -O es_ES-sharvard-medium.onnx")
sh("wget -q 'https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json' -O es_ES-sharvard-medium.onnx.json")
assert os.path.exists("es_ES-sharvard-medium.onnx"), "Fallo descarga voz"

# ============================================================
# 3. GENERAR CLIPS SINTÉTICOS CON PIPER + ESPAÑOL
# ============================================================
print(f"\n=== GENERANDO {NUM_EXAMPLES} CLIPS CON VOZ ESPAÑOLA ===")

# Importar piper-tts
import piper

output_dir = f"./my_custom_model/{TARGET_WORD}/positive_train"
os.makedirs(output_dir, exist_ok=True)

# Cargar modelo Piper
voice = piper.PiperVoice.load(
    "es_ES-sharvard-medium.onnx",
    config_path="es_ES-sharvard-medium.onnx.json",
    use_cuda=False
)

# Variaciones de entonación para "casa"
textos = [
    "casa",
    "casa.",  # tono neutro
]

n_existentes = len([f for f in os.listdir(output_dir) if f.endswith(".wav")])
n_generar = max(0, NUM_EXAMPLES - n_existentes)

if n_generar > 0:
    for i in tqdm(range(n_generar), desc="Generando clips"):
        # Pequeña variación: texto alternado + random seed
        texto = textos[i % len(textos)]

        # Sintetizar con Piper
        audio_stream = voice.synthesize(texto)
        audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_stream)

        # Añadir pequeña variación de volumen aleatoria
        audio_arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        factor = 0.7 + random.random() * 0.6  # 0.7 a 1.3
        audio_arr = (audio_arr * factor).clip(-32768, 32767).astype(np.int16)

        # Recortar silencios al inicio/final (opcional)
        # Guardar con nombre único
        filename = f"synth_{uuid.uuid4().hex[:12]}.wav"
        filepath = os.path.join(output_dir, filename)
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(audio_arr.tobytes())

    print(f"Generados {n_generar} clips sinteticos en '{output_dir}'")
else:
    print(f"Ya existen {n_existentes} clips, no hace falta generar mas.")

total_clips = len([f for f in os.listdir(output_dir) if f.endswith(".wav")])
print(f"Total clips en positive_train: {total_clips}")

# ============================================================
# 4. DATOS DE RUIDO / RIR
# ============================================================
print("\n=== DESCARGANDO DATOS DE RUIDO ===")

import scipy.io.wavfile

if not os.path.exists("./mit_rirs"):
    os.mkdir("./mit_rirs")

# Asegurar que existe el directorio de impulse_responses
os.makedirs("./openwakeword/openwakeword/resources/impulse_responses", exist_ok=True)

if not os.path.exists("./synthetic_noise"):
    os.makedirs("./synthetic_noise", exist_ok=True)
    n_noise_clips = 500
    print(f"Generando {n_noise_clips} clips de ruido sintetico...")
    sr = 16000
    for i in range(n_noise_clips):
        duration = random.uniform(0.5, 2.0)
        n_samples = int(sr * duration)
        noise_type = random.choice(["white", "pink", "brown"])
        if noise_type == "white":
            noise = np.random.randn(n_samples).astype(np.float32)
        elif noise_type == "pink":
            n_half = n_samples // 2 + 1
            white = np.random.randn(n_half).astype(np.complex64)
            f = np.fft.rfftfreq(n_samples)
            f[0] = 1
            pink_spec = white / np.sqrt(f)
            noise = np.fft.irfft(pink_spec, n=n_samples).real
        else:  # brown
            white = np.random.randn(n_samples).astype(np.float32)
            noise = np.cumsum(white)
            noise = noise / (np.max(np.abs(noise)) + 1e-10)
        # normalizar
        noise = noise / (np.max(np.abs(noise)) + 1e-10)
        noise = (noise * 0.3 * 32767).clip(-32768, 32767).astype(np.int16)
        scipy.io.wavfile.write(f"./synthetic_noise/noise_{i:04d}.wav", sr, noise)
    print(f"Generados {n_noise_clips} clips de ruido sintetico en ./synthetic_noise/")
    del noise; gc.collect()

if not os.path.exists("openwakeword_features_ACAV100M_2000_hrs_16bit.npy"):
    sh("wget -q https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy")
if not os.path.exists("validation_set_features.npy"):
    sh("wget -q https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/validation_set_features.npy")

# ============================================================
# 5. CONFIGURAR ENTRENAMIENTO
# ============================================================
print("\n=== CONFIGURANDO ENTRENAMIENTO ===")

config = yaml.load(open("openwakeword/examples/custom_model.yml", "r").read(), yaml.Loader)

# Config básica
config["target_phrase"] = [TARGET_WORD]
config["model_name"] = TARGET_WORD
config["n_samples"] = NUM_EXAMPLES
config["n_samples_val"] = max(500, NUM_EXAMPLES // 10)
config["steps"] = TRAIN_STEPS
config["output_dir"] = "./my_custom_model"
config["max_negative_weight"] = FP_PENALTY
# La ruta a piper-sample-generator (no necesitamos generate_clips, pero train.py lo requiere)
config["piper_sample_generator_path"] = "."

# Datos de ruido
background_paths = []
if os.path.exists("./synthetic_noise") and len(os.listdir("./synthetic_noise")) > 0:
    background_paths.append("./synthetic_noise")
config["background_paths"] = background_paths
config["background_paths_duplication_rate"] = [1] * len(background_paths) if background_paths else []

# RIR
if os.path.exists("./mit_rirs") and len(os.listdir("./mit_rirs")) > 0:
    config["rir_paths"] = ["./mit_rirs"]
else:
    config["rir_paths"] = ["./openwakeword/openwakeword/resources/impulse_responses"]

config["false_positive_validation_data_path"] = "validation_set_features.npy"
config["feature_data_files"] = {"ACAV100M_sample": "openwakeword_features_ACAV100M_2000_hrs_16bit.npy"}

# Guardar
with open("my_model.yaml", "w") as f:
    yaml.dump(config, f)

print("Configuracion guardada en my_model.yaml")

# ============================================================
# 6. AÑADIR GRABACIONES REALES (AUTO-DETECTAR)
# ============================================================
clips_dir = f"./my_custom_model/{TARGET_WORD}/positive_train"
os.makedirs(clips_dir, exist_ok=True)

reales_existentes = [f for f in os.listdir(clips_dir) if f.startswith("real_")]
if reales_existentes:
    print(f"✓ {len(reales_existentes)} grabaciones reales ya existen en positive_train, saltando carga")
else:
    print()
    print("=" * 60)
    print("PASO: AÑADE TUS GRABACIONES REALES")
    print("=" * 60)
    print("Busco grabaciones ya subidas en la raiz de Colab...")
    
    found = False
    for fname in os.listdir("."):
        if fname.endswith(".wav") and fname != "generate_samples.py":
            import shutil
            dest = os.path.join(clips_dir, f"real_{uuid.uuid4().hex[:8]}.wav")
            shutil.copy(fname, dest)
            print(f"  Copiado: {fname} -> {dest}")
            found = True
    
    if not found:
        from google.colab import files as colab_files
        print("Selecciona tus archivos .wav (varios a la vez):")
        subidos = colab_files.upload()
        for nombre, contenido in subidos.items():
            ruta = os.path.join(clips_dir, f"real_{uuid.uuid4().hex[:8]}.wav")
            with open(ruta, "wb") as f:
                f.write(contenido)
            print(f"  Guardado: {ruta}")
            found = True
    
    if found:
        n_reales = len([f for f in os.listdir(clips_dir) if f.startswith("real_")])
        total = len([f for f in os.listdir(clips_dir) if f.endswith(".wav")])
        print(f"\nReales: {n_reales} | Total en positive_train: {total}")
    else:
        print("No se añadieron grabaciones reales, continuando solo con sinteticas.")

# ============================================================
# 7. PREPARAR CLIPS DE TEST Y NEGATIVOS (train.py necesita estos directorios)
# ============================================================
base = f"./my_custom_model/{TARGET_WORD}"
train_dir = f"{base}/positive_train"

# Copiar 50 clips a positive_test
test_dir = f"{base}/positive_test"
os.makedirs(test_dir, exist_ok=True)
if len([f for f in os.listdir(test_dir) if f.endswith(".wav")]) == 0:
    import shutil
    for f in os.listdir(train_dir)[:50]:
        shutil.copy(os.path.join(train_dir, f), os.path.join(test_dir, f))
    print(f"Copiados 50 clips a positive_test")

# Generar clips negativos (ruido) si no existen
sr = 16000
for neg_dir, n_clips in [("negative_train", 100), ("negative_test", 20)]:
    d = f"{base}/{neg_dir}"
    os.makedirs(d, exist_ok=True)
    existing = [f for f in os.listdir(d) if f.endswith(".wav")]
    if len(existing) < n_clips:
        for i in range(n_clips - len(existing)):
            ns = int(sr * random.uniform(0.5, 1.5))
            noise = np.random.randn(ns).astype(np.float32)
            noise = (noise / (np.max(np.abs(noise)) + 1e-10) * 0.3 * 32767).clip(-32768, 32767).astype(np.int16)
            scipy.io.wavfile.write(os.path.join(d, f"neg_{uuid.uuid4().hex[:8]}.wav"), sr, noise)
        print(f"Generados {n_clips} clips negativos en {neg_dir}")

# ============================================================
# 8. COMPUTAR FEATURES Y ENTRENAR (arquitectura definida inline)
# ============================================================
print("\n=== COMPUTANDO FEATURES ===")
import torch, torch.nn as nn, torch.utils.data

# Cargar modelos ONNX de openWakeWord para extraer features
import onnxruntime as ort
ort_session = ort.InferenceSession("./openwakeword/openwakeword/resources/models/melspectrogram.onnx",
                                    providers=["CPUExecutionProvider"])
ort_embed = ort.InferenceSession("./openwakeword/openwakeword/resources/models/embedding_model.onnx",
                                  providers=["CPUExecutionProvider"])

sr = 16000

def compute_embedding(audio_batch):
    """audio_batch: (N, samples) int16, returns (N, frames, 96) float32"""
    x = audio_batch.astype(np.float32)
    melspec = ort_session.run(None, {'input': x})[0]  # (N, frames, 32)
    melspec = melspec / 10 + 2
    # sliding windows of 76 frames, step 8
    windows = []
    for i in range(0, melspec.shape[1] - 75, 8):
        windows.append(melspec[:, i:i+76, :])
    if not windows:
        return np.empty((audio_batch.shape[0], 0, 96), dtype=np.float32)
    batch = np.stack(windows, axis=1).astype(np.float32)[..., None]  # (N, n_windows, 76, 32, 1)
    N, nW, H, W, C = batch.shape
    flat = batch.reshape(-1, H, W, C)
    emb = ort_embed.run(None, {'input_1': flat})[0]  # (N*nW, 96)
    return emb.reshape(N, nW, 96)

def load_and_embed_streaming(dir_path, label, max_len=16000, bs=16):
    """Load audio files in batches, embed each batch, discard audio immediately.
    Never keeps all audio in RAM."""
    files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(".wav")]
    if not files:
        return np.empty((0, 16, 96), dtype=np.float32), np.empty(0, dtype=np.float32)
    all_feats = []
    for start in range(0, len(files), bs):
        batch_files = files[start:start+bs]
        batch = np.zeros((len(batch_files), max_len), dtype=np.int16)
        for i, f in enumerate(batch_files):
            try:
                rate, data = scipy.io.wavfile.read(f)
                if rate != sr:
                    from scipy.signal import resample
                    data = resample(data, int(len(data) * sr / rate)).astype(np.int16)
                n = min(len(data), max_len)
                batch[i, :n] = data[:n]
            except Exception as e:
                print(f"    Error leyendo {f}: {e}")
        emb = compute_embedding(batch)
        all_feats.append(emb)
        del batch, emb; gc.collect()
    features = np.vstack(all_feats) if all_feats else np.empty((0, 16, 96))
    return features, np.full(features.shape[0], label, dtype=np.float32)

feature_save_dir = f"./my_custom_model/{TARGET_WORD}"

print("  positive_train (streaming)...")
X_pos_train, y_pos_train = load_and_embed_streaming(f"{base}/positive_train", 1)
print(f"    {len(X_pos_train)} clips")
gc.collect()
print("  positive_test (streaming)...")
X_pos_test, y_pos_test = load_and_embed_streaming(f"{base}/positive_test", 1)
print(f"    {len(X_pos_test)} clips")
gc.collect()
print("  negative_train (streaming)...")
X_neg_train, y_neg_train = load_and_embed_streaming(f"{base}/negative_train", 0)
print(f"    {len(X_neg_train)} clips")
gc.collect()
print("  negative_test (streaming)...")
X_neg_test, y_neg_test = load_and_embed_streaming(f"{base}/negative_test", 0)
print(f"    {len(X_neg_test)} clips")
gc.collect()

np.save(os.path.join(feature_save_dir, "positive_features_train.npy"), X_pos_train)
np.save(os.path.join(feature_save_dir, "positive_features_test.npy"), X_pos_test)
np.save(os.path.join(feature_save_dir, "negative_features_train.npy"), X_neg_train)
np.save(os.path.join(feature_save_dir, "negative_features_test.npy"), X_neg_test)
print("Features guardados")

print("  Cargando ACAV100M features (memory-mapped)...")
X_acav = np.load("openwakeword_features_ACAV100M_2000_hrs_16bit.npy", mmap_mode='r')
print(f"    Shape: {X_acav.shape}")
gc.collect()

n_pos = len(X_pos_train)
n_neg_needed = n_pos - len(X_neg_train)
print(f"  Necesitamos {n_neg_needed} negativos de ACAV100M")
X_neg_sample = X_acav[:max(0, n_neg_needed)].copy()  # solo lo que necesitamos
del X_acav; gc.collect()

X_train_neg = np.vstack([X_neg_train, X_neg_sample])
y_train = np.hstack([np.ones(n_pos), np.zeros(len(X_train_neg))])
X_train = np.vstack([X_pos_train, X_train_neg])
del X_pos_train, X_neg_train, X_neg_sample, y_pos_train, y_neg_train; gc.collect()

X_val = np.vstack([X_pos_test, X_neg_test])
y_val = np.hstack([np.ones(len(X_pos_test)), np.zeros(len(X_neg_test))])
del X_pos_test, X_neg_test; gc.collect()

print(f"\nTrain: {len(X_train)} ({int(sum(y_train))} pos, {int(len(y_train)-sum(y_train))} neg)")
print(f"Val: {len(X_val)} ({int(sum(y_val))} pos, {int(len(y_val)-sum(y_val))} neg)")

# === DEFINIR MODELO (misma arquitectura que openWakeWord) ===
class FCNBlock(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.fc = nn.Linear(d, d)
        self.r = nn.ReLU()
        self.ln = nn.LayerNorm(d)
    def forward(self, x):
        return self.r(self.ln(self.fc(x)))

class WakeWordModel(nn.Module):
    def __init__(self, input_shape, layer_dim=128, n_blocks=1):
        super().__init__()
        self.flatten = nn.Flatten()
        self.layer1 = nn.Linear(input_shape[0]*input_shape[1], layer_dim)
        self.r1 = nn.ReLU()
        self.ln1 = nn.LayerNorm(layer_dim)
        self.blocks = nn.ModuleList([FCNBlock(layer_dim) for _ in range(n_blocks)])
        self.out = nn.Linear(layer_dim, 1)
        self.sig = nn.Sigmoid()
    def forward(self, x):
        x = self.r1(self.ln1(self.layer1(self.flatten(x))))
        for b in self.blocks:
            x = b(x)
        return self.sig(self.out(x))

input_shape = X_train.shape[1:]
model = WakeWordModel(input_shape, layer_dim=128)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
opt = torch.optim.Adam(model.parameters(), lr=0.0001)
loss_fn = nn.BCELoss()

train_ds = torch.utils.data.TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
train_loader = torch.utils.data.DataLoader(train_ds, batch_size=128, shuffle=True)
val_ds = torch.utils.data.TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=len(y_val))
del X_train, y_train, X_val, y_val, train_ds; gc.collect()

n_steps = TRAIN_STEPS
val_steps = set(np.linspace(0, n_steps-1, 20, dtype=int))
best_loss = float('inf')
best_state = None
patience = 5
no_improve = 0

print(f"\n=== ENTRENANDO ({n_steps} pasos) ===")
for step, (x, y) in enumerate(train_loader):
    if step >= n_steps:
        break
    x, y = x.to(device), y.to(device)
    opt.zero_grad()
    loss = loss_fn(model(x), y[..., None])
    loss.backward()
    opt.step()
    if step % 100 == 0:
        print(f"  step {step}/{n_steps}  loss={loss.item():.4f}")
    if step in val_steps and step > 0:
        model.eval()
        vlosses = []
        with torch.no_grad():
            for vx, vy in val_loader:
                vlosses.append(loss_fn(model(vx.to(device)), vy.to(device)[..., None]).item())
        avg = np.mean(vlosses)
        print(f"  VAL step {step}: loss={avg:.4f}")
        if avg < best_loss:
            best_loss = avg
            best_state = copy.deepcopy(model.state_dict())
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  Early stopping en step {step}")
                break
    model.train()

if best_state is not None:
    model.load_state_dict(best_state)

print("\n=== EXPORTANDO A ONNX ===")
model.to("cpu")
dummy = torch.rand(1, *input_shape)
onnx_path = f"my_custom_model/{TARGET_WORD}.onnx"
torch.onnx.export(model, dummy, onnx_path, opset_version=13, output_names=[TARGET_WORD])
print(f"Modelo guardado: {onnx_path} ({os.path.getsize(onnx_path)/1024:.1f} KB)")

# ============================================================
# 9. RESULTADOS Y DESCARGA
# ============================================================
print("\n" + "=" * 40)
print("RESULTADOS:")
print("=" * 40)
sh("ls -lh my_custom_model/")

onnx_path = f"my_custom_model/{TARGET_WORD}.onnx"
if os.path.exists(onnx_path):
    size = os.path.getsize(onnx_path)
    print(f"\nModelo ONNX: {size/1024:.1f} KB")

    print("Descargando...")
    try:
        from google.colab import files
        files.download(onnx_path)
    except ImportError:
        print("No estas en Colab. Descarga manual desde el panel de archivos.")
else:
    print(f"ERROR: No se encontro {onnx_path}")
    print("El modelo no se genero correctamente.")

print(f"""
============================================================
LISTO!
============================================================
Coloca casa.onnx en:  TFG/TFG Alejandro/models/
Luego ejecuta:        python test_casa.py
============================================================
""")
