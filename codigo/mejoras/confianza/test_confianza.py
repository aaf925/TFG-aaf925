import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ablacion"))
from test_set import TEST_SET
from confianza import procesar_con_confianza, UMBRAL_AUTO, UMBRAL_CONFIRMAR

def test():
    resultados = []
    for caso in TEST_SET:
        orden = caso["cmd"]
        resp, score, motivo, fuente = procesar_con_confianza(orden)

        # Determinar si el sistema aceptaria o pediria confirmacion
        if score >= UMBRAL_AUTO:
            decision = "auto"
        elif score >= UMBRAL_CONFIRMAR:
            decision = "confirmar"
        else:
            decision = "rechazar"

        accion = resp.get("accion") if resp else None
        dispositivos = (resp.get("dispositivos") or [resp.get("dispositivo")]) if resp else []

        # Evaluar si la accion es correcta
        accion_correcta = (accion == caso["accion"])
        if accion_correcta and caso["accion"] is None:
            accion_correcta = True  # rechazar correctamente

        resultados.append({
            "id": caso["id"],
            "cmd": orden,
            "esperado": caso["accion"],
            "obtenido": accion,
            "dispositivos": dispositivos,
            "confianza": score,
            "motivo": motivo,
            "fuente": fuente,
            "decision": decision,
            "acierto": accion_correcta,
        })

    total = len(resultados)
    auto = sum(1 for r in resultados if r["decision"] == "auto")
    confirmar = sum(1 for r in resultados if r["decision"] == "confirmar")
    rechazar = sum(1 for r in resultados if r["decision"] == "rechazar")
    aciertos = sum(1 for r in resultados if r["acierto"])

    print("=== TEST SISTEMA DE CONFIANZA ===")
    print(f"Total casos: {total}")
    print(f"Auto (sin preguntar): {auto} ({auto/total*100:.1f}%)")
    print(f"Pide confirmacion: {confirmar}")
    print(f"Rechazados: {rechazar}")
    print(f"Aciertos: {aciertos}/{total} ({aciertos/total*100:.1f}%)")
    print()

    print("--- Casos con decision no-auto ---")
    for r in resultados:
        if r["decision"] != "auto":
            print(f"  [{r['decision']}] id={r['id']} '{r['cmd']}' -> {r['obtenido']} (score={r['confianza']}, {r['motivo']})")

    with open("resultados_confianza.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    test()
