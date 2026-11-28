# Componentes de respaldo

| Pieza incompleta | Respaldo | Mismo contrato | Cómo se activa | Cómo se ve | Condición de retiro |
|---|---|---|---|---|---|
| Modelo real (Gemini en servicio HTTP) | `ModeloRespaldo` en `servicio/respaldo.py` | `generar(prompt)` devuelve `str`; sin contexto responde `SIN_INFORMACION` | `MODELO=real` y `PERMITIR_RESPALDO=1` | `/health` muestra `modelo_activo: respaldo` | `CLIENTE_INTEGRADO = True` y las pruebas de contrato de `ModeloReal` pasan sin omitirse |

Reglas de este proyecto:

- El respaldo nunca se activa solo: sin `PERMITIR_RESPALDO=1`, un modelo real no disponible produce un error HTTP `503` a la vista.
- Toda ejecución que use el respaldo lo declara en `docs/registro_ejecucion.md`.
- El respaldo se retira cuando se cumple la condición de la tabla.
