"""Indexación de corpus y persistencia en ChromaDB para el flujo RAG (U2.5).

Parte un corpus propio del asistente del gestor académico usando
chunking recursivo con solapamiento, preserva metadatos de fuente y
fecha, asigna IDs explícitos y persiste los embeddings en disco.

Los nombres del fuente están en inglés; los comentarios, metadatos y
documentos del corpus están en español.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_COLLECTION_NAME = "academic_assistant_rag"
DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent / "vectorstore"
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 45

# Corpus propio de 8 documentos breves y coherentes sobre el asistente del
# gestor académico y el reglamento escolar ficticio del proyecto.
CORPUS: list[dict[str, str]] = [
    {
        "id": "doc0",
        "fuente": "reglamento_asistencia.md",
        "fecha": "2026-11-25",
        "tema": "asistencia",
        "contenido": (
            "El porcentaje mínimo de asistencia para promoción escolar es del 85 %. "
            "Cuando un estudiante baja del 80 % o acumula más de 8 días de inasistencia "
            "en el trimestre, el gestor académico debe revisar el caso y coordinar "
            "un contacto preventivo con el apoderado."
        ),
    },
    {
        "id": "doc1",
        "fuente": "reglamento_notas.md",
        "fecha": "2026-11-25",
        "tema": "calificaciones",
        "contenido": (
            "La escala de calificaciones chilena va de 1.0 a 7.0, con nota mínima de "
            "aprobación 4.0. Un promedio bajo 4.0 en asignaturas troncales activa una "
            "alerta académica que el gestor debe registrar antes del cierre del período."
        ),
    },
    {
        "id": "doc2",
        "fuente": "protocolo_apoderados.md",
        "fecha": "2026-11-25",
        "tema": "comunicaciones",
        "contenido": (
            "Todo aviso formal enviado al apoderado por riesgo de repitencia o baja "
            "asistencia requiere aprobación humana explícita antes de despacharse. "
            "El mensaje enviado no se puede retirar y queda auditado con fecha y motivo."
        ),
    },
    {
        "id": "doc3",
        "fuente": "cliente_reintentos.md",
        "fecha": "2026-11-25",
        "tema": "resiliencia",
        "contenido": (
            "El cliente HTTP del asistente reintenta hasta 3 veces ante errores 429, "
            "5xx o cortes de red, aplicando espera exponencial (2, 4 y 8 segundos, "
            "tope 30 s) con jitter del 10 %. Los errores 401 y 403 nunca se reintentan "
            "y fallan de inmediato con ValueError."
        ),
    },
    {
        "id": "doc4",
        "fuente": "decision_modelo_costos.md",
        "fecha": "2026-11-25",
        "tema": "costos",
        "contenido": (
            "El modelo elegido para generación es gemini-3.5-flash-lite por su baja "
            "latencia y bajo costo: USD 0.30 por millón de tokens de entrada y "
            "USD 2.50 por millón de tokens de salida. El costo de sesión solo suma "
            "respuestas válidas."
        ),
    },
    {
        "id": "doc5",
        "fuente": "arquitectura_solo_lectura.md",
        "fecha": "2026-11-25",
        "tema": "arquitectura",
        "contenido": (
            "En producción sobre la intranet escolar, el asistente consulta datos "
            "académicos con un rol de base de datos de solo lectura (intranet_ai_ro). "
            "No puede crear, modificar ni eliminar registros oficiales de estudiantes."
        ),
    },
    {
        "id": "doc6",
        "fuente": "limites_autonomia.md",
        "fecha": "2026-11-25",
        "tema": "gobernanza",
        "contenido": (
            "El agente limita su ciclo razonar-actuar a un máximo de 5 iteraciones "
            "(MAX_ITERATIONS = 5) para evitar bucles costosos. Cada interacción queda "
            "registrada en agent-traces.jsonl y cada decisión de aprobación en "
            "agent-approvals.jsonl."
        ),
    },
    {
        "id": "doc7",
        "fuente": "estrategia_pruebas.md",
        "fecha": "2026-11-25",
        "tema": "calidad",
        "contenido": (
            "Las pruebas unitarias del repositorio usan mocks y embeddings deterministas "
            "para verificar lógica, reintentos, métricas y citas sin gastar cuota ni "
            "depender de la red; la suite completa corre en pocos segundos."
        ),
    },
]


def build_embeddings(api_key: str | None = None, model: str = DEFAULT_EMBEDDING_MODEL):
    """Inicializa GoogleGenerativeAIEmbeddings validando que exista la clave."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    resolved_key = api_key or os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
    if not resolved_key:
        raise ValueError(
            "Falta API_KEY o GEMINI_API_KEY en el entorno. Defínela en tu archivo .env."
        )
    return GoogleGenerativeAIEmbeddings(model=model, google_api_key=resolved_key)


def split_corpus(
    corpus: list[dict[str, str]] = CORPUS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[list[Document], list[str]]:
    """Parte el corpus con chunking recursivo y genera IDs explícitos 1 a 1.

    Si un documento cabe en un solo chunk conserva su ID base (ej. `doc0`);
    si se divide en varios, agrega sufijo secuencial (`doc0_0`, `doc0_1`, ...).
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) debe ser menor que chunk_size ({chunk_size})."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    all_chunks: list[Document] = []
    all_ids: list[str] = []

    for index, entry in enumerate(corpus):
        base_id = entry.get("id", f"doc{index}")
        metadata = {
            "fuente": entry["fuente"],
            "fecha": entry.get("fecha", "sin_fecha"),
            "tema": entry.get("tema", "general"),
            "doc_id": base_id,
        }
        pieces = splitter.create_documents([entry["contenido"]], metadatas=[metadata])
        if len(pieces) == 1:
            pieces[0].id = base_id
            all_chunks.append(pieces[0])
            all_ids.append(base_id)
        else:
            for part_idx, piece in enumerate(pieces):
                chunk_id = f"{base_id}_{part_idx}"
                piece.id = chunk_id
                all_chunks.append(piece)
                all_ids.append(chunk_id)

    return all_chunks, all_ids


def index_corpus(
    embedding_function,
    corpus: list[dict[str, str]] = CORPUS,
    persist_directory: str | Path = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    reset: bool = True,
) -> tuple[Chroma, list[Document], list[str]]:
    """Indexa el corpus en ChromaDB y persiste los embeddings en disco.

    Con `reset=True` (por defecto) elimina el directorio previo antes de
    reindexar para evitar duplicación de chunks.
    """
    target_dir = Path(persist_directory)
    if reset and target_dir.exists():
        shutil.rmtree(target_dir)

    chunks, ids = split_corpus(
        corpus=corpus,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        ids=ids,
        collection_name=collection_name,
        persist_directory=str(target_dir),
    )
    return vectorstore, chunks, ids


def load_vectorstore(
    embedding_function,
    persist_directory: str | Path = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Chroma:
    """Se reconecta a un índice Chroma ya persistido sin recalcular embeddings."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=str(persist_directory),
    )


def inspect_chunks(vectorstore: Chroma) -> list[dict[str, object]]:
    """Devuelve ID, metadatos y vista previa de cada chunk almacenado."""
    data = vectorstore.get()
    rows: list[dict[str, object]] = []
    for chunk_id, text, metadata in zip(
        data.get("ids", []),
        data.get("documents", []),
        data.get("metadatas", []),
    ):
        rows.append(
            {
                "id": chunk_id,
                "metadata": metadata or {},
                "preview": (text or "")[:100],
            }
        )
    return rows


def main() -> None:
    """Indexa el corpus propio con Gemini Embeddings y verifica la persistencia."""
    from dotenv import load_dotenv

    load_dotenv()
    embeddings = build_embeddings()
    try:
        _, chunks, ids = index_corpus(embeddings, reset=True)
    except Exception as error:
        message = str(error)
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            print("Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
        elif "API key" in message or "401" in message or "403" in message:
            print("La API rechazó tu clave. Revisa API_KEY / GEMINI_API_KEY en tu .env.")
        else:
            print(f"No se pudo indexar el corpus ({type(error).__name__}): {message}")
        raise SystemExit(1)

    reloaded = load_vectorstore(embeddings)
    count = reloaded._collection.count()
    print(f"Indexados {len(chunks)} chunks con IDs {ids} en {DEFAULT_PERSIST_DIR}")
    print(f"Verificación tras recargar desde disco: {count} chunks persistidos.")
    for row in inspect_chunks(reloaded):
        print(f"  - {row['id']} | {row['metadata']} | {row['preview']}...")


if __name__ == "__main__":
    main()
