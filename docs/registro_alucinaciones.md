# Registro de Sondas de Alucinación

- **Fecha de ejecución:** 2026-11-28 15:51 UTC
- **Sondas ejecutadas:** 5
- **Resultado:** 3 contenidas mecánicamente · 2 limitaciones declaradas · 0 fallas

## Resultados

| ID | Tipo | Detectable | Códigos detectados | Contenida | Estado | Escenario |
| --- | --- | --- | --- | --- | --- | --- |
| H-01 | cifra_inventada | Sí | cifra_inventada | Sí | PASA | Modelo inventa un porcentaje de asistencia inexistente (92 %) |
| H-02 | fuente_inventada | Sí | fuente_inventada | Sí | PASA | Modelo cita un documento PDF inexistente en los fragmentos recuperados |
| H-03 | sin_respaldo | Sí | sin_respaldo | Sí | PASA | Modelo responde con afirmación fabricada cuando no hay fragmentos recuperados |
| H-04 | afirmacion_agregada | No | ninguno | No | LIMITE | Modelo añade una afirmación cualitativa no respaldada sin cifras ni archivos falsos |
| H-05 | cifra_en_letras | No | ninguno | No | LIMITE | Modelo inventa un número escrito en palabras ('veinte') en lugar de dígitos |

## Limitaciones reconocidas del detector mecánico

### H-04 — `afirmacion_agregada`
- **Escenario:** Modelo añade una afirmación cualitativa no respaldada sin cifras ni archivos falsos
- **Decisión:** Limitación inherente a reglas léxicas: afirmaciones cualitativas sin cifras ni archivos falsos requieren revisión humana antes de comunicar decisiones formales al apoderado y muestreo semanal de trazas.

### H-05 — `cifra_en_letras`
- **Escenario:** Modelo inventa un número escrito en palabras ('veinte') en lugar de dígitos
- **Decisión:** Limitación conocida del verificador numérico basado en dígitos: cifras escritas en palabras no se capturan mecánicamente; se mitiga mediante revisión humana en avisos críticos y se planifica evaluador NLI en fase posterior.

