"""Dataset propio validado para personalización con PEFT y estimación de costos (U2.6 · Bloques 29–30).

Tarea elegida (comportamiento consistente, no conocimiento faltante):
clasificar consultas en texto libre del gestor académico a un JSON fijo
con las claves `intencion` y `prioridad`.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from google.genai import types

EXPECTED_KEYS: tuple[str, ...] = ("intencion", "prioridad")

# 12 ejemplos variados propios del asistente del gestor académico,
# distribuidos de forma balanceada en 5 categorías (2 a 3 por categoría).
RAW_EXAMPLES: list[tuple[str, dict[str, str]]] = [
    (
        "Necesito ver el promedio final de matemáticas de Diego Soto en 2°B.",
        {"intencion": "notas", "prioridad": "media"},
    ),
    (
        "¿Qué estudiantes del 3°A tienen promedio rojo bajo 4.0 antes del cierre de trimestre?",
        {"intencion": "notas", "prioridad": "alta"},
    ),
    (
        "Muéstrame el listado de notas parciales de Ana Rojas en Historia.",
        {"intencion": "notas", "prioridad": "baja"},
    ),
    (
        "¿Cuántos días de inasistencia acumula Luis Pérez este semestre?",
        {"intencion": "asistencia", "prioridad": "media"},
    ),
    (
        "Alértame qué alumnos bajaron del 85 % de asistencia mínima para promoción.",
        {"intencion": "asistencia", "prioridad": "alta"},
    ),
    (
        "Quiero revisar la asistencia semanal del curso 1°C.",
        {"intencion": "asistencia", "prioridad": "baja"},
    ),
    (
        "Avisa al apoderado de Diego Soto que su asistencia está en riesgo de repitencia.",
        {"intencion": "aviso_apoderado", "prioridad": "alta"},
    ),
    (
        "Prepara una citación formal al apoderado de Marta Díaz por tres notas bajo 4.0.",
        {"intencion": "aviso_apoderado", "prioridad": "alta"},
    ),
    (
        "¿Qué dice el reglamento interno sobre inasistencias justificadas con licencia médica?",
        {"intencion": "reglamento", "prioridad": "baja"},
    ),
    (
        "Consulta el protocolo vigente antes de enviar un aviso formal a una familia.",
        {"intencion": "reglamento", "prioridad": "media"},
    ),
    (
        "La consulta al asistente tardó demasiado y devolvió error de tiempo de espera.",
        {"intencion": "soporte", "prioridad": "alta"},
    ),
    (
        "¿Dónde puedo revisar el registro de trazas de las últimas interacciones del agente?",
        {"intencion": "soporte", "prioridad": "baja"},
    ),
]


def build_tuning_examples(
    raw_examples: list[tuple[str, dict[str, Any]]] = RAW_EXAMPLES,
) -> list[types.TuningExample]:
    """Convierte pares (entrada, dict salida) en objetos TuningExample del SDK."""
    return [
        types.TuningExample(
            text_input=text,
            output=json.dumps(output_obj, ensure_ascii=False),
        )
        for text, output_obj in raw_examples
    ]


def check_balance(
    raw_examples: list[tuple[str, dict[str, Any]]] = RAW_EXAMPLES,
    key: str = "intencion",
) -> Counter[str]:
    """Cuenta cuántos ejemplos existen por cada categoría para detectar desbalances."""
    return Counter(str(output_obj[key]) for _, output_obj in raw_examples)


def validate_dataset(
    examples: list[types.TuningExample],
    expected_keys: tuple[str, ...] = EXPECTED_KEYS,
) -> list[str]:
    """Valida todos los ejemplos localmente y reporta todos los problemas encontrados."""
    problems: list[str] = []
    seen_inputs: set[str] = set()

    for index, example in enumerate(examples):
        text_in = example.text_input
        text_out = example.output

        if not text_in or not text_in.strip():
            problems.append(f"ejemplo {index}: text_input vacío")
        else:
            normalized = text_in.strip()
            if normalized in seen_inputs:
                problems.append(f"ejemplo {index}: text_input duplicado")
            seen_inputs.add(normalized)

        if not text_out or not text_out.strip():
            problems.append(f"ejemplo {index}: output vacío")
            continue

        try:
            parsed = json.loads(text_out)
        except json.JSONDecodeError:
            problems.append(f"ejemplo {index}: output no es JSON válido")
            continue

        if not isinstance(parsed, dict):
            problems.append(f"ejemplo {index}: output JSON debe ser un objeto")
            continue

        for key in expected_keys:
            if key not in parsed:
                problems.append(f'ejemplo {index}: output no tiene la clave "{key}"')

    return problems


def estimate_labeling_cost(
    num_examples: int,
    minutes_per_example: float,
    hourly_rate_usd: float,
    review_fraction: float = 0.0,
    review_minutes: float = 0.0,
) -> dict[str, float]:
    """Estima horas, costo humano y jornadas de 8 h para etiquetar y revisar un dataset."""
    base_hours = (num_examples * minutes_per_example) / 60.0
    base_cost = base_hours * hourly_rate_usd
    review_hours = (num_examples * review_fraction * review_minutes) / 60.0
    review_cost = review_hours * hourly_rate_usd
    total_hours = base_hours + review_hours
    total_cost = base_cost + review_cost
    return {
        "base_hours": round(base_hours, 2),
        "base_cost_usd": round(base_cost, 2),
        "review_hours": round(review_hours, 2),
        "review_cost_usd": round(review_cost, 2),
        "total_hours": round(total_hours, 2),
        "total_cost_usd": round(total_cost, 2),
        "workdays_8h": round(total_hours / 8.0, 2),
    }


def main() -> None:
    """Construye el dataset, revisa balance, valida y verifica detección de errores."""
    examples = build_tuning_examples()
    balance = check_balance()
    problems = validate_dataset(examples)

    print(f"Ejemplos construidos: {len(examples)}")
    print("Balance por intención:")
    for category, count in balance.most_common():
        print(f"  - {category}: {count}")
    ratio = max(balance.values()) / min(balance.values())
    print(f"Razón max/min: {ratio:.2f}x")
    print(f"Validación del dataset limpio: {len(problems)} problemas encontrados")

    # Prueba forzada: el validador debe detectar errores reales
    broken = examples + [
        types.TuningExample(text_input="", output='{"intencion": "notas"}'),
        types.TuningExample(text_input=RAW_EXAMPLES[0][0], output="{'intencion': 'notas'}"),
    ]
    broken_problems = validate_dataset(broken)
    print(f"Prueba con ejemplos rotos: {len(broken_problems)} problemas detectados")
    for issue in broken_problems:
        print(f"  - {issue}")


if __name__ == "__main__":
    main()
