# Flujo RAG: evaluación, latencia, costo y checklist operativo (U2.5 · Bloque 28)

Evidencia generada en vivo el **2026-11-25** contra Gemini (`models/gemini-embedding-001` + `gemini-3.5-flash-lite`) y ChromaDB persistido localmente en `vectorstore/` (excluido en `.gitignore`). Datos completos en [`rag-metrics.json`](./rag-metrics.json).

---

## 1. Corpus e indexación (`src/rag_indexer.py`)

- **Corpus propio**: 8 documentos del asistente del gestor académico (`reglamento_asistencia.md`, `reglamento_notas.md`, `protocolo_apoderados.md`, `cliente_reintentos.md`, `decision_modelo_costos.md`, `arquitectura_solo_lectura.md`, `limites_autonomia.md`, `estrategia_pruebas.md`).
- **Estrategia de chunking**: `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=45)` — respeta párrafos/oraciones, preserva metadatos (`fuente`, `fecha`, `tema`, `doc_id`) y asigna IDs explícitos (`doc0`..`doc7`).
- **Persistencia verificada**: tras indexar una vez, `load_vectorstore()` se reconecta desde disco sin recalcular embeddings (`count() == 8`).

## 2. Evaluación de recuperación (`src/rag_evaluator.py`)

Conjunto de **8 casos etiquetados manualmente** (7 respondibles + 1 fuera del corpus con `relevant_ids = set()`):

| `k` | Precisión promedio | Exhaustividad (Recall) | F1 |
|---:|---:|---:|---:|
| 1 | 0.8750 | 1.0000 | **0.9333** |
| 2 | 0.4375 | 1.0000 | 0.6087 |
| 3 | 0.2916 | 1.0000 | 0.4515 |
| 4 | 0.2188 | 1.0000 | 0.3590 |

- En los 7 casos con respuesta, el chunk correcto apareció en el **puesto #1** (`recall = 1.0` desde `k=1`).
- El caso 8 (sin respuesta en el corpus) devolvió `recall = None` (ignorado en el promedio para no distorsionar la métrica) y en la generación el modelo respondió explícitamente que el contexto no alcanza.

## 3. Latencia y costo real del flujo RAG completo (`src/rag_pipeline.py`, `k=3`)

| Consulta | Recuperación (ms) | Generación (ms) | Total (ms) | Tokens (emb / in / out) | Costo (USD) | Cita principal |
|---|---:|---:|---:|---:|---:|---|
| Porcentaje mínimo de asistencia | 307.43 | 1650.34 | 1957.87 | 17 / 257 / 17 | 0.00012215 | `[1]` `reglamento_asistencia.md` |
| Cliente HTTP ante 429 y 401 | 311.92 | 1419.78 | 1731.75 | 15 / 284 / 80 | 0.00028745 | `[1]` `cliente_reintentos.md` |
| Rol de BD en producción | 310.86 | 784.70 | 1095.60 | 15 / 277 / 24 | 0.00014535 | `[1]` `arquitectura_solo_lectura.md` |
| Nombre del director (fuera de corpus) | 309.84 | 1176.28 | 1486.17 | 12 / 240 / 17 | 0.00011630 | Rechazó inventar |
| **Promedio / Total** | **310.01 ms** | **1257.78 ms** | **1567.85 ms** | — | **USD 0.00067125** | — |

- La búsqueda dentro de Chroma es local y gratuita; los ~310 ms de recuperación corresponden al embedding de la consulta en Gemini.
- El ~80 % de la latencia total y casi todo el costo corresponde a la llamada de generación.

## 4. Checklist operativo del flujo RAG

- [x] `vectorstore/` excluido en `.gitignore` y reconstruible con `python src/rag_indexer.py`.
- [x] Reconexión a disco sin re-indexar (`load_vectorstore`) en cada consulta.
- [x] Metadatos `fuente` y `fecha` presentes en 100 % de los chunks (cero citas `"desconocida"`).
- [x] Prompt dinámico con instrucción explícita de citar `[N]` y admitir falta de contexto.
- [x] Manejo de errores sin caídas ni exposición de stack traces al usuario.
- [x] Suite de pruebas unitarias sin llamadas a la API (`pytest tests/test_rag.py`: 11/11 en verde; suite completa: 97/97 en verde).
