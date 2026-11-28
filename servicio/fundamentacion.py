"""Detección mecánica de alucinaciones y falta de respaldo (U3.5 · Bloque 43).

Reglas mecánicas verificables sin red:
- `sin_respaldo`: no hay fragmentos recuperados y la respuesta no coincide con `SIN_INFORMACION`.
- `cifra_inventada`: cifra numérica presente en la respuesta (excluyendo nombres de archivo
  y marcas de cita `[1]`) que no aparece en el contexto recuperado.
- `fuente_inventada`: nombre de documento citado (`.pdf`, `.md`, `.txt`, `.docx`) que no
  pertenece a los fragmentos recuperados.
"""
from __future__ import annotations

import re

DOCUMENTOS = re.compile(r"\b[\w.-]+\.(?:pdf|md|txt|docx)\b", re.IGNORECASE)
CITAS = re.compile(r"\[\d+\]")
CIFRAS = re.compile(r"\b\d+(?:[.,]\d+)?\b")


def _extraer_cifras(texto: str) -> set[str]:
    sin_docs = DOCUMENTOS.sub(" ", texto)
    sin_citas = CITAS.sub(" ", sin_docs)
    return set(CIFRAS.findall(sin_citas))


def problemas_de_respaldo(
    respuesta: str,
    fragmentos: list[dict[str, str]],
    sin_informacion: str,
) -> list[tuple[str, str]]:
    """Devuelve lista de `(codigo, detalle)` cuando la respuesta carece de respaldo."""
    problemas: list[tuple[str, str]] = []

    if not fragmentos:
        if respuesta.strip() != sin_informacion.strip():
            problemas.append(
                ("sin_respaldo", "respuesta emitida sin fragmentos recuperados")
            )
        return problemas

    contexto = " ".join(f.get("texto", "") for f in fragmentos)
    fuentes_validas = {f.get("fuente", "").lower() for f in fragmentos}
    contexto_lower = contexto.lower()

    vistos_docs: set[str] = set()
    for doc in DOCUMENTOS.findall(respuesta):
        doc_low = doc.lower()
        if doc_low not in fuentes_validas and doc_low not in contexto_lower and doc_low not in vistos_docs:
            vistos_docs.add(doc_low)
            problemas.append(("fuente_inventada", doc))

    cifras_contexto = _extraer_cifras(contexto)
    for cifra in sorted(_extraer_cifras(respuesta)):
        if cifra not in cifras_contexto:
            problemas.append(("cifra_inventada", cifra))

    return problemas
