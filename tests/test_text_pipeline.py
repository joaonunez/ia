"""Pruebas del pipeline y de la métrica. Ninguna llama al proveedor."""
import pytest

from text_metrics import calculate_metrics, count_matches, overlap_ratio, precision_recall_f1
from text_pipeline import clean_text, process_text, vectorize


def test_process_text_normalizes_case_and_punctuation():
    assert process_text("El Cielo, es AZUL!") == ["el", "cielo", "es", "azul"]


def test_process_text_only_punctuation_returns_empty_list():
    assert process_text("¡¡¡...!!!") == []


def test_clean_text_rejects_non_text():
    with pytest.raises(TypeError):
        clean_text(None)


def test_clean_text_keeps_numbers_and_spanish_letters():
    assert clean_text("Tiene 3 gatos y una Ñ.") == "tiene 3 gatos y una ñ"


def test_vectorize_counts_repeats():
    counts = vectorize(["el", "gato", "el"])
    assert counts["el"] == 2
    assert counts["gato"] == 1


def test_raw_split_punishes_format_and_pipeline_does_not():
    reference = "El cielo es azul."
    response = "el cielo es azul"
    raw = overlap_ratio(reference.split(), response.split())
    processed = overlap_ratio(process_text(reference), process_text(response))
    assert raw == pytest.approx(0.5)
    assert processed == pytest.approx(1.0)


def test_same_words_in_another_order_still_match():
    reference = process_text("El perro persiguió al gato.")
    response = process_text("El gato persiguió al perro.")
    assert overlap_ratio(reference, response) == pytest.approx(1.0)
    assert precision_recall_f1(reference, response)["f1"] == pytest.approx(1.0)


def test_count_matches_caps_extra_repeats():
    assert count_matches(["el", "gato"], ["el", "gato", "el", "gato"]) == 2


def test_synonyms_score_half():
    result = calculate_metrics("El auto es veloz.", "El vehículo es rápido.")
    assert result["f1"] == pytest.approx(0.5)


def test_wrong_year_still_scores_high():
    result = calculate_metrics("Python fue creado en 1991.", "Python fue creado en 1989.")
    assert result["precision"] == pytest.approx(0.8)
    assert result["f1"] == pytest.approx(0.8)


def test_missing_negation_scores_almost_perfect():
    result = calculate_metrics(
        "Python no es un lenguaje compilado.",
        "Python es un lenguaje compilado.",
    )
    assert result["precision"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(5 / 6)
    assert result["f1"] == pytest.approx(0.9090909090909091)


def test_empty_text_returns_zeros():
    assert precision_recall_f1([], ["python"]) == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert calculate_metrics("¡¡¡", "Python es un lenguaje.")["f1"] == 0.0
