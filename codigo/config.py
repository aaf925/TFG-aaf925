import os

# --- SpaceLynk ---
SPACELYNK_IP = "192.168.X.X"
SPACELYNK_USER = "USUARIO"
SPACELYNK_PASS = "PONER_AQUI_CONTRASENA"
SPACELYNK_URL = f"http://{SPACELYNK_IP}/scada-remote"

# --- Ollama ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_LLM = "qwen2.5:1.5b"

# --- Whisper ---
MODELO_WHISPER = "tiny"
IDIOMA = "es"
USAR_WHISPER_FINETUNED = True
WHISPER_FINETUNED_PATH = os.path.join(os.path.dirname(__file__), "whisper_finetuned")

# --- Wake word ---
WAKE_WORD = "casa"
UMBRAL_WAKE_WORD = 0.4
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# --- Audio ---
RATE = 16000
CHUNK = 1280
UMBRAL_SILENCIO = 650
SILENCIO_MAXIMO = 1.8
DURACION_MAXIMA = 10

# --- Personalización ---
USUARIO = "Alejandro"

# --- Confianza ---
UMBRAL_AUTO = 0.7
UMBRAL_CONFIRMAR = 0.4

# --- Sonos ---
SONOS_IP = "192.168.X.X"
EDGE_TTS_VOICE = "es-ES-ElviraNeural"
PUERTO_HTTP = 8000
AUDIO_FILE = "respuesta.mp3"

# --- Servidor Flask ---
HOST = "0.0.0.0"
PORT = 5000

# --- Dispositivos KNX ---
DISPOSITIVOS = {
    # Luces individuales
    "luz aula 16": {"tipo": "luz", "addr": "1/1/1", "dpt": 1001},
    "luz aula 17": {"tipo": "luz", "addr": "1/1/3", "dpt": 1001},
    "luz aula 18": {"tipo": "luz", "addr": "1/2/26", "dim": "1/2/28", "dpt": 1001, "dim_dpt": 5001},
    "luz bano 5": {"tipo": "luz", "addr": "1/1/11", "dpt": 1001},
    "luz bano 6": {"tipo": "luz", "addr": "1/1/13", "dpt": 1001},
    "luz cocina": {"tipo": "luz", "addr": "1/1/7", "dpt": 1001},
    "luz entrada 1": {"tipo": "luz", "addr": "1/1/5", "dpt": 1001},
    "luz entrada 4": {"tipo": "luz", "addr": "1/1/9", "dpt": 1001},
    "luz salon 9": {"tipo": "luz", "addr": "1/2/11", "dim": "1/2/13", "dpt": 1001, "dim_dpt": 5001},
    "luz salon 10": {"tipo": "luz", "addr": "1/2/16", "dim": "1/2/18", "dpt": 1001, "dim_dpt": 5001},
    "luz salon 3": {"tipo": "luz", "addr": "1/2/1", "dim": "1/2/3", "dpt": 1001, "dim_dpt": 5001},
    "luz salon 7": {"tipo": "luz", "addr": "1/1/15", "dpt": 1001},
    "luz ordenador": {"tipo": "luz", "addr": "1/2/6", "dim": "1/2/8", "dpt": 1001, "dim_dpt": 5001},
    "luz salon 11": {"tipo": "luz", "addr": "1/2/21", "dim": "1/2/23", "dpt": 1001, "dim_dpt": 5001},
    "luz dormitorio 12": {"tipo": "luz", "addr": "1/1/17", "dpt": 1001},
    "luz dormitorio 13": {"tipo": "luz", "addr": "1/1/19", "dpt": 1001},
    "luz dormitorio 14": {"tipo": "luz", "addr": "1/1/21", "dpt": 1001},

    # Agrupaciones
    "luces aula": {"tipo": "luz", "addr": ["1/1/1", "1/1/3", "1/2/26"], "dpt": 1001},
    "luces bano": {"tipo": "luz", "addr": ["1/1/11", "1/1/13"], "dpt": 1001},
    "luces cocina": {"tipo": "luz", "addr": ["1/1/7"], "dpt": 1001},
    "luces entrada": {"tipo": "luz", "addr": ["1/1/5", "1/1/9"], "dpt": 1001},
    "luces salon": {"tipo": "luz", "addr": ["1/2/1", "1/1/15", "1/2/21", "1/2/11", "1/2/16"], "dpt": 1001},
    "luces dormitorio": {"tipo": "luz", "addr": ["1/1/17", "1/1/19", "1/1/21"], "dpt": 1001},
    "luces ordenador": {"tipo": "luz", "addr": ["1/2/6"], "dpt": 1001},
    "todas las luces de la casa": {"tipo": "luz", "addr": [
        "1/2/1", "1/1/15", "1/2/6", "1/2/21", "1/2/11", "1/2/16",
        "1/1/11", "1/1/13",
        "1/1/7",
        "1/1/5", "1/1/9",
        "1/2/26", "1/1/1", "1/1/3",
        "1/1/17", "1/1/19", "1/1/21"
    ], "dpt": 1001},

    # Persianas y clima
    "persiana cocina": {"tipo": "persiana", "mov": "2/1/1", "altura": "2/1/4", "mov_dpt": 1008, "alt_dpt": 5001},
    "persiana bano": {"tipo": "persiana", "mov": "2/1/5", "altura": "2/1/8", "mov_dpt": 1008, "alt_dpt": 5001},
    "persiana dormitorio": {"tipo": "persiana", "mov": "2/1/9", "altura": "2/1/12", "mov_dpt": 1008, "alt_dpt": 5001},
    "estor salon": {"tipo": "persiana", "mov": "2/3/1", "altura": "2/3/4", "mov_dpt": 1008, "alt_dpt": 5001},
    "estor dormitorio": {"tipo": "persiana", "mov": "2/3/5", "altura": "2/3/8", "mov_dpt": 1008, "alt_dpt": 5001},
    "estor aula": {"tipo": "persiana", "mov": "2/3/9", "altura": "2/3/12", "mov_dpt": 1008, "alt_dpt": 5001},
    "todas las persianas": {"tipo": "persiana", "mov": ["2/1/1", "2/1/5", "2/1/9", "2/3/1", "2/3/5", "2/3/9"], "altura": ["2/1/4", "2/1/8", "2/1/12", "2/3/4", "2/3/8", "2/3/12"], "mov_dpt": 1008, "alt_dpt": 5001},
    "temperatura actual salon": {"tipo": "clima", "read": "3/1/1"},
    "temperatura exterior": {"tipo": "clima", "read": "3/2/5"},
}
