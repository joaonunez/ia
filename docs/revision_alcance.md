# Revisión del alcance

Revisor: Joao Nunez (autorrevisión)
Fecha: 2026-11-27

Acierto: el alcance mantiene el foco de solo lectura sobre datos y reglamentos simulados, reutilizando al 100 % las piezas ya probadas del Módulo 2 (Chroma, citas, filtro anti-inyección, logs JSON con trace_id y LangGraph).

- Hallazgo 1 (criterio 4): CA-03 debía especificar claramente qué ocurre cuando una pregunta no existe en el corpus de reglamentos para que sea decidible en prueba ciega.
  Decisión: aceptado. Cambio: CA-03 ahora usa la pregunta concreta "¿Cómo se llama el director del establecimiento?" y exige indicar explícitamente que no cuenta con esa información sin inventar nombres.

- Hallazgo 2 (criterio 2): RF-05 (aprobación humana de despliegue de instrucciones con LangGraph) podría subirse a imprescindible porque el código ya existe en el repositorio.
  Decisión: rechazado. Motivo: el problema de negocio se resuelve sin exponer un endpoint de despliegue en el MVP, por lo que mantener RF-05 como deseable protege el presupuesto de 10 h de construcción.

- Hallazgo 3 (criterio 5): H5 concentra pruebas QA, documentación técnica y ensayo de defensa en un solo bloque de 6 h.
  Decisión: aplazado. Motivo: queda acotado y comprobable con CA-06 y CA-07; se revisará al cierre de H4 si conviene dividirlo en sub-entregas diarias.
