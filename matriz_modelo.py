"""Matriz de pruebas modelo con detección de limitación léxica (U3.5 · Bloque 42).

Incluye casos válidos, inválidos y de borde (NFD, 404, 422, límite de longitud
y ambigüedad/sinonimia semántica `MP-08` declarada como limitación conocida).
"""
from __future__ import annotations

from typing import Any

MATRIZ: list[dict[str, Any]] = [
    {
        "id": "MP-01",
        "tipo": "valido",
        "escenario": "Consulta reglamentaria sobre porcentaje mínimo de asistencia con cita verificable",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"},
        },
        "esperado": {
            "estado": 200,
            "contiene": ["85 %"],
            "fuentes": ["reglamento_asistencia.md"],
        },
        "cubre": ["RF-01", "RF-02", "CA-01", "CA-02"],
    },
    {
        "id": "MP-02",
        "tipo": "valido",
        "escenario": "Consulta de notas y asistencia de estudiante simulado existente",
        "peticion": {
            "metodo": "GET",
            "ruta": "/estudiantes/Sofía Rojas",
        },
        "esperado": {
            "estado": 200,
            "contiene": ["Sofía Rojas", "6.2"],
        },
        "cubre": ["RF-03", "CA-04"],
    },
    {
        "id": "MP-03",
        "tipo": "valido",
        "escenario": "Pregunta fuera del corpus escolar no inventa datos y devuelve fuentes vacías",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "¿Cómo se llama el director del establecimiento?"},
        },
        "esperado": {
            "estado": 200,
            "contiene": ["No cuento con información suficiente"],
            "fuentes": [],
        },
        "cubre": ["RF-02", "CA-03"],
    },
    {
        "id": "MP-04",
        "tipo": "invalido",
        "escenario": "Pregunta bajo el mínimo de 3 caracteres rechazada con 422",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "ok"},
        },
        "esperado": {
            "estado": 422,
            "contiene": ["entrada_invalida"],
        },
        "cubre": ["RF-01"],
    },
    {
        "id": "MP-05",
        "tipo": "invalido",
        "escenario": "Pregunta de 501 caracteres (límite + 1) rechazada con 422",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "a" * 501},
        },
        "esperado": {
            "estado": 422,
            "contiene": ["entrada_invalida"],
        },
        "cubre": ["RF-01"],
    },
    {
        "id": "MP-06",
        "tipo": "borde",
        "escenario": "Nombre de estudiante con formato válido pero inexistente devuelve 404",
        "peticion": {
            "metodo": "GET",
            "ruta": "/estudiantes/Carlos Vega",
        },
        "esperado": {
            "estado": 404,
            "contiene": ["no_encontrado"],
        },
        "cubre": ["RF-03"],
    },
    {
        "id": "MP-07",
        "tipo": "borde",
        "escenario": "Pregunta con tildes combinantes Unicode NFD recupera correctamente el reglamento",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "¿Cuál es la promocio\u0301n escolar mi\u0301nima de asistencia?"},
        },
        "esperado": {
            "estado": 200,
            "contiene": ["85 %"],
            "fuentes": ["reglamento_asistencia.md"],
        },
        "cubre": ["RF-02"],
    },
    {
        "id": "MP-08",
        "tipo": "borde",
        "escenario": "Paráfrasis sin palabras clave literales del corpus (sinonimia: faltas/alumno/repetir)",
        "peticion": {
            "metodo": "POST",
            "ruta": "/ask",
            "json": {"pregunta": "¿Cuántas faltas a clases puede tener un alumno antes de repetir el año?"},
        },
        "esperado": {
            "estado": 200,
            "contiene": ["85 %"],
            "fuentes": ["reglamento_asistencia.md"],
        },
        "cubre": ["RF-02"],
        "hallazgo": {
            "clasificacion": "limitacion",
            "decision": (
                "En modo simulado la recuperación léxica exige coincidencia exacta de raíces y no "
                "resuelve sinónimos ('faltas'/'inasistencia'); en producción con USE_LIVE_RAG=true "
                "se mitiga con embeddings en Chroma y se declara en README.md."
            ),
        },
    },
    {
        "id": "MP-09",
        "tipo": "borde",
        "escenario": "Nombre de estudiante con símbolos inválidos rechazado con 422",
        "peticion": {
            "metodo": "GET",
            "ruta": "/estudiantes/123!!!",
        },
        "esperado": {
            "estado": 422,
            "contiene": ["entrada_invalida"],
        },
        "cubre": ["RF-03"],
    },
]
