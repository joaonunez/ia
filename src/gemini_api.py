import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Cómo actúa el asistente. Va en systemInstruction, aparte de la pregunta y del contexto.
SYSTEM_INSTRUCTION = (
    "Eres el asistente de solo lectura del gestor académico de la intranet escolar. "
    "Respondes en español y en pocas frases. "
    "Usas únicamente el JSON de contexto que acompaña la pregunta. "
    "No inventas alumnos, notas, asistencia, cursos ni promedios. "
    "No propones crear, editar ni borrar datos. "
    "Si el dato no está en el contexto, dices que no lo tienes."
)


def build_request(
    question: str,
    model: str,
    system_instruction: str | None = None,
    response_schema: dict | None = None,
) -> tuple[str, dict, dict]:
    if not question or not question.strip():
        raise ValueError("La pregunta no puede estar vacía")

    api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("No se encontro API_KEY ni GEMINI_API_KEY en el archivo .env")

    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    url = f"{base_url}/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    instruction = SYSTEM_INSTRUCTION if system_instruction is None else system_instruction
    body: dict = {
        "contents": [
            {
                "parts": [
                    {
                        "text": question.strip(),
                    }
                ]
            }
        ]
    }
    if instruction.strip():
        body["systemInstruction"] = {"parts": [{"text": instruction.strip()}]}
    if response_schema:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        }
    return url, headers, body


def send_request(url: str, headers: dict, body: dict) -> dict:
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "El servicio no respondió a tiempo. Intenta de nuevo en unos segundos."
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "No se pudo conectar con el servicio. Intenta de nuevo en unos segundos."
        )

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")


def extract_text(data: dict) -> str:
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(
            "La respuesta no trae el texto generado en el lugar esperado."
        )


def calculate_cost(data: dict, input_price: float, output_price: float) -> float:
    """Calcula el costo en USD de una respuesta usando usageMetadata.

    input_price y output_price son precios en USD por token.
    """
    try:
        usage = data["usageMetadata"]
        input_tokens = usage["promptTokenCount"]
        output_tokens = usage["candidatesTokenCount"]
    except KeyError:
        raise RuntimeError(
            "La respuesta no trae usageMetadata con el conteo de tokens esperado."
        )
    return input_tokens * input_price + output_tokens * output_price


def get_generated_text(question: str, model: str) -> str:
    url, headers, body = build_request(question, model)
    data = send_request(url, headers, body)
    return extract_text(data)


if __name__ == "__main__":
    print("Escribe una pregunta y pulsa Enter. Para cerrar, escribe salir.")
    while True:
        question = input("> ").strip()
        if question.lower() in {"salir", "exit", "quit"}:
            break
        try:
            result = get_generated_text(question, "gemini-flash-latest")
            print(result)
        except (ValueError, RuntimeError) as error:
            print("No se pudo completar la operación:", error)
