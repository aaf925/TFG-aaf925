# Estudio de Ablación

## Qué hace
Evalúa sistemáticamente todas las combinaciones del asistente para medir precisión y latencia. Genera tablas LaTeX listas para incluir en el TFG.

## Combinaciones evaluadas
- **LLMs**: qwen2.5:0.5B, qwen2.5:1.5B, Llama 3.1
- **Fallback parser**: activado / desactivado
- **Combinado**: LLM + fallback vs cada uno por separado

## Archivos

| Archivo | Descripción |
|---|---|
| `test_set.py` | 103 órdenes etiquetadas con acción y dispositivo esperados. |
| `evaluador.py` | Prueba cada combinación contra el test set, mide precisión y tiempo. |
| `generar_tablas.py` | Lee los resultados y genera tabla LaTeX. |

## Cómo usar

```bash
cd mejoras/ablacion
python evaluador.py        # tarda ~5-10 min (consulta Ollama)
python generar_tablas.py   # imprime tabla LaTeX lista para copiar
```

## Salida
- `resumen_ablacion.json`: tabla resumen con precisiones y tiempos medios
- `resultados_*.json`: detalle por caso para cada configuración
- Tabla LaTeX por consola (stdout) para pegar en `06_experimentacion.tex`
