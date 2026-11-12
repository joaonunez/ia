"""Mide salidas reales del cliente contra una referencia escrita a mano.

Veinte preguntas cortas. Guarda el archivo después de cada una, por si
el cupo se corta a mitad. La instrucción pide una frase en español y no
usa el rol del gestor académico: esta unidad mide el texto, no ese rol.
"""
import json
from pathlib import Path

import client
from text_metrics import calculate_metrics, overlap_ratio, summarize_metrics
from text_pipeline import process_text

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "metric-results.json"
INSTRUCTION = "Responde en español, en una sola frase."

CASES = [
    ("¿Qué es Python?", "Python es un lenguaje de programación interpretado."),
    ("¿Cuándo se creó Python?", "Python fue creado en 1991."),
    ("¿Qué es una lista en Python?", "Una lista es una colección ordenada y modificable."),
    ("¿Quién creó Python?", "Python fue creado por Guido van Rossum."),
    ("¿Python es un lenguaje compilado?", "Python no es un lenguaje compilado."),
    ("¿Qué es una variable?", "Una variable es un nombre que guarda un valor."),
    ("¿Qué es un bucle for?", "Un bucle for repite un bloque para cada elemento de una secuencia."),
    ("¿Qué es una función?", "Una función es un bloque de código reutilizable."),
    ("¿Qué significa el código HTTP 429?", "El código 429 indica que se superó el límite de uso."),
    ("¿Qué significa el código HTTP 401?", "El código 401 indica que la credencial es inválida."),
    ("¿Cuánto es 2 más 2?", "2 más 2 es 4."),
    ("¿En qué año declaró Chile su independencia?", "Chile declaró su independencia en 1810."),
    ("¿Qué es Git?", "Git es un sistema de control de versiones."),
    ("¿Qué es un token en un modelo de lenguaje?", "Un token es una pieza de texto que el modelo procesa."),
    ("¿Qué es JSON?", "JSON es un formato de texto para objetos y listas."),
    ("¿De qué color es el cielo despejado?", "El cielo despejado es azul."),
    ("¿Un auto veloz es lo mismo que un vehículo rápido?", "Un auto veloz es un vehículo rápido."),
    ("¿Cuántos días tiene una semana?", "Una semana tiene 7 días."),
    ("¿Qué es pytest?", "pytest es una herramienta para correr pruebas en Python."),
    ("¿Qué es una API?", "Una API es una interfaz para que un programa hable con otro."),
]


def raw_and_processed(reference: str, response: str) -> tuple[float, float]:
    raw = overlap_ratio(reference.split(), response.split())
    processed = overlap_ratio(process_text(reference), process_text(response))
    return raw, processed


def main() -> None:
    results = []
    for index, (question, reference) in enumerate(CASES, start=1):
        print(f"\n=== {index}. {question} ===")
        try:
            answer = client.ask_model(question, system_instruction=INSTRUCTION)
        except ValueError as error:
            print("Credencial, no es el 429:", error)
            break
        except RuntimeError as error:
            print(f"[{index}] intentos agotados:", error)
            results.append({
                "question": question,
                "reference": reference,
                "answer": "",
                "error": str(error),
            })
            OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            continue

        raw, processed = raw_and_processed(reference, answer)
        metrics = calculate_metrics(reference, answer)
        row = {
            "question": question,
            "reference": reference,
            "answer": answer,
            "raw_overlap": round(raw, 4),
            "processed_overlap": round(processed, 4),
            **{key: round(value, 4) for key, value in metrics.items()},
        }
        results.append(row)
        print(answer)
        print(
            f"crudo {raw:.1%} | procesado {processed:.1%} | "
            f"precisión {metrics['precision']:.2f} | "
            f"cobertura {metrics['recall']:.2f} | f1 {metrics['f1']:.2f}"
        )
        OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    scored = [row for row in results if "f1" in row]
    summary = summarize_metrics(scored)
    print(
        f"\nPromedio sobre {len(scored)} respuestas: "
        f"precisión {summary['precision_avg']:.2f} | "
        f"cobertura {summary['recall_avg']:.2f} | "
        f"f1 {summary['f1_avg']:.2f}"
    )
    print(f"Costo de la sesión: USD {client.session_cost_usd:.5f}")
    print(f"Registro en {OUTPUT}")


if __name__ == "__main__":
    main()
