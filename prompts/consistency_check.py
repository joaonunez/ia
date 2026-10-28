"""Corre cada prompt del banco 3 veces y guarda el conteo.

Éxito = JSON válido y con las claves de ese prompt.
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prompt_bank import PROMPT_BANK
from gemini_api import build_request, extract_text, send_request

MODEL = "gemini-3.5-flash-lite"
REPEATS = 3
PAUSE_SECONDS = 1
OUTPUT = Path(__file__).resolve().parent / "registro_resultados.json"


def parse_response(text: str, expected_keys: list[str]) -> dict:
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text.strip(),
        flags=re.IGNORECASE | re.DOTALL,
    )
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("La respuesta no es un objeto JSON")
    missing = [key for key in expected_keys if key not in data]
    if missing:
        raise ValueError(f"Faltan claves: {', '.join(missing)}")
    return data


def run_once(prompt: dict) -> dict:
    url, headers, body = build_request(
        prompt["user_example"],
        MODEL,
        system_instruction=prompt["system_instruction"],
        response_schema=prompt.get("response_schema"),
    )
    data = send_request(url, headers, body)
    error = data.get("error")
    if error:
        code = error.get("code")
        raise RuntimeError(f"{code}: {error.get('message')}")
    text = extract_text(data)
    return parse_response(text, prompt["expected_keys"])


def main() -> None:
    record = {"modelo": MODEL, "repeticiones": REPEATS, "prompts": {}}
    for index, prompt in enumerate(PROMPT_BANK):
        name = prompt["name"]
        print(f"\n=== {name} ===")
        runs = []
        successes = 0
        for i in range(1, REPEATS + 1):
            try:
                data = run_once(prompt)
                successes += 1
                runs.append({"corrida": i, "ok": True, "datos": data})
                print(f"[{i}] ok {data}")
            except (ValueError, RuntimeError, json.JSONDecodeError) as error:
                runs.append({"corrida": i, "ok": False, "error": str(error)})
                print(f"[{i}] fallo: {error}")
            another_left = index < len(PROMPT_BANK) - 1 or i < REPEATS
            if another_left:
                time.sleep(PAUSE_SECONDS)
        record["prompts"][name] = {
            "exitos": successes,
            "total": REPEATS,
            "corridas": runs,
        }
        print(f"{name}: {successes}/{REPEATS}")
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRegistro en {OUTPUT}")


if __name__ == "__main__":
    main()
