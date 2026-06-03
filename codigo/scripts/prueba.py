import requests

IP_SPACELYNK = "192.168.X.X"
USUARIO = "USUARIO"
PASSWORD = "PONER_AQUI_CONTRASENA"
SPACELYNK_URL = f"http://{IP_SPACELYNK}/scada-remote"

def diagnostico_spacelynk():
    print(f"[CARG]  Conectando a {SPACELYNK_URL}...")
    
    # Usamos el comando 'find' sobre un alias que sabemos que existe en tus capturas
    params = {'m': 'json', 'r': 'grp', 'fn': 'find', 'alias': '1/1/15'}
    
    try:
        r = requests.get(url=SPACELYNK_URL, params=params, auth=(USUARIO, PASSWORD), timeout=5)
        print(f"[KNX]  Código de respuesta HTTP: {r.status_code}")
        
        # Vamos a imprimir el texto en bruto primero, pase lo que pase
        print(f"[ARCH]  Texto bruto devuelto por el servidor:\n{r.text}")
        
        # Ahora intentamos pasarlo a JSON
        if r.text.strip():
            datos = r.json()
            print(f"[OK]  JSON decodificado con éxito: {datos}")
        else:
            print("[AVISO]  El servidor devolvió una respuesta completamente vacía.")
            
    except Exception as e:
        print(f"[ERR]  Error en la prueba: {e}")

diagnostico_spacelynk()