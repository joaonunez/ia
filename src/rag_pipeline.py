"""Flujo RAG completo con citas, medición de latencia y registro de costo (U2.5).

Conecta el índice Chroma persistido con el modelo generativo, arma el
prompt dinámico con citas numeradas `[1]`, `[2]`, y registra latencia
(recuperación, generación, total) y costo estimado por consulta.
"""
from __future__ import annotations

import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from client import DEFAULT_MODEL, INPUT_USD_PER_TOKEN, OUTPUT_USD_PER_TOKEN
from rag_evaluator import EVALUATION_CASES, compare_k_values, evaluate_retrieval
from rag_indexer import (
    DEFAULT_PERSIST_DIR,
    build_embeddings,
    index_corpus,
    load_vectorstore,
)

logger = logging.getLogger(__name__)

# Tarifa de referencia para gemini-embedding-001 (USD 0.15 por millón de tokens).
EMBEDDING_USD_PER_TOKEN = 0.15 / 1_000_000
METRICS_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "rag-metrics.json"
JSONL_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "rag-latency-cost.jsonl"

RAG_PROMPT_TEMPLATE = (
    "Eres el asistente del gestor académico. Responde la pregunta usando SOLO el "
    "contexto de abajo. Cita la fuente de cada afirmación con su número entre "
    "corchetes, como [1]. Si el contexto no alcanza para responder, dilo "
    "explícitamente en vez de inventar.\n\n"
    "Contexto:\n{contexto}\n\n"
    "Pregunta: {pregunta}\n"
    "Respuesta:"
)

EMPTY_QUESTION_REPLY = "Escribe una pregunta para consultar la documentación."
ERROR_REPLY = "No pudimos completar la consulta RAG en este momento. Intenta más tarde."


def normalize_content(content: Any) -> str:
    """Convierte contenido de LangChain (texto o lista de bloques) a string plano."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content)


def format_context(retrieved_chunks: list[Document]) -> tuple[str, dict[int, str]]:
    """Arma el bloque de contexto numerado y el diccionario numero -> fuente."""
    lines: list[str] = []
    citations: dict[int, str] = {}
    for index, doc in enumerate(retrieved_chunks, start=1):
        source = (doc.metadata or {}).get("fuente", "desconocida")
        lines.append(f"[{index}] {doc.page_content}")
        citations[index] = source
    return "\n\n".join(lines), citations


def build_rag_prompt(
    question: str,
    retrieved_chunks: list[Document],
) -> tuple[str, dict[int, str]]:
    """Construye el prompt dinámico con contexto numerado y diccionario de citas."""
    context, citations = format_context(retrieved_chunks)
    prompt = RAG_PROMPT_TEMPLATE.format(contexto=context, pregunta=question)
    return prompt, citations


def estimate_tokens(text: str) -> int:
    """Estimación conservadora (~4 caracteres por token) cuando no hay metadata."""
    cleaned = text.strip()
    if not cleaned:
        return 0
    return max(1, math.ceil(len(cleaned) / 4))


def extract_usage_tokens(response: Any, prompt_text: str, answer_text: str) -> tuple[int, int]:
    """Lee tokens reales de usage_metadata si existen; si no, estima por longitud."""
    usage = getattr(response, "usage_metadata", None)
    if isinstance(usage, dict):
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        if input_tokens > 0 or output_tokens > 0:
            return input_tokens, output_tokens
    return estimate_tokens(prompt_text), estimate_tokens(answer_text)


def calculate_rag_cost_usd(
    embedding_tokens: int,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calcula el costo total de una consulta RAG (embedding + generación)."""
    return (
        embedding_tokens * EMBEDDING_USD_PER_TOKEN
        + input_tokens * INPUT_USD_PER_TOKEN
        + output_tokens * OUTPUT_USD_PER_TOKEN
    )


def answer_with_rag(
    question: str,
    vectorstore,
    model,
    k: int = 3,
) -> dict[str, Any]:
    """Ejecuta el flujo RAG end-to-end y devuelve respuesta, citas, latencia y costo."""
    if not isinstance(question, str) or not question.strip():
        return {
            "question": question,
            "answer": EMPTY_QUESTION_REPLY,
            "citations": {},
            "retrieved_ids": [],
            "retrieval_latency_ms": 0.0,
            "generation_latency_ms": 0.0,
            "total_latency_ms": 0.0,
            "embedding_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "error": None,
        }

    total_start = time.perf_counter()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    try:
        retrieval_start = time.perf_counter()
        chunks = retriever.invoke(question)
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000.0

        prompt, citations = build_rag_prompt(question, chunks)

        generation_start = time.perf_counter()
        response = model.invoke(prompt)
        generation_ms = (time.perf_counter() - generation_start) * 1000.0

        raw_content = getattr(response, "content", response)
        answer = normalize_content(raw_content).strip()
        embedding_tokens = estimate_tokens(question)
        input_tokens, output_tokens = extract_usage_tokens(response, prompt, answer)
        cost_usd = calculate_rag_cost_usd(embedding_tokens, input_tokens, output_tokens)
        total_ms = (time.perf_counter() - total_start) * 1000.0

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "retrieved_ids": [chunk.id for chunk in chunks if chunk.id is not None],
            "retrieval_latency_ms": round(retrieval_ms, 2),
            "generation_latency_ms": round(generation_ms, 2),
            "total_latency_ms": round(total_ms, 2),
            "embedding_tokens": embedding_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(cost_usd, 8),
            "error": None,
        }
    except Exception as error:
        total_ms = (time.perf_counter() - total_start) * 1000.0
        logger.exception("Falló la ejecución del flujo RAG")
        return {
            "question": question,
            "answer": ERROR_REPLY,
            "citations": {},
            "retrieved_ids": [],
            "retrieval_latency_ms": 0.0,
            "generation_latency_ms": 0.0,
            "total_latency_ms": round(total_ms, 2),
            "embedding_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "error": type(error).__name__,
        }


def to_jsonl_record(run: dict[str, Any], k: int) -> dict[str, Any]:
    """Convierte una corrida de answer_with_rag al formato JSONL del Bloque 28."""
    input_tokens = int(run.get("input_tokens") or 0)
    output_tokens = int(run.get("output_tokens") or 0)
    has_tokens = input_tokens > 0 or output_tokens > 0
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": run["question"],
        "k": k,
        "tiempos_ms": {
            "embed_y_busqueda": run["retrieval_latency_ms"],
            "generacion": run["generation_latency_ms"],
        },
        "tiempo_total_ms": run["total_latency_ms"],
        "tokens": (
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
            if has_tokens
            else None
        ),
        "estimated_cost_usd": run["estimated_cost_usd"],
    }


def write_jsonl_records(
    records: list[dict[str, Any]],
    output_path: str | Path = JSONL_OUTPUT_PATH,
    append: bool = False,
) -> Path:
    """Guarda registros en formato JSON Lines (un objeto JSON por línea)."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with target.open(mode, encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return target


def run_benchmark(
    questions: list[str],
    vectorstore,
    model,
    k: int = 3,
    output_path: str | Path | None = METRICS_OUTPUT_PATH,
    evaluation_report: dict[str, Any] | None = None,
    k_comparison: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Corre un lote de preguntas RAG y guarda métricas agregadas en JSON."""
    runs = [answer_with_rag(q, vectorstore, model, k=k) for q in questions]
    successful = [r for r in runs if r["error"] is None]
    count = len(successful)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": getattr(model, "model", DEFAULT_MODEL),
        "k": k,
        "queries_total": len(runs),
        "queries_ok": count,
        "avg_retrieval_latency_ms": round(
            sum(r["retrieval_latency_ms"] for r in successful) / count, 2
        )
        if count
        else 0.0,
        "avg_generation_latency_ms": round(
            sum(r["generation_latency_ms"] for r in successful) / count, 2
        )
        if count
        else 0.0,
        "avg_total_latency_ms": round(
            sum(r["total_latency_ms"] for r in successful) / count, 2
        )
        if count
        else 0.0,
        "total_cost_usd": round(sum(r["estimated_cost_usd"] for r in successful), 8),
        "avg_cost_usd": round(
            sum(r["estimated_cost_usd"] for r in successful) / count, 8
        )
        if count
        else 0.0,
        "retrieval_evaluation": evaluation_report,
        "k_comparison": k_comparison,
        "runs": runs,
    }

    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return summary


def main() -> None:
    """Indexa si hace falta, evalúa recuperación y corre el benchmark real RAG."""
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    load_dotenv()
    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
    embeddings = build_embeddings(api_key=api_key)

    if not DEFAULT_PERSIST_DIR.exists():
        index_corpus(embeddings, persist_directory=DEFAULT_PERSIST_DIR, reset=True)

    vectorstore = load_vectorstore(embeddings, persist_directory=DEFAULT_PERSIST_DIR)
    if vectorstore._collection.count() == 0:
        index_corpus(embeddings, persist_directory=DEFAULT_PERSIST_DIR, reset=True)
        vectorstore = load_vectorstore(embeddings, persist_directory=DEFAULT_PERSIST_DIR)

    k_comparison = compare_k_values(vectorstore, EVALUATION_CASES, k_values=(1, 2, 3, 4))
    best_k = max(k_comparison, key=lambda item: item["avg_f1"])["k"]
    evaluation = evaluate_retrieval(
        vectorstore.as_retriever(search_kwargs={"k": 3}),
        cases=EVALUATION_CASES,
        k=3,
    )

    model = ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        api_key=api_key,
        timeout=20,
        max_retries=2,
    )

    sample_questions = [
        "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        "¿Qué hace el cliente HTTP ante un error 429 y ante un 401?",
        "¿Qué rol de base de datos usa el asistente en producción?",
        "¿Cómo se llama el director del establecimiento?",
    ]
    report = run_benchmark(
        questions=sample_questions,
        vectorstore=vectorstore,
        model=model,
        k=3,
        output_path=METRICS_OUTPUT_PATH,
        evaluation_report=evaluation,
        k_comparison=k_comparison,
    )

    # Comparación directa de la misma pregunta con k=3 vs k=6 (prueba del Bloque 28)
    k6_run = answer_with_rag(sample_questions[0], vectorstore, model, k=6)
    jsonl_records = [to_jsonl_record(run, k=3) for run in report["runs"]]
    jsonl_records.append(to_jsonl_record(k6_run, k=6))
    write_jsonl_records(jsonl_records, output_path=JSONL_OUTPUT_PATH, append=False)

    print("Comparación por k:", k_comparison)
    print(f"Mejor k por F1: {best_k}")
    print(
        f"Evaluación k=3 -> precisión={evaluation['avg_precision']}, "
        f"recall={evaluation['avg_recall']}, F1={evaluation['avg_f1']}"
    )
    print(
        f"Latencia promedio: total={report['avg_total_latency_ms']} ms "
        f"(recuperación={report['avg_retrieval_latency_ms']} ms, "
        f"generación={report['avg_generation_latency_ms']} ms)"
    )
    print(
        f"Prueba k=3 vs k=6 (misma pregunta) -> "
        f"input_tokens k=3: {report['runs'][0]['input_tokens']} | "
        f"k=6: {k6_run['input_tokens']}"
    )
    print(f"Costo total del lote: USD {report['total_cost_usd']:.8f}")
    print(f"Evidencia guardada en: {METRICS_OUTPUT_PATH} y {JSONL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
