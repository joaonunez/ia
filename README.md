# Proyecto gradual de Joao Nunez — Especialización en Desarrollo con IA Generativa (Accenture)

Repositorio: https://github.com/joaonunez/ia

Asistente IA de **solo lectura** para el gestor académico de una intranet escolar: responde consultas en lenguaje natural sobre notas y asistencia usando la API de Gemini (`gemini-3.5-flash-lite`, elegido en [`docs/decision-arquitectura.md`](docs/decision-arquitectura.md)).

## Qué hay hecho

| Unidad | Fecha | Qué | Dónde |
| --- | --- | --- | --- |
| U1.2–U1.3 | 2026-10-16 | Primera petición autenticada, módulo de consumo y excepciones | `src/gemini_api.py` |
| U1.4 | 2026-10-21 | Arquitectura y comparación de modelos | `docs/decision-arquitectura.md`, `src/compare_models.py` |
| U1.5 | 2026-10-22 | Banco de prompts y prueba de consistencia | `prompts/` |
| U2.1 | 2026-10-28 | Cliente modular con reintentos, costo y pruebas | `src/client.py`, `tests/test_client.py` |
| U2.2 | 2026-10-28 | Pipeline de texto, métricas y límites | `src/text_pipeline.py`, `src/text_metrics.py`, `docs/metric-limits.md` |
| U2.3 | 2026-11-05 | Chain orquestada con LangChain: clasificar, bifurcar, revisar y manejar fallos | `src/routing.py`, `docs/orchestration.md` |
| U2.4 | 2026-11-12 | Agente con tres herramientas, memoria por sesión, aprobación humana y trazas | `src/agent.py`, `src/supervision.py`, `docs/agents.md`, `docs/agent-autonomy-limits.md` |
| U2.5 | 2026-11-25 | Flujo RAG modular con Chroma, citas, evaluación P/R/F1 y registro de latencia y costo | `src/rag_indexer.py`, `src/rag_evaluator.py`, `src/rag_pipeline.py`, `tests/test_rag.py`, `docs/rag-latency-cost.md`, `docs/rag-latency-cost.jsonl`, `docs/rag-metrics.json` |
| U2.6 | 2026-11-27 | Dataset PEFT validado, estimación de costos de etiquetado y decisión fundamentada de personalización | `src/tuning_dataset.py`, `src/personalization_decision.py`, `tests/test_personalization.py`, `docs/decision-personalizacion.md` |
| U2.7 | 2026-11-27 | Logging JSON con `trace_id`, filtro anti-inyección en 3 capas, versionado de prompts, supervisión LangGraph y matriz de riesgos | `src/observability_security.py`, `src/prompt_registry.py`, `src/supervision_graph.py`, `src/risk_matrix.py`, `tests/test_observability_security.py`, `docs/matriz-riesgos.md` |

## Cómo correrlo

```bash
python -m venv venv
pip install -r requirements.txt
python -m pytest
python src/routing.py
python src/agent.py
python src/rag_indexer.py
python src/rag_pipeline.py
python src/tuning_dataset.py
python src/personalization_decision.py
python src/observability_security.py
python src/prompt_registry.py
python src/supervision_graph.py
python src/risk_matrix.py
```

Las pruebas no llaman al proveedor (132 tests en verde). `src/routing.py`, `src/agent.py`, `src/rag_indexer.py` y `src/rag_pipeline.py` sí: necesitan `API_KEY` (o `GEMINI_API_KEY`) en el `.env`. `routing.py` hace nueve llamadas reales; `agent.py` hace unas doce y se detiene a pedir tu aprobación (`s`/`n`) antes de enviar el aviso simulado al apoderado; `rag_indexer.py` indexa los 8 documentos en `vectorstore/` y `rag_pipeline.py` evalúa `k=1..4` y registra latencia y costo en `docs/rag-metrics.json`.

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
