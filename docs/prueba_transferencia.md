# Registro de Prueba Cruzada de Transferencia

- **Fecha:** 2026-11-28
- **Revisor:** Revisión cruzada entre pares (simulada con protocolo limpio)
- **Duración total:** 18 min
- **Preguntas al autor:** 0
- **Documentos usados:** `README.md`, `docs/api.md`
- **Tareas logradas:** 5 de 5
- **Huella de la prueba:** 33b469a3753e

## Tareas ejecutadas

| ID | Tarea | Lograda | Min | Nota |
| --- | --- | --- | --- | --- |
| T-01 | Instalar entorno y arrancar el servicio siguiendo solo README.md | Sí | 6 | Arrancó en puerto 8000 con /health en estado ok y modelo_activo simulado. |
| T-02 | Ejecutar una consulta reglamentaria usando el ejemplo de docs/api.md | Sí | 3 | POST /ask devolvió 85 % y fuente reglamento_asistencia.md. |
| T-03 | Consultar un estudiante simulado de solo lectura | Sí | 2 | GET /estudiantes/Sofía Rojas devolvió promedio 6.2 y simulado=true. |
| T-04 | Provocar un error 422 y un 404 y comprobar el contrato de error | Sí | 3 | Ambos devolvieron codigo, mensaje y campos sin trazas ni secretos. |
| T-05 | Realizar dos preguntas propias fuera del ejemplo (una válida y una paráfrasis) | Sí | 4 | La consulta de escala de notas respondió 1.0 a 7.0; la paráfrasis pura activó LIM-01. |

## Observaciones y cierre

### O-01 (T-01) — `documentacion` / `resuelta`
- **Observación:** Se agregó el comando exacto de activación del venv en PowerShell y el arranque local con uvicorn.
- **Acción:** Se incorporó la sección Instalación con nota de Windows y el comando uvicorn en README.md.

### O-02 (T-05) — `producto` / `declarada` · Limitación: `LIM-01`
- **Observación:** En modo simulado sin embeddings, una paráfrasis sin palabras clave literales devuelve SIN_INFORMACION.
- **Acción:** Declarada como limitación LIM-01 en docs/limitaciones.md y mitigada en producción con USE_LIVE_RAG=true.
