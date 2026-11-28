# Registro de Decisiones de Arquitectura

Decisiones técnicas vigentes del **Asistente Académico IA (Solo Lectura)**. Cada decisión documenta su contexto, alternativas descartadas y costo asumido (`DEC-1..DEC-7`).

## D-01 — Arquitectura RAG de solo lectura sobre reglamentos y datos simulados

- **Estado:** vigente
- **Contexto:** El equipo académico necesita respuestas consistentes y verificables sobre reglamentos escolares y resúmenes de notas/asistencia sin arriesgar modificaciones accidentales ni exponer datos reales de estudiantes.
- **Decisión:** Construir un servicio RAG desacoplado de solo lectura con corpus reglamentario indexado, citas explícitas y dataset simulado de estudiantes.
- **Alternativas descartadas:** Fine-tuning del modelo sobre reglamentos (caro de actualizar ante cada cambio normativo) y conexión directa de escritura a la base de datos productiva escolar.
- **Costo:** Cada consulta depende de mantener el corpus sincronizado y actualizado, y el asistente no puede ejecutar cambios ni enviar avisos automáticamente sin intervención humana.

## D-02 — Respaldo explícito con HTTP 503 ante ausencia del modelo real

- **Estado:** vigente
- **Contexto:** Si el servicio se configura con `MODELO=real` sin `GEMINI_API_KEY` válida, sustituir silenciosamente la respuesta por un modelo simulado engañaría al operador y al usuario.
- **Decisión:** Lanzar `ModeloNoDisponible` y responder `HTTP 503` (`codigo: modelo_no_disponible`) salvo que el operador active explícitamente `PERMITIR_RESPALDO=1`.
- **Alternativas descartadas:** Degradación silenciosa automática al modelo simulado o devolver `HTTP 200` con un texto genérico de error oculto en el campo `respuesta`.
- **Costo:** Exige configurar explícitamente `PERMITIR_RESPALDO=1` en escenarios de contingencia y añade pruebas específicas para ambos comportamientos (`503` vs `respaldo`).

## D-03 — Cadena de 4 componentes desacoplados con guardias de contrato Pydantic

- **Estado:** vigente
- **Contexto:** Mezclar recuperación, armado de prompt, invocación al modelo y empaquetado en una sola función impedía aislar defectos de interfaz y probar sin red.
- **Decisión:** Separar `recuperar`, `construir_prompt`, `modelo.generar` y `empaquetar` en `servicio/cadena.py`, validando cada frontera con `exigir()` y `Fragmento` (`extra="forbid"`).
- **Alternativas descartadas:** Función monolítica acoplada al SDK de Gemini sin validación de contratos internos y pruebas que dependieran de llamadas en vivo a la API externa.
- **Costo:** Añade capas y tipos explícitos entre componentes, obligando a actualizar el contrato cuando se agregan metadatos nuevos a los fragmentos recuperados.

## D-04 — Defensa en profundidad contra inyección, alucinaciones y fugas

- **Estado:** vigente
- **Contexto:** Un único filtro en la entrada no basta si un documento del corpus está envenenado o si el modelo intenta filtrar instrucciones internas, secretos o cifras inventadas.
- **Decisión:** Combinar filtro normalizado `NFKD` en entrada, descarte de fragmentos sospechosos, limpieza de salida (`limpiar_salida`), compuerta mecánica `fundamentacion.py` y logs sin texto crudo ni PII.
- **Alternativas descartadas:** Confiar únicamente en instrucciones del prompt de sistema o bloquear cualquier aparición de palabras como "instrucciones" o "contraseña" sin calificadores.
- **Costo:** Requiere mantener pruebas de control para evitar falsos positivos (`B-01`, `B-02`) y asumir limitaciones léxicas documentadas (`A-07`, `H-04`, `H-05`) cubiertas con supervisión humana.

## D-05 — Exposición HTTP con FastAPI, errores uniformes y composición Docker en dos servicios

- **Estado:** vigente
- **Contexto:** El asistente debe poder ejecutarse de forma reproducible en cualquier equipo con Docker, separando la API del cliente web y sin incrustar secretos en la imagen.
- **Decisión:** Exponer `/health`, `/ask` y `/estudiantes/{nombre}` en FastAPI con manejador único de errores (`codigo`, `mensaje`, `campos`) y componer `api` (8000) + `interfaz` (8080) en `compose.yaml` con `.env` externo y usuario no root.
- **Alternativas descartadas:** Script CLI sin contrato HTTP o contenedor único monolítico corriendo como `root` con variables de entorno empotradas en el `Dockerfile`.
- **Costo:** Implica mantener dos `Dockerfile`, verificación de salud (`depends_on: service_healthy`) y regenerar `docs/api.md` cuando cambia cualquier esquema o endpoint.

## D-06 — Selección de `gemini-3.5-flash-lite` para generación en modo real

- **Estado:** vigente
- **Contexto:** El asistente atiende consultas breves y repetitivas sobre reglamentos donde priman latencia baja y costo controlado por millón de tokens.
- **Decisión:** Usar `gemini-3.5-flash-lite` como modelo objetivo en modo real (USD 0.30/M entrada y USD 2.50/M salida), manteniendo `ModeloSimulado` por defecto para pruebas y demostraciones sin red.
- **Alternativas descartadas:** Modelos de gama mayor con costo 5x–10x superior por token o despliegue de un LLM local pesado que excede los recursos de un equipo estándar.
- **Costo:** Menor capacidad de razonamiento complejo en tareas abiertas fuera del corpus reglamentario, lo cual es aceptable dado el alcance acotado de solo lectura.
