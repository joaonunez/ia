# Límites de la métrica de evaluación

## Qué mide

Coincidencia de palabras entre una respuesta generada y una referencia escrita a mano, contando repeticiones. Devuelve precisión, cobertura (`recall`) y F1.

## Modos de falla conocidos

- Una paráfrasis correcta puntúa bajo. «¿Qué es pytest?» dio F1 0,26: la respuesta describe un marco para escribir y ejecutar pruebas, y la referencia decía una herramienta para correr pruebas. El sentido está bien.
- Decir lo mismo sin la negación también puntúa bajo. Ante «¿Python es un lenguaje compilado?», la referencia era «no es un lenguaje compilado» y la respuesta dijo que es interpretado. F1 0,28, sin contradicción.
- Un número en letras no es el mismo token que el dígito. «siete» contra «7» en los días de la semana no se cuenta. El F1 igual quedó en 0,80 porque el resto de la frase coincide. «Dos más dos es cuatro» contra «2 más 2 es 4» bajó a 0,40.
- Un dato distinto puede puntuar alto. La referencia de la independencia de Chile dice 1810 y la respuesta dijo 1818. F1 0,71. Cambia una cifra y el número no lo marca como grave.
- La misma palabra en otro sentido sí baja el número, y ahí el aviso sirve. «¿Qué es una función?» respondió la definición matemática, no un bloque de código. F1 0,31.
- El texto crudo también miente por el formato. En «¿Qué es Python?» la coincidencia por conjuntos pasó de 85,7 % en crudo a 100 % después de limpiar. El contenido no cambió.

## Muestra revisada

20 respuestas generadas el 2026-10-28 con `src/evaluate_outputs.py`, modelo `gemini-3.5-flash-lite`, una frase en español. La pregunta de la API agotó los reintentos en esa corrida y se completó en un llamado aparte. Costo de las veinte cerca de USD 0,0013.

Se leyeron 10 a mano: las 5 de menor F1 (pytest, compilado, API, función, token) y las 5 de mayor F1 (cielo, semana, independencia de Chile, quién creó Python, cuándo se creó Python). El registro está en `docs/manual-review.json`.

## Recomendación de uso

Usar el F1 para comparar en volumen dos versiones del cliente. Leer siempre a mano una respuesta con fecha, cifra o negación, y también una de F1 bajo si la frase es larga: en esta muestra el F1 bajo fue, casi siempre, una paráfrasis correcta.
