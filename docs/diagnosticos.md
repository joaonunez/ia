# Registro de diagnósticos de integración (U3.4 · Bloque 39)

## Fallo 1: KeyError en la frontera entre `recuperar` y `construir_prompt`

- **Síntoma:** la interfaz y la API responden `500 error_interno` al consultar el reglamento escolar.
- **Dónde se rompió:** `recuperar()` entregó la clave `contenido` en lugar de `texto` (el nombre del campo interno de `CORPUS` en `src/rag_corpus.py`), y `construir_prompt()` falló con `KeyError: 'texto'`.
- **Causa:** desacuerdo de contrato entre el esquema del corpus (`contenido`) y el contrato de fragmentos de la cadena (`{"fuente", "texto"}`).
- **Arreglo:** `recuperar()` mapea explícitamente `{"fuente": doc["fuente"], "texto": doc["contenido"]}` para cumplir el contrato `Fragmento`.
- **Qué lo evita:** guardia `exigir(list[Fragmento], fragmentos, "recuperar")` en `servicio/contratos.py` con `ConfigDict(extra="forbid")` y la suite `tests/parciales/test_contratos.py`.
