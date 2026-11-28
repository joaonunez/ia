# Plan de pruebas parciales

| Componente | Entrada | Salida | Doble | Archivo | Defecto introducido | Detectado |
|---|---|---|---|---|---|---|
| recuperar | pregunta (texto) | lista de {fuente, texto} | ninguno: lógica pura sobre `CORPUS` | tests/parciales/test_recuperar.py | clave `"texto"` renombrada a `"contenido"` | sí |
| construir_prompt | pregunta y fragmentos | texto del prompt | fragmentos escritos a mano | tests/parciales/test_prompt.py | el prompt omite `{contexto}` | sí |
| generar (modelo) | texto del prompt | texto de la respuesta con cita | `ModeloSimulado` | tests/parciales/test_modelo.py | devuelve un diccionario en lugar de texto | sí |
| empaquetar | texto y fragmentos | pareja `(texto, fuentes sin repetir)` | fragmentos escritos a mano | tests/parciales/test_empaquetar.py | repite fuentes duplicadas (`if True:`) | sí |
| configuración | variables de entorno | entorno, clave y estado del modelo | `monkeypatch` con valores falsos | tests/parciales/test_config.py | pedir la clave sin definirla ya no falla | sí |
| consulta de estudiantes | nombre del estudiante | diccionario de resumen o `None` | ninguno: datos simulados | tests/parciales/test_estudiantes.py | estudiante inexistente devuelve `"desconocido"` | sí |
