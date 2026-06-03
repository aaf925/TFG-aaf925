# Sistema de Confianza y Confirmación

## Qué hace
Asigna un nivel de confianza (0.0–1.0) a cada comando detectado. Si la confianza es baja, el asistente pide confirmación antes de ejecutar. Evita activaciones accidentales cuando el LLM o el parser no están seguros.

## Cómo funciona
- **Score ≥ 0.7**: ejecución automática
- **0.4 ≤ Score < 0.7**: pregunta "¿Confirmar?" al usuario
- **Score < 0.4**: rechaza silenciosamente

El score se calcula combinando:
- Puntuación de la acción (qué tan clara es en el texto)
- Puntuación del dispositivo (qué tan bien coincide con el mapa KNX)
- Validación de consistencia (ej. "subir" + "luz" = inconsistente → penaliza)

## Archivos

| Archivo | Descripción |
|---|---|
| `confianza.py` | Núcleo: funciones `evaluar_confianza()` y `procesar_con_confianza()`. Incluye modo demo interactivo. |
| `test_confianza.py` | Prueba automática contra el conjunto de 103 órdenes. |

## Cómo usar

### Modo interactivo
```bash
cd mejoras/confianza
python confianza.py
```
Escribe órdenes y ves el score, motivo, y si pide confirmación.

### Evaluación automática
```bash
python test_confianza.py
```
Procesa las 103 órdenes del banco de pruebas y muestra:
- % de ejecuciones automáticas
- % de aciertos
- Lista de casos que requieren confirmación

### Integrar en el asistente
```python
from confianza import procesar_con_confianza, UMBRAL_AUTO

resp, score, motivo, fuente = procesar_con_confianza(orden)
if score >= UMBRAL_AUTO:
    ejecutar(resp)
else:
    # preguntar al usuario
    print(f"Confianza baja ({score}): {motivo}")
```
