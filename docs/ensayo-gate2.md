# Registro del ensayo funcional — Gate 2 (U2.8 · Bloque S1)

Fecha: **2026-11-27**. Suite de autochequeo: [`tests/test_gate2.py`](../tests/test_gate2.py).

## 1. Hallazgos y correcciones del ensayo integrado

1. **Interfaz de documento entre Bloque 31 y retriever real de LangChain**:
   - **Encontrado**: `filter_suspicious_documents` en `src/observability_security.py` asumía la clase propia `SourceDocument(content, source)`, mientras el retriever real de Chroma/LangChain devuelve objetos `Document(page_content, metadata)`.
   - **Corregido**: se agregó `_extract_doc_fields` en `src/observability_security.py` para soportar ambos contratos (`Document.page_content` + `metadata["fuente"]` y `SourceDocument`), y se verificó en `test_5_filtro_soporta_document_real_y_corta_si_todo_es_sospechoso`.
2. **Validación de `usage_metadata` en `AIMessage`**:
   - **Encontrado**: en `langchain-core` 1.x, construir `AIMessage(usage_metadata={...})` exige incluir `total_tokens` además de `input_tokens` y `output_tokens`.
   - **Corregido**: se normalizaron los fixtures y `log_consumption` mantiene tolerancia si `usage_metadata` viene `None` o vacío.
3. **Contexto 100 % comprometido por inyección indirecta**:
   - **Verificado**: cuando todos los documentos recuperados contienen patrones de inyección, `answer_with_rag` corta antes de invocar al modelo (`model.calls == 0`), devuelve `ALL_DOCS_DISCARDED_REPLY` y emite el warning estructurado con `trace_id`.

## 2. Resultado de los 4 criterios no compensables + ensayo en vivo

Ejecución de `python -m pytest tests/test_gate2.py -v`:

| Prueba | Criterio verificado | Resultado |
| --- | --- | :---: |
| `test_1_pipeline_sin_excepciones` | Indexa, recupera y responde sin excepciones no capturadas | PASSED |
| `test_2_respuesta_cita_fuente` | Respuesta incluye cita numerada `[1]` y fuente verificable | PASSED |
| `test_3_logs_sin_contenido_crudo` | Cero PII (`ana.perez@example.com`) ni pregunta cruda en logs | PASSED |
| `test_4_supervision_pausa_y_reanuda` | Grafo LangGraph pausa (`__interrupt__`) y reanuda (`Command(resume=True)`) | PASSED |
| `test_5_filtro_soporta_document_real_y_corta_si_todo_es_sospechoso` | Interfaz `Document` real y corte seguro sin llamar al LLM | PASSED |
| `test_6_aislamiento_trace_id_en_consultas_consecutivas` | `trace_id` distinto por consulta y `trace_id_var.get() is None` al salir | PASSED |

Suite completa del repositorio (`python -m pytest -q`): **138 passed**.
