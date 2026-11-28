"""Datos de la prueba cruzada de transferencia (U3.6 · Bloque 45)."""
from __future__ import annotations

from typing import Any

META_MINUTOS = 30
CAUSAS_VALIDAS = ("documentacion", "entorno", "expectativa", "producto")
ESTADOS_VALIDOS = ("resuelta", "declarada")

PRUEBA: dict[str, Any] = {
    "fecha": "2026-11-28",
    "revisor": "Revisión cruzada entre pares (simulada con protocolo limpio)",
    "duracion_minutos": 18,
    "preguntas_al_autor": 0,
    "documentos_usados": ["README.md", "docs/api.md"],
    "tareas": [
        {
            "id": "T-01",
            "tarea": "Instalar entorno y arrancar el servicio siguiendo solo README.md",
            "lograda": True,
            "minutos": 6,
            "nota": "Arrancó en puerto 8000 con /health en estado ok y modelo_activo simulado.",
        },
        {
            "id": "T-02",
            "tarea": "Ejecutar una consulta reglamentaria usando el ejemplo de docs/api.md",
            "lograda": True,
            "minutos": 3,
            "nota": "POST /ask devolvió 85 % y fuente reglamento_asistencia.md.",
        },
        {
            "id": "T-03",
            "tarea": "Consultar un estudiante simulado de solo lectura",
            "lograda": True,
            "minutos": 2,
            "nota": "GET /estudiantes/Sofía Rojas devolvió promedio 6.2 y simulado=true.",
        },
        {
            "id": "T-04",
            "tarea": "Provocar un error 422 y un 404 y comprobar el contrato de error",
            "lograda": True,
            "minutos": 3,
            "nota": "Ambos devolvieron codigo, mensaje y campos sin trazas ni secretos.",
        },
        {
            "id": "T-05",
            "tarea": "Realizar dos preguntas propias fuera del ejemplo (una válida y una paráfrasis)",
            "lograda": True,
            "minutos": 4,
            "nota": "La consulta de escala de notas respondió 1.0 a 7.0; la paráfrasis pura activó LIM-01.",
        },
    ],
    "observaciones": [
        {
            "id": "O-01",
            "tarea": "T-01",
            "causa": "documentacion",
            "estado": "resuelta",
            "descripcion": "Se agregó el comando exacto de activación del venv en PowerShell y el arranque local con uvicorn.",
            "accion": "Se incorporó la sección Instalación con nota de Windows y el comando uvicorn en README.md.",
        },
        {
            "id": "O-02",
            "tarea": "T-05",
            "causa": "producto",
            "estado": "declarada",
            "descripcion": "En modo simulado sin embeddings, una paráfrasis sin palabras clave literales devuelve SIN_INFORMACION.",
            "accion": "Declarada como limitación LIM-01 en docs/limitaciones.md y mitigada en producción con USE_LIVE_RAG=true.",
            "limitacion": "LIM-01",
        },
    ],
}
