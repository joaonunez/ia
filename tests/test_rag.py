"""Pruebas unitarias exhaustivas del flujo RAG (U2.5), sin llamadas a la API.

Usa embeddings deterministas por bolsa de palabras sobre Chroma en un
directorio temporal y un modelo falso para probar chunking, persistencia,
citas, evaluación (precisión, recall, F1), latencia, costo y errores.
"""
from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from rag_evaluator import (
    EVALUATION_CASES,
    average_metric,
    compare_k_values,
    evaluate_retrieval,
    f1_score,
    precision_at_k,
    recall_at_k,
)
from rag_indexer import (
    CORPUS,
    index_corpus,
    inspect_chunks,
    load_vectorstore,
    split_corpus,
)
from rag_pipeline import (
    EMPTY_QUESTION_REPLY,
    ERROR_REPLY,
    answer_with_rag,
    build_rag_prompt,
    calculate_rag_cost_usd,
    format_context,
    run_benchmark,
    to_jsonl_record,
    write_jsonl_records,
)


class DeterministicEmbeddings(Embeddings):
    """Embeddings deterministas basados en vocabulario para pruebas locales."""

    VOCAB = [
        "asistencia",
        "promocion",
        "85",
        "nota",
        "calificaciones",
        "4.0",
        "apoderado",
        "aviso",
        "aprobacion",
        "429",
        "401",
        "reintenta",
        "cliente",
        "gemini",
        "costo",
        "tokens",
        "lectura",
        "base",
        "datos",
        "iteraciones",
        "trazas",
        "pruebas",
        "mocks",
    ]

    def _encode(self, text: str) -> list[float]:
        normalized = (
            text.lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        vec = [1.0 if term in normalized else 0.0 for term in self.VOCAB]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._encode(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._encode(text)


class FakeModel:
    """Modelo generativo falso con soporte para usage_metadata y content blocks."""

    def __init__(self, reply="Respuesta con cita [1].", usage=None, error=None):
        self.model = "fake-gemini-flash-lite"
        self._reply = reply
        self._usage = usage or {"input_tokens": 120, "output_tokens": 30}
        self._error = error
        self.prompts: list[str] = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        if self._error is not None:
            raise self._error
        return SimpleNamespace(content=self._reply, usage_metadata=self._usage)


# --- Bloque 24 y 25: chunking, indexación y persistencia ---


def test_split_corpus_preserves_metadata_and_explicit_ids():
    chunks, ids = split_corpus(CORPUS, chunk_size=300, chunk_overlap=45)
    assert len(chunks) == len(ids)
    assert len(chunks) >= len(CORPUS)
    for chunk, chunk_id in zip(chunks, ids):
        assert chunk.id == chunk_id
        assert chunk.metadata["fuente"].endswith(".md")
        assert chunk.metadata["fecha"] == "2026-11-25"


def test_split_corpus_splits_long_document_with_suffixed_ids():
    long_corpus = [
        {
            "id": "largo",
            "fuente": "manual.md",
            "fecha": "2026-11-25",
            "tema": "test",
            "contenido": ("Párrafo con información útil sobre asistencia escolar.\n\n" * 6),
        }
    ]
    chunks, ids = split_corpus(long_corpus, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    assert ids == [f"largo_{i}" for i in range(len(chunks))]
    assert all(c.metadata["fuente"] == "manual.md" for c in chunks)


def test_split_corpus_rejects_overlap_greater_or_equal_to_chunk_size():
    with pytest.raises(ValueError, match="chunk_overlap"):
        split_corpus(CORPUS, chunk_size=100, chunk_overlap=100)


def test_index_corpus_persists_reloads_and_resets_without_duplicates(tmp_path):
    embeddings = DeterministicEmbeddings()
    persist_dir = tmp_path / "vectorstore"

    _, chunks, ids = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=persist_dir,
        collection_name="test_persist",
        reset=True,
    )
    assert persist_dir.exists()
    assert any(persist_dir.iterdir())

    # Reconexión en una instancia nueva sin reindexar
    reloaded = load_vectorstore(
        embeddings,
        persist_directory=persist_dir,
        collection_name="test_persist",
    )
    assert reloaded._collection.count() == len(chunks)

    rows = inspect_chunks(reloaded)
    assert len(rows) == len(ids)
    assert {r["id"] for r in rows} == set(ids)
    assert all(r["metadata"]["fuente"] != "desconocida" for r in rows)

    # Reindexar con reset=True no debe duplicar chunks
    # (cerrar cliente previo liberando referencias antes de borrar en Windows)
    del reloaded
    _, chunks2, _ = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=persist_dir,
        collection_name="test_persist_2",
        reset=False,
    )
    reloaded2 = load_vectorstore(
        embeddings,
        persist_directory=persist_dir,
        collection_name="test_persist_2",
    )
    assert reloaded2._collection.count() == len(chunks2)


# --- Bloque 26: recuperación semántica y citas ---


def test_format_context_numbers_consecutively_and_tracks_sources():
    docs = [
        Document(page_content="Texto A", metadata={"fuente": "a.md"}),
        Document(page_content="Texto B", metadata={"fuente": "b.md"}),
        Document(page_content="Texto C", metadata={}),
    ]
    context, citations = format_context(docs)
    assert "[1] Texto A" in context
    assert "[2] Texto B" in context
    assert "[3] Texto C" in context
    assert citations == {1: "a.md", 2: "b.md", 3: "desconocida"}


def test_build_rag_prompt_contains_exact_question_and_citation_rules():
    docs = [Document(page_content="Regla de asistencia 85 %.", metadata={"fuente": "reg.md"})]
    question = "¿Cuál es el porcentaje mínimo de asistencia?"
    prompt, citations = build_rag_prompt(question, docs)
    assert f"Pregunta: {question}" in prompt
    assert "[1] Regla de asistencia 85 %." in prompt
    assert "corchetes" in prompt.lower()
    assert "inventar" in prompt.lower()
    assert citations == {1: "reg.md"}


# --- Bloque 27: precisión, recall, F1 y conjunto de evaluación ---


def test_retrieval_metrics_and_edge_cases():
    assert precision_at_k(["doc2", "doc0", "doc4"], {"doc0"}) == pytest.approx(1 / 3)
    assert recall_at_k(["doc2", "doc0", "doc4"], {"doc0"}) == pytest.approx(1.0)
    assert f1_score(1 / 3, 1.0) == pytest.approx(0.5)

    # Casos borde: sin ZeroDivisionError
    assert precision_at_k([], {"doc0"}) == 0.0
    assert recall_at_k(["doc0"], set()) is None
    assert f1_score(0.5, None) == 0.0
    assert f1_score(0.0, 0.0) == 0.0
    assert average_metric([1.0, None, 0.5]) == pytest.approx(0.75)
    assert average_metric([None, None]) == 0.0


def test_evaluate_retrieval_and_compare_k_on_deterministic_vectorstore(tmp_path):
    embeddings = DeterministicEmbeddings()
    vectorstore, _, _ = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=tmp_path / "vs_eval",
        collection_name="test_eval",
        chunk_size=400,
        chunk_overlap=40,
        reset=True,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    report = evaluate_retrieval(retriever, cases=EVALUATION_CASES, k=3)

    assert report["k"] == 3
    assert report["cases_total"] == len(EVALUATION_CASES)
    assert report["cases_with_answer"] == len(EVALUATION_CASES) - 1
    assert report["avg_recall"] >= 0.85
    # El último caso es sin respuesta en el corpus -> recall debe ser None
    assert report["cases"][-1]["recall"] is None

    comparison = compare_k_values(vectorstore, EVALUATION_CASES, k_values=(1, 2, 3))
    assert [row["k"] for row in comparison] == [1, 2, 3]
    # Con k=1 la precisión suele ser mayor o igual que con k=3 cuando hay 1 relevante
    assert comparison[0]["avg_precision"] >= comparison[2]["avg_precision"]


# --- Bloque 28: flujo RAG completo, latencia, costo y benchmark ---


def test_answer_with_rag_measures_latency_cost_and_handles_content_blocks(tmp_path):
    embeddings = DeterministicEmbeddings()
    vectorstore, _, _ = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=tmp_path / "vs_rag",
        collection_name="test_rag",
        chunk_size=400,
        chunk_overlap=40,
        reset=True,
    )
    model = FakeModel(
        reply=[{"type": "text", "text": "La asistencia mínima es 85 % [1]."}],
        usage={"input_tokens": 200, "output_tokens": 40},
    )

    result = answer_with_rag(
        "¿Cuál es la asistencia mínima para promoción?",
        vectorstore=vectorstore,
        model=model,
        k=3,
    )
    assert result["error"] is None
    assert result["answer"] == "La asistencia mínima es 85 % [1]."
    assert len(result["citations"]) == 3
    assert all(src != "desconocida" for src in result["citations"].values())
    assert result["total_latency_ms"] >= 0.0
    assert result["input_tokens"] == 200
    assert result["output_tokens"] == 40
    expected_cost = calculate_rag_cost_usd(result["embedding_tokens"], 200, 40)
    assert result["estimated_cost_usd"] == pytest.approx(round(expected_cost, 8))


def test_answer_with_rag_handles_empty_input_and_model_errors(tmp_path):
    embeddings = DeterministicEmbeddings()
    vectorstore, _, _ = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=tmp_path / "vs_err",
        collection_name="test_err",
        chunk_size=400,
        chunk_overlap=40,
        reset=True,
    )
    model = FakeModel()
    empty_res = answer_with_rag("   ", vectorstore=vectorstore, model=model)
    assert empty_res["answer"] == EMPTY_QUESTION_REPLY
    assert model.prompts == []

    broken_model = FakeModel(error=RuntimeError("proveedor caído"))
    err_res = answer_with_rag("¿Qué nota aprueba?", vectorstore=vectorstore, model=broken_model)
    assert err_res["answer"] == ERROR_REPLY
    assert err_res["error"] == "RuntimeError"
    assert err_res["estimated_cost_usd"] == 0.0


def test_run_benchmark_writes_valid_json_report(tmp_path):
    embeddings = DeterministicEmbeddings()
    vectorstore, _, _ = index_corpus(
        embeddings,
        corpus=CORPUS,
        persist_directory=tmp_path / "vs_bench",
        collection_name="test_bench",
        chunk_size=400,
        chunk_overlap=40,
        reset=True,
    )
    model = FakeModel()
    out_file = tmp_path / "rag-metrics.json"
    report = run_benchmark(
        questions=["¿Qué nota aprueba?", "¿Qué hace ante 429?"],
        vectorstore=vectorstore,
        model=model,
        k=3,
        output_path=out_file,
    )

    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["queries_total"] == 2
    assert loaded["queries_ok"] == 2
    assert loaded["total_cost_usd"] == pytest.approx(report["total_cost_usd"])
    assert len(loaded["runs"]) == 2


def test_jsonl_records_follow_block_28_schema(tmp_path):
    run = {
        "question": "¿Cuál es la asistencia mínima?",
        "retrieval_latency_ms": 15.2,
        "generation_latency_ms": 820.5,
        "total_latency_ms": 835.7,
        "input_tokens": 150,
        "output_tokens": 35,
        "estimated_cost_usd": 0.00013,
    }
    rec_k3 = to_jsonl_record(run, k=3)
    rec_k6 = to_jsonl_record({**run, "input_tokens": 260}, k=6)
    jsonl_path = write_jsonl_records([rec_k3, rec_k6], output_path=tmp_path / "out.jsonl")

    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first, second = json.loads(lines[0]), json.loads(lines[1])
    assert set(["timestamp", "pregunta", "k", "tiempos_ms", "tiempo_total_ms", "tokens"]).issubset(
        first.keys()
    )
    assert first["k"] == 3 and second["k"] == 6
    assert second["tokens"]["input_tokens"] > first["tokens"]["input_tokens"]
