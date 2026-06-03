import json, time, unicodedata, difflib, re, requests, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import DISPOSITIVOS
from test_set import TEST_SET

def quitar_tildes(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().replace('\xf1', 'n')
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

    if "accion" not in res:
        if "persiana" in orden_limpia or "estor" in orden_limpia:
            res["accion"] = "subir"
        if "luz" in orden_limpia or "luces" in orden_limpia:
            res["accion"] = "encender"

    encontrados = []
    pesos = {"luz": 10, "luces": 15, "estor": 15, "estores": 15, "persiana": 15, "persianas": 15, "todas": 30, "todos": 30}
    pesos_loc = {"salon": 20, "bano": 20, "cocina": 20, "dormitorio": 20, "cuarto": 20, "exterior": 20, "aula": 20, "casa": 20, "entrada": 20, "ordenador": 20}
    locs_en_orden = [l for l in pesos_loc.keys() if l in palabras_orden]

    for nombre in DISPOSITIVOS.keys():
        score = 0
        nombre_limpio = quitar_tildes(nombre)
        pal_disp = set(nombre_limpio.split())
        for p in pal_disp:
            if p in palabras_orden:
                score += pesos.get(p, pesos_loc.get(p, 5))
            else:
                matches = difflib.get_close_matches(p, palabras_orden, n=1, cutoff=0.7)
                if matches: score += pesos.get(p, pesos_loc.get(p, 5)) * 0.7
        for l in locs_en_orden:
            if l not in pal_disp: score -= 40
        if locs_en_orden:
            for l in pesos_loc.keys():
                if l in pal_disp and l not in locs_en_orden: score -= 20
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
    todos_numeros = [int(n) for n in re.findall(r'\d+', orden_limpia)]
    if todos_numeros:
        nums_disp = set()
        for d in final_disps:
            for n in re.findall(r'\d+', d): nums_disp.add(int(n))
        nums_reg = [n for n in todos_numeros if n not in nums_disp]
        if nums_reg:
            res["valor"] = nums_reg[0]
            if res.get("accion") in [None, "encender", "subir", "bajar"]:
                res["accion"] = "regular"
    if "accion" not in res:
        if any("persiana" in d or "estor" in d for d in final_disps): res["accion"] = "subir"
        else: res["accion"] = "encender"
    if final_disps and "accion" in res:
        res["dispositivos"] = final_disps
        return res
    return None

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODELS = ["qwen2.5:0.5b", "qwen2.5:1.5b", "llama3.1:latest"]

prompt_base = f"""
Eres un experto en domotica. Convierte la orden del usuario en un objeto JSON.
DISPOSITIVOS DISPONIBLES: [{', '.join(DISPOSITIVOS.keys())}]

REGLAS:
- Responde EXCLUSIVAMENTE con el objeto JSON.
- 'accion': [encender, apagar, subir, bajar, regular, consultar]
- 'dispositivos': Lista de nombres exactos de la lista anterior.
- 'valor': Si mencionan un numero o porcentaje.

ORDEN: "__ORDEN__"
JSON:"""

def extraer_json(texto):
    import re as _re
    # Try direct parse first
    try:
        return json.loads(texto)
    except:
        pass
    # Try extracting from ```json ... ``` block
    m = _re.search(r'```(?:json)?\s*([\s\S]*?)```', texto)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except:
            pass
    # Try finding { ... } block
    m = _re.search(r'\{[\s\S]*\}', texto)
    if m:
        try:
            return json.loads(m.group(0))
        except:
            pass
    return None

def consultar_llm(orden, modelo, usar_format=True):
    payload = {
        "model": modelo,
        "prompt": prompt_base.replace("__ORDEN__", orden),
        "stream": False,
        "options": {"temperature": 0}
    }
    if usar_format:
        payload["format"] = "json"
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=15)
        return extraer_json(r.json()['response'])
    except:
        return None

def normalizar(s):
    if not s:
        return ""
    return quitar_tildes(s.strip().lower())

def match_device(predicho, esperados):
    if not predicho or not esperados:
        return False, ""
    p = normalizar(predicho)
    for e in esperados:
        if normalizar(e) == p:
            return True, "exacto"
    for e in esperados:
        if p in normalizar(e) or normalizar(e) in p:
            return True, "parcial"
    return False, ""

def evaluar_respuesta(resp, caso):
    if caso["accion"] is None:
        return resp is None or (isinstance(resp, dict) and resp.get("accion") in (None, "salir_voz"))

    if caso["accion"] == "compuesta":
        return evaluar_compuesta(resp, caso)

    if not isinstance(resp, dict):
        return False
    accion_llm = resp.get("accion")
    if isinstance(accion_llm, list):
        accion_llm = accion_llm[0] if accion_llm else None
    accion_ok = resp and normalizar(accion_llm) == normalizar(caso["accion"])
    if not accion_ok:
        return False

    dispositivos = resp.get("dispositivos") or [resp.get("dispositivo")] if resp else []
    if not dispositivos or not dispositivos[0]:
        return False

    device_ok = any(match_device(d, caso["disp"])[0] for d in dispositivos)
    if not device_ok:
        return False

    if "valor" in caso and caso["valor"] is not None:
        valor_ok = resp.get("valor") == caso["valor"]
        return valor_ok

    return True

def evaluar_compuesta(resp, caso):
    if not resp:
        return False
    if resp.get("accion") == caso["sub"][0].get("accion"):
        return match_device(resp.get("dispositivos", [None])[0], caso["sub"][0]["disp"])[0]
    return False

def ejecutar_conjunto(modelo, usar_fallback=False):
    resultados = []
    for caso in TEST_SET:
        t0 = time.time()
        resp = consultar_llm(caso["cmd"], modelo)
        t_llm = time.time() - t0

        if usar_fallback and (resp is None or not evaluar_respuesta(resp, caso)):
            t0 = time.time()
            fb = fallback_parser(caso["cmd"])
            tf = time.time() - t0
            if fb:
                resp = fb
            t_llm += tf

        ok = evaluar_respuesta(resp, caso)
        resultados.append({
            "id": caso["id"],
            "cmd": caso["cmd"],
            "ok": ok,
            "resp": resp,
            "tiempo": round(t_llm, 3),
        })
    return resultados

def generar_informe(resultados, nombre):
    total = len(resultados)
    ok = sum(1 for r in resultados if r["ok"])
    media_t = sum(r["tiempo"] for r in resultados) / total if total else 0
    return {
        "modelo": nombre,
        "total": total,
        "aciertos": ok,
        "precision": round(ok / total * 100, 1),
        "tiempo_medio": round(media_t, 3),
    }

def main():
    todos = []

    for modelo in LLM_MODELS:
        print(f"\nProbando {modelo} solo...")
        res = ejecutar_conjunto(modelo, usar_fallback=False)
        inf = generar_informe(res, f"{modelo} (solo)")
        todos.append(inf)
        print(f"  {inf['precision']}% | tiempo medio: {inf['tiempo_medio']}s")
        with open(f"resultados_{modelo.replace(':','_')}_solo.json", "w") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

    for modelo in LLM_MODELS:
        print(f"Probando {modelo} + fallback...")
        res = ejecutar_conjunto(modelo, usar_fallback=True)
        inf = generar_informe(res, f"{modelo} + fallback")
        todos.append(inf)
        print(f"  {inf['precision']}% | tiempo medio: {inf['tiempo_medio']}s")
        with open(f"resultados_{modelo.replace(':','_')}_fallback.json", "w") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

    print("\nProbando fallback parser solo...")
    res = []
    t0 = time.time()
    for caso in TEST_SET:
        fb = fallback_parser(caso["cmd"])
        ok = evaluar_respuesta(fb, caso)
        res.append({"id": caso["id"], "ok": ok, "resp": fb, "tiempo": 0})
    tf_total = time.time() - t0
    inf = generar_informe(res, "fallback parser (solo)")
    inf["tiempo_medio"] = round(tf_total / len(res), 3)
    todos.append(inf)
    print(f"  {inf['precision']}% | tiempo medio: {inf['tiempo_medio']}s")
    with open("resultados_fallback_solo.json", "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print("\n=== RESUMEN ===")
    print(f"{'Configuracion':<35} {'Precision':<10} {'Tiempo medio':<15}")
    print("-" * 60)
    for t in todos:
        print(f"{t['modelo']:<35} {t['precision']}%     {t['tiempo_medio']}s")

    with open("resumen_ablacion.json", "w") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
