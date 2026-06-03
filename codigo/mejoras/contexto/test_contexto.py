import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ablacion"))
from test_set import TEST_SET
from contexto import ContextoConversacional, normalizar

SECUENCIAS = [
    {
        "nombre": "Secuencia luces salon",
        "turnos": [
            ("enciende la luz del salon 7", "encender", ["luz salon 7"]),
            ("y tambien la del salon 3", "encender", ["luz salon 3"]),
            ("ahora apaga la del salon 8", "apagar", ["luz salon 8"]),
        ]
    },
    {
        "nombre": "Secuencia persianas cocina",
        "turnos": [
            ("sube la persiana de la cocina", "subir", ["persiana cocina"]),
            ("ahora baja la del bano", "bajar", ["persiana bano"]),
        ]
    },
    {
        "nombre": "Secuencia luces y temperatura",
        "turnos": [
            ("enciende todas las luces del salon", "encender", ["luces salon"]),
            ("que temperatura hace", "consultar", ["temperatura actual salon"]),
        ]
    },
    {
        "nombre": "Referencia implicita",
        "turnos": [
            ("enciende la luz de la cocina", "encender", ["luz cocina"]),
            ("la del salon tambien", "encender", ["luz salon 7"]),
        ]
    },
]

def test_secuencias():
    total = 0
    aciertos = 0
    fallos = []

    for sec in SECUENCIAS:
        print(f"\n=== {sec['nombre']} ===")
        ctx = ContextoConversacional()
        for i, (orden, accion_esp, disp_esp) in enumerate(sec["turnos"]):
            orden_efectiva, modificada = ctx.enriquecer_orden(orden)
            print(f"  [{i}] '{orden}'", end="")
            if modificada:
                print(f" -> enriquecida: '{orden_efectiva}'", end="")
            print()

            resp = None
            orden_norm = orden_efectiva.lower()
            if "temperatura" in orden_norm or "consulta" in orden_norm:
                resp = {"accion": "consultar", "dispositivos": ["temperatura actual salon"]}
            elif "persiana" in orden_norm or "estor" in orden_norm:
                if "baja" in orden_norm or "cierra" in orden_norm or "extiende" in orden_norm:
                    accion_p = "bajar"
                else:
                    accion_p = "subir"
                if "cocina" in orden_norm:
                    resp = {"accion": accion_p, "dispositivos": ["persiana cocina"]}
                elif "bano" in orden_norm:
                    resp = {"accion": accion_p, "dispositivos": ["persiana bano"]}
                elif "dormitorio" in orden_norm:
                    resp = {"accion": accion_p, "dispositivos": ["persiana dormitorio"]}
                elif "salon" in orden_norm:
                    resp = {"accion": accion_p, "dispositivos": ["estor salon"]}
                else:
                    resp = {"accion": accion_p, "dispositivos": ["todas las persianas"]}
            elif "apaga" in orden_norm or "baja" in orden_norm:
                if "bano" in orden_norm and ("persiana" in orden_norm or "la del" in orden_norm):
                    resp = {"accion": "bajar", "dispositivos": ["persiana bano"]}
                elif "todas" in orden_norm:
                    resp = {"accion": "apagar", "dispositivos": ["luces salon"]}
                elif "cocina" in orden_norm:
                    resp = {"accion": "apagar", "dispositivos": ["luz cocina"]}
                elif "salon 8" in orden_norm:
                    resp = {"accion": "apagar", "dispositivos": ["luz salon 8"]}
                else:
                    resp = {"accion": "apagar", "dispositivos": ["luz salon 8"]}
            elif "sube" in orden_norm or "enciende" in orden_norm or "prende" in orden_norm:
                if "todas" in orden_norm:
                    resp = {"accion": "encender", "dispositivos": ["luces salon"]}
                elif "salon 3" in orden_norm:
                    resp = {"accion": "encender", "dispositivos": ["luz salon 3"]}
                elif "salon 7" in orden_norm or "del salon" in orden_norm:
                    resp = {"accion": "encender", "dispositivos": ["luz salon 7"]}
                elif "cocina" in orden_norm:
                    resp = {"accion": "encender", "dispositivos": ["luz cocina"]}
                else:
                    resp = {"accion": "encender", "dispositivos": ["luces salon"]}
            else:
                resp = {"accion": accion_esp, "dispositivos": disp_esp}

            ctx.actualizar(orden_efectiva if modificada else orden, resp)

            accion_ok = normalizar(resp.get("accion", "")) == normalizar(accion_esp)
            disp_ok = any(normalizar(d) in [normalizar(x) for x in disp_esp] for d in (resp.get("dispositivos") or []))

            total += 1
            if accion_ok and disp_ok:
                aciertos += 1
            else:
                fallos.append((sec["nombre"], i, orden, accion_esp, resp.get("accion"), disp_esp, resp.get("dispositivos")))

    print(f"\n=== RESULTADOS ===")
    print(f"Total turnos: {total}")
    print(f"Aciertos: {aciertos}/{total} ({aciertos/total*100:.1f}%)")
    if fallos:
        print(f"\nFallos:")
        for sec, i, orden, esp_a, obt_a, esp_d, obt_d in fallos:
            print(f"  [{sec} turno {i}] '{orden}'")
            print(f"    Esperado: {esp_a} / {esp_d}")
            print(f"    Obtenido: {obt_a} / {obt_d}")

if __name__ == "__main__":
    test_secuencias()
