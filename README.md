# Proyecto gradual de Joao Nunez — Especialización en Desarrollo con IA Generativa (Accenture)

Repositorio: https://github.com/joaonunez/ia

Asistente IA de **solo lectura** para el gestor académico de una intranet escolar: responde consultas en lenguaje natural sobre notas y asistencia usando la API de Gemini (`gemini-3.5-flash-lite`, elegido en [`docs/decision-arquitectura.md`](docs/decision-arquitectura.md)).

## Qué hay hecho

| Unidad | Qué | Dónde |
| --- | --- | --- |
| U1.2–U1.3 | Primera petición autenticada, módulo de consumo y excepciones | `src/gemini_api.py` |
| U1.4 | Arquitectura y comparación de modelos | `docs/decision-arquitectura.md`, `src/compare_models.py` |
| U1.5 | Banco de prompts y prueba de consistencia | `prompts/` |
| U2.1 | Cliente modular con reintentos, costo y pruebas | `src/client.py`, `tests/test_client.py` |
| U2.2 | Pipeline de texto, métricas y límites | `src/text_pipeline.py`, `src/text_metrics.py`, `docs/metric-limits.md` |
| U2.3 | Chain orquestada con LangChain: clasificar, bifurcar, revisar y manejar fallos | `src/routing.py`, `docs/orchestration.md` |

## Cómo correrlo

```bash
python -m venv venv
pip install -r requirements.txt
python -m pytest
python src/routing.py
```

Las pruebas no llaman al proveedor. `src/routing.py` sí: necesita `API_KEY` en el `.env` y hace nueve llamadas reales.

## Idioma del código

Archivos, funciones y variables van en inglés. Comentarios, mensajes y la instrucción del modelo van en español. El detalle está en [`docs/idioma-del-codigo.md`](docs/idioma-del-codigo.md).

## Cómo empezar

Estos pasos se completan de forma progresiva a lo largo de la Unidad U1.2, no todos el mismo día:

1. Descarga este archivo comprimido (adjunto en la plataforma) y descomprímelo en tu computador. Inicializa el control de versiones sobre esa carpeta y registra tu primer commit con esta estructura base, tal como llegó, antes de modificar nada.
2. Crea tu entorno virtual de Python (por ejemplo, con `venv`) y actívalo.
3. Instala las dependencias que necesites y regístralas en `requirements.txt` (al inicio puede estar vacío o con muy pocas).
4. Copia `.env.example` a un archivo nuevo llamado `.env`, y completa ahí tus credenciales reales (llaves de API, tokens). El archivo `.env` nunca se sube al repositorio: ya está excluido en `.gitignore`.

## Estructura de carpetas

- `src/` : todo el código fuente de tu proyecto va aquí.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de tu código (las vas a usar más adelante en el programa, cuando el proyecto lo requiera).
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno que tu proyecto necesita, sin valores reales. Tu archivo `.env` real (con tus credenciales) nunca se commitea.
- `.gitignore` : le dice a Git qué archivos y carpetas ignorar (entre ellos, tu entorno virtual y tu archivo `.env`).

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.
