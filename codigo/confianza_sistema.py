import unicodedata, difflib, re
from config import DISPOSITIVOS, UMBRAL_AUTO, UMBRAL_CONFIRMAR

def quitar_tildes(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().replace('ñ', 'n')
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def normalizar(s):
    if not s: return ""
    return quitar_tildes(s.strip().lower())

def puntuar_accion(orden, accion):
    pesos = {
        "encender": ["enciende", "prende", "activa", "conecta", "pon", "enciend"],
        "apagar": ["apaga", "apag", "quita", "desactiva", "desconect"],
        "subir": ["sube", "subir", "abre", "levant"],
        "bajar": ["baja", "bajar", "cierra", "extiend"],
        "regular": ["regula", "ajusta", "poner", "coloca", "ponlo"],
        "consultar": ["temperatura", "dime", "cuanto", "cual es", "consulta"],
    }
    orden_norm = normalizar(orden)
    if accion not in pesos:
        return 0.0
    for p in pesos[accion]:
        if p in orden_norm:
            return 1.0
    return 0.3

def puntuar_dispositivo(orden, nombre_disp):
    orden_norm = normalizar(orden)
    disp_norm = normalizar(nombre_disp)
    pal_orden = set(orden_norm.split())
    pal_disp = set(disp_norm.split())
    matches = pal_orden & pal_disp
    if not matches:
        fuzzy = difflib.get_close_matches(" ".join(pal_disp), [" ".join(pal_orden)], n=1, cutoff=0.6)
        return 0.5 if fuzzy else 0.0
    ratio = len(matches) / max(len(pal_disp), 1)
    return min(1.0, ratio + 0.2)

def validar_consistencia(accion, tipo_dispositivo):
    inconsistencias = {
        ("subir", "luz"): True,
        ("bajar", "luz"): True,
        ("encender", "persiana"): True,
        ("apagar", "persiana"): True,
    }
    return 0.0 if inconsistencias.get((accion, tipo_dispositivo)) else 1.0

def evaluar_confianza(resp, orden, fuente="llm"):
    if not resp:
        return 0.0, "sin respuesta"

    if not isinstance(resp, dict):
        return 0.0, "formato invalido"

    accion = resp.get("accion")
    if not accion:
        return 0.0, "sin accion"

    if accion not in ("encender", "apagar", "subir", "bajar", "regular", "consultar", "salir_voz"):
        return 0.2, f"accion desconocida: {accion}"

    dispositivos = resp.get("dispositivos") or [resp.get("dispositivo")]
    if not dispositivos or not dispositivos[0]:
        return 0.3, "sin dispositivo"

    if fuente == "llm":
        return _evaluar_llm(resp, orden, accion, dispositivos)
    return _evaluar_fallback(resp, orden, accion, dispositivos)

def _evaluar_llm(resp, orden, accion, dispositivos):
    disp = dispositivos[0]
    if disp not in DISPOSITIVOS:
        cercano = difflib.get_close_matches(disp, DISPOSITIVOS.keys(), n=1, cutoff=0.6)
        if cercano:
            return 0.4, f"dispositivo corregido: {disp} -> {cercano[0]}"
        return 0.2, f"dispositivo inexistente: {disp}"

    tipo = DISPOSITIVOS[disp].get("tipo", "")
    p_accion = puntuar_accion(orden, accion)
    p_disp = puntuar_dispositivo(orden, disp)
    p_cons = validar_consistencia(accion, tipo)
    score = 0.3 + 0.3 * p_accion + 0.3 * p_disp + 0.1 * p_cons
    motivo = []
    if p_accion < 0.5: motivo.append("accion dudosa")
    if p_disp < 0.5: motivo.append("dispositivo dudoso")
    if p_cons < 0.5: motivo.append("inconsistencia")
    return round(min(1.0, score), 2), ", ".join(motivo) if motivo else "confianza alta"

def _evaluar_fallback(resp, orden, accion, dispositivos):
    puntuaciones = []
    for d in dispositivos:
        if d in DISPOSITIVOS:
            tipo = DISPOSITIVOS[d].get("tipo", "")
            p_disp = puntuar_dispositivo(orden, d)
            p_cons = validar_consistencia(accion, tipo)
            puntuaciones.append(0.7 * p_disp + 0.3 * p_cons)
        else:
            puntuaciones.append(0.0)
    score = sum(puntuaciones) / max(len(puntuaciones), 1)
    orden_norm = normalizar(orden)
    tiene_num = bool(re.findall(r'\d+', orden_norm))
    tiene_accion_clara = any(w in orden_norm for w in ["enciende", "apaga", "sube", "baja", "regula", "dime"])
    if tiene_num: score += 0.1
    if tiene_accion_clara: score += 0.1
    return round(min(1.0, score), 2), "ok"

def clasificar_confianza(score):
    if score >= UMBRAL_AUTO:
        return "auto"
    if score >= UMBRAL_CONFIRMAR:
        return "confirmar"
    return "rechazar"
