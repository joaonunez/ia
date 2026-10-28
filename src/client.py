"""Cliente modular del asistente.

Clasifica el HTTP, reintenta solo lo momentáneo y anota el costo
después de cada respuesta válida. Los nombres del fuente están en
inglés; los comentarios y lo que lee el modelo, en español.
"""
import random
import time
from collections.abc import Callable
from typing import Any

import requests

from gemini_api import build_request, calculate_cost, extract_text

DEFAULT_MODEL = "gemini-3.5-flash-lite"
# Precios de flash-lite en USD por token. Consultados el 2026-10-21.
INPUT_USD_PER_TOKEN = 0.30 / 1_000_000
OUTPUT_USD_PER_TOKEN = 2.50 / 1_000_000

session_cost_usd = 0.0


def post_generation(url: str, headers: dict, body: dict) -> dict:
    """Una llamada a generateContent.

    401 y 403 son una credencial mala: no se reintentan.
    429, 5xx y un corte de red son momentáneos: el reintento sí aplica.
    """
    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")

    if response.status_code in (401, 403):
        raise ValueError("Credencial inválida o sin permiso. Revisa tu API_KEY.")
    if response.status_code == 429 or response.status_code >= 500:
        raise TimeoutError(
            "El proveedor no pudo procesar la petición. Hay que esperar y reintentar."
        )

    response.raise_for_status()
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")


def with_retry(
    operation: Callable[[], Any],
    attempts: int = 3,
    base_wait_seconds: float = 2,
    max_wait_seconds: float = 30,
) -> Any:
    """Reintenta solo TimeoutError. ValueError pasa de inmediato.

    La espera crece al doble en cada intento y se detiene en 30 s.
    El jitter evita que varios procesos despierten juntos.
    """
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except TimeoutError:
            if attempt == attempts:
                raise
            wait = min(base_wait_seconds * (2 ** (attempt - 1)), max_wait_seconds)
            wait_with_jitter = wait + random.uniform(0, wait * 0.1)
            print(
                f"Intento {attempt} de {attempts} falló. "
                f"Reintentando en {wait_with_jitter:.1f}s..."
            )
            time.sleep(wait_with_jitter)


def record_cost(response: dict) -> float:
    """Suma el costo de una respuesta que sí llegó. Una falla no suma."""
    global session_cost_usd
    cost = calculate_cost(response, INPUT_USD_PER_TOKEN, OUTPUT_USD_PER_TOKEN)
    session_cost_usd += cost
    usage = response.get("usageMetadata", {})
    total_tokens = usage.get("totalTokenCount", 0)
    print(
        f"Operación: {total_tokens} tokens, "
        f"costo estimado: ${cost:.5f} "
        f"(acumulado: ${session_cost_usd:.5f})"
    )
    return cost


def ask_model(
    question: str,
    system_instruction: str | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Pregunta al modelo, reintenta lo momentáneo y devuelve el texto.

    Si se agotan los reintentos, el mensaje es para la persona, no el 429.
    Una credencial mala no se convierte en ese mensaje.
    """
    url, headers, body = build_request(question, model, system_instruction)
    try:
        response = with_retry(lambda: post_generation(url, headers, body))
    except TimeoutError:
        raise RuntimeError(
            "El servicio no respondió tras varios intentos. Intenta más tarde."
        )
    record_cost(response)
    return extract_text(response)
