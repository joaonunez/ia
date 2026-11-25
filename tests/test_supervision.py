"""Pruebas de la supervisión humana y de las trazas. Ninguna llama al proveedor."""
import json
import threading
import time
from types import SimpleNamespace

import pytest

from supervision import (
    flag_repeated_tools,
    record_approval,
    record_trace,
    wait_for_approval,
)


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def step(tool, arguments=None, observation="ok"):
    """Un par (acción, observación) como los de `intermediate_steps`."""
    return (SimpleNamespace(tool=tool, tool_input=arguments or {}), observation)


# Aprobación


@pytest.mark.parametrize("answer, expected", [("s", True), (" S \n", True), ("n", False), ("sí", False), ("", False)])
def test_wait_for_approval_only_accepts_s(answer, expected):
    assert wait_for_approval("¿Aprobar?", ask=lambda prompt: answer) is expected


def test_wait_for_approval_without_answer_in_time_is_not_approved():
    """Sin respuesta a tiempo la acción no se ejecuta, que es el valor seguro."""
    release = threading.Event()
    started = time.perf_counter()
    approved = wait_for_approval("¿Aprobar?", timeout_seconds=0.05, ask=lambda prompt: release.wait(5) and "s")
    elapsed = time.perf_counter() - started
    release.set()
    assert approved is False
    assert elapsed < 2


def test_wait_for_approval_without_standard_input_is_not_approved():
    def no_stdin(prompt):
        raise EOFError

    assert wait_for_approval("¿Aprobar?", ask=no_stdin) is False


# Registro de aprobaciones


@pytest.mark.parametrize("approved", [True, False])
def test_record_approval_saves_the_decision_either_way(tmp_path, approved):
    path = tmp_path / "approvals.jsonl"
    record_approval("send_guardian_notice", {"student_name": "Diego Soto"}, approved, path=path)
    [record] = read_lines(path)
    assert record["approved"] is approved
    assert record["tool"] == "send_guardian_notice"
    assert record["arguments"] == {"student_name": "Diego Soto"}
    assert record["timestamp"]


# Trazas


def test_record_trace_saves_actions_and_final_answer(tmp_path):
    path = tmp_path / "traces.jsonl"
    result = {
        "output": "Diego Soto tiene 3.7.",
        "intermediate_steps": [step("get_grades", {"student_name": "Diego Soto"}, "Diego Soto tiene promedio 3.7.")],
    }
    record_trace("s1", "¿Promedio de Diego?", result, path=path)
    [record] = read_lines(path)
    assert record["session_id"] == "s1"
    assert record["input"] == "¿Promedio de Diego?"
    assert record["actions"] == [
        {
            "tool": "get_grades",
            "arguments": {"student_name": "Diego Soto"},
            "observation": "Diego Soto tiene promedio 3.7.",
        }
    ]
    assert record["final_answer"] == "Diego Soto tiene 3.7."


def test_record_trace_without_intermediate_steps_leaves_actions_empty(tmp_path):
    path = tmp_path / "traces.jsonl"
    record_trace("s1", "hola", {"output": "hola"}, path=path)
    assert read_lines(path)[0]["actions"] == []


def test_record_trace_keeps_accents(tmp_path):
    path = tmp_path / "traces.jsonl"
    record_trace("s1", "¿Cuántos días?", {"output": "Once días"}, path=path)
    assert "¿Cuántos días?" in path.read_text(encoding="utf-8")


def test_record_trace_appends_one_line_per_call(tmp_path):
    path = tmp_path / "traces.jsonl"
    record_trace("s1", "a", {"output": "a"}, path=path)
    record_trace("s2", "b", {"output": "b"}, path=path)
    assert [r["session_id"] for r in read_lines(path)] == ["s1", "s2"]


# Repeticiones sospechosas


def write_traces(path, sessions):
    for session_id, tools in sessions.items():
        result = {"output": "x", "intermediate_steps": [step(tool) for tool in tools]}
        record_trace(session_id, "q", result, path=path)


def test_flag_repeated_tools_marks_consecutive_repetitions(tmp_path):
    path = tmp_path / "traces.jsonl"
    write_traces(path, {"a": ["get_grades"], "b": ["get_grades", "get_grades"]})
    assert flag_repeated_tools(path) == [("b", "get_grades")]


def test_flag_repeated_tools_ignores_non_consecutive_reuse(tmp_path):
    path = tmp_path / "traces.jsonl"
    write_traces(path, {"a": ["get_grades", "get_attendance", "get_grades"]})
    assert flag_repeated_tools(path) == []


def test_flag_repeated_tools_without_file_returns_nothing(tmp_path):
    assert flag_repeated_tools(tmp_path / "does-not-exist.jsonl") == []
