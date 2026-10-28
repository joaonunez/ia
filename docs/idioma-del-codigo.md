# Idioma del código

Decisión del 2026-10-28. El fuente del proyecto va en inglés para que los nombres ocupen menos y haya un solo idioma en archivos, funciones y variables. Lo que lee una persona, y lo que lee el modelo, sigue en español.

| Qué | Idioma |
| --- | --- |
| Nombres de archivo, funciones, variables y clases | Inglés |
| Comentarios y docstrings | Español |
| Mensajes que ve quien usa el programa | Español |
| Instrucción de sistema y prompts | Español |
| Claves del JSON que devuelve el modelo (`tipo`, `confianza`, `grupo`, `respuesta`) | Español: son el contrato de la respuesta, no nombres del fuente |

`gemini-3.5-flash-lite` sigue siendo el modelo elegido. La llave va en el header `x-goog-api-key`, no en la URL.

## Archivos

| Antes | Ahora |
| --- | --- |
| `src/consumir_gemini.py` | `src/gemini_api.py` |
| `src/comparar_modelos.py` | `src/compare_models.py` |
| `prompts/banco.py` | `prompts/prompt_bank.py` |
| `prompts/test_consistencia.py` | `prompts/consistency_check.py` |
| — | `src/client.py` |
| — | `tests/test_client.py` |

`prompts/registro_resultados.json` conserva el nombre: es la evidencia de la corrida del banco, no código.

## Cliente

`src/client.py` es la entrada del asistente.

- `post_generation`: 401 y 403 lanzan `ValueError` y no se reintentan. 429, un código 500 o más, y un corte de red lanzan `TimeoutError`.
- `with_retry`: solo atrapa `TimeoutError`. Tres intentos. La espera es `min(base * 2 ** (intento - 1), 30)` más un jitter de hasta el 10 %.
- `record_cost`: suma solo después de una respuesta válida. Precio de flash-lite: USD 0.30 por millón de tokens de entrada y 2.50 por millón de salida.
- `ask_model`: si se agotan los reintentos, dice «El servicio no respondió tras varios intentos. Intenta más tarde.»

Las pruebas no llaman al proveedor:

```bash
python -m pytest tests/test_client.py -v
```
