"""Cadena de 4 componentes desacoplados con guardias de contrato, seguridad y fundamentación.

Componentes (U3.4 Bloque 39 + U3.5 Bloque 43):
1. `recuperar(pregunta)` -> lista de fragmentos `{"fuente", "texto"}`
2. `construir_prompt(pregunta, fragmentos)` -> texto del prompt
3. `modelo.generar(prompt)` -> texto de respuesta (por defecto `ModeloSimulado`)
4. `empaquetar(texto, fragmentos)` -> `(texto, fuentes_sin_repetir)`

Defensas integradas en `ejecutar()`:
- Detección de inyección en entrada (antes de recuperar o invocar modelo).
- Contrato `list[Fragmento]` antes de filtrar fragmentos sospechosos del corpus.
- Limpieza de salida (instrucciones internas y secretos).
- Compuerta mecánica de fundamentación (`problemas_de_respaldo`).
"""
from __future__ import annotations

import logging
import sys
import unicodedata
from pathlib import Path
from typing import Any

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from rag_corpus import CORPUS  # noqa: E402
from servicio import fundamentacion, seguridad  # noqa: E402
from servicio.contratos import Fragmento, exigir  # noqa: E402

logger = logging.getLogger("servicio.cadena")

SIN_INFORMACION = (
    "No cuento con información suficiente en los documentos indexados para "
    "responder esa pregunta."
)

INSTRUCCION = "Responde usando todo el contexto. Si no alcanza, dilo."

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


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").lower()


def _palabras_clave(texto: str) -> set[str]:
    norm = _normalizar(texto)
    tokens: list[str] = []
    actual: list[str] = []
    for ch in norm:
        if ch.isalnum():
            actual.append(ch)
        elif actual:
            tokens.append("".join(actual))
            actual = []
    if actual:
        tokens.append("".join(actual))
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def recuperar(pregunta: str) -> list[dict[str, str]]:
    """Devuelve los fragmentos del corpus escolar pertinentes a la pregunta."""
    q_terms = _palabras_clave(pregunta)
    if not q_terms:
        return []

    candidatos: list[tuple[int, dict[str, str]]] = []
    for doc in CORPUS:
        doc_terms = _palabras_clave(doc["contenido"] + " " + doc["tema"])
        coincidencias = len(q_terms & doc_terms)
        if coincidencias >= 2:
            candidatos.append(
                (
                    coincidencias,
                    {"fuente": doc["fuente"], "texto": doc["contenido"]},
                )
            )

    candidatos.sort(key=lambda par: par[0], reverse=True)
    return [frag for _, frag in candidatos]


def sin_fragmentos_sospechosos(fragmentos: list[dict[str, str]]) -> list[dict[str, str]]:
    """Descarta fragmentos del corpus que contengan patrones de inyección indirecta."""
    limpios: list[dict[str, str]] = []
    for fragmento in fragmentos:
        regla = seguridad.detectar_inyeccion(fragmento["texto"])
        if regla:
            logger.warning(
                "fragmento descartado fuente=%s regla=%s",
                fragmento["fuente"],
                regla,
            )
            continue
        limpios.append(fragmento)
    return limpios


def construir_prompt(pregunta: str, fragmentos: list[dict[str, str]]) -> str:
    """Arma el prompt que recibe el modelo usando únicamente el contexto recuperado."""
    contexto = "\n".join(f"- {f['texto']}" for f in fragmentos)
    return (
        f"{INSTRUCCION}\n"
        f"Contexto:\n{contexto}\n"
        f"Pregunta: {pregunta}"
    )


class ModeloSimulado:
    """Doble de prueba sin red ni API key: responde con el contexto recuperado."""

    nombre = "simulado"

    def generar(self, prompt: str) -> str:
        instruccion, _, resto = prompt.partition("Contexto:\n")
        contexto, _, _ = resto.partition("\nPregunta:")
        lineas = [ln[2:] for ln in contexto.splitlines() if ln.startswith("- ")]
        if not lineas:
            return SIN_INFORMACION
        if "todo el contexto" in instruccion.lower():
            return f"{' '.join(lineas)} [1]"
        return f"{lineas[0]} [1]"


def empaquetar(texto: str, fragmentos: list[dict[str, str]]) -> tuple[str, list[str]]:
    """Devuelve la respuesta y la lista de fuentes sin duplicados preservando el orden."""
    fuentes: list[str] = []
    for fragmento in fragmentos:
        if fragmento["fuente"] not in fuentes:
            fuentes.append(fragmento["fuente"])
    return texto, fuentes


def ejecutar(pregunta: str, modelo: Any | None = None) -> tuple[str, list[str]]:
    """Ejecuta la cadena completa verificando contratos, seguridad y fundamentación."""
    regla = seguridad.detectar_inyeccion(pregunta)
    if regla:
        logger.warning("pregunta rechazada regla=%s longitud=%d", regla, len(pregunta))
        return seguridad.RECHAZO, []

    modelo = modelo or ModeloSimulado()
    fragmentos = recuperar(pregunta)
    exigir(list[Fragmento], fragmentos, "recuperar")
    fragmentos = sin_fragmentos_sospechosos(fragmentos)
    prompt = construir_prompt(pregunta, fragmentos)
    texto = modelo.generar(prompt)
    exigir(str, texto, "generar")
    texto = seguridad.limpiar_salida(texto, internos=(INSTRUCCION,))
    problemas = fundamentacion.problemas_de_respaldo(texto, fragmentos, SIN_INFORMACION)
    if problemas:
        codigos = ",".join(codigo for codigo, _ in problemas)
        logger.warning("respuesta sin respaldo codigos=%s", codigos)
        return SIN_INFORMACION, []
    return empaquetar(texto, fragmentos)
