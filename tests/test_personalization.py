"""Pruebas unitarias exhaustivas de U2.6 (Bloques 29 y 30), sin llamadas a la API.

Valida el dataset propio para PEFT (tamaño, balance, detección forzada de
errores, estimación de costos de etiquetado), el método puntuable de decisión
(ganador claro, empates explícitos, validación de tipos, análisis de
sensibilidad) y la completitud de `docs/decision-personalizacion.md`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from google.genai import types

from personalization_decision import (
    PROJECT_ANSWERS,
    build_decision_skeleton,
    recommend_strategy,
    sensitivity_analysis,
)
from tuning_dataset import (
    EXPECTED_KEYS,
    RAW_EXAMPLES,
    build_tuning_examples,
    check_balance,
    estimate_labeling_cost,
    validate_dataset,
)

DECISION_DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "decision-personalizacion.md"


# --- Bloque 29: dataset propio, balance y validador ---


def test_dataset_has_at_least_ten_valid_and_balanced_examples():
    examples = build_tuning_examples(RAW_EXAMPLES)
    assert len(examples) >= 10

    balance = check_balance(RAW_EXAMPLES, key="intencion")
    assert len(balance) >= 3
    ratio = max(balance.values()) / min(balance.values())
    assert ratio <= 2.0

    problems = validate_dataset(examples, expected_keys=EXPECTED_KEYS)
    assert problems == []

    # Cada output debe parsear como JSON con exactamente las claves esperadas
    for example in examples:
        parsed = json.loads(example.output)
        assert set(EXPECTED_KEYS).issubset(parsed.keys())


def test_validate_dataset_reports_all_errors_on_broken_examples():
    valid = build_tuning_examples(RAW_EXAMPLES[:2])
    broken = valid + [
        types.TuningExample(text_input="", output='{"intencion": "notas"}'),
        types.TuningExample(text_input=RAW_EXAMPLES[0][0], output="{'intencion': 'notas'}"),
        types.TuningExample(text_input="Caso sin salida", output="   "),
    ]
    problems = validate_dataset(broken, expected_keys=EXPECTED_KEYS)

    # Debe reportar todos los fallos acumulados, no detenerse en el primero
    assert any("text_input vacío" in p for p in problems)
    assert any('no tiene la clave "prioridad"' in p for p in problems)
    assert any("text_input duplicado" in p for p in problems)
    assert any("no es JSON válido" in p for p in problems)
    assert any("output vacío" in p for p in problems)


# --- Bloque 30: costos de etiquetado, método de decisión y sensibilidad ---


def test_estimate_labeling_cost_matches_block_30_reference_exercise():
    # Ejercicio oficial del Bloque 30: 500 ejemplos, 4 min, USD 20/h, 20% revisión de 2 min
    result = estimate_labeling_cost(
        num_examples=500,
        minutes_per_example=4,
        hourly_rate_usd=20,
        review_fraction=0.20,
        review_minutes=2,
    )
    assert result["base_hours"] == pytest.approx(33.33)
    assert result["base_cost_usd"] == pytest.approx(666.67)
    assert result["review_hours"] == pytest.approx(3.33)
    assert result["review_cost_usd"] == pytest.approx(66.67)
    assert result["total_hours"] == pytest.approx(36.67)
    assert result["total_cost_usd"] == pytest.approx(733.33)
    assert result["workdays_8h"] == pytest.approx(4.58)


def test_recommend_strategy_reports_clear_winner_for_project():
    scores, winners = recommend_strategy(PROJECT_ANSWERS)
    assert scores == {"RAG": 5, "Fine-tuning completo": 0, "PEFT": 1}
    assert winners == ["RAG"]


def test_recommend_strategy_exposes_ties_instead_of_hiding_them():
    tie_case = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }
    scores, winners = recommend_strategy(tie_case)
    assert scores == {"RAG": 0, "Fine-tuning completo": 3, "PEFT": 3}
    assert set(winners) == {"Fine-tuning completo", "PEFT"}


def test_recommend_strategy_rejects_none_and_non_boolean_strings():
    with_none = {**PROJECT_ANSWERS, "informacion_cambia_seguido": None}
    with pytest.raises(ValueError, match="None"):
        recommend_strategy(with_none)  # type: ignore[arg-type]

    with_string = {**PROJECT_ANSWERS, "informacion_cambia_seguido": "si"}
    with pytest.raises(TypeError, match="bool"):
        recommend_strategy(with_string)  # type: ignore[arg-type]


def test_sensitivity_analysis_detects_fragile_tie_and_stable_project():
    tie_case = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }
    tie_sensitivity = sensitivity_analysis(tie_case)
    assert len(tie_sensitivity) == 5
    # En el empate 3-3 del Bloque 30, las 5 preguntas cambian el resultado
    assert all(row["changed"] for row in tie_sensitivity)

    project_sensitivity = sensitivity_analysis(PROJECT_ANSWERS)
    assert len(project_sensitivity) == 5
    # En nuestro proyecto RAG gana con holgura y ninguna inversión individual cambia el ganador
    assert all(not row["changed"] for row in project_sensitivity)


def test_build_decision_skeleton_handles_winner_and_tie():
    skeleton_tie = build_decision_skeleton(
        "Problema de prueba.",
        {"RAG": 0, "Fine-tuning completo": 3, "PEFT": 3},
        ["Fine-tuning completo", "PEFT"],
    )
    assert "**Empate entre: Fine-tuning completo, PEFT**" in skeleton_tie
    assert "## 1. El problema" in skeleton_tie
    assert "## 4. Qué necesitarías para ejecutarla" in skeleton_tie


def test_decision_document_is_complete_ordered_and_has_concrete_numbers():
    assert DECISION_DOC_PATH.exists()
    content = DECISION_DOC_PATH.read_text(encoding="utf-8")

    # No debe quedar ningún marcador sin completar
    assert "[COMPLETAR" not in content

    # Las 4 secciones obligatorias en orden
    positions = [
        content.index("## 1. El problema"),
        content.index("## 2. Resultado del método de decisión"),
        content.index("## 3. Técnica elegida y por qué"),
        content.index("## 4. Qué necesitarías para ejecutarla"),
    ]
    assert positions == sorted(positions)

    # La sección 4 debe contener cifras concretas (no solo vaguedades)
    section_4 = content[positions[3] :]
    numbers = re.findall(r"\b\d+\b", section_4)
    assert len(numbers) >= 4
