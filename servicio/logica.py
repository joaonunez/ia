"""Lógica de negocio del asistente académico IA, desacoplada de HTTP (U3.2 · Bloque 35).

Regla de diseño: no inicializa clientes externos ni exige API_KEY al importar.
Reutiliza el corpus reglamentario de U2.5 y el filtro anti-inyección + logging
JSON con `trace_id` de U2.7.
"""
from __future__ import annotations

import logging
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any

# Permite importar módulos del Módulo 2 en `src/` desde la raíz del repositorio.
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from observability_security import (  # noqa: E402
    new_trace_id,
    text_fingerprint,
    trace_id_var,
)
from rag_corpus import CORPUS  # noqa: E402
from servicio import cadena, respaldo, seguridad  # noqa: E402

logger = logging.getLogger("servicio.logica")

SIN_INFORMACION_REPLY = (
    "No cuento con información suficiente en los documentos indexados para "
    "responder esa pregunta."
)

# Dataset simulado de solo lectura (extiende los datos ficticios de 2°B de U2.4).
ESTUDIANTES_SIMULADOS: dict[str, dict[str, Any]] = {
    "sofia rojas": {
        "nombre": "Sofía Rojas",
        "curso": "2°B",
        "notas": [6.2, 5.8, 6.5],
        "promedio": 6.2,
        "asistencia_pct": 94,
        "inasistencias": 3,
        "simulado": True,
    },
    "ana rojas": {
        "nombre": "Ana Rojas",
        "curso": "2°B",
        "notas": [6.0, 6.2, 6.1],
        "promedio": 6.1,
        "asistencia_pct": 96,
        "inasistencias": 2,
        "simulado": True,
    },
    "diego soto": {
        "nombre": "Diego Soto",
        "curso": "2°B",
        "notas": [3.5, 3.8, 3.8],
        "promedio": 3.7,
        "asistencia_pct": 72,
        "inasistencias": 11,
        "simulado": True,
    },
    "luis perez": {
        "nombre": "Luis Pérez",
        "curso": "2°B",
        "notas": [5.2, 5.5, 5.5],
        "promedio": 5.4,
        "asistencia_pct": 88,
        "inasistencias": 5,
        "simulado": True,
    },
    "marta diaz": {
        "nombre": "Marta Díaz",
        "curso": "2°B",
        "notas": [4.6, 5.0, 4.8],
        "promedio": 4.8,
        "asistencia_pct": 81,
        "inasistencias": 8,
        "simulado": True,
    },
}

_STOPWORDS = {
    "cual",
    "cuales",
    "como",
    "donde",
    "para",
    "este",
    "esta",
    "esto",
    "unos",
    "unas",
    "sobre",
    "entre",
    "hace",
    "llama",
    "tiene",
    "puede",
    "del",
    "los",
    "las",
    "una",
    "con",
    "por",
    "que",
}

_live_rag_bundle: tuple[Any, Any] | None = None


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    limpio = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").lower()
    return limpio


def _palabras_clave(texto: str) -> set[str]:
    norm = _normalizar(texto)
    tokens = []
    actual = []
    for ch in norm:
        if ch.isalnum():
            actual.append(ch)
        elif actual:
            tokens.append("".join(actual))
            actual = []
    if actual:
        tokens.append("".join(actual))
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def _obtener_rag_en_vivo():
    """Inicialización lazy del flujo RAG real (solo si USE_LIVE_RAG=true y hay API_KEY)."""
    global _live_rag_bundle
    if _live_rag_bundle is None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from client import DEFAULT_MODEL
        from rag_indexer import DEFAULT_PERSIST_DIR, build_embeddings, index_corpus, load_vectorstore

        api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
        embeddings = build_embeddings(api_key=api_key)
        if not DEFAULT_PERSIST_DIR.exists():
            index_corpus(embeddings, persist_directory=DEFAULT_PERSIST_DIR, reset=True)
        vs = load_vectorstore(embeddings, persist_directory=DEFAULT_PERSIST_DIR)
        model = ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            api_key=api_key,
            timeout=20,
            max_retries=2,
        )
        _live_rag_bundle = (vs, model)
    return _live_rag_bundle


def _buscar_en_corpus_local(pregunta: str) -> tuple[str, list[str]]:
    """Delega la recuperación y generación local en la cadena usando el modelo activo."""
    return cadena.ejecutar(pregunta, respaldo.elegir_modelo())


def responder_consulta(pregunta: str) -> dict[str, Any]:
    """Orquesta trazabilidad, filtro anti-inyección y recuperación con citas."""
    current_trace = new_trace_id()
    token = trace_id_var.set(current_trace)

    try:
        logger.info(
            "api_consulta_recibida",
            extra={
                "extra_data": {
                    "trace_id": current_trace,
                    "longitud_pregunta": len(pregunta),
                    "huella_pregunta": text_fingerprint(pregunta),
                }
            },
        )

        regla = seguridad.detectar_inyeccion(pregunta)
        if regla:
            logger.warning(
                "api_inyeccion_bloqueada",
                extra={
                    "extra_data": {
                        "trace_id": current_trace,
                        "regla": regla,
                        "longitud_pregunta": len(pregunta),
                    }
                },
            )
            return {
                "respuesta": seguridad.RECHAZO,
                "fuentes": [],
                "trace_id": current_trace,
                "bloqueada": True,
            }

        usar_vivo = os.getenv("USE_LIVE_RAG", "").lower() == "true" and bool(
            os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        if usar_vivo:
            from rag_pipeline import answer_with_rag

            vs, model = _obtener_rag_en_vivo()
            res = answer_with_rag(pregunta, vectorstore=vs, model=model, k=3)
            fuentes = list(dict.fromkeys(res["citations"].values()))
            return {
                "respuesta": res["answer"],
                "fuentes": fuentes,
                "trace_id": res["trace_id"],
                "bloqueada": res["blocked"],
            }

        respuesta, fuentes = _buscar_en_corpus_local(pregunta)
        bloqueada = respuesta == seguridad.RECHAZO
        logger.info(
            "api_consulta_respondida",
            extra={
                "extra_data": {
                    "trace_id": current_trace,
                    "citas": len(fuentes),
                    "longitud_respuesta": len(respuesta),
                    "bloqueada": bloqueada,
                }
            },
        )
        return {
            "respuesta": respuesta,
            "fuentes": fuentes,
            "trace_id": current_trace,
            "bloqueada": bloqueada,
        }
    finally:
        trace_id_var.reset(token)


def consultar_estudiante(nombre: str) -> dict[str, Any] | None:
    """Busca un estudiante en el dataset simulado de solo lectura (insensible a tildes/caso)."""
    clave = _normalizar(nombre).strip()
    return ESTUDIANTES_SIMULADOS.get(clave)
