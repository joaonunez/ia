import os

import requests
from dotenv import load_dotenv

load_dotenv()


def build_request(question: str, model: str) -> tuple[str, dict, dict]:
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
    body = {
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
