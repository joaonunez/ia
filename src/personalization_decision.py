"""Método puntuable y análisis de sensibilidad para decidir estrategia de personalización (U2.6 · Bloque 30).

Evalúa RAG, Fine-tuning completo y PEFT a partir de cinco criterios
booleanos verificables, reportando empates explícitamente (sin ocultarlos).
"""
from __future__ import annotations

from typing import Any

REQUIRED_KEYS: tuple[str, ...] = (
    "informacion_cambia_seguido",
    "problema_de_formato_o_tono",
    "dataset_grande_y_de_calidad",
    "presupuesto_limitado_o_iterar_rapido",
    "necesita_multiples_variantes",
)

# Respuestas reales del proyecto "Asistente del gestor académico" con evidencia.
PROJECT_ANSWERS: dict[str, bool] = {
    # Reglamentos internos, circulares, calendarios y políticas escolares cambian cada mes/trimestre.
    "informacion_cambia_seguido": True,
    # En 20 respuestas medidas (U2.2) + 4 corridas RAG (U2.5) + schema JSON (U1.5), <15 % falló formato.
    "problema_de_formato_o_tono": False,
    # Tenemos 12 ejemplos validados en src/tuning_dataset.py (umbral: >= 200 ejemplos).
    "dataset_grande_y_de_calidad": False,
    # Nivel gratuito de Gemini y necesidad de reflejar cambios normativos en minutos (< 1 día).
    "presupuesto_limitado_o_iterar_rapido": True,
    # Un solo asistente base con RAG filtrado por metadatos cubre el MVP actual.
    "necesita_multiples_variantes": False,
}


def validate_answers(answers: dict[str, Any]) -> None:
    """Exige que estén las 5 claves y que todos los valores sean bool reales."""
    missing = [key for key in REQUIRED_KEYS if key not in answers]
    if missing:
        raise ValueError(f"Faltan claves obligatorias en answers: {missing}")

    for key in REQUIRED_KEYS:
        value = answers[key]
        if value is None:
            raise ValueError(
                f'La clave "{key}" está en None. Completa con True o False antes de continuar.'
            )
        if not isinstance(value, bool):
            raise TypeError(
                f'La clave "{key}" debe ser bool (True/False), no {type(value).__name__}.'
            )


def recommend_strategy(answers: dict[str, bool]) -> tuple[dict[str, int], list[str]]:
    """Calcula puntajes para RAG, Fine-tuning completo y PEFT, conservando empates."""
    validate_answers(answers)

    scores: dict[str, int] = {
        "RAG": 0,
        "Fine-tuning completo": 0,
        "PEFT": 0,
    }
    if answers["informacion_cambia_seguido"]:
        scores["RAG"] += 3
    if answers["problema_de_formato_o_tono"]:
        scores["PEFT"] += 2
        scores["Fine-tuning completo"] += 1
    if answers["dataset_grande_y_de_calidad"]:
        scores["Fine-tuning completo"] += 2
        scores["PEFT"] += 1
    if answers["presupuesto_limitado_o_iterar_rapido"]:
        scores["RAG"] += 2
        scores["PEFT"] += 1
    if answers["necesita_multiples_variantes"]:
        scores["PEFT"] += 2

    top_score = max(scores.values())
    winners = [strategy for strategy, score in scores.items() if score == top_score]
    return scores, winners


def sensitivity_analysis(answers: dict[str, bool]) -> list[dict[str, Any]]:
    """Invierte una respuesta a la vez y reporta si cambian las estrategias ganadoras."""
    _, base_winners = recommend_strategy(answers)
    base_set = set(base_winners)
    results: list[dict[str, Any]] = []

    for key in REQUIRED_KEYS:
        variant = dict(answers)
        variant[key] = not answers[key]
        variant_scores, variant_winners = recommend_strategy(variant)
        results.append(
            {
                "key": key,
                "original": answers[key],
                "flipped_to": variant[key],
                "scores": variant_scores,
                "winners": variant_winners,
                "changed": set(variant_winners) != base_set,
            }
        )
    return results


def build_decision_skeleton(
    problem: str,
    scores: dict[str, int],
    winners: list[str],
) -> str:
    """Genera el esqueleto Markdown de las 4 secciones del documento de decisión."""
    is_tie = len(winners) > 1
    lines = [
        "# Decisión de personalización",
        "",
        "## 1. El problema",
        problem,
        "",
        "## 2. Resultado del método de decisión",
    ]
    for strategy, score in sorted(scores.items(), key=lambda item: -item[1]):
        lines.append(f"- {strategy}: {score} puntos")
    if is_tie:
        lines.append("")
        lines.append(f"**Empate entre: {', '.join(winners)}**")
    lines.extend(["", "## 3. Técnica elegida y por qué"])
    if is_tie:
        lines.append(
            "[COMPLETAR: el puntaje no resolvió el empate solo -- justifica aquí con criterio propio]"
        )
    else:
        lines.append(f"[COMPLETAR: por qué {winners[0]} responde mejor a este caso]")
    lines.extend(
        [
            "",
            "## 4. Qué necesitarías para ejecutarla",
            "[COMPLETAR: corpus faltante o cantidad exacta de ejemplos etiquetados que faltan]",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Ejecuta el método de decisión y el análisis de sensibilidad sobre el proyecto."""
    scores, winners = recommend_strategy(PROJECT_ANSWERS)
    print("Puntajes del proyecto:", scores)
    print("Candidatas ganadoras:", winners)
    print("\nAnálisis de sensibilidad (cambiando una respuesta a la vez):")
    for row in sensitivity_analysis(PROJECT_ANSWERS):
        tag = "CAMBIA" if row["changed"] else "igual"
        print(f"  - {row['key']} -> {row['flipped_to']}: {row['winners']} [{tag}]")


if __name__ == "__main__":
    main()
