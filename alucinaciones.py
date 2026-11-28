"""Sondas de alucinación y limitaciones de detección mecánica (U3.5 · Bloque 43)."""
from __future__ import annotations

from typing import Any

SONDAS: list[dict[str, Any]] = [
    {
        "id": "H-01",
        "tipo": "cifra_inventada",
        "escenario": "Modelo inventa un porcentaje de asistencia inexistente (92 %)",
        "pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        "respuesta_modelo": "El porcentaje mínimo de asistencia para promoción escolar es del 92 % [1].",
        "detectable": True,
        "codigo_esperado": "cifra_inventada",
    },
    {
        "id": "H-02",
        "tipo": "fuente_inventada",
        "escenario": "Modelo cita un documento PDF inexistente en los fragmentos recuperados",
        "pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        "respuesta_modelo": (
            "Según decreto_inexistente_2099.pdf, el porcentaje mínimo de asistencia "
            "para promoción escolar es del 85 % [1]."
        ),
        "detectable": True,
        "codigo_esperado": "fuente_inventada",
    },
    {
        "id": "H-03",
        "tipo": "sin_respaldo",
        "escenario": "Modelo responde con afirmación fabricada cuando no hay fragmentos recuperados",
        "pregunta": "¿Cuál es el menú del casino los viernes por la tarde?",
        "respuesta_modelo": "El casino sirve menú vegetariano todos los viernes por la tarde.",
        "detectable": True,
        "codigo_esperado": "sin_respaldo",
    },
    {
        "id": "H-04",
        "tipo": "afirmacion_agregada",
        "escenario": "Modelo añade una afirmación cualitativa no respaldada sin cifras ni archivos falsos",
        "pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        "respuesta_modelo": (
            "El porcentaje mínimo de asistencia para promoción escolar es del 85 % "
            "y el establecimiento entrega un diploma especial a fin de año [1]."
        ),
        "detectable": False,
        "codigo_esperado": None,
        "decision": (
            "Limitación inherente a reglas léxicas: afirmaciones cualitativas sin cifras ni "
            "archivos falsos requieren revisión humana antes de comunicar decisiones formales "
            "al apoderado y muestreo semanal de trazas."
        ),
    },
    {
        "id": "H-05",
        "tipo": "cifra_en_letras",
        "escenario": "Modelo inventa un número escrito en palabras ('veinte') en lugar de dígitos",
        "pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        "respuesta_modelo": (
            "El porcentaje mínimo de asistencia es del 85 % y se permiten veinte faltas "
            "justificadas sin revisión del gestor [1]."
        ),
        "detectable": False,
        "codigo_esperado": None,
        "decision": (
            "Limitación conocida del verificador numérico basado en dígitos: cifras escritas "
            "en palabras no se capturan mecánicamente; se mitiga mediante revisión humana en "
            "avisos críticos y se planifica evaluador NLI en fase posterior."
        ),
    },
]
