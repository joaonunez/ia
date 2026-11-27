# Decisión de personalización: asistente del gestor académico

Cierra la Unidad 2.6 (Bloque 30 · Actividad Core). Fecha: **2026-11-27**. Respaldado por [`src/personalization_decision.py`](../src/personalization_decision.py), [`src/tuning_dataset.py`](../src/tuning_dataset.py) y las mediciones reales de [`rag-latency-cost.md`](./rag-latency-cost.md).

## 1. El problema

El asistente del gestor académico necesita responder consultas operativas y normativas del establecimiento (porcentaje mínimo de asistencia para promoción, escala de notas, protocolos de aviso a apoderados, políticas internas y operación del propio servicio) citando la fuente vigente y admitiendo cuando el contexto no alcanza. El contenido reglamentario y las circulares del establecimiento cambian a lo largo del año escolar, y el modelo base no conoce documentos internos que no existían en su entrenamiento.

## 2. Resultado del método de decisión

Evaluación ejecutada con `recommend_strategy(PROJECT_ANSWERS)` sobre las cinco preguntas del Bloque 30:

| Criterio | Respuesta | Evidencia concreta del proyecto |
|---|---|---|
| `informacion_cambia_seguido` | `True` | Reglamentos internos, circulares y calendarios escolares se actualizan cada trimestre/mes; el corpus propio de 8 documentos se actualizó el 2026-11-25. |
| `problema_de_formato_o_tono` | `False` | En las 20 salidas evaluadas en U2.2 (`docs/metric-limits.md`), el banco de prompts con `responseSchema` (U1.5) y las 4 corridas RAG de U2.5 (`docs/rag-metrics.json`), menos del 15 % incumplió el formato esperado. |
| `dataset_grande_y_de_calidad` | `False` | Existen 12 ejemplos etiquetados y validados en `src/tuning_dataset.py`, por debajo del umbral de 200 ejemplos. |
| `presupuesto_limitado_o_iterar_rapido` | `True` | Operamos en nivel gratuito de Gemini (`gemini-3.5-flash-lite`) y un cambio de normativa debe reflejarse en minutos, no en horas de reentrenamiento. |
| `necesita_multiples_variantes` | `False` | Un solo asistente base con metadatos por fuente/tema cubre el alcance actual sin mantener múltiples adapters. |

Puntaje obtenido:
- **RAG**: **5 puntos**
- **PEFT**: **1 punto**
- **Fine-tuning completo**: **0 puntos**

Ganadora sin empate: **RAG**.

### Análisis de sensibilidad

Al invertir una respuesta a la vez (`sensitivity_analysis(PROJECT_ANSWERS)`):
- Cambiar cualquiera de las otras 4 respuestas (`problema_de_formato_o_tono`, `dataset_grande_y_de_calidad`, `presupuesto_limitado_o_iterar_rapido` o `necesita_multiples_variantes`) mantiene a **RAG** como ganador único (5 vs 3, 5 vs 2, 3 vs 0, 5 vs 3).
- Solo si `informacion_cambia_seguido` pasara a `False` (escenario irreal para normativa escolar viva), RAG bajaría a 2 puntos y seguiría ganando frente a PEFT (1) y Fine-tuning (0). La decisión es estable ante cualquier cambio individual.

## 3. Técnica elegida y por qué

**Elijo RAG** (combinado con `responseSchema` / prompt de sistema para el formato JSON).

1. **Resuelve el problema real**: al asistente le falta información interna y vigente del colegio, no capacidad de redacción. Enseñar hechos cambiantes por fine-tuning o PEFT introduce riesgo de memorización desactualizada y no permite citar el documento fuente `[1]`.
2. **Costo e iteración**: en nuestra corrida real de U2.5 (`docs/rag-metrics.json`), el flujo RAG completo logró **recall = 1.0** en los 7 casos respondibles, latencia promedio de **1.17 s** y un costo de **USD 0.00017 por consulta**. Actualizar un reglamento toma segundos (reindexar el documento), frente a minutos u horas por intento en PEFT/fine-tuning.
3. **Descarte fundado de alternativas**:
   - **Fine-tuning completo**: descartado por costo de cómputo, lentitud de iteración y falta de un dataset de cientos/miles de ejemplos.
   - **PEFT**: descartado para esta etapa porque hoy solo tenemos 12 ejemplos validados y no existe un problema de formato/tono ≥15 %. Se deja anotado como complemento futuro únicamente si a escala se exige un formato institucional rígido con ≥200 ejemplos reales aprobados.
   - **Soft-prompting**: descartado porque no está expuesto en la API gestionada de Gemini.

## 4. Qué necesitarías para ejecutarla

- **Corpus ya indexado**: **8 documentos** propios en `src/rag_indexer.py` (8 chunks en ChromaDB local, `count() == 8`), evaluados con **8 casos** etiquetados manualmente en `src/rag_evaluator.py`.
- **Corpus faltante para pasar de demo a piloto escolar completo**: falta indexar **12 documentos** adicionales (reglamento de evaluación vigente, reglamento interno de convivencia, calendario anual, circulares de apoderados y protocolos Mineduc/SIGE) para completar un corpus piloto de **20 documentos**, y ampliar el conjunto de evaluación manual de **8 a 20 preguntas** (12 preguntas adicionales, ~1 hora de etiquetado a 5 minutos por pregunta).
- **Infraestructura y mantenimiento**: mantener el índice vectorial persistente (Chroma local en el proyecto del curso; migración a `pgvector` en Postgres al llevarlo a producción) con reindexación controlada cada vez que se modifique un documento (tiempo estimado < 1 minuto por lote de 20 documentos).
- **Referencia comparativa si a futuro se evaluara PEFT**: pasar de los **12 ejemplos** actuales en `src/tuning_dataset.py` a **200 ejemplos** requeriría etiquetar **188 ejemplos adicionales**; a 5 minutos por ejemplo más 20 % de segunda revisión (2 minutos por ejemplo revisado), equivaldría a **16,92 horas de trabajo humano (2,12 jornadas de 8 h)** y aproximadamente **USD 423** (a USD 25/h), costo que hoy se evita al usar RAG.
