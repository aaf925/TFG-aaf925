# Asistente SmartHome - TFG

Asistente de voz para domótica KNX con inteligencia artificial local.

## Requisitos

- Python 3.12
- Ollama (con qwen2.5:1.5b)
- SpaceLynk en la red local
- Micrófono y altavoz (opcional: Sonos)

## Instalación

```bash
pip install -r requirements.txt
ollama pull qwen2.5:1.5b
```

Configurar `config.py` con la IP de SpaceLynk y credenciales.

## Uso

```bash
python asistente.py
```

Seleccionar modo: T (texto), V (voz).

## App móvil

Si se desea usar la aplicación móvil, clonar también el repositorio CTFG en la misma carpeta:

```bash
git clone github.com/aaf925/TFG-aaf925 ../CTFG
```

El asistente en modo voz arrancará automáticamente la API para la app móvil.
