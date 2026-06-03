import requests
import json

IP_SPACELYNK = "192.168.X.X"
USUARIO = "USUARIO"
PASSWORD = "PONER_AQUI_CONTRASENA"

# Ruta de la API para comandos remotos
SPACELYNK_URL = f"http://{IP_SPACELYNK}/scada-remote"

def obtener_datos_spacelynk():
    print(f"[CARG]  Conectando a {SPACELYNK_URL} en modo LECTURA...")
    
    # 'fn': 'getall' pide la lista completa sin modificar nada
    params = {'m': 'json', 'r': 'grp', 'fn': 'getall'}
    
    try:
        # Autenticación segura con auth=(USUARIO, PASSWORD)
        r = requests.get(url=SPACELYNK_URL, params=params, auth=(USUARIO, PASSWORD), timeout=5)
        print(f"[KNX]  Código de respuesta HTTP: {r.status_code}")
        
        if r.status_code == 200:
            datos = r.json()
            print(f"[OK]  ¡Éxito! El SpaceLynk ha devuelto {len(datos)} objetos.")
            
            # Guardamos todos los datos en un archivo JSON para no saturar la consola
            nombre_archivo = "mis_dispositivos.json"
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            print(f"[DOC]  Se ha creado el archivo '{nombre_archivo}' con toda la información.")
            
            # Imprimimos solo los 5 primeros para verificar visualmente
            print("\n--- Muestra de los primeros 5 dispositivos ---")
            for obj in datos[:5]:
                nombre = obj.get('name', 'Sin nombre')
                alias = obj.get('address', 'Sin alias')
                print(f" - Nombre: {nombre} | Alias KNX: {alias}")
                
        elif r.status_code in [401, 403]:
            print("[ERR]  Error de autenticación: Verifica el usuario y contraseña.")
        else:
            print(f"[AVISO]  Respuesta inesperada del servidor.")
            
    except Exception as e:
        print(f"[ERR]  Error de red conectando al equipo: {e}")

# Llamamos a la función para que el script se ejecute
obtener_datos_spacelynk()