# Matriz de riesgos — Asistente académico IA (U2.7 · Bloque 32)

Fecha: **2026-11-27**. Fuente verificable en código: [`src/risk_matrix.py`](../src/risk_matrix.py).

## 1. Escala y cortes aplicados

- **Probabilidad** (`1` a `5`) × **Impacto** (`1` a `5`) = **Puntaje** (`1` a `25`).
- **Categorías**: `CRITICO` (`>= 15`), `ALTO` (`>= 9`), `MEDIO` (`>= 4`), `BAJO` (`< 4`).
- **Regla de gobernanza**: todo riesgo `ALTO` o `CRITICO` cuenta con un **punto de supervisión humana concreto** y al menos dos mitigaciones apuntan a controles ya construidos en el proyecto con su número de bloque.

---

## 2. Matriz de riesgos del proyecto

| # | Riesgo | P | I | Puntaje | Categoría | Al límite (±1) | Mitigación (control construido) | Punto de supervisión humana |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- | --- |
| 1 | Inyección de prompt indirecta incrustada en un reglamento o comentario indexado en Chroma que intenta filtrar instrucciones internas o cambiar el rol | 4 | 4 | 16 | **CRITICO** | Sí (`12` ALTO si P=3 o I=3) | Defensa en 3 capas: separación `SystemMessage`/`HumanMessage`, delimitadores `<contexto_referencia>` y filtro determinista previo en `src/observability_security.py` (**Bloque 31**) | Revisión humana por el encargado técnico antes de re-indexar o aprobar cualquier documento descartado por el filtro de inyección |
| 2 | Alucinación de cifras escolares (porcentaje de asistencia o nota mínima) cuando el corpus RAG no contiene la norma consultada | 3 | 4 | 12 | **ALTO** | Sí (`8` MEDIO si P=2, `16` CRITICO si P=4) | Prompt estricto con citas numeradas `[1]` y regla explícita de admitir falta de contexto + evaluación P/R/F1 en `src/rag_pipeline.py` y `src/rag_evaluator.py` (**Bloques 26 y 27**) | Verificación semanal de respuestas sin cita o con rechazo por el equipo académico antes de cerrar cambios de prompt o corpus |
| 3 | Envío no autorizado de un aviso a un apoderado por error de interpretación del agente con herramientas | 2 | 5 | 10 | **ALTO** | Sí (`8` MEDIO si I=4, `15` CRITICO si P=3) | Compuerta de aprobación humana explícita y traza JSONL auditada en `src/supervision.py` y `docs/agent-autonomy-limits.md` (**Bloque 23**) | Confirmación humana obligatoria (`s`/`n` o botón de aprobación) antes de ejecutar cualquier acción externa hacia apoderados |
| 4 | Despliegue silencioso de una modificación defectuosa del prompt de sistema que degrada citas o desactiva defensas anti-inyección | 2 | 4 | 8 | **MEDIO** | Sí (`12` ALTO si P=3, `10` ALTO si I=5) | Versionado con huella SHA-256 + diff unificado en `src/prompt_registry.py` y flujo de aprobación con `interrupt()` en `src/supervision_graph.py` (**Bloque 32**) | Aprobación explícita de un revisor sobre el diff de prompt antes de activar la nueva huella en producción |
| 5 | Agotamiento de cuota o picos de costo/latencia por aumento excesivo de `k` o bucles de reintento ante errores 429 del proveedor | 2 | 3 | 6 | **MEDIO** | Sí (`9` ALTO si P=3, `3` BAJO si P=1) | Backoff exponencial con jitter, máximo 3 intentos y registro de costo por operación en `src/client.py` (**Bloques 12 y 13**) + benchmark `k=3` vs `k=6` en `src/rag_pipeline.py` (**Bloque 28**) | Revisión mensual del consumo acumulado en JSONL y ajuste de `k` o presupuesto |
| 6 | Exposición accidental de preguntas con PII o llaves de API en logs de depuración del servicio | 1 | 3 | 3 | **BAJO** | Sí (`6` MEDIO si P=2, `4` MEDIO si I=4) | Logging JSON que registra solo longitud y huella SHA-256 corta en `src/observability_security.py` (**Bloque 31**) y exclusión de `.env` en `.gitignore` (**Bloque 4**) | Revisión puntual en PRs que agreguen nuevos campos al logger estructurado |

---

## 3. Análisis de sensibilidad en frontera (`±1`)

Todos los riesgos de la tabla se encuentran a un punto de cambiar de categoría si se ajusta su probabilidad o impacto en `±1`, en especial:
- **Riesgo 4 (`MEDIO`, puntaje 8)**: subir `probabilidad` de 2 a 3 o `impacto` de 4 a 5 lo vuelve **ALTO**; por eso ya cuenta con el grafo de supervisión `interrupt()` en [`src/supervision_graph.py`](../src/supervision_graph.py).
- **Riesgo 2 (`ALTO`, puntaje 12)** y **Riesgo 3 (`ALTO`, puntaje 10)**: un incremento de `+1` en probabilidad los sube a **CRITICO** (`16` y `15`), por lo que sus controles de citas obligatorias y compuerta humana son no negociables.
