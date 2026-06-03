import requests
import json
import time

IP_SPACELYNK = "192.168.X.X"
USUARIO = "USUARIO"
PASSWORD = "PONER_AQUI_CONTRASENA"
SPACELYNK_URL = f"http://{IP_SPACELYNK}/scada-remote"

def escanear_red_knx():
    print("[BUSCAR]  Iniciando escáner de barrido en la red KNX...")
    print("[ESP]  Esto puede tardar un par de minutos. Paciencia...\n")
    
    dispositivos_encontrados = []
    
    # Rango de escaneo: 
    # Principales del 1 al 4 (Suelen ser Luces, Persianas, Clima)
    # Medios del 1 al 4
    # Subgrupos del 1 al 50 (Para abarcar los 141 objetos que vimos)
    for principal in range(1, 5):
        for medio in range(1, 5):
            for sub in range(1, 51):
                alias = f"{principal}/{medio}/{sub}"
                # Usamos la función 'find' que ya confirmamos que funciona
                params = {'m': 'json', 'r': 'grp', 'fn': 'find', 'alias': alias}
                
                try:
                    r = requests.get(url=SPACELYNK_URL, params=params, auth=(USUARIO, PASSWORD), timeout=2)
                    
                    # Si responde con 200 y el texto no está vacío
                    if r.status_code == 200 and r.text.strip():
                        datos = r.json()
                        
                        # Verificamos si es un objeto válido comprobando si tiene 'name'
                        if isinstance(datos, dict) and 'name' in datos:
                            nombre = datos['name']
                            print(f"[OK]  ¡Encontrado! Alias: {alias.ljust(8)} | Nombre: {nombre}")
                            
                            dispositivos_encontrados.append({
                                "alias": alias,
                                "nombre": nombre,
                                "tipo_dato": datos.get('datatype', 'Desconocido')
                            })
                except Exception:
                    pass # Si hay timeout, simplemente saltamos al siguiente
                
                # Pausa minúscula de 50ms para no saturar/bloquear el SpaceLynk
                time.sleep(0.05)
                
    print(f"\n[BIEN]  Escaneo completado. Se han encontrado {len(dispositivos_encontrados)} objetos válidos.")
    
    # Lo guardamos todo en un archivo JSON bonito y ordenado
    nombre_archivo = "inventario_completo_knx.json"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(dispositivos_encontrados, f, indent=4, ensure_ascii=False)
        
    print(f"[DOC]  Tienes la lista completa en el archivo: '{nombre_archivo}'")

escanear_red_knx()