"""Chain orquestada del asistente del gestor académico (U2.3).

Tres pasos encadenados: clasificar la consulta, responder según el tema
(notas, asistencia u otro) y revisar la respuesta antes de entregarla.
Cada ruta tiene su propio fallback y hay una red de seguridad general
alrededor de toda la chain. El modelo entra como parámetro para poder
reemplazarlo por uno falso en las pruebas.

Los nombres del fuente están en inglés; los prompts y los mensajes que
ve quien usa el programa, en español.
"""
import logging
import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)

from gemini_api import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

# Las tres categorías que puede devolver el clasificador. Son palabras
# que lee el modelo, por eso van en español.
GRADES = "notas"
ATTENDANCE = "asistencia"
OTHER = "otro"

# Pasos 1, 2 y 3. Cada ruta usa un prompt distinto porque cada tema pide
# mirar otra parte del contexto. Todas heredan las reglas de solo lectura.
CLASSIFICATION_PROMPT = (
    "Clasifica la consulta de un gestor académico en una sola palabra: "
    f"{GRADES}, {ATTENDANCE} u {OTHER}. Responde solo con esa palabra.\n\n"
    "Consulta: {message}"
)
GRADES_PROMPT = (
    f"{SYSTEM_INSTRUCTION} La consulta es sobre notas y promedios: "
    "nombra a los estudiantes y da los valores exactos del contexto.\n\n"
    "Contexto:\n{context}\n\nConsulta: {message}"
)
ATTENDANCE_PROMPT = (
    f"{SYSTEM_INSTRUCTION} La consulta es sobre asistencia: "
    "da los porcentajes de asistencia exactos del contexto.\n\n"
    "Contexto:\n{context}\n\nConsulta: {message}"
)
OTHER_PROMPT = (
    f"{SYSTEM_INSTRUCTION} La consulta no es de notas ni de asistencia: "
    "responde solo si el contexto lo permite; si no, explica que este "
    "asistente consulta notas y asistencia.\n\n"
    "Contexto:\n{context}\n\nConsulta: {message}"
)
REVIEW_PROMPT = (
    "Revisa la respuesta de un asistente de solo lectura. Devuélvela en "
    "español y en pocas frases, quitando cualquier dato que no esté en el "
    "contexto y cualquier sugerencia de crear, editar o borrar datos. "
    "Si ya está bien, devuélvela igual.\n\n"
    "Contexto:\n{context}\n\nRespuesta: {answer}"
)

NO_CONTEXT = "(sin datos)"
FALLBACK_REPLY = (
    "Gracias por tu consulta. Una persona del equipo académico te "
    "responderá pronto."
)
ERROR_REPLY = (
    "No pudimos procesar tu consulta en este momento. Intenta de nuevo más tarde."
)
EMPTY_REPLY = "Escribe tu consulta para poder ayudarte."


def normalize_category(text: str) -> str:
    """Minúsculas, sin espacios ni puntuación en los bordes.

    El modelo puede devolver «Notas.» o «notas \\n» aunque el prompt pida
    una palabra suelta; sin esto, la comparación exacta caería siempre
    en la ruta por defecto sin avisar.
    """
    return text.strip().strip(".,;:!¡¿?\"'").lower()


def build_classification_step(model):
    """Paso 1: devuelve la categoría ya normalizada."""
    return (
        PromptTemplate.from_template(CLASSIFICATION_PROMPT)
        | model
        | StrOutputParser()
        | RunnableLambda(normalize_category)
    )


def build_route(prompt: str, model):
    """Pasos 2 y 3 de una ruta: responder y revisar.

    `assign` agrega `answer` sin perder `message` ni `context`, que la
    revisión también necesita. Un solo fallback cubre generar y revisar:
    si cualquiera de los dos falla, la persona recibe la respuesta de
    respaldo en vez de un texto sin revisar.
    """
    generation = PromptTemplate.from_template(prompt) | model | StrOutputParser()
    review = PromptTemplate.from_template(REVIEW_PROMPT) | model | StrOutputParser()
    route = RunnablePassthrough.assign(answer=generation) | review
    return route.with_fallbacks([RunnableLambda(lambda _: FALLBACK_REPLY)])


def build_routed_chain(
    classification_step,
    grades_route=None,
    attendance_route=None,
    default_route=None,
):
    """Clasifica y bifurca. Las rutas se pueden inyectar para probarlas.

    El orden importa: RunnableBranch se detiene en la primera condición
    verdadera, y la ruta por defecto (sin condición) va al final.
    """
    grades_route = grades_route or RunnablePassthrough()
    attendance_route = attendance_route or RunnablePassthrough()
    default_route = default_route or RunnablePassthrough()
    branch = RunnableBranch(
        (lambda x: x["category"] == GRADES, grades_route),
        (lambda x: x["category"] == ATTENDANCE, attendance_route),
        default_route,
    )
    return RunnablePassthrough.assign(category=classification_step) | branch


def build_chain(model):
    """La chain completa con las tres rutas reales, lista para invocar."""
    return build_routed_chain(
        build_classification_step(model),
        grades_route=build_route(GRADES_PROMPT, model),
        attendance_route=build_route(ATTENDANCE_PROMPT, model),
        default_route=build_route(OTHER_PROMPT, model),
    )


def process_message_safely(chain, message: str, context: str = "") -> str:
    """Red de seguridad general: ningún fallo deja a la persona sin respuesta.

    Cubre lo que un fallback de ruta no alcanza, como un error en la
    clasificación, que ocurre antes de elegir ruta. El error se registra;
    el texto de la consulta no, porque puede nombrar a un estudiante.
    """
    if not isinstance(message, str) or not message.strip():
        return EMPTY_REPLY
    try:
        return chain.invoke({"message": message, "context": context or NO_CONTEXT})
    except Exception:
        logger.exception("Falló el procesamiento de una consulta")
        return ERROR_REPLY


def main() -> None:
    """Corre la chain real con tres consultas y datos ficticios."""
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    from client import DEFAULT_MODEL

    load_dotenv()
    logging.basicConfig(level=logging.WARNING)
    api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
    # Sin `temperature`: gemini-3.5-flash-lite usa valores de muestreo fijos
    # e ignora el parámetro. El timeout convierte una demora en una excepción
    # que with_fallbacks sí puede atrapar.
    model = ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        api_key=api_key,
        timeout=20,
        max_retries=2,
    )
    chain = build_chain(model)
    context = (
        '{"curso": "2°B", "estudiantes": ['
        '{"nombre": "Ana Rojas", "promedio": 6.1, "asistencia": 96},'
        '{"nombre": "Diego Soto", "promedio": 3.7, "asistencia": 72},'
        '{"nombre": "Luis Pérez", "promedio": 5.4, "asistencia": 88},'
        '{"nombre": "Marta Díaz", "promedio": 4.8, "asistencia": 81}]}'
    )
    messages = [
        "¿Qué estudiante de 2°B tiene el promedio más bajo?",
        "¿Quiénes tienen menos de 85% de asistencia?",
        "¿Puedes borrar las notas de Diego Soto?",
    ]
    for message in messages:
        print(f"\nConsulta: {message}")
        print(f"Respuesta: {process_message_safely(chain, message, context)}")


if __name__ == "__main__":
    main()
