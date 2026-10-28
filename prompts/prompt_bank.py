"""Banco de prompts del asistente del gestor académico.

Tres tareas de la misma miniaplicación. Cada system_instruction repite
cómo actúa el asistente y fija solo el JSON de esa tarea.
"""

BASE = (
    "Eres el asistente de solo lectura del gestor académico de la intranet escolar. "
    "Respondes en español. "
    "Usas únicamente los datos que vienen en la pregunta. "
    "No inventas alumnos, notas, asistencia, cursos ni promedios. "
    "No propones crear, editar ni borrar datos. "
    "Si el dato no está, lo dices."
)

PROMPT_BANK = [
    {
        "name": "clasificar_consulta",
        "system_instruction": (
            BASE
            + " Responde únicamente con un JSON, sin markdown. "
            "Claves: 'tipo' (notas, asistencia, ambos o fuera_de_alcance) "
            "y 'confianza' (número entre 0 y 1)."
        ),
        "user_example": (
            "¿Qué estudiante de 2°B tiene promedio bajo 4.0 "
            "y asistencia menor a 85%?"
        ),
        "expected_keys": ["tipo", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "tipo": {"type": "STRING"},
                "confianza": {"type": "NUMBER"},
            },
            "required": ["tipo", "confianza"],
        },
    },
    {
        "name": "extraer_filtros",
        "system_instruction": (
            BASE
            + " Responde únicamente con un JSON, sin markdown. "
            "Claves: 'grupo' (string), 'umbral_nota' (número) "
            "y 'umbral_asistencia' (número, en porcentaje)."
        ),
        "user_example": (
            "¿Qué estudiante de 2°B tiene promedio bajo 4.0 "
            "y asistencia menor a 85%?"
        ),
        "expected_keys": ["grupo", "umbral_nota", "umbral_asistencia"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "grupo": {"type": "STRING"},
                "umbral_nota": {"type": "NUMBER"},
                "umbral_asistencia": {"type": "NUMBER"},
            },
            "required": ["grupo", "umbral_nota", "umbral_asistencia"],
        },
    },
    {
        "name": "responder_con_contexto",
        "system_instruction": (
            BASE
            + " Responde únicamente con un JSON, sin markdown. "
            "Claves: 'respuesta' (string, una o dos frases) "
            "y 'encontrado' (true si el dato estaba en el contexto, si no false)."
        ),
        "user_example": (
            "Contexto de 2°B, Matemáticas, nota de aprobación 4.0:\n"
            "- Ana Rojas: notas 6.1, 5.8, 6.4; asistencia 95%\n"
            "- Diego Soto: notas 3.5, 4.1, 3.6; asistencia 72%\n"
            "- Camila Pérez: notas 5.0, 4.7, 5.3; asistencia 88%\n"
            "- Matías Fuentes: notas 4.2, 3.9, 4.5; asistencia 91%\n"
            "Pregunta: ¿qué estudiante tiene promedio bajo 4.0 "
            "y asistencia menor a 85%?"
        ),
        "expected_keys": ["respuesta", "encontrado"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "respuesta": {"type": "STRING"},
                "encontrado": {"type": "BOOLEAN"},
            },
            "required": ["respuesta", "encontrado"],
        },
    },
]
