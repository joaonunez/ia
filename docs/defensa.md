# Guion de Defensa Técnica — Gate 3 / Capstone

Presupuesto total: **8 minutos** (`130` palabras por minuto en secciones habladas + `2` minutos de demo en vivo).

## 1. Problema (1 min)

El equipo de coordinación académica de un establecimiento escolar responde cerca de 45 consultas semanales sobre reglamentos de asistencia, calificaciones y situación de estudiantes revisando documentos dispersos a mano. Cada consulta toma unos 7 minutos y las respuestas varían según quién interprete la norma. Construimos un Asistente Académico IA de solo lectura que entrega respuestas consistentes en segundos, siempre respaldadas por su fuente documental y trabajando exclusivamente sobre datos simulados. El alcance excluye escrituras en bases productivas y se mide con criterios verificables de precisión, privacidad en logs y arranque reproducible en menos de 10 minutos.

## 2. Arquitectura (2 min)

La solución se compone en Docker con dos servicios desacoplados: una API en FastAPI ejecutada con uvicorn en el puerto 8000 y una interfaz web ligera en el puerto 8080 (`D-05`). Cada consulta recorre una cadena de cuatro pasos validados con contratos Pydantic (`D-03`): recuperación del corpus reglamentario, armado del prompt, generación del modelo y empaquetado de fuentes.

Para evitar respuestas inventadas o manipulaciones aplicamos defensa en profundidad (`D-04`): filtro de entrada normalizado, descarte de fragmentos envenenados, limpieza de salida que redacta instrucciones internas o secretos, y compuerta mecánica de fundamentación. La arquitectura RAG de solo lectura (`D-01`) usa Chroma y Gemini en modo real (`D-06`), mientras que por defecto corre con modelo simulado para pruebas deterministas sin red. Si se solicita el modelo real sin clave, responde HTTP 503 explícito en lugar de degradar en silencio (`D-02`).

## 3. Riesgos y límites (2 min)

Evaluamos 9 riesgos en una matriz auditable cuya evidencia se ejecuta automáticamente. El riesgo residual más alto es `R-03` (residual 9, ALTO): alucinaciones cualitativas agregadas (`H-04`, `LIM-03`) o cifras escritas en palabras (`H-05`, `LIM-04`) que escapan al detector mecánico de dígitos y fuentes. Por eso `R-03` exige supervisión humana obligatoria: el gestor académico valida la fuente citada antes de emitir avisos formales a apoderados y audita diez trazas semanales.

En segundo lugar están `R-01` (inyección ofuscada con guiones `A-07`, `LIM-02`, mitigada por limpieza de salida y solo lectura) y `R-06` (paráfrasis puras sin palabras clave en modo simulado, `LIM-01`, mitigada en producción con embeddings). Los demás riesgos —fuga de secretos, inyección indirecta, exposición de PII en logs, falsos positivos y caídas del proveedor— quedan en residual bajo con evidencia automatizada en verde.

## 4. Demo (2 min)

Pasos sincronizados con `ensayo_demo.py` (Plan B actualizado en `docs/demo_respaldo.md`):

- PASO-1 Servicio vivo
- PASO-2 Una respuesta con su fuente
- PASO-3 Consulta de estudiante simulado
- PASO-4 Un error uniforme
- PASO-5 Un ataque rechazado
- PASO-6 Una limitación a la vista
- PASO-7 Una falla honesta sin modelo

## 5. Cierre (1 min)

Todo lo expuesto tiene respaldo ejecutable en el repositorio: 255 pruebas automáticas en verde, 7 ejemplos reales verificados en la documentación de la API, prueba de transferencia completada en 18 minutos con cero preguntas al autor (`T-01` a `T-05`) y cero secretos expuestos. El siguiente paso hacia producción es activar la colección Chroma con `GEMINI_API_KEY` en entorno controlado y mantener el muestreo semanal de trazas para `R-03`.

## Diapositivas

| N | Sección | Qué muestra |
| --- | --- | --- |
| 1 | Problema | Dolencia actual (45 consultas/sem, 7 min), alcance solo lectura y métricas |
| 2 | Arquitectura | Diagrama `docs/diagrama_arquitectura.png`, cadena de 4 pasos y decisiones `D-01..D-06` |
| 3 | Seguridad y QA | Defensa en profundidad, matriz de pruebas y 17 mitigaciones verificadas |
| 4 | Riesgos y límites | Ranking por residual (`R-03` ALTO con supervisión) y tabla `LIM-01..LIM-04` |
| 5 | Demo | Ejecución en vivo de `PASO-1` a `PASO-7` (Plan B: `docs/demo_respaldo.md`) |
| 6 | Cierre | Informe del Gate 3 (`docs/gate3.md`), transferencia y próximos pasos |
