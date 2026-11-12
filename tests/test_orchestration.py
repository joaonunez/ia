"""Pruebas de la chain orquestada. Ninguna llama al proveedor real.

Cubren las cuatro filas del checklist del Bloque 20: clasificación,
bifurcación, cada ruta de destino y el flujo completo.
"""
import logging
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from routing import (
    ATTENDANCE_PROMPT,
    EMPTY_REPLY,
    ERROR_REPLY,
    FALLBACK_REPLY,
    GRADES_PROMPT,
    OTHER_PROMPT,
    build_chain,
    build_classification_step,
    build_route,
    build_routed_chain,
    normalize_category,
    process_message_safely,
)

INPUT = {"message": "¿quién está bajo 4.0?", "context": "{}"}


def fake_classification(category: str) -> MagicMock:
    """Fuerza la categoría sin importar qué modelo haya detrás.

    Se configura `return_value` en el mock y no `invoke.return_value`:
    LangChain llama al mock como una función común dentro de la chain.
    """
    step = MagicMock()
    step.return_value = category
    return step


def fake_route(reply: str) -> MagicMock:
    route = MagicMock()
    route.return_value = reply
    return route


def failing(x):
    raise ConnectionError("simulado")


# Clasificación


@pytest.mark.parametrize(
    "raw, expected",
    [
        (" Notas \n", "notas"),
        ("Asistencia.", "asistencia"),
        ('"otro"', "otro"),
        ("", ""),
    ],
)
def test_normalize_category(raw, expected):
    assert normalize_category(raw) == expected


def test_classification_normalizes_before_comparing():
    model = MagicMock()
    model.return_value = AIMessage(content=" Notas. \n")
    result = build_classification_step(model).invoke({"message": "algo"})
    assert result == "notas"


# Bifurcación


def test_routes_to_grades():
    grades = fake_route("respuesta de notas")
    chain = build_routed_chain(fake_classification("notas"), grades_route=grades)
    assert chain.invoke(INPUT) == "respuesta de notas"
    assert grades.called


def test_routes_to_attendance():
    attendance = fake_route("respuesta de asistencia")
    chain = build_routed_chain(
        fake_classification("asistencia"), attendance_route=attendance
    )
    assert chain.invoke(INPUT) == "respuesta de asistencia"
    assert attendance.called


def test_routes_to_default_on_known_other_category():
    default = fake_route("respuesta por defecto")
    chain = build_routed_chain(fake_classification("otro"), default_route=default)
    assert chain.invoke(INPUT) == "respuesta por defecto"


def test_routes_to_default_on_unknown_category():
    """Una categoría inventada no lanza error: cae en la ruta por defecto."""
    grades = fake_route("no debe ejecutarse")
    default = fake_route("respuesta por defecto")
    chain = build_routed_chain(
        fake_classification("categoria_inventada"),
        grades_route=grades,
        default_route=default,
    )
    assert chain.invoke(INPUT) == "respuesta por defecto"
    assert not grades.called


# Rutas de destino


def test_each_route_uses_a_different_prompt():
    prompts = {GRADES_PROMPT, ATTENDANCE_PROMPT, OTHER_PROMPT}
    assert len(prompts) == 3


def test_route_falls_back_when_the_model_fails():
    model = MagicMock()
    model.side_effect = ConnectionError("simulado")
    route = build_route(GRADES_PROMPT, model)
    assert route.invoke({**INPUT, "category": "notas"}) == FALLBACK_REPLY


def test_route_falls_back_when_only_the_review_fails():
    """Si la revisión falla, no se entrega la respuesta sin revisar."""
    model = MagicMock()
    model.side_effect = [AIMessage(content="borrador"), ConnectionError("simulado")]
    route = build_route(GRADES_PROMPT, model)
    assert route.invoke({**INPUT, "category": "notas"}) == FALLBACK_REPLY


def test_fallback_runs_the_given_alternative():
    """Un fallo forzado confirma que with_fallbacks sí ejecuta la alternativa."""
    safe = RunnableLambda(failing).with_fallbacks(
        [RunnableLambda(lambda _: "respaldo")]
    )
    assert safe.invoke(INPUT) == "respaldo"


# Flujo completo


def test_full_chain_runs_the_three_steps_in_order():
    model = MagicMock()
    model.side_effect = [
        AIMessage(content="notas"),
        AIMessage(content="Diego Soto tiene 3.7."),
        AIMessage(content="Diego Soto tiene el promedio más bajo: 3.7."),
    ]
    context = '{"estudiantes": [{"nombre": "Diego Soto", "promedio": 3.7}]}'
    result = build_chain(model).invoke({"message": "¿quién está bajo 4.0?", "context": context})

    assert model.call_count == 3
    assert result == "Diego Soto tiene el promedio más bajo: 3.7."

    prompts = [call.args[0].to_string() for call in model.call_args_list]
    assert "¿quién está bajo 4.0?" in prompts[0]
    # La ruta de notas ve el mensaje y el contexto; la revisión ve la respuesta.
    assert "Diego Soto" in prompts[1] and "¿quién está bajo 4.0?" in prompts[1]
    assert "Diego Soto tiene 3.7." in prompts[2] and "Diego Soto" in prompts[2]


def test_full_chain_falls_back_when_a_route_fails():
    model = MagicMock()
    model.side_effect = [AIMessage(content="asistencia"), ConnectionError("simulado")]
    result = process_message_safely(build_chain(model), "¿quién falta mucho?", "{}")
    assert result == FALLBACK_REPLY


def test_process_message_safely_does_not_propagate_exceptions():
    """Un fallo en la clasificación ocurre antes de elegir ruta: solo lo cubre el try/except general."""
    classification = MagicMock()
    classification.side_effect = ConnectionError("simulado")
    chain = build_routed_chain(classification)
    result = process_message_safely(chain, "mensaje de prueba")
    assert result == ERROR_REPLY


def test_process_message_safely_logs_the_error_without_the_message(caplog):
    classification = MagicMock()
    classification.side_effect = ConnectionError("simulado")
    chain = build_routed_chain(classification)
    with caplog.at_level(logging.ERROR, logger="routing"):
        process_message_safely(chain, "consulta sobre Diego Soto")
    assert "ConnectionError" in caplog.text
    assert "Diego Soto" not in caplog.text


@pytest.mark.parametrize("message", ["", "   ", None, 42])
def test_empty_or_invalid_message_does_not_call_the_chain(message):
    chain = MagicMock()
    assert process_message_safely(chain, message) == EMPTY_REPLY
    chain.invoke.assert_not_called()
