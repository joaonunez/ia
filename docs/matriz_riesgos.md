# Matriz de Riesgos con Mitigaciones Verificadas

- **Fecha de generación:** 2026-11-28 15:51 UTC
- **Huella de la matriz:** dba95220e248
- **Riesgos evaluados:** 9

## Resumen ordenado por riesgo residual

| ID | Riesgo | Inherente | Residual | Estado | Evidencias | Límites |
| --- | --- | --- | --- | --- | --- | --- |
| R-03 | Alucinación cualitativa o cifras inventadas en letras no detectables mecánicamente | 16 (CRITICO) | 9 (ALTO) | parcial | `alucinacion:H-01`, `alucinacion:H-02`, `alucinacion:H-03`, `alucinacion:H-04`, `alucinacion:H-05` | H-04, H-05 |
| R-01 | Inyección directa de instrucciones y ofuscación en preguntas del usuario | 20 (CRITICO) | 6 (MEDIO) | parcial | `ataques:A-01`, `ataques:A-04`, `ataques:A-05`, `ataques:A-07`, `matriz:MP-03` | A-07 |
| R-06 | Falla de recuperación ante sinónimos o paráfrasis sin palabras clave literales | 9 (ALTO) | 6 (MEDIO) | parcial | `matriz:MP-06`, `matriz_modelo:MP-07`, `matriz_modelo:MP-08` | MP-08 |
| R-02 | Extracción de instrucciones internas del sistema o secretos mediante el modelo | 15 (CRITICO) | 3 (BAJO) | verificada | `ataques:A-02`, `ataques:A-03`, `fuga:F-03` | — |
| R-04 | Inyección indirecta incrustada en documentos envenenados del corpus | 15 (CRITICO) | 3 (BAJO) | verificada | `ataques:A-06` | — |
| R-08 | Indisponibilidad del proveedor externo o caída silenciosa sin aviso operativo | 12 (ALTO) | 3 (BAJO) | verificada | `pruebas:tests/parciales/test_respaldo.py` | — |
| R-05 | Exposición de PII o texto crudo de consultas en logs y respuestas de error 422 | 16 (CRITICO) | 2 (BAJO) | verificada | `fuga:F-01`, `fuga:F-02`, `matriz:MP-04` | — |
| R-07 | Falsos positivos del filtro anti-inyección que bloquean consultas legítimas | 9 (ALTO) | 2 (BAJO) | verificada | `ataques:B-01`, `ataques:B-02` | — |
| R-09 | Desviación de contratos entre componentes internos o entradas malformadas | 12 (ALTO) | 2 (BAJO) | verificada | `pruebas:tests/parciales/test_contratos.py`, `matriz:MP-05`, `matriz:MP-07` | — |

## Detalle de mitigaciones, límites y supervisión humana

### R-03 — Alucinación cualitativa o cifras inventadas en letras no detectables mecánicamente
- **Puntaje:** inherente `16` (CRITICO) → residual `9` (ALTO)
- **Estado:** `parcial`
- **Mitigación:** Compuerta mecánica `problemas_de_respaldo` bloquea cifras en dígitos, fuentes falsas y respuestas sin fragmentos; los casos semánticos quedan bajo revisión humana obligatoria.
- **Evidencias:** `alucinacion:H-01`, `alucinacion:H-02`, `alucinacion:H-03`, `alucinacion:H-04`, `alucinacion:H-05`
- **Límites cubiertos:** H-04, H-05
- **Nota técnica:** Las afirmaciones cualitativas agregadas (H-04) y cifras escritas en palabras (H-05) no son detectadas por reglas léxicas; se documentan como limitación activa del detector.
- **Supervisión humana obligatoria:** El gestor académico debe validar toda respuesta con la fuente citada antes de emitir comunicaciones formales a apoderados y realizar muestreo semanal de 10 trazas.

### R-01 — Inyección directa de instrucciones y ofuscación en preguntas del usuario
- **Puntaje:** inherente `20` (CRITICO) → residual `6` (MEDIO)
- **Estado:** `parcial`
- **Mitigación:** Normalización Unicode NFKD + casefold y 4 reglas de entrada en `servicio/seguridad.py`, más limpieza de salida en profundidad y ejecución en modo solo lectura.
- **Evidencias:** `ataques:A-01`, `ataques:A-04`, `ataques:A-05`, `ataques:A-07`, `matriz:MP-03`
- **Límites cubiertos:** A-07
- **Nota técnica:** Las variantes con letras separadas por guiones (A-07) evaden las expresiones regulares de entrada; quedan contenidas por limpieza de salida, compuerta de respaldo y solo lectura.

### R-06 — Falla de recuperación ante sinónimos o paráfrasis sin palabras clave literales
- **Puntaje:** inherente `9` (ALTO) → residual `6` (MEDIO)
- **Estado:** `parcial`
- **Mitigación:** Normalización Unicode NFD para tildes combinantes en modo simulado; recuperación semántica con embeddings en Chroma cuando se activa `USE_LIVE_RAG=true`.
- **Evidencias:** `matriz:MP-06`, `matriz_modelo:MP-07`, `matriz_modelo:MP-08`
- **Límites cubiertos:** MP-08
- **Nota técnica:** En modo simulado sin embeddings la paráfrasis pura sin palabras clave compartidas (MP-08) devuelve SIN_INFORMACION en lugar de inventar; aceptado para entorno sin red.

### R-02 — Extracción de instrucciones internas del sistema o secretos mediante el modelo
- **Puntaje:** inherente `15` (CRITICO) → residual `3` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** Bloqueo en entrada (`pedir_instrucciones`, `pedir_secretos`) y capa independiente `limpiar_salida()` que redacta `INSTRUCCION` y claves `AIza...`/`sk-...`.
- **Evidencias:** `ataques:A-02`, `ataques:A-03`, `fuga:F-03`

### R-04 — Inyección indirecta incrustada en documentos envenenados del corpus
- **Puntaje:** inherente `15` (CRITICO) → residual `3` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** `sin_fragmentos_sospechosos()` filtra cada fragmento recuperado antes de construir el prompt y descarta cualquier documento que dispare reglas de inyección.
- **Evidencias:** `ataques:A-06`

### R-08 — Indisponibilidad del proveedor externo o caída silenciosa sin aviso operativo
- **Puntaje:** inherente `12` (ALTO) → residual `3` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** `servicio/respaldo.py` devuelve HTTP 503 explícito por defecto si falta el modelo real y exige habilitar `PERMITIR_RESPALDO=1` para degradación controlada.
- **Evidencias:** `pruebas:tests/parciales/test_respaldo.py`

### R-05 — Exposición de PII o texto crudo de consultas en logs y respuestas de error 422
- **Puntaje:** inherente `16` (CRITICO) → residual `2` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** Logging estructurado con longitudes y huellas SHA-256 (sin texto crudo ni correos) y manejador unificado `servicio/errores.py` que omite valores de entrada y stacktraces.
- **Evidencias:** `fuga:F-01`, `fuga:F-02`, `matriz:MP-04`

### R-07 — Falsos positivos del filtro anti-inyección que bloquean consultas legítimas
- **Puntaje:** inherente `9` (ALTO) → residual `2` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** Reglas de entrada calibradas con calificadores explícitos para permitir palabras académicas comunes ('instrucciones para calcular', 'contraseña del portal').
- **Evidencias:** `ataques:B-01`, `ataques:B-02`

### R-09 — Desviación de contratos entre componentes internos o entradas malformadas
- **Puntaje:** inherente `12` (ALTO) → residual `2` (BAJO)
- **Estado:** `verificada`
- **Mitigación:** Guardias Pydantic (`exigir` con `Fragmento` en `extra='forbid'`) en cada frontera de `servicio/cadena.py` y validación estricta de rutas/body en FastAPI.
- **Evidencias:** `pruebas:tests/parciales/test_contratos.py`, `matriz:MP-05`, `matriz:MP-07`

