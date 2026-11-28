# Bitácora de ajustes

| Iteración | Qué falló | Palanca | Cambio | Antes | Después | Decisión |
|---|---|---|---|---|---|---|
| 1 | E-03 y E-04: consultas en mayúsculas o con tildes no recuperaban el fragmento esperado | configuración (normalización) | normalizar NFD sin tildes y minúsculas en `_palabras_clave()` de `servicio/cadena.py` | 10 de 12 | 11 de 12 | conservar |
| 2 | E-07: pregunta compuesta devolvía solo el primer fragmento del contexto | prompt (instrucción) | cambiar `INSTRUCCION` a `"Responde usando todo el contexto. Si no alcanza, dilo."` y unir líneas en `ModeloSimulado` | 11 de 12 | 12 de 12 | conservar |
| 3 | E-08 y E-09: bajar el umbral de coincidencias a 1 produjo falsos positivos en preguntas fuera de corpus | configuración (umbral) | bajar umbral de `coincidencias >= 2` a `coincidencias >= 1` | 12 de 12 | 10 de 12 | descartar |
| 4 | E-13 y E-14 (control): validación de no-regresión al sumar escenarios de gobernanza y costos | escenarios de control | agregar `E-13` y `E-14` y verificar repetibilidad con `--dos-veces` | 12 de 12 | 14 de 14 | conservar |
