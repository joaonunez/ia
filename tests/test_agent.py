"""Pruebas del agente. Ninguna llama al proveedor real.

Un modelo falso con guion hace de Gemini: devuelve, turno a turno, la
llamada a una herramienta o la respuesta final. Así se verifica qué
herramienta elige el agente leyendo `intermediate_steps`, sin depender
de que un modelo real razone igual cada vez.
"""
import itertools
import json
from unittest.mock import MagicMock

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from agent import (
    EMPTY_REPLY,
    ERROR_REPLY,
    MAX_ITERATIONS,
    ask_agent,
    build_agent,
    build_tools,
    content_to_text,
)


class ScriptedModel(GenericFakeChatModel):
    """Modelo falso que acepta `bind_tools`, como exige el agente.

    Sin streaming: el modelo falso de LangChain no sabe trocear una
    llamada a herramienta que no trae texto.
    """

    disable_streaming: bool = True

    def bind_tools(self, tools, **kwargs):
        return self


def call(tool: str, arguments: dict, call_id: str = "call_1") -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": tool, "args": arguments, "id": call_id, "type": "tool_call"}],
    )


def scripted(*messages) -> ScriptedModel:
    return ScriptedModel(messages=iter(messages))


@pytest.fixture
def approvals(tmp_path):
    return tmp_path / "approvals.jsonl"


@pytest.fixture
def traces(tmp_path):
    return tmp_path / "traces.jsonl"


def make_agent(model, approvals, approve=lambda prompt: True):
    return build_agent(model, approve=approve, approval_path=approvals)


def steps_of(agent, session_id, message):
    """Corre el agente y devuelve (salida, pasos intermedios)."""
    result = agent.invoke({"input": message}, {"configurable": {"session_id": session_id}})
    return result["output"], result["intermediate_steps"]


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# Herramientas, directamente


def tools_by_name(approve=lambda prompt: True, approval_path=None):
    return {t.name: t for t in build_tools(approve, approval_path)}


def test_get_grades_finds_a_student_ignoring_case():
    tools = tools_by_name()
    assert tools["get_grades"].invoke({"student_name": "  diego SOTO "}) == "Diego Soto tiene promedio 3.7."


def test_get_grades_reports_an_unknown_student_instead_of_failing():
    assert "No se encontró" in tools_by_name()["get_grades"].invoke({"student_name": "Nadie"})


def test_get_attendance_adds_absences_only_when_asked():
    tools = tools_by_name()
    plain = tools["get_attendance"].invoke({"student_name": "Diego Soto"})
    detailed = tools["get_attendance"].invoke({"student_name": "Diego Soto", "include_absences": True})
    assert plain == "Diego Soto tiene 72% de asistencia."
    assert "11 días de inasistencia" in detailed


def test_args_schema_rejects_a_value_of_the_wrong_type():
    with pytest.raises(ValidationError):
        tools_by_name()["get_attendance"].invoke({"student_name": "Diego Soto", "include_absences": "tal vez"})


def test_notice_is_sent_only_after_approval_and_the_decision_is_recorded(approvals):
    approve = MagicMock(return_value=True)
    tools = tools_by_name(approve, approvals)
    result = tools["send_guardian_notice"].invoke({"student_name": "Diego Soto", "reason": "promedio bajo"})
    assert "simulado" in result
    approve.assert_called_once()
    assert read_lines(approvals)[0]["approved"] is True


def test_notice_is_not_sent_when_the_supervisor_rejects_it(approvals):
    tools = tools_by_name(lambda prompt: False, approvals)
    result = tools["send_guardian_notice"].invoke({"student_name": "Diego Soto", "reason": "promedio bajo"})
    assert "no aprobado" in result.lower()
    assert "simulado" not in result
    assert read_lines(approvals)[0]["approved"] is False


def test_unknown_student_never_asks_for_approval(approvals):
    approve = MagicMock(return_value=True)
    tools = tools_by_name(approve, approvals)
    result = tools["send_guardian_notice"].invoke({"student_name": "Nadie", "reason": "x"})
    assert "No se encontró" in result
    approve.assert_not_called()
    assert not approvals.exists()


# Elección de herramienta por el agente


def test_agent_picks_the_grades_tool_for_a_grades_question(approvals):
    agent, _ = make_agent(
        scripted(call("get_grades", {"student_name": "Diego Soto"}), AIMessage(content="Diego Soto tiene 3.7.")),
        approvals,
    )
    output, steps = steps_of(agent, "s1", "¿Qué promedio tiene Diego Soto?")
    assert [action.tool for action, _ in steps] == ["get_grades"]
    assert steps[0][0].tool_input == {"student_name": "Diego Soto"}
    assert output == "Diego Soto tiene 3.7."


def test_agent_picks_the_attendance_tool_with_its_optional_argument(approvals):
    agent, _ = make_agent(
        scripted(
            call("get_attendance", {"student_name": "Diego Soto", "include_absences": True}),
            AIMessage(content="Tiene 11 días de inasistencia."),
        ),
        approvals,
    )
    _, steps = steps_of(agent, "s1", "¿Cuántos días faltó Diego Soto?")
    assert steps[0][0].tool == "get_attendance"
    assert "11 días" in steps[0][1]


def test_agent_uses_no_tool_for_a_general_question(approvals):
    agent, _ = make_agent(scripted(AIMessage(content="No tengo ese dato.")), approvals)
    output, steps = steps_of(agent, "s1", "¿Cómo se llama el director?")
    assert steps == []
    assert output == "No tengo ese dato."


def test_agent_chains_two_tools_using_the_first_result(approvals):
    agent, _ = make_agent(
        scripted(
            call("get_grades", {"student_name": "Marta Díaz"}, "c1"),
            call("get_attendance", {"student_name": "Marta Díaz"}, "c2"),
            AIMessage(content="Promedio 4.8 y 81% de asistencia."),
        ),
        approvals,
    )
    _, steps = steps_of(agent, "s1", "Dame notas y asistencia de Marta Díaz")
    assert [action.tool for action, _ in steps] == ["get_grades", "get_attendance"]


# Supervisión dentro del agente


def test_agent_does_not_send_a_notice_the_supervisor_rejected(approvals):
    agent, _ = make_agent(
        scripted(
            call("send_guardian_notice", {"student_name": "Diego Soto", "reason": "promedio bajo"}),
            AIMessage(content="No se envió el aviso."),
        ),
        approvals,
        approve=lambda prompt: False,
    )
    _, steps = steps_of(agent, "s1", "Avisa al apoderado de Diego Soto")
    assert "no aprobado" in steps[0][1].lower()
    assert read_lines(approvals)[0]["approved"] is False


# Memoria


def test_second_turn_receives_the_first_turn_in_its_prompt(approvals):
    model = scripted(AIMessage(content="Es Diego Soto."), AIMessage(content="Tiene 3.7."))
    agent, _ = make_agent(model, approvals)
    steps_of(agent, "s1", "Hablemos de Diego Soto.")
    # Se inspecciona el prompt de la segunda llamada al modelo.
    captured = []
    original = model._generate

    def spy(messages, *args, **kwargs):
        captured.append(" ".join(str(m.content) for m in messages))
        return original(messages, *args, **kwargs)

    model._generate = spy
    steps_of(agent, "s1", "¿Y su promedio?")
    assert "Hablemos de Diego Soto." in captured[0]
    assert "Es Diego Soto." in captured[0]


def test_two_sessions_do_not_share_history(approvals):
    model = scripted(AIMessage(content="uno"), AIMessage(content="dos"), AIMessage(content="tres"))
    agent, histories = make_agent(model, approvals)
    steps_of(agent, "cliente_1", "Pregunto por Diego Soto.")
    steps_of(agent, "cliente_2", "¿De quién te pregunté?")
    contents_2 = " ".join(str(m.content) for m in histories["cliente_2"].messages)
    assert "Diego Soto" not in contents_2
    assert len(histories["cliente_1"].messages) == 2
    assert len(histories["cliente_2"].messages) == 2


# Límite de autonomía


def test_agent_stops_after_the_iteration_limit(approvals):
    endless = ScriptedModel(
        messages=(
            call("get_grades", {"student_name": "Ana Rojas"}, f"c{n}") for n in itertools.count()
        )
    )
    agent, _ = make_agent(endless, approvals)
    output, steps = steps_of(agent, "s1", "Consulta sin fin")
    assert len(steps) == MAX_ITERATIONS
    assert "max iterations" in output.lower() or "time limit" in output.lower()


# Contenido en bloques (formato real de Gemini)


@pytest.mark.parametrize(
    "content, expected",
    [
        ("hola", "hola"),
        ([{"type": "text", "text": "Tiene 3.7.", "extras": {"signature": "abc"}}], "Tiene 3.7."),
        ([{"type": "text", "text": "Uno. "}, {"type": "text", "text": "Dos."}], "Uno. Dos."),
        (["suelto"], "suelto"),
        ([], ""),
    ],
)
def test_content_to_text(content, expected):
    assert content_to_text(content) == expected


def test_memory_survives_a_model_that_answers_with_content_blocks(approvals):
    """Reproduce el fallo visto con Gemini real: la respuesta llega como lista de bloques."""
    block = [{"type": "text", "text": "Diego Soto tiene 3.7.", "extras": {"signature": "abc"}}]
    agent, histories = make_agent(scripted(AIMessage(content=block), AIMessage(content="Sí.")), approvals)
    output_1, _ = steps_of(agent, "s1", "¿Promedio de Diego Soto?")
    output_2, _ = steps_of(agent, "s1", "¿Y es bajo?")
    assert output_1 == "Diego Soto tiene 3.7."
    assert output_2 == "Sí."
    assert len(histories["s1"].messages) == 4


# Entrada segura


def test_ask_agent_records_the_trace_and_returns_the_answer(approvals, traces):
    agent, _ = make_agent(
        scripted(call("get_grades", {"student_name": "Ana Rojas"}), AIMessage(content="Ana tiene 6.1.")),
        approvals,
    )
    answer = ask_agent(agent, "s1", "¿Promedio de Ana Rojas?", trace_path=traces)
    assert answer == "Ana tiene 6.1."
    [record] = read_lines(traces)
    assert record["actions"][0]["tool"] == "get_grades"
    assert record["session_id"] == "s1"


def test_ask_agent_does_not_propagate_failures(approvals, traces):
    class FailingModel(ScriptedModel):
        def _generate(self, *args, **kwargs):
            raise ConnectionError("simulado")

    agent, _ = make_agent(FailingModel(messages=iter([])), approvals)
    assert ask_agent(agent, "s1", "hola", trace_path=traces) == ERROR_REPLY
    assert not traces.exists()


@pytest.mark.parametrize("message", ["", "   ", None, 7])
def test_ask_agent_rejects_empty_messages_without_calling_the_agent(message):
    agent = MagicMock()
    assert ask_agent(agent, "s1", message) == EMPTY_REPLY
    agent.invoke.assert_not_called()
