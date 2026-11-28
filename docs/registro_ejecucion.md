# Registro de ejecución

<!-- AUTO:INICIO -->
## Ejecución

| Campo | Valor |
|---|---|
| Fecha (UTC) | 2026-11-28 15:25:54 |
| Commit del código | b8d3f07 (con cambios sin confirmar) |
| Python | 3.13.7 |
| Imágenes | ejecución local uvicorn (api:8000, interfaz:8080) |

## Componentes

| Componente | Modo | Detalle |
|---|---|---|
| Interfaz web | real | interfaz/main.py (FastAPI puerto 8080) |
| API | real | servicio/main.py (FastAPI puerto 8000) |
| Recuperación | simulado | corpus en memoria (src/rag_corpus.py + servicio/cadena.py) |
| Datos de estudiantes | simulado | ESTUDIANTES_SIMULADOS en servicio/logica.py |
| Modelo | simulado | ModeloSimulado, sin red ni clave |

## Resultados

- Escenarios: 14 de 14 cumplidos (por la interfaz).
- Pruebas automáticas: 218 pasan, 0 fallan.
- Ajustes: 4 iteraciones, 3 conservadas (ver docs/bitacora_ajustes.md).

| Escenario | Categoría | Resultado |
|---|---|---|
| E-01 | frecuente | pasa |
| E-02 | frecuente | pasa |
| E-03 | variante | pasa |
| E-04 | variante | pasa |
| E-05 | variante | pasa |
| E-06 | variante | pasa |
| E-07 | compuesta | pasa |
| E-08 | fuera de alcance | pasa |
| E-09 | fuera de alcance | pasa |
| E-10 | sin mezcla | pasa |
| E-11 | error esperado | pasa |
| E-12 | error esperado | pasa |
| E-13 | control | pasa |
| E-14 | control | pasa |
<!-- AUTO:FIN -->

## Qué se observó

La cadena completa de cuatro componentes (`recuperar`, `construir_prompt`, `generar` y `empaquetar`) respondió de forma determinista a través de la interfaz web y la API FastAPI en los 14 escenarios de prueba, manteniendo citas verificables y tiempos locales de milisegundos. Las guardias de contrato en frontera (`servicio/contratos.py`) y la validación estricta `422` evitaron fugas de contenido interno ante entradas vacías o de 600 caracteres.

## Qué no se probó

Esta ejecución corrió con `ModeloSimulado` en memoria (sin llamadas de red al proveedor real de Gemini ni consumo de cuota real) y con datos ficticios de estudiantes y corpus reglamentario de prueba; si se activa `MODELO=real` con `PERMITIR_RESPALDO=1`, el componente `Modelo` opera en modo `respaldo` (`ModeloRespaldo`, ver `docs/respaldos.md`) hasta integrar el cliente real. Tampoco se probó concurrencia multiusuario ni conexión a base de datos PostgreSQL de producción.

## Siguiente paso

Avanzar a la Unidad 3.5 para ejecutar la matriz formal de pruebas de borde, las sondas de detección mecánica de alucinaciones y la verificación de mitigaciones de inyección y fuga de datos antes del Gate 3.
