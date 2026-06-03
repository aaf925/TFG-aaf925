import unicodedata, difflib, re, json, requests, time, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "TFG Alejandro"))
from asistente_texto import DISPOSITIVOS, quitar_tildes, fallback_parser

class ContextoConversacional:
    def __init__(self):
        self.ultima_accion = None
        self.ultimos_dispositivos = []
        self.ultimo_valor = None
        self.ultima_orden = ""
        self.historial = []

    def actualizar(self, orden, resp):
        self.ultima_orden = orden
        if resp:
            self.ultima_accion = resp.get("accion")
            self.ultimos_dispositivos = (
                resp.get("dispositivos") or [resp.get("dispositivo")] or []
            )
            self.ultimo_valor = resp.get("valor")
        self.historial.append((orden, resp))
        if len(self.historial) > 10:
            self.historial.pop(0)

    def limpiar(self):
        self.ultima_accion = None
        self.ultimos_dispositivos = []
        self.ultimo_valor = None
        self.ultima_orden = ""

    def enriquecer_orden(self, orden):
        orden_norm = quitar_tildes(orden.lower().strip())
        if not self.ultima_accion:
            return orden, False

        modificada = False
        palabras = set(orden_norm.split())

        es_referencia = any(
            p in palabras for p in [
                "tambien", "igual", "igualito", "lo mismo",
                "ahi", "alli", "allí", "ahora",
                "y", "ademas", "también",
            ]
        )

        es_parcial = (
            not any(a in orden_norm for a in [
                "enciende", "apaga", "sube", "baja", "regula",
                "prende", "activa", "desactiva", "abre", "cierra",
                "levanta", "extiende", "consulta", "dime",
            ])
            and "luz" not in orden_norm
            and "persiana" not in orden_norm
            and "estor" not in orden_norm
        )

        if es_referencia or es_parcial:
            accion = self.ultima_accion
            if es_parcial and not es_referencia:
                orden = f"{self.ultima_accion} {orden}"
                modificada = True
            elif es_referencia:
                refs = {
                    "tambien": "tambien", "también": "tambien",
                    "igual": "igual", "ademas": "ademas",
                    "ahora": "ahora", "y": "ademas",
                }
                conector = "ademas"
                for k, v in refs.items():
                    if k in palabras:
                        conector = v
                        break
                orden = f"{accion} {conector} {orden}"
                modificada = True

        return orden, modificada

    def prompt_contexto(self):
        if not self.ultima_accion:
            return ""
        disp_str = ", ".join(self.ultimos_dispositivos[:3])
        return (
            f"\nContexto de la orden anterior: "
            f"accion='{self.ultima_accion}', "
            f"dispositivos=[{disp_str}]"
            f"{', valor=' + str(self.ultimo_valor) if self.ultimo_valor is not None else ''}."
            f"\nSi la nueva orden es una continuacion o referencia a la anterior, "
            f"usa el contexto para completarla."
        )

def normalizar(s):
    if not s: return ""
    return quitar_tildes(s.strip().lower())

def consultar_llm(orden, contexto=""):
    url = "http://localhost:11434/api/generate"
    prompt = (
        "Convierte la orden del usuario en JSON. "
        f"Dispositivos: [{', '.join(DISPOSITIVOS.keys())}]. "
        f"Campos: accion, dispositivos, valor (opcional)."
        f"{contexto}"
        f"\nOrden: {orden}\nJSON:"
    )
    try:
        r = requests.post(url, json={
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False, "format": "json",
            "options": {"temperature": 0}
        }, timeout=7)
        return json.loads(r.json()["response"])
    except:
        return None

def procesar_con_contexto(orden, ctx, usar_llm=True):
    orden_enriquecida, modificada = ctx.enriquecer_orden(orden)
    prompt_ctx = ctx.prompt_contexto()
    resp = None
    if usar_llm:
        resp = consultar_llm(orden_enriquecida, prompt_ctx)
    if not resp:
        resp = fallback_parser(orden_enriquecida)
    ctx.actualizar(orden_enriquecida if modificada else orden, resp)
    return resp, orden_enriquecida if modificada else orden, modificada

def modo_demo():
    print("=== MODO DEMO: Contexto Conversacional ===")
    ctx = ContextoConversacional()

    while True:
        orden = input("\nOrden (o 'salir'): ").strip().lower()
        if orden in ("salir", "exit"):
            break
        if not orden:
            continue

        resp, orden_efectiva, modificada = procesar_con_contexto(orden, ctx)
        if modificada:
            print(f"  (orden enriquecida: '{orden}' -> '{orden_efectiva}')")
        if resp:
            print(f"  Accion: {resp.get('accion')}")
            print(f"  Dispositivo(s): {resp.get('dispositivos') or resp.get('dispositivo')}")
            print(f"  Valor: {resp.get('valor')}")
        else:
            print("  Sin respuesta")

if __name__ == "__main__":
    modo_demo()
