"""Evaluación cuantitativa de la recuperación RAG (Bloque 27).

Implementa precisión@k, exhaustividad (recall@k), F1 y comparación de
valores de k sobre un conjunto de evaluación etiquetado manualmente.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# Conjunto de evaluación etiquetado manualmente leyendo el corpus (antes de
# consultar el retriever). Incluye 7 preguntas respondibles y 1 pregunta
# fuera del corpus (ids relevantes vacío) para validar el caso borde.
EVALUATION_CASES: list[dict[str, Any]] = [
    {
        "question": "¿Cuál es el porcentaje mínimo de asistencia para pasar de curso?",
        "relevant_ids": {"doc0"},
    },
    {
        "question": "¿Desde qué nota se aprueba una asignatura en la escala escolar?",
        "relevant_ids": {"doc1"},
    },
    {
        "question": "¿Se puede enviar un aviso formal al apoderado sin confirmación humana?",
        "relevant_ids": {"doc2"},
    },
    {
        "question": "¿Qué hace el cliente HTTP cuando recibe un error 429 o un 401?",
        "relevant_ids": {"doc3"},
    },
    {
        "question": "¿Qué modelo de Gemini se eligió y cuánto cuesta por millón de tokens?",
        "relevant_ids": {"doc4"},
    },
    {
        "question": "¿Puede el asistente modificar registros oficiales en la base de datos?",
        "relevant_ids": {"doc5"},
    },
    {
        "question": "¿Cuántas vueltas máximas puede dar el agente y dónde guarda sus trazas?",
        "relevant_ids": {"doc6"},
    },
    {
        "question": "¿Cómo se llama el director del establecimiento y cuál es su horario?",
        "relevant_ids": set(),
    },
]


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Fracción de los IDs recuperados que son relevantes.

    Devuelve 0.0 si el retriever no devolvió ningún ID.
    """
    if not retrieved_ids:
        return 0.0
    hits = [chunk_id for chunk_id in retrieved_ids if chunk_id in relevant_ids]
    return len(hits) / len(retrieved_ids)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str]) -> float | None:
    """Fracción de los IDs relevantes que efectivamente se recuperaron.

    Devuelve None si el caso no tiene IDs relevantes (pregunta sin respuesta
    en el corpus), evitando ZeroDivisionError.
    """
    if not relevant_ids:
        return None
    hits = [chunk_id for chunk_id in retrieved_ids if chunk_id in relevant_ids]
    return len(hits) / len(relevant_ids)


def f1_score(precision: float, recall: float | None) -> float:
    """Media armónica de precisión y recall. Devuelve 0.0 si recall es None."""
    if recall is None or (precision + recall) == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def average_metric(values: Iterable[float | None]) -> float:
    """Promedio que ignora valores None y devuelve 0.0 si no hay datos válidos."""
    valid = [value for value in values if value is not None]
    return sum(valid) / len(valid) if valid else 0.0


def evaluate_retrieval(
    retriever,
    cases: list[dict[str, Any]] = EVALUATION_CASES,
    k: int = 3,
) -> dict[str, Any]:
    """Ejecuta todos los casos contra el retriever y calcula métricas promedio."""
    per_case: list[dict[str, Any]] = []
    for case in cases:
        chunks = retriever.invoke(case["question"])
        retrieved_ids = [chunk.id for chunk in chunks if chunk.id is not None][:k]
        relevant_ids: set[str] = case["relevant_ids"]
        precision = precision_at_k(retrieved_ids, relevant_ids)
        recall = recall_at_k(retrieved_ids, relevant_ids)
        f1 = f1_score(precision, recall)
        per_case.append(
            {
                "question": case["question"],
                "relevant_ids": sorted(relevant_ids),
                "retrieved_ids": retrieved_ids,
                "precision": round(precision, 4),
                "recall": round(recall, 4) if recall is not None else None,
                "f1": round(f1, 4),
            }
        )

    avg_precision = round(average_metric(item["precision"] for item in per_case), 4)
    avg_recall = round(average_metric(item["recall"] for item in per_case), 4)
    avg_f1 = round(f1_score(avg_precision, avg_recall), 4)

    return {
        "k": k,
        "cases_total": len(per_case),
        "cases_with_answer": sum(1 for item in per_case if item["recall"] is not None),
        "avg_precision": avg_precision,
        "avg_recall": avg_recall,
        "avg_f1": avg_f1,
        "cases": per_case,
    }


def compare_k_values(
    vectorstore,
    cases: list[dict[str, Any]] = EVALUATION_CASES,
    k_values: Iterable[int] = (1, 2, 3, 4),
) -> list[dict[str, Any]]:
    """Compara el desempeño de recuperación para distintos valores de k."""
    summary: list[dict[str, Any]] = []
    for k in k_values:
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        report = evaluate_retrieval(retriever, cases=cases, k=k)
        summary.append(
            {
                "k": k,
                "avg_precision": report["avg_precision"],
                "avg_recall": report["avg_recall"],
                "avg_f1": report["avg_f1"],
            }
        )
    return summary
