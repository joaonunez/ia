"""Supervisión humana y trazas del agente (Bloque 23).

Aprobación con límite de tiempo, registro de cada decisión, registro de
cada interacción y una primera pasada automática sobre las trazas.

La espera de aprobación usa un hilo y no `select()`: `select()` sobre
`stdin` no funciona en Windows, y este proyecto se desarrolla ahí.
"""
import json
import logging
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DOCS = Path(__file__).resolve().parent.parent / "docs"
TRACE_FILE = DOCS / "agent-traces.jsonl"
APPROVAL_FILE = DOCS / "agent-approvals.jsonl"
DEFAULT_APPROVAL_TIMEOUT_SECONDS = 300


def wait_for_approval(
    prompt: str,
    timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS,
    ask: Callable[[str], str] = input,
) -> bool:
    """Pide una confirmación a una persona. Sin respuesta a tiempo, no aprueba.

    Para una acción de riesgo alto, «no aprobado» es el valor por defecto
    seguro: un timeout que ejecutara la acción anularía la supervisión.
    Cualquier respuesta que no sea «s» también cuenta como no aprobada, y
    un fallo al leer (por ejemplo, sin entrada estándar) igual.

    `ask` se puede reemplazar en las pruebas. Si se agota el tiempo, el hilo
    que espera la respuesta queda vivo hasta que alguien escriba algo; es
    un hilo demonio, así que no impide cerrar el programa.
    """
    answer: list[str] = []

    def read_answer() -> None:
        try:
            answer.append(ask(prompt))
        except (EOFError, OSError):
            logger.warning("No hay entrada estándar para pedir la aprobación")

    reader = threading.Thread(target=read_answer, daemon=True)
    reader.start()
    reader.join(timeout_seconds)
    if reader.is_alive() or not answer:
        return False
    return answer[0].strip().lower() == "s"


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_approval(
    tool: str,
    arguments: dict,
    approved: bool,
    path: Path = APPROVAL_FILE,
) -> None:
    """Guarda quién pidió qué, cuándo y con qué resultado. Se apruebe o no."""
    _append_jsonl(
        path,
        {
            "timestamp": _now(),
            "tool": tool,
            "arguments": arguments,
            "approved": approved,
        },
    )


def record_trace(
    session_id: str,
    user_input: str,
    result: dict,
    path: Path = TRACE_FILE,
) -> None:
    """Guarda una interacción: qué se preguntó, qué herramientas se usaron y la respuesta.

    Si `result` no trae `intermediate_steps` (el ejecutor se armó sin
    `return_intermediate_steps=True`), `actions` queda vacía en vez de fallar.
    """
    _append_jsonl(
        path,
        {
            "timestamp": _now(),
            "session_id": session_id,
            "input": user_input,
            "actions": [
                {
                    "tool": action.tool,
                    "arguments": action.tool_input,
                    "observation": observation,
                }
                for action, observation in result.get("intermediate_steps", [])
            ],
            "final_answer": result["output"],
        },
    )


def flag_repeated_tools(path: Path = TRACE_FILE) -> list[tuple[str, str]]:
    """Marca las sesiones donde la misma herramienta se usó dos veces seguidas.

    Devuelve pares (session_id, herramienta). Es una primera pasada que
    reduce muchas trazas a unas pocas candidatas: la decisión de si algo
    está mal sigue siendo de una persona. Compara solo el nombre de la
    herramienta, no sus argumentos, así que dos consultas seguidas a la
    misma herramienta con datos distintos también se marcan.
    """
    try:
        with open(path, encoding="utf-8") as file:
            records = [json.loads(line) for line in file if line.strip()]
    except FileNotFoundError:
        return []

    flagged = []
    for record in records:
        tools = [action["tool"] for action in record.get("actions", [])]
        for index in range(1, len(tools)):
            if tools[index] == tools[index - 1]:
                flagged.append((record["session_id"], tools[index]))
                break
    return flagged
