"""Contratos Pydantic de entrada, salida y error del servicio HTTP (U3.2 · Bloques 35-36)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EstadoSalud(BaseModel):
    """Respuesta del endpoint de salud del servicio."""

    estado: str = Field(
        description="Estado operativo del servicio ('ok' cuando está disponible).",
        examples=["ok"],
    )
    servicio: str = Field(
        description="Nombre identificador del microservicio.",
        examples=["asistente-academico-ia"],
    )
    version: str = Field(
        description="Versión semántica del servicio HTTP.",
        examples=["0.2.0"],
    )
    entorno: str = Field(
        default="desarrollo",
        description="Entorno de ejecución configurado mediante variable de entorno ENTORNO.",
        examples=["desarrollo"],
    )
    modelo: str = Field(
        default="sin clave",
        description="Estado de la credencial del proveedor ('configurado' o 'sin clave', sin exponer secretos).",
        examples=["sin clave"],
    )


class Consulta(BaseModel):
    """Petición de consulta académica o reglamentaria en lenguaje natural."""

    model_config = ConfigDict(str_strip_whitespace=True)

    pregunta: str = Field(
        min_length=3,
        max_length=500,
        description="Pregunta del usuario en lenguaje natural (entre 3 y 500 caracteres).",
        examples=["¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"],
    )


class Respuesta(BaseModel):
    """Respuesta estructurada con citas verificables y trazabilidad."""

    respuesta: str = Field(
        description="Texto de la respuesta generada o mensaje de rechazo seguro.",
        examples=["La asistencia mínima anual para promoción escolar es 85 % [1]."],
    )
    fuentes: list[str] = Field(
        description="Lista de documentos que respaldan la respuesta; vacía si no hay respaldo.",
        examples=[["reglamento_asistencia.md"]],
    )
    trace_id: str = Field(
        description="Identificador único de trazabilidad generado para la consulta.",
        examples=["trace-a1b2c3d4"],
    )
    bloqueada: bool = Field(
        description="Indica si la consulta fue bloqueada por el filtro anti-inyección.",
        examples=[False],
    )


class EstudianteResumen(BaseModel):
    """Resumen académico de solo lectura de un estudiante simulado."""

    nombre: str = Field(
        description="Nombre completo del estudiante ficticio.",
        examples=["Sofía Rojas"],
    )
    curso: str = Field(
        description="Curso escolar asignado en los datos simulados.",
        examples=["2°B"],
    )
    notas: list[float] = Field(
        description="Lista de calificaciones parciales registradas (escala 1.0 a 7.0).",
        examples=[[6.2, 5.8, 6.5]],
    )
    promedio: float = Field(
        description="Promedio general de calificaciones del estudiante.",
        examples=[6.2],
    )
    asistencia_pct: int = Field(
        description="Porcentaje de asistencia acumulada (0 a 100).",
        examples=[94],
    )
    inasistencias: int = Field(
        description="Cantidad de días de inasistencia registrados.",
        examples=[3],
    )
    simulado: bool = Field(
        description="Confirma que los datos provienen del dataset simulado de solo lectura.",
        examples=[True],
    )


class CampoInvalido(BaseModel):
    """Detalle de un campo que no superó la validación de entrada."""

    campo: str = Field(
        description="Ruta del campo inválido dentro de la petición (sin incluir el valor crudo).",
        examples=["body.pregunta"],
    )
    motivo: str = Field(
        description="Motivo de rechazo reportado por el validador.",
        examples=["String should have at least 3 characters"],
    )


class ErrorRespuesta(BaseModel):
    """Formato único de respuesta para errores controlados del servicio."""

    codigo: str = Field(
        description="Código corto y estable del tipo de error.",
        examples=["entrada_invalida"],
    )
    mensaje: str = Field(
        description="Mensaje claro y seguro para el cliente, sin trazas ni secretos.",
        examples=["Los datos enviados no cumplen el formato esperado."],
    )
    campos: list[CampoInvalido] = Field(
        default_factory=list,
        description="Lista de campos inválidos cuando corresponde a un error 422.",
    )
