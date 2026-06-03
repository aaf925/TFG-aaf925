import requests, json, time, os, unicodedata, re, difflib, socket, threading, sys, random
from threading import Thread
from datetime import datetime
import numpy as np
import scipy.io.wavfile as wav
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from config import *
from confianza_sistema import evaluar_confianza, clasificar_confianza
from contexto import ContextoConversacional
from tts import TTSManager

# --- Contexto global ---
ctx = ContextoConversacional()
tts = TTSManager()
SONOS_DEVICE = None
MODO_ACTUAL = "T"
WHISPER_MODEL = None

# --- Personalización ---
def saludo_hora():
    h = datetime.now().hour
    if h < 12: return "Buenos dias"
    if h < 18: return "Buenas tardes"
    return "Buenas noches"

def genero_numero(nombres):
    plural = len(nombres) > 1
    fem = False
    fem_palabras = ["luz", "luces", "cocina", "entrada", "persiana", "persianas", "aula"]
    plural_palabras = ["luces", "persianas", "estores", "todas", "todos"]
    for n in nombres:
        for p in fem_palabras:
            if p in n:
                fem = True
        for p in plural_palabras:
            if p in n:
                plural = True
    return plural, fem

def conjugar(adj, plural, fem):
    if fem:
        return adj + "a" if not plural else adj + "as"
    return adj + "o" if not plural else adj + "os"

def generar_respuesta(accion, nombres, valor=None, contexto=""):
    hora = datetime.now().hour
    es_noche = hora < 7 or hora > 22
    plural, fem = genero_numero(nombres)
    participio = {
        "encender": "encendid",
        "apagar": "apagad",
        "subir": "subid",
        "bajar": "bajad",
        "regular": "regulad",
    }

    if accion == "salir_voz":
        return random.choice([
            f"De nada, {USUARIO}. Hasta luego.",
            f"Un placer, {USUARIO}. Cuando quieras.",
            f"Hasta pronto, {USUARIO}.",
        ])

    if accion == "consultar":
        return None

    if accion in participio:
        p = conjugar(participio[accion], plural, fem)
        frases = []
        if accion in ("encender", "apagar"):
            queda = "quedan" if plural else "queda"
            frases = [
                f"{p.capitalize()}, {USUARIO}.",
                f"Listo, {USUARIO}. {p}.",
                f"Hecho. {queda} {p}.",
            ]
            if es_noche and accion == "apagar":
                frases.append(f"{p.capitalize()}, que descanses.")
        elif accion in ("subir", "bajar"):
            frases = [
                f"{p.capitalize()}, {USUARIO}.",
                f"Listo, {p}.",
            ]
            adverbio = "arriba" if accion == "subir" else "abajo"
            frases.append(f"{adverbio.capitalize()}.")
        elif accion == "regular":
            ajs = conjugar("ajustad", plural, fem)
            frases = [
                f"{p.capitalize()} a {valor}, {USUARIO}." if valor else f"{p.capitalize()}, {USUARIO}.",
                f"{ajs.capitalize()}. Valor {valor}." if valor else f"{ajs.capitalize()}, {USUARIO}.",
            ]
        return random.choice(frases)

    return f"Hecho, {USUARIO}."

# --- Servidor HTTP (Sonos) ---
def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def iniciar_servidor_http():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args): return
    with TCPServer(("", PUERTO_HTTP), QuietHandler) as httpd:
        httpd.serve_forever()

IP_LOCAL = obtener_ip_local()
threading.Thread(target=iniciar_servidor_http, daemon=True).start()

# --- KNX ---
def api_call(params):
    try:
        r = requests.get(url=SPACELYNK_URL, params=params, auth=(SPACELYNK_USER, SPACELYNK_PASS), timeout=5)
        if r.status_code == 200: return r.json()
    except: return None

def enviar_comando_knx(alias, valor, dpt=None):
    if isinstance(alias, list):
        for a in alias: enviar_comando_knx(a, valor, dpt)
        return True
    params = {'m': 'json', 'r': 'grp', 'fn': 'write', 'alias': alias, 'value': valor}
    if dpt: params['datatype'] = dpt
    res = api_call(params)
    if res: print(f"  KNX {alias} -> {valor} OK")
    return res is not None

def leer_valor_knx(alias):
    params = {'m': 'json', 'r': 'grp', 'fn': 'find', 'alias': alias}
    res = api_call(params)
    return res.get('value') if res else None

# --- Fallback parser ---
def quitar_tildes(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().replace('ñ', 'n')
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def fallback_parser(orden):
    orden_limpia = quitar_tildes(orden)
    reemplazos = [
        ("aseo", "bano"), ("termperatura", "temperatura"), ("perciana", "persiana"),
        ("luzes", "luces"), ("historias", "estores"), ("deluses", "luces"),
        ("pepsianas", "persiana"), ("tantas", "levanta"), ("quanta", "levanta"),
        ("pantalas", "levanta"), ("pantala", "levanta"), ("personas", "persianas"),
        ("cuarto", "dormitorio"),
    ]
    for a, b in reemplazos:
        orden_limpia = orden_limpia.replace(a, b)

    palabras_orden = set(orden_limpia.split())
    res = {}

    # 1. Determinar acción basándonos en palabras clave primero
    if any(w in orden_limpia for w in ["apagar", "apaga", "quita", "desactivar", "desconecta"]):
        res["accion"] = "apagar"
    elif any(w in orden_limpia for w in ["encender", "prender", "enciende", "pon", "activar", "conecta"]):
        res["accion"] = "encender"
    elif any(w in orden_limpia for w in ["sube", "subir", "abre", "abrir", "levanta", "recoge"]):
        res["accion"] = "subir"
    elif any(w in orden_limpia for w in ["baja", "bajar", "cierra", "cerrar", "extiende"]):
        res["accion"] = "bajar"
    elif any(w in orden_limpia for w in ["dime", "consulta", "cual es", "estado", "temperatura", "cuanto"]):
        res["accion"] = "consultar"
    elif any(w in orden_limpia for w in ["regula", "ajusta", "poner", "coloca", "ponlo", "situa"]):
        res["accion"] = "regular"
    elif any(w in orden_limpia for w in ["adios", "gracias", "luego"]):
        res["accion"] = "salir_voz"

    # 2. Buscar coincidencias de dispositivos
    encontrados = []
    pesos = {
        "luz": 10, "luces": 15, 
        "estor": 15, "estores": 15, 
        "persiana": 15, "persianas": 15, 
        "todas": 30, "todos": 30
    }
    pesos_loc = {"salon": 20, "bano": 20, "cocina": 20, "dormitorio": 20, "cuarto": 20, "exterior": 20, "aula": 20, "casa": 20, "entrada": 20, "ordenador": 20}
    locs_en_orden = [l for l in pesos_loc.keys() if l in palabras_orden]

    for nombre in DISPOSITIVOS.keys():
        score = 0
        nombre_limpio = quitar_tildes(nombre)
        pal_disp = set(nombre_limpio.split())
        for p in pal_disp:
            if p in palabras_orden: score += pesos.get(p, pesos_loc.get(p, 5))
            else:
                matches = difflib.get_close_matches(p, palabras_orden, n=1, cutoff=0.7)
                if matches: score += pesos.get(p, pesos_loc.get(p, 5)) * 0.7
        # PENALIZACIÓN 1: Ubicación incorrecta
        for l in locs_en_orden:
            if l not in pal_disp:
                score -= 40 
        
        # PENALIZACIÓN 1b: Ubicación no solicitada
        if locs_en_orden:
            for l in pesos_loc.keys():
                if l in pal_disp and l not in locs_en_orden:
                    score -= 20

        # PENALIZACIÓN 1c: Tipo incorrecto
        es_pedido_luz = any(w in palabras_orden for w in ["luz", "luces", "iluminacion", "lampara"])
        es_pedido_persiana = any(w in palabras_orden for w in ["persiana", "persianas", "estor", "estores", "ventana"])
        
        tipo_disp = DISPOSITIVOS[nombre]["tipo"]
        if es_pedido_luz and tipo_disp != "luz": score -= 30
        if es_pedido_persiana and tipo_disp != "persiana": score -= 30
        num_disp, num_user = re.findall(r'\d+', nombre), re.findall(r'\d+', orden_limpia)
        if num_user and num_disp and not any(n in num_user for n in num_disp): score -= 60 
        if score >= 10: encontrados.append((nombre, score))
        
    if not encontrados: return None
    encontrados.sort(key=lambda x: x[1], reverse=True)
    max_s = encontrados[0][1]
    final_disps = [d for d, s in encontrados if s >= max_s * 0.9]

    # Si dice "luces"/"luz" sin ubicación ni número de dispositivo, agrupar en "todas las luces"
    if ({"luz", "luces", "iluminacion", "lampara"} & palabras_orden
            and not (set(pesos_loc.keys()) & palabras_orden)):
        nums_orden = re.findall(r'\d+', orden_limpia)
        nums_en_dispositivos = [n for d in DISPOSITIVOS for n in re.findall(r'\d+', d)]
        if not nums_orden or not any(n in nums_orden for n in nums_en_dispositivos):
            if "todas las luces de la casa" in DISPOSITIVOS:
                final_disps = ["todas las luces de la casa"]

    # Si dice "persianas"/"estores" sin ubicación, agrupar en "todas las persianas"
    if ({"persiana", "persianas", "estor", "estores", "ventana"} & palabras_orden
            and not (set(pesos_loc.keys()) & palabras_orden)):
        nums_orden = re.findall(r'\d+', orden_limpia)
        nums_en_dispositivos = [n for d in DISPOSITIVOS for n in re.findall(r'\d+', d)]
        if not nums_orden or not any(n in nums_orden for n in nums_en_dispositivos):
            if "todas las persianas" in DISPOSITIVOS:
                final_disps = ["todas las persianas"]

    # 3. Determinar el valor de regulación si aplica
    todos_numeros = [int(n) for n in re.findall(r'\d+', orden_limpia)]
    if todos_numeros:
        # Identificar qué números pertenecen a los nombres de los dispositivos seleccionados
        numeros_dispositivos = set()
        for d in final_disps:
            for n in re.findall(r'\d+', d):
                numeros_dispositivos.add(int(n))
        # Los números restantes son candidatos a regulación
        numeros_regulacion = [n for n in todos_numeros if n not in numeros_dispositivos]
        if numeros_regulacion:
            res["valor"] = numeros_regulacion[0]
            if res.get("accion") in [None, "encender", "subir", "bajar"]:
                res["accion"] = "regular"

    # Si no hay acción pero hay dispositivos claros, inferir por defecto
    if "accion" not in res:
        if any("persiana" in d or "estor" in d for d in final_disps): res["accion"] = "subir"
        else: res["accion"] = "encender"

    if final_disps and "accion" in res:
        res["dispositivos"] = final_disps
        print(f"[Buscador] Entendido: {res['accion']} en {', '.join(final_disps)}")
        return res
    return None

# --- LLM (Ollama) ---
def consultar_llm(orden, prompt_ctx=""):
    prompt = f"""Eres un experto en domotica. Convierte la orden del usuario en un objeto JSON.
DISPOSITIVOS DISPONIBLES: [{', '.join(DISPOSITIVOS.keys())}]

REGLAS:
- Responde EXCLUSIVAMENTE con el objeto JSON.
- 'accion': [encender, apagar, subir, bajar, regular, consultar]
- 'dispositivos': Lista de nombres exactos de la lista anterior.
- 'valor': Si mencionan un numero o porcentaje.{prompt_ctx}

ORDEN: "{orden}"
JSON:"""
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODELO_LLM,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0}
        }, timeout=7)
        return json.loads(r.json()['response'])
    except:
        return None

# --- Procesamiento de comandos ---
def procesar(res, orden_orig, pedir_confirmacion=False):
    if not res:
        res = fallback_parser(orden_orig)
    if not res:
        decir(random.choice([
            f"No te he entendido, {USUARIO}.",
            f"¿Puedes repetirlo, {USUARIO}?",
            f"No he captado eso, {USUARIO}. Dímelo otra vez.",
        ]))
        return

    accion = res.get("accion")
    nombres = res.get("dispositivos") or [res.get("dispositivo")]
    valor = res.get("valor")

    if pedir_confirmacion:
        disp_str = ", ".join(nombres[:3])
        if MODO_ACTUAL == "V":
            respuesta = confirmar_voz(accion, nombres)
            es_no = any(w in respuesta for w in ["no", "nada", "cancelar", "quit", "cancel"])
        else:
            confirmar = input(f"  Confirmar: {accion} en {disp_str}? [S/n]: ").strip().lower()
            es_no = confirmar == "n"
        if es_no:
            decir(random.choice([
                f"Cancelado, {USUARIO}.",
                f"Vale, lo dejo, {USUARIO}.",
                f"Como quieras, {USUARIO}.",
            ]))
            return

    for nombre in [n for n in nombres if n]:
        info = DISPOSITIVOS.get(nombre)
        if not info: continue

        if accion == "consultar":
            val = leer_valor_knx(info.get("read") or info.get("addr"))
            if val is not None:
                decir(f"{nombre} tiene un valor de {val}, {USUARIO}.")
            else:
                decir(f"No pude leer {nombre}, lo siento {USUARIO}.")
        elif info["tipo"] == "luz":
            if accion == "encender":
                enviar_comando_knx(info["addr"], 1, info.get("dpt"))
            elif accion == "apagar":
                enviar_comando_knx(info["addr"], 0, info.get("dpt"))
            elif accion == "regular" and valor is not None:
                if "dim" in info:
                    enviar_comando_knx(info["dim"], valor, info.get("dim_dpt"))
                else:
                    decir(random.choice([
                        f"Esta luz no es regulable, {USUARIO}.",
                        f"No puedo regular esa luz, {USUARIO}.",
                        f"Lo siento, {USUARIO}, esa luz no admite regulación.",
                    ]))
        elif info["tipo"] == "persiana":
            if accion == "subir":
                enviar_comando_knx(info["mov"], 0, info.get("mov_dpt"))
            elif accion == "bajar":
                enviar_comando_knx(info["mov"], 1, info.get("mov_dpt"))
            elif accion == "regular" and valor is not None:
                enviar_comando_knx(info["altura"], valor, info.get("alt_dpt"))

    frase = generar_respuesta(accion, nombres, valor)
    if frase:
        decir(frase)

def decir(texto):
    global SONOS_DEVICE

    if SONOS_DEVICE:
        try:
            import edge_tts
            import asyncio
            asyncio.run(edge_tts.Communicate(texto, EDGE_TTS_VOICE).save(AUDIO_FILE))
            url = f"http://{IP_LOCAL}:{PUERTO_HTTP}/{AUDIO_FILE}"
            SONOS_DEVICE.play_uri(url)
            return
        except:
            pass

        try:
            from gtts import gTTS
            tts_g = gTTS(text=texto, lang='es')
            tts_g.save(AUDIO_FILE)
            url = f"http://{IP_LOCAL}:{PUERTO_HTTP}/{AUDIO_FILE}"
            SONOS_DEVICE.play_uri(url)
            return
        except:
            pass

    tts.decir(texto)

# --- Confirmación por voz ---
def confirmar_voz(accion, nombres):
    import sounddevice as sd
    import scipy.io.wavfile as wav

    nombres_limpios = []
    for n in nombres:
        if "todas las luces de la casa" in n:
            nombres_limpios.append("todas las luces")
        elif "todas las persianas" in n:
            nombres_limpios.append("todas las persianas")
        else:
            nombres_limpios.append(n)
    unicos = []
    for n in nombres_limpios:
        if n not in unicos:
            unicos.append(n)

    disp_str = ", ".join(unicos[:3])
    pregunta = f"¿{accion} en {disp_str}? Di sí o no."
    decir(pregunta)
    time.sleep(5)

    RATE, CHUNK, UMBRAL = 16000, 1024, 650
    audio_data, silencio_inicio = [], None
    with sd.InputStream(samplerate=RATE, channels=1, dtype='int16') as stream:
        t_start = time.time()
        while True:
            data, _ = stream.read(CHUNK)
            audio_data.append(data)
            volumen = np.sqrt(np.mean(data.astype(np.float64)**2))
            if volumen < UMBRAL:
                if silencio_inicio is None:
                    silencio_inicio = time.time()
                elif time.time() - silencio_inicio > 1.8:
                    break
            else:
                silencio_inicio = None
            if time.time() - t_start > 10:
                break

    audio_final = np.concatenate(audio_data)
    wav.write("temp_confirm.wav", RATE, audio_final)

    if WHISPER_MODEL:
        segments, _ = WHISPER_MODEL.transcribe("temp_confirm.wav", language="es")
        respuesta = " ".join([s.text for s in segments]).strip().lower()
    else:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile("temp_confirm.wav") as source:
                audio = recognizer.record(source)
            respuesta = recognizer.recognize_google(audio, language="es-ES").lower()
        except:
            respuesta = ""

    if os.path.exists("temp_confirm.wav"):
        os.remove("temp_confirm.wav")

    return respuesta

# --- Pipeline principal ---
def procesar_orden(orden, usar_llm=True):
    orden_enriquecida, modificada = ctx.enriquecer_orden(orden)
    prompt_ctx = ctx.prompt_contexto()

    resp = None
    fuente = "fallback"

    if usar_llm:
        resp = consultar_llm(orden_enriquecida, prompt_ctx)
        if resp:
            fuente = "llm"

    if not resp:
        resp = fallback_parser(orden_enriquecida)
        fuente = "fallback"

    if resp:
        score, motivo = evaluar_confianza(resp, orden_enriquecida, fuente)
        nivel = clasificar_confianza(score)
        print(f"  Confianza: {score} ({nivel}) - {motivo}")

        ctx.actualizar(orden_enriquecida if modificada else orden, resp)

        if nivel == "rechazar":
            decir(random.choice([
                f"No te he entendido, {USUARIO}.",
                f"¿Puedes repetirlo, {USUARIO}?",
                f"No he captado eso, {USUARIO}.",
            ]))
            return
        if nivel == "confirmar":
            procesar(resp, orden_enriquecida, pedir_confirmacion=True)
            return

    procesar(resp, orden_enriquecida)
    return resp

# --- Modo voz ---
def escuchar_activacion(oww_model, sd_lib):
    CHUNK = 1280
    with sd_lib.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
        while True:
            audio_chunk, _ = stream.read(CHUNK)
            oww_model.predict(audio_chunk.flatten())
            if oww_model.prediction_buffer.get(WAKE_WORD, [0])[-1] > UMBRAL_WAKE_WORD:
                return True

def cargar_whisper():
    try:
        from faster_whisper import WhisperModel
        if USAR_WHISPER_FINETUNED and os.path.exists(WHISPER_FINETUNED_PATH):
            try:
                print(f"  Cargando Whisper finetuned desde {WHISPER_FINETUNED_PATH}...")
                return WhisperModel(WHISPER_FINETUNED_PATH, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"  Error cargando Whisper finetuned: {e}")
        print(f"  Cargando Whisper {MODELO_WHISPER}...")
        return WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")
    except ImportError:
        print("  faster-whisper no instalado")
        return None

def principal_voz(whisper_model, sd_lib, oww_model):
    while True:
        try:
            print(f"\n Di '{WAKE_WORD.replace('_v0.1', '').replace('_', ' ').upper()}' PARA EMPEZAR...")
            if escuchar_activacion(oww_model, sd_lib):
                oww_model.reset()
                print(" ACTIVADO")
                decir(f"{saludo_hora()}, {USUARIO}. ¿En qué puedo ayudarte?")
                time.sleep(5)

                RATE, CHUNK, UMBRAL = 16000, 1024, 650
                audio_data, silencio_inicio = [], None
                with sd_lib.InputStream(samplerate=RATE, channels=1, dtype='int16') as stream:
                    t_start = time.time()
                    while True:
                        data, _ = stream.read(CHUNK)
                        audio_data.append(data)
                        volumen = np.sqrt(np.mean(data.astype(np.float64)**2))
                        if volumen < UMBRAL:
                            if silencio_inicio is None:
                                silencio_inicio = time.time()
                            elif time.time() - silencio_inicio > 1.8:
                                break
                        else:
                            silencio_inicio = None
                        if time.time() - t_start > 10:
                            break

                audio_final = np.concatenate(audio_data)
                wav.write("temp_voz.wav", RATE, audio_final)

                if whisper_model:
                    segments, _ = whisper_model.transcribe("temp_voz.wav", language="es")
                    orden = " ".join([s.text for s in segments]).strip().lower()
                else:
                    try:
                        import speech_recognition as sr
                        recognizer = sr.Recognizer()
                        with sr.AudioFile("temp_voz.wav") as source:
                            audio = recognizer.record(source)
                        orden = recognizer.recognize_google(audio, language="es-ES").lower()
                    except:
                        orden = ""

                if os.path.exists("temp_voz.wav"):
                    os.remove("temp_voz.wav")

                if orden:
                    print(f" Has dicho: {orden}")
                    for sub in [s.strip() for s in orden.split(" y ")]:
                        if len(sub) < 3: continue
                        procesar_orden(sub, usar_llm=True)
        except KeyboardInterrupt:
            break

# --- Main ---
def main():
    global SONOS_DEVICE
    print(" ASISTENTE SMARTHOME v2 (CON MEJORAS INTEGRADAS) ")
    print(f"   LLM: {MODELO_LLM}  |  Wake word: {WAKE_WORD}  |  Piper TTS: {tts.piper.disponible}")

    try:
        import soco
        if SONOS_IP:
            print(f" Conectando a Sonos en {SONOS_IP}...")
            SONOS_DEVICE = soco.SoCo(SONOS_IP)
            if SONOS_DEVICE.player_name:
                print(f"  Sonos: {SONOS_DEVICE.player_name}")
        else:
            print(" Buscando Sonos por descubrimiento...")
            dispositivos_sonos = soco.discover()
            if dispositivos_sonos:
                SONOS_DEVICE = list(dispositivos_sonos)[0]
                print(f"  Sonos: {SONOS_DEVICE.player_name}")
    except Exception as e:
        print(f"  No se pudo conectar al Sonos: {e}")

    modo = input("Modo: [T]exto, [V]oz o [A]PI? ").strip().upper()

    if modo == 'V':
        global MODO_ACTUAL, WHISPER_MODEL
        MODO_ACTUAL = "V"
        try:
            import openwakeword
            import sounddevice as sd

            oww_model = openwakeword.Model(
                wakeword_models=[os.path.join(MODELS_DIR, f"{WAKE_WORD}.onnx")],
                inference_framework="onnx",
                melspec_model_path=os.path.join(MODELS_DIR, "melspectrogram.onnx"),
                embedding_model_path=os.path.join(MODELS_DIR, "embedding_model.onnx")
            )
            whisper_model = cargar_whisper()
            WHISPER_MODEL = whisper_model
            if not whisper_model:
                print(" Whisper no disponible, modo voz usara Google STT como fallback")

            # Iniciar API en segundo plano para la app móvil
            try:
                backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "CTFG", "ctfg_app", "backend"  # Ajustar ruta si es necesario)
                if 'config' in sys.modules:
                    del sys.modules['config']
                sys.path.insert(0, backend_path)
                import importlib
                import app as backend_mod
                importlib.reload(backend_mod)
                t = Thread(target=lambda: backend_mod.app.run(host=HOST, port=PORT, debug=False, use_reloader=False), daemon=True)
                t.start()
                print(f"  API activa en http://{IP_LOCAL}:{PORT}")
            except Exception as e:
                print(f"  No se pudo iniciar API: {e}")

            principal_voz(whisper_model, sd, oww_model)
        except Exception as e:
            print(f" Error modo voz: {e}. Pasando a texto.")
            modo = 'T'

    if modo == 'A':
        print(f"Iniciando servidor API REST en http://{IP_LOCAL}:{PORT}")
        print(f"  Configura la app con: http://{IP_LOCAL}:{PORT}")
        backend_path = os.path.join(os.path.dirname(__file__), "..", "..", "CTFG", "ctfg_app", "backend"  # Ajustar ruta si es necesario)
        if 'config' in sys.modules:
            del sys.modules['config']
        sys.path.insert(0, backend_path)
        import importlib
        import app as backend_mod
        importlib.reload(backend_mod)
        backend_mod.app.run(host=HOST, port=PORT, debug=False)

    print(f"{saludo_hora()}, {USUARIO}. Estoy lista.")

    if modo == 'T' or modo not in ('V', 'A'):
        while True:
            try:
                orden = input("\n Orden (o 'salir'): ").strip().lower()
                if orden in ["salir", "exit"]:
                    break
                if not orden:
                    continue

                sub_ordenes = [s.strip() for s in orden.split(" y ")]
                for sub in sub_ordenes:
                    if len(sub) < 3: continue
                    resp = procesar_orden(sub, usar_llm=True)
                    if resp:
                        print(f"  Accion: {resp.get('accion')} | Dispositivos: {resp.get('dispositivos')}")
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
