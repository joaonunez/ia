"""Agente con herramientas del asistente del gestor académico (U2.4).

Decide por sí mismo qué herramienta usar: consultar notas, consultar
asistencia o enviar un aviso al apoderado. Las dos primeras son de solo
lectura. La tercera es de riesgo alto y exige aprobación de una persona.
Los datos son ficticios y el aviso es simulado: no hay conexión con la
intranet real.

Los nombres del fuente están en inglés; lo que lee el modelo y la
persona, en español.
"""
import logging
import os
from collections.abc import Callable

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from supervision import (
    APPROVAL_FILE,
    TRACE_FILE,
    flag_repeated_tools,
    record_approval,
    record_trace,
    wait_for_approval,
)

logger = logging.getLogger(__name__)

# Datos ficticios de 2°B, los mismos de la comparación de modelos.
STUDENTS = {
    "ana rojas": {"name": "Ana Rojas", "average": 6.1, "attendance": 96, "absences": 2},
    "diego soto": {"name": "Diego Soto", "average": 3.7, "attendance": 72, "absences": 11},
    "luis pérez": {"name": "Luis Pérez", "average": 5.4, "attendance": 88, "absences": 5},
    "marta díaz": {"name": "Marta Díaz", "average": 4.8, "attendance": 81, "absences": 8},
}

# Tope de vueltas del ciclo razonar-actuar. Es un límite de autonomía: un
# agente que no converge se corta en vez de seguir llamando al modelo.
MAX_ITERATIONS = 5

AGENT_SYSTEM_PROMPT = (
    "Eres el asistente del gestor académico de la intranet escolar. "
    "Respondes en español y en pocas frases. "
    "Obtienes los datos solo con las herramientas: no inventas estudiantes, "
    "notas ni asistencia. Si una herramienta no encuentra al estudiante, "
    "lo dices. Solo envías un aviso a un apoderado cuando la persona lo "
    "pide de forma explícita."
)

ERROR_REPLY = "No pudimos procesar tu consulta en este momento. Intenta de nuevo más tarde."
EMPTY_REPLY = "Escribe tu consulta para poder ayudarte."


class GradesArgs(BaseModel):
    student_name: str = Field(
        description="Nombre completo del estudiante, por ejemplo 'Diego Soto'."
    )


class AttendanceArgs(BaseModel):
    student_name: str = Field(
        description="Nombre completo del estudiante, por ejemplo 'Diego Soto'."
    )
    include_absences: bool = Field(
        default=False,
        description="Si es True, agrega la cantidad de días de inasistencia.",
    )


class NoticeArgs(BaseModel):
    student_name: str = Field(
        description="Nombre completo del estudiante cuyo apoderado recibirá el aviso."
    )
    reason: str = Field(description="Motivo del aviso, en una frase.")


def content_to_text(content) -> str:
    """Deja el contenido de una respuesta como texto plano.

    Gemini puede devolver el contenido como una lista de bloques
    (`{"type": "text", "text": ..., "extras": {...}}`) en vez de un
    string. Guardado así en el historial, rompe el turno siguiente con
    «Message dict must contain 'role' and 'content'».
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


def find_student(name: str) -> dict | None:
    return STUDENTS.get(name.strip().lower())


def build_tools(
    approve: Callable[[str], bool] = wait_for_approval,
    approval_path=APPROVAL_FILE,
) -> list:
    """Las tres herramientas. `approve` entra como parámetro para probarlas.

    Todas devuelven texto y atrapan sus errores adentro: así el agente
    recibe una observación con la que razonar, no una excepción que
    corte el ciclo.
    """

    @tool("get_grades", args_schema=GradesArgs)
    def get_grades(student_name: str) -> str:
        """Consulta el promedio de notas de un estudiante de 2°B. Usar cuando
        la pregunta es sobre notas, promedio o rendimiento. Riesgo bajo:
        solo lee."""
        student = find_student(student_name)
        if student is None:
            return f"No se encontró un estudiante llamado {student_name}."
        return f"{student['name']} tiene promedio {student['average']}."

    @tool("get_attendance", args_schema=AttendanceArgs)
    def get_attendance(student_name: str, include_absences: bool = False) -> str:
        """Consulta el porcentaje de asistencia de un estudiante de 2°B, y
        opcionalmente sus días de inasistencia. Usar cuando la pregunta es
        sobre asistencia o inasistencias. Riesgo bajo: solo lee."""
        student = find_student(student_name)
        if student is None:
            return f"No se encontró un estudiante llamado {student_name}."
        text = f"{student['name']} tiene {student['attendance']}% de asistencia"
        if include_absences:
            text += f" ({student['absences']} días de inasistencia)"
        return text + "."

    @tool("send_guardian_notice", args_schema=NoticeArgs)
    def send_guardian_notice(student_name: str, reason: str) -> str:
        """Envía un aviso al apoderado de un estudiante. Acción de riesgo
        alto: no se puede deshacer y requiere aprobación humana antes de
        ejecutarse. Usar solo si la persona pide explícitamente avisar al
        apoderado."""
        student = find_student(student_name)
        if student is None:
            return f"No se encontró un estudiante llamado {student_name}."
        approved = approve(
            f"El agente quiere avisar al apoderado de {student['name']} "
            f"(motivo: {reason}). ¿Aprobar? (s/n): "
        )
        record_approval(
            "send_guardian_notice",
            {"student_name": student["name"], "reason": reason},
            approved,
            path=approval_path,
        )
        if not approved:
            return "Aviso no aprobado por la persona supervisora. No se envió nada."
        # Simulado: aquí iría el envío real por la intranet.
        return f"Aviso enviado (simulado) al apoderado de {student['name']}."

    return [get_grades, get_attendance, send_guardian_notice]


def build_executor(model, tools: list) -> AgentExecutor:
    """Agente y ejecutor. El historial y el scratchpad son dos placeholders distintos."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        return_intermediate_steps=True,
        max_iterations=MAX_ITERATIONS,
    )


def build_agent(model, approve: Callable[[str], bool] = wait_for_approval, approval_path=APPROVAL_FILE):
    """Agente con memoria por sesión. Devuelve (agente, historiales)."""
    executor = build_executor(model, build_tools(approve, approval_path))
    # La salida pasa por `content_to_text` antes de llegar al historial.
    normalized = executor | RunnableLambda(
        lambda result: {**result, "output": content_to_text(result["output"])}
    )
    histories: dict[str, InMemoryChatMessageHistory] = {}

    def get_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in histories:
            histories[session_id] = InMemoryChatMessageHistory()
        return histories[session_id]

    agent = RunnableWithMessageHistory(
        normalized,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    return agent, histories


def ask_agent(agent, session_id: str, message: str, trace_path=TRACE_FILE) -> str:
    """Una consulta con sesión, traza y red de seguridad.

    Dos `session_id` distintos no comparten historial. Si algo falla, la
    persona recibe un mensaje y el error queda en el log, sin la consulta.
    """
    if not isinstance(message, str) or not message.strip():
        return EMPTY_REPLY
    try:
        result = agent.invoke(
            {"input": message}, {"configurable": {"session_id": session_id}}
        )
        record_trace(session_id, message, result, path=trace_path)
        return result["output"]
    except Exception:
        logger.exception("Falló el procesamiento de una consulta del agente")
        return ERROR_REPLY


def main() -> None:
    """Conversación de demostración contra el modelo real, con datos ficticios."""
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    from client import DEFAULT_MODEL

    load_dotenv()
    logging.basicConfig(level=logging.WARNING)
    model = ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        api_key=os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY"),
        timeout=20,
        max_retries=2,
    )
    agent, _ = build_agent(model)
    for message in [
        "¿Qué promedio tiene Diego Soto?",
        "¿Y cuántos días de inasistencia tiene?",
        "Avisa al apoderado de Diego Soto que su promedio está bajo 4.0.",
        "¿Cómo se llama el director del colegio?",
    ]:
        print(f"\nConsulta: {message}")
        print(f"Respuesta: {ask_agent(agent, 'demo', message)}")
    print("\nRepeticiones sospechosas:", flag_repeated_tools())


if __name__ == "__main__":
    main()
