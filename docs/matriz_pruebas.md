# Registro de Matriz de Pruebas — `matriz_pruebas`

- **Fecha de ejecución:** 2026-11-28 15:51 UTC
- **Huella de la matriz:** 5c994f05b61a
- **Escenarios ejecutados:** 7
- **Resultado:** 7 PASA · 0 FALLA · 0 limitaciones declaradas

## Resultados por escenario

| ID | Tipo | Cubre | HTTP | Resultado | Escenario |
| --- | --- | --- | --- | --- | --- |
| MP-01 | valido | RF-01, RF-02, CA-01, CA-02 | 200 | PASA | Consulta reglamentaria sobre asistencia mínima con respuesta respaldada y cita |
| MP-02 | valido | RF-03, CA-04 | 200 | PASA | Consulta de notas y asistencia del estudiante simulado Sofía Rojas |
| MP-03 | valido | RF-04, CA-05 | 200 | PASA | Bloqueo temprano de intento directo de inyección de instrucciones |
| MP-04 | invalido | RF-01 | 422 | PASA | Pregunta que excede el límite máximo (501 caracteres) devuelve 422 estructurado |
| MP-05 | invalido | RF-03 | 422 | PASA | Identificador de estudiante con caracteres prohibidos devuelve 422 |
| MP-06 | borde | RF-02 | 200 | PASA | Pregunta con tildes combinantes NFD recupera el reglamento sin perder coincidencia |
| MP-07 | borde | RF-03 | 404 | PASA | Estudiante con formato de nombre válido pero inexistente devuelve 404 controlado |
