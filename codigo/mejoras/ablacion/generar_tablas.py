import json

def cargar_resumen(path="resumen_ablacion.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def escape_latex(s):
    return s.replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")

def tabla_principal(resumen):
    nombres = {
        "qwen2.5:0.5b": "qwen2.5:0.5B",
        "qwen2.5:1.5b": "qwen2.5:1.5B",
        "llama3.1": "Llama 3.1",
    }
    for n, v in nombres.items():
        for r in resumen:
            r["modelo"] = r["modelo"].replace(n, v)

    out = []
    out.append("% Generado automaticamente por mejoras/ablacion/generar_tablas.py")
    out.append("\\begin{table}[ht]")
    out.append("\\centering")
    out.append("\\begin{tabular}{l c c c}")
    out.append("\\hline")
    out.append("\\textbf{Configuracion} & \\textbf{Precision} & \\textbf{Tiempo medio} & \\textbf{Aciertos} \\\\")
    out.append("\\hline")
    for r in resumen:
        m = escape_latex(r["modelo"])
        out.append(f"{m} & {r['precision']}\\% & {r['tiempo_medio']}s & {r['aciertos']}/{r['total']} \\\\")
    out.append("\\hline")
    out.append("\\end{tabular}")
    out.append("\\caption{Resultados del estudio de ablacion.}")
    out.append("\\label{tab:ablacion}")
    out.append("\\end{table}")
    return "\n".join(out)

if __name__ == "__main__":
    try:
        resumen = cargar_resumen()
        print(tabla_principal(resumen))
    except FileNotFoundError:
        print("Ejecuta primero: python evaluador.py")
