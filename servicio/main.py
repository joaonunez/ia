"""Capa HTTP con FastAPI del asistente académico IA (U3.2 · Bloques 35-36).

Mantiene los endpoints delgados: recibe datos validados por Pydantic, delega
toda la lógica a `servicio.logica`, aplica formato único de error mediante
`servicio.errores` y devuelve respuestas tipadas.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

from servicio import errores, logica
from servicio.esquemas import (
    Consulta,
    ErrorRespuesta,
    EstadoSalud,
    EstudianteResumen,
    Respuesta,
)

VERSION_SERVICIO = "0.2.0"

app = FastAPI(
    title="Asistente Académico IA (Solo Lectura)",
    version=VERSION_SERVICIO,
    description=(
        "Servicio HTTP para consultar reglamentos escolares con citas verificables, "
        "filtro anti-inyección, validación estricta y datos académicos simulados de solo lectura."
    ),
)

errores.registrar(app)


@app.get(
    "/health",
    response_model=EstadoSalud,
    tags=["sistema"],
    summary="Comprobar estado del servicio",
)
def health() -> EstadoSalud:
    """Indica que el servicio HTTP está levantado sin requerir clave de API."""
    return EstadoSalud(
        estado="ok",
        servicio="asistente-academico-ia",
        version=VERSION_SERVICIO,
    )


@app.post(
    "/ask",
    response_model=Respuesta,
    responses={
        422: {
            "model": ErrorRespuesta,
            "description": "Los datos enviados no cumplen el formato esperado.",
        },
    },
    tags=["consultas"],
    summary="Consultar reglamentos escolares con citas",
)
def ask(consulta: Consulta) -> Respuesta:
    """Responde preguntas académicas con citas verificables y filtro anti-inyección."""
    return Respuesta(**logica.responder_consulta(consulta.pregunta))


@app.get(
    "/estudiantes/{nombre}",
    response_model=EstudianteResumen,
    responses={
        404: {
            "model": ErrorRespuesta,
            "description": "No se encontró el estudiante simulado solicitado.",
        },
        422: {
            "model": ErrorRespuesta,
            "description": "El nombre de estudiante no tiene un formato válido.",
        },
    },
    tags=["estudiantes"],
    summary="Consultar notas y asistencia de un estudiante simulado",
)
def obtener_estudiante(
    nombre: Annotated[
        str,
        Path(
            min_length=2,
            max_length=60,
            pattern=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$",
            description="Nombre completo del estudiante simulado (solo letras y espacios).",
            examples=["Sofía Rojas"],
        ),
    ],
) -> EstudianteResumen:
    """Devuelve notas y asistencia de solo lectura desde el dataset simulado."""
    datos = logica.consultar_estudiante(nombre)
    if datos is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el estudiante simulado '{nombre}'.",
        )
    return EstudianteResumen(**datos)
