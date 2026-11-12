"""Precisión, cobertura y F1 sobre tokens ya procesados.

La precisión pregunta cuánto de la respuesta está en la referencia.
La cobertura pregunta cuánto de la referencia dijo la respuesta.
F1 junta las dos. Ninguna de las tres entiende sinónimos, orden ni negaciones.
"""
from collections import Counter

from text_pipeline import process_text


def overlap_ratio(reference_tokens: list[str], response_tokens: list[str]) -> float:
    """Proporción de palabras distintas de la referencia que también están en la respuesta.

    Usa conjuntos: una palabra repetida cuenta igual que una sola.
    """
    if not reference_tokens:
        return 0.0
    common = set(reference_tokens) & set(response_tokens)
    return len(common) / len(set(reference_tokens))


def count_matches(reference_tokens: list[str], response_tokens: list[str]) -> int:
    """Coincidencias contando repeticiones. El tope de cada palabra es el mínimo de los dos lados."""
    reference_counts = Counter(reference_tokens)
    response_counts = Counter(response_tokens)
    return sum((reference_counts & response_counts).values())


def precision_recall_f1(
    reference_tokens: list[str],
    response_tokens: list[str],
) -> dict[str, float]:
    """Precisión, cobertura (recall) y F1. Lista vacía en cualquier lado devuelve ceros."""
    if not reference_tokens or not response_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    matches = count_matches(reference_tokens, response_tokens)
    precision = matches / len(response_tokens)
    recall = matches / len(reference_tokens)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def calculate_metrics(reference_text: str, response_text: str) -> dict[str, float]:
    """Procesa los dos textos y calcula la métrica. Hay que pasar los dos por el pipeline."""
    return precision_recall_f1(process_text(reference_text), process_text(response_text))


def summarize_metrics(results: list[dict]) -> dict[str, float]:
    """Promedio de precisión, cobertura y F1. Un promedio esconde un caso malo entre varios buenos."""
    if not results:
        return {"precision_avg": 0.0, "recall_avg": 0.0, "f1_avg": 0.0}
    count = len(results)
    return {
        "precision_avg": sum(item["precision"] for item in results) / count,
        "recall_avg": sum(item["recall"] for item in results) / count,
        "f1_avg": sum(item["f1"] for item in results) / count,
    }
