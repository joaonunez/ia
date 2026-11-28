# Registro de Matriz de Pruebas — `matriz_modelo`

- **Fecha de ejecución:** 2026-11-28 15:51 UTC
- **Huella de la matriz:** 5242114684fd
- **Escenarios ejecutados:** 9
- **Resultado:** 8 PASA · 1 FALLA · 1 limitaciones declaradas

## Resultados por escenario

| ID | Tipo | Cubre | HTTP | Resultado | Escenario |
| --- | --- | --- | --- | --- | --- |
| MP-01 | valido | RF-01, RF-02, CA-01, CA-02 | 200 | PASA | Consulta reglamentaria sobre porcentaje mínimo de asistencia con cita verificable |
| MP-02 | valido | RF-03, CA-04 | 200 | PASA | Consulta de notas y asistencia de estudiante simulado existente |
| MP-03 | valido | RF-02, CA-03 | 200 | PASA | Pregunta fuera del corpus escolar no inventa datos y devuelve fuentes vacías |
| MP-04 | invalido | RF-01 | 422 | PASA | Pregunta bajo el mínimo de 3 caracteres rechazada con 422 |
| MP-05 | invalido | RF-01 | 422 | PASA | Pregunta de 501 caracteres (límite + 1) rechazada con 422 |
| MP-06 | borde | RF-03 | 404 | PASA | Nombre de estudiante con formato válido pero inexistente devuelve 404 |
| MP-07 | borde | RF-02 | 200 | PASA | Pregunta con tildes combinantes Unicode NFD recupera correctamente el reglamento |
| MP-08 | borde | RF-02 | 200 | FALLA | Paráfrasis sin palabras clave literales del corpus (sinonimia: faltas/alumno/repetir) |
| MP-09 | borde | RF-03 | 422 | PASA | Nombre de estudiante con símbolos inválidos rechazado con 422 |

## Hallazgos y limitaciones declaradas

### MP-08 — limitacion
- **Escenario:** Paráfrasis sin palabras clave literales del corpus (sinonimia: faltas/alumno/repetir)
- **Motivo observado:** falta texto esperado: '85 %'; falta fuente: 'reglamento_asistencia.md'
- **Decisión:** En modo simulado la recuperación léxica exige coincidencia exacta de raíces y no resuelve sinónimos ('faltas'/'inasistencia'); en producción con USE_LIVE_RAG=true se mitiga con embeddings en Chroma y se declara en README.md.

