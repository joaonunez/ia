"""Revisión manual de una muestra de las respuestas medidas (Bloque 17).

Diez casos de docs/metric-results.json: los 5 de menor F1 y los 5 de
mayor F1. Cada uno lleva la rúbrica de tres preguntas (corrección factual,
completitud, contradicción) y una nota que explica la calificación.

Escribe docs/manual-review.json con json.dump, no a mano.
"""
import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "manual-review.json"

MANUAL_REVIEW = [
    # Los 5 de menor F1.
    {
        "question": "¿Qué es pytest?",
        "f1": 0.2632,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Dice que es un marco para escribir y ejecutar pruebas. La referencia "
            "decía herramienta para correr pruebas. El sentido está bien y el F1 "
            "es el más bajo de las 20."
        ),
    },
    {
        "question": "¿Python es un lenguaje compilado?",
        "f1": 0.2759,
        "factual": "si",
        "completeness": "parcialmente",
        "contradiction": "no",
        "note": (
            "La referencia dice que no es compilado. La respuesta dice que es "
            "interpretado y no usa la palabra no. El dato es correcto por otra "
            "vía. El F1 castiga esa paráfrasis."
        ),
    },
    {
        "question": "¿Qué es una API?",
        "f1": 0.2857,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Reglas para que aplicaciones se comuniquen, en vez de interfaz para "
            "que un programa hable con otro. Misma idea, otras palabras."
        ),
    },
    {
        "question": "¿Qué es una función?",
        "f1": 0.3125,
        "factual": "no",
        "completeness": "no",
        "contradiction": "no",
        "note": (
            "La referencia habla de un bloque de código. La respuesta define la "
            "función matemática. Aquí el F1 bajo sí avisa de otro sentido."
        ),
    },
    {
        "question": "¿Qué es un token en un modelo de lenguaje?",
        "f1": 0.3265,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Unidad mínima de texto, más larga que la referencia. Correcta, y el "
            "número queda bajo."
        ),
    },
    # Los 5 de mayor F1.
    {
        "question": "¿De qué color es el cielo despejado?",
        "f1": 0.8333,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Casi el mismo texto, con de color de más. El F1 alto coincide con "
            "una respuesta correcta."
        ),
    },
    {
        "question": "¿Cuántos días tiene una semana?",
        "f1": 0.8,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Siete y 7 no son el mismo token. El resto de la frase coincide y el "
            "F1 igual queda en 0,80."
        ),
    },
    {
        "question": "¿En qué año declaró Chile su independencia?",
        "f1": 0.7143,
        "factual": "no",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "La referencia dice 1810 y la respuesta dice 1818. El F1 queda alto "
            "porque cambia una sola cifra."
        ),
    },
    {
        "question": "¿Quién creó Python?",
        "f1": 0.7,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Nombra a Guido van Rossum y agrega finales de los años ochenta. El "
            "autor está bien."
        ),
    },
    {
        "question": "¿Cuándo se creó Python?",
        "f1": 0.5882,
        "factual": "si",
        "completeness": "si",
        "contradiction": "no",
        "note": (
            "Febrero de 1991. La cobertura es 1 y la precisión baja a 0,42 porque "
            "la frase es más larga que la referencia."
        ),
    },
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(MANUAL_REVIEW, file, indent=2, ensure_ascii=False)
        file.write("\n")
    print(f"{len(MANUAL_REVIEW)} casos revisados en {OUTPUT}")


if __name__ == "__main__":
    main()
