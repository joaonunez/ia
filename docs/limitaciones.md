# Registro de Limitaciones Conocidas

Todas las limitaciones técnicas observadas en código y pruebas están trazadas con su origen, riesgo asociado en `riesgos.py` y decisión operativa (`DEC-4..DEC-7`).

| ID | Qué no hace | Origen | Riesgo | Efecto | Qué se decidió |
| --- | --- | --- | --- | --- | --- |
| LIM-01 | No resuelve sinónimos ni paráfrasis puras sin palabras clave literales en modo simulado | MP-08 | R-06 | Devuelve `SIN_INFORMACION` en vez de inventar cuando no hay coincidencia léxica en el corpus local | Aceptada en modo simulado sin red; en producción con `USE_LIVE_RAG=true` se mitiga usando embeddings semánticos en Chroma |
| LIM-02 | No detecta inyecciones ofuscadas separando letras con guiones en el filtro de entrada | A-07 | R-01 | La petición ofuscada supera el regex inicial y llega a las capas internas del flujo | Mitigada en profundidad con limpieza de salida, compuerta de respaldo y modo solo lectura; se amplían reglas según revisión semanal |
| LIM-03 | No detecta mecánicamente afirmaciones cualitativas agregadas sin cifras ni nombres de archivo falsos | H-04 | R-03 | Una frase adicional no respaldada pero sin dígitos ni archivos falsos puede llegar al usuario | Cubierta por supervisión humana obligatoria del gestor académico contra la fuente citada y muestreo semanal de 10 trazas |
| LIM-04 | No detecta mecánicamente cifras inventadas cuando el modelo las escribe en palabras en lugar de dígitos | H-05 | R-03 | Un número escrito en letras ('veinte') no dispara la regla numérica `cifra_inventada` | Cubierta por supervisión humana obligatoria en avisos formales a apoderados y planificada mejora futura con evaluador NLI |
