"""Pruebas del cliente modular. Ninguna llama al proveedor real."""
from unittest.mock import Mock, patch

import pytest

import client
from client import (
    INPUT_USD_PER_TOKEN,
    OUTPUT_USD_PER_TOKEN,
    ask_model,
    post_generation,
    record_cost,
    with_retry,
)


@pytest.fixture(autouse=True)
def reset_session_cost():
    client.session_cost_usd = 0.0
    yield
    client.session_cost_usd = 0.0


@pytest.mark.parametrize("status_code", [401, 403])
def test_post_generation_invalid_credentials(status_code):
    fake = Mock()
    fake.status_code = status_code
    with patch("client.requests.post", return_value=fake):
        with pytest.raises(ValueError):
            post_generation("https://example.test", {}, {})


@pytest.mark.parametrize("status_code", [429, 500])
def test_post_generation_rate_limit(status_code):
    fake = Mock()
    fake.status_code = status_code
    with patch("client.requests.post", return_value=fake):
        with pytest.raises(TimeoutError):
            post_generation("https://example.test", {}, {})


def test_post_generation_success():
    fake = Mock()
    fake.status_code = 200
    fake.json.return_value = {"candidates": []}
    with patch("client.requests.post", return_value=fake):
        data = post_generation("https://example.test", {}, {})
    assert data == {"candidates": []}


def test_with_retry_exhausts_attempts():
    operation = Mock(side_effect=TimeoutError("simulado"))
    with patch("client.time.sleep") as sleep:
        with pytest.raises(TimeoutError):
            with_retry(operation, attempts=3, base_wait_seconds=2)
    assert operation.call_count == 3
    assert sleep.call_count == 2


def test_with_retry_does_not_retry_value_error():
    operation = Mock(side_effect=ValueError("credencial"))
    with patch("client.time.sleep") as sleep:
        with pytest.raises(ValueError):
            with_retry(operation, attempts=3)
    assert operation.call_count == 1
    sleep.assert_not_called()


def test_record_cost_accumulates():
    response = {
        "usageMetadata": {
            "promptTokenCount": 800,
            "candidatesTokenCount": 200,
            "totalTokenCount": 1000,
        }
    }
    expected = 800 * INPUT_USD_PER_TOKEN + 200 * OUTPUT_USD_PER_TOKEN
    first = record_cost(response)
    second = record_cost(response)
    assert first == pytest.approx(expected)
    assert second == pytest.approx(expected)
    assert client.session_cost_usd == pytest.approx(expected * 2)


def test_ask_model_converts_error(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    with patch("client.with_retry", side_effect=TimeoutError("simulado")):
        with pytest.raises(RuntimeError, match="varios intentos"):
            ask_model("pregunta de prueba")


def test_ask_model_lets_value_error_through(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    with patch("client.with_retry", side_effect=ValueError("credencial")):
        with pytest.raises(ValueError):
            ask_model("pregunta de prueba")
